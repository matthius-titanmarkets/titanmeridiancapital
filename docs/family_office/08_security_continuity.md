# 08 · Security & Continuity

Discretion is a structural feature. So is survivability.

---

## 1. Principles

1. **Least privilege, personally issued.** Access is granted to named
   people, for named systems, and revoked the day it stops being needed.
2. **No secrets in the repo.** This repository is public-facing; nothing
   credential-shaped is ever committed (keys, tokens, account numbers,
   statements). The public surfaces run on sample/simulated data only.
3. **Two sets of eyes** on money movement and reconciliation.
4. **Append-only records.** Corrections are new entries, never edits.

## 2. Credentials & keys

- Passwords/API keys live in a reputable password manager vault with
  role-scoped collections (Desk, Ops, IC). Hardware security keys for email,
  GitHub, broker, and bank where supported.
- Broker/bot credentials exist **only** in the bot host's environment file,
  never in TradingView alert text beyond the shared-secret token the webhook
  verifies.
- Portal demo code is public by design (it gates nothing). Production
  credentials, when built (07 §4), are issued in person and rotated on a
  calendar.
- Rotation: shared secrets quarterly; personal credentials on any suspicion;
  everything on any offboarding (06 §D).

## 3. Device & channel hygiene

- Desk and Ops machines: full-disk encryption, auto-lock, OS current.
- Email is the weakest door: no account numbers or credentials by email;
  wire/distribution instructions confirmed by a second channel (call-back to
  a number on file — never a number from the requesting message).
- Public Wi-Fi: no broker or bank sessions without VPN.

## 4. Backups

| What | Where | Cadence | Test |
|---|---|---|---|
| This repository | GitHub + local clones on ≥2 machines | On push | Clone-and-serve check quarterly |
| Trade logs & bot state | Bot host → encrypted off-machine copy | Daily | Restore test quarterly |
| Statements/minutes archive | Private encrypted storage ×2 locations | Monthly | Open-and-read check quarterly |
| Vault export | Encrypted offline copy in physical safe | Quarterly | Annual drill |

## 5. Incident response (short form)

1. **Contain:** halt trading (terminal halt + bot stop), freeze the affected
   account/channel.
2. **Assess:** what was touched, when, from where; preserve logs.
3. **Rotate:** every credential the incident could have exposed.
4. **Notify:** committee same day; institutions as required; counsel if any
   personal data or funds are implicated.
5. **Post-mortem:** written within 5 business days (Runbook format); update
   this document with the lesson.

Drill annually (Runbook §5): simulate a lost laptop and a compromised email;
minute the gaps found.

## 6. Continuity & succession

- **Successor map:** each role (Charter §1) names a successor; reviewed each
  January.
- **The sealed runbook:** an envelope (physical + encrypted digital) holding:
  where the vault is and how to open it, account register location, counsel
  and accountant contacts, and first-week instructions for an orderly
  wind-down to cash of the trading book. Held by [Principal] and [named
  successor]; existence minuted, contents private.
- **Dead-man protocol:** if the desk is unreachable for [5] trading days,
  Ops flattens open risk via broker support using the documented procedure —
  preservation before performance, in succession as in trading.
