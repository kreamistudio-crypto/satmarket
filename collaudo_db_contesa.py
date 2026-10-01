# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL DATABASE CONTESO (1 ott 2026, «database is locked»).

Alle 16:40 UTC il giro del negozio «STACKER NEWS» ha tenuto il lucchetto
di scrittura di sqlite per minuti — le foto si scaricavano DENTRO la
transazione della riga nuova — e ogni rotta che scriveva moriva con
«database is locked» dopo i 5 secondi del timeout di Python. Dalla
cura 8 la riconciliazione gira in un thread, quindi le rotte scrivono
mentre gira: e' il giorno in cui la transazione lunga ha smesso di
essere invisibile.

`prove.py` gira la riconciliazione da sola. Qui gira il SERVER VERO —
`sincronizza_connettori`, il thread, `db()` — su un database usa-e-
getta, con un negozio di cartone e uno scaricatore di foto LENTO, e si
chiedono le cose che solo l'esecuzione dice:

  · MENTRE il giro scarica, una «rotta» impaziente (db() con un timeout
    di 0,2 s) scrive decine di volte e non muore mai;
  · db() ASPETTA davvero: un lucchetto tenuto per un secondo da un
    altro thread non fa morire la scrittura, mentre una connessione
    senza pazienza muore subito (la prova che il timeout e' applicato);
  · UN NEGOZIO GRANDE: mille prodotti Woo, trecento dei quali con
    cinque varianti (2.200 righe), per MISURARE quanto dura un giro, con
    quante chiamate all'AI, quante righe entrano, e se le rotte scrivono
    nel frattempo. Si gira col tetto di lettura di oggi (200) e con il
    tetto alzato a mille, e i numeri si stampano: servono alla domanda
    di Andrea sul tetto dei 30 nuovi a giro.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, le foto non si scaricano (si dorme al posto del
download), l'AI si conta e non si chiama.

USO:  python collaudo_db_contesa.py
"""

import asyncio
import json
import os
import re
import sqlite3
import sys
import tempfile
import threading
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
VENDITORE = 222
CAMBIO = 100_000.0           # 1000 sats = 1 €


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


# --- IL WOOCOMMERCE DI CARTONE, CON LE PAGINE VERE ---------------------
# A differenza di collaudo_connettori qui le pagine contano: mille
# prodotti sono dieci pagine da cento, e il lettore si ferma al tetto.
CATALOGO_WOO = []
VARIAZIONI_WOO = {}
LETTURE = []
DORMI_FOTO = [0.0]            # quanto dorme lo scaricatore di cartone
CHIAMATE_AI = []


def prodotto_woo(pid, nome, tipo="simple", foto=2):
    return {"id": pid, "name": nome, "description": f"<p>Descrizione {pid}</p>",
            "type": tipo, "status": "publish", "catalog_visibility": "visible",
            "price": "7.50", "regular_price": "7.50", "manage_stock": True,
            "stock_quantity": 12, "stock_status": "instock",
            "images": [{"src": f"https://cdn.esempio/{pid}-{k}.jpg"}
                       for k in range(foto)],
            "categories": [{"id": 1, "name": "Casa"}]}


def variazione_woo(vid, opzione):
    return {"id": vid, "price": "7.50", "regular_price": "7.50",
            "status": "publish", "manage_stock": True, "stock_quantity": 3,
            "stock_status": "instock", "virtual": False, "downloadable": False,
            "attributes": [{"id": 0, "name": "Taglia", "option": opzione}],
            "image": None}


def api_finta(metodo, url, intestazioni):
    LETTURE.append(url)
    if url.endswith("/settings/general"):
        return 200, {"lista": [{"id": "woocommerce_calc_taxes", "value": "yes"}]}, {}
    if url.endswith("/settings/tax"):
        return 200, {"lista": [{"id": "woocommerce_prices_include_tax", "value": "yes"}]}, {}
    m = re.search(r"/products/(\d+)/variations.*?[?&]page=(\d+)", url)
    if m:
        lista = VARIAZIONI_WOO.get(int(m.group(1)), [])
        return 200, {"lista": lista if int(m.group(2)) == 1 else []}, {}
    per_pagina = int(re.search(r"per_page=(\d+)", url).group(1))
    pagina = int(re.search(r"[?&]page=(\d+)", url).group(1))   # non il per_page
    fetta = CATALOGO_WOO[(pagina - 1) * per_pagina: pagina * per_pagina]
    return 200, {"lista": fetta}, {"X-WP-Total": str(len(CATALOGO_WOO))}


def avvio():
    """Il config finto PRIMA di importare server."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-contesa-"), "usa-e-getta.db")
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

    # lo scaricatore LENTO: non scarica, dorme quanto dormirebbe un
    # download vero (fino a 10 s l'uno sul server) e annota il nome
    def foto_lenta(annuncio_id, indice, url):
        if DORMI_FOTO[0]:
            time.sleep(DORMI_FOTO[0])
        return f"a{annuncio_id}_{indice}.jpg"
    server._salva_foto_connettore = foto_lenta
    server.cambio_per_import = lambda: {"EUR": CAMBIO, "USD": CAMBIO}

    async def lotto_finto(voci):
        CHIAMATE_AI.append(len(voci))
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


