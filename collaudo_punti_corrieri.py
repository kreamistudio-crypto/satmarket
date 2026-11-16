# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEI PUNTI DI RITIRO E DEI CORRIERI (12 ott 2026, cantiere
«punti-ritiro»).

IL CASO VERO DA CUI NASCE, l'ordine 213: il venditore non aveva
dichiarato corrieri; alla cassa chi comprava ha scelto «punto di
ritiro» e ha scritto a mano una tabaccheria, con davanti le sole mappe
di Poste e InPost; il venditore ha spedito con DHL senza contestare;
la tabaccheria con DHL non lavora, il pacco e' tornato indietro, si e'
aperta una disputa. Barattolo non aveva avvisato nessuno dei due, e in
disputa il punto scelto non si leggeva da nessuna parte.

`prove.py` difende la FORMA e fa girare i giudici puri. Questo script
fa girare la cosa VERA — database, rotte, fatture contate — e risponde
alle domande su cui il cantiere si regge:

  · senza corrieri dichiarati (o coi soli corrieri senza mappa) la via
    punto NON si offre e NON si compra — ma a un indirizzo si vende lo
    stesso: nessuna vendita si blocca;
  · coi corrieri giusti la via punto c'e', con la rete del punto
    scritta nell'ordine (SDA vale Punto Poste);
  · a «Segna come spedito» il corriere che a quella rete non consegna
    viene FERMATO, l'ordine resta com'era e nessuno riceve un avviso
    falso; col corriere giusto parte;
  · un ordine nato PRIMA (il 213 com'era: via punto, rete vuota) non
    si rompe: si spedisce, si corregge, si contesta come ieri;
  · gli annunci importati da Nostr ereditano i corrieri dal Profilo
    di chi li ha pubblicati, perche' il venditore e' la stessa riga;
  · in disputa l'admin riceve il punto, la rete e quante volte il
    venditore l'aveva contestato — e mai l'indirizzo o l'email;
  · la campagna «indica i tuoi corrieri» a leva spenta non fa niente,
    a leva accesa parla UNA volta e solo a chi serve.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. LNbits non
viene mai chiamato — le fatture si contano, non si chiedono — e le
notifiche si registrano invece di partire: gira senza rete e senza
chiavi, ed e' cosi' che gira nella gabbia della CI.

USO:  python collaudo_punti_corrieri.py
"""

import asyncio
import os
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
INVOICES = []
DETTI = []      # (a chi, testo): le notifiche alle persone
ADMIN = []      # quel che arriva ai moderatori

CAMBIO = 100_000.0
UTENTE = {"id": 111, "nome": "Compra", "username": "compra", "admin": False}

CASA = {"nome": "Mario Rossi", "via": "Via Roma 1", "cap": "10100",
        "citta": "Torino", "provincia": "TO", "telefono": "3330000000"}


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
    """Come `prova`, ma per i rifiuti: chiede che alzi 400 e che il
    messaggio dica la cosa giusta — qui il messaggio E' il prodotto,
    perche' e' l'avviso che al 213 e' mancato."""
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
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-punti-corrieri-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    # i segnaposto del config d'esempio: lo scanner dei segreti in CI
    # cerca queste chiavi per NOME e lascia passare solo INCOLLA_QUI
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
    # la leva della campagna NON si scrive qui apposta: deve nascere
    # spenta dal default del codice, ed e' una delle cose da provare
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

    async def detta(chi, testo, *a, **k):
        DETTI.append((chi, testo))

    async def ai_moderatori(testo, *a, **k):
        ADMIN.append(testo)

    server.crea_invoice_escrow = invoice_finta
    server.invoice_pagata = mai_pagata
    server.cambio_btc_eur = cambio_finto
    server.notifica = detta
    server.notifica_admin = ai_moderatori
    server.premia_distintivi = zitta
    server.premia_xp = zitta
    server.polso_ordini_admin = zitta
    server.verifica_utente = lambda *a, **k: UTENTE
    return db


def come(tg_id, admin=False):
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "username": f"u{tg_id}",
        "admin": admin}


def chiama(fn, corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(fn(None))


def esegui(fn, *args, corpo=None):
    """Come `chiama`, ma per le rotte che prendono l'ordine."""
    if corpo is not None:
        async def leggi(_req):
            return corpo
        SRV.leggi_json = leggi
    return asyncio.run(fn(*args))


def semina(corrieri, venditore=222, pulisci=True):
    """Un venditore coi corrieri che ha dichiarato (una LISTA, come li
    manda il cassetto del Profilo) e due annunci che si spediscono.
    I corrieri passano dalla ROTTA VERA: e' lei che decide cosa finisce
    in colonna, e seminare la colonna a mano proverebbe la semina."""
    con = SRV.db()
    if pulisci:
        for t in ("ordine_righe", "ordini", "annunci"):
            con.execute(f"DELETE FROM {t}")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(?,?,?,1)",
                (venditore, f"Vende{venditore}", f"neg{venditore}"))
    con.execute("INSERT OR IGNORE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(111,'Compra','neg11111',1)")
    ids = []
    for titolo in ("Cosa", "Altra"):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
            "spedizione_sats) VALUES(?,?,'desc',30000,'Altro',"
            "'Torino (TO)','attivo',1,'spedizione',5,'sats','buono',1000)",
            (venditore, titolo))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    come(venditore)
    chiama(SRV.scegli_spedizioniere, {"spedizionieri": list(corrieri)})
    come(111)
    return ids


