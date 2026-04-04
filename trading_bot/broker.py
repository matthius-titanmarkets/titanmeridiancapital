"""
Interactive Brokers wrapper using ib_insync.

Responsibilities
----------------
- Connect / disconnect (paper or live)
- Resolve contract objects for FX, Gold (commodity), and Index CFDs
- Fetch historical OHLCV bars
- Place bracket orders (entry + attached SL + TP)
- Query open positions and account NAV
- Cancel orders / close positions at market
"""
from __future__ import annotations

import logging
import time as _time
from typing import Optional

import pandas as pd

try:
    from ib_insync import (
        IB, Contract, Forex, ComboLeg,
        Stock, CFD, Future, Commodity,
        MarketOrder, LimitOrder, StopOrder,
        BracketOrder, util,
    )
    IB_AVAILABLE = True
except ImportError:
    IB_AVAILABLE = False
    logging.warning(
        "ib_insync not installed — broker will run in SIMULATION mode. "
        "Run: pip install ib_insync"
    )

import config as cfg
from signals import Signal

logger = logging.getLogger(__name__)


# ── Contract resolution ────────────────────────────────────────────────────────

# FX pairs traded via IDEALPRO
_FX_PAIRS = {
    "EURUSD", "GBPUSD", "AUDUSD", "USDJPY",
    "USDCAD", "NZDUSD", "USDCHF",
}

# Commodity / precious metals
_COMMODITY_MAP = {
    "XAUUSD": ("XAUUSD", "CMDTY", "SMART"),
    "XAGUSD": ("XAGUSD", "CMDTY", "SMART"),
    "GOLD":   ("XAUUSD", "CMDTY", "SMART"),
}

# Indices — traded as CFDs (check IB availability in your region)
_INDEX_CFD_MAP = {
    "NAS100": ("NAS100", "USD"),
    "SPX500": ("SPX500", "USD"),
    "US30":   ("US30",   "USD"),
}


def _make_contract(symbol: str) -> "Contract":
    """Return an IB Contract object for the given symbol string."""
    if not IB_AVAILABLE:
        return None  # type: ignore

    if symbol in _FX_PAIRS:
        base, quote = symbol[:3], symbol[3:]
        return Forex(pair=symbol)

    if symbol in _COMMODITY_MAP:
        sym, sec_type, exchange = _COMMODITY_MAP[symbol]
        c = Contract()
        c.symbol    = sym
        c.secType   = sec_type
        c.exchange  = exchange
        c.currency  = "USD"
        return c

    if symbol in _INDEX_CFD_MAP:
        sym, currency = _INDEX_CFD_MAP[symbol]
        c = CFD(symbol=sym, currency=currency)
        return c

    raise ValueError(f"Unknown symbol: {symbol}. Add it to broker.py contract maps.")


# ── Pip / tick size helpers ────────────────────────────────────────────────────

def _pip_size(symbol: str) -> float:
    """Return the pip size for position-size calculations."""
    if symbol in {"USDJPY", "EURJPY", "GBPJPY"}:
        return 0.01
    if symbol in _COMMODITY_MAP or symbol in {"GOLD", "XAUUSD"}:
        return 0.10   # gold: $0.10/oz per contract
    if symbol in _INDEX_CFD_MAP:
        return 1.0    # index points
    return 0.0001     # standard FX


# ── Broker class ───────────────────────────────────────────────────────────────

