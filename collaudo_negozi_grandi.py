# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEI NEGOZI GRANDI (1 ott 2026, seguito di «Database is
locked»: le quattro decisioni di Andrea, girate col SERVER VERO).

`prove.py` gira i pezzi uno per uno. Qui gira il server intero —
`sincronizza_connettori`, `_un_connettore`, i due lettori veri, la
moderazione, `db()` — su un database usa-e-getta, con tre negozi di
cartone e il traffico vero della app nel frattempo:

  1. IL NEGOZIO GRANDE: mille prodotti Woo, trecento dei quali con cinque
     taglie (2.200 righe), letto per intero col tetto di serie (mille).
     MENTRE il giro gira, la app risponde: richieste HTTP vere (la home e
     una scrittura con BEGIN IMMEDIATE) e una «rotta» che scrive — tutte
     con due secondi di pazienza (in produzione quindici), e nessuna muore.
     L'AI guarda SOLO le righe che entrano: cento a giro nel rodaggio, poi
     trenta, piu' i testi cambiati di chi e' gia' in vetrina.
     E' QUI CHE SI E' VISTA LA FAME DI LUCCHETTO (1 ott 2026): con la
     pazienza a 0,2 s una scrittura della app moriva durante le cento
     nascite del rodaggio, transazioni brevi ma a raffica. La cura e' il
     respiro del giro (RESPIRO_MAX_S in importa_negozio), provato contato
     in `prove.py`; qui si stampano i tempi veri — l'attesa piu' lunga di
     una scrittura, la home piu' lenta, il ciclo principale fermo — e le
     soglie sono larghe apposta: un collaudo che cade secondo il disco
     della macchina e' un collaudo che la CI impara a ignorare.
  2. IL WOO LENTO: la lettura a tempo si ferma da sola e il giro e' BUONO
     — nessun errore contato, il collegamento resta attivo, il venditore
     legge «risponde piano» — le figlie di chi aspetta non si spengono,
     le sparizioni vere si fanno lo stesso, e la rotazione porta tutto in
     vetrina nei giri dopo. E IL CONTROLLO: senza la lettura a tempo lo
     stesso negozio scade e si conta come errore (il guasto che c'era).
  3. SHOPIFY A MILLE: quattro pagine, e fra l'una e l'altra la pausa
     vera, misurata sull'orologio delle chiamate.

I numeri si stampano: sono quelli del verbale.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, i negozi e l'AI sono di cartone, nessuna rete
(le richieste HTTP passano dal trasporto ASGI, in memoria).

USO:  python collaudo_negozi_grandi.py
"""

import asyncio
import json
import os
import re
import sqlite3
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
VENDITORE = 222
CAMBIO = 100_000.0           # 1000 sats = 1 €
COMPRATORE = {"X-Tg-Init-Data": "collaudo:111:Compratore"}
# la pazienza della app durante i giri: in produzione quindici secondi
# (DB_BUSY_TIMEOUT), qui due — cento volte un commit, e meno di quanto
# durava la fame di lucchetto senza il respiro su un disco lento
PAZIENZA_S = 2.0


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


# --- I NEGOZI DI CARTONE, uno per host --------------------------------
NEGOZI = {}                   # host -> {"catalogo", "variazioni", "ritardo"}
LETTURE = []                  # (host, url, istante)
VOCI_AI = []


def prodotto_woo(pid, nome, tipo="simple", descrizione=None):
    return {"id": pid, "name": nome,
            "description": f"<p>{descrizione or f'Descrizione {pid}'}</p>",
            "type": tipo, "status": "publish", "catalog_visibility": "visible",
            "price": "7.50", "regular_price": "7.50", "manage_stock": True,
            "stock_quantity": 12, "stock_status": "instock", "images": [],
            "categories": [{"id": 1, "name": "Casa"}]}


def variazione_woo(vid, opzione):
    return {"id": vid, "price": "7.50", "regular_price": "7.50",
            "status": "publish", "manage_stock": True, "stock_quantity": 3,
            "stock_status": "instock", "virtual": False, "downloadable": False,
            "attributes": [{"id": 0, "name": "Taglia", "option": opzione}],
            "image": None}


def prodotto_shopify(pid):
    return {"id": pid, "title": f"Tazza {pid}", "body_html": "<p>Buona</p>",
            "status": "active", "product_type": "Casa", "images": [],
            "variants": [{"id": pid * 10, "price": "9.00",
                          "inventory_quantity": 4,
                          "inventory_management": "shopify"}]}


def api_finta(metodo, url, intestazioni):
    host = re.match(r"https://([^/]+)", url).group(1)
    negozio = NEGOZI[host]
    LETTURE.append((host, url, time.monotonic()))
    if negozio.get("ritardo"):
        time.sleep(negozio["ritardo"])
    if host.endswith(".myshopify.com"):
        m = re.search(r"page_info=(\d+)", url)
        pagina = int(m.group(1)) if m else 0
        fetta = negozio["catalogo"][pagina * 250:(pagina + 1) * 250]
        testa = {}
        if (pagina + 1) * 250 < len(negozio["catalogo"]):
            testa = {"Link": f"<https://{host}/admin/api/2024-07/products.json"
                             f"?limit=250&page_info={pagina + 1}>; rel=\"next\""}
        return 200, {"products": fetta}, testa
    if url.endswith("/settings/general"):
        return 200, {"lista": [{"id": "woocommerce_calc_taxes", "value": "yes"}]}, {}
    if url.endswith("/settings/tax"):
        return 200, {"lista": [{"id": "woocommerce_prices_include_tax",
                                "value": "yes"}]}, {}
    m = re.search(r"/products/(\d+)/variations.*?[?&]page=(\d+)", url)
    if m:
        lista = negozio["variazioni"].get(int(m.group(1)), [])
        return 200, {"lista": lista if int(m.group(2)) == 1 else []}, {}
    per_pagina = int(re.search(r"per_page=(\d+)", url).group(1))
    pagina = int(re.search(r"[?&]page=(\d+)", url).group(1))   # non il per_page
    fetta = negozio["catalogo"][(pagina - 1) * per_pagina: pagina * per_pagina]
    return 200, {"lista": fetta}, {"X-WP-Total": str(len(negozio["catalogo"]))}


def avvio():
    """Il config finto PRIMA di importare server."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-grandi-"), "usa-e-getta.db")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [999]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    cfg.CONNETTORI_NEGOZIO_APERTI = True
    sys.modules["config"] = cfg
    if "anthropic" not in sys.modules:
        finto = types.ModuleType("anthropic")
        finto.Anthropic = lambda **k: types.SimpleNamespace(messages=None)
        sys.modules["anthropic"] = finto
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server
    server.init_db()
    server.chiama_api_negozio = api_finta
    server._salva_foto_connettore = lambda annuncio_id, indice, url: None
    server.cambio_per_import = lambda: {"EUR": CAMBIO, "USD": CAMBIO}

    async def lotto_finto(voci):
        VOCI_AI.extend(t for _, t, _ in voci)
        return {}
    server.moderazione_ai_lotto = lotto_finto

    async def niente(*a, **k):
        return None
    server.notifica_admin = niente
    server.notifica = niente
    server.polso_ordini_admin = niente
    server.annuncio_su_nostr = niente
    server.promo_venduto = niente
    return db