def preventivo(aid):
    come(111)
    return chiama(SRV.preventivo_ordine,
                  {"annuncio_id": aid, "quantita": 1, "offerta_id": 0})


def preventivo_set(ids):
    come(111)
    return chiama(SRV.preventivo_ordine,
                  {"righe": [{"annuncio_id": a, "quantita": 1} for a in ids]})


def vie(p):
    return [s["via"] for s in p["strade"]]


def al_punto(aid, **extra):
    come(111)
    corpo = {"annuncio_id": aid, "quantita": 1, "consegna": "spedizione",
             "spedizione_via": "punto", "tipo_punto": "banco",
             "punto_ritiro": "Tabaccheria Rossi, Via Roma 1"}
    corpo.update(extra)
    return chiama(SRV.compra, corpo)


def a_casa(aid):
    come(111)
    return chiama(SRV.compra, {"annuncio_id": aid, "quantita": 1,
                               "consegna": "spedizione",
                               "spedizione_via": "casa", "indirizzo": CASA})


def riga(oid):
    con = SRV.db()
    r = con.execute("SELECT * FROM ordini WHERE id=?", (oid,)).fetchone()
    con.close()
    return r


def tocca(oid, **campi):
    con = SRV.db()
    con.execute("UPDATE ordini SET " + ", ".join(f"{k}=?" for k in campi)
                + " WHERE id=?", tuple(campi.values()) + (oid,))
    con.commit()
    con.close()


def n_ordini():
    con = SRV.db()
    n = con.execute("SELECT COUNT(*) FROM ordini").fetchone()[0]
    con.close()
    return n


def spedisci(oid, corriere, chi=222):
    come(chi)
    return esegui(SRV.segna_spedito, oid, None, "", "",
                  corpo={"corriere": corriere, "tracking": "JJD0001234567"})


