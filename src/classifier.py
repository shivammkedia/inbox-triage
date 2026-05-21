from pydantic import BaseModel, Field
from typing import Literal
from .llm_client import chat_json
from . import config

Label = Literal["urgent", "needs_reply", "fyi", "spam"]


class Classification(BaseModel):
    label: Label
    confidence: float = Field(ge=0, le=1)
    reason: str


SYSTEM = """You classify emails for an executive's inbox. Output STRICT JSON with keys:
  label: one of "urgent" | "needs_reply" | "fyi" | "spam"
  confidence: 0..1
  reason: one short sentence

Definitions:
- urgent      : time-sensitive AND requires the user's action (deadlines, outages, exec asks, customer escalations)
- needs_reply : the sender expects a personal response, but it is not urgent
- fyi         : informational; no response expected (newsletters, receipts, notifications, CC for awareness)
- spam        : marketing, cold outreach, phishing, automated promotions

Examples:
1) "Server down in prod" from a teammate -> {"label":"urgent","confidence":0.95,"reason":"Production incident requiring action"}
2) "Quick question about the proposal" from a client -> {"label":"needs_reply","confidence":0.85,"reason":"Direct question from client expecting reply"}
3) "Your weekly Stripe summary" -> {"label":"fyi","confidence":0.9,"reason":"Automated informational summary"}
4) "Boost your sales 10x with our AI tool" -> {"label":"spam","confidence":0.95,"reason":"Cold marketing outreach"}
"""


def classify(email: dict) -> tuple[Classification, dict]:
    user = (
        f"From: {email['from']}\n"
        f"Subject: {email['subject']}\n"
        f"Snippet: {email['snippet']}\n\n"
        f"Body:\n{email['body'][:2000]}"
    )
    data, meta = chat_json(config.CLASSIFIER_MODEL, SYSTEM, user, temperature=0.0)
    return Classification(**data), meta
