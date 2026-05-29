"""Tests for the compiled C++ extension ``newskoo_native``.

Skipped automatically when the extension has not been built (the pure-Python
fallbacks in ``newskoo.core.accel`` are exercised by ``test_foundation.py``).
"""

from __future__ import annotations

import pytest

native = pytest.importorskip("newskoo_native")


def test_normalize_collapses_whitespace_and_lowercases() -> None:
    assert native.normalize("  Hello\t WORLD\n") == "hello world"


def test_normalize_preserves_non_ascii_bytes() -> None:
    # Multilingual text must survive byte-for-byte (only ASCII is lowercased).
    text = "  서울   증시  "
    assert native.normalize(text) == "서울 증시"


def test_simhash_near_duplicate_small_distance() -> None:
    a = native.simhash64("The quick brown fox jumps over the lazy dog")
    b = native.simhash64("The quick brown fox jumps over the lazy dogs")
    c = native.simhash64("Completely unrelated text about economics and markets")
    near = native.hamming(a, b)
    far = native.hamming(a, c)
    assert near < far
    assert near <= 6  # near-dup should be well within the dedup threshold band


def test_hamming_identity_is_zero() -> None:
    h = native.simhash64("identical content hashes to the same value")
    assert native.hamming(h, h) == 0


def test_simhash_tokens_matches_string_path() -> None:
    text = "the quick brown fox"
    from_string = native.simhash64(text)
    from_tokens = native.simhash_tokens(["the", "quick", "brown", "fox"])
    assert from_string == from_tokens


def test_hamming_table_batched() -> None:
    q = native.simhash64("alpha beta gamma delta")
    others = [
        native.simhash64("alpha beta gamma delta"),
        native.simhash64("alpha beta gamma delta epsilon"),
        native.simhash64("zeta eta theta iota kappa lambda"),
    ]
    table = native.hamming_table(q, others)
    assert len(table) == 3
    assert table[0] == 0  # exact match
    assert table[0] <= table[1] <= table[2] or table[1] <= table[2]


def test_nearest_returns_index_and_distance() -> None:
    q = native.simhash64("alpha beta gamma delta")
    others = [
        native.simhash64("zeta eta theta iota kappa lambda mu nu"),
        native.simhash64("alpha beta gamma delta"),  # exact match at index 1
    ]
    idx, dist = native.nearest(q, others)
    assert idx == 1
    assert dist == 0


def test_nearest_empty_list() -> None:
    idx, dist = native.nearest(123, [])
    assert idx == -1
    assert dist == 64
