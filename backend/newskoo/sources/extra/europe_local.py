"""Extra seed bucket — EUROPE LOCAL / REGIONAL & smaller-country depth.

Hand-curated, individually live-verified RSS/Atom feeds for the long tail of
European journalism that the core catalog and the existing ``europe.py`` bucket
under-serve: German public-broadcaster regional desks (WDR, NDR, MDR, hr, rbb)
and regional Zeitungen; French regional / departmental dailies (Nice-Matin,
La Dépêche, Le Progrès, L'Alsace, Midi Libre, L'Indépendant, Var-Matin,
Ouest/Lyon city press) and France Bleu; Italian regional dailies plus the ANSA
regional desks and the *Today city network; Spanish regional press incl.
Galician, Basque-country and Catalan-language outlets; Nordic regional desks
(NRK district feeds, Swedish/Finnish regional, Icelandic); the Baltics in their
native languages; Poland / Czechia / Slovakia / Hungary / Romania regional and
city press; the Balkans (HR/SI/RS); Benelux regional; German- and
French-speaking Switzerland regional; Austrian regional (Kleine Zeitung,
Vienna/Bezirk); Luxembourg; Malta; and a couple of Greek outlets.

National flagships and outlets already present in the core catalog or in
``europe.py`` (BBC, Le Monde, Der Spiegel, FAZ, El País, Corriere, NOS, NRK
national, DR, Yle-EN, Der Standard, Il Fatto Quotidiano, To Vima, Denník N,
etc.) are intentionally excluded; the focus here is regional / city / native-
language long-tail desks.

Every ``feed_url`` below was fetched with a desktop-browser User-Agent on
2026-06-03 and confirmed to return a parseable feed (<rss / <feed / <rdf) with
at least one real <item / <entry. Feeds that 404'd, 403'd, returned empty, or
served HTML-only on that date were discarded. Shape matches
``newskoo.sources.schemas.SourceCreate``: name, homepage_url, feed_url,
api_kind, fetch_method, region, languages, categories, bot_sensitivity.
"""

from __future__ import annotations

