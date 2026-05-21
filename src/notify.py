import httpx
from . import config


def send_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    httpx.post(
        url,
        json={
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        },
        timeout=15,
    ).raise_for_status()


def build_digest(stats: dict, drafted: list[dict]) -> str:
    lines = [
        "*Inbox triage run complete*",
        f"Processed: {stats['processed']}  |  "
        f"Urgent: {stats['urgent']}  |  Reply: {stats['needs_reply']}  |  "
        f"FYI: {stats['fyi']}  |  Spam: {stats['spam']}",
    ]
    if stats.get("dry_run"):
        lines.append("_(dry-run: no drafts written)_")
    if drafted:
        lines.append("\n*Drafts ready for review:*")
        for d in drafted[:10]:
            subj = d["subject"][:80].replace("*", "")
            lines.append(f"- _{d['from'][:40]}_ — {subj}")
    return "\n".join(lines)
