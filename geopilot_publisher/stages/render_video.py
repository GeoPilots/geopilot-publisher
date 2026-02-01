import subprocess
from pathlib import Path


def _ffmpeg_subtitles_filter(srt_path: Path) -> str:
    """
    Build a safe subtitles filter string.
    We keep it simple: bottom-center captions, large font, readable margin.
    """
    # Use absolute path in CI to avoid working-dir surprises
    srt_abs = srt_path.resolve()

    # Escape single quotes for ffmpeg filter parsing
    srt_str = str(srt_abs).replace("'", r"\'")

    # libass style:
    # Alignment=2 => bottom-center
    # MarginV => distance from bottom
    style = "Fontsize=56,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=140"
    return f"subtitles='{srt_str}':force_style='{style}'"


def render_video(script: str, audio_path: str) -> str:
    """
    Render a 9:16 (1080x1920) black background video with audio.
    If artifacts/captions.srt exists, burn captions into the video.
    Outputs: artifacts/video.mp4
    """
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    out_path = artifacts_dir / "video.mp4"
    audio_path = str(audio_path)

    captions_path = artifacts_dir / "captions.srt"
    vf = None
    if captions_path.exists() and captions_path.stat().st_size > 0:
        vf = _ffmpeg_subtitles_filter(captions_path)

    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel", "error",
        "-f", "lavfi",
        "-i", "color=c=black:s=1080x1920:r=30",
        "-i", audio_path,
        "-shortest",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
    ]

    if vf:
        cmd += ["-vf", vf]

    cmd.append(str(out_path))

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as e:
        raise RuntimeError("ffmpeg not found. Install ffmpeg locally and in GitHub Actions.") from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg failed with exit code {e.returncode}") from e

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError("video.mp4 was not created or is empty")

    return str(out_path)