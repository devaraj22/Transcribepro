"""
Module F — PDF Report Generation
TC-F01 to TC-F03
"""

import pytest


class TestReportGeneration:
    """Tests for the PDF report download endpoint."""

    def test_f01_download_pdf_report_for_completed_job(self, client):
        """TC-F01: GET /report/{job_id} returns a PDF for a completed job."""
        from backend.app.modules.meeting_mode.background_jobs import complete_job, create_job

        job = create_job()
        complete_job(
            job.job_id,
            {
                "transcript": "Speaker 1: Hello\nSpeaker 2: Hi there",
                "summary": "A brief greeting exchange.",
                "action_items": ["Follow up with Speaker 2"],
            },
        )

        response = client.get(f"/report/{job.job_id}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        # Verify it's actually a PDF (starts with %PDF)
        assert response.content[:5] == b"%PDF-"

    def test_f02_report_for_incomplete_job_returns_404(self, client):
        """TC-F02: GET /report/{job_id} returns 404 for an incomplete job."""
        from backend.app.modules.meeting_mode.background_jobs import create_job, set_job_status

        job = create_job()
        set_job_status(job.job_id, "processing", percent=50, current_step="transcribing")

        response = client.get(f"/report/{job.job_id}")
        assert response.status_code == 404
        assert "not available" in response.json()["detail"]

    def test_f03_report_for_nonexistent_job_returns_404(self, client):
        """TC-F03: GET /report/{nonexistent} returns 404."""
        response = client.get("/report/nonexistent-job-id")
        assert response.status_code == 404

    def test_report_with_missing_optional_fields(self, client):
        """Report generation handles missing summary/action_items gracefully."""
        from backend.app.modules.meeting_mode.background_jobs import complete_job, create_job

        job = create_job()
        complete_job(
            job.job_id,
            {
                "transcript": "Speaker 1: Hello world",
                "summary": None,
                "action_items": None,
            },
        )

        response = client.get(f"/report/{job.job_id}")
        assert response.status_code == 200
        assert response.content[:5] == b"%PDF-"
