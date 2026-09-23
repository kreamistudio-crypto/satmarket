# -*- coding: utf-8 -*-
"""
SATS IN PAGAMENTO, DETTO A CHI VENDE — e la recensione a tutt'e due
(23 set 2026, «Ritocchi allo scambio P2P», dalla prova vera a due
telefoni).

Chi vende libera, e il coordinatore gli dice subito «garanzia
incassata»: il client lo leggeva «Scambio concluso» anche quando il
pagamento a chi compra non passava (quel giorno: la fattura scaduta).
Adesso chi vende resta su «Sats in pagamento» finche' il server — che
dal coordinatore sa tutto (patch 0007) — non gli dice che il pagamento
e' riuscito. E la recensione, che a chi vendeva non compariva, si
decide su quello stesso fatto.

`prove.py` difende i giudici estratti e le sentinelle del client. Qui
gira il SERVER VERO su un database usa-e-getta, e si cammina:

  1. gli eventi di mostrod entrano dalla loro porta (i due giudici
     della rotta, `_evento_p2p_pulito` e `_registra_evento_p2p`), e le
     due parti le dice lui;
  2. liberati: la domanda di chi vende risponde «in corso» — e anche a
     chi compra, che e' l'altra parte; all'estraneo e a un ordine che
     non c'e' non risponde niente, e i due casi non si distinguono;
  3. il pagamento NON passa: «fallito»; la fattura nuova: di nuovo «in
     corso»; un secondo fallimento: «fallito»; e due fatti nello stesso
     secondo li decide il fallimento, che e' sempre la conseguenza di
     un tentativo;
  4. a scambio non ancora concluso la recensione non si lascia (e la
     domanda lo dice prima, `non_conclusa`);
  5. il pagamento RIUSCITO: «riuscito», con l'ora di mostrod;
  6. COL LIBRO ANCORA INDIETRO (`in-progress`) la recensione si lascia
     lo stesso — il fatto l'ha detto chi lo fa — da tutt'e due le
     parti, UNA per parte: la seconda trova il database;
  7. la strada di ieri resta: col solo libro a `success` si recensisce
     come prima;
  8. la rotta non guarda la leva del P2P (un 409 colpirebbe chi ha uno
     scambio a meta' il giorno che si spegne), e un corpo storto e' un
     400, mai un 500.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. Nessuna
rete: niente Telegram (le notifiche sono sostituite), niente relay,
niente coordinatore.

USO:  python collaudo_pagamento_p2p.py
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
DETTO = []          # (destinatario, testo) di ogni notifica

SCAMBIO = "5a1e0000-1111-4a2b-9c3d-000000000001"
SOLO_LIBRO = "5a1e0000-2222-4a2b-9c3d-000000000002"
MAI_VISTO = "5a1e0000-3333-4a2b-9c3d-000000000003"
VENDE, COMPRA, ESTRANEO = 111, 222, 333
CHIAVE_VENDE = "a1" * 32
CHIAVE_COMPRA = "b2" * 32


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ok {nome}")
    else:
        FALLITE += 1
        print(f"  NO {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


class Busta:
    """Una richiesta finta: le rotte del P2P leggono il body da qui."""

    def __init__(self, dati):
        self.dati = dati
        self.headers = {}

    async def json(self):
        return self.dati


def avvio():
    """Il config finto PRIMA di importare server."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("ATTENTO: server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-pagamento-"),
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
    cfg.PROTEZIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def notifica_finta(chi, testo, *a, **k):
        DETTO.append((chi, testo))

    async def zitto(*a, **k):
        return None

    server.notifica = notifica_finta
    server.notifica_admin = zitto
    server.premia_distintivi = zitto
    server.premia_xp = zitto
    server.polso_ordini_admin = zitto
    return db


def come(tg_id):
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "first_name": f"U{tg_id}",
        "username": f"u{tg_id}", "admin": False}


