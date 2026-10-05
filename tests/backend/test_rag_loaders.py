import tempfile
from pathlib import Path
from app.rag.loaders.markdown_loader import MarkdownLoader


def test_markdown_loader_single_file():
    """
    Test loading a single markdown file with header and category inference.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        runbooks_dir = Path(tmpdir) / "runbooks"
        runbooks_dir.mkdir()
        md_file = runbooks_dir / "checkout-service.md"
        md_file.write_text("# Checkout Service Runbook\n\nRunbook instructions here.", encoding="utf-8")

        loader = MarkdownLoader()
        doc = loader.load_file(md_file, base_dir=tmpdir)

        assert doc.title == "Checkout Service Runbook"
        assert doc.category == "runbook"
        assert doc.filename == "checkout-service.md"
        assert "Runbook instructions here." in doc.content
        assert len(doc.content_hash) == 64


def test_markdown_loader_title_fallback():
    """
    Test title extraction fallback to filename when no # header exists.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_file = Path(tmpdir) / "database-recovery.md"
        doc_file.write_text("No top-level markdown heading here.", encoding="utf-8")

        loader = MarkdownLoader()
        doc = loader.load_file(doc_file)

        assert doc.title == "Database Recovery"
        assert doc.category == "general"


def test_markdown_loader_directory_discovery():
    """
    Test recursive discovery of markdown files and ignoring non-markdown and hidden files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "architecture").mkdir()
        (base / "incidents").mkdir()
        (base / ".hidden_dir").mkdir()

        (base / "architecture" / "arch.md").write_text("# Architecture\nDetails", encoding="utf-8")
        (base / "incidents" / "inc1.md").write_text("# Incident 1\nDetails", encoding="utf-8")
        (base / "architecture" / "diagram.png").write_bytes(b"binary data")
        (base / ".hidden_dir" / "secret.md").write_text("# Secret", encoding="utf-8")

        loader = MarkdownLoader()
        docs = loader.load_directory(base)

        assert len(docs) == 2
        categories = {d.category for d in docs}
        assert "architecture" in categories
        assert "incident" in categories
