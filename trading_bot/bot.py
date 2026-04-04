"""
Titan Markets LLC — Trading Bot
================================
Main event loop.

Usage
-----
  python3 bot.py --paper          # paper trading (default)
  python3 bot.py --live           # live trading (requires prior 10% threshold)
  python3 bot.py --sim            # full simulation, no IB connection needed
  python3 bot.py --paper --reset  # re-initialise state from PropFirm NAV

The loop runs every POLL_INTERVAL_SEC seconds and:
  1. Fetches fresh bars for each symbol
  2. Generates MACD + BB + session signals
  3. Also drains any queued TradingView webhook signals
  4. Gates each signal through RiskManager
  5. Sizes the position and places a bracket order via Broker
  6. Checks open positions for time-based exits
  7. Listens for terminal input to confirm live-mode switch
"""
from __future__ import annotations

import argparse
import logging
import queue
import sys
import threading
import time
from datetime import datetime, timezone

import config as cfg
from broker import Broker, compute_position_size
from risk_manager import RiskManager
from signals import Signal, generate_signals, should_time_exit
from state_manager import StateManager, get_propfirm_nav

# ── Logging setup ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", mode="a"),
    ],
)
logger = logging.getLogger("bot")

# ── Shared webhook signal queue (written by webhook_server.py thread) ──────────
webhook_queue: queue.Queue[Signal] = queue.Queue()

POLL_INTERVAL_SEC = 60   # check for new bars every minute


# ── Main bot class ─────────────────────────────────────────────────────────────

