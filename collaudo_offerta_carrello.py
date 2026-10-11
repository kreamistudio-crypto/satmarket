# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'OFFERTA SUL CARRELLO (ago 2026): il giro vero,
proposta -> contro -> rilancio -> accetta -> pagamento, con la bolt11
confrontata AL SAT.

`prove.py` difende la FORMA; quello che non puo' fare e' far girare la
trattativa VERA — e questo cantiere ha gia' dimostrato perche' serve:
il primo giro di QUESTO script ha preso un `ORDER BY id` su
offerte_righe, che una colonna id non ce l'ha (il gemello del bug
della ronda). Le sentinelle erano verdi, il pagamento sarebbe esploso
sul database vero.

LA PROVA REGINA: `prezzo_sats = Σlordo − accordo + spedizione +
protezione`, con l'accordo = max(0, Σlordo − pattuito) — e preventivo
== compra, al sat, perche' passano dalle stesse pure. Accanto, le
domande che si fanno insieme:
  · gli SCONTI SPENTI sotto accordo (la regola del negozio NON si
    applica, il codice nel body -> 400) — provati GIRANDO il conto
    nei due mondi, mai dalla sola forma;
  · la SPEDIZIONE GRATIS che resta e misura il PATTUITO;
  · le DECADENZE della tabella, una per una (esaurito fra proposta e
    accetta, parziale che non decade, prezzo calato sotto il pattuito,
    modifica() sulle pendenti, pausa dello stock, orologio, ferie);
  · l'ESCLUSIONE RECIPROCA nei due versi;
  · la FUSIONE senza figlie orfane;
  · la ronda del libro mastro, che su tutto questo deve TACERE.

NON TOCCA NIENTE DI VERO: il config si sostituisce PRIMA dell'import
di server, LNbits e' finto (le invoice si contano, non si chiedono),
le notifiche si catturano in una lista invece di partire.

USO:  python collaudo_offerta_carrello.py
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
INVOICES = []       # le cifre che la bolt11 finta ha chiesto
NOTIFICHE = []      # (tg_id, testo): il 🕊 delle decadenze si legge qui

# 1 BTC = 100.000 €, cioe' MILLE SATS = UN EURO (il patto di
# collaudo_conto): ogni cifra si legge a mente nelle due unita'
CAMBIO = 100_000.0