def collega(host, fonte="woo"):
    """Un collegamento pronto (costi detti), che parte in pausa: lo si
    accende quando tocca a lui, cosi' ogni giro legge un negozio solo."""
    url = host if fonte == "shopify" else f"https://{host}"
    cred = ({"token": "shpat_finto"} if fonte == "shopify" else
            {"consumer_key": "ck_finta", "consumer_secret": "cs_finta"})
    con = SRV.db()
    cur = con.execute(
        "INSERT INTO connettori(tg_id,fonte,url_negozio,credenziali,"
        "consegna,spedizione_eur,zona,stato,creato) VALUES(?,?,?,?,?,?,?,?,?)",
        (VENDITORE, fonte, url, SRV._cifra_contenuto(json.dumps(cred)),
         "spedizione", 5.0, "Carmagnola (TO)", "pausa", int(time.time())))
    con.commit()
    cid = cur.lastrowid
    con.close()
    return cid


def solo(cid):
    con = SRV.db()
    con.execute("UPDATE connettori SET stato=CASE WHEN id=? THEN 'attivo' "
                "ELSE 'pausa' END", (cid,))
    con.commit()
    con.close()


def connettore(cid):
    con = SRV.db()
    r = dict(con.execute("SELECT * FROM connettori WHERE id=?", (cid,)).fetchone())
    con.close()
    r["esito"] = json.loads(r["ultimo_esito"] or "{}")
    return r


