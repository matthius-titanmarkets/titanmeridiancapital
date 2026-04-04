import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

from data_pipeline import (
    load_propfirm_trades,
    load_paper_orders,
    compute_paper_trade_pnl,
    compute_metrics,
    load_monthly_summary,
)

st.set_page_config(
    page_title="Titan Markets LLC — Trading Dashboard",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Data loading ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_all():
    pf_trades  = load_propfirm_trades()
    monthly    = load_monthly_summary()
    paper_orders = load_paper_orders()
    paper_pnl  = compute_paper_trade_pnl()
    return pf_trades, monthly, paper_orders, paper_pnl

pf_trades, monthly_summary, paper_orders, paper_pnl = load_all()


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("Titan Markets LLC")
    st.caption("Risk & Portfolio Dashboard")

    st.divider()
    starting_capital = st.number_input(
        "Starting Capital (USD)",
        min_value=0,
        value=100_000,
        step=10_000,
        format="%d",
    )

    st.divider()
    st.markdown("**Data Sources**")
    st.success(f"PropFirm: {len(pf_trades)} trades loaded")
    st.info(f"Paper Trading: {len(paper_orders)} orders loaded")
    date_min = pf_trades["date"].min().strftime("%Y-%m-%d")
    date_max = pf_trades["date"].max().strftime("%Y-%m-%d")
    st.caption(f"PropFirm period: {date_min} → {date_max}")

    st.divider()
    symbol_filter = st.multiselect(
        "Filter by Symbol",
        sorted(pf_trades["symbol"].unique()),
    )
    asset_filter = st.multiselect(
        "Filter by Asset Class",
        sorted(pf_trades["asset_class"].unique()),
    )

    st.caption(f"Last refreshed: {datetime.now().strftime('%H:%M:%S')}")


# ── Apply filters ──────────────────────────────────────────────────────────────

filtered = pf_trades.copy()
if symbol_filter:
    filtered = filtered[filtered["symbol"].isin(symbol_filter)]
if asset_filter:
    filtered = filtered[filtered["asset_class"].isin(asset_filter)]

metrics = compute_metrics(filtered, starting_capital=starting_capital)
nav_df  = metrics["nav_series"]


# ── Helpers ────────────────────────────────────────────────────────────────────

def fmt_usd(v: float) -> str:
    return f"${v:,.0f}"

def fmt_pct(v: float) -> str:
    return f"{v:.1f}%"

DARK = "plotly_dark"


# ── Header ─────────────────────────────────────────────────────────────────────

st.title("Titan Markets LLC — Trading & Risk Dashboard")
st.caption(
    f"Live feed: PropFirm_Portfolio.numbers + Paper Trading History  "
    f"·  {len(filtered)} trades  ·  {filtered['symbol'].nunique()} instruments"
)

# ── KPI Row ────────────────────────────────────────────────────────────────────

k1, k2, k3, k4, k5, k6 = st.columns(6)

k1.metric(
    "Total P&L",
    fmt_usd(metrics["total_pnl"]),
    delta=fmt_usd(filtered.iloc[-5:]["pnl"].sum()) if len(filtered) >= 5 else None,
    delta_color="normal",
)
k2.metric(
    "Current NAV",
    fmt_usd(metrics["current_nav"]),
)
k3.metric(
    "Win Rate",
    fmt_pct(metrics["win_rate"] * 100),
)
k4.metric(
    "Sharpe Ratio",
    f"{metrics['sharpe']:.2f}",
)
k5.metric(
    "Max Drawdown",
    fmt_usd(metrics["max_drawdown"]),
    delta=fmt_pct(metrics["max_drawdown_pct"]),
    delta_color="inverse",
)
k6.metric(
    "Profit Factor",
    f"{metrics['profit_factor']:.2f}" if not np.isinf(metrics["profit_factor"]) else "∞",
)

st.divider()


# ── Tabs ───────────────────────────────────────────────────────────────────────

tab_perf, tab_risk, tab_log, tab_paper = st.tabs([
    "📈 Performance",
    "🛡️ Risk Center",
    "📋 Trade Log",
    "🧪 Paper Trading",
])


# ── Tab 1: Performance ─────────────────────────────────────────────────────────

with tab_perf:
    col_eq, col_monthly = st.columns([3, 2])

    with col_eq:
        st.subheader("Equity / NAV Curve")
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(
            x=nav_df["date"], y=nav_df["nav"],
            fill="tozeroy", line=dict(color="#66d9ff", width=2),
            name="NAV",
        ))
        fig_eq.update_layout(
            template=DARK, height=350,
            yaxis_tickformat="$,.0f",
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False,
        )
        st.plotly_chart(fig_eq, use_container_width=True)

    with col_monthly:
        st.subheader("Monthly P&L")
        if not monthly_summary.empty:
            mdf = monthly_summary[monthly_summary["total_profit"].notna()].copy()
            mdf["month_label"] = mdf["month"].dt.strftime("%b %Y")
            mdf["color"] = mdf["total_profit"].apply(
                lambda v: "#2ca02c" if v >= 0 else "#d62728"
            )
            fig_m = go.Figure(go.Bar(
                x=mdf["month_label"],
                y=mdf["total_profit"],
                marker_color=mdf["color"].tolist(),
                text=mdf["total_profit"].apply(lambda v: f"${v:,.0f}"),
                textposition="outside",
            ))
            fig_m.update_layout(
                template=DARK, height=350,
                yaxis_tickformat="$,.0f",
                margin=dict(l=0, r=0, t=30, b=0),
                showlegend=False,
            )
            st.plotly_chart(fig_m, use_container_width=True)

    col_sym, col_cls = st.columns(2)

    with col_sym:
        st.subheader("P&L by Symbol")
        sym_pnl = (
            filtered.groupby("symbol")["pnl"]
            .sum()
            .sort_values()
            .reset_index()
        )
        sym_pnl["color"] = sym_pnl["pnl"].apply(
            lambda v: "#2ca02c" if v >= 0 else "#d62728"
        )
        fig_sym = go.Figure(go.Bar(
            x=sym_pnl["pnl"],
            y=sym_pnl["symbol"],
            orientation="h",
            marker_color=sym_pnl["color"].tolist(),
            text=sym_pnl["pnl"].apply(lambda v: f"${v:,.0f}"),
            textposition="auto",
        ))
        fig_sym.update_layout(
            template=DARK, height=320,
            xaxis_tickformat="$,.0f",
            margin=dict(l=0, r=0, t=20, b=0),
        )
        st.plotly_chart(fig_sym, use_container_width=True)

    with col_cls:
        st.subheader("P&L by Asset Class")
        cls_pnl = filtered.groupby("asset_class")["pnl"].sum().reset_index()
        fig_pie = px.pie(
            cls_pnl,
            values="pnl",
            names="asset_class",
            template=DARK,
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.45,
        )
        fig_pie.update_traces(textinfo="label+percent+value",
                              texttemplate="%{label}<br>%{percent}<br>$%{value:,.0f}")
        fig_pie.update_layout(height=320, showlegend=False,
                              margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    # Symbol stats table
    st.subheader("Instrument Breakdown")
    sym_stats = []
    for sym, g in filtered.groupby("symbol"):
        p = g["pnl"]
        wins   = p[p > 0]
        losses = p[p < 0]
        sym_stats.append({
            "Symbol":        sym,
            "Asset Class":   g["asset_class"].iloc[0],
            "Trades":        len(p),
            "Total P&L":     p.sum(),
            "Win Rate":      f"{len(wins)/len(p):.0%}",
            "Avg Win":       wins.mean() if len(wins) else 0,
            "Avg Loss":      losses.mean() if len(losses) else 0,
            "Expectancy":    p.mean(),
        })
    sym_df = (
        pd.DataFrame(sym_stats)
        .sort_values("Total P&L", ascending=False)
    )
    st.dataframe(
        sym_df.style.format({
            "Total P&L": "${:,.2f}",
            "Avg Win":   "${:,.2f}",
            "Avg Loss":  "${:,.2f}",
            "Expectancy":"${:,.2f}",
        }),
        use_container_width=True,
        height=280,
    )


# ── Tab 2: Risk Center ─────────────────────────────────────────────────────────

with tab_risk:
    col_dd, col_metrics = st.columns([2, 1])

    with col_dd:
        st.subheader("Drawdown Curve")
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=nav_df["date"],
            y=nav_df["drawdown"],
            fill="tozeroy",
            line=dict(color="#d62728", width=1.5),
            name="Drawdown ($)",
        ))
        fig_dd.update_layout(
            template=DARK, height=280,
            yaxis_tickformat="$,.0f",
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False,
        )
        st.plotly_chart(fig_dd, use_container_width=True)

        # Drawdown % chart
        fig_ddp = go.Figure()
        fig_ddp.add_trace(go.Scatter(
            x=nav_df["date"],
            y=nav_df["drawdown_pct"],
            fill="tozeroy",
            line=dict(color="#ff7f0e", width=1.5),
            name="Drawdown (%)",
        ))
        fig_ddp.update_layout(
            template=DARK, height=220,
            yaxis_ticksuffix="%",
            margin=dict(l=0, r=0, t=10, b=0),
            showlegend=False,
        )
        st.plotly_chart(fig_ddp, use_container_width=True)

    with col_metrics:
        st.subheader("Risk Metrics")
        risk_items = [
            ("Total P&L",      fmt_usd(metrics["total_pnl"])),
            ("NAV",            fmt_usd(metrics["current_nav"])),
            ("Max Drawdown",   fmt_usd(metrics["max_drawdown"])),
            ("Max DD %",       fmt_pct(metrics["max_drawdown_pct"])),
            ("Sharpe Ratio",   f"{metrics['sharpe']:.2f}"),
            ("Sortino Ratio",  f"{metrics['sortino']:.2f}" if not np.isnan(metrics["sortino"]) else "N/A"),
            ("Win Rate",       fmt_pct(metrics["win_rate"] * 100)),
            ("Profit Factor",  f"{metrics['profit_factor']:.2f}" if not np.isinf(metrics["profit_factor"]) else "∞"),
            ("Expectancy",     fmt_usd(metrics["expectancy"])),
            ("Avg Win",        fmt_usd(metrics["avg_win"])),
            ("Avg Loss",       fmt_usd(metrics["avg_loss"])),
            ("Total Trades",   str(metrics["total_trades"])),
        ]
        risk_df = pd.DataFrame(risk_items, columns=["Metric", "Value"])
        st.dataframe(risk_df, use_container_width=True, hide_index=True, height=480)

    # Monthly risk summary
    st.subheader("Monthly Risk Summary")
    if not monthly_summary.empty:
        mdf = monthly_summary.copy()
        mdf["month_label"] = mdf["month"].dt.strftime("%b %Y")
        display_cols = {
            "month_label": "Month",
            "total_trades": "Trades",
            "winning_trades": "Wins",
            "losing_trades": "Losses",
            "win_rate_pct": "Win Rate %",
            "total_profit": "Total P&L",
            "max_profit": "Largest Win",
            "max_loss": "Largest Loss",
        }
        mdf_display = mdf[list(display_cols.keys())].rename(columns=display_cols)
        st.dataframe(
            mdf_display.style.format({
                "Total P&L":   "${:,.2f}",
                "Largest Win": "${:,.2f}",
                "Largest Loss":"${:,.2f}",
                "Win Rate %":  "{:.1f}%",
            }),
            use_container_width=True,
            hide_index=True,
        )

    # Asset class exposure heatmap-style bar
    st.subheader("Exposure by Asset Class (Trade Count)")
    ac_count = filtered.groupby("asset_class")["pnl"].agg(
        count="count", total="sum"
    ).reset_index()
    fig_ac = px.bar(
        ac_count,
        x="asset_class", y="count",
        color="total",
        color_continuous_scale="RdYlGn",
        text="count",
        template=DARK,
        labels={"asset_class": "Asset Class", "count": "Trade Count", "total": "P&L ($)"},
    )
    fig_ac.update_layout(height=260, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig_ac, use_container_width=True)