# ---------------------------------------------------------------
def prove_senza_corrieri():
    print("\n── IL 213, RIFATTO: venditore senza corrieri dichiarati ──")
    aid, bid = semina([])
    p = preventivo(aid)
    prova("la cassa NON offre il punto di ritiro", ["casa"], vie(p))
    prova("...e non nomina nessuna rete", ([], ""),
          (p.get("reti"), p.get("spedizioniere")))
    prova("...nemmeno nel carrello", ["casa"], vie(preventivo_set([aid, bid])))
    prima = len(INVOICES)
    alza("chi ci prova lo stesso (la pagina aperta da prima) viene "
         "fermato", lambda: al_punto(aid), "non spedisce ai punti di ritiro")
    alza("...e il rifiuto dice la strada che resta",
         lambda: al_punto(aid), "scegli la spedizione a un indirizzo")
    come(111)
    alza("...anche dal carrello",
         lambda: chiama(SRV.compra, {
             "righe": [{"annuncio_id": aid, "quantita": 1},
                       {"annuncio_id": bid, "quantita": 1}],
             "consegna": "spedizione", "spedizione_via": "punto",
             "tipo_punto": "banco", "punto_ritiro": "Tabaccheria Rossi"}),
         "non spedisce ai punti di ritiro")
    prova("...senza far nascere ordini ne' fatture", (0, 0),
          (n_ordini(), len(INVOICES) - prima))
    # NESSUNA VENDITA SI BLOCCA: e' la meta' della decisione
    r = a_casa(aid)
    o = riga(r["ordine_id"])
    prova("MA la vendita non si ferma: a un indirizzo si compra", True,
          bool(r.get("ordine_id")) and len(INVOICES) == prima + 1)
    prova("...ed e' una spedizione normale, non un punto",
          ("spedizione", 0, "", ""),
          (o["consegna_scelta"], o["via_punto"], o["punto_ritiro"],
           o["rete_punto"]))


def prove_corrieri_senza_mappa():
    print("\n── I CORRIERI SENZA MAPPA: dichiarati, ma niente punto ──")
    aid, _ = semina(["DHL"])
    con = SRV.db()
    u = con.execute("SELECT spedizionieri, spedizioniere FROM utenti "
                    "WHERE tg_id=222").fetchone()
    con.close()
    prova("DHL si puo' dichiarare, e resta scritto", ("|DHL|", "DHL"),
          (u["spedizionieri"], u["spedizioniere"]))
    prova("...ma la cassa non offre il punto", ["casa"],
          vie(preventivo(aid)))
    alza("...e comprare verso un punto si rifiuta",
         lambda: al_punto(aid), "non spedisce ai punti di ritiro")
    aid, _ = semina(["BRT", "GLS", "DHL", "UPS", "Altro"])
    prova("tutti quelli senza mappa insieme: ancora niente punto",
          ["casa"], vie(preventivo(aid)))
    prova("...e a un indirizzo si vende", True,
          bool(a_casa(aid).get("ordine_id")))


def prove_corrieri_giusti():
    print("\n── I CORRIERI CHE AI PUNTI CONSEGNANO ──")
    aid, bid = semina(["SDA"])
    p = preventivo(aid)
    prova("SDA: la cassa offre il punto", ["casa", "punto"], vie(p))
    prova("...ed e' un punto POSTE (SDA consegna li')",
          ["Poste Italiane"], p.get("reti"))
    r = al_punto(aid)
    o = riga(r["ordine_id"])
    prova("...e l'ordine nasce con la rete del PUNTO, non col corriere",
          ("Poste Italiane", "banco", 1),
          (o["rete_punto"], o["tipo_punto"], o["via_punto"]))
    prova("...anche dal carrello", ["casa", "punto"],
          vie(preventivo_set([aid, bid])))

    aid, _ = semina(["Poste Italiane", "SDA"])
    prova("Poste e SDA insieme: la rete e' una, non si chiede quale",
          ["Poste Italiane"], preventivo(aid).get("reti"))

    aid, _ = semina(["InPost", "Poste Italiane", "DHL"])
    p = preventivo(aid)
    prova("due reti con la mappa (piu' DHL): tutte e due, DHL no",
          ["InPost", "Poste Italiane"], p.get("reti"))
    alza("...e chi compra deve dire a quale appartiene il punto",
         lambda: al_punto(aid), "scegli con quale corriere")
    alza("...e non puo' dire DHL, che un punto non ce l'ha",
         lambda: al_punto(aid, rete_punto="DHL"),
         "non spedisce con quel corriere")
    r = al_punto(aid, rete_punto="InPost", tipo_punto="locker",
                 punto_ritiro="Locker InPost Via Verdi 3")
    prova("...con la rete scelta l'ordine nasce, e la porta scritta",
          "InPost", riga(r["ordine_id"])["rete_punto"])


