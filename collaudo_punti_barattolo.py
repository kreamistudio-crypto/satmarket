# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEI PUNTI DI BARATTOLO: la prima rete che e' nostra
(ago 2026).

`prove.py` difende la FORMA — che il gate sia in lettura, che il
giudice sia puro, che una guardia non sparisca in un riordino. Quello
che non puo' fare e' far girare la cosa VERA: le sue prove non hanno
un database, non hanno un endpoint e non coniano una invoice.

E QUI IL RISCHIO NON E' TEORICO: la colonna nuova entra in DUE INSERT
che elencano i campi a mano, e un segnaposto in piu' o in meno non
fallisce leggendo il codice — **fallisce al primo acquisto, con un
500 e la fattura gia' coniata**. E' la stessa famiglia della colonna
`id` che `offerte_righe` non ha, che le prove non potevano vedere
perche' i cartoni gliela davano.

Le domande a cui risponde, e sono quelle su cui il commit si regge:

  · IL SERVER SI AVVIA con la colonna nuova, e i due INSERT scrivono
    davvero — mono e carrello, uno per uno;
  · IL GATE E' IN LETTURA: a punti spenti «Barattolo» non esce dalle
    reti di nessun venditore, e accendendo esce all'istante — nessuna
    scopa, nessun orologio, il patto di `sponsor_vivo`;
  · IL FAIL-CLOSED in tutti e tre i posti: l'id fuori catalogo, il
    punto spento al momento dell'acquisto, il codice negozio che non
    risolve. Meglio nessun punto che uno che porta al vuoto;
  · IL TESTO LO COMPONE IL SERVER: nell'ordine finisce quello del
    catalogo e mai una stringa arrivata dal client — o il giorno che
    il punto cambia indirizzo un ordine vecchio direbbe il falso;
  · IL MONDO DI IERI E' INTATTO: un ordine verso una rete di terzi si
    comporta come prima, byte per byte, e il campo libero resta.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. LNbits non
viene mai chiamato — le invoice si contano, non si chiedono — quindi
lo script gira anche senza rete e senza chiavi.

USO:  python collaudo_punti_barattolo.py
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
CAMBIO = 100_000.0
UTENTE = {"id": 111, "nome": "Compra", "username": "compra", "admin": False}

# Il catalogo di collaudo. Nel repo `PUNTI_BARATTOLO` e' VUOTO ed e'
# giusto — si entra su invito, uno alla volta — quindi qui se ne mette
# uno di cartone: e' l'unico modo di far girare per davvero la strada
# che il giorno del primo ristoratore sara' quella vera.
FINTI = (
    {"id": "da-mario", "nome": "Da Mario", "indirizzo": "Via Roma 1",
     "comune": "Milano (MI)", "orari": "lun-sab 9-19",
     "negozio": "neg22222"},
    {"id": "bar-luna", "nome": "Bar Luna", "indirizzo": "Via Po 9",
     "comune": "Torino (TO)", "negozio": "neg33333"},
)


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
    """Come `prova`, ma per i rifiuti: chiede il 400 E che il messaggio
    dica la cosa giusta. «scegli il punto» e «quel punto non c'e' piu'»
    sono due problemi diversi per chi legge, e mandano a cercare in due
    posti diversi."""
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
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-punti-"),
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

    async def invoice_finta(sats, memo, expiry=None):
        INVOICES.append(int(sats))
        return {"payment_hash": f"hash{len(INVOICES)}",
                "payment_request": f"lnbc{sats}collaudo{len(INVOICES)}"}

    async def cambio_finto():
        return CAMBIO

    async def zitta(*a, **k):
        return None

    async def mai_pagata(_hash):
        return False

    server.crea_invoice_escrow = invoice_finta
    server.invoice_pagata = mai_pagata
    server.cambio_btc_eur = cambio_finto
    server.notifica = zitta
    server.polso_ordini_admin = lambda *a, **k: None
    server.verifica_utente = lambda *a, **k: UTENTE

    # IL CATALOGO DI CARTONE si innesta DOPO l'import, ed e' l'unica
    # cosa che questo collaudo cambia del server: la cache si azzera a
    # mano perche' `_PUNTI` la riempie al primo giro e non tornerebbe
    # mai piu' a guardare la tupla.
    server.PUNTI_BARATTOLO = FINTI
    server.ID_PUNTI_BARATTOLO = tuple(p["id"] for p in FINTI)
    server._PUNTI = None
    return db


