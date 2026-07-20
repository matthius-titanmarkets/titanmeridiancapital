#!/usr/bin/env python3
"""Fetch real market quotes + candles into platform/data/quotes.json.

Standard library only. Sources are Yahoo Finance's public v8 chart endpoint
(no key; widely used for personal dashboards — keep volume tiny and cadence
modest). The Meridian Terminal reads quotes.json at load for real price
anchors and candle history; a browser-side layer (Kraken/Coinbase public
APIs) streams live ticks for FX and crypto on top of it.

Run locally or from the scheduled quotes workflow:

    python3 scripts/fetch_quotes.py

Failure posture mirrors fetch_news.py: any symbol may fail without sinking
the run; if every symbol fails the existing file is left untouched, and the
terminal keeps its previous anchors (or falls back to labeled simulation).
"""

from __future__ import annotations

import json
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT_PATH = Path(__file__).resolve().parent.parent / "platform" / "data" / "quotes.json"
UA = "Mozilla/5.0 (MeridianTerminal quotes; +github actions)"
TIMEOUT_S = 15
INTRADAY_BARS = 128   # ~2 sessions of 15m bars (32h for 24h markets)
DAILY_BARS = 132      # ~6 months of daily candles

# Terminal symbol → Yahoo candidates (first that returns data wins).
SYMBOLS = [
    ("XAUUSD", "Gold · COMEX",      ["GC=F"],      2),
    ("EURUSD", "Euro / Dollar",     ["EURUSD=X"],  4),
    ("GBPUSD", "Pound / Dollar",    ["GBPUSD=X"],  4),
    ("USDJPY", "Dollar / Yen",      ["JPY=X"],     2),
    ("US500",  "S&P 500 Index",     ["^GSPC"],     1),
    ("NAS100", "Nasdaq 100 Index",  ["^NDX"],      1),
    ("US30",   "Dow Jones 30",      ["^DJI"],      0),
    ("XAGUSD", "Silver · COMEX",    ["SI=F"],      3),
    ("WTIUSD", "WTI Crude · NYMEX", ["CL=F"],      2),
    ("BTCUSD", "Bitcoin",           ["BTC-USD"],   0),
]


def http_get(url: str) -> bytes:
    """urllib first; curl fallback for hosts whose local Python lacks certs."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            return resp.read()
    except (ssl.SSLError, urllib.error.URLError) as exc:
        is_ssl = isinstance(exc, ssl.SSLError) or isinstance(
            getattr(exc, "reason", None), ssl.SSLError
        )
        if not is_ssl:
            raise
        out = subprocess.run(
            ["curl", "-sS", "-m", str(TIMEOUT_S), "-A", UA, url],
            capture_output=True, check=True,
        )
        return out.stdout


def yahoo_chart(symbol: str, rng: str, interval: str) -> dict:
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + urllib.parse.quote(symbol)
        + f"?range={rng}&interval={interval}"
    )
    payload = json.loads(http_get(url))
    chart = payload.get("chart") or {}
    if chart.get("error"):
        raise ValueError(chart["error"].get("description", "chart error"))
    return chart["result"][0]


def rnd(v, dp):
    return None if v is None else round(float(v), dp + 1)


def pack_candles(result: dict, dp: int, keep: int) -> dict:
    """Compact OHLC arrays: epoch-second timestamps + rounded values."""
    ts = result.get("timestamp") or []
    quote = result["indicators"]["quote"][0]
    rows = []
    for i, t in enumerate(ts):
        o, h = quote["open"][i], quote["high"][i]
        l, c = quote["low"][i], quote["close"][i]
        if None in (o, h, l, c):
            continue
        rows.append((int(t), rnd(o, dp), rnd(h, dp), rnd(l, dp), rnd(c, dp)))
    rows = rows[-keep:]
    return {
        "t": [r[0] for r in rows],
        "o": [r[1] for r in rows],
        "h": [r[2] for r in rows],
        "l": [r[3] for r in rows],
        "c": [r[4] for r in rows],
    }


def fetch_symbol(sym: str, name: str, candidates: list[str], dp: int) -> dict:
    last_err: Exception | None = None
    for ysym in candidates:
        try:
            intra = yahoo_chart(ysym, "5d", "15m")
            daily = yahoo_chart(ysym, "6mo", "1d")
            meta = intra.get("meta") or {}
            last = meta.get("regularMarketPrice")
            prev = meta.get("chartPreviousClose") or meta.get("previousClose")
            if last is None:
                raise ValueError("no regularMarketPrice")
            return {
                "name": name,
                "src": ysym,
                "dp": dp,
                "last": rnd(last, dp),
                "prevClose": rnd(prev, dp) if prev is not None else None,
                "marketTime": int(meta.get("regularMarketTime") or 0),
                "intraday": pack_candles(intra, dp, INTRADAY_BARS),
                "daily": pack_candles(daily, dp, DAILY_BARS),
            }
        except Exception as exc:  # noqa: BLE001 — try next candidate
            last_err = exc
    raise RuntimeError(f"{sym}: all candidates failed ({last_err})")


def main() -> int:
    symbols: dict[str, dict] = {}
    errors: list[str] = []
    for sym, name, candidates, dp in SYMBOLS:
        try:
            symbols[sym] = fetch_symbol(sym, name, candidates, dp)
            print(f"[quotes] {sym}: {symbols[sym]['last']} "
                  f"({len(symbols[sym]['intraday']['t'])} intraday bars)")
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))
            print(f"[quotes] {sym}: FAILED ({exc})", file=sys.stderr)

    if not symbols:
        print("[quotes] every symbol failed; leaving existing quotes.json untouched",
              file=sys.stderr)
        return 0

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": "live",
        "errors": errors,
        "symbols": symbols,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, separators=(",", ":")) + "\n",
                        encoding="utf-8")
    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"[quotes] wrote {len(symbols)} symbols -> {OUT_PATH} ({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
