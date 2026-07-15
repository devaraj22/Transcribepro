from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ....core.config import settings
from ....modules.meeting_mode.background_jobs import get_job_status
from backend.services.reportlab_service import build_report

router = APIRouter()


@router.get("/report/{job_id}")
def report(job_id: str):
    job = get_job_status(job_id)
    if not job or job.status != "complete":
        raise HTTPException(status_code=404, detail="Report not available until job completion.")

    transcript = job.result.get("transcript", "")
    summary = job.result.get("summary") or ""
    action_items = "\n".join(job.result.get("action_items") or [])
    output_path = settings.REPORT_DIR / f"report_{job_id}.pdf"
    build_report(job_id, transcript, summary, action_items, output_path)
    return FileResponse(str(output_path), media_type="application/pdf", filename=output_path.name)
