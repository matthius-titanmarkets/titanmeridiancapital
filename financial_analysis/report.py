"""
HTML report generator.

Charts are rendered by matplotlib and embedded as base64 PNGs so the
output is a single self-contained HTML file — no external dependencies.
"""
import base64
import io
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")           # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import pandas as pd

from analysis import daily_returns, cumulative_returns, drawdown_series
from backtest import Backtest
from indicators import sma, rsi, macd, bollinger_bands


# ─── Chart helpers ────────────────────────────────────────────────────────────

_STYLE = {
    "axes.facecolor":   "#fafafa",
    "figure.facecolor": "white",
    "axes.spines.top":  False,
    "axes.spines.right": False,
    "axes.grid":        True,
    "grid.alpha":       0.3,
    "grid.linewidth":   0.6,
}

def _fig_to_b64(fig: plt.Figure) -> str:
    """Save a matplotlib figure to a base64-encoded PNG data URI."""
    buf = io.BytesIO()
    with plt.style.context(_STYLE):
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{b64}"


def _date_fmt(ax: plt.Axes) -> None:
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.figure.autofmt_xdate(rotation=30, ha="right")


# ─── Individual chart functions ───────────────────────────────────────────────

def chart_cumulative_returns(prices: pd.DataFrame, benchmark_col: str | None = None) -> str:
    rets = daily_returns(prices)
    cum  = cumulative_returns(rets) * 100   # in percent

    fig, ax = plt.subplots(figsize=(12, 5))
    for col in cum.columns:
        lw = 2.5 if col == benchmark_col else 1.5
        ls = "--" if col == benchmark_col else "-"
        ax.plot(cum.index, cum[col], label=col, linewidth=lw, linestyle=ls)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_title("Cumulative Returns (%)", fontweight="bold", pad=12)
    ax.set_ylabel("Return (%)")
    ax.legend(fontsize=9)
    _date_fmt(ax)
    return _fig_to_b64(fig)


def chart_drawdown(prices: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(12, 4))
    for col in prices.columns:
        dd = drawdown_series(prices[col]) * 100
        ax.fill_between(dd.index, dd, 0, alpha=0.35, label=col)
    ax.set_title("Drawdown (%)", fontweight="bold", pad=12)
    ax.set_ylabel("Drawdown (%)")
    ax.legend(fontsize=9)
    _date_fmt(ax)
    return _fig_to_b64(fig)


def chart_correlation(prices: pd.DataFrame) -> str:
    corr = daily_returns(prices).corr()
    n    = len(corr)

    fig, ax = plt.subplots(figsize=(max(5, n), max(4, n - 1)))
    im = ax.imshow(corr.values, cmap="RdYlGn", vmin=-1, vmax=1)
    fig.colorbar(im, ax=ax, fraction=0.04, pad=0.04)
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(corr.columns, fontsize=9)
    for i in range(n):
        for j in range(n):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}",
                    ha="center", va="center", fontsize=9,
                    color="black" if abs(corr.iloc[i, j]) < 0.8 else "white")
    ax.set_title("Return Correlation Matrix", fontweight="bold", pad=12)
    return _fig_to_b64(fig)


def chart_technical(
    ohlcv: pd.DataFrame,
    symbol: str,
    sma_short: int,
    sma_long: int,
    bb_window: int,
    rsi_period: int,
) -> str:
    prices = ohlcv["Close"]
    bb     = bollinger_bands(prices, bb_window)
    macd_df = macd(prices)
    rsi_s  = rsi(prices, rsi_period)

    fig, axes = plt.subplots(
        3, 1, figsize=(12, 12), sharex=True,
        gridspec_kw={"height_ratios": [3, 1.5, 1.5]},
    )
    fig.suptitle(f"{symbol}  —  Technical Analysis", fontweight="bold", fontsize=14, y=1.01)

    # ── Panel 1: Price + SMAs + Bollinger Bands ──
    ax1 = axes[0]
    ax1.plot(prices.index, prices, label="Close", linewidth=1.2, color="#1f77b4")
    ax1.plot(prices.index, sma(prices, sma_short), label=f"SMA {sma_short}", linewidth=1, color="darkorange")
    ax1.plot(prices.index, sma(prices, sma_long),  label=f"SMA {sma_long}",  linewidth=1, color="purple")
    ax1.plot(bb.index, bb["upper"], "--", color="grey", linewidth=0.8)
    ax1.plot(bb.index, bb["lower"], "--", color="grey", linewidth=0.8)
    ax1.fill_between(bb.index, bb["upper"], bb["lower"], alpha=0.08, color="grey", label="BB")
    ax1.set_ylabel("Price ($)")
    ax1.legend(fontsize=8, loc="upper left")

    # ── Panel 2: MACD ──
    ax2 = axes[1]
    ax2.plot(macd_df.index, macd_df["macd"],   label="MACD",   color="#1f77b4")
    ax2.plot(macd_df.index, macd_df["signal"], label="Signal", color="darkorange")
    colors = ["#2ca02c" if v >= 0 else "#d62728" for v in macd_df["histogram"]]
    ax2.bar(macd_df.index, macd_df["histogram"], color=colors, alpha=0.5, label="Histogram", width=1.5)
    ax2.axhline(0, color="black", linewidth=0.5)
    ax2.set_ylabel("MACD")
    ax2.legend(fontsize=8, loc="upper left")

    # ── Panel 3: RSI ──
    ax3 = axes[2]
    ax3.plot(rsi_s.index, rsi_s, color="#1f77b4", linewidth=1)
    ax3.axhline(70, color="#d62728", linestyle="--", linewidth=0.8, label="Overbought (70)")
    ax3.axhline(30, color="#2ca02c", linestyle="--", linewidth=0.8, label="Oversold (30)")
    ax3.fill_between(rsi_s.index, 30, rsi_s.clip(upper=30), alpha=0.15, color="#2ca02c")
    ax3.fill_between(rsi_s.index, 70, rsi_s.clip(lower=70), alpha=0.15, color="#d62728")
    ax3.set_ylim(0, 100)
    ax3.set_ylabel(f"RSI ({rsi_period})")
    ax3.legend(fontsize=8, loc="upper left")
    _date_fmt(ax3)

    plt.tight_layout()
    return _fig_to_b64(fig)


