from supabase import create_client, Client
from . import config

_client: Client | None = None


def db() -> Client:
    global _client
    if _client is None:
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _client


def already_processed(email_id: str, step: str) -> bool:
    """Idempotency check across runs."""
    res = (
        db().table("events")
        .select("id")
        .eq("email_id", email_id)
        .eq("step", step)
        .limit(1)
        .execute()
    )
    return bool(res.data)


def log(event: dict) -> None:
    db().table("events").insert(event).execute()
