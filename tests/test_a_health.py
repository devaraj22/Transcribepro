"""
Module A — Health Check & Server Bootstrap
TC-A01 to TC-A04
"""

import pytest


class TestHealthEndpoint:
    """TC-A01: Health endpoint returns OK."""

    def test_health_returns_200_ok(self, client):
        """TC-A01: GET /health returns 200 with {"status": "ok"}."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestStorageBootstrap:
    """TC-A02: Storage directories are auto-created on startup."""

    def test_storage_dirs_created(self, tmp_path):
        """TC-A02: ensure_storage_dirs creates all required directories."""
        from backend.app.core.config import settings
        from backend.app.utils.file_handlers import ensure_storage_dirs

        # Directories should already exist from the fixture, but let's remove
        # one to verify the function re-creates it
        import shutil
        if settings.REPORT_DIR.exists():
            shutil.rmtree(settings.REPORT_DIR)
        assert not settings.REPORT_DIR.exists()

        ensure_storage_dirs()

        assert settings.STORAGE_DIR.exists()
        assert settings.UPLOAD_DIR.exists()
        assert settings.REPORT_DIR.exists()
        assert settings.TRANSCRIPT_DIR.exists()
        assert settings.VECTOR_DIR.exists()


class TestCORS:
    """TC-A03 / TC-A04: CORS middleware allows/blocks origins."""

    def test_cors_allows_frontend_origin(self, client):
        """TC-A03: OPTIONS with frontend origin gets CORS headers."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        allow_origin = response.headers.get("access-control-allow-origin", "")
        assert allow_origin == "http://127.0.0.1:5173"

    def test_cors_blocks_unknown_origin(self, client):
        """TC-A04: OPTIONS with unknown origin does not get CORS headers."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://malicious.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        allow_origin = response.headers.get("access-control-allow-origin", "")
        assert allow_origin != "http://malicious.example.com"
