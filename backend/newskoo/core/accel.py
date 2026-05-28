"""Acceleration facade: use the compiled ``newskoo_native`` (C++/pybind11) when
available, otherwise transparent pure-Python fallbacks. Callers import from
here and never depend on the native module directly, so the backend runs even
before the C++ extension is built.

The Phase-4 C++ module must expose: ``simhash64(str) -> int``,
``hamming(int,int) -> int``, and ``normalize(str) -> str`` with semantics
matching the fallbacks below.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

try:  # pragma: no cover - presence depends on build
    import newskoo_native as _native  # type: ignore

    HAVE_NATIVE = True
except ImportError:  # pragma: no cover
    _native = None
    HAVE_NATIVE = False

_WS = re.compile(r"\s+")
_TOKEN = re.compile(r"\w+", re.UNICODE)


def normalize(text: str) -> str:
    """Unicode NFKC + lowercase + whitespace-collapse."""
    if HAVE_NATIVE:
        return _native.normalize(text)
    text = unicodedata.normalize("NFKC", text).lower()
    return _WS.sub(" ", text).strip()


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(normalize(text))


def simhash64(text: str) -> int:
    """64-bit SimHash over word tokens (for near-duplicate detection)."""
    if HAVE_NATIVE:
        return int(_native.simhash64(text))
    bits = [0] * 64
    for tok in _tokens(text):
        h = int.from_bytes(hashlib.blake2b(tok.encode(), digest_size=8).digest(), "big")
        for i in range(64):
            bits[i] += 1 if (h >> i) & 1 else -1
    out = 0
    for i in range(64):
        if bits[i] > 0:
            out |= 1 << i
    return out


def hamming(a: int, b: int) -> int:
    """Hamming distance between two 64-bit hashes."""
    if HAVE_NATIVE:
        return int(_native.hamming(a, b))
    return ((a ^ b) & ((1 << 64) - 1)).bit_count()


def content_hash(text: str) -> bytes:
    """Stable sha256 of normalized text (revision detection)."""
    return hashlib.sha256(normalize(text).encode("utf-8")).digest()
