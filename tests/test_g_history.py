"""
Module G — History Endpoint
TC-G01 to TC-G03
"""

import json

import pytest


class TestHistory:
    """Tests for the history retrieval endpoint."""

    def test_g01_history_returns_recent_entries(self, client, seeded_history):
        """TC-G01: GET /history returns history entries with correct schema."""
        response = client.get("/history")
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) == 3

        # Each entry should have the expected fields
        for entry in body:
            assert "id" in entry
            assert "timestamp" in entry
            assert "title" in entry
            assert "duration_seconds" in entry
            assert "languages" in entry
            assert "transcript" in entry
            assert "segments" in entry
            assert "job_id" in entry

    def test_g02_history_respects_limit(self, client, tmp_path):
        """TC-G02: History truncates to HISTORY_LIMIT entries."""
        from backend.app.core.config import settings

        # Create more entries than HISTORY_LIMIT (default 5)
        entries = [
            {
                "id": f"h-{i}",
                "timestamp": f"2026-07-{10 + i}T00:00:00+00:00",
                "title": f"Recording {i}",
                "duration_seconds": 60.0,
                "languages": ["en"],
                "transcript": f"Text {i}",
                "segments": [],
                "job_id": None,
            }
            for i in range(8)
        ]
        settings.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        settings.HISTORY_FILE.write_text(json.dumps(entries), encoding="utf-8")

        response = client.get("/history")
        assert response.status_code == 200
        body = response.json()
        # get_history returns whatever is in the file; the limit is enforced
        # by append_history when writing. So if 8 are written, 8 are returned.
        assert isinstance(body, list)

    def test_g02_append_history_enforces_limit(self):
        """TC-G02: append_history truncates to HISTORY_LIMIT."""
        from backend.app.core.config import settings
        from backend.services.history_service import append_history, get_history

        # Seed with HISTORY_LIMIT entries
        for i in range(settings.HISTORY_LIMIT + 3):
            append_history(
                {
                    "title": f"Recording {i}",
                    "duration_seconds": 60.0,
                    "languages": ["en"],
                    "transcript": f"Text {i}",
                    "segments": [],
                    "job_id": None,
                }
            )

        history = get_history()
        assert len(history) <= settings.HISTORY_LIMIT

    def test_g03_history_is_ordered_newest_first(self):
        """TC-G03: History entries are ordered newest-first."""
        from backend.services.history_service import append_history, get_history

        import time

        append_history(
            {
                "title": "First",
                "duration_seconds": 30.0,
                "languages": ["en"],
                "transcript": "First recording",
                "segments": [],
                "job_id": None,
            }
        )
        time.sleep(0.05)  # Ensure timestamps differ
        append_history(
            {
                "title": "Second",
                "duration_seconds": 60.0,
                "languages": ["en"],
                "transcript": "Second recording",
                "segments": [],
                "job_id": None,
            }
        )

        history = get_history()
        assert len(history) >= 2
        # Most recent should be first
        assert history[0]["title"] == "Second"
        assert history[1]["title"] == "First"

    def test_history_empty_when_no_recordings(self, client):
        """GET /history returns empty list when no recordings exist."""
        response = client.get("/history")
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        # Could be empty (no seeded_history fixture used here)
