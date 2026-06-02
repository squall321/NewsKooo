"""Latin America & Caribbean depth seed sources.

Native Spanish- and Portuguese-language outlets (plus a few English/French
Caribbean and pan-regional feeds) spanning BR/AR/CL/CO/PE/MX/UY/EC/BO/VE/PY/CR/
PA/DO and the wider Caribbean. Focus is general news, business/economy and
politics, deliberately reaching beyond the big internationals already in the
core catalog (Folha, O Globo, G1, Valor, Clarín, La Nación AR, Emol, El Tiempo,
El Comercio PE, Infobae, El Universal MX, Milenio).

Every ``rss`` entry below was fetched live with a desktop browser User-Agent and
confirmed to return a parseable feed (``<rss``/``<feed``/``<rdf`` + ``<item``/
``<entry``) with at least one real article. Outlets without a working public
feed are omitted rather than guessed.

Each entry is a plain dict matching ``newskoo.sources.schemas.SourceCreate``:
``name, homepage_url, feed_url, api_kind, fetch_method, region, languages,
categories, bot_sensitivity``.
"""

from __future__ import annotations

SOURCES: list[dict] = [
    # ── Brazil (pt) ──────────────────────────────────────────────────────────
    {"name": "Agência Brasil (EBC)", "homepage_url": "https://agenciabrasil.ebc.com.br/", "feed_url": "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["general", "politics", "world"], "bot_sensitivity": 0},
    {"name": "CartaCapital", "homepage_url": "https://www.cartacapital.com.br/", "feed_url": "https://www.cartacapital.com.br/feed/", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Poder360", "homepage_url": "https://www.poder360.com.br/", "feed_url": "https://www.poder360.com.br/feed/", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["politics", "general"], "bot_sensitivity": 0},
    {"name": "Nexo Jornal", "homepage_url": "https://www.nexojornal.com.br/", "feed_url": "https://www.nexojornal.com.br/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Gazeta do Povo", "homepage_url": "https://www.gazetadopovo.com.br/", "feed_url": "https://www.gazetadopovo.com.br/feed/rss/ultimas-noticias.xml", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Exame", "homepage_url": "https://exame.com/", "feed_url": "https://exame.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["business", "economy", "markets"], "bot_sensitivity": 0},
    {"name": "InfoMoney", "homepage_url": "https://www.infomoney.com.br/", "feed_url": "https://www.infomoney.com.br/feed/", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["economy", "markets", "business"], "bot_sensitivity": 0},
    {"name": "O Antagonista", "homepage_url": "https://oantagonista.com.br/", "feed_url": "https://oantagonista.com.br/feed/", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["politics", "general"], "bot_sensitivity": 0},
    {"name": "Canaltech", "homepage_url": "https://canaltech.com.br/", "feed_url": "https://canaltech.com.br/rss/", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["technology", "niche"], "bot_sensitivity": 0},
    {"name": "The Intercept Brasil", "homepage_url": "https://www.intercept.com.br/", "feed_url": "https://www.intercept.com.br/feed/", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["politics", "general"], "bot_sensitivity": 0},
    {"name": "CNN Brasil", "homepage_url": "https://www.cnnbrasil.com.br/", "feed_url": "https://www.cnnbrasil.com.br/feed/", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Veja", "homepage_url": "https://veja.abril.com.br/", "feed_url": "https://veja.abril.com.br/feed/", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "IstoÉ", "homepage_url": "https://istoe.com.br/", "feed_url": "https://istoe.com.br/feed/", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "JOTA (law & politics)", "homepage_url": "https://www.jota.info/", "feed_url": "https://www.jota.info/feed", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["politics", "business", "niche"], "bot_sensitivity": 0},
    {"name": "UOL Notícias", "homepage_url": "https://noticias.uol.com.br/", "feed_url": "https://rss.uol.com.br/feed/noticias.xml", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "((o))eco (environment)", "homepage_url": "https://oeco.org.br/", "feed_url": "https://oeco.org.br/feed/", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["environment", "science", "niche"], "bot_sensitivity": 0},
    {"name": "Jornal da USP", "homepage_url": "https://jornal.usp.br/", "feed_url": "https://jornal.usp.br/feed/", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["science", "research", "niche"], "bot_sensitivity": 0},
    {"name": "Pesquisa FAPESP", "homepage_url": "https://revistapesquisa.fapesp.br/", "feed_url": "https://revistapesquisa.fapesp.br/feed/", "api_kind": None, "fetch_method": "rss", "region": "BR", "languages": ["pt"], "categories": ["science", "research", "niche"], "bot_sensitivity": 0},

    # ── Argentina (es) ───────────────────────────────────────────────────────
    {"name": "El Cronista", "homepage_url": "https://www.cronista.com/", "feed_url": "https://www.cronista.com/files/rss/news.xml", "api_kind": None, "fetch_method": "rss", "region": "AR", "languages": ["es"], "categories": ["economy", "business", "markets"], "bot_sensitivity": 0},
    {"name": "elDiarioAR", "homepage_url": "https://www.eldiarioar.com/", "feed_url": "https://www.eldiarioar.com/rss/", "api_kind": None, "fetch_method": "rss", "region": "AR", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Chequeado (fact-check)", "homepage_url": "https://chequeado.com/", "feed_url": "https://chequeado.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "AR", "languages": ["es"], "categories": ["politics", "niche"], "bot_sensitivity": 0},
    {"name": "Cenital", "homepage_url": "https://www.cenital.com/", "feed_url": "https://www.cenital.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "AR", "languages": ["es"], "categories": ["politics", "economy", "general"], "bot_sensitivity": 0},
    {"name": "El Cohete a la Luna", "homepage_url": "https://www.elcohetealaluna.com/", "feed_url": "https://www.elcohetealaluna.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "AR", "languages": ["es"], "categories": ["politics", "general"], "bot_sensitivity": 0},
    {"name": "Agencia Paco Urondo", "homepage_url": "https://www.agenciapacourondo.com.ar/", "feed_url": "https://www.agenciapacourondo.com.ar/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "AR", "languages": ["es"], "categories": ["politics", "general"], "bot_sensitivity": 0},

    # ── Chile (es) ───────────────────────────────────────────────────────────
    {"name": "La Tercera", "homepage_url": "https://www.latercera.com/", "feed_url": "https://www.latercera.com/arc/outboundfeeds/rss/?outputType=xml", "api_kind": None, "fetch_method": "rss", "region": "CL", "languages": ["es"], "categories": ["general", "politics", "economy"], "bot_sensitivity": 0},
    {"name": "The Clinic", "homepage_url": "https://www.theclinic.cl/", "feed_url": "https://www.theclinic.cl/feed/", "api_kind": None, "fetch_method": "rss", "region": "CL", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Interferencia", "homepage_url": "https://interferencia.cl/", "feed_url": "https://interferencia.cl/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "CL", "languages": ["es"], "categories": ["politics", "general", "niche"], "bot_sensitivity": 0},
    {"name": "CIPER Chile (investigative)", "homepage_url": "https://www.ciperchile.cl/", "feed_url": "https://www.ciperchile.cl/feed/", "api_kind": None, "fetch_method": "rss", "region": "CL", "languages": ["es"], "categories": ["politics", "niche"], "bot_sensitivity": 0},

    # ── Colombia (es) ────────────────────────────────────────────────────────
    {"name": "Semana", "homepage_url": "https://www.semana.com/", "feed_url": "https://www.semana.com/arc/outboundfeeds/rss/?outputType=xml", "api_kind": None, "fetch_method": "rss", "region": "CO", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "La República (Colombia)", "homepage_url": "https://www.larepublica.co/", "feed_url": "https://www.larepublica.co/rss/", "api_kind": None, "fetch_method": "rss", "region": "CO", "languages": ["es"], "categories": ["economy", "business", "markets"], "bot_sensitivity": 0},
    {"name": "La República — Economía (Colombia)", "homepage_url": "https://www.larepublica.co/economia", "feed_url": "https://www.larepublica.co/rss/economia", "api_kind": None, "fetch_method": "rss", "region": "CO", "languages": ["es"], "categories": ["economy", "markets"], "bot_sensitivity": 0},
    {"name": "Razón Pública", "homepage_url": "https://razonpublica.com/", "feed_url": "https://razonpublica.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "CO", "languages": ["es"], "categories": ["politics", "niche"], "bot_sensitivity": 0},
    {"name": "Kienyke", "homepage_url": "https://www.kienyke.com/", "feed_url": "https://www.kienyke.com/feed", "api_kind": None, "fetch_method": "rss", "region": "CO", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "VerdadAbierta (conflict & memory)", "homepage_url": "https://verdadabierta.com/", "feed_url": "https://verdadabierta.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "CO", "languages": ["es"], "categories": ["politics", "niche"], "bot_sensitivity": 0},
    {"name": "La Silla Vacía", "homepage_url": "https://www.lasillavacia.com/", "feed_url": "https://lasillavacia.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "CO", "languages": ["es"], "categories": ["politics", "general"], "bot_sensitivity": 0},

    # ── Peru (es) ────────────────────────────────────────────────────────────
    {"name": "Gestión", "homepage_url": "https://gestion.pe/", "feed_url": "https://gestion.pe/arcio/rss/", "api_kind": None, "fetch_method": "rss", "region": "PE", "languages": ["es"], "categories": ["economy", "business", "markets"], "bot_sensitivity": 0},
    {"name": "RPP Noticias", "homepage_url": "https://rpp.pe/", "feed_url": "https://rpp.pe/feed", "api_kind": None, "fetch_method": "rss", "region": "PE", "languages": ["es"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Perú21", "homepage_url": "https://peru21.pe/", "feed_url": "https://peru21.pe/arcio/rss/", "api_kind": None, "fetch_method": "rss", "region": "PE", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Wayka (investigative)", "homepage_url": "https://wayka.pe/", "feed_url": "https://wayka.pe/feed/", "api_kind": None, "fetch_method": "rss", "region": "PE", "languages": ["es"], "categories": ["politics", "niche"], "bot_sensitivity": 0},
    {"name": "El Búho (Arequipa)", "homepage_url": "https://elbuho.pe/", "feed_url": "https://elbuho.pe/feed/", "api_kind": None, "fetch_method": "rss", "region": "PE", "languages": ["es"], "categories": ["general", "regional"], "bot_sensitivity": 0},

    # ── Mexico (es) ──────────────────────────────────────────────────────────
    {"name": "La Jornada", "homepage_url": "https://www.jornada.com.mx/", "feed_url": "https://www.jornada.com.mx/rss/edicion.xml", "api_kind": None, "fetch_method": "rss", "region": "MX", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "El Economista (Mexico)", "homepage_url": "https://www.eleconomista.com.mx/", "feed_url": "https://www.eleconomista.com.mx/rss/ultimas-noticias", "api_kind": None, "fetch_method": "rss", "region": "MX", "languages": ["es"], "categories": ["economy", "business", "markets"], "bot_sensitivity": 0},
    {"name": "El Financiero (Mexico)", "homepage_url": "https://www.elfinanciero.com.mx/", "feed_url": "https://www.elfinanciero.com.mx/arc/outboundfeeds/rss/?outputType=xml", "api_kind": None, "fetch_method": "rss", "region": "MX", "languages": ["es"], "categories": ["economy", "business", "markets"], "bot_sensitivity": 0},
    {"name": "Expansión (Mexico)", "homepage_url": "https://expansion.mx/", "feed_url": "https://expansion.mx/rss", "api_kind": None, "fetch_method": "rss", "region": "MX", "languages": ["es"], "categories": ["economy", "business"], "bot_sensitivity": 0},
    {"name": "El Sol de México", "homepage_url": "https://www.elsoldemexico.com.mx/", "feed_url": "https://www.elsoldemexico.com.mx/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "MX", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Excélsior", "homepage_url": "https://www.excelsior.com.mx/", "feed_url": "https://www.excelsior.com.mx/rss/", "api_kind": None, "fetch_method": "rss", "region": "MX", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Pie de Página (investigative)", "homepage_url": "https://piedepagina.mx/", "feed_url": "https://piedepagina.mx/feed/", "api_kind": None, "fetch_method": "rss", "region": "MX", "languages": ["es"], "categories": ["politics", "niche"], "bot_sensitivity": 0},

    # ── Uruguay (es) ─────────────────────────────────────────────────────────
    {"name": "la diaria", "homepage_url": "https://ladiaria.com.uy/", "feed_url": "https://ladiaria.com.uy/feeds/articulos/", "api_kind": None, "fetch_method": "rss", "region": "UY", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Montevideo Portal", "homepage_url": "https://www.montevideo.com.uy/", "feed_url": "https://www.montevideo.com.uy/anxml.aspx?59", "api_kind": None, "fetch_method": "rss", "region": "UY", "languages": ["es"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── Ecuador (es) ─────────────────────────────────────────────────────────
    {"name": "El Comercio (Ecuador)", "homepage_url": "https://www.elcomercio.com/", "feed_url": "https://www.elcomercio.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "EC", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "El Universo", "homepage_url": "https://www.eluniverso.com/", "feed_url": "https://www.eluniverso.com/arc/outboundfeeds/rss/?outputType=xml", "api_kind": None, "fetch_method": "rss", "region": "EC", "languages": ["es"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Expreso (Ecuador)", "homepage_url": "https://www.expreso.ec/", "feed_url": "https://www.expreso.ec/rss", "api_kind": None, "fetch_method": "rss", "region": "EC", "languages": ["es"], "categories": ["general", "economy"], "bot_sensitivity": 0},
    {"name": "GK", "homepage_url": "https://gk.city/", "feed_url": "https://gk.city/feed/", "api_kind": None, "fetch_method": "rss", "region": "EC", "languages": ["es"], "categories": ["general", "niche"], "bot_sensitivity": 0},

    # ── Bolivia (es) ─────────────────────────────────────────────────────────
    {"name": "Los Tiempos", "homepage_url": "https://www.lostiempos.com/", "feed_url": "https://www.lostiempos.com/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "BO", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Opinión (Bolivia)", "homepage_url": "https://www.opinion.com.bo/", "feed_url": "https://www.opinion.com.bo/rss/", "api_kind": None, "fetch_method": "rss", "region": "BO", "languages": ["es"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Erbol", "homepage_url": "https://www.erbol.com.bo/", "feed_url": "https://www.erbol.com.bo/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "BO", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},

    # ── Venezuela (es) ───────────────────────────────────────────────────────
    {"name": "El Nacional (Venezuela)", "homepage_url": "https://www.elnacional.com/", "feed_url": "https://www.elnacional.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "VE", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Efecto Cocuyo", "homepage_url": "https://efectococuyo.com/", "feed_url": "https://efectococuyo.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "VE", "languages": ["es"], "categories": ["politics", "general"], "bot_sensitivity": 0},
    {"name": "TalCual", "homepage_url": "https://talcualdigital.com/", "feed_url": "https://talcualdigital.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "VE", "languages": ["es"], "categories": ["politics", "general"], "bot_sensitivity": 0},
    {"name": "El Impulso", "homepage_url": "https://www.elimpulso.com/", "feed_url": "https://www.elimpulso.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "VE", "languages": ["es"], "categories": ["general", "regional"], "bot_sensitivity": 0},
    {"name": "Crónica.Uno", "homepage_url": "https://cronica.uno/", "feed_url": "https://cronica.uno/feed/", "api_kind": None, "fetch_method": "rss", "region": "VE", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Runrun.es", "homepage_url": "https://runrun.es/", "feed_url": "https://runrun.es/feed/", "api_kind": None, "fetch_method": "rss", "region": "VE", "languages": ["es"], "categories": ["politics", "general"], "bot_sensitivity": 0},

    # ── Paraguay (es) ────────────────────────────────────────────────────────
    {"name": "La Nación (Paraguay)", "homepage_url": "https://www.lanacion.com.py/", "feed_url": "https://www.lanacion.com.py/arc/outboundfeeds/rss/?outputType=xml", "api_kind": None, "fetch_method": "rss", "region": "PY", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "IP — Agencia de Información Paraguaya", "homepage_url": "https://www.ip.gov.py/", "feed_url": "https://www.ip.gov.py/ip/feed/", "api_kind": None, "fetch_method": "rss", "region": "PY", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},

    # ── Costa Rica (es) ──────────────────────────────────────────────────────
    {"name": "La Nación (Costa Rica)", "homepage_url": "https://www.nacion.com/", "feed_url": "https://www.nacion.com/arc/outboundfeeds/rss/?outputType=xml", "api_kind": None, "fetch_method": "rss", "region": "CR", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Delfino.cr", "homepage_url": "https://delfino.cr/", "feed_url": "https://delfino.cr/feed", "api_kind": None, "fetch_method": "rss", "region": "CR", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Semanario Universidad", "homepage_url": "https://semanariouniversidad.com/", "feed_url": "https://semanariouniversidad.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "CR", "languages": ["es"], "categories": ["politics", "niche"], "bot_sensitivity": 0},
    {"name": "El Mundo CR", "homepage_url": "https://www.elmundo.cr/", "feed_url": "https://www.elmundo.cr/feed/", "api_kind": None, "fetch_method": "rss", "region": "CR", "languages": ["es"], "categories": ["general", "economy"], "bot_sensitivity": 0},

    # ── Panama (es) ──────────────────────────────────────────────────────────
    {"name": "Panamá América", "homepage_url": "https://www.panamaamerica.com.pa/", "feed_url": "https://www.panamaamerica.com.pa/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "PA", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "TVN Noticias (Panama)", "homepage_url": "https://www.tvn-2.com/", "feed_url": "https://www.tvn-2.com/rss/", "api_kind": None, "fetch_method": "rss", "region": "PA", "languages": ["es"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── Dominican Republic (es) ──────────────────────────────────────────────
    {"name": "El Nuevo Diario (RD)", "homepage_url": "https://elnuevodiario.com.do/", "feed_url": "https://elnuevodiario.com.do/feed/", "api_kind": None, "fetch_method": "rss", "region": "DO", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Hoy Digital (RD)", "homepage_url": "https://hoy.com.do/", "feed_url": "https://hoy.com.do/rss/", "api_kind": None, "fetch_method": "rss", "region": "DO", "languages": ["es"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Dominican Today", "homepage_url": "https://www.dominicantoday.com/", "feed_url": "https://www.dominicantoday.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "DO", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 0},

    # ── Central America (es) ─────────────────────────────────────────────────
    {"name": "Prensa Libre (Guatemala)", "homepage_url": "https://www.prensalibre.com/", "feed_url": "https://www.prensalibre.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GT", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "La Hora (Guatemala)", "homepage_url": "https://lahora.gt/", "feed_url": "https://lahora.gt/feed/", "api_kind": None, "fetch_method": "rss", "region": "GT", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Criterio.hn (Honduras)", "homepage_url": "https://criterio.hn/", "feed_url": "https://criterio.hn/feed/", "api_kind": None, "fetch_method": "rss", "region": "HN", "languages": ["es"], "categories": ["politics", "niche"], "bot_sensitivity": 0},
    {"name": "ElSalvador.com", "homepage_url": "https://www.elsalvador.com/", "feed_url": "https://www.elsalvador.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "SV", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},

    # ── Cuba (es) ────────────────────────────────────────────────────────────
    {"name": "OnCuba News", "homepage_url": "https://oncubanews.com/", "feed_url": "https://oncubanews.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "CU", "languages": ["es"], "categories": ["general", "politics"], "bot_sensitivity": 0},

    # ── Caribbean (en) ───────────────────────────────────────────────────────
    {"name": "Jamaica Observer", "homepage_url": "https://www.jamaicaobserver.com/", "feed_url": "https://www.jamaicaobserver.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "JM", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Jamaica Gleaner", "homepage_url": "https://jamaica-gleaner.com/", "feed_url": "https://jamaica-gleaner.com/feed/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "JM", "languages": ["en"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Nation News (Barbados)", "homepage_url": "https://www.nationnews.com/", "feed_url": "https://www.nationnews.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "BB", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Barbados Today", "homepage_url": "https://www.barbadostoday.bb/", "feed_url": "https://www.barbadostoday.bb/feed/", "api_kind": None, "fetch_method": "rss", "region": "BB", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Trinidad & Tobago Newsday", "homepage_url": "https://newsday.co.tt/", "feed_url": "https://newsday.co.tt/feed/", "api_kind": None, "fetch_method": "rss", "region": "TT", "languages": ["en"], "categories": ["general", "world"], "bot_sensitivity": 0},
    {"name": "Kaieteur News (Guyana)", "homepage_url": "https://www.kaieteurnewsonline.com/", "feed_url": "https://www.kaieteurnewsonline.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GY", "languages": ["en"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "Searchlight (St Vincent)", "homepage_url": "https://www.searchlight.vc/", "feed_url": "https://www.searchlight.vc/feed/", "api_kind": None, "fetch_method": "rss", "region": "VC", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 0},
    {"name": "St Lucia Times", "homepage_url": "https://stluciatimes.com/", "feed_url": "https://stluciatimes.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "LC", "languages": ["en"], "categories": ["general", "regional"], "bot_sensitivity": 0},

    # ── Pan-regional / multilateral (es/en/pt) ───────────────────────────────
    {"name": "MercoPress (South Atlantic)", "homepage_url": "https://www.mercopress.com/", "feed_url": "https://www.mercopress.com/rss/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["world", "economy", "politics"], "bot_sensitivity": 0},
    {"name": "AméricaEconomía", "homepage_url": "https://www.americaeconomia.com/", "feed_url": "https://www.americaeconomia.com/rss.xml", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["es"], "categories": ["economy", "business", "markets"], "bot_sensitivity": 0},
    {"name": "Latin American Post", "homepage_url": "https://latinamericanpost.com/", "feed_url": "https://latinamericanpost.com/feed/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["world", "business", "general"], "bot_sensitivity": 0},
    {"name": "Diálogo Chino", "homepage_url": "https://dialogochino.net/", "feed_url": "https://dialogochino.net/en/feed/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["environment", "economy", "niche"], "bot_sensitivity": 0},
    {"name": "Buenos Aires Times", "homepage_url": "https://www.batimes.com.ar/", "feed_url": "https://www.batimes.com.ar/feed", "api_kind": None, "fetch_method": "rss", "region": "AR", "languages": ["en"], "categories": ["general", "politics"], "bot_sensitivity": 0},
    {"name": "IDB / IADB Blogs", "homepage_url": "https://blogs.iadb.org/", "feed_url": "https://blogs.iadb.org/feed/", "api_kind": None, "fetch_method": "rss", "region": "GLOBAL", "languages": ["en"], "categories": ["economy", "research", "niche"], "bot_sensitivity": 0},
]
