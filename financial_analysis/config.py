"""
Configuration for the financial analysis suite.
Edit symbols, date range, portfolio weights, and strategy parameters here.
"""
from datetime import date, timedelta

# ─── Universe ─────────────────────────────────────────────────────────────────

SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "SPY"]
BENCHMARK = "SPY"

# ─── Date range ───────────────────────────────────────────────────────────────

END_DATE = date.today().isoformat()
START_DATE = (date.today() - timedelta(days=365 * 3)).isoformat()   # 3 years

# ─── Portfolio ────────────────────────────────────────────────────────────────

# Weights must sum to 1.0; benchmark excluded
PORTFOLIO: dict[str, float] = {
    "AAPL": 0.25,
    "MSFT": 0.25,
    "GOOGL": 0.25,
    "AMZN": 0.25,
}

# Annualised risk-free rate (e.g. 4.5% T-bill)
RISK_FREE_RATE = 0.045

# ─── Technical indicators ─────────────────────────────────────────────────────

INDICATORS: dict[str, int] = {
    "sma_short": 20,
    "sma_long":  50,
    "rsi_period": 14,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_window": 20,
    "bb_std": 2,
}

# ─── Backtest ─────────────────────────────────────────────────────────────────

BACKTEST: dict = {
    "symbol": "SPY",
    "initial_capital": 100_000,
    # "sma_crossover" | "rsi_mean_reversion"
    "strategy": "sma_crossover",
    "sma_short": 20,
    "sma_long":  50,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
}

# ─── Output ───────────────────────────────────────────────────────────────────

REPORT_PATH = "report.html"