COMPRA = {"id": 111, "nome": "Compra", "username": "compra", "admin": False}
VENDE = {"id": 222, "nome": "Vende", "username": "vende", "admin": False}
RIVALE = {"id": 333, "nome": "Rivale", "username": "rivale", "admin": False}
CHI = [COMPRA]      # l'identita' che verifica_utente rispondera'


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def avvio():
    """Il config finto PRIMA di importare server, o si aprirebbe il
    database di casa. La PROTEZIONE e' accesa apposta: si calcola sul
    NETTO, cioe' sul pattuito — se l'accordo smettesse di entrare nel
    conto prima di lei, i totali qui sotto non tornerebbero piu'."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-collaudo-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    # i segnaposto del config d'esempio, la convenzione che lo scanner
    # dei segreti riconosce (vedi collaudo_conto.py per il perche')
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [999]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    cfg.PROTEZIONE_PERCENTO = 5
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
        return CAMBIO

    async def pagata_finta(payment_hash, _cassaforte=""):
        # il saldo del giro completo: verifica_pagamento chiede a
        # LNbits, e qui LNbits dice sempre di si'
        return True

    async def nota_finta(tg_id, testo, **k):
        NOTIFICHE.append((tg_id, testo))

    async def zitto(*a, **k):
        return None

    server.crea_invoice_escrow = invoice_finta
    server.cambio_btc_eur = cambio_finto
    server.invoice_pagata = pagata_finta
    server.notifica = nota_finta
    server.polso_ordini_admin = zitto
    server.annuncio_su_nostr = zitto
    server.promo_venduto = zitto
    # l'identita' si CAMBIA fra una chiamata e l'altra: la trattativa
    # e' di due persone, e un utente fisso non saprebbe rispondere
    server.verifica_utente = lambda *a, **k: CHI[0]
    return db


def chiama(fn, corpo, chi=COMPRA, *args):
    """Chiama un endpoint VERO: leggi_json e verifica_utente si
    sostituiscono, il resto e' il codice di produzione. `args` sono i
    posizionali prima della Request (l'id di offerta/annuncio)."""
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    CHI[0] = chi
    return asyncio.run(fn(*args, None) if args else fn(None))


def errore(fn, corpo, chi=COMPRA, *args):
    """La stessa chiamata, quando il no e' la risposta giusta: torna
    (status, detail) o ('OK', risposta) se non ha alzato."""
    try:
        return "OK", chiama(fn, corpo, chi, *args)
    except SRV.HTTPException as e:
        return e.status_code, e.detail


def semina(prezzo=30_000, quantita=5, consegna="ritiro", n=2,
           spedizione_sats=0, **venditore):
    """Il venditore coi suoi annunci, il compratore e il rivale.
    Ogni sezione riparte da un mercatino pulito."""
    con = SRV.db()
    for t in ("offerte_righe", "offerte", "ordine_righe", "ordini",
              "annunci"):
        con.execute(f"DELETE FROM {t}")
    colonne = "".join(f",{c}" for c in venditore)
    segni = "".join("," + "?" for _ in venditore)
    con.execute(
        f"INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato"
        f"{colonne}) VALUES(222,'Vende','neg22222',1{segni})",
        tuple(venditore.values()))
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato) VALUES(111,'Compra','neg11111',1)")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato) VALUES(333,'Rivale','neg33333',1)")
    ids = []
    for i in range(n):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,"
            "prezzo_sats,categoria,zona,stato,creato,consegna,quantita,"
            "valuta,condizione,spedizione_sats,foto) "
            "VALUES(222,?,'desc',?,'Altro','Torino (TO)','attivo',1,?,"
            # la foto (11 ott 2026, cantiere foto-obbligatorie): un
            # annuncio vero ne ha almeno una, e senza la modifica
            # del prezzo (sezione e) si fermerebbe a chiederla
            "?,'sats','buono',?,?)",
            (f"Cosa {i}", prezzo, consegna, quantita, spedizione_sats,
             '["cosa.jpg"]'))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    NOTIFICHE.clear()
    return ids


def leggi_off(off_id):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    o = con.execute("SELECT * FROM offerte WHERE id=?",
                    (off_id,)).fetchone()
    figlie = con.execute("SELECT * FROM offerte_righe WHERE offerta_id=? "
                         "ORDER BY rowid", (off_id,)).fetchall()
    con.close()
    return o, figlie


def proponi(righe, importo, chi=COMPRA):
    r = chiama(SRV.fai_offerta_carrello,
               {"righe": [{"annuncio_id": a, "quantita": q}
                          for a, q in righe],
                "importo": str(importo)}, chi)
    return r["offerta_id"]


def accordo(righe, importo, chi=COMPRA):
    """La strada corta delle sezioni che partono da un accordo gia'
    stretto: proposta + accetta del venditore."""
    off_id = proponi(righe, importo, chi)
    chiama(SRV.rispondi_offerta, {"azione": "accetta"}, VENDE, off_id)
    return off_id


def corpo_righe(coppie, off=0, bugiardo=False):
    """Il body che il client manda DAVVERO sotto accordo: le righe ci
    sono sempre (>=2, il gate di _compra_set sta prima dell'accordo).
    Con `bugiardo` le quantita' sono STORTE apposta — e' l'unico modo
    di dimostrare che a comandare sono le figlie fotografate e non il
    client: coi numeri giusti le due strade darebbero lo stesso conto
    e la prova non proverebbe niente (l'ha detto la tortura, non la
    rilettura)."""
    return [{"annuncio_id": a, "quantita": (q + 2 if bugiardo else q),
             **({"offerta_id": off} if off else {})} for a, q in coppie]


