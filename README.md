# Titan Meridian Capital

**Private family investment office — the complete estate in one repository.**
*Stewardship. Discipline. Permanence.*

Everything the office operates lives here: the public fund site, the trading
terminal, the client portal, the trading division site, the execution stack,
the research tooling, and the governance pack that binds it together.

## The estate

| Surface | Path | What it is |
|---|---|---|
| **Fund website** | [`/`](index.html) | Public face of the office — mandates, the fund, governance cadence, access |
| **Meridian Terminal** | [`/platform/`](platform/index.html) | Trading platform surface: watchlist tape, candlestick charts, paper book with risk limits and desk halt, session clocks, live news wire |
| **Client portal** | [`/clients/`](clients/index.html) | Family dashboard: NAV, performance, allocation, capital account, statements, activity — demo gate, sample data (preview code `MERIDIAN`) |
| **Titan Markets LLC** | [`/titan-markets/`](titan-markets/index.html) | Trading division site (Chicago desk) + promo reel |
| **Family Office Blueprint** | [`/family-office/`](family-office/index.html) | The operating manual, presented — links to the documents of record |
| **Governance pack** | [`/docs/family_office/`](docs/family_office/README.md) | IPS, governance charter, ops runbook, compliance calendar, onboarding, technology estate, security & continuity |
| **Trading bot** | [`/trading_bot/`](trading_bot/README.md) | TradingView alerts → risk-gated webhook → Interactive Brokers execution |
| **Research & analytics** | [`/financial_analysis/`](financial_analysis/) | Backtests, indicators, portfolio math, trade reports |
| **Ops dashboard** | [`dashboard.py`](dashboard.py) | Streamlit risk & portfolio dashboard (local) |

## News wire

`scripts/fetch_news.py` (stdlib-only) pulls public RSS wires into
`platform/data/news.json`. The [news workflow](.github/workflows/news.yml)
runs it every 30 minutes on weekdays and commits when headlines change; the
terminal reads the file at load and falls back to built-in desk briefing
items if it is missing or stale. Run it manually anytime:

```bash
python3 scripts/fetch_news.py
```

## Deploy

Pushes to `main` deploy the whole repo to GitHub Pages via
[`pages.yml`](.github/workflows/pages.yml). News refresh commits re-trigger
the deploy, so the published terminal stays current.

Local preview:

```bash
python3 -m http.server 4173   # then open http://localhost:4173
```

## Checks

```bash
npm test   # structural smoke checks across every surface
```

## Honesty posture (deliberate)

- Terminal market data is **simulated for display** and labeled as such; the
  paper book stays in the browser and transmits nothing.
- Portal figures are **sample data** behind a demo gate that is documented as
  demonstration-only; production access requires a real backend
  (path documented in [docs/family_office/07_technology_estate.md](docs/family_office/07_technology_estate.md)).
- Public pages carry private-office disclaimers: no products or services
  offered to the public, nothing is an offer of securities.
- No credentials, account data, or statements are ever committed here.

© 2026 Titan Meridian Capital · Titan Markets LLC
