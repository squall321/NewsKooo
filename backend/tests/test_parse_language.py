"""Language detection tests: ISO 639-1, deterministic, multilingual.

No network. ``langdetect`` is seeded deterministically inside the module.
"""

from __future__ import annotations

from newskoo.parse.language import detect_language

_EN = (
    "Global equity markets advanced on Thursday after inflation data came in "
    "cooler than economists had expected, lifting technology shares broadly."
)
_KO = (
    "목요일 글로벌 증시는 물가 지표가 예상보다 낮게 나오면서 상승했고, "
    "기술주가 전반적으로 강세를 보였습니다."
)


def test_detect_english() -> None:
    assert detect_language(_EN) == "en"


def test_detect_korean_non_latin() -> None:
    assert detect_language(_KO) == "ko"


def test_detect_is_deterministic() -> None:
    # Same input → same code across repeated calls (seeded factory).
    assert detect_language(_EN) == detect_language(_EN)
    assert detect_language(_KO) == detect_language(_KO)


def test_empty_and_short_text_returns_none() -> None:
    assert detect_language("") is None
    assert detect_language("   ") is None
    assert detect_language("a") is None


def test_region_subtag_reduced_to_base_code() -> None:
    # Chinese often detects as zh-cn/zh-tw; we keep the bare 639-1 "zh".
    code = detect_language("这是一篇关于全球经济和金融市场的中文新闻报道文章内容。")
    assert code == "zh"
