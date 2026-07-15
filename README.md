# VoiceScribe AI

Self-hosted voice/video/text transcription and meeting-intelligence platform.
Backend: FastAPI (modular `app/` + `services/`). Frontend: React + TypeScript (Vite).

## Backend setup
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp _env.example .env          # fill in HUGGINGFACE_TOKEN
uvicorn backend.app.main:app --reload --port 8000
```

## Frontend setup
```bash
cd frontend
npm install
cp .env.example .env          # set VITE_BACKEND_URL if needed
npm run dev
```
Open http://127.0.0.1:5173

## Notes
- Ollama must be running locally with `qwen3:8b` pulled (`ollama pull qwen3:8b`).
- `pyannote.audio` requires a Hugging Face token with diarization model access.
- Long recordings (> LONG_RECORDING_THRESHOLD seconds) route through the async job/polling path (Meeting Mode); short ones process synchronously (Quick Capture).
