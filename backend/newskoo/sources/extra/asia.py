"""Asia-Pacific depth bucket — verified live RSS/Atom feeds.

Coverage: South Asia (IN/PK/BD/LK/NP), Southeast Asia (SG/MY/TH/VN/PH/ID/MM/KH),
East Asia (JP/KR/CN/HK/TW), Central Asia / Caspian (KZ/KG/AZ), and Oceania
(AU/NZ + Pacific Islands: FJ/PG). A mix of general, business/markets, and
technology/startup outlets, with many language-native feeds (hi, ur, bn, th, vi,
id, ms, ja, ko, zh) alongside regional English editions.

Every ``feed_url`` below was fetched with a desktop-browser User-Agent and
confirmed to return a parseable RSS/Atom/RDF document with >= 1 real article
item on 2026-06-02. Big internationals already in the core catalog (NHK, Yonhap,
BBC, Guardian, etc.) are deliberately excluded.
"""

from __future__ import annotations

SOURCES: list[dict] = [
    # ── South Asia: India — general / regional ───────────────────────────────
    {"name": "The Hindu", "homepage_url": "https://www.thehindu.com/", "feed_url": "https://www.thehindu.com/feeder/default.rss", "api_kind": None, "fetch_method": "rss", "region": "IN", "languages": ["en"], "categories": ["general", "world", "politics"], "bot_sensitivity": 1},
    {"name": "NDTV Top Stories", "homepage_url": "https://www.ndtv.com/", "feed_url": "https://feeds.feedburner.com/ndtvnews-top-stories", "api_kind": None, "fetch_method": "rss", "region": "IN", "languages": ["en"], "categories": ["general", "world", "politics"], "bot_sensitivity": 1},
    {"name": "Deccan Chronicle", "homepage_url": "https://www.deccanchronicle.com/", "feed_url": "https://www.deccanchronicle.com/google_feeds.xml", "api_kind": None, "fetch_method": "rss", "region": "IN", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Oneindia News", "homepage_url": "https://www.oneindia.com/", "feed_url": "https://www.oneindia.com/rss/news-fb.xml", "api_kind": None, "fetch_method": "rss", "region": "IN", "languages": ["en"], "categories": ["general"], "bot_sensitivity": 1},
    # India — Hindi language-native
    {"name": "Amar Ujala (Hindi)", "homepage_url": "https://www.amarujala.com/", "feed_url": "https://www.amarujala.com/rss/breaking-news.xml", "api_kind": None, "fetch_method": "rss", "region": "IN", "languages": ["hi"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Dainik Bhaskar (Hindi)", "homepage_url": "https://www.bhaskar.com/", "feed_url": "https://www.bhaskar.com/rss-v1--category-12238.xml", "api_kind": None, "fetch_method": "rss", "region": "IN", "languages": ["hi"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    # India — business / markets
    {"name": "Mint", "homepage_url": "https://www.livemint.com/", "feed_url": "https://www.livemint.com/rss/news", "api_kind": None, "fetch_method": "rss", "region": "IN", "languages": ["en"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 1},
    {"name": "The Hindu BusinessLine", "homepage_url": "https://www.thehindubusinessline.com/", "feed_url": "https://www.thehindubusinessline.com/feeder/default.rss", "api_kind": None, "fetch_method": "rss", "region": "IN", "languages": ["en"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 1},
    {"name": "Moneycontrol", "homepage_url": "https://www.moneycontrol.com/", "feed_url": "https://www.moneycontrol.com/rss/latestnews.xml", "api_kind": None, "fetch_method": "rss", "region": "IN", "languages": ["en"], "categories": ["business", "markets", "finance"], "bot_sensitivity": 1},
    {"name": "The Economic Times", "homepage_url": "https://economictimes.indiatimes.com/", "feed_url": "https://economictimes.indiatimes.com/rssfeedstopstories.cms", "api_kind": None, "fetch_method": "rss", "region": "IN", "languages": ["en"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 1},
    # India — technology / startups
    {"name": "TechGig", "homepage_url": "https://www.techgig.com/", "feed_url": "https://feeds.feedburner.com/techgig", "api_kind": None, "fetch_method": "rss", "region": "IN", "languages": ["en"], "categories": ["technology"], "bot_sensitivity": 1},
    {"name": "MediaNama", "homepage_url": "https://www.medianama.com/", "feed_url": "https://www.medianama.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "IN", "languages": ["en"], "categories": ["technology", "policy", "media"], "bot_sensitivity": 1},
    {"name": "Inc42", "homepage_url": "https://inc42.com/", "feed_url": "https://inc42.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "IN", "languages": ["en"], "categories": ["technology", "startups", "business"], "bot_sensitivity": 1},
    {"name": "YourStory", "homepage_url": "https://yourstory.com/", "feed_url": "https://yourstory.com/feed", "api_kind": None, "fetch_method": "rss", "region": "IN", "languages": ["en"], "categories": ["technology", "startups", "business"], "bot_sensitivity": 1},

    # ── South Asia: Pakistan ─────────────────────────────────────────────────
    {"name": "Dawn", "homepage_url": "https://www.dawn.com/", "feed_url": "https://www.dawn.com/feeds/home", "api_kind": None, "fetch_method": "rss", "region": "PK", "languages": ["en"], "categories": ["general", "world", "politics"], "bot_sensitivity": 1},
    {"name": "The Express Tribune", "homepage_url": "https://tribune.com.pk/", "feed_url": "https://tribune.com.pk/feed/home", "api_kind": None, "fetch_method": "rss", "region": "PK", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 1},
    {"name": "The News International", "homepage_url": "https://www.thenews.com.pk/", "feed_url": "https://www.thenews.com.pk/rss/1/1", "api_kind": None, "fetch_method": "rss", "region": "PK", "languages": ["en"], "categories": ["general", "politics"], "bot_sensitivity": 1},
    {"name": "Business Recorder", "homepage_url": "https://www.brecorder.com/", "feed_url": "https://www.brecorder.com/feeds/latest-news", "api_kind": None, "fetch_method": "rss", "region": "PK", "languages": ["en"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 1},
    {"name": "ARY News", "homepage_url": "https://arynews.tv/", "feed_url": "https://arynews.tv/feed/", "api_kind": None, "fetch_method": "rss", "region": "PK", "languages": ["en"], "categories": ["general"], "bot_sensitivity": 1},
    {"name": "ProPakistani", "homepage_url": "https://propakistani.pk/", "feed_url": "https://propakistani.pk/feed/", "api_kind": None, "fetch_method": "rss", "region": "PK", "languages": ["en"], "categories": ["technology", "business"], "bot_sensitivity": 1},
    {"name": "Daily Express (Urdu)", "homepage_url": "https://www.express.pk/", "feed_url": "https://www.express.pk/feed/", "api_kind": None, "fetch_method": "rss", "region": "PK", "languages": ["ur"], "categories": ["general", "regional"], "bot_sensitivity": 1},

    # ── South Asia: Bangladesh ───────────────────────────────────────────────
    {"name": "The Daily Star (BD)", "homepage_url": "https://www.thedailystar.net/", "feed_url": "https://www.thedailystar.net/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "BD", "languages": ["en"], "categories": ["general", "world", "politics"], "bot_sensitivity": 1},
    {"name": "Prothom Alo English", "homepage_url": "https://en.prothomalo.com/", "feed_url": "https://en.prothomalo.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "BD", "languages": ["en"], "categories": ["general"], "bot_sensitivity": 1},
    {"name": "The Business Standard (BD)", "homepage_url": "https://www.tbsnews.net/", "feed_url": "https://www.tbsnews.net/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "BD", "languages": ["en"], "categories": ["business", "economy"], "bot_sensitivity": 1},

    # ── South Asia: Sri Lanka ────────────────────────────────────────────────
    {"name": "The Island (LK)", "homepage_url": "https://island.lk/", "feed_url": "https://island.lk/feed/", "api_kind": None, "fetch_method": "rss", "region": "LK", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "EconomyNext", "homepage_url": "https://economynext.com/", "feed_url": "https://economynext.com/feed", "api_kind": None, "fetch_method": "rss", "region": "LK", "languages": ["en"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 1},

    # ── South Asia: Nepal ────────────────────────────────────────────────────
    {"name": "The Kathmandu Post", "homepage_url": "https://kathmandupost.com/", "feed_url": "https://kathmandupost.com/rss", "api_kind": None, "fetch_method": "rss", "region": "NP", "languages": ["en"], "categories": ["general", "politics"], "bot_sensitivity": 1},
    {"name": "Online Khabar English", "homepage_url": "https://english.onlinekhabar.com/", "feed_url": "https://english.onlinekhabar.com/feed", "api_kind": None, "fetch_method": "rss", "region": "NP", "languages": ["en"], "categories": ["general"], "bot_sensitivity": 1},

    # ── Southeast Asia: Singapore ────────────────────────────────────────────
    {"name": "The Straits Times — Singapore", "homepage_url": "https://www.straitstimes.com/", "feed_url": "https://www.straitstimes.com/news/singapore/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "SG", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Channel NewsAsia", "homepage_url": "https://www.channelnewsasia.com/", "feed_url": "https://www.channelnewsasia.com/rssfeeds/8395986", "api_kind": None, "fetch_method": "rss", "region": "SG", "languages": ["en"], "categories": ["general", "world", "business"], "bot_sensitivity": 1},
    {"name": "The Business Times (SG)", "homepage_url": "https://www.businesstimes.com.sg/", "feed_url": "https://www.businesstimes.com.sg/rss/top-stories", "api_kind": None, "fetch_method": "rss", "region": "SG", "languages": ["en"], "categories": ["business", "markets", "finance"], "bot_sensitivity": 1},
    {"name": "Vulcan Post", "homepage_url": "https://vulcanpost.com/", "feed_url": "https://vulcanpost.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "SG", "languages": ["en"], "categories": ["technology", "startups", "business"], "bot_sensitivity": 1},
    {"name": "Mothership", "homepage_url": "https://mothership.sg/", "feed_url": "https://mothership.sg/feed/", "api_kind": None, "fetch_method": "rss", "region": "SG", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},

    # ── Southeast Asia: Malaysia ─────────────────────────────────────────────
    {"name": "New Straits Times", "homepage_url": "https://www.nst.com.my/", "feed_url": "https://www.nst.com.my/feed", "api_kind": None, "fetch_method": "rss", "region": "MY", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Malay Mail — Malaysia", "homepage_url": "https://www.malaymail.com/", "feed_url": "https://www.malaymail.com/feed/rss/malaysia", "api_kind": None, "fetch_method": "rss", "region": "MY", "languages": ["en"], "categories": ["general"], "bot_sensitivity": 1},
    {"name": "Free Malaysia Today", "homepage_url": "https://www.freemalaysiatoday.com/", "feed_url": "https://www.freemalaysiatoday.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "MY", "languages": ["en"], "categories": ["general", "politics"], "bot_sensitivity": 1},
    {"name": "Malaysiakini", "homepage_url": "https://www.malaysiakini.com/", "feed_url": "https://www.malaysiakini.com/rss/en/news.rss", "api_kind": None, "fetch_method": "rss", "region": "MY", "languages": ["en"], "categories": ["general", "politics"], "bot_sensitivity": 1},
    {"name": "Berita Harian (Malay)", "homepage_url": "https://www.bharian.com.my/", "feed_url": "https://www.bharian.com.my/feed", "api_kind": None, "fetch_method": "rss", "region": "MY", "languages": ["ms"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Harian Metro (Malay)", "homepage_url": "https://www.hmetro.com.my/", "feed_url": "https://www.hmetro.com.my/feed", "api_kind": None, "fetch_method": "rss", "region": "MY", "languages": ["ms"], "categories": ["general", "regional"], "bot_sensitivity": 1},

    # ── Southeast Asia: Thailand ─────────────────────────────────────────────
    {"name": "Bangkok Post", "homepage_url": "https://www.bangkokpost.com/", "feed_url": "https://www.bangkokpost.com/rss/data/most-recent.xml", "api_kind": None, "fetch_method": "rss", "region": "TH", "languages": ["en"], "categories": ["general", "business", "world"], "bot_sensitivity": 1},
    {"name": "Khaosod English", "homepage_url": "https://www.khaosodenglish.com/", "feed_url": "https://www.khaosodenglish.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "TH", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "The Thaiger", "homepage_url": "https://thethaiger.com/", "feed_url": "https://thethaiger.com/feed", "api_kind": None, "fetch_method": "rss", "region": "TH", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Thairath (Thai)", "homepage_url": "https://www.thairath.co.th/", "feed_url": "https://www.thairath.co.th/rss/news", "api_kind": None, "fetch_method": "rss", "region": "TH", "languages": ["th"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Matichon (Thai)", "homepage_url": "https://www.matichon.co.th/", "feed_url": "https://www.matichon.co.th/feed", "api_kind": None, "fetch_method": "rss", "region": "TH", "languages": ["th"], "categories": ["general", "politics"], "bot_sensitivity": 1},
    {"name": "Prachachat Business (Thai)", "homepage_url": "https://www.prachachat.net/", "feed_url": "https://www.prachachat.net/feed", "api_kind": None, "fetch_method": "rss", "region": "TH", "languages": ["th"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 1},

    # ── Southeast Asia: Vietnam ──────────────────────────────────────────────
    {"name": "VnExpress (Vietnamese)", "homepage_url": "https://vnexpress.net/", "feed_url": "https://vnexpress.net/rss/tin-moi-nhat.rss", "api_kind": None, "fetch_method": "rss", "region": "VN", "languages": ["vi"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "VnExpress International", "homepage_url": "https://e.vnexpress.net/", "feed_url": "https://e.vnexpress.net/rss/news.rss", "api_kind": None, "fetch_method": "rss", "region": "VN", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 1},
    {"name": "VOV English", "homepage_url": "https://english.vov.vn/", "feed_url": "https://english.vov.vn/rss/home.rss", "api_kind": None, "fetch_method": "rss", "region": "VN", "languages": ["en"], "categories": ["general", "politics"], "bot_sensitivity": 1},
    {"name": "Tuoi Tre (Vietnamese)", "homepage_url": "https://tuoitre.vn/", "feed_url": "https://tuoitre.vn/rss/tin-moi-nhat.rss", "api_kind": None, "fetch_method": "rss", "region": "VN", "languages": ["vi"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Thanh Nien (Vietnamese)", "homepage_url": "https://thanhnien.vn/", "feed_url": "https://thanhnien.vn/rss/home.rss", "api_kind": None, "fetch_method": "rss", "region": "VN", "languages": ["vi"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Dan Tri (Vietnamese)", "homepage_url": "https://dantri.com.vn/", "feed_url": "https://dantri.com.vn/rss/home.rss", "api_kind": None, "fetch_method": "rss", "region": "VN", "languages": ["vi"], "categories": ["general", "regional"], "bot_sensitivity": 1},

    # ── Southeast Asia: Philippines ──────────────────────────────────────────
    {"name": "The Philippine Star", "homepage_url": "https://www.philstar.com/", "feed_url": "https://www.philstar.com/rss/headlines", "api_kind": None, "fetch_method": "rss", "region": "PH", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 1},
    {"name": "Rappler", "homepage_url": "https://www.rappler.com/", "feed_url": "https://www.rappler.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "PH", "languages": ["en"], "categories": ["general", "politics"], "bot_sensitivity": 1},
    {"name": "Philippine Daily Inquirer", "homepage_url": "https://newsinfo.inquirer.net/", "feed_url": "https://newsinfo.inquirer.net/feed", "api_kind": None, "fetch_method": "rss", "region": "PH", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "The Manila Times", "homepage_url": "https://www.manilatimes.net/", "feed_url": "https://www.manilatimes.net/news/feed/", "api_kind": None, "fetch_method": "rss", "region": "PH", "languages": ["en"], "categories": ["general"], "bot_sensitivity": 1},
    {"name": "GMA News", "homepage_url": "https://www.gmanetwork.com/news/", "feed_url": "https://data.gmanetwork.com/gno/rss/news/feed.xml", "api_kind": None, "fetch_method": "rss", "region": "PH", "languages": ["en"], "categories": ["general"], "bot_sensitivity": 1},
    {"name": "BusinessMirror", "homepage_url": "https://businessmirror.com.ph/", "feed_url": "https://businessmirror.com.ph/feed/", "api_kind": None, "fetch_method": "rss", "region": "PH", "languages": ["en"], "categories": ["business", "economy"], "bot_sensitivity": 1},
    {"name": "BusinessWorld (PH)", "homepage_url": "https://www.bworldonline.com/", "feed_url": "https://www.bworldonline.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "PH", "languages": ["en"], "categories": ["business", "markets", "economy"], "bot_sensitivity": 1},

    # ── Southeast Asia: Indonesia ────────────────────────────────────────────
    {"name": "Antara News English", "homepage_url": "https://en.antaranews.com/", "feed_url": "https://en.antaranews.com/rss/news", "api_kind": None, "fetch_method": "rss", "region": "ID", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 1},
    {"name": "Antara News (Indonesian)", "homepage_url": "https://www.antaranews.com/", "feed_url": "https://www.antaranews.com/rss/terkini", "api_kind": None, "fetch_method": "rss", "region": "ID", "languages": ["id"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Tempo (Indonesian)", "homepage_url": "https://www.tempo.co/", "feed_url": "https://rss.tempo.co/nasional", "api_kind": None, "fetch_method": "rss", "region": "ID", "languages": ["id"], "categories": ["general", "politics"], "bot_sensitivity": 1},
    {"name": "Detik (Indonesian)", "homepage_url": "https://news.detik.com/", "feed_url": "https://news.detik.com/rss", "api_kind": None, "fetch_method": "rss", "region": "ID", "languages": ["id"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "CNN Indonesia (Indonesian)", "homepage_url": "https://www.cnnindonesia.com/", "feed_url": "https://www.cnnindonesia.com/nasional/rss", "api_kind": None, "fetch_method": "rss", "region": "ID", "languages": ["id"], "categories": ["general", "politics"], "bot_sensitivity": 1},
    {"name": "CNBC Indonesia (Indonesian)", "homepage_url": "https://www.cnbcindonesia.com/", "feed_url": "https://www.cnbcindonesia.com/news/rss", "api_kind": None, "fetch_method": "rss", "region": "ID", "languages": ["id"], "categories": ["business", "markets", "economy"], "bot_sensitivity": 1},
    {"name": "Republika (Indonesian)", "homepage_url": "https://www.republika.co.id/", "feed_url": "https://www.republika.co.id/rss", "api_kind": None, "fetch_method": "rss", "region": "ID", "languages": ["id"], "categories": ["general", "regional"], "bot_sensitivity": 1},

    # ── Southeast Asia: Myanmar / Cambodia ───────────────────────────────────
    {"name": "Myanmar Now", "homepage_url": "https://myanmar-now.org/en/", "feed_url": "https://myanmar-now.org/en/feed/", "api_kind": None, "fetch_method": "rss", "region": "MM", "languages": ["en"], "categories": ["general", "politics"], "bot_sensitivity": 1},
    {"name": "Khmer Times", "homepage_url": "https://www.khmertimeskh.com/", "feed_url": "https://www.khmertimeskh.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "KH", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},

    # ── East Asia: Japan ─────────────────────────────────────────────────────
    {"name": "The Japan Times", "homepage_url": "https://www.japantimes.co.jp/", "feed_url": "https://www.japantimes.co.jp/feed/", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["en"], "categories": ["general", "world", "business"], "bot_sensitivity": 1},
    {"name": "Mainichi (Japanese)", "homepage_url": "https://mainichi.jp/", "feed_url": "https://mainichi.jp/rss/etc/mainichi-flash.rss", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["ja"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Asahi Shimbun (Japanese)", "homepage_url": "https://www.asahi.com/", "feed_url": "https://www.asahi.com/rss/asahi/newsheadlines.rdf", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["ja"], "categories": ["general", "politics"], "bot_sensitivity": 1},
    {"name": "Jiji Press (Japanese)", "homepage_url": "https://www.jiji.com/", "feed_url": "https://www.jiji.com/rss/ranking.rdf", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["ja"], "categories": ["general", "world"], "bot_sensitivity": 1},
    {"name": "Japan Today", "homepage_url": "https://japantoday.com/", "feed_url": "https://japantoday.com/feed", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["en"], "categories": ["general"], "bot_sensitivity": 1},
    {"name": "The Tokyo Reporter", "homepage_url": "https://www.tokyoreporter.com/", "feed_url": "https://www.tokyoreporter.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "SoraNews24", "homepage_url": "https://soranews24.com/", "feed_url": "https://soranews24.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["en"], "categories": ["culture", "society"], "bot_sensitivity": 1},
    {"name": "Nippon.com", "homepage_url": "https://www.nippon.com/en/", "feed_url": "https://www.nippon.com/en/feed/", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["en"], "categories": ["general", "society", "economy"], "bot_sensitivity": 1},
    {"name": "Nikkei Asia", "homepage_url": "https://asia.nikkei.com/", "feed_url": "https://asia.nikkei.com/rss/feed/nar", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["en"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 1},
    {"name": "GIGAZINE (Japanese)", "homepage_url": "https://gigazine.net/", "feed_url": "https://gigazine.net/news/rss_2.0/", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["ja"], "categories": ["technology", "science"], "bot_sensitivity": 1},
    {"name": "Impress Keitai Watch (Japanese)", "homepage_url": "https://k-tai.watch.impress.co.jp/", "feed_url": "https://k-tai.watch.impress.co.jp/data/rss/1.0/ktw/feed.rdf", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["ja"], "categories": ["technology"], "bot_sensitivity": 1},
    {"name": "Publickey (Japanese)", "homepage_url": "https://www.publickey1.jp/", "feed_url": "https://www.publickey1.jp/atom.xml", "api_kind": None, "fetch_method": "rss", "region": "JP", "languages": ["ja"], "categories": ["technology"], "bot_sensitivity": 1},

    # ── East Asia: South Korea ───────────────────────────────────────────────
    {"name": "The Korea Times", "homepage_url": "https://www.koreatimes.co.kr/", "feed_url": "https://www.koreatimes.co.kr/www/rss/nation.xml", "api_kind": None, "fetch_method": "rss", "region": "KR", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Hankyoreh English", "homepage_url": "https://english.hani.co.kr/", "feed_url": "https://english.hani.co.kr/rss/", "api_kind": None, "fetch_method": "rss", "region": "KR", "languages": ["en"], "categories": ["general", "politics"], "bot_sensitivity": 1},
    {"name": "Dong-A Ilbo (Korean)", "homepage_url": "https://www.donga.com/", "feed_url": "https://rss.donga.com/total.xml", "api_kind": None, "fetch_method": "rss", "region": "KR", "languages": ["ko"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Hankyung (Korean)", "homepage_url": "https://www.hankyung.com/", "feed_url": "https://www.hankyung.com/feed/all-news", "api_kind": None, "fetch_method": "rss", "region": "KR", "languages": ["ko"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 1},
    {"name": "Chosun Ilbo (Korean)", "homepage_url": "https://www.chosun.com/", "feed_url": "https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml", "api_kind": None, "fetch_method": "rss", "region": "KR", "languages": ["ko"], "categories": ["general", "politics"], "bot_sensitivity": 1},
    {"name": "Maeil Business (Korean)", "homepage_url": "https://www.mk.co.kr/", "feed_url": "https://www.mk.co.kr/rss/30000001/", "api_kind": None, "fetch_method": "rss", "region": "KR", "languages": ["ko"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 1},

    # ── East Asia: China / Hong Kong / Taiwan ────────────────────────────────
    {"name": "South China Morning Post — China", "homepage_url": "https://www.scmp.com/", "feed_url": "https://www.scmp.com/rss/91/feed", "api_kind": None, "fetch_method": "rss", "region": "HK", "languages": ["en"], "categories": ["general", "world", "politics"], "bot_sensitivity": 1},
    {"name": "Global Times", "homepage_url": "https://www.globaltimes.cn/", "feed_url": "https://www.globaltimes.cn/rss/outbrain.xml", "api_kind": None, "fetch_method": "rss", "region": "CN", "languages": ["en"], "categories": ["general", "world", "politics"], "bot_sensitivity": 1},
    {"name": "Sixth Tone", "homepage_url": "https://www.sixthtone.com/", "feed_url": "https://www.sixthtone.com/rss", "api_kind": None, "fetch_method": "rss", "region": "CN", "languages": ["en"], "categories": ["society", "culture", "general"], "bot_sensitivity": 1},
    {"name": "TechNode", "homepage_url": "https://technode.com/", "feed_url": "https://technode.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "CN", "languages": ["en"], "categories": ["technology", "startups", "business"], "bot_sensitivity": 1},
    {"name": "Pandaily", "homepage_url": "https://pandaily.com/", "feed_url": "https://pandaily.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "CN", "languages": ["en"], "categories": ["technology", "business"], "bot_sensitivity": 1},
    {"name": "36Kr (Chinese)", "homepage_url": "https://36kr.com/", "feed_url": "https://36kr.com/feed", "api_kind": None, "fetch_method": "rss", "region": "CN", "languages": ["zh"], "categories": ["technology", "startups", "business"], "bot_sensitivity": 1},
    {"name": "Hong Kong Free Press", "homepage_url": "https://www.hongkongfp.com/", "feed_url": "https://www.hongkongfp.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "HK", "languages": ["en"], "categories": ["general", "politics"], "bot_sensitivity": 1},
    {"name": "Taipei Times", "homepage_url": "https://www.taipeitimes.com/", "feed_url": "https://www.taipeitimes.com/xml/index.rss", "api_kind": None, "fetch_method": "rss", "region": "TW", "languages": ["en"], "categories": ["general", "politics"], "bot_sensitivity": 1},
    {"name": "Liberty Times Net (Chinese)", "homepage_url": "https://news.ltn.com.tw/", "feed_url": "https://news.ltn.com.tw/rss/all.xml", "api_kind": None, "fetch_method": "rss", "region": "TW", "languages": ["zh"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "DIGITIMES", "homepage_url": "https://www.digitimes.com/", "feed_url": "https://www.digitimes.com/rss/daily.xml", "api_kind": None, "fetch_method": "rss", "region": "TW", "languages": ["en"], "categories": ["technology", "semiconductors", "business"], "bot_sensitivity": 1},

    # ── Central Asia / Caspian ───────────────────────────────────────────────
    {"name": "The Astana Times", "homepage_url": "https://astanatimes.com/", "feed_url": "https://astanatimes.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "KZ", "languages": ["en"], "categories": ["general", "politics", "economy"], "bot_sensitivity": 1},
    {"name": "24.kg News Agency", "homepage_url": "https://24.kg/", "feed_url": "https://24.kg/rss/", "api_kind": None, "fetch_method": "rss", "region": "KG", "languages": ["ru"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Trend News Agency", "homepage_url": "https://en.trend.az/", "feed_url": "https://en.trend.az/feeds/index.rss", "api_kind": None, "fetch_method": "rss", "region": "AZ", "languages": ["en"], "categories": ["general", "energy", "economy"], "bot_sensitivity": 1},
    {"name": "The Diplomat", "homepage_url": "https://thediplomat.com/", "feed_url": "https://thediplomat.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["politics", "world", "analysis"], "bot_sensitivity": 1},

    # ── Oceania: Australia ───────────────────────────────────────────────────
    {"name": "ABC News (Australia) — Top Stories", "homepage_url": "https://www.abc.net.au/news", "feed_url": "https://www.abc.net.au/news/feed/51120/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "AU", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "The Sydney Morning Herald", "homepage_url": "https://www.smh.com.au/", "feed_url": "https://www.smh.com.au/rss/feed.xml", "api_kind": None, "fetch_method": "rss", "region": "AU", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Australian Financial Review", "homepage_url": "https://www.afr.com/", "feed_url": "https://www.afr.com/rss/feed.xml", "api_kind": None, "fetch_method": "rss", "region": "AU", "languages": ["en"], "categories": ["business", "markets", "finance"], "bot_sensitivity": 1},
    {"name": "The West Australian", "homepage_url": "https://thewest.com.au/", "feed_url": "https://thewest.com.au/news/rss", "api_kind": None, "fetch_method": "rss", "region": "AU", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Crikey", "homepage_url": "https://www.crikey.com.au/", "feed_url": "https://www.crikey.com.au/feed/", "api_kind": None, "fetch_method": "rss", "region": "AU", "languages": ["en"], "categories": ["politics", "analysis", "media"], "bot_sensitivity": 1},
    {"name": "SBS News", "homepage_url": "https://www.sbs.com.au/news", "feed_url": "https://www.sbs.com.au/news/feed", "api_kind": None, "fetch_method": "rss", "region": "AU", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 1},

    # ── Oceania: New Zealand ─────────────────────────────────────────────────
    {"name": "RNZ National", "homepage_url": "https://www.rnz.co.nz/", "feed_url": "https://www.rnz.co.nz/rss/national.xml", "api_kind": None, "fetch_method": "rss", "region": "NZ", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Stuff (NZ)", "homepage_url": "https://www.stuff.co.nz/", "feed_url": "https://www.stuff.co.nz/rss", "api_kind": None, "fetch_method": "rss", "region": "NZ", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "The Spinoff", "homepage_url": "https://thespinoff.co.nz/", "feed_url": "https://thespinoff.co.nz/feed", "api_kind": None, "fetch_method": "rss", "region": "NZ", "languages": ["en"], "categories": ["culture", "politics", "society"], "bot_sensitivity": 1},

    # ── Oceania: Pacific Islands ─────────────────────────────────────────────
    {"name": "RNZ Pacific", "homepage_url": "https://www.rnz.co.nz/international/pacific-news", "feed_url": "https://www.rnz.co.nz/rss/pacific.xml", "api_kind": None, "fetch_method": "rss", "region": "PACIFIC", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "FBC News (Fiji)", "homepage_url": "https://www.fbcnews.com.fj/", "feed_url": "https://www.fbcnews.com.fj/feed/", "api_kind": None, "fetch_method": "rss", "region": "FJ", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Post Courier (PNG)", "homepage_url": "https://www.postcourier.com.pg/", "feed_url": "https://www.postcourier.com.pg/feed/", "api_kind": None, "fetch_method": "rss", "region": "PG", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 1},
    {"name": "Islands Business", "homepage_url": "https://islandsbusiness.com/", "feed_url": "https://islandsbusiness.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "PACIFIC", "languages": ["en"], "categories": ["business", "economy", "regional"], "bot_sensitivity": 1},

    # ── Pan-Asia tech / startups / business ──────────────────────────────────
    {"name": "e27", "homepage_url": "https://e27.co/", "feed_url": "https://e27.co/feed/", "api_kind": None, "fetch_method": "rss", "region": "SG", "languages": ["en"], "categories": ["technology", "startups", "business"], "bot_sensitivity": 1},
    {"name": "Rest of World", "homepage_url": "https://restofworld.org/", "feed_url": "https://restofworld.org/feed/latest/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["technology", "society", "analysis"], "bot_sensitivity": 1},
]
