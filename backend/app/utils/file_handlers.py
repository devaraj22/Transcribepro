import shutil
from pathlib import Path

from fastapi import HTTPException, UploadFile

from ..core.config import settings

SUPPORTED_EXTENSIONS = [ext.strip().lower() for ext in settings.SUPPORTED_FORMATS.split(",")]


def ensure_storage_dirs() -> None:
    for path in [
        settings.UPLOAD_DIR,
        settings.REPORT_DIR,
        settings.TRANSCRIPT_DIR,
        settings.STORAGE_DIR,
        settings.VECTOR_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def safe_save_upload(upload: UploadFile, destination: Path) -> Path:
    if upload.content_type is None or "." not in upload.filename:
        raise HTTPException(status_code=400, detail="Unsupported file type or missing filename.")

    extension = upload.filename.rsplit(".", 1)[-1].lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {extension}")

    destination = destination.with_suffix(f".{extension}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    return destination


def parse_language_mode(language_mode: str) -> str:
    if language_mode.lower() not in {"automatic", "manual"}:
        raise ValueError("language_mode must be automatic or manual")
    return language_mode.lower()


def is_video_file(path: Path) -> bool:
    return path.suffix.lower().lstrip(".") not in {"mp3", "wav", "m4a", "webm"}
