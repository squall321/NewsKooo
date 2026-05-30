"""Normalization tests: canonical keys, legal-suffix stripping, script safety."""

from __future__ import annotations

from newskoo.resolve.normalize import normalize_name, tokens


def test_org_legal_forms_collapse_to_same_key() -> None:
    keys = {
        normalize_name("Apple Inc.", "org"),
        normalize_name("Apple, Inc", "org"),
        normalize_name("APPLE INCORPORATED", "org"),
        normalize_name("Apple", "org"),
    }
    assert keys == {"apple"}


def test_samsung_strips_co_ltd_suffix_chain() -> None:
    assert normalize_name("Samsung Electronics Co., Ltd.", "org") == "samsung electronics"
    assert normalize_name("Samsung Electronics", "org") == "samsung electronics"


def test_multi_token_and_cjk_legal_suffixes_stripped() -> None:
    # English multi-token suffix.
    assert normalize_name("Foo Bar Pty Ltd", "org") == "foo bar"
    # Japanese kabushiki-gaisha suffix stripped, base name preserved.
    assert normalize_name("トヨタ 株式会社", "org") == "トヨタ"
    # Chinese joint-stock suffix.
    assert normalize_name("阿里巴巴 股份有限公司", "org") == "阿里巴巴"


def test_diacritics_stripped_for_person() -> None:
    assert normalize_name("José Mourinho", "person") == "jose mourinho"
    assert normalize_name("Müller", "person") == "muller"
    # Person keeps token order (no reordering of given/family names).
    assert normalize_name("  José   Mourinho  ", "person") == "jose mourinho"


def test_person_does_not_strip_legal_suffix_tokens() -> None:
    # "Co" is a legal suffix only for orgs; a person named with such a token keeps it.
    assert normalize_name("Jane Co", "person") == "jane co"


def test_cjk_and_arabic_scripts_preserved() -> None:
    # CJK ideographs are not Latinized or dropped.
    assert normalize_name("삼성전자", "org") == "삼성전자"
    assert normalize_name("中国移动", "org") == "中国移动"
    # Arabic base letters preserved; the key is non-empty and keeps the letters.
    key = normalize_name("شركة آبل", "org")
    assert "ا" in key or "آ" in key or "بل" in key  # noqa: RUF001 (Arabic is the subject)
    assert key  # non-empty


def test_empty_and_whitespace_yield_empty_key() -> None:
    assert normalize_name("", "org") == ""
    assert normalize_name("   ", "person") == ""
    # A bare suffix does not collapse to empty (keeps the final token).
    assert normalize_name("Inc", "org") == "inc"


def test_tokens_are_normalized_and_order_preserving() -> None:
    assert tokens("JPMorgan Chase & Co.") == ["jpmorgan", "chase", "co"]
    assert tokens("José Mourinho") == ["jose", "mourinho"]
    assert tokens("") == []


def test_fullwidth_and_compatibility_forms_normalized() -> None:
    # Full-width Latin → ASCII via NFKC.
    assert normalize_name("ＡＢＣ", "product") == "abc"  # noqa: RUF001 (fullwidth is the subject)
    # Ligature decomposition.
    assert normalize_name("ﬁle", "product") == "file"
