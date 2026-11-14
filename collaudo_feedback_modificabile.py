# -*- coding: utf-8 -*-
"""
IL FEEDBACK SI MODIFICA E SI CANCELLA, PER UN PO' (14 nov 2026).

Richiesta di Andrea: «possibilita' di modificare o cancellare un
feedback». Fino a ieri era definitivo («chiude il ricatto "cambia il
feedback o…"»); adesso chi l'ha scritto lo cambia UNA volta o lo
cancella, per FEEDBACK_MODIFICA_GIORNI giorni, e i paletti contro il
ricatto stanno sul server.

`prove.py` difende la FORMA (il giudice sui suoi casi, la leva, le
rotte, le frasi del client). Qui si CAMMINA sul server vero, con un
database usa e getta:

  1. il compratore lascia 2★; la lista degli ordini gli offre i due
     gesti, con la data giusta;
  2. li modifica a 5★: la media sale, chi riceve lo sa (★★ → ★★★★★),
     i moderatori vedono il voto basso alzato; il profilo dice
     «modificato»; una seconda modifica no, la cancellazione si';
  3. chi non ha scritto prende 404 (l'altra parte, un estraneo);
  4. cancella: la riga sparisce, la media si rifa' i conti, resta la
     lapide, e un feedback nuovo sullo stesso affare e' rifiutato;
  5. un 1★ cancellato: i moderatori lo vedono;
  6. passata la finestra: niente gesti, e le due rotte dicono perche';
  7. la leva spenta: 409, nessun gesto offerto, la frase del definitivo;
  8. la recensione di uno SCAMBIO P2P: stesse regole, dalle gemelle;
  9. la fusione porta con se' la lapide.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server. Niente rete, niente LNbits, niente Blossom.

USO:  python collaudo_feedback_modificabile.py
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
AI_MODERATORI = []  # (testo, argomento) di ogni avviso admin

SCAMBIO = "992e288e-aaaa-4a2b-9c3d-000000000001"
GIORNO = 86400


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


class Busta:
    def __init__(self, dati):
        self.dati = dati

    async def json(self):
        return self.dati


def avvio():
    """Il config finto PRIMA di importare server."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-fb-modifica-"),
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
    # niente righe FEEDBACK_*: il collaudo prova i valori DI SERIE
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def notifica_finta(chi, testo, *a, **k):
        DETTO.append((chi, testo))

    async def admin_finto(testo, *a, **k):
        AI_MODERATORI.append((testo, k.get("argomento", "")))

    async def zitto(*a, **k):
        return None

    server.notifica = notifica_finta
    server.notifica_admin = admin_finto
    server.premia_distintivi = zitto
    server.premia_xp = zitto
    server.polso_ordini_admin = zitto
    server._p2p_per = lambda tg_id: {"attivo": True}
    return db


def come(tg_id):
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "first_name": f"U{tg_id}",
        "username": f"u{tg_id}", "admin": False}


def chiama(fn, *args, corpo=None):
    async def leggi(_req):
        return corpo or {}
    SRV.leggi_json = leggi
    esito = fn(*args)
    # le rotte sincrone (la lista degli ordini, il negozio) rispondono
    # subito; le altre sono coroutine
    return asyncio.run(esito) if asyncio.iscoroutine(esito) else esito


def errore(fn, *args, corpo=None):
    """Il codice e il messaggio di un rifiuto, o None se e' passato."""
    try:
        chiama(fn, *args, corpo=corpo)
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
    u = dict(con.execute("SELECT rating, n_feedback, n_recensori FROM "
                         "utenti WHERE tg_id=?", (tg_id,)).fetchone())
    con.close()
    return u


def righe_fb(ordine_id):
    con = con_db()
    r = [dict(x) for x in con.execute(
        "SELECT da_tg_id, voto, commento, modificato>0 AS mod FROM feedback "
        "WHERE ordine_id=? ORDER BY da_tg_id", (ordine_id,))]
    con.close()
    return r


def lapidi():
    con = con_db()
    r = [tuple(x) for x in con.execute(
        "SELECT ordine_id, da_tg_id, per_tg_id, scambio FROM "
        "feedback_ritirati ORDER BY ordine_id, da_tg_id")]
    con.close()
    return r


