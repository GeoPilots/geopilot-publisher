from geopilot_publisher.services.openai_tts_client import tts_to_mp3


def synthesize_voice(script: str) -> str:
    # Keep this deterministic for CI: always write artifacts/voice.mp3
    return tts_to_mp3(
        text=script,
        out_path="artifacts/voice.mp3",
        model="gpt-4o-mini-tts",
        voice="marin",
    )