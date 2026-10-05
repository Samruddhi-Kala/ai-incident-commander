import math
from app.rag.embeddings.fake_provider import FakeEmbeddingProvider
from app.rag.embeddings.service import EmbeddingService


def test_fake_embedding_determinism():
    """
    Test that the fake embedding provider is completely deterministic.
    """
    provider = FakeEmbeddingProvider(dimension=1536)
    text = "Database connection pool timeout in payment-service"

    v1 = provider.embed_text(text)
    v2 = provider.embed_text(text)

    assert len(v1) == 1536
    assert v1 == v2


def test_fake_embedding_different_inputs():
    """
    Test that different inputs produce distinct vectors.
    """
    provider = FakeEmbeddingProvider(dimension=1536)
    v1 = provider.embed_text("Query A: memory leak")
    v2 = provider.embed_text("Query B: network flap")

    assert v1 != v2


def test_fake_embedding_unit_normalization():
    """
    Test that generated vectors are unit-normalized (L2 norm ~ 1.0).
    """
    provider = FakeEmbeddingProvider(dimension=1536)
    vec = provider.embed_text("Sample input for norm test")

    norm_sq = sum(x * x for x in vec)
    assert math.isclose(norm_sq, 1.0, rel_tol=1e-3)


def test_fake_embedding_batch():
    """
    Test batch embedding matches individual calls.
    """
    provider = FakeEmbeddingProvider(dimension=1536)
    texts = ["First text", "Second text", "Third text"]

    batch_vecs = provider.embed_texts(texts)
    assert len(batch_vecs) == 3

    for i, t in enumerate(texts):
        single_vec = provider.embed_text(t)
        assert batch_vecs[i] == single_vec


def test_embedding_service_dimension():
    """
    Test EmbeddingService enforces and exposes correct vector dimension.
    """
    svc = EmbeddingService()
    assert svc.dimension == 1536
    vec = svc.embed_text("Hello Incident Commander")
    assert len(vec) == 1536
