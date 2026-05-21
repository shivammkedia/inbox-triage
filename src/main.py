import sys
import uuid
import traceback
from . import config, audit, gmail_client, classifier, drafter, notify


def run() -> int:
    run_id = str(uuid.uuid4())
    stats = {
        "processed": 0, "urgent": 0, "needs_reply": 0, "fyi": 0, "spam": 0,
        "drafted": 0, "errors": 0, "dry_run": config.DRY_RUN,
    }
    drafted_summaries: list[dict] = []

    print(f"[run {run_id}] dry_run={config.DRY_RUN}")

    messages = gmail_client.list_recent_unread(
        max_results=config.MAX_EMAILS_PER_RUN,
        lookback_hours=config.LOOKBACK_HOURS,
    )
    print(f"found {len(messages)} candidate messages")

    for m in messages:
        email_id = m["id"]
        try:
            if audit.already_processed(email_id, "classify"):
                continue

            email = gmail_client.get_message(email_id)

            cls, cls_meta = classifier.classify(email)
            stats[cls.label] += 1
            stats["processed"] += 1

            audit.log({
                "run_id": run_id,
                "email_id": email_id,
                "thread_id": email["thread_id"],
                "step": "classify",
                "classification": cls.label,
                "confidence": cls.confidence,
                "dry_run": config.DRY_RUN,
                "payload": {
                    "subject": email["subject"],
                    "from": email["from"],
                    "reason": cls.reason,
                },
                **cls_meta,
            })

            if cls.label != "needs_reply":
                continue

            reply, draft_meta = drafter.draft_reply(email, cls.reason)

            draft_id = None
            if not config.DRY_RUN:
                draft_id = gmail_client.create_draft_reply(email, reply)

            audit.log({
                "run_id": run_id,
                "email_id": email_id,
                "thread_id": email["thread_id"],
                "step": "draft",
                "classification": cls.label,
                "dry_run": config.DRY_RUN,
                "draft_id": draft_id,
                "payload": {
                    "subject": email["subject"],
                    "from": email["from"],
                    "reply": reply,
                },
                **draft_meta,
            })

            stats["drafted"] += 1
            drafted_summaries.append({"from": email["from"], "subject": email["subject"]})

        except Exception as e:
            stats["errors"] += 1
            traceback.print_exc()
            try:
                audit.log({
                    "run_id": run_id,
                    "email_id": email_id,
                    "step": "error",
                    "dry_run": config.DRY_RUN,
                    "error": f"{type(e).__name__}: {e}",
                })
            except Exception:
                pass

    try:
        notify.send_telegram(notify.build_digest(stats, drafted_summaries))
    except Exception as e:
        print(f"telegram notify failed: {e}", file=sys.stderr)

    print(f"done: {stats}")
    return 0 if stats["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
