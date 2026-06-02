"""Extra seed sources — FINANCE + TECH + NICHE/TRADE depth.

Hand-curated, *live-verified* feeds extending the main catalog with long-tail
specialist coverage that the core ``SEED_SOURCES`` list does not yet carry:

  * central banks & financial regulators (BoE, BoJ, BoC, Fed Board/SF/StL,
    ECB research, ESMA, EBA, FCA, CFTC, BOK, Riksbank)
  * markets / economics trade press and macro blogs
  * specialist trade beats: semiconductors, AI/ML, cloud & devops,
    cybersecurity, crypto/blockchain, energy / oil & gas / renewables,
    shipping & logistics, mining & commodities, agriculture, biotech/pharma,
    automotive/EV, aerospace/defense, space, climate/ESG, telecoms
  * a slice of non-English trade press (DE/FR/ES/JA)

Every ``rss`` entry below was fetched with a desktop-browser User-Agent and
confirmed to return a parseable feed with >= 1 real <item>/<entry> at curation
time (2026-06). Outlets with no working public feed are omitted rather than
listed as ``html`` here, since this bucket targets verified feeds.

Each entry matches the dict shape consumed by
:class:`newskoo.sources.schemas.SourceCreate`.
"""

from __future__ import annotations

SOURCES: list[dict] = [
    # ── Central banks & financial regulators ────────────────────────────────
    {"name": "Bank of England — News", "homepage_url": "https://www.bankofengland.co.uk/", "feed_url": "https://www.bankofengland.co.uk/rss/news", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["central-bank", "economy", "markets"], "bot_sensitivity": 1},
    {"name": "Bank of Japan — What's New", "homepage_url": "https://www.boj.or.jp/en/", "feed_url": "https://www.boj.or.jp/en/rss/whatsnew.xml", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["en"], "categories": ["central-bank", "economy", "markets"], "bot_sensitivity": 0},
    {"name": "Bank of Canada — Press Releases", "homepage_url": "https://www.bankofcanada.ca/", "feed_url": "https://www.bankofcanada.ca/content_type/press-releases/feed/", "api_kind": None, "fetch_method": "rss", "region": "CA", "languages": ["en"], "categories": ["central-bank", "economy"], "bot_sensitivity": 0},
    {"name": "US Federal Reserve Board — All Press Releases", "homepage_url": "https://www.federalreserve.gov/", "feed_url": "https://www.federalreserve.gov/feeds/press_all.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["central-bank", "economy", "markets"], "bot_sensitivity": 0},
    {"name": "Federal Reserve Bank of San Francisco", "homepage_url": "https://www.frbsf.org/", "feed_url": "https://www.frbsf.org/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["central-bank", "economy"], "bot_sensitivity": 0},
    {"name": "St. Louis Fed — FRED Blog", "homepage_url": "https://fredblog.stlouisfed.org/", "feed_url": "https://fredblog.stlouisfed.org/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["central-bank", "economy", "markets"], "bot_sensitivity": 0},
    {"name": "ECB — Working Papers & Research", "homepage_url": "https://www.ecb.europa.eu/", "feed_url": "https://www.ecb.europa.eu/rss/wppub.html", "api_kind": None, "fetch_method": "rss", "region": "EU", "languages": ["en"], "categories": ["central-bank", "economy", "research"], "bot_sensitivity": 0},
    {"name": "ESMA — Securities Markets Regulator", "homepage_url": "https://www.esma.europa.eu/", "feed_url": "https://www.esma.europa.eu/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "EU", "languages": ["en"], "categories": ["regulator", "markets", "finance"], "bot_sensitivity": 0},
    {"name": "European Banking Authority (EBA)", "homepage_url": "https://www.eba.europa.eu/", "feed_url": "https://www.eba.europa.eu/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "EU", "languages": ["en"], "categories": ["regulator", "banking", "finance"], "bot_sensitivity": 0},
    {"name": "UK Financial Conduct Authority (FCA)", "homepage_url": "https://www.fca.org.uk/", "feed_url": "https://www.fca.org.uk/news/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["regulator", "finance", "markets"], "bot_sensitivity": 0},
    {"name": "US CFTC — Press", "homepage_url": "https://www.cftc.gov/", "feed_url": "https://www.cftc.gov/RSS/RSSGP/rssgp.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["regulator", "commodities", "markets"], "bot_sensitivity": 0},
    {"name": "Bank of Korea — News", "homepage_url": "https://www.bok.or.kr/", "feed_url": "https://www.bok.or.kr/portal/bbs/B0000338/news.rss?menuNo=200761", "api_kind": None, "fetch_method": "rss", "region": "KR", "languages": ["ko"], "categories": ["central-bank", "economy"], "bot_sensitivity": 0},
    {"name": "Sveriges Riksbank — Press Releases", "homepage_url": "https://www.riksbank.se/", "feed_url": "https://www.riksbank.se/en-gb/rss/press-releases/", "api_kind": None, "fetch_method": "rss", "region": "SE", "languages": ["en"], "categories": ["central-bank", "economy"], "bot_sensitivity": 0},

    # ── Markets / economics trade press & macro ─────────────────────────────
    {"name": "ZeroHedge", "homepage_url": "https://www.zerohedge.com/", "feed_url": "https://feeds.feedburner.com/zerohedge/feed", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["markets", "economy", "finance"], "bot_sensitivity": 1},
    {"name": "Calculated Risk", "homepage_url": "https://www.calculatedriskblog.com/", "feed_url": "https://www.calculatedriskblog.com/feeds/posts/default", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["economy", "markets", "housing"], "bot_sensitivity": 0},
    {"name": "Wolf Street", "homepage_url": "https://wolfstreet.com/", "feed_url": "https://wolfstreet.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["economy", "markets", "finance"], "bot_sensitivity": 0},
    {"name": "Naked Capitalism", "homepage_url": "https://www.nakedcapitalism.com/", "feed_url": "https://www.nakedcapitalism.com/feed", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["economy", "finance", "markets"], "bot_sensitivity": 0},
    {"name": "Risk.net", "homepage_url": "https://www.risk.net/", "feed_url": "https://www.risk.net/feeds/rss", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["finance", "markets", "risk"], "bot_sensitivity": 1},
    {"name": "Finextra (fintech)", "homepage_url": "https://www.finextra.com/", "feed_url": "https://www.finextra.com/rss/headlines.aspx", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["fintech", "banking", "finance"], "bot_sensitivity": 0},
    {"name": "Peterson Institute (PIIE)", "homepage_url": "https://www.piie.com/", "feed_url": "https://www.piie.com/rss/update.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["economy", "trade", "research"], "bot_sensitivity": 0},
    {"name": "Tax Foundation", "homepage_url": "https://taxfoundation.org/", "feed_url": "https://taxfoundation.org/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["economy", "tax", "policy"], "bot_sensitivity": 0},
    {"name": "Moneycontrol (India markets)", "homepage_url": "https://www.moneycontrol.com/", "feed_url": "https://www.moneycontrol.com/rss/latestnews.xml", "api_kind": None, "fetch_method": "rss", "region": "IN", "languages": ["en"], "categories": ["markets", "finance", "economy"], "bot_sensitivity": 0},

    # ── Semiconductors ──────────────────────────────────────────────────────
    {"name": "EE Times", "homepage_url": "https://www.eetimes.com/", "feed_url": "https://www.eetimes.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["semiconductors", "electronics", "technology"], "bot_sensitivity": 1},
    {"name": "SemiWiki", "homepage_url": "https://semiwiki.com/", "feed_url": "https://semiwiki.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["semiconductors", "eda", "technology"], "bot_sensitivity": 0},
    {"name": "Semiconductor Digest", "homepage_url": "https://www.semiconductor-digest.com/", "feed_url": "https://www.semiconductor-digest.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["semiconductors", "manufacturing", "technology"], "bot_sensitivity": 0},
    {"name": "DIGITIMES Asia", "homepage_url": "https://www.digitimes.com/", "feed_url": "https://www.digitimes.com/rss/daily.xml", "api_kind": None, "fetch_method": "rss", "region": "TW", "languages": ["en"], "categories": ["semiconductors", "supply-chain", "technology"], "bot_sensitivity": 1},

    # ── AI / ML ─────────────────────────────────────────────────────────────
    {"name": "Berkeley AI Research (BAIR) Blog", "homepage_url": "https://bair.berkeley.edu/blog/", "feed_url": "https://bair.berkeley.edu/blog/feed.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["ai", "machine-learning", "research"], "bot_sensitivity": 0},
    {"name": "Google AI Blog", "homepage_url": "https://blog.google/technology/ai/", "feed_url": "https://blog.google/technology/ai/rss/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["ai", "machine-learning", "technology"], "bot_sensitivity": 0},
    {"name": "Google DeepMind — Blog", "homepage_url": "https://deepmind.google/", "feed_url": "https://deepmind.google/blog/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["ai", "machine-learning", "research"], "bot_sensitivity": 0},
    {"name": "MarkTechPost", "homepage_url": "https://www.marktechpost.com/", "feed_url": "https://www.marktechpost.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["ai", "machine-learning", "technology"], "bot_sensitivity": 0},
    {"name": "The Gradient", "homepage_url": "https://thegradient.pub/", "feed_url": "https://thegradient.pub/rss/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["ai", "machine-learning", "research"], "bot_sensitivity": 0},
    {"name": "Hugging Face — Blog", "homepage_url": "https://huggingface.co/blog", "feed_url": "https://huggingface.co/blog/feed.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["ai", "machine-learning", "open-source"], "bot_sensitivity": 0},
    {"name": "Import AI (Jack Clark)", "homepage_url": "https://importai.substack.com/", "feed_url": "https://importai.substack.com/feed", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["ai", "machine-learning", "policy"], "bot_sensitivity": 0},

    # ── Cloud / DevOps / enterprise IT ──────────────────────────────────────
    {"name": "AWS — What's New", "homepage_url": "https://aws.amazon.com/new/", "feed_url": "https://aws.amazon.com/about-aws/whats-new/recent/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["cloud", "devops", "technology"], "bot_sensitivity": 0},
    {"name": "Cloudflare Blog", "homepage_url": "https://blog.cloudflare.com/", "feed_url": "https://blog.cloudflare.com/rss/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["cloud", "networking", "security"], "bot_sensitivity": 0},
    {"name": "The New Stack", "homepage_url": "https://thenewstack.io/", "feed_url": "https://thenewstack.io/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["cloud", "devops", "technology"], "bot_sensitivity": 0},
    {"name": "InfoQ", "homepage_url": "https://www.infoq.com/", "feed_url": "https://feed.infoq.com/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["software", "devops", "technology"], "bot_sensitivity": 0},
    {"name": "Kubernetes Blog", "homepage_url": "https://kubernetes.io/blog/", "feed_url": "https://kubernetes.io/feed.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["cloud", "devops", "open-source"], "bot_sensitivity": 0},
    {"name": "DevOps.com", "homepage_url": "https://devops.com/", "feed_url": "https://devops.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["devops", "software", "technology"], "bot_sensitivity": 0},
    {"name": "HashiCorp Blog", "homepage_url": "https://www.hashicorp.com/blog", "feed_url": "https://www.hashicorp.com/blog/feed.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["devops", "cloud", "infrastructure"], "bot_sensitivity": 0},
    {"name": "Data Center Dynamics", "homepage_url": "https://www.datacenterdynamics.com/", "feed_url": "https://www.datacenterdynamics.com/en/rss/", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["datacenter", "cloud", "infrastructure"], "bot_sensitivity": 0},

    # ── Cybersecurity ───────────────────────────────────────────────────────
    {"name": "Dark Reading", "homepage_url": "https://www.darkreading.com/", "feed_url": "https://www.darkreading.com/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["cybersecurity", "infosec", "technology"], "bot_sensitivity": 0},
    {"name": "SecurityWeek", "homepage_url": "https://www.securityweek.com/", "feed_url": "https://www.securityweek.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["cybersecurity", "infosec"], "bot_sensitivity": 0},
    {"name": "CISA — Cybersecurity Advisories", "homepage_url": "https://www.cisa.gov/", "feed_url": "https://www.cisa.gov/cybersecurity-advisories/all.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["cybersecurity", "government", "advisories"], "bot_sensitivity": 0},
    {"name": "Schneier on Security", "homepage_url": "https://www.schneier.com/", "feed_url": "https://www.schneier.com/feed/atom/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["cybersecurity", "infosec", "policy"], "bot_sensitivity": 0},

    # ── Crypto / blockchain ─────────────────────────────────────────────────
    {"name": "Decrypt", "homepage_url": "https://decrypt.co/", "feed_url": "https://decrypt.co/feed", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["crypto", "blockchain", "finance"], "bot_sensitivity": 0},
    {"name": "Bitcoin Magazine", "homepage_url": "https://bitcoinmagazine.com/", "feed_url": "https://bitcoinmagazine.com/feed", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["crypto", "blockchain", "bitcoin"], "bot_sensitivity": 0},
    {"name": "CryptoSlate", "homepage_url": "https://cryptoslate.com/", "feed_url": "https://cryptoslate.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["crypto", "blockchain", "markets"], "bot_sensitivity": 0},
    {"name": "DL News", "homepage_url": "https://www.dlnews.com/", "feed_url": "https://www.dlnews.com/arc/outboundfeeds/rss/", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["crypto", "blockchain", "finance"], "bot_sensitivity": 0},
    {"name": "Protos", "homepage_url": "https://protos.com/", "feed_url": "https://protos.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["crypto", "blockchain"], "bot_sensitivity": 0},
    {"name": "Blockworks", "homepage_url": "https://blockworks.co/", "feed_url": "https://blockworks.co/feed", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["crypto", "blockchain", "markets"], "bot_sensitivity": 0},

    # ── Energy / oil & gas / renewables ─────────────────────────────────────
    {"name": "Rigzone (oil & gas)", "homepage_url": "https://www.rigzone.com/", "feed_url": "https://www.rigzone.com/news/rss/rigzone_latest.aspx", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["energy", "oil-gas"], "bot_sensitivity": 0},
    {"name": "Utility Dive", "homepage_url": "https://www.utilitydive.com/", "feed_url": "https://www.utilitydive.com/feeds/news/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["energy", "utilities", "power"], "bot_sensitivity": 0},
    {"name": "pv magazine (solar)", "homepage_url": "https://www.pv-magazine.com/", "feed_url": "https://www.pv-magazine.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["en"], "categories": ["energy", "renewables", "solar"], "bot_sensitivity": 0},
    {"name": "World Oil", "homepage_url": "https://worldoil.com/", "feed_url": "https://worldoil.com/rss?feed=news", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["energy", "oil-gas"], "bot_sensitivity": 0},
    {"name": "US EIA — Today in Energy", "homepage_url": "https://www.eia.gov/", "feed_url": "https://www.eia.gov/rss/todayinenergy.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["energy", "government", "data"], "bot_sensitivity": 0},
    {"name": "POWER Magazine", "homepage_url": "https://www.powermag.com/", "feed_url": "https://www.powermag.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["energy", "power", "utilities"], "bot_sensitivity": 0},
    {"name": "CleanTechnica", "homepage_url": "https://cleantechnica.com/", "feed_url": "https://cleantechnica.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["energy", "renewables", "cleantech"], "bot_sensitivity": 0},

    # ── Shipping / maritime / logistics ─────────────────────────────────────
    {"name": "Splash247 (maritime)", "homepage_url": "https://splash247.com/", "feed_url": "https://splash247.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "SG", "languages": ["en"], "categories": ["shipping", "maritime", "logistics"], "bot_sensitivity": 0},
    {"name": "gCaptain (maritime)", "homepage_url": "https://gcaptain.com/", "feed_url": "https://gcaptain.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["shipping", "maritime", "logistics"], "bot_sensitivity": 0},
    {"name": "Hellenic Shipping News", "homepage_url": "https://www.hellenicshippingnews.com/", "feed_url": "https://www.hellenicshippingnews.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GR", "languages": ["en"], "categories": ["shipping", "maritime", "commodities"], "bot_sensitivity": 0},
    {"name": "The Loadstar (logistics)", "homepage_url": "https://theloadstar.com/", "feed_url": "https://theloadstar.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["logistics", "shipping", "supply-chain"], "bot_sensitivity": 0},
    {"name": "Container News", "homepage_url": "https://container-news.com/", "feed_url": "https://container-news.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["shipping", "logistics", "containers"], "bot_sensitivity": 0},
    {"name": "Supply Chain Dive", "homepage_url": "https://www.supplychaindive.com/", "feed_url": "https://www.supplychaindive.com/feeds/news/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["supply-chain", "logistics"], "bot_sensitivity": 0},
    {"name": "Marine Insight", "homepage_url": "https://www.marineinsight.com/", "feed_url": "https://www.marineinsight.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "IN", "languages": ["en"], "categories": ["shipping", "maritime"], "bot_sensitivity": 0},

    # ── Mining / commodities ────────────────────────────────────────────────
    {"name": "The Northern Miner", "homepage_url": "https://www.northernminer.com/", "feed_url": "https://www.northernminer.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "CA", "languages": ["en"], "categories": ["mining", "commodities", "metals"], "bot_sensitivity": 0},

    # ── Agriculture ─────────────────────────────────────────────────────────
    {"name": "Feedstuffs", "homepage_url": "https://www.feedstuffs.com/", "feed_url": "https://www.feedstuffs.com/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["agriculture", "livestock", "commodities"], "bot_sensitivity": 0},
    {"name": "Farm Progress", "homepage_url": "https://www.farmprogress.com/", "feed_url": "https://www.farmprogress.com/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["agriculture", "farming", "commodities"], "bot_sensitivity": 0},
    {"name": "AgFunderNews (agtech)", "homepage_url": "https://agfundernews.com/", "feed_url": "https://agfundernews.com/feed", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["agriculture", "agtech", "venture"], "bot_sensitivity": 0},
    {"name": "Brownfield Ag News", "homepage_url": "https://brownfieldagnews.com/", "feed_url": "https://brownfieldagnews.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["agriculture", "farming", "commodities"], "bot_sensitivity": 0},

    # ── Biotech / pharma ────────────────────────────────────────────────────
    {"name": "FiercePharma", "homepage_url": "https://www.fiercepharma.com/", "feed_url": "https://www.fiercepharma.com/rss/xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["pharma", "biotech", "healthcare"], "bot_sensitivity": 0},
    {"name": "BioPharma Dive", "homepage_url": "https://www.biopharmadive.com/", "feed_url": "https://www.biopharmadive.com/feeds/news/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["biotech", "pharma", "healthcare"], "bot_sensitivity": 0},
    {"name": "Pharmaceutical Technology", "homepage_url": "https://www.pharmaceutical-technology.com/", "feed_url": "https://www.pharmaceutical-technology.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["pharma", "biotech", "manufacturing"], "bot_sensitivity": 0},
    {"name": "Genetic Engineering & Biotechnology News (GEN)", "homepage_url": "https://www.genengnews.com/", "feed_url": "https://www.genengnews.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["biotech", "genomics", "research"], "bot_sensitivity": 0},

    # ── Automotive / EV ─────────────────────────────────────────────────────
    {"name": "InsideEVs", "homepage_url": "https://insideevs.com/", "feed_url": "https://insideevs.com/rss/articles/all/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["automotive", "ev", "technology"], "bot_sensitivity": 0},
    {"name": "just-auto", "homepage_url": "https://www.just-auto.com/", "feed_url": "https://www.just-auto.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["automotive", "manufacturing", "supply-chain"], "bot_sensitivity": 0},
    {"name": "Charged EVs", "homepage_url": "https://chargedevs.com/", "feed_url": "https://chargedevs.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["automotive", "ev", "energy"], "bot_sensitivity": 0},

    # ── Aerospace / defense ─────────────────────────────────────────────────
    {"name": "Defense One", "homepage_url": "https://www.defenseone.com/", "feed_url": "https://www.defenseone.com/rss/all/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["defense", "military", "policy"], "bot_sensitivity": 0},
    {"name": "FlightGlobal", "homepage_url": "https://www.flightglobal.com/", "feed_url": "https://www.flightglobal.com/rss/feed", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["aerospace", "aviation", "defense"], "bot_sensitivity": 0},
    {"name": "The War Zone (TWZ)", "homepage_url": "https://www.twz.com/", "feed_url": "https://www.twz.com/feed", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["defense", "military", "aerospace"], "bot_sensitivity": 0},
    {"name": "Naval News", "homepage_url": "https://www.navalnews.com/", "feed_url": "https://www.navalnews.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["en"], "categories": ["defense", "naval", "military"], "bot_sensitivity": 0},
    {"name": "Defense Daily", "homepage_url": "https://www.defensedaily.com/", "feed_url": "https://www.defensedaily.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["defense", "military", "procurement"], "bot_sensitivity": 0},

    # ── Space ───────────────────────────────────────────────────────────────
    {"name": "SpaceNews", "homepage_url": "https://spacenews.com/", "feed_url": "https://spacenews.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["space", "aerospace", "satellite"], "bot_sensitivity": 0},
    {"name": "NASASpaceflight", "homepage_url": "https://www.nasaspaceflight.com/", "feed_url": "https://www.nasaspaceflight.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["space", "launch", "aerospace"], "bot_sensitivity": 0},
    {"name": "Spaceflight Now", "homepage_url": "https://spaceflightnow.com/", "feed_url": "https://spaceflightnow.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["space", "launch", "aerospace"], "bot_sensitivity": 0},
    {"name": "Payload", "homepage_url": "https://payloadspace.com/", "feed_url": "https://payloadspace.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["space", "satellite", "business"], "bot_sensitivity": 0},

    # ── Climate / ESG ───────────────────────────────────────────────────────
    {"name": "Grist", "homepage_url": "https://grist.org/", "feed_url": "https://grist.org/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["climate", "environment", "energy"], "bot_sensitivity": 0},
    {"name": "ESG Today", "homepage_url": "https://www.esgtoday.com/", "feed_url": "https://www.esgtoday.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["esg", "climate", "finance"], "bot_sensitivity": 0},
    {"name": "Climate Home News", "homepage_url": "https://www.climatechangenews.com/", "feed_url": "https://www.climatechangenews.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["climate", "policy", "environment"], "bot_sensitivity": 0},
    {"name": "Carbon Pulse", "homepage_url": "https://carbon-pulse.com/", "feed_url": "https://carbon-pulse.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["climate", "carbon-markets", "esg"], "bot_sensitivity": 0},

    # ── Telecoms ────────────────────────────────────────────────────────────
    {"name": "Light Reading", "homepage_url": "https://www.lightreading.com/", "feed_url": "https://www.lightreading.com/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["telecoms", "networking", "5g"], "bot_sensitivity": 0},
    {"name": "Fierce Network (telecom)", "homepage_url": "https://www.fierce-network.com/", "feed_url": "https://www.fierce-network.com/rss/xml", "api_kind": None, "fetch_method": "rss", "region": "US", "languages": ["en"], "categories": ["telecoms", "networking", "5g"], "bot_sensitivity": 0},
    {"name": "Total Telecom", "homepage_url": "https://totaltele.com/", "feed_url": "https://totaltele.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GB", "languages": ["en"], "categories": ["telecoms", "networking"], "bot_sensitivity": 0},

    # ── Non-English trade / finance / tech press ────────────────────────────
    {"name": "Capital (France, finance)", "homepage_url": "https://www.capital.fr/", "feed_url": "https://www.capital.fr/rss", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["finance", "economy", "markets"], "bot_sensitivity": 0},
    {"name": "Investing.com Deutschland", "homepage_url": "https://de.investing.com/", "feed_url": "https://de.investing.com/rss/news.rss", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["finance", "markets", "economy"], "bot_sensitivity": 0},
    {"name": "ITmedia (Japan, tech)", "homepage_url": "https://www.itmedia.co.jp/", "feed_url": "https://rss.itmedia.co.jp/rss/2.0/itmedia_all.xml", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["ja"], "categories": ["technology", "it", "business"], "bot_sensitivity": 0},
    {"name": "Golem.de (Germany, tech)", "homepage_url": "https://www.golem.de/", "feed_url": "https://rss.golem.de/rss.php?feed=RSS2.0", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["technology", "it"], "bot_sensitivity": 0},
    {"name": "Clubic (France, tech)", "homepage_url": "https://www.clubic.com/", "feed_url": "https://www.clubic.com/feed/news.rss", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["technology", "it", "consumer-tech"], "bot_sensitivity": 0},
    {"name": "Xataka (Spain, tech)", "homepage_url": "https://www.xataka.com/", "feed_url": "https://www.xataka.com/feedburner.xml", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["es"], "categories": ["technology", "it", "consumer-tech"], "bot_sensitivity": 0},
]