# ── Tab 3: Trade Log ───────────────────────────────────────────────────────────

with tab_log:
    st.subheader("PropFirm Trade Log")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        dir_filter = st.multiselect("Direction", ["BUY", "SELL"],
                                    default=["BUY", "SELL"])
    with col_f2:
        outcome_filter = st.radio("Outcome", ["All", "Winners", "Losers"],
                                  horizontal=True)

    log_df = filtered.copy()
    if dir_filter:
        log_df = log_df[log_df["direction"].str.upper().isin(dir_filter)]
    if outcome_filter == "Winners":
        log_df = log_df[log_df["pnl"] > 0]
    elif outcome_filter == "Losers":
        log_df = log_df[log_df["pnl"] < 0]

    display_log = log_df[["id", "date", "symbol", "asset_class",
                           "direction", "entry", "exit", "lots", "pnl"]].copy()
    display_log["date"] = display_log["date"].dt.strftime("%Y-%m-%d")
    display_log = display_log.rename(columns={
        "id": "#", "asset_class": "Class",
        "direction": "Dir", "entry": "Entry",
        "exit": "Exit", "lots": "Lots", "pnl": "P&L ($)",
    })

    st.dataframe(
        display_log.style.format({"P&L ($)": "${:,.2f}", "Entry": "{:.5g}", "Exit": "{:.5g}"}),
        use_container_width=True,
        height=540,
        hide_index=True,
    )
    st.caption(f"Showing {len(display_log)} of {len(filtered)} trades")


