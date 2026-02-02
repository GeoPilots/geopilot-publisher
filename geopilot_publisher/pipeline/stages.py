"""
Orchestration layer: orders the stages and passes artifacts between them.
"""

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

    reuse = os.getenv("GP_REUSE_SCRIPT") == "1"
    script_path = artifacts_dir / "script.txt"
    audio_path = artifacts_dir / "voice.mp3"
    keywords_path = artifacts_dir / "keywords.txt"

    if reuse:
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
