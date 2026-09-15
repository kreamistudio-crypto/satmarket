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

E dal secondo tempo (la PRESA IN CARICO, che e' l'unico fatto che
questa rete compra):

  · IL TITOLARE SEGNA e da li' il codice ESISTE: lo conia il server,
    lo vedono chi compra e il punto, mai il venditore — che dal
    deposito in poi non ha piu' niente da fare;
  · NON TOCCA `spedito_il` ne' `aggiornato` ne' lo stato: prendere in
    carico non e' consegnare, ed e' la trappola dell'ancora mobile
    gia' pagata quattro volte;
  · IL SECONDO TOCCO E' UN NO-OP e non manda una seconda notifica;
  · L'ANTI-ORACOLO sul database VERO: estraneo, titolare di un ALTRO
    punto, il venditore in persona e un ordine inesistente rispondono
    IDENTICO — ed e' il caso che smaschera una guardia scritta su
    «sei un titolare?» invece che «e' TUO?»;
  · LA LISTA DEL TITOLARE non porta ne' chi compra ne' cosa c'e'
    dentro, e il codice esce SOLO dopo la presa in carico;
  · LA NOTA AL MODERATORE dice il fatto con la data e la regola di
    default che la strada B compra — mai il codice, mai il nome.

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
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
INVOICES = []
DETTI = []          # (destinatario, testo) di ogni notifica
ADMIN = []          # i testi arrivati dalla ronda del libro mastro
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


def sezione(fn, *a):
    """⚠️ UNA SEZIONE CHE ESPLODE NON DEVE PORTARSI VIA IL CONTO, e
    l'ha detto la tortura: una mutazione faceva alzare una rotta due
    sezioni piu' avanti, il collaudo si fermava li' e la riga finale
    non si stampava — quindi il banco della tortura leggeva «nessuna
    fallita» e contava la mutazione come SOPRAVVISSUTA, mentre delle
    righe rosse c'erano gia' state. Un'eccezione e' un fallimento, e
    si dice cosi': si scrive, si conta, e le sezioni dopo girano."""
    global FALLITE
    try:
        return fn(*a)
    except Exception as e:
        FALLITE += 1
        print(f"  \u2717 la sezione «{fn.__name__}» e' ESPLOSA")
        print(f"      {type(e).__name__}: {e}")
        return None


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

    async def invoice_finta(sats, memo, expiry=None, cassaforte=""):
        INVOICES.append(int(sats))
        return {"payment_hash": f"hash{len(INVOICES)}",
                "payment_request": f"lnbc{sats}collaudo{len(INVOICES)}"}

    async def cambio_finto():
        return CAMBIO

    async def zitta(*a, **k):
        return None

    async def mai_pagata(_hash, _cassaforte=""):
        return False

    # LE NOTIFICHE NON SI BUTTANO PIU', SI REGISTRANO: dal secondo
    # tempo il loro contenuto e' una delle cose da provare — che il
    # codice di ritiro non ci entri MAI, che il secondo tocco non ne
    # mandi una seconda, e che la nota al moderatore dica il fatto
    # senza il contenuto. La nota della disputa arriva ai moderatori
    # da `notifica(admin, ...)` e non da `notifica_admin`, che invece
    # la ronda del libro mastro usa: due registri, due mestieri.
    async def detta(chi, testo, *a, **k):
        DETTI.append((chi, testo))

    async def alla_ronda(testo, *a, **k):
        ADMIN.append(testo)

    # L'USCITA DEI SATS: il giro si chiude con la conferma di chi ha
    # ritirato, e senza questi due `_sblocca_sats` andrebbe a chiedere
    # a LNbits. Qui non si prova il payout — quello ha il suo collaudo
    # — si prova che l'ordine ci arrivi.
    async def ln_finta(_addr, sats):
        return f"lnbc{sats}collaudo"

    async def paga_finta(_bolt11, _atteso, _diario=None, cassaforte=""):
        return server.PAGATO

    server.crea_invoice_escrow = invoice_finta
    server.invoice_pagata = mai_pagata
    server.cambio_btc_eur = cambio_finto
    server.notifica = detta
    server.notifica_admin = alla_ronda
    server.invoice_da_ln_address = ln_finta
    server.paga_venditore = paga_finta
    server.premia_distintivi = zitta
    server.premia_xp = zitta
    # ⚠️ E' ATTESO: il primo tempo non arrivava mai alla chiusura di un
    # ordine, quindi un `lambda` bastava; da qui il giro si chiude e
    # `_sblocca_sats` lo attende — un None non si puo' attendere.
    server.polso_ordini_admin = zitta
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


