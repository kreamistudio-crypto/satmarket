# -*- coding: utf-8 -*-
"""
UNA RECENSIONE PER SCAMBIO, NELLA MEDIA DI SEMPRE (set 2026).

A scambio P2P concluso le due parti si recensiscono come si
recensiscono nel mercatino — stelle e commento — e quel voto finisce
nella STESSA tabella e nella STESSA media: «una reputazione sola».

`prove.py` difende la FORMA (i giudici sui loro casi, le sentinelle
del client, la parita' fra il gesto e la rotta). Quello che non puo'
fare e' far girare il giro intero su un database vero. Qui si cammina:

  1. lo scambio concluso: A recensisce B, B recensisce A — UNA per
     parte, e le due medie si muovono;
  2. LA MEDIA E' UNA SOLA: chi ha gia' un feedback del mercatino se lo
     vede mediare con quello dello scambio, e `n_recensori` conta le
     PERSONE — le due strade non fanno due conti;
  3. il DOPPIONE: la seconda recensione della stessa parte trova il
     database, non una SELECT gentile;
  4. lo scambio NON CONCLUSO: rifiutato, e nessuna riga scritta;
  5. l'altra parte SENZA PROFILO da noi (chi prende entrando da Nostr,
     chi scambia da un altro client): rifiutata, con la sua ragione —
     e la rotta che apre il foglio lo dice PRIMA, che e' il motivo per
     cui esiste;
  6. l'ESTRANEO prende il 403, non il 400 dello stato;
  7. la provenienza si vede nel negozio («da uno scambio P2P») e la
     media resta una;
  8. il posto di chi ha preso non si ruba a cose fatte (o si
     dirotterebbe la recensione di un altro);
  9. l'invito nella notifica compare SOLO dove porta a qualcosa;
 10. (12 ott 2026) chi entra da Nostr e' riconosciuto come tutti: la
     presa si annota, la recensione si apre nei due versi; lo scambio di
     prima (presa mai annotata) non si recupera. Prima diceva:
     L'INTERRUTTORE del riconoscimento: chi entra da Nostr prende un
     ordine e resta invisibile — nessuna recensione, in nessuno dei due
     versi — poi lo accende, e dal prossimo scambio le due parti si
     recensiscono;
 11. e la fusione di due account non esplode sulle recensioni fra le
     due meta' (ULTIMA, che porta via la meta' Nostr da `utenti`).

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. Nessuna
rete: ne' LNbits, ne' relay, ne' coordinatore.

USO:  python collaudo_recensione_p2p.py
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
DETTO = []          # (destinatario, testo) di ogni notifica

SCAMBIO = "992e288e-1111-4a2b-9c3d-000000000001"
SCAMBIO2 = "992e288e-2222-4a2b-9c3d-000000000002"
APERTO = "992e288e-3333-4a2b-9c3d-000000000003"
IGNOTO = "992e288e-4444-4a2b-9c3d-000000000004"
FUSO = "992e288e-5555-4a2b-9c3d-000000000005"
DA_NOSTR = "992e288e-6666-4a2b-9c3d-000000000006"
DA_NOSTR2 = "992e288e-7777-4a2b-9c3d-000000000007"


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

    async def json(self):
        return self.dati


def avvio():
    """Il config finto PRIMA di importare server."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("ATTENTO: server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-recensione-"),
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
    # LA LEVA DEL P2P CEDE, non la regola: le rotte che REGISTRANO
    # vogliono la funzione attiva per quella persona, e nel config
    # finto non c'e' nessun coordinatore da raggiungere. Quel gate ha
    # le sue prove altrove; qui si cammina su quel che viene dopo.
    server._p2p_per = lambda tg_id: {"attivo": True}
    server.premia_distintivi = zitto
    server.premia_xp = zitto
    server.polso_ordini_admin = zitto
    return db


def come(tg_id, admin=False):
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "first_name": f"U{tg_id}",
        "username": f"u{tg_id}", "admin": admin}


def corpo_json(d):
    """Il body, dalle due porte: le rotte del P2P leggono da
    `leggi_json`, quelle vecchie del mercatino pure — e la Busta serve
    a chi chiama `req.json()` da se'. Una sola verita' per il giro."""
    async def leggi(_req):
        return d
    SRV.leggi_json = leggi


def chiama(fn, corpo=None):
    corpo_json(corpo or {})
    return asyncio.run(fn(Busta(corpo or {})))


