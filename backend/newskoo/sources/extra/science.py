"""Extra seed bucket — SCIENCE & ACADEMIA depth.

Hand-curated, individually live-verified feeds for the long tail of science:
peer-reviewed journals & publishers (PLOS, Cell Press, The Lancet, BMJ, eLife,
Springer, IEEE, ACM, Nature subject journals), preprint servers (bioRxiv,
medRxiv), university / research-institute press (MIT, Stanford, Harvard,
Cambridge, Berkeley, Caltech, ETH Zurich, Max Planck, Fraunhofer, CNRS, RIKEN,
JAXA, CERN), government science agencies (NASA, ESA, JPL, NIST, DOE, USGS, CDC,
WHO, ECDC, NOAA SWPC) and serious popular-science desks (Quanta, Scientific
American, Pew Research).

Every ``rss`` entry below was fetched with a desktop browser User-Agent on
2026-06-02 and confirmed to return a parseable feed with >= 1 real item, and was
de-duplicated against the existing ``SEED_SOURCES`` catalog (entries already in
the main seeds — e.g. PLOS ONE, PNAS current-issue, Science news_current,
The Lancet online, Nature main + nm.rss, NASA breaking_news, ESA Space_News —
are intentionally omitted here).

Shape matches ``newskoo.sources.schemas.SourceCreate``: name, homepage_url,
feed_url, api_kind, fetch_method, region, languages, categories, bot_sensitivity.
"""

from __future__ import annotations

