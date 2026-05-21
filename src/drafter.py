from .llm_client import chat_text
from . import config

SYSTEM = """You draft email replies in the voice of the recipient (a busy professional).
Rules:
- Be concise: 2-5 sentences unless complexity demands more.
- Match the sender's tone (formal vs casual).
- Do NOT invent facts, commitments, dates, or numbers. If you don't know, leave a [BRACKETED PLACEHOLDER].
- No subject line, no signature, no "Best regards". Just the body.
- If a clear answer requires info you don't have, write a short reply that asks the clarifying question."""


def draft_reply(email: dict, classification_reason: str) -> tuple[str, dict]:
    user = (
        f"Incoming email:\n"
        f"From: {email['from']}\n"
        f"Subject: {email['subject']}\n\n"
        f"{email['body'][:3000]}\n\n"
        f"---\n"
        f"Why this needs a reply: {classification_reason}\n"
        f"Draft the reply body now."
    )
    text, meta = chat_text(config.DRAFTER_MODEL, SYSTEM, user, temperature=0.4)
    return text.strip(), meta
