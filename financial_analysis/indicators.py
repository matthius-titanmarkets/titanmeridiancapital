"""
Technical indicators: SMA, EMA, RSI, MACD, Bollinger Bands.
All functions accept a pd.Series of closing prices and return
a pd.Series or pd.DataFrame aligned to the same index.
"""
import numpy as np
import pandas as pd


def sma(prices: pd.Series, window: int) -> pd.Series:
    """Simple Moving Average."""
    return prices.rolling(window).mean()


def ema(prices: pd.Series, span: int) -> pd.Series:
    """Exponential Moving Average."""
    return prices.ewm(span=span, adjust=False).mean()


def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index (Wilder smoothing via rolling mean).
    Returns values in [0, 100].
    """
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """
    MACD indicator.

    Returns a DataFrame with columns:
        macd      – MACD line (fast EMA − slow EMA)
        signal    – signal line (EMA of MACD)
        histogram – MACD − signal
    """
    fast_ema = ema(prices, fast)
    slow_ema = ema(prices, slow)
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return pd.DataFrame({
        "macd":      macd_line,
        "signal":    signal_line,
        "histogram": macd_line - signal_line,
    })


def bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """
    Bollinger Bands.

    Returns a DataFrame with columns: upper, mid, lower.
    """
    mid = sma(prices, window)
    std = prices.rolling(window).std()
    return pd.DataFrame({
        "upper": mid + num_std * std,
        "mid":   mid,
        "lower": mid - num_std * std,
    })
