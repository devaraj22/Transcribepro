"""
Shared pytest fixtures for VoiceScribe AI test suite.

Provides a FastAPI TestClient, temporary storage directories,
mock audio files, and patched external services (Whisper, Pyannote, Ollama, FFmpeg).
"""

import json
import shutil
import struct
import wave
from io import BytesIO
from pathlib import Path
from typing import Dict, List
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_STORAGE = REPO_ROOT / "tests" / "_test_storage"
TEST_VECTOR_STORE = REPO_ROOT / "tests" / "_test_vector_store"


# ---------------------------------------------------------------------------
# WAV generators (in-memory, no real audio needed)
# ---------------------------------------------------------------------------
def _make_wav_bytes(duration_seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Generate a silent WAV file in memory."""
    n_samples = int(sample_rate * duration_seconds)
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{n_samples}h", *([0] * n_samples)))
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Mock segment / diarization data
# ---------------------------------------------------------------------------
def _mock_segments(count: int = 3):
    """Return a list of mock Segment-like objects."""
    from backend.app.schemas.process import Segment
    return [
        Segment(start=i * 10.0, end=(i + 1) * 10.0 - 0.1, text=f"Segment {i} text.", language="en")
        for i in range(count)
    ]


def _mock_diarization(count: int = 3) -> List[Dict]:
    """Return mock speaker-turn dicts that align with _mock_segments."""
    speakers = ["SPEAKER_00", "SPEAKER_01"]
    return [
        {"start": i * 10.0, "end": (i + 1) * 10.0, "speaker": speakers[i % 2]}
        for i in range(count)
    ]


# ---------------------------------------------------------------------------
# Fixtures — settings override
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _override_settings(tmp_path):
    """Redirect all storage to a temporary directory so tests are isolated."""
    from backend.app.core.config import settings

    original_storage = settings.STORAGE_DIR
    original_vector = settings.VECTOR_DIR
    original_history = settings.HISTORY_FILE
    original_upload = settings.UPLOAD_DIR
    original_report = settings.REPORT_DIR
    original_transcript = settings.TRANSCRIPT_DIR

    settings.STORAGE_DIR = tmp_path / "storage"
    settings.VECTOR_DIR = tmp_path / "vector_store"
    settings.HISTORY_FILE = tmp_path / "storage" / "history.json"
    settings.UPLOAD_DIR = tmp_path / "storage" / "uploads"
    settings.REPORT_DIR = tmp_path / "storage" / "reports"
    settings.TRANSCRIPT_DIR = tmp_path / "storage" / "transcripts"

    # Create dirs
    for p in [settings.STORAGE_DIR, settings.VECTOR_DIR, settings.UPLOAD_DIR, settings.REPORT_DIR, settings.TRANSCRIPT_DIR]:
        p.mkdir(parents=True, exist_ok=True)

    yield

    # Restore
    settings.STORAGE_DIR = original_storage
    settings.VECTOR_DIR = original_vector
    settings.HISTORY_FILE = original_history
    settings.UPLOAD_DIR = original_upload
    settings.REPORT_DIR = original_report
    settings.TRANSCRIPT_DIR = original_transcript


# ---------------------------------------------------------------------------
# Fixtures — TestClient
# ---------------------------------------------------------------------------
@pytest.fixture()
def client():
    """FastAPI TestClient with the real app."""
    from backend.app.main import app
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Fixtures — WAV file bytes
# ---------------------------------------------------------------------------
@pytest.fixture()
def short_wav_bytes():
    """In-memory WAV bytes for a 1-second silent clip."""
    return _make_wav_bytes(duration_seconds=1.0)


@pytest.fixture()
def long_wav_bytes():
    """In-memory WAV bytes that represents a >600s recording (used with mocked duration)."""
    return _make_wav_bytes(duration_seconds=1.0)  # actual bytes are short; duration is mocked


# ---------------------------------------------------------------------------
# Fixtures — mock patches
# ---------------------------------------------------------------------------
@pytest.fixture()
def mock_ffmpeg():
    """Patch ffmpeg service: probe_duration returns 30s, prepare_audio_file is a no-op."""
    with patch("backend.services.ffmpeg_service.probe_duration", return_value=30.0) as m_dur, \
         patch("backend.services.ffmpeg_service.prepare_audio_file", side_effect=lambda p: p) as m_prep, \
         patch("backend.services.ffmpeg_service.extract_audio", side_effect=lambda inp, out: out) as m_extract:
        yield {"probe_duration": m_dur, "prepare_audio_file": m_prep, "extract_audio": m_extract}


@pytest.fixture()
def mock_ffmpeg_long():
    """Patch ffmpeg service: probe_duration returns 700s (> LONG_RECORDING_THRESHOLD)."""
    with patch("backend.services.ffmpeg_service.probe_duration", return_value=700.0) as m_dur, \
         patch("backend.services.ffmpeg_service.prepare_audio_file", side_effect=lambda p: p) as m_prep:
        yield {"probe_duration": m_dur, "prepare_audio_file": m_prep}


@pytest.fixture()
def mock_whisper():
    """Patch Whisper transcription to return canned segments."""
    segments = _mock_segments(3)
    with patch("backend.services.whisper_service.transcribe_segments", return_value=segments) as m:
        yield m


@pytest.fixture()
def mock_pyannote():
    """Patch pyannote diarization to return canned speaker turns."""
    turns = _mock_diarization(3)
    with patch("backend.services.pyannote_service.diarize_audio", return_value=turns) as m:
        yield m


@pytest.fixture()
def mock_ollama():
    """Patch Ollama LLM service for completion and embedding."""
    with patch("ollama.generate", return_value={"response": "Mocked LLM response."}) as m_gen, \
         patch("ollama.embeddings", return_value={"embedding": [0.1] * 768}) as m_emb:
        yield {"llm_complete": m_gen, "llm_embed": m_emb}


@pytest.fixture()
def mock_all_services(mock_ffmpeg, mock_whisper, mock_pyannote, mock_ollama):
    """Convenience fixture that patches all external services at once."""
    return {
        "ffmpeg": mock_ffmpeg,
        "whisper": mock_whisper,
        "pyannote": mock_pyannote,
        "ollama": mock_ollama,
    }


# ---------------------------------------------------------------------------
# Fixtures — helpers
# ---------------------------------------------------------------------------
@pytest.fixture()
def upload_short_wav(client, short_wav_bytes, mock_all_services):
    """Upload a short WAV file and return the response."""
    resp = client.post(
        "/process",
        files={"upload_file": ("test_short.wav", BytesIO(short_wav_bytes), "audio/wav")},
        data={"language_mode": "automatic"},
    )
    return resp


@pytest.fixture()
def seeded_history(tmp_path):
    """Write a pre-populated history.json with 3 entries."""
    from backend.app.core.config import settings

    entries = [
        {
            "id": f"hist-{i}",
            "timestamp": f"2026-07-{10 + i}T00:00:00+00:00",
            "title": f"Meeting {i}",
            "duration_seconds": 120.0 + i * 60,
            "languages": ["en"],
            "transcript": f"Speaker 1: Hello from meeting {i}",
            "segments": [],
            "job_id": f"job-{i}" if i > 0 else None,
        }
        for i in range(3)
    ]
    settings.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    settings.HISTORY_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    return entries