def prove_segna_spedito():
    print("\n── «SEGNA COME SPEDITO»: il corriere sbagliato si ferma ──")
    aid, _ = semina(["Poste Italiane", "DHL"])
    oid = al_punto(aid)["ordine_id"]
    tocca(oid, stato="locked")
    DETTI.clear()
    alza("punto Poste, corriere DHL: FERMATO",
         lambda: spedisci(oid, "DHL"),
         "Questo punto accetta solo Poste Italiane/SDA: con DHL il pacco "
         "verrà rifiutato")
    alza("...e la frase dice le due uscite",
         lambda: spedisci(oid, "DHL"),
         "Cambia corriere, oppure segnala che il punto non va bene")
    o = riga(oid)
    prova("...l'ordine resta com'era: non spedito, nessun corriere",
          ("locked", "", ""), (o["stato"], o["corriere"], o["tracking"]))
    prova("...e chi ha comprato NON riceve «il pacco e' in viaggio»",
          [], DETTI)
    alza("un corriere senza nome si ferma uguale",
         lambda: spedisci(oid, "Altro corriere"), "con un altro corriere")
    alza("...e InPost verso un punto Poste pure",
         lambda: spedisci(oid, "InPost"), "accetta solo Poste Italiane/SDA")
    # L'USCITA 2: contestare il punto, col gesto che c'era gia'
    come(222)
    esegui(SRV.obietta_punto, oid, None, "", "",
           corpo={"motivo": "rete", "nota": "", "proposte": []})
    o = riga(oid)
    prova("la seconda uscita: il venditore contesta il punto", True,
          o["punto_obiettato_il"] > 0 and o["punto_obiezione"] == "rete")
    prova("...e il contatore per il moderatore sale", 1,
          o["punto_obiezioni"])
    # L'USCITA 1: cambiare corriere
    DETTI.clear()
    spedisci(oid, "SDA")
    o = riga(oid)
    prova("la prima uscita: con SDA parte", ("shipped", "SDA"),
          (o["stato"], o["corriere"]))
    # (dal 16 nov 2026 alla spedizione via punto parte anche
    # «arriverà a te» al VENDITORE: chi compra resta uno solo)
    al_compratore = [t for chi, t in DETTI if chi == 111]
    prova("...e adesso si' che chi ha comprato viene avvisato", True,
          len(al_compratore) == 1
          and "in viaggio verso il punto" in al_compratore[0])
    prova("...e il venditore sa che il codice arriva a lui", True,
          [chi for chi, t in DETTI if chi != 111] == [222]
          and any("arriverà a te" in t for chi, t in DETTI if chi == 222))
    prova("...e il contatore delle contestazioni resta (e' la memoria "
          "del moderatore)", 1, o["punto_obiezioni"])

    aid, _ = semina(["InPost"])
    oid = al_punto(aid, tipo_punto="locker",
                   punto_ritiro="Locker InPost Via Verdi 3")["ordine_id"]
    tocca(oid, stato="locked")
    alza("locker InPost, corriere Poste Italiane: fermato",
         lambda: spedisci(oid, "Poste Italiane"), "accetta solo InPost")
    spedisci(oid, "Consegna a mano")
    prova("la consegna a mano passa: non c'e' un corriere da confrontare",
          "shipped", riga(oid)["stato"])

    # la spedizione a CASA non ha niente da confrontare
    aid, _ = semina(["InPost"])
    oid = a_casa(aid)["ordine_id"]
    tocca(oid, stato="locked")
    spedisci(oid, "DHL")
    prova("a un indirizzo si spedisce con chi si vuole", ("shipped", "DHL"),
          (riga(oid)["stato"], riga(oid)["corriere"]))


