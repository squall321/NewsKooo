"""Self-hosted embeddings provider tests (no network, no real model download).

A fake ``sentence_transformers`` module is injected via
``monkeypatch.setitem(sys.modules, ...)``; its ``SentenceTransformer`` returns a
recording stub whose ``.encode`` yields deterministic unit vectors of the
configured ``embedding_dim`` (a small 8 here). These tests must never require the
real package nor download a model.
"""

from __future__ import annotations

import sys
import types
from typing import Any

import pytest
from newskoo.core.config import Settings
from newskoo.llm import st_embed_provider
from newskoo.llm.base import ChatMessage, Role
from newskoo.llm.registry import _CACHE, get_provider
from newskoo.llm.st_embed_provider import STEmbeddingProvider

_DIM = 8

_SETTINGS = Settings(
    embedding_provider="st",
    embedding_st_model="BAAI/bge-m3",
    embedding_st_device="cpu",
    embedding_dim=_DIM,
)


@pytest.fixture(autouse=True)
def _clear_provider_cache():
    """Keep the registry cache from leaking provider instances between tests."""
    _CACHE.clear()
    yield
    _CACHE.clear()


class _FakeModel:
    """Stand-in for a loaded SentenceTransformer model."""

    def __init__(self, name: str, device: str, dim: int = _DIM) -> None:
        self.name = name
        self.device = device
        self._dim = dim
        self.encode_calls: list[dict[str, Any]] = []

    def encode(self, texts: list[str], *, normalize_embeddings: bool) -> list[list[float]]:
        self.encode_calls.append({"texts": texts, "normalize_embeddings": normalize_embeddings})
        # Deterministic unit vector (first component 1.0, rest 0.0) per text.
        return [[1.0] + [0.0] * (self._dim - 1) for _ in texts]


class _FakeSentenceTransformerFactory:
    """Records construction and hands back a ``_FakeModel`` (one per build)."""

    def __init__(self, dim: int = _DIM) -> None:
        self._dim = dim
        self.builds: list[_FakeModel] = []

    def __call__(self, name: str, *, device: str) -> _FakeModel:
        model = _FakeModel(name, device, dim=self._dim)
        self.builds.append(model)
        return model


@pytest.fixture
def fake_st(monkeypatch: pytest.MonkeyPatch) -> _FakeSentenceTransformerFactory:
    factory = _FakeSentenceTransformerFactory()
    module = types.ModuleType("sentence_transformers")
    module.SentenceTransformer = factory  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sentence_transformers", module)
    return factory


def _provider() -> STEmbeddingProvider:
    return STEmbeddingProvider(_SETTINGS)


# ── registration ───────────────────────────────────────────────────────────


def test_registers_under_st(fake_st: _FakeSentenceTransformerFactory) -> None:
    # Importing the module (done at top) must have registered the builder, so
    # the registry resolves "st" to our provider class.
    provider = get_provider("st")
    assert isinstance(provider, STEmbeddingProvider)
    assert provider.name == "st"


# ── embed happy path ─────────────────────────────────────────────────────────


async def test_embed_returns_vectors_of_dim(fake_st: _FakeSentenceTransformerFactory) -> None:
    provider = _provider()
    result = await provider.embed(["a", "b"])

    assert result.provider == "st"
    assert result.model == "BAAI/bge-m3"
    assert result.dim == _DIM
    assert len(result.vectors) == 2
    assert all(len(vector) == _DIM for vector in result.vectors)
    # encode was called once with normalize_embeddings=True.
    assert len(fake_st.builds) == 1
    model = fake_st.builds[0]
    assert model.encode_calls == [{"texts": ["a", "b"], "normalize_embeddings": True}]
    # Model was constructed with the configured name + device.
    assert model.name == "BAAI/bge-m3"
    assert model.device == "cpu"


async def test_model_loaded_once_across_calls(
    fake_st: _FakeSentenceTransformerFactory,
) -> None:
    provider = _provider()
    await provider.embed(["a"])
    await provider.embed(["b", "c"])

    # Only one model construction despite two embed calls.
    assert len(fake_st.builds) == 1
    assert len(fake_st.builds[0].encode_calls) == 2


async def test_embed_model_override_is_reported(
    fake_st: _FakeSentenceTransformerFactory,
) -> None:
    provider = _provider()
    result = await provider.embed(["x"], model="custom/model")
    # The resolved model name flows into the result even though the loaded model
    # is the one from settings (override affects reporting, not which model loads).
    assert result.model == "custom/model"


# ── dim enforcement ──────────────────────────────────────────────────────────


async def test_dim_mismatch_raises_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    # Fake model returns vectors of the WRONG length (dim+1).
    factory = _FakeSentenceTransformerFactory(dim=_DIM + 1)
    module = types.ModuleType("sentence_transformers")
    module.SentenceTransformer = factory  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sentence_transformers", module)

    provider = _provider()
    with pytest.raises(ValueError, match=str(_DIM)):
        await provider.embed(["a"])


# ── chat / extract are not supported ─────────────────────────────────────────


async def test_chat_not_implemented() -> None:
    provider = _provider()
    with pytest.raises(NotImplementedError, match="embedding-only"):
        await provider.chat([ChatMessage(role=Role.USER, content="hi")])


async def test_extract_not_implemented() -> None:
    provider = _provider()
    with pytest.raises(NotImplementedError, match="embedding-only"):
        await provider.extract([ChatMessage(role=Role.USER, content="hi")], {"type": "object"})


# ── missing package surfaces a clear error ───────────────────────────────────


async def test_missing_package_raises_clear_import_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _boom() -> None:
        raise ImportError(
            "The 'sentence-transformers' package is required for the self-hosted "
            "embeddings provider ('st'). Install it with the optional extra: "
            "`uv sync --extra embed-local`."
        )

    monkeypatch.setattr(st_embed_provider, "_import_sentence_transformer", _boom)
    provider = _provider()
    with pytest.raises(ImportError, match="embed-local"):
        await provider.embed(["a"])


# ── aclose drops the cached model ────────────────────────────────────────────


async def test_aclose_clears_cached_model(fake_st: _FakeSentenceTransformerFactory) -> None:
    provider = _provider()
    await provider.embed(["a"])
    assert len(fake_st.builds) == 1

    await provider.aclose()
    # After close, a fresh embed rebuilds the model.
    await provider.embed(["b"])
    assert len(fake_st.builds) == 2
