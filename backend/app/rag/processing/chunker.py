import re
from typing import List, Dict, Any, Optional
from app.rag.schemas import LoadedDocument, ChunkMetadata
from app.rag.processing.metadata import estimate_token_count, extract_service_hint
from app.core.config import settings


class HeadingChunker:
    """
    Heading-aware Markdown chunker.
    Splits documents into coherent chunks respecting Markdown section boundaries (#, ##, ###),
    attaches section titles, token counts, and chunk indexes.
    """

    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        self.chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.RAG_CHUNK_OVERLAP

    def _split_into_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Splits text by Markdown headers (#, ##, ###) while preserving the header line with each section.
        """
        lines = text.split("\n")
        sections: List[Dict[str, Any]] = []
        current_title: Optional[str] = None
        current_lines: List[str] = []

        header_regex = re.compile(r"^(#{1,4})\s+(.+)$")

        for line in lines:
            match = header_regex.match(line.strip())
            if match:
                # If we have accumulated lines, close previous section
                if current_lines:
                    section_content = "\n".join(current_lines).strip()
                    if section_content:
                        sections.append({
                            "title": current_title,
                            "content": section_content,
                        })
                    current_lines = []
                current_title = match.group(2).strip()
                current_lines.append(line)
            else:
                current_lines.append(line)

        if current_lines:
            section_content = "\n".join(current_lines).strip()
            if section_content:
                sections.append({
                    "title": current_title,
                    "content": section_content,
                })

        return sections

    def _subdivide_text(self, text: str, max_chars: int, overlap_chars: int) -> List[str]:
        """
        Subdivides long text blocks into smaller overlapping chunks on paragraph or line boundaries.
        """
        if len(text) <= max_chars:
            return [text]

        paragraphs = text.split("\n\n")
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_len = 0

        for para in paragraphs:
            para_len = len(para)
            if current_len + para_len + 2 > max_chars and current_chunk:
                joined = "\n\n".join(current_chunk).strip()
                if joined:
                    chunks.append(joined)
                
                # Overlap retention: keep the last paragraph if small enough
                if overlap_chars > 0 and len(current_chunk[-1]) <= overlap_chars:
                    current_chunk = [current_chunk[-1], para]
                    current_len = len(current_chunk[0]) + para_len + 2
                else:
                    current_chunk = [para]
                    current_len = para_len
            else:
                current_chunk.append(para)
                current_len += para_len + 2

        if current_chunk:
            joined = "\n\n".join(current_chunk).strip()
            if joined:
                # Avoid tiny trailing chunks (< 60 chars) if we already have chunks
                if chunks and len(joined) < 60:
                    chunks[-1] = chunks[-1] + "\n\n" + joined
                else:
                    chunks.append(joined)

        return chunks

    def chunk(self, doc: LoadedDocument) -> List[Dict[str, Any]]:
        """
        Processes a LoadedDocument into a list of chunk dictionaries with content and ChunkMetadata.
        """
        raw_sections = self._split_into_sections(doc.content)
        service_hint = extract_service_hint(doc.content, doc.file_path)

        # If no explicit Markdown headers found, treat entire text as one section
        if not raw_sections:
            raw_sections = [{"title": doc.title, "content": doc.content}]

        processed_chunks: List[Dict[str, Any]] = []
        chunk_idx = 0

        for section in raw_sections:
            sec_title = section["title"] or doc.title
            sec_content = section["content"]

            sub_chunks = self._subdivide_text(sec_content, self.chunk_size, self.chunk_overlap)

            for sub_content in sub_chunks:
                clean_chunk_content = sub_content.strip()
                if not clean_chunk_content:
                    continue

                token_count = estimate_token_count(clean_chunk_content)
                char_count = len(clean_chunk_content)

                chunk_meta = ChunkMetadata(
                    source_path=doc.file_path,
                    document_type=doc.category,
                    title=doc.title,
                    chunk_index=chunk_idx,
                    section_title=sec_title,
                    token_count=token_count,
                    character_count=char_count,
                    service_hint=service_hint,
                )

                processed_chunks.append({
                    "chunk_index": chunk_idx,
                    "content": clean_chunk_content,
                    "metadata": chunk_meta.model_dump(),
                })
                chunk_idx += 1

        return processed_chunks
