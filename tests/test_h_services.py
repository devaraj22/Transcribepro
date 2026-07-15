"""
Module H — Service-Layer Unit Tests
TC-H01 to TC-H12
"""

import json
import os
from pathlib import Path
from typing import Dict, List
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import _mock_diarization, _mock_segments


# ---------------------------------------------------------------------------
# TC-H01 to TC-H03: FFmpeg service
# ---------------------------------------------------------------------------
class TestFFmpegService:
    """Unit tests for ffmpeg_service functions."""

    def test_h01_probe_duration_returns_float(self):
        """TC-H01: probe_duration returns correct duration as float."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="30.5\n", stderr="")
            from backend.services.ffmpeg_service import probe_duration
            duration = probe_duration(Path("test.wav"))
            assert isinstance(duration, float)
            assert duration == pytest.approx(30.5)

    def test_h01_probe_duration_raises_on_failure(self):
        """TC-H01: probe_duration raises RuntimeError when ffprobe fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Invalid data")
            from backend.services.ffmpeg_service import probe_duration
            with pytest.raises(RuntimeError, match="ffprobe failed"):
                probe_duration(Path("corrupt.wav"))

    def test_h02_extract_audio_produces_wav(self, tmp_path):
        """TC-H02: extract_audio produces a .wav output file."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            from backend.services.ffmpeg_service import extract_audio

            input_path = tmp_path / "video.mp4"
            input_path.touch()
            output_path = tmp_path / "audio"

            result = extract_audio(input_path, output_path)
            assert result.suffix == ".wav"
            # Verify ffmpeg was called with correct arguments
            call_args = mock_run.call_args[0][0]
            assert "ffmpeg" in call_args[0]
            assert "-ar" in call_args
            assert "16000" in call_args

    def test_h02_extract_audio_raises_on_failure(self, tmp_path):
        """TC-H02: extract_audio raises RuntimeError when ffmpeg fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="codec error")
            from backend.services.ffmpeg_service import extract_audio

            with pytest.raises(RuntimeError, match="ffmpeg extraction failed"):
                extract_audio(tmp_path / "bad.mp4", tmp_path / "out")

    def test_h03_prepare_audio_returns_same_path_for_audio(self, tmp_path):
        """TC-H03: prepare_audio_file returns the same path for audio files (.wav)."""
        audio_path = tmp_path / "recording.wav"
        audio_path.touch()

        from backend.services.ffmpeg_service import prepare_audio_file
        result = prepare_audio_file(audio_path)
        assert result == audio_path  # No extraction needed

    def test_h03_prepare_audio_extracts_for_video(self, tmp_path):
        """TC-H03: prepare_audio_file calls extract_audio for video files (.mp4)."""
        video_path = tmp_path / "meeting.mp4"
        video_path.touch()

        with patch("backend.services.ffmpeg_service.extract_audio") as mock_extract:
            expected_output = tmp_path / "meeting_extracted.wav"
            mock_extract.return_value = expected_output

            from backend.services.ffmpeg_service import prepare_audio_file
            result = prepare_audio_file(video_path)
            mock_extract.assert_called_once()