def prove_proposta():
    """[1] LA PROPOSTA E LE SUE GUARDIE: la testata con annuncio_id=0
    e quantita=0, le figlie fotografate, il minimo sulla somma, e
    l'esclusione reciproca nei due versi."""
    print("\n[1] LA PROPOSTA — testata, figlie e guardie")
    a, b = semina()                      # 2 annunci da 30.000, qta 5
    off_id = proponi([(a, 2), (b, 1)], 60_000)   # listino 90.000
    o, figlie = leggi_off(off_id)
    prova("la testata e' un'offerta con annuncio_id=0", 0,
          o["annuncio_id"])
    prova("...e quantita=0: la cifra e' il totale, mai «× pezzi»", 0,
          o["quantita"])
    prova("...in stato proposta, coi totali in colonna",
          ("proposta", 60_000), (o["stato"], o["importo_sats"]))
    prova("le figlie sono due, nell'ordine della proposta", [a, b],
          [f["annuncio_id"] for f in figlie])
    prova("...con quantita' e unitario FOTOGRAFATI", [(2, 30_000),
          (1, 30_000)], [(f["quantita"], f["unitario_sats"])
                         for f in figlie])
    prova("...e il titolo fotografato (display e notifiche)",
          "Cosa 0", figlie[0]["titolo"])
    prova("il venditore riceve UNA notifica, col listino dentro", True,
          len(NOTIFICHE) == 1 and NOTIFICHE[0][0] == 222
          and "90.000 sats" in NOTIFICHE[0][1])
    # le guardie, ognuna col suo no
    st, det = errore(SRV.fai_offerta_carrello,
                     {"righe": [{"annuncio_id": a, "quantita": 1}],
                      "importo": "10000"})
    prova("una riga sola: 400 verso l'offerta di sempre", (400, True),
          (st, "per uno solo" in det))
    st, det = errore(SRV.fai_offerta_carrello,
                     {"righe": [{"annuncio_id": a, "quantita": 2},
                                {"annuncio_id": b, "quantita": 1}],
                      "importo": "90000"}, RIVALE)
    prova("pari al listino: «puoi comprare direttamente»", (400, True),
          (st, "comprare direttamente" in det))
    st, det = errore(SRV.fai_offerta_carrello,
                     {"righe": [{"annuncio_id": a, "quantita": 2},
                                {"annuncio_id": b, "quantita": 1}],
                      "importo": "40000"}, RIVALE)
    prova("sotto il 50% della SOMMA: il minimo lo dice", (400, True),
          (st, "partono da 45.000 sats" in det))
    st, det = errore(SRV.fai_offerta_carrello,
                     {"righe": [{"annuncio_id": a, "quantita": 1},
                                {"annuncio_id": b, "quantita": 1}],
                      "importo": "31000"})
    prova("UNA viva per coppia: la seconda aspetta", (400, True),
          (st, "già un'offerta sul carrello in corso" in det))
    # l'ESCLUSIONE RECIPROCA, verso singolo->carrello: il pezzo sta
    # dentro la mia offerta di carrello viva
    st, det = errore(SRV.fai_offerta, {"importo": "20000"}, COMPRA, a)
    prova("esclusione, verso singolo→carrello", (400, True),
          (st, "dentro la tua offerta sul carrello" in det))
    # ...e il verso carrello->singolo: offerta singola viva del
    # RIVALE su `a`, che poi prova il carrello con dentro `a`
    chiama(SRV.fai_offerta, {"importo": "20000"}, RIVALE, a)
    st, det = errore(SRV.fai_offerta_carrello,
                     {"righe": [{"annuncio_id": a, "quantita": 1},
                                {"annuncio_id": b, "quantita": 1}],
                      "importo": "31000"}, RIVALE)
    prova("esclusione, verso carrello→singolo, col nome del pezzo",
          (400, True), (st, "«Cosa 0»" in det))
    # la quantita' si LIMA allo stock, mai uno scarto
    a2, b2 = semina()
    # limata a 5, il listino fa 180.000: la cifra sta sopra il minimo
    off2 = proponi([(a2, 99), (b2, 1)], 100_000)
    _, figlie2 = leggi_off(off2)
    prova("la quantita' fuori scala si lima allo stock", 5,
          figlie2[0]["quantita"])


