from pathlib import Path
from typing import List, Optional

from faster_whisper import WhisperModel

from ..app.core.config import settings
from ..app.schemas.process import Segment

_model: Optional[WhisperModel] = None


def get_whisper_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(settings.WHISPER_MODEL, device="auto", compute_type="int8")
    return _model


def transcribe_segments(audio_path: Path, manual_language: Optional[str] = None) -> List[Segment]:
    model = get_whisper_model()
    kwargs = {
        "vad_filter": True,
    }
    if manual_language:
        kwargs["language"] = manual_language

    try:
        segments, info = model.transcribe(str(audio_path), **kwargs)
    except ValueError as exc:
        if "max() arg is an empty sequence" not in str(exc):
            raise
        segments = []
        info = None

    detected_language = manual_language or getattr(info, "language", None) or "unknown"
    return [
        Segment(
            start=seg.start,
            end=seg.end,
            language=detected_language,
            text=seg.text.strip(),
        )
        for seg in segments
    ]