def chart_backtest(bt: Backtest) -> str:
    fig, axes = plt.subplots(
        2, 1, figsize=(12, 8), sharex=True,
        gridspec_kw={"height_ratios": [3, 1]},
    )

    # ── Equity curves ──
    ax1 = axes[0]
    ax1.plot(bt.equity_curve.index,    bt.equity_curve,    label="Strategy",    linewidth=1.5, color="#1f77b4")
    ax1.plot(bt.bh_equity_curve.index, bt.bh_equity_curve, label="Buy & Hold", linewidth=1.5, color="darkorange", linestyle="--")
    ax1.set_title(f"Backtest  —  {bt.results['Strategy']}", fontweight="bold", pad=12)
    ax1.set_ylabel("Portfolio Value ($)")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax1.legend(fontsize=9)

    # ── Position indicator ──
    ax2 = axes[1]
    ax2.fill_between(bt.position.index, bt.position, 0, step="post",
                     alpha=0.45, color="#2ca02c", label="Long")
    ax2.set_ylabel("Position")
    ax2.set_ylim(-0.1, 1.3)
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(["Cash", "Long"])
    _date_fmt(ax2)

    plt.tight_layout()
    return _fig_to_b64(fig)


# ─── HTML helpers ─────────────────────────────────────────────────────────────

def _df_html(df: pd.DataFrame) -> str:
    return df.to_html(classes="data-table", border=0, escape=True)


def _stats_table(d: dict, caption: str = "") -> str:
    rows = "".join(
        f"<tr><td class='label'>{k}</td><td class='value'>{v}</td></tr>"
        for k, v in d.items()
    )
    cap = f"<caption>{caption}</caption>" if caption else ""
    return f"<table class='stats-table'>{cap}<tbody>{rows}</tbody></table>"


# ─── CSS ──────────────────────────────────────────────────────────────────────

_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f0f2f5; color: #222; font-size: 14px; line-height: 1.6;
}
.container { max-width: 1200px; margin: 0 auto; padding: 24px 16px; }

