from functools import lru_cache

import whisper


@lru_cache(maxsize=1)
def get_model():
    return whisper.load_model("base")


def transcribe_audio(file_path: str) -> str:
    model = get_model()
    result = model.transcribe(file_path, fp16=False)
    transcript = result.get("text", "").strip()

    if not transcript:
        raise ValueError("Whisper could not detect any speech in the uploaded audio.")

    return transcript
