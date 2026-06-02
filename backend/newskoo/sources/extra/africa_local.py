"""Extra seed bucket — AFRICA LOCAL / REGIONAL depth (new countries).

Hand-curated, individually live-verified RSS/Atom feeds extending NewsKoo's
African coverage into countries and outlets NOT already present in the main
catalog or in ``africa_me.py``. The focus is the long tail of national and
regional journalism rather than continental flagships:

  * Francophone West/Central Africa — Cameroon, Cote d'Ivoire / Abidjan,
    Senegal, Mali, Burkina Faso, DR Congo, Gabon, Benin, Togo, Niger, Chad,
    Madagascar.
  * Lusophone Africa — Mozambique, Cabo Verde, Sao Tome.
  * Anglophone regional — Ghana, Kenya (incl. Swahili), Uganda, Tanzania
    (incl. Swahili), Zambia, Malawi, Botswana, Namibia, Zimbabwe, Rwanda,
    Sierra Leone, Liberia, Gambia, South Sudan, Sudan, Somalia, Ethiopia.
  * Maghreb regional — Morocco, Algeria (incl. Arabic), Tunisia, Libya.

Native languages represented: French (fr), Portuguese (pt), Swahili (sw),
Arabic (ar) and English (en).

Every ``rss`` entry below was fetched with a desktop browser User-Agent on
2026-06-03 and confirmed to return a parseable feed (``<rss>``/``<feed>``/
``<rdf>`` with at least one real ``<item>``/``<entry>``). Outlets whose feeds
404'd / 403'd / returned HTML-only on that date were discarded (notable dead
ones: cameroon-info.net, abidjan.net, koaci, fratmat, seneweb, maliweb;
Angolan press — angop, jornaldeangola, novojornal; Botswana mmegi; Zimbabwe
Herald/Newsday/Chronicle; Nigeria guardian.ng / tribuneonline; Morocco le360 /
yabiladi / mapnews; Algeria aps.dz / elwatan). Outlets already covered in
``africa_me.py`` (Dakaractu, The Namibian, TSA Algerie, etc.) are intentionally
omitted here to avoid duplicates.

Shape matches ``newskoo.sources.schemas.SourceCreate``: name, homepage_url,
feed_url, api_kind, fetch_method, region, languages, categories,
bot_sensitivity.
"""

from __future__ import annotations

