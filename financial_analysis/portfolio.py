"""
Portfolio-level analysis: weighted returns, correlation, and summary stats.
"""
import pandas as pd

from analysis import (
    daily_returns,
    annualized_return,
    annualized_volatility,
    sharpe_ratio,
    max_drawdown,
    cumulative_returns,
)


def portfolio_returns(prices: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    """
    Compute daily weighted portfolio returns.

    weights – dict mapping symbol → weight (must sum to 1.0)
    """
    syms = list(weights.keys())
    w = pd.Series(weights)
    rets = daily_returns(prices[syms]).dropna()
    return rets.dot(w).rename("Portfolio")


def correlation_matrix(prices: pd.DataFrame) -> pd.DataFrame:
    """Return pairwise correlation of daily returns."""
    return daily_returns(prices).corr()


def portfolio_stats(
    prices: pd.DataFrame,
    weights: dict[str, float],
    risk_free_rate: float = 0.045,
) -> dict[str, str]:
    """High-level performance stats for the weighted portfolio."""
    port_rets = portfolio_returns(prices, weights)
    port_equity = (1 + port_rets).cumprod()
    return {
        "Total Return":          f"{(1 + port_rets).prod() - 1:.2%}",
        "Annualized Return":     f"{annualized_return(port_rets):.2%}",
        "Annualized Volatility": f"{annualized_volatility(port_rets):.2%}",
        "Sharpe Ratio":          f"{sharpe_ratio(port_rets, risk_free_rate):.2f}",
        "Max Drawdown":          f"{max_drawdown(port_equity):.2%}",
    }


def asset_stats_table(prices: pd.DataFrame, risk_free_rate: float = 0.045) -> pd.DataFrame:
    """
    Return a formatted summary statistics DataFrame, one row per symbol.
    """
    rows = []
    for sym in prices.columns:
        r = daily_returns(prices[sym]).dropna()
        p = prices[sym].dropna()
        rows.append({
            "Symbol":       sym,
            "Total Return": f"{(1 + r).prod() - 1:.2%}",
            "Ann. Return":  f"{annualized_return(r):.2%}",
            "Ann. Vol":     f"{annualized_volatility(r):.2%}",
            "Sharpe":       f"{sharpe_ratio(r, risk_free_rate):.2f}",
            "Max DD":       f"{max_drawdown(p):.2%}",
        })
    return pd.DataFrame(rows).set_index("Symbol")
