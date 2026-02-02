#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Activate venv
source .venv/bin/activate

# Ensure ffmpeg-full is used (Apple Silicon brew path)
export PATH="/opt/homebrew/opt/ffmpeg-full/bin:$PATH"
hash -r

# Force fresh render output
rm -f artifacts/video.mp4

# Run pipeline
python -m geopilot_publisher.pipeline.run --publish false

# Auto-play (macOS)
open artifacts/video.mp4
