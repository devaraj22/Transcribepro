from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from ....core.config import settings
from ....core.exceptions import JobNotFoundError
from ....modules.meeting_mode.background_jobs import complete_job, create_job, get_job_status, set_job_status
from ....modules.meeting_mode.pipeline import process_long_recording
from ....modules.quick_capture.pipeline import process_short_recording
from ....schemas.process import JobStatus, ProcessResponse
from ....utils.file_handlers import parse_language_mode, safe_save_upload
from backend.services.ffmpeg_service import prepare_audio_file, probe_duration


def _validate_upload_file(upload_file: UploadFile) -> None:
    if upload_file.size is None:
        raise HTTPException(status_code=400, detail="The uploaded file is empty or unreadable.")
    if upload_file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds the maximum supported size.")

router = APIRouter()


def _run_long_job(job_id: str, upload_path: Path, language_mode: str, manual_language: Optional[str]) -> None:
    set_job_status(job_id, "processing", percent=10, current_step="preparing audio")
    result = process_long_recording(upload_path, language_mode, manual_language, job_id=job_id)
    complete_job(job_id, result)


@router.post("/process", response_model=ProcessResponse)
async def process(
    upload_file: UploadFile = File(...),
    language_mode: str = Form(settings.LANGUAGE_MODE),
    manual_language: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
):
    _validate_upload_file(upload_file)

    upload_path = settings.UPLOAD_DIR / upload_file.filename
    saved_path = safe_save_upload(upload_file, upload_path)
    language_mode = parse_language_mode(language_mode)

    try:
        if settings.LONG_RECORDING_THRESHOLD > 0:
            audio_path = prepare_audio_file(saved_path)
            duration = probe_duration(audio_path)
            if duration > settings.LONG_RECORDING_THRESHOLD:
                job = create_job()
                set_job_status(job.job_id, "queued", percent=0, current_step="waiting")
                background_tasks.add_task(_run_long_job, job.job_id, saved_path, language_mode, manual_language)
                return ProcessResponse(job_id=job.job_id, status="queued", detail="Long recording accepted; poll status.")

        process_short_recording(saved_path, language_mode, manual_language)
        return ProcessResponse(job_id=None, status="complete", detail="Processed successfully.")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/process/{job_id}/status", response_model=JobStatus)
def process_status(job_id: str):
    job = get_job_status(job_id)
    if not job:
        raise JobNotFoundError(job_id)
    return JobStatus(job_id=job.job_id, status=job.status, percent_complete=job.percent_complete, current_step=job.current_step)


@router.get("/process/{job_id}/result")
def process_result(job_id: str):
    job = get_job_status(job_id)
    if not job:
        raise JobNotFoundError(job_id)
    if job.status != "complete":
        raise HTTPException(status_code=400, detail="Job is not complete yet.")
    return JSONResponse(content=job.result)
