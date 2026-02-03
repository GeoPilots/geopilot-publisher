"""
Orchestration layer: orders the stages and passes artifacts between them.
"""

import hashlib
import os
from pathlib import Path

from geopilot_publisher.stages.generate_ideas import generate_ideas
from geopilot_publisher.stages.generate_script import generate_script
from geopilot_publisher.stages.tts import synthesize_voice
from geopilot_publisher.stages.render_video import render_video
from geopilot_publisher.stages.upload_youtube import upload_video



def run_all(publish: bool = False) -> None:
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    use_content = os.getenv("GP_USE_CONTENT") == "1"
    reuse = os.getenv("GP_REUSE_SCRIPT") == "1"
    script_path = artifacts_dir / "script.txt"
    audio_path = artifacts_dir / "voice.mp3"
    keywords_path = artifacts_dir / "keywords.txt"
    content_script = Path("content") / "script.txt"
    content_keywords = Path("content") / "keywords.txt"

    if use_content:
        if (
            not content_script.exists()
            or not content_keywords.exists()
            or not content_script.read_text(encoding="utf-8").strip()
            or not content_keywords.read_text(encoding="utf-8").strip()
        ):
            raise RuntimeError(
                "GP_USE_CONTENT=1 requires non-empty content/script.txt and content/keywords.txt"
            )
        script = content_script.read_text(encoding="utf-8")
        keywords_text = content_keywords.read_text(encoding="utf-8")
        script_path.write_text(script, encoding="utf-8")
        keywords_path.write_text(keywords_text, encoding="utf-8")
        if script_path.read_text(encoding="utf-8") != script:
            raise RuntimeError("GP_USE_CONTENT=1 script copy verification failed")
        script_preview = " ".join(script.strip().split())[:80]
        script_hash = hashlib.sha256(script.encode("utf-8")).hexdigest()[:12]
        keyword_count = len([line for line in keywords_text.splitlines() if line.strip()])
        print(f"[content] script preview: {script_preview}")
        print(f"[content] script sha256: {script_hash}")
        print(f"[content] keywords: {keyword_count}")
        audio_path = Path(synthesize_voice(script))
    elif reuse:
        if not script_path.exists() or not audio_path.exists():
            raise RuntimeError(
                "GP_REUSE_SCRIPT=1 requires artifacts/script.txt and artifacts/voice.mp3"
            )
        script = script_path.read_text(encoding="utf-8")
    else:
        idea = generate_ideas()
        script = generate_script(idea)
        script_path.write_text(script, encoding="utf-8")
        audio_path = Path(synthesize_voice(script))

    if publish and (not keywords_path.exists() or not keywords_path.read_text(encoding="utf-8").strip()):
        raise RuntimeError(
            "Publish requested but artifacts/keywords.txt is missing or empty. "
            "CI runs clean; add keywords.txt to artifacts before publishing."
        )

    video_path = render_video(script, audio_path)

    if publish:
        upload_video(video_path)
    else:
        print(f"[dry-run] would upload: {video_path}")
