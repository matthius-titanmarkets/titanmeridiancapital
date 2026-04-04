"""
Signal generation: MACD + Bollinger Bands with London/NY session filter.

Entry logic
-----------
Long:   MACD line crosses ABOVE signal line  AND  close <= lower BB  AND  in session
Short:  MACD line crosses BELOW signal line  AND  close >= upper BB  AND  in session

Stop-loss:   lower BB - SL_ATR_BUFFER * ATR  (long)
             upper BB + SL_ATR_BUFFER * ATR  (short)
Take-profit: entry ± (entry - stop_loss) * TAKE_PROFIT_RR
"""
from __future__ import annotations

import sys
import os
from datetime import datetime, time, timezone
from typing import Literal

import numpy as np
import pandas as pd

# Reuse indicators already in the repo
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "financial_analysis"))
from indicators import macd as _macd, bollinger_bands as _bb  # type: ignore

import config as cfg


# ── Types ──────────────────────────────────────────────────────────────────────

SignalDirection = Literal["LONG", "SHORT"]


class Signal:
    __slots__ = ("symbol", "direction", "entry_price", "stop_loss", "take_profit", "timestamp")

    def __init__(
        self,
        symbol: str,
        direction: SignalDirection,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        timestamp: datetime,
    ) -> None:
        self.symbol      = symbol
        self.direction   = direction
        self.entry_price = entry_price
        self.stop_loss   = stop_loss
        self.take_profit = take_profit
        self.timestamp   = timestamp

    def __repr__(self) -> str:
        return (
            f"Signal({self.symbol} {self.direction} @ {self.entry_price:.5g} "
            f"SL={self.stop_loss:.5g} TP={self.take_profit:.5g})"
        )


# ── Session helpers ────────────────────────────────────────────────────────────

def _parse_time(t: str) -> time:
    """Parse 'HH:MM' string into a time object."""
    h, m = t.split(":")
    return time(int(h), int(m), tzinfo=timezone.utc)


def in_session(now: datetime | None = None) -> bool:
    """Return True if *now* (UTC) falls inside any configured session window."""
    if now is None:
        now = datetime.now(timezone.utc)
    now_time = now.timetz()
    for session in cfg.SESSIONS:
        start = _parse_time(session["start_utc"])
        end   = _parse_time(session["end_utc"])
        if start <= now_time <= end:
            return True
    return False


def minutes_to_session_end(now: datetime | None = None) -> int | None:
    """
    Return minutes remaining until the *current* session ends.
    Returns None if not currently in any session.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    now_time = now.timetz()
    for session in cfg.SESSIONS:
        start = _parse_time(session["start_utc"])
        end   = _parse_time(session["end_utc"])
        if start <= now_time <= end:
            end_dt = now.replace(hour=end.hour, minute=end.minute, second=0, microsecond=0)
            return max(0, int((end_dt - now).total_seconds() / 60))
    return None


# ── ATR ────────────────────────────────────────────────────────────────────────

def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range."""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


# ── Signal generation ──────────────────────────────────────────────────────────

def generate_signals(
    ohlcv: pd.DataFrame,
    symbol: str,
    now: datetime | None = None,
) -> list[Signal]:
    """
    Analyse a bar DataFrame and return any entry signals.

    Parameters
    ----------
    ohlcv : DataFrame with columns [open, high, low, close, volume],
            DatetimeIndex in UTC, most-recent bar last.
    symbol : Instrument ticker (for labelling the signal).
    now    : Override for current UTC time (useful in tests).

    Returns
    -------
    List of Signal objects (empty if no entry triggered).
    """
    if now is None:
        now = datetime.now(timezone.utc)

    if not in_session(now):
        return []

    close = ohlcv["close"]
    high  = ohlcv["high"]
    low   = ohlcv["low"]

    if len(close) < cfg.BB_WINDOW + cfg.MACD_SLOW + cfg.MACD_SIGNAL:
        return []  # not enough bars to warm up indicators

    # Compute indicators
    macd_df = _macd(close, cfg.MACD_FAST, cfg.MACD_SLOW, cfg.MACD_SIGNAL)
    bb_df   = _bb(close, cfg.BB_WINDOW, cfg.BB_NUM_STD)
    atr_s   = _atr(high, low, close, cfg.ATR_PERIOD)

    # Current bar (last complete bar)
    c_macd  = macd_df["macd"].iloc[-1]
    c_sig   = macd_df["signal"].iloc[-1]
    p_macd  = macd_df["macd"].iloc[-2]
    p_sig   = macd_df["signal"].iloc[-2]

    c_close = close.iloc[-1]
    c_upper = bb_df["upper"].iloc[-1]
    c_lower = bb_df["lower"].iloc[-1]
    c_atr   = atr_s.iloc[-1]

    if np.isnan(c_atr) or c_atr == 0:
        return []

    signals: list[Signal] = []

    # Long: MACD crossed up + price at/below lower BB
    macd_crossed_up   = (p_macd <= p_sig) and (c_macd > c_sig)
    price_at_lower_bb = c_close <= c_lower

    if macd_crossed_up and price_at_lower_bb:
        sl = c_lower - cfg.SL_ATR_BUFFER * c_atr
        tp = c_close + (c_close - sl) * cfg.TAKE_PROFIT_RR
        signals.append(Signal(symbol, "LONG", c_close, sl, tp, now))

    # Short: MACD crossed down + price at/above upper BB
    macd_crossed_down  = (p_macd >= p_sig) and (c_macd < c_sig)
    price_at_upper_bb  = c_close >= c_upper

    if macd_crossed_down and price_at_upper_bb:
        sl = c_upper + cfg.SL_ATR_BUFFER * c_atr
        tp = c_close - (sl - c_close) * cfg.TAKE_PROFIT_RR
        signals.append(Signal(symbol, "SHORT", c_close, sl, tp, now))

    return signals


def should_time_exit(symbol: str, now: datetime | None = None) -> bool:
    """
    Return True if the bot should force-close a position because the
    session ends in ≤ SESSION_CLOSE_BUFFER_MINUTES.
    """
    mins = minutes_to_session_end(now)
    if mins is None:
        return False
    return mins <= cfg.SESSION_CLOSE_BUFFER_MINUTES
