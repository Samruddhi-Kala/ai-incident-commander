import uuid
import pytest
from unittest.mock import MagicMock
from app.rag.schemas import RetrievalResult
from app.rag.retrieval.retriever import KnowledgeRetriever
from app.rag.embeddings.service import EmbeddingService
from app.rag.retrieval.vector_search import VectorSearcher
from app.rag.retrieval.full_text_search import FullTextSearcher
from app.core.exceptions import ValidationException


@pytest.fixture
def mock_retriever():
    mock_emb_svc = MagicMock(spec=EmbeddingService)
    mock_emb_svc.embed_text.return_value = [0.1] * 1536

    mock_vec_searcher = MagicMock(spec=VectorSearcher)
    mock_txt_searcher = MagicMock(spec=FullTextSearcher)

    cid1 = uuid.uuid4()
    did1 = uuid.uuid4()
    sample_res = [
        RetrievalResult(
            chunk_id=cid1,
            document_id=did1,
            content="Sample runbook chunk content",
            source_path="knowledge_base/runbooks/sample.md",
            document_type="runbook",
            title="Sample Runbook",
            score=0.88,
            chunk_index=0,
        )
    ]
    mock_vec_searcher.search.return_value = sample_res
    mock_txt_searcher.search.return_value = sample_res

    retriever = KnowledgeRetriever(
        embedding_service=mock_emb_svc,
        vector_searcher=mock_vec_searcher,
        text_searcher=mock_txt_searcher,
    )
    return retriever, mock_vec_searcher, mock_txt_searcher


def test_retriever_vector_mode(mock_retriever):
    retriever, mock_vec, mock_txt = mock_retriever
    results = retriever.search("payment gateway timeout", mode="vector", top_k=3)

    assert len(results) == 1
    assert results[0].title == "Sample Runbook"
    mock_vec.search.assert_called_once()
    mock_txt.search.assert_not_called()


def test_retriever_text_mode(mock_retriever):
    retriever, mock_vec, mock_txt = mock_retriever
    results = retriever.search("gateway timeout", mode="text", top_k=2)

    assert len(results) == 1
    mock_txt.search.assert_called_once()


def test_retriever_hybrid_mode(mock_retriever):
    retriever, mock_vec, mock_txt = mock_retriever
    results = retriever.search("504 timeout", mode="hybrid", top_k=5)

    assert len(results) == 1
    assert results[0].score > 0.0


def test_retriever_invalid_mode(mock_retriever):
    retriever, _, _ = mock_retriever
    with pytest.raises(ValidationException):
        retriever.search("test query", mode="unsupported_quantum_mode")


def test_retriever_empty_query(mock_retriever):
    retriever, _, _ = mock_retriever
    results = retriever.search("   ", mode="vector")
    assert results == []
