"""Analysis (Phase 6): multi-provider LLM extraction (entities/keywords/topics/
sentiment/summary), embeddings, and the issue-detection engine
(volume/velocity anomaly detection). Consumes ``analyze.requests`` and produces
``analyze.results`` / ``issues.alerts``."""

from newskoo.analyze.embeddings import embed_text, embed_texts
from newskoo.analyze.extractors import (
    analyze,
    analyze_entities,
    analyze_keywords,
    analyze_sentiment,
    analyze_summary,
    analyze_topics,
)
from newskoo.analyze.issues import (
    IssueDetector,
    Series,
    SeriesPoint,
    compute_series_anomalies,
)
from newskoo.analyze.schemas import (
    SCHEMAS,
    EntitiesResult,
    EntityItem,
    KeywordItem,
    KeywordsResult,
    SentimentResult,
    SummaryResult,
    TopicItem,
    TopicsResult,
    model_for,
    schema_for,
)

__all__ = [
    "SCHEMAS",
    "EntitiesResult",
    "EntityItem",
    "IssueDetector",
    "KeywordItem",
    "KeywordsResult",
    "SentimentResult",
    "Series",
    "SeriesPoint",
    "SummaryResult",
    "TopicItem",
    "TopicsResult",
    "analyze",
    "analyze_entities",
    "analyze_keywords",
    "analyze_sentiment",
    "analyze_summary",
    "analyze_topics",
    "compute_series_anomalies",
    "embed_text",
    "embed_texts",
    "model_for",
    "schema_for",
]
