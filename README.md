# Inbox Triage

> An agentic inbox triage system built around **trust primitives** — capability scopes, dry-run mode, append-only audit log, idempotency. Production-shaped, not a toy.

Every 15 minutes, an LLM agent reads new Gmail, classifies each message (`urgent` / `needs_reply` / `fyi` / `spam`), and drafts replies into the Gmail Drafts folder for the ones that need one. **It never sends.** Every action is logged to a Postgres audit trail, and a Telegram digest summarises the run.

Built to run entirely on free tiers — Groq + Supabase + GitHub Actions + Gmail API. **$0/month.**

---

## Why this exists

Most "AI inbox" demos wire an LLM to Gmail and let it act. That's fine for a screenshot, but it fails the production test: what happens when the model hallucinates? Who approves a send? Where's the audit trail when something goes wrong?

This project is the smallest meaningful version of an agent that's **safe to leave running**:

- The agent can read, classify, and draft — but **cannot send.** Enforced at the OAuth scope level, not by prompt engineering.
- A **dry-run mode** flips between observe-only and act, controlled by a single env var.
- Every classification, draft, and error is **logged immutably** with full I/O, model, tokens, and latency — auditable end-to-end.
- An **idempotency guard** means a re-run never double-processes an email.

These are the same primitives a real "agentic system you can trust in production" needs. Inbox triage is just the simplest workflow to demonstrate them.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  GitHub Actions (cron every 15 min)                          │
│   - Free, no server, no ops                                  │
│   - Secrets stored in repo settings                          │
└────────────────────────┬─────────────────────────────────────┘
                         │ spins up ephemeral Ubuntu runner
                         ▼
              ┌──────────────────────┐
              │   Python orchestrator│
              │   (src/main.py)      │
              └─────┬──────┬──────┬──┘
                    │      │      │
       ┌────────────┘      │      └────────────┐
       ▼                   ▼                   ▼
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│ Gmail API   │    │ Groq (Llama) │    │ Supabase     │
│ scope:      │    │ Llama 3.1 8B │    │ append-only  │
│ gmail.modify│    │ (classifier) │    │ events table │
│ — read +    │    │ Llama 3.3 70B│    │ + idempotency│
│ draft only  │    │ (drafter)    │    │ unique index │
└─────────────┘    └──────────────┘    └──────────────┘
                                              │
                                              ▼
                                       ┌──────────────┐
                                       │ Telegram     │
                                       │ digest msg   │
                                       └──────────────┘