def prove_regina():
    """[2] IL GIRO COMPLETO E LA PROVA REGINA: contro e rilancio sui
    totali, l'accetta col consolidamento, e il pagamento con la bolt11
    al sat — prezzo = Σlordo − accordo + prot, righe LORDE."""
    print("\n[2] IL GIRO COMPLETO — proposta→contro→rilancio→accetta→paga")
    a, b = semina()
    off_id = proponi([(a, 2), (b, 1)], 60_000)       # listino 90.000
    chiama(SRV.rispondi_offerta, {"azione": "contro",
                                  "importo": "75000"}, VENDE, off_id)
    o, _ = leggi_off(off_id)
    prova("la contro del venditore, sul totale",
          ("controproposta", 75_000), (o["stato"], o["contro_sats"]))
    chiama(SRV.rispondi_offerta, {"azione": "rilancia",
                                  "importo": "65000"}, COMPRA, off_id)
    o, _ = leggi_off(off_id)
    prova("il rilancio del compratore: pavimento su, turno al venditore",
          ("proposta", 65_000, 75_000),
          (o["stato"], o["importo_sats"], o["contro_sats"]))
    chiama(SRV.rispondi_offerta, {"azione": "accetta"}, VENDE, off_id)
    o, _ = leggi_off(off_id)
    prova("accettata, col CONSOLIDAMENTO (la contro si azzera)",
          ("accettata", 65_000, 0),
          (o["stato"], o["importo_sats"], o["contro_sats"]))

    # LA REGINA: preventivo == compra, al sat, e la bolt11 quel totale
    INVOICES.clear()
    corpo = {"righe": corpo_righe([(a, 2), (b, 1)], bugiardo=True),
             "offerta_carrello_id": off_id, "consegna": "ritiro"}
    p = chiama(SRV.preventivo_ordine,
               {"righe": corpo_righe([(a, 2), (b, 1)]),
                "offerta_carrello_id": off_id})
    atteso = next(s["totale_sats"] for s in p["strade"]
                  if s["via"] == "ritiro")
    c = chiama(SRV.compra, corpo)
    prova("preventivo == compra, al sat", atteso, c["prezzo_sats"])
    # 90.000 lordi − 25.000 di accordo = 65.000 pattuiti; la
    # protezione (5%) si misura sul pattuito: 3.250 -> 68.250
    prova("il conto a mano: Σlordo − accordo + protezione", 68_250,
          c["prezzo_sats"])
    prova("...e l'accordo e' la differenza dal pattuito",
          (25_000, 65_000), (c["accordo_sats"], c["pattuito_sats"]))
    prova("la bolt11 chiede ESATTAMENTE quel totale",
          [c["prezzo_sats"]], INVOICES)
    con = SRV.db()
    con.row_factory = sqlite3.Row
    ordine = con.execute("SELECT * FROM ordini WHERE id=?",
                         (c["ordine_id"],)).fetchone()
    righe = con.execute("SELECT * FROM ordine_righe WHERE ordine_id=? "
                        "ORDER BY id", (c["ordine_id"],)).fetchall()
    con.close()
    merce = sum(r["unitario_sats"] * r["quantita"] for r in righe)
    prova("le righe dell'ordine restano LORDE", (90_000, 30_000),
          (merce, righe[0]["unitario_sats"]))
    # IL CLIENT SI IGNORA: il body chiedeva 4+3 pezzi, l'accordo ne
    # diceva 2+1 — comandano le figlie fotografate alla proposta
    prova("la quantita' dell'accordo comanda, non quella del client",
          [(a, 2), (b, 1)],
          [(r["annuncio_id"], r["quantita"]) for r in righe])
    prova("il bilancio torna, RILETTO dal database", ordine["prezzo_sats"],
          merce - ordine["sconto_sats"] - ordine["accordo_sats"]
          + ordine["spedizione_sats"] + ordine["protezione_sats"])
    o, _ = leggi_off(off_id)
    prova("la testata e' legata all'ordine nella stessa transazione",
          c["ordine_id"], o["ordine_id"])

    # il SALDO chiude il giro: verifica_pagamento -> _incassa_ordine,
    # l'offerta si conclude e lo stock scala
    chiama(SRV.verifica_pagamento, {}, COMPRA, c["ordine_id"])
    o, _ = leggi_off(off_id)
    con = SRV.db()
    stati = con.execute(
        "SELECT stato, quantita FROM annunci WHERE id IN (?,?) "
        "ORDER BY id", (a, b)).fetchall()
    con.close()
    prova("pagato: l'offerta si conclude", "conclusa", o["stato"])
    prova("...e lo stock scala riga per riga", [3, 4],
          [s["quantita"] for s in stati])


