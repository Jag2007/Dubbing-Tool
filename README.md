# AI Dubbing Tool MVP

A simple interview-friendly AI dubbing application. The user uploads an English audio file, the backend transcribes it with local Whisper, translates the transcript, and generates a dubbed MP3 using an ElevenLabs voice.

## Architecture

```text
User uploads English audio
        |
        v
React frontend
        |
        v
FastAPI backend
        |
        v
Local Whisper speech-to-text
        |
        v
English transcript
        |
        v
Local NLLB-200 translation
        |
        v
Translated text
        |
        v
ElevenLabs Text-to-Speech
        |
        v
Dubbed audio output
```

## Tech Stack

- Frontend: React + Vite
- Backend: FastAPI
- Transcription: local Whisper base model through `openai-whisper`
- Translation: local NLLB-200 distilled 600M through Hugging Face Transformers
- Voice generation: ElevenLabs Text-to-Speech API
- Original delivery preservation: ElevenLabs Dubbing API
- Storage: local `backend/uploads/` and `backend/outputs/`

## Supported Languages

The demo supports:

- Hindi
- Telugu
- Kannada
- French
- Spanish

NLLB-200 distilled 600M is used locally because it supports all five required target languages without a paid translation API. The first run downloads the model from Hugging Face, then subsequent runs use the local cache.

## Project Structure

```text
.
├── backend
│   ├── main.py
│   ├── whisper_service.py
│   ├── translation_service.py
│   ├── elevenlabs_service.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── uploads
│   └── outputs
├── frontend
│   ├── package.json
│   ├── index.html
│   └── src
│       ├── App.jsx
│       ├── main.jsx
│       └── styles.css
└── README.md
```

## Environment Variables

Create `backend/.env` from `backend/.env.example`:

```env
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
FRONTEND_ORIGIN=http://localhost:5173
```

You also need `ffmpeg` installed locally because Whisper uses it to read audio files.

On macOS:

```bash
brew install ffmpeg
```

## Run Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs at:

```text
http://localhost:8000
```

Useful endpoints:

- `GET /languages`
- `GET /voices`
- `POST /dub`
- `GET /outputs/{filename}`

## Run Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

## How It Works

1. The React frontend loads supported languages from the backend.
2. The frontend fetches ElevenLabs voices from `GET /voices`.
3. The user uploads an English audio file.
4. The user selects a target language and ElevenLabs voice.
5. The frontend sends `FormData` to `POST /dub`.
6. FastAPI saves the upload in `backend/uploads/`.
7. Whisper transcribes the audio locally.
8. NLLB-200 translates the transcript locally.
9. ElevenLabs generates dubbed audio from the translated text, or uses Dubbing mode to preserve the source speaker's delivery.
10. FastAPI saves the MP3 in `backend/outputs/`.
11. The frontend displays transcript, translation, audio player, and download link.

## Delivery Modes

- `Use selected voice`: the translated text is rendered with a chosen ElevenLabs voice. This mode supports extra modulation presets: Natural, Expressive, Steady, and Dramatic.
- `Preserve original delivery`: the source audio/video is sent to ElevenLabs Dubbing so the output can retain more of the original speaker's pacing, emotion, and vocal delivery. This mode depends on ElevenLabs Dubbing availability for the account.

## Interview Explanation

This project demonstrates a clean end-to-end AI media pipeline. The frontend handles upload, language selection, delivery mode selection, voice selection, loading states, errors, and playback. The backend keeps each AI responsibility separated into small service modules: Whisper for speech-to-text, NLLB-200 for local multilingual translation, and ElevenLabs for voice generation or original delivery preservation.

The MVP intentionally avoids authentication, databases, cloud storage, and background workers so the core AI workflow stays easy to understand and demo. Uploaded files and generated MP3s are stored locally.

This version supports both ElevenLabs prebuilt voices and a preserve-original-delivery mode. For production-level speaker identity preservation, this can be extended further with dedicated voice cloning, speaker diarization, and segment-level timing alignment.

## Demo Notes

- Use a short English audio clip for the interview demo.
- The first Whisper/NLLB run can take longer because local models need to load and may download once.
- NLLB local translation avoids paid translation APIs, but API-based translators may be faster in production.
- ElevenLabs output quality depends on the selected voice and language.
- Keep API keys private and do not commit `backend/.env`.
