import os
import re
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

    script_text = _read_text(Path("artifacts") / "script.txt")
    keywords = _load_keywords_preferred()
    title = _build_title(script_text, keywords)
    description = _build_description(script_text, keywords)
    tags = _build_tags(script_text, keywords)
    privacy_status = "unlisted"

    print(f"[upload_youtube] title: {title}")
    print(f"[upload_youtube] description: {description[:200]}{'...' if len(description) > 200 else ''}")
    print(f"[upload_youtube] tags: {len(tags)}")

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


def _read_text(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _load_keywords_preferred() -> list[str]:
    candidates = [
        Path("content") / "keywords.txt",
        Path("artifacts") / "keywords.txt",
    ]
    for path in candidates:
        if path.exists():
            lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
            keywords = [line for line in lines if line and not line.startswith("#")]
            if keywords:
                return keywords[:10]
    return []


def _normalize_keyword(text: str) -> str:
    cleaned = re.sub(r"[→&/]", " ", text)
    cleaned = re.sub(r"[^A-Za-z0-9 ]+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _title_case(text: str) -> str:
    return " ".join(word.capitalize() for word in text.split())


def _build_title(script_text: str, keywords: list[str]) -> str:
    primary = ""
    if keywords:
        primary = _title_case(_normalize_keyword(keywords[0]))
    if not primary:
        first_line = ""
        for line in script_text.splitlines():
            line = line.strip()
            if line:
                first_line = line
                break
        primary = " ".join(first_line.split()[:5]) if first_line else "GeoPilots Insight"
    angle = ""
    if len(keywords) > 1:
        angle = _title_case(_normalize_keyword(keywords[1]))
    elif script_text:
        words = script_text.replace("\n", " ").split()
        angle = " ".join(words[5:10]).strip()
    title = f"{primary}: {angle}" if angle else primary
    title = re.sub(r"\s+", " ", title).strip()
    if len(title) > 70:
        title = title[:70].rstrip(" :,-")
    if len(title) < 45 and angle and primary:
        title = f"{primary}: {angle}"
    return title


def _build_description(script_text: str, keywords: list[str]) -> str:
    summary = _summarize_script(script_text, max_sentences=3)
    keyword_line = ""
    if keywords:
        keyword_line = "Keywords: " + ", ".join(keywords[:10])
    hashtags = _build_hashtags(keywords)
    parts = [p for p in [summary, keyword_line, " ".join(hashtags)] if p]
    return "\n\n".join(parts)


def _summarize_script(script_text: str, max_sentences: int = 2) -> str:
    if not script_text:
        return "Automated analysis of real-world signals and decision systems."
    text = re.sub(r"\s+", " ", script_text.strip())
    sentences = re.split(r"(?<=[.!?])\s+", text)
    summary = " ".join(sentences[:max_sentences]).strip()
    return summary[:400]


def _build_hashtags(keywords: list[str]) -> list[str]:
    tags = []
    for kw in keywords[:5]:
        cleaned = _normalize_keyword(kw)
        if not cleaned:
            continue
        tag = "#" + "".join(word.capitalize() for word in cleaned.split())
        tags.append(tag)
    if not tags:
        tags = ["#AI", "#MachineLearning", "#DataScience"]
    return tags


def _build_tags(script_text: str, keywords: list[str]) -> list[str]:
    if keywords:
        tags = [_title_case(_normalize_keyword(k)) for k in keywords]
        tags = [t for t in tags if t]
        return tags[:20]
    # Basic fallback from script
    words = re.findall(r"[A-Za-z]{4,}", script_text.lower())
    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    common = sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:12]
    return [_title_case(w) for w, _ in common]
