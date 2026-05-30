"""Self-hosted embeddings backend (``sentence-transformers``) for the
:class:`LLMProvider` interface.

This provider gives NewsKoo embeddings — semantic search, event clustering,
cross-language linking — with NO external LLM API. It loads a local
``sentence-transformers`` model (default ``BAAI/bge-m3``, a strong multilingual
model) once and runs encoding on the CPU/GPU.

``sentence-transformers`` is an *optional* dependency (``pyproject`` extra
``embed-local``); it pulls in ``torch`` and is heavy, so it is imported lazily
inside :func:`_import_sentence_transformer`. The module is importable without it
installed and raises a clear error only when an embed call is actually attempted.

Key behaviours:

* The model is built **once** and cached on the instance behind an
  :class:`asyncio.Lock`, so concurrent callers share a single in-memory model
  (loading it more than once would waste memory and time).
* ``embed`` offloads the synchronous, CPU/GPU-bound ``model.encode`` call to a
  worker thread via :func:`asyncio.to_thread`, keeping the event loop responsive.
  Vectors are L2-normalised (``normalize_embeddings=True``) so cosine similarity
  reduces to a dot product — what the clustering/search layer expects.
* Each returned vector's length is validated against ``settings.embedding_dim``
  (the pgvector column width); a mismatch is a hard error.
* ``chat``/``extract`` raise :class:`NotImplementedError` — this is an
  embedding-only backend.

Registers itself as ``"st"`` at import time (see
:func:`newskoo.llm.registry._load_builtin`, which lazy-imports this module for
the provider key ``"st"``).
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Protocol

from newskoo.core.config import Settings, get_settings
from newskoo.core.logging import get_logger
from newskoo.llm.base import ChatMessage, EmbeddingResult, LLMProvider, LLMResponse
from newskoo.llm.registry import register_provider

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sentence_transformers import SentenceTransformer

log = get_logger(__name__)


class _Encoder(Protocol):
    """Minimal structural type for the loaded model (what we actually call)."""

    def encode(self, texts: list[str], *, normalize_embeddings: bool) -> Any: ...


def _import_sentence_transformer() -> type[SentenceTransformer]:
    """Import :class:`SentenceTransformer` lazily with a clear error if missing."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch in tests
        raise ImportError(
            "The 'sentence-transformers' package is required for the self-hosted "
            "embeddings provider ('st'). Install it with the optional extra: "
            "`uv sync --extra embed-local` (it pulls in torch, so install it only "
            "on the embedding host)."
        ) from exc
    return SentenceTransformer


class STEmbeddingProvider(LLMProvider):
    """Local sentence-transformers embeddings backend. Safe for concurrent use:
    the model is loaded once under a lock and ``encode`` is thread-offloaded."""

    name = "st"

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._model: _Encoder | None = None
        self._lock = asyncio.Lock()

    # ── model lifecycle ──────────────────────────────────────────────────────
    async def _get_model(self) -> _Encoder:
        """Return the cached model, loading it once on first use.

        Loading happens under an :class:`asyncio.Lock` so that concurrent
        ``embed`` calls do not each construct a (heavy) model; the construction
        itself is offloaded to a thread because it can block on disk/CPU.
        """
        if self._model is not None:
            return self._model
        async with self._lock:
            if self._model is None:  # re-check after acquiring the lock
                self._model = await asyncio.to_thread(self._load_model)
        return self._model

    def _load_model(self) -> _Encoder:
        sentence_transformer = _import_sentence_transformer()
        log.info(
            "loading sentence-transformers model",
            model=self._settings.embedding_st_model,
            device=self._settings.embedding_st_device,
        )
        return sentence_transformer(
            self._settings.embedding_st_model,
            device=self._settings.embedding_st_device,
        )

    async def aclose(self) -> None:
        """Drop the cached model so its memory can be reclaimed."""
        self._model = None

    # ── LLMProvider API ──────────────────────────────────────────────────────
    async def embed(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult:
        resolved_model = model or self._settings.embedding_st_model
        encoder = await self._get_model()

        raw = await asyncio.to_thread(encoder.encode, texts, normalize_embeddings=True)
        vectors = [[float(value) for value in vector] for vector in raw]

        expected_dim = self._settings.embedding_dim
        for index, vector in enumerate(vectors):
            if len(vector) != expected_dim:
                raise ValueError(
                    f"Embedding dimension mismatch at index {index}: model "
                    f"{resolved_model!r} returned dim {len(vector)}, but "
                    f"settings.embedding_dim is {expected_dim}. Align "
                    f"embedding_st_model with embedding_dim (the pgvector column "
                    f"width) — e.g. BAAI/bge-m3 has dim 1024."
                )

        return EmbeddingResult(
            vectors=vectors,
            model=resolved_model,
            provider=self.name,
            dim=expected_dim,
            tokens=0,
        )

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        raise NotImplementedError(
            "st is an embedding-only provider; set llm_provider to "
            "anthropic/openai/local for chat."
        )

    async def extract(
        self,
        messages: list[ChatMessage],
        schema: dict,
        *,
        model: str | None = None,
    ) -> dict:
        raise NotImplementedError(
            "st is an embedding-only provider; set llm_provider to "
            "anthropic/openai/local for chat."
        )


def _build(settings: Settings) -> LLMProvider:
    return STEmbeddingProvider(settings)


register_provider("st", _build)
