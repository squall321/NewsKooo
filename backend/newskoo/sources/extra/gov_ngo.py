"""Extra seed bucket — GOVERNMENT / IGO / NGO / THINK-TANK official feeds.

Hand-curated, individually live-verified official feeds for the long tail of
public-institution news: central banks & financial regulators (ECB, BoE, Fed,
SNB, Bundesbank, Bank of Canada, SEC, FTC, FCA), national statistics &
indicator agencies (ONS, US Census), government press desks & ministries
(US DOJ / State / White-House-adjacent, EU Commission presscorner, gov.uk
department feeds), parliaments & courts (European Parliament, UK Judiciary,
ICC), IGOs and UN-system agencies (UN News, WHO, WTO, WIPO, UNEP, ReliefWeb,
regional development banks AfDB), NGOs (Amnesty, HRW, MSF, Greenpeace, Oxfam,
ICRC via ReliefWeb, International Crisis Group) and policy think tanks
(Brookings-adjacent, CSIS, RAND, Bruegel, PIIE, Atlantic Council, ECFR,
Carnegie via Ecoscope, Elcano).

Every ``rss`` entry below was fetched with a desktop browser User-Agent on
2026-06-03 and confirmed to return a parseable feed (``<rss>`` / ``<feed>`` /
``<rdf>`` with >= 1 real ``<item>`` / ``<entry>``). Obvious national flagships
and majors already in the main ``SEED_SOURCES`` catalog are intentionally
omitted; this bucket targets official institutional sources specifically.

Shape matches ``newskoo.sources.schemas.SourceCreate``: name, homepage_url,
feed_url, api_kind, fetch_method, region, languages, categories, bot_sensitivity.
"""

from __future__ import annotations

