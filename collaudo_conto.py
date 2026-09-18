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
cantiere per cui e' nato (ago 2026, «da 3 pezzi O da 25 €»), i codici
sconto, e dal set 2026 LE DUE PROMESSE INSIEME — sconto e spedizione
gratis con una spedizione VERA da pagare, e la percentuale che l'invito
del foglio Paga deve poter leggere anche sotto soglia. CHI TOCCA
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
import time
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

    async def invoice_finta(sats, memo, expiry=None, cassaforte=""):
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




def semina_codice(codice="SATOSHI10", pct=20, giorni=0, usi_max=0,
                  attivo=1, di_chi=222, tipo="percento", val_sats=0,
                  val_eur=0, valuta="eur"):
    """Un codice sconto in tabella. Torna il suo id.

    Dall'ago 2026 semina anche il tipo a CIFRA FISSA: i default lo
    lasciano 'percento', quindi ogni chiamata di ieri semina lo stesso
    codice di ieri — e' la regressione a costo zero, e se il tipo nuovo
    avesse spostato di un sat il mondo di prima le prove della sezione
    [6] diventerebbero rosse tutte insieme."""
    con = SRV.db()
    con.execute("DELETE FROM codici_sconto")
    scad = (int(time.time()) + giorni * 86400) if giorni else 0
    cur = con.execute(
        "INSERT INTO codici_sconto(venditore_id,codice,percento,scadenza,"
        "usi_max,attivo,creato,tipo,valore_sats,valore_eur,valore_valuta) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (di_chi, codice, pct, scad, usi_max, attivo, int(time.time()),
         tipo, val_sats, val_eur, valuta))
    con.commit()
    cid = cur.lastrowid
    con.close()
    return cid


def paga(ordine_id):
    """Porta l'ordine a 'locked', come farebbe il pagamento.

    Serve al tetto degli usi: due compra() di fila sullo stesso
    annuncio innescherebbero la RIPRESA del pentito, e il suo ramo di
    rinnovo chiama invoice_pagata — cioe' LNbits vero. Qui invece si
    fa quel che succede nella realta' fra un uso e l'altro: il primo
    ordine viene pagato."""
    con = SRV.db()
    con.execute("UPDATE ordini SET stato='locked' WHERE id=?", (ordine_id,))
    con.commit()
    con.close()


def usi_di(cid):
    """Quanti usi risultano consumati, letti come li legge il server."""
    con = SRV.db()
    n = SRV._usi_codice(con, cid)
    con.close()
    return n



def confronta(nome, richiesta, via="ritiro", alla_cassa=None):
    """LE QUATTRO DOMANDE, sulla stessa richiesta: il preventivo e la
    invoice dicono la stessa cifra? la bolt11 chiede quel totale? il
    bilancio torna RILEGGENDO dal database? lo sconto in colonna e'
    quello annunciato?
    Non sa niente di sconti ne' di criteri: chi tocca il conto le puo'
    fare sulla SUA regola passando un'altra richiesta."""
    INVOICES.clear()
    p = chiama(SRV.preventivo_ordine, richiesta)
    atteso = next(s["totale_sats"] for s in p["strade"] if s["via"] == via)
    # `alla_cassa` (set 2026): quel che la via chiede IN PIU' per
    # comprare davvero — a casa serve un indirizzo, e la consegna si
    # chiama «spedizione». Il default lascia ogni chiamata di ieri
    # identica, byte per byte.
    c = chiama(SRV.compra, {**richiesta, "consegna": via,
                            **(alla_cassa or {})})
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




