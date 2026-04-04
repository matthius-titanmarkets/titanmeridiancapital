"""
Financial Markets Analysis Suite — entry point.

Usage
-----
    cd financial_analysis
    pip install -r requirements.txt
    python main.py

Edit config.py to change symbols, date range, portfolio weights,
strategy parameters, and the output report path.
"""
import sys

from config import (
    SYMBOLS, START_DATE, END_DATE,
    PORTFOLIO, BENCHMARK, RISK_FREE_RATE,
    INDICATORS, BACKTEST, REPORT_PATH,
)
from data_loader import fetch_prices, fetch_ohlcv
from portfolio import portfolio_stats, asset_stats_table
from backtest import Backtest
from report import generate_report


def main() -> None:
    # ── 1. Fetch closing prices ───────────────────────────────────────────────
    all_symbols = list(dict.fromkeys(SYMBOLS + [BENCHMARK]))   # deduplicated, order-preserved
    print(f"Fetching prices for: {all_symbols}")
    prices = fetch_prices(all_symbols, START_DATE, END_DATE)
    prices = prices.reindex(columns=all_symbols).dropna(how="all")
    print(f"  {len(prices)} trading days  ({prices.index[0].date()} → {prices.index[-1].date()})")

    # ── 2. Asset statistics ───────────────────────────────────────────────────
    print("\nAsset summary statistics:")
    asts = asset_stats_table(prices, RISK_FREE_RATE)
    print(asts.to_string())

    # ── 3. Portfolio statistics ───────────────────────────────────────────────
    port_syms   = list(PORTFOLIO.keys())
    port_prices = prices[port_syms].dropna()
    port_stats  = portfolio_stats(port_prices, PORTFOLIO, RISK_FREE_RATE)
    print("\nPortfolio statistics:")
    for k, v in port_stats.items():
        print(f"  {k:<28} {v}")

    # ── 4. OHLCV data for technical charts ────────────────────────────────────
    ohlcv_map: dict = {}
    bt_sym = BACKTEST["symbol"]
    fetch_targets = list(dict.fromkeys(SYMBOLS + [bt_sym]))

    for sym in fetch_targets:
        print(f"Fetching OHLCV for {sym}…")
        try:
            ohlcv_map[sym] = fetch_ohlcv(sym, START_DATE, END_DATE)
        except Exception as exc:
            print(f"  Warning: could not fetch OHLCV for {sym}: {exc}")

    # ── 5. Backtest ───────────────────────────────────────────────────────────
    strategy = BACKTEST["strategy"]
    print(f"\nRunning backtest on {bt_sym} ({strategy})…")

    if bt_sym not in ohlcv_map:
        print(f"  Error: no OHLCV data for {bt_sym}. Check config.")
        sys.exit(1)

    bt = Backtest(ohlcv_map[bt_sym], initial_capital=BACKTEST["initial_capital"])

    if strategy == "sma_crossover":
        bt.run_sma_crossover(BACKTEST["sma_short"], BACKTEST["sma_long"])
    elif strategy == "rsi_mean_reversion":
        bt.run_rsi_mean_reversion(14, BACKTEST["rsi_oversold"], BACKTEST["rsi_overbought"])
    else:
        print(f"  Unknown strategy '{strategy}', defaulting to SMA crossover.")
        bt.run_sma_crossover(BACKTEST["sma_short"], BACKTEST["sma_long"])

    print("Backtest results:")
    for k, v in bt.results.items():
        print(f"  {k:<28} {v}")

    # ── 6. Generate HTML report ───────────────────────────────────────────────
    print(f"\nGenerating report → {REPORT_PATH}")
    generate_report(
        prices             = prices,
        benchmark          = BENCHMARK,
        portfolio_weights  = PORTFOLIO,
        ohlcv_map          = ohlcv_map,
        backtest           = bt,
        asset_stats        = asts,
        portfolio_stats_dict = port_stats,
        indicator_params   = INDICATORS,
        output_path        = REPORT_PATH,
    )

    print("Done.")


if __name__ == "__main__":
    main()
