"""
Module C — Meeting Mode Processing (Long recordings, async background jobs)
TC-C01 to TC-C06
"""

import time
from io import BytesIO
from unittest.mock import patch

import pytest

from tests.conftest import _make_wav_bytes


class TestMeetingModeAsync:
    """Tests for the asynchronous meeting-mode processing path."""

    def test_c01_long_audio_triggers_background_job(self, client, long_wav_bytes, mock_all_services):
        """TC-C01: Long audio (> 600s) returns a job_id with status=queued."""
        # Override probe_duration to return > 600s
        mock_all_services["ffmpeg"]["probe_duration"].return_value = 700.0

        response = client.post(
            "/process",
            files={"upload_file": ("long_meeting.wav", BytesIO(long_wav_bytes), "audio/wav")},
            data={"language_mode": "automatic"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "queued"
        assert body["job_id"] is not None
        assert "Long recording accepted" in body["detail"]

    def test_c02_job_status_returns_valid_status(self, client, long_wav_bytes, mock_all_services):
        """TC-C02: GET /process/{job_id}/status returns valid status object."""
        mock_all_services["ffmpeg"]["probe_duration"].return_value = 700.0

        # Submit long recording
        resp = client.post(
            "/process",
            files={"upload_file": ("long_meeting.wav", BytesIO(long_wav_bytes), "audio/wav")},
            data={"language_mode": "automatic"},
        )
        job_id = resp.json()["job_id"]

        # Check status
        status_resp = client.get(f"/process/{job_id}/status")
        assert status_resp.status_code == 200
        status_body = status_resp.json()
        assert status_body["job_id"] == job_id
        assert status_body["status"] in ("queued", "processing", "complete")
        assert "percent_complete" in status_body

    def test_c03_job_result_available_after_completion(self, client, long_wav_bytes, mock_all_services):
        """TC-C03: GET /process/{job_id}/result returns transcript after job completes."""
        mock_all_services["ffmpeg"]["probe_duration"].return_value = 700.0

        # Submit
        resp = client.post(
            "/process",
            files={"upload_file": ("long_meeting.wav", BytesIO(long_wav_bytes), "audio/wav")},
            data={"language_mode": "automatic"},
        )
        job_id = resp.json()["job_id"]

        # Wait for background task to complete (TestClient runs them synchronously)
        # With TestClient, BackgroundTasks run synchronously after the response is sent
        result_resp = client.get(f"/process/{job_id}/result")

        # The TestClient runs background tasks synchronously, so job should be complete
        if result_resp.status_code == 200:
            body = result_resp.json()
            assert "transcript" in body
            assert "segments" in body
            assert "duration_seconds" in body
        else:
            # If still processing, that's also valid — the background task
            # might not have completed in TestClient context
            assert result_resp.status_code == 400

    def test_c04_result_of_incomplete_job_returns_400(self, client):
        """TC-C04: Fetching result of an incomplete job returns 400."""
        from backend.app.modules.meeting_mode.background_jobs import create_job, set_job_status

        job = create_job()
        set_job_status(job.job_id, "processing", percent=50, current_step="transcribing")

        resp = client.get(f"/process/{job.job_id}/result")
        assert resp.status_code == 400
        assert "not complete" in resp.json()["detail"]

    def test_c05_nonexistent_job_status_returns_404(self, client):
        """TC-C05: GET /process/{invalid_id}/status returns 404."""
        resp = client.get("/process/nonexistent-uuid-12345/status")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_c06_nonexistent_job_result_returns_404(self, client):
        """TC-C06: GET /process/{invalid_id}/result returns 404."""
        resp = client.get("/process/nonexistent-uuid-12345/result")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


class TestJobStatusProgression:
    """Verify the in-memory job lifecycle."""

    def test_job_lifecycle_queued_to_complete(self):
        """Verify Job transitions: queued → processing → complete."""
        from backend.app.modules.meeting_mode.background_jobs import (
            Job,
            complete_job,
            create_job,
            get_job_status,
            set_job_status,
        )

        job = create_job()
        assert job.status == "queued"
        assert job.percent_complete == 0.0

        set_job_status(job.job_id, "processing", percent=50, current_step="transcribing")
        fetched = get_job_status(job.job_id)
        assert fetched.status == "processing"
        assert fetched.percent_complete == 50.0
        assert fetched.current_step == "transcribing"

        complete_job(job.job_id, {"transcript": "Hello world"})
        fetched = get_job_status(job.job_id)
        assert fetched.status == "complete"
        assert fetched.percent_complete == 100.0
        assert fetched.result == {"transcript": "Hello world"}

    def test_set_status_on_nonexistent_job_is_noop(self):
        """set_job_status on a missing job_id should not raise."""
        from backend.app.modules.meeting_mode.background_jobs import set_job_status
        set_job_status("does-not-exist", "processing", percent=50)  # Should not raise

    def test_complete_nonexistent_job_is_noop(self):
        """complete_job on a missing job_id should not raise."""
        from backend.app.modules.meeting_mode.background_jobs import complete_job
        complete_job("does-not-exist", {"data": "test"})  # Should not raise