SOURCES: list[dict] = [
    # ── Germany: public-broadcaster regional desks ───────────────────────────
    {"name": "WDR (Westdeutscher Rundfunk)", "homepage_url": "https://www1.wdr.de/", "feed_url": "https://www1.wdr.de/uebersicht-100.feed", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "NDR (Norddeutscher Rundfunk)", "homepage_url": "https://www.ndr.de/", "feed_url": "https://www.ndr.de/home/index-rss.xml", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "MDR (Mitteldeutscher Rundfunk)", "homepage_url": "https://www.mdr.de/nachrichten/", "feed_url": "https://www.mdr.de/nachrichten/index-rss.xml", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "hessenschau (hr, Hesse)", "homepage_url": "https://www.hessenschau.de/", "feed_url": "https://www.hessenschau.de/index.rss", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "rbb24 (Berlin-Brandenburg)", "homepage_url": "https://www.rbb24.de/", "feed_url": "https://www.rbb24.de/aktuell/index.xml/feed=rss.xml", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Tagesschau — Regional", "homepage_url": "https://www.tagesschau.de/inland/regional/", "feed_url": "https://www.tagesschau.de/inland/regional/index~rss2.xml", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},

    # ── Germany: regional / metro Zeitungen ──────────────────────────────────
    {"name": "Süddeutsche Zeitung — Topthemen", "homepage_url": "https://www.sueddeutsche.de/", "feed_url": "https://rss.sueddeutsche.de/rss/Topthemen", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Frankfurter Rundschau", "homepage_url": "https://www.fr.de/", "feed_url": "https://www.fr.de/rssfeed.rdf", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Stuttgarter Zeitung", "homepage_url": "https://www.stuttgarter-zeitung.de/", "feed_url": "https://www.stuttgarter-zeitung.de/news.rss.feed", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "RP Online (Rheinische Post)", "homepage_url": "https://rp-online.de/", "feed_url": "https://www.rp-online.de/feed.rss", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Münchner Merkur", "homepage_url": "https://www.merkur.de/", "feed_url": "https://www.merkur.de/rssfeed.rdf", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "tz München", "homepage_url": "https://www.tz.de/", "feed_url": "https://www.tz.de/rssfeed.rdf", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Berliner Zeitung", "homepage_url": "https://www.berliner-zeitung.de/", "feed_url": "https://www.berliner-zeitung.de/feed.xml", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Neue Osnabrücker Zeitung (NOZ)", "homepage_url": "https://www.noz.de/", "feed_url": "https://www.noz.de/rss", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Freie Presse (Chemnitz/Saxony)", "homepage_url": "https://www.freiepresse.de/", "feed_url": "https://www.freiepresse.de/rss/rss_chemnitz.php", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "come-on.de (Märkischer Kreis)", "homepage_url": "https://www.come-on.de/", "feed_url": "https://www.come-on.de/rssfeed.rdf", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "HNA (Hessen/Nordhessen)", "homepage_url": "https://www.hna.de/", "feed_url": "https://www.hna.de/rssfeed.rdf", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Frankfurter Neue Presse (FNP)", "homepage_url": "https://www.fnp.de/", "feed_url": "https://www.fnp.de/rssfeed.rdf", "api_kind": None, "fetch_method": "rss", "region": "DE", "languages": ["de"], "categories": ["general", "local"], "bot_sensitivity": 0},

    # ── France: regional / departmental dailies + France Bleu ────────────────
    {"name": "Nice-Matin", "homepage_url": "https://www.nicematin.com/", "feed_url": "https://www.nicematin.com/rss", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Var-Matin", "homepage_url": "https://www.varmatin.com/", "feed_url": "https://www.varmatin.com/rss", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "La Dépêche du Midi", "homepage_url": "https://www.ladepeche.fr/", "feed_url": "https://www.ladepeche.fr/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Le Progrès (Lyon/Rhône-Alpes)", "homepage_url": "https://www.leprogres.fr/", "feed_url": "https://www.leprogres.fr/rss", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "L'Alsace", "homepage_url": "https://www.lalsace.fr/", "feed_url": "https://www.lalsace.fr/rss", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Midi Libre", "homepage_url": "https://www.midilibre.fr/", "feed_url": "https://www.midilibre.fr/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "L'Indépendant (Perpignan/Aude)", "homepage_url": "https://www.lindependant.fr/", "feed_url": "https://www.lindependant.fr/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Centre Presse Aveyron", "homepage_url": "https://www.centrepresseaveyron.fr/", "feed_url": "https://www.centrepresseaveyron.fr/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "France Bleu (à la une)", "homepage_url": "https://www.francebleu.fr/", "feed_url": "https://www.francebleu.fr/rss/a-la-une.xml", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["general", "local", "world"], "bot_sensitivity": 0},
    {"name": "Lyon Capitale", "homepage_url": "https://www.lyoncapitale.fr/", "feed_url": "https://www.lyoncapitale.fr/feed/", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Rue89 Lyon", "homepage_url": "https://rue89lyon.fr/", "feed_url": "https://rue89lyon.fr/feed/", "api_kind": None, "fetch_method": "rss", "region": "FR", "languages": ["fr"], "categories": ["general", "local", "politics"], "bot_sensitivity": 0},

    # ── Italy: regional dailies, ANSA regional desks, *Today city network ─────
    {"name": "La Stampa (Turin)", "homepage_url": "https://www.lastampa.it/", "feed_url": "https://www.lastampa.it/rss", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Il Mattino (Naples)", "homepage_url": "https://www.ilmattino.it/", "feed_url": "https://www.ilmattino.it/rss/home.xml", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Il Gazzettino (Veneto)", "homepage_url": "https://www.ilgazzettino.it/", "feed_url": "https://www.ilgazzettino.it/rss/home.xml", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Il Secolo XIX (Genoa)", "homepage_url": "https://www.ilsecoloxix.it/", "feed_url": "https://www.ilsecoloxix.it/rss", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "La Nazione (Florence/Tuscany)", "homepage_url": "https://www.lanazione.it/", "feed_url": "https://www.lanazione.it/rss", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Il Resto del Carlino (Bologna/Emilia)", "homepage_url": "https://www.ilrestodelcarlino.it/", "feed_url": "https://www.ilrestodelcarlino.it/rss", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "ANSA — Sicilia", "homepage_url": "https://www.ansa.it/sicilia/", "feed_url": "https://www.ansa.it/sicilia/notizie/sicilia_rss.xml", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "ANSA — Lombardia", "homepage_url": "https://www.ansa.it/lombardia/", "feed_url": "https://www.ansa.it/lombardia/notizie/lombardia_rss.xml", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "ANSA — Lazio", "homepage_url": "https://www.ansa.it/lazio/", "feed_url": "https://www.ansa.it/lazio/notizie/lazio_rss.xml", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "ANSA — Piemonte", "homepage_url": "https://www.ansa.it/piemonte/", "feed_url": "https://www.ansa.it/piemonte/notizie/piemonte_rss.xml", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "ANSA — Campania", "homepage_url": "https://www.ansa.it/campania/", "feed_url": "https://www.ansa.it/campania/notizie/campania_rss.xml", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "ANSA — Veneto", "homepage_url": "https://www.ansa.it/veneto/", "feed_url": "https://www.ansa.it/veneto/notizie/veneto_rss.xml", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "RomaToday", "homepage_url": "https://www.romatoday.it/", "feed_url": "https://www.romatoday.it/rss", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "MilanoToday", "homepage_url": "https://www.milanotoday.it/", "feed_url": "https://www.milanotoday.it/rss", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "NapoliToday", "homepage_url": "https://www.napolitoday.it/", "feed_url": "https://www.napolitoday.it/rss", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "TorinoToday", "homepage_url": "https://www.torinotoday.it/", "feed_url": "https://www.torinotoday.it/rss", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "LeccePrima (Puglia)", "homepage_url": "https://www.lecceprima.it/", "feed_url": "https://www.lecceprima.it/rss", "api_kind": None, "fetch_method": "rss", "region": "IT", "languages": ["it"], "categories": ["general", "local"], "bot_sensitivity": 0},

    # ── Spain: regional press incl. Galician/Basque-country/Catalan ──────────
    {"name": "El Correo Gallego (Galicia)", "homepage_url": "https://www.elcorreogallego.es/", "feed_url": "https://www.elcorreogallego.es/rss", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["es"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "El Comercio (Asturias)", "homepage_url": "https://www.elcomercio.es/", "feed_url": "https://www.elcomercio.es/rss/2.0/portada", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["es"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Las Provincias (Valencia)", "homepage_url": "https://www.lasprovincias.es/", "feed_url": "https://www.lasprovincias.es/rss/2.0/portada", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["es"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "El Diario Vasco (Basque Country)", "homepage_url": "https://www.diariovasco.com/", "feed_url": "https://www.diariovasco.com/rss/2.0/portada", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["es"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "El Diario Montañés (Cantabria)", "homepage_url": "https://www.eldiariomontanes.es/", "feed_url": "https://www.eldiariomontanes.es/rss/2.0/portada", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["es"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Ideal (Granada/Andalucía)", "homepage_url": "https://www.ideal.es/", "feed_url": "https://www.ideal.es/rss/2.0/portada", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["es"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "La Rioja", "homepage_url": "https://www.larioja.com/", "feed_url": "https://www.larioja.com/rss/2.0/portada", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["es"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Ara (Catalan)", "homepage_url": "https://www.ara.cat/", "feed_url": "https://www.ara.cat/rss", "api_kind": None, "fetch_method": "rss", "region": "ES", "languages": ["ca"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},

    # ── Nordics: regional / native-language desks ────────────────────────────
    {"name": "NRK Nordland (Norway)", "homepage_url": "https://www.nrk.no/nordland/", "feed_url": "https://www.nrk.no/nordland/toppsaker.rss", "api_kind": None, "fetch_method": "rss", "region": "NO", "languages": ["no"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "NRK Vestland (Norway)", "homepage_url": "https://www.nrk.no/vestland/", "feed_url": "https://www.nrk.no/vestland/toppsaker.rss", "api_kind": None, "fetch_method": "rss", "region": "NO", "languages": ["no"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "NRK Rogaland (Norway)", "homepage_url": "https://www.nrk.no/rogaland/", "feed_url": "https://www.nrk.no/rogaland/toppsaker.rss", "api_kind": None, "fetch_method": "rss", "region": "NO", "languages": ["no"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "NRK Trøndelag (Norway)", "homepage_url": "https://www.nrk.no/trondelag/", "feed_url": "https://www.nrk.no/trondelag/toppsaker.rss", "api_kind": None, "fetch_method": "rss", "region": "NO", "languages": ["no"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "NRK Troms og Finnmark (Norway)", "homepage_url": "https://www.nrk.no/tromsogfinnmark/", "feed_url": "https://www.nrk.no/tromsogfinnmark/toppsaker.rss", "api_kind": None, "fetch_method": "rss", "region": "NO", "languages": ["no"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Aftenposten (Norway)", "homepage_url": "https://www.aftenposten.no/", "feed_url": "https://www.aftenposten.no/rss", "api_kind": None, "fetch_method": "rss", "region": "NO", "languages": ["no"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Bergens Tidende (Norway)", "homepage_url": "https://www.bt.no/", "feed_url": "https://www.bt.no/rss", "api_kind": None, "fetch_method": "rss", "region": "NO", "languages": ["no"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Sydsvenskan (Malmö, Sweden)", "homepage_url": "https://www.sydsvenskan.se/", "feed_url": "https://www.sydsvenskan.se/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "SE", "languages": ["sv"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Helsingborgs Dagblad (Sweden)", "homepage_url": "https://www.hd.se/", "feed_url": "https://www.hd.se/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "SE", "languages": ["sv"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Hufvudstadsbladet (HBL, Finland, Swedish)", "homepage_url": "https://www.hbl.fi/", "feed_url": "https://www.hbl.fi/rss", "api_kind": None, "fetch_method": "rss", "region": "FI", "languages": ["sv"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Yle (Finland, Swedish)", "homepage_url": "https://svenska.yle.fi/", "feed_url": "https://yle.fi/rss/t/18-34837/sv", "api_kind": None, "fetch_method": "rss", "region": "FI", "languages": ["sv"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "RÚV (Iceland)", "homepage_url": "https://www.ruv.is/", "feed_url": "https://www.ruv.is/rss/frettir", "api_kind": None, "fetch_method": "rss", "region": "IS", "languages": ["is"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "DV (Iceland)", "homepage_url": "https://www.dv.is/", "feed_url": "https://www.dv.is/feed/", "api_kind": None, "fetch_method": "rss", "region": "IS", "languages": ["is"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Heimildin (Iceland)", "homepage_url": "https://heimildin.is/", "feed_url": "https://heimildin.is/rss/", "api_kind": None, "fetch_method": "rss", "region": "IS", "languages": ["is"], "categories": ["general", "politics"], "bot_sensitivity": 0},

    # ── Baltics: native-language ─────────────────────────────────────────────
    {"name": "ERR (Estonia, Estonian)", "homepage_url": "https://www.err.ee/", "feed_url": "https://www.err.ee/rss", "api_kind": None, "fetch_method": "rss", "region": "EE", "languages": ["et"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Postimees (Estonia)", "homepage_url": "https://www.postimees.ee/", "feed_url": "https://www.postimees.ee/rss", "api_kind": None, "fetch_method": "rss", "region": "EE", "languages": ["et"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "LSM (Latvia, Latvian)", "homepage_url": "https://www.lsm.lv/", "feed_url": "https://www.lsm.lv/rss/", "api_kind": None, "fetch_method": "rss", "region": "LV", "languages": ["lv"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "TVNET (Latvia)", "homepage_url": "https://www.tvnet.lv/", "feed_url": "https://www.tvnet.lv/rss", "api_kind": None, "fetch_method": "rss", "region": "LV", "languages": ["lv"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Diena (Latvia)", "homepage_url": "https://www.diena.lv/", "feed_url": "https://www.diena.lv/rss", "api_kind": None, "fetch_method": "rss", "region": "LV", "languages": ["lv"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "15min (Lithuania)", "homepage_url": "https://www.15min.lt/", "feed_url": "https://www.15min.lt/rss", "api_kind": None, "fetch_method": "rss", "region": "LT", "languages": ["lt"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── Poland: regional / city press + aggregators ──────────────────────────
    {"name": "Onet Wiadomości (Poland)", "homepage_url": "https://wiadomosci.onet.pl/", "feed_url": "https://wiadomosci.onet.pl/.feed", "api_kind": None, "fetch_method": "rss", "region": "PL", "languages": ["pl"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Money.pl (Poland, finance)", "homepage_url": "https://www.money.pl/", "feed_url": "https://www.money.pl/rss/wszystkie", "api_kind": None, "fetch_method": "rss", "region": "PL", "languages": ["pl"], "categories": ["business", "economy", "markets", "finance"], "bot_sensitivity": 0},

    # ── Czechia & Slovakia: regional / native-language ───────────────────────
    {"name": "Novinky.cz (Czechia)", "homepage_url": "https://www.novinky.cz/", "feed_url": "https://www.novinky.cz/rss", "api_kind": None, "fetch_method": "rss", "region": "CZ", "languages": ["cs"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "iDNES.cz — Zpravodaj", "homepage_url": "https://www.idnes.cz/", "feed_url": "https://servis.idnes.cz/rss.aspx?c=zpravodaj", "api_kind": None, "fetch_method": "rss", "region": "CZ", "languages": ["cs"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Seznam Zprávy (Czechia)", "homepage_url": "https://www.seznamzpravy.cz/", "feed_url": "https://www.seznamzpravy.cz/rss", "api_kind": None, "fetch_method": "rss", "region": "CZ", "languages": ["cs"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "SME (Slovakia)", "homepage_url": "https://www.sme.sk/", "feed_url": "https://www.sme.sk/rss-title", "api_kind": None, "fetch_method": "rss", "region": "SK", "languages": ["sk"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},

    # ── Hungary: native-language ─────────────────────────────────────────────
    {"name": "Index.hu (Hungary)", "homepage_url": "https://index.hu/", "feed_url": "https://index.hu/24ora/rss/", "api_kind": None, "fetch_method": "rss", "region": "HU", "languages": ["hu"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "444.hu (Hungary)", "homepage_url": "https://444.hu/", "feed_url": "https://444.hu/feed", "api_kind": None, "fetch_method": "rss", "region": "HU", "languages": ["hu"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},

    # ── Romania: regional / native-language ──────────────────────────────────
    {"name": "HotNews.ro (Romania)", "homepage_url": "https://www.hotnews.ro/", "feed_url": "https://www.hotnews.ro/rss", "api_kind": None, "fetch_method": "rss", "region": "RO", "languages": ["ro"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "G4Media (Romania)", "homepage_url": "https://www.g4media.ro/", "feed_url": "https://www.g4media.ro/feed", "api_kind": None, "fetch_method": "rss", "region": "RO", "languages": ["ro"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Mediafax (Romania)", "homepage_url": "https://www.mediafax.ro/", "feed_url": "https://www.mediafax.ro/rss", "api_kind": None, "fetch_method": "rss", "region": "RO", "languages": ["ro"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Știrile ProTV (Romania)", "homepage_url": "https://stirileprotv.ro/", "feed_url": "https://stirileprotv.ro/rss", "api_kind": None, "fetch_method": "rss", "region": "RO", "languages": ["ro"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Libertatea (Romania)", "homepage_url": "https://www.libertatea.ro/", "feed_url": "https://www.libertatea.ro/rss", "api_kind": None, "fetch_method": "rss", "region": "RO", "languages": ["ro"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── Balkans: HR / SI / RS ────────────────────────────────────────────────
    {"name": "Index.hr (Croatia)", "homepage_url": "https://www.index.hr/", "feed_url": "https://www.index.hr/rss/vijesti", "api_kind": None, "fetch_method": "rss", "region": "HR", "languages": ["hr"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "24sata (Croatia)", "homepage_url": "https://www.24sata.hr/", "feed_url": "https://www.24sata.hr/feeds/aktualno.xml", "api_kind": None, "fetch_method": "rss", "region": "HR", "languages": ["hr"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Večernji list (Croatia)", "homepage_url": "https://www.vecernji.hr/", "feed_url": "https://www.vecernji.hr/feeds/latest", "api_kind": None, "fetch_method": "rss", "region": "HR", "languages": ["hr"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "tportal (Croatia)", "homepage_url": "https://www.tportal.hr/", "feed_url": "https://www.tportal.hr/rss", "api_kind": None, "fetch_method": "rss", "region": "HR", "languages": ["hr"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Slobodna Dalmacija (Split, Croatia)", "homepage_url": "https://www.slobodnadalmacija.hr/", "feed_url": "https://www.slobodnadalmacija.hr/feed", "api_kind": None, "fetch_method": "rss", "region": "HR", "languages": ["hr"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Delo (Slovenia)", "homepage_url": "https://www.delo.si/", "feed_url": "https://www.delo.si/rss/", "api_kind": None, "fetch_method": "rss", "region": "SI", "languages": ["sl"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "24ur (Slovenia)", "homepage_url": "https://www.24ur.com/", "feed_url": "https://www.24ur.com/rss", "api_kind": None, "fetch_method": "rss", "region": "SI", "languages": ["sl"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Danas (Serbia)", "homepage_url": "https://www.danas.rs/", "feed_url": "https://www.danas.rs/feed/", "api_kind": None, "fetch_method": "rss", "region": "RS", "languages": ["sr"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},

    # ── Greece ───────────────────────────────────────────────────────────────
    {"name": "Protothema (Greece)", "homepage_url": "https://www.protothema.gr/", "feed_url": "https://www.protothema.gr/rss/", "api_kind": None, "fetch_method": "rss", "region": "GR", "languages": ["el"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Keep Talking Greece (English)", "homepage_url": "https://www.keeptalkinggreece.com/", "feed_url": "https://www.keeptalkinggreece.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GR", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── Benelux: regional / native-language ──────────────────────────────────
    {"name": "de Volkskrant (Netherlands)", "homepage_url": "https://www.volkskrant.nl/", "feed_url": "https://www.volkskrant.nl/voorpagina/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "NL", "languages": ["nl"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Het Parool (Amsterdam)", "homepage_url": "https://www.parool.nl/", "feed_url": "https://www.parool.nl/voorpagina/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "NL", "languages": ["nl"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "NU.nl (Netherlands)", "homepage_url": "https://www.nu.nl/", "feed_url": "https://www.nu.nl/rss/Algemeen", "api_kind": None, "fetch_method": "rss", "region": "NL", "languages": ["nl"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "7sur7 (Belgium)", "homepage_url": "https://www.7sur7.be/", "feed_url": "https://www.7sur7.be/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "BE", "languages": ["fr"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── Switzerland: German- & French-speaking regional ──────────────────────
    {"name": "NZZ (Neue Zürcher Zeitung)", "homepage_url": "https://www.nzz.ch/", "feed_url": "https://www.nzz.ch/recent.rss", "api_kind": None, "fetch_method": "rss", "region": "CH", "languages": ["de"], "categories": ["general", "world", "politics"], "bot_sensitivity": 0},
    {"name": "Berner Zeitung (Switzerland)", "homepage_url": "https://www.bernerzeitung.ch/", "feed_url": "https://www.bernerzeitung.ch/rss.html", "api_kind": None, "fetch_method": "rss", "region": "CH", "languages": ["de"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "24 heures (Lausanne, Switzerland)", "homepage_url": "https://www.24heures.ch/", "feed_url": "https://www.24heures.ch/rss.html", "api_kind": None, "fetch_method": "rss", "region": "CH", "languages": ["fr"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Tribune de Genève (Switzerland)", "homepage_url": "https://www.tdg.ch/", "feed_url": "https://www.tdg.ch/rss.html", "api_kind": None, "fetch_method": "rss", "region": "CH", "languages": ["fr"], "categories": ["general", "local"], "bot_sensitivity": 0},

    # ── Austria: regional / native-language ──────────────────────────────────
    {"name": "Kleine Zeitung (Styria/Carinthia)", "homepage_url": "https://www.kleinezeitung.at/", "feed_url": "https://www.kleinezeitung.at/rss", "api_kind": None, "fetch_method": "rss", "region": "AT", "languages": ["de"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Vienna.at", "homepage_url": "https://www.vienna.at/", "feed_url": "https://www.vienna.at/rss/news", "api_kind": None, "fetch_method": "rss", "region": "AT", "languages": ["de"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "MeinBezirk.at (Austria, local)", "homepage_url": "https://www.meinbezirk.at/", "feed_url": "https://www.meinbezirk.at/rss", "api_kind": None, "fetch_method": "rss", "region": "AT", "languages": ["de"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "eXXpress (Austria)", "homepage_url": "https://exxpress.at/", "feed_url": "https://exxpress.at/feed/", "api_kind": None, "fetch_method": "rss", "region": "AT", "languages": ["de"], "categories": ["general", "politics"], "bot_sensitivity": 0},

    # ── Luxembourg & Malta ───────────────────────────────────────────────────
    {"name": "Virgule (Luxembourg, French)", "homepage_url": "https://www.virgule.lu/", "feed_url": "https://www.virgule.lu/rss", "api_kind": None, "fetch_method": "rss", "region": "LU", "languages": ["fr"], "categories": ["general", "local"], "bot_sensitivity": 0},
    {"name": "Lovin Malta", "homepage_url": "https://lovinmalta.com/", "feed_url": "https://lovinmalta.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "MT", "languages": ["en"], "categories": ["general", "local"], "bot_sensitivity": 0},
]