# --- gli attrezzi del secondo tempo (la presa in carico) -------
# Il primo tempo gira tutto con UNA identita' perche' li' bastava; da
# qui in poi sono QUATTRO, e a distinguerle e' l'unica cosa che rende
# provabile l'anti-oracolo.
def come(tg_id, admin=False):
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "username": f"u{tg_id}",
        "admin": admin}


def esegui(fn, *args, corpo=None):
    """Come `chiama`, ma per le rotte che prendono l'ordine: il corpo
    e' FACOLTATIVO, che meta' di quelle del giro non lo leggono."""
    if corpo is not None:
        async def leggi(_req):
            return corpo
        SRV.leggi_json = leggi
    return asyncio.run(fn(*args))


def rifiuta(fn, *args, corpo=None):
    """Torna `(codice, messaggio)` invece di far esplodere il collaudo:
    e' la forma che permette di CONFRONTARE due rifiuti fra loro, cioe'
    precisamente quel che l'anti-oracolo chiede."""
    try:
        esegui(fn, *args, corpo=corpo)
        return 0, ""
    except Exception as e:
        return getattr(e, "status_code", None), str(getattr(e, "detail", e))


def semina_b():
    """Le quattro identita' del secondo tempo. IL TITOLARE E' 333 e NON
    il venditore: `da-mario` sta a `neg22222`, quindi il venditore e'
    titolare di un ALTRO punto — ed e' il caso che serve, perche' una
    guardia scritta su «sei un titolare?» lo lascerebbe passare."""
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address,spedizionieri,spedizioniere) VALUES"
                "(222,'Vende','neg22222',1,'vende@wallet.tld',"
                "'|Barattolo|InPost|','Barattolo')")
    for tg, neg, nome in ((111, "neg11111", "Compra"),
                          (333, "neg33333", "Luna"),
                          (777, "neg77777", "Estraneo")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato) VALUES(?,?,?,1)", (tg, nome, neg))
    ids = []
    for n in range(10):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
            "spedizione_sats) VALUES(222,?,'desc',30000,'Altro',"
            "'Torino (TO)','attivo',1,'spedizione',5,'sats','buono',1000)",
            (f"Cosa {n}",))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    accendi("da-mario", "bar-luna")
    return ids


def tocca(oid, **campi):
    con = SRV.db()
    con.execute("UPDATE ordini SET " + ", ".join(f"{k}=?" for k in campi)
                + " WHERE id=?", tuple(campi.values()) + (oid,))
    con.commit()
    con.close()


def al_punto(aid, pid="bar-luna"):
    """L'ordine verso un punto NOSTRO. `punto_ritiro` non si passa
    apposta: sulla rete di casa quel campo lo scrive il server."""
    come(111)
    r = compra(aid, rete_punto="Barattolo", punto_barattolo=pid)
    tocca(r["ordine_id"], stato="locked")
    return r["ordine_id"]


def a_inpost(aid):
    come(111)
    r = compra(aid, rete_punto="InPost",
               punto_ritiro="Locker InPost Via Verdi 3", tipo_punto="locker")
    tocca(r["ordine_id"], stato="locked")
    return r["ordine_id"]


def spedisci(oid, chi=222):
    come(chi)
    return esegui(SRV.segna_spedito, oid, None,
                  corpo={"corriere": "BRT", "tracking": "1234567890"})


def prendi(oid, chi=333):
    come(chi)
    return esegui(SRV.punto_preso_in_carico, oid)


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


