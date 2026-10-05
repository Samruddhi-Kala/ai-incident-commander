import os
import re
import hashlib
from pathlib import Path
from typing import List, Optional
from app.rag.schemas import LoadedDocument
from app.core.logging import logger

CATEGORY_MAP = {
    "runbooks": "runbook",
    "runbook": "runbook",
    "architecture": "architecture",
    "incidents": "incident",
    "incident": "incident",
    "policies": "policy",
    "policy": "policy",
}


class MarkdownLoader:
    """
    Discovers, parses, and normalizes Markdown documentation files from the knowledge base.
    """

    @staticmethod
    def infer_category(file_path: Path) -> str:
        """
        Infers document category based on the directory hierarchy.
        """
        for part in reversed(file_path.parent.parts):
            clean_part = part.lower().strip()
            if clean_part in CATEGORY_MAP:
                return CATEGORY_MAP[clean_part]
        return "general"

    @staticmethod
    def extract_title(content: str, filename: str) -> str:
        """
        Extracts title from the first Markdown header '# ...', or derives it from the filename.
        """
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                title = stripped[2:].strip()
                if title:
                    return title

        # Fallback: humanize the filename stem (e.g. 'payment-service.md' -> 'Payment Service')
        stem = Path(filename).stem
        return stem.replace("-", " ").replace("_", " ").title()

    @staticmethod
    def compute_hash(content: str) -> str:
        """
        Computes SHA-256 hash of text content for idempotency checks.
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def load_file(self, file_path: str | Path, base_dir: Optional[str | Path] = None) -> LoadedDocument:
        """
        Loads and parses a single Markdown file into a LoadedDocument.
        """
        path = Path(file_path).resolve()
        if not path.is_file() or path.suffix.lower() != ".md":
            raise ValueError(f"File '{file_path}' is not a valid Markdown (.md) file.")

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="latin-1")

        # Format relative path if base_dir is supplied, otherwise store normalized POSIX path
        if base_dir:
            try:
                rel_path = path.relative_to(Path(base_dir).resolve()).as_posix()
            except ValueError:
                rel_path = path.as_posix()
        else:
            rel_path = path.as_posix()

        category = self.infer_category(path)
        title = self.extract_title(content, path.name)
        content_hash = self.compute_hash(content)

        return LoadedDocument(
            title=title,
            category=category,
            file_path=rel_path,
            filename=path.name,
            content=content,
            content_hash=content_hash,
            metadata={
                "absolute_path": str(path),
                "file_size_bytes": len(content.encode("utf-8")),
            },
        )

    def load_directory(self, directory_path: str | Path) -> List[LoadedDocument]:
        """
        Recursively discovers and parses all .md files in the specified directory.
        Ignores hidden files and non-markdown assets.
        """
        dir_path = Path(directory_path).resolve()
        if not dir_path.is_dir():
            logger.warning(f"Knowledge base directory '{directory_path}' does not exist.")
            return []

        documents: List[LoadedDocument] = []
        md_files = sorted(dir_path.rglob("*.md"))

        for file_path in md_files:
            # Skip hidden files or files in hidden folders (e.g. .git, .pytest_cache)
            if any(part.startswith(".") for part in file_path.parts):
                continue

            try:
                doc = self.load_file(file_path, base_dir=dir_path.parent)
                documents.append(doc)
                logger.debug(f"Loaded Markdown doc: '{doc.title}' [{doc.file_path}]")
            except Exception as e:
                logger.error(f"Failed to load Markdown file '{file_path}': {str(e)}")

        logger.info(f"Discovered and loaded {len(documents)} Markdown document(s) from '{directory_path}'")
        return documents
