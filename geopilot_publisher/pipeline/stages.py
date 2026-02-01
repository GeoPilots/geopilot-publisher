"""
Orchestration layer: orders the stages and passes artifacts between them.
"""

from pathlib import Path

from geopilot_publisher.stages.generate_ideas import generate_ideas
from geopilot_publisher.stages.generate_script import generate_script
from geopilot_publisher.stages.tts import synthesize_voice
from geopilot_publisher.stages.render_video import render_video
from geopilot_publisher.stages.upload_youtube import upload_video
from geopilot_publisher.utils.captions import build_captions_from_script, write_srt


def run_all(publish: bool = False) -> None:
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    idea = generate_ideas()
    script = generate_script(idea)

    # Save script artifact
    (artifacts_dir / "script.txt").write_text(script, encoding="utf-8")

    # Build captions from the script and save SRT
    captions = build_captions_from_script(script)
    write_srt(captions, artifacts_dir / "captions.srt")

    audio_path = synthesize_voice(script)

    # Render video (will burn captions if captions.srt exists)
    video_path = render_video(script, audio_path)

    if publish:
        upload_video(video_path)