def prove_presa_in_carico():
    print("\n\u2500\u2500 LA PRESA IN CARICO: il fatto che la rete compra \u2500\u2500")
    ann = semina_b()
    oid = al_punto(ann[0])
    spedisci(oid)
    r = riga_ordine(oid)
    prova("prima della presa la busta e' vuota", "", r["busta_codice"])
    prova("...e il timbro pure", 0, r["punto_preso_il"])

    prima = riga_ordine(oid)
    DETTI.clear()
    esito = prendi(oid)
    dopo = riga_ordine(oid)
    prova("la rotta risponde ok", True, bool(esito.get("ok")))
    prova("il momento resta scritto", True, dopo["punto_preso_il"] > 0)
    prova("...col codice negozio del punto, per il libro mastro",
          "neg33333", dopo["punto_preso_da"])
    # LE TRE ANCORE CHE NON SI TOCCANO
    prova("NON tocca `spedito_il` (l'ancora dei promemoria)",
          prima["spedito_il"], dopo["spedito_il"])
    prova("...ne' `aggiornato`", prima["aggiornato"], dopo["aggiornato"])
    prova("...ne' lo stato: prendere in carico non e' consegnare",
          "shipped", dopo["stato"])

    prova("la busta si e' scritta da sola", True, bool(dopo["busta_codice"]))
    prova("...col `busta_il` nello stesso istante", True,
          dopo["busta_il"] == dopo["punto_preso_il"])
    prova("...e in colonna il codice non e' in chiaro", True,
          ":" in dopo["busta_codice"])
    codice = SRV._decifra_contenuto(dopo["busta_codice"])
    prova("il codice e' di sei caratteri", 6, len(codice))
    prova("...senza 0, 1, I e O", True, not (set(codice) & set("01IO")))
    prova("il nome sulla busta e' quello DEL PUNTO — il ribaltamento",
          "Bar Luna", SRV._decifra_contenuto(dopo["busta_nome"]))

    chi = [c for c, _ in DETTI]
    prova("avvisa chi compra", True, 111 in chi)
    prova("...e chi vende", True, 222 in chi)
    testi = " || ".join(t for _, t in DETTI)
    prova("IL CODICE NON ENTRA IN NESSUNA NOTIFICA", False, codice in testi)
    prova("...e a chi compra si dice dove trovarlo", True,
          "codice di ritiro" in testi)

    print("\n\u2500\u2500 ...e il codice esce solo dopo, e solo a chi deve \u2500\u2500")
    come(333)
    d = esegui(SRV.pacchi_del_punto)
    prova("ora il titolare vede il codice", codice, d["pacchi"][0]["codice"])
    come(111)
    b = esegui(SRV.leggi_busta_ritiro, oid)
    prova("e chi compra lo legge dalla busta", codice, b["codice"])
    prova("...col nome del punto", "Bar Luna", b["nome"])
    come(999, admin=True)
    cod, _ = rifiuta(SRV.leggi_busta_ritiro, oid)
    prova("il moderatore NON legge la busta, nemmeno adesso", 400, cod)

    print("\n\u2500\u2500 ...e il secondo tocco e' un no-op \u2500\u2500")
    DETTI.clear()
    prima = riga_ordine(oid)
    esito = prendi(oid)
    dopo = riga_ordine(oid)
    prova("risponde ok lo stesso", True, bool(esito.get("ok")))
    prova("...ma il timbro non si muove", prima["punto_preso_il"],
          dopo["punto_preso_il"])
    prova("...il codice non si riconia", prima["busta_codice"],
          dopo["busta_codice"])
    prova("...e non parte nessuna seconda notifica", [], DETTI)
    return ann