# ── Tab 4: Paper Trading ───────────────────────────────────────────────────────

with tab_paper:
    st.subheader("Paper Trading Activity — TradingView")
    st.info(
        "Paper trading history Oct 2024 – May 2025. "
        "Positions were sized at paper-account scale (500:1 leverage); "
        "P&L figures reflect notional movement, not real capital at risk."
    )

    col_act, col_sym_paper = st.columns([2, 1])

    with col_act:
        st.markdown("**Order Activity Timeline**")
        fig_timeline = go.Figure()
        for side, color in [("Buy", "#2ca02c"), ("Sell", "#d62728")]:
            sub = paper_orders[paper_orders["Side"] == side]
            fig_timeline.add_trace(go.Scatter(
                x=sub["Placing Time"],
                y=sub["clean_symbol"],
                mode="markers",
                name=side,
                marker=dict(color=color, size=9, symbol="circle"),
            ))
        fig_timeline.update_layout(
            template=DARK, height=340,
            xaxis_title="Date",
            yaxis_title="Symbol",
            margin=dict(l=0, r=0, t=20, b=0),
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

    with col_sym_paper:
        st.markdown("**Orders by Symbol**")
        sym_counts = paper_orders["clean_symbol"].value_counts().reset_index()
        sym_counts.columns = ["Symbol", "Orders"]
        fig_sc = px.bar(
            sym_counts, x="Orders", y="Symbol", orientation="h",
            template=DARK, color="Orders",
            color_continuous_scale="Blues",
        )
        fig_sc.update_layout(height=340, showlegend=False,
                             margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig_sc, use_container_width=True)

    # Paper round-trip P&L (USD-quoted only)
    if not paper_pnl.empty:
        pnl_known = paper_pnl.dropna(subset=["pnl"])
        if not pnl_known.empty:
            st.subheader("Matched Round-Trip P&L (USD-quoted instruments)")
            st.caption(
                f"{len(pnl_known)} complete round-trips matched "
                f"(EURUSD, GOLD, XAUUSD, AUDUSD)"
            )
            pnl_known_display = pnl_known[
                ["date", "close_date", "symbol", "direction", "entry", "exit", "qty", "pnl"]
            ].copy()
            pnl_known_display["date"] = pnl_known_display["date"].dt.strftime("%Y-%m-%d %H:%M")
            pnl_known_display["close_date"] = pnl_known_display["close_date"].dt.strftime("%Y-%m-%d %H:%M")
            pnl_known_display = pnl_known_display.rename(columns={
                "date": "Open", "close_date": "Close",
                "direction": "Side", "entry": "Entry", "exit": "Exit",
                "qty": "Qty", "pnl": "P&L ($)",
            })
            st.dataframe(
                pnl_known_display.style.format({
                    "P&L ($)": "${:,.2f}",
                    "Entry":   "{:.6g}",
                    "Exit":    "{:.6g}",
                    "Qty":     "{:,.0f}",
                }),
                use_container_width=True,
                height=340,
                hide_index=True,
            )

    # Paper trading asset class breakdown
    st.subheader("Paper Trading — Asset Class Activity")
    ac_paper = paper_orders.groupby(["asset_class", "Side"]).size().reset_index(name="count")
    fig_ap = px.bar(
        ac_paper, x="asset_class", y="count", color="Side",
        template=DARK, barmode="group",
        color_discrete_map={"Buy": "#2ca02c", "Sell": "#d62728"},
        labels={"asset_class": "Asset Class", "count": "Order Count", "Side": "Side"},
    )
    fig_ap.update_layout(height=280, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig_ap, use_container_width=True)

    # Full paper order log
    with st.expander("Full Paper Order Log"):
        paper_display = paper_orders[[
            "Symbol", "Side", "Type", "Qty",
            "Fill Price", "Placing Time", "Closing Time", "Status",
        ]].copy()
        paper_display["Placing Time"] = paper_display["Placing Time"].dt.strftime("%Y-%m-%d %H:%M")
        paper_display["Closing Time"] = paper_display["Closing Time"].dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(paper_display, use_container_width=True, height=400, hide_index=True)
