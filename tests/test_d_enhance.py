"""
Module D — Enhance Endpoints (LLM-powered)
TC-D01 to TC-D07
"""

from unittest.mock import patch

import pytest


class TestEnhanceCleanup:
    """TC-D01: Cleanup endpoint."""

    def test_d01_cleanup_returns_cleaned_text(self, client, mock_ollama):
        """TC-D01: POST /enhance/cleanup returns cleaned transcript."""
        response = client.post(
            "/enhance/cleanup",
            json={"text": "um so like the meeting was uh about the new product launch"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "text" in body
        assert isinstance(body["text"], str)
        assert len(body["text"]) > 0
        # Verify llm_complete was called with a cleanup prompt
        mock_ollama["llm_complete"].assert_called_once()
        call_args = mock_ollama["llm_complete"].call_args
        assert "Clean up" in call_args[0][0] or "cleanup" in str(call_args)


class TestEnhanceSummarize:
    """TC-D02: Summarize endpoint."""

    def test_d02_summarize_returns_summary(self, client, mock_ollama):
        """TC-D02: POST /enhance/summarize returns a summary."""
        response = client.post(
            "/enhance/summarize",
            json={"text": "Speaker 1: We need to launch the product by Q3. Speaker 2: I agree, let's set up a timeline."},
        )
        assert response.status_code == 200
        body = response.json()
        assert "summary" in body
        assert isinstance(body["summary"], str)
        assert len(body["summary"]) > 0


class TestEnhanceActionItems:
    """TC-D03: Action items endpoint."""

    def test_d03_action_items_returns_list(self, client):
        """TC-D03: POST /enhance/action-items returns items array."""
        with patch(
            "backend.services.ollama_service.llm_complete",
            return_value="- Complete the report by Friday\n- Book the venue\n- Send invitations",
        ):
            response = client.post(
                "/enhance/action-items",
                json={"text": "John will complete the report by Friday. Sarah needs to book the venue."},
            )
        assert response.status_code == 200
        body = response.json()
        assert "items" in body
        assert isinstance(body["items"], list)
        assert len(body["items"]) >= 2


class TestEnhanceTranslate:
    """TC-D04: Translation endpoint."""

    def test_d04_translate_to_target_language(self, client, mock_ollama):
        """TC-D04: POST /enhance/translate returns translated text."""
        response = client.post(
            "/enhance/translate",
            json={"text": "Hello, how are you?", "target_language": "Spanish"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "text" in body
        assert isinstance(body["text"], str)
        # Verify prompt contains the target language
        call_args = mock_ollama["llm_complete"].call_args
        assert "Spanish" in call_args[0][0]


class TestEnhanceTitle:
    """TC-D05: Auto-title endpoint."""

    def test_d05_auto_title_returns_title(self, client, mock_ollama):
        """TC-D05: POST /enhance/title returns a short title."""
        response = client.post(
            "/enhance/title",
            json={"text": "We discussed the Q3 product launch timeline and marketing strategy."},
        )
        assert response.status_code == 200
        body = response.json()
        assert "title" in body
        assert isinstance(body["title"], str)
        assert len(body["title"]) > 0


class TestEnhanceEdgeCases:
    """TC-D06 / TC-D07: Edge cases and error handling."""

    def test_d06_cleanup_with_empty_text(self, client, mock_ollama):
        """TC-D06: POST /enhance/cleanup with empty text does not crash."""
        response = client.post("/enhance/cleanup", json={"text": ""})
        assert response.status_code == 200
        body = response.json()
        assert "text" in body

    def test_d07_enhance_fails_gracefully_when_ollama_down(self, client):
        """TC-D07: When Ollama is down, enhance endpoints return 502."""
        from backend.app.core.exceptions import LLMServiceError

        with patch(
            "backend.services.ollama_service.llm_complete",
            side_effect=LLMServiceError("Connection refused"),
        ):
            response = client.post(
                "/enhance/summarize",
                json={"text": "Some transcript text here."},
            )
        assert response.status_code == 502
        assert "LLM service failed" in response.json()["detail"]

    def test_enhance_cleanup_missing_text_field(self, client):
        """POST /enhance/cleanup without text field returns 422."""
        response = client.post("/enhance/cleanup", json={})
        assert response.status_code == 422

    def test_enhance_translate_missing_target_language(self, client):
        """POST /enhance/translate without target_language returns 422."""
        response = client.post("/enhance/translate", json={"text": "Hello"})
        assert response.status_code == 422