def accendi(*ids):
    """Il gesto del comando del bot, senza passare dal bot."""
    SRV.imposta_punti(list(ids))
    SRV._PUNTI = None


def chiama(fn, corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(fn(None))


def semina(reti="|Barattolo|", prezzo=30_000):
    """Un venditore con le sue reti e un annuncio che si spedisce."""
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute(
        "INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
        "spedizionieri,spedizioniere) VALUES(222,'Vende','neg22222',1,?,?)",
        (reti, [s for s in reti.split("|") if s][0] if reti else ""))
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(111,'Compra','neg11111',1)")
    ids = []
    for titolo in ("Cosa", "Altra"):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
            "spedizione_sats) VALUES(222,?,'desc',?,'Altro',"
            "'Torino (TO)','attivo',1,'spedizione',5,'sats','buono',1000)",
            (titolo, prezzo))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    return ids


def compra(aid, **extra):
    corpo = {"annuncio_id": aid, "quantita": 1,
             "consegna": "spedizione", "spedizione_via": "punto"}
    corpo.update(extra)
    return chiama(SRV.compra, corpo)


def carrello(ids, **extra):
    corpo = {"righe": [{"annuncio_id": a, "quantita": 1} for a in ids],
             "consegna": "spedizione", "spedizione_via": "punto"}
    corpo.update(extra)
    return chiama(SRV.compra, corpo)


def riga_ordine(oid):
    con = SRV.db()
    r = con.execute("SELECT * FROM ordini WHERE id=?", (oid,)).fetchone()
    con.close()
    return r


# ---------------------------------------------------------------
def prove_avvio():
    print("\n── IL SERVER SI AVVIA, E LA COLONNA C'E' ──")
    con = SRV.db()
    cols = {r[1] for r in con.execute("PRAGMA table_info(ordini)")}
    con.close()
    prova("la colonna dell'ordine nasce con la migrazione",
          True, "punto_barattolo" in cols)
    # ⚠️ LA DOMANDA CHE NESSUNA SENTINELLA PUO' FARE: che gli INSERT
    # abbiano tanti segnaposto quanti argomenti. Un mismatch qui non
    # si legge nel codice — si vede al primo acquisto, con la fattura
    # gia' coniata e un 500 in faccia a chi paga.
    prova("...e nasce vuota, cioe' il mondo di ieri",
          "", con_default("ordini", "punto_barattolo"))


def con_default(tabella, colonna):
    con = SRV.db()
    for r in con.execute(f"PRAGMA table_info({tabella})"):
        if r[1] == colonna:
            con.close()
            d = r[4]
            return "" if d in (None, "''") else d
    con.close()
    return None


