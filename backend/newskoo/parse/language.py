"""Language detection (langdetect), deterministic and returning ISO 639-1.

``langdetect`` is non-deterministic by default (random init). We seed it once at
import so repeated runs over the same text yield stable codes — important for
idempotent reprocessing. Codes are already ISO 639-1 (e.g. ``en``, ``ko``,
``zh-cn``); we trim region subtags to the bare language where present.
"""

from __future__ import annotations

from langdetect import DetectorFactory, LangDetectException, detect

from newskoo.core.logging import get_logger

log = get_logger(__name__)

# Deterministic detection across runs/processes.
DetectorFactory.seed = 0

# Minimum characters worth attempting detection on; below this langdetect is
# unreliable and we prefer to return None.
_MIN_CHARS = 3


def detect_language(text: str) -> str | None:
    """Detect the dominant language of ``text`` as an ISO 639-1 code.

    Returns ``None`` for empty/too-short input or when detection fails. Region
    subtags (e.g. ``zh-cn``) are reduced to the base language code.
    """
    if not text:
        return None
    stripped = text.strip()
    if len(stripped) < _MIN_CHARS:
        return None

    try:
        code = detect(stripped)
    except LangDetectException as exc:
        log.debug("language.detect_failed", error=str(exc))
        return None

    if not code:
        return None
    # langdetect emits things like "zh-cn"/"zh-tw"; keep the base 639-1 code.
    base = code.split("-", 1)[0].strip().lower()
    return base or None
