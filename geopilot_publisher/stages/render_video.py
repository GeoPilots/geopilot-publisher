import subprocess
from pathlib import Path


def render_video(script: str, audio_path: str) -> str:
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    out_path = artifacts_dir / "video.mp4"
    audio_path = str(audio_path)

    print(f"[render_video] audio_path={audio_path}")
    print(f"[render_video] out_path={out_path}")

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
        str(out_path),
    ]

    print("[render_video] running:", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as e:
        raise RuntimeError("ffmpeg not found") from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg failed with exit code {e.returncode}") from e

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError("video.mp4 was not created or is empty")

    return str(out_path)