def prove_lista_del_punto(ann):
    print("\n\u2500\u2500 LA LISTA DEL TITOLARE: un codice e basta \u2500\u2500")
    oid = al_punto(ann[1])
    spedisci(oid)
    come(333)
    d = esegui(SRV.pacchi_del_punto)
    prova("il titolare vede il suo punto", ["bar-luna"],
          [x["id"] for x in d["punti"]])
    p0 = [x for x in d["pacchi"] if x["id"] == oid][0]
    prova("vede il tracciamento del corriere", "1234567890", p0["tracking"])
    prova("...e il nome del suo punto", "Bar Luna", p0["punto_nome"])
    prova("MA NON il codice, che non esiste ancora", "", p0["codice"])
    # ⚠️ E LA PROVA VERA E' QUESTA, che l'ha detto la tortura: sopra la
    # colonna e' VUOTA, quindi il gate non ha niente da nascondere e la
    # riga passerebbe anche togliendolo. Qui la busta si scrive a mano
    # SENZA la presa in carico — lo stato che il gate esiste per
    # coprire — e il codice deve restare dentro lo stesso.
    tocca(oid, busta_codice=SRV._cifra_contenuto("ZZZ999"))
    come(333)
    dz = esegui(SRV.pacchi_del_punto)
    pz = [x for x in dz["pacchi"] if x["id"] == oid][0]
    prova("...e nemmeno se la busta c'e' ma il punto non ha segnato",
          "", pz["codice"])
    prova("...e la colonna non esce nuda per un'altra strada", False,
          "busta_codice" in pz)
    tocca(oid, busta_codice="")
    prova("...ne' chi compra", False, "compratore_id" in p0)
    prova("...ne' cosa c'e' dentro", False,
          any(k in p0 for k in ("titolo", "annuncio_id", "prezzo_sats")))
    come(222)                       # titolare di un ALTRO punto
    d2 = esegui(SRV.pacchi_del_punto)
    prova("il titolare dell'altro punto non vede questo pacco", [],
          [x for x in d2["pacchi"] if x["id"] == oid])
    come(777)
    d3 = esegui(SRV.pacchi_del_punto)
    prova("e chi non tiene un punto non vede niente", ([], []),
          (d3["punti"], d3["pacchi"]))
    # ⚠️ IL GATE IN LETTURA VALE ANCHE QUI, e senza questa prova non lo
    # esercitava nessuno: togliere una voce dal catalogo e' l'unica
    # sanzione che abbiamo, e col catalogo INTERO al posto dei vivi il
    # titolare di un punto spento continuerebbe a vedere la sua coda —
    # cioe' la pagina pubblica prometterebbe una cosa che non succede.
    accendi("da-mario")                         # bar-luna si spegne
    come(333)
    d4 = esegui(SRV.pacchi_del_punto)
    prova("il titolare di un punto SPENTO non vede piu' niente",
          ([], []), (d4["punti"], d4["pacchi"]))
    accendi("da-mario", "bar-luna")
    return oid


def prove_anti_oracolo(ann, aperto):
    print("\n\u2500\u2500 L'ANTI-ORACOLO, sul database VERO \u2500\u2500")
    come(777)
    a = rifiuta(SRV.punto_preso_in_carico, aperto)
    come(222)          # il venditore, che e' titolare di un ALTRO punto
    b = rifiuta(SRV.punto_preso_in_carico, aperto)
    come(111)          # chi ha comprato
    c = rifiuta(SRV.punto_preso_in_carico, aperto)
    come(333)
    d = rifiuta(SRV.punto_preso_in_carico, 999999)
    prova("l'estraneo si sente dire 400", 400, a[0])
    prova("...e il titolare di un altro punto risponde IDENTICO", a, b)
    prova("...e chi ha comprato pure", a, c)
    prova("...e l'ordine inesistente pure", a, d)
    prova("...con UN messaggio solo, che non racconta niente",
          "Operazione non permessa", a[1])

    print("\n\u2500\u2500 ...e gli stati che non sono suoi \u2500\u2500")
    o3 = al_punto(ann[2])                       # ancora 'locked'
    come(333)
    prova("un ordine non ancora spedito risponde uguale", a,
          rifiuta(SRV.punto_preso_in_carico, o3))
    o4 = a_inpost(ann[3])
    spedisci(o4)
    come(333)
    prova("...e un ordine su una rete di terzi pure", a,
          rifiuta(SRV.punto_preso_in_carico, o4))
    # IL PUNTO SPENTO NON PRENDE PIU' IN CARICO NIENTE: e' la sola
    # sanzione che abbiamo, e la pagina pubblica la promette.
    o5 = al_punto(ann[4])
    spedisci(o5)
    accendi("da-mario")                         # bar-luna si spegne
    come(333)
    prova("e un punto TOLTO dalla rete non lavora piu'", a,
          rifiuta(SRV.punto_preso_in_carico, o5))
    accendi("da-mario", "bar-luna")
    return o4, o5


