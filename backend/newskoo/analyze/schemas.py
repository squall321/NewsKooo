"""Extraction schemas for the analyze stage.

Two parallel representations per :class:`AnalysisKind`:

* a **JSON Schema** dict — handed verbatim to ``LLMProvider.extract`` (used as
  an Anthropic tool ``input_schema``, an OpenAI function ``parameters``, or an
  Ollama ``format="json"`` steering instruction);
* a small **Pydantic model** — for validating/normalising the returned dict on
  our side.

Multilingual contract (ADR-0005): the model reasons over the article's ORIGINAL
language. Free-text fields (entity ``name``, keyword ``term``, ``summary``) stay
in the original language; canonical *category* fields — entity ``type`` and
topic ``slug``/``label`` — are emitted in canonical English so they aggregate
across languages. Sentiment ``polarity`` is a float in ``[-1, 1]``.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from newskoo.core.contracts import AnalysisKind

# ── Pydantic models (server-side validation of returned dicts) ───────────────

# Canonical (English) entity types the taxonomy recognises.
ENTITY_TYPES = ("person", "org", "product", "place", "ticker", "event", "other")


class EntityItem(BaseModel):
    name: str
    type: str = "other"
    salience: float = Field(default=0.0, ge=0.0, le=1.0)
    sentiment: float = Field(default=0.0, ge=-1.0, le=1.0)


class EntitiesResult(BaseModel):
    entities: list[EntityItem] = Field(default_factory=list)


class KeywordItem(BaseModel):
    term: str
    weight: float = Field(default=0.0, ge=0.0, le=1.0)


class KeywordsResult(BaseModel):
    keywords: list[KeywordItem] = Field(default_factory=list)


class TopicItem(BaseModel):
    slug: str
    label: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class TopicsResult(BaseModel):
    topics: list[TopicItem] = Field(default_factory=list)


class SentimentResult(BaseModel):
    polarity: float = Field(default=0.0, ge=-1.0, le=1.0)
    label: str = "neutral"  # negative | neutral | positive


class SummaryResult(BaseModel):
    summary: str = ""


# ── JSON Schemas (handed to the provider's structured-extraction path) ───────

_ENTITIES_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "description": "Salient named entities mentioned in the article.",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Entity name in the article's ORIGINAL language.",
                    },
                    "type": {
                        "type": "string",
                        "description": "Canonical English entity type.",
                        "enum": list(ENTITY_TYPES),
                    },
                    "salience": {
                        "type": "number",
                        "description": "Importance to the article, 0..1.",
                    },
                    "sentiment": {
                        "type": "number",
                        "description": "Sentiment toward the entity, -1..1.",
                    },
                },
                "required": ["name", "type", "salience", "sentiment"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["entities"],
    "additionalProperties": False,
}

_KEYWORDS_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "keywords": {
            "type": "array",
            "description": "Key terms/phrases in the article's ORIGINAL language.",
            "items": {
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "Keyword or phrase."},
                    "weight": {
                        "type": "number",
                        "description": "Relevance weight, 0..1.",
                    },
                },
                "required": ["term", "weight"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["keywords"],
    "additionalProperties": False,
}

_TOPICS_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "topics": {
            "type": "array",
            "description": "Taxonomy topics the article belongs to.",
            "items": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": (
                            "Canonical English hierarchical slug, e.g. "
                            "'economy/markets/equities'."
                        ),
                    },
                    "label": {
                        "type": "string",
                        "description": "Human-readable canonical English label.",
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence, 0..1.",
                    },
                },
                "required": ["slug", "label", "confidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["topics"],
    "additionalProperties": False,
}

_SENTIMENT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "polarity": {
            "type": "number",
            "description": "Overall document sentiment, -1 (negative)..1 (positive).",
        },
        "label": {
            "type": "string",
            "description": "Categorical sentiment label.",
            "enum": ["negative", "neutral", "positive"],
        },
    },
    "required": ["polarity", "label"],
    "additionalProperties": False,
}

_SUMMARY_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": (
                "Concise 2-4 sentence summary in the article's ORIGINAL language."
            ),
        }
    },
    "required": ["summary"],
    "additionalProperties": False,
}


SCHEMAS: dict[AnalysisKind, dict] = {
    AnalysisKind.ENTITIES: _ENTITIES_SCHEMA,
    AnalysisKind.KEYWORDS: _KEYWORDS_SCHEMA,
    AnalysisKind.TOPICS: _TOPICS_SCHEMA,
    AnalysisKind.SENTIMENT: _SENTIMENT_SCHEMA,
    AnalysisKind.SUMMARY: _SUMMARY_SCHEMA,
}

MODELS: dict[AnalysisKind, type[BaseModel]] = {
    AnalysisKind.ENTITIES: EntitiesResult,
    AnalysisKind.KEYWORDS: KeywordsResult,
    AnalysisKind.TOPICS: TopicsResult,
    AnalysisKind.SENTIMENT: SentimentResult,
    AnalysisKind.SUMMARY: SummaryResult,
}


def schema_for(kind: AnalysisKind) -> dict:
    """Return the JSON Schema for ``kind`` (raises for unsupported kinds)."""
    try:
        return SCHEMAS[kind]
    except KeyError as exc:
        raise ValueError(f"No extraction schema for analysis kind: {kind}") from exc


def model_for(kind: AnalysisKind) -> type[BaseModel]:
    """Return the Pydantic validation model for ``kind``."""
    try:
        return MODELS[kind]
    except KeyError as exc:
        raise ValueError(f"No extraction model for analysis kind: {kind}") from exc