def collega(url="https://negozio.esempio"):
    con = SRV.db()
    cur = con.execute(
        "INSERT INTO connettori(tg_id,fonte,url_negozio,credenziali,"
        "consegna,spedizione_eur,zona,creato) VALUES(?,?,?,?,?,?,?,?)",
        (VENDITORE, "woo", url,
         SRV._cifra_contenuto(json.dumps({"consumer_key": "ck_finta",
                                          "consumer_secret": "cs_finta"})),
         "spedizione", 5.0, "Carmagnola (TO)", int(time.time())))
    con.commit()
    cid = cur.lastrowid
    con.close()
    return cid


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


async def giro_con_le_rotte(ogni=0.02):
    """Un giro di sync come lo farebbe l'orologio, e nel frattempo il
    ciclo principale scrive ogni `ogni` secondi. Torna (secondi, conto)."""
    SRV._prossimo_giro_connettori = 0.0
    conto = {"ok": 0, "locked": 0, "altro": []}
    finito = False

    async def rotte():
        while not finito:
            e = scrivi_come_una_rotta()
            if e == "ok":
                conto["ok"] += 1
            elif e == "locked":
                conto["locked"] += 1
            else:
                conto["altro"].append(e)
            await asyncio.sleep(ogni)

    inizio = time.time()
    compito = asyncio.create_task(rotte())
    await SRV.sincronizza_connettori()
    finito = True
    await compito
    return time.time() - inizio, conto


def annunci(cid):
    con = SRV.db()
    righe = [dict(r) for r in con.execute(
        "SELECT * FROM annunci WHERE connettore_id=? ORDER BY id", (cid,))]
    con.close()
    return righe


def esito_giro(cid):
    con = SRV.db()
    r = con.execute("SELECT ultimo_esito FROM connettori WHERE id=?", (cid,)).fetchone()
    con.close()
    return json.loads(r[0] or "{}")


