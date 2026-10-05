import uuid
from app.rag.schemas import RetrievalResult
from app.rag.context.builder import ContextBuilder


def test_context_builder_empty():
    """
    Test empty results list returns NO_RELEVANT_KNOWLEDGE_FOUND.
    """
    context = ContextBuilder.build([])
    assert context == "NO_RELEVANT_KNOWLEDGE_FOUND"


def test_context_builder_formatting():
    """
    Test attribution headers and chunk content formatting.
    """
    chunk1 = RetrievalResult(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        content="Verify timeout setting in payment-service config. Default is >= 5000ms.",
        source_path="knowledge_base/runbooks/payment-service.md",
        document_type="runbook",
        title="Payment Service Runbook",
        section_title="Timeout Diagnostic Steps",
        score=0.92,
        chunk_index=0,
    )

    chunk2 = RetrievalResult(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        content="Incident postmortem: Deployment v2.1.0 reduced timeout to 500ms.",
        source_path="knowledge_base/incidents/INC-2025-08-01-payment-timeout.md",
        document_type="incident",
        title="Payment Timeout Postmortem",
        section_title="Root Cause Analysis",
        score=0.85,
        chunk_index=1,
    )

    context = ContextBuilder.build([chunk1, chunk2])

    assert "SOURCE: knowledge_base/runbooks/payment-service.md" in context
    assert "TYPE: runbook" in context
    assert "TITLE: Payment Service Runbook" in context
    assert "SECTION: Timeout Diagnostic Steps" in context
    assert "---" in context
    assert "SOURCE: knowledge_base/incidents/INC-2025-08-01-payment-timeout.md" in context
