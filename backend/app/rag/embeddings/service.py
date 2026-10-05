from typing import List, Optional
from app.rag.embeddings.base import BaseEmbeddingProvider
from app.rag.embeddings.fake_provider import FakeEmbeddingProvider
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import AppException


class EmbeddingService:
    """
    Unified embedding service that orchestrates the active embedding provider.
    Enforces dimensional integrity and provides seamless fallback to fake embeddings for offline environments.
    """

    def __init__(self, provider: Optional[BaseEmbeddingProvider] = None):
        if provider:
            self.provider = provider
        else:
            self.provider = self._init_provider()

    def _init_provider(self) -> BaseEmbeddingProvider:
        provider_name = settings.EMBEDDING_PROVIDER.lower().strip()

        if provider_name in ("fake", "mock", "offline"):
            logger.info(f"Using FakeEmbeddingProvider [Dimension: {settings.EMBEDDING_DIMENSION}]")
            return FakeEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)

        elif provider_name == "openai":
            if not settings.OPENAI_API_KEY:
                logger.warning(
                    "EMBEDDING_PROVIDER is 'openai' but OPENAI_API_KEY is not configured. Falling back to FakeEmbeddingProvider."
                )
                return FakeEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)

            try:
                from app.rag.embeddings.openai_provider import OpenAIEmbeddingProvider
                return OpenAIEmbeddingProvider(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.EMBEDDING_MODEL,
                    dimension=settings.EMBEDDING_DIMENSION,
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize OpenAIEmbeddingProvider ({str(e)}). Falling back to FakeEmbeddingProvider."
                )
                return FakeEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)

        else:
            logger.warning(
                f"Unknown EMBEDDING_PROVIDER '{provider_name}'. Defaulting to FakeEmbeddingProvider."
            )
            return FakeEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)

    @property
    def dimension(self) -> int:
        return self.provider.dimension

    def embed_text(self, text: str) -> List[float]:
        vector = self.provider.embed_text(text)
        self._validate_dimension(vector)
        return vector

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        vectors = self.provider.embed_texts(texts)
        for vector in vectors:
            self._validate_dimension(vector)
        return vectors

    def _validate_dimension(self, vector: List[float]) -> None:
        if len(vector) != settings.EMBEDDING_DIMENSION:
            raise AppException(
                message=(
                    f"Embedding dimension mismatch: generated vector has length {len(vector)}, "
                    f"expected {settings.EMBEDDING_DIMENSION}."
                ),
                status_code=500,
            )
