"""
Module E — RAG / Ask Endpoint
TC-E01 to TC-E03
"""

import json
from unittest.mock import patch

import pytest


class TestRAGAsk:
    """Tests for the RAG question-answering endpoint."""

    def test_e01_ask_about_processed_transcript(self, client, mock_ollama):
        """TC-E01: POST /ask with a valid job_id returns an answer with sources."""
        from backend.app.core.config import settings
        import numpy as np
        import faiss

        # Seed a FAISS index manually
        job_id = "test-rag-job"
        index_dir = settings.VECTOR_DIR / job_id
        index_dir.mkdir(parents=True, exist_ok=True)

        dimension = 768
        index = faiss.IndexFlatL2(dimension)
        vectors = np.array([[0.1] * dimension, [0.2] * dimension], dtype="float32")
        index.add(vectors)
        faiss.write_index(index, str(index_dir / "index.faiss"))

        metadata = [
            {"chunk_id": "0", "text": "Speaker 1: We discussed Q3 goals.", "start": 0.0, "end": 30.0},
            {"chunk_id": "1", "text": "Speaker 2: Budget allocation for marketing.", "start": 30.0, "end": 60.0},
        ]
        (index_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        response = client.post(
            "/ask",
            json={"job_id": job_id, "question": "What were the Q3 goals?"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "answer" in body
        assert isinstance(body["answer"], str)
        assert len(body["answer"]) > 0
        assert "sources" in body
        assert isinstance(body["sources"], list)
        assert len(body["sources"]) > 0
        # Sources should reference chunk IDs
        assert all(s.startswith("chunk_") for s in body["sources"])

    def test_e02_ask_with_nonexistent_job_fails(self, client, mock_ollama):
        """TC-E02: POST /ask with a non-existent job_id returns an error."""
        response = client.post(
            "/ask",
            json={"job_id": "nonexistent-job", "question": "What is this about?"},
        )
        # FAISS index doesn't exist, so this should error
        assert response.status_code in (404, 500, 422)

    def test_e03_ask_with_empty_question(self, client, mock_ollama):
        """TC-E03: POST /ask with empty question does not crash the server."""
        from backend.app.core.config import settings
        import numpy as np
        import faiss

        # Seed a FAISS index
        job_id = "test-rag-empty-q"
        index_dir = settings.VECTOR_DIR / job_id
        index_dir.mkdir(parents=True, exist_ok=True)

        dimension = 768
        index = faiss.IndexFlatL2(dimension)
        vectors = np.array([[0.1] * dimension], dtype="float32")
        index.add(vectors)
        faiss.write_index(index, str(index_dir / "index.faiss"))

        metadata = [{"chunk_id": "0", "text": "Test chunk", "start": 0.0, "end": 10.0}]
        (index_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        response = client.post(
            "/ask",
            json={"job_id": job_id, "question": ""},
        )
        # Should not crash — either returns 200 with an answer or a validation error
        assert response.status_code in (200, 422)

    def test_ask_missing_fields_returns_422(self, client):
        """POST /ask without required fields returns 422."""
        response = client.post("/ask", json={"question": "test"})
        assert response.status_code == 422

        response = client.post("/ask", json={"job_id": "test"})
        assert response.status_code == 422
