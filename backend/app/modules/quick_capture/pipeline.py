from pathlib import Path
from typing import Dict, Optional

from ...core.config import settings
from ...schemas.process import Segment
from ..meeting_mode.pipeline import merge_transcript_segments
from ..meeting_mode.text_chunker import chunk_segments
from backend.services.ffmpeg_service import prepare_audio_file, probe_duration
from backend.services.faiss_service import build_index
from backend.services.history_service import append_history
from backend.services.pyannote_service import diarize_audio
from backend.services.whisper_service import transcribe_segments


def process_short_recording(upload_path: Path, language_mode: str, manual_language: Optional[str] = None) -> Dict:
    """Synchronous flow for quick-capture (short) recordings — no job polling needed."""
    audio_path = prepare_audio_file(upload_path)
    duration = probe_duration(audio_path)

    raw_segments = transcribe_segments(audio_path, manual_language if language_mode == "manual" else None)
    diarization = diarize_audio(audio_path)
    merged_segments = merge_transcript_segments(raw_segments, diarization)
    full_text = "\n".join(f"{seg['speaker']}: {seg['text']}" for seg in merged_segments)

    chunks = chunk_segments([Segment(**seg) for seg in merged_segments], settings.CHUNK_LENGTH)
    build_index(chunks, "inline")

    append_history(
        {
            "title": None,
            "duration_seconds": duration,
            "languages": list({seg["language"] for seg in merged_segments if seg.get("language")}),
            "transcript": full_text,
            "segments": merged_segments,
            "job_id": None,
        }
    )

    return {
        "transcript": full_text,
        "segments": merged_segments,
        "languages": list({seg["language"] for seg in merged_segments if seg.get("language")}),
        "duration_seconds": duration,
    }
