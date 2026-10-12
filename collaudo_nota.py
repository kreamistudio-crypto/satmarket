# -*- coding: utf-8 -*-
"""LA NOTA DEL COMPRATORE, fatta girare per davvero (ago 2026).

`prove.py` difende la FORMA e fa girare i pezzi (il giudice,
l'endpoint, la coda) su un database di cartone. Qui gira il SERVER
VERO, su un database usa-e-getta, e si chiedono le tre cose che solo
la filiera intera puo' dire:

  · la nota scritta alla cassa arriva IN COLONNA, su tutte le vie —
    spedizione, punto, ritiro a mano, codice online;
  · esce da /api/orders a TUTTE E TRE le parti, moderatore compreso:
    e' l'unica cosa scritta dal compratore che un moderatore legge, e
    la pagina «I tuoi dati» lo dichiara — se un domani un pop la
    togliesse, quella pagina direbbe il falso;
  · LA RIPRESA: due «Paga» di fila con la nota cambiata in mezzo
    devono dare LA STESSA FATTURA e la nota NUOVA. E' il caso che la
    guardia sbagliata (`if nota and ...`, copiata dall'indirizzo)
    romperebbe in silenzio.

Piu' la REGRESSIONE, che e' meta' del valore: senza nota l'ordine
nasce identico a prima, byte per byte.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. LNbits non
viene mai chiamato — le invoice si contano, non si chiedono — quindi
lo script gira anche senza rete e senza chiavi.

USO:  python collaudo_nota.py
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
INVOICES = []
AVVISI = []

COMPRA = {"id": 111, "nome": "Compra", "username": "compra", "admin": False}
VENDE = {"id": 222, "nome": "Vende", "username": "vende", "admin": False}
ADMIN = {"id": 999, "nome": "Admin", "username": "admin", "admin": True}


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def alza(nome, fn, dentro=""):
    global PASSATE, FALLITE
    try:
        fn()
    except Exception as e:
        codice = getattr(e, "status_code", None)
        testo = str(getattr(e, "detail", e))
        if codice == 400 and (not dentro or dentro.lower() in testo.lower()):
            PASSATE += 1
            print(f"  ✓ {nome}")
            return
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso 400 con {dentro!r}"
              f"\n      avuto:  {codice} {testo!r}")
        return
    FALLITE += 1
    print(f"  ✗ {nome}\n      atteso un rifiuto, non e' arrivato")


def avvio():
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-nota-"),
                      "usa-e-getta.db")
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
    cfg.PROTEZIONE_PERCENTO = 0
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def invoice_finta(sats, memo, expiry=None, cassaforte=""):
        INVOICES.append(int(sats))
        return {"payment_hash": f"hash{len(INVOICES)}",
                "payment_request": f"lnbc{sats}collaudo{len(INVOICES)}"}

    async def cambio_finto():
        return 100_000.0

    async def zitta(chi=None, testo="", *a, **k):
        AVVISI.append((chi, testo))
        return None

    async def mai_pagata(_hash, _cassaforte=""):
        return False

    server.crea_invoice_escrow = invoice_finta
    server.invoice_pagata = mai_pagata
    server.cambio_btc_eur = cambio_finto
    server.notifica = zitta
    server.polso_ordini_admin = lambda *a, **k: None
    return db


def chi(u):
    SRV.verifica_utente = lambda *a, **k: u


def compra(corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(SRV.compra(None))


def endpoint(fn, oid, corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(fn(oid, None))


def semina(db):
    con = sqlite3.connect(db)
    # il venditore DICHIARA InPost: dal 12 ott 2026 (cantiere
    # «punti-ritiro») senza un corriere che consegna a una rete di
    # punti la via punto non si offre, e la nota qui si prova su
    # TUTTE le vie
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,negozio,"
                "spedizionieri,spedizioniere) "
                "VALUES(222,'Vende','vende','negozio22','|InPost|','InPost')")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,negozio) "
                "VALUES(111,'Compra','compra','negozio11')")
    # quattro annunci, uno per strada: la nota non dipende dalla via, ed
    # e' precisamente quello che si vuole vedere
    for aid, consegna, extra in ((1, "spedizione", ""), (2, "spedizione", ""),
                                 (3, "ritiro", ""), (4, "digitale", "")):
        con.execute(
            "INSERT OR REPLACE INTO annunci(id,titolo,descrizione,prezzo_sats,"
            "venditore_id,stato,categoria,quantita,consegna,zona,valuta) "
            "VALUES(?,?,'x',50000,222,'attivo','Altro',5,?,'Pavia (PV)','sats')",
            (aid, f"Cosa {aid}", consegna))
    con.commit()
    con.close()


def main():
    print("=" * 58)
    print("  LA NOTA DEL COMPRATORE — il giro vero")
    print("=" * 58)
    db = avvio()
    semina(db)
    vero = sqlite3.connect(db)
    vero.row_factory = sqlite3.Row

    def leggi_col(oid):
        return vero.execute("SELECT nota_compratore FROM ordini WHERE id=?",
                            (oid,)).fetchone()[0]

    # ---- 1. la nota arriva in colonna, su TUTTE le vie -------------
    print("\n[la nota arriva in colonna, qualunque sia la strada]")
    chi(COMPRA)
    casi = ((1, {"annuncio_id": 1, "quantita": 1, "consegna": "spedizione",
                 "spedizione_via": "casa",
                 "indirizzo": {"nome": "Mario Rossi", "via": "Via Roma 1",
                               "cap": "27100", "citta": "Pavia"},
                 "nota_compratore": "taglia L"}, "casa"),
            (2, {"annuncio_id": 2, "quantita": 1, "consegna": "spedizione",
                 "spedizione_via": "punto", "punto_ritiro": "Via Roma 1",
                 "tipo_punto": "locker",
                 "nota_compratore": "numero 42"}, "punto"),
            (3, {"annuncio_id": 3, "quantita": 1, "consegna": "ritiro",
                 "nota_compratore": "la variante blu"}, "ritiro"),
            (4, {"annuncio_id": 4, "quantita": 1, "consegna": "digitale",
                 "nota_compratore": "mandalo in maiuscolo"}, "digitale"))
    ordini = {}
    for aid, corpo, come in casi:
        r = compra(corpo)
        ordini[come] = r["ordine_id"]
        prova(f"via «{come}»: la nota e' nella risposta",
              corpo["nota_compratore"], r["nota_compratore"])
        prova(f"via «{come}»: ...e in colonna",
              corpo["nota_compratore"], leggi_col(r["ordine_id"]))

    # ---- 2. la normalizzazione e il tetto --------------------------
    print("\n[il giudice, dal vivo]")
    r = compra({"annuncio_id": 3, "quantita": 1, "consegna": "ritiro",
                "nota_compratore": "  taglia   L\ne il  blu  "})
    prova("spazi collassati e a-capo tolti: resta UNA riga",
          "taglia L e il blu", leggi_col(r["ordine_id"]))
    alza("201 caratteri si rifiutano, e prima della invoice",
         lambda: compra({"annuncio_id": 3, "quantita": 1,
                         "consegna": "ritiro",
                         "nota_compratore": "x" * 201}), "troppo lunga")
    quante = len(INVOICES)
    try:
        compra({"annuncio_id": 3, "quantita": 1, "consegna": "ritiro",
                "nota_compratore": "y" * 500})
    except Exception:
        pass
    prova("...e il rifiuto non conia nessuna fattura orfana",
          quante, len(INVOICES))

    # ---- 3. la regressione: senza nota, il mondo di ieri -----------
    print("\n[la regressione: senza nota non cambia niente]")
    r = compra({"annuncio_id": 3, "quantita": 1, "consegna": "ritiro"})
    prova("chiave assente: la colonna nasce vuota", "",
          leggi_col(r["ordine_id"]))
    prova("...e la risposta la porta vuota, non assente", "",
          r["nota_compratore"])

    # ---- 4. LA RIPRESA: stessa fattura, nota nuova -----------------
    print("\n[la ripresa del pentito: la fattura NON si riconia]")
    base = {"annuncio_id": 4, "quantita": 1, "consegna": "digitale"}
    a = compra({**base, "nota_compratore": "prima versione"})
    n_prima = len(INVOICES)
    b = compra({**base, "nota_compratore": "seconda versione"})
    prova("il secondo «Paga» e' una RIPRESA", True, b.get("ripresa") is True)
    prova("...e la fattura e' LA STESSA", a["invoice"], b["invoice"])
    prova("...nessuna fattura nuova coniata", n_prima, len(INVOICES))
    prova("...ma la nota e' quella NUOVA, in colonna",
          "seconda versione", leggi_col(a["ordine_id"]))
    prova("...e anche nella risposta (mai quella letta prima)",
          "seconda versione", b["nota_compratore"])
    # ⚠️ IL CASO CHE LA GUARDIA SBAGLIATA ROMPEREBBE IN SILENZIO:
    # con `if nota and ...` (la forma copiata dall'indirizzo) svuotare
    # non riscriverebbe, e la nota di prima resterebbe li'.
    c = compra({**base, "nota_compratore": ""})
    prova("SVUOTARE e ripagare cancella davvero", "",
          leggi_col(a["ordine_id"]))
    prova("...ed e' ancora una ripresa, non un ordine nuovo",
          True, c.get("ripresa") is True)

    # ---- 5. l'endpoint di correzione -------------------------------
    print("\n[la correzione dentro l'ordine]")
    oid = ordini["ritiro"]
    vero.execute("UPDATE ordini SET stato='locked' WHERE id=?", (oid,))
    vero.commit()
    chi(VENDE)
    alza("il venditore non la scrive",
         lambda: endpoint(SRV.indica_nota, oid, {"nota_compratore": "no"}),
         "non permessa")
    chi({"id": 777, "nome": "X", "username": "x", "admin": False})
    alza("l'estraneo nemmeno, con la STESSA risposta",
         lambda: endpoint(SRV.indica_nota, oid, {"nota_compratore": "no"}),
         "non permessa")
    chi(COMPRA)
    AVVISI.clear()
    r = endpoint(SRV.indica_nota, oid, {"nota_compratore": "meglio la M"})
    prova("il compratore la corregge", "meglio la M", leggi_col(oid))
    prova("...e il venditore riceve UN avviso senza il testo dentro",
          True, len(AVVISI) == 1 and AVVISI[0][0] == 222
          and "meglio la M" not in AVVISI[0][1])
    AVVISI.clear()
    endpoint(SRV.indica_nota, oid, {"nota_compratore": ""})
    prova("il VUOTO cancella (l'inverso del punto)", "", leggi_col(oid))
    prova("...e lo dice", True,
          len(AVVISI) == 1 and "tolto" in AVVISI[0][1])

    # ---- 6. chi la legge da /api/orders ----------------------------
    print("\n[chi la legge: le due parti E il moderatore]")
    oid = ordini["punto"]
    vero.execute("UPDATE ordini SET stato='dispute', disputata=1 WHERE id=?",
                 (oid,))
    vero.commit()

    def righe(u):
        chi(u)
        return SRV.miei_ordini()       # sincrona, a differenza di compra()

    for u, nome in ((COMPRA, "il compratore"), (VENDE, "il venditore"),
                    (ADMIN, "il MODERATORE")):
        mio = [r for r in righe(u) if r["id"] == oid]
        prova(f"{nome} la legge", ["numero 42"],
              [r.get("nota_compratore") for r in mio])
    # ...e le sorelle restano invisibili, che e' la meta' che conta
    mio = [r for r in righe(ADMIN) if r["id"] == oid][0]
    prova("...mentre indirizzo e busta al moderatore non escono", [],
          [k for k in ("indirizzo", "busta_nome", "busta_codice")
           if k in mio])

    vero.close()
    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
