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

  · MENTRE il giro scarica, dentro OGNI scaricamento un'altra connessione
    scrive — e ci riesce sempre: se il giro tenesse il lucchetto attorno
    alle foto non ci riuscirebbe mai, perche' il giro e' fermo li' ad
    aspettarla — e intanto le «rotte» del ciclo principale scrivono e non
    muoiono;
  · db() ASPETTA davvero: un lucchetto tenuto da un altro thread non fa
    morire la scrittura, mentre una connessione senza pazienza muore
    subito (la prova che il timeout e' applicato).

STABILE IN CI (1 ott 2026, sera, decisione di Andrea: «cade a volte su
una prova a tempo, in locale passa sempre»). Le prove che dipendevano
dall'OROLOGIO sono diventate prove che dipendono dall'ORDINE:
  · la «rotta impaziente» da 0,2 s non c'e' piu': contro le transazioni a
    raffica del giro moriva per fame di lucchetto (sqlite non fa la fila,
    vedi RESPIRO_MAX_S in importa_negozio), cioe' secondo il disco della
    macchina e non secondo il codice. Al suo posto la SONDA dentro lo
    scaricatore, che non dipende da nessun tempo, e le rotte con due
    secondi di pazienza;
  · «almeno quaranta scritture» contava quanto e' veloce il disco della
    CI: adesso basta che le rotte abbiano scritto, e non siano morte;
  · «dopo circa un secondo» cronometrava un thread: adesso il lucchetto
    si tiene finche' la connessione impaziente non ha provato (un
    Event, non un sonno), e si guarda che db() abbia finito DOPO il
    rilascio e molto prima dei quindici secondi.
Il negozio grande (mille prodotti) che stava qui in fondo e' passato a
`collaudo_negozi_grandi`, coi numeri delle decisioni dello stesso giorno.

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
# la pazienza delle rotte del collaudo: in produzione e' quindici secondi
# (DB_BUSY_TIMEOUT); qui due, che sono cento volte un commit e restano un
# tempo che un lucchetto tenuto attorno alle foto supererebbe
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


# --- IL WOOCOMMERCE DI CARTONE, CON LE PAGINE VERE ---------------------
CATALOGO_WOO = []
VARIAZIONI_WOO = {}
LETTURE = []
DORMI_FOTO = [0.0]            # quanto dorme lo scaricatore di cartone
CHIAMATE_AI = []
SONDE = []                    # l'esito della scrittura fatta DENTRO ogni download
DB_PERCORSO = [""]


def prodotto_woo(pid, nome, tipo="simple", foto=2):
    return {"id": pid, "name": nome, "description": f"<p>Descrizione {pid}</p>",
            "type": tipo, "status": "publish", "catalog_visibility": "visible",
            "price": "7.50", "regular_price": "7.50", "manage_stock": True,
            "stock_quantity": 12, "stock_status": "instock",
            "images": [{"src": f"https://cdn.esempio/{pid}-{k}.jpg"}
                       for k in range(foto)],
            "categories": [{"id": 1, "name": "Casa"}]}


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


def sonda():
    """Una scrittura con una connessione SUA, fatta dal thread del giro
    mentre «scarica» una foto. Il giro e' fermo qui dentro ad aspettarla:
    se la sua connessione avesse una transazione aperta (il guasto del 1
    ott), nessuno potrebbe chiuderla e la sonda morirebbe dopo la sua
    pazienza. Non dipende da nessun orologio: o il lucchetto e' libero,
    o non lo sara' mai."""
    c = sqlite3.connect(DB_PERCORSO[0], timeout=PAZIENZA_S)
    try:
        c.execute("INSERT OR REPLACE INTO timbri(nome, valore, quando) "
                  "VALUES('sonda_del_giro', '1', ?)", (int(time.time()),))
        c.commit()
        return "ok"
    except sqlite3.OperationalError as e:
        return "locked" if "locked" in str(e) else str(e)
    finally:
        c.close()


