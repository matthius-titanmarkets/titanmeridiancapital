# 07 · Technology Estate

Everything the office runs, where it lives, and who owns it. The design bias
is deliberate: **static-first, self-contained, few moving parts.**

---

## 1. Map

| System | Path / Location | Runtime | Owner |
|---|---|---|---|
| Fund website | `/index.html` | Static (GitHub Pages) | Ops |
| Meridian Terminal | `/platform/` | Static + browser JS (simulated data; paper book in localStorage) | Desk |
| Client portal (demo) | `/clients/` | Static + browser JS (sample data; demo gate) | Ops |
| Titan Markets site | `/titan-markets/` | Static | Ops |
| Family office pack | `/docs/family_office/` | Markdown | IC |
| News pipeline | `scripts/fetch_news.py` + `.github/workflows/news.yml` | GitHub Actions cron (30 min, weekdays) → `platform/data/news.json` | Ops |
| Pages deploy | `.github/workflows/pages.yml` | GitHub Actions on push to `main` | Ops |
| Trading bot | `/trading_bot/` | Python service: TradingView alert → Flask webhook → Interactive Brokers (ib_insync), risk-gated | Desk |
| Strategy code | `/trading_bot/pine_script/` | TradingView Pine | Desk |
| Research & backtests | `/financial_analysis/` | Python (pandas) | Desk |
| Ops dashboard | `/dashboard.py` | Streamlit (local) | Ops |

## 2. Data flows

```
TradingView strategy ──alert──▶ webhook_server.py ──checks──▶ risk_manager.py
                                                       │ pass
                                                       ▼
                                              broker.py ──▶ Interactive Brokers
                                                       │
                                                       ▼
                                             state_manager.py → trade log
                                                       │
                     financial_analysis / dashboard.py ◀┘ (reporting)

Public RSS wires ──cron──▶ fetch_news.py ──▶ platform/data/news.json ──▶ Terminal
```

The public surfaces (site, terminal, portal) hold **no live account data**.
Terminal prices are simulated for display; the paper book never leaves the
browser. Live execution exists only in the bot stack, which runs privately.

## 3. Environments & deploys

- `main` → GitHub Pages via `pages.yml` (upload-artifact of repo root).
- News refresh commits `platform/data/news.json` on a 30-minute weekday
  cron, which re-triggers the Pages deploy.
- Local preview: `python3 -m http.server 4173` at repo root (or the
  `.claude/launch.json` "estate" config).
- Bot: runs on a desk machine/VPS; **never** from this public repo's CI.
  Broker credentials live only in that machine's environment (08 §2).

## 4. Known gaps / next build steps

1. **Production portal auth** — the demo gate is client-side by design (it
   protects nothing). Production requires a backend: recommended path is
   Supabase Auth (or Auth0) + a small API serving real statements, with the
   static portal as the shell. Until then the portal carries sample data
   only.
2. **Real market data in the terminal** — plug a quote API key in behind a
   thin proxy if live quotes are ever wanted publicly; until then simulated
   mode is labeled honestly.
3. **Statement generation** — automate monthly PDF statements from the trade
   log (Python, reportlab) into the archive.

## 5. Registers (keep current)

- **Account register:** every bank/broker account — institution, title,
  signers, API keys issued, added-to-reconciliation date.
- **Access register:** who can touch what (repo, hosting, broker, portal
  issuance), reviewed each January.
- **Archive:** statements, minutes, letters, executed documents — stored
  outside the public repo (private storage), backed up per 08 §4.