SOURCES: list[dict] = [
    # ── Central banks ────────────────────────────────────────────────────────
    {"name": "European Central Bank — Press", "homepage_url": "https://www.ecb.europa.eu/", "feed_url": "https://www.ecb.europa.eu/rss/press.html", "api_kind": None, "fetch_method": "rss", "region": "EU", "languages": ["en"], "categories": ["economy", "policy", "government"], "bot_sensitivity": 1},
    {"name": "Bank of England — News", "homepage_url": "https://www.bankofengland.co.uk/", "feed_url": "https://www.bankofengland.co.uk/rss/news", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["economy", "policy", "government"], "bot_sensitivity": 1},
    {"name": "Bank of England — Publications", "homepage_url": "https://www.bankofengland.co.uk/", "feed_url": "https://www.bankofengland.co.uk/rss/publications", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["economy", "policy"], "bot_sensitivity": 1},
    {"name": "US Federal Reserve — Press Releases", "homepage_url": "https://www.federalreserve.gov/", "feed_url": "https://www.federalreserve.gov/feeds/press_all.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["economy", "policy", "government"], "bot_sensitivity": 1},
    {"name": "Swiss National Bank — News", "homepage_url": "https://www.snb.ch/", "feed_url": "https://www.snb.ch/public/en/rss/news", "api_kind": None, "fetch_method": "rss", "region": "CH", "languages": ["en"], "categories": ["economy", "policy", "government"], "bot_sensitivity": 1},
    {"name": "Deutsche Bundesbank — Aktuelles", "homepage_url": "https://www.bundesbank.de/", "feed_url": "https://www.bundesbank.de/service/rss/de/633286/feed.rss", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["economy", "policy", "government"], "bot_sensitivity": 1},
    {"name": "Bank of Canada — Press Releases", "homepage_url": "https://www.bankofcanada.ca/", "feed_url": "https://www.bankofcanada.ca/content_type/press-releases/feed/", "api_kind": None, "fetch_method": "rss", "region": "CA", "languages": ["en"], "categories": ["economy", "policy", "government"], "bot_sensitivity": 1},

    # ── Financial & market regulators ────────────────────────────────────────
    {"name": "US SEC — Press Releases", "homepage_url": "https://www.sec.gov/", "feed_url": "https://www.sec.gov/news/pressreleases.rss", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["economy", "policy", "government", "security"], "bot_sensitivity": 1},
    {"name": "US FTC — Press Releases", "homepage_url": "https://www.ftc.gov/", "feed_url": "https://www.ftc.gov/feeds/press-release.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["economy", "policy", "government"], "bot_sensitivity": 1},
    {"name": "UK Financial Conduct Authority — News", "homepage_url": "https://www.fca.org.uk/", "feed_url": "https://www.fca.org.uk/news/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["economy", "policy", "government"], "bot_sensitivity": 1},

    # ── National statistics & economic indicators ────────────────────────────
    {"name": "UK Office for National Statistics — Release Calendar", "homepage_url": "https://www.ons.gov.uk/", "feed_url": "https://www.ons.gov.uk/releasecalendar?rss", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["economy", "government"], "bot_sensitivity": 1},
    {"name": "US Census Bureau — Economic Indicators", "homepage_url": "https://www.census.gov/", "feed_url": "https://www.census.gov/economic-indicators/indicator.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["economy", "government"], "bot_sensitivity": 1},
    {"name": "US Energy Information Administration — Today in Energy", "homepage_url": "https://www.eia.gov/", "feed_url": "https://www.eia.gov/rss/todayinenergy.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["economy", "energy", "government"], "bot_sensitivity": 1},

    # ── Government press desks & ministries ──────────────────────────────────
    {"name": "European Commission — Press Corner", "homepage_url": "https://ec.europa.eu/commission/presscorner/", "feed_url": "https://ec.europa.eu/commission/presscorner/api/rss?language=en", "api_kind": None, "fetch_method": "rss", "region": "EU", "languages": ["en"], "categories": ["policy", "government"], "bot_sensitivity": 1},
    {"name": "US Department of Justice — News", "homepage_url": "https://www.justice.gov/", "feed_url": "https://www.justice.gov/news/rss?type=press_release&m=1", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["government", "security", "policy"], "bot_sensitivity": 1},
    {"name": "US Department of State — Press Releases", "homepage_url": "https://www.state.gov/", "feed_url": "https://www.state.gov/rss-feed/press-releases/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["government", "policy", "security"], "bot_sensitivity": 1},
    {"name": "GOV.UK — News & Communications", "homepage_url": "https://www.gov.uk/", "feed_url": "https://www.gov.uk/search/news-and-communications.atom", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["government", "policy"], "bot_sensitivity": 1},
    {"name": "UK HM Treasury — Announcements", "homepage_url": "https://www.gov.uk/government/organisations/hm-treasury", "feed_url": "https://www.gov.uk/government/organisations/hm-treasury.atom", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["economy", "government", "policy"], "bot_sensitivity": 1},
    {"name": "UK Foreign, Commonwealth & Development Office", "homepage_url": "https://www.gov.uk/government/organisations/foreign-commonwealth-development-office", "feed_url": "https://www.gov.uk/government/organisations/foreign-commonwealth-development-office.atom", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["government", "policy", "development", "security"], "bot_sensitivity": 1},

    # ── Parliaments, courts & justice ────────────────────────────────────────
    {"name": "European Parliament — Press Releases", "homepage_url": "https://www.europarl.europa.eu/", "feed_url": "https://www.europarl.europa.eu/rss/doc/press-releases/en.xml", "api_kind": None, "fetch_method": "rss", "region": "EU", "languages": ["en"], "categories": ["government", "policy"], "bot_sensitivity": 1},
    {"name": "UK Judiciary — News & Judgments", "homepage_url": "https://www.judiciary.uk/", "feed_url": "https://www.judiciary.uk/feed/", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["government", "security", "policy"], "bot_sensitivity": 1},
    {"name": "International Criminal Court — News", "homepage_url": "https://www.icc-cpi.int/", "feed_url": "https://www.icc-cpi.int/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["security", "policy", "government"], "bot_sensitivity": 1},

    # ── IGOs & UN-system agencies ────────────────────────────────────────────
    {"name": "UN News — All", "homepage_url": "https://news.un.org/", "feed_url": "https://news.un.org/feed/subscribe/en/news/all/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["policy", "development", "security", "government"], "bot_sensitivity": 1},
    {"name": "UN News — Health", "homepage_url": "https://news.un.org/en/news/topic/health", "feed_url": "https://news.un.org/feed/subscribe/en/news/topic/health/feed/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["health", "development", "policy"], "bot_sensitivity": 1},
    {"name": "World Health Organization — News", "homepage_url": "https://www.who.int/", "feed_url": "https://www.who.int/rss-feeds/news-english.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["health", "policy", "government"], "bot_sensitivity": 1},
    {"name": "World Trade Organization — Latest News", "homepage_url": "https://www.wto.org/", "feed_url": "https://www.wto.org/library/rss/latest_news_e.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["economy", "policy", "government"], "bot_sensitivity": 1},
    {"name": "WIPO — Press Room", "homepage_url": "https://www.wipo.int/", "feed_url": "https://www.wipo.int/pressroom/en/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["economy", "policy", "government"], "bot_sensitivity": 1},
    {"name": "UN Environment Programme — News", "homepage_url": "https://www.unep.org/", "feed_url": "https://www.unep.org/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["climate", "development", "policy"], "bot_sensitivity": 1},
    {"name": "ReliefWeb — Updates", "homepage_url": "https://reliefweb.int/", "feed_url": "https://reliefweb.int/updates/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["development", "security", "policy"], "bot_sensitivity": 1},
    {"name": "ReliefWeb — Headlines", "homepage_url": "https://reliefweb.int/headlines", "feed_url": "https://reliefweb.int/headlines/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["development", "security", "policy"], "bot_sensitivity": 1},

    # ── Regional development banks ───────────────────────────────────────────
    {"name": "African Development Bank — News & Events", "homepage_url": "https://www.afdb.org/", "feed_url": "https://www.afdb.org/en/news-and-events/rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["development", "economy", "policy"], "bot_sensitivity": 1},

    # ── NGOs / humanitarian / rights ─────────────────────────────────────────
    {"name": "Amnesty International — News", "homepage_url": "https://www.amnesty.org/", "feed_url": "https://www.amnesty.org/en/feed/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["security", "policy", "development"], "bot_sensitivity": 1},
    {"name": "Human Rights Watch — News", "homepage_url": "https://www.hrw.org/", "feed_url": "https://www.hrw.org/rss/news", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["security", "policy", "development"], "bot_sensitivity": 1},
    {"name": "Medecins Sans Frontieres (MSF) — Global", "homepage_url": "https://www.msf.org/", "feed_url": "https://www.msf.org/rss/all", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["health", "development", "security"], "bot_sensitivity": 1},
    {"name": "Greenpeace International — News", "homepage_url": "https://www.greenpeace.org/international/", "feed_url": "https://www.greenpeace.org/international/feed/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["climate", "policy", "development"], "bot_sensitivity": 1},
    {"name": "Oxfam International — News", "homepage_url": "https://www.oxfam.org/", "feed_url": "https://www.oxfam.org/en/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["development", "policy", "economy"], "bot_sensitivity": 1},
    {"name": "International Crisis Group — Latest", "homepage_url": "https://www.crisisgroup.org/", "feed_url": "https://www.crisisgroup.org/rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["security", "policy", "development"], "bot_sensitivity": 1},

    # ── Think tanks ──────────────────────────────────────────────────────────
    {"name": "CSIS — Latest", "homepage_url": "https://www.csis.org/", "feed_url": "https://www.csis.org/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["policy", "security", "economy"], "bot_sensitivity": 1},
    {"name": "RAND Corporation — News Releases", "homepage_url": "https://www.rand.org/", "feed_url": "https://www.rand.org/news/press.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["policy", "security"], "bot_sensitivity": 1},
    {"name": "RAND Corporation — Commentary", "homepage_url": "https://www.rand.org/", "feed_url": "https://www.rand.org/blog.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["policy", "security"], "bot_sensitivity": 1},
    {"name": "Bruegel — Latest", "homepage_url": "https://www.bruegel.org/", "feed_url": "https://www.bruegel.org/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "EU", "languages": ["en"], "categories": ["economy", "policy"], "bot_sensitivity": 1},
    {"name": "Peterson Institute for International Economics — Update", "homepage_url": "https://www.piie.com/", "feed_url": "https://www.piie.com/rss/update.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["economy", "policy"], "bot_sensitivity": 1},
    {"name": "Atlantic Council — Latest", "homepage_url": "https://www.atlanticcouncil.org/", "feed_url": "https://www.atlanticcouncil.org/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["policy", "security", "economy"], "bot_sensitivity": 1},
    {"name": "European Council on Foreign Relations (ECFR)", "homepage_url": "https://ecfr.eu/", "feed_url": "https://ecfr.eu/feed/", "api_kind": None, "fetch_method": "rss", "region": "EU", "languages": ["en"], "categories": ["policy", "security"], "bot_sensitivity": 1},
    {"name": "OECD Ecoscope (Economics blog)", "homepage_url": "https://oecdecoscope.blog/", "feed_url": "https://oecdecoscope.blog/feed/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["economy", "policy"], "bot_sensitivity": 1},
    {"name": "Real Instituto Elcano", "homepage_url": "https://www.realinstitutoelcano.org/en/", "feed_url": "https://www.realinstitutoelcano.org/en/feed/", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["en"], "categories": ["policy", "security", "economy"], "bot_sensitivity": 1},

    # ── Government science / public-health / space agencies ──────────────────
    {"name": "NASA — Breaking News", "homepage_url": "https://www.nasa.gov/", "feed_url": "https://www.nasa.gov/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "government"], "bot_sensitivity": 1},
    {"name": "European Space Agency — Our Activities", "homepage_url": "https://www.esa.int/", "feed_url": "https://www.esa.int/rssfeed/Our_Activities", "api_kind": None, "fetch_method": "rss", "region": "EU", "languages": ["en"], "categories": ["science", "government"], "bot_sensitivity": 1},
    {"name": "US CDC — Newsroom", "homepage_url": "https://www.cdc.gov/", "feed_url": "https://tools.cdc.gov/api/v2/resources/media/132608.rss", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["health", "government", "policy"], "bot_sensitivity": 1},
]