SOURCES: list[dict] = [
    # ── Cameroon (fr/en) ─────────────────────────────────────────────────────
    {"name": "Actu Cameroun", "homepage_url": "https://actucameroun.com/", "feed_url": "https://actucameroun.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "CM", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "Journal du Cameroun", "homepage_url": "https://www.journalducameroun.com/", "feed_url": "https://www.journalducameroun.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "CM", "languages": ["fr"], "categories": ["general", "politics", "world"], "bot_sensitivity": 0},

    # ── Cote d'Ivoire (fr) ───────────────────────────────────────────────────
    {"name": "Le Banco (Cote d'Ivoire)", "homepage_url": "https://www.lebanco.net/", "feed_url": "https://www.lebanco.net/feed/", "api_kind": None, "fetch_method": "rss", "region": "CI", "languages": ["fr"], "categories": ["general", "local", "politics"], "bot_sensitivity": 0},

    # ── Senegal (fr) ─────────────────────────────────────────────────────────
    {"name": "PressAfrik (Senegal)", "homepage_url": "https://www.pressafrik.com/", "feed_url": "https://www.pressafrik.com/xml/syndication.rss", "api_kind": None, "fetch_method": "rss", "region": "SN", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "Leral (Senegal)", "homepage_url": "https://www.leral.net/", "feed_url": "https://www.leral.net/xml/syndication.rss", "api_kind": None, "fetch_method": "rss", "region": "SN", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},

    # ── Mali (fr) ────────────────────────────────────────────────────────────
    {"name": "Mali Actu", "homepage_url": "https://maliactu.net/", "feed_url": "https://maliactu.net/feed/", "api_kind": None, "fetch_method": "rss", "region": "ML", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},

    # ── Burkina Faso (fr) ────────────────────────────────────────────────────
    {"name": "Lefaso.net (Burkina Faso)", "homepage_url": "https://lefaso.net/", "feed_url": "https://lefaso.net/spip.php?page=backend", "api_kind": None, "fetch_method": "rss", "region": "BF", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "Burkina24", "homepage_url": "https://www.burkina24.com/", "feed_url": "https://www.burkina24.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "BF", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},

    # ── DR Congo (fr) ────────────────────────────────────────────────────────
    {"name": "Actualite.cd (DR Congo)", "homepage_url": "https://actualite.cd/", "feed_url": "https://actualite.cd/feed", "api_kind": None, "fetch_method": "rss", "region": "CD", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "Radio Okapi (DR Congo)", "homepage_url": "https://www.radiookapi.net/", "feed_url": "https://www.radiookapi.net/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "CD", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},

    # ── Gabon (fr) ───────────────────────────────────────────────────────────
    {"name": "Gabon Review", "homepage_url": "https://www.gabonreview.com/", "feed_url": "https://www.gabonreview.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GA", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "Gabon Actu", "homepage_url": "https://www.gabonactu.com/", "feed_url": "https://www.gabonactu.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GA", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},

    # ── Benin (fr) ───────────────────────────────────────────────────────────
    {"name": "La Nouvelle Tribune (Benin)", "homepage_url": "https://lanouvelletribune.info/", "feed_url": "https://lanouvelletribune.info/feed/", "api_kind": None, "fetch_method": "rss", "region": "BJ", "languages": ["fr"], "categories": ["general", "politics", "world"], "bot_sensitivity": 0},
    {"name": "Benin Web TV", "homepage_url": "https://beninwebtv.com/", "feed_url": "https://beninwebtv.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "BJ", "languages": ["fr"], "categories": ["general", "local", "politics"], "bot_sensitivity": 0},
    {"name": "Matin Libre (Benin)", "homepage_url": "https://www.matinlibre.com/", "feed_url": "https://www.matinlibre.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "BJ", "languages": ["fr"], "categories": ["general", "local", "politics"], "bot_sensitivity": 0},

    # ── Togo (fr) ────────────────────────────────────────────────────────────
    {"name": "IciLome (Togo)", "homepage_url": "https://www.icilome.com/", "feed_url": "https://www.icilome.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "TG", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "Togo-Presse", "homepage_url": "https://www.togopresse.tg/", "feed_url": "https://www.togopresse.tg/feed/", "api_kind": None, "fetch_method": "rss", "region": "TG", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},

    # ── Niger / Chad / Madagascar (fr) ───────────────────────────────────────
    {"name": "Tchad Infos", "homepage_url": "https://www.tchadinfos.com/", "feed_url": "https://www.tchadinfos.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "TD", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "Madagascar Tribune", "homepage_url": "https://madagascar-tribune.com/", "feed_url": "https://madagascar-tribune.com/spip.php?page=backend", "api_kind": None, "fetch_method": "rss", "region": "MG", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},

    # ── Mozambique (pt) ──────────────────────────────────────────────────────
    {"name": "O Pais (Mozambique)", "homepage_url": "https://opais.co.mz/", "feed_url": "https://opais.co.mz/feed/", "api_kind": None, "fetch_method": "rss", "region": "MZ", "languages": ["pt"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "@Verdade (Mozambique)", "homepage_url": "https://www.verdade.co.mz/", "feed_url": "https://www.verdade.co.mz/feed", "api_kind": None, "fetch_method": "rss", "region": "MZ", "languages": ["pt"], "categories": ["general", "investigative", "local"], "bot_sensitivity": 0},
    {"name": "Carta de Mocambique", "homepage_url": "https://www.cartamz.com/", "feed_url": "https://www.cartamz.com/index.php/feed", "api_kind": None, "fetch_method": "rss", "region": "MZ", "languages": ["pt"], "categories": ["general", "politics", "investigative"], "bot_sensitivity": 0},
    {"name": "Club of Mozambique", "homepage_url": "https://clubofmozambique.com/", "feed_url": "https://clubofmozambique.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "MZ", "languages": ["en"], "categories": ["general", "business", "world"], "bot_sensitivity": 0},

    # ── Cabo Verde (pt) ──────────────────────────────────────────────────────
    {"name": "A Nacao (Cabo Verde)", "homepage_url": "https://anacao.cv/", "feed_url": "https://anacao.cv/feed/", "api_kind": None, "fetch_method": "rss", "region": "CV", "languages": ["pt"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},

    # ── Sao Tome and Principe (pt) ───────────────────────────────────────────
    {"name": "Tela Non (Sao Tome)", "homepage_url": "https://www.telanon.info/", "feed_url": "https://www.telanon.info/feed/", "api_kind": None, "fetch_method": "rss", "region": "ST", "languages": ["pt"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},

    # ── Ghana (en) ───────────────────────────────────────────────────────────
    {"name": "Adom Online (Ghana)", "homepage_url": "https://www.adomonline.com/", "feed_url": "https://www.adomonline.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GH", "languages": ["en"], "categories": ["general", "local", "politics"], "bot_sensitivity": 0},

    # ── Kenya (en / sw) ──────────────────────────────────────────────────────
    {"name": "Daily Nation (Kenya)", "homepage_url": "https://nation.africa/kenya", "feed_url": "https://nation.africa/kenya/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "KE", "languages": ["en"], "categories": ["general", "politics", "local"], "bot_sensitivity": 1},
    {"name": "KBC (Kenya Broadcasting)", "homepage_url": "https://www.kbc.co.ke/", "feed_url": "https://www.kbc.co.ke/feed/", "api_kind": None, "fetch_method": "rss", "region": "KE", "languages": ["en"], "categories": ["general", "local", "world"], "bot_sensitivity": 0},
    {"name": "Taifa Leo (Kenya, Swahili)", "homepage_url": "https://taifaleo.nation.co.ke/", "feed_url": "https://taifaleo.nation.co.ke/feed", "api_kind": None, "fetch_method": "rss", "region": "KE", "languages": ["sw"], "categories": ["general", "local", "politics"], "bot_sensitivity": 1},

    # ── Uganda (en) ──────────────────────────────────────────────────────────
    {"name": "SoftPower News (Uganda)", "homepage_url": "https://www.softpower.ug/", "feed_url": "https://www.softpower.ug/feed/", "api_kind": None, "fetch_method": "rss", "region": "UG", "languages": ["en"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},

    # ── Tanzania (en / sw) ───────────────────────────────────────────────────
    {"name": "Daily News (Tanzania)", "homepage_url": "https://dailynews.co.tz/", "feed_url": "https://dailynews.co.tz/feed/", "api_kind": None, "fetch_method": "rss", "region": "TZ", "languages": ["en"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "Global Publishers (Tanzania, Swahili)", "homepage_url": "https://globalpublishers.co.tz/", "feed_url": "https://globalpublishers.co.tz/feed/", "api_kind": None, "fetch_method": "rss", "region": "TZ", "languages": ["sw"], "categories": ["general", "local", "entertainment"], "bot_sensitivity": 0},

    # ── Zambia (en) ──────────────────────────────────────────────────────────
    {"name": "News Diggers! (Zambia)", "homepage_url": "https://diggers.news/", "feed_url": "https://diggers.news/feed/", "api_kind": None, "fetch_method": "rss", "region": "ZM", "languages": ["en"], "categories": ["general", "politics", "investigative"], "bot_sensitivity": 0},
    {"name": "Mwebantu (Zambia)", "homepage_url": "https://www.mwebantu.com/", "feed_url": "https://www.mwebantu.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "ZM", "languages": ["en"], "categories": ["general", "local", "politics"], "bot_sensitivity": 0},
    {"name": "Zambian Eye", "homepage_url": "https://zambianeye.com/", "feed_url": "https://zambianeye.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "ZM", "languages": ["en"], "categories": ["general", "local", "politics"], "bot_sensitivity": 0},
    {"name": "Zambia Daily Mail", "homepage_url": "https://www.daily-mail.co.zm/", "feed_url": "https://www.daily-mail.co.zm/feed/", "api_kind": None, "fetch_method": "rss", "region": "ZM", "languages": ["en"], "categories": ["general", "local", "politics"], "bot_sensitivity": 0},

    # ── Malawi (en) ──────────────────────────────────────────────────────────
    {"name": "Nyasa Times (Malawi)", "homepage_url": "https://www.nyasatimes.com/", "feed_url": "https://www.nyasatimes.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "MW", "languages": ["en"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "The Nation (Malawi)", "homepage_url": "https://mwnation.com/", "feed_url": "https://mwnation.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "MW", "languages": ["en"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "Times Group (Malawi)", "homepage_url": "https://times.mw/", "feed_url": "https://times.mw/feed/", "api_kind": None, "fetch_method": "rss", "region": "MW", "languages": ["en"], "categories": ["general", "local", "business"], "bot_sensitivity": 0},
    {"name": "The Maravi Post (Malawi)", "homepage_url": "https://www.maravipost.com/", "feed_url": "https://www.maravipost.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "MW", "languages": ["en"], "categories": ["general", "politics", "world"], "bot_sensitivity": 0},

    # ── Botswana (en) ────────────────────────────────────────────────────────
    {"name": "Sunday Standard (Botswana)", "homepage_url": "https://www.sundaystandard.info/", "feed_url": "https://www.sundaystandard.info/feed/", "api_kind": None, "fetch_method": "rss", "region": "BW", "languages": ["en"], "categories": ["general", "politics", "investigative"], "bot_sensitivity": 0},

    # ── Namibia (en) ─────────────────────────────────────────────────────────
    {"name": "New Era (Namibia)", "homepage_url": "https://neweralive.na/", "feed_url": "https://neweralive.na/feed/", "api_kind": None, "fetch_method": "rss", "region": "NA", "languages": ["en"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "Windhoek Observer", "homepage_url": "https://www.observer24.com.na/", "feed_url": "https://www.observer24.com.na/feed/", "api_kind": None, "fetch_method": "rss", "region": "NA", "languages": ["en"], "categories": ["general", "local", "politics"], "bot_sensitivity": 0},

    # ── Zimbabwe (en) ────────────────────────────────────────────────────────
    {"name": "ZimLive", "homepage_url": "https://www.zimlive.com/", "feed_url": "https://www.zimlive.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "ZW", "languages": ["en"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},

    # ── Rwanda (en) ──────────────────────────────────────────────────────────
    {"name": "KT Press (Rwanda)", "homepage_url": "https://www.ktpress.rw/", "feed_url": "https://www.ktpress.rw/feed/", "api_kind": None, "fetch_method": "rss", "region": "RW", "languages": ["en"], "categories": ["general", "politics", "business"], "bot_sensitivity": 0},

    # ── Sierra Leone (en) ────────────────────────────────────────────────────
    {"name": "Sierraloaded", "homepage_url": "https://www.sierraloaded.sl/", "feed_url": "https://www.sierraloaded.sl/feed/", "api_kind": None, "fetch_method": "rss", "region": "SL", "languages": ["en"], "categories": ["general", "local", "politics"], "bot_sensitivity": 0},

    # ── Liberia (en) ─────────────────────────────────────────────────────────
    {"name": "The New Dawn (Liberia)", "homepage_url": "https://thenewdawnliberia.com/", "feed_url": "https://thenewdawnliberia.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "LR", "languages": ["en"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},

    # ── Gambia (en) ──────────────────────────────────────────────────────────
    {"name": "Foroyaa (Gambia)", "homepage_url": "https://foroyaa.net/", "feed_url": "https://foroyaa.net/feed/", "api_kind": None, "fetch_method": "rss", "region": "GM", "languages": ["en"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "The Fatu Network (Gambia)", "homepage_url": "https://www.thefatunetwork.com/", "feed_url": "https://www.thefatunetwork.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GM", "languages": ["en"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},

    # ── South Sudan / Sudan (en) ─────────────────────────────────────────────
    {"name": "Radio Tamazuj (South Sudan)", "homepage_url": "https://www.radiotamazuj.org/", "feed_url": "https://www.radiotamazuj.org/en/rss", "api_kind": None, "fetch_method": "rss", "region": "SS", "languages": ["en"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "Eye Radio (South Sudan)", "homepage_url": "https://eyeradio.org/", "feed_url": "https://eyeradio.org/feed/", "api_kind": None, "fetch_method": "rss", "region": "SS", "languages": ["en"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "Sudans Post (South Sudan)", "homepage_url": "https://www.sudanspost.com/", "feed_url": "https://www.sudanspost.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "SS", "languages": ["en"], "categories": ["general", "politics", "world"], "bot_sensitivity": 0},
    {"name": "Radio Dabanga (Sudan)", "homepage_url": "https://www.dabangasudan.org/en", "feed_url": "https://www.dabangasudan.org/en/feed", "api_kind": None, "fetch_method": "rss", "region": "SD", "languages": ["en"], "categories": ["general", "politics", "world"], "bot_sensitivity": 0},

    # ── Somalia / Ethiopia (en) ──────────────────────────────────────────────
    {"name": "Goobjoog News (Somalia)", "homepage_url": "https://goobjoog.com/english/", "feed_url": "https://goobjoog.com/english/feed/", "api_kind": None, "fetch_method": "rss", "region": "SO", "languages": ["en"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "The Reporter (Ethiopia)", "homepage_url": "https://www.thereporterethiopia.com/", "feed_url": "https://www.thereporterethiopia.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "ET", "languages": ["en"], "categories": ["general", "politics", "business"], "bot_sensitivity": 0},

    # ── Nigeria (en) — additional national/regional ──────────────────────────
    {"name": "Premium Times (Nigeria)", "homepage_url": "https://www.premiumtimesng.com/", "feed_url": "https://www.premiumtimesng.com/feed", "api_kind": None, "fetch_method": "rss", "region": "NG", "languages": ["en"], "categories": ["general", "politics", "investigative"], "bot_sensitivity": 0},
    {"name": "Daily Trust (Nigeria)", "homepage_url": "https://dailytrust.com/", "feed_url": "https://dailytrust.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "NG", "languages": ["en"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "THISDAY (Nigeria)", "homepage_url": "https://www.thisdaylive.com/", "feed_url": "https://www.thisdaylive.com/index.php/feed/", "api_kind": None, "fetch_method": "rss", "region": "NG", "languages": ["en"], "categories": ["general", "politics", "business"], "bot_sensitivity": 0},

    # ── Morocco (fr) ─────────────────────────────────────────────────────────
    {"name": "Medias24 (Morocco)", "homepage_url": "https://www.medias24.com/", "feed_url": "https://www.medias24.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "MA", "languages": ["fr"], "categories": ["business", "economy", "politics"], "bot_sensitivity": 0},
    {"name": "TelQuel (Morocco)", "homepage_url": "https://telquel.ma/", "feed_url": "https://telquel.ma/feed", "api_kind": None, "fetch_method": "rss", "region": "MA", "languages": ["fr"], "categories": ["general", "politics", "world"], "bot_sensitivity": 0},

    # ── Algeria (fr / ar) ────────────────────────────────────────────────────
    {"name": "Algerie360", "homepage_url": "https://www.algerie360.com/", "feed_url": "https://www.algerie360.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "DZ", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "Observ'Algerie", "homepage_url": "https://www.observalgerie.com/", "feed_url": "https://www.observalgerie.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "DZ", "languages": ["fr"], "categories": ["general", "politics", "world"], "bot_sensitivity": 0},
    {"name": "El Khabar (Algeria, Arabic)", "homepage_url": "https://www.elkhabar.com/", "feed_url": "https://www.elkhabar.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "DZ", "languages": ["ar"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},

    # ── Tunisia (fr) ─────────────────────────────────────────────────────────
    {"name": "La Presse de Tunisie", "homepage_url": "https://lapresse.tn/", "feed_url": "https://lapresse.tn/feed/", "api_kind": None, "fetch_method": "rss", "region": "TN", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},
    {"name": "Mosaique FM (Tunisia)", "homepage_url": "https://www.mosaiquefm.net/fr", "feed_url": "https://www.mosaiquefm.net/fr/rss", "api_kind": None, "fetch_method": "rss", "region": "TN", "languages": ["fr"], "categories": ["general", "politics", "local"], "bot_sensitivity": 0},

    # ── Libya (en) ───────────────────────────────────────────────────────────
    {"name": "Libya Herald", "homepage_url": "https://libyaherald.com/", "feed_url": "https://libyaherald.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "LY", "languages": ["en"], "categories": ["general", "politics", "business"], "bot_sensitivity": 0},
]
