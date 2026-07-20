# 02 · Investment Policy Statement (IPS)

**Adopted:** ____________  **Re-ratified:** annually (January)
**Signatories:** Investment Committee (see Governance Charter)

> Template for internal adoption. Review with counsel and tax advisors before
> signing. Bracketed values are the working defaults of the office — edit
> deliberately, in committee, never mid-drawdown.

---

## 1. Purpose & objectives

This IPS governs all investable capital of the family office. Objectives, in
priority order:

1. **Capital preservation** across a full market cycle.
2. **Absolute return** of [CPI + 3–5%] annually, net, measured over rolling
   3-year windows — not calendar quarters.
3. **Liquidity** sufficient to fund [24] months of family and office
   operating needs without forced sales.

## 2. Mandates, targets & bands

| Mandate | Target | Band | Instruments |
|---|---|---|---|
| Public Markets & Trading | [35%] | [25–45%] | FX spot, gold/silver, index futures, rate futures |
| Income & Credit | [27%] | [20–35%] | T-bills/notes ladder, money funds, IG credit |
| Real & Hard Assets | [23%] | [15–30%] | Allocated metals, property |
| Strategic Reserves | [15%] | [10–25%] | Cash, bills < 6 months |

**Rebalancing:** review monthly; act when a mandate breaches its band, using
cash flows first, then trades. Document every rebalance in the journal.

## 3. Trading-book risk doctrine (binding on humans and software)

The rules below are enforced in code in the execution stack
(`trading_bot/risk_manager.py`) and may only be loosened by unanimous
committee sign-off, in writing, effective the **next** trading day:

- **Per-position risk:** ≤ [1.0%] of trading-book equity, stop distance
  defined before entry.
- **Daily loss limit:** [2.0%] of trading-book equity → flat all positions,
  no re-entry until next session.
- **Weekly drawdown brake:** [4.0%] → position sizes halve for the following
  week.
- **Equity circuit breaker:** [10%] peak-to-trough → trading halts; committee
  post-mortem required to restart.
- **Concentration:** ≤ [2] correlated majors positions simultaneously; no
  averaging into losers; no weekend gap exposure beyond [50%] of normal size
  in index futures.
- **News blackout:** no new entries [15] minutes before/after tier-1 releases
  (FOMC, NFP, CPI).

## 4. Prohibited

- Leverage beyond instrument-native margin; no portfolio-level borrowing.
- Naked short options; unhedged exotic derivatives.
- Illiquid private placements without unanimous committee approval and
  counsel review.
- Any position that cannot be marked daily from an independent source.
- Lending, guaranteeing, or pledging estate assets outside written committee
  resolution.

## 5. Benchmarks & measurement

- Trading book: absolute return vs. daily loss-limit adherence (process
  metrics outrank return metrics).
- Income: rolling bill/note ladder yield vs. 3-month T-bill.
- Whole estate: net total return vs. [CPI + 4%], 3-year rolling.
- **Every reported figure must reconcile to the trade log and custodian
  statements.** Unreconcilable figures are not reported.

## 6. Review & amendment

- Monthly: allocation vs. bands (ops runbook §3).
- Quarterly: mandate scoring in the family letter.
- Annually: full re-ratification, signatures, and a written record of every
  amendment with rationale.
- Amendments require [unanimous] committee approval with [7] days' notice.
  No amendments during an active circuit-breaker halt.
