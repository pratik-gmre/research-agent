"""
Wraps a local multilingual embedding model so both Nepali and English
chunks/queries land in the same vector space.

Uses intfloat/multilingual-e5-large by default - it's free, runs
locally (no per-call API cost, which matters for a student project
re-indexing PDFs repeatedly), and is trained explicitly for
cross-lingual retrieval.

E5 models expect a "query: " / "passage: " prefix on the input text -
this is part of how the model was trained, not optional decoration,
and skipping it measurably hurts retrieval quality.
"""

from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import settings


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def embed_passages(texts: list[str]) -> list[list[float]]:
    """Embed document chunks for storage in the vector index."""
    model = _get_model()
    prefixed = [f"passage: {t}" for t in texts]
    vectors = model.encode(prefixed, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    """Embed a user question for similarity search."""
    model = _get_model()
    vector = model.encode(f"query: {text}", normalize_embeddings=True, show_progress_bar=False)
    return vector.tolist()
