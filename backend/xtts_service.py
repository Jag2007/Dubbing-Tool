from pathlib import Path
import os
import subprocess
import tempfile


BASE_DIR = Path(__file__).resolve().parent
REFERENCE_VOICE_PATH = BASE_DIR / "my_voice.wav"
XTTS_VENV_PYTHON = BASE_DIR / ".xtts-venv" / "bin" / "python"
XTTS_RUNNER_PATH = BASE_DIR / "xtts_runner.py"
XTTS_LANGUAGE_MAP = {
    "en": "en",
    "fr": "fr",
    "es": "es",
    "hi": "en",
    "te": "en",
    "kn": "en",
}


def generate_jagruthi_voice(text: str, target_language: str, output_path: str) -> None:
    xtts_language = XTTS_LANGUAGE_MAP.get(target_language, "en")

    if not REFERENCE_VOICE_PATH.exists():
        raise ValueError("Missing backend/my_voice.wav for Jagruthi's local voice.")

    if not XTTS_VENV_PYTHON.exists():
        raise RuntimeError(
            "Local XTTS is not installed yet. Create backend/.xtts-venv with Python 3.10 "
            "and install backend/xtts_requirements.txt."
        )

    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as text_file:
        text_file.write(text)
        text_file_path = text_file.name

    try:
        subprocess.run(
            [
                str(XTTS_VENV_PYTHON),
                str(XTTS_RUNNER_PATH),
                "--text-file",
                text_file_path,
                "--speaker-wav",
                str(REFERENCE_VOICE_PATH),
                "--language",
                xtts_language,
                "--output",
                output_path,
            ],
            check=True,
            capture_output=True,
            env={**os.environ, "COQUI_TOS_AGREED": "1"},
            text=True,
            timeout=300,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr or exc.stdout or "Local XTTS generation failed.") from exc
    finally:
        Path(text_file_path).unlink(missing_ok=True)
