"""
Central configuration for the Titan Markets LLC trading bot.
All tuneable parameters live here — no magic numbers elsewhere.
"""
from __future__ import annotations

# ── Symbols ───────────────────────────────────────────────────────────────────

# Symbols the bot is allowed to trade.
# IB contract specs are resolved in broker.py per symbol type.
SYMBOLS: list[str] = [
    # FX majors
    "EURUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCAD", "NZDUSD",
    # Gold
    "XAUUSD",
    # Indices (traded as CFDs/futures via IB)
    "NAS100", "SPX500", "US30",
]

# ── Session windows (UTC) ─────────────────────────────────────────────────────

SESSIONS: list[dict] = [
    {"name": "London Open",  "start_utc": "08:00", "end_utc": "11:00"},
    {"name": "New York Open", "start_utc": "13:30", "end_utc": "16:00"},
]

# Minutes before session end to force-close any open position
SESSION_CLOSE_BUFFER_MINUTES: int = 30

# ── MACD parameters ───────────────────────────────────────────────────────────

MACD_FAST:   int = 12
MACD_SLOW:   int = 26
MACD_SIGNAL: int = 9

# ── Bollinger Band parameters ─────────────────────────────────────────────────

BB_WINDOW:   int   = 20
BB_NUM_STD:  float = 2.0

# ATR period (used for SL buffer beyond the BB)
ATR_PERIOD:  int   = 14

# How many ATRs beyond the BB to place the stop loss
SL_ATR_BUFFER: float = 0.5

# ── Risk management ───────────────────────────────────────────────────────────

# Fraction of current NAV to risk per trade (1 % default)
RISK_PER_TRADE_PCT: float = 0.01

# Take-profit as a multiple of the risk amount (R:R)
TAKE_PROFIT_RR: float = 2.5

# Maximum number of open positions at any time
MAX_POSITIONS: int = 3

# Daily loss limit as a fraction of NAV — bot pauses for the day when hit
DAILY_LOSS_LIMIT_PCT: float = 0.02

# Peak-to-trough drawdown that triggers a full bot stop + alert
MAX_DRAWDOWN_PCT: float = 0.05

# ── Live-mode trigger ─────────────────────────────────────────────────────────

# When bot_nav >= starting_nav * (1 + LIVE_THRESHOLD), prompt to go live
LIVE_THRESHOLD: float = 0.10   # 10 %

# ── Interactive Brokers connection ────────────────────────────────────────────

IB_HOST: str = "127.0.0.1"

# TWS paper: 7497  |  IB Gateway paper: 4002
# TWS live:  7496  |  IB Gateway live:  4001
IB_PORT_PAPER: int = 7497
IB_PORT_LIVE:  int = 7496

IB_CLIENT_ID: int = 42          # must be unique per connected client
IB_RECONNECT_ATTEMPTS: int = 5
IB_RECONNECT_DELAY_SEC: int = 5

# ── Data / bars ───────────────────────────────────────────────────────────────

# How many historical bars to fetch for indicator warm-up
WARMUP_BARS: int = 100

# Bar size used for signal generation (IB barSizeSetting string)
BAR_SIZE: str = "5 mins"

# ── Webhook server ────────────────────────────────────────────────────────────

WEBHOOK_PORT: int  = 5001
WEBHOOK_HOST: str  = "0.0.0.0"

# Set a random secret in your environment: WEBHOOK_SECRET=<token>
# The Pine Script alert JSON must include {"secret": "<token>", ...}
WEBHOOK_SECRET_ENV_VAR: str = "WEBHOOK_SECRET"

# ── State file ────────────────────────────────────────────────────────────────

import os
STATE_FILE: str = os.path.join(os.path.dirname(__file__), "bot_state.json")

# Starting NAV is pulled from PropFirm P&L at bot launch (see state_manager.py)
# Override here if you want a fixed starting value
STARTING_NAV_OVERRIDE: float | None = None
