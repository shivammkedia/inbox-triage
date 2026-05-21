-- Run this once in Supabase SQL editor.

create table if not exists events (
  id              bigserial primary key,
  run_id          uuid not null,
  email_id        text not null,
  thread_id       text,
  step            text not null,            -- 'classify' | 'draft' | 'skip' | 'error'
  classification  text,                     -- urgent | needs_reply | fyi | spam
  confidence      real,
  model           text,
  prompt_tokens   int,
  output_tokens   int,
  latency_ms      int,
  dry_run         boolean default false,
  draft_id        text,                     -- Gmail draft id when written
  payload         jsonb,                    -- full input/output snapshot
  error           text,
  created_at      timestamptz default now()
);

-- idempotency: a given email is processed at most once per step per run
create unique index if not exists events_unique_step
  on events (email_id, step, run_id);

create index if not exists events_created_idx on events (created_at desc);
create index if not exists events_email_idx   on events (email_id);

-- tracks last-seen email so polls don't reprocess history
create table if not exists cursor (
  id              int primary key default 1,
  last_history_id text,
  last_run_at     timestamptz,
  check (id = 1)
);
insert into cursor (id) values (1) on conflict do nothing;
