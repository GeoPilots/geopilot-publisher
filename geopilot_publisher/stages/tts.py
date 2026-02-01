from geopilot_publisher.services.openai_tts_client import tts_to_mp3

def synthesize_voice(script: str) -> str:
    return tts_to_mp3(script, "artifacts/voice.mp3")