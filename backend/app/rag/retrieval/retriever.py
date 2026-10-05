import uuid
from typing import List, Optional, Dict
from app.rag.schemas import RetrievalResult
from app.rag.embeddings.service import EmbeddingService
from app.rag.retrieval.vector_search import VectorSearcher
from app.rag.retrieval.full_text_search import FullTextSearcher
from app.core.exceptions import ValidationException
from app.core.logging import logger

VALID_RETRIEVAL_MODES = {"vector", "text", "hybrid"}


class KnowledgeRetriever:
    """
    High-level retriever supporting vector, full-text, and hybrid retrieval modes.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_searcher: VectorSearcher,
        text_searcher: FullTextSearcher,
    ):
        self.embedding_service = embedding_service
        self.vector_searcher = vector_searcher
        self.text_searcher = text_searcher

    def search(
        self,
        query: str,
        top_k: int = 5,
        mode: str = "vector",
        service_id: Optional[uuid.UUID] = None,
    ) -> List[RetrievalResult]:
        """
        Executes knowledge retrieval according to the requested mode.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        clean_mode = mode.lower().strip()
        if clean_mode not in VALID_RETRIEVAL_MODES:
            raise ValidationException(
                f"Unsupported retrieval mode '{mode}'. Allowed modes are: {sorted(list(VALID_RETRIEVAL_MODES))}"
            )

        if clean_mode == "vector":
            query_embedding = self.embedding_service.embed_text(clean_query)
            results = self.vector_searcher.search(
                query_embedding=query_embedding,
                top_k=top_k,
                service_id=service_id,
            )
            logger.debug(f"Vector search returned {len(results)} chunks for query: '{clean_query[:40]}...'")
            return results

        elif clean_mode == "text":
            results = self.text_searcher.search(
                query=clean_query,
                top_k=top_k,
                service_id=service_id,
            )
            logger.debug(f"Full-text search returned {len(results)} chunks for query: '{clean_query[:40]}...'")
            return results

        elif clean_mode == "hybrid":
            # 1. Fetch dense candidates
            query_embedding = self.embedding_service.embed_text(clean_query)
            dense_results = self.vector_searcher.search(
                query_embedding=query_embedding,
                top_k=top_k * 2,
                service_id=service_id,
            )

            # 2. Fetch sparse candidates
            sparse_results = self.text_searcher.search(
                query=clean_query,
                top_k=top_k * 2,
                service_id=service_id,
            )

            # 3. Simple hybrid score blending (70% dense + 30% sparse)
            combined: Dict[uuid.UUID, RetrievalResult] = {}
            dense_scores: Dict[uuid.UUID, float] = {}
            sparse_scores: Dict[uuid.UUID, float] = {}

            for res in dense_results:
                combined[res.chunk_id] = res
                dense_scores[res.chunk_id] = res.score

            max_sparse = max((r.score for r in sparse_results), default=1.0)
            if max_sparse <= 0.0:
                max_sparse = 1.0

            for res in sparse_results:
                if res.chunk_id not in combined:
                    combined[res.chunk_id] = res
                sparse_scores[res.chunk_id] = res.score / max_sparse

            # Calculate fused score
            fused_list: List[RetrievalResult] = []
            for chunk_id, res in combined.items():
                d_score = dense_scores.get(chunk_id, 0.0)
                s_score = sparse_scores.get(chunk_id, 0.0)
                fused_score = round(0.7 * d_score + 0.3 * s_score, 4)

                fused_item = res.model_copy()
                fused_item.score = fused_score
                fused_list.append(fused_item)

            fused_list.sort(key=lambda x: x.score, reverse=True)
            return fused_list[:top_k]

        return []