def errore(fn, corpo=None):
    """Il codice e il messaggio di un rifiuto, o None se e' passato."""
    try:
        chiama(fn, corpo)
        return None
    except Exception as e:
        return (getattr(e, "status_code", type(e).__name__),
                str(getattr(e, "detail", e)))


def con_db():
    con = SRV.db()
    con.row_factory = sqlite3.Row
    return con


def utente(tg_id):
    con = con_db()
    u = con.execute("SELECT * FROM utenti WHERE tg_id=?", (tg_id,)).fetchone()
    con.close()
    return dict(u)


def recensioni(scambio):
    con = con_db()
    r = [dict(x) for x in con.execute(
        "SELECT da_tg_id, per_tg_id, voto, commento, ordine_id FROM feedback "
        "WHERE scambio=? ORDER BY da_tg_id", (scambio,))]
    con.close()
    return r


def preso_da(ordine):
    con = con_db()
    r = con.execute("SELECT preso_da FROM p2p_ordini WHERE ordine=?",
                    (ordine,)).fetchone()
    con.close()
    return r["preso_da"] if r else None


def concludi(ordine):
    """Lo scambio si chiude: e' quel che scriverebbe il giro del libro
    vedendo il 38383 a `success`. Qui a mano, che di relay non ce n'e'."""
    con = con_db()
    con.execute("UPDATE p2p_ordini SET stato='success' WHERE ordine=?",
                (ordine,))
    con.commit()
    con.close()


def riconosce(tg_id):
    con = con_db()
    r = con.execute("SELECT riconosci_p2p FROM utenti WHERE tg_id=?",
                    (tg_id,)).fetchone()
    con.close()
    return r["riconosci_p2p"] if r else None


def quante_righe():
    con = con_db()
    n = con.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
    con.close()
    return n


def semina():
    """Due persone, e gli scambi che il server ha visto passare.
    111 pubblica, 222 prende: sono i due posti di `p2p_ordini`."""
    con = con_db()
    for t in ("feedback", "p2p_ordini", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute("UPDATE utenti SET rating=0, n_feedback=0, n_recensori=0")
    for tg, nome, neg in ((111, "Chi pubblica", "neg11111"),
                          (222, "Chi prende", "neg22222"),
                          (333, "Un estraneo", "neg33333"),
                          (-77, "Da Nostr", "neg77777")):
        # `npub_accesso` solo a chi e' nato da Nostr: senza, le
        # guardie della fusione lo rimandano indietro (caso 10)
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address,npub_accesso) VALUES(?,?,?,1,'',?)",
                    (tg, nome, neg, "npub1collaudo" if tg < 0 else ""))
    adesso = int(time.time())
    for ordine, tg_id, preso_da, stato in (
            (SCAMBIO, 111, 222, "success"),
            (SCAMBIO2, 111, 222, "success"),
            (APERTO, 111, 222, "in-progress"),
            # chi ha preso entrando da Nostr non viene annotato: il
            # posto resta a zero, ed e' il caso 5
            (IGNOTO, 111, 0, "success"),
            (FUSO, 111, -77, "success"),
            # i due ordini del caso 11: nascono VIVI e senza nessuno
            # nel posto di chi prende, perche' la presa si dichiara a
            # scambio in corso — a cose fatte quel posto non si prende
            # piu' (ed e' una delle cose che il caso prova)
            (DA_NOSTR, 111, 0, "in-progress"),
            (DA_NOSTR2, 111, 0, "in-progress")):
        con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,"
                    "lato,maker,visto,preso_da) VALUES(?,?,?,?,'sell',1,?,?)",
                    (ordine, tg_id, adesso, stato, adesso, preso_da))
    # LE PARTI LE DICE MOSTROD (23 set 2026, la cura di A1): senza la sua
    # riga in `p2p_scambi` una presa dichiarata resta in attesa e nessuno
    # vede l'altra parte. Qui e' come se avesse gia' parlato di ogni
    # scambio: ordini `sell`, ha preso chi compra. IGNOTO resta senza
    # riga (un altro client, mai una parola).
    for ordine, compra in ((SCAMBIO, 222), (SCAMBIO2, 222), (APERTO, 222),
                           (FUSO, -77), (DA_NOSTR, -77), (DA_NOSTR2, -77)):
        con.execute("INSERT OR REPLACE INTO p2p_scambi(ordine, compratore, "
                    "venditore, preso_dal, giro, aggiornato) "
                    "VALUES(?,?,111,'buyer',1,?)", (ordine, compra, adesso))
    con.commit()
    con.close()


