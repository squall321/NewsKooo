"""Analyze extractor + embedding tests with an injected fake provider (no network).

The fake provider returns canned, schema-shaped JSON; we assert ``analyze``
dispatches per kind, validates against the Pydantic models, and that
``embed_texts`` enforces the configured dimension.
"""

from __future__ import annotations

import pytest
from newskoo.analyze import embeddings as emb_mod
from newskoo.analyze.embeddings import embed_texts
from newskoo.analyze.extractors import analyze
from newskoo.core.contracts import AnalysisKind
from newskoo.llm.base import ChatMessage, EmbeddingResult, LLMProvider, LLMResponse, Role

_CANNED: dict[str, dict] = {
    "entities": {
        "entities": [
            {"name": "Société Générale", "type": "org", "salience": 0.9, "sentiment": -0.2}
        ]
    },
    "keywords": {"keywords": [{"term": "taux directeur", "weight": 0.8}]},
    "topics": {
        "topics": [{"slug": "economy/markets", "label": "Markets", "confidence": 0.75}]
    },
    "sentiment": {"polarity": -0.4, "label": "negative"},
    "summary": {"summary": "Une banque centrale relève ses taux."},
}


class FakeProvider(LLMProvider):
    """Records the last extract call; returns canned JSON keyed by the schema's prop."""

    name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[list[ChatMessage], dict]] = []

    async def chat(self, messages, *, model=None, max_tokens=None, temperature=None):
        return LLMResponse(text="", model="fake", provider=self.name)

    async def extract(self, messages: list[ChatMessage], schema: dict, *, model=None) -> dict:
        self.calls.append((messages, schema))
        # Identify the kind from the top-level required property name.
        top_prop = schema["required"][0]
        mapping = {
            "entities": "entities",
            "keywords": "keywords",
            "topics": "topics",
            "polarity": "sentiment",
            "summary": "summary",
        }
        return _CANNED[mapping[top_prop]]

    async def embed(self, texts, *, model=None):
        return EmbeddingResult(
            vectors=[[0.0] * 4 for _ in texts], model="fake", provider=self.name, dim=4
        )


@pytest.mark.parametrize(
    ("kind", "key"),
    [
        (AnalysisKind.ENTITIES, "entities"),
        (AnalysisKind.KEYWORDS, "keywords"),
        (AnalysisKind.TOPICS, "topics"),
        (AnalysisKind.SENTIMENT, "polarity"),
        (AnalysisKind.SUMMARY, "summary"),
    ],
)
async def test_analyze_dispatch_returns_schema_shape(kind: AnalysisKind, key: str) -> None:
    provider = FakeProvider()
    result = await analyze(
        kind, "Le corps de l'article.", title="Titre", language="fr", provider=provider
    )
    assert key in result
    # The system block is cached and the user block carries title/body/lang.
    messages, _schema = provider.calls[-1]
    assert messages[0].role == Role.SYSTEM and messages[0].cache is True
    user = messages[-1].content
    assert "Titre" in user and "fr" in user and "Le corps" in user


async def test_analyze_entities_normalises_via_model() -> None:
    provider = FakeProvider()
    result = await analyze(
        AnalysisKind.ENTITIES, "body", title=None, language=None, provider=provider
    )
    entity = result["entities"][0]
    assert entity["name"] == "Société Générale"
    assert entity["type"] == "org"
    assert 0.0 <= entity["salience"] <= 1.0


async def test_analyze_rejects_embedding_kind() -> None:
    provider = FakeProvider()
    with pytest.raises(ValueError, match="embeddings"):
        await analyze(AnalysisKind.EMBEDDING, "body", provider=provider)


async def test_analyze_rejects_empty_text() -> None:
    provider = FakeProvider()
    with pytest.raises(ValueError, match="non-empty"):
        await analyze(AnalysisKind.SUMMARY, "   ", provider=provider)


# ── embeddings dimension enforcement ──────────────────────────────────────────


async def test_embed_texts_passes_when_dim_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    _force_dim(monkeypatch, 4)
    provider = FakeProvider()
    vectors = await embed_texts(["a", "b"], provider=provider)
    assert vectors == [[0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]]


async def test_embed_texts_raises_on_dim_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    _force_dim(monkeypatch, 1024)  # provider returns dim 4 → mismatch
    provider = FakeProvider()
    with pytest.raises(ValueError, match="dimension mismatch"):
        await embed_texts(["a"], provider=provider)


async def test_embed_texts_raises_on_count_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    _force_dim(monkeypatch, 4)

    class ShortProvider(FakeProvider):
        async def embed(self, texts, *, model=None):
            return EmbeddingResult(
                vectors=[[0.0, 0.0, 0.0, 0.0]], model="fake", provider=self.name, dim=4
            )

    with pytest.raises(ValueError, match="count mismatch"):
        await embed_texts(["a", "b"], provider=ShortProvider())


async def test_embed_texts_empty_returns_empty() -> None:
    assert await embed_texts([], provider=FakeProvider()) == []


def _force_dim(monkeypatch: pytest.MonkeyPatch, dim: int) -> None:
    """Make embed_texts see ``embedding_dim == dim`` regardless of env."""
    settings = emb_mod.get_settings()
    monkeypatch.setattr(settings, "embedding_dim", dim, raising=False)
