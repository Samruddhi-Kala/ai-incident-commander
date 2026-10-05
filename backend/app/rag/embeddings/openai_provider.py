from typing import List, Optional
from app.rag.embeddings.base import BaseEmbeddingProvider
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import logger


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    Real embedding provider integrating OpenAI's text-embedding models (e.g. text-embedding-3-small).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dimension: Optional[int] = None,
    ):
        self._api_key = api_key or settings.OPENAI_API_KEY
        self._model = model or settings.EMBEDDING_MODEL
        self._dimension = dimension or settings.EMBEDDING_DIMENSION
        self._client = None

        if not self._api_key:
            raise AppException(
                message="OPENAI_API_KEY is not configured in settings. Set EMBEDDING_PROVIDER='fake' or provide a key.",
                status_code=500,
            )

        try:
            import openai
            self._client = openai.OpenAI(api_key=self._api_key)
        except ImportError:
            raise AppException(
                message="The 'openai' Python package is not installed. Run 'pip install openai' or use EMBEDDING_PROVIDER='fake'.",
                status_code=500,
            )

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> List[float]:
        results = self.embed_texts([text])
        return results[0]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        try:
            response = self._client.embeddings.create(
                input=texts,
                model=self._model,
                dimensions=self._dimension,
            )
            embeddings = [item.embedding for item in response.data]
            return embeddings
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {str(e)}")
            raise AppException(
                message=f"OpenAI embedding API call failed: {str(e)}",
                status_code=502,
            )