def ordine_di_prima(aid, punto="Tabaccheria Rossi, Via Roma 1"):
    """Il 213 COM'ERA: un ordine nato quando la via punto si offriva
    senza rete. Oggi la rotta non lo farebbe piu' nascere, quindi lo si
    scrive com'e' in colonna nei database veri — via punto, punto
    scritto a mano, rete VUOTA."""
    oid = a_casa(aid)["ordine_id"]
    tocca(oid, stato="locked", via_punto=1, punto_ritiro=punto,
          tipo_punto="banco", rete_punto="", indirizzo="",
          indirizzo_il=0, indirizzo_atteso=0)
    return oid


def prove_ordini_di_prima():
    print("\n── GLI ORDINI GIA' APERTI NON SI ROMPONO ──")
    aid, _ = semina([])
    oid = ordine_di_prima(aid)
    # chi compra corregge ancora il punto, dal campo dentro l'ordine
    come(111)
    r = esegui(SRV.indica_punto_ritiro, oid, None, "", "",
               corpo={"punto_ritiro": "Bar Sport, Via Po 2",
                      "tipo_punto": "banco"})
    prova("il punto si corregge ancora dal campo dell'ordine",
          "Bar Sport, Via Po 2", r.get("punto_ritiro"))
    # chi vende contesta ancora
    come(222)
    esegui(SRV.obietta_punto, oid, None, "", "",
           corpo={"motivo": "rete", "nota": "", "proposte": []})
    prova("il venditore puo' ancora contestarlo", "rete",
          riga(oid)["punto_obiezione"])
    # ...e spedisce: la rete non c'e', il giudice non sa e lascia fare
    spedisci(oid, "DHL")
    o = riga(oid)
    prova("...e spedirlo, anche con DHL: dove la rete non si sa non si "
          "ferma un ordine gia' aperto", ("shipped", "DHL"),
          (o["stato"], o["corriere"]))

    # un ordine di prima con la rete «Altro» (la voce senza mappa)
    oid = ordine_di_prima(aid)
    tocca(oid, rete_punto="Altro")
    spedisci(oid, "GLS")
    prova("la rete «Altro» di ieri non ferma niente", "shipped",
          riga(oid)["stato"])


def prove_importati():
    print("\n── GLI ANNUNCI IMPORTATI DA NOSTR ──")
    # Chi pubblica su Nostr e' accolto con un account nativo (tg_id
    # negativo, npub_accesso): i suoi annunci importati portano QUEL
    # venditore_id, ed e' la stessa riga in cui entra quando fa il
    # login con la stessa chiave. Quindi il Profilo vale per loro —
    # ed e' cio' che questa sezione prova, invece di crederci.
    npub = "npub1collaudopuntiritiro"
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "npub,npub_verificata,npub_accesso) "
                "VALUES(-501,'Nostrano','negnostr1',1,?,1,?)", (npub, npub))
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
        "spedizione_sats,contatto_nostr,nostr_origine_d) "
        "VALUES(-501,'Importato','desc',30000,'Altro','Torino (TO)',"
        "'attivo',1,'spedizione',1,'sats','buono',1000,?,'d-importato')",
        (npub,))
    aid = cur.lastrowid
    con.commit()
    a = con.execute("SELECT * FROM annunci WHERE id=?", (aid,)).fetchone()
    con.close()
    prova("la riga di prova e' davvero un importato da Nostr", "nostr",
          SRV.origine_annuncio(a))
    prova("senza corrieri nel Profilo: niente punto, come per tutti",
          ["casa"], vie(preventivo(aid)))
    # entra con la sua chiave (la sessione e' la sua riga) e dichiara
    come(-501)
    chiama(SRV.scegli_spedizioniere, {"spedizionieri": ["InPost"]})
    p = preventivo(aid)
    prova("dichiara InPost nel Profilo: l'importato offre il punto",
          ["casa", "punto"], vie(p))
    prova("...della sua rete", ["InPost"], p.get("reti"))
    r = al_punto(aid, tipo_punto="locker",
                 punto_ritiro="Locker InPost Via Verdi 3")
    prova("...e si compra, con la rete scritta nell'ordine", "InPost",
          riga(r["ordine_id"])["rete_punto"])


