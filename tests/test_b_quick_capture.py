"""
Module B — Quick Capture Processing (Short recordings, synchronous)
TC-B01 to TC-B06
"""

from io import BytesIO
from unittest.mock import patch

import pytest

from tests.conftest import _make_wav_bytes


class TestQuickCaptureSync:
    """Tests for the synchronous quick-capture processing path."""

    def test_b01_short_audio_processed_synchronously(self, client, short_wav_bytes, mock_all_services):
        """TC-B01: Short audio file (< 600s) returns immediately with status=complete."""
        response = client.post(
            "/process",
            files={"upload_file": ("test_short.wav", BytesIO(short_wav_bytes), "audio/wav")},
            data={"language_mode": "automatic"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "complete"
        assert body["job_id"] is None
        assert body["detail"] == "Processed successfully."

    def test_b02_short_audio_manual_language(self, client, short_wav_bytes, mock_all_services):
        """TC-B02: Short audio with manual language mode passes language to whisper."""
        response = client.post(
            "/process",
            files={"upload_file": ("test_short.wav", BytesIO(short_wav_bytes), "audio/wav")},
            data={"language_mode": "manual", "manual_language": "en"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "complete"
        # Verify that whisper was called with the manual language
        mock_all_services["whisper"].assert_called_once()
        call_args = mock_all_services["whisper"].call_args
        assert call_args[0][1] == "en"  # second positional arg is manual_language

    def test_b03_video_file_triggers_audio_extraction(self, client, short_wav_bytes, mock_all_services):
        """TC-B03: Video file (.mp4) triggers prepare_audio_file which calls extract_audio."""
        response = client.post(
            "/process",
            files={"upload_file": ("test_video.mp4", BytesIO(short_wav_bytes), "video/mp4")},
            data={"language_mode": "automatic"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "complete"
        # prepare_audio_file should have been called
        mock_all_services["ffmpeg"]["prepare_audio_file"].assert_called()

    def test_b04_multi_speaker_diarization(self, client, short_wav_bytes, mock_all_services):
        """TC-B04: Multi-speaker audio produces diarized segments with distinct speaker labels."""
        response = client.post(
            "/process",
            files={"upload_file": ("multi_speaker.wav", BytesIO(short_wav_bytes), "audio/wav")},
            data={"language_mode": "automatic"},
        )
        assert response.status_code == 200
        # Verify pyannote diarization was invoked
        mock_all_services["pyannote"].assert_called_once()

    def test_b05_submit_without_file_returns_422(self, client):
        """TC-B05: POST /process without upload_file returns 422 validation error."""
        response = client.post("/process", data={"language_mode": "automatic"})
        assert response.status_code == 422

    def test_b06_unsupported_file_extension_rejected(self, client):
        """TC-B06: Upload file with unsupported extension returns 400."""
        response = client.post(
            "/process",
            files={"upload_file": ("test.xyz", BytesIO(b"not real audio"), "application/octet-stream")},
            data={"language_mode": "automatic"},
        )
        assert response.status_code == 400
        assert "Unsupported file extension" in response.json()["detail"]


class TestQuickCaptureHistoryWritten:
    """Verify that quick-capture processing writes to history."""

    def test_history_entry_created_after_quick_capture(self, client, short_wav_bytes, mock_all_services, tmp_path):
        """After quick-capture, history.json should contain a new entry with job_id=None."""
        from backend.app.core.config import settings

        client.post(
            "/process",
            files={"upload_file": ("test.wav", BytesIO(short_wav_bytes), "audio/wav")},
            data={"language_mode": "automatic"},
        )

        import json
        history = json.loads(settings.HISTORY_FILE.read_text(encoding="utf-8"))
        assert len(history) >= 1
        latest = history[0]
        assert latest["job_id"] is None
        assert latest["transcript"]  # non-empty transcript
        assert "duration_seconds" in latest


class TestQuickCaptureVectorIndex:
    """Verify that quick-capture processing builds a FAISS index."""

    def test_faiss_index_created_after_quick_capture(self, client, short_wav_bytes, mock_all_services, tmp_path):
        """After quick-capture, vector_store/inline/ should contain index.faiss."""
        from backend.app.core.config import settings

        client.post(
            "/process",
            files={"upload_file": ("test.wav", BytesIO(short_wav_bytes), "audio/wav")},
            data={"language_mode": "automatic"},
        )

        inline_dir = settings.VECTOR_DIR / "inline"
        assert inline_dir.exists()
        assert (inline_dir / "index.faiss").exists()
        assert (inline_dir / "metadata.json").exists()
