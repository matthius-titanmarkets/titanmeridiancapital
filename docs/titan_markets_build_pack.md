# TITAN MARKETS — Trade Analytics & Risk Dashboard Build Pack

This build pack aggregates UI guidance, data architecture, API design, operational templates, testing, and delivery milestones so teams can ship an end-to-end real-time risk and analytics dashboard.

## 1. Executive Summary
- Single surface for trader performance, strategy analytics, risk monitoring, portfolio exposure, payouts, and administration.
- Goals: prevent blowups, raise trader profitability/retention, automate evaluation & funding, and provide auditable data.
- Primary personas: risk operations, trader success, finance, compliance, and executives.

## 2. UI Mockups & Component Library (React + Tailwind)
**Theme & Layout**
- Dark, high-contrast theme with accessible colors; desktop-first responsive 12-column grid.
- Left vertical navigation: Home, Traders, Strategies, Risk Center, Payouts, Integrations, Admin.
- Top bar KPIs: Firm P/L today, Funds at Risk, Active Alerts, % Profitable Traders.
- Card-driven grid; charts for trends, tables for detail logs; contextual modals for actions.

**Screens**
- **Home**: KPI row (mini-cards), firm equity curve (full-width BigChart), Top 5 traders (TraderCard + sparkline), Alerts feed, Exposure heatmap by asset class.
- **Trader Profile**: Left column: profile, KPI summary, risk score. Main tabs: Performance (equity + trades), Strategy breakdown, Violations timeline, AI analysis. Bottom: recent trades table with tags/violation badges.
- **Risk Center**: Live positions table (per-trader toggles), correlation matrix heatmap, active rule violations list with actions (review, reduce leverage, lock account), rules engine control panel (create/disable/test rules).
- **Strategy Dashboard**: Strategy selector, performance metrics (win rate, avg RR, expectancy, avg hold time), market condition filters, scaling recommendation panel.
- **Payouts/Finance**: Payout forecast graph per trader, live payout queue, revenue center comparing challenge sales vs payouts.

**Component Inventory**
KPICard, Sparkline, BigChart (time series), TradeTable, TraderCard, RuleRow, AlertsList, ExposureHeatmap, CorrelationMatrix, Modal (action confirm), Tag (strategy), Badge (violation). Specify props for data, loading states, and onAction callbacks to keep components stateless and reusable.

## 3. Database Schema (PostgreSQL ± TimescaleDB)
Key tables (see sample migration below): traders, accounts, trades, position_snapshots, alerts, strategies, correlation_cache, daily_trader_aggregates. Index trades on trader_id/account_id/symbol/entry_time; partition trades monthly if volume is high; use Timescale hypertables for position_snapshots. Encrypt PII fields where required.