# ---------------------------------------------------------------------------
# TC-H04: Whisper service
# ---------------------------------------------------------------------------
class TestWhisperService:
    """Unit tests for whisper_service functions."""

    def test_h04_transcribe_segments_returns_valid_segments(self):
        """TC-H04: transcribe_segments returns List[Segment] with valid fields."""
        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 5.0
        mock_segment.text = " Hello, world. "

        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)

        with patch("backend.services.whisper_service._model", mock_model), \
             patch("backend.services.whisper_service.get_whisper_model", return_value=mock_model):
            from backend.services import whisper_service
            # Reset the module-level singleton
            whisper_service._model = mock_model
            segments = whisper_service.transcribe_segments(Path("test.wav"))

        assert len(segments) == 1
        seg = segments[0]
        assert seg.start == 0.0
        assert seg.end == 5.0
        assert seg.text == "Hello, world."  # stripped
        assert seg.language == "en"

    def test_h04_transcribe_with_manual_language(self):
        """TC-H04: transcribe_segments passes manual_language to Whisper."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([], MagicMock(language="fr"))

        with patch("backend.services.whisper_service.get_whisper_model", return_value=mock_model):
            from backend.services import whisper_service
            whisper_service._model = mock_model
            whisper_service.transcribe_segments(Path("test.wav"), manual_language="fr")

        call_kwargs = mock_model.transcribe.call_args
        assert call_kwargs[1].get("language") == "fr"


# ---------------------------------------------------------------------------
# TC-H05: Pyannote service
# ---------------------------------------------------------------------------
class TestPyannoteService:
    """Unit tests for pyannote_service functions."""

    def test_h05_diarize_audio_returns_speaker_turns(self):
        """TC-H05: diarize_audio returns List[Dict] with start, end, speaker keys."""
        mock_turn1 = MagicMock()
        mock_turn1.start = 0.0
        mock_turn1.end = 10.0

        mock_turn2 = MagicMock()
        mock_turn2.start = 10.0
        mock_turn2.end = 20.0

        # The pipeline itself is called with the audio path, returning a diarization object
        mock_diarization_result = MagicMock()
        mock_diarization_result.itertracks.return_value = [
            (mock_turn1, None, "SPEAKER_00"),
            (mock_turn2, None, "SPEAKER_01"),
        ]

        mock_pipeline = MagicMock()
        mock_pipeline.return_value = mock_diarization_result

        with patch("backend.services.pyannote_service.get_diarization_pipeline", return_value=mock_pipeline):
            from backend.services import pyannote_service
            pyannote_service._pipeline = mock_pipeline
            turns = pyannote_service.diarize_audio(Path("test.wav"))

        assert len(turns) == 2
        for turn in turns:
            assert "start" in turn
            assert "end" in turn
            assert "speaker" in turn
        assert turns[0]["speaker"] == "SPEAKER_00"
        assert turns[1]["speaker"] == "SPEAKER_01"

    def test_h05_get_diarization_pipeline_uses_token_kwarg_for_modern_hf_hub(self):
        """TC-H05: use token= when initializing pyannote pipelines for newer huggingface_hub."""
        from backend.services import pyannote_service

        pyannote_service._pipeline = None
        with patch.dict(os.environ, {"HUGGINGFACE_TOKEN": "test-token"}, clear=False), \
             patch("backend.services.pyannote_service.Pipeline.from_pretrained") as mock_from_pretrained:
            mock_from_pretrained.return_value = MagicMock()
            pyannote_service.get_diarization_pipeline()

        kwargs = mock_from_pretrained.call_args.kwargs
        assert kwargs.get("token") == "test-token"


# ---------------------------------------------------------------------------
# TC-H06, TC-H07: Ollama service
# ---------------------------------------------------------------------------
class TestOllamaService:
    """Unit tests for ollama_service functions."""

    def test_h06_llm_complete_returns_string(self):
        """TC-H06: llm_complete returns a non-empty string."""
        with patch("ollama.generate", return_value={"response": "Hello! "}):
            from backend.services.ollama_service import llm_complete
            result = llm_complete("Say hello", task="cleanup")
            assert isinstance(result, str)
            assert result == "Hello!"  # stripped

    def test_h06_llm_complete_raises_on_failure(self):
        """TC-H06: llm_complete raises LLMServiceError on exception."""
        from backend.app.core.exceptions import LLMServiceError

        with patch("ollama.generate", side_effect=ConnectionError("refused")):
            from backend.services.ollama_service import llm_complete
            with pytest.raises(LLMServiceError):
                llm_complete("test prompt")

    def test_h07_llm_embed_returns_vector(self):
        """TC-H07: llm_embed returns a List[float] with correct dimension."""
        embedding = [0.1] * 768
        with patch("ollama.embeddings", return_value={"embedding": embedding}):
            from backend.services.ollama_service import llm_embed
            result = llm_embed("test sentence")
            assert isinstance(result, list)
            assert len(result) == 768
            assert all(isinstance(x, float) for x in result)

    def test_h07_llm_embed_raises_on_failure(self):
        """TC-H07: llm_embed raises LLMServiceError on exception."""
        from backend.app.core.exceptions import LLMServiceError

        with patch("ollama.embeddings", side_effect=ConnectionError("refused")):
            from backend.services.ollama_service import llm_embed
            with pytest.raises(LLMServiceError):
                llm_embed("test")


# ---------------------------------------------------------------------------
# TC-H08, TC-H09: FAISS service
# ---------------------------------------------------------------------------
class TestFAISSService:
    """Unit tests for faiss_service functions."""

    def test_h08_build_index_creates_files(self, mock_ollama):
        """TC-H08: build_index creates index.faiss and metadata.json."""
        from backend.app.core.config import settings
        from backend.services.faiss_service import build_index

        chunks = [
            {"text": "Hello world", "start": 0.0, "end": 5.0},
            {"text": "Goodbye world", "start": 5.0, "end": 10.0},
        ]
        build_index(chunks, "test_build_job")

        index_dir = settings.VECTOR_DIR / "test_build_job"
        assert index_dir.exists()
        assert (index_dir / "index.faiss").exists()
        assert (index_dir / "metadata.json").exists()

        # Verify metadata content
        metadata = json.loads((index_dir / "metadata.json").read_text(encoding="utf-8"))
        assert len(metadata) == 2
        assert metadata[0]["chunk_id"] == "0"
        assert metadata[0]["text"] == "Hello world"
        assert metadata[1]["chunk_id"] == "1"

    def test_h09_retrieve_returns_answer_and_sources(self, mock_ollama):
        """TC-H09: retrieve returns (answer, sources) tuple."""
        from backend.app.core.config import settings
        from backend.services.faiss_service import build_index, retrieve

        chunks = [
            {"text": "We discussed the Q3 roadmap.", "start": 0.0, "end": 30.0},
            {"text": "Budget was approved for marketing.", "start": 30.0, "end": 60.0},
        ]
        build_index(chunks, "test_retrieve_job")

        answer, sources = retrieve("test_retrieve_job", "What was discussed?")
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert isinstance(sources, list)
        assert len(sources) > 0
        assert all(s.startswith("chunk_") for s in sources)


# ---------------------------------------------------------------------------
# TC-H10: Merge transcript segments
# ---------------------------------------------------------------------------
class TestMergeTranscriptSegments:
    """Unit tests for merge_transcript_segments."""

    def test_h10_merge_assigns_speakers(self):
        """TC-H10: merge_transcript_segments assigns speaker labels based on diarization."""
        from backend.app.modules.meeting_mode.pipeline import merge_transcript_segments

        segments = _mock_segments(3)
        diarization = _mock_diarization(3)

        merged = merge_transcript_segments(segments, diarization)
        assert len(merged) == 3
        for seg in merged:
            assert "speaker" in seg
            assert "text" in seg
            assert "start" in seg
            assert "end" in seg

        # First and third segments should have SPEAKER_00 (index 0, 2)
        assert merged[0]["speaker"] == "SPEAKER_00"
        assert merged[1]["speaker"] == "SPEAKER_01"
        assert merged[2]["speaker"] == "SPEAKER_00"

    def test_h10_merge_defaults_to_speaker_1_when_no_match(self):
        """TC-H10: When no diarization turn matches, speaker defaults to 'Speaker 1'."""
        from backend.app.modules.meeting_mode.pipeline import merge_transcript_segments

        segments = _mock_segments(1)
        # Empty diarization — no matching turns
        merged = merge_transcript_segments(segments, [])
        assert merged[0]["speaker"] == "Speaker 1"


# ---------------------------------------------------------------------------
# TC-H11: Text chunker
# ---------------------------------------------------------------------------
class TestTextChunker:
    """Unit tests for chunk_segments."""

    def test_h11_chunks_group_by_time_window(self):
        """TC-H11: chunk_segments groups segments by chunk_length seconds."""
        from backend.app.modules.meeting_mode.text_chunker import chunk_segments
        from backend.app.schemas.process import Segment

        # 10 segments spanning 0–1000s
        segments = [
            Segment(start=i * 100.0, end=(i + 1) * 100.0 - 1.0, text=f"Text {i}", speaker=f"Speaker {i % 2}")
            for i in range(10)
        ]

        chunks = chunk_segments(segments, chunk_length=300)
        assert len(chunks) >= 3  # 1000s / 300s ≈ 3-4 chunks
        for chunk in chunks:
            assert "text" in chunk
            assert "start" in chunk
            assert "end" in chunk
            assert chunk["end"] - chunk["start"] <= 350  # approximately chunk_length

    def test_h11_single_segment_produces_one_chunk(self):
        """TC-H11: A single short segment produces exactly one chunk."""
        from backend.app.modules.meeting_mode.text_chunker import chunk_segments
        from backend.app.schemas.process import Segment

        segments = [Segment(start=0.0, end=5.0, text="Short", speaker="A")]
        chunks = chunk_segments(segments, chunk_length=300)
        assert len(chunks) == 1

    def test_h11_empty_segments_produces_empty_chunks(self):
        """TC-H11: No segments produces no chunks."""
        from backend.app.modules.meeting_mode.text_chunker import chunk_segments

        chunks = chunk_segments([], chunk_length=300)
        assert chunks == []


# ---------------------------------------------------------------------------
# TC-H12: ReportLab service
# ---------------------------------------------------------------------------
class TestReportLabService:
    """Unit tests for reportlab_service."""

    def test_h12_build_report_generates_valid_pdf(self, tmp_path):
        """TC-H12: build_report creates a non-empty PDF file."""
        from backend.services.reportlab_service import build_report

        output = tmp_path / "test_report.pdf"
        result = build_report(
            job_id="test-123",
            transcript="Speaker 1: Hello\nSpeaker 2: Hi there",
            summary="A greeting exchange between two speakers.",
            action_items="- Follow up with Speaker 2\n- Schedule next meeting",
            output_path=output,
        )

        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Verify it's actually a PDF
        with open(output, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-"

    def test_h12_build_report_handles_empty_content(self, tmp_path):
        """TC-H12: build_report handles empty transcript/summary gracefully."""
        from backend.services.reportlab_service import build_report

        output = tmp_path / "empty_report.pdf"
        result = build_report(
            job_id="empty-test",
            transcript="",
            summary="",
            action_items="",
            output_path=output,
        )
        assert output.exists()
        assert output.stat().st_size > 0