def prove_gate_busta(o5, ann_busta):
    print("\n\u2500\u2500 SULLA RETE DI CASA IL VENDITORE NON DEPOSITA \u2500\u2500")
    come(222)
    cod, msg = rifiuta(SRV.deposita_busta_ritiro, o5, None,
                       corpo={"nome": "Mario Rossi", "codice": "ABC123"})
    prova("il deposito si rifiuta", 400, cod)
    prova("...e il rifiuto dice chi scrive il codice", True,
          "codice" in msg.lower())
    cod, msg = rifiuta(SRV.dichiara_busta_diretta, o5)
    prova("e nemmeno la busta diretta si dichiara", 400, cod)
    prova("...col suo perche'", True, len(msg) > 20)
    r = riga_ordine(o5)
    prova("...e la busta e' rimasta intatta", ("", 0),
          (r["busta_codice"], r["busta_il"]))

    # E NEMMENO LA LEGGE (ago 2026, trovato dal GIRO DAL VIVO e non
    # leggendo il codice): il gate qui sopra chiude la SCRITTURA, ma
    # dopo la presa in carico `busta_il` e' pieno — l'ha scritto il
    # server — e chi vende cadeva nel ramo di RILETTURA, leggendo un
    # codice che non ha coniato, col pannello che gli diceva pure
    # <<cio' che HAI depositato>>. Il piano lo dichiara al contrario:
    # lo vedono il compratore e il punto, mai chi vende. La guardia
    # sta nel SERVER e non nel solo client, o sarebbe mezza regola —
    # un client rimasto in cache chiamerebbe la rotta lo stesso.
    oid = al_punto(ann_busta[0])
    spedisci(oid)
    prendi(oid)
    cod_vero = SRV._decifra_contenuto(riga_ordine(oid)["busta_codice"])
    come(222)
    cod, msg = rifiuta(SRV.leggi_busta_ritiro, oid)
    prova("chi vende non legge la busta della rete di casa", 400, cod)
    prova("...e il rifiuto dice il PERCHE', non il 400 muto", True,
          "acquirente" in msg)
    prova("...e non si porta dietro il codice", False, cod_vero in msg)
    # IL ROVESCIO, che e' la meta' che rende la prova capace di
    # fallire: a chi COMPRA la busta si legge come sempre.
    come(111)
    b = esegui(SRV.leggi_busta_ritiro, oid)
    prova("...ma chi compra la legge, col codice", cod_vero, b["codice"])
    prova("...e col nome del PUNTO sul pacco", True, "Bar Luna" in b["nome"])


def prove_promemoria(nostro, terzi):
    print("\n\u2500\u2500 I PROMEMORIA: la rete di casa e' un'altra popolazione \u2500\u2500")
    ora = int(time.time())
    tocca(nostro, spedito_il=ora - 9 * 86400)
    tocca(terzi, spedito_il=ora - 9 * 86400)
    DETTI.clear()
    asyncio.run(SRV.sollecita_buste_ferme())
    # ⚠️ SI GUARDA IL CONTATORE E NON IL TESTO: il promemoria al
    # venditore porta il TITOLO e non il numero dell'ordine (l'id lo
    # scrive solo il 🧊 al tetto), quindi cercarlo nel testo sarebbe
    # una prova che non puo' fallire. `solleciti_busta` invece dice
    # che la RIGA e' entrata nella query, che e' la domanda vera.
    prova("il promemoria della busta SALTA la rete di casa",
          0, riga_ordine(nostro)["solleciti_busta"])
    prova("...e continua a bussare sulle reti di terzi",
          1, riga_ordine(terzi)["solleciti_busta"])
    prova("...bussando a chi vende", [222], [c for c, _ in DETTI])
    # LA MANIGLIA DI CHI COMPRA CAMBIA BERSAGLIO: su questa strada il
    # codice non lo scrive il venditore, quindi bussare a lui sarebbe
    # mandare qualcuno a chiedere una cosa a chi non ce l'ha.
    DETTI.clear()
    come(111)
    esegui(SRV.sollecita_venditore, nostro)
    prova("la maniglia di chi compra bussa al PUNTO, non al venditore",
          [333], [c for c, _ in DETTI])