class Broker:
    """
    Thin IB wrapper.  All order methods are no-ops (logged only) when
    ib_insync is unavailable OR when simulation=True.
    """

    def __init__(self, mode: str = "paper", simulation: bool = False) -> None:
        self.mode       = mode        # "paper" | "live"
        self.simulation = simulation or not IB_AVAILABLE
        self._ib: Optional["IB"] = None

        if self.simulation:
            logger.info("Broker running in SIMULATION mode — no real orders will be placed.")

    # ── Connection ─────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        if self.simulation:
            logger.info("[SIM] connect() called — skipped.")
            return True

        port = cfg.IB_PORT_PAPER if self.mode == "paper" else cfg.IB_PORT_LIVE
        self._ib = IB()

        for attempt in range(1, cfg.IB_RECONNECT_ATTEMPTS + 1):
            try:
                self._ib.connect(cfg.IB_HOST, port, clientId=cfg.IB_CLIENT_ID)
                logger.info(
                    "Connected to IB %s (port %d) on attempt %d",
                    self.mode, port, attempt,
                )
                return True
            except Exception as exc:
                logger.warning("IB connect attempt %d failed: %s", attempt, exc)
                if attempt < cfg.IB_RECONNECT_ATTEMPTS:
                    _time.sleep(cfg.IB_RECONNECT_DELAY_SEC * attempt)

        logger.error("Could not connect to IB after %d attempts.", cfg.IB_RECONNECT_ATTEMPTS)
        return False

    def disconnect(self) -> None:
        if self._ib and self._ib.isConnected():
            self._ib.disconnect()
            logger.info("Disconnected from IB.")

    def is_connected(self) -> bool:
        if self.simulation:
            return True
        return bool(self._ib and self._ib.isConnected())

    def switch_mode(self, new_mode: str) -> bool:
        """Switch between paper and live — reconnects to new port."""
        logger.info("Switching broker mode: %s → %s", self.mode, new_mode)
        self.disconnect()
        self.mode = new_mode
        return self.connect()

    # ── Market data ────────────────────────────────────────────────────────────

    def get_bars(self, symbol: str, bar_size: str = None, num_bars: int = None) -> pd.DataFrame:
        """
        Fetch historical OHLCV bars from IB.

        Returns a DataFrame with columns [open, high, low, close, volume]
        and a UTC DatetimeIndex.  Returns empty DataFrame on error.
        """
        bar_size = bar_size or cfg.BAR_SIZE
        num_bars = num_bars or cfg.WARMUP_BARS

        if self.simulation:
            logger.debug("[SIM] get_bars(%s) — returning empty DataFrame.", symbol)
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        if not self.is_connected():
            logger.error("get_bars called but IB not connected.")
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        try:
            contract = _make_contract(symbol)
            self._ib.qualifyContracts(contract)

            # IB duration string: estimate from bar size and num_bars
            duration = _bars_to_duration(bar_size, num_bars)
            bars = self._ib.reqHistoricalData(
                contract,
                endDateTime="",
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow="MIDPOINT" if symbol in _FX_PAIRS else "TRADES",
                useRTH=False,
                formatDate=1,
            )
            df = util.df(bars)
            if df.empty:
                return df
            df = df.rename(columns={"date": "datetime", "barCount": "bar_count"})
            df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
            df = df.set_index("datetime")[["open", "high", "low", "close", "volume"]]
            return df

        except Exception as exc:
            logger.error("get_bars(%s) failed: %s", symbol, exc)
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    # ── Orders ─────────────────────────────────────────────────────────────────

    def place_bracket_order(
        self,
        signal: Signal,
        quantity: float,
    ) -> dict:
        """
        Place a bracket order: entry (limit) + stop-loss + take-profit.

        Returns a dict with order IDs (or simulated IDs).
        """
        direction = signal.direction  # "LONG" | "SHORT"
        action    = "BUY" if direction == "LONG" else "SELL"
        sl_action = "SELL" if direction == "LONG" else "BUY"

        logger.info(
            "%s %s %s qty=%.4f entry=%.5g SL=%.5g TP=%.5g",
            "[SIM]" if self.simulation else "[LIVE]",
            action, signal.symbol, quantity,
            signal.entry_price, signal.stop_loss, signal.take_profit,
        )

        if self.simulation:
            return {
                "parent_id": -1,
                "sl_id":     -2,
                "tp_id":     -3,
                "symbol":    signal.symbol,
                "direction": direction,
                "quantity":  quantity,
                "entry":     signal.entry_price,
                "sl":        signal.stop_loss,
                "tp":        signal.take_profit,
                "simulated": True,
            }

        if not self.is_connected():
            raise ConnectionError("IB not connected — cannot place order.")

        contract = _make_contract(signal.symbol)
        self._ib.qualifyContracts(contract)

        parent = LimitOrder(
            action     = action,
            totalQuantity = quantity,
            lmtPrice   = round(signal.entry_price, 5),
            transmit   = False,
        )
        sl = StopOrder(
            action     = sl_action,
            totalQuantity = quantity,
            stopPrice  = round(signal.stop_loss, 5),
            transmit   = False,
        )
        tp = LimitOrder(
            action     = sl_action,
            totalQuantity = quantity,
            lmtPrice   = round(signal.take_profit, 5),
            transmit   = True,
        )

        bracket = self._ib.bracketOrder(action, quantity,
                                         signal.entry_price,
                                         signal.take_profit,
                                         signal.stop_loss)
        trades = [self._ib.placeOrder(contract, o) for o in bracket]
        self._ib.sleep(0.5)

        return {
            "parent_id": trades[0].order.orderId,
            "sl_id":     trades[2].order.orderId,
            "tp_id":     trades[1].order.orderId,
            "symbol":    signal.symbol,
            "direction": direction,
            "quantity":  quantity,
            "entry":     signal.entry_price,
            "sl":        signal.stop_loss,
            "tp":        signal.take_profit,
            "simulated": False,
        }

    def close_position_market(self, symbol: str, quantity: float, direction: str) -> bool:
        """Close an open position at market price."""
        close_action = "SELL" if direction == "LONG" else "BUY"
        logger.info(
            "%s closing %s %s qty=%.4f at market",
            "[SIM]" if self.simulation else "[LIVE]",
            close_action, symbol, quantity,
        )

        if self.simulation:
            return True

        if not self.is_connected():
            logger.error("close_position_market: not connected.")
            return False

        try:
            contract = _make_contract(symbol)
            self._ib.qualifyContracts(contract)
            order = MarketOrder(close_action, quantity)
            self._ib.placeOrder(contract, order)
            self._ib.sleep(0.5)
            return True
        except Exception as exc:
            logger.error("close_position_market(%s) failed: %s", symbol, exc)
            return False

    def cancel_all_orders(self, symbol: str | None = None) -> None:
        """Cancel all open orders, optionally filtered by symbol."""
        if self.simulation:
            logger.info("[SIM] cancel_all_orders(%s)", symbol)
            return
        if not self.is_connected():
            return
        try:
            open_orders = self._ib.openOrders()
            for order in open_orders:
                self._ib.cancelOrder(order)
            self._ib.sleep(0.5)
        except Exception as exc:
            logger.error("cancel_all_orders failed: %s", exc)

    # ── Account info ───────────────────────────────────────────────────────────

    def get_nav(self) -> float:
        """Return account Net Asset Value in USD."""
        if self.simulation:
            return 0.0   # caller should use state_manager NAV instead

        if not self.is_connected():
            return 0.0

        try:
            account_values = self._ib.accountValues()
            for av in account_values:
                if av.tag == "NetLiquidation" and av.currency == "USD":
                    return float(av.value)
        except Exception as exc:
            logger.error("get_nav failed: %s", exc)
        return 0.0

    def get_positions(self) -> list[dict]:
        """Return a list of open position dicts."""
        if self.simulation:
            return []

        if not self.is_connected():
            return []

        try:
            positions = self._ib.positions()
            result = []
            for pos in positions:
                result.append({
                    "symbol":    pos.contract.symbol,
                    "quantity":  pos.position,
                    "avg_cost":  pos.avgCost,
                })
            return result
        except Exception as exc:
            logger.error("get_positions failed: %s", exc)
            return []