class TitanBot:
    def __init__(self, mode: str = "paper", simulation: bool = False) -> None:
        self.mode       = mode
        self.simulation = simulation
        self.state      = StateManager()
        self.broker     = Broker(mode=mode, simulation=simulation)
        self.risk       = RiskManager(self.state)
        self._running   = False

    # ── Startup ────────────────────────────────────────────────────────────────

    def start(self, reset: bool = False) -> None:
        logger.info("=" * 60)
        logger.info("Titan Markets LLC — Trading Bot starting")
        logger.info("Mode: %s  |  Simulation: %s", self.mode.upper(), self.simulation)
        logger.info("=" * 60)

        # Initialise state
        if reset or self.state.get().get("starting_nav", 0) == 0:
            starting_nav = (
                cfg.STARTING_NAV_OVERRIDE
                or get_propfirm_nav()
                or 100_000.0
            )
            self.state.initialise(starting_nav=starting_nav, mode=self.mode)
            logger.info("Starting NAV set to $%.2f", starting_nav)
        else:
            logger.info(
                "Resuming from saved state: NAV=$%.2f  mode=%s",
                self.state.get()["current_nav"],
                self.state.get()["mode"],
            )

        # Connect to IB
        if not self.broker.connect():
            logger.error("Failed to connect to IB. Exiting.")
            sys.exit(1)

        self._running = True

        # Start background threads
        threading.Thread(target=self._terminal_input_thread, daemon=True).start()
        threading.Thread(target=self._position_monitor_thread, daemon=True).start()

        logger.info("Bot loop started. Press Ctrl+C to stop.")
        self._loop()

    def stop(self) -> None:
        self._running = False
        self.state.update({"status": "stopped"})
        self.broker.disconnect()
        logger.info("Bot stopped.")

    # ── Main loop ──────────────────────────────────────────────────────────────

    def _loop(self) -> None:
        while self._running:
            try:
                self._tick()
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt — shutting down.")
                self.stop()
                break
            except Exception as exc:
                logger.error("Unhandled error in main loop: %s", exc, exc_info=True)

            time.sleep(POLL_INTERVAL_SEC)

    def _tick(self) -> None:
        """One iteration: scan symbols + drain webhook queue."""
        if self.risk.is_stopped():
            logger.warning("Bot is stopped — skipping tick.")
            return

        # Sync mode from state (in case webhook_server toggled it)
        saved_mode = self.state.get().get("mode", self.mode)
        if saved_mode != self.mode:
            self._switch_live()

        open_positions = self.state.get_positions()

        # 1. Python-generated signals
        for symbol in cfg.SYMBOLS:
            self._process_symbol(symbol, open_positions)

        # 2. TradingView webhook signals
        while not webhook_queue.empty():
            try:
                signal = webhook_queue.get_nowait()
                logger.info("Processing webhook signal: %s", signal)
                self._execute_signal(signal, open_positions)
                open_positions = self.state.get_positions()  # refresh after each order
            except queue.Empty:
                break

    def _process_symbol(self, symbol: str, open_positions: list[dict]) -> None:
        """Fetch bars, generate signals, attempt entry."""
        bars = self.broker.get_bars(symbol)
        if bars.empty:
            if not self.simulation:
                return
            # In simulation mode, generate mock bars for testing
            bars = _mock_bars(symbol)

        signals = generate_signals(bars, symbol)
        for signal in signals:
            self._execute_signal(signal, open_positions)
            open_positions = self.state.get_positions()

    def _execute_signal(self, signal: Signal, open_positions: list[dict]) -> None:
        """Gate through risk, size position, place order, update state."""
        allowed, reason = self.risk.can_trade(signal.symbol, open_positions)
        if not allowed:
            logger.debug("Signal rejected [%s]: %s", signal.symbol, reason)
            return

        nav = self.state.get().get("current_nav", 0)
        if nav <= 0:
            logger.warning("NAV is zero — cannot size position for %s.", signal.symbol)
            return

        qty = compute_position_size(nav, signal.entry_price, signal.stop_loss, signal.symbol)
        if qty <= 0:
            logger.warning("Computed zero quantity for %s — skipping.", signal.symbol)
            return

        logger.info("Executing %s", signal)

        order_info = self.broker.place_bracket_order(signal, qty)

        position = {
            "symbol":     signal.symbol,
            "direction":  signal.direction,
            "quantity":   qty,
            "entry":      signal.entry_price,
            "sl":         signal.stop_loss,
            "tp":         signal.take_profit,
            "opened_at":  datetime.now(timezone.utc).isoformat(),
            "order_info": order_info,
        }
        self.state.add_position(position)
        self.state.log_signal({
            "symbol":    signal.symbol,
            "direction": signal.direction,
            "entry":     signal.entry_price,
            "sl":        signal.stop_loss,
            "tp":        signal.take_profit,
        })
        logger.info("Position opened: %s %s qty=%.4f", signal.direction, signal.symbol, qty)

    # ── Position monitor ────────────────────────────────────────────────────────

    def _position_monitor_thread(self) -> None:
        """
        Background thread: checks open positions for time-based exits every 30s.
        Also syncs IB-closed positions (filled SL/TP) back to state.
        """
        while self._running:
            time.sleep(30)
            try:
                self._check_time_exits()
                self._sync_closed_positions()
            except Exception as exc:
                logger.error("Position monitor error: %s", exc)

    def _check_time_exits(self) -> None:
        """Force-close positions if session is about to end."""
        now = datetime.now(timezone.utc)
        for pos in self.state.get_positions():
            if should_time_exit(pos["symbol"], now):
                logger.info(
                    "Time exit: closing %s %s — session ending soon.",
                    pos["direction"], pos["symbol"],
                )
                self.broker.close_position_market(
                    pos["symbol"], pos["quantity"], pos["direction"]
                )
                # Record as time-exit with unknown exact P&L
                self._close_position_in_state(pos["symbol"], pnl=0.0, exit_reason="time_exit")

    def _sync_closed_positions(self) -> None:
        """
        Check if IB has closed any positions (SL/TP filled) and update state.
        In simulation mode this is skipped.
        """
        if self.simulation:
            return

        ib_positions = {p["symbol"] for p in self.broker.get_positions()}
        for pos in self.state.get_positions():
            if pos["symbol"] not in ib_positions:
                # Position was closed by IB (SL or TP hit)
                logger.info("IB closed position detected: %s", pos["symbol"])
                self._close_position_in_state(pos["symbol"], pnl=0.0, exit_reason="ib_filled")

    def _close_position_in_state(
        self, symbol: str, pnl: float, exit_reason: str
    ) -> None:
        pos = self.state.remove_position(symbol)
        if pos is None:
            return
        trade = {
            "symbol":       symbol,
            "direction":    pos.get("direction"),
            "entry":        pos.get("entry"),
            "quantity":     pos.get("quantity"),
            "sl":           pos.get("sl"),
            "tp":           pos.get("tp"),
            "opened_at":    pos.get("opened_at"),
            "closed_at":    datetime.now(timezone.utc).isoformat(),
            "pnl":          pnl,
            "exit_reason":  exit_reason,
        }
        self.state.log_trade(trade)
        if pnl != 0:
            self.risk.record_trade_result(pnl)

    # ── Live mode switch ────────────────────────────────────────────────────────

    def _switch_live(self) -> None:
        logger.info("Switching to LIVE trading mode.")
        self.state.confirm_live_switch()
        self.mode = "live"
        self.broker.switch_mode("live")
        self.state.update({"mode": "live"})
        logger.info("Now trading LIVE on IB port %d.", cfg.IB_PORT_LIVE)

    # ── Terminal input thread ───────────────────────────────────────────────────

    def _terminal_input_thread(self) -> None:
        """Listen for terminal commands in a background thread."""
        while self._running:
            try:
                cmd = input().strip().lower()
            except EOFError:
                break

            if cmd == "confirm live":
                if self.state.get().get("mode") == "paper":
                    if self.state.get().get("live_threshold_reached"):
                        self._switch_live()
                    else:
                        print(
                            "10% profit target not yet reached. "
                            "Current NAV: ${:,.2f} / Target: ${:,.2f}".format(
                                self.state.get()["current_nav"],
                                self.state.get()["starting_nav"] * (1 + cfg.LIVE_THRESHOLD),
                            )
                        )
                else:
                    print("Already in live mode.")

            elif cmd == "force live":
                # Override — switch to live without the threshold requirement
                print("WARNING: Forcing live mode without 10% target. Confirm? (yes/no)")
                confirm = input().strip().lower()
                if confirm == "yes":
                    self._switch_live()

            elif cmd == "status":
                s = self.state.get()
                print(
                    f"\nMode: {s['mode'].upper()}  |  Status: {s['status']}\n"
                    f"NAV: ${s['current_nav']:,.2f}  |  "
                    f"Start: ${s['starting_nav']:,.2f}  |  "
                    f"Peak: ${s['peak_nav']:,.2f}\n"
                    f"Open positions: {len(s['open_positions'])}\n"
                    f"Trades today: {len(s['signals_today'])}\n"
                )

            elif cmd == "stop":
                print("Stopping bot...")
                self._running = False
                self.state.update({"stopped": True, "status": "stopped"})

            elif cmd == "help":
                print(
                    "\nCommands:\n"
                    "  status         — show current bot status\n"
                    "  confirm live   — switch to live trading (requires 10% target)\n"
                    "  force live     — switch to live without target (use with caution)\n"
                    "  stop           — stop the bot\n"
                )