def main():
    db = avvio()
    print("=" * 62)
    print("  IL DATABASE CONTESO: il giro dei negozi e le rotte")
    print("=" * 62)

    # --- 1) il giro conteso: foto lente, rotte impazienti ----------------
    print("\n[1. le foto lente non chiudono il database alle rotte]")
    CATALOGO_WOO[:] = [prodotto_woo(k, f"Cosa {k}") for k in range(1, 13)]
    DORMI_FOTO[0] = 0.15                 # 12 righe × 2 foto × 0,15 s ≈ 3,6 s di download
    cid = collega()
    pazienza_vera = SRV.DB_BUSY_TIMEOUT
    SRV.DB_BUSY_TIMEOUT = 0.2            # la rotta impaziente: muore se aspetta piu' di 0,2 s
    try:
        secondi, conto = asyncio.run(giro_con_le_rotte())
    finally:
        SRV.DB_BUSY_TIMEOUT = pazienza_vera
    nati = annunci(cid)
    prova("il giro ha portato le dodici righe in vetrina", 12,
          len([a for a in nati if a["stato"] == "attivo"]))
    prova("...coi nomi locali delle foto (il secondo commit c'e' stato)", True,
          all(json.loads(a["foto"]) == [f"a{a['id']}_0.jpg", f"a{a['id']}_1.jpg"] for a in nati))
    prova("il giro e' durato quanto le foto (non c'e' stato un blocco a monte)", True,
          3.0 <= secondi < 12.0)
    prova("...e le rotte hanno scritto davvero nel frattempo (decine di volte)", True,
          conto["ok"] >= 40)
    prova("...senza MAI un «database is locked» (ieri: una morte ogni 0,2 s)", (0, []),
          (conto["locked"], conto["altro"]))
    print(f"    giro: {secondi:.1f} s, rotte: {conto['ok']} scritture ok")

    # --- 2) db() aspetta davvero -------------------------------------------
    print("\n[2. la pazienza di db(): un lucchetto tenuto un secondo]")
    prova("il timeout dichiarato e' di 15 secondi (il config del VPS vince)", 15,
          SRV.DB_BUSY_TIMEOUT)
    preso = threading.Event()

    def tieni_il_lucchetto():
        c = sqlite3.connect(db)
        c.execute("BEGIN IMMEDIATE")
        c.execute("UPDATE timbri SET valore='tenuto' WHERE nome='p2p_libro_visto'")
        preso.set()
        time.sleep(1.0)
        c.commit()
        c.close()

    t = threading.Thread(target=tieni_il_lucchetto)
    t.start()
    preso.wait(5)
    impaziente = sqlite3.connect(db, timeout=0)
    try:
        impaziente.execute("UPDATE timbri SET valore='x' WHERE nome='p2p_libro_visto'")
        impaziente.commit()
        senza_pazienza = "ok"
    except sqlite3.OperationalError as e:
        senza_pazienza = "locked" if "locked" in str(e) else str(e)
    impaziente.close()
    inizio = time.time()
    esito = scrivi_come_una_rotta()
    attesa = time.time() - inizio
    t.join()
    prova("una connessione senza pazienza muore subito (il lucchetto era preso davvero)",
          "locked", senza_pazienza)
    prova("...db() invece aspetta e scrive", "ok", esito)
    prova("...dopo circa un secondo, non dopo quindici", True, 0.5 <= attesa < 5.0)
    print(f"    attesa di db(): {attesa:.2f} s")

    # --- 3) il negozio grande ------------------------------------------------
    print("\n[3. il negozio grande: mille prodotti, 2.200 righe]")
    DORMI_FOTO[0] = 0.0
    CATALOGO_WOO[:] = []
    VARIAZIONI_WOO.clear()
    for k in range(1, 1001):
        if k % 10 < 3:          # trecento variabili con cinque taglie
            CATALOGO_WOO.append(prodotto_woo(k, f"Maglia {k}", tipo="variable"))
            VARIAZIONI_WOO[k] = [variazione_woo(k * 10 + j, t)
                                 for j, t in enumerate(("XS", "S", "M", "L", "XL"))]
        else:
            CATALOGO_WOO.append(prodotto_woo(k, f"Cosa {k}"))
    # il primo collegamento non si rilegge: gli diamo un url suo
    con = SRV.db()
    con.execute("UPDATE connettori SET stato='pausa' WHERE id=?", (cid,))
    con.commit()
    con.close()
    grande = collega("https://grande.esempio")

    def un_giro(etichetta):
        CHIAMATE_AI.clear()
        LETTURE.clear()
        secondi, conto = asyncio.run(giro_con_le_rotte())
        e = esito_giro(grande)
        vivi = len([a for a in annunci(grande) if a["stato"] == "attivo"])
        print(f"    {etichetta}: {secondi:.1f} s, {len(LETTURE)} chiamate al negozio, "
              f"{len(CHIAMATE_AI)} lotti AI ({sum(CHIAMATE_AI)} righe giudicate), "
              f"{e.get('nuovi')} nuovi, {e.get('rimandati')} rimandati, "
              f"parziale={e.get('parziale')}, in vetrina {vivi}; "
              f"rotte ok {conto['ok']}, locked {conto['locked']}")
        return secondi, conto, e, vivi

    # a) col tetto di lettura di oggi: 200 prodotti letti, il resto mai
    tetto_oggi = SRV.MAX_PRODOTTI_CONNETTORE
    prova("il tetto di lettura di oggi e' 200 prodotti", 200, tetto_oggi)
    s1, c1, e1, v1 = un_giro("giro 1 (tetto 200)")
    prova("col tetto di oggi il giro legge 200 prodotti e lo dice (parziale)", True,
          e1.get("parziale") is True)
    prova("...entrano 30 righe", 30, e1.get("nuovi"))
    # 200 prodotti letti, 60 dei quali variabili con cinque taglie: 440 righe
    prova("...le altre lette (200 prodotti → 440 righe) aspettano", 410, e1.get("rimandati"))
    prova("...l'AI ha giudicato TUTTE le 440 righe lette, non le 30 che entrano", 440,
          sum(CHIAMATE_AI))
    # il giro dura mezzo secondo e le rotte hanno poche occasioni: quel che
    # conta e' che nessuna muoia
    prova("...e le rotte hanno scritto senza morire", (True, 0), (c1["ok"] >= 1, c1["locked"]))
    s2, c2, e2, v2 = un_giro("giro 2 (tetto 200)")
    prova("al secondo giro altre 30, e l'AI rigiudica le rimandate", (30, True),
          (e2.get("nuovi"), sum(CHIAMATE_AI) >= 200))
    prova("...il giro resta breve (secondi, non minuti)", True, s2 < 20)

    # b) col tetto alzato a mille: tutto letto, 2.200 righe
    SRV.MAX_PRODOTTI_CONNETTORE = 1000
    try:
        s3, c3, e3, v3 = un_giro("giro 3 (tetto 1000)")
        prova("col tetto a mille il catalogo si legge intero", False, e3.get("parziale"))
        prova("...2.200 righe: 30 entrano, il resto rimandato", (30, 2200 - 60 - 30),
              (e3.get("nuovi"), e3.get("rimandati")))
        prova("...l'AI giudica le 2.140 mai viste in un giro solo", True,
              sum(CHIAMATE_AI) >= 2100)
        prova("...le rotte scrivono anche sotto il giro grande", (True, 0),
              (c3["ok"] >= 1, c3["locked"]))
        prova("...e il giro grande dura secondi", True, s3 < 60)
        # il quarto giro: quanto costa un giro «di regime» su 2.200 righe
        s4, c4, e4, v4 = un_giro("giro 4 (tetto 1000)")
        prova("ogni giro va avanti di 30", 30, e4.get("nuovi"))
        prova("...e un giro di regime su 2.200 righe non blocca le rotte", 0, c4["locked"])
    finally:
        SRV.MAX_PRODOTTI_CONNETTORE = tetto_oggi

    print("\n" + "=" * 62)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 62)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
