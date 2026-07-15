import os
from pathlib import Path
from typing import Dict, List

from pyannote.audio import Pipeline

from ..app.core.config import settings

_pipeline = None


def get_diarization_pipeline():
    global _pipeline
    if _pipeline is None:
        hf_token = os.environ.get("HUGGINGFACE_TOKEN")
        if not hf_token:
            return None
        try:
            _pipeline = Pipeline.from_pretrained(settings.DIARIZATION_MODEL, token=hf_token)
        except TypeError:
            # Fall back for older pyannote/huggingface_hub combinations.
            try:
                _pipeline = Pipeline.from_pretrained(settings.DIARIZATION_MODEL, use_auth_token=hf_token)
            except Exception:
                _pipeline = None
        except Exception:
            _pipeline = None
    return _pipeline


def diarize_audio(audio_path: Path) -> List[Dict]:
    pipeline = get_diarization_pipeline()
    if pipeline is None:
        return []
    diarization = pipeline(str(audio_path))
    turns = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        turns.append({"start": turn.start, "end": turn.end, "speaker": speaker})
    return turns