def main():
    avvio()
    semina()
    print("\n[1. lo scambio concluso: una recensione per parte]")
    come(111)
    r = chiama(SRV.recensibile_p2p, {"ordine": SCAMBIO})
    prova("a chi ha pubblicato la rotta dice si'",
          {"si": True, "motivo": "", "gia": False,
           # (14 nov 2026) i giorni della finestra, per la frase
           "giorni": 7}, r)
    chiama(SRV.recensione_p2p,
           {"ordine": SCAMBIO, "voto": 5, "commento": "Puntuale e gentile"})
    come(222)
    chiama(SRV.recensione_p2p, {"ordine": SCAMBIO, "voto": 4})
    righe = recensioni(SCAMBIO)
    prova("due righe, una per parte", 2, len(righe))
    prova("...e ognuna sa a chi va",
          [(111, 222, 5), (222, 111, 4)],
          [(x["da_tg_id"], x["per_tg_id"], x["voto"]) for x in righe])
    prova("...col posto dell'ordine NEGATIVO (i due mondi non si toccano)",
          True, all(x["ordine_id"] < 0 for x in righe))
    prova("...e lo stesso scambio da' lo stesso numero alle due righe",
          1, len({x["ordine_id"] for x in righe}))
    prova("chi ha preso ha preso 5 stelle", (5.0, 1, 1),
          (utente(222)["rating"], utente(222)["n_feedback"],
           utente(222)["n_recensori"]))
    prova("chi ha pubblicato ne ha prese 4", (4.0, 1, 1),
          (utente(111)["rating"], utente(111)["n_feedback"],
           utente(111)["n_recensori"]))
    detti = [t for chi, t in DETTO if chi == 222]
    prova("...e chi la riceve lo sa", True,
          any("Hai ricevuto una recensione" in t for t in detti))
    prova("...senza che l'id dello scambio finisca in un messaggio",
          [], [t for _, t in DETTO if SCAMBIO in t])

    print("\n[2. la media e' una sola: mercatino e scambio insieme]")
    con = con_db()
    con.execute("INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
                "prezzo_sats,stato,creato) VALUES(0,111,222,1000,"
                "'released',?)", (int(time.time()),))
    oid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.commit()
    con.close()
    come(111)
    corpo_json({"voto": 1, "commento": "qui male"})
    asyncio.run(SRV.lascia_feedback(oid, None))
    prova("il voto del mercatino e quello dello scambio fanno UNA media",
          (3.0, 2), (utente(222)["rating"], utente(222)["n_feedback"]))
    prova("...e le persone diverse restano UNA", 1, utente(222)["n_recensori"])
    con = con_db()
    prov = [dict(x) for x in con.execute(
        "SELECT scambio FROM feedback WHERE per_tg_id=222 ORDER BY id")]
    con.close()
    prova("...ma da dove vengono si distingue", [SCAMBIO, ""],
          [x["scambio"] for x in prov])

    print("\n[3. il doppione]")
    come(111)
    e = errore(SRV.recensione_p2p, {"ordine": SCAMBIO, "voto": 2})
    prova("la seconda della stessa parte e' rifiutata",
          (400, "Hai già lasciato la recensione per questo scambio"), e)
    prova("...e non ha scritto niente", 2, len(recensioni(SCAMBIO)))
    r = chiama(SRV.recensibile_p2p, {"ordine": SCAMBIO})
    prova("...e la rotta del foglio la ricorda (anche da un altro telefono)",
          (False, True, 5), (r["si"], r["gia"], r["voto"]))
    prova("...col commento che avevo lasciato", "Puntuale e gentile",
          r["commento"])
    # e la stessa persona su un ALTRO scambio passa: e' la trappola
    # dello zero al posto dell'ordine — bloccherebbe tutti i successivi
    chiama(SRV.recensione_p2p, {"ordine": SCAMBIO2, "voto": 5})
    prova("...mentre un ALTRO scambio della stessa persona passa",
          1, len(recensioni(SCAMBIO2)))

    print("\n[4. lo scambio non concluso]")
    e = errore(SRV.recensione_p2p, {"ordine": APERTO, "voto": 5})
    prova("rifiutata", (400, "La recensione si lascia a scambio concluso"), e)
    prova("...e nessuna riga", 0, len(recensioni(APERTO)))
    r = chiama(SRV.recensibile_p2p, {"ordine": APERTO})
    prova("...e il foglio lo sa prima", {"si": False, "motivo": "non_conclusa",
                                         "gia": False}, r)

    print("\n[5. l'altra parte non ha un profilo da noi]")
    e = errore(SRV.recensione_p2p, {"ordine": IGNOTO, "voto": 5})
    prova("rifiutata, e la ragione e' sua",
          (400, "Dell'altra persona non sappiamo il profilo: la recensione "
                "non avrebbe dove andare"), e)
    r = chiama(SRV.recensibile_p2p, {"ordine": IGNOTO})
    prova("...e il foglio lo sa PRIMA di chiedere le stelle",
          {"si": False, "motivo": "ignota", "gia": False}, r)
    r = chiama(SRV.recensibile_p2p,
               {"ordine": "992e288e-9999-4a2b-9c3d-000000009999"})
    prova("...e uno scambio che il server non ha mai visto e' lo stesso caso",
          {"si": False, "motivo": "ignota", "gia": False}, r)
    e = errore(SRV.recensione_p2p,
               {"ordine": "992e288e-9999-4a2b-9c3d-000000009999", "voto": 5})
    prova("...ma la rotta che scrive lo chiama col suo nome",
          (404, "Scambio non trovato"), e)

    print("\n[6. l'estraneo]")
    come(333)
    e = errore(SRV.recensione_p2p, {"ordine": SCAMBIO, "voto": 1})
    prova("403, e non il 400 dello stato", (403, "Operazione non permessa"), e)
    r = chiama(SRV.recensibile_p2p, {"ordine": SCAMBIO})
    # ...e la rotta che APRE il foglio gli risponde come a un id che
    # non esiste: distinguere direbbe a chiunque abbia una sessione che
    # quell'ordine del libro e' passato da Barattolo
    prova("...e la domanda gli risponde come a uno scambio che non c'e'",
          {"si": False, "motivo": "ignota", "gia": False}, r)
    ignoto = chiama(SRV.recensibile_p2p,
                    {"ordine": "992e288e-9999-4a2b-9c3d-000000009999"})
    prova("...cioe' le due risposte non si distinguono", ignoto, r)
    prova("nessuno dei rifiuti ha scritto una riga", 4, quante_righe())

    print("\n[7. il negozio dice da dove viene il voto]")
    come(222)
    neg = SRV.negozio("neg22222")
    fb = neg["feedback"]
    prova("i tre voti ricevuti ci sono", 3, len(fb))
    prova("...e due dicono che vengono da uno scambio",
          ["acquirente", "scambio", "scambio"],
          sorted(x["ruolo"] for x in fb))
    # (5 dello scambio + 1 del mercatino + 5 del secondo scambio) / 3
    prova("...mentre la media resta una sola, su tutti e tre", 3.7,
          neg["venditore"]["rating"])
    prova("...e le PERSONE diverse sono una", 1,
          neg["venditore"]["n_recensori"])

    print("\n[8. il posto di chi ha preso non si ruba]")
    con = con_db()
    esito = SRV._registra_ordini_p2p(con, 333, [SCAMBIO], int(time.time()),
                                     presi=True)
    preso = con.execute("SELECT preso_da FROM p2p_ordini WHERE ordine=?",
                        (SCAMBIO,)).fetchone()[0]
    con.close()
    prova("a scambio concluso l'intestazione della presa non si sposta",
          222, preso)
    prova("...e la dichiarazione dell'estraneo e' RIFIUTATA: mostrod dice 222 "
          "(23 set 2026, A1)", 1, esito["rifiutate"])
    con = con_db()
    SRV._registra_ordini_p2p(con, 333, [APERTO], int(time.time()), presi=True)
    preso = con.execute("SELECT preso_da FROM p2p_ordini WHERE ordine=?",
                        (APERTO,)).fetchone()[0]
    con.close()
    prova("...e nemmeno su uno scambio vivo che ha gia' chi l'ha preso",
          222, preso)
    # ...e dalla ROTTA, con la sessione dell'estraneo, e' un 403 (A1)
    come(333)
    e = errore(SRV.registra_ordini_p2p, {"ordini": [APERTO], "presi": True})
    prova("...e la rotta risponde 403 a chi non e' una delle due parti",
          (403, "Non risulti fra le due parti di questo scambio"), e)

    print("\n[9. l'invito nella notifica]")
    ev = {"id": SCAMBIO, "stato": "success", "lato": "sell",
          "sats": 7000, "euro": ["25"], "metodi": ["Satispay"]}
    con_posto = SRV._testo_libro_p2p("concluso", ev, 0.02, 168, "maker", True)
    senza = SRV._testo_libro_p2p("concluso", ev, 0.02, 168, "maker", False)
    prova("dove c'e' un posto, l'invito c'e'", True,
          "Lascia una recensione" in con_posto)
    prova("...e dice dove si fa", True,
          "pagina dello scambio" in con_posto)
    prova("dove non c'e', non si promette niente", False,
          "recensione" in senza)
    prova("...ma lo scambio resta concluso", True,
          "Scambio concluso" in senza)

    print("\n[10. chi entra da Nostr e' riconosciuto come tutti (12 ott 2026)]")
    # -77 e' l'account nato da Nostr: dal 12 ott 2026 (cantiere
    # chi-e-l-altro, decisione di Andrea con Alan) la sua presa si annota
    # come quella di chiunque, e la recensione ha un posto nei due versi.
    # L'interruttore «Fatti riconoscere» non esiste piu': per l'anonimato
    # c'e' una chiave Nostr nuova.
    prova("la rotta dell'interruttore e' uscita", False,
          hasattr(SRV, "scegli_riconoscimi_p2p"))
    come(-77)
    chiama(SRV.registra_ordini_p2p, {"ordini": [DA_NOSTR2], "presi": True})
    prova("la presa del nativo si annota, senza nessun interruttore", -77,
          preso_da(DA_NOSTR2))
    concludi(DA_NOSTR2)
    r = chiama(SRV.recensibile_p2p, {"ordine": DA_NOSTR2})
    prova("...e la recensione si apre", {"si": True, "motivo": "",
                                         "gia": False,
                                         "giorni": 7}, r)
    chiama(SRV.recensione_p2p, {"ordine": DA_NOSTR2, "voto": 5})
    come(111)
    chiama(SRV.recensione_p2p, {"ordine": DA_NOSTR2, "voto": 4,
                                "commento": "Veloce"})
    prova("le due parti si sono recensite", 2, len(recensioni(DA_NOSTR2)))
    prova("...e il voto e' arrivato anche a chi non ha un nome",
          (4.0, 1), (utente(-77)["rating"], utente(-77)["n_feedback"]))

    # LO SCAMBIO DI PRIMA — la presa mai annotata, com'era per chi entrava
    # da Nostr fino al 12 ott — NON si recupera a cose fatte: la promessa
    # del 17 set vale sul passato (e la guardia del caso 8 tiene)
    concludi(DA_NOSTR)
    come(111)
    e = errore(SRV.recensione_p2p, {"ordine": DA_NOSTR, "voto": 5})
    prova("uno scambio di prima: chi ha pubblicato non ha chi recensire",
          (400, "Dell'altra persona non sappiamo il profilo: la recensione "
                "non avrebbe dove andare"), e)
    come(-77)
    r = chiama(SRV.recensibile_p2p, {"ordine": DA_NOSTR})
    prova("...e per lui il server non sa che e' parte: «ignota»",
          {"si": False, "motivo": "ignota", "gia": False}, r)
    chiama(SRV.registra_ordini_p2p, {"ordini": [DA_NOSTR], "presi": True})
    prova("...e a cose fatte la presa non si annota piu'", 0, preso_da(DA_NOSTR))

    print("\n[11. la fusione non esplode]")
    come(-77)
    chiama(SRV.recensione_p2p, {"ordine": FUSO, "voto": 5})
    come(111)
    chiama(SRV.recensione_p2p, {"ordine": FUSO, "voto": 5})
    prova("le due meta' si sono recensite", 2, len(recensioni(FUSO)))
    esito = SRV.esegui_fusione(111, -77)
    prova("la fusione passa", False, isinstance(esito, str))
    prova("...e le recensioni fra le due meta' se ne sono andate",
          0, len(recensioni(FUSO)))
    prova("...mentre le altre restano", 2, len(recensioni(SCAMBIO)))

    print("\n" + "=" * 60)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 60)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
