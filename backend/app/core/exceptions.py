from fastapi import Request
from fastapi.responses import JSONResponse


class TranscriptionError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class DiarizationError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class LLMServiceError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class JobNotFoundError(Exception):
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.detail = f"Job '{job_id}' not found."


def register_exception_handlers(app):
    @app.exception_handler(TranscriptionError)
    async def transcription_error_handler(request: Request, exc: TranscriptionError):
        return JSONResponse(status_code=422, content={"detail": f"Transcription failed: {exc.detail}"})

    @app.exception_handler(DiarizationError)
    async def diarization_error_handler(request: Request, exc: DiarizationError):
        return JSONResponse(status_code=422, content={"detail": f"Diarization failed: {exc.detail}"})

    @app.exception_handler(LLMServiceError)
    async def llm_error_handler(request: Request, exc: LLMServiceError):
        return JSONResponse(status_code=502, content={"detail": f"LLM service failed: {exc.detail}"})

    @app.exception_handler(JobNotFoundError)
    async def job_not_found_handler(request: Request, exc: JobNotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.detail})
