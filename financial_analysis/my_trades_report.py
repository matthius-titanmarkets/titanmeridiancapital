"""
Personalised trade analysis report.
Reads all trades from Titan Terminal.numbers, analyses P&L,
and fetches live market data for each instrument traded.

Usage:
    python3 my_trades_report.py
"""
import base64
import io
import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import yfinance as yf
from numbers_parser import Document

# ─── Config ───────────────────────────────────────────────────────────────────

NUMBERS_PATH = "/Users/mattdoug/Desktop/TMLLC/Analysis report/Titan Terminal.numbers"
OUTPUT_PATH  = "/Users/mattdoug/Downloads/CODE/financial_analysis/my_trades_report.html"

# Map instrument names → yfinance tickers
TICKER_MAP = {
    "SPX500": "^GSPC",
    "SPY":    "SPY",
    "XAUUSD": "GC=F",
    "EURUSD": "EURUSD=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "AUDJPY": "AUDJPY=X",
    "GBPUSD": "GBPUSD=X",
}

# ─── Load trades ──────────────────────────────────────────────────────────────

def load_trades(path: str) -> pd.DataFrame:
    doc   = Document(path)
    table = doc.sheets["TRADES"].tables[0]
    headers = [table.cell(0, c).value for c in range(table.num_cols)]

    rows = []
    for r in range(1, table.num_rows):
        if table.cell(r, 0).value is None:
            break
        rows.append({headers[c]: table.cell(r, c).value for c in range(table.num_cols)})

    df = pd.DataFrame(rows)
    df = df.rename(columns={
        "Trade ID":             "id",
        "Open Date":            "open_date",
        "Close Date":           "close_date",
        "Symbol":               "symbol",
        "Direction":            "direction",
        "Strategy":             "strategy",
        "Entry Price":          "entry_price",
        "Exit Price":           "exit_price",
        "Position Size (lots)": "lots",
        "P&L $":                "pnl",
        "Cum. Equity $":        "cum_equity",
        "Outcome":              "outcome",
    })

    df["id"]       = df["id"].astype(int)
    df["open_date"] = pd.to_datetime(df["open_date"])
    df["pnl"]      = pd.to_numeric(df["pnl"], errors="coerce")
    return df


# ─── Stats helpers ────────────────────────────────────────────────────────────

def trade_stats(df: pd.DataFrame) -> dict:
    pnl      = df["pnl"].dropna()
    wins     = pnl[pnl > 0]
    losses   = pnl[pnl < 0]
    win_rate = len(wins) / len(pnl) if len(pnl) > 0 else 0
    return {
        "Total Trades":      len(pnl),
        "Win Rate":          f"{win_rate:.1%}",
        "Total P&L":         f"${pnl.sum():,.2f}",
        "Avg Win":           f"${wins.mean():,.2f}" if len(wins) else "N/A",
        "Avg Loss":          f"${losses.mean():,.2f}" if len(losses) else "N/A",
        "Largest Win":       f"${wins.max():,.2f}" if len(wins) else "N/A",
        "Largest Loss":      f"${losses.min():,.2f}" if len(losses) else "N/A",
        "Profit Factor":     f"{wins.sum() / abs(losses.sum()):.2f}" if len(losses) and losses.sum() != 0 else "∞",
        "Expectancy":        f"${pnl.mean():,.2f}",
    }


# ─── Chart helpers ────────────────────────────────────────────────────────────

_STYLE = {
    "axes.facecolor":    "#fafafa",
    "figure.facecolor":  "white",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.3,
}

def _b64(fig: plt.Figure) -> str:
    buf = io.BytesIO()
    with plt.style.context(_STYLE):
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{b64}"

def _date_fmt(ax):
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.figure.autofmt_xdate(rotation=30, ha="right")