```

The whole system is dormant 99% of the time. Every 15 min, GitHub spins up a runner for ~30 seconds, the script runs, and the runner is destroyed. Supabase persists the audit log across runs.

---

## Trust primitives demonstrated

| Primitive | How it's implemented |
|---|---|
| **Capability scoping** | OAuth grants `gmail.modify` only — the code physically cannot call `messages.send` because the token has no permission. Defence in depth, not just policy. |
| **Dry-run mode** | `DRY_RUN=true` classifies + logs as normal but skips draft writes. Safe to test against a real inbox. |
| **Append-only audit log** | Every `classify` / `draft` / `error` step writes a Supabase row with model, token usage, latency, full input/output payload, and dry-run flag. |
| **Idempotency** | `(email_id, step)` unique index + pre-check. If the cron re-fires or the runner dies mid-flight, re-runs are no-ops. |
| **Structured LLM I/O** | Classifier output is JSON schema validated via Pydantic, retried on parse failure. The drafter is constrained by an explicit "do not invent facts" prompt + bracketed-placeholder convention. |
| **Two-model split** | Classification (high volume, simple) runs on Llama 3.1 8B; drafting (lower volume, quality matters) on Llama 3.3 70B. Cheaper, faster, more focused prompts. |

---

## Stack

| Layer | Choice | Why |
|---|---|---|
| **LLM** | Groq (Llama 3.1 8B + Llama 3.3 70B) | Free, fast, OpenAI-compatible API |
| **Email** | Gmail API, `gmail.modify` scope | Lowest-privilege scope that allows drafts |
| **Compute** | GitHub Actions cron | Free, zero ops, secrets + logs built in |
| **Database** | Supabase Postgres | Free 500 MB tier, hosted, persistent across runs |
| **Notifier** | Telegram bot | Free, instant, mobile-native |
| **Language** | Python 3.11 + uv | Fast deps, lockfile by default |
| **Validation** | Pydantic v2 | Structured LLM outputs without prompt-engineering JSON parsing |

---

## Tradeoffs worth knowing

- **Why GitHub Actions cron and not a real server?** Polling every 15 min from an ephemeral runner costs nothing and has zero failure modes around uptime. A real server is needed only when you want webhook-driven runs (Gmail push notifications via Pub/Sub). Trivial migration path when needed.
- **Why Llama and not GPT/Claude?** The product point is the trust primitives, not the model. Llama via Groq is good enough for this workflow and removes API cost from the equation.
- **Why two models instead of one?** Smaller focused prompts beat one giant prompt on open models. Llama 3.1 8B is more than sufficient for 4-way classification; saving the 70B for drafting cuts latency and improves quality where it matters.
- **Why Supabase and not SQLite?** SQLite would need to be committed to the repo (rewritten by every Actions run = race conditions, leaked data) or stored on a volume (no free option). Supabase is the simplest hosted Postgres tier that survives ephemeral compute.
- **Why no web UI?** YAGNI for v1. The "review surface" is the Gmail Drafts folder itself + the Telegram digest. A dashboard is the obvious v2.

---

## Project layout

```
inbox-triage/
├── .github/workflows/triage.yml   # cron every 15 min
├── scripts/
│   └── bootstrap_gmail_oauth.py   # one-time refresh token minting
├── sql/
│   └── schema.sql                 # events table + idempotency index
├── src/
│   ├── main.py                    # orchestrator: fetch -> classify -> draft -> log -> notify
│   ├── gmail_client.py            # read + draft (capability-scoped)
│   ├── llm_client.py              # Groq wrapper, JSON + text, retries
│   ├── classifier.py              # Pydantic-validated 4-way classification
│   ├── drafter.py                 # reply drafter, conservative on facts
│   ├── audit.py                   # Supabase append-only event log
│   ├── notify.py                  # Telegram digest
│   └── config.py                  # env config
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Setup

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (`winget install astral-sh.uv` on Windows)
- Free accounts: [Groq](https://console.groq.com), [Supabase](https://supabase.com), Telegram, Google Cloud

### 1. Clone & install
```bash
git clone https://github.com/shivammkedia/inbox-triage.git
cd inbox-triage
uv sync
cp .env.example .env
```

### 2. Supabase
- New project → SQL editor → paste contents of `sql/schema.sql` → run.
- Settings → API → copy `URL` and `service_role` key into `.env`.

### 3. Groq
- https://console.groq.com/keys → create key → paste into `.env`.

### 4. Telegram
- DM `@BotFather` → `/newbot` → save token.
- DM your new bot anything (required to activate the chat).
- Visit `https://api.telegram.org/bot<TOKEN>/getUpdates` and grab `chat.id`.
- Paste both into `.env`.

### 5. Gmail OAuth (one-time)
- https://console.cloud.google.com → new project → enable Gmail API.
- OAuth consent screen → External → add your Gmail as a Test user.
- Credentials → Create OAuth client ID → **Desktop app** → download JSON → save as `scripts/credentials.json`.
- Run:
  ```bash
  cd scripts
  uv run python bootstrap_gmail_oauth.py
  ```
- Approve in browser. Paste the three printed values into `.env`.

### 6. Dry run
```bash
DRY_RUN=true uv run python -m src.main
```
Watch Supabase `events` table fill up and your Telegram for the digest.

### 7. Cloud cron
- Push to a **private** GitHub repo.
- Settings → Secrets and variables → Actions → add all 8 secrets from `.env`.
- Actions tab → enable workflows.
- The cron runs every 15 min automatically.

---

## Extending this

Inbox triage is one workflow on a control plane. The same primitives apply to:

- **CRM hygiene** — agent finds stale opportunities, proposes fixes, human approves batch.
- **Support ticket drafting** — agent drafts KB-grounded replies, auto-sends only for tier-1 categories.
- **Invoice reconciliation** — auto-clear high-confidence matches, queue exceptions.
- **Vendor renewal** — agent flags risky clauses, routes to multi-approver workflow.

Each shares the same shape: capability scopes, dry-run, audit log, idempotency, approval surface. The runtime is reusable — only the tools and prompts change.

---

## License

MIT.
