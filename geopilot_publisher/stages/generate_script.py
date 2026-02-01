from openai import OpenAI
import os

def generate_script(idea: dict) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    client = OpenAI(api_key=api_key)

    prompt = f"""
Write a 45–60 second YouTube Shorts script in a calm, analytical voice.

Idea:
Hook: {idea.get('hook')}
Premise: {idea.get('premise')}
Takeaway: {idea.get('takeaway')}

Rules:
- Short sentences.
- Natural pauses.
- No hype words.
- No emojis.
- End with a strong final line.
Return plain text only.
""".strip()

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
    )

    return resp.choices[0].message.content.strip()