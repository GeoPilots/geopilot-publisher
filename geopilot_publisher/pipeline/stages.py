"""
Orchestration layer: orders the stages and passes artifacts between them.
"""

from pathlib import Path

from geopilot_publisher.stages.generate_ideas import generate_ideas
from geopilot_publisher.stages.generate_script import generate_script
from geopilot_publisher.stages.tts import synthesize_voice
from geopilot_publisher.stages.render_video import render_video
from geopilot_publisher.stages.upload_youtube import upload_video


def run_all(publish: bool = False) -> None:
    # Ensure artifacts directory exists
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    # 1. Generate idea
    idea = generate_ideas()

    # 2. Generate script
    script = generate_script(idea)

    # Save script as an artifact so we can inspect it in CI
    (artifacts_dir / "script.txt").write_text(script, encoding="utf-8")

    # 3. Generate voice audio from script
    audio_path = synthesize_voice(script)

    # 4. Render video (still placeholder/minimal for now)
    video_path = render_video(script, audio_path)

    # 5. Optionally upload
    if publish:
        upload_video(video_path)