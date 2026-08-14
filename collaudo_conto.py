# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL CONTO: preventivo == compra, AL SAT (ago 2026).

`prove.py` difende la FORMA — che le pure siano pure, che i chiamanti
siano quattro, che una guardia non sparisca in un riordino. Quello che
non puo' fare e' far girare il conto VERO: le sue prove non hanno un
database, non hanno un endpoint e non coniano una invoice.

Questo script chiude quel buco. Fa partire il SERVER VERO su un
database usa-e-getta, con LNbits finto, e chiede la sola cosa che
conta davvero: che la cifra mostrata a chi compra e la cifra che
finisce nella fattura siano LA STESSA, al sat.

LA PROVA REGINA E' QUELLA, e vale ogni volta che qualcuno tocca il
conto — non solo lo sconto. Se preventivo e invoice divergono, il
compratore vede un prezzo e ne paga un altro: e' il difetto peggiore
che questo progetto possa avere, e non fallisce da solo — nessuna
eccezione, nessun log, solo due numeri diversi.

Accanto ci sono le altre tre domande che si fanno insieme a quella:
  · la BOLT11 chiede esattamente il totale che finisce in colonna
    (se la fattura chiedesse il netto e `prezzo_sats` tenesse il
    lordo, il payout pretenderebbe dalla cassaforte piu' di quanto
    quell'ordine ha versato — e la cintura di paga_venditore non lo
    vedrebbe, perche' per lei i conti tornerebbero);
  · l'identita' di bilancio RILETTA DAL DATABASE, non dalla risposta;
  · la ronda del libro mastro, che su tutto questo deve TACERE.

COSA COPRE OGGI: lo sconto carrello coi suoi due criteri, che e' il
cantiere per cui e' nato (ago 2026, «da 3 pezzi O da 25 €»). CHI TOCCA
IL CONTO CI AGGIUNGA IL SUO CASO invece di rifarsi un ambiente: la
funzione `confronta()` non sa niente dello sconto — prende una
richiesta e verifica le quattro cose qui sopra, qualunque sia la
regola che le ha prodotte.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. LNbits non
viene mai chiamato — le invoice si contano, non si chiedono — quindi
lo script gira anche senza rete e senza chiavi, ed e' il motivo per
cui non serve la produzione per fidarsi del suo esito.

USO:  python collaudo_conto.py
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None          # il modulo server, importato in avvio()
INVOICES = []       # le cifre che la bolt11 finta ha chiesto

# 1 BTC = 100.000 €, cioe' MILLE SATS = UN EURO: ogni cifra si legge a
# mente nelle due unita', e gli asserti dicono quello che sembrano dire
CAMBIO = 100_000.0

UTENTE = {"id": 111, "nome": "Compra", "username": "compra", "admin": False}


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
    NETTO, quindi e' anche il modo di accorgersi se lo sconto smettesse
    di entrare nel conto prima di lei."""
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
    # I SEGNAPOSTO DEL CONFIG D'ESEMPIO, e non un «non-si-usa»
    # qualunque: lo scanner dei segreti in CI cerca queste due chiavi
    # per NOME con un valore non vuoto — e' l'unico modo di riconoscere
    # trentadue esadecimali che somigliano a mezzo mondo — e lascia
    # passare solo cio' che contiene INCOLLA_QUI. Qui il valore non
    # serve a niente (LNbits non si chiama mai), quindi si usa la
    # convenzione di casa invece di allargare lo scanner: una regola
    # aggirata da un'altra strada e' una regola morta.
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

    async def invoice_finta(sats, memo, expiry=None):
        """LNbits non si chiama mai: la cifra si annota e basta. E' lei
        che poi si confronta con `prezzo_sats`."""
        INVOICES.append(int(sats))
        return {"payment_hash": f"hash{len(INVOICES)}",
                "payment_request": f"lnbc{sats}collaudo{len(INVOICES)}"}

    async def cambio_finto():
        return CAMBIO

    server.crea_invoice_escrow = invoice_finta
    server.cambio_btc_eur = cambio_finto
    # le notifiche non c'entrano col conto, e senza bot direbbero solo
    # righe in console
    server.notifica = lambda *a, **k: None
    server.polso_ordini_admin = lambda *a, **k: None
    server.verifica_utente = lambda *a, **k: UTENTE
    return db


def chiama(fn, corpo):
    """Gli endpoint del conto leggono il body da leggi_json e l'utente
    da verifica_utente: si sostituiscono tutti e due e si chiamano
    davvero, invece di rifare a mano quello che fanno."""
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(fn(None))


def semina(criterio, soglia, valore_eur, pct, prezzo=30_000, quantita=9,
           valuta_soglia="eur"):
    """Un venditore con la sua regola e due annunci, piu' il
    compratore. 30.000 sats = 30 € col cambio tondo qui sopra."""
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute(
        "INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
        "sconto_pacco_criterio,sconto_pacco_soglia,sconto_pacco_valore,"
        "sconto_pacco_valore_eur,sconto_pacco_valore_valuta,"
        "sconto_pacco_percento) VALUES(222,'Vende','neg22222',1,?,?,0,?,?,?)",
        (criterio, soglia, valore_eur, valuta_soglia, pct))
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(111,'Compra','neg11111',1)")
    ids = []
    for n in range(2):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(222,?,'desc',?,'Altro','Torino (TO)','attivo',1,"
            "'ritiro',?,'sats','buono')", (f"Cosa {n}", prezzo, quantita))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    return ids


def confronta(nome, richiesta, via="ritiro"):
    """LE QUATTRO DOMANDE, sulla stessa richiesta: il preventivo e la
    invoice dicono la stessa cifra? la bolt11 chiede quel totale? il
    bilancio torna RILEGGENDO dal database? lo sconto in colonna e'
    quello annunciato?
    Non sa niente di sconti ne' di criteri: chi tocca il conto le puo'
    fare sulla SUA regola passando un'altra richiesta."""
    INVOICES.clear()
    p = chiama(SRV.preventivo_ordine, richiesta)
    atteso = next(s["totale_sats"] for s in p["strade"] if s["via"] == via)
    c = chiama(SRV.compra, dict(richiesta, consegna=via))
    prova(f"{nome}: preventivo == compra, al sat", atteso, c["prezzo_sats"])
    prova(f"{nome}: ...e la bolt11 chiede quel totale",
          [c["prezzo_sats"]], INVOICES)
    con = SRV.db()
    con.row_factory = sqlite3.Row
    o = con.execute("SELECT * FROM ordini WHERE id=?",
                    (c["ordine_id"],)).fetchone()
    righe = con.execute("SELECT * FROM ordine_righe WHERE ordine_id=?",
                        (c["ordine_id"],)).fetchall()
    con.close()
    if righe:      # il set: la testata deve quadrare con la sua merce
        merce = sum(r["unitario_sats"] * r["quantita"] for r in righe)
        prova(f"{nome}: il bilancio torna, riletto dal database",
              o["prezzo_sats"],
              merce - o["sconto_sats"] + o["spedizione_sats"]
              + o["protezione_sats"])
    prova(f"{nome}: lo sconto in colonna e' quello del preventivo",
          p["sconto_sats"], o["sconto_sats"])
    return p


def prove_due_criteri():
    """I DUE CRITERI INSIEME (ago 2026): «da 3 pezzi O da 25 € di
    articoli», e basta che ne scatti uno. La percentuale e' UNA, quindi
    le gambe sono due STRADE per lo stesso sconto: la prova che conta
    e' quella che si accorgerebbe di una somma travestita."""
    print("\n[1] I DUE CRITERI INSIEME — «da 3 pezzi O da 25 €»")
    a, _ = semina("entrambi", 3, 25, 10)          # 30.000 sats = 30 €
    p = confronta("un pezzo (scatta a VALORE)",
                  {"annuncio_id": a, "quantita": 1})
    prova("...lo sconto c'e'", 3_000, p["sconto_sats"])
    prova("...e si nomina la gamba che l'ha fatto scattare", "valore",
          p["sconto_criterio"])

    a, _ = semina("entrambi", 3, 25, 10, prezzo=5_000)
    p = confronta("tre pezzi piccoli (scatta a PEZZI)",
                  {"annuncio_id": a, "quantita": 3})
    prova("...lo sconto c'e'", 1_500, p["sconto_sats"])
    prova("...e la gamba nominata e' quella", "pezzi", p["sconto_criterio"])

    a, _ = semina("entrambi", 3, 25, 10, prezzo=5_000)
    p = confronta("due pezzi piccoli: NESSUNA gamba scatta",
                  {"annuncio_id": a, "quantita": 2})
    prova("...e il prezzo resta pieno", 0, p["sconto_sats"])

    # LA PROVA CHE SI ACCORGE DI UNA SOMMA: 90.000 sats di articoli
    # superano tutte e due le soglie, e lo sconto deve restare −10% —
    # mai −20%, che sarebbe una cifra che nessuno ha scritto nel
    # cassetto (e che bucherebbe il tetto della leva)
    a, _ = semina("entrambi", 3, 25, 10)
    p = confronta("tre pezzi grandi: scattano TUTTE E DUE",
                  {"annuncio_id": a, "quantita": 3})
    prova("...e lo sconto NON raddoppia", 9_000, p["sconto_sats"])


def prove_set():
    """Il carrello: stesse regole, altra strada nel codice."""
    print("\n[2] IL SET, con le stesse regole")
    a, b = semina("entrambi", 3, 25, 10, prezzo=5_000)
    righe = [{"annuncio_id": a, "quantita": 2},
             {"annuncio_id": b, "quantita": 1}]
    p = confronta("carrello da 3 pezzi (scatta a PEZZI)", {"righe": righe})
    prova("...lo sconto c'e'", 1_500, p["sconto_sats"])

    a, b = semina("entrambi", 3, 25, 10, prezzo=5_000)
    righe = [{"annuncio_id": a, "quantita": 1},
             {"annuncio_id": b, "quantita": 1}]
    p = confronta("carrello da 2 pezzi: nessuna gamba", {"righe": righe})
    prova("...e il prezzo resta pieno", 0, p["sconto_sats"])


def prove_invito():
    """L'INVITO mostra UNA gamba, la piu' vicina — e mai una che quello
    stock non puo' percorrere."""
    print("\n[3] L'INVITO: la gamba PIU' VICINA, e una sola")
    a, _ = semina("entrambi", 3, 25, 10, prezzo=5_000)
    # 1 pezzo su 3 = 33% · 5 € su 25 = 20% → vincono i PEZZI
    p = chiama(SRV.preventivo_ordine, {"annuncio_id": a, "quantita": 1})
    prova("un pezzo piccolo: invita sui PEZZI", ("pezzi", 2),
          (p["sconto_criterio"], p["mancano_pezzi"]))
    prova("...e la chiave dell'altra unita' tace", 0, p["mancano_eur"])

    a, _ = semina("entrambi", 3, 20, 10, prezzo=18_000)
    # 1 pezzo su 3 = 33% · 18 € su 20 = 90% → vince il VALORE
    p = chiama(SRV.preventivo_ordine, {"annuncio_id": a, "quantita": 1})
    prova("un pezzo caro: invita sul VALORE", ("valore", 2),
          (p["sconto_criterio"], p["mancano_eur"]))
    prova("...e la chiave dei pezzi tace", 0, p["mancano_pezzi"])

    # LA RAGGIUNGIBILITA': un invito verso una strada che questo stock
    # non puo' percorrere chiede una cosa che non si puo' fare
    a, _ = semina("entrambi", 3, 25, 10, prezzo=5_000, quantita=1)
    p = chiama(SRV.preventivo_ordine, {"annuncio_id": a, "quantita": 1})
    prova("stock 1: nessuna gamba raggiungibile, niente invito",
          (False, ""), (p["sconto_raggiungibile"], p["sconto_criterio"]))

    a, _ = semina("entrambi", 3, 25, 10, prezzo=15_000, quantita=2)
    # 2 pezzi = 30 € ≥ 25: la gamba a VALORE si puo' percorrere, quella
    # a pezzi no (stock 2 < 3) — e l'invito deve indicare quella buona
    p = chiama(SRV.preventivo_ordine, {"annuncio_id": a, "quantita": 1})
    prova("stock 2: si invita sulla gamba PERCORRIBILE", ("valore", True),
          (p["sconto_criterio"], p["sconto_raggiungibile"]))


def prove_regressione():
    """I CRITERI SINGOLI, identici al sat: e' la regressione dei negozi
    che c'erano gia'. Se il criterio nuovo avesse spostato di un sat il
    mondo di prima, queste diventerebbero rosse tutte insieme."""
    print("\n[4] LA REGRESSIONE: i criteri singoli, identici al sat")
    for crit, sog, val, nome, qta, atteso in (
            ("pezzi", 3, 0, "solo pezzi, sotto soglia", 2, 0),
            ("pezzi", 3, 0, "solo pezzi, sopra soglia", 3, 1_500),
            ("valore", 0, 25, "solo valore, sotto soglia", 1, 0),
            ("valore", 0, 25, "solo valore, sopra soglia", 6, 3_000)):
        a, _ = semina(crit, sog, val, 10, prezzo=5_000)
        p = confronta(nome, {"annuncio_id": a, "quantita": qta})
        prova(f"{nome}: la cifra e' quella di sempre", atteso,
              p["sconto_sats"])
    # ...e un negozio SENZA regola non sconta e non esplode
    a, _ = semina("pezzi", 0, 0, 0, prezzo=5_000)
    p = confronta("negozio senza nessuna promessa",
                  {"annuncio_id": a, "quantita": 3})
    prova("...e non c'e' nessuno sconto", 0, p["sconto_sats"])


def prove_ronda():
    """La ronda del libro mastro LEGGE E BASTA, e su un database sano
    deve TACERE: un allarme che suona sul normale e' peggio di nessun
    allarme."""
    print("\n[5] LA RONDA DEL LIBRO MASTRO tace su tutto questo")
    prova("nessun controllo suona", {},
          asyncio.run(SRV.controlla_libro_mastro()) or {})


def main():
    db = avvio()
    print(__doc__.strip().splitlines()[0])
    print(f"  database usa-e-getta: {db}")
    prove_due_criteri()
    prove_set()
    prove_invito()
    prove_regressione()
    prove_ronda()
    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