def prove_disputa():
    print("\n── IN DISPUTA: cosa arriva a chi decide ──")
    aid, _ = semina(["Poste Italiane"])
    oid = al_punto(aid)["ordine_id"]
    tocca(oid, stato="locked")
    come(222)
    esegui(SRV.obietta_punto, oid, None, "", "",
           corpo={"motivo": "inesistente", "nota": "", "proposte": []})
    come(111)
    esegui(SRV.indica_punto_ritiro, oid, None, "", "",
           corpo={"punto_ritiro": "Tabaccheria Rossi, Via Roma 1",
                  "tipo_punto": "banco"})
    come(222)
    esegui(SRV.obietta_punto, oid, None, "", "",
           corpo={"motivo": "rete", "nota": "", "proposte": []})
    spedisci(oid, "Poste Italiane")
    come(111)
    esegui(SRV.apri_disputa, oid, "", "")
    prova("la disputa e' aperta", "dispute", riga(oid)["stato"])
    come(999, admin=True)
    mio = [r for r in SRV.miei_ordini(0, "", "") if r["id"] == oid]
    prova("l'admin la trova nella sua lista", 1, len(mio))
    r = mio[0] if mio else {}
    prova("...col PUNTO di ritiro scelto",
          "Tabaccheria Rossi, Via Roma 1", r.get("punto_ritiro"))
    prova("...la rete e il tipo del punto", ("Poste Italiane", "banco"),
          (r.get("rete_punto"), r.get("tipo_punto")))
    prova("...e QUANTE VOLTE il venditore l'aveva contestato", 2,
          r.get("punto_obiezioni"))
    prova("...e il corriere con cui e' partito", "Poste Italiane",
          r.get("corriere"))
    prova("...ma MAI l'indirizzo o l'email di chi ha comprato",
          (False, False), ("indirizzo" in r, "email_corriere" in r))
    # e le due parti lo ricevono come prima (la pagina lo ridisegna)
    come(111)
    c = [x for x in SRV.miei_ordini(0, "", "") if x["id"] == oid]
    prova("chi ha comprato riceve il suo punto anche in disputa",
          "Tabaccheria Rossi, Via Roma 1",
          c[0].get("punto_ritiro") if c else None)
    come(222)
    v = [x for x in SRV.miei_ordini(0, "", "") if x["id"] == oid]
    prova("...e chi ha venduto pure", "Tabaccheria Rossi, Via Roma 1",
          v[0].get("punto_ritiro") if v else None)


def prove_profilo():
    print("\n── IL PROFILO: cosa sa la pagina dei punti di casa ──")
    # la pagina nasconde la pillola «Barattolo» finche' non c'e' un
    # punto acceso, e per saperlo chiede a /api/me: qui si prova la
    # risposta vera, a punti spenti e accesi
    semina(["DHL"])
    come(222)
    me = asyncio.run(SRV.mio_profilo("", ""))
    prova("a punti spenti il profilo lo dice", False,
          me.get("rete_barattolo_viva"))
    prova("...ma il catalogo arriva INTERO (e' lui che dice quali punti "
          "salvati sono vivi)", list(SRV.SPEDIZIONIERI),
          me.get("spedizionieri"))
    prova("...e le spunte sono quelle dichiarate", ["DHL"],
          me.get("spedizionieri_miei"))
    # un punto di cartone, acceso col gesto del bot
    prima = (SRV.PUNTI_BARATTOLO, SRV.ID_PUNTI_BARATTOLO)
    SRV.PUNTI_BARATTOLO = ({"id": "bar-luna", "nome": "Bar Luna",
                            "indirizzo": "Via Roma 1",
                            "comune": "Torino (TO)", "orari": "lun-sab",
                            "negozio": "neg333"},)
    SRV.ID_PUNTI_BARATTOLO = ("bar-luna",)
    SRV._PUNTI = None
    SRV.imposta_punti(["bar-luna"])
    SRV._PUNTI = None
    me = asyncio.run(SRV.mio_profilo("", ""))
    prova("acceso un punto, il profilo lo dice", True,
          me.get("rete_barattolo_viva"))
    SRV.imposta_punti([])
    SRV.PUNTI_BARATTOLO, SRV.ID_PUNTI_BARATTOLO = prima
    SRV._PUNTI = None
    me = asyncio.run(SRV.mio_profilo("", ""))
    prova("...e spento di nuovo, torna a dire di no", False,
          me.get("rete_barattolo_viva"))
    come(111)


