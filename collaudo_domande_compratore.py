# -*- coding: utf-8 -*-
"""LE DOMANDE DEL VENDITORE A CHI COMPRA, fatte girare per davvero
(6 nov 2026, cantiere domande-compratore).

`prove.py` difende la FORMA e i giudici puri. Qui gira il SERVER VERO,
su un database usa-e-getta, e si chiedono le cose che solo la filiera
intera puo' dire:

  · il preventivo porta le domande dell'annuncio alla cassa;
  · la cassa le esige (le obbligatorie) e le scrive CIFRATE in colonna
    — in collaudo 'plain:', come tutto il resto;
  · da /api/orders il testo non esce a NESSUNO, il fatto (`risposte_il`)
    si'; da /risposte lo leggono le due parti e basta, il moderatore no;
  · la ripresa riscrive le risposte senza coniare una fattura nuova;
  · la combo spedizione + codice: chi sceglie la spedizione non risponde;
  · la scopa le cancella a ordine chiuso;
  · l'ordine on-chain le porta dalla cassa alla riga di `ordini`.

Piu' la REGRESSIONE, che e' meta' del valore: un annuncio senza domande
compra come ieri, byte per byte.

NON TOCCA NIENTE DI VERO: config sostituito PRIMA dell'import di server,
LNbits mai chiamato (le invoice si contano), nessuna rete.

USO:  python collaudo_domande_compratore.py
"""

import asyncio
import json
import os
import sqlite3
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
INVOICES = []

COMPRA = {"id": 111, "nome": "Compra", "username": "compra", "admin": False}
VENDE = {"id": 222, "nome": "Vende", "username": "vende", "admin": False}
ADMIN = {"id": 999, "nome": "Admin", "username": "admin", "admin": True}

DOMANDE = [{"t": "Nome", "k": "testo", "o": [], "obb": True},
           {"t": "Cognome", "k": "testo", "o": [], "obb": True},
           {"t": "Email", "k": "email", "o": [], "obb": True},
           {"t": "Giorno", "k": "scelta", "o": ["Venerdì", "Sabato"],
            "obb": False},
           {"t": "Vegetariano", "k": "sino", "o": [], "obb": False}]
BUONE = ["Mario", "Rossi", "mario@esempio.it", "Sabato", "No"]


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def alza(nome, fn, codice_atteso=400, dentro=""):
    global PASSATE, FALLITE
    try:
        fn()
    except Exception as e:
        codice = getattr(e, "status_code", None)
        testo = str(getattr(e, "detail", e))
        if codice == codice_atteso and (not dentro
                                        or dentro.lower() in testo.lower()):
            PASSATE += 1
            print(f"  ✓ {nome}")
            return
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso {codice_atteso} con {dentro!r}"
              f"\n      avuto:  {codice} {testo!r}")
        return
    FALLITE += 1
    print(f"  ✗ {nome}\n      atteso un rifiuto, non e' arrivato")


def avvio():
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-domande-"),
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

    async def zitta(*a, **k):
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


def chiama(fn, corpo, *arg):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(fn(*arg, None))


def compra(corpo):
    return chiama(SRV.compra, corpo)


def semina(db):
    con = sqlite3.connect(db)
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,negozio) "
                "VALUES(222,'Vende','vende','negozio22')")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,negozio) "
                "VALUES(111,'Compra','compra','negozio11')")
    # 1: il biglietto (solo codice online, con le domande)
    # 2: la combo spedizione + codice, con le domande
    # 3: il codice online di ieri, senza domande (la regressione)
    for aid, consegna, anche, dom in (
            (1, "digitale", 0, json.dumps(DOMANDE)),
            (2, "spedizione", 1, json.dumps(DOMANDE)),
            (3, "digitale", 0, "")):
        con.execute(
            "INSERT OR REPLACE INTO annunci(id,titolo,descrizione,prezzo_sats,"
            "venditore_id,stato,categoria,quantita,consegna,anche_digitale,"
            "zona,valuta,domande) VALUES(?,?,'x',50000,222,'attivo','Altro',"
            "50,?,?,'Pavia (PV)','sats',?)",
            (aid, f"Cosa {aid}", consegna, anche, dom))
    con.commit()
    con.close()


