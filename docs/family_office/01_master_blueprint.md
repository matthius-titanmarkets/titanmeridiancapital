# 01 · Master Blueprint

**Titan Meridian Capital — Private Family Investment Office**
*Stewardship. Discipline. Permanence.*

---

## 1. What the office is

Titan Meridian Capital (TMC) is a **single-family investment office**. It
exists to steward the family's capital across market cycles and generations.
It does **not** manage outside money, market products, or offer services to
the public — a structural fact that keeps the office outside most
public-offering regimes (confirm scope with counsel; see standing disclaimer
in the README).

The office concentrates on four functions:

1. **Invest** — run the mandates under a written Investment Policy Statement.
2. **Trade** — operate the professional desk (Titan Markets LLC) with
   automated, risk-gated execution.
3. **Report** — one standard of record: every figure traceable to the trade
   log; statements on a fixed calendar.
4. **Govern** — an investment committee, a constitution (IPS + Charter), and
   an annual review that actually happens.

## 2. Organizational map

```
                    ┌─────────────────────────────┐
                    │      The Family / Trust     │
                    │   (beneficial ownership)    │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │   TITAN MERIDIAN CAPITAL    │
                    │  Family Investment Office   │
                    │  · Investment Committee     │
                    │  · IPS / Governance Charter │
                    │  · Reporting & Portal       │
                    └──────┬───────────────┬──────┘
                           │               │
            ┌──────────────▼─────┐   ┌─────▼──────────────────┐
            │  TITAN MARKETS LLC │   │  Custody & Banking     │
            │  Trading Division  │   │  · Brokerage accounts  │
            │  · Desk & terminal │   │  · Bank accounts       │
            │  · Bot execution   │   │  · Metals/real assets  │
            │  · Risk rules      │   │    (segregated titles) │
            └────────────────────┘   └────────────────────────┘
```

Entity choices (LLC vs. LP, trust situs, tax elections) are jurisdiction-
specific — settle them with counsel and record the final map here.

## 3. The four mandates

| Mandate | Purpose | Policy anchor | Review |
|---|---|---|---|
| Public Markets & Trading | Absolute-return trading in FX, metals, index futures, rates | ≤ 1% equity risk per position; daily loss limit; drawdown brake | Daily |
| Income & Credit | Treasury ladder & yield to fund operations, dampen volatility | Duration & credit-quality floors | Monthly |
| Real & Hard Assets | Metals, property, long-duration ballast | Held in segregated title; decades horizon | Quarterly |
| Strategic Reserves | Dry powder for dislocation | Written deployment triggers; always funded | Standing |

Target weights, bands, and rebalancing rules live in the IPS (doc 02).

## 4. Operating surfaces (all in this repository)

| Surface | Path | Role |
|---|---|---|
| Fund website | `/` | Public face; discreet, informational |
| Meridian Terminal | `/platform/` | Desk surface — watchlist, charts, paper book, risk limits, news wire |
| Client portal | `/clients/` | Family-facing statements, performance, documents (demo gate) |
| Titan Markets site | `/titan-markets/` | Trading division public site |
| Trading bot | `/trading_bot/` | TradingView alerts → webhook → Interactive Brokers, risk-gated |
| Analytics | `/financial_analysis/`, `dashboard.py` | Backtests, trade reports, Streamlit ops dashboard |
| News pipeline | `scripts/fetch_news.py` + Actions | Public RSS wires → `platform/data/news.json` every 30 min |

## 5. Build sequence (state of completion)

- [x] Trading stack: signals → webhook → broker with pre-trade risk checks
- [x] Public estate: fund site, division site, terminal, portal demo
- [x] News wire automation
- [x] Governance pack drafted (this directory)
- [ ] Ratify IPS & Charter at first formal committee meeting
- [ ] Production portal authentication (see 07 §4 — requires a backend)
- [ ] External annual review engagement (accountant/auditor selection)
- [ ] Continuity drill #1 (see 08 §5)

## 6. Principles (the short version)

1. **Preservation before performance.**
2. **Process over prediction** — positions are outputs of written rules.
3. **One standard of record** — if it isn't logged, it didn't happen.
4. **Quiet by design** — the office compounds in private.
