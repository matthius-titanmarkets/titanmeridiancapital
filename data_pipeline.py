"""
data_pipeline.py
Real-data feed layer for the Titan Markets dashboard.

Sources
-------
* PropFirm_Portfolio.numbers  — 126 closed trades with explicit USD P&L
* paper-trading-history CSV   — TradingView paper-account order history

Public API
----------
load_propfirm_trades()   -> pd.DataFrame
load_paper_orders()      -> pd.DataFrame
compute_paper_trade_pnl()-> pd.DataFrame   (matched round-trips only)
compute_metrics(df)      -> dict
load_monthly_summary()   -> pd.DataFrame
"""

from __future__ import annotations

import re
import numpy as np
import pandas as pd
from numbers_parser import Document

# ── Paths ─────────────────────────────────────────────────────────────────────

NUMBERS_PATH = (
    "/Users/mattdoug/Desktop/TMLLC/Analysis report/PropFirm_Portfolio.numbers"
)
CSV_PATH = (
    "/Users/mattdoug/Downloads/paper-trading-history-all-"
    "2025-05-31T03_02_39.908Z_04290.csv"
)

# ── Helpers ───────────────────────────────────────────────────────────────────

_FX_TOKENS  = {"USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CHF", "CAD"}
_COMM_SYMS  = {"XAUUSD", "XAGUSD", "GOLD", "OIL", "WTI", "XAUUSD"}
_IDX_SYMS   = {"SPX500", "NAS100", "US30", "DAX", "ES", "MES", "SPY",
               "SPX", "DOW"}
_USD_QUOTED = {"EURUSD", "GBPUSD", "AUDUSD", "NZDUSD",
               "GOLD", "XAUUSD", "XAGUSD"}   # P&L is in USD directly


def classify_symbol(sym: str) -> str:
    s = sym.upper().strip()
    if s in _COMM_SYMS:
        return "Commodities"
    if s in _IDX_SYMS:
        return "Indices"
    parts = re.findall(r"[A-Z]{3}", s)
    if any(p in _FX_TOKENS for p in parts):
        return "FX"
    return "Other"


def _clean_qty(val) -> float:
    """Strip commas / currency suffixes and coerce to float."""
    if pd.isna(val):
        return float("nan")
    return float(re.sub(r"[^\d.]", "", str(val)))


# ── PropFirm Numbers loader ────────────────────────────────────────────────────

def load_propfirm_trades(path: str = NUMBERS_PATH) -> pd.DataFrame:
    """
    Load the 'Trade Log' sheet from PropFirm_Portfolio.numbers.

    Returns a DataFrame with columns:
        id, date, symbol, direction, entry, exit, lots, pnl, asset_class
    """
    doc   = Document(path)
    table = doc.sheets["Trade Log"].tables[0]
    hdrs  = [table.cell(0, c).value for c in range(table.num_cols)]

    rows = []
    for r in range(1, table.num_rows):
        if table.cell(r, 0).value is None:
            break
        rows.append({hdrs[c]: table.cell(r, c).value for c in range(table.num_cols)})

    df = pd.DataFrame(rows).rename(columns={
        "Trade ID":     "id",
        "Date":         "date",
        "Pair":         "symbol",
        "Position":     "direction",
        "Entry Price":  "entry",
        "Exit Price":   "exit",
        "Lots":         "lots",
        "Profit (USD)": "pnl",
    })

    df["id"]        = pd.to_numeric(df["id"],  errors="coerce").apply(lambda x: int(x) if pd.notna(x) else pd.NA).astype("Int64")
    df["date"]      = pd.to_datetime(df["date"])
    df["pnl"]       = pd.to_numeric(df["pnl"], errors="coerce")
    df["entry"]     = pd.to_numeric(df["entry"], errors="coerce")
    df["exit"]      = pd.to_numeric(df["exit"],  errors="coerce")
    df["lots"]      = pd.to_numeric(df["lots"],  errors="coerce")
    df["symbol"]    = df["symbol"].str.strip().str.upper()
    df["asset_class"] = df["symbol"].map(classify_symbol)
    df["source"]    = "propfirm"

    return (
        df.dropna(subset=["pnl"])
          .sort_values("date")
          .reset_index(drop=True)
    )