def prove_campagna():
    print("\n── LA CAMPAGNA «INDICA I TUOI CORRIERI», DIETRO LA LEVA ──")
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.commit()
    con.close()
    semina([], venditore=301, pulisci=False)            # niente dichiarato
    semina(["Altro"], venditore=302, pulisci=False)     # la voce di ieri
    semina(["DHL"], venditore=303, pulisci=False)       # ha dichiarato
    semina(["InPost"], venditore=304, pulisci=False)    # ha gia' i punti
    # 305 non dichiara niente ma vende solo col ritiro in zona: la
    # spedizione non lo riguarda, e nemmeno i punti
    con = SRV.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(305,'Ritira','neg305',1)")
    con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione) "
        "VALUES(305,'A mano','desc',30000,'Altro','Torino (TO)','attivo',1,"
        "'ritiro',1,'sats','buono')")
    # 306 non dichiara niente ma il suo annuncio a spedizione e' venduto
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(306,'Finito','neg306',1)")
    con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione) "
        "VALUES(306,'Venduto','desc',30000,'Altro','Torino (TO)','venduto',"
        "1,'spedizione',0,'sats','buono')")
    con.commit()
    con.close()

    prova("la leva nasce SPENTA dal default del codice", False,
          SRV.AVVISO_CORRIERI_PUNTI)
    DETTI.clear()
    asyncio.run(SRV.avvisa_corrieri_per_punti())
    prova("a leva spenta non parte niente", [], DETTI)
    prova("...e non si timbra: la campagna resta intera per quando "
          "Andrea l'accende", "",
          SRV.timbro_letto(SRV.TIMBRO_CAMPAGNA_CORRIERI_PUNTI))

    SRV.AVVISO_CORRIERI_PUNTI = True
    asyncio.run(SRV.avvisa_corrieri_per_punti())
    prova("a leva accesa: chi non ha dichiarato, e chi aveva solo "
          "«Altro»", [301, 302], sorted(chi for chi, _ in DETTI))
    prova("...un messaggio a testa", 2, len(DETTI))
    testo = DETTI[0][1] if DETTI else ""
    prova("...che dice cosa fare e perche'", True,
          "Indica i tuoi corrieri per offrire anche il ritiro nei punti"
          in testo and "Come spedisci" in testo)
    prova("...e che senza si vende lo stesso", True,
          "si vendono lo stesso" in testo)
    prova("chi ha dichiarato DHL, chi ha gia' InPost, chi fa solo il "
          "ritiro e chi non ha annunci attivi: nessuno", [],
          [chi for chi, _ in DETTI if chi in (303, 304, 305, 306)])
    prova("il timbro e' scritto", "fatto",
          SRV.timbro_letto(SRV.TIMBRO_CAMPAGNA_CORRIERI_PUNTI))
    DETTI.clear()
    asyncio.run(SRV.avvisa_corrieri_per_punti())
    prova("UNA VOLTA SOLA: al giro dopo tace, a leva ancora accesa",
          [], DETTI)
    SRV.AVVISO_CORRIERI_PUNTI = False


def main():
    db = avvio()
    print("=" * 66)
    print("COLLAUDO PUNTI DI RITIRO E CORRIERI — db usa-e-getta, LNbits finto")
    print("=" * 66)
    prove_senza_corrieri()
    prove_corrieri_senza_mappa()
    prove_corrieri_giusti()
    prove_segna_spedito()
    prove_ordini_di_prima()
    prove_importati()
    prove_disputa()
    prove_profilo()
    prove_campagna()
    print("\n" + "=" * 66)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 66)
    try:
        os.remove(db)
    except OSError:
        pass
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
