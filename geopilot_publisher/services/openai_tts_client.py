import os
from pathlib import Path
from openai import OpenAI


def tts_to_mp3(
    text: str,
    out_path: str = "artifacts/voice.mp3",
    model: str = "gpt-4o-mini-tts",
    voice: str = "marin",
) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    client = OpenAI(api_key=api_key)

    # NOTE: It's `response_format`, not `format`
    audio = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        response_format="mp3",
    )

    # openai-python returns binary audio content
    with open(out_path, "wb") as f:
        f.write(audio.read() if hasattr(audio, "read") else audio)

    return out_path