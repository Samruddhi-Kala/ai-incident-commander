from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    """
    Abstract interface for text embedding providers.
    """

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        Generates an embedding vector for a single string.
        """
        pass

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embedding vectors for a batch of strings.
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        Returns the vector dimension produced by this provider (e.g. 1536).
        """
        pass