def invecchia(ordine_id, da, giorni):
    con = con_db()
    con.execute("UPDATE feedback SET creato=? WHERE ordine_id=? AND "
                "da_tg_id=?", (int(time.time()) - giorni * GIORNO,
                               ordine_id, da))
    con.commit()
    con.close()


def ordine_mio(oid, tg_id):
    come(tg_id)
    for o in chiama(SRV.miei_ordini, 0):
        if o["id"] == oid:
            return o
    return None


def semina():
    """Tre ordini gia' conclusi (released) fra 111 che compra e 222 che
    vende, e uno scambio P2P concluso fra gli stessi due. Gli stati si
    scrivono a mano: il giro che li produce ha i suoi collaudi
    (collaudo_feedback_confermato), qui conta quel che viene DOPO."""
    con = con_db()
    for t in ("feedback", "feedback_ritirati", "ordini", "annunci",
              "p2p_ordini"):
        con.execute(f"DELETE FROM {t}")
    for tg, nome, neg in ((111, "Compra", "neg11111"),
                          (222, "Vende", "neg22222"),
                          (333, "Estraneo", "neg33333")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address,rating,n_feedback,n_recensori) "
                    "VALUES(?,?,?,1,'',0,0,0)", (tg, nome, neg))
    adesso = int(time.time())
    ids = []
    for n in range(3):
        a = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(222,?,'una cosa vera',50000,'Altro','Pavia (PV)',"
            "'venduto',1,'spedizione',1,'sats','nuovo')",
            (f"Cosa {n}",)).lastrowid
        o = con.execute(
            "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
            "prezzo_sats,stato,creato,aggiornato) "
            "VALUES(?,111,222,50000,'released',?,?)",
            (a, adesso, adesso)).lastrowid
        ids.append(o)
    con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,"
                "maker,visto,preso_da) VALUES(?,111,?,'success','sell',1,?,"
                "222)", (SCAMBIO, adesso, adesso))
    con.execute("INSERT OR REPLACE INTO p2p_scambi(ordine, compratore, "
                "venditore, preso_dal, giro, aggiornato) "
                "VALUES(?,222,111,'buyer',1,?)", (SCAMBIO, adesso))
    con.commit()
    con.close()
    return ids


