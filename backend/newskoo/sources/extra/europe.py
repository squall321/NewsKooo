"""Europe-depth seed bucket: outlets beyond the big internationals.

Hand-curated, individually live-verified RSS/Atom feeds covering European
breadth that the core catalog under-serves: the Nordics (SE/NO/DK/FI/IS),
the Baltics (EE/LV/LT), Central/Eastern Europe (PL/CZ/SK/HU/RO/BG/HR/SI/GR/UA),
Iberia incl. regional/Catalan/Basque press (ES/PT), Italy, Benelux + Luxembourg,
DACH regional (DE/AT/CH incl. French/German Switzerland), Ireland, plus
pan-European EU/Brussels affairs and a few European science/research bodies.
General + business/economy + technology, mostly in the native language.

Every ``feed_url`` below was fetched on 2026-06 with a desktop-browser
User-Agent and confirmed to return a parseable feed containing >= 1 real
article item. Outlets already present in the core catalog (BBC, Le Monde,
Der Spiegel, FAZ, El Pais, El Mundo, La Vanguardia, Corriere, RTE, NOS, NRK,
DR, Heise, Yle-EN, etc.) are intentionally excluded. Each entry matches the
dict shape consumed by :class:`newskoo.sources.schemas.SourceCreate`.
"""

from __future__ import annotations