def annunci(cid):
    con = SRV.db()
    righe = [dict(r) for r in con.execute(
        "SELECT * FROM annunci WHERE connettore_id=? ORDER BY id", (cid,))]
    con.close()
    return righe


def invecchia(cid, ore):
    """Il primo annuncio nato `ore` ore fa: il rodaggio si conta da li'."""
    con = SRV.db()
    con.execute("UPDATE annunci SET creato=creato-? WHERE connettore_id=?",
                (int(ore * 3600), cid))
    con.commit()
    con.close()


def scrivi_come_una_rotta():
    """Quel che fa `timbro_scrivi` nel ciclo principale: db(), una
    scrittura, commit. Torna 'ok' o 'locked'."""
    try:
        con = SRV.db()
        con.execute("INSERT OR REPLACE INTO timbri(nome, valore, quando) "
                    "VALUES('p2p_libro_visto', '1', ?)", (int(time.time()),))
        con.commit()
        con.close()
        return "ok"
    except sqlite3.OperationalError as e:
        return "locked" if "locked" in str(e) else str(e)


async def giro(cid, traffico=False):
    """Un giro dell'orologio sul solo collegamento `cid`; col traffico, la
    app riceve richieste vere per tutta la sua durata. Torna (secondi,
    conto del traffico)."""
    solo(cid)
    SRV._prossimo_giro_connettori = 0.0
    conto = {"home": [], "scrive": [], "stati": [], "ok": 0, "locked": 0,
             "altro": [], "fermo": [0.0]}
    if not traffico:
        inizio = time.monotonic()
        await SRV.sincronizza_connettori()
        return time.monotonic() - inizio, conto
    import httpx
    finito = asyncio.Event()
    trasporto = httpx.ASGITransport(app=SRV.app)
    async with httpx.AsyncClient(transport=trasporto,
                                 base_url="http://collaudo.local") as cl:
        async def la_app():
            while not finito.is_set():
                t0 = time.perf_counter()
                r = await cl.get("/api/listings")
                conto["home"].append(time.perf_counter() - t0)
                conto["stati"].append(r.status_code)
                t0 = time.perf_counter()
                r = await cl.post("/api/me/visti", json={"visti": {"giro": 1}},
                                  headers=COMPRATORE)
                conto["scrive"].append(time.perf_counter() - t0)
                conto["stati"].append(r.status_code)
                e = scrivi_come_una_rotta()
                if e in ("ok", "locked"):
                    conto[e] += 1
                else:
                    conto["altro"].append(e)
                await asyncio.sleep(0.005)
        # IL BATTITO: un compito che chiede al ciclo principale di
        # svegliarlo ogni 10 ms e misura quanto ritardo ha avuto — e'
        # il tempo per cui il server intero NON poteva rispondere a
        # nessuno (le parti del giro che girano fuori dai thread)
        async def battito():
            while not finito.is_set():
                t0 = time.perf_counter()
                await asyncio.sleep(0.01)
                conto["fermo"].append(time.perf_counter() - t0 - 0.01)
        compito = asyncio.create_task(la_app())
        cuore = asyncio.create_task(battito())
        await asyncio.sleep(0.05)            # la app sta gia' rispondendo
        inizio = time.monotonic()
        await SRV.sincronizza_connettori()
        durata = time.monotonic() - inizio
        finito.set()
        await compito
        await cuore
    return durata, conto


def chiamate(host, pezzo=""):
    return [u for h, u, _ in LETTURE if h == host and pezzo in u]


def main():
    avvio()
    print("=" * 66)
    print("  I NEGOZI GRANDI: mille prodotti, il Woo lento, Shopify a mille")
    print("=" * 66)

    # --- 1) il negozio grande, col traffico ---------------------------------
    print("\n[1. mille prodotti, 2.200 righe: si giudica solo cio' che entra]")
    prova("il tetto di lettura di serie e' mille prodotti", 1000,
          SRV.MAX_PRODOTTI_CONNETTORE)
    prova("...il rodaggio di serie: cento a giro per ventiquattro ore", (100, 24, 30),
          (SRV.MAX_NUOVI_CONNETTORE_RODAGGIO, SRV.ORE_RODAGGIO_CONNETTORE,
           SRV.MAX_NUOVI_CONNETTORE_GIRO))
    catalogo, variazioni = [], {}
    for k in range(1, 1001):
        if k % 10 < 3:          # trecento variabili con cinque taglie
            catalogo.append(prodotto_woo(k, f"Maglia {k}", tipo="variable"))
            variazioni[k] = [variazione_woo(k * 10 + j, t)
                             for j, t in enumerate(("XS", "S", "M", "L", "XL"))]
        else:
            catalogo.append(prodotto_woo(k, f"Cosa {k}"))
    NEGOZI["grande.esempio"] = {"catalogo": catalogo, "variazioni": variazioni}
    grande = collega("grande.esempio")
    pazienza_vera = SRV.DB_BUSY_TIMEOUT
    SRV.DB_BUSY_TIMEOUT = PAZIENZA_S     # la app: due secondi, non quindici
    try:
        LETTURE.clear()
        VOCI_AI.clear()
        secondi, conto = asyncio.run(giro(grande, traffico=True))
    finally:
        SRV.DB_BUSY_TIMEOUT = pazienza_vera
    c = connettore(grande)
    e = c["esito"]
    print(f"    giro 1: {secondi:.1f} s, {len(chiamate('grande.esempio'))} chiamate "
          f"al negozio, {len(VOCI_AI)} righe all'AI, {e.get('nuovi')} nuovi, "
          f"{e.get('rimandati')} rimandati; la app: {len(conto['home'])} home "
          f"(la piu' lenta {max(conto['home'] or [0]):.2f} s), "
          f"{len(conto['scrive'])} scritture HTTP (la piu' lenta "
          f"{max(conto['scrive'] or [0]):.2f} s), {conto['ok']} scritture dirette; "
          f"il ciclo principale fermo al piu' {max(conto['fermo']):.2f} s di fila")
    prova("il catalogo si legge INTERO: dieci pagine, trecento variazioni, due impostazioni",
          (312, False), (len(chiamate("grande.esempio")), e.get("parziale")))
    prova("...nel rodaggio nascono cento righe, le altre 2.100 aspettano",
          (100, 2100), (e.get("nuovi"), e.get("rimandati")))
    prova("...e l'AI ha guardato SOLO quelle cento (ieri: tutte le 2.140 mai viste)",
          100, len(VOCI_AI))
    prova("...nessuna riga «non giudicata» fra i saltati: le altre sono in arrivo", 0,
          len([s for s in e.get("saltati", []) if "moderazione" in s.get("perche", "")]))
    prova("la app ha risposto durante il giro, sempre 200", (True, []),
          (len(conto["home"]) >= 1 and len(conto["scrive"]) >= 1,
           sorted({s for s in conto["stati"] if s != 200})))
    prova("...e chi scrive con due secondi di pazienza non e' mai morto", (0, []),
          (conto["locked"], conto["altro"]))
    # la soglia e' larga apposta (vedi la testa del file): il numero vero e'
    # quello stampato qui sopra, e va nel verbale
    prova("...e nessuna home e' rimasta appesa per secondi", True,
          max(conto["home"] or [0]) < 5.0)
    prova("il collegamento resta sano", ("attivo", 0, ""),
          (c["stato"], c["errori_di_fila"], c["ultimo_errore"]))

    VOCI_AI.clear()
    asyncio.run(giro(grande))
    e = connettore(grande)["esito"]
    prova("secondo giro nel rodaggio: altre cento, e l'AI ne guarda cento", (100, 100),
          (e.get("nuovi"), len(VOCI_AI)))

    invecchia(grande, 25)
    VOCI_AI.clear()
    SRV.DB_BUSY_TIMEOUT = PAZIENZA_S
    try:
        secondi, conto = asyncio.run(giro(grande, traffico=True))
    finally:
        SRV.DB_BUSY_TIMEOUT = pazienza_vera
    e = connettore(grande)["esito"]
    print(f"    giro 3 (fuori dal rodaggio): {secondi:.1f} s, {len(VOCI_AI)} righe "
          f"all'AI, {e.get('nuovi')} nuovi, {e.get('aggiornati')} aggiornati, "
          f"{e.get('rimandati')} rimandati; home piu' lenta "
          f"{max(conto['home'] or [0]):.2f} s, ciclo fermo al piu' "
          f"{max(conto['fermo']):.2f} s")
    prova("passate le ventiquattro ore dal primo annuncio: il regime, trenta",
          (30, 30, 2200 - 230), (e.get("nuovi"), len(VOCI_AI), e.get("rimandati")))
    prova("...anche col traffico, nessuna rotta morta", (0, [], []),
          (conto["locked"], conto["altro"],
           sorted({s for s in conto["stati"] if s != 200})))

    for k in range(1, 11):          # dieci testi cambiati sul negozio
        if catalogo[k - 1]["type"] == "simple":
            catalogo[k - 1] = prodotto_woo(k, f"Cosa {k}", descrizione="Nuova versione")
    cambiati = len([p for p in catalogo[:10] if "Nuova" in p["description"]])
    VOCI_AI.clear()
    asyncio.run(giro(grande))
    e = connettore(grande)["esito"]
    prova("i testi cambiati di chi e' gia' in vetrina si guardano, oltre ai trenta posti",
          (cambiati + 30, 30), (len(VOCI_AI), e.get("nuovi")))
    vivi = [a for a in annunci(grande) if a["stato"] == "attivo"]
    print(f"    dopo quattro giri: {len(vivi)} annunci in vetrina su 2.200 righe")

    # --- 2) il Woo lento -------------------------------------------------------
    print("\n[2. il Woo lento: la lettura a tempo si ferma da sola]")
    catalogo_l, variazioni_l = [], {}
    for k in range(1, 201):
        if k % 2 == 0:              # cento variabili con due taglie
            catalogo_l.append(prodotto_woo(k, f"Felpa {k}", tipo="variable"))
            variazioni_l[k] = [variazione_woo(k * 10 + j, t)
                               for j, t in enumerate(("S", "M"))]
        else:
            catalogo_l.append(prodotto_woo(k, f"Tazza {k}"))
    NEGOZI["lento.esempio"] = {"catalogo": catalogo_l, "variazioni": variazioni_l,
                               "ritardo": 0.01}
    lento = collega("lento.esempio")
    leve = (SRV.CONNETTORI_VARIANTI_MAX_S, SRV.CONNETTORI_LETTURA_MAX_S,
            SRV.MAX_NUOVI_CONNETTORE_GIRO)
    # il tempo in piccolo (i dieci minuti diventano secondi), e nessun tetto
    # all'ingresso: qui si guarda la LETTURA, non il rodaggio
    SRV.CONNETTORI_VARIANTI_MAX_S = 0.5
    SRV.CONNETTORI_LETTURA_MAX_S = 10
    SRV.MAX_NUOVI_CONNETTORE_GIRO = 0
    try:
        LETTURE.clear()
        secondi, _ = asyncio.run(giro(lento))
        c = connettore(lento)
        e = c["esito"]
        lette1 = [int(re.search(r"/products/(\d+)/variations", u).group(1))
                  for u in chiamate("lento.esempio", "/variations")]
        print(f"    giro L1: {secondi:.2f} s, variazioni lette per {len(lette1)} "
              f"prodotti su 100, {e.get('varianti_al_prossimo')} al prossimo giro, "
              f"segno {e.get('varianti_dopo')}")
        prova("il giro lento NON e' un errore: niente contato, il collegamento resta attivo",
              ("attivo", 0, ""), (c["stato"], c["errori_di_fila"], c["ultimo_errore"]))
        # la prova vera e' il conto (non tutte e cento: si e' fermato da
        # solo); il tempo e' solo la cintura contro un giro appeso
        prova("...si e' fermato a meta' delle variazioni, da solo", True,
              0 < len(lette1) < 100 and secondi < 30)
        prova("...il report conta chi aspetta e ricorda dove ci si e' fermati",
              (100 - len(lette1), max(lette1 or [0])),
              (e.get("varianti_al_prossimo"), e.get("varianti_dopo")))
        prova("...e il venditore legge «risponde piano», non un errore", True,
              any("risponde piano" in s.get("perche", "") for s in e.get("saltati", [])))
        prova("...il catalogo resta completo: le sparizioni non sono sospese", False,
              e.get("parziale"))
        figlie1 = {a["origine_chiave"] for a in annunci(lento)
                   if ":" in a["origine_chiave"]}
        prova("...le figlie dei prodotti letti sono entrate", 2 * len(lette1), len(figlie1))

        # secondo giro: si riparte DOPO il segno, e una tazza sparisce dal negozio
        tolta = catalogo_l.pop(0)                       # la «Tazza 1»
        LETTURE.clear()
        asyncio.run(giro(lento))
        e2 = connettore(lento)["esito"]
        lette2 = [int(re.search(r"/products/(\d+)/variations", u).group(1))
                  for u in chiamate("lento.esempio", "/variations")]
        prova("il giro dopo riparte DA DOVE si era fermato", True,
              bool(lette2) and lette2[0] > max(lette1))
        stati = {a["origine_chiave"]: a["stato"] for a in annunci(lento)}
        prova("...le figlie di chi questo giro non ha letto NON si spengono", [],
              sorted(k for k in figlie1 if stati.get(k) != "attivo"
                     and int(k.split(":")[0]) not in lette2))
        prova("...mentre il prodotto tolto dal negozio si spegne: le sparizioni sono vere",
              "rimosso", stati.get(str(tolta["id"])))
        prova("...e anche questo giro e' buono", (0, "attivo"),
              (connettore(lento)["errori_di_fila"], connettore(lento)["stato"]))
        # qualche giro ancora, finche' serve (al piu' dieci): la rotazione
        # porta in vetrina tutte le figlie — quanti giri dipende dal disco
        # della macchina, che quante figlie entrano no
        giri = 2
        while giri < 10:
            figlie = [a for a in annunci(lento)
                      if ":" in a["origine_chiave"] and a["stato"] == "attivo"]
            if len(figlie) >= 200:
                break
            asyncio.run(giro(lento))
            giri += 1
        figlie = [a for a in annunci(lento)
                  if ":" in a["origine_chiave"] and a["stato"] == "attivo"]
        print(f"    tutte le figlie in vetrina dopo {giri} giri")
        prova("dopo qualche giro la rotazione ha portato in vetrina TUTTE le figlie",
              200, len(figlie))
        prova("...e il collegamento non si e' mai dichiarato rotto", (0, "attivo"),
              (connettore(lento)["errori_di_fila"], connettore(lento)["stato"]))

        # IL CONTROLLO: senza la lettura a tempo lo stesso negozio SCADE
        print("\n[2-bis. il controllo: senza la lettura a tempo]")
        SRV.CONNETTORI_VARIANTI_MAX_S = 3600
        SRV.CONNETTORI_LETTURA_MAX_S = 0.5
        asyncio.run(giro(lento))
        c = connettore(lento)
        prova("senza la lettura a tempo il Woo lento scade, e si conta come errore",
              (1, True), (c["errori_di_fila"], "superato" in c["ultimo_errore"]))
        prova("...cioe' il guasto di ieri: a cinque di fila il collegamento si dichiarerebbe rotto",
              5, SRV.CONNETTORI_ERRORI_MAX)
    finally:
        (SRV.CONNETTORI_VARIANTI_MAX_S, SRV.CONNETTORI_LETTURA_MAX_S,
         SRV.MAX_NUOVI_CONNETTORE_GIRO) = leve

    # --- 3) Shopify a mille, con la pausa vera -------------------------------
    print("\n[3. Shopify a mille prodotti: la pausa vera fra le pagine]")
    NEGOZI["mio.myshopify.com"] = {"catalogo": [prodotto_shopify(k)
                                                for k in range(1, 1001)]}
    shop = collega("mio.myshopify.com", fonte="shopify")
    LETTURE.clear()
    VOCI_AI.clear()
    asyncio.run(giro(shop))
    e = connettore(shop)["esito"]
    istanti = [t for h, _, t in LETTURE if h == "mio.myshopify.com"]
    pause = [round(b - a, 2) for a, b in zip(istanti, istanti[1:])]
    print(f"    Shopify: {len(istanti)} pagine, pause fra le chiamate {pause} s, "
          f"{e.get('nuovi')} nuovi, {len(VOCI_AI)} righe all'AI")
    prova("mille prodotti in quattro pagine, lette tutte", (4, False),
          (len(istanti), e.get("parziale")))
    import importa_negozio
    prova("...e fra una pagina e l'altra la pausa vera, misurata sull'orologio", True,
          len(pause) == 3 and all(p >= importa_negozio.PAUSA_PAGINE_SHOPIFY * 0.9
                                  for p in pause))
    prova("...e anche qui l'AI guarda solo il rodaggio: cento", (100, 100),
          (e.get("nuovi"), len(VOCI_AI)))

    print("\n" + "=" * 66)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 66)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
