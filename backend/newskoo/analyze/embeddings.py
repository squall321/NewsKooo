"""Embedding helper for the analyze stage.

Wraps the configured embedding provider (``settings.embedding_provider`` —
Anthropic has none, so this is ``local`` or ``openai``) and enforces that every
returned vector matches ``settings.embedding_dim`` (the pgvector column width).
A dimension mismatch is a hard error: a silently wrong-width vector would fail
on insert or corrupt similarity search, so we surface it clearly here.
"""

from __future__ import annotations

from newskoo.core.config import get_settings
from newskoo.core.logging import get_logger
from newskoo.llm.base import LLMProvider
from newskoo.llm.registry import get_provider

log = get_logger(__name__)


async def embed_texts(
    texts: list[str],
    *,
    provider: LLMProvider | None = None,
    model: str | None = None,
) -> list[list[float]]:
    """Embed ``texts`` and return one vector per input.

    Uses ``get_provider(settings.embedding_provider)`` unless a provider is
    injected. Asserts each vector's length equals ``settings.embedding_dim`` and
    that the count matches the input — no padding/truncation is performed; a
    mismatch means the configured model/dim are inconsistent and must be fixed.
    """
    if not texts:
        return []

    settings = get_settings()
    expected_dim = settings.embedding_dim
    prov = provider or get_provider(settings.embedding_provider)

    result = await prov.embed(texts, model=model or settings.embedding_model)
    vectors = result.vectors

    if len(vectors) != len(texts):
        raise ValueError(
            f"Embedding count mismatch: requested {len(texts)} texts, "
            f"got {len(vectors)} vectors from provider {prov.name!r}."
        )
    for i, vector in enumerate(vectors):
        if len(vector) != expected_dim:
            raise ValueError(
                f"Embedding dimension mismatch at index {i}: provider {prov.name!r} "
                f"model {result.model!r} returned dim {len(vector)}, but "
                f"settings.embedding_dim is {expected_dim}. Align the embedding "
                f"model with the configured dimension (pgvector column width)."
            )
    return vectors


async def embed_text(
    text: str,
    *,
    provider: LLMProvider | None = None,
    model: str | None = None,
) -> list[float]:
    """Convenience wrapper for a single text."""
    vectors = await embed_texts([text], provider=provider, model=model)
    return vectors[0]