SOURCES: list[dict] = [
    # ── Nordics: Sweden ──────────────────────────────────────────────────────
    {"name": "The Local Sweden", "homepage_url": "https://www.thelocal.se/", "feed_url": "https://www.thelocal.se/feeds/rss.php", "api_kind": None, "fetch_method": "rss", "region": "SE", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Expressen (Sweden)", "homepage_url": "https://www.expressen.se/", "feed_url": "https://feeds.expressen.se/nyheter/", "api_kind": None, "fetch_method": "rss", "region": "SE", "languages": ["sv"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "SVT Nyheter (Sweden)", "homepage_url": "https://www.svt.se/nyheter/", "feed_url": "https://www.svt.se/nyheter/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "SE", "languages": ["sv"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Aftonbladet (Sweden)", "homepage_url": "https://www.aftonbladet.se/", "feed_url": "https://www.aftonbladet.se/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "SE", "languages": ["sv"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Dagens Industri (Sweden)", "homepage_url": "https://www.di.se/", "feed_url": "https://www.di.se/rss", "api_kind": None, "fetch_method": "rss", "region": "SE", "languages": ["sv"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 0},

    # ── Nordics: Norway ──────────────────────────────────────────────────────
    {"name": "VG (Norway)", "homepage_url": "https://www.vg.no/", "feed_url": "https://www.vg.no/rss/feed/", "api_kind": None, "fetch_method": "rss", "region": "NO", "languages": ["no"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "E24 (Norway, business)", "homepage_url": "https://e24.no/", "feed_url": "https://e24.no/rss", "api_kind": None, "fetch_method": "rss", "region": "NO", "languages": ["no"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 0},
    {"name": "The Local Norway", "homepage_url": "https://www.thelocal.no/", "feed_url": "https://www.thelocal.no/feeds/rss.php", "api_kind": None, "fetch_method": "rss", "region": "NO", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── Nordics: Denmark ─────────────────────────────────────────────────────
    {"name": "Børsen (Denmark, business)", "homepage_url": "https://borsen.dk/", "feed_url": "https://borsen.dk/rss", "api_kind": None, "fetch_method": "rss", "region": "DK", "languages": ["da"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 0},
    {"name": "Berlingske (Denmark)", "homepage_url": "https://www.berlingske.dk/", "feed_url": "https://www.berlingske.dk/content/rss", "api_kind": None, "fetch_method": "rss", "region": "DK", "languages": ["da"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "The Local Denmark", "homepage_url": "https://www.thelocal.dk/", "feed_url": "https://www.thelocal.dk/feeds/rss.php", "api_kind": None, "fetch_method": "rss", "region": "DK", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── Nordics: Finland ─────────────────────────────────────────────────────
    {"name": "Ilta-Sanomat (Finland)", "homepage_url": "https://www.is.fi/", "feed_url": "https://www.is.fi/rss/tuoreimmat.xml", "api_kind": None, "fetch_method": "rss", "region": "FI", "languages": ["fi"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Yle Uutiset (Finland, Finnish)", "homepage_url": "https://yle.fi/uutiset", "feed_url": "https://yle.fi/rss/uutiset/paauutiset", "api_kind": None, "fetch_method": "rss", "region": "FI", "languages": ["fi"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},

    # ── Nordics: Iceland ─────────────────────────────────────────────────────
    {"name": "Morgunblaðið (mbl.is, Iceland)", "homepage_url": "https://www.mbl.is/", "feed_url": "https://www.mbl.is/feeds/fp/", "api_kind": None, "fetch_method": "rss", "region": "IS", "languages": ["is"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Vísir (Iceland)", "homepage_url": "https://www.visir.is/", "feed_url": "https://www.visir.is/rss/allt", "api_kind": None, "fetch_method": "rss", "region": "IS", "languages": ["is"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── Baltics ──────────────────────────────────────────────────────────────
    {"name": "ERR News (Estonia)", "homepage_url": "https://news.err.ee/", "feed_url": "https://news.err.ee/rss", "api_kind": None, "fetch_method": "rss", "region": "EE", "languages": ["en"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Delfi (Lithuania)", "homepage_url": "https://www.delfi.lt/", "feed_url": "https://www.delfi.lt/rss/feeds/daily.xml", "api_kind": None, "fetch_method": "rss", "region": "LT", "languages": ["lt"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "LSM (Latvia, English)", "homepage_url": "https://eng.lsm.lv/", "feed_url": "https://eng.lsm.lv/rss/", "api_kind": None, "fetch_method": "rss", "region": "LV", "languages": ["en"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "The Baltic Times", "homepage_url": "https://www.baltictimes.com/", "feed_url": "https://www.baltictimes.com/rss/", "api_kind": None, "fetch_method": "rss", "region": "EE", "languages": ["en"], "categories": ["general", "world", "business"], "bot_sensitivity": 0},

    # ── Poland ───────────────────────────────────────────────────────────────
    {"name": "Rzeczpospolita (Poland)", "homepage_url": "https://www.rp.pl/", "feed_url": "https://www.rp.pl/rss_main", "api_kind": None, "fetch_method": "rss", "region": "PL", "languages": ["pl"], "categories": ["general", "business", "economy"], "bot_sensitivity": 0},
    {"name": "Wirtualna Polska (WP, Poland)", "homepage_url": "https://wiadomosci.wp.pl/", "feed_url": "https://wiadomosci.wp.pl/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "PL", "languages": ["pl"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Polsat News (Poland)", "homepage_url": "https://www.polsatnews.pl/", "feed_url": "https://www.polsatnews.pl/rss/wszystkie.xml", "api_kind": None, "fetch_method": "rss", "region": "PL", "languages": ["pl"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Bankier.pl (Poland, finance)", "homepage_url": "https://www.bankier.pl/", "feed_url": "https://www.bankier.pl/rss/wiadomosci.xml", "api_kind": None, "fetch_method": "rss", "region": "PL", "languages": ["pl"], "categories": ["business", "economy", "markets", "finance"], "bot_sensitivity": 0},
    {"name": "Notes from Poland (English)", "homepage_url": "https://notesfrompoland.com/", "feed_url": "https://notesfrompoland.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "PL", "languages": ["en"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},

    # ── Czechia & Slovakia ───────────────────────────────────────────────────
    {"name": "iROZHLAS (Czech Radio)", "homepage_url": "https://www.irozhlas.cz/", "feed_url": "https://www.irozhlas.cz/rss/irozhlas", "api_kind": None, "fetch_method": "rss", "region": "CZ", "languages": ["cs"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "ČT24 (Czech Television)", "homepage_url": "https://ct24.ceskatelevize.cz/", "feed_url": "https://ct24.ceskatelevize.cz/rss", "api_kind": None, "fetch_method": "rss", "region": "CZ", "languages": ["cs"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Denník N (Slovakia)", "homepage_url": "https://dennikn.sk/", "feed_url": "https://dennikn.sk/feed/", "api_kind": None, "fetch_method": "rss", "region": "SK", "languages": ["sk"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "The Slovak Spectator (English)", "homepage_url": "https://spectator.sme.sk/", "feed_url": "https://spectator.sme.sk/rss", "api_kind": None, "fetch_method": "rss", "region": "SK", "languages": ["en"], "categories": ["general", "world", "business"], "bot_sensitivity": 0},
    {"name": "Pravda (Slovakia)", "homepage_url": "https://spravy.pravda.sk/", "feed_url": "https://spravy.pravda.sk/rss/xml/", "api_kind": None, "fetch_method": "rss", "region": "SK", "languages": ["sk"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── Hungary ──────────────────────────────────────────────────────────────
    {"name": "HVG (Hungary)", "homepage_url": "https://hvg.hu/", "feed_url": "https://hvg.hu/rss", "api_kind": None, "fetch_method": "rss", "region": "HU", "languages": ["hu"], "categories": ["general", "business", "economy"], "bot_sensitivity": 0},
    {"name": "Telex (Hungary)", "homepage_url": "https://telex.hu/", "feed_url": "https://telex.hu/rss", "api_kind": None, "fetch_method": "rss", "region": "HU", "languages": ["hu"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Hungary Today (English)", "homepage_url": "https://hungarytoday.hu/", "feed_url": "https://hungarytoday.hu/feed/", "api_kind": None, "fetch_method": "rss", "region": "HU", "languages": ["en"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},

    # ── Romania ──────────────────────────────────────────────────────────────
    {"name": "Digi24 (Romania)", "homepage_url": "https://www.digi24.ro/", "feed_url": "https://www.digi24.ro/rss", "api_kind": None, "fetch_method": "rss", "region": "RO", "languages": ["ro"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Adevărul (Romania)", "homepage_url": "https://adevarul.ro/", "feed_url": "https://adevarul.ro/rss", "api_kind": None, "fetch_method": "rss", "region": "RO", "languages": ["ro"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── Bulgaria ─────────────────────────────────────────────────────────────
    {"name": "Novinite (Bulgaria, English)", "homepage_url": "https://www.novinite.com/", "feed_url": "https://www.novinite.com/services/news_rdf.php", "api_kind": None, "fetch_method": "rss", "region": "BG", "languages": ["en"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Dnevnik (Bulgaria)", "homepage_url": "https://www.dnevnik.bg/", "feed_url": "https://www.dnevnik.bg/rss/", "api_kind": None, "fetch_method": "rss", "region": "BG", "languages": ["bg"], "categories": ["general", "business", "economy"], "bot_sensitivity": 0},

    # ── Croatia & Slovenia & Balkans ─────────────────────────────────────────
    {"name": "Jutarnji list (Croatia)", "homepage_url": "https://www.jutarnji.hr/", "feed_url": "https://www.jutarnji.hr/feed", "api_kind": None, "fetch_method": "rss", "region": "HR", "languages": ["hr"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Total Croatia News (English)", "homepage_url": "https://www.total-croatia-news.com/", "feed_url": "https://www.total-croatia-news.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "HR", "languages": ["en"], "categories": ["general", "world", "business"], "bot_sensitivity": 0},
    {"name": "RTV SLO (Slovenia)", "homepage_url": "https://www.rtvslo.si/", "feed_url": "https://www.rtvslo.si/feeds/00.xml", "api_kind": None, "fetch_method": "rss", "region": "SI", "languages": ["sl"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Balkan Insight (BIRN)", "homepage_url": "https://balkaninsight.com/", "feed_url": "https://balkaninsight.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "RS", "languages": ["en"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},

    # ── Greece ───────────────────────────────────────────────────────────────
    {"name": "To Vima (Greece)", "homepage_url": "https://www.tovima.com/", "feed_url": "https://www.tovima.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GR", "languages": ["el"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Naftemporiki (Greece, business)", "homepage_url": "https://www.naftemporiki.gr/", "feed_url": "https://www.naftemporiki.gr/feed/", "api_kind": None, "fetch_method": "rss", "region": "GR", "languages": ["el"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 0},
    {"name": "Greek City Times (English)", "homepage_url": "https://greekcitytimes.com/", "feed_url": "https://greekcitytimes.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GR", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── Ukraine ──────────────────────────────────────────────────────────────
    {"name": "Ukrainska Pravda (UA-language)", "homepage_url": "https://www.pravda.com.ua/", "feed_url": "https://www.pravda.com.ua/rss/", "api_kind": None, "fetch_method": "rss", "region": "UA", "languages": ["uk"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},

    # ── Spain: national + regional + Catalan/Basque ──────────────────────────
    {"name": "El Diario (Spain)", "homepage_url": "https://www.eldiario.es/", "feed_url": "https://www.eldiario.es/rss/", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["es"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "ABC (Spain)", "homepage_url": "https://www.abc.es/", "feed_url": "https://www.abc.es/rss/feeds/abcPortada.xml", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["es"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "El Correo (Basque Country)", "homepage_url": "https://www.elcorreo.com/", "feed_url": "https://www.elcorreo.com/rss/2.0/portada", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["es"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "El Periódico — Economía (Spain)", "homepage_url": "https://www.elperiodico.com/", "feed_url": "https://www.elperiodico.com/es/rss/economia/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["es"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 0},
    {"name": "20minutos (Spain)", "homepage_url": "https://www.20minutos.es/", "feed_url": "https://www.20minutos.es/rss/", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["es"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Nació Digital (Catalan)", "homepage_url": "https://www.naciodigital.cat/", "feed_url": "https://www.naciodigital.cat/rss/portada", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["ca"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "VilaWeb (Catalan)", "homepage_url": "https://www.vilaweb.cat/", "feed_url": "https://www.vilaweb.cat/rss/", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["ca"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},

    # ── Portugal ─────────────────────────────────────────────────────────────
    {"name": "Observador (Portugal)", "homepage_url": "https://observador.pt/", "feed_url": "https://observador.pt/feed/", "api_kind": None, "fetch_method": "rss", "region": "PT", "languages": ["pt"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "ECO (Portugal, economy)", "homepage_url": "https://eco.sapo.pt/", "feed_url": "https://eco.sapo.pt/feed/", "api_kind": None, "fetch_method": "rss", "region": "PT", "languages": ["pt"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 0},
    {"name": "Jornal de Negócios (Portugal)", "homepage_url": "https://www.jornaldenegocios.pt/", "feed_url": "https://www.jornaldenegocios.pt/rss", "api_kind": None, "fetch_method": "rss", "region": "PT", "languages": ["pt"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 0},
    {"name": "The Portugal News (English)", "homepage_url": "https://www.theportugalnews.com/", "feed_url": "https://www.theportugalnews.com/rss", "api_kind": None, "fetch_method": "rss", "region": "PT", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── Italy ────────────────────────────────────────────────────────────────
    {"name": "Il Fatto Quotidiano (Italy)", "homepage_url": "https://www.ilfattoquotidiano.it/", "feed_url": "https://www.ilfattoquotidiano.it/feed/", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Il Messaggero (Italy)", "homepage_url": "https://www.ilmessaggero.it/", "feed_url": "https://www.ilmessaggero.it/rss/home.xml", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Il Giornale (Italy)", "homepage_url": "https://www.ilgiornale.it/", "feed_url": "https://www.ilgiornale.it/feed.xml", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Open (Italy)", "homepage_url": "https://www.open.online/", "feed_url": "https://www.open.online/feed/", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Wired Italia (tech)", "homepage_url": "https://www.wired.it/", "feed_url": "https://www.wired.it/feed/rss", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["technology", "science"], "bot_sensitivity": 0},
    {"name": "La Gazzetta dello Sport (Italy)", "homepage_url": "https://www.gazzetta.it/", "feed_url": "https://www.gazzetta.it/rss/homepage.xml", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["sport"], "bot_sensitivity": 0},

    # ── Benelux: Netherlands ─────────────────────────────────────────────────
    {"name": "NRC (Netherlands)", "homepage_url": "https://www.nrc.nl/", "feed_url": "https://www.nrc.nl/rss/", "api_kind": None, "fetch_method": "rss", "region": "NL", "languages": ["nl"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "De Telegraaf (Netherlands)", "homepage_url": "https://www.telegraaf.nl/", "feed_url": "https://www.telegraaf.nl/rss", "api_kind": None, "fetch_method": "rss", "region": "NL", "languages": ["nl"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "DutchNews.nl (English)", "homepage_url": "https://www.dutchnews.nl/", "feed_url": "https://www.dutchnews.nl/feed/", "api_kind": None, "fetch_method": "rss", "region": "NL", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── Benelux: Belgium ─────────────────────────────────────────────────────
    {"name": "De Morgen (Belgium)", "homepage_url": "https://www.demorgen.be/", "feed_url": "https://www.demorgen.be/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "BE", "languages": ["nl"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Het Laatste Nieuws (HLN, Belgium)", "homepage_url": "https://www.hln.be/", "feed_url": "https://www.hln.be/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "BE", "languages": ["nl"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "De Tijd (Belgium, business)", "homepage_url": "https://www.tijd.be/", "feed_url": "https://www.tijd.be/rss/top_stories.xml", "api_kind": None, "fetch_method": "rss", "region": "BE", "languages": ["nl"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 0},
    {"name": "La Libre Belgique", "homepage_url": "https://www.lalibre.be/", "feed_url": "https://www.lalibre.be/arc/outboundfeeds/rss/?outputType=xml", "api_kind": None, "fetch_method": "rss", "region": "BE", "languages": ["fr"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "The Brussels Times (Belgium, English)", "homepage_url": "https://www.brusselstimes.com/", "feed_url": None, "api_kind": None, "fetch_method": "html", "region": "BE", "languages": ["en"], "categories": ["general", "world", "politics"], "bot_sensitivity": 1},

    # ── Benelux: Luxembourg ──────────────────────────────────────────────────
    {"name": "Luxembourg Times (English)", "homepage_url": "https://www.luxtimes.lu/", "feed_url": "https://www.luxtimes.lu/rss", "api_kind": None, "fetch_method": "rss", "region": "LU", "languages": ["en"], "categories": ["general", "world", "business"], "bot_sensitivity": 0},

    # ── DACH regional: Germany ───────────────────────────────────────────────
    {"name": "Tagesschau (Germany)", "homepage_url": "https://www.tagesschau.de/", "feed_url": "https://www.tagesschau.de/index~rss2.xml", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Der Tagesspiegel (Berlin)", "homepage_url": "https://www.tagesspiegel.de/", "feed_url": "https://www.tagesspiegel.de/contentexport/feed/home", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "WirtschaftsWoche (Germany)", "homepage_url": "https://www.wiwo.de/", "feed_url": "https://www.wiwo.de/contentexport/feed/rss/schlagzeilen", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 0},
    {"name": "taz (die tageszeitung, Germany)", "homepage_url": "https://taz.de/", "feed_url": "https://taz.de/!p4608;rss/", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Golem.de (Germany, tech)", "homepage_url": "https://www.golem.de/", "feed_url": "https://www.golem.de/rss.php?feed=RSS2.0", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["technology", "science"], "bot_sensitivity": 0},
    {"name": "t3n (Germany, digital/tech)", "homepage_url": "https://www.t3n.de/", "feed_url": "https://www.t3n.de/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["technology", "business"], "bot_sensitivity": 0},

    # ── DACH regional: Austria ───────────────────────────────────────────────
    {"name": "Der Standard (Austria)", "homepage_url": "https://www.derstandard.at/", "feed_url": "https://www.derstandard.at/rss", "api_kind": None, "fetch_method": "rss", "region": "AT", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "ORF News (Austria)", "homepage_url": "https://orf.at/", "feed_url": "https://rss.orf.at/news.xml", "api_kind": None, "fetch_method": "rss", "region": "AT", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Kurier (Austria)", "homepage_url": "https://kurier.at/", "feed_url": "https://kurier.at/xml/rss", "api_kind": None, "fetch_method": "rss", "region": "AT", "languages": ["de"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── DACH regional: Switzerland ───────────────────────────────────────────
    {"name": "Tages-Anzeiger (Switzerland)", "homepage_url": "https://www.tagesanzeiger.ch/", "feed_url": "https://www.tagesanzeiger.ch/rss.html", "api_kind": None, "fetch_method": "rss", "region": "CH", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "SRF News (Switzerland)", "homepage_url": "https://www.srf.ch/news", "feed_url": "https://www.srf.ch/news/bnf/rss/1646", "api_kind": None, "fetch_method": "rss", "region": "CH", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Le Temps (Switzerland, French)", "homepage_url": "https://www.letemps.ch/", "feed_url": "https://www.letemps.ch/articles.rss", "api_kind": None, "fetch_method": "rss", "region": "CH", "languages": ["fr"], "categories": ["general", "world", "business"], "bot_sensitivity": 0},
    {"name": "RTS Info (Switzerland, French)", "homepage_url": "https://www.rts.ch/info/", "feed_url": "https://www.rts.ch/info/?format=rss/news", "api_kind": None, "fetch_method": "rss", "region": "CH", "languages": ["fr"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},

    # ── France: regional + business + tech (beyond the majors) ───────────────
    {"name": "Ouest-France", "homepage_url": "https://www.ouest-france.fr/", "feed_url": "https://www.ouest-france.fr/rss/une", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Mediapart (France)", "homepage_url": "https://www.mediapart.fr/", "feed_url": "https://www.mediapart.fr/articles/feed", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "RFI (France, français)", "homepage_url": "https://www.rfi.fr/fr/", "feed_url": "https://www.rfi.fr/fr/rss", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Numerama (France, tech)", "homepage_url": "https://www.numerama.com/", "feed_url": "https://www.numerama.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["technology", "science"], "bot_sensitivity": 0},
    {"name": "01net (France, tech)", "homepage_url": "https://www.01net.com/", "feed_url": "https://www.01net.com/actualites/feed/", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["technology"], "bot_sensitivity": 0},

    # ── Ireland (beyond RTÉ / Irish Times) ───────────────────────────────────
    {"name": "TheJournal.ie (Ireland)", "homepage_url": "https://www.thejournal.ie/", "feed_url": "https://www.thejournal.ie/feed/", "api_kind": None, "fetch_method": "rss", "region": "IE", "languages": ["en"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Irish Independent", "homepage_url": "https://www.independent.ie/", "feed_url": "https://www.independent.ie/rss", "api_kind": None, "fetch_method": "rss", "region": "IE", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── Cyprus ───────────────────────────────────────────────────────────────
    {"name": "Cyprus Mail (English)", "homepage_url": "https://cyprus-mail.com/", "feed_url": "https://cyprus-mail.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "CY", "languages": ["en"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},

    # ── Pan-European / EU affairs (Brussels) ─────────────────────────────────
    {"name": "EURACTIV (EU affairs)", "homepage_url": "https://www.euractiv.com/", "feed_url": "https://www.euractiv.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["politics", "general", "economy"], "bot_sensitivity": 0},
    {"name": "POLITICO Europe", "homepage_url": "https://www.politico.eu/", "feed_url": "https://www.politico.eu/feed/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["politics", "general", "world"], "bot_sensitivity": 1},
    {"name": "EUbusiness", "homepage_url": "https://www.eubusiness.com/", "feed_url": "https://www.eubusiness.com/feed", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["business", "economy", "politics"], "bot_sensitivity": 0},
    {"name": "Emerging Europe", "homepage_url": "https://emerging-europe.com/", "feed_url": "https://emerging-europe.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["business", "economy", "general"], "bot_sensitivity": 0},
    {"name": "Kafkadesk (Central Europe)", "homepage_url": "https://kafkadesk.org/", "feed_url": "https://kafkadesk.org/feed/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Sifted (European startups/tech)", "homepage_url": "https://sifted.eu/", "feed_url": "https://sifted.eu/feed", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["technology", "business", "niche"], "bot_sensitivity": 0},
    {"name": "Tech.eu (European tech)", "homepage_url": "https://tech.eu/", "feed_url": "https://tech.eu/feed/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["technology", "business", "niche"], "bot_sensitivity": 0},

    # ── European science / research bodies ───────────────────────────────────
    {"name": "CNRS (France, research)", "homepage_url": "https://www.cnrs.fr/", "feed_url": "https://www.cnrs.fr/fr/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["science", "research", "niche"], "bot_sensitivity": 0},
    {"name": "EMBL (European Molecular Biology Lab)", "homepage_url": "https://www.embl.org/", "feed_url": "https://www.embl.org/news/feed/", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["en"], "categories": ["science", "research", "niche"], "bot_sensitivity": 0},
]
