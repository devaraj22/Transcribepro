"""
Module K — Error Handling & Edge Cases
TC-K01 to TC-K05
"""

from io import BytesIO
from unittest.mock import patch

import pytest

from tests.conftest import _make_wav_bytes


class TestCorruptFiles:
    """TC-K01: Corrupt audio file handling."""

    def test_k01_corrupt_audio_returns_meaningful_error(self, client, mock_ffmpeg, mock_pyannote, mock_ollama):
        """TC-K01: Uploading a corrupt file results in a meaningful error, not 500."""
        # Mock whisper to raise a transcription error
        from backend.app.core.exceptions import TranscriptionError

        with patch(
            "backend.services.whisper_service.transcribe_segments",
            side_effect=TranscriptionError("Could not decode audio data"),
        ):
            response = client.post(
                "/process",
                files={"upload_file": ("corrupt.wav", BytesIO(b"not valid wav data"), "audio/wav")},
                data={"language_mode": "automatic"},
            )
        assert response.status_code == 422
        assert "Transcription failed" in response.json()["detail"]


class TestOllamaDown:
    """TC-K02: Ollama service unavailability."""

    def test_k02_process_with_ollama_down_for_embeddings(self, client, mock_ffmpeg, mock_whisper, mock_pyannote):
        """TC-K02: When Ollama is down, FAISS indexing (embeddings) fails with LLMServiceError."""
        from backend.app.core.exceptions import LLMServiceError

        with patch(
            "backend.services.ollama_service.llm_embed",
            side_effect=LLMServiceError("Connection refused"),
        ):
            response = client.post(
                "/process",
                files={"upload_file": ("test.wav", BytesIO(_make_wav_bytes()), "audio/wav")},
                data={"language_mode": "automatic"},
            )
        # Should return 502 for LLM service failure
        assert response.status_code == 502
        assert "LLM service failed" in response.json()["detail"]


class TestDiarizationFailure:
    """Diarization service failures."""

    def test_diarization_error_returns_422(self, client, mock_ffmpeg, mock_whisper, mock_ollama):
        """When diarization fails, the endpoint returns 422."""
        from backend.app.core.exceptions import DiarizationError

        with patch(
            "backend.services.pyannote_service.diarize_audio",
            side_effect=DiarizationError("Model failed to load"),
        ):
            response = client.post(
                "/process",
                files={"upload_file": ("test.wav", BytesIO(_make_wav_bytes()), "audio/wav")},
                data={"language_mode": "automatic"},
            )
        assert response.status_code == 422
        assert "Diarization failed" in response.json()["detail"]


class TestEdgeCases:
    """TC-K03 to TC-K05: Various edge cases."""

    def test_k03_silent_audio_produces_minimal_transcript(self, client, mock_ffmpeg, mock_pyannote, mock_ollama):
        """TC-K03: Silent audio produces empty or minimal transcript without crashing."""
        from backend.app.schemas.process import Segment

        # Whisper returns no segments for silent audio
        with patch(
            "backend.services.whisper_service.transcribe_segments",
            return_value=[],
        ), patch(
            "backend.services.faiss_service.build_index",
        ):
            response = client.post(
                "/process",
                files={"upload_file": ("silent.wav", BytesIO(_make_wav_bytes()), "audio/wav")},
                data={"language_mode": "automatic"},
            )
        # Should complete without crashing
        assert response.status_code == 200

    def test_k05_map_reduce_handles_long_text(self, mock_ollama):
        """TC-K05: map_reduce_summary handles text > 4000 characters."""
        from backend.app.modules.meeting_mode.text_chunker import map_reduce_summary

        # Create a text > 8000 characters
        long_text = "Speaker 1: This is a test sentence. " * 500  # ~18000 chars
        assert len(long_text) > 8000

        result = map_reduce_summary(long_text)
        assert isinstance(result, str)
        assert len(result) > 0
        # llm_complete should have been called multiple times (map + reduce)
        assert mock_ollama["llm_complete"].call_count >= 2

    def test_k05_map_reduce_action_items_handles_long_text(self, mock_ollama):
        """TC-K05: map_reduce_action_items handles text > 4000 characters."""
        from backend.app.modules.meeting_mode.text_chunker import map_reduce_action_items

        long_text = "Action: Complete task number X. " * 200  # ~6400 chars
        assert len(long_text) > 4000

        result = map_reduce_action_items(long_text)
        assert isinstance(result, str)
        assert mock_ollama["llm_complete"].call_count >= 2


class TestFileValidation:
    """Additional file validation edge cases."""

    def test_file_without_extension_rejected(self, client):
        """Upload file without extension returns 400."""
        response = client.post(
            "/process",
            files={"upload_file": ("noextension", BytesIO(b"data"), "audio/wav")},
            data={"language_mode": "automatic"},
        )
        assert response.status_code == 400

    def test_invalid_language_mode(self, client):
        """Invalid language_mode value raises error."""
        response = client.post(
            "/process",
            files={"upload_file": ("test.wav", BytesIO(_make_wav_bytes()), "audio/wav")},
            data={"language_mode": "invalid_mode"},
        )
        # Should fail with some error (ValueError from parse_language_mode)
        assert response.status_code in (400, 422, 500)


class TestConcurrentJobs:
    """TC-K04: Independent job handling."""

    def test_k04_multiple_jobs_independent(self):
        """TC-K04: Multiple jobs are tracked independently in the job store."""
        from backend.app.modules.meeting_mode.background_jobs import (
            complete_job,
            create_job,
            get_job_status,
            set_job_status,
        )

        job1 = create_job()
        job2 = create_job()

        assert job1.job_id != job2.job_id

        set_job_status(job1.job_id, "processing", percent=50)
        complete_job(job2.job_id, {"transcript": "Job 2 done"})

        j1 = get_job_status(job1.job_id)
        j2 = get_job_status(job2.job_id)

        assert j1.status == "processing"
        assert j1.percent_complete == 50.0

        assert j2.status == "complete"
        assert j2.percent_complete == 100.0
        assert j2.result == {"transcript": "Job 2 done"}