def chiama(fn, corpo=None):
    """La rotta, col body dalle due porte (`leggi_json` e `req.json()`);
    una JSONResponse torna come dizionario, con le sue intestazioni."""
    d = corpo if corpo is not None else {}

    async def leggi(_req):
        if not isinstance(d, dict):
            raise SRV.HTTPException(400, "Richiesta malformata")
        return d
    SRV.leggi_json = leggi
    r = asyncio.run(fn(Busta(d)))
    if hasattr(r, "body"):
        fuori = json.loads(r.body)
        fuori["__cache"] = r.headers.get("cache-control", "")
        return fuori
    return r


def errore(fn, corpo=None):
    """Il codice e il messaggio di un rifiuto, o None se e' passato."""
    try:
        chiama(fn, corpo)
        return None
    except Exception as e:
        return (getattr(e, "status_code", type(e).__name__),
                str(getattr(e, "detail", e)))


def esito(fn, corpo=None):
    """La risposta, o il rifiuto come coppia (codice, messaggio): un
    passo che doveva riuscire e viene rifiutato diventa una rossa COL
    SUO NOME, non un'eccezione che si porta via il giro (la lezione
    della tortura: un banco che esplode non dice cosa si e' rotto)."""
    try:
        return chiama(fn, corpo)
    except Exception as e:
        return (getattr(e, "status_code", type(e).__name__),
                str(getattr(e, "detail", e)))


def con_db():
    con = SRV.db()
    con.row_factory = sqlite3.Row
    return con


def semina():
    """Tre persone, le due chiavi di scambio, e le righe del libro."""
    con = con_db()
    adesso = int(time.time())
    for tg, nome in ((VENDE, "Chi vende"), (COMPRA, "Chi compra"),
                     (ESTRANEO, "Un estraneo")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, f"neg{tg}{tg}"))
    for chiave, tg in ((CHIAVE_VENDE, VENDE), (CHIAVE_COMPRA, COMPRA)):
        con.execute("INSERT OR REPLACE INTO chiavi_p2p(pubkey, tg_id, creato) "
                    "VALUES(?,?,?)", (chiave, tg, adesso))
    # chi vende ha pubblicato, chi compra ha preso: i due posti del
    # libro, da cui passa il destinatario di una recensione. Il libro
    # dello SCAMBIO resta indietro (`in-progress`) apposta: e' il caso
    # dei due orologi.
    for ordine, stato in ((SCAMBIO, "in-progress"), (SOLO_LIBRO, "success")):
        con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,"
                    "maker,visto,preso_da) VALUES(?,?,?,?,'sell',1,?,?)",
                    (ordine, VENDE, adesso, stato, adesso, COMPRA))
    con.commit()
    con.close()


def evento(ordine, azione, ts, attore="mostro", dettaglio=None, **extra):
    """Un POST di mostrod, fatto passare dai due giudici della rotta
    `/api/p2p/evento` (la rotta intera lancia l'invio in un task, e qui
    si guarda la cronaca, non Telegram)."""
    d = {"v": 1, "order": ordine, "action": azione, "ts": ts,
         "buyer": CHIAVE_COMPRA, "seller": CHIAVE_VENDE, "actor": attore,
         "detail": dettaglio}
    d.update(extra)
    con = con_db()
    try:
        ev = SRV._evento_p2p_pulito(d, int(time.time()))
        return SRV._registra_evento_p2p(con, ev, int(time.time()))
    finally:
        con.close()


def pagamento(chi, ordini=None):
    """La domanda di `chi`; un rifiuto torna come risposta vuota con
    l'errore accanto, cosi' le prove dopo dicono il loro nome."""
    come(chi)
    r = esito(SRV.pagamenti_p2p, {"ordini": ordini or [SCAMBIO]})
    if not isinstance(r, dict):
        return {"pagamenti": {}, "__errore": r, "__cache": ""}
    return r


def stato_di(chi, ordine=SCAMBIO):
    return (pagamento(chi, [ordine]).get("pagamenti") or {}).get(ordine, {}).get("stato")


