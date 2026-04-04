"""
Market data fetching via yfinance.
"""
import pandas as pd
import yfinance as yf


def fetch_prices(symbols: list[str], start: str, end: str, price_col: str = "Close") -> pd.DataFrame:
    """
    Fetch adjusted closing prices for one or more symbols.

    Returns a DataFrame with dates as index and symbols as columns.
    """
    data = yf.download(symbols, start=start, end=end, auto_adjust=True, progress=False)

    if len(symbols) == 1:
        prices = data[[price_col]].rename(columns={price_col: symbols[0]})
    else:
        prices = data[price_col]

    # Drop timezone from index so comparisons with plain dates work
    prices.index = pd.to_datetime(prices.index).tz_localize(None)
    return prices.dropna(how="all")


def fetch_ohlcv(symbol: str, start: str, end: str) -> pd.DataFrame:
    """
    Fetch full OHLCV data for a single symbol.

    Returns a DataFrame with columns: Open, High, Low, Close, Volume.
    """
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end, auto_adjust=True)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df[["Open", "High", "Low", "Close", "Volume"]]
