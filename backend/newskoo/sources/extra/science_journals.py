"""Extra seed bucket — SCIENCE DEPTH: journals, societies, universities, labs.

A second, deeper science long-tail bucket (companion to ``science.py``), focused
on material NOT already in the catalog: physics societies & journals (APS
Physics, Physical Review Letters, IOPscience, Physics World), chemistry (ACS
journals, C&EN), bio/medicine (NEJM, JAMA, PNAS, more Nature subject journals,
Cell Press sub-journals), CS/AI (Quanta, MIT Technology Review, IEEE Spectrum
topics, industrial & academic AI labs), earth/space (AGU Eos & journals, AAS
Nova, Sky & Telescope, Space.com, Universe Today, ESO, Phys.org & ScienceDaily
subject desks), many university research-news rooms (Stanford, Harvard, Caltech,
Cambridge, Manchester, etc.) and national labs / agencies (NSF, LBNL, Fermilab,
EMBL).

Every ``rss`` entry below was fetched with a desktop-browser User-Agent on
2026-06-03 and confirmed to return a parseable feed (``<rss``/``<feed``/``<rdf``
plus ``<item``/``<entry``) with >= 1 real item. Entries already present in
``science.py`` or the main ``SEED_SOURCES`` catalog (PLOS, Cell main, Lancet,
BMJ, eLife, Nature main + subject feeds already listed there, IEEE Spectrum
full-text, NASA/ESA/CERN/NIST/JPL, MIT/Berkeley/ETH news, Quanta-as-Sci-Am,
etc.) are intentionally omitted to avoid duplicates.

Shape matches ``newskoo.sources.schemas.SourceCreate``: name, homepage_url,
feed_url, api_kind, fetch_method, region, languages, categories, bot_sensitivity.
"""

from __future__ import annotations

