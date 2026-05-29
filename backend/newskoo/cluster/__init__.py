"""Dedup + event clustering (Phase 5).

Two cooperating pieces operating on top of the structured store:

* :mod:`newskoo.cluster.dedup` — near-duplicate detection via 64-bit SimHash
  Hamming distance (C++ accelerated when ``newskoo_native`` is built). Flags an
  incoming article as a near-duplicate of a recently-seen one within
  ``settings.dedup_hamming_threshold``.
* :mod:`newskoo.cluster.events` — cross-source / cross-language clustering of
  articles into **events** using pgvector cosine similarity over embeddings;
  attaches to the nearest event above ``settings.cluster_similarity_threshold``
  or seeds a new one.
"""

from newskoo.cluster.dedup import NearDuplicateResult, find_near_duplicate
from newskoo.cluster.events import assign_event

__all__ = [
    "NearDuplicateResult",
    "assign_event",
    "find_near_duplicate",
]