SOURCES: list[dict] = [
    # ── Peer-reviewed journals: PLOS family ──────────────────────────────────
    {"name": "PLOS Biology", "homepage_url": "https://journals.plos.org/plosbiology/", "feed_url": "https://journals.plos.org/plosbiology/feed/atom", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},
    {"name": "PLOS Medicine", "homepage_url": "https://journals.plos.org/plosmedicine/", "feed_url": "https://journals.plos.org/plosmedicine/feed/atom", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "medicine"], "bot_sensitivity": 1},
    {"name": "PLOS Computational Biology", "homepage_url": "https://journals.plos.org/ploscompbiol/", "feed_url": "https://journals.plos.org/ploscompbiol/feed/atom", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},
    {"name": "PLOS Genetics", "homepage_url": "https://journals.plos.org/plosgenetics/", "feed_url": "https://journals.plos.org/plosgenetics/feed/atom", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},
    {"name": "PLOS Pathogens", "homepage_url": "https://journals.plos.org/plospathogens/", "feed_url": "https://journals.plos.org/plospathogens/feed/atom", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology", "medicine"], "bot_sensitivity": 1},
    {"name": "PLOS Climate", "homepage_url": "https://journals.plos.org/climate/", "feed_url": "https://journals.plos.org/climate/feed/atom", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "climate"], "bot_sensitivity": 1},

    # ── Peer-reviewed journals: Cell Press ───────────────────────────────────
    {"name": "Cell (Current Issue)", "homepage_url": "https://www.cell.com/cell/home", "feed_url": "https://www.cell.com/cell/current.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},
    {"name": "Cell Reports (In Press)", "homepage_url": "https://www.cell.com/cell-reports/home", "feed_url": "https://www.cell.com/cell-reports/inpress.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},
    {"name": "Neuron (Current Issue)", "homepage_url": "https://www.cell.com/neuron/home", "feed_url": "https://www.cell.com/neuron/current.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology", "medicine"], "bot_sensitivity": 1},
    {"name": "Molecular Cell (Current Issue)", "homepage_url": "https://www.cell.com/molecular-cell/home", "feed_url": "https://www.cell.com/molecular-cell/current.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},
    {"name": "Trends in Cell Biology", "homepage_url": "https://www.cell.com/trends/cell-biology/home", "feed_url": "https://www.cell.com/trends/cell-biology/current.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},

    # ── Peer-reviewed journals: The Lancet family ────────────────────────────
    {"name": "The Lancet (Current Issue)", "homepage_url": "https://www.thelancet.com/", "feed_url": "https://www.thelancet.com/rssfeed/lancet_current.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "medicine"], "bot_sensitivity": 1},
    {"name": "The Lancet Infectious Diseases (Online First)", "homepage_url": "https://www.thelancet.com/journals/laninf/home", "feed_url": "https://www.thelancet.com/rssfeed/laninf_online.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "medicine"], "bot_sensitivity": 1},
    {"name": "The Lancet Oncology (Current Issue)", "homepage_url": "https://www.thelancet.com/journals/lanonc/home", "feed_url": "https://www.thelancet.com/rssfeed/lanonc_current.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "medicine"], "bot_sensitivity": 1},

    # ── Peer-reviewed journals: BMJ / eLife / Springer ───────────────────────
    {"name": "The BMJ (Recent)", "homepage_url": "https://www.bmj.com/", "feed_url": "https://www.bmj.com/rss/recent.xml", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["science", "medicine"], "bot_sensitivity": 1},
    {"name": "eLife (Recent Articles)", "homepage_url": "https://elifesciences.org/", "feed_url": "https://elifesciences.org/rss/recent.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology", "medicine"], "bot_sensitivity": 1},
    {"name": "SpringerLink (Latest Articles)", "homepage_url": "https://link.springer.com/", "feed_url": "https://link.springer.com/search.rss?query=&facet-content-type=Article", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science"], "bot_sensitivity": 1},

    # ── Nature subject journals (distinct from the main Nature feed) ─────────
    {"name": "Nature Physics", "homepage_url": "https://www.nature.com/nphys/", "feed_url": "https://www.nature.com/nphys.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "physics"], "bot_sensitivity": 1},
    {"name": "Nature Communications", "homepage_url": "https://www.nature.com/ncomms/", "feed_url": "https://www.nature.com/ncomms.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science"], "bot_sensitivity": 1},
    {"name": "Nature Biotechnology", "homepage_url": "https://www.nature.com/nbt/", "feed_url": "https://www.nature.com/nbt.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},
    {"name": "Nature Astronomy", "homepage_url": "https://www.nature.com/natastron/", "feed_url": "https://www.nature.com/natastron.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "space"], "bot_sensitivity": 1},
    {"name": "Nature Climate Change", "homepage_url": "https://www.nature.com/nclimate/", "feed_url": "https://www.nature.com/nclimate.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "climate"], "bot_sensitivity": 1},
    {"name": "Nature Materials", "homepage_url": "https://www.nature.com/nmat/", "feed_url": "https://www.nature.com/nmat.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "materials"], "bot_sensitivity": 1},
    {"name": "Nature Energy", "homepage_url": "https://www.nature.com/nenergy/", "feed_url": "https://www.nature.com/nenergy.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "energy"], "bot_sensitivity": 1},
    {"name": "Nature Machine Intelligence", "homepage_url": "https://www.nature.com/natmachintell/", "feed_url": "https://www.nature.com/natmachintell.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "ai"], "bot_sensitivity": 1},
    {"name": "Nature Chemistry", "homepage_url": "https://www.nature.com/nchem/", "feed_url": "https://www.nature.com/nchem.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "chemistry"], "bot_sensitivity": 1},
    {"name": "Nature Nanotechnology", "homepage_url": "https://www.nature.com/nnano/", "feed_url": "https://www.nature.com/nnano.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "materials"], "bot_sensitivity": 1},

    # ── Open-access mega-journal: Frontiers (per-subject feeds) ──────────────
    {"name": "Frontiers in Microbiology", "homepage_url": "https://www.frontiersin.org/journals/microbiology", "feed_url": "https://www.frontiersin.org/journals/microbiology/rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},
    {"name": "Frontiers in Neuroscience", "homepage_url": "https://www.frontiersin.org/journals/neuroscience", "feed_url": "https://www.frontiersin.org/journals/neuroscience/rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology", "medicine"], "bot_sensitivity": 1},
    {"name": "Frontiers in Immunology", "homepage_url": "https://www.frontiersin.org/journals/immunology", "feed_url": "https://www.frontiersin.org/journals/immunology/rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "medicine"], "bot_sensitivity": 1},
    {"name": "Frontiers in Psychology", "homepage_url": "https://www.frontiersin.org/journals/psychology", "feed_url": "https://www.frontiersin.org/journals/psychology/rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science"], "bot_sensitivity": 1},
    {"name": "Frontiers in Physics", "homepage_url": "https://www.frontiersin.org/journals/physics", "feed_url": "https://www.frontiersin.org/journals/physics/rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "physics"], "bot_sensitivity": 1},
    {"name": "Frontiers in Marine Science", "homepage_url": "https://www.frontiersin.org/journals/marine-science", "feed_url": "https://www.frontiersin.org/journals/marine-science/rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "climate"], "bot_sensitivity": 1},
    {"name": "Frontiers in Public Health", "homepage_url": "https://www.frontiersin.org/journals/public-health", "feed_url": "https://www.frontiersin.org/journals/public-health/rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "medicine"], "bot_sensitivity": 1},
    {"name": "Frontiers in Artificial Intelligence", "homepage_url": "https://www.frontiersin.org/journals/artificial-intelligence", "feed_url": "https://www.frontiersin.org/journals/artificial-intelligence/rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "ai"], "bot_sensitivity": 1},

    # ── Preprint servers ─────────────────────────────────────────────────────
    {"name": "bioRxiv (All Subjects)", "homepage_url": "https://www.biorxiv.org/", "feed_url": "https://connect.biorxiv.org/biorxiv_xml.php?subject=all", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},
    {"name": "medRxiv (All Subjects)", "homepage_url": "https://www.medrxiv.org/", "feed_url": "https://connect.medrxiv.org/medrxiv_xml.php?subject=all", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "medicine"], "bot_sensitivity": 1},

    # ── Engineering / computing society publications ─────────────────────────
    {"name": "IEEE Spectrum", "homepage_url": "https://spectrum.ieee.org/", "feed_url": "https://spectrum.ieee.org/feeds/feed.rss", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "ai", "materials", "energy"], "bot_sensitivity": 1},
    {"name": "Communications of the ACM", "homepage_url": "https://cacm.acm.org/", "feed_url": "https://cacm.acm.org/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "ai"], "bot_sensitivity": 1},

    # ── Government / agency science: space ───────────────────────────────────
    {"name": "NASA (All News)", "homepage_url": "https://www.nasa.gov/", "feed_url": "https://www.nasa.gov/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "space"], "bot_sensitivity": 1},
    {"name": "NASA News Releases", "homepage_url": "https://www.nasa.gov/news-release/", "feed_url": "https://www.nasa.gov/news-release/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "space"], "bot_sensitivity": 1},
    {"name": "NASA Science", "homepage_url": "https://science.nasa.gov/", "feed_url": "https://science.nasa.gov/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "space"], "bot_sensitivity": 1},
    {"name": "NASA JPL News", "homepage_url": "https://www.jpl.nasa.gov/news", "feed_url": "https://www.jpl.nasa.gov/feeds/news", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "space"], "bot_sensitivity": 1},
    {"name": "ESA Space Science", "homepage_url": "https://www.esa.int/Science_Exploration/Space_Science", "feed_url": "https://www.esa.int/rssfeed/Our_Activities/Space_Science", "api_kind": None, "fetch_method": "rss", "region": "EU", "languages": ["en"], "categories": ["science", "space"], "bot_sensitivity": 1},
    {"name": "ESA Human and Robotic Exploration", "homepage_url": "https://www.esa.int/Science_Exploration/Human_and_Robotic_Exploration", "feed_url": "https://www.esa.int/rssfeed/Our_Activities/Human_and_Robotic_Exploration", "api_kind": None, "fetch_method": "rss", "region": "EU", "languages": ["en"], "categories": ["science", "space"], "bot_sensitivity": 1},
    {"name": "ESA Observing the Earth", "homepage_url": "https://www.esa.int/Applications/Observing_the_Earth", "feed_url": "https://www.esa.int/rssfeed/Our_Activities/Observing_the_Earth", "api_kind": None, "fetch_method": "rss", "region": "EU", "languages": ["en"], "categories": ["science", "space", "climate"], "bot_sensitivity": 1},
    {"name": "JAXA Press Releases", "homepage_url": "https://global.jaxa.jp/", "feed_url": "https://global.jaxa.jp/rss/press.rdf", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["en"], "categories": ["science", "space"], "bot_sensitivity": 1},
    {"name": "CERN News", "homepage_url": "https://home.cern/news", "feed_url": "https://home.cern/feed/", "api_kind": None, "fetch_method": "rss", "region": "CH", "languages": ["en"], "categories": ["science", "physics"], "bot_sensitivity": 1},

    # ── Government / agency science: health, earth, standards, energy ────────
    {"name": "NIST News", "homepage_url": "https://www.nist.gov/news-events/news", "feed_url": "https://www.nist.gov/news-events/news/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "materials", "physics"], "bot_sensitivity": 1},
    {"name": "US Department of Energy", "homepage_url": "https://www.energy.gov/", "feed_url": "https://www.energy.gov/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "energy"], "bot_sensitivity": 1},
    {"name": "USGS Technical Announcements", "homepage_url": "https://www.usgs.gov/news", "feed_url": "https://www.usgs.gov/news/technical-announcement/feed", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "climate"], "bot_sensitivity": 1},
    {"name": "USGS Significant Earthquakes (past month)", "homepage_url": "https://earthquake.usgs.gov/earthquakes/", "feed_url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.atom", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "climate"], "bot_sensitivity": 0},
    {"name": "NOAA Space Weather Prediction Center", "homepage_url": "https://www.swpc.noaa.gov/", "feed_url": "https://www.swpc.noaa.gov/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "space", "climate"], "bot_sensitivity": 0},
    {"name": "WHO News", "homepage_url": "https://www.who.int/news", "feed_url": "https://www.who.int/rss-feeds/news-english.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "medicine"], "bot_sensitivity": 1},
    {"name": "ECDC Threats and Outbreaks", "homepage_url": "https://www.ecdc.europa.eu/en/news-events", "feed_url": "https://www.ecdc.europa.eu/en/taxonomy/term/1301/feed", "api_kind": None, "fetch_method": "rss", "region": "EU", "languages": ["en"], "categories": ["science", "medicine"], "bot_sensitivity": 1},
    {"name": "ECDC News", "homepage_url": "https://www.ecdc.europa.eu/en/news-events", "feed_url": "https://www.ecdc.europa.eu/en/taxonomy/term/1244/feed", "api_kind": None, "fetch_method": "rss", "region": "EU", "languages": ["en"], "categories": ["science", "medicine"], "bot_sensitivity": 1},
    {"name": "CDC Podcasts", "homepage_url": "https://www2c.cdc.gov/podcasts/", "feed_url": "https://tools.cdc.gov/podcasts/feed.asp?feedid=183", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "medicine"], "bot_sensitivity": 1},

    # ── Research institutes ──────────────────────────────────────────────────
    {"name": "Max Planck Society — Research News", "homepage_url": "https://www.mpg.de/en", "feed_url": "https://www.mpg.de/en/research.rss", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["en"], "categories": ["science"], "bot_sensitivity": 1},
    {"name": "Fraunhofer Research News", "homepage_url": "https://www.fraunhofer.de/en.html", "feed_url": "https://www.fraunhofer.de/en/rss/press.rss", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["en"], "categories": ["science", "materials", "energy"], "bot_sensitivity": 1},
    {"name": "CNRS News (EN)", "homepage_url": "https://www.cnrs.fr/en", "feed_url": "https://www.cnrs.fr/en/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["en"], "categories": ["science"], "bot_sensitivity": 1},
    {"name": "RIKEN Press Releases (EN)", "homepage_url": "https://www.riken.jp/en/", "feed_url": "https://www.riken.jp/en/feed/press_feed/", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["en"], "categories": ["science"], "bot_sensitivity": 1},
    {"name": "RIKEN Topics", "homepage_url": "https://www.riken.jp/", "feed_url": "https://www.riken.jp/feed/topics_feed/", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["ja", "en"], "categories": ["science"], "bot_sensitivity": 1},

    # ── University press / research news desks ───────────────────────────────
    {"name": "MIT News — Research", "homepage_url": "https://news.mit.edu/topic/research", "feed_url": "https://news.mit.edu/topic/mitresearch-rss.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science"], "bot_sensitivity": 1},
    {"name": "UC Berkeley News", "homepage_url": "https://news.berkeley.edu/", "feed_url": "https://news.berkeley.edu/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science"], "bot_sensitivity": 1},
    {"name": "ETH Zurich News", "homepage_url": "https://ethz.ch/en/news-and-events/eth-news.html", "feed_url": "https://ethz.ch/en/news-and-events/eth-news/_jcr_content.feed.rss.xml", "api_kind": None, "fetch_method": "rss", "region": "CH", "languages": ["en"], "categories": ["science"], "bot_sensitivity": 1},

    # ── Serious popular-science / research desks ─────────────────────────────
    {"name": "Scientific American (Global)", "homepage_url": "https://www.scientificamerican.com/", "feed_url": "https://feeds.feedburner.com/scientificamerican-global", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science"], "bot_sensitivity": 1},
    {"name": "Pew Research Center", "homepage_url": "https://www.pewresearch.org/", "feed_url": "https://www.pewresearch.org/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science"], "bot_sensitivity": 1},
]
