"""
One-time OAuth bootstrap script.
Place your downloaded OAuth client JSON at:
  bootstrap/client_secret.json

Then run from repo root:
  python bootstrap/get_refresh_token.py
"""
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        "bootstrap/client_secret.json",
        SCOPES,
    )
    creds = flow.run_local_server(port=0)

    print("\n=== COPY THESE INTO GITHUB SECRETS ===")
    print("YT_CLIENT_ID:", creds.client_id)
    print("YT_CLIENT_SECRET:", creds.client_secret)
    print("YT_REFRESH_TOKEN:", creds.refresh_token)

if __name__ == "__main__":
    main()
