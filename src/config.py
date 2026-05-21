import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY        = os.environ["GROQ_API_KEY"]
OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY", "")

CLASSIFIER_MODEL    = os.getenv("CLASSIFIER_MODEL", "llama-3.3-70b-versatile")
DRAFTER_MODEL       = os.getenv("DRAFTER_MODEL", "llama-3.3-70b-versatile")

GMAIL_CLIENT_ID     = os.environ["GMAIL_CLIENT_ID"]
GMAIL_CLIENT_SECRET = os.environ["GMAIL_CLIENT_SECRET"]
GMAIL_REFRESH_TOKEN = os.environ["GMAIL_REFRESH_TOKEN"]

SUPABASE_URL        = os.environ["SUPABASE_URL"]
SUPABASE_KEY        = os.environ["SUPABASE_KEY"]

TELEGRAM_BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID    = os.environ["TELEGRAM_CHAT_ID"]

DRY_RUN             = os.getenv("DRY_RUN", "true").lower() == "true"
MAX_EMAILS_PER_RUN  = int(os.getenv("MAX_EMAILS_PER_RUN", "20"))
LOOKBACK_HOURS      = int(os.getenv("LOOKBACK_HOURS", "2"))