def prove_nota_moderatore(ann, terzi):
    print("\n\u2500\u2500 LA NOTA AL MODERATORE \u2500\u2500")
    oid = al_punto(ann[5])
    spedisci(oid)
    prendi(oid)
    codice = SRV._decifra_contenuto(riga_ordine(oid)["busta_codice"])
    DETTI.clear()
    come(111)
    esegui(SRV.apri_disputa, oid)
    nota = " || ".join(t for c, t in DETTI if c == 999)
    prova("la nota arriva ai moderatori", True, "Disputa aperta" in nota)
    prova("...e dice che il punto e' NOSTRO", True, "Bar Luna" in nota)
    prova("...e che il punto ha segnato di aver ricevuto il pacco",
          True, "segnato di aver RICEVUTO il pacco il" in nota)
    prova("...col codice negozio, che e' la maniglia del libro mastro",
          True, "neg33333" in nota)
    prova("...e la regola di default che la strada B compra", True,
          "chi ha spedito ha consegnato" in nota)
    prova("MA NON il codice di ritiro", False, codice in nota)
    # IL RAMO DI IERI, sulle reti di terzi, non si e' mosso
    DETTI.clear()
    come(111)
    esegui(SRV.apri_disputa, terzi)
    nota4 = " || ".join(t for c, t in DETTI if c == 999)
    prova("sulla rete di terzi la nota resta quella di sempre", False,
          "Bar Luna" in nota4)
    prova("...col ramo del locker, intatto", True,
          "LOCKER/PUNTO DI RITIRO" in nota4)
    # ⚠️ E LI' IL PUNTO SCRITTO DAL COMPRATORE NON C'E', ed e' giusto:
    # quella nota dice il FATTO (depositata sì/no, quando) e mai il
    # contenuto della busta — l'indirizzo del locker e' roba delle
    # parti. La prova guarda che resti fuori.
    prova("...e senza il punto che il compratore ha scritto", False,
          "Via Verdi" in nota4)

    # L'ALTRA STORIA, che nessuna prova guardava: <<il pacco non e'
    # mai arrivato al punto>> e <<e' arrivato e non l'hanno ritirato>>
    # sono due cose diverse, e prima della presa in carico il
    # moderatore non poteva distinguerle. Il ramo `else` della nota
    # esiste apposta, e va esercitato o resta una promessa che nessuno
    # ha mai letto.
    mai = al_punto(ann[8])
    spedisci(mai)          # spedito, ma il punto non segna niente
    DETTI.clear()
    come(111)
    esegui(SRV.apri_disputa, mai)
    nota5 = " || ".join(t for c, t in DETTI if c == 999)
    prova("il punto che NON ha ricevuto ha una nota sua", True,
          "NON ha mai segnato" in nota5)
    prova("...che manda a guardare il tracciamento", True,
          "tracciamento del corriere" in nota5)
    prova("...e NON applica la regola di default", False,
          "chi ha spedito ha consegnato" in nota5)
    prova("...e le due storie sono due note diverse", False, nota5 == nota)

    # LA DOMANDA DEL PIANO, formulata come tale: <<se non gli dice
    # niente di piu' di oggi, il cantiere non ha comprato quello che
    # prometteva>>. Non basta che una riga esista: si guarda cosa la
    # nota nuova dice E quella di ieri non puo' dire.
    piu = [f for f in ("segnato di aver RICEVUTO il pacco il",
                       "chi ha spedito ha consegnato",
                       "l'ha scritto la piattaforma", "neg33333")
           if f in nota and f not in nota4]
    prova("la nota del punto dice 4 cose che ieri non si potevano dire",
          4, len(piu))


