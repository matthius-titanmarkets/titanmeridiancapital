"""
Core return and risk metrics for individual assets.
"""
import numpy as np
import pandas as pd


# ─── Returns ──────────────────────────────────────────────────────────────────

def daily_returns(prices: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    return prices.pct_change().dropna()


def cumulative_returns(returns: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    return (1 + returns).cumprod() - 1


# ─── Drawdown ─────────────────────────────────────────────────────────────────

def drawdown_series(prices: pd.Series) -> pd.Series:
    """Percentage drawdown from the rolling peak."""
    rolling_max = prices.cummax()
    return (prices - rolling_max) / rolling_max


def max_drawdown(prices: pd.Series) -> float:
    return drawdown_series(prices).min()


# ─── Risk / return statistics ─────────────────────────────────────────────────

def annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    n = len(returns)
    if n == 0:
        return float("nan")
    total = (1 + returns).prod()
    return float(total ** (periods_per_year / n) - 1)


def annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    return float(returns.std() * np.sqrt(periods_per_year))


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
    excess = returns - risk_free_rate / periods_per_year
    std = excess.std()
    if std == 0:
        return 0.0
    return float((excess.mean() / std) * np.sqrt(periods_per_year))


def sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
    excess = returns - risk_free_rate / periods_per_year
    downside_std = excess[excess < 0].std()
    if downside_std == 0:
        return 0.0
    return float((excess.mean() / downside_std) * np.sqrt(periods_per_year))


def calmar_ratio(returns: pd.Series, prices: pd.Series) -> float:
    mdd = abs(max_drawdown(prices))
    if mdd == 0:
        return 0.0
    return float(annualized_return(returns) / mdd)


# ─── Summary table ────────────────────────────────────────────────────────────

def summary_stats(returns: pd.Series, prices: pd.Series, risk_free_rate: float = 0.045) -> dict[str, str]:
    return {
        "Total Return":          f"{cumulative_returns(returns).iloc[-1]:.2%}",
        "Annualized Return":     f"{annualized_return(returns):.2%}",
        "Annualized Volatility": f"{annualized_volatility(returns):.2%}",
        "Sharpe Ratio":          f"{sharpe_ratio(returns, risk_free_rate):.2f}",
        "Sortino Ratio":         f"{sortino_ratio(returns, risk_free_rate):.2f}",
        "Max Drawdown":          f"{max_drawdown(prices):.2%}",
        "Calmar Ratio":          f"{calmar_ratio(returns, prices):.2f}",
    }
