from pathlib import Path
from pydantic_settings import BaseSettings

# backend/app/core/config.py -> repo root is 3 levels up (core -> app -> backend -> root)
REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    WHISPER_MODEL: str = "base"
    DIARIZATION_MODEL: str = "pyannote/speaker-diarization"
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024
    SUPPORTED_FORMATS: str = "webm,mp3,wav,m4a,mp4,mov,avi,mkv"
    LONG_RECORDING_THRESHOLD: int = 600
    CHUNK_LENGTH: int = 300
    HISTORY_LIMIT: int = 5
    LANGUAGE_MODE: str = "automatic"
    LLM_MODEL: str = "qwen3:8b"
    LLM_THINKING_MODE_TASKS: str = "summarize,action_items,ask"
    LLM_CONTEXT_MODE: str = "native"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    RAG_TOP_K: int = 5
    BACKEND_URL: str = "http://127.0.0.1:8000"
    FRONTEND_ORIGIN: str = "http://127.0.0.1:5173"

    STORAGE_DIR: Path = REPO_ROOT / "storage"
    VECTOR_DIR: Path = REPO_ROOT / "vector_store"
    HISTORY_FILE: Path = REPO_ROOT / "storage" / "history.json"
    UPLOAD_DIR: Path = REPO_ROOT / "storage" / "uploads"
    REPORT_DIR: Path = REPO_ROOT / "storage" / "reports"
    TRANSCRIPT_DIR: Path = REPO_ROOT / "storage" / "transcripts"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
