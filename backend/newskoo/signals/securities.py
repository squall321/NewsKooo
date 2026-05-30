"""Security catalog seed + entity→security linking.

Two concerns:

1. :data:`SECURITIES` — a curated seed of >=120 major, liquid, news-heavy
   instruments (US large caps, big ADRs, key ETFs/indices, plus a handful of KR
   / JP / EU names) so the signal layer has something to attach news to out of
   the box. :func:`seed_securities` idempotently upserts them by ``symbol``.

2. :func:`link_entities_to_securities` — bridges the *news* world
   (:class:`Entity` rows produced by the analyze/resolve stages) to the *market*
   world (:class:`Security`) by writing :class:`EntitySecurity` links with a
   match ``confidence``.

Linking strategy (precision-first, recall via fuzzy fallback)
-------------------------------------------------------------
Only org / product / ticker entities are considered (people/places never map to
a security). For each such entity we try, in order:

* **Exact symbol** — the entity's name or any alias, upper-cased, equals a
  security ``symbol`` (covers ticker entities like "AAPL" and aliases that carry
  the ticker). Confidence ``1.0``.
* **Exact normalized name / alias** — the entity's normalized name or any
  normalized alias equals a security's normalized name or alias. Confidence
  ``0.97`` (near-certain; only normalization differences).
* **Fuzzy name** — RapidFuzz ``token_sort_ratio`` (order-invariant, penalizes
  extra/missing words) over normalized names; the best security above
  :data:`FUZZY_THRESHOLD` (default 90/100 = 0.90) links with confidence equal to
  the similarity. The threshold is deliberately *high*: a false link pollutes a
  tradeable signal, so we favour precision over recall here.

We do our *own* light normalization (lower / strip accents / drop punctuation /
peel common corporate suffixes) rather than importing :mod:`newskoo.resolve`, to
keep the signal layer independent of the resolution layer (they evolve
separately). It is a small, self-contained reimplementation, documented inline.
"""

from __future__ import annotations

import re
import unicodedata

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.core.logging import get_logger
from newskoo.models.finance import EntitySecurity, Security
from newskoo.models.taxonomy import Entity

log = get_logger(__name__)

# Entity types that can plausibly denote a tradeable instrument.
_LINKABLE_TYPES: frozenset[str] = frozenset({"org", "organization", "product", "ticker"})

# Fuzzy name-match acceptance threshold (RapidFuzz ratio, 0..100). High by design:
# a wrong link corrupts a tradeable signal, so precision > recall here.
FUZZY_THRESHOLD: float = 90.0

# Confidence assigned to each match tier.
_CONF_SYMBOL: float = 1.0
_CONF_EXACT_NAME: float = 0.97

# Corporate legal-form / descriptor tokens peeled off the tail when normalizing a
# company name (kept small and high-precision — see module docstring).
_LEGAL_SUFFIXES: frozenset[str] = frozenset(
    {
        "inc",
        "incorporated",
        "corp",
        "corporation",
        "co",
        "company",
        "ltd",
        "limited",
        "plc",
        "llc",
        "group",
        "holdings",
        "holding",
        "sa",
        "ag",
        "se",
        "nv",
        "spa",
        "the",
    }
)

_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_WS_RE = re.compile(r"\s+", flags=re.UNICODE)


def _normalize(name: str) -> str:
    """Light, self-contained name normalization for security matching.

    NFKC → casefold → strip diacritics (NFD, drop combining marks, recompose) →
    punctuation→space → collapse whitespace → peel trailing legal-suffix tokens
    and trailing single-character tokens (the latter are abbreviation artifacts
    left when punctuation splits a legal form, e.g. "S.A." → "s a" → ""). Never
    strips the last remaining token, so a bare suffix-only name keeps a key.
    Returns ``""`` for empty/whitespace input.
    """
    text = unicodedata.normalize("NFKC", name).casefold()
    decomposed = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    text = unicodedata.normalize("NFC", text)
    text = _PUNCT_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    if not text:
        return ""
    parts = text.split()
    # Peel trailing legal-suffix tokens and single-character abbreviation
    # fragments (e.g. the "s"/"a" from a punctuation-split "S.A.").
    while len(parts) > 1 and (parts[-1] in _LEGAL_SUFFIXES or len(parts[-1]) == 1):
        parts = parts[:-1]
    while len(parts) > 1 and parts[0] in _LEGAL_SUFFIXES:
        parts = parts[1:]
    return " ".join(parts)


