# 04 · Operations Runbook

The office runs on a calendar, and the calendar does not move for markets.

---

## 1. Daily (desk days, before first session traded)

- [ ] **Risk check:** confirm daily loss limit armed; bot heartbeat green
      (`trading_bot` webhook server up, broker session authenticated).
- [ ] **Mark:** yesterday's P&L written to the log; equity curve updated.
- [ ] **Limits:** open exposure within doctrine (positions, concentration).
- [ ] **Calendar:** tier-1 releases today? Blackout windows loaded.
- [ ] **Wire:** scan the news feed (terminal) for overnight surprises.

*Time budget: 15 minutes. If any check fails → no new risk until resolved.*

## 2. Weekly (Friday close or Sunday prep)

- [ ] Desk review meeting (Charter §3): drawdown state vs. weekly brake.
- [ ] Strategy performance snapshot: win rate, expectancy, slippage vs.
      backtest (`financial_analysis/backtest.py` comparison).
- [ ] Bot config diff: any parameter changes this week? Logged and signed?
- [ ] Backups verified (see 08 §4): repo pushed, statements archived.

## 3. Monthly (by the 5th business day)

- [ ] **Reconciliation:** broker statements ↔ trade log ↔ bank accounts.
      Break protocol: unexplained difference > [$100] → investigate before
      publishing anything.
- [ ] Capital statements drafted → second-eyes check → published to portal.
- [ ] Allocation vs. IPS bands; rebalance memo if any band is breached.
- [ ] Expense sweep: office costs booked; runway (24-month liquidity test).
- [ ] News pipeline & site health: Actions runs green, pages deploying.

## 4. Quarterly

- [ ] Family letter drafted and delivered; mandate scoring table updated.
- [ ] Distribution programme executed and logged in capital accounts.
- [ ] Strategy deep-dive: retire, scale, or incubate one strategy with data.
- [ ] Access review lite: portal codes rotated; stale credentials revoked.

## 5. Annually (January)

- [ ] Full governance meeting (Charter §3): IPS re-ratification.
- [ ] External review: accountant/reviewer engagement for the prior year.
- [ ] Vendor & fee audit: brokers, data, hosting, subscriptions.
- [ ] Continuity drill (08 §5) — actually run it, minute the results.
- [ ] Insurance & titles: coverage adequate to asset values; titles clean.

## 6. Reporting formats (fixed)

| Artifact | Format | Standard |
|---|---|---|
| Trade log | Machine-readable (CSV/DB), append-only | Every fill, every tag |
| Capital statement | Fixed template, monthly | Reconciled before publishing |
| Family letter | 2–4 pages, quarterly | Same section order every quarter |
| Meeting minute | 1 page | Decisions + owners only |
| Post-mortem | 1–2 pages within 5 business days | Cause → contributing factors → rule change (if any) |

## 7. Break glass

If reconciliation breaks, a limit is breached, or an account behaves
unexpectedly: **stop adding risk first, investigate second, report third** —
same day, to the full committee, in writing.
