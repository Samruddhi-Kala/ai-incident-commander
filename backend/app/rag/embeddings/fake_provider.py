import math
import random
import hashlib
from typing import List
from app.rag.embeddings.base import BaseEmbeddingProvider


class FakeEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic, offline mock embedding provider for local development and testing.
    Produces unit-normalized vectors of configurable dimension (default 1536)
    without making any external API calls.
    """

    def __init__(self, dimension: int = 1536):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def _generate_vector(self, text: str) -> List[float]:
        """
        Deterministically maps text to an L2-normalized vector using SHA-256 seeded RNG.
        """
        if not text:
            # Deterministic default vector for empty string
            vec = [1.0 / math.sqrt(self._dimension)] * self._dimension
            return vec

        # Generate integer seed from SHA-256 hash of text
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        seed_val = int(digest[:16], 16)

        rng = random.Random(seed_val)
        raw = [rng.gauss(0.0, 1.0) for _ in range(self._dimension)]

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in raw))
        if norm == 0.0:
            norm = 1.0

        return [round(x / norm, 6) for x in raw]

    def embed_text(self, text: str) -> List[float]:
        return self._generate_vector(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]
