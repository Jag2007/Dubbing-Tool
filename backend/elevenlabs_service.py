import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"

MODULATION_PRESETS = {
    "natural": {
        "label": "Natural",
        "settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0},
    },
    "expressive": {
        "label": "Expressive",
        "settings": {"stability": 0.35, "similarity_boost": 0.8, "style": 0.35},
    },
    "steady": {
        "label": "Steady",
        "settings": {"stability": 0.75, "similarity_boost": 0.7, "style": 0.0},
    },
    "dramatic": {
        "label": "Dramatic",
        "settings": {"stability": 0.25, "similarity_boost": 0.85, "style": 0.55},
    },
}


def _api_key() -> str:
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        raise ValueError("ELEVENLABS_API_KEY is missing. Add it to backend/.env.")
    return key


def get_voices() -> list[dict[str, str]]:
    response = requests.get(
        f"{ELEVENLABS_API_BASE}/voices",
        headers={"xi-api-key": _api_key()},
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"ElevenLabs voices fetch failed with {response.status_code}: {response.text}"
        )

    voices = response.json().get("voices", [])
    api_ready_voices = [
        voice
        for voice in voices
        if voice.get("category") in {"premade", "cloned", "generated"}
    ]

    if not api_ready_voices:
        api_ready_voices = voices

    clean_voices = [
        {
            "voice_id": voice.get("voice_id"),
            "name": voice.get("name"),
            "category": voice.get("category", "unknown"),
        }
        for voice in api_ready_voices
        if voice.get("voice_id") and voice.get("name")
    ]

    if not clean_voices:
        raise RuntimeError("ElevenLabs returned no usable voices.")

    return clean_voices


def get_modulation_presets() -> list[dict[str, str]]:
    return [
        {"code": code, "name": preset["label"]}
        for code, preset in MODULATION_PRESETS.items()
    ]


def generate_speech(
    text: str,
    voice_id: str,
    output_path: str,
    modulation_preset: str = "natural",
) -> None:
    if not voice_id:
        raise ValueError("No ElevenLabs voice selected.")

    model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
    preset = MODULATION_PRESETS.get(modulation_preset, MODULATION_PRESETS["natural"])
    voice_settings = {
        **preset["settings"],
        "use_speaker_boost": True,
    }

    response = requests.post(
        f"{ELEVENLABS_API_BASE}/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": _api_key(),
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        json={
            "text": text,
            "model_id": model_id,
            "voice_settings": voice_settings,
        },
        timeout=60,
    )

    if not response.ok:
        if response.status_code == 402:
            raise RuntimeError(
                "ElevenLabs rejected this voice because it requires a paid plan. "
                "Choose one of the default prebuilt voices for the demo."
            )

        raise RuntimeError(
            f"ElevenLabs TTS failed with {response.status_code}: {response.text}"
        )

    with open(output_path, "wb") as audio_file:
        audio_file.write(response.content)


def generate_dubbed_audio(
    source_path: str,
    target_lang: str,
    output_path: str,
    poll_interval_seconds: int = 5,
    max_wait_seconds: int = 300,
) -> None:
    with open(source_path, "rb") as media_file:
        create_response = requests.post(
            f"{ELEVENLABS_API_BASE}/dubbing",
            headers={"xi-api-key": _api_key()},
            data={
                "source_lang": "en",
                "target_lang": target_lang,
                "num_speakers": "1",
                "watermark": "false",
                "drop_background_audio": "true",
            },
            files={"file": media_file},
            timeout=120,
        )

    if not create_response.ok:
        raise RuntimeError(
            f"ElevenLabs Dubbing failed to start with {create_response.status_code}: "
            f"{create_response.text}"
        )

    dubbing_id = create_response.json().get("dubbing_id")
    if not dubbing_id:
        raise RuntimeError("ElevenLabs Dubbing did not return a dubbing_id.")

    deadline = time.time() + max_wait_seconds
    status = "unknown"

    while time.time() < deadline:
        status_response = requests.get(
            f"{ELEVENLABS_API_BASE}/dubbing/{dubbing_id}",
            headers={"xi-api-key": _api_key()},
            timeout=30,
        )

        if not status_response.ok:
            raise RuntimeError(
                f"ElevenLabs Dubbing status failed with {status_response.status_code}: "
                f"{status_response.text}"
            )

        status_data = status_response.json()
        status = status_data.get("status", "unknown")

        if status == "dubbed":
            break

        if status in {"failed", "error"}:
            raise RuntimeError(f"ElevenLabs Dubbing failed: {status_data}")

        time.sleep(poll_interval_seconds)
    else:
        raise RuntimeError(
            "ElevenLabs Dubbing is still processing. Try a shorter clip or retry shortly."
        )

    audio_response = requests.get(
        f"{ELEVENLABS_API_BASE}/dubbing/{dubbing_id}/audio/{target_lang}",
        headers={"xi-api-key": _api_key(), "Accept": "audio/mpeg"},
        timeout=120,
    )

    if not audio_response.ok:
        raise RuntimeError(
            f"ElevenLabs Dubbing audio download failed with {audio_response.status_code}: "
            f"{audio_response.text}"
        )

    with open(output_path, "wb") as audio_file:
        audio_file.write(audio_response.content)