# ── Simulation helpers ─────────────────────────────────────────────────────────

def _mock_bars(symbol: str) -> "pd.DataFrame":
    """
    Return synthetic OHLCV bars for use in simulation / testing.
    Generates 100 bars of random-walk price data around a base price.
    """
    import numpy as np
    import pandas as pd

    base_prices = {
        "EURUSD": 1.0850, "GBPUSD": 1.2700, "AUDUSD": 0.6500,
        "USDJPY": 150.00, "USDCAD": 1.3600, "NZDUSD": 0.6000,
        "XAUUSD": 3050.0, "NAS100": 19500.0, "SPX500": 5200.0, "US30": 42000.0,
    }
    base  = base_prices.get(symbol, 1.0)
    n     = 100
    noise = base * 0.001
    close = base + np.cumsum(np.random.randn(n) * noise)
    high  = close + np.abs(np.random.randn(n) * noise)
    low   = close - np.abs(np.random.randn(n) * noise)
    open_ = np.roll(close, 1)
    open_[0] = close[0]

    idx = pd.date_range(end=pd.Timestamp.utcnow(), periods=n, freq="5min", tz="UTC")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": 1000},
        index=idx,
    )


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Titan Markets LLC Trading Bot")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--paper", action="store_true", default=True,
                       help="Paper trading mode (default)")
    group.add_argument("--live",  action="store_true",
                       help="Live trading mode")
    group.add_argument("--sim",   action="store_true",
                       help="Full simulation — no IB connection")
    parser.add_argument("--reset", action="store_true",
                        help="Re-initialise state from PropFirm NAV")
    args = parser.parse_args()

    if args.live:
        mode, sim = "live", False
    elif args.sim:
        mode, sim = "paper", True
    else:
        mode, sim = "paper", False

    bot = TitanBot(mode=mode, simulation=sim)
    bot.start(reset=args.reset)


if __name__ == "__main__":
    main()