def chart_equity_curve(df: pd.DataFrame) -> str:
    """Cumulative P&L over time from trades with P&L data."""
    d = df.dropna(subset=["pnl"]).sort_values("open_date").copy()
    d["cum_pnl"] = d["pnl"].cumsum()

    fig, ax = plt.subplots(figsize=(12, 5))
    colors = ["#2ca02c" if v >= 0 else "#d62728" for v in d["pnl"]]

    ax.plot(d["open_date"], d["cum_pnl"], color="#1f77b4", linewidth=2, zorder=3)
    ax.fill_between(d["open_date"], d["cum_pnl"], 0,
                    where=d["cum_pnl"] >= 0, alpha=0.15, color="#2ca02c")
    ax.fill_between(d["open_date"], d["cum_pnl"], 0,
                    where=d["cum_pnl"] < 0,  alpha=0.15, color="#d62728")
    ax.scatter(d["open_date"], d["cum_pnl"], c=colors, s=40, zorder=4)
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set_title("Cumulative P&L ($)", fontweight="bold", pad=12)
    ax.set_ylabel("P&L ($)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    _date_fmt(ax)
    return _b64(fig)


def chart_pnl_by_symbol(df: pd.DataFrame) -> str:
    d   = df.dropna(subset=["pnl"])
    grp = d.groupby("symbol")["pnl"].sum().sort_values()

    fig, ax = plt.subplots(figsize=(9, max(4, len(grp) * 0.6)))
    colors = ["#2ca02c" if v >= 0 else "#d62728" for v in grp]
    bars = ax.barh(grp.index, grp.values, color=colors, edgecolor="white", height=0.6)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("Total P&L by Symbol ($)", fontweight="bold", pad=12)
    ax.set_xlabel("P&L ($)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    for bar, val in zip(bars, grp.values):
        ax.text(val + (500 if val >= 0 else -500), bar.get_y() + bar.get_height() / 2,
                f"${val:,.0f}", va="center", ha="left" if val >= 0 else "right", fontsize=9)
    return _b64(fig)


def chart_win_loss_breakdown(df: pd.DataFrame) -> str:
    d   = df.dropna(subset=["pnl"])
    grp = d.groupby("symbol").apply(
        lambda x: pd.Series({
            "Wins":   (x["pnl"] > 0).sum(),
            "Losses": (x["pnl"] < 0).sum(),
        })
    )

    fig, ax = plt.subplots(figsize=(9, max(4, len(grp) * 0.6)))
    y   = np.arange(len(grp))
    h   = 0.35
    ax.barh(y + h/2, grp["Wins"],   h, label="Wins",   color="#2ca02c", alpha=0.85)
    ax.barh(y - h/2, grp["Losses"], h, label="Losses", color="#d62728", alpha=0.85)
    ax.set_yticks(y)
    ax.set_yticklabels(grp.index)
    ax.set_title("Wins vs Losses by Symbol", fontweight="bold", pad=12)
    ax.set_xlabel("Number of Trades")
    ax.legend()
    return _b64(fig)


def chart_monthly_pnl(df: pd.DataFrame) -> str:
    d = df.dropna(subset=["pnl"]).copy()
    d["month"] = d["open_date"].dt.to_period("M")
    monthly = d.groupby("month")["pnl"].sum()

    fig, ax = plt.subplots(figsize=(12, 4))
    colors = ["#2ca02c" if v >= 0 else "#d62728" for v in monthly.values]
    ax.bar(monthly.index.astype(str), monthly.values, color=colors, edgecolor="white")
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set_title("Monthly P&L ($)", fontweight="bold", pad=12)
    ax.set_ylabel("P&L ($)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    plt.xticks(rotation=45, ha="right")
    return _b64(fig)


def chart_market_price(ticker: str, label: str, start: str, end: str) -> str | None:
    try:
        data = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
        if data.empty:
            return None
        prices = data["Close"].squeeze()
        prices.index = pd.to_datetime(prices.index).tz_localize(None)

        fig, ax = plt.subplots(figsize=(12, 3.5))
        ax.plot(prices.index, prices, linewidth=1.3, color="#1f77b4")
        ax.fill_between(prices.index, prices, prices.min(), alpha=0.08, color="#1f77b4")
        ax.set_title(f"{label} — Price History", fontweight="bold", pad=12)
        ax.set_ylabel("Price")
        _date_fmt(ax)
        return _b64(fig)
    except Exception as e:
        print(f"  Warning: could not fetch {ticker}: {e}")
        return None


# ─── HTML helpers ─────────────────────────────────────────────────────────────

_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f0f2f5; color: #222; font-size: 14px; line-height: 1.6;
}
.container { max-width: 1200px; margin: 0 auto; padding: 24px 16px; }
header {
  background: linear-gradient(135deg, #0d1b2a 0%, #1b3a5c 100%);
  color: white; padding: 36px 24px; border-radius: 10px; margin-bottom: 32px;
}
header h1 { font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; }
header p  { opacity: 0.65; margin-top: 6px; font-size: 0.9rem; }
h2 {
  font-size: 1.15rem; font-weight: 700; color: #0d1b2a;
  border-left: 4px solid #f4a300; padding-left: 10px;
  margin: 28px 0 14px;
}
h3 { font-size: 1rem; font-weight: 600; color: #444; margin: 16px 0 8px; }
.card {
  background: white; border-radius: 10px; padding: 24px;
  margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}
.card img { width: 100%; border-radius: 6px; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 16px; }
.stat-box {
  background: #f8f9fb; border-radius: 8px; padding: 14px 16px;
  border-left: 3px solid #f4a300;
}
.stat-box .label { font-size: 0.78rem; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
.stat-box .value { font-size: 1.15rem; font-weight: 700; color: #0d1b2a; margin-top: 2px; }
.stat-box .value.green { color: #2ca02c; }
.stat-box .value.red   { color: #d62728; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 700px) { .two-col { grid-template-columns: 1fr; } }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
.data-table th { background: #0d1b2a; color: white; padding: 9px 12px; text-align: left; }
.data-table td { padding: 7px 12px; border-bottom: 1px solid #eef0f3; }
.data-table tr:hover td { background: #f5f7ff; }
.win  { color: #2ca02c; font-weight: 600; }
.loss { color: #d62728; font-weight: 600; }
footer { text-align: center; color: #aaa; font-size: 0.8rem; padding: 28px 0 12px; }
"""

def stat_box(label: str, value: str, color: str = "") -> str:
    cls = f' {color}' if color else ""
    return f"""
    <div class="stat-box">
      <div class="label">{label}</div>
      <div class="value{cls}">{value}</div>
    </div>"""

def trade_table(df: pd.DataFrame) -> str:
    d = df.dropna(subset=["pnl"]).sort_values("open_date")
    rows = ""
    for _, t in d.iterrows():
        outcome_cls = "win" if (t["pnl"] or 0) >= 0 else "loss"
        outcome_lbl = "Win" if (t["pnl"] or 0) >= 0 else "Loss"
        rows += f"""<tr>
          <td>{int(t['id'])}</td>
          <td>{t['open_date'].strftime('%Y-%m-%d')}</td>
          <td>{t['symbol']}</td>
          <td>{t.get('direction', '')}</td>
          <td>{t['entry_price']:.4g}</td>
          <td>{f"{t['exit_price']:.4g}" if t['exit_price'] else '—'}</td>
          <td>${t['pnl']:,.2f}</td>
          <td class="{outcome_cls}">{outcome_lbl}</td>
        </tr>"""
    return f"""
    <table class="data-table">
      <thead><tr>
        <th>#</th><th>Date</th><th>Symbol</th><th>Direction</th>
        <th>Entry</th><th>Exit</th><th>P&amp;L</th><th>Outcome</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("Loading trades from Titan Terminal…")
    df = load_trades(NUMBERS_PATH)
    df_pnl = df.dropna(subset=["pnl"])
    print(f"  {len(df)} total trades, {len(df_pnl)} with P&L data")

    stats = trade_stats(df_pnl)

    # Date range for market data
    start = (df_pnl["open_date"].min() - timedelta(days=30)).strftime("%Y-%m-%d")
    end   = datetime.today().strftime("%Y-%m-%d")

    sections = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── KPI strip ────────────────────────────────────────────────────────────
    total_pnl = df_pnl["pnl"].sum()
    pnl_color = "green" if total_pnl >= 0 else "red"
    kpis = "".join([
        stat_box("Total P&L",    f"${total_pnl:,.2f}", pnl_color),
        stat_box("Trades",       str(stats["Total Trades"])),
        stat_box("Win Rate",     stats["Win Rate"]),
        stat_box("Profit Factor",stats["Profit Factor"]),
        stat_box("Avg Win",      stats["Avg Win"], "green"),
        stat_box("Avg Loss",     stats["Avg Loss"], "red"),
        stat_box("Largest Win",  stats["Largest Win"], "green"),
        stat_box("Expectancy",   stats["Expectancy"]),
    ])
    sections.append(f'<div class="card"><h2>Performance Overview</h2><div class="stats-grid">{kpis}</div></div>')

    # ── Equity curve ─────────────────────────────────────────────────────────
    print("Rendering equity curve…")
    sections.append(f"""
    <div class="card">
      <h2>Cumulative P&amp;L</h2>
      <img src="{chart_equity_curve(df_pnl)}" alt="Equity Curve">
    </div>""")

    # ── Monthly P&L ──────────────────────────────────────────────────────────
    print("Rendering monthly P&L…")
    sections.append(f"""
    <div class="card">
      <h2>Monthly P&amp;L</h2>
      <img src="{chart_monthly_pnl(df_pnl)}" alt="Monthly PnL">
    </div>""")

    # ── Symbol breakdowns ─────────────────────────────────────────────────────
    print("Rendering symbol breakdowns…")
    sections.append(f"""
    <div class="card">
      <h2>Performance by Instrument</h2>
      <div class="two-col">
        <img src="{chart_pnl_by_symbol(df_pnl)}" alt="P&L by Symbol">
        <img src="{chart_win_loss_breakdown(df_pnl)}" alt="Win/Loss by Symbol">
      </div>
    </div>""")

    # ── Per-symbol stats table ────────────────────────────────────────────────
    sym_rows = ""
    traded_syms = df_pnl["symbol"].unique()
    for sym in sorted(traded_syms):
        s = df_pnl[df_pnl["symbol"] == sym]
        pnl_s = s["pnl"]
        wins  = pnl_s[pnl_s > 0]
        loss  = pnl_s[pnl_s < 0]
        wr    = len(wins) / len(pnl_s)
        cls   = "win" if pnl_s.sum() >= 0 else "loss"
        sym_rows += f"""<tr>
          <td><strong>{sym}</strong></td>
          <td>{len(pnl_s)}</td>
          <td class="{cls}">${pnl_s.sum():,.2f}</td>
          <td>{wr:.0%}</td>
          <td class="win">${wins.mean():,.2f}</td>
          <td class="loss">${loss.mean():,.2f}</td>
          <td>${pnl_s.mean():,.2f}</td>
        </tr>"""
    sym_table = f"""
    <table class="data-table">
      <thead><tr>
        <th>Symbol</th><th>Trades</th><th>Total P&L</th>
        <th>Win Rate</th><th>Avg Win</th><th>Avg Loss</th><th>Expectancy</th>
      </tr></thead>
      <tbody>{sym_rows}</tbody>
    </table>"""
    sections.append(f'<div class="card"><h2>Instrument Breakdown</h2>{sym_table}</div>')

    # ── Market price charts ───────────────────────────────────────────────────
    price_cards = ""
    for sym in sorted(traded_syms):
        ticker = TICKER_MAP.get(sym)
        if not ticker:
            continue
        print(f"Fetching market data: {sym} ({ticker})…")
        img = chart_market_price(ticker, sym, start, end)
        if img:
            price_cards += f"""
            <div class="card">
              <h3>{sym}</h3>
              <img src="{img}" alt="{sym} price">
            </div>"""
    if price_cards:
        sections.append(f"<h2>Market Price History</h2>{price_cards}")

    # ── Trade log ────────────────────────────────────────────────────────────
    sections.append(f"""
    <div class="card">
      <h2>Full Trade Log</h2>
      {trade_table(df_pnl)}
    </div>""")

    # ── Assemble ─────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Titan Markets — My Trade Analysis</title>
  <style>{_CSS}</style>
</head>
<body>
  <header>
    <div class="container">
      <h1>Titan Markets — Trade Analysis</h1>
      <p>Generated {now} &nbsp;·&nbsp; Source: Titan Terminal &nbsp;·&nbsp; {len(df_pnl)} trades with P&amp;L data</p>
    </div>
  </header>
  <div class="container">
    {"".join(sections)}
    <footer>TMLLC · Titan Markets Analytics</footer>
  </div>
</body>
</html>"""

    Path(OUTPUT_PATH).write_text(html, encoding="utf-8")
    print(f"\nReport saved → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
