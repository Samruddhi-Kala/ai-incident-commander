from typing import List
from app.rag.schemas import RetrievalResult


class ContextBuilder:
    """
    Transforms retrieved knowledge chunks into structured, citation-attributed
    context suitable for downstream agentic consumption without invoking an LLM.
    """

    @staticmethod
    def build(results: List[RetrievalResult]) -> str:
        """
        Formats a list of RetrievalResults into a deterministic context block with source attribution.
        """
        if not results:
            return "NO_RELEVANT_KNOWLEDGE_FOUND"

        blocks: List[str] = []

        for res in results:
            header_lines = [
                f"SOURCE: {res.source_path}",
                f"TYPE: {res.document_type}",
                f"TITLE: {res.title}",
            ]
            if res.section_title and res.section_title != res.title:
                header_lines.append(f"SECTION: {res.section_title}")

            header = "\n".join(header_lines)
            block = f"{header}\n\n{res.content}"
            blocks.append(block)

        return "\n\n---\n\n".join(blocks)
