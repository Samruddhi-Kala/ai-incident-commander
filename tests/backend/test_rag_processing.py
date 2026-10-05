from app.rag.processing.cleaner import TextCleaner
from app.rag.processing.chunker import HeadingChunker
from app.rag.processing.metadata import (
    extract_headings,
    estimate_token_count,
    extract_service_hint,
)
from app.rag.schemas import LoadedDocument


def test_text_cleaner_line_endings_and_whitespace():
    """
    Test TextCleaner normalizes Windows CRLF and removes excessive blank lines.
    """
    raw_text = "Line 1   \r\n\r\n\r\n\r\nLine 2\t  \r\n\r\n```python\r\n  x = 10\r\n```\r\n\n\n"
    cleaned = TextCleaner.clean(raw_text)

    assert "\r" not in cleaned
    assert "\n\n\n" not in cleaned
    assert "Line 1\n\nLine 2" in cleaned
    assert "  x = 10" in cleaned  # leading indent preserved in code block


def test_metadata_utilities():
    """
    Test heading extraction, token count estimation, and service hints.
    """
    sample = (
        "# Service Guide\n\n"
        "**Service Name**: `auth-service`\n\n"
        "## Authentication Setup\n"
        "Details about tokens.\n\n"
        "### Error Codes\n"
        "List of errors.\n"
    )
    headings = extract_headings(sample)
    assert len(headings) == 3
    assert headings[0] == (1, "Service Guide")
    assert headings[1] == (2, "Authentication Setup")
    assert headings[2] == (3, "Error Codes")

    hint = extract_service_hint(sample, "knowledge_base/runbooks/auth.md")
    assert hint == "auth-service"

    tokens = estimate_token_count("This is a short sample string.")
    assert tokens > 0


def test_heading_chunker_basic():
    """
    Test HeadingChunker splits on Markdown headers and preserves metadata.
    """
    content = (
        "# Payment Service Runbook\n\n"
        "Introductory content.\n\n"
        "## Overview\n"
        "Overview description.\n\n"
        "## Troubleshooting\n"
        "Diagnostic steps for timeout errors.\n"
    )
    doc = LoadedDocument(
        title="Payment Service Runbook",
        category="runbook",
        file_path="knowledge_base/runbooks/payment-service.md",
        filename="payment-service.md",
        content=content,
        content_hash="dummyhash123",
    )

    chunker = HeadingChunker(chunk_size=200, chunk_overlap=20)
    chunks = chunker.chunk(doc)

    assert len(chunks) >= 2
    for i, c in enumerate(chunks):
        assert c["chunk_index"] == i
        meta = c["metadata"]
        assert meta["source_path"] == "knowledge_base/runbooks/payment-service.md"
        assert meta["document_type"] == "runbook"
        assert "section_title" in meta
        assert meta["token_count"] > 0
