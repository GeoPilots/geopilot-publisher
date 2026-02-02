from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import List, Tuple


@dataclass
class Caption:
    start_s: float
    end_s: float
    line1: str
    line2: str = ""


def _clean(text: str) -> str:
    return " ".join(text.strip().split())


def _split_phrases(text: str) -> List[str]:
    """
    Split into short phrases appropriate for captions.
    Prefer breaking on punctuation, then on conjunctions if needed.
    """
    text = _clean(text)
    if not text:
        return []

    # Split by sentence punctuation first
    parts = re.split(r"(?<=[.!?])\s+", text)
    phrases: List[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # Further split long sentences on commas/semicolons/dashes
        sub = re.split(r"(?<=[,;:])\s+|—\s+|-{2,}\s+", p)
        for s in sub:
            s = s.strip()
            if s:
                phrases.append(s)
    return phrases


def _wrap_two_lines(phrase: str, max_chars: int = 34) -> Tuple[str, str]:
    """
    Wrap into at most two lines with a roughly balanced break.
    """
    phrase = _clean(phrase)
    if len(phrase) <= max_chars:
        return phrase, ""

    words = phrase.split()
    if len(words) <= 3:
        return phrase, ""

    # Find a split point near the middle that keeps both lines <= max_chars (best effort)
    best_i = None
    best_score = 10**9
    for i in range(2, len(words) - 1):
        l1 = " ".join(words[:i])
        l2 = " ".join(words[i:])
        score = abs(len(l1) - len(l2))
        if len(l1) <= max_chars and len(l2) <= max_chars and score < best_score:
            best_score = score
            best_i = i

    if best_i is None:
        # fallback: split by word count
        mid = len(words) // 2
        return " ".join(words[:mid]), " ".join(words[mid:])

    return " ".join(words[:best_i]), " ".join(words[best_i:])


def build_captions_from_script(
    script: str,
    *,
    words_per_second: float = 2.2,
    min_segment_s: float = 1.2,
    max_segment_s: float = 2.6,
    max_chars_per_line: int = 34,
) -> List[Caption]:
    """
    Make captions that are:
    - 1–3 seconds each
    - max two lines
    - NOT single-word spam
    """
    phrases = _split_phrases(script)

    # If the script is already short lines, preserve them as phrases
    if not phrases:
        return []

    captions: List[Caption] = []
    t = 0.0

    for phrase in phrases:
        wc = max(1, len(phrase.split()))
        dur = wc / max(0.1, words_per_second)
        dur = max(min_segment_s, min(max_segment_s, dur))

        l1, l2 = _wrap_two_lines(phrase, max_chars=max_chars_per_line)
        captions.append(Caption(start_s=t, end_s=t + dur, line1=l1, line2=l2))
        t += dur

    return captions


def _ass_time(seconds: float) -> str:
    # ASS time format: H:MM:SS.cs (centiseconds)
    if seconds < 0:
        seconds = 0.0
    cs = int(round((seconds - int(seconds)) * 100))
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = int(seconds) // 3600
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def write_ass(
    captions: List[Caption],
    out_path: str | Path,
    *,
    play_res_x: int = 1080,
    play_res_y: int = 1920,
    panel_top_y: int = 1152,   # top of caption panel (for 40% panel on 1920h)
    panel_height: int = 768,
) -> str:
    """
    Writes an .ass subtitle file with a fixed lower-third layout.
    Captions are centered horizontally and positioned inside the panel.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Place captions comfortably inside the panel (not hugging bottom)
    # ASS "MarginV" is distance from bottom when Alignment=2 (bottom-center)
    margin_v = int(panel_height * 0.28)  # about 28% up from panel bottom

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Inter,54,&H00FFFFFF,&H00101010,&H64000000,0,0,0,0,100,100,0,0,3,2,0,2,80,80,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]

    # Gentle fade in/out (in ms) using ASS \fad
    fad_in = 120
    fad_out = 160

    for c in captions:
        start = _ass_time(c.start_s)
        end = _ass_time(c.end_s)

        text = c.line1
        if c.line2:
            text = f"{c.line1}\\N{c.line2}"

        # Keep it clean: no per-word styling; just smooth fade.
        # \fad(a,b) uses milliseconds.
        dialogue = f"Dialogue: 0,{start},{end},Caption,,0,0,0,,{{\\fad({fad_in},{fad_out})}}{text}\n"
        lines.append(dialogue)

    out_path.write_text("".join(lines), encoding="utf-8")
    return str(out_path)