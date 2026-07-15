import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

_JOBS: Dict[str, "Job"] = {}


@dataclass
class Job:
    job_id: str
    status: str = "queued"
    percent_complete: float = 0.0
    current_step: Optional[str] = None
    result: Optional[dict] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def create_job() -> Job:
    job = Job(job_id=str(uuid.uuid4()))
    _JOBS[job.job_id] = job
    return job


def get_job_status(job_id: str) -> Optional[Job]:
    return _JOBS.get(job_id)


def set_job_status(job_id: str, status: str, percent: float = None, current_step: str = None) -> None:
    job = _JOBS.get(job_id)
    if not job:
        return
    job.status = status
    if percent is not None:
        job.percent_complete = percent
    if current_step is not None:
        job.current_step = current_step


def complete_job(job_id: str, result: dict) -> None:
    job = _JOBS.get(job_id)
    if not job:
        return
    job.status = "complete"
    job.percent_complete = 100
    job.current_step = "done"
    job.result = result