/* Header */
header {
  background: linear-gradient(135deg, #0d1b2a 0%, #1b3a5c 100%);
  color: white; padding: 36px 24px; border-radius: 10px; margin-bottom: 32px;
}
header h1 { font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; }
header p  { opacity: 0.65; margin-top: 6px; font-size: 0.9rem; }

/* Section headings */
h2 {
  font-size: 1.15rem; font-weight: 700; color: #0d1b2a;
  border-left: 4px solid #3a86ff; padding-left: 10px;
  margin: 28px 0 14px;
}
h3 { font-size: 1rem; font-weight: 600; color: #444; margin: 16px 0 8px; }

/* Cards */
.card {
  background: white; border-radius: 10px; padding: 24px;
  margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}
.card img { width: 100%; border-radius: 6px; }

/* Stats table (key-value pairs) */
.stats-table { border-collapse: collapse; width: 100%; }
.stats-table caption { text-align: left; font-weight: 700; padding: 4px 0 10px; color: #0d1b2a; }
.stats-table td { padding: 7px 10px; border-bottom: 1px solid #eef0f3; font-size: 0.88rem; }
.stats-table td.label { color: #666; width: 55%; }
.stats-table td.value { font-weight: 600; }

/* Data tables (multi-column) */
.data-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.data-table th { background: #0d1b2a; color: white; padding: 9px 14px; text-align: left; font-weight: 600; }
.data-table td { padding: 7px 14px; border-bottom: 1px solid #eef0f3; }
.data-table tr:hover td { background: #f0f5ff; }

/* Two-column layout helpers */
.two-col { display: grid; grid-template-columns: 1fr 2fr; gap: 24px; align-items: start; }
@media (max-width: 700px) { .two-col { grid-template-columns: 1fr; } }

footer { text-align: center; color: #aaa; font-size: 0.8rem; padding: 28px 0 12px; }
"""


# ─── Report assembly ──────────────────────────────────────────────────────────

def generate_report(
    prices: pd.DataFrame,
    benchmark: str,
    portfolio_weights: dict[str, float],
    ohlcv_map: dict[str, pd.DataFrame],
    backtest: Backtest,
    asset_stats: pd.DataFrame,
    portfolio_stats_dict: dict[str, str],
    indicator_params: dict[str, int],
    output_path: str = "report.html",
) -> None:
    """
    Build a self-contained HTML report and write it to *output_path*.
    """
    now        = datetime.now().strftime("%Y-%m-%d %H:%M")
    start_date = prices.index[0].strftime("%Y-%m-%d")
    end_date   = prices.index[-1].strftime("%Y-%m-%d")
    symbols    = list(prices.columns)

    sections: list[str] = []

    # 1 ── Cumulative returns ──────────────────────────────────────────────────
    print("  Rendering: cumulative returns chart…")
    sections.append(f"""
    <div class="card">
      <h2>Cumulative Returns</h2>
      <p style="color:#777;font-size:0.85rem;margin-bottom:10px">
        {start_date} → {end_date} &nbsp;·&nbsp; dashed line = {benchmark} benchmark
      </p>
      <img src="{chart_cumulative_returns(prices, benchmark_col=benchmark)}" alt="Cumulative Returns">
    </div>""")

    # 2 ── Drawdown ────────────────────────────────────────────────────────────
    print("  Rendering: drawdown chart…")
    sections.append(f"""
    <div class="card">
      <h2>Drawdown Analysis</h2>
      <img src="{chart_drawdown(prices)}" alt="Drawdown">
    </div>""")

    # 3 ── Asset stats table ───────────────────────────────────────────────────
    sections.append(f"""
    <div class="card">
      <h2>Asset Summary Statistics</h2>
      {_df_html(asset_stats)}
    </div>""")

    # 4 ── Portfolio: stats + correlation heatmap ──────────────────────────────
    print("  Rendering: correlation heatmap…")
    port_syms = list(portfolio_weights.keys())
    sections.append(f"""
    <div class="card">
      <h2>Portfolio Analysis</h2>
      <div class="two-col">
        {_stats_table(portfolio_stats_dict, "Weighted Portfolio")}
        <div>
          <h3>Return Correlation</h3>
          <img src="{chart_correlation(prices[port_syms])}" alt="Correlation Matrix">
        </div>
      </div>
    </div>""")

    # 5 ── Technical charts ────────────────────────────────────────────────────
    tech_html = ""
    for sym in symbols:
        if sym in ohlcv_map:
            print(f"  Rendering: technical chart for {sym}…")
            img = chart_technical(
                ohlcv_map[sym], sym,
                indicator_params["sma_short"],
                indicator_params["sma_long"],
                indicator_params["bb_window"],
                indicator_params["rsi_period"],
            )
            tech_html += f"""
            <div class="card">
              <h3>{sym}  —  Price · MACD · RSI</h3>
              <img src="{img}" alt="{sym} Technical">
            </div>"""
    sections.append(f"<h2>Technical Indicators</h2>{tech_html}")

    # 6 ── Backtest ────────────────────────────────────────────────────────────
    print("  Rendering: backtest chart…")
    bt_img    = chart_backtest(backtest)
    bt_stats  = _stats_table(backtest.results, "Backtest Results")
    trade_log = (
        backtest.trades.drop(columns=["win"], errors="ignore")
        .to_html(classes="data-table", border=0, index=False)
        if len(backtest.trades) > 0
        else "<p style='color:#888'>No completed trades in this period.</p>"
    )
    sections.append(f"""
    <div class="card">
      <h2>Backtest  —  {backtest.results['Strategy']}</h2>
      <img src="{bt_img}" alt="Backtest Equity Curve">
      <div class="two-col" style="margin-top:24px">
        {bt_stats}
        <div>
          <h3>Trade Log ({len(backtest.trades)} trades)</h3>
          {trade_log}
        </div>
      </div>
    </div>""")

    # ── Assemble HTML ─────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Market Analysis Report — {now}</title>
  <style>{_CSS}</style>
</head>
<body>
  <header>
    <div class="container">
      <h1>Market Analysis Report</h1>
      <p>Generated {now} &nbsp;·&nbsp; Symbols: {", ".join(symbols)} &nbsp;·&nbsp; Data: Yahoo Finance</p>
    </div>
  </header>
  <div class="container">
    {"".join(sections)}
    <footer>Python Financial Analysis Suite</footer>
  </div>
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")
    print(f"\nReport saved → {output_path}")