```sql
-- Core tables
-- Traders
CREATE TABLE traders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trader_tag VARCHAR(64) UNIQUE NOT NULL,
  first_name VARCHAR(64),
  last_name VARCHAR(64),
  email VARCHAR(254),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  status VARCHAR(32) DEFAULT 'active',
  metadata JSONB

-- Accounts
CREATE TABLE accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trader_id UUID REFERENCES traders(id),
  provider_account_id VARCHAR(128),
  account_type VARCHAR(32),
  starting_equity NUMERIC(18,6),
  current_equity NUMERIC(18,6),
  leverage NUMERIC(10,4),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Trades
CREATE TABLE trades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID REFERENCES accounts(id),
  trader_id UUID REFERENCES traders(id),
  provider_trade_id VARCHAR(128),
  symbol VARCHAR(32),
  side VARCHAR(8),
  entry_time TIMESTAMP WITH TIME ZONE,
  exit_time TIMESTAMP WITH TIME ZONE,
  entry_price NUMERIC(18,8),
  exit_price NUMERIC(18,8),
  lots NUMERIC(18,6),
  pnl NUMERIC(18,6),
  realized_pnl NUMERIC(18,6),
  commission NUMERIC(12,6),
  slippage NUMERIC(12,6),
  strategy_tag VARCHAR(64),
  tags TEXT[],
  metadata JSONB
);

-- Position snapshots (for live views)
CREATE TABLE position_snapshots (
  id BIGSERIAL PRIMARY KEY,
  account_id UUID REFERENCES accounts(id),
  trader_id UUID REFERENCES traders(id),
  symbol VARCHAR(32),
  lots NUMERIC(18,6),
  unrealized_pnl NUMERIC(18,6),
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Alerts
CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  related_trader UUID REFERENCES traders(id),
  related_account UUID REFERENCES accounts(id),
  rule VARCHAR(128),
  severity VARCHAR(16),
  payload JSONB,
  resolved BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  resolved_at TIMESTAMP WITH TIME ZONE
);

-- Strategies
CREATE TABLE strategies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(128),
  description TEXT,
  default_tags TEXT[],
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Correlation cache
CREATE TABLE correlation_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot_time TIMESTAMP WITH TIME ZONE,
  matrix JSONB
);

-- Daily aggregates
CREATE TABLE daily_trader_aggregates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trader_id UUID REFERENCES traders(id),
  day DATE,
  pnl NUMERIC(18,6),
  trades_count INT,
  max_drawdown NUMERIC(18,6),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

## 4. API Design (REST + WebSockets)
- **Auth**: `/api/v1/auth/login`, `/api/v1/auth/refresh` (JWT-based; roles: admin, risk-ops, trader-support, viewer).
- **Traders & Accounts**: list/create/update traders, fetch trader profile KPIs, list accounts.
- **Trades/Positions**: broker webhook `/api/v1/webhooks/trade`; list trades per trader; positions per account; WebSocket `/api/v1/positions/stream` for live updates.
- **Alerts & Rules**: list/resolve alerts; create/list/test rules.
- **Reports**: firm KPIs, trader summaries, strategy performance.
- **Outbound webhooks**: alert delivery (Slack/Discord), payout notifications.

## 5. Notion Internal Space ("TITAN - Risk & Analytics")
- **Dashboard** (ops-visible) with embedded charts and links.
- **Traders DB**: Trader ID, Name, Status, Risk Score, Last Payout, Notes, link to profile page.
- **Active Alerts DB**: unresolved alerts, severity, assigned operator, timestamp.
- **Rules DB**: rule name, description, severity, last tested, owner.
- **Release Log / Roadmap**: features, status, owner, ETA.
- **Runbooks**: step-by-step responses for critical alerts.
- **Integrations**: credentials vault pointers and broker/API docs.
- **Metrics Archive**: weekly snapshots with embedded charts.
- Templates: trader onboarding, alert triage checklist, post-mortem report.

## 6. Tech Stack Recommendations
- **Tier A (Lean MVP)**: Supabase (Postgres/Auth/Edge Functions), React + Vite + Tailwind, Vercel + Supabase hosting, Supabase Realtime or Pusher, Discord webhooks + SendGrid. Low cost and fast to ship.
- **Tier B (Production recommended)**: Node.js (TypeScript + Express/Nest), PostgreSQL (AWS RDS) + TimescaleDB, Next.js + Tailwind, WebSockets via API Gateway or Redis + Socket.io, Auth0 or Supabase Auth, GitHub Actions, monitoring via Sentry + Datadog, Slack/Discord/Twilio alerts.
- **Tier C (Enterprise scale)**: Go/Rust microservices on Kubernetes, CockroachDB or Aurora, Kafka for ingestion, Prometheus + Grafana + Datadog, Vault for secrets. Higher cost; multi-tenant/high-throughput ready.

## 7. Rules Engine & Examples
- JSON-based DSL with fields: id, name, description, severity, condition, action array (`alert|lock_account|soft_block`).
- Example: `daily-loss-limit` condition `(realized_pnl + unrealized_pnl) < -1000` with actions `["alert","lock_account"]`.
- Other patterns: trailing drawdown (10% of peak equity), overtrading (>20 trades/day), correlated exposures (>$X in same symbol across firm), blackout around news events. Support test runs against historical trades and staged rollout per trader cohort.

## 8. AI Features
- **Trader Risk Score (0–100)**: features include avg trade size, win rate, max drawdown, avg hold time, trades/day, money-management consistency, return kurtosis; start with gradient-boosted trees (XGBoost).
- **Predictive Payout Model**: time-series forecasting on equity curves (Prophet/ARIMA/LSTM) to estimate payout-threshold probability within N days.
- **AI Trade Breakdown**: heuristic + classifier tags, plus short GPT-style explanations; surface in violations timeline and trade detail.

## 9. Security & Compliance
- RBAC roles (admin, risk-ops, trader-support, viewer); enforce via JWT claims.
- Encrypt PII at rest; restrict secrets to Vault/SM, never Notion.
- Audit logs for rule changes, account locks, payouts; immutable storage recommended.
- 2FA for ops accounts; regular backups and DR runbooks.

## 10. Testing & QA
- Unit tests: rules engine logic, KPI aggregations.
- Integration: broker webhook ingestion (simulate trade open/close), auth flows.
- Load: k6 for ingestion throughput; target <1s webhook-to-alert latency.
- E2E: Cypress for core flows (trade appears in profile; alert surfaces in feed; payout queue update).
- Canary: staged rollout for new rules; feature flags per cohort.

## 11. Monitoring & Observability
- Metrics: ingestion latency, alerts/sec, API error rate, DB/query latency, WebSocket connect count.
- Dashboards: Grafana for infra/uptime, Sentry for FE/BE errors, Datadog for APM.
- SLAs: trade ingestion + alerting <1s, WebSocket availability >=99.5%.

## 12. Deployment & CI/CD
- GitHub Actions: lint, unit tests, integration/E2E, build artifacts, deploy to staging, manual approval to prod.
- Blue/green deploys for backend/frontend; database migrations via Flyway or Prisma migrate.
- Artifacts: Docker images for backend/frontend; versioned OpenAPI spec; migration bundle.

## 13. Step-by-Step Timeline (12 Weeks)
- **Week 0 (Kickoff)**: requirements, broker API access, sample trade CSVs, choose tier.
- **Weeks 1–3 (MVP)**: DB schema + migrations, ingestion (CSV + webhook), daily aggregates, Home/Trader list/Profile pages, basic daily loss-limit alert.
- **Weeks 4–6 (Risk)**: real-time positions, alerts feed, rule editor, correlation engine, exposure heatmap, Notion ops pages/runbooks.
- **Weeks 7–9 (Strategy/Analytics)**: strategy tagging & dashboards, behavior analytics, payout forecast skeleton.
- **Weeks 10–12 (AI & Release)**: risk scoring model, predictive payout, polish UI, staging→prod release, ops training & documentation.

## 14. CI/CD & Ops Runbook (Quick Notes)
- Secrets via environment injection from cloud secret manager.
- Rollback: retain previous release artifacts; feature flags to disable risky modules.
- Backups: nightly DB backups; weekly DR test.
- Access control reviews monthly; log retention aligned with compliance needs.

## 15. Next Steps Menu
1) Generate Figma-ready UI kit & components; 2) Export SQL migrations + seeds; 3) Produce OpenAPI/Swagger; 4) Scaffold Next.js app with sample pages/charts; 5) Build ingestion microservice for CSV + webhook feeds.