def main():
    print("=" * 58)
    print("  LE DOMANDE DEL VENDITORE — il giro vero")
    print("=" * 58)
    db = avvio()
    semina(db)
    vero = sqlite3.connect(db)
    vero.row_factory = sqlite3.Row

    def col(oid, c):
        return vero.execute(f"SELECT {c} FROM ordini WHERE id=?",
                            (oid,)).fetchone()[0]

    # ---- 1. il preventivo porta le domande -------------------------
    print("\n[il preventivo porta le domande alla cassa]")
    chi(COMPRA)
    p = chiama(SRV.preventivo_ordine, {"annuncio_id": 1, "quantita": 1})
    prova("le domande arrivano, nell'ordine del venditore",
          [q["t"] for q in DOMANDE], [q["t"] for q in p.get("domande", [])])
    p3 = chiama(SRV.preventivo_ordine, {"annuncio_id": 3, "quantita": 1})
    prova("...e un annuncio senza domande ne porta zero", [],
          p3.get("domande"))

    # ---- 2. la cassa le esige ---------------------------------------
    print("\n[la cassa: le obbligatorie, la forma, i no]")
    base = {"annuncio_id": 1, "quantita": 1, "consegna": "digitale"}
    n0 = len(INVOICES)
    alza("l'app vecchia (nessuna risposta) si sente dire di aggiornarla",
         lambda: compra(base), dentro="aggiorna l'app")
    alza("un'obbligatoria vuota si rifiuta, nominandola",
         lambda: compra({**base, "risposte": ["Mario", "", "m@e.it"]}),
         dentro="Cognome")
    alza("una scelta fuori dall'elenco no",
         lambda: compra({**base, "risposte":
                         ["Mario", "Rossi", "m@e.it", "Domenica"]}),
         dentro="elenco")
    alza("un'email senza chiocciola no",
         lambda: compra({**base, "risposte": ["Mario", "Rossi", "mario"]}),
         dentro="email")
    prova("...e nessun rifiuto conia una fattura orfana", n0, len(INVOICES))

    r = compra({**base, "risposte": BUONE})
    oid = r["ordine_id"]
    blob = col(oid, "risposte")
    prova("le risposte sono in colonna, nella busta dei contenuti",
          True, blob.startswith(("plain:", "f2:")))
    prova("...con la domanda fotografata accanto a ogni risposta",
          [{"d": q["t"], "r": v} for q, v in zip(DOMANDE, BUONE)],
          SRV.risposte_lette(blob))
    prova("...e il quando", True, col(oid, "risposte_il") > 0)

    # ---- 3. la ripresa ---------------------------------------------
    print("\n[la ripresa: stessa fattura, risposte nuove]")
    n1 = len(INVOICES)
    b = compra({**base, "risposte": ["Maria", "Rossi", "maria@esempio.it"]})
    prova("il secondo «Paga» e' una ripresa", True, b.get("ripresa") is True)
    prova("...nessuna fattura nuova", n1, len(INVOICES))
    prova("...ma le risposte sono quelle nuove", "Maria",
          SRV.risposte_lette(col(oid, "risposte"))[0]["r"])

    # ---- 4. chi le legge -------------------------------------------
    print("\n[chi le legge: le due parti, il moderatore MAI]")
    vero.execute("UPDATE ordini SET stato='dispute', disputata=1 WHERE id=?",
                 (oid,))
    vero.commit()
    for u, nome in ((COMPRA, "il compratore"), (VENDE, "il venditore"),
                    (ADMIN, "il moderatore")):
        chi(u)
        mio = [x for x in SRV.miei_ordini() if x["id"] == oid]
        prova(f"/api/orders a {nome}: il testo non c'e', il fatto si'",
              (False, True),
              (any("risposte" == k for k in (mio[0] if mio else {})),
               bool(mio and mio[0].get("risposte_il"))))
    for u, nome in ((COMPRA, "il compratore"), (VENDE, "il venditore")):
        chi(u)
        d = asyncio.run(SRV.leggi_risposte(oid))
        prova(f"/risposte: {nome} le legge", ["Nome", "Maria"],
              [d["risposte"][0]["domanda"], d["risposte"][0]["risposta"]])
    chi(ADMIN)
    alza("/risposte: il moderatore no, col no opaco",
         lambda: asyncio.run(SRV.leggi_risposte(oid)), dentro="non permessa")
    chi({"id": 777, "nome": "X", "username": "x", "admin": False})
    alza("/risposte: l'estraneo nemmeno, con la STESSA risposta",
         lambda: asyncio.run(SRV.leggi_risposte(oid)), dentro="non permessa")

    # ---- 5. la combo e la regressione ------------------------------
    print("\n[la combo e il mondo di ieri]")
    chi(COMPRA)
    r = compra({"annuncio_id": 2, "quantita": 1, "consegna": "spedizione",
                "spedizione_via": "casa",
                "indirizzo": {"nome": "Mario Rossi", "via": "Via Roma 1",
                              "cap": "27100", "citta": "Pavia"},
                "indirizzo_confermato": True})
    prova("combo, chi sceglie la SPEDIZIONE non risponde a niente", "",
          col(r["ordine_id"], "risposte"))
    alza("combo, chi sceglie il CODICE risponde",
         lambda: compra({"annuncio_id": 2, "quantita": 1,
                         "consegna": "digitale"}), dentro="aggiorna")
    r = compra({"annuncio_id": 3, "quantita": 1, "consegna": "digitale"})
    prova("senza domande: compra come ieri, colonna vuota", ("", 0),
          (col(r["ordine_id"], "risposte"),
           col(r["ordine_id"], "risposte_il")))
    r = compra({"annuncio_id": 3, "quantita": 1, "consegna": "digitale",
                "risposte": ["avanzo"]})
    prova("...e risposte mandate a un annuncio senza domande non si "
          "scrivono", "", col(r["ordine_id"], "risposte"))

    # ---- 6. la scopa -----------------------------------------------
    print("\n[la scopa a ordine chiuso]")
    vecchio = int(time.time()) - (SRV.GIORNI_INDIRIZZO + 1) * 86400
    vero.execute("UPDATE ordini SET stato='refunded', aggiornato=? "
                 "WHERE id=?", (vecchio, oid))
    vero.commit()
    SRV.pulisci_indirizzi()
    prova("chiuso da piu' della finestra: risposte cancellate, col timbro",
          ("", True), (col(oid, "risposte"),
                       col(oid, "risposte_purgate_il") > 0))
    chi(VENDE)
    alza("/risposte dopo la scopa lo dice", lambda: asyncio.run(
        SRV.leggi_risposte(oid)), codice_atteso=404, dentro="cancellate")

    # ---- 7. l'ordine on-chain: dalla cassa alla riga di `ordini` ----
    print("\n[l'ordine on-chain porta le risposte]")
    con = SRV.db()
    SRV._onchain_prepara_ordini(con)
    blob = SRV._risposte_da_payload(DOMANDE, {"risposte": BUONE})
    con.execute(
        "INSERT INTO onchain_ordini(indirizzo_id,annuncio_id,compratore_id,"
        "venditore_id,quantita,prezzo_sats,margine_sats,importo_sats,"
        "incasso,rimborso,stato,creato,aggiornato,scade,dettagli) "
        "VALUES(4242,1,111,222,1,50000,0,50000,'','','pagato',?,?,?,?)",
        (int(time.time()), int(time.time()), int(time.time()) + 86400,
         json.dumps({"consegna": "digitale",
                                       "risposte": blob})))
    o = con.execute("SELECT * FROM onchain_ordini ORDER BY id DESC "
                    "LIMIT 1").fetchone()
    nuovo = SRV._onchain_nasce_ordine(con, o)
    con.commit()
    riga = con.execute("SELECT risposte, risposte_il FROM ordini WHERE id=?",
                       (nuovo,)).fetchone()
    con.close()
    prova("la riga di `ordini` nasce con le risposte della cassa",
          "Mario", (SRV.risposte_lette(riga["risposte"]) or [{}])[0].get("r"))
    prova("...e col quando", True, riga["risposte_il"] > 0)

    vero.close()
    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
