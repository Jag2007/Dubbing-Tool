import shutil
import uuid
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from elevenlabs_service import (
    generate_dubbed_audio,
    generate_speech,
    get_modulation_presets,
    get_voices,
)
from translation_service import get_supported_languages, translate_text
from whisper_service import transcribe_audio
from xtts_service import generate_jagruthi_voice

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"
UPLOADS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="AI Dubbing Tool API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "AI Dubbing Tool API"}


@app.get("/languages")
def languages():
    return get_supported_languages()


@app.get("/voices")
def voices():
    try:
        return get_voices()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/modulation-presets")
def modulation_presets():
    return get_modulation_presets()


def resolve_voice_id(voice_id: str) -> str:
    if voice_id:
        return voice_id

    voices = get_voices()
    fallback_voice_id = voices[0].get("voice_id") if voices else ""
    if not fallback_voice_id:
        raise ValueError("No ElevenLabs voice is available for fallback speech.")

    return fallback_voice_id


@app.post("/dub")
def dub_audio(
    audio_file: UploadFile = File(...),
    target_language: str = Form(...),
    voice_id: str = Form(""),
    delivery_mode: str = Form("selected_voice"),
    modulation_preset: str = Form("natural"),
):
    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="Please upload an audio file.")

    if delivery_mode not in {"selected_voice", "preserve_original", "jagruthi_voice"}:
        raise HTTPException(status_code=400, detail="Unsupported delivery mode selected.")

    if delivery_mode == "selected_voice" and not voice_id:
        raise HTTPException(status_code=400, detail="Please select an ElevenLabs voice.")

    upload_suffix = Path(audio_file.filename).suffix or ".audio"
    upload_filename = f"{uuid.uuid4()}{upload_suffix}"
    output_filename = f"dubbed-{uuid.uuid4()}.mp3"

    upload_path = UPLOADS_DIR / upload_filename
    output_path = OUTPUTS_DIR / output_filename

    try:
        with open(upload_path, "wb") as saved_file:
            shutil.copyfileobj(audio_file.file, saved_file)

        started_at = time.perf_counter()
        transcript = transcribe_audio(str(upload_path))
        transcribed_at = time.perf_counter()
        translated_text = translate_text(transcript, target_language)
        translated_at = time.perf_counter()
        if delivery_mode == "jagruthi_voice":
            voice_id = "jagruthi_voice"
            generate_jagruthi_voice(translated_text, target_language, str(output_path))
        elif delivery_mode == "preserve_original":
            try:
                generate_dubbed_audio(str(upload_path), target_language, str(output_path))
            except RuntimeError as exc:
                message = str(exc)
                can_fallback_to_voice = (
                    "subscription_required" in message
                    or "watermark_not_allowed" in message
                    or "Dubbing failed to start with 400" in message
                )

                if not can_fallback_to_voice:
                    raise

                voice_id = resolve_voice_id(voice_id)
                delivery_mode = "selected_voice"
                generate_speech(translated_text, voice_id, str(output_path), modulation_preset)
        else:
            generate_speech(translated_text, voice_id, str(output_path), modulation_preset)
        finished_at = time.perf_counter()

        timings = {
            "transcription_seconds": round(transcribed_at - started_at, 2),
            "translation_seconds": round(translated_at - transcribed_at, 2),
            "voice_generation_seconds": round(finished_at - translated_at, 2),
            "total_seconds": round(finished_at - started_at, 2),
        }

        return {
            "original_transcript": transcript,
            "translated_text": translated_text,
            "selected_language": target_language,
            "selected_voice_id": voice_id,
            "delivery_mode": delivery_mode,
            "modulation_preset": modulation_preset,
            "output_audio_url": f"/outputs/{output_filename}",
            "timings": timings,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        audio_file.file.close()


@app.get("/outputs/{filename}")
def serve_output(filename: str):
    output_path = OUTPUTS_DIR / filename

    if not output_path.exists() or output_path.parent != OUTPUTS_DIR:
        raise HTTPException(status_code=404, detail="Output audio file not found.")

    return FileResponse(
        output_path,
        media_type="audio/mpeg",
        filename=filename,
    )
