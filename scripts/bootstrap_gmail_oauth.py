"""
One-time local script to get a Gmail refresh token.

Setup:
  1. Go to https://console.cloud.google.com/apis/credentials
  2. Create OAuth 2.0 Client ID -> Desktop app
  3. Download the JSON, save it next to this script as 'credentials.json'
  4. Enable Gmail API for the project
  5. Add your Gmail address as a "test user" under OAuth consent screen
  6. Run: uv run python scripts/bootstrap_gmail_oauth.py
  7. A browser will open. Approve. Copy the refresh_token printed at the end.
  8. Put GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET / GMAIL_REFRESH_TOKEN into .env
     (and later into GitHub Actions secrets).
"""
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def main() -> None:
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    print("\n=== COPY THESE INTO .env ===")
    print(f"GMAIL_CLIENT_ID={creds.client_id}")
    print(f"GMAIL_CLIENT_SECRET={creds.client_secret}")
    print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
    print("============================\n")


if __name__ == "__main__":
    main()
