from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import List


@dataclass
class Caption:
    start_s: float
    end_s: float
    text: str


def _format_srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    ms = int(round((seconds - int(seconds)) * 1000))
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = int(seconds) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _split_into_sentences(text: str) -> List[str]:
    text = " ".join(text.strip().split())
    if not text:
        return []
    # Basic sentence splitter. Good enough for Shorts scripts.
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _chunk_words(sentence: str, max_words: int = 8) -> List[str]:
    words = sentence.split()
    if not words:
        return []
    chunks = []
    for i in range(0, len(words), max_words):
        chunks.append(" ".join(words[i : i + max_words]))
    return chunks


def build_captions_from_script(
    script: str,
    *,
    words_per_second: float = 2.4,
    min_segment_s: float = 1.0,
    max_segment_s: float = 4.0,
    max_words_per_line: int = 8,
) -> List[Caption]:
    """
    Turn a script into timed captions using a simple reading-speed model.

    - We split into sentences, then chunk to short lines.
    - Each chunk duration is proportional to word count.
    - This is deterministic and works well enough for a first end-to-end pipeline.
    """
    sentences = _split_into_sentences(script)
    lines: List[str] = []
    for s in sentences:
        lines.extend(_chunk_words(s, max_words=max_words_per_line))

    captions: List[Caption] = []
    t = 0.0
    for line in lines:
        wc = max(1, len(line.split()))
        dur = wc / max(0.1, words_per_second)
        dur = max(min_segment_s, min(max_segment_s, dur))
        captions.append(Caption(start_s=t, end_s=t + dur, text=line))
        t += dur

    return captions


def write_srt(captions: List[Caption], out_path: str | Path) -> str:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    for i, c in enumerate(captions, start=1):
        lines.append(str(i))
        lines.append(f"{_format_srt_timestamp(c.start_s)} --> {_format_srt_timestamp(c.end_s)}")
        lines.append(c.text)
        lines.append("")  # blank line between entries

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return str(out_path)