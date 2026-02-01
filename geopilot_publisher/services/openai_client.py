import os
from pathlib import Path
from openai import OpenAI


def tts_to_mp3(
    *,
    text: str,
    out_path: str = "artifacts/voice.mp3",
    model: str = "gpt-4o-mini-tts",
    voice: str = "marin",
) -> str:
    """
    Generate speech from text using OpenAI Audio TTS and save as MP3.

    Models for /v1/audio/speech: gpt-4o-mini-tts, tts-1, tts-1-hd.
    Voices include: alloy, ash, ballad, coral, echo, fable, nova, onyx,
    sage, shimmer, verse, marin, cedar. (Docs recommend marin/cedar.)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    client = OpenAI(api_key=api_key)

    # OpenAI Audio API: POST /v1/audio/speech
    audio = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        format="mp3",
    )

    # SDK returns binary audio; write to file
    with open(out_path, "wb") as f:
        f.write(audio.read() if hasattr(audio, "read") else audio)

    return out_path