def prove_gate():
    print("\n── IL GATE E' IN LETTURA, MAI UNA SCOPA ──")
    accendi()
    prova("a punti spenti la rete di casa non e' viva",
          False, SRV.rete_barattolo_viva())
    prova("...e non esce dalle reti del venditore che l'ha dichiarata",
          ["InPost"], SRV.reti_venditore("|Barattolo|InPost|", ""))
    # ⚠️ IL PERMESSO SI DEVE SCRIVERE: senza il quarto argomento la
    # rete non esce nemmeno al venditore che la sta guardando nel suo
    # cassetto — ed e' la riga per cui `barattolo` e' un ARGOMENTO e
    # non una lettura dentro il giudice.
    prova("...ma al venditore, nel suo cassetto, si mostra lo stesso",
          ["Barattolo", "InPost"],
          SRV.reti_venditore("|Barattolo|InPost|", "", True))

    accendi("da-mario")
    prova("accendendo un punto la rete e' viva ALL'ISTANTE",
          True, SRV.rete_barattolo_viva())
    # ⚠️ SI CHIAMA COME LO CHIAMA `compra`, col gate PASSATO: il
    # giudice e' puro e da solo risponde sempre col mondo di ieri —
    # e' il fail-closed, non un difetto. Chiamarlo senza il gate qui
    # proverebbe una strada che nel server non gira.
    gate = SRV.rete_barattolo_viva()
    prova("...e comincia a uscire a chi compra",
          ["Barattolo", "InPost"],
          SRV.reti_venditore("|Barattolo|InPost|", "", gate))
    prova("...e chi non l'ha dichiarata non se la ritrova",
          ["InPost"], SRV.reti_venditore("|InPost|", "", gate))

    # FAIL-CLOSED: un id scritto a mano sul VPS non accende niente
    SRV.scrivi_impostazione("punti_barattolo", "|mai-esistito|")
    SRV._PUNTI = None
    prova("un id fuori catalogo non accende niente",
          False, SRV.rete_barattolo_viva())


def prove_acquisto_mono():
    print("\n── L'ACQUISTO: il testo lo compone il SERVER ──")
    accendi("da-mario")
    aid, _ = semina()
    r = compra(aid, punto_barattolo="da-mario")
    o = riga_ordine(r["ordine_id"])
    prova("l'ordine nasce con l'id del punto in colonna",
          "da-mario", o["punto_barattolo"])
    # LA RIGA CHE VALE IL CANTIERE: il testo NON arriva dal client.
    prova("...e col testo composto dal catalogo, non dal payload",
          "Da Mario - Via Roma 1 - Milano (MI)", o["punto_ritiro"])
    prova("...sulla via punto, come sempre", 1, o["via_punto"])
    # e il TIPO lo dice il catalogo: dietro un punto nostro c'e' sempre
    # una persona, quindi non si chiede e non si legge dal client
    prova("...col tipo che lo dice il catalogo, mai chi compra",
          "banco", o["tipo_punto"])

    # il client mente: manda un testo suo. Non deve entrare.
    aid2, _ = semina()
    r2 = compra(aid2, punto_barattolo="da-mario",
                punto_ritiro="Casa mia, Via Falsa 1")
    o2 = riga_ordine(r2["ordine_id"])
    prova("un testo arrivato dal client non entra mai in colonna",
          "Da Mario - Via Roma 1 - Milano (MI)", o2["punto_ritiro"])


def prove_acquisto_set():
    print("\n── ...e il carrello scrive lo stesso ──")
    accendi("da-mario")
    a, b = semina()
    r = carrello([a, b], punto_barattolo="da-mario")
    o = riga_ordine(r["ordine_id"])
    prova("anche il carrello nasce col punto in colonna",
          "da-mario", o["punto_barattolo"])
    prova("...e col testo del catalogo",
          "Da Mario - Via Roma 1 - Milano (MI)", o["punto_ritiro"])
    con = SRV.db()
    n = con.execute("SELECT COUNT(*) c FROM ordine_righe "
                    "WHERE ordine_id=?", (r["ordine_id"],)).fetchone()["c"]
    con.close()
    prova("...con le sue due righe di merce", 2, n)

    # ⚠️ E ANCHE QUI IL CLIENT PUO' MENTIRE, ed e' il caso che la
    # tortura ha chiesto: la riga `punto = testo` vive in DUE posti —
    # uno per chiamante — e `_compra_set` sta PRIMA di `compra` nel
    # file, quindi una mutazione che la scrive `punto or testo` cade
    # sul RAMO DEL CARRELLO. Col caso solo nel mono restava viva: non
    # un buco del codice, un buco del banco.
    c, d2 = semina()
    r2 = carrello([c, d2], punto_barattolo="da-mario",
                  punto_ritiro="Casa mia, Via Falsa 1")
    o2 = riga_ordine(r2["ordine_id"])
    prova("...e un testo del client non entra nemmeno nel carrello",
          "Da Mario - Via Roma 1 - Milano (MI)", o2["punto_ritiro"])