# ── Seed catalog ──────────────────────────────────────────────────────────────
# Each entry: {symbol, name, exchange, country, asset_class, aliases}.
# Curated for liquidity + news volume. Aliases carry common surface forms so the
# linker can attach Entity rows that use a short/brand/former name.
SECURITIES: list[dict] = [
    # ── US mega/large-cap tech & internet ───────────────────────────────────
    {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Apple"]},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Microsoft"]},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Nvidia"]},
    {"symbol": "AMZN", "name": "Amazon.com, Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Amazon", "Amazon.com", "AWS"]},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Alphabet", "Google"]},
    {"symbol": "GOOG", "name": "Alphabet Inc. (Class C)", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Alphabet Class C", "Google Class C"]},
    {"symbol": "META", "name": "Meta Platforms, Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Meta", "Facebook", "Meta Platforms"]},
    {"symbol": "TSLA", "name": "Tesla, Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Tesla"]},
    {"symbol": "NFLX", "name": "Netflix, Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Netflix"]},
    {"symbol": "AMD", "name": "Advanced Micro Devices, Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["AMD", "Advanced Micro Devices"]},
    {"symbol": "INTC", "name": "Intel Corporation", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Intel"]},
    {"symbol": "AVGO", "name": "Broadcom Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Broadcom"]},
    {"symbol": "QCOM", "name": "QUALCOMM Incorporated", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Qualcomm"]},
    {"symbol": "TXN", "name": "Texas Instruments Incorporated", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Texas Instruments"]},
    {"symbol": "MU", "name": "Micron Technology, Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Micron"]},
    {"symbol": "ORCL", "name": "Oracle Corporation", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Oracle"]},
    {"symbol": "CRM", "name": "Salesforce, Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Salesforce"]},
    {"symbol": "ADBE", "name": "Adobe Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Adobe"]},
    {"symbol": "CSCO", "name": "Cisco Systems, Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Cisco"]},
    {"symbol": "IBM", "name": "International Business Machines Corporation", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["IBM"]},
    {"symbol": "NOW", "name": "ServiceNow, Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["ServiceNow"]},
    {"symbol": "UBER", "name": "Uber Technologies, Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Uber"]},
    {"symbol": "PLTR", "name": "Palantir Technologies Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Palantir"]},
    {"symbol": "SNOW", "name": "Snowflake Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Snowflake"]},
    {"symbol": "SHOP", "name": "Shopify Inc.", "exchange": "NYSE", "country": "CA", "asset_class": "equity", "aliases": ["Shopify"]},
    {"symbol": "PYPL", "name": "PayPal Holdings, Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["PayPal"]},
    {"symbol": "MSTR", "name": "MicroStrategy Incorporated", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["MicroStrategy"]},
    # ── US financials ────────────────────────────────────────────────────────
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["JPMorgan", "JP Morgan", "JPMorgan Chase"]},
    {"symbol": "BAC", "name": "Bank of America Corporation", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Bank of America", "BofA"]},
    {"symbol": "WFC", "name": "Wells Fargo & Company", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Wells Fargo"]},
    {"symbol": "C", "name": "Citigroup Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Citigroup", "Citi"]},
    {"symbol": "GS", "name": "The Goldman Sachs Group, Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Goldman Sachs", "Goldman"]},
    {"symbol": "MS", "name": "Morgan Stanley", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Morgan Stanley"]},
    {"symbol": "BLK", "name": "BlackRock, Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["BlackRock"]},
    {"symbol": "BRK.B", "name": "Berkshire Hathaway Inc. (Class B)", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Berkshire Hathaway", "Berkshire"]},
    {"symbol": "V", "name": "Visa Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Visa"]},
    {"symbol": "MA", "name": "Mastercard Incorporated", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Mastercard"]},
    {"symbol": "AXP", "name": "American Express Company", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["American Express", "Amex"]},
    {"symbol": "SCHW", "name": "The Charles Schwab Corporation", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Charles Schwab", "Schwab"]},
    {"symbol": "COIN", "name": "Coinbase Global, Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Coinbase"]},
    # ── US healthcare / pharma ────────────────────────────────────────────────
    {"symbol": "UNH", "name": "UnitedHealth Group Incorporated", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["UnitedHealth"]},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Johnson & Johnson", "J&J"]},
    {"symbol": "LLY", "name": "Eli Lilly and Company", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Eli Lilly", "Lilly"]},
    {"symbol": "PFE", "name": "Pfizer Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Pfizer"]},
    {"symbol": "MRK", "name": "Merck & Co., Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Merck"]},
    {"symbol": "ABBV", "name": "AbbVie Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["AbbVie"]},
    {"symbol": "TMO", "name": "Thermo Fisher Scientific Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Thermo Fisher"]},
    {"symbol": "ABT", "name": "Abbott Laboratories", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Abbott"]},
    {"symbol": "DHR", "name": "Danaher Corporation", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Danaher"]},
    {"symbol": "AMGN", "name": "Amgen Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Amgen"]},
    {"symbol": "MRNA", "name": "Moderna, Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Moderna"]},
    # ── US consumer / retail / staples ───────────────────────────────────────
    {"symbol": "WMT", "name": "Walmart Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Walmart"]},
    {"symbol": "COST", "name": "Costco Wholesale Corporation", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Costco"]},
    {"symbol": "HD", "name": "The Home Depot, Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Home Depot"]},
    {"symbol": "MCD", "name": "McDonald's Corporation", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["McDonald's", "McDonalds"]},
    {"symbol": "SBUX", "name": "Starbucks Corporation", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Starbucks"]},
    {"symbol": "NKE", "name": "NIKE, Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Nike"]},
    {"symbol": "KO", "name": "The Coca-Cola Company", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Coca-Cola", "Coca Cola", "Coke"]},
    {"symbol": "PEP", "name": "PepsiCo, Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["PepsiCo", "Pepsi"]},
    {"symbol": "PG", "name": "The Procter & Gamble Company", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Procter & Gamble", "P&G"]},
    {"symbol": "DIS", "name": "The Walt Disney Company", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Disney", "Walt Disney"]},
    {"symbol": "PM", "name": "Philip Morris International Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Philip Morris"]},
    {"symbol": "TGT", "name": "Target Corporation", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Target"]},
    {"symbol": "LULU", "name": "Lululemon Athletica Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Lululemon"]},
    # ── US industrials / energy / materials ──────────────────────────────────
    {"symbol": "XOM", "name": "Exxon Mobil Corporation", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["ExxonMobil", "Exxon"]},
    {"symbol": "CVX", "name": "Chevron Corporation", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Chevron"]},
    {"symbol": "BA", "name": "The Boeing Company", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Boeing"]},
    {"symbol": "CAT", "name": "Caterpillar Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Caterpillar"]},
    {"symbol": "GE", "name": "GE Aerospace", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["General Electric", "GE"]},
    {"symbol": "HON", "name": "Honeywell International Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Honeywell"]},
    {"symbol": "LMT", "name": "Lockheed Martin Corporation", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Lockheed Martin", "Lockheed"]},
    {"symbol": "RTX", "name": "RTX Corporation", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Raytheon", "RTX"]},
    {"symbol": "UPS", "name": "United Parcel Service, Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["UPS", "United Parcel Service"]},
    {"symbol": "F", "name": "Ford Motor Company", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Ford"]},
    {"symbol": "GM", "name": "General Motors Company", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["General Motors", "GM"]},
    {"symbol": "DE", "name": "Deere & Company", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["John Deere", "Deere"]},
    # ── US telecom / media ────────────────────────────────────────────────────
    {"symbol": "T", "name": "AT&T Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["AT&T", "ATT"]},
    {"symbol": "VZ", "name": "Verizon Communications Inc.", "exchange": "NYSE", "country": "US", "asset_class": "equity", "aliases": ["Verizon"]},
    {"symbol": "TMUS", "name": "T-Mobile US, Inc.", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["T-Mobile", "T Mobile"]},
    {"symbol": "CMCSA", "name": "Comcast Corporation", "exchange": "NASDAQ", "country": "US", "asset_class": "equity", "aliases": ["Comcast"]},
    # ── Big ADRs (non-US listed in the US) ───────────────────────────────────
    {"symbol": "TSM", "name": "Taiwan Semiconductor Manufacturing Company Limited", "exchange": "NYSE", "country": "TW", "asset_class": "adr", "aliases": ["TSMC", "Taiwan Semiconductor"]},
    {"symbol": "BABA", "name": "Alibaba Group Holding Limited", "exchange": "NYSE", "country": "CN", "asset_class": "adr", "aliases": ["Alibaba"]},
    {"symbol": "PDD", "name": "PDD Holdings Inc.", "exchange": "NASDAQ", "country": "CN", "asset_class": "adr", "aliases": ["Pinduoduo", "PDD", "Temu"]},
    {"symbol": "JD", "name": "JD.com, Inc.", "exchange": "NASDAQ", "country": "CN", "asset_class": "adr", "aliases": ["JD.com", "JD"]},
    {"symbol": "NIO", "name": "NIO Inc.", "exchange": "NYSE", "country": "CN", "asset_class": "adr", "aliases": ["NIO"]},
    {"symbol": "BIDU", "name": "Baidu, Inc.", "exchange": "NASDAQ", "country": "CN", "asset_class": "adr", "aliases": ["Baidu"]},
    {"symbol": "SHEL", "name": "Shell plc", "exchange": "NYSE", "country": "GB", "asset_class": "adr", "aliases": ["Shell", "Royal Dutch Shell"]},
    {"symbol": "BP", "name": "BP p.l.c.", "exchange": "NYSE", "country": "GB", "asset_class": "adr", "aliases": ["BP", "British Petroleum"]},
    {"symbol": "NVO", "name": "Novo Nordisk A/S", "exchange": "NYSE", "country": "DK", "asset_class": "adr", "aliases": ["Novo Nordisk"]},
    {"symbol": "TM", "name": "Toyota Motor Corporation (ADR)", "exchange": "NYSE", "country": "JP", "asset_class": "adr", "aliases": ["Toyota ADR"]},
    {"symbol": "SONY", "name": "Sony Group Corporation (ADR)", "exchange": "NYSE", "country": "JP", "asset_class": "adr", "aliases": ["Sony ADR"]},
    {"symbol": "SAP", "name": "SAP SE (ADR)", "exchange": "NYSE", "country": "DE", "asset_class": "adr", "aliases": ["SAP"]},
    {"symbol": "ASML", "name": "ASML Holding N.V.", "exchange": "NASDAQ", "country": "NL", "asset_class": "adr", "aliases": ["ASML"]},
    {"symbol": "TTE", "name": "TotalEnergies SE (ADR)", "exchange": "NYSE", "country": "FR", "asset_class": "adr", "aliases": ["TotalEnergies", "Total"]},
    {"symbol": "UL", "name": "Unilever PLC (ADR)", "exchange": "NYSE", "country": "GB", "asset_class": "adr", "aliases": ["Unilever"]},
    {"symbol": "HSBC", "name": "HSBC Holdings plc (ADR)", "exchange": "NYSE", "country": "GB", "asset_class": "adr", "aliases": ["HSBC"]},
    {"symbol": "TD", "name": "The Toronto-Dominion Bank", "exchange": "NYSE", "country": "CA", "asset_class": "equity", "aliases": ["TD Bank", "Toronto-Dominion"]},
    {"symbol": "RY", "name": "Royal Bank of Canada", "exchange": "NYSE", "country": "CA", "asset_class": "equity", "aliases": ["RBC", "Royal Bank of Canada"]},
    {"symbol": "MELI", "name": "MercadoLibre, Inc.", "exchange": "NASDAQ", "country": "AR", "asset_class": "equity", "aliases": ["MercadoLibre"]},
    {"symbol": "SE", "name": "Sea Limited", "exchange": "NYSE", "country": "SG", "asset_class": "adr", "aliases": ["Sea Limited", "Shopee", "Garena"]},
    {"symbol": "INFY", "name": "Infosys Limited (ADR)", "exchange": "NYSE", "country": "IN", "asset_class": "adr", "aliases": ["Infosys"]},
    {"symbol": "RIO", "name": "Rio Tinto Group (ADR)", "exchange": "NYSE", "country": "GB", "asset_class": "adr", "aliases": ["Rio Tinto"]},
    {"symbol": "BHP", "name": "BHP Group Limited (ADR)", "exchange": "NYSE", "country": "AU", "asset_class": "adr", "aliases": ["BHP"]},
    # ── Korea (.KS / .KQ KRX) ─────────────────────────────────────────────────
    {"symbol": "005930.KS", "name": "Samsung Electronics Co., Ltd.", "exchange": "KRX", "country": "KR", "asset_class": "equity", "aliases": ["Samsung Electronics", "Samsung", "삼성전자"]},
    {"symbol": "000660.KS", "name": "SK hynix Inc.", "exchange": "KRX", "country": "KR", "asset_class": "equity", "aliases": ["SK Hynix", "SK하이닉스"]},
    {"symbol": "035420.KS", "name": "NAVER Corporation", "exchange": "KRX", "country": "KR", "asset_class": "equity", "aliases": ["Naver", "네이버"]},
    {"symbol": "035720.KS", "name": "Kakao Corp.", "exchange": "KRX", "country": "KR", "asset_class": "equity", "aliases": ["Kakao", "카카오"]},
    {"symbol": "005380.KS", "name": "Hyundai Motor Company", "exchange": "KRX", "country": "KR", "asset_class": "equity", "aliases": ["Hyundai Motor", "Hyundai", "현대자동차"]},
    {"symbol": "051910.KS", "name": "LG Chem, Ltd.", "exchange": "KRX", "country": "KR", "asset_class": "equity", "aliases": ["LG Chem", "LG화학"]},
    {"symbol": "373220.KS", "name": "LG Energy Solution, Ltd.", "exchange": "KRX", "country": "KR", "asset_class": "equity", "aliases": ["LG Energy Solution"]},
    # ── Japan (.T TSE) ────────────────────────────────────────────────────────
    {"symbol": "7203.T", "name": "Toyota Motor Corporation", "exchange": "TSE", "country": "JP", "asset_class": "equity", "aliases": ["Toyota", "トヨタ"]},
    {"symbol": "6758.T", "name": "Sony Group Corporation", "exchange": "TSE", "country": "JP", "asset_class": "equity", "aliases": ["Sony", "ソニー"]},
    {"symbol": "6861.T", "name": "Keyence Corporation", "exchange": "TSE", "country": "JP", "asset_class": "equity", "aliases": ["Keyence"]},
    {"symbol": "9984.T", "name": "SoftBank Group Corp.", "exchange": "TSE", "country": "JP", "asset_class": "equity", "aliases": ["SoftBank", "ソフトバンク"]},
    {"symbol": "7974.T", "name": "Nintendo Co., Ltd.", "exchange": "TSE", "country": "JP", "asset_class": "equity", "aliases": ["Nintendo", "任天堂"]},
    {"symbol": "8306.T", "name": "Mitsubishi UFJ Financial Group, Inc.", "exchange": "TSE", "country": "JP", "asset_class": "equity", "aliases": ["Mitsubishi UFJ", "MUFG"]},
    {"symbol": "6098.T", "name": "Recruit Holdings Co., Ltd.", "exchange": "TSE", "country": "JP", "asset_class": "equity", "aliases": ["Recruit Holdings"]},
    # ── Europe (local listings) ───────────────────────────────────────────────
    {"symbol": "MC.PA", "name": "LVMH Moët Hennessy Louis Vuitton SE", "exchange": "EPA", "country": "FR", "asset_class": "equity", "aliases": ["LVMH", "Louis Vuitton"]},
    {"symbol": "OR.PA", "name": "L'Oréal S.A.", "exchange": "EPA", "country": "FR", "asset_class": "equity", "aliases": ["L'Oreal", "LOreal"]},
    {"symbol": "AIR.PA", "name": "Airbus SE", "exchange": "EPA", "country": "FR", "asset_class": "equity", "aliases": ["Airbus"]},
    {"symbol": "SIE.DE", "name": "Siemens AG", "exchange": "XETRA", "country": "DE", "asset_class": "equity", "aliases": ["Siemens"]},
    {"symbol": "VOW3.DE", "name": "Volkswagen AG", "exchange": "XETRA", "country": "DE", "asset_class": "equity", "aliases": ["Volkswagen", "VW"]},
    {"symbol": "MBG.DE", "name": "Mercedes-Benz Group AG", "exchange": "XETRA", "country": "DE", "asset_class": "equity", "aliases": ["Mercedes-Benz", "Mercedes", "Daimler"]},
    {"symbol": "BMW.DE", "name": "Bayerische Motoren Werke AG", "exchange": "XETRA", "country": "DE", "asset_class": "equity", "aliases": ["BMW"]},
    {"symbol": "NESN.SW", "name": "Nestlé S.A.", "exchange": "SIX", "country": "CH", "asset_class": "equity", "aliases": ["Nestle", "Nestlé"]},
    {"symbol": "ROG.SW", "name": "Roche Holding AG", "exchange": "SIX", "country": "CH", "asset_class": "equity", "aliases": ["Roche"]},
    {"symbol": "NOVN.SW", "name": "Novartis AG", "exchange": "SIX", "country": "CH", "asset_class": "equity", "aliases": ["Novartis"]},
    {"symbol": "AZN.L", "name": "AstraZeneca PLC", "exchange": "LSE", "country": "GB", "asset_class": "equity", "aliases": ["AstraZeneca"]},
    {"symbol": "ULVR.L", "name": "Unilever PLC", "exchange": "LSE", "country": "GB", "asset_class": "equity", "aliases": ["Unilever UK"]},
    {"symbol": "SAN.MC", "name": "Banco Santander, S.A.", "exchange": "BME", "country": "ES", "asset_class": "equity", "aliases": ["Santander"]},
    # ── Key ETFs / indices ────────────────────────────────────────────────────
    {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "exchange": "NYSEARCA", "country": "US", "asset_class": "etf", "aliases": ["SPDR S&P 500", "S&P 500 ETF"]},
    {"symbol": "VOO", "name": "Vanguard S&P 500 ETF", "exchange": "NYSEARCA", "country": "US", "asset_class": "etf", "aliases": ["Vanguard S&P 500"]},
    {"symbol": "IVV", "name": "iShares Core S&P 500 ETF", "exchange": "NYSEARCA", "country": "US", "asset_class": "etf", "aliases": ["iShares Core S&P 500"]},
    {"symbol": "QQQ", "name": "Invesco QQQ Trust", "exchange": "NASDAQ", "country": "US", "asset_class": "etf", "aliases": ["Invesco QQQ", "QQQ"]},
    {"symbol": "DIA", "name": "SPDR Dow Jones Industrial Average ETF Trust", "exchange": "NYSEARCA", "country": "US", "asset_class": "etf", "aliases": ["Dow Jones ETF", "DIA"]},
    {"symbol": "IWM", "name": "iShares Russell 2000 ETF", "exchange": "NYSEARCA", "country": "US", "asset_class": "etf", "aliases": ["Russell 2000 ETF"]},
    {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF", "exchange": "NYSEARCA", "country": "US", "asset_class": "etf", "aliases": ["Vanguard Total Stock Market"]},
    {"symbol": "EEM", "name": "iShares MSCI Emerging Markets ETF", "exchange": "NYSEARCA", "country": "US", "asset_class": "etf", "aliases": ["Emerging Markets ETF"]},
    {"symbol": "GLD", "name": "SPDR Gold Shares", "exchange": "NYSEARCA", "country": "US", "asset_class": "etf", "aliases": ["Gold ETF", "SPDR Gold"]},
    {"symbol": "TLT", "name": "iShares 20+ Year Treasury Bond ETF", "exchange": "NASDAQ", "country": "US", "asset_class": "etf", "aliases": ["20 Year Treasury ETF"]},
    {"symbol": "ARKK", "name": "ARK Innovation ETF", "exchange": "NYSEARCA", "country": "US", "asset_class": "etf", "aliases": ["ARK Innovation"]},
    {"symbol": "XLK", "name": "Technology Select Sector SPDR Fund", "exchange": "NYSEARCA", "country": "US", "asset_class": "etf", "aliases": ["Technology Sector ETF"]},
    {"symbol": "XLF", "name": "Financial Select Sector SPDR Fund", "exchange": "NYSEARCA", "country": "US", "asset_class": "etf", "aliases": ["Financial Sector ETF"]},
    {"symbol": "XLE", "name": "Energy Select Sector SPDR Fund", "exchange": "NYSEARCA", "country": "US", "asset_class": "etf", "aliases": ["Energy Sector ETF"]},
    {"symbol": "^GSPC", "name": "S&P 500 Index", "exchange": "INDEX", "country": "US", "asset_class": "index", "aliases": ["S&P 500", "SP500", "S&P500"]},
    {"symbol": "^IXIC", "name": "NASDAQ Composite Index", "exchange": "INDEX", "country": "US", "asset_class": "index", "aliases": ["Nasdaq Composite", "NASDAQ Composite"]},
    {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "exchange": "INDEX", "country": "US", "asset_class": "index", "aliases": ["Dow Jones", "Dow", "DJIA"]},
    {"symbol": "^RUT", "name": "Russell 2000 Index", "exchange": "INDEX", "country": "US", "asset_class": "index", "aliases": ["Russell 2000"]},
    {"symbol": "^VIX", "name": "CBOE Volatility Index", "exchange": "INDEX", "country": "US", "asset_class": "index", "aliases": ["VIX", "Volatility Index"]},
    {"symbol": "^N225", "name": "Nikkei 225 Index", "exchange": "INDEX", "country": "JP", "asset_class": "index", "aliases": ["Nikkei 225", "Nikkei"]},
    {"symbol": "^KS11", "name": "KOSPI Composite Index", "exchange": "INDEX", "country": "KR", "asset_class": "index", "aliases": ["KOSPI", "코스피"]},
    {"symbol": "^FTSE", "name": "FTSE 100 Index", "exchange": "INDEX", "country": "GB", "asset_class": "index", "aliases": ["FTSE 100", "FTSE"]},
    {"symbol": "^GDAXI", "name": "DAX Index", "exchange": "INDEX", "country": "DE", "asset_class": "index", "aliases": ["DAX"]},
    {"symbol": "^STOXX50E", "name": "EURO STOXX 50 Index", "exchange": "INDEX", "country": "EU", "asset_class": "index", "aliases": ["EURO STOXX 50", "STOXX 50"]},
    {"symbol": "^HSI", "name": "Hang Seng Index", "exchange": "INDEX", "country": "HK", "asset_class": "index", "aliases": ["Hang Seng"]},
    # ── Crypto (a few; the catalog is asset-class-agnostic) ──────────────────
    {"symbol": "BTC-USD", "name": "Bitcoin USD", "exchange": "CRYPTO", "country": None, "asset_class": "crypto", "aliases": ["Bitcoin", "BTC"]},
    {"symbol": "ETH-USD", "name": "Ethereum USD", "exchange": "CRYPTO", "country": None, "asset_class": "crypto", "aliases": ["Ethereum", "ETH"]},
    {"symbol": "SOL-USD", "name": "Solana USD", "exchange": "CRYPTO", "country": None, "asset_class": "crypto", "aliases": ["Solana", "SOL"]},
]


async def seed_securities(session: AsyncSession) -> int:
    """Idempotently upsert :data:`SECURITIES` by ``symbol``.

    Existing rows (matched on ``symbol``) have their name/exchange/mic/country/
    asset_class refreshed and aliases merged (union, order-preserving); missing
    rows are inserted. Flushes so ids are assigned; does not commit (the caller's
    ``session_scope`` owns the transaction). Returns the number of rows
    inserted + updated (i.e. ``len(SECURITIES)``).
    """
    existing_rows = (await session.execute(select(Security))).scalars().all()
    by_symbol = {s.symbol: s for s in existing_rows}

    touched = 0
    for spec in SECURITIES:
        symbol = spec["symbol"]
        row = by_symbol.get(symbol)
        if row is None:
            session.add(
                Security(
                    symbol=symbol,
                    name=spec["name"],
                    exchange=spec.get("exchange"),
                    mic=spec.get("mic"),
                    country=spec.get("country"),
                    asset_class=spec["asset_class"],
                    aliases=list(spec.get("aliases", [])),
                    metadata_=dict(spec.get("metadata", {})),
                )
            )
        else:
            row.name = spec["name"]
            row.exchange = spec.get("exchange")
            row.mic = spec.get("mic")
            row.country = spec.get("country")
            row.asset_class = spec["asset_class"]
            merged = list(row.aliases or [])
            seen = {a.casefold() for a in merged}
            for a in spec.get("aliases", []):
                if a.casefold() not in seen:
                    merged.append(a)
                    seen.add(a.casefold())
            row.aliases = merged
        touched += 1

    await session.flush()
    log.info("signals.seed_securities", count=touched)
    return touched


def _security_keys(sec: Security) -> tuple[set[str], set[str]]:
    """Return (symbol-keys, name/alias-keys) for a security.

    Symbol keys are upper-cased symbol + any upper-cased alias that *looks like*
    a ticker (so a security carrying its ticker as an alias still matches a
    ticker entity). Name keys are the normalized name + normalized aliases.
    """
    symbol_keys = {sec.symbol.upper()}
    name_keys: set[str] = set()
    norm_name = _normalize(sec.name)
    if norm_name:
        name_keys.add(norm_name)
    for alias in sec.aliases or []:
        norm = _normalize(alias)
        if norm:
            name_keys.add(norm)
        # An alias that is a bare ticker-ish token also counts as a symbol key.
        if alias.isupper() and alias.isascii() and 1 <= len(alias) <= 6:
            symbol_keys.add(alias.upper())
    return symbol_keys, name_keys


def _best_match(
    entity: Entity, securities: list[Security]
) -> tuple[Security, float] | None:
    """Best (security, confidence) match for ``entity`` or ``None``.

    Tiered: exact symbol (1.0) > exact normalized name/alias (0.97) > fuzzy
    ``token_sort_ratio`` over normalized names (>= :data:`FUZZY_THRESHOLD`,
    confidence = ratio/100). Returns the single best match; ties broken by tier
    then by similarity. See module docstring.
    """
    ent_surface = [entity.name, *(entity.aliases or [])]
    ent_symbol_keys = {
        s.upper() for s in ent_surface if s and s.isascii() and len(s) <= 12
    }
    ent_name_keys = {k for k in (_normalize(s) for s in ent_surface) if k}

    best: tuple[Security, float] | None = None
    for sec in securities:
        sym_keys, name_keys = _security_keys(sec)
        # Tier 1: exact symbol.
        if ent_symbol_keys & sym_keys:
            return sec, _CONF_SYMBOL  # symbols are unique → unambiguous, return now
        # Tier 2: exact normalized name / alias.
        if ent_name_keys & name_keys:
            if best is None or best[1] < _CONF_EXACT_NAME:
                best = (sec, _CONF_EXACT_NAME)
            continue
        # Tier 3: fuzzy over normalized names (skip if a tier-2 hit already won).
        if best is not None and best[1] >= _CONF_EXACT_NAME:
            continue
        for ek in ent_name_keys:
            for nk in name_keys:
                ratio = fuzz.token_sort_ratio(ek, nk)
                if ratio >= FUZZY_THRESHOLD and (best is None or ratio / 100.0 > best[1]):
                    best = (sec, ratio / 100.0)
    return best


async def link_entities_to_securities(session: AsyncSession) -> int:
    """Link org/product/ticker :class:`Entity` rows to :class:`Security` rows.

    For each linkable entity, finds its best matching security (see
    :func:`_best_match`) and upserts an :class:`EntitySecurity` with the match
    confidence (existing links have their confidence refreshed). Flushes; does
    not commit. Returns the number of links written (inserted + updated).

    People/places are skipped entirely (they never denote a tradeable
    instrument). Entities with no match above threshold produce no link.
    """
    securities = (await session.execute(select(Security))).scalars().all()
    if not securities:
        return 0

    entities = (
        (
            await session.execute(
                select(Entity).where(Entity.type.in_(tuple(_LINKABLE_TYPES)))
            )
        )
        .scalars()
        .all()
    )

    existing_links = (await session.execute(select(EntitySecurity))).scalars().all()
    by_pair = {(link.entity_id, link.security_id): link for link in existing_links}

    written = 0
    for entity in entities:
        match = _best_match(entity, list(securities))
        if match is None:
            continue
        sec, confidence = match
        pair = (int(entity.id), int(sec.id))
        link = by_pair.get(pair)
        if link is None:
            session.add(
                EntitySecurity(
                    entity_id=int(entity.id),
                    security_id=int(sec.id),
                    confidence=confidence,
                )
            )
        else:
            link.confidence = confidence
        written += 1

    await session.flush()
    log.info("signals.link_entities_to_securities", links=written, entities=len(entities))
    return written
