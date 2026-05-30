"""Source credibility + article quality scoring (heuristic, bounded ``[0, 1]``).

Pure, documented formulas over observable signals — no LLM calls, no new deps:

* :mod:`source_score` — :func:`source_credibility` from crawl reliability,
  longevity, output volume, multi-source corroboration and error rate;
  :func:`compute_source_scores` persists it into ``Source.health['credibility']``.
* :mod:`article_quality` — :func:`article_quality` from structural signals
  (length sweet-spot, byline, date, language confidence, title form, near-dup,
  source prior); :func:`score_article` derives features from a stored article.
* :mod:`bias` — honest :func:`subjectivity` / :func:`sensationalism` *heuristics*
  (explicitly not ground truth) plus the :class:`LLMStanceHook` Protocol for a
  future model-based stance/bias call (interface only).

These scores are ranking/trust *priors*: search & trend ranking can multiply an
article's relevance by ``quality`` (which already folds in source credibility),
and the financial-signal layer can weight each article's impact by
``credibility * quality`` so unproven or low-quality items contribute less.
"""

from newskoo.quality.article_quality import (
    ArticleFeatures,
    article_quality,
    quality_components,
    score_article,
)
from newskoo.quality.bias import (
    LLMStanceHook,
    StanceResult,
    sensationalism,
    subjectivity,
)
from newskoo.quality.source_score import (
    SourceFeatures,
    compute_source_scores,
    credibility_components,
    source_credibility,
)

__all__ = [
    "ArticleFeatures",
    "LLMStanceHook",
    "SourceFeatures",
    "StanceResult",
    "article_quality",
    "compute_source_scores",
    "credibility_components",
    "quality_components",
    "score_article",
    "sensationalism",
    "source_credibility",
    "subjectivity",
]
