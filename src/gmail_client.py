import base64
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from typing import Iterator

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from . import config

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
# gmail.modify lets us read + create drafts + mark read. NOT gmail.send.


def _service():
    creds = Credentials(
        token=None,
        refresh_token=config.GMAIL_REFRESH_TOKEN,
        client_id=config.GMAIL_CLIENT_ID,
        client_secret=config.GMAIL_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def list_recent_unread(max_results: int, lookback_hours: int) -> list[dict]:
    svc = _service()
    after_ts = int((datetime.now(timezone.utc) - timedelta(hours=lookback_hours)).timestamp())
    query = f"is:unread -category:promotions -category:social after:{after_ts}"
    resp = svc.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    return resp.get("messages", [])


def get_message(message_id: str) -> dict:
    svc = _service()
    msg = svc.users().messages().get(userId="me", id=message_id, format="full").execute()
    return _parse_message(msg)


def _parse_message(msg: dict) -> dict:
    headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
    body = _extract_body(msg["payload"])
    return {
        "id": msg["id"],
        "thread_id": msg.get("threadId"),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", ""),
        "message_id_header": headers.get("message-id", ""),
        "references": headers.get("references", ""),
        "snippet": msg.get("snippet", ""),
        "body": body[:8000],  # cap context
    }


def _extract_body(payload: dict) -> str:
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
        # fall back to first part recursively
        for part in payload["parts"]:
            sub = _extract_body(part)
            if sub:
                return sub
    data = payload.get("body", {}).get("data")
    if data:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    return ""


def create_draft_reply(email: dict, reply_text: str) -> str:
    """Create a draft as a reply on the existing thread. Returns draft id."""
    svc = _service()
    mime = MIMEText(reply_text)
    mime["To"] = email["from"]
    mime["Subject"] = "Re: " + email["subject"] if not email["subject"].lower().startswith("re:") else email["subject"]
    if email.get("message_id_header"):
        mime["In-Reply-To"] = email["message_id_header"]
        refs = (email.get("references") or "") + " " + email["message_id_header"]
        mime["References"] = refs.strip()
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    draft = svc.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw, "threadId": email["thread_id"]}},
    ).execute()
    return draft["id"]