def prove_sconti_spenti():
    """[3] GLI SCONTI SPENTI SOTTO ACCORDO, provati girando il conto
    nei DUE mondi: lo stesso carrello sconta senza accordo e non
    sconta con — la forma non lo saprebbe dire."""
    print("\n[3] GLI SCONTI SPENTI — la regola del negozio e il codice")
    a, b = semina(sconto_pacco_criterio="pezzi", sconto_pacco_soglia=2,
                  sconto_pacco_percento=10)
    # SENZA accordo lo stesso carrello sconta: 10% di 90.000
    c0 = chiama(SRV.compra,
                {"righe": [{"annuncio_id": a, "quantita": 2},
                           {"annuncio_id": b, "quantita": 1}],
                 "consegna": "ritiro"})
    prova("senza accordo la regola del negozio sconta", 9_000,
          c0["sconto_sats"])
    # si annulla l'ordine-sonda: un 'creato' fresco non deve
    # intralciare le prove dopo (e' la finestra di _riservati)
    con = SRV.db()
    con.execute("DELETE FROM ordini WHERE id=?", (c0["ordine_id"],))
    con.execute("DELETE FROM ordine_righe WHERE ordine_id=?",
                (c0["ordine_id"],))
    con.commit()
    con.close()
    off_id = accordo([(a, 2), (b, 1)], 60_000)
    c = chiama(SRV.compra, {"righe": corpo_righe([(a, 2), (b, 1)]),
                            "offerta_carrello_id": off_id,
                            "consegna": "ritiro"})
    prova("SOTTO accordo la stessa regola tace: sconto zero",
          (0, 30_000), (c["sconto_sats"], c["accordo_sats"]))
    prova("...e il totale e' pattuito + protezione", 63_000,
          c["prezzo_sats"])
    # il codice sconto nel body: 400 esplicito, mai un silenzio
    con = SRV.db()
    con.execute("DELETE FROM ordini")
    con.execute("DELETE FROM ordine_righe")
    con.execute("UPDATE offerte SET ordine_id=0 WHERE id=?", (off_id,))
    con.commit()
    con.close()
    st, det = errore(SRV.compra,
                     {"righe": corpo_righe([(a, 2), (b, 1)]),
                      "offerta_carrello_id": off_id,
                      "codice_sconto": "SATOSHI10",
                      "consegna": "ritiro"})
    prova("un codice sopra l'accordo: 400 «già pattuito»", (400, True),
          (st, "già pattuito" in det))
    # ...e le offerte per-riga nemmeno: o l'uno o le altre
    st, det = errore(SRV.compra,
                     {"righe": corpo_righe([(a, 1), (b, 1)], off=7),
                      "offerta_carrello_id": off_id,
                      "consegna": "ritiro"})
    prova("accordo + offerte per-riga: non si sommano", (400, True),
          (st, "non si sommano" in det))


def prove_sped_gratis():
    """[4] LA SPEDIZIONE GRATIS MISURA IL PATTUITO: sopra il pattuito
    ma sotto il lordo NON scatta — se misurasse il lordo, questo caso
    la regalerebbe."""
    print("\n[4] LA SPEDIZIONE GRATIS misura il pattuito")
    a, b = semina(consegna="entrambe", spedizione_sats=1_000,
                  sped_gratis_soglia=70_000, sped_gratis_valuta="sats")
    off_id = accordo([(a, 2), (b, 1)], 60_000)   # lordo 90k, patto 60k
    p = chiama(SRV.preventivo_ordine,
               {"righe": [{"annuncio_id": a, "quantita": 2},
                          {"annuncio_id": b, "quantita": 1}],
                "offerta_carrello_id": off_id})
    # le vie del preventivo sono ritiro/casa/punto (il cantiere del
    # locker): la spedizione a casa e' la via «casa»
    sped = next(s for s in p["strade"] if s["via"] == "casa")
    prova("soglia 70k: il pattuito (60k) NON ci arriva — si paga",
          1_000, sped["spedizione_sats"])
    c = chiama(SRV.compra, {"righe": corpo_righe([(a, 2), (b, 1)]),
                            "offerta_carrello_id": off_id,
                            "consegna": "spedizione"})
    prova("...e compra dice lo stesso, al sat", sped["totale_sats"],
          c["prezzo_sats"])
    # con la soglia sotto il pattuito, scatta
    a, b = semina(consegna="entrambe", spedizione_sats=1_000,
                  sped_gratis_soglia=50_000, sped_gratis_valuta="sats")
    off_id = accordo([(a, 2), (b, 1)], 60_000)
    c = chiama(SRV.compra, {"righe": corpo_righe([(a, 2), (b, 1)]),
                            "offerta_carrello_id": off_id,
                            "consegna": "spedizione"})
    con = SRV.db()
    con.row_factory = sqlite3.Row
    o = con.execute("SELECT * FROM ordini WHERE id=?",
                    (c["ordine_id"],)).fetchone()
    con.close()
    prova("soglia 50k: il pattuito la supera e la spedizione e' offerta",
          (0, 1_000), (o["spedizione_sats"], o["sped_gratis_sats"]))


