import json
import os
from pathlib import Path
from openai import OpenAI


def generate_ideas() -> dict:
    """
    Generate ONE AI Shorts idea and return a dict with keys:
      hook, premise, takeaway

    This is CI-safe:
    - Forces JSON output via response_format
    - Writes raw model output to artifacts/idea_raw.txt for debugging
    - Falls back to a safe default if parsing fails
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)

    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    prompt = (
        "Generate ONE strong YouTube Shorts idea about AI.\n"
        "Return JSON only with keys: hook, premise, takeaway.\n"
        "No hype. Calm, analytical. Values must be strings.\n"
    )

    # Force JSON output (prevents the exact failure you hit)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    text = (resp.choices[0].message.content or "").strip()

    # Always save raw output for debugging
    (artifacts_dir / "idea_raw.txt").write_text(text, encoding="utf-8")

    # Parse JSON safely
    try:
        data = json.loads(text) if text else {}
    except json.JSONDecodeError:
        data = {}

    # Validate and normalize output
    hook = str(data.get("hook", "")).strip()
    premise = str(data.get("premise", "")).strip()
    takeaway = str(data.get("takeaway", "")).strip()

    # Hard fallback so pipeline never dies here
    if not hook or not premise or not takeaway:
        return {
            "hook": "AI isn’t replacing jobs—it's replacing tasks.",
            "premise": "The real change is job compression: more output per person, fewer repetitive responsibilities.",
            "takeaway": "The advantage isn’t learning every tool—it's learning how to think in workflows.",
        }

    return {"hook": hook, "premise": premise, "takeaway": takeaway}