# ── Monthly summary loader ────────────────────────────────────────────────────

def load_monthly_summary(path: str = NUMBERS_PATH) -> pd.DataFrame:
    """
    Load the 'Portfolio Summary' sheet.

    Returns monthly stats with columns:
        month, winning_trades, losing_trades, win_rate_pct,
        total_profit, avg_profit, max_profit, max_loss, total_trades
    """
    doc   = Document(path)
    table = doc.sheets["Portfolio Summary"].tables[0]
    hdrs  = [table.cell(0, c).value for c in range(table.num_cols)]

    rows = []
    for r in range(1, table.num_rows):
        row = {hdrs[c]: table.cell(r, c).value for c in range(table.num_cols)}
        tp  = row.get("Total Profit (USD)")
        if tp is not None and tp != 0 and isinstance(tp, (int, float)):
            rows.append(row)

    df = pd.DataFrame(rows).rename(columns={
        "Months":                           "month",
        "Winning Trades":                   "winning_trades",
        "Losing Trades":                    "losing_trades",
        "Win Rate (%)":                     "win_rate_pct",
        "Total Profit (USD)":               "total_profit",
        "Average Profit per Trade (USD)":   "avg_profit",
        "Max Profit (USD)":                 "max_profit",
        "Max Loss (USD)":                   "max_loss",
        "Total Trades (98)":                "total_trades",
    })

    df["month"]       = pd.to_datetime(df["month"])
    df["win_rate_pct"] = pd.to_numeric(df["win_rate_pct"], errors="coerce") * 100
    for col in ["total_profit", "avg_profit", "max_profit", "max_loss", "total_trades",
                "winning_trades", "losing_trades"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.sort_values("month").reset_index(drop=True)


# ── Paper trading loader ──────────────────────────────────────────────────────

def load_paper_orders(path: str = CSV_PATH) -> pd.DataFrame:
    """
    Load the raw paper-trading order CSV.

    Returns all Filled orders with clean_symbol and asset_class columns.
    """
    raw = pd.read_csv(path)
    raw.columns = raw.columns.str.strip()

    for col in ["Fill Price", "Limit Price", "Stop Price"]:
        raw[col] = pd.to_numeric(raw[col], errors="coerce")

    raw["Qty"]          = raw["Qty"].apply(_clean_qty)
    raw["Placing Time"] = pd.to_datetime(raw["Placing Time"])
    raw["Closing Time"] = pd.to_datetime(raw["Closing Time"])

    filled = raw[raw["Status"] == "Filled"].copy()
    filled["clean_symbol"] = (
        filled["Symbol"]
        .str.split(":")
        .str[-1]
        .str.replace(r"\d+!?$", "", regex=True)
        .str.upper()
        .str.strip()
    )
    filled["asset_class"]  = filled["clean_symbol"].map(classify_symbol)
    filled["has_margin"]   = (
        filled["Margin"].notna() &
        (filled["Margin"].astype(str).str.strip() != "")
    )

    return filled.reset_index(drop=True)


def compute_paper_trade_pnl(path: str = CSV_PATH) -> pd.DataFrame:
    """
    Match opening and closing filled orders to produce round-trip P&L.

    P&L is computed only for USD-quoted instruments (EURUSD, GOLD, XAUUSD, …).
    Other pairs are included with pnl=NaN.
    """
    df = load_paper_orders(path)
    df = df.sort_values("Placing Time").reset_index(drop=True)

    # Separate openers (margin present) and closers (no margin)
    openers = df[df["has_margin"]].copy().reset_index(drop=True)
    closers = df[~df["has_margin"]].copy().reset_index(drop=True)

    used_closer_idx = set()
    trades = []

    for _, op in openers.iterrows():
        sym  = op["clean_symbol"]
        side = op["Side"]
        qty  = op["Qty"]
        ep   = op["Fill Price"]

        # Find earliest unmatched closer: same symbol, opposite side, same qty
        opp = "Sell" if side == "Buy" else "Buy"
        mask = (
            (closers["clean_symbol"] == sym) &
            (closers["Side"] == opp) &
            (np.abs(closers["Qty"] - qty) < 1) &        # exact qty match
            (closers["Closing Time"] >= op["Placing Time"]) &
            (~closers.index.isin(used_closer_idx))
        )
        match = closers[mask].sort_values("Closing Time").head(1)

        if match.empty:
            continue

        cl_idx = match.index[0]
        used_closer_idx.add(cl_idx)
        xp = match.iloc[0]["Fill Price"]

        # P&L for USD-quoted instruments
        if sym in _USD_QUOTED and pd.notna(ep) and pd.notna(xp):
            pnl = (xp - ep) * qty if side == "Buy" else (ep - xp) * qty
        else:
            pnl = float("nan")

        trades.append({
            "date":       op["Placing Time"],
            "close_date": match.iloc[0]["Closing Time"],
            "symbol":     sym,
            "asset_class": op["asset_class"],
            "direction":  side,
            "entry":      ep,
            "exit":       xp,
            "qty":        qty,
            "pnl":        pnl,
            "source":     "paper",
        })

    return pd.DataFrame(trades).sort_values("date").reset_index(drop=True)


# ── Risk metrics ──────────────────────────────────────────────────────────────

def compute_metrics(trades: pd.DataFrame,
                    starting_capital: float = 0.0) -> dict:
    """
    Compute NAV curve and key risk / performance metrics.

    Parameters
    ----------
    trades : DataFrame with at least 'date' and 'pnl' columns
    starting_capital : baseline to add to cumulative P&L for NAV

    Returns
    -------
    dict with keys:
        nav_series      – DataFrame(date, cum_pnl, nav, drawdown, drawdown_pct)
        current_nav     – float
        total_pnl       – float
        max_drawdown    – float (negative)
        max_drawdown_pct– float (negative %)
        sharpe          – float (annualised)
        sortino         – float (annualised)
        win_rate        – float [0,1]
        profit_factor   – float
        total_trades    – int
        avg_win         – float
        avg_loss        – float
        expectancy      – float
    """
    df = trades.dropna(subset=["pnl"]).sort_values("date").copy()
    pnl_arr = df["pnl"].values

    cum_pnl = np.cumsum(pnl_arr)
    nav_arr = starting_capital + cum_pnl

    # Drawdown (absolute and %)
    peak       = np.maximum.accumulate(nav_arr)
    dd_abs     = nav_arr - peak
    peak_safe  = np.where(peak > 0, peak, 1.0)
    dd_pct     = dd_abs / peak_safe * 100

    nav_series = pd.DataFrame({
        "date":          df["date"].values,
        "cum_pnl":       cum_pnl,
        "nav":           nav_arr,
        "drawdown":      dd_abs,
        "drawdown_pct":  dd_pct,
    })

    # Sharpe & Sortino (annualised, daily granularity)
    daily = df.groupby(df["date"].dt.date)["pnl"].sum()
    std   = daily.std()
    mean  = daily.mean()
    sharpe  = (mean / std  * np.sqrt(252)) if std  > 0 else 0.0
    neg     = daily[daily < 0]
    down_std = neg.std() if len(neg) > 1 else float("nan")
    sortino = (mean / down_std * np.sqrt(252)) if (pd.notna(down_std) and down_std > 0) else float("nan")

    wins   = pnl_arr[pnl_arr > 0]
    losses = pnl_arr[pnl_arr < 0]
    win_rate       = len(wins) / len(pnl_arr)   if len(pnl_arr)  else 0.0
    profit_factor  = wins.sum() / abs(losses.sum()) if losses.sum() != 0 else float("inf")

    return {
        "nav_series":       nav_series,
        "current_nav":      float(nav_arr[-1]) if len(nav_arr) else starting_capital,
        "total_pnl":        float(cum_pnl[-1]) if len(cum_pnl) else 0.0,
        "max_drawdown":     float(dd_abs.min()),
        "max_drawdown_pct": float(dd_pct.min()),
        "sharpe":           float(sharpe),
        "sortino":          float(sortino),
        "win_rate":         float(win_rate),
        "profit_factor":    float(profit_factor),
        "total_trades":     len(pnl_arr),
        "avg_win":          float(wins.mean())   if len(wins)   else 0.0,
        "avg_loss":         float(losses.mean()) if len(losses) else 0.0,
        "expectancy":       float(pnl_arr.mean()) if len(pnl_arr) else 0.0,
    }