def avvio():
    """Il config finto PRIMA di importare server."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-contesa-"), "usa-e-getta.db")
    DB_PERCORSO[0] = db
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
    # download vero (fino a 10 s l'uno sul server) e annota il nome —
    # e PRIMA di dormire fa la sua sonda (vedi `sonda`)
    def foto_lenta(annuncio_id, indice, url):
        if DORMI_FOTO[0]:
            SONDE.append(sonda())
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
    conto = {"ok": 0, "locked": 0, "altro": [], "attese": []}
    finito = False

    async def rotte():
        while not finito:
            t0 = time.perf_counter()
            e = scrivi_come_una_rotta()
            conto["attese"].append(time.perf_counter() - t0)
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


def main():
    db = avvio()
    print("=" * 62)
    print("  IL DATABASE CONTESO: il giro dei negozi e le rotte")
    print("=" * 62)

    # --- 1) il giro conteso: foto lente, rotte che scrivono --------------
    print("\n[1. le foto lente non chiudono il database alle rotte]")
    CATALOGO_WOO[:] = [prodotto_woo(k, f"Cosa {k}") for k in range(1, 13)]
    DORMI_FOTO[0] = 0.15                 # 12 righe × 2 foto × 0,15 s ≈ 3,6 s di download
    SONDE.clear()
    cid = collega()
    pazienza_vera = SRV.DB_BUSY_TIMEOUT
    SRV.DB_BUSY_TIMEOUT = PAZIENZA_S
    try:
        secondi, conto = asyncio.run(giro_con_le_rotte())
    finally:
        SRV.DB_BUSY_TIMEOUT = pazienza_vera
    nati = annunci(cid)
    print(f"    giro: {secondi:.1f} s, sonde: {len(SONDE)}, rotte: {conto['ok']} "
          f"scritture ok, la piu' lunga attesa di una rotta "
          f"{max(conto['attese'] or [0]):.2f} s")
    prova("il giro ha portato le dodici righe in vetrina", 12,
          len([a for a in nati if a["stato"] == "attivo"]))
    prova("...coi nomi locali delle foto (il secondo commit c'e' stato)", True,
          all(json.loads(a["foto"]) == [f"a{a['id']}_0.jpg", f"a{a['id']}_1.jpg"] for a in nati))
    # LA PROVA CHE NON DIPENDE DALL'OROLOGIO (vedi `sonda`)
    prova("durante OGNI download un'altra connessione scrive: ventiquattro su ventiquattro",
          ["ok"] * 24, SONDE)
    prova("il giro e' durato almeno quanto le foto, e non e' rimasto appeso", True,
          3.0 <= secondi < 60.0)
    prova("...le rotte hanno scritto davvero nel frattempo", True, conto["ok"] >= 5)
    prova("...e con due secondi di pazienza non e' morta nessuna", (0, []),
          (conto["locked"], conto["altro"]))

    # --- 2) db() aspetta davvero -------------------------------------------
    print("\n[2. la pazienza di db(): un lucchetto tenuto da un altro thread]")
    prova("il timeout dichiarato e' di 15 secondi (il config del VPS vince)", 15,
          SRV.DB_BUSY_TIMEOUT)
    preso, provato = threading.Event(), threading.Event()
    tempi = {}

    def tieni_il_lucchetto():
        c = sqlite3.connect(db)
        c.execute("BEGIN IMMEDIATE")
        c.execute("UPDATE timbri SET valore='tenuto' WHERE nome='p2p_libro_visto'")
        preso.set()
        # il lucchetto si tiene finche' l'impaziente NON HA PROVATO (un
        # Event, non un sonno: era il cronometro a cadere in CI), poi
        # ancora mezzo secondo, perche' db() lo trovi preso e aspetti
        provato.wait(10)
        time.sleep(0.5)
        tempi["rilascio"] = time.monotonic()      # preso fino a qui, e oltre
        c.commit()
        c.close()

    t = threading.Thread(target=tieni_il_lucchetto)
    t.start()
    preso.wait(10)
    impaziente = sqlite3.connect(db, timeout=0)
    try:
        impaziente.execute("UPDATE timbri SET valore='x' WHERE nome='p2p_libro_visto'")
        impaziente.commit()
        senza_pazienza = "ok"
    except sqlite3.OperationalError as e:
        senza_pazienza = "locked" if "locked" in str(e) else str(e)
    impaziente.close()
    provato.set()
    inizio = time.monotonic()
    esito = scrivi_come_una_rotta()
    fatto = time.monotonic()
    t.join(30)
    print(f"    attesa di db(): {fatto - inizio:.2f} s")
    prova("una connessione senza pazienza muore subito (il lucchetto era preso davvero)",
          "locked", senza_pazienza)
    prova("...db() invece aspetta e scrive", "ok", esito)
    # L'ORDINE, NON IL CRONOMETRO: la scrittura di db() non puo' finire
    # prima che il lucchetto si liberi, e finisce molto prima dei quindici
    # secondi della sua pazienza
    prova("...e ha finito DOPO il rilascio del lucchetto, molto prima dei quindici secondi",
          True, "rilascio" in tempi and tempi["rilascio"] <= fatto < tempi["rilascio"] + 10)

    # --- 3) il negozio grande ------------------------------------------------
    # passato a `collaudo_negozi_grandi` (1 ott 2026, sera): coi numeri delle
    # decisioni dello stesso giorno — mille prodotti letti, il rodaggio, l'AI
    # che giudica solo cio' che entra — e col traffico vero della app
    print("\n[3. il negozio grande: in collaudo_negozi_grandi]")

    print("\n" + "=" * 62)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 62)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
