import json
from openai import OpenAI
import os

def generate_ideas() -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    client = OpenAI(api_key=api_key)

    prompt = (
        "Generate ONE strong YouTube Shorts idea about AI.\n"
        "Return JSON ONLY with keys: hook, premise, takeaway.\n"
        "Tone: calm, analytical. No hype. 1 idea only."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    text = resp.choices[0].message.content.strip()
    return json.loads(text)