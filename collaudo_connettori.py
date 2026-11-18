# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEI CONNETTORI: il giro vero su un negozio di cartone.

`prove.py` difende la FORMA — che il giudice sia uno, che le guardie
non si allentino, che una colonna nasca additiva. Quello che non puo'
fare e' far GIRARE il sync: le sue prove non hanno un database, non
hanno un catalogo e non scrivono un annuncio.

Questo script chiude quel buco. Fa partire il SERVER VERO su un
database usa-e-getta, con due negozi finti al posto dell'API — uno
Shopify e uno WooCommerce — e chiede le cose che solo l'esecuzione
puo' dire.

LA PROVA REGINA DELLA FASE 1 e' una sola: **una vendita fatta qui non
viene rialzata dal giro dopo**. Il sync ricopre la giacenza dalla
lettura esterna, quindi senza il registro delle uscite ogni acquisto
su Barattolo verrebbe annullato entro l'ora — e sul pezzo unico il
'venduto' risorgerebbe, rimettendo in vendita una cosa gia' venduta.
Non fallisce da solo: nessuna eccezione, nessun log, solo un numero
che torna su.

Le altre domande che si fanno insieme a quella:
  · un catalogo che non si e' potuto LEGGERE non e' un catalogo
    vuoto — un errore di rete non deve spegnere la vetrina;
  · un prodotto tolto dal negozio sparisce anche qui, e i suoi ordini
    mai pagati si annullano;
  · uno gia' rimosso QUI non risorge, mentre un esaurito che viene
    rifornito sul negozio torna in vetrina (la differenza dichiarata
    con Nostr);
  · la moderazione si paga UNA volta: al secondo giro, a testo
    invariato, all'AI non si chiede niente;
  · quel che il negozio non dichiara non si inventa (lo stock non
    tracciato) e quel che non sappiamo trattare si salta DICENDOLO
    (gruppi e affiliazioni; i multi-variante dal set 2026 ENTRANO,
    una riga per variante — vedi la sezione 16);
  · (set 2026) il libro in due formati diventa due annunci, il PDF e
    il corso online nascono DIGITALI senza spedizione ne' ritiro, il
    corso importato ieri come pacco si corregge al giro dopo, e la
    vendita di un PDF senza magazzino non scrive il registro e torna
    in vetrina al giro dopo;
  · a SCRIVERE il registro c'e' `_incassa_ordine` (tappa 4), e un
    annuncio nato qui non ci entra;
  · un reso lo rimette in pari — se il negozio non aveva ancora
    scalato la vendita le due si cancellano in silenzio, se l'aveva
    gia' fatto i pezzi vanno rimessi e glielo si dice.

E dalla tappa 5 anche gli ENDPOINT del cassetto, chiamati per davvero:
  · un token che il negozio rifiuta non lascia in piedi una riga —
    «si prova prima di crederci», e la prova e' che il collegamento
    NON viene scritto;
  · le credenziali non escono mai dal server: si guarda il JSON vero
    che il client riceverebbe, non la forma della funzione;
  · la consegna dichiarata nel cassetto scende anche sulle righe gia'
    entrate — la Modifica sugli annunci di un connettore e' chiusa
    apposta, quindi senza quella riga un errore sarebbe per sempre;
  · in pausa il catalogo non si rilegge e gli annunci restano;
  · un estraneo non vede e non tocca, e «non e' tuo» si racconta come
    «non esiste»;
  · scollegare spegne gli annunci e non lascia il registro orfano.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. L'API del
negozio non viene mai chiamata — c'e' un catalogo in memoria — quindi
lo script gira senza rete e senza chiavi.

COSA NON PUO' DIRE, ed e' dichiarato: come si comporta l'API vera (il
rate limit di Shopify, il suo header `Link` contro un negozio in
carne e ossa, i permessi veri di un token, i certificati di un Woo
self-hosted) e la moderazione vera. Per quelle serve il rodaggio con
uno store di sviluppo, prima di accendere la leva.

USO:  python collaudo_connettori.py
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
CHIAMATE_AI = []        # quante volte la moderazione e' stata chiamata
NOTIFICHE = []          # (tg_id, testo)

CAMBIO = 100_000.0      # 1 BTC = 100.000 €, cioe' 1000 sats = 1 €
VENDITORE = 222
COMPRATORE = 111


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


# --- IL NEGOZIO DI CARTONE -------------------------------------------
# Un catalogo in memoria che si comporta come l'API di Shopify: stessa
# forma della risposta, stesso header di paginazione. Si cambia da
# fuori (CATALOGO[:] = [...]) per raccontare cosa succede sul negozio
# fra un giro e l'altro.
CATALOGO = []
ERRORE_API = [None]     # se pieno, l'API alza: la rete che cade
LETTURE = []            # gli URL chiesti, per contare le pagine

# --- IL WOOCOMMERCE DI CARTONE ---------------------------------------
# Un secondo negozio, con l'altro dialetto e con la cosa che Shopify
# non ha: le due impostazioni da cui dipende il significato di
# `price`. `IVA_WOO` a 'no' vuol dire «prezzi scritti al NETTO», cioe'
# il caso in cui il catalogo NON si deve leggere.
CATALOGO_WOO = []
TASSE_WOO = ["yes"]     # woocommerce_calc_taxes
# Risposte di Woo per PREFISSO d'indirizzo (set 2026): la pagina 404 di
# un tema, un firewall, un WordPress senza WooCommerce — quel che il
# modulo deve saper spiegare, e la radice che risponde al posto della
# pagina del negozio. {prefisso: (stato, corpo, intestazioni)}.
RISPOSTE_WOO = {}
IVA_WOO = ["yes"]       # woocommerce_prices_include_tax
# le variazioni dei prodotti `variable`, per id del padre (set 2026):
# su Woo vivono a un indirizzo loro, e il lettore le chiede a parte
VARIAZIONI_WOO = {}


def variazione_woo(vid, prezzo, opzione, stock=None, gestito=False,
                   disponibile="instock", virtuale=False,
                   scaricabile=False, stato="publish", foto=""):
    return {"id": vid, "price": prezzo, "regular_price": prezzo,
            "status": stato, "manage_stock": gestito,
            "stock_quantity": stock if gestito else None,
            "stock_status": disponibile, "virtual": virtuale,
            "downloadable": scaricabile,
            "attributes": [{"id": 0, "name": "Formato", "option": opzione}],
            "image": {"src": foto} if foto else None}


def prodotto(pid, titolo, prezzo="7.50", stock=12, stato="active",
             varianti=1, gestito=True, foto=("https://cdn.esempio/a.jpg",),
             tipo="Alimenti e bevande", desc="<p>Buono</p>"):
    v = [{"id": pid * 10 + k, "price": prezzo,
          "inventory_quantity": stock,
          "inventory_management": "shopify" if gestito else None,
          "inventory_item_id": pid * 100 + k,
          # col multi-variante ogni variante ha il suo nome, come sul
          # negozio vero («S», «M»...): e' quel che finisce nel titolo
          **({"title": f"T{k + 1}"} if varianti > 1 else {})}
         for k in range(varianti)]
    return {"id": pid, "title": titolo, "body_html": desc, "status": stato,
            "product_type": tipo, "variants": v,
            "images": [{"src": u} for u in foto]}


def prodotto_woo(pid, nome, prezzo="7.50", stock=12, gestito=True,
                 tipo="simple", stato="publish", visibile="visible",
                 disponibile="instock", desc="<p>Buono</p>",
                 foto=("https://cdn.esempio/w.jpg",), categoria="Casa"):
    return {"id": pid, "name": nome, "description": desc, "type": tipo,
            "status": stato, "catalog_visibility": visibile,
            "price": prezzo, "regular_price": prezzo,
            "manage_stock": gestito,
            "stock_quantity": stock if gestito else None,
            "stock_status": disponibile,
            "images": [{"src": u} for u in foto],
            "categories": [{"id": 1, "name": categoria}]}


TOKEN_BUONO = ["shpat_finto"]   # il negozio sa dire di no (tappa 5)


def api_finta(metodo, url, intestazioni):
    """Al posto di `chiama_api_negozio`. A smistare e' l'indirizzo,
    che i due dialetti costruiscono diverso.

    IL TOKEN SHOPIFY SI GUARDA, e serve alla tappa 5: «si prova prima
    di crederci» si puo' provare solo contro un negozio che sappia
    dire di NO — con un'API che risponde 200 a chiunque, un token
    sbagliato e uno buono si comporterebbero allo stesso modo e la
    prova non direbbe niente. Woo resta senza: le sue chiavi viaggiano
    in basic auth, e quel che li' interessa e' l'IVA."""
    LETTURE.append(url)
    if ERRORE_API[0]:
        raise RuntimeError(ERRORE_API[0])
    if "/wp-json/" not in url:
        if (intestazioni or {}).get("X-Shopify-Access-Token") \
                not in TOKEN_BUONO:
            return 401, {"errors": "Invalid API key or access token"}, {}
        return 200, {"products": list(CATALOGO)}, {}
    # --- WooCommerce ---
    for prefisso, risposta in RISPOSTE_WOO.items():
        if url.startswith(prefisso):
            return risposta
    if url.endswith("/settings/general"):
        return 200, {"lista": [{"id": "woocommerce_calc_taxes",
                                "value": TASSE_WOO[0]}]}, {}
    if url.endswith("/settings/tax"):
        return 200, {"lista": [{"id": "woocommerce_prices_include_tax",
                                "value": IVA_WOO[0]}]}, {}
    m = re.search(r"/products/(\d+)/variations", url)
    if m:
        return 200, {"lista": list(VARIAZIONI_WOO.get(int(m.group(1)),
                                                      []))}, {}
    return (200, {"lista": list(CATALOGO_WOO)},
            {"X-WP-Total": str(len(CATALOGO_WOO))})


def avvio():
    """Il config finto PRIMA di importare server."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-connettori-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    # i segnaposto del config d'esempio: lo scanner dei segreti in CI
    # cerca queste chiavi per NOME e lascia passare solo INCOLLA_QUI
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
    # LA LEVA ACCESA, che e' l'unica differenza col mondo di oggi: in
    # produzione nasce False apposta, qui si prova il giro
    cfg.CONNETTORI_NEGOZIO_APERTI = True
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server
    server.init_db()

    # il trasporto: il negozio di cartone al posto della rete
    server.chiama_api_negozio = api_finta

    # le foto: non si scarica niente, si annota il nome che avrebbe
    def foto_finta(annuncio_id, indice, url):
        return f"a{annuncio_id}_{indice}.jpg"
    server._salva_foto_connettore = foto_finta

    # il cambio, senza CoinGecko
    server.cambio_per_import = lambda: {"EUR": CAMBIO, "USD": CAMBIO}

    # la moderazione: si CONTA e si passa. Il verdetto vero lo prova
    # collaudo_impersonazione.py, che vuole la chiave; qui interessa
    # QUANTE volte la si chiama — cioe' che si paghi una volta sola.
    async def lotto_finto(voci):
        CHIAMATE_AI.append(len(voci))
        return {}
    server.moderazione_ai_lotto = lotto_finto

    async def niente(*a, **k):
        return None
    server.notifica_admin = niente
    # Il giro di una vendita vera (tappa 4) passa dal funnel
    # dell'accredito: quel che non c'entra col registro si spegne —
    # le due piazze, il polso dei moderatori e il cambio, che
    # altrimenti andrebbe a chiedere a CoinGecko.
    server.polso_ordini_admin = niente
    server.annuncio_su_nostr = niente
    server.promo_venduto = niente

    async def cambio_finto():
        return CAMBIO
    server.cambio_btc_eur = cambio_finto

    async def annota(tg_id, testo, *a, **k):
        NOTIFICHE.append((tg_id, testo))
    server.notifica = annota
    return db


def collega(fonte="shopify", url="mio.myshopify.com", consegna="spedizione",
            zona="Carmagnola (TO)"):
    """Scrive il collegamento a mano: l'endpoint arriva alla tappa 5,
    e quel che si prova qui e' il GIRO."""
    # ogni piattaforma ha la sua busta: Shopify un token, Woo una
    # chiave e un segreto — ed e' il LETTORE a sapere che forma hanno
    chiavi = ({"consumer_key": "ck_finta",
               "consumer_secret": "cs_segretissima"} if fonte == "woo"
              else {"token": "shpat_finto"})
    con = SRV.db()
    cur = con.execute(
        "INSERT INTO connettori(tg_id,fonte,url_negozio,credenziali,"
        "consegna,spedizione_eur,zona,creato) VALUES(?,?,?,?,?,?,?,?)",
        (VENDITORE, fonte, url,
         SRV._cifra_contenuto(json.dumps(chiavi)),
         consegna, 5.0, zona, int(time.time())))
    con.commit()
    cid = cur.lastrowid
    con.close()
    return cid


def giro():
    """Un giro di sync, come lo farebbe l'orologio."""
    SRV._prossimo_giro_connettori = 0.0
    asyncio.run(SRV.sincronizza_connettori())


def annunci(cid=None):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    q = ("SELECT * FROM annunci WHERE connettore_id=? ORDER BY id"
         if cid else "SELECT * FROM annunci ORDER BY id")
    righe = [dict(r) for r in con.execute(q, (cid,) if cid else ())]
    con.close()
    return righe


def uno(cid, chiave):
    for a in annunci(cid):
        if a["origine_chiave"] == str(chiave):
            return a
    return None


def ordine_pagato(annuncio_id, pezzi=1):
    """Un ordine appena pagato, pronto per `_incassa_ordine`.

    Si scrive a mano perche' quel che si prova qui non e' il checkout
    — quello ha i suoi collaudi — ma cosa succede al REGISTRO quando
    i sats arrivano in cassaforte."""
    adesso = int(time.time())
    con = SRV.db()
    cur = con.execute(
        "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
        "prezzo_sats,quantita,stato,consegna_scelta,creato,aggiornato) "
        "VALUES(?,?,?,?,?,'creato','spedizione',?,?)",
        (annuncio_id, COMPRATORE, VENDITORE, 20_000 * pezzi, pezzi,
         adesso, adesso))
    con.commit()
    oid = cur.lastrowid
    con.close()
    return oid


def rimborsa(ordine_id):
    """La disputa decisa a favore del compratore. `payout_stato` a
    'uscito' fa prendere a `_rimborsa_compratore` il ramo PAGATO
    senza chiedere niente a Lightning: qui non si prova il pagamento,
    si prova che il registro torni in pari."""
    con = SRV.db()
    con.execute("UPDATE ordini SET stato='dispute', payout_stato='uscito' "
                "WHERE id=?", (ordine_id,))
    con.commit()
    con.close()
    return asyncio.run(SRV._rimborsa_compratore(ordine_id))


# --- GLI ENDPOINT (tappa 5) -------------------------------------------
# Il cassetto si prova chiamando le rotte VERE: `verifica_utente` e
# `leggi_json` si sostituiscono con due stub (il pattern di
# collaudo_feedback_confermato) e il resto e' il server di sempre.

def come(tg_id):
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "first_name": f"U{tg_id}",
        "username": f"u{tg_id}", "admin": False}


def chiama(fn, *args, corpo=None):
    if corpo is not None:
        async def leggi(_req):
            return corpo
        SRV.leggi_json = leggi
    return asyncio.run(fn(*args))


def errore(fn, *args, corpo=None):
    """Il codice e il messaggio di un rifiuto, o None se e' passato."""
    try:
        chiama(fn, *args, corpo=corpo)
        return None
    except Exception as e:
        return (getattr(e, "status_code", type(e).__name__),
                str(getattr(e, "detail", e)))


def quanti_connettori():
    con = SRV.db()
    n = con.execute("SELECT COUNT(*) AS n FROM connettori").fetchone()[0]
    con.close()
    return n


def maglia_woo(vid, prezzo, taglia, disponibile="instock"):
    """Una variazione con DUE attributi, come quelle di AGORA."""
    return {"id": vid, "price": prezzo, "regular_price": prezzo,
            "status": "publish", "manage_stock": False,
            "stock_quantity": None, "stock_status": disponibile,
            "virtual": False, "downloadable": False,
            "attributes": [{"id": 1, "name": "Colore",
                            "option": "Golden Yellow"},
                           {"id": 2, "name": "Taglia", "option": taglia}],
            "image": None}


def vetrina(**extra):
    """La prima pagina vera della vetrina, come la chiede il client."""
    return asyncio.run(SRV.lista_annunci(
        limit=60, cursore="", q=extra.pop("q", ""), cat="", ordina="",
        x_tg_init_data="", barattolo_sessione="", **extra))


def famiglie_collaudo(wid):
    base = len(CATALOGO_WOO)
    numeri = {1: "#01/21", 2: "#02/21", 9: "#09/21", 19: "#19/21"}
    for n, ed in numeri.items():
        # il #09 porta il cuore davanti, come sul negozio vero
        cuore = "💛 " if n == 9 else ""
        CATALOGO_WOO.append(prodotto_woo(
            300 + n, f"{cuore}ɅGOᏒɅ COWBOY Limited Edition {ed}", "30.00",
            tipo="variable", gestito=False, categoria="Abbigliamento"))
        VARIAZIONI_WOO[300 + n] = [
            maglia_woo(3000 + n * 10 + k, prezzo, t, disp)
            for k, (t, prezzo, disp) in enumerate((
                ("S", "30.00", "instock"),
                # la M del #02 costa di piu': la card dira' «da»
                ("M", "32.00" if n == 2 else "30.00", "instock"),
                # la L del #19 e' finita: il #19 ne ha una in meno
                ("L", "30.00", "outofstock" if n == 19 else "instock")))]
    CATALOGO_WOO.extend([
        prodotto_woo(337, "ɅGOᏒɅ COWBOY 1st EDITION", "45.00",
                     tipo="variable", gestito=False),
        # un numero SENZA cancelletto non fa famiglia, e un solo
        # prodotto numerato nemmeno
        prodotto_woo(338, "Scarpe 42/43", "50.00", gestito=False),
        prodotto_woo(339, "Stampa d'arte #3/10", "20.00", gestito=False),
    ])
    VARIAZIONI_WOO[337] = [maglia_woo(3371, "45.00", "M"),
                           maglia_woo(3372, "45.00", "L")]
    giro()
    righe = [a for a in annunci(wid) if a["origine_chiave"].startswith(
        tuple(str(x) for x in (301, 302, 309, 319, 337, 338, 339)))]
    cow = [a for a in righe if "Limited" in a["titolo"]]
    prova("le magliette numerate entrano tutte, una riga per variante",
          (12, 11), (len(cow), sum(a["stato"] == "attivo" for a in cow)))
    prova("...e sono UNA famiglia, anche il #09 col cuore davanti",
          1, len({a["famiglia"] for a in cow}))
    fam = cow[0]["famiglia"]
    prova("...la chiave porta il collegamento davanti", True,
          fam.startswith(f"c{wid}:e:"))
    prova("...col titolo pulito dal numero", "ɅGOᏒɅ COWBOY Limited Edition",
          cow[0]["famiglia_titolo"])
    nove = next(a for a in cow if a["origine_chiave"] == "309:3091")
    prova("le opzioni: il Numero davanti, poi colore e taglia",
          [["Numero", "09/21"], ["Colore", "Golden Yellow"], ["Taglia", "M"]],
          json.loads(nove["opzioni"]))
    prima = next(a for a in righe if a["origine_chiave"].startswith("337:"))
    prova("la 1st EDITION e' un'altra famiglia (niente numero)", True,
          prima["famiglia"].startswith(f"c{wid}:p:")
          and prima["famiglia"] != fam)
    prova("un numero senza cancelletto e un numerato solo: nessuna famiglia",
          ("", ""), (uno(wid, 338)["famiglia"], uno(wid, 339)["famiglia"]))

    # LA VETRINA: una card per famiglia, ed e' la piu' economica
    d = vetrina()
    carte = [a for a in d["annunci"] if a.get("famiglia") == fam]
    prova("in vetrina la famiglia e' UNA card", 1, len(carte))
    prova("...la variante disponibile piu' economica (e la piu' vecchia)",
          min((a["prezzo_sats"], a["id"]) for a in cow
              if a["stato"] == "attivo")[1], carte[0]["id"])
    prova("...con quante sono e il «da», perche' la M del #02 costa di piu'",
          (11, True), (carte[0]["famiglia_n"], carte[0]["famiglia_varia"]))
    prova("...e le opzioni come lista, non come testo", list,
          type(carte[0]["opzioni"]))
    prova("la 1st EDITION: una card anche lei, senza «da»", [(2, False)],
          [(a["famiglia_n"], a["famiglia_varia"]) for a in d["annunci"]
           if a.get("famiglia") == prima["famiglia"]])
    con = SRV.db()
    abbigliamento = con.execute(
        "SELECT COUNT(*) FROM annunci WHERE categoria=? AND stato='attivo'",
        (carte[0]["categoria"],)).fetchone()[0]
    con.close()
    prova("i conteggi per categoria contano la famiglia UNA volta", True,
          d["conteggi"].get(carte[0]["categoria"], 0) < abbigliamento)

    # LA RICERCA: la prima variante PERTINENTE, una volta sola
    d = vetrina(q="cowboy limited 09")
    trovate = [a for a in d["annunci"] if a.get("famiglia") == fam]
    prova("cercando il #09 la famiglia esce una volta, ed e' il #09", True,
          len(trovate) == 1 and "#09" in trovate[0]["titolo"])

    # IL NEGOZIO: una card per famiglia, e le varianti finite della
    # famiglia viva non si ripetono fra gli esauriti
    neg = SRV.negozio(chi="abc123", limit=60, cursore="",
                      x_tg_init_data="", barattolo_sessione="")
    prova("nel negozio la famiglia e' una card", 1,
          sum(a.get("famiglia") == fam for a in neg["annunci"]))
    prova("...e la L esaurita del #19 non sta fra gli esauriti", 0,
          sum(a.get("famiglia") == fam for a in neg.get("esauriti", [])))

    # LA SCHEDA: tutte le sorelle vendibili o finite, con le opzioni
    r = SRV.un_annuncio(nove["id"], x_tg_init_data="", barattolo_sessione="")
    prova("la scheda porta le sorelle (esaurite comprese)", (12, 1),
          (len(r["famiglia_varianti"]),
           sum(s["stato"] == "venduto" for s in r["famiglia_varianti"])))
    prova("...ognuna con le sue opzioni", ["Numero", "Colore", "Taglia"],
          [o[0] for o in r["famiglia_varianti"][0]["opzioni"]])
    prova("un annuncio senza famiglia non ne porta", None,
          SRV.un_annuncio(uno(wid, 338)["id"], x_tg_init_data="",
                          barattolo_sessione="").get("famiglia_varianti"))

    # L'ACQUISTO VA ALLA VARIANTE: la M del #09 venduta qui scende lei,
    # e le sorelle non se ne accorgono
    ordine = ordine_pagato(nove["id"])
    asyncio.run(SRV._incassa_ordine(ordine))
    prova("comprata la M del #09: e' lei a finire", "venduto",
          uno(wid, "309:3091")["stato"])
    prova("...e le sorelle restano in vetrina", ("attivo", "attivo"),
          (uno(wid, "309:3090")["stato"], uno(wid, "309:3092")["stato"]))
    d = vetrina()
    prova("...la famiglia resta UNA card, con una variante in meno",
          [10], [a["famiglia_n"] for a in d["annunci"]
                 if a.get("famiglia") == fam])

    # LA FAMIGLIA SI SCIOGLIE: restano il #01 e la 1st EDITION
    CATALOGO_WOO[:] = [p for p in CATALOGO_WOO
                       if p["id"] not in (302, 309, 319)]
    giro()
    uno01 = uno(wid, "301:3010")
    prova("rimasto solo il #01, e' una famiglia di taglie e basta", True,
          uno01["famiglia"] == f"c{wid}:p:301"
          and json.loads(uno01["opzioni"])[0][0] == "Colore")
    prova("...e il titolo della card e' il suo",
          "ɅGOᏒɅ COWBOY Limited Edition #01/21", uno01["famiglia_titolo"])

    # SHOPIFY: i nomi delle opzioni stanno sul padre, i valori sulla
    # variante (option1, option2)
    tee = prodotto(40, "Felpa", "35.00", varianti=2)
    tee["options"] = [{"name": "Taglia"}, {"name": "Colore"}]
    tee["variants"][0].update(option1="S", option2="Nero")
    tee["variants"][1].update(option1="M", option2="Nero")
    CATALOGO.append(tee)
    # un collegamento nuovo: quello della sezione 1 e' finito in errore
    # alla sezione 10, apposta, e il giro non lo legge piu'
    sid = collega(url="felpe.myshopify.com")
    giro()
    prova("Shopify: le opzioni hanno i nomi del negozio",
          [["Taglia", "M"], ["Colore", "Nero"]],
          json.loads(uno(sid, "40:401")["opzioni"]))
    prova("...e le due felpe sono una famiglia di titolo «Felpa»",
          (f"c{sid}:p:40", "Felpa"),
          (uno(sid, "40:400")["famiglia"], uno(sid, "40:400")["famiglia_titolo"]))

    # via, per non cambiare le sezioni che seguono (il cassetto conta i
    # collegamenti del venditore): il collegamento di qui si toglie coi
    # suoi annunci, e i prodotti di qui escono dai due cataloghi
    con = SRV.db()
    con.execute("UPDATE annunci SET stato='rimosso' WHERE connettore_id=?",
                (sid,))
    con.execute("DELETE FROM connettori WHERE id=?", (sid,))
    con.commit()
    con.close()
    del CATALOGO_WOO[base:]
    CATALOGO[:] = [p for p in CATALOGO if p["id"] != 40]
    giro()


def main():
    print("=" * 62)
    print("  IL COLLAUDO DEI CONNETTORI")
    print("=" * 62)
    avvio()
    con = SRV.db()
    con.execute("INSERT OR IGNORE INTO utenti(tg_id,nome,negozio) "
                "VALUES(?,?,?)", (VENDITORE, "Il Negozio", "abc123"))
    con.commit()
    con.close()
    cid = collega()

    # ---- 1. il primo giro -------------------------------------------
    print("\n[il primo giro: il catalogo diventa vetrina]")
    CATALOGO[:] = [
        prodotto(1, "Miele di castagno", "7.50", stock=12),
        prodotto(2, "Olio EVO 500ml", "12.00", stock=3),
        prodotto(3, "Maglietta", "20.00", varianti=3),      # multi-variante
        prodotto(4, "Birra artigianale", "4.00", gestito=False),
        prodotto(5, "Bozza mai pubblicata", "9.00", stato="draft"),
    ]
    giro()
    righe = annunci(cid)
    # (set 2026) il multi-variante non si salta piu': entra come UNA
    # RIGA PER VARIANTE, «Titolo — variante»
    prova("entrano i prodotti trattabili, e il multi-variante per variante",
          {"Miele di castagno", "Olio EVO 500ml", "Birra artigianale",
           "Maglietta — T1", "Maglietta — T2", "Maglietta — T3"},
          {a["titolo"] for a in righe if a["stato"] == "attivo"})
    miele = uno(cid, 1)
    prova("il prezzo e' il listino in EURO", (7.5, "eur"),
          (miele["prezzo_eur"], miele["valuta"]))
    prova("...e i sats sono l'equivalente al cambio del giro", 7_500,
          miele["prezzo_sats"])
    prova("la giacenza arriva dal negozio", 12, miele["quantita"])
    prova("l'origine e' scritta", ("shopify", cid, "1"),
          (miele["fonte"], miele["connettore_id"], miele["origine_chiave"]))
    prova("la consegna viene dal CASSETTO, non dal negozio",
          ("spedizione", 5.0, "Carmagnola (TO)"),
          (miele["consegna"], miele["spedizione_eur"], miele["zona"]))
    # EMENDATA (16 nov 2026, cantiere categoria-connettori): era «la
    # categoria nasce Altro, la sceglie la coda, non il product_type».
    # Adesso il nome del negozio vale quando combacia PER INTERO con una
    # nostra categoria o un sinonimo intero («Alimenti» lo e'); il dubbio
    # resta in «Altro» per la coda (vedi Architettura, «LA CATEGORIA DEI
    # NEGOZI COLLEGATI»)
    prova("la categoria nasce da quella del negozio, quando combacia per "
          "intero", "Alimenti e bevande", miele["categoria"])
    prova("la descrizione e' spogliata dell'HTML", "Buono",
          miele["descrizione"])
    birra = uno(cid, 4)
    prova("lo stock NON tracciato non si inventa: resta 1", 1,
          birra["quantita"])
    prova("...e si annota che non lo sappiamo", -1,
          birra["origine_stock_visto"])
    # EMENDATA (1 ott 2026 sera, «negozi grandi», decisione di Andrea): la
    # bozza nasceva «rimosso», cioe' con la lapide — e il giorno che il
    # negoziante la pubblicava restava fuori per sempre. Adesso non nasce
    # proprio, ed entra quando la pubblica (lo prova collaudo_negozi_grandi)
    prova("la bozza non entra in vetrina: non nasce proprio", None,
          uno(cid, 5))
    prova("il PADRE multi-variante non e' un annuncio: lo sono le figlie",
          (None, "3:30", 20.0),
          (uno(cid, 3), uno(cid, "3:30")["origine_chiave"],
           uno(cid, "3:30")["prezzo_eur"]))
    con = SRV.db()
    esito = json.loads(con.execute(
        "SELECT ultimo_esito FROM connettori WHERE id=?", (cid,)
    ).fetchone()[0])
    con.close()
    prova("...e il report non le salta: le elenca fra gli ENTRATI",
          ([], 3),
          ([s for s in esito["saltati"] if s["titolo"].startswith("Maglietta")],
           len([e for e in esito["entrati"]
                if e["titolo"].startswith("Maglietta")])))
    prova("il venditore riceve UN riepilogo", 1, len(NOTIFICHE))

    # ---- 2. il secondo giro, a catalogo fermo ------------------------
    print("\n[il secondo giro: la moderazione si paga una volta sola]")
    prima = len(CHIAMATE_AI)
    giro()
    prova("a testo invariato all'AI non si chiede niente", prima,
          len(CHIAMATE_AI))
    # sei: Miele, Olio, Birra e le TRE varianti della Maglietta (set 2026);
    # erano quattro quando il multi-variante si saltava, e sette finche' la
    # bozza nasceva «rimossa» (fino al 1 ott 2026 sera: adesso non nasce)
    prova("...e non nasce nessun doppione", 6, len(annunci(cid)))
    prova("...ne' un secondo riepilogo (niente e' successo)", 1,
          len(NOTIFICHE))

    # ---- 3. il prezzo cambia sul negozio -----------------------------
    print("\n[il negozio si muove: prezzo e giacenza]")
    CATALOGO[0] = prodotto(1, "Miele di castagno", "9.00", stock=10)
    giro()
    miele = uno(cid, 1)
    prova("il prezzo nuovo arriva qui", (9.0, 9_000),
          (miele["prezzo_eur"], miele["prezzo_sats"]))
    prova("...e cosi' la giacenza", 10, miele["quantita"])

    # ---- 4. LA PROVA REGINA ------------------------------------------
    print("\n[la prova regina: una vendita qui non si rialza]")
    # si vende UN pezzo su Barattolo: lo stock locale scala e resta la
    # pendente, che e' quel che la fase 2 drenera' verso il negozio
    con = SRV.db()
    con.execute("UPDATE annunci SET quantita=quantita-1 WHERE id=?",
                (miele["id"],))
    con.execute("INSERT INTO connettori_uscite(connettore_id,annuncio_id,"
                "ordine_id,delta,tipo,stato,creato) "
                "VALUES(?,?,?,?,'vendita','pendente',?)",
                (cid, miele["id"], 4242, -1, int(time.time())))
    con.commit()
    con.close()
    prova("dopo la vendita qui la giacenza e' scesa", 9,
          uno(cid, 1)["quantita"])
    # il negozio non sa ancora niente: la sua lettura dice ancora 10
    giro()
    prova("il sync NON la rialza (la pendente si sottrae)", 9,
          uno(cid, 1)["quantita"])
    # il venditore riallinea il suo magazzino: adesso di la' sono 9
    CATALOGO[0] = prodotto(1, "Miele di castagno", "9.00", stock=9)
    giro()
    prova("quando il venditore riallinea, il conto resta giusto", 9,
          uno(cid, 1)["quantita"])

    # ---- 5. il pezzo unico venduto qui -------------------------------
    print("\n[il pezzo unico venduto qui non risorge]")
    olio = uno(cid, 2)
    con = SRV.db()
    con.execute("UPDATE annunci SET quantita=0, stato='venduto' WHERE id=?",
                (olio["id"],))
    con.execute("INSERT INTO connettori_uscite(connettore_id,annuncio_id,"
                "ordine_id,delta,tipo,stato,creato) "
                "VALUES(?,?,?,?,'vendita','pendente',?)",
                (cid, olio["id"], 4243, -3, int(time.time())))
    con.commit()
    con.close()
    giro()   # sul negozio sono ancora 3
    olio = uno(cid, 2)
    prova("resta venduto, e la giacenza resta a zero",
          ("venduto", 0), (olio["stato"], olio["quantita"]))

    # ---- 6. il rifornimento vero -------------------------------------
    print("\n[il rifornimento sul negozio riaccende l'annuncio]")
    con = SRV.db()
    con.execute("UPDATE connettori_uscite SET stato='riflessa' "
                "WHERE annuncio_id=?", (olio["id"],))
    con.commit()
    con.close()
    CATALOGO[1] = prodotto(2, "Olio EVO 500ml", "12.00", stock=6)
    giro()
    olio = uno(cid, 2)
    prova("torna in vetrina con la giacenza vera", ("attivo", 6),
          (olio["stato"], olio["quantita"]))

    # ---- 7. la sparizione --------------------------------------------
    print("\n[il prodotto tolto dal negozio sparisce anche qui]")
    con = SRV.db()
    con.execute("INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
                "prezzo_sats,stato,creato,aggiornato) "
                "VALUES(?,?,?,?,'creato',?,?)",
                (uno(cid, 4)["id"], 111, VENDITORE, 4000,
                 int(time.time()), int(time.time())))
    con.commit()
    con.close()
    CATALOGO[:] = [c for c in CATALOGO if c["id"] != 4]
    giro()
    prova("l'annuncio si spegne", "rimosso", uno(cid, 4)["stato"])
    con = SRV.db()
    stato_ordine = con.execute(
        "SELECT stato FROM ordini WHERE annuncio_id=?",
        (uno(cid, 4)["id"],)).fetchone()[0]
    con.close()
    prova("...e l'ordine mai pagato si annulla", "annullato", stato_ordine)

    # ---- 8. lo scudo anti-resurrezione -------------------------------
    print("\n[quel che e' stato tolto qui non torna da solo]")
    # il prodotto torna sul negozio, e per giunta col titolo cambiato
    CATALOGO.append(prodotto(4, "Birra artigianale IPA", "4.00",
                             gestito=False))
    giro()
    prova("il prodotto rimesso sul negozio NON risorge", "rimosso",
          uno(cid, 4)["stato"])
    # ...e NON si continua a lavorarci sopra: senza lo scudo la riga
    # verrebbe aggiornata lo stesso — titolo riscritto, foto
    # riscaricate — restando invisibile. Il titolo vecchio e' la prova
    # che la riga e' stata SALTATA e non solo lasciata spenta.
    prova("...e non si aggiorna nemmeno", "Birra artigianale",
          uno(cid, 4)["titolo"])
    con = SRV.db()
    esito = json.loads(con.execute(
        "SELECT ultimo_esito FROM connettori WHERE id=?", (cid,)
    ).fetchone()[0])
    con.close()
    prova("...e il report dice perche'",
          ["gia' rimosso qui: non si ricrea da solo"],
          [s["perche"] for s in esito["saltati"]
           if s["titolo"].startswith("Birra")])

    # ---- 9. la rete che cade -----------------------------------------
    print("\n[un catalogo che non si legge non e' un catalogo vuoto]")
    vivi = [a["id"] for a in annunci(cid) if a["stato"] == "attivo"]
    ERRORE_API[0] = "connessione rifiutata"
    giro()
    ERRORE_API[0] = None
    prova("nessun annuncio si spegne", vivi,
          [a["id"] for a in annunci(cid) if a["stato"] == "attivo"])
    con = SRV.db()
    c = con.execute("SELECT errori_di_fila, stato, ultimo_errore "
                    "FROM connettori WHERE id=?", (cid,)).fetchone()
    con.close()
    prova("...ma l'errore si conta e si scrive", (1, "attivo"),
          (c[0], c[1]))
    prova("...senza mai il token nel messaggio", False,
          "shpat_finto" in (c[2] or ""))

    # ---- 10. il collegamento rotto -----------------------------------
    print("\n[cinque giri a vuoto: il collegamento si dichiara rotto]")
    ERRORE_API[0] = "connessione rifiutata"
    for _ in range(4):
        giro()
    ERRORE_API[0] = None
    con = SRV.db()
    stato = con.execute("SELECT stato FROM connettori WHERE id=?",
                        (cid,)).fetchone()[0]
    con.close()
    prova("il collegamento passa in errore", "errore", stato)
    prova("...e il venditore lo viene a sapere UNA volta", 1,
          len([n for n in NOTIFICHE if "non risponde" in n[1]]))
    giro()
    prova("...e da li' il giro lo salta", "errore", stato)

    # ---- 11. il secondo dialetto -------------------------------------
    # Da qui in avanti il connettore Shopify e' in 'errore', quindi il
    # giro guarda solo il Woo: e' quel che serve per leggere le due
    # sezioni che seguono senza confondere i due negozi.
    print("\n[WooCommerce: l'altro dialetto]")
    wid = collega(fonte="woo", url="https://ilmionegozio.it")
    CATALOGO_WOO[:] = [
        prodotto_woo(11, "Tazza in ceramica", "14.00", stock=8),
        prodotto_woo(12, "Maglietta", "20.00", tipo="variable"),
        prodotto_woo(13, "Corso di cucina", "80.00", tipo="external"),
        prodotto_woo(14, "Set di posate", "35.00", tipo="grouped"),
        prodotto_woo(15, "Sapone all'olio", "6.00", gestito=False,
                     disponibile="outofstock"),
        prodotto_woo(16, "Vaso di scorta", "9.00", visibile="hidden"),
        prodotto_woo(17, "Tovaglia su ordinazione", "22.00",
                     gestito=False, disponibile="onbackorder"),
    ]
    giro()
    prova("entra quel che sappiamo trattare",
          {"Tazza in ceramica", "Tovaglia su ordinazione"},
          {a["titolo"] for a in annunci(wid) if a["stato"] == "attivo"})
    tazza = uno(wid, 11)
    prova("il prezzo e' il listino in EURO, coi sats al cambio del giro",
          (14.0, "eur", 14_000),
          (tazza["prezzo_eur"], tazza["valuta"], tazza["prezzo_sats"]))
    prova("l'origine dice WooCommerce", ("woo", wid, "11"),
          (tazza["fonte"], tazza["connettore_id"], tazza["origine_chiave"]))
    prova("la giacenza arriva dal negozio", 8, tazza["quantita"])
    con = SRV.db()
    esito = json.loads(con.execute(
        "SELECT ultimo_esito FROM connettori WHERE id=?", (wid,)
    ).fetchone()[0])
    con.close()
    # I TRE TIPI CHE NON SAPPIAMO TRATTARE, e `external` e' quello che
    # si dimentica: un prezzo ce l'ha e sembra un prodotto normale, ma
    # il suo bottone porta su un ALTRO sito.
    # (set 2026) il `variable` si legge; la Maglietta qui non ha
    # variazioni in vendita, e il motivo dice QUELLO
    prova("i tre tipi che non sappiamo trattare si saltano, col motivo",
          {"Maglietta": "nessuna delle sue varianti e' in vendita",
           "Set di posate": "e' un gruppo di prodotti",
           "Corso di cucina": "si compra su un altro sito"},
          {s["titolo"]: s["perche"] for s in esito["saltati"]
           if s["titolo"] in ("Maglietta", "Set di posate",
                              "Corso di cucina")})
    # L'INVARIANTE DI CASA VALE ANCHE ALLA NASCITA: un prodotto che
    # arriva GIA' esaurito non deve nascere 'attivo' con zero pezzi —
    # sarebbe un annuncio comprabile all'occhio che alla cassa dice di
    # no, e nessuna scopa lo raddrizza. Su Woo e' il caso quotidiano.
    sapone = uno(wid, 15)
    prova("chi arriva gia' esaurito nasce «venduto», non «attivo»",
          ("venduto", 0), (sapone["stato"], sapone["quantita"]))
    # EMENDATA (1 ott 2026 sera): come la bozza, il nascosto mai visto non
    # nasce piu' «rimosso» (la lapide): non nasce, ed entra se lo mostra
    prova("il prodotto nascosto nello scaffale non entra in vetrina",
          None, uno(wid, 16))
    # ...e il rovescio: «su ordinazione» sul suo sito si compra ancora,
    # quindi la giacenza resta IGNOTA e non diventa zero
    prova("«su ordinazione» resta comprabile", ("attivo", 1),
          (uno(wid, 17)["stato"], uno(wid, 17)["quantita"]))
    prova("...e si annota che la giacenza non la sappiamo", -1,
          uno(wid, 17)["origine_stock_visto"])
    prova("la consegna viene dal CASSETTO anche qui",
          ("spedizione", 5.0), (tazza["consegna"], tazza["spedizione_eur"]))

    # ---- 12. L'IVA -----------------------------------------------------
    # LA PROVA CHE CONTA DELLA TAPPA 3. WooCommerce non dice nel
    # prodotto se `price` include le tasse: dipende da un'impostazione
    # del negozio. Con i prezzi scritti al NETTO, importarli com'e'
    # vorrebbe dire mettere in vetrina una cifra piu' bassa di quella
    # che sul suo sito si paga — e il venditore lo scoprirebbe
    # incassando.
    print("\n[l'IVA: un prezzo che non e' il prezzo non si importa]")
    vivi = [(a["id"], a["stato"]) for a in annunci(wid)]
    quante = len(NOTIFICHE)
    IVA_WOO[0] = "no"          # «prezzi inseriti SENZA le tasse»
    giro()
    prova("col netto il catalogo non si legge: nessun prezzo cambia",
          vivi, [(a["id"], a["stato"]) for a in annunci(wid)])
    # ...ed e' QUESTA la ragione per cui `prezzi_finiti_woo` ALZA invece
    # di marchiare le righe una per una: una riga saltata non entra in
    # `viste`, quindi la riconciliazione la tratterebbe come sparita
    # dal negozio e la spegnerebbe — saltare tutto il catalogo
    # vorrebbe dire spegnere la vetrina di quel venditore in un colpo.
    prova("...e SOPRATTUTTO nessun annuncio si spegne",
          {"Tazza in ceramica", "Tovaglia su ordinazione"},
          {a["titolo"] for a in annunci(wid) if a["stato"] == "attivo"})
    con = SRV.db()
    c = con.execute("SELECT errori_di_fila, ultimo_errore FROM connettori "
                    "WHERE id=?", (wid,)).fetchone()
    con.close()
    prova("l'errore si conta, come una rete caduta", 1, c[0])
    prova("...e il motivo VERO resta scritto, per il venditore", True,
          "NETTO" in (c[1] or ""))
    prova("...senza mai le chiavi nel messaggio", False,
          "cs_segretissima" in (c[1] or ""))
    prova("nessuno viene svegliato per un giro solo", quante,
          len(NOTIFICHE))
    # e il rientro: rimessa l'impostazione, il giro riprende da solo
    IVA_WOO[0] = "yes"
    CATALOGO_WOO[0] = prodotto_woo(11, "Tazza in ceramica", "16.00",
                                   stock=5)
    giro()
    tazza = uno(wid, 11)
    prova("sistemata l'impostazione, il catalogo torna a scorrere",
          (16.0, 16_000, 5),
          (tazza["prezzo_eur"], tazza["prezzo_sats"], tazza["quantita"]))
    con = SRV.db()
    prova("...e il conto degli errori si azzera", 0,
          con.execute("SELECT errori_di_fila FROM connettori WHERE id=?",
                      (wid,)).fetchone()[0])
    con.close()
    # LE TASSE SPENTE sono l'altro caso lecito: il prezzo e' quel che e'
    TASSE_WOO[0], IVA_WOO[0] = "no", "no"
    CATALOGO_WOO[0] = prodotto_woo(11, "Tazza in ceramica", "18.00",
                                   stock=5)
    giro()
    prova("col negozio senza tasse il prezzo si legge com'e'", 18.0,
          uno(wid, 11)["prezzo_eur"])

    # ---- 13. IL REGISTRO SCRITTO DA UNA VENDITA VERA ----------------
    # Fin qui le pendenti erano state messe A MANO: era il modo di
    # provare la CORREZIONE dello stock senza avere ancora chi la
    # scrive. Dalla tappa 4 a scriverla c'e' `_incassa_ordine`, cioe'
    # il funnel da cui passano tutte e tre le strade dell'accredito —
    # e questa e' la prova che il giro si chiude da solo.
    print("\n[la vendita vera scrive il registro, e non si rialza]")
    tazza = uno(wid, 11)
    NOTIFICHE.clear()
    ordine = ordine_pagato(tazza["id"], pezzi=2)
    asyncio.run(SRV._incassa_ordine(ordine))
    con = SRV.db()
    uscite = [(r[0], r[1], r[2]) for r in con.execute(
        "SELECT tipo, delta, stato FROM connettori_uscite "
        "WHERE annuncio_id=? ORDER BY id", (tazza["id"],))]
    con.close()
    prova("la vendita lascia la pendente, col segno",
          [("vendita", -2, "pendente")], uscite)
    prova("...e lo stock locale e' sceso", 3, uno(wid, 11)["quantita"])
    venditore = [t for chi, t in NOTIFICHE if chi == VENDITORE]
    prova("il venditore riceve la riga operativa", True,
          bool(venditore) and "Aggiorna il magazzino" in venditore[-1]
          and "−2" in venditore[-1])
    prova("...e la riga dice perche' tocca a lui", True,
          "non lo scrive" in venditore[-1])
    # LA PROVA CHE CONTA: il negozio non sa ancora niente (di la' sono
    # sempre 5), e il sync NON deve rialzare la vendita.
    giro()
    prova("il sync non rialza la vendita fatta qui", 3,
          uno(wid, 11)["quantita"])
    # ...e quando il venditore scala il suo magazzino, il conto resta
    # giusto invece di sottrarre due volte
    CATALOGO_WOO[0] = prodotto_woo(11, "Tazza in ceramica", "18.00",
                                   stock=3)
    giro()
    prova("quando il venditore riallinea, il conto non si sdoppia", 3,
          uno(wid, 11)["quantita"])
    con = SRV.db()
    prova("...e la pendente si spegne da sola", "riflessa",
          con.execute("SELECT stato FROM connettori_uscite WHERE "
                      "annuncio_id=? AND tipo='vendita'",
                      (tazza["id"],)).fetchone()[0])
    con.close()

    # ---- 13-bis. IL CATALOGO PIU' GRANDE DEL TETTO -------------------
    # IL GUASTO DEL §0, sul percorso VERO. Il tetto di lettura
    # troncava il catalogo e consegnava alla riconciliazione una lista
    # corta — che sulle sparizioni si fida — quindi tutto cio' che
    # stava oltre passava a 'rimosso'. Per sempre: lo scudo
    # anti-resurrezione non lo ricrea, serve una chiave nuova.
    # `prove.py` gira la riconciliazione da sola; qui passa il SERVER,
    # che e' l'unico posto dove si vede se i due parametri arrivano
    # davvero fin la'. E se un domani qualcuno li perde per strada,
    # questo blocco MOSTRA il difetto — annunci spenti che si contano —
    # invece di descriverlo.
    # SI USA IL CONNETTORE WOO: a questo punto del collaudo quello
    # Shopify e' 'rotto' apposta (i cinque giri a vuoto della sezione
    # 10) e il giro non lo rilegge piu'.
    print("\n[il catalogo piu' grande del tetto: nessuno si spegne]")
    # I VASETTI SI AGGIUNGONO, non sostituiscono il catalogo: quel che
    # sparisce dal negozio si spegne, e 'rimosso' non risorge — con un
    # `CATALOGO_WOO[:] =` la Tazza e la Tovaglia morirebbero qui, e a
    # cadere sarebbero le prove DOPO questa (successo: e' cosi' che si
    # e' scoperto).
    woo_prima = list(CATALOGO_WOO)
    CATALOGO_WOO.extend([prodotto_woo(100 + i, f"Vasetto {i}", "3.00",
                                      stock=2) for i in range(6)])
    tetto_prima = SRV.MAX_PRODOTTI_CONNETTORE
    nuovi_prima = SRV.MAX_NUOVI_CONNETTORE_GIRO
    # (1 ott 2026) qui si guarda il REGIME del tetto all'ingresso: il
    # rodaggio delle prime ventiquattro ore ha il suo collaudo
    # (collaudo_negozi_grandi), e acceso darebbe cento posti invece di due
    rodaggio_prima = SRV.MAX_NUOVI_CONNETTORE_RODAGGIO
    SRV.MAX_NUOVI_CONNETTORE_RODAGGIO = 0

    def quanti(prefisso, solo_attivi=True):
        return len([a for a in annunci(wid)
                    if a["origine_chiave"].startswith(prefisso)
                    and (a["stato"] == "attivo" or not solo_attivi)])

    def report():
        con = SRV.db()
        r = json.loads(con.execute(
            "SELECT ultimo_esito FROM connettori WHERE id=?",
            (wid,)).fetchone()[0])
        con.close()
        return r

    try:
        # il tetto si prende dal catalogo, non da un numero scritto a
        # mano: cosi' resta «ci stanno tutti» anche se un domani il
        # collaudo aggiunge un prodotto Woo piu' su
        SRV.MAX_PRODOTTI_CONNETTORE = len(CATALOGO_WOO)
        SRV.MAX_NUOVI_CONNETTORE_GIRO = 0    # nessun tetto all'ingresso
        giro()
        prova("col catalogo intero entrano tutti i vasetti", 6,
              quanti("10"))
        prova("...e la lettura si dichiara completa", False,
              report()["parziale"])
        # ...e adesso il tetto tronca: il negozio non e' cambiato di
        # una riga, ma noi ne leggiamo la meta'. Prima di questa cura
        # i tre vasetti oltre il tetto passavano a 'rimosso'.
        SRV.MAX_PRODOTTI_CONNETTORE = 3
        giro()
        prova("il tetto tronca, e NESSUN annuncio si spegne", 6,
              quanti("10"))
        prova("...e il report dichiara la lettura parziale", True,
              report()["parziale"])
        prova("...dicendo al venditore che le sparizioni sono sospese",
              True, any("non spegniamo" in s["perche"]
                        for s in report()["saltati"]))
        # ---- e il tetto sull'INGRESSO, che e' l'altra cosa -----------
        # Legge tutto (quindi le sparizioni restano vere) e distribuisce
        # solo la nascita: e' la leva contro l'ondata in vetrina.
        SRV.MAX_PRODOTTI_CONNETTORE = 50
        SRV.MAX_NUOVI_CONNETTORE_GIRO = 2
        CATALOGO_WOO.extend([prodotto_woo(200 + i, f"Tisana {i}", "5.00",
                                          stock=1) for i in range(5)])
        giro()
        prova("le righe nuove entrano a scaglioni", 2, quanti("20"))
        prova("...e il report dice quante ne restano", 3,
              report()["rimandati"])
        prova("...mentre le altre non si spengono: sono sul negozio", 6,
              quanti("10"))
        giro()
        prova("...e al giro dopo arrivano le successive", 4, quanti("20"))
    finally:
        SRV.MAX_PRODOTTI_CONNETTORE = tetto_prima
        SRV.MAX_NUOVI_CONNETTORE_GIRO = nuovi_prima
        SRV.MAX_NUOVI_CONNETTORE_RODAGGIO = rodaggio_prima
        CATALOGO_WOO[:] = woo_prima

    # ---- 14. il pezzo che NON viene da un negozio --------------------
    print("\n[un annuncio nato qui non entra nel registro]")
    con = SRV.db()
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,categoria,prezzo_sats,"
        "quantita,quantita_max,stato,creato) "
        "VALUES(?,'Bici da corsa','Biciclette',90000,1,1,'attivo',?)",
        (VENDITORE, int(time.time())))
    nativo = cur.lastrowid
    con.commit()
    con.close()
    NOTIFICHE.clear()
    asyncio.run(SRV._incassa_ordine(ordine_pagato(nativo)))
    con = SRV.db()
    quante = con.execute("SELECT COUNT(*) FROM connettori_uscite "
                         "WHERE annuncio_id=?", (nativo,)).fetchone()[0]
    con.close()
    prova("niente registro per chi e' nato qui", 0, quante)
    prova("...e niente riga sul magazzino nella notifica", False,
          any("magazzino" in t for chi, t in NOTIFICHE if chi == VENDITORE))

    # ---- 15. IL RESO RIMETTE IN PARI --------------------------------
    # Senza questo, la vendita rimborsata continuerebbe a sottrarre un
    # pezzo fantasma A OGNI GIRO, per sempre: il sync ricopre la
    # giacenza dalla lettura esterna, e la pendente e' quel che la
    # corregge. Non fallisce da solo — un numero un po' piu' basso, e
    # basta.
    print("\n[il reso rimette in pari il registro]")
    # (a) rimborso PRIMA che il negozio scali: le due si cancellano
    tovaglia = uno(wid, 17)
    ord_a = ordine_pagato(tovaglia["id"])
    asyncio.run(SRV._incassa_ordine(ord_a))
    NOTIFICHE.clear()
    rimborsa(ord_a)
    con = SRV.db()
    stati = [r[0] for r in con.execute(
        "SELECT stato FROM connettori_uscite WHERE annuncio_id=? "
        "ORDER BY id", (tovaglia["id"],))]
    con.close()
    prova("il rimborso prima del negozio spegne la vendita",
          ["annullata"], stati)
    prova("...e al venditore non si chiede niente", False,
          any("magazzino" in t for chi, t in NOTIFICHE if chi == VENDITORE))
    giro()
    prova("...e il sync non sottrae piu' niente", 1,
          uno(wid, 17)["quantita"])

    # (b) rimborso DOPO: i pezzi vanno RIMESSI, e glielo si dice
    ord_b = ordine_pagato(tazza["id"], pezzi=1)
    asyncio.run(SRV._incassa_ordine(ord_b))
    con = SRV.db()
    con.execute("UPDATE connettori_uscite SET stato='riflessa' "
                "WHERE ordine_id=?", (ord_b,))
    con.commit()
    con.close()
    NOTIFICHE.clear()
    rimborsa(ord_b)
    con = SRV.db()
    reso = con.execute(
        "SELECT delta, stato FROM connettori_uscite WHERE ordine_id=? "
        "AND tipo='rimborso'", (ord_b,)).fetchone()
    con.close()
    prova("il rimborso dopo il negozio chiede di rimettere i pezzi",
          (1, "pendente"), (reso[0], reso[1]))
    venditore = [t for chi, t in NOTIFICHE if chi == VENDITORE]
    prova("...e glielo si dice", True,
          bool(venditore) and "Rimetti a magazzino" in venditore[-1]
          and "+1" in venditore[-1])
    # il negozio dice ancora 3 (aveva scalato la vendita), ma noi
    # sappiamo che il pezzo e' tornato: 4
    giro()
    prova("...e la giacenza qui dice la verita', non quella del negozio",
          4, uno(wid, 11)["quantita"])


    # ---- 16. VARIANTI E DIGITALI (set 2026) --------------------------
    # LE DUE SEGNALAZIONI DI «UN TEMPO PER TE», sul percorso vero: il
    # libro in PDF o cartaceo che non entrava («ha piu' varianti») e il
    # corso online entrato con «🚚 Spedizione» e «🤝 Ritiro».
    print("\n[varianti e digitali: il libro in due formati e il corso]")
    NOTIFICHE.clear()
    CATALOGO_WOO.extend([
        prodotto_woo(18, "Healthy Poke Bowls", "13.00", tipo="variable",
                     gestito=False),
        # il corso, OGGI dichiarato fisico sul negozio: e' il pregresso
        # della segnalazione, che si corregge qui sotto
        prodotto_woo(19, "Lo Yoga dell'Ascolto", "45.00", gestito=False),
    ])
    VARIAZIONI_WOO[18] = [
        variazione_woo(181, "13.00", "pdf", virtuale=True, scaricabile=True,
                       foto="https://cdn.esempio/pdf.jpg"),
        variazione_woo(182, "15.90", "cartaceo", disponibile="outofstock"),
    ]
    giro()
    pdf, carta = uno(wid, "18:181"), uno(wid, "18:182")
    corso = uno(wid, 19)
    prova("il variabile entra: un annuncio per variante, «Titolo — formato»",
          ("Healthy Poke Bowls — pdf", "Healthy Poke Bowls — cartaceo"),
          (pdf and pdf["titolo"], carta and carta["titolo"]))
    prova("...il PADRE no", None, uno(wid, 18))
    prova("il PDF e' DIGITALE: niente spedizione ne' ritiro, costi a zero",
          ("digitale", 0.0, 0.0, 0, 0.0, "attivo", 1),
          (pdf["consegna"], pdf["spedizione_eur"], pdf["spedizione_punto_eur"],
           pdf["spedizione_punto_dichiarata"], pdf["spedizione_extra_eur"],
           pdf["stato"], pdf["quantita"]))
    prova("il cartaceo ha la consegna del CASSETTO e, esaurito, e' fuori vetrina",
          ("spedizione", 5.0, "venduto", 0),
          (carta["consegna"], carta["spedizione_eur"], carta["stato"],
           carta["quantita"]))
    prova("...coi prezzi di ciascuna variante", (13.0, 15.9),
          (pdf["prezzo_eur"], carta["prezzo_eur"]))
    prova("...e la foto della variante davanti", True,
          json.loads(pdf["origine_foto"])[0].endswith("pdf.jpg"))
    prova("il corso, oggi fisico sul negozio, entra col cassetto",
          ("spedizione", 5.0), (corso["consegna"], corso["spedizione_eur"]))
    con = SRV.db()
    esito = json.loads(con.execute(
        "SELECT ultimo_esito FROM connettori WHERE id=?", (wid,)
    ).fetchone()[0])
    con.close()
    prova("il report dice CHI e' entrato, coi digitali marcati",
          {("Healthy Poke Bowls — pdf", True, "attivo"),
           ("Healthy Poke Bowls — cartaceo", False, "venduto"),
           ("Lo Yoga dell'Ascolto", False, "attivo")},
          {(e["titolo"], e["digitale"], e["stato"]) for e in esito["entrati"]})
    venditore = [t for chi, t in NOTIFICHE if chi == VENDITORE]
    prova("...e la notifica elenca gli entrati", True,
          bool(venditore) and "Entrati:" in venditore[-1]
          and "💾 digitale" in venditore[-1]
          and "(esaurito, fuori vetrina)" in venditore[-1])

    # (d) IL PREGRESSO SI CORREGGE AL GIRO DOPO: il negozio spunta
    # «Virtuale» sul corso, e da qui non serve nessun gesto
    NOTIFICHE.clear()
    CATALOGO_WOO[-1] = dict(prodotto_woo(19, "Lo Yoga dell'Ascolto", "45.00",
                                         gestito=False), virtual=True)
    giro()
    corso = uno(wid, 19)
    prova("al giro dopo il corso e' digitale, coi costi a zero",
          ("digitale", 0.0, 0.0, 0, 0.0),
          (corso["consegna"], corso["spedizione_eur"],
           corso["spedizione_punto_eur"], corso["spedizione_punto_dichiarata"],
           corso["spedizione_extra_eur"]))
    venditore = [t for chi, t in NOTIFICHE if chi == VENDITORE]
    prova("...e il venditore lo viene a sapere", True,
          bool(venditore) and "con la consegna corretta" in venditore[-1])

    # LA DICHIARAZIONE DEL CASSETTO NON RICOPRE I DIGITALI: un ritocco
    # alla tariffa scende sul cartaceo e lascia stare PDF e corso
    con = SRV.db()
    SRV._applica_dichiarazione(con, wid, {
        "consegna": "entrambe", "spedizione_eur": 7.0,
        "spedizione_punto_eur": 0.0, "spedizione_punto_dichiarata": 0,
        "spedizione_extra_eur": 0.0,
        "spedizione_sats": 0, "spedizione_punto_sats": 0,
        "spedizione_extra_sats": 0, "zona": "Carmagnola (TO)"})
    con.commit()
    con.close()
    prova("il ritocco del cassetto scende sul cartaceo...",
          ("entrambe", 7.0),
          (uno(wid, "18:182")["consegna"], uno(wid, "18:182")["spedizione_eur"]))
    prova("...e NON sul PDF ne' sul corso", ("digitale", 0.0, "digitale", 0.0),
          (uno(wid, "18:181")["consegna"], uno(wid, "18:181")["spedizione_eur"],
           uno(wid, 19)["consegna"], uno(wid, 19)["spedizione_eur"]))
    con = SRV.db()
    SRV._applica_dichiarazione(con, wid, {
        "consegna": "spedizione", "spedizione_eur": 5.0,
        "spedizione_punto_eur": 0.0, "spedizione_punto_dichiarata": 0,
        "spedizione_extra_eur": 0.0,
        "spedizione_sats": 0, "spedizione_punto_sats": 0,
        "spedizione_extra_sats": 0, "zona": "Carmagnola (TO)"})
    con.commit()
    con.close()

    # LA VENDITA DEL PDF: non c'e' un magazzino da scalare, quindi il
    # registro non lo conta e il venditore non riceve «aggiorna il
    # magazzino»; e al giro dopo il PDF e' di nuovo in vetrina
    NOTIFICHE.clear()
    ordine = ordine_pagato(pdf["id"])
    asyncio.run(SRV._incassa_ordine(ordine))
    prova("il PDF venduto e' fuori vetrina, per ora", ("venduto", 0),
          (uno(wid, "18:181")["stato"], uno(wid, "18:181")["quantita"]))
    con = SRV.db()
    uscite = con.execute("SELECT COUNT(*) FROM connettori_uscite "
                         "WHERE annuncio_id=?", (pdf["id"],)).fetchone()[0]
    con.close()
    prova("...il registro NON lo conta: niente da scalare sul negozio", 0,
          uscite)
    venditore = [t for chi, t in NOTIFICHE if chi == VENDITORE]
    prova("...e nessun «aggiorna il magazzino» al venditore", False,
          any("Aggiorna il magazzino" in t for t in venditore))
    giro()
    prova("al giro dopo il PDF e' di nuovo in vetrina", ("attivo", 1),
          (uno(wid, "18:181")["stato"], uno(wid, "18:181")["quantita"]))
    # e il cartaceo che il negozio rifornisce torna come sempre
    VARIAZIONI_WOO[18][1] = variazione_woo(182, "15.90", "cartaceo",
                                           gestito=True, stock=2)
    giro()
    prova("il cartaceo rifornito sul negozio torna in vetrina", ("attivo", 2),
          (uno(wid, "18:182")["stato"], uno(wid, "18:182")["quantita"]))

    # ---- 17. LE FAMIGLIE (set 2026) -----------------------------------
    # IL DIFETTO DAL CAMPO: il negozio AGORA ha 19 prodotti «COWBOY
    # Limited Edition #N/21», ognuno con le sue taglie, e la vetrina si
    # era riempita di magliette gialle uguali. Ogni variante resta il
    # suo annuncio; la famiglia li lega, la vetrina ne mostra UNO.
    print("\n[le famiglie: una card per prodotto, la scelta nella scheda]")
    famiglie_collaudo(wid)

    # ---- 7. il cassetto e i suoi endpoint (tappa 5) -----------------
    print("\n[tappa 5: il cassetto e i suoi endpoint]")
    come(VENDITORE)
    CATALOGO[:] = [prodotto(41, "Sale grosso", "2.00", stock=5)]
    prima = quanti_connettori()

    # SI PROVA PRIMA DI CREDERCI: un token che il negozio rifiuta non
    # deve lasciare in piedi un collegamento «attivo» che non porta
    # niente — e a dirlo, senza questa riga, ci vorrebbero cinque giri
    # dell'orologio.
    esito = errore(SRV.salva_connettore, None, corpo={
        "fonte": "shopify", "url_negozio": "nuovo.myshopify.com",
        "credenziali": {"token": "shpat_sbagliato"},
        "consegna": "spedizione", "spedizione_eur": 5})
    prova("il token sbagliato si rifiuta subito", 400,
          esito and esito[0])
    prova("...col motivo vero (il 401 del negozio)", True,
          bool(esito) and "401" in esito[1])
    prova("...e NON lascia una riga scritta", prima, quanti_connettori())

    # il collegamento vero, dall'endpoint
    fuori = chiama(SRV.salva_connettore, None, corpo={
        "fonte": "shopify", "url_negozio": "HTTPS://Nuovo.MyShopify.com/",
        "credenziali": {"token": "shpat_finto"},
        "consegna": "entrambe", "zona": "Pavia (PV)",
        "spedizione_eur": "4,90", "spedizione_extra_eur": 1.5})
    nid = fuori["connettore"]["id"]
    prova("il collegamento nasce", prima + 1, quanti_connettori())
    prova("...con l'indirizzo normalizzato", "nuovo.myshopify.com",
          fuori["connettore"]["url_negozio"])
    prova("...e la virgola dei decimali si legge", 4.9,
          fuori["connettore"]["spedizione_eur"])
    # LE CREDENZIALI NON ESCONO MAI, ed e' la riga per cui la whitelist
    # in uscita esiste: qui si guarda il JSON VERO che il client
    # riceverebbe, non la forma della funzione
    lista = chiama(SRV.lista_connettori)
    riga = [c for c in lista["connettori"] if c["id"] == nid][0]
    prova("nel JSON non c'e' traccia delle chiavi", [],
          [k for k in riga if "credenzial" in k or "token" in k])
    prova("...e nemmeno nei valori", True,
          "shpat_finto" not in json.dumps(lista))
    # ...ma nel database ci sono, cifrate quanto il config permette
    con = SRV.db()
    blob = con.execute("SELECT credenziali FROM connettori WHERE id=?",
                       (nid,)).fetchone()[0]
    con.close()
    prova("le chiavi sono nel database dietro un prefisso", True,
          blob.startswith("plain:") or blob.startswith("f2:"))

    # IL PRIMO GIRO PARTE SUBITO: chi ha appena visto che il catalogo
    # si legge non deve aspettare l'ora tonda. (Il create_task del
    # collegamento muore col suo loop: qui si chiede lo stesso lavoro
    # a mano, che e' la stessa funzione.)
    asyncio.run(SRV._sync_uno(nid))
    prova("il catalogo entra in vetrina", 1, len(annunci(nid)))
    entrato = annunci(nid)[0]
    prova("...con la consegna dichiarata nel cassetto", "entrambe",
          entrato["consegna"])
    prova("...e la zona del collegamento", "Pavia (PV)", entrato["zona"])

    # LA DICHIARAZIONE SCENDE SULLE RIGHE GIA' ENTRATE, o chi sbaglia
    # la prima volta se la terrebbe addosso per sempre: la Modifica
    # sugli annunci di un connettore e' chiusa apposta.
    chiama(SRV.salva_connettore, None, corpo={
        "id": nid, "fonte": "shopify", "url_negozio": "nuovo.myshopify.com",
        "consegna": "ritiro", "zona": "Carmagnola (TO)"})
    dopo = annunci(nid)[0]
    prova("cambiare la dichiarazione tocca anche il pregresso",
          ("ritiro", "Carmagnola (TO)"), (dopo["consegna"], dopo["zona"]))
    # e la geografia segue la zona, che e' derivata e non chiesta
    prova("...e la geografia la segue", True,
          dopo["lat"] != 0.0 and dopo["regione"] == "Piemonte")
    # LE CHIAVI NON SI RIBATTONO per correggere una tariffa: chiave
    # assente = conserva (il patto dello stock)
    con = SRV.db()
    ancora = con.execute("SELECT credenziali FROM connettori WHERE id=?",
                         (nid,)).fetchone()[0]
    con.close()
    prova("...e le chiavi restano quelle di prima", blob, ancora)

    # LE TARIFFE IN SATS (set 2026): il venditore gira il bottoncino e
    # scrive 7000 sats; sulla riga del collegamento e su TUTTI gli
    # articoli di quel negozio scendono sats FISSI e zeri nell'euro —
    # anche se i prezzi dei prodotti arrivano in euro — e le righe che
    # il giro fa nascere DOPO nascono cosi'. Poi torna all'euro e i sats
    # si azzerano: «fisso batte ancorato» non deve trovare un resto.
    fuori = chiama(SRV.salva_connettore, None, corpo={
        "id": nid, "fonte": "shopify", "url_negozio": "nuovo.myshopify.com",
        "consegna": "spedizione", "tariffe_valuta": "sats",
        "spedizione_sats": "7000", "spedizione_punto_sats": "0",
        "spedizione_extra_sats": 300})
    c_ = fuori["connettore"]
    prova("le tariffe in sats si salvano come sats, con zeri nell'euro",
          ("sats", 7000, 0.0, 0, 1, 300, 0.0),
          (c_["tariffe_valuta"], c_["spedizione_sats"], c_["spedizione_eur"],
           c_["spedizione_punto_sats"], c_["spedizione_punto_dichiarata"],
           c_["spedizione_extra_sats"], c_["spedizione_extra_eur"]))
    dopo = annunci(nid)[0]
    prova("...e scendono sugli articoli gia' in vetrina, fissi",
          (7000, 0.0, 0, 1, 300, 0.0, "eur"),
          (dopo["spedizione_sats"], dopo["spedizione_eur"],
           dopo["spedizione_punto_sats"], dopo["spedizione_punto_dichiarata"],
           dopo["spedizione_extra_sats"], dopo["spedizione_extra_eur"],
           dopo["valuta"]))
    CATALOGO.append(prodotto(42, "Pepe nero", "3.00", stock=2))
    asyncio.run(SRV._sync_uno(nid))
    nato = uno(nid, 42)
    prova("...e le righe che nascono dopo nascono in sats",
          (7000, 0.0, 300, 3.0), (nato["spedizione_sats"],
                                  nato["spedizione_eur"],
                                  nato["spedizione_extra_sats"],
                                  nato["prezzo_eur"]))
    prova("i sats con la virgola si rifiutano, dicendolo", (400, True),
          (lambda e: (e[0], "senza punti" in e[1]))(errore(
              SRV.salva_connettore, None, corpo={
                  "id": nid, "fonte": "shopify",
                  "url_negozio": "nuovo.myshopify.com",
                  "consegna": "spedizione", "tariffe_valuta": "sats",
                  "spedizione_sats": "7.000"})))
    fuori = chiama(SRV.salva_connettore, None, corpo={
        "id": nid, "fonte": "shopify", "url_negozio": "nuovo.myshopify.com",
        "consegna": "spedizione", "tariffe_valuta": "eur",
        "spedizione_eur": "4,90", "spedizione_extra_eur": 1.5})
    dopo = annunci(nid)[0]
    prova("tornando all'euro i sats si azzerano, sulla riga e sugli articoli",
          (("eur", 0, 4.9), (0, 4.9, 0, 1.5)),
          ((fuori["connettore"]["tariffe_valuta"],
            fuori["connettore"]["spedizione_sats"],
            fuori["connettore"]["spedizione_eur"]),
           (dopo["spedizione_sats"], dopo["spedizione_eur"],
            dopo["spedizione_extra_sats"], dopo["spedizione_extra_eur"])))
    CATALOGO.pop()
    # (la riga nata qui se ne va: i casi di sotto contano gli attivi)
    con = SRV.db()
    con.execute("DELETE FROM annunci WHERE id=?", (nato["id"],))
    con.commit()
    con.close()

    # LA RADICE DI UN WOO (set 2026): scritto con la pagina del negozio,
    # dove `/negozio/wp-json/...` e' una pagina 404 del tema (niente
    # codice WordPress), si collega la RADICE e lo si dice; se la radice
    # tace e il percorso risponde, vale il percorso; e i rifiuti dicono
    # se e' l'indirizzo, le chiavi o il sito.
    # (li collega il moderatore: il venditore e' gia' al tetto dei tre)
    come(999)
    prima_woo = quanti_connettori()
    RISPOSTE_WOO["https://untempo.it/negozio/wp-json/"] = (404, {}, {})
    fuori = chiama(SRV.salva_connettore, None, corpo={
        "fonte": "woo", "url_negozio": "https://untempo.it/negozio/",
        "credenziali": {"consumer_key": "ck_x", "consumer_secret": "cs_y"},
        "consegna": "spedizione", "spedizione_eur": 5})
    wid = fuori["connettore"]["id"]
    prova("un Woo scritto con la pagina del negozio si collega alla radice",
          "https://untempo.it", fuori["connettore"]["url_negozio"])
    prova("...e lo dice", True,
          "indirizzo principale del sito" in fuori.get("indirizzo_nota", "")
          and "(https://untempo.it/negozio)" in fuori.get("indirizzo_nota", ""))
    chiama(SRV.scollega_connettore, wid)
    RISPOSTE_WOO["https://sub.it/wp-json/"] = (404, {}, {})
    fuori = chiama(SRV.salva_connettore, None, corpo={
        "fonte": "woo", "url_negozio": "https://sub.it/shop",
        "credenziali": {"consumer_key": "ck_x", "consumer_secret": "cs_y"},
        "consegna": "spedizione", "spedizione_eur": 5})
    prova("...ma se la radice tace vale la sottocartella, senza nota",
          ("https://sub.it/shop", None),
          (fuori["connettore"]["url_negozio"], fuori.get("indirizzo_nota")))
    chiama(SRV.scollega_connettore, fuori["connettore"]["id"])
    RISPOSTE_WOO["https://muto.it/"] = (404, {}, {})
    esito = errore(SRV.salva_connettore, None, corpo={
        "fonte": "woo", "url_negozio": "https://muto.it/negozio",
        "credenziali": {"consumer_key": "ck_x", "consumer_secret": "cs_y"},
        "consegna": "spedizione", "spedizione_eur": 5})
    prova("se tacciono tutt'e due si racconta la radice e il percorso",
          (400, True, True),
          (esito[0], "https://muto.it: a https://muto.it non risponde "
                     "nessun WordPress: controlla l'indirizzo" in esito[1],
           "E nemmeno da https://muto.it/negozio: a https://muto.it/negozio "
           "non risponde nessun WordPress: usa l'indirizzo principale del "
           "sito" in esito[1]))

    def rifiuto_woo(stato, corpo):
        RISPOSTE_WOO["https://woo-r.it/"] = (stato, corpo, {})
        e = errore(SRV.salva_connettore, None, corpo={
            "fonte": "woo", "url_negozio": "https://woo-r.it",
            "credenziali": {"consumer_key": "ck_x", "consumer_secret": "cs_y"},
            "consegna": "spedizione", "spedizione_eur": 5})
        return e[0], e[1]

    e = rifiuto_woo(401, {"code": "woocommerce_rest_authentication_error",
                          "message": "Consumer key is invalid"})
    prova("chiavi sbagliate: si dice di ricontrollarle", (400, True),
          (e[0], "Consumer key e Consumer secret" in e[1]))
    e = rifiuto_woo(403, {"code": "woocommerce_rest_cannot_view",
                          "message": "Sorry, you cannot list resources."})
    prova("chiavi senza permesso di lettura: si dice il permesso", (400, True),
          (e[0], "permesso «Lettura»" in e[1]))
    e = rifiuto_woo(403, {})
    prova("un muro senza codice WordPress: il sito blocca", (400, True),
          (e[0], "blocca le richieste" in e[1]))
    e = rifiuto_woo(404, {"code": "rest_no_route", "message": "No route"})
    prova("WordPress senza WooCommerce: si dice quello", (400, True),
          (e[0], "non WooCommerce" in e[1]))
    prova("...e nessun rifiuto ha lasciato una riga", prima_woo,
          quanti_connettori())
    RISPOSTE_WOO.clear()
    come(VENDITORE)

    # LA PAUSA: il giro non lo guarda piu', ma gli annunci restano
    chiama(SRV.pausa_connettore, nid)
    CATALOGO[:] = []          # sul negozio non c'e' piu' niente
    giro()
    prova("in pausa il catalogo non si rilegge", 1,
          len([a for a in annunci(nid) if a["stato"] == "attivo"]))
    prova("...e il giro a mano si rifiuta", 400,
          (errore(SRV.sincronizza_uno_a_mano, nid) or [None])[0])
    chiama(SRV.pausa_connettore, nid)     # riacceso
    CATALOGO[:] = [prodotto(41, "Sale grosso", "2.00", stock=5)]

    # IL FRENO DEL GIRO A MANO: `ultimo_giro` e' appena stato scritto
    prova("«aggiorna ora» ha un freno", 400,
          (errore(SRV.sincronizza_uno_a_mano, nid) or [None])[0])
    con = SRV.db()
    con.execute("UPDATE connettori SET ultimo_giro=0 WHERE id=?", (nid,))
    con.commit()
    con.close()
    prova("...che si apre col tempo", {"ok": True},
          chiama(SRV.sincronizza_uno_a_mano, nid))

    # UN ESTRANEO NON VEDE E NON TOCCA: la proprieta' sta nella WHERE,
    # e la risposta e' la stessa che darebbe un id inesistente — chi
    # enumera non impara niente.
    come(COMPRATORE)
    prova("un estraneo non vede i collegamenti altrui", [],
          chiama(SRV.lista_connettori)["connettori"])
    suo = errore(SRV.pausa_connettore, nid)
    inesistente = errore(SRV.pausa_connettore, 99999)
    prova("...e «non e' tuo» si racconta come «non esiste»",
          inesistente, suo)
    come(VENDITORE)

    # SCOLLEGARE: la riga se ne va, gli annunci si spengono e il
    # registro delle uscite non resta orfano.
    con = SRV.db()
    con.execute("INSERT INTO connettori_uscite(connettore_id,annuncio_id,"
                "ordine_id,delta,tipo,creato,aggiornato) "
                "VALUES(?,?,?,-1,'vendita',0,0)",
                (nid, annunci(nid)[0]["id"], 777))
    con.commit()
    con.close()
    esito = chiama(SRV.scollega_connettore, nid)
    prova("scollegare spegne gli annunci", 1, esito["spenti"])
    prova("...e la vetrina non ne tiene nessuno", [],
          [a for a in annunci(nid) if a["stato"] != "rimosso"])
    prova("...la riga del collegamento non c'e' piu'", prima,
          quanti_connettori())
    con = SRV.db()
    resti = con.execute("SELECT COUNT(*) AS n FROM connettori_uscite "
                        "WHERE connettore_id=?", (nid,)).fetchone()[0]
    con.close()
    prova("...e il registro non resta orfano", 0, resti)

    # ---- 18. IL ROTTO RIPROVA DA SOLO (18 nov 2026) ------------------
    # I due collegamenti di un negozio vero erano fermi da settimane per
    # qualche timeout di fila: il rotto non riprovava mai, e nessuno se
    # ne accorgeva. Adesso il giro lo rilegge una volta al giorno, e se
    # risponde torna attivo da solo e lo dice al venditore.
    print("\n[il collegamento rotto riprova da solo una volta al giorno]")
    come(VENDITORE)
    CATALOGO_WOO[:] = [prodotto_woo(81, "Adesivo arancione", "3.00",
                                    stock=40)]
    rid = collega(fonte="woo", url="https://rotto.it")

    def rotto(**colonne):
        con = SRV.db()
        sets = ", ".join(f"{k}=?" for k in colonne)
        con.execute(f"UPDATE connettori SET {sets} WHERE id=?",
                    (*colonne.values(), rid))
        con.commit()
        con.close()

    def riga_rotto():
        con = SRV.db()
        r = con.execute("SELECT stato, errori_di_fila, ultimo_giro "
                        "FROM connettori WHERE id=?", (rid,)).fetchone()
        con.close()
        return tuple(r)

    ieri = int(time.time()) - SRV.CONNETTORI_RIPROVA_ERRORE_S - 3600
    rotto(stato="errore", errori_di_fila=5, ultimo_giro=int(time.time()))
    quante = len(NOTIFICHE)
    giro()
    prova("rotto da meno di un giorno: il giro non lo tocca",
          ("errore", 5, []), (*riga_rotto()[:2], annunci(rid)))
    rotto(ultimo_giro=ieri)
    ERRORE_API[0] = "timed out"
    giro()
    ERRORE_API[0] = None
    r = riga_rotto()
    prova("dopo un giorno riprova; se tace resta rotto e conta",
          ("errore", 6), r[:2])
    prova("...e il prossimo tentativo e' fra un giorno", True,
          r[2] > ieri)
    # (il Woo di prima, attivo, conta i suoi errori per conto suo: qui
    # si guarda solo quel che il giro scrive di QUESTO negozio)
    prova("...senza riscrivere al venditore ogni giorno", [],
          [x for _, x in NOTIFICHE[quante:] if "rotto.it" in x])
    rotto(ultimo_giro=ieri)
    giro()
    prova("se il sito risponde torna attivo, col conto azzerato",
          ("attivo", 0), riga_rotto()[:2])
    prova("...e il catalogo entra", ["Adesivo arancione"],
          [a["titolo"] for a in annunci(rid) if a["stato"] == "attivo"])
    prova("...e il venditore sa che e' ripartito", True,
          any(t == VENDITORE and "risponde di nuovo" in x
              for t, x in NOTIFICHE[quante:]))
    # il primo avviso promette la riprova: e' vero da oggi, quindi lo dice
    rotto(errori_di_fila=SRV.CONNETTORI_ERRORI_MAX - 1)
    ERRORE_API[0] = "timed out"
    giro()
    ERRORE_API[0] = None
    avviso = ([x for t, x in NOTIFICHE[quante:] if "non risponde" in x
               and "rotto.it" in x] or [""])[-1]
    prova("l'avviso del collegamento fermo dice che riprovo da solo",
          ("errore", True), (riga_rotto()[0],
                             "una volta al giorno" in avviso))
    # IN PAUSA NON RIPROVA: il gesto del venditore vince sull'orologio
    rotto(stato="pausa", ultimo_giro=ieri)
    giro()
    prova("in pausa non si riprova mai", ("pausa", ieri),
          (riga_rotto()[0], riga_rotto()[2]))

    print("\n[lo stesso negozio con altre maiuscole e' un doppione]")
    come(999)     # il moderatore vede la sezione e non ha negozi suoi
    esito = errore(SRV.salva_connettore, None, corpo={
        "fonte": "woo", "url_negozio": "https://ROTTO.it",
        "credenziali": {"consumer_key": "ck_x", "consumer_secret": "cs_y"},
        "consegna": "spedizione", "spedizione_eur": 5})
    prova("«ROTTO.it» quando c'e' «rotto.it»: si rifiuta", (400, True),
          (esito and esito[0], bool(esito) and "già collegato" in esito[1]))
    con = SRV.db()
    try:
        con.execute("INSERT INTO connettori(tg_id,fonte,url_negozio,"
                    "credenziali) VALUES(999,'woo','https://Rotto.IT','x')")
        doppio = "entrato"
    except sqlite3.IntegrityError:
        doppio = "rifiutato"
    con.close()
    prova("...e lo rifiuta il database stesso, non solo l'endpoint",
          "rifiutato", doppio)
    # IL DATABASE DI IERI, coi doppioni gia' dentro e l'indice che non
    # puo' nascere: la cintura dell'endpoint tiene, e del negozio si
    # riprova solo la riga piu' giovane
    con = SRV.db()
    con.execute("DROP INDEX idx_connettori_url_senza_maiuscole")
    cur = con.execute(
        "INSERT INTO connettori(tg_id,fonte,url_negozio,credenziali,"
        "consegna,spedizione_eur,zona,creato,stato,ultimo_giro) "
        "VALUES(?,?,?,?,?,?,?,?,'errore',?)",
        (VENDITORE, "woo", "https://ROTTO.it",
         SRV._cifra_contenuto(json.dumps({"consumer_key": "ck",
                                          "consumer_secret": "cs"})),
         "spedizione", 5.0, "Carmagnola (TO)", int(time.time()), ieri))
    giovane = cur.lastrowid
    con.commit()
    con.close()
    rotto(stato="errore", ultimo_giro=ieri)
    giro()
    con = SRV.db()
    stati = {r[0]: r[1] for r in con.execute(
        "SELECT id, stato FROM connettori WHERE id IN (?,?)",
        (rid, giovane))}
    con.close()
    prova("doppioni di ieri: riparte solo il piu' giovane",
          {rid: "errore", giovane: "attivo"}, stati)
    esito = errore(SRV.salva_connettore, None, corpo={
        "fonte": "woo", "url_negozio": "https://Rotto.it",
        "credenziali": {"consumer_key": "ck_x", "consumer_secret": "cs_y"},
        "consegna": "spedizione", "spedizione_eur": 5})
    prova("...e senza indice la cintura dell'endpoint rifiuta lo stesso",
          (400, True),
          (esito and esito[0], bool(esito) and "già collegato" in esito[1]))
    SRV.init_db()
    prova("all'avvio, coi doppioni dentro, l'indice non nasce e "
          "nessuno cade", True, True)
    come(VENDITORE)

    print("\n" + "=" * 62)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 62)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
