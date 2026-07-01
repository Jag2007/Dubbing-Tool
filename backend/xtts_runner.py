import argparse
from pathlib import Path

import torch
from TTS.api import TTS


XTTS_MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-file", required=True)
    parser.add_argument("--speaker-wav", required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    text = Path(args.text_file).read_text(encoding="utf-8")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tts = TTS(XTTS_MODEL_NAME).to(device)
    tts.tts_to_file(
        text=text,
        speaker_wav=args.speaker_wav,
        language=args.language,
        file_path=args.output,
    )


if __name__ == "__main__":
    main()