def prove_decadenze():
    """[5] LE DECADENZE DELLA TABELLA, una per una: e' la domanda
    esplicita di Andrea («cosa succede fra proposta e risposta»)."""
    print("\n[5] LE DECADENZE — la tabella, riga per riga")
    # a) un pezzo si esaurisce fra la proposta e l'accetta
    a, b = semina()
    off_id = proponi([(a, 2), (b, 1)], 60_000)
    con = SRV.db()
    con.execute("UPDATE annunci SET stato='venduto', quantita=0 "
                "WHERE id=?", (b,))
    con.commit()
    con.close()
    st, det = errore(SRV.rispondi_offerta, {"azione": "accetta"},
                     VENDE, off_id)
    o, _ = leggi_off(off_id)
    prova("esaurito fra proposta e accetta: 400 e l'offerta decade",
          (400, "decaduta"), (st, o["stato"]))
    # b) esaurito fra l'accetta e il pagamento
    a, b = semina()
    off_id = accordo([(a, 2), (b, 1)], 60_000)
    con = SRV.db()
    con.execute("UPDATE annunci SET stato='venduto', quantita=0 "
                "WHERE id=?", (b,))
    con.commit()
    con.close()
    st, det = errore(SRV.compra, {"righe": corpo_righe([(a, 2), (b, 1)]),
                                  "offerta_carrello_id": off_id,
                                  "consegna": "ritiro"})
    o, _ = leggi_off(off_id)
    prova("esaurito al pagamento: 400 col nome, e l'accordo decade",
          (400, True, "decaduta"),
          (st, "«Cosa 1»" in det, o["stato"]))
    # c) il PARZIALE non decade: accettare non riserva, e se il
    # venditore rifornisce entro la scadenza si paga
    a, b = semina()
    off_id = accordo([(a, 2), (b, 1)], 60_000)
    con = SRV.db()
    con.execute("UPDATE annunci SET quantita=1 WHERE id=?", (a,))
    con.commit()
    con.close()
    st, det = errore(SRV.compra, {"righe": corpo_righe([(a, 2), (b, 1)]),
                                  "offerta_carrello_id": off_id,
                                  "consegna": "ritiro"})
    o, _ = leggi_off(off_id)
    prova("stock parziale: 400 onesto e l'offerta RESTA accettata",
          (400, "accettata"), (st, o["stato"]))
    con = SRV.db()
    con.execute("UPDATE annunci SET quantita=5 WHERE id=?", (a,))
    con.commit()
    con.close()
    c = chiama(SRV.compra, {"righe": corpo_righe([(a, 2), (b, 1)]),
                            "offerta_carrello_id": off_id,
                            "consegna": "ritiro"})
    prova("...e rifornito, si paga alla cifra pattuita", 63_000,
          c["prezzo_sats"])
    # d) il prezzo cala SOTTO il pattuito: si paga il listino, mai di
    # piu' — il max(0, ...) e' la protezione del compratore
    a, b = semina()
    off_id = accordo([(a, 2), (b, 1)], 60_000)
    con = SRV.db()
    con.execute("UPDATE annunci SET prezzo_sats=15000 WHERE id IN (?,?)",
                (a, b))
    con.commit()
    con.close()
    c = chiama(SRV.compra, {"righe": corpo_righe([(a, 2), (b, 1)]),
                            "offerta_carrello_id": off_id,
                            "consegna": "ritiro"})
    prova("listino calato sotto il pattuito: si paga il MEGLIO dei due",
          (0, 47_250), (c["accordo_sats"], c["prezzo_sats"]))
    # e) modifica() del prezzo: le PENDENTI decadono, le ACCETTATE no
    a, b = semina()
    off_pend = proponi([(a, 1), (b, 1)], 31_000)
    off_acc = accordo([(a, 1), (b, 1)], 32_000, RIVALE)
    NOTIFICHE.clear()
    chiama(SRV.modifica_annuncio,
           {"titolo": "Cosa 0", "descrizione": "desc",
            "prezzo_sats": 25_000, "valuta": "sats",
            "categoria": "Altro", "zona": "Torino (TO)",
            "condizione": "buono"},
           VENDE, a)
    op, _ = leggi_off(off_pend)
    oa, _ = leggi_off(off_acc)
    prova("prezzo ritoccato: la pendente sul carrello decade",
          "decaduta", op["stato"])
    prova("...e l'accordo stretto sopravvive (la cifra e' assoluta)",
          "accettata", oa["stato"])
    prova("...col 🕊 al compratore della pendente", True,
          any(t == 111 and "decade" in msg for t, msg in NOTIFICHE))
    # f) la PAUSA dello stock (ricarica a zero): decadono anche le
    # accettate — la merce non c'e', l'accordo non e' onorabile
    a, b = semina()
    off_id = accordo([(a, 1), (b, 1)], 31_000)
    chiama(SRV.ricarica_quantita, {"quantita": 0}, VENDE, a)
    o, _ = leggi_off(off_id)
    prova("la pausa dello stock fa decadere anche l'accettata",
          "decaduta", o["stato"])
    # g) l'orologio: l'annuncio RIMOSSO lo prende scadenze_offerte
    a, b = semina()
    off_id = proponi([(a, 1), (b, 1)], 31_000)
    con = SRV.db()
    con.execute("UPDATE annunci SET stato='rimosso' WHERE id=?", (a,))
    con.commit()
    con.close()
    NOTIFICHE.clear()
    asyncio.run(SRV.scadenze_offerte())
    o, _ = leggi_off(off_id)
    prova("annuncio rimosso: l'orologio la fa decadere", "decaduta",
          o["stato"])
    prova("...e il 🕊 nomina il carrello", True,
          any(t == 111 and "carrello" in msg for t, msg in NOTIFICHE))
    # ...e la scadenza passata la fa SCADERE (un'altra parola: nessuno
    # ha tolto niente, e' finito il tempo)
    a, b = semina()
    off_id = proponi([(a, 1), (b, 1)], 31_000)
    con = SRV.db()
    con.execute("UPDATE offerte SET scadenza=1 WHERE id=?", (off_id,))
    con.commit()
    con.close()
    asyncio.run(SRV.scadenze_offerte())
    o, _ = leggi_off(off_id)
    prova("scadenza passata: scaduta, non decaduta", "scaduta",
          o["stato"])
    # h) le FERIE: un accordo di carrello vivo TRATTIENE la partenza
    a, b = semina()
    off_id = accordo([(a, 1), (b, 1)], 31_000)
    st, det = errore(SRV.imposta_ferie,
                     {"fino": int(time.time()) + 5 * 86400}, VENDE)
    prova("le ferie non partono con un accordo di carrello vivo",
          (400, True), (st, "sul carrello" in det))
    # i) l'esaurimento per VENDITA fa decadere il carrello del rivale
    # (il sito dentro _incassa_ordine, via il saldo vero)
    a, b = semina(quantita=1)
    off_rivale = proponi([(a, 1), (b, 1)], 31_000, RIVALE)
    c = chiama(SRV.compra, {"annuncio_id": a, "quantita": 1,
                            "consegna": "ritiro"})
    NOTIFICHE.clear()
    chiama(SRV.verifica_pagamento, {}, COMPRA, c["ordine_id"])
    o, _ = leggi_off(off_rivale)
    prova("il pezzo venduto a un altro fa decadere il carrello del "
          "rivale", "decaduta", o["stato"])
    prova("...col 🕊 che dice il pezzo", True,
          any(t == 333 and "Cosa 0" in msg for t, msg in NOTIFICHE))


