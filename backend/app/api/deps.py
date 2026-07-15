"""Dependency-injected singletons (loaded once, reused across requests)."""

from functools import lru_cache

from backend.services.whisper_service import get_whisper_model
from backend.services.pyannote_service import get_diarization_pipeline


@lru_cache
def whisper_model_dependency():
    return get_whisper_model()


@lru_cache
def diarization_pipeline_dependency():
    return get_diarization_pipeline()