# ── Helpers ────────────────────────────────────────────────────────────────────

def _bars_to_duration(bar_size: str, num_bars: int) -> str:
    """Convert bar_size + num_bars into an IB durationStr."""
    bar_minutes = {
        "1 min": 1, "2 mins": 2, "3 mins": 3, "5 mins": 5,
        "10 mins": 10, "15 mins": 15, "30 mins": 30,
        "1 hour": 60, "4 hours": 240, "1 day": 1440,
    }.get(bar_size, 5)

    total_minutes = bar_minutes * num_bars
    if total_minutes <= 1440:
        return f"{max(1, total_minutes // 60 + 1)} D"
    days = total_minutes // 1440 + 1
    if days <= 30:
        return f"{days} D"
    return f"{days // 7 + 1} W"


def compute_position_size(
    nav: float,
    entry: float,
    stop_loss: float,
    symbol: str,
    risk_pct: float = None,
) -> float:
    """
    Calculate position size (in lots/contracts) given a risk percentage of NAV.

    For FX: size in standard lots (100,000 units).
    For Gold/Indices: size in contracts.
    """
    risk_pct  = risk_pct or cfg.RISK_PER_TRADE_PCT
    risk_usd  = nav * risk_pct
    sl_distance = abs(entry - stop_loss)

    if sl_distance == 0:
        return 0.0

    pip = _pip_size(symbol)

    if symbol in _FX_PAIRS:
        # 1 standard lot = 100,000 units; 1 pip = $10 per lot (USD-quoted)
        # For JPY pairs, pip value differs — simplified here
        pip_value_per_lot = 10.0 if not symbol.endswith("JPY") else 1000.0
        sl_pips = sl_distance / pip
        lots = risk_usd / (sl_pips * pip_value_per_lot)
        # Clamp to min 0.01 lot (micro), max 10 lots
        return round(max(0.01, min(10.0, lots)), 2)

    if symbol in _COMMODITY_MAP or symbol in {"GOLD"}:
        # Gold: contract = 100 oz; pip = $0.01 — simplify to units
        value_per_unit_per_pip = 1.0
        units = risk_usd / (sl_distance * value_per_unit_per_pip)
        return round(max(0.1, min(100.0, units)), 1)

    if symbol in _INDEX_CFD_MAP:
        # Index CFD: $1 per point per contract
        contracts = risk_usd / sl_distance
        return round(max(1.0, min(50.0, contracts)), 0)

    return 1.0