def prove_fusione():
    """[6] LA FUSIONE: le testate migrano coi loro id, le figlie non
    restano MAI orfane — nemmeno quando l'auto-trattativa muore."""
    print("\n[6] LA FUSIONE — mai figlie orfane")
    a, b = semina()
    con = SRV.db()
    # `npub_accesso` NON e' un ornamento: senza, _guardie_fusione
    # risponde «questo account Nostr non esiste piu'» e la fusione non
    # parte — il collaudo direbbe verde su una migrazione mai avvenuta
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato,npub_accesso) "
                "VALUES(-500,'Nativo','neg55555',1,'abc123')")
    con.commit()
    con.close()
    # la meta' Nostr ha un'offerta di carrello VERSO il venditore 222
    off_id = proponi([(a, 1), (b, 1)], 31_000,
                     {"id": -500, "nome": "Nativo", "username": "",
                      "admin": False})
    SRV.esegui_fusione(111, -500)
    o, figlie = leggi_off(off_id)
    prova("la testata migra al superstite", 111, o["compratore_id"])
    prova("...e le figlie restano attaccate", 2, len(figlie))
    con = SRV.db()
    orfane = con.execute(
        "SELECT COUNT(*) AS n FROM offerte_righe r WHERE NOT EXISTS "
        "(SELECT 1 FROM offerte o WHERE o.id=r.offerta_id)"
    ).fetchone()["n"]
    con.close()
    prova("zero figlie orfane dopo la migrazione", 0, orfane)
    # l'AUTO-TRATTATIVA: la meta' Nostr aveva un carrello verso la
    # meta' Telegram — muore la testata E muoiono le figlie
    a, b = semina()
    con = SRV.db()
    con.execute("UPDATE annunci SET venditore_id=111 WHERE id IN (?,?)",
                (a, b))
    # `npub_accesso` NON e' un ornamento: senza, _guardie_fusione
    # risponde «questo account Nostr non esiste piu'» e la fusione non
    # parte — il collaudo direbbe verde su una migrazione mai avvenuta
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato,npub_accesso) "
                "VALUES(-500,'Nativo','neg55555',1,'abc123')")
    con.commit()
    con.close()
    off_auto = proponi([(a, 1), (b, 1)], 31_000,
                       {"id": -500, "nome": "Nativo", "username": "",
                        "admin": False})
    SRV.esegui_fusione(111, -500)
    con = SRV.db()
    resta = con.execute("SELECT COUNT(*) AS n FROM offerte WHERE id=?",
                        (off_auto,)).fetchone()["n"]
    orfane = con.execute(
        "SELECT COUNT(*) AS n FROM offerte_righe r WHERE NOT EXISTS "
        "(SELECT 1 FROM offerte o WHERE o.id=r.offerta_id)"
    ).fetchone()["n"]
    con.close()
    prova("l'auto-trattativa muore con la fusione", 0, resta)
    prova("...e le sue figlie con lei: zero orfane", 0, orfane)


def prove_ronda():
    """[7] LA RONDA TACE: dopo tutto questo — accordi pagati, decadute,
    fusioni — il libro mastro non deve avere niente da dire. Un
    controllo che suona sul normale e' peggio di nessun controllo."""
    print("\n[7] LA RONDA DEL LIBRO MASTRO tace su tutto questo")
    prova("nessun controllo suona", {},
          asyncio.run(SRV.controlla_libro_mastro()) or {})


def main():
    db = avvio()
    print(__doc__.strip().splitlines()[0])
    print(f"  database usa-e-getta: {db}")
    prove_proposta()
    prove_regina()
    prove_sconti_spenti()
    prove_sped_gratis()
    prove_decadenze()
    prove_fusione()
    prove_ronda()
    print(f"\n{PASSATE} passate, {FALLITE} fallite")
    sys.exit(1 if FALLITE else 0)


if __name__ == "__main__":
    main()
