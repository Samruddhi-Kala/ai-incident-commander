import uuid
from unittest.mock import MagicMock, patch
from fastapi import status
from app.main import app
from app.db.session import get_db
from app.rag.schemas import RetrievalResult, IngestionSummary, IngestionResult


def test_api_rag_search_success(client):
    """
    Test POST /api/v1/rag/search returns valid RetrievalResponse.
    """
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    fake_res = [
        RetrievalResult(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            content="Sample retrieved content for testing.",
            source_path="knowledge_base/runbooks/test.md",
            document_type="runbook",
            title="Test Runbook",
            score=0.89,
            chunk_index=0,
        )
    ]

    with patch("app.api.v1.routes.rag.RAGService") as MockRAGService:
        mock_instance = MockRAGService.return_value
        mock_instance.search.return_value = fake_res

        payload = {
            "query": "gateway timeout error",
            "top_k": 3,
            "mode": "vector",
        }
        response = client.post("/api/v1/rag/search", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["query"] == "gateway timeout error"
        assert data["mode"] == "vector"
        assert data["total_results"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["title"] == "Test Runbook"

    app.dependency_overrides.clear()


def test_api_rag_search_validation_error(client):
    """
    Test POST /api/v1/rag/search with empty query returns 422 Unprocessable Entity.
    """
    payload = {
        "query": "",
        "top_k": 5,
        "mode": "vector",
    }
    response = client.post("/api/v1/rag/search", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_api_rag_ingest_success(client):
    """
    Test POST /api/v1/rag/ingest triggers ingestion and returns summary.
    """
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    fake_summary = IngestionSummary(
        discovered_count=4,
        processed_count=4,
        skipped_count=0,
        failed_count=0,
        total_chunks=8,
        details=[
            IngestionResult(
                file_path="knowledge_base/runbooks/payment-service.md",
                title="Payment Service Runbook",
                category="runbook",
                status="created",
                chunks_count=2,
            )
        ],
    )

    with patch("app.api.v1.routes.rag.RAGService") as MockRAGService:
        mock_instance = MockRAGService.return_value
        mock_instance.ingest_directory.return_value = fake_summary

        payload = {
            "force": True,
        }
        response = client.post("/api/v1/rag/ingest", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["discovered_count"] == 4
        assert data["processed_count"] == 4
        assert data["total_chunks"] == 8
        assert len(data["details"]) == 1

    app.dependency_overrides.clear()
