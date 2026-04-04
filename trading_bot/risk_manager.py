"""
Risk management layer.

Responsibilities
----------------
- Gate new entries against daily loss limit and max drawdown
- Track daily P&L reset at midnight UTC
- Detect when the 10% live-mode threshold is reached
- Expose a single check() method the bot loop calls before every order
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, date

import config as cfg

logger = logging.getLogger(__name__)


class RiskManager:
    def __init__(self, state) -> None:
        """
        Parameters
        ----------
        state : StateManager instance (passed in to avoid circular imports)
        """
        self._state = state
        self._daily_reset_date: date | None = None
        self._daily_pnl: float = 0.0

    # ── Daily reset ────────────────────────────────────────────────────────────

    def _maybe_reset_daily(self) -> None:
        today = datetime.now(timezone.utc).date()
        if self._daily_reset_date != today:
            self._daily_reset_date = today
            self._daily_pnl = 0.0
            logger.info("Daily P&L counter reset for %s.", today)

    # ── Core gate ──────────────────────────────────────────────────────────────

    def can_trade(self, symbol: str, open_positions: list[dict]) -> tuple[bool, str]:
        """
        Return (True, "") if a new entry is allowed, else (False, reason).

        Checks (in order):
        1. Bot is not stopped
        2. Max concurrent positions not reached
        3. No existing position in this symbol
        4. Daily loss budget not exhausted
        5. Peak drawdown kill-switch not triggered
        """
        self._maybe_reset_daily()
        s = self._state.get()

        if s.get("stopped"):
            return False, "Bot is stopped."

        if len(open_positions) >= cfg.MAX_POSITIONS:
            return False, f"Max positions ({cfg.MAX_POSITIONS}) reached."

        if any(p["symbol"] == symbol for p in open_positions):
            return False, f"Already have a position in {symbol}."

        nav = s.get("current_nav", s.get("starting_nav", 1))
        if nav <= 0:
            return False, "NAV is zero or negative."

        daily_loss_limit = nav * cfg.DAILY_LOSS_LIMIT_PCT
        if self._daily_pnl <= -daily_loss_limit:
            return False, (
                f"Daily loss limit hit "
                f"(${self._daily_pnl:,.2f} / limit ${-daily_loss_limit:,.2f})."
            )

        peak_nav = s.get("peak_nav", nav)
        drawdown_pct = (nav - peak_nav) / peak_nav if peak_nav > 0 else 0.0
        if drawdown_pct <= -cfg.MAX_DRAWDOWN_PCT:
            self._state.update({"stopped": True})
            msg = (
                f"MAX DRAWDOWN KILL-SWITCH triggered "
                f"({drawdown_pct:.1%} drawdown). Bot stopped."
            )
            logger.critical(msg)
            return False, msg

        return True, ""

    # ── Post-trade update ──────────────────────────────────────────────────────

    def record_trade_result(self, pnl: float) -> None:
        """Call after each closed trade to update daily P&L and NAV."""
        self._maybe_reset_daily()
        self._daily_pnl += pnl

        s = self._state.get()
        new_nav  = s.get("current_nav", s.get("starting_nav", 0)) + pnl
        peak_nav = max(s.get("peak_nav", new_nav), new_nav)

        self._state.update({
            "current_nav": new_nav,
            "peak_nav":    peak_nav,
        })

        logger.info(
            "Trade result: P&L=%.2f  daily_pnl=%.2f  NAV=%.2f",
            pnl, self._daily_pnl, new_nav,
        )

        self._check_live_threshold(new_nav, s)

    # ── Live-mode threshold check ──────────────────────────────────────────────

    def _check_live_threshold(self, current_nav: float, state: dict) -> None:
        if state.get("mode") != "paper":
            return
        if state.get("live_threshold_reached"):
            return

        starting = state.get("starting_nav", current_nav)
        target   = starting * (1 + cfg.LIVE_THRESHOLD)

        if current_nav >= target:
            self._state.update({"live_threshold_reached": True})
            logger.warning(
                "LIVE THRESHOLD REACHED: NAV $%.2f >= target $%.2f (+%.0f%%). "
                "Type 'confirm live' in the terminal or click the button in the Bot tab "
                "to switch to live trading.",
                current_nav, target, cfg.LIVE_THRESHOLD * 100,
            )
            print(
                f"\n{'='*60}\n"
                f"  10% PROFIT TARGET HIT — NAV: ${current_nav:,.2f}\n"
                f"  Bot is ready to switch to LIVE trading.\n"
                f"  Type 'confirm live' and press Enter to activate.\n"
                f"{'='*60}\n"
            )

    # ── Accessors ──────────────────────────────────────────────────────────────

    @property
    def daily_pnl(self) -> float:
        return self._daily_pnl

    def is_stopped(self) -> bool:
        return bool(self._state.get().get("stopped", False))
