from pathlib import Path
from typing import Dict, List, Optional

from ...core.config import settings
from ...schemas.process import Segment
from .background_jobs import set_job_status
from .text_chunker import chunk_segments
from backend.services.ffmpeg_service import prepare_audio_file, probe_duration
from backend.services.faiss_service import build_index
from backend.services.history_service import append_history
from backend.services.pyannote_service import diarize_audio
from backend.services.whisper_service import transcribe_segments


def merge_transcript_segments(transcript_segments: List[Segment], diarization: List[Dict]) -> List[Dict]:
    merged = []
    for segment in transcript_segments:
        mid = (segment.start + segment.end) / 2
        speaker = None
        for turn in diarization:
            if turn["start"] <= mid <= turn["end"]:
                speaker = turn["speaker"]
                break
        merged.append(
            {
                "start": segment.start,
                "end": segment.end,
                "speaker": speaker or "Speaker 1",
                "language": segment.language,
                "text": segment.text,
            }
        )
    return merged


def process_long_recording(
    upload_path: Path,
    language_mode: str,
    manual_language: Optional[str] = None,
    job_id: Optional[str] = None,
) -> Dict:
    set_job_status(job_id, "processing", percent=15, current_step="extracting audio")
    audio_path = prepare_audio_file(upload_path)
    duration = probe_duration(audio_path)

    set_job_status(job_id, "processing", percent=35, current_step="transcribing")
    raw_segments = transcribe_segments(audio_path, manual_language if language_mode == "manual" else None)

    set_job_status(job_id, "processing", percent=55, current_step="diarizing speakers")
    diarization = diarize_audio(audio_path)
    merged_segments = merge_transcript_segments(raw_segments, diarization)
    full_text = "\n".join(f"{seg['speaker']}: {seg['text']}" for seg in merged_segments)

    set_job_status(job_id, "processing", percent=75, current_step="indexing chunks")
    chunks = chunk_segments([Segment(**seg) for seg in merged_segments], settings.CHUNK_LENGTH)
    build_index(chunks, job_id or "inline")

    set_job_status(job_id, "processing", percent=90, current_step="saving history")
    append_history(
        {
            "title": None,
            "duration_seconds": duration,
            "languages": list({seg["language"] for seg in merged_segments if seg.get("language")}),
            "transcript": full_text,
            "segments": merged_segments,
            "job_id": job_id,
        }
    )

    return {
        "transcript": full_text,
        "segments": merged_segments,
        "languages": list({seg["language"] for seg in merged_segments if seg.get("language")}),
        "duration_seconds": duration,
        "title": None,
        "summary": None,
        "action_items": None,
    }