def prove_codice_sconto():
    """I CODICI SCONTO (ago 2026): il venditore ne crea uno e lo da' a
    chi vuole; chi lo scrive alla cassa ha -X% sugli articoli.
    VINCE IL MAGGIORE fra il codice e la promessa del negozio: mai la
    somma, e a PARI MERITO vince il negozio — perche' un uso non si
    brucia per dare quello che era gia' dato."""
    print("\n[6] I CODICI SCONTO — «vince il maggiore»")

    # --- LA PROVA REGINA, col codice: preventivo == compra AL SAT
    a, b = semina("pezzi", 3, 0, 10)          # promessa: -10% da 3 pezzi
    semina_codice("SATOSHI10", 20)            # codice:   -20%
    p = confronta("codice sul mono",
                  {"annuncio_id": a, "quantita": 1,
                   "codice_sconto": "SATOSHI10"})
    prova("...e a scontare e' stato il CODICE", "codice", p["sconto_origine"])
    prova("...col suo 20%, non col 10% del negozio", 6_000, p["sconto_sats"])

    # il set: strada diversa nel codice, stessa risposta
    a, b = semina("pezzi", 3, 0, 10)
    semina_codice("SATOSHI10", 20)
    confronta("codice sul carrello",
              {"righe": [{"annuncio_id": a, "quantita": 1},
                         {"annuncio_id": b, "quantita": 1}],
               "codice_sconto": "SATOSHI10"})

    # --- VINCE IL MAGGIORE, nei tre casi
    a, _ = semina("pezzi", 3, 0, 30)          # promessa piu' generosa
    semina_codice("PICCOLO", 10)
    p = confronta("il negozio batte il codice",
                  {"annuncio_id": a, "quantita": 3, "codice_sconto": "PICCOLO"})
    prova("...vince il NEGOZIO", "negozio", p["sconto_origine"])
    prova("...col suo 30%", 27_000, p["sconto_sats"])
    prova("...e il codice si dice COPERTO, non rifiutato", "coperto",
          p["codice_sconto"]["stato"])

    # PARI MERITO: vince il negozio, e il codice NON consuma un uso
    a, _ = semina("pezzi", 3, 0, 10)
    cid = semina_codice("PARI", 10)
    p = confronta("pari merito",
                  {"annuncio_id": a, "quantita": 3, "codice_sconto": "PARI"})
    prova("...vince il negozio", "negozio", p["sconto_origine"])
    prova("...e l'uso NON si brucia per dare quel che era gia' dato",
          0, usi_di(cid))

    # LA SOMMA NON ESISTE: 30.000 x 3 con promessa -10% e codice -20%
    a, _ = semina("pezzi", 3, 0, 10)
    semina_codice("VENTI", 20)
    p = confronta("scattano tutte e due",
                  {"annuncio_id": a, "quantita": 3, "codice_sconto": "VENTI"})
    prova("...e lo sconto NON si somma", 18_000, p["sconto_sats"])

    # --- L'USO SI CONTA UNA VOLTA SOLA, E ALLA FATTURA
    a, _ = semina("pezzi", 0, 0, 0)           # nessuna promessa
    cid = semina_codice("CONTA", 10)
    for _ in range(3):
        chiama(SRV.preventivo_ordine,
               {"annuncio_id": a, "quantita": 1, "codice_sconto": "CONTA"})
    prova("tre preventivi non muovono il contatore", 0, usi_di(cid))
    chiama(SRV.compra, {"annuncio_id": a, "quantita": 1,
                        "consegna": "ritiro", "codice_sconto": "CONTA"})
    prova("...e la fattura si', UNA volta", 1, usi_di(cid))
    # LA RIPRESA DEL PENTITO non incrementa: e' la mutazione piu' facile
    # da scrivere e la piu' difficile da vedere
    r = chiama(SRV.compra, {"annuncio_id": a, "quantita": 1,
                            "consegna": "ritiro", "codice_sconto": "CONTA"})
    prova("...e la ripresa ripresenta la stessa fattura", True,
          bool(r.get("ripresa")))
    prova("...senza consumare un secondo uso", 1, usi_di(cid))

    # --- I DUE LIMITI, letti dal database
    a, _ = semina("pezzi", 0, 0, 0)
    semina_codice("VECCHIO", 10, giorni=-1)   # scaduto ieri
    p = chiama(SRV.preventivo_ordine,
               {"annuncio_id": a, "quantita": 1, "codice_sconto": "VECCHIO"})
    prova("un codice scaduto e' rifiutato", "rifiutato",
          p["codice_sconto"]["stato"])
    prova("...e il conto resta PIENO", 0, p["sconto_sats"])
    prova("...ma il preventivo risponde lo stesso (200, mai un errore)",
          30_000, p["articolo_sats"])

    # IL FILO DEL TETTO: l'uso N scatta, l'N+1 no. E' dove vive sempre
    # un off-by-one.
    a, _ = semina("pezzi", 0, 0, 0)
    cid = semina_codice("DUEVOLTE", 10, usi_max=2)
    for giro in (1, 2):
        c = chiama(SRV.compra, {"annuncio_id": a, "quantita": giro,
                                "consegna": "ritiro",
                                "codice_sconto": "DUEVOLTE"})
        prova(f"il tetto a 2: l'uso {giro} scatta", True,
              c["sconto_sats"] > 0)
        paga(c["ordine_id"])
    prova("...e gli usi contati sono due", 2, usi_di(cid))
    p = chiama(SRV.preventivo_ordine,
               {"annuncio_id": a, "quantita": 3, "codice_sconto": "DUEVOLTE"})
    prova("...il terzo no", "rifiutato", p["codice_sconto"]["stato"])
    # e la CORSA: chi ci prova lo stesso non fa nascere un ordine
    # scontato — il fail-fast lo ferma prima della invoice
    try:
        chiama(SRV.compra, {"annuncio_id": a, "quantita": 3,
                            "consegna": "ritiro",
                            "codice_sconto": "DUEVOLTE"})
        prova("...e la fattura non nasce", "400", "nessun errore")
    except SRV.HTTPException as e:
        prova("...e la fattura non nasce", 400, e.status_code)
    prova("...ne' si e' consumato un uso di troppo", 2, usi_di(cid))

    # --- IL CODICE NON ATTRAVERSA I NEGOZI
    a, _ = semina("pezzi", 0, 0, 0)
    semina_codice("ALTRUI", 20, di_chi=999)   # e' di un altro venditore
    p = chiama(SRV.preventivo_ordine,
               {"annuncio_id": a, "quantita": 1, "codice_sconto": "ALTRUI"})
    prova("il codice di un altro negozio e' rifiutato", "rifiutato",
          p["codice_sconto"]["stato"])
    prova("...e non sconta un sat", 0, p["sconto_sats"])

    # --- L'ANTI-ORACOLO: chi indovina non impara niente
    a, _ = semina("pezzi", 0, 0, 0)
    semina_codice("ESISTE", 10, attivo=0)     # esiste ma e' spento
    motivi = set()
    for tentativo in ("ESISTE", "NONESISTE", "ALTRO123"):
        p = chiama(SRV.preventivo_ordine,
                   {"annuncio_id": a, "quantita": 1,
                    "codice_sconto": tentativo})
        motivi.add((p["codice_sconto"]["stato"], p["codice_sconto"]["motivo"]))
    prova("esistente-ma-spento e inesistente si raccontano IDENTICI",
          1, len(motivi))

    # --- LA NORMALIZZAZIONE: si scrive come capita, vale lo stesso
    a, _ = semina("pezzi", 0, 0, 0)
    semina_codice("SATOSHI10", 10)
    p = chiama(SRV.preventivo_ordine,
               {"annuncio_id": a, "quantita": 1,
                "codice_sconto": " satoshi-10 "})
    prova("il codice si normalizza (minuscole, spazi, trattini)",
          "applicato", p["codice_sconto"]["stato"])
    prova("...e torna scritto come l'abbiamo capito", "SATOSHI10",
          p["codice_sconto"]["codice"])

    # --- LA DIVISIONE A RITROSO regge coi numeri, non solo di forma
    a, _ = semina("pezzi", 0, 0, 0, prezzo=10_000)
    semina_codice("TERZI", 10)
    c = chiama(SRV.compra, {"annuncio_id": a, "quantita": 3,
                            "consegna": "ritiro", "codice_sconto": "TERZI"})
    con = SRV.db()
    o = con.execute("SELECT * FROM ordini WHERE id=?",
                    (c["ordine_id"],)).fetchone()
    con.close()
    lordo = (o["prezzo_sats"] - o["spedizione_sats"] - o["protezione_sats"]
             + o["sconto_sats"])
    prova("la divisione a ritroso resta ESATTA col codice", 0, lordo % 3)
    prova("...e l'unitario e' quello di sempre", 10_000, lordo // 3)



def prove_codice_valore():
    """IL CODICE A CIFRA FISSA (ago 2026): «−10 €» invece di «−10%».

    `prove.py` gira i giudici e dice che l'aritmetica e' giusta; quel
    che non puo' fare e' far nascere un ORDINE — e le due cose che
    contano si vedono solo qui: che la bolt11 chieda esattamente quel
    che la pagina ha promesso, e che un codice a valore consumi un uso
    come il fratello a percentuale.
    LE QUATTRO DOMANDE le fa `confronta`, che di tipi non sa niente:
    e' precisamente il motivo per cui il tipo nuovo si innesta qui
    senza un ambiente suo."""
    print("\n[7] IL CODICE A CIFRA FISSA")

    # ---- 1. IL GIRO VERO, in euro. MILLE SATS = UN EURO, quindi
    # «−10 €» su un carrello da 30.000 sats deve togliere 10.000.
    a, _ = semina("pezzi", 99, 0, 0, prezzo=30_000)   # regola irraggiungibile
    cid = semina_codice("REGALO10", 0, tipo="valore", val_eur=10,
                        valuta="eur")
    p = confronta("codice −10 €", {"annuncio_id": a, "quantita": 1,
                                   "codice_sconto": "REGALO10"})
    prova("...toglie 10.000 sats (mille sats = un euro)", 10_000,
          p["sconto_sats"])
    # LA PERCENTUALE E' ZERO, e non «dedotta»: quel codice una
    # percentuale non ce l'ha, e inventargliela direbbe 33,33%.
    prova("...e la percentuale in ricevuta e' ZERO, non dedotta", 0,
          p["sconto_percento"])
    prova("...ma lo sconto e' dichiarato applicato", "applicato",
          p["codice_sconto"]["stato"])
    prova("...e l'origine dice che ha vinto il codice", "codice",
          p["sconto_origine"])
    prova("...e ha consumato il suo uso", 1, usi_di(cid))

    # ---- 2. IN SATS, senza mai guardare il cambio ------------------
    a2, _ = semina("pezzi", 99, 0, 0, prezzo=30_000)
    semina_codice("SATFISSI", 0, tipo="valore", val_sats=7_000,
                  valuta="sats")
    p2 = confronta("codice −7.000 sats", {"annuncio_id": a2, "quantita": 1,
                                          "codice_sconto": "SATFISSI"})
    prova("...toglie esattamente 7.000 sats", 7_000, p2["sconto_sats"])

    # ---- 3. VINCE IL MAGGIORE, coi due tipi a confronto -----------
    # ⚠️ LA SOGLIA A PEZZI E' 2 E LA QUANTITA' PURE, o la regola non
    # scatterebbe affatto (_sconto_pacco ha `minimo = 2` a criterio
    # pezzi) e il confronto proverebbe il codice contro il NULLA — cioe'
    # passerebbe per la ragione sbagliata. L'ha detto il collaudo al
    # primo giro, non la rilettura.
    # Articolo 2 x 30.000 = 60.000; la regola -10% ne toglie 6.000.
    a3, _ = semina("pezzi", 2, 0, 10, prezzo=30_000)
    semina_codice("GROSSO", 0, tipo="valore", val_eur=10, valuta="eur")
    p3 = confronta("il valore batte la regola", {"annuncio_id": a3,
                                                 "quantita": 2,
                                                 "codice_sconto": "GROSSO"})
    prova("...vince il codice (10.000 contro 6.000)", 10_000,
          p3["sconto_sats"])
    # ...e al contrario: un codice da 1 € perde contro il -10%
    a4, _ = semina("pezzi", 2, 0, 10, prezzo=30_000)
    cid4 = semina_codice("PICCOLO", 0, tipo="valore", val_eur=1,
                         valuta="eur")
    p4 = confronta("...e perde quando toglie di meno",
                   {"annuncio_id": a4, "quantita": 2,
                    "codice_sconto": "PICCOLO"})
    prova("...vince la regola del negozio (6.000)", 6_000,
          p4["sconto_sats"])
    prova("...e la ricevuta dice la percentuale DEL VINCITORE", 10,
          p4["sconto_percento"])
    # LA REGOLA DERIVATA, e si prova in una riga: un uso non si brucia
    # per dare quel che era gia' dato.
    prova("...e l'uso NON si e' bruciato", 0, usi_di(cid4))

    # ---- 4. SI LIMA AL CARRELLO, MAI GRATIS -----------------------
    # un buono da 50 € su un carrello da 20.000 sats (= 20 €)
    a5, _ = semina("pezzi", 99, 0, 0, prezzo=20_000)
    semina_codice("ENORME", 0, tipo="valore", val_eur=50, valuta="eur")
    p5 = confronta("un buono piu' grande del carrello",
                   {"annuncio_id": a5, "quantita": 1,
                    "codice_sconto": "ENORME"})
    prova("...si lima al carrello meno un sat", 19_999, p5["sconto_sats"])
    art = next(s for s in p5["strade"] if s["via"] == "ritiro")
    prova("...e chi compra paga comunque qualcosa", True,
          art["totale_sats"] >= 1)

    # ---- 5. IL 100%, che e' il tetto nuovo e non vuol dire gratis --
    a6, _ = semina("pezzi", 99, 0, 0, prezzo=30_000)
    semina_codice("TUTTO", 100)
    p6 = confronta("un codice al 100%", {"annuncio_id": a6, "quantita": 1,
                                         "codice_sconto": "TUTTO"})
    prova("...lascia UN SAT di articoli", 29_999, p6["sconto_sats"])
    prova("...e la ricevuta dice 100%", 100, p6["sconto_percento"])

    # ---- 6. I RIFIUTI, che restano quelli di sempre ---------------
    a7, _ = semina("pezzi", 99, 0, 0, prezzo=30_000)
    semina_codice("MORTO", 0, tipo="valore", val_eur=10, valuta="eur",
                  attivo=0)
    p7 = chiama(SRV.preventivo_ordine, {"annuncio_id": a7, "quantita": 1,
                                        "codice_sconto": "MORTO"})
    prova("un codice a valore in pausa e' rifiutato", "rifiutato",
          p7["codice_sconto"]["stato"])
    prova("...e il conto resta PIENO", 0, p7["sconto_sats"])
    # LA CIFRA A ZERO: il codice esiste, ma non sconta niente — ed e'
    # esattamente lo stato che il libro mastro chiama «non puo'
    # scattare». Alla cassa deve rispondere come un codice che non c'e'.
    semina_codice("VUOTO", 0, tipo="valore", val_eur=0, valuta="eur")
    p8 = chiama(SRV.preventivo_ordine, {"annuncio_id": a7, "quantita": 1,
                                        "codice_sconto": "VUOTO"})
    prova("un codice a valore con la cifra a zero e' rifiutato",
          "rifiutato", p8["codice_sconto"]["stato"])

    # ---- 7. LA DIVISIONE A RITROSO regge anche col valore ---------
    a9, _ = semina("pezzi", 99, 0, 0, prezzo=10_000)
    semina_codice("TRE", 0, tipo="valore", val_eur=6, valuta="eur")
    c9 = chiama(SRV.compra, {"annuncio_id": a9, "quantita": 3,
                             "consegna": "ritiro", "codice_sconto": "TRE"})
    con = SRV.db()
    o9 = con.execute("SELECT * FROM ordini WHERE id=?",
                     (c9["ordine_id"],)).fetchone()
    con.close()
    lordo9 = (o9["prezzo_sats"] - o9["spedizione_sats"]
              - o9["protezione_sats"] + o9["sconto_sats"])
    prova("la divisione a ritroso resta ESATTA col codice a valore",
          0, lordo9 % 3)
    prova("...e l'unitario e' quello di sempre", 10_000, lordo9 // 3)


A_CASA = {"consegna": "spedizione", "spedizione_via": "casa",
          "indirizzo": {"nome": "Mario Rossi", "via": "Via Roma 1",
                        "cap": "10100", "citta": "Torino",
                        "provincia": "TO", "telefono": "3330000000"}}


def semina_due_promesse(unita="eur", listino="sats"):
    """LE DUE PROMESSE DEL NEGOZIO INSIEME: spedizione gratis da 40 e
    sconto −10% da 25, tutt'e due nell'unita' `unita` ('eur' | 'sats').
    Tre annunci da 10 € — 10.000 sats col cambio tondo — nati nel
    listino `listino`, che spediscono a casa per 3.000 sats.
    Le soglie sono DIVERSE apposta: fra 25 e 40 lo sconto e' scattato
    e la spedizione no, che e' il caso in cui le due promesse si
    distinguono (e quello visto dal vivo il 19 set 2026)."""
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci", "codici_sconto"):
        con.execute(f"DELETE FROM {t}")
    in_eur = unita == "eur"
    con.execute(
        "INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
        "sconto_pacco_criterio,sconto_pacco_soglia,sconto_pacco_valore,"
        "sconto_pacco_valore_eur,sconto_pacco_valore_valuta,"
        "sconto_pacco_percento,sped_gratis_soglia,sped_gratis_soglia_eur,"
        "sped_gratis_valuta) VALUES(222,'Vende','neg22222',1,'valore',0,"
        "?,?,?,10,?,?,?)",
        (0 if in_eur else 25_000, 25 if in_eur else 0, unita,
         0 if in_eur else 40_000, 40 if in_eur else 0, unita))
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(111,'Compra','neg11111',1)")
    ids = []
    for n in range(3):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "prezzo_eur,categoria,zona,stato,creato,consegna,quantita,valuta,"
            "condizione,spedizione_sats) VALUES(222,?,'desc',10000,?,'Altro',"
            "'Torino (TO)','attivo',1,'entrambe',9,?,'buono',3000)",
            (f"Cosa {n}", 10 if listino == "eur" else 0, listino))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    return ids


def prove_due_promesse():
    """LE DUE PROMESSE INSIEME, e la percentuale dell'INVITO (19 set
    2026, il difetto visto dal vivo: nel foglio Paga l'avanzamento dello
    sconto era sparito e restava la sola spedizione).
    IL CONTO NON AVEVA MAI SBAGLIATO — a mancare era una chiave del
    preventivo — ma la domanda «lo sconto sopra soglia finisce DAVVERO
    nella fattura, anche quando insieme scatta la spedizione gratis?»
    non l'aveva mai fatta nessuno con le due promesse accese insieme e
    una spedizione VERA da pagare: tutte le sezioni qui sopra comprano
    col ritiro. Il conto a mano, col cambio tondo e la protezione al 5%
    sul NETTO:
      1 pezzo  = 10.000            + 3.000 + 500   = 13.500
      3 pezzi  = 30.000 − 3.000    + 3.000 + 1.350 = 31.350
      4 pezzi  = 40.000 − 4.000    + 0     + 1.800 = 37.800
    LA SPEDIZIONE GRATIS MISURA IL LORDO, come lo sconto: a 4 pezzi si
    pagano 36 € di articoli e la spedizione e' gratis lo stesso, perche'
    la soglia dei 40 guarda i 40 del listino — le due promesse sono
    indipendenti, e nessuna delle due misura l'altra."""
    print("\n[8] LE DUE PROMESSE INSIEME — sconto da 25, spedizione da 40")
    for unita in ("eur", "sats"):
        manca_sc = "mancano_eur" if unita == "eur" else "mancano_sats"
        manca_sg = ("mancano_sped_eur" if unita == "eur"
                    else "mancano_sped_sats")
        k = 1 if unita == "eur" else 1_000
        a, b, _ = semina_due_promesse(unita)
        p = confronta(f"[{unita}] un pezzo: sotto TUTTE E DUE",
                      {"annuncio_id": a, "quantita": 1}, "casa", A_CASA)
        prova("...il totale e' quello fatto a mano", 13_500,
              next(s["totale_sats"] for s in p["strade"]
                   if s["via"] == "casa"))
        # IL DIFETTO DEL 19 SET: qui usciva la sola `sconto_percento`,
        # che sotto soglia vale zero — e il client spegneva l'invito
        prova("...l'INVITO porta la percentuale della promessa", 10,
              p.get("sconto_promessa_percento"))
        prova("...mentre quella di chi HA SCONTATO resta a zero", 0,
              p["sconto_percento"])
        prova("...e quanto manca, per tutte e due", (15 * k, 30 * k),
              (p[manca_sc], p[manca_sg]))

        a, b, _ = semina_due_promesse(unita)
        p = confronta(f"[{unita}] tre pezzi: SCONTO si', spedizione no",
                      {"annuncio_id": a, "quantita": 3}, "casa", A_CASA)
        prova("...il totale e' quello fatto a mano", 31_350,
              next(s["totale_sats"] for s in p["strade"]
                   if s["via"] == "casa"))
        prova("...lo sconto e' il 10% del lordo", (3_000, 10, "negozio"),
              (p["sconto_sats"], p["sconto_percento"], p["sconto_origine"]))
        prova("...alla spedizione manca ancora il suo", 10 * k, p[manca_sg])

        a, b, _ = semina_due_promesse(unita)
        p = confronta(f"[{unita}] quattro pezzi: scattano TUTTE E DUE",
                      {"annuncio_id": a, "quantita": 4}, "casa", A_CASA)
        casa = next(s for s in p["strade"] if s["via"] == "casa")
        prova("...il totale e' quello fatto a mano", 37_800,
              casa["totale_sats"])
        prova("...sconto pieno E spedizione a zero", (4_000, 0),
              (p["sconto_sats"], casa["spedizione_sats"]))

        # IL CARRELLO: altra strada nel codice, stesse cifre
        a, b, _ = semina_due_promesse(unita)
        p = confronta(f"[{unita}] carrello da 2: sotto tutte e due",
                      {"righe": [{"annuncio_id": a, "quantita": 1},
                                 {"annuncio_id": b, "quantita": 1}]},
                      "casa", A_CASA)
        prova("...l'INVITO porta la percentuale anche nel carrello",
              (10, 0, 5 * k, 20 * k),
              (p.get("sconto_promessa_percento"), p["sconto_percento"],
               p[manca_sc], p[manca_sg]))

        a, b, _ = semina_due_promesse(unita)
        p = confronta(f"[{unita}] carrello da 3: SCONTO si', spedizione no",
                      {"righe": [{"annuncio_id": a, "quantita": 2},
                                 {"annuncio_id": b, "quantita": 1}]},
                      "casa", A_CASA)
        prova("...il totale e' quello del singolo a tre pezzi", 31_350,
              next(s["totale_sats"] for s in p["strade"]
                   if s["via"] == "casa"))

        a, b, _ = semina_due_promesse(unita)
        p = confronta(f"[{unita}] carrello da 4: scattano TUTTE E DUE",
                      {"righe": [{"annuncio_id": a, "quantita": 2},
                                 {"annuncio_id": b, "quantita": 2}]},
                      "casa", A_CASA)
        casa = next(s for s in p["strade"] if s["via"] == "casa")
        prova("...il totale e' quello del singolo a quattro pezzi",
              (37_800, 4_000, 0),
              (casa["totale_sats"], p["sconto_sats"],
               casa["spedizione_sats"]))

    # SOGLIE IN UN'UNITA', LISTINO NELL'ALTRA: l'avanzamento usa lo
    # STESSO cambio del conto, perche' lo conta il server nella stessa
    # chiamata che fa il conto — il client riceve, non calcola. Col
    # cambio tondo 10 € e 10.000 sats sono la stessa cosa, quindi le
    # cifre devono essere quelle di sopra in tutti e due gli incroci.
    a, _, _ = semina_due_promesse("sats", listino="eur")
    p = confronta("listino in EURO, soglie in SATS: tre pezzi",
                  {"annuncio_id": a, "quantita": 3}, "casa", A_CASA)
    prova("...sconto scattato, e alla spedizione mancano 10.000 sats",
          (3_000, 10_000, 0), (p["sconto_sats"], p["mancano_sped_sats"],
                               p["mancano_sped_eur"]))
    a, _, _ = semina_due_promesse("sats", listino="eur")
    p = chiama(SRV.preventivo_ordine, {"annuncio_id": a, "quantita": 2})
    prova("...e a due pezzi l'invito dice 5.000 sats al −10%",
          (10, 5_000, 0), (p.get("sconto_promessa_percento"),
                           p["mancano_sats"], p["mancano_eur"]))

    # IL CASO CHE LA FORMA DI PRIMA NON AVREBBE RETTO: un codice −5%
    # sconta GIA', e la promessa −10% e' ancora da raggiungere. Le due
    # percentuali sono due FATTI diversi e il preventivo li dice tutti
    # e due: chi ha scontato (5) e cosa promette l'invito (10).
    a, _, _ = semina_due_promesse("eur")
    semina_codice("CINQUE", 5)
    p = confronta("codice −5% sotto la soglia della promessa −10%",
                  {"annuncio_id": a, "quantita": 1,
                   "codice_sconto": "CINQUE"}, "casa", A_CASA)
    prova("...sconta il CODICE col suo 5, l'invito promette il 10",
          ("codice", 5, 10, 15),
          (p["sconto_origine"], p["sconto_percento"],
           p.get("sconto_promessa_percento"), p["mancano_eur"]))
    # ...e un codice che COPRE la promessa spegne l'invito: niente
    # percentuale da promettere, perche' non c'e' piu' niente da
    # guadagnare aggiungendo pezzi
    a, _, _ = semina_due_promesse("eur")
    semina_codice("VENTI", 20)
    p = chiama(SRV.preventivo_ordine, {"annuncio_id": a, "quantita": 1,
                                       "codice_sconto": "VENTI"})
    prova("un codice che copre: l'invito tace, percentuale compresa",
          (0, "", False),
          (p.get("sconto_promessa_percento"), p["sconto_criterio"],
           p["sconto_raggiungibile"]))


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
    prove_codice_sconto()
    prove_codice_valore()
    prove_due_promesse()
    prove_ronda()
    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