def main():
    print("=" * 60)
    print("  IL FEEDBACK SI MODIFICA E SI CANCELLA, PER UN PO'")
    print("=" * 60)
    avvio()
    prova("la leva nasce accesa, la finestra e' di 7 giorni",
          (True, 7), (SRV.FEEDBACK_MODIFICABILE, SRV.FEEDBACK_MODIFICA_GIORNI))
    o1, o2, o3 = semina()

    # ---- 1. Il voto basso, e i gesti offerti ---------------------------
    print("\n[1. il compratore lascia 2★, e la lista gli offre i gesti]")
    come(111)
    chiama(SRV.lascia_feedback, o1, None,
           corpo={"voto": 2, "commento": "Arrivato tardi"})
    prova("la media del venditore e' 2", 2.0, utente(222)["rating"])
    o = ordine_mio(o1, 111)
    g = o["mio_fb_gesti"]
    creato = righe_fb(o1) and con_db().execute(
        "SELECT creato FROM feedback WHERE ordine_id=?", (o1,)).fetchone()[0]
    prova("i due gesti offerti, fino a 7 giorni dalla nascita",
          {"modifica": True, "cancella": True, "fino": creato + 7 * GIORNO}, g)
    prova("...e i giorni per la frase del modulo", 7, o["fb_giorni"])
    prova("non e' ritirato, e non e' modificato", (0, 0),
          (o["mio_fb_ritirato"], o["mio_fb_modificato"]))
    ov = ordine_mio(o1, 222)
    prova("al venditore, che non ha votato, nessun gesto", None,
          ov["mio_fb_gesti"])

    # ---- 2. La modifica ------------------------------------------------
    print("\n[2. lo modifica a 5★]")
    DETTO.clear()
    AI_MODERATORI.clear()
    come(111)
    d = chiama(SRV.modifica_feedback, o1, None,
               corpo={"voto": 5, "commento": "Ci siamo chiariti, ottimo!"})
    prova("la modifica passa", True, d["ok"])
    prova("...e la riga e' cambiata, col timbro della modifica",
          [{"da_tg_id": 111, "voto": 5,
            "commento": "Ci siamo chiariti, ottimo!", "mod": 1}],
          righe_fb(o1))
    prova("la media si rifa' i conti (non si somma)",
          {"rating": 5.0, "n_feedback": 1, "n_recensori": 1}, utente(222))
    avvisi_222 = [t for chi, t in DETTO if chi == 222]
    prova("chi riceve lo sa, con le stelle di prima e di dopo", True,
          len(avvisi_222) == 1 and "★★ → ★★★★★" in avvisi_222[0]
          and f"#{o1}" in avvisi_222[0])
    prova("i moderatori vedono il voto basso alzato, in «moderazione»",
          [("moderazione", True)],
          [(arg, "alzato" in t and f"#{o1}" in t) for t, arg in AI_MODERATORI])
    o = ordine_mio(o1, 111)
    prova("dopo la modifica resta solo «Cancella»",
          (False, True), (o["mio_fb_gesti"]["modifica"],
                          o["mio_fb_gesti"]["cancella"]))
    prova("...e il venditore legge che e' modificato", True,
          ordine_mio(o1, 222)["suo_fb_modificato"] > 0)
    come(333)
    neg = chiama(SRV.negozio, "neg22222", 0, "", "", 0)
    prova("sul profilo pubblico la riga porta `modificato`", True,
          len(neg["feedback"]) == 1 and neg["feedback"][0]["modificato"] > 0)
    come(111)
    e = errore(SRV.modifica_feedback, o1, None, corpo={"voto": 1})
    prova("una seconda modifica no, e lo dice", 400, e and e[0])
    prova("...con la frase giusta", True, "una volta sola" in e[1])
    prova("...e la riga non si e' mossa", 5, righe_fb(o1)[0]["voto"])
    e = errore(SRV.modifica_feedback, o1, None, corpo={"voto": 9})
    prova("un voto fuori da 1-5 non arriva nemmeno al giudice",
          (400, "Il voto va da 1 a 5 stelle"), e)

    # ---- 3. Chi non l'ha scritto ---------------------------------------
    print("\n[3. chi non l'ha scritto non lo tocca]")
    come(222)
    e = errore(SRV.modifica_feedback, o1, None, corpo={"voto": 1})
    prova("l'altra parte (che non ha votato) prende 404", 404, e and e[0])
    e = errore(SRV.cancella_feedback, o1, None)
    prova("...anche per cancellare", 404, e and e[0])
    come(333)
    e = errore(SRV.cancella_feedback, o1, None)
    prova("l'estraneo prende 404", 404, e and e[0])
    prova("il feedback e' ancora li'", 1, len(righe_fb(o1)))

    # ---- 4. La cancellazione -------------------------------------------
    print("\n[4. lo cancella, per sempre]")
    DETTO.clear()
    AI_MODERATORI.clear()
    come(111)
    prova("la cancellazione passa", {"ok": True},
          chiama(SRV.cancella_feedback, o1, None))
    prova("la riga non c'e' piu'", [], righe_fb(o1))
    prova("la media torna a zero",
          {"rating": 0.0, "n_feedback": 0, "n_recensori": 0}, utente(222))
    prova("resta la lapide: chi, dove, verso chi — niente voto",
          [(o1, 111, 222, "")], lapidi())
    prova("chi riceveva lo sa", True,
          any(chi == 222 and "cancellato" in t for chi, t in DETTO))
    prova("un 5★ cancellato non e' un ricatto: i moderatori tacciono",
          [], AI_MODERATORI)
    e = errore(SRV.lascia_feedback, o1, None, corpo={"voto": 4})
    prova("un feedback nuovo sullo stesso affare: rifiutato",
          (400, SRV.MSG_FEEDBACK_RITIRATO), e)
    o = ordine_mio(o1, 111)
    prova("la lista lo dice (lapide), e non offre gesti",
          (1, None, 0), (o["mio_fb_ritirato"], o["mio_fb_gesti"],
                         o["mio_voto"] or 0))
    e = errore(SRV.cancella_feedback, o1, None)
    prova("cancellare due volte: 404", 404, e and e[0])

    # ---- 5. Il 1★ cancellato -------------------------------------------
    print("\n[5. il voto basso cancellato si dice ai moderatori]")
    AI_MODERATORI.clear()
    come(111)
    chiama(SRV.lascia_feedback, o2, None, corpo={"voto": 1})
    chiama(SRV.cancella_feedback, o2, None)
    prova("i moderatori lo vedono", [("moderazione", True)],
          [(arg, "cancellato" in t and f"#{o2}" in t)
           for t, arg in AI_MODERATORI])

    # ---- 6. La finestra ------------------------------------------------
    print("\n[6. passati i 7 giorni il feedback e' definitivo]")
    come(222)
    chiama(SRV.lascia_feedback, o3, None, corpo={"voto": 3})
    invecchia(o3, 222, 8)
    o = ordine_mio(o3, 222)
    prova("nessun gesto offerto", {"modifica": False, "cancella": False,
                                   "fino": 0}, o["mio_fb_gesti"])
    e = errore(SRV.modifica_feedback, o3, None, corpo={"voto": 5})
    prova("la modifica e' rifiutata col perche'", True,
          e is not None and e[0] == 400 and "7 giorni" in e[1])
    e = errore(SRV.cancella_feedback, o3, None)
    prova("...e la cancellazione pure", True,
          e is not None and e[0] == 400 and "definitivo" in e[1])
    invecchia(o3, 222, 6)
    o = ordine_mio(o3, 222)
    prova("a sei giorni i gesti ci sono ancora", (True, True),
          (o["mio_fb_gesti"]["modifica"], o["mio_fb_gesti"]["cancella"]))

    # ---- 7. La leva spenta ---------------------------------------------
    print("\n[7. la leva spenta: definitivo come prima]")
    SRV.FEEDBACK_MODIFICABILE = False
    try:
        o = ordine_mio(o3, 222)
        prova("nessun gesto, e i giorni a zero (la frase del definitivo)",
              ({"modifica": False, "cancella": False, "fino": 0}, 0),
              (o["mio_fb_gesti"], o["fb_giorni"]))
        e = errore(SRV.modifica_feedback, o3, None, corpo={"voto": 5})
        prova("la modifica prende 409", 409, e and e[0])
        e = errore(SRV.cancella_feedback, o3, None)
        prova("...e la cancellazione pure", 409, e and e[0])
        prova("la riga resta com'era", 3, righe_fb(o3)[0]["voto"])
    finally:
        SRV.FEEDBACK_MODIFICABILE = True

    # ---- 8. La recensione di uno scambio P2P ---------------------------
    print("\n[8. la recensione di uno scambio P2P, dalle gemelle]")
    firma = SRV._numero_scambio_p2p(SCAMBIO)
    come(222)
    r = chiama(SRV.recensibile_p2p, Busta({}), corpo={"ordine": SCAMBIO})
    prova("prima di scrivere, la domanda dice i giorni della finestra",
          (True, 7), (r["si"], r.get("giorni")))
    chiama(SRV.recensione_p2p, Busta({}),
           corpo={"ordine": SCAMBIO, "voto": 2, "commento": "lento"})
    r = chiama(SRV.recensibile_p2p, Busta({}), corpo={"ordine": SCAMBIO})
    prova("dopo, dice gia' e i gesti (i giorni non servono piu')",
          (True, True, True, None, 0),
          (r["gia"], r["gesti"]["modifica"], r["gesti"]["cancella"],
           r.get("giorni"), r["modificato"]))
    AI_MODERATORI.clear()
    DETTO.clear()
    chiama(SRV.modifica_recensione_p2p, Busta({}),
           corpo={"ordine": SCAMBIO, "voto": 4, "commento": "ok <b>bravo</b>"})
    # 111 ha gia' il 3★ ricevuto sull'affare del caso 6: UNA media sola,
    # mercatino e scambi insieme, quindi (3 + 4) / 2
    prova("modificata, e la media UNICA di chi pubblicava segue", 3.5,
          utente(111)["rating"])
    prova("l'avviso non porta l'id dello scambio", True,
          all(SCAMBIO not in t for _, t in DETTO)
          and any("uno scambio di sats" in t for _, t in DETTO))
    prova("il commento nuovo arriva scappato (e' testo di un altro)", True,
          any("ok &lt;b&gt;bravo&lt;/b&gt;" in t for _, t in DETTO)
          and all("<b>bravo" not in t for _, t in DETTO))
    prova("...e nemmeno quello ai moderatori", True,
          len(AI_MODERATORI) == 1 and SCAMBIO not in AI_MODERATORI[0][0]
          and str(firma) not in AI_MODERATORI[0][0])
    r = chiama(SRV.recensibile_p2p, Busta({}), corpo={"ordine": SCAMBIO})
    prova("dopo la modifica: modificata, resta solo «Cancella»",
          (True, False, True), (r["modificato"] > 0, r["gesti"]["modifica"],
                                r["gesti"]["cancella"]))
    e = errore(SRV.modifica_recensione_p2p, Busta({}),
               corpo={"ordine": SCAMBIO, "voto": 5})
    prova("una seconda modifica no", 400, e and e[0])
    come(111)
    e = errore(SRV.cancella_recensione_p2p, Busta({}),
               corpo={"ordine": SCAMBIO})
    prova("l'altra parte (senza recensione sua) prende 404", 404, e and e[0])
    come(222)
    chiama(SRV.cancella_recensione_p2p, Busta({}), corpo={"ordine": SCAMBIO})
    prova("cancellata: nella media resta solo il 3★ del mercatino",
          {"rating": 3.0, "n_feedback": 1, "n_recensori": 1}, utente(111))
    prova("...e la lapide porta la firma e l'id dello scambio", True,
          (firma, 222, 111, SCAMBIO) in lapidi())
    r = chiama(SRV.recensibile_p2p, Busta({}), corpo={"ordine": SCAMBIO})
    prova("la domanda dice «ritirata», senza invito", (False, False,
                                                     "ritirata"),
          (r["si"], r["gia"], r["motivo"]))
    e = errore(SRV.recensione_p2p, Busta({}),
               corpo={"ordine": SCAMBIO, "voto": 5})
    prova("una recensione nuova sullo scambio: rifiutata", True,
          e is not None and e[0] == 400 and "cancellato" in e[1])
    e = errore(SRV.cancella_recensione_p2p, Busta({}),
               corpo={"ordine": "../../etc"})
    prova("un ordine in una forma sconosciuta: 400", 400, e and e[0])

    # ---- 9. La fusione porta la lapide ---------------------------------
    print("\n[9. la fusione non dimentica le lapidi]")
    # -5 e' la meta' Nostr di 333: aveva cancellato un feedback su un
    # affare (999999) che la meta' Telegram non ha mai visto. Dopo la
    # fusione 333 non deve poterlo riscrivere.
    con = con_db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,registrato,"
                "npub_accesso) VALUES(-5,'Nostrino',1,'npub1collaudo')")
    con.execute("UPDATE utenti SET npub_accesso='' WHERE tg_id=333")
    con.execute("INSERT INTO feedback_ritirati(ordine_id, da_tg_id, "
                "per_tg_id, scambio, ritirato) VALUES(999999, -5, 222, '', 1)")
    # ...e una lapide sullo stesso affare per tutt'e due le meta': ne
    # resta una, e la fusione non si ferma sulla chiave primaria
    con.execute("INSERT INTO feedback_ritirati(ordine_id, da_tg_id, "
                "per_tg_id, scambio, ritirato) VALUES(888888, -5, 222, '', 1)")
    con.execute("INSERT INTO feedback_ritirati(ordine_id, da_tg_id, "
                "per_tg_id, scambio, ritirato) VALUES(888888, 333, 222, '', 1)")
    con.commit()
    con.close()
    esito = SRV.esegui_fusione(333, -5)
    prova("la fusione passa (nessuna collisione sulla lapide doppia)", True,
          not isinstance(esito, str))
    prova("le lapidi della meta' Nostr sono della meta' viva, una per affare",
          [(888888, 333, 222, ""), (999999, 333, 222, "")],
          [x for x in lapidi() if x[0] in (888888, 999999)])
    prova("...e del tg_id morto non resta niente", [],
          [x for x in lapidi() if x[1] == -5])

    print("\n" + "=" * 60)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 60)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