def main():
    avvio()
    semina()
    t0 = int(time.time()) - 600       # dentro i 900 s dell'orologio
    rotta = SRV.pagamenti_p2p

    print("\n1) gli eventi entrano, e le parti le dice mostrod")
    fatto = evento(SCAMBIO, "taken", t0, attore="buyer", dettaglio="invoice-next")
    prova("la presa si registra", "preso", (fatto or {}).get("momento"))
    prova("...e le parti sono quelle delle due chiavi", (COMPRA, VENDE),
          ((fatto or {}).get("compratore"), (fatto or {}).get("venditore")))
    evento(SCAMBIO, "hold-invoice-paid", t0 + 10, attore="seller",
           dettaglio="invoice-next")
    evento(SCAMBIO, "buyer-invoice-added", t0 + 20, attore="buyer",
           dettaglio="active")
    evento(SCAMBIO, "fiat-sent", t0 + 30, attore="buyer")
    prova("prima del rilascio non c'e' niente da dire", {},
          {k: v for k, v in pagamento(VENDE).items() if k != "__cache"}
          .get("pagamenti"))

    print("\n2) liberati: in corso, a tutt'e due le parti e a nessun altro")
    evento(SCAMBIO, "released", t0 + 40, attore="seller",
           sats=7300, sats_buyer=7228, sats_seller=7372)
    r = pagamento(VENDE)
    prova("chi vende: in corso", {"stato": "in_corso", "quando": t0 + 40},
          (r.get("pagamenti") or {}).get(SCAMBIO))
    prova("...e la risposta non si mette in cache", "no-store", r.get("__cache"))
    prova("chi compra, che e' l'altra parte: lo stesso",
          {"stato": "in_corso", "quando": t0 + 40},
          (pagamento(COMPRA).get("pagamenti") or {}).get(SCAMBIO))
    prova("l'estraneo non riceve la riga", {},
          pagamento(ESTRANEO).get("pagamenti"))
    prova("...come un ordine che non esiste: i due casi non si distinguono", {},
          pagamento(VENDE, [MAI_VISTO]).get("pagamenti"))
    prova("...e uno scambio che il server ha visto solo dal libro, pure", {},
          pagamento(VENDE, [SOLO_LIBRO]).get("pagamenti"))

    print("\n3) il pagamento non passa, la fattura nuova, di nuovo")
    evento(SCAMBIO, "payout-failed", t0 + 50, dettaglio="INVOICE_EXPIRED")
    prova("il pagamento non passato: fallito",
          {"stato": "fallito", "quando": t0 + 50},
          (pagamento(VENDE).get("pagamenti") or {}).get(SCAMBIO))
    evento(SCAMBIO, "buyer-invoice-added", t0 + 60, attore="buyer",
           dettaglio="new-invoice")
    prova("la fattura nuova: di nuovo in corso",
          {"stato": "in_corso", "quando": t0 + 60},
          (pagamento(VENDE).get("pagamenti") or {}).get(SCAMBIO))
    evento(SCAMBIO, "payout-failed", t0 + 70, dettaglio="NO_ROUTE")
    prova("un secondo fallimento: fallito",
          {"stato": "fallito", "quando": t0 + 70},
          (pagamento(VENDE).get("pagamenti") or {}).get(SCAMBIO))
    evento(SCAMBIO, "buyer-invoice-added", t0 + 80, attore="buyer",
           dettaglio="new-invoice")
    evento(SCAMBIO, "payout-failed", t0 + 80, dettaglio="INVOICE_INVALID")
    prova("fattura nuova e fallimento nello stesso secondo: vince il fallimento",
          {"stato": "fallito", "quando": t0 + 80},
          (pagamento(VENDE).get("pagamenti") or {}).get(SCAMBIO))
    evento(SCAMBIO, "buyer-invoice-added", t0 + 90, attore="buyer",
           dettaglio="new-invoice")

    print("\n4) a scambio non concluso la recensione non si lascia")
    come(VENDE)
    rec = chiama(SRV.recensibile_p2p, {"ordine": SCAMBIO})
    prova("la domanda di chi vende lo dice prima", (False, "non_conclusa"),
          (rec["si"], rec["motivo"]))
    prova("...e l'invio e' un 400 con la sua ragione",
          (400, "La recensione si lascia a scambio concluso"),
          errore(SRV.recensione_p2p, {"ordine": SCAMBIO, "voto": 5}))

    print("\n5) il pagamento riesce")
    evento(SCAMBIO, "success", t0 + 100, sats=7300, sats_buyer=7228,
           sats_seller=7372)
    prova("riuscito, con l'ora di mostrod",
          {"stato": "riuscito", "quando": t0 + 100},
          (pagamento(VENDE).get("pagamenti") or {}).get(SCAMBIO))
    prova("...e un fallimento vecchio non lo smentisce", "riuscito",
          stato_di(COMPRA))

    print("\n6) col libro ancora indietro, la recensione da tutt'e due")
    con = con_db()
    prova("(il libro dello scambio e' ancora in-progress)", "in-progress",
          con.execute("SELECT stato FROM p2p_ordini WHERE ordine=?",
                      (SCAMBIO,)).fetchone()["stato"])
    con.close()
    for chi, nome in ((VENDE, "chi vende"), (COMPRA, "chi compra")):
        come(chi)
        rec = chiama(SRV.recensibile_p2p, {"ordine": SCAMBIO})
        prova(f"{nome}: c'e' un posto per la recensione", (True, "", False),
              (rec.get("si"), rec.get("motivo"), rec.get("gia")))
    come(VENDE)
    prova("chi vende la lascia", {"ok": True, "voto": 4},
          esito(SRV.recensione_p2p, {"ordine": SCAMBIO, "voto": 4,
                                     "commento": "Tutto liscio"}))
    come(COMPRA)
    prova("chi compra la lascia", {"ok": True, "voto": 5},
          esito(SRV.recensione_p2p, {"ordine": SCAMBIO, "voto": 5}))
    come(VENDE)
    prova("la seconda di chi vende trova il database",
          (400, "Hai già lasciato la recensione per questo scambio"),
          errore(SRV.recensione_p2p, {"ordine": SCAMBIO, "voto": 1}))
    rec = chiama(SRV.recensibile_p2p, {"ordine": SCAMBIO})
    prova("...e la domanda dice che c'e' gia', con le sue stelle",
          (False, True, 4, "Tutto liscio"),
          (rec.get("si"), rec.get("gia"), rec.get("voto"), rec.get("commento")))
    con = con_db()
    righe = [tuple(r) for r in con.execute(
        "SELECT da_tg_id, per_tg_id, voto FROM feedback WHERE scambio=? "
        "ORDER BY da_tg_id", (SCAMBIO,))]
    medie = {r["tg_id"]: (r["rating"], r["n_feedback"]) for r in con.execute(
        "SELECT tg_id, rating, n_feedback FROM utenti WHERE tg_id IN (?,?)",
        (VENDE, COMPRA))}
    con.close()
    prova("una recensione per parte, ognuna all'altra",
          [(VENDE, COMPRA, 4), (COMPRA, VENDE, 5)], righe)
    prova("...e le due medie si muovono", {VENDE: (5.0, 1), COMPRA: (4.0, 1)},
          medie)

    print("\n7) la strada di ieri resta: il solo libro a success")
    come(COMPRA)
    rec = chiama(SRV.recensibile_p2p, {"ordine": SOLO_LIBRO})
    prova("col libro a success si recensisce come prima", (True, ""),
          (rec["si"], rec["motivo"]))

    print("\n8) la leva non conta, e un corpo storto e' un 400")
    SRV._p2p_per = lambda *a, **k: {"attivo": False}
    prova("a leva spenta la domanda risponde lo stesso", "riuscito",
          stato_di(VENDE))
    come(VENDE)
    prova("una lista vuota: 400", (400, "Nessun ordine"),
          errore(rotta, {"ordini": []}))
    prova("un id in una forma storta: 400",
          (400, "Ordine in una forma sconosciuta"),
          errore(rotta, {"ordini": ["../../etc"]}))
    prova("un corpo che non e' un oggetto: 400", (400, "Richiesta malformata"),
          errore(rotta, ["x"]))
    prova("nessuna notifica partita da queste rotte, salvo le due recensioni ricevute",
          sorted([COMPRA, VENDE]), sorted(chi for chi, _ in DETTO))

    print(f"\n{PASSATE} passate, {FALLITE} fallite")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