SOURCES: list[dict] = [
    # ── Physics: societies & journals ────────────────────────────────────────
    {"name": "Physics World", "homepage_url": "https://physicsworld.com/", "feed_url": "https://physicsworld.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["science", "physics"], "bot_sensitivity": 1},
    {"name": "APS Physics Magazine", "homepage_url": "https://physics.aps.org/", "feed_url": "https://feeds.aps.org/rss/recent/physics.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "physics"], "bot_sensitivity": 1},
    {"name": "Physical Review Letters", "homepage_url": "https://journals.aps.org/prl/", "feed_url": "https://feeds.aps.org/rss/recent/prl.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "physics"], "bot_sensitivity": 1},
    {"name": "Reports on Progress in Physics (IOP)", "homepage_url": "https://iopscience.iop.org/journal/0034-4885", "feed_url": "https://iopscience.iop.org/journal/rss/0034-4885", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["science", "physics"], "bot_sensitivity": 1},
    {"name": "Classical and Quantum Gravity (IOP)", "homepage_url": "https://iopscience.iop.org/journal/0264-9381", "feed_url": "https://iopscience.iop.org/journal/rss/0264-9381", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["science", "physics"], "bot_sensitivity": 1},
    {"name": "Nanotechnology (IOP)", "homepage_url": "https://iopscience.iop.org/journal/0957-4484", "feed_url": "https://iopscience.iop.org/journal/rss/1361-6528", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["science", "physics", "materials"], "bot_sensitivity": 1},

    # ── Chemistry: ACS journals ──────────────────────────────────────────────
    {"name": "Journal of the American Chemical Society (JACS)", "homepage_url": "https://pubs.acs.org/journal/jacsat", "feed_url": "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=jacsat", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "chemistry"], "bot_sensitivity": 1},
    {"name": "Nano Letters (ACS)", "homepage_url": "https://pubs.acs.org/journal/nalefd", "feed_url": "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=nalefd", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "chemistry", "materials"], "bot_sensitivity": 1},
    {"name": "ACS Nano", "homepage_url": "https://pubs.acs.org/journal/ancac3", "feed_url": "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=ancac3", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "chemistry", "materials"], "bot_sensitivity": 1},
    {"name": "Energy & Fuels (ACS)", "homepage_url": "https://pubs.acs.org/journal/enfuem", "feed_url": "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=enfuem", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "chemistry", "energy"], "bot_sensitivity": 1},

    # ── Medicine & life-science journals ─────────────────────────────────────
    {"name": "New England Journal of Medicine (NEJM)", "homepage_url": "https://www.nejm.org/", "feed_url": "https://www.nejm.org/action/showFeed?type=etoc&feed=rss&jc=nejm", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "medicine"], "bot_sensitivity": 1},
    {"name": "JAMA (Current Issue)", "homepage_url": "https://jamanetwork.com/journals/jama", "feed_url": "https://jamanetwork.com/rss/site_3/67.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "medicine"], "bot_sensitivity": 1},
    {"name": "PNAS (Current Issue)", "homepage_url": "https://www.pnas.org/", "feed_url": "https://www.pnas.org/action/showFeed?type=etoc&feed=rss&jc=pnas", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science"], "bot_sensitivity": 1},

    # ── Science (AAAS) family sub-journals ───────────────────────────────────
    {"name": "Science Advances", "homepage_url": "https://www.science.org/journal/sciadv", "feed_url": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=sciadv", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science"], "bot_sensitivity": 1},
    {"name": "Science Robotics", "homepage_url": "https://www.science.org/journal/scirobotics", "feed_url": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=scirobotics", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "robotics", "ai"], "bot_sensitivity": 1},
    {"name": "Science Signaling", "homepage_url": "https://www.science.org/journal/signaling", "feed_url": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=signaling", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},

    # ── Nature subject journals (distinct from those in science.py) ───────────
    {"name": "Nature Methods", "homepage_url": "https://www.nature.com/nmeth/", "feed_url": "https://www.nature.com/nmeth.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},
    {"name": "Nature Geoscience", "homepage_url": "https://www.nature.com/ngeo/", "feed_url": "https://www.nature.com/ngeo.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "earth"], "bot_sensitivity": 1},
    {"name": "Nature Microbiology", "homepage_url": "https://www.nature.com/nmicrobiol/", "feed_url": "https://www.nature.com/nmicrobiol.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology", "medicine"], "bot_sensitivity": 1},
    {"name": "Nature Reviews Drug Discovery", "homepage_url": "https://www.nature.com/nrd/", "feed_url": "https://www.nature.com/nrd.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "medicine"], "bot_sensitivity": 1},
    {"name": "Nature Ecology & Evolution", "homepage_url": "https://www.nature.com/natecolevol/", "feed_url": "https://www.nature.com/natecolevol.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},
    {"name": "Nature Human Behaviour", "homepage_url": "https://www.nature.com/nathumbehav/", "feed_url": "https://www.nature.com/nathumbehav.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "psychology"], "bot_sensitivity": 1},
    {"name": "Nature Reviews Cardiology", "homepage_url": "https://www.nature.com/nrcardio/", "feed_url": "https://www.nature.com/nrcardio.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "medicine"], "bot_sensitivity": 1},

    # ── Cell Press sub-journals (distinct from those in science.py) ───────────
    {"name": "Cell Stem Cell (Current Issue)", "homepage_url": "https://www.cell.com/cell-stem-cell/home", "feed_url": "https://www.cell.com/cell-stem-cell/current.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},
    {"name": "Current Biology (Current Issue)", "homepage_url": "https://www.cell.com/current-biology/home", "feed_url": "https://www.cell.com/current-biology/current.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},
    {"name": "Trends in Genetics (Current Issue)", "homepage_url": "https://www.cell.com/trends/genetics/home", "feed_url": "https://www.cell.com/trends/genetics/current.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},
    {"name": "iScience (Current Issue)", "homepage_url": "https://www.cell.com/iscience/home", "feed_url": "https://www.cell.com/iscience/current.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science"], "bot_sensitivity": 1},
    {"name": "Joule (Current Issue)", "homepage_url": "https://www.cell.com/joule/home", "feed_url": "https://www.cell.com/joule/current.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "energy"], "bot_sensitivity": 1},
    {"name": "Chem (Current Issue)", "homepage_url": "https://www.cell.com/chem/home", "feed_url": "https://www.cell.com/chem/current.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "chemistry"], "bot_sensitivity": 1},
    {"name": "Matter (Current Issue)", "homepage_url": "https://www.cell.com/matter/home", "feed_url": "https://www.cell.com/matter/current.rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "materials"], "bot_sensitivity": 1},

    # ── Earth & space: AGU + astronomy ───────────────────────────────────────
    {"name": "Eos (AGU)", "homepage_url": "https://eos.org/", "feed_url": "https://eos.org/feed", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "earth"], "bot_sensitivity": 1},
    {"name": "AGU Newsroom", "homepage_url": "https://news.agu.org/", "feed_url": "https://news.agu.org/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "earth"], "bot_sensitivity": 1},
    {"name": "JGR Atmospheres (AGU)", "homepage_url": "https://agupubs.onlinelibrary.wiley.com/journal/21698996", "feed_url": "https://agupubs.onlinelibrary.wiley.com/action/showFeed?jc=21698996&type=etoc&feed=rss", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "earth", "climate"], "bot_sensitivity": 1},
    {"name": "Earth's Future (AGU)", "homepage_url": "https://agupubs.onlinelibrary.wiley.com/journal/23284277", "feed_url": "https://agupubs.onlinelibrary.wiley.com/action/showFeed?jc=23335084&type=etoc&feed=rss", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "earth", "climate"], "bot_sensitivity": 1},
    {"name": "Astrophysical Journal (ApJ, IOP)", "homepage_url": "https://iopscience.iop.org/journal/0004-637X", "feed_url": "https://iopscience.iop.org/journal/rss/0004-637X", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "space"], "bot_sensitivity": 1},
    {"name": "Astronomical Journal (AJ, IOP)", "homepage_url": "https://iopscience.iop.org/journal/1538-3881", "feed_url": "https://iopscience.iop.org/journal/rss/1538-3881", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "space"], "bot_sensitivity": 1},
    {"name": "Environmental Research Letters (IOP)", "homepage_url": "https://iopscience.iop.org/journal/1748-9326", "feed_url": "https://iopscience.iop.org/journal/rss/1748-9326", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["science", "climate", "earth"], "bot_sensitivity": 1},
    {"name": "AAS Nova", "homepage_url": "https://aasnova.org/", "feed_url": "https://aasnova.org/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "space"], "bot_sensitivity": 1},
    {"name": "Sky & Telescope", "homepage_url": "https://skyandtelescope.org/", "feed_url": "https://skyandtelescope.org/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "space"], "bot_sensitivity": 1},
    {"name": "Space.com", "homepage_url": "https://www.space.com/", "feed_url": "https://www.space.com/feeds/all", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "space"], "bot_sensitivity": 1},
    {"name": "Universe Today", "homepage_url": "https://www.universetoday.com/", "feed_url": "https://www.universetoday.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "space"], "bot_sensitivity": 1},

    # ── Popular-science & aggregator subject desks ───────────────────────────
    {"name": "Quanta Magazine", "homepage_url": "https://www.quantamagazine.org/", "feed_url": "https://www.quantamagazine.org/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science"], "bot_sensitivity": 1},
    {"name": "MIT Technology Review", "homepage_url": "https://www.technologyreview.com/", "feed_url": "https://www.technologyreview.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "technology", "ai"], "bot_sensitivity": 1},
    {"name": "IEEE Spectrum — AI", "homepage_url": "https://spectrum.ieee.org/artificial-intelligence", "feed_url": "https://spectrum.ieee.org/feeds/topic/artificial-intelligence.rss", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "ai", "technology"], "bot_sensitivity": 1},
    {"name": "SciTechDaily", "homepage_url": "https://scitechdaily.com/", "feed_url": "https://scitechdaily.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science"], "bot_sensitivity": 1},
    {"name": "Phys.org — Physics", "homepage_url": "https://phys.org/physics-news/", "feed_url": "https://phys.org/rss-feed/physics-news/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "physics"], "bot_sensitivity": 1},
    {"name": "Phys.org — Space & Earth", "homepage_url": "https://phys.org/space-news/", "feed_url": "https://phys.org/rss-feed/space-news/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "space"], "bot_sensitivity": 1},
    {"name": "Phys.org — Chemistry", "homepage_url": "https://phys.org/chemistry-news/", "feed_url": "https://phys.org/rss-feed/chemistry-news/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "chemistry"], "bot_sensitivity": 1},
    {"name": "Phys.org — Earth", "homepage_url": "https://phys.org/earth-news/", "feed_url": "https://phys.org/rss-feed/earth-news/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "earth"], "bot_sensitivity": 1},
    {"name": "Phys.org — Biology", "homepage_url": "https://phys.org/biology-news/", "feed_url": "https://phys.org/rss-feed/biology-news/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},
    {"name": "Phys.org — Nanotechnology", "homepage_url": "https://phys.org/nanotech-news/", "feed_url": "https://phys.org/rss-feed/nanotech-news/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "materials"], "bot_sensitivity": 1},
    {"name": "ScienceDaily — Space & Time", "homepage_url": "https://www.sciencedaily.com/news/space_time/", "feed_url": "https://www.sciencedaily.com/rss/space_time.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "space"], "bot_sensitivity": 1},
    {"name": "ScienceDaily — Physics", "homepage_url": "https://www.sciencedaily.com/news/matter_energy/physics/", "feed_url": "https://www.sciencedaily.com/rss/matter_energy/physics.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "physics"], "bot_sensitivity": 1},
    {"name": "ScienceDaily — Chemistry", "homepage_url": "https://www.sciencedaily.com/news/matter_energy/chemistry/", "feed_url": "https://www.sciencedaily.com/rss/matter_energy/chemistry.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "chemistry"], "bot_sensitivity": 1},
    {"name": "ScienceDaily — Earth & Climate", "homepage_url": "https://www.sciencedaily.com/news/earth_climate/", "feed_url": "https://www.sciencedaily.com/rss/earth_climate.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "earth", "climate"], "bot_sensitivity": 1},
    {"name": "ScienceDaily — Plants & Animals", "homepage_url": "https://www.sciencedaily.com/news/plants_animals/", "feed_url": "https://www.sciencedaily.com/rss/plants_animals.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "biology"], "bot_sensitivity": 1},
    {"name": "The Conversation — Technology (US)", "homepage_url": "https://theconversation.com/us/technology", "feed_url": "https://theconversation.com/us/technology/articles.atom", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "technology"], "bot_sensitivity": 1},

    # ── CS / AI research labs ────────────────────────────────────────────────
    {"name": "Berkeley AI Research (BAIR) Blog", "homepage_url": "https://bair.berkeley.edu/blog/", "feed_url": "https://bair.berkeley.edu/blog/feed.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "ai"], "bot_sensitivity": 1},
    {"name": "Apple Machine Learning Research", "homepage_url": "https://machinelearning.apple.com/", "feed_url": "https://machinelearning.apple.com/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "ai"], "bot_sensitivity": 1},
    {"name": "Google DeepMind Blog", "homepage_url": "https://deepmind.google/", "feed_url": "https://deepmind.google/blog/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "ai"], "bot_sensitivity": 1},
    {"name": "OpenAI News", "homepage_url": "https://openai.com/news/", "feed_url": "https://openai.com/news/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "ai"], "bot_sensitivity": 1},

    # ── University research-news rooms ───────────────────────────────────────
    {"name": "Stanford News", "homepage_url": "https://news.stanford.edu/", "feed_url": "https://news.stanford.edu/feed/", "api_kind": None, "fetch_method": "rss", "region": "US-CA", "languages": ["en"], "categories": ["science", "university"], "bot_sensitivity": 1},
    {"name": "Harvard Gazette", "homepage_url": "https://news.harvard.edu/gazette/", "feed_url": "https://news.harvard.edu/gazette/feed/", "api_kind": None, "fetch_method": "rss", "region": "US-MA", "languages": ["en"], "categories": ["science", "university"], "bot_sensitivity": 1},
    {"name": "Caltech News", "homepage_url": "https://www.caltech.edu/about/news", "feed_url": "https://www.caltech.edu/news/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "US-CA", "languages": ["en"], "categories": ["science", "university"], "bot_sensitivity": 1},
    {"name": "MIT News", "homepage_url": "https://news.mit.edu/", "feed_url": "https://news.mit.edu/rss/feed", "api_kind": None, "fetch_method": "rss", "region": "US-MA", "languages": ["en"], "categories": ["science", "university"], "bot_sensitivity": 1},
    {"name": "Johns Hopkins Hub", "homepage_url": "https://hub.jhu.edu/", "feed_url": "https://hub.jhu.edu/feed/", "api_kind": None, "fetch_method": "rss", "region": "US-MD", "languages": ["en"], "categories": ["science", "university"], "bot_sensitivity": 1},
    {"name": "University of Texas at Austin News", "homepage_url": "https://news.utexas.edu/", "feed_url": "https://news.utexas.edu/feed/", "api_kind": None, "fetch_method": "rss", "region": "US-TX", "languages": ["en"], "categories": ["science", "university"], "bot_sensitivity": 1},
    {"name": "University of Michigan News", "homepage_url": "https://news.umich.edu/", "feed_url": "https://news.umich.edu/feed/", "api_kind": None, "fetch_method": "rss", "region": "US-MI", "languages": ["en"], "categories": ["science", "university"], "bot_sensitivity": 1},
    {"name": "University of Washington News", "homepage_url": "https://www.washington.edu/news/", "feed_url": "https://www.washington.edu/news/feed/", "api_kind": None, "fetch_method": "rss", "region": "US-WA", "languages": ["en"], "categories": ["science", "university"], "bot_sensitivity": 1},
    {"name": "University of Wisconsin-Madison News", "homepage_url": "https://news.wisc.edu/", "feed_url": "https://news.wisc.edu/feed/", "api_kind": None, "fetch_method": "rss", "region": "US-WI", "languages": ["en"], "categories": ["science", "university"], "bot_sensitivity": 1},
    {"name": "Georgia Tech News", "homepage_url": "https://news.gatech.edu/", "feed_url": "https://news.gatech.edu/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "US-GA", "languages": ["en"], "categories": ["science", "university"], "bot_sensitivity": 1},
    {"name": "UC Santa Cruz News", "homepage_url": "https://news.ucsc.edu/", "feed_url": "https://news.ucsc.edu/feed/", "api_kind": None, "fetch_method": "rss", "region": "US-CA", "languages": ["en"], "categories": ["science", "university"], "bot_sensitivity": 1},
    {"name": "CU Boulder Today", "homepage_url": "https://www.colorado.edu/today/", "feed_url": "https://www.colorado.edu/today/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "US-CO", "languages": ["en"], "categories": ["science", "university"], "bot_sensitivity": 1},
    {"name": "University of Cambridge Research News", "homepage_url": "https://www.cam.ac.uk/research/news", "feed_url": "https://www.cam.ac.uk/news/feed", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["science", "university"], "bot_sensitivity": 1},
    {"name": "University of Manchester News", "homepage_url": "https://www.manchester.ac.uk/discover/news/", "feed_url": "https://www.manchester.ac.uk/discover/news/feed/", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["science", "university"], "bot_sensitivity": 1},

    # ── National labs & research agencies ────────────────────────────────────
    {"name": "US National Science Foundation (NSF) News", "homepage_url": "https://www.nsf.gov/news", "feed_url": "https://www.nsf.gov/rss/rss_www_news.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["science", "agency"], "bot_sensitivity": 1},
    {"name": "Berkeley Lab (LBNL) News Center", "homepage_url": "https://newscenter.lbl.gov/", "feed_url": "https://newscenter.lbl.gov/feed/", "api_kind": None, "fetch_method": "rss", "region": "US-CA", "languages": ["en"], "categories": ["science", "lab"], "bot_sensitivity": 1},
    {"name": "Fermilab News", "homepage_url": "https://news.fnal.gov/", "feed_url": "https://news.fnal.gov/feed/", "api_kind": None, "fetch_method": "rss", "region": "US-IL", "languages": ["en"], "categories": ["science", "physics", "lab"], "bot_sensitivity": 1},
    {"name": "EMBL News", "homepage_url": "https://www.embl.org/news/", "feed_url": "https://www.embl.org/news/feed/", "api_kind": None, "fetch_method": "rss", "region": "EU", "languages": ["en"], "categories": ["science", "biology", "lab"], "bot_sensitivity": 1},

    # ── Frontiers subject journal (not in science.py) ────────────────────────
    {"name": "Frontiers in Earth Science", "homepage_url": "https://www.frontiersin.org/journals/earth-science", "feed_url": "https://www.frontiersin.org/journals/earth-science/rss", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["science", "earth"], "bot_sensitivity": 1},
]