def prove_rifiuti():
    print("\n── I TRE RIFIUTI, e il messaggio che li distingue ──")
    accendi("da-mario")
    aid, _ = semina()
    quanti = len(INVOICES)
    alza("sulla rete di casa senza scelta si rifiuta",
         lambda: compra(aid), "punto")
    alza("...e su un punto spento pure",
         lambda: compra(aid, punto_barattolo="bar-luna"), "punto")
    alza("...e su un id inventato",
         lambda: compra(aid, punto_barattolo="mai-esistito"), "punto")
    # ⚠️ LA META' CHE CONTA: il rifiuto arriva PRIMA della fattura, o
    # resterebbe una invoice viva senza un ordine su cui posarsi — la
    # lezione lunga di `pulisci_ordini_fantasma`.
    prova("...e nessuno dei tre conia una fattura", quanti, len(INVOICES))


def prove_regressione():
    print("\n── IL MONDO DI IERI: le reti di terzi ──")
    accendi("da-mario")
    aid, _ = semina(reti="|InPost|")
    r = compra(aid, punto_ritiro="Locker InPost, Via Po 1",
               tipo_punto="locker")
    o = riga_ordine(r["ordine_id"])
    prova("il testo libero resta il testo libero",
          "Locker InPost, Via Po 1", o["punto_ritiro"])
    prova("...e la colonna del punto nostro resta vuota",
          "", o["punto_barattolo"])
    prova("...col tipo che lo dice chi compra, come sempre",
          "locker", o["tipo_punto"])
    # e un punto di casa non vale su una rete di terzi
    aid2, _ = semina(reti="|InPost|")
    r2 = compra(aid2, punto_ritiro="Locker InPost, Via Po 1",
                tipo_punto="locker", punto_barattolo="da-mario")
    o2 = riga_ordine(r2["ordine_id"])
    prova("un punto di casa non entra su una rete di terzi",
          "", o2["punto_barattolo"])
    prova("...e il testo di quella rete non si tocca",
          "Locker InPost, Via Po 1", o2["punto_ritiro"])


def prove_titolare():
    print("\n── IL TITOLARE, dal codice negozio ──")
    prova("un codice negozio vero risolve nel suo tg_id",
          222, SRV.titolare_punto("neg22222"))
    prova("...e uno che non esiste risolve a ZERO, mai a un altro",
          0, SRV.titolare_punto("mai-visto"))
    prova("...e il vuoto non va nemmeno a chiedere", 0, SRV.titolare_punto(""))


def prove_spento_si_legge():
    print("\n── SPEGNERE NON RISCRIVE GLI ORDINI GIA' NATI ──")
    accendi("da-mario")
    aid, _ = semina()
    r = compra(aid, punto_barattolo="da-mario")
    oid = r["ordine_id"]
    accendi()          # il comando del bot lo spegne
    o = riga_ordine(oid)
    prova("l'ordine tiene il suo punto anche a rete spenta",
          "da-mario", o["punto_barattolo"])
    prova("...e il testo dove sta il pacco resta leggibile",
          "Da Mario - Via Roma 1 - Milano (MI)", o["punto_ritiro"])
    # ⚠️ E il punto si ritrova ANCORA per id, che e' la riga da non
    # ammorbidire: chi ha un pacco in giro deve poter sapere dov'e'.
    prova("...e il catalogo lo risolve ancora per id",
          "Da Mario", SRV.punto_barattolo("da-mario").get("nome"))


def main():
    print("=" * 58)
    print("  IL COLLAUDO DEI PUNTI DI BARATTOLO")
    print("=" * 58)
    avvio()
    prove_avvio()
    prove_gate()
    prove_acquisto_mono()
    prove_acquisto_set()
    prove_rifiuti()
    prove_regressione()
    prove_titolare()
    prove_spento_si_legge()
    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
