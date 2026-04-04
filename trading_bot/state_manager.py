"""
Persistent state manager — reads/writes bot_state.json.

The state file is the single source of truth shared between:
  - bot.py (writes live updates)
  - dashboard.py Bot tab (reads for display)
  - webhook_server.py (reads mode to decide whether to enqueue signals)

Schema
------
{
  "mode":                  "paper" | "live",
  "stopped":               false,
  "starting_nav":          100000.0,
  "current_nav":           100000.0,
  "peak_nav":              100000.0,
  "live_threshold_reached": false,
  "last_updated":          "2026-04-04T08:30:00Z",
  "open_positions":        [],      // list of position dicts
  "trade_log":             [],      // list of closed trade dicts
  "signals_today":         [],      // list of signal dicts (reset daily)
  "status":                "running" | "paused" | "stopped",
  "daily_pnl":             0.0,
  "bot_version":           "1.0.0"
}
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from threading import Lock
from typing import Any

import config as cfg

logger = logging.getLogger(__name__)

_DEFAULT_STATE: dict[str, Any] = {
    "mode":                   "paper",
    "stopped":                False,
    "starting_nav":           0.0,
    "current_nav":            0.0,
    "peak_nav":               0.0,
    "live_threshold_reached": False,
    "last_updated":           "",
    "open_positions":         [],
    "trade_log":              [],
    "signals_today":          [],
    "status":                 "running",
    "daily_pnl":              0.0,
    "bot_version":            "1.0.0",
}


class StateManager:
    def __init__(self, path: str = None) -> None:
        self._path  = path or cfg.STATE_FILE
        self._lock  = Lock()
        self._state: dict[str, Any] = {}
        self._load()

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if os.path.exists(self._path):
            try:
                with open(self._path, "r") as f:
                    data = json.load(f)
                self._state = {**_DEFAULT_STATE, **data}
                logger.info("State loaded from %s", self._path)
                return
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not load state file (%s) — starting fresh.", exc)
        self._state = dict(_DEFAULT_STATE)

    def _save(self) -> None:
        self._state["last_updated"] = datetime.now(timezone.utc).isoformat()
        try:
            tmp = self._path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(self._state, f, indent=2, default=str)
            os.replace(tmp, self._path)
        except OSError as exc:
            logger.error("Failed to save state: %s", exc)

    # ── Public API ─────────────────────────────────────────────────────────────

    def get(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._state)

    def update(self, patch: dict[str, Any]) -> None:
        with self._lock:
            self._state.update(patch)
            self._save()

    def initialise(self, starting_nav: float, mode: str = "paper") -> None:
        """Call once at bot startup to set starting NAV and mode."""
        with self._lock:
            # Preserve existing trade_log and open_positions across restarts
            existing_log       = self._state.get("trade_log", [])
            existing_positions = self._state.get("open_positions", [])
            self._state = {
                **_DEFAULT_STATE,
                "starting_nav":    starting_nav,
                "current_nav":     starting_nav,
                "peak_nav":        starting_nav,
                "mode":            mode,
                "trade_log":       existing_log,
                "open_positions":  existing_positions,
                "status":          "running",
            }
            self._save()
        logger.info("State initialised: mode=%s  starting_nav=$%.2f", mode, starting_nav)

    # ── Position tracking ──────────────────────────────────────────────────────

    def add_position(self, position: dict) -> None:
        with self._lock:
            positions = self._state.get("open_positions", [])
            # Avoid duplicates by symbol
            positions = [p for p in positions if p.get("symbol") != position["symbol"]]
            positions.append(position)
            self._state["open_positions"] = positions
            self._save()

    def remove_position(self, symbol: str) -> dict | None:
        with self._lock:
            positions = self._state.get("open_positions", [])
            removed = next((p for p in positions if p["symbol"] == symbol), None)
            self._state["open_positions"] = [p for p in positions if p["symbol"] != symbol]
            self._save()
        return removed

    def get_positions(self) -> list[dict]:
        with self._lock:
            return list(self._state.get("open_positions", []))

    # ── Trade log ──────────────────────────────────────────────────────────────

    def log_trade(self, trade: dict) -> None:
        """Append a closed trade to the trade log (max 500 entries)."""
        with self._lock:
            log = self._state.get("trade_log", [])
            log.append({**trade, "logged_at": datetime.now(timezone.utc).isoformat()})
            self._state["trade_log"] = log[-500:]
            self._save()

    # ── Signal log ─────────────────────────────────────────────────────────────

    def log_signal(self, signal_dict: dict) -> None:
        """Append a signal to today's signal log (max 100 entries)."""
        with self._lock:
            signals = self._state.get("signals_today", [])
            signals.append({**signal_dict, "ts": datetime.now(timezone.utc).isoformat()})
            self._state["signals_today"] = signals[-100:]
            self._save()

    # ── Live mode switch ───────────────────────────────────────────────────────

    def confirm_live_switch(self) -> None:
        """Persist the mode change to 'live'. Broker reconnection handled by bot.py."""
        with self._lock:
            self._state["mode"] = "live"
            self._save()
        logger.info("State updated: mode=live")


# ── Utility: derive starting NAV from PropFirm data ───────────────────────────

def get_propfirm_nav() -> float:
    """
    Pull the current NAV from the existing data_pipeline so the bot starts
    relative to real firm performance.  Falls back to 0 on any error.
    """
    try:
        pipeline_dir = os.path.join(os.path.dirname(__file__), "..")
        sys.path.insert(0, pipeline_dir)
        from data_pipeline import load_propfirm_trades, compute_metrics  # type: ignore
        trades = load_propfirm_trades()
        if trades.empty:
            return 0.0
        metrics = compute_metrics(trades, starting_capital=100_000)
        nav = metrics.get("current_nav", 0.0)
        logger.info("PropFirm NAV loaded: $%.2f", nav)
        return float(nav)
    except Exception as exc:
        logger.warning("Could not load PropFirm NAV (%s) — defaulting to 0.", exc)
        return 0.0
