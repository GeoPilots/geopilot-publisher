import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
TOKEN_URI = "https://oauth2.googleapis.com/token"


def _require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val


def _get_youtube_client():
    client_id = _require_env("YT_CLIENT_ID")
    client_secret = _require_env("YT_CLIENT_SECRET")
    refresh_token = _require_env("YT_REFRESH_TOKEN")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=[YOUTUBE_UPLOAD_SCOPE],
    )

    # IMPORTANT: refresh explicitly so we fail here (with a clear error) if auth is wrong
    creds.refresh(Request())

    # cache_discovery=False avoids some CI edge cases
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload_video(video_path: str) -> str:
    """
    Upload the MP4 to YouTube and return the video URL.
    Default privacy is 'unlisted' (safe).
    """
    path = Path(video_path)

    if not path.exists():
        raise RuntimeError(f"Video file does not exist: {path}")

    size = path.stat().st_size
    if size <= 0:
        raise RuntimeError(f"Video file is empty: {path}")

    print(f"[upload_youtube] uploading file: {path} ({size} bytes)")
    print("[upload_youtube] privacy=unlisted (video won't appear on public channel page)")
    print("[upload_youtube] find it in YouTube Studio → Content → Unlisted")

    # Minimal safe defaults (we can later make these dynamic from script/idea)
    title = "GeoPilot Publisher Test"
    description = "Test upload from GeoPilot Publisher pipeline."
    tags = ["GeoPilot", "AI", "Publisher"]
    privacy_status = "unlisted"

    youtube = _get_youtube_client()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "28",  # Science & Technology
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(path), mimetype="video/mp4", resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    try:
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"[upload_youtube] progress: {pct}%")

        # The only success condition: response contains id
        video_id = response.get("id")
        if not video_id:
            raise RuntimeError(f"Upload finished but response had no video id: {response}")

        url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"✅ Uploaded: {url}")
        return url

    except HttpError as e:
        # This prints the real YouTube API error message
        err_text = ""
        try:
            err_text = e.content.decode("utf-8", errors="replace") if hasattr(e, "content") else str(e)
        except Exception:
            err_text = str(e)

        raise RuntimeError(f"YouTube API upload failed:\n{err_text}") from e
