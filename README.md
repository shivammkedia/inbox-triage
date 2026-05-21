# Inbox Triage

Free, cloud-hosted, agentic inbox triage. Every 15 min:
1. Read unread Gmail (last 2h, excluding promotions/social)
2. Classify each: `urgent` / `needs_reply` / `fyi` / `spam` (Llama via Groq)
3. Draft replies into Gmail Drafts for `needs_reply` (never sends)
4. Log every action to Supabase
5. Telegram digest

Stack: Groq + Gmail API + Supabase + Telegram + GitHub Actions cron. Cost: $0.

---

## Setup

### 1. Free accounts
- **Groq**: https://console.groq.com -> API key
- **Supabase**: https://supabase.com -> new project -> SQL editor -> paste `sql/schema.sql`
- **Telegram bot**: message `@BotFather` -> `/newbot` -> save token. Then message your bot, visit `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your `chat.id`.
- **Google Cloud**: enable Gmail API, create OAuth Desktop client, add yourself as test user, download `credentials.json`.

### 2. Gmail OAuth (one time, local)
```
uv sync
cp .env.example .env   # fill what you can
# put credentials.json in scripts/
cd scripts && uv run python bootstrap_gmail_oauth.py
```
Copy the printed `CLIENT_ID` / `CLIENT_SECRET` / `REFRESH_TOKEN` into `.env`.

### 3. Local dry run
```
DRY_RUN=true uv run python -m src.main
```
Check Supabase `events` table and your Telegram for the digest.

### 4. Cloud
- Push repo to GitHub (private).
- Settings -> Secrets and variables -> Actions -> add all 8 secrets from `.env`.
- Actions tab -> enable workflows.
- Cron runs every 15 minutes automatically.

### Toggling dry-run in prod
Edit `DRY_RUN` in `.github/workflows/triage.yml`, or trigger manually via `workflow_dispatch`.

---

## Files

| Path | Purpose |
|---|---|
| `src/main.py` | Orchestrator: fetch -> classify -> draft -> log -> notify |
| `src/gmail_client.py` | Read inbox, create drafts. Scope: `gmail.modify` (cannot send) |
| `src/llm_client.py` | Groq wrapper, JSON + text modes, retries |
| `src/classifier.py` | Structured classification, Pydantic-validated |
| `src/drafter.py` | Reply drafter, conservative on facts |
| `src/audit.py` | Supabase append-only event log + idempotency check |
| `src/notify.py` | Telegram digest |
| `sql/schema.sql` | `events` table + idempotency unique index |
| `.github/workflows/triage.yml` | Cron every 15 min |
| `scripts/bootstrap_gmail_oauth.py` | One-time refresh-token minting |

## Trust primitives demonstrated

- **Capability scope**: OAuth grants `gmail.modify` only -> code literally cannot `send`.
- **Dry-run**: `DRY_RUN=true` classifies + logs but skips draft writes.
- **Audit log**: every classify/draft/error row written with model, tokens, latency, full I/O.
- **Idempotency**: `(email_id, step)` unique index + pre-check; re-runs are no-ops.
- **Structured I/O**: classifier output JSON-validated via Pydantic, retried on parse failure.
