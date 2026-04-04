"""
Single-asset backtesting engine.

Supported strategies
--------------------
  sma_crossover       – long when SMA(short) > SMA(long), else cash
  rsi_mean_reversion  – buy on RSI < oversold, sell on RSI > overbought
"""
import pandas as pd

from analysis import annualized_return, annualized_volatility, sharpe_ratio, max_drawdown
from indicators import sma, rsi


class Backtest:
    """
    Vectorised backtest for a single asset.

    Parameters
    ----------
    ohlcv : pd.DataFrame
        Must have at least a 'Close' column.
    initial_capital : float
        Starting portfolio value in dollars.
    """

    def __init__(self, ohlcv: pd.DataFrame, initial_capital: float = 100_000):
        self.ohlcv = ohlcv
        self.initial_capital = initial_capital

        # Populated by run_*
        self.results: dict = {}
        self.equity_curve: pd.Series = pd.Series(dtype=float)
        self.bh_equity_curve: pd.Series = pd.Series(dtype=float)
        self.strategy_returns: pd.Series = pd.Series(dtype=float)
        self.bh_returns: pd.Series = pd.Series(dtype=float)
        self.df: pd.DataFrame = pd.DataFrame()
        self.position: pd.Series = pd.Series(dtype=float)
        self.trades: pd.DataFrame = pd.DataFrame()

    # ─── Public strategies ────────────────────────────────────────────────────

    def run_sma_crossover(self, short: int = 20, long: int = 50) -> None:
        """Buy when SMA(short) crosses above SMA(long); sell when it crosses below."""
        df = self.ohlcv.copy()
        df["sma_short"] = sma(df["Close"], short)
        df["sma_long"]  = sma(df["Close"], long)
        df.dropna(inplace=True)

        signal   = (df["sma_short"] > df["sma_long"]).astype(int)
        position = signal.shift(1).fillna(0)   # execute on next open
        self._simulate(df, position, f"SMA Crossover ({short}/{long})")

    def run_rsi_mean_reversion(
        self,
        period: int = 14,
        oversold: int = 30,
        overbought: int = 70,
    ) -> None:
        """Enter long when RSI drops below *oversold*; exit when RSI rises above *overbought*."""
        df = self.ohlcv.copy()
        df["rsi"] = rsi(df["Close"], period)
        df.dropna(inplace=True)

        raw_pos  = pd.Series(0, index=df.index, dtype=int)
        in_trade = False
        for i, r in enumerate(df["rsi"]):
            if not in_trade and r < oversold:
                in_trade = True
            elif in_trade and r > overbought:
                in_trade = False
            raw_pos.iloc[i] = 1 if in_trade else 0

        position = raw_pos.shift(1).fillna(0)
        self._simulate(df, position, f"RSI Mean Reversion ({period}/{oversold}/{overbought})")

    # ─── Internal ─────────────────────────────────────────────────────────────

    def _simulate(self, df: pd.DataFrame, position: pd.Series, name: str) -> None:
        daily_ret     = df["Close"].pct_change().fillna(0)
        strategy_ret  = position * daily_ret
        bh_ret        = daily_ret

        equity    = self.initial_capital * (1 + strategy_ret).cumprod()
        bh_equity = self.initial_capital * (1 + bh_ret).cumprod()
        trades_df = self._extract_trades(df, position)

        self.df               = df
        self.position         = position
        self.equity_curve     = equity
        self.bh_equity_curve  = bh_equity
        self.strategy_returns = strategy_ret.iloc[1:]   # drop leading 0
        self.bh_returns       = bh_ret.iloc[1:]
        self.trades           = trades_df

        win_rate = trades_df["win"].mean() if len(trades_df) > 0 else float("nan")
        self.results = {
            "Strategy":               name,
            "Strategy Total Return":  f"{equity.iloc[-1] / self.initial_capital - 1:.2%}",
            "Buy & Hold Return":      f"{bh_equity.iloc[-1] / self.initial_capital - 1:.2%}",
            "Strategy Sharpe":        f"{sharpe_ratio(self.strategy_returns):.2f}",
            "B&H Sharpe":             f"{sharpe_ratio(self.bh_returns):.2f}",
            "Strategy Max Drawdown":  f"{max_drawdown(equity):.2%}",
            "B&H Max Drawdown":       f"{max_drawdown(bh_equity):.2%}",
            "Total Trades":           len(trades_df),
            "Win Rate":               f"{win_rate:.1%}" if trades_df is not None and len(trades_df) > 0 else "N/A",
        }

    def _extract_trades(self, df: pd.DataFrame, position: pd.Series) -> pd.DataFrame:
        """Parse position series into a trade-by-trade log."""
        transitions = position.diff()
        entries = df.index[transitions == 1]
        exits   = df.index[transitions == -1]

        records = []
        for entry in entries:
            later_exits = exits[exits > entry]
            exit_date   = later_exits[0] if len(later_exits) > 0 else df.index[-1]
            entry_px    = df.loc[entry,     "Close"]
            exit_px     = df.loc[exit_date, "Close"]
            ret         = exit_px / entry_px - 1
            records.append({
                "Entry":       entry.date(),
                "Exit":        exit_date.date(),
                "Entry Price": round(entry_px, 2),
                "Exit Price":  round(exit_px,  2),
                "Return":      f"{ret:.2%}",
                "win":         ret > 0,
            })
        return pd.DataFrame(records)
