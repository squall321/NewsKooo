"""LLM extraction dispatch for the analyze stage.

One coroutine per :class:`AnalysisKind` (entities/keywords/topics/sentiment/
summary) plus a :func:`analyze` dispatcher. Each builds a cached system prompt
plus a user prompt carrying the article ``title`` + ``body`` and delegates to
``LLMProvider.extract(messages, schema)``, then validates the returned dict
against the kind's Pydantic model.

The system prompt is flagged ``cache=True`` so Anthropic caches the stable
instruction prefix across the many articles processed by the worker. Prompts
instruct the model to reason in the article's ORIGINAL language while emitting
canonical English category labels where applicable (ADR-0005).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from newskoo.analyze.schemas import model_for, schema_for
from newskoo.core.contracts import AnalysisKind
from newskoo.core.logging import get_logger
from newskoo.llm.base import ChatMessage, LLMProvider, Role
from newskoo.llm.registry import get_provider

log = get_logger(__name__)

# Per-kind system instruction. Shared cacheable preamble + a kind-specific task.
_BASE_SYSTEM = (
    "You are NewsKoo's multilingual news analysis engine. You analyze news "
    "articles in their ORIGINAL language without translating them. Work "
    "directly on the source text. Be precise and conservative: only report what "
    "the text supports. Return structured output via the provided schema/tool — "
    "never add commentary."
)

_KIND_INSTRUCTIONS: dict[AnalysisKind, str] = {
    AnalysisKind.ENTITIES: (
        "Task: extract the salient named entities (people, organizations, "
        "products, places, tickers, events). Keep each entity 'name' in the "
        "article's original language, but classify 'type' using the canonical "
        "English enum. Score 'salience' (0..1) by importance to the article and "
        "'sentiment' (-1..1) for the tone toward that entity."
    ),
    AnalysisKind.KEYWORDS: (
        "Task: extract the most informative keywords and key phrases. Keep each "
        "'term' in the article's original language. Score 'weight' (0..1) by "
        "how central the term is to the article's content."
    ),
    AnalysisKind.TOPICS: (
        "Task: classify the article into hierarchical taxonomy topics. Emit each "
        "'slug' and 'label' in canonical English (e.g. slug "
        "'economy/markets/equities', label 'Equities') so topics aggregate "
        "across languages. Score 'confidence' (0..1)."
    ),
    AnalysisKind.SENTIMENT: (
        "Task: assess the overall sentiment of the article as a whole. Provide a "
        "'polarity' float in -1..1 and a categorical 'label' "
        "(negative/neutral/positive)."
    ),
    AnalysisKind.SUMMARY: (
        "Task: write a concise 2-4 sentence summary capturing the key facts. "
        "Write the summary in the article's ORIGINAL language."
    ),
}


def _system_message(kind: AnalysisKind) -> ChatMessage:
    instruction = _KIND_INSTRUCTIONS[kind]
    return ChatMessage(
        role=Role.SYSTEM,
        content=f"{_BASE_SYSTEM}\n\n{instruction}",
        cache=True,
    )


def _user_message(text: str, *, title: str | None, language: str | None) -> ChatMessage:
    parts: list[str] = []
    if language:
        parts.append(f"Article language (ISO): {language}")
    if title:
        parts.append(f"Title: {title}")
    parts.append("Body:")
    parts.append(text)
    return ChatMessage(role=Role.USER, content="\n".join(parts))


def _build_messages(
    kind: AnalysisKind, text: str, *, title: str | None, language: str | None
) -> list[ChatMessage]:
    return [
        _system_message(kind),
        _user_message(text, title=title, language=language),
    ]


async def _run(
    kind: AnalysisKind,
    text: str,
    *,
    title: str | None,
    language: str | None,
    provider: LLMProvider,
) -> dict:
    """Extract + validate for one kind. Returns the normalised dict."""
    messages = _build_messages(kind, text, title=title, language=language)
    raw = await provider.extract(messages, schema_for(kind))
    model = model_for(kind)
    # Validate/normalise; ``model_dump`` gives a clean JSON-serialisable dict.
    validated = model.model_validate(raw)
    return validated.model_dump(mode="json")


async def analyze_entities(
    text: str, *, title: str | None, language: str | None, provider: LLMProvider
) -> dict:
    return await _run(
        AnalysisKind.ENTITIES, text, title=title, language=language, provider=provider
    )


async def analyze_keywords(
    text: str, *, title: str | None, language: str | None, provider: LLMProvider
) -> dict:
    return await _run(
        AnalysisKind.KEYWORDS, text, title=title, language=language, provider=provider
    )


async def analyze_topics(
    text: str, *, title: str | None, language: str | None, provider: LLMProvider
) -> dict:
    return await _run(
        AnalysisKind.TOPICS, text, title=title, language=language, provider=provider
    )


async def analyze_sentiment(
    text: str, *, title: str | None, language: str | None, provider: LLMProvider
) -> dict:
    return await _run(
        AnalysisKind.SENTIMENT, text, title=title, language=language, provider=provider
    )


async def analyze_summary(
    text: str, *, title: str | None, language: str | None, provider: LLMProvider
) -> dict:
    return await _run(
        AnalysisKind.SUMMARY, text, title=title, language=language, provider=provider
    )


_DISPATCH: dict[
    AnalysisKind,
    Callable[..., Awaitable[dict]],
] = {
    AnalysisKind.ENTITIES: analyze_entities,
    AnalysisKind.KEYWORDS: analyze_keywords,
    AnalysisKind.TOPICS: analyze_topics,
    AnalysisKind.SENTIMENT: analyze_sentiment,
    AnalysisKind.SUMMARY: analyze_summary,
}


async def analyze(
    kind: AnalysisKind,
    text: str,
    *,
    title: str | None = None,
    language: str | None = None,
    provider: LLMProvider | None = None,
) -> dict:
    """Run the LLM extraction for ``kind`` over ``text``.

    Uses the configured provider (``get_provider()``) unless one is injected
    (tests pass a fake). Raises :class:`ValueError` for kinds that are not LLM
    extractions (e.g. ``EMBEDDING``/``TRANSLATION``).
    """
    handler = _DISPATCH.get(kind)
    if handler is None:
        raise ValueError(f"analyze() does not handle kind {kind!r}; use embeddings/translation")
    if not text or not text.strip():
        raise ValueError("analyze() requires non-empty text")
    prov = provider or get_provider()
    return await handler(text, title=title, language=language, provider=prov)
