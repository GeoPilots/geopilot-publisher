"""
Orchestration layer: orders the stages and passes artifacts between them.
"""
from geopilot_publisher.stages.generate_ideas import generate_ideas
from geopilot_publisher.stages.generate_script import generate_script
from geopilot_publisher.stages.tts import synthesize_voice
from geopilot_publisher.stages.render_video import render_video
from geopilot_publisher.stages.upload_youtube import upload_video

def run_all(publish: bool = False) -> None:
    idea = generate_ideas()
    script = generate_script(idea)
    audio_path = synthesize_voice(script)
    video_path = render_video(script, audio_path)

    if publish:
        upload_video(video_path)