def prove_giro_chiuso(ann):
    print("\n\u2500\u2500 IL GIRO SI CHIUDE, E LA REGRESSIONE \u2500\u2500")
    oid = al_punto(ann[6])
    spedisci(oid)
    prendi(oid)
    come(111)
    esegui(SRV.conferma_ricezione, oid)
    r = riga_ordine(oid)
    prova("chi ritira conferma e l'ordine si chiude", "released", r["stato"])
    prova("...e la presa in carico resta scritta", True,
          r["punto_preso_il"] > 0)

    # LA REGRESSIONE: su InPost il giro e' quello di ieri, byte per byte
    o7 = a_inpost(ann[7])
    spedisci(o7)
    r7 = riga_ordine(o7)
    prova("su InPost il punto e' il testo del COMPRATORE",
          "Locker InPost Via Verdi 3", r7["punto_ritiro"])
    prova("...l'id del catalogo e' vuoto", "", r7["punto_barattolo"])
    prova("...e la presa in carico non esiste", 0, r7["punto_preso_il"])
    come(222)
    esegui(SRV.deposita_busta_ritiro, o7, None,
           corpo={"nome": "Mario Rossi", "codice": "XY99"})
    prova("il venditore deposita la busta come sempre", True,
          bool(riga_ordine(o7)["busta_codice"]))
    come(111)
    b7 = esegui(SRV.leggi_busta_ritiro, o7)
    prova("...e chi compra la legge", "XY99", b7["codice"])
    prova("...col nome che ha scritto lui", "Mario Rossi", b7["nome"])
    return oid, o7


def prove_libro_mastro(sano, terzi):
    print("\n\u2500\u2500 LA RONDA DEL LIBRO MASTRO \u2500\u2500")

    def ronda():
        ADMIN.clear()
        SRV.timbro_scrivi(SRV.TIMBRO_LIBRO_MASTRO, "")
        asyncio.run(SRV.controlla_libro_mastro())
        return " || ".join(ADMIN)

    fuori = ronda()
    prova("sul sano TACE sulla presa in carico", False,
          "presa in carico" in fuori)
    prova("...e sul punto di casa", False, "punto di casa" in fuori)
    # IL TIMBRO SENZA IL CODICE NEGOZIO: una guardia caduta
    tocca(sano, punto_preso_da="")
    fuori = ronda()
    prova("la presa in carico a meta' si vede", True,
          "presa in carico fuori contratto" in fuori)
    prova("...col suo id", True, str(sano) in fuori)
    tocca(sano, punto_preso_da="neg33333")
    # UN PUNTO DI CASA SU UNA STRADA CHE NON E' LA SUA
    # ⚠️ SERVONO TUTT'E DUE I CAMPI: il controllo guarda «l'id del
    # catalogo c'e' MA la via punto no», quindi mettere l'id su un
    # ordine che la via punto ce l'ha costruisce una riga SANA — e la
    # ronda tacerebbe giustamente, mentre la prova crederebbe di aver
    # trovato un buco nel controllo.
    tocca(terzi, punto_barattolo="bar-luna", via_punto=0)
    fuori = ronda()
    prova("il punto di casa fuori dalla via punto si vede", True,
          "punto di casa fuori contratto" in fuori)
    prova("...col suo id", True, str(terzi) in fuori)
    tocca(terzi, punto_barattolo="", via_punto=1)
    prova("...e rimesso a posto la ronda tace di nuovo", False,
          "punto di casa fuori contratto" in ronda())


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
    # --- il secondo tempo: la presa in carico ---
    ann = sezione(prove_presa_in_carico) or []
    aperto = sezione(prove_lista_del_punto, ann)
    terzi, o5 = sezione(prove_anti_oracolo, ann, aperto) or (0, 0)
    sezione(prove_gate_busta, o5, ann[7:])
    sezione(prove_promemoria, o5, terzi)
    sezione(prove_nota_moderatore, ann, terzi)
    sano, o7 = sezione(prove_giro_chiuso, ann) or (0, 0)
    sezione(prove_libro_mastro, sano, o7)
    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
