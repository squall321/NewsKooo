"""Pure decision layer: pick the best existing entity or declare NEW.

This module contains *no* I/O. Given a candidate side and a list of existing
entity sides (already fetched by blocking), it scores every existing side with
:func:`newskoo.resolve.match.score`, picks the best, and decides:

* if the best score ``>= threshold`` → **MATCH** that entity;
* otherwise → **NEW** entity.

On a match it also computes ``new_aliases``: the candidate's surface forms
(its name plus any supplied aliases) whose *normalized* key is not already
covered by the matched entity's name/aliases — i.e. the genuinely novel surface
forms worth recording on the canonical entity. Surface forms are de-duplicated
by normalized key while the *original* spelling is preserved in the output
(we store the human-readable surface form, not the folded key).

Determinism: ties are broken by the existing side's position (first wins), so a
given candidate + candidate-list always yields the same decision — important for
reproducible tests and idempotent re-processing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from newskoo.resolve.match import MatchSide, score
from newskoo.resolve.normalize import normalize_name


@dataclass(slots=True)
class ExistingEntity:
    """An existing catalog entity as seen by the decision layer.

    ``id`` is the DB primary key; the remaining fields mirror :class:`MatchSide`.
    """

    id: int
    name: str
    type: str
    aliases: list[str] = field(default_factory=list)
    embedding: list[float] | None = None

    def as_side(self) -> MatchSide:
        return MatchSide(
            name=self.name,
            type=self.type,
            aliases=list(self.aliases),
            embedding=self.embedding,
        )


@dataclass(slots=True)
class ResolveDecision:
    """Outcome of resolving a candidate against existing entities.

    * ``matched_id`` — PK of the matched entity, or ``None`` when ``is_new``.
    * ``score`` — the best score observed (0.0 when there were no candidates).
    * ``is_new`` — True when no existing entity cleared the threshold.
    * ``new_aliases`` — surface forms to add to the matched entity (empty on NEW;
      on NEW the candidate's own surface forms become the new entity's aliases,
      which the service layer handles, not this decision).
    """

    matched_id: int | None
    score: float
    is_new: bool
    new_aliases: list[str] = field(default_factory=list)


def _candidate_surface_forms(candidate: MatchSide) -> list[str]:
    """Candidate name + aliases, original spelling, de-duped by normalized key."""
    seen: set[str] = set()
    forms: list[str] = []
    for form in (candidate.name, *candidate.aliases):
        if not form or not form.strip():
            continue
        key = normalize_name(form, candidate.type)
        if not key or key in seen:
            continue
        seen.add(key)
        forms.append(form)
    return forms


def _new_aliases(candidate: MatchSide, matched: ExistingEntity) -> list[str]:
    """Candidate surface forms whose normalized key the match doesn't already know."""
    known = {normalize_name(f, matched.type) for f in (matched.name, *matched.aliases)}
    known.discard("")
    out: list[str] = []
    for form in _candidate_surface_forms(candidate):
        if normalize_name(form, candidate.type) not in known:
            out.append(form)
    return out


def resolve(
    candidate: MatchSide,
    existing: list[ExistingEntity],
    *,
    threshold: float,
) -> ResolveDecision:
    """Resolve ``candidate`` against ``existing`` at ``threshold``.

    Picks the highest-scoring existing entity at or above ``threshold``; if none
    qualifies (or ``existing`` is empty) the decision is NEW. The boundary is
    inclusive: a best score *exactly* equal to ``threshold`` is a MATCH.
    """
    best_id: int | None = None
    best_side: ExistingEntity | None = None
    best_score = 0.0

    for ent in existing:
        s = score(candidate, ent.as_side())
        if s > best_score:
            best_score = s
            best_id = ent.id
            best_side = ent

    if best_side is not None and best_score >= threshold:
        return ResolveDecision(
            matched_id=best_id,
            score=best_score,
            is_new=False,
            new_aliases=_new_aliases(candidate, best_side),
        )

    return ResolveDecision(matched_id=None, score=best_score, is_new=True, new_aliases=[])
