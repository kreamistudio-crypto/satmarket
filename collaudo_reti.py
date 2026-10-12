# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE RETI: chi spedisce dichiara, chi compra sceglie
(ago 2026).

`prove.py` difende la FORMA — che il giudice sia puro, che le due
colonne si scrivano insieme, che una guardia non sparisca in un
riordino. Quello che non puo' fare e' far girare la cosa VERA: le sue
prove non hanno un database, non hanno un endpoint e non coniano una
invoice.

Questo script chiude quel buco, ed e' il calco di `collaudo_conto.py`.
Le domande a cui risponde sono quattro, e sono quelle su cui il
cantiere si regge:

  · il BACKFILL: chi aveva dichiarato UNA rete la ritrova dentro la
    colonna nuova — se sbagliasse, sedici venditori veri perderebbero
    la mappa il giorno del deploy, in silenzio;
  · le DUE COLONNE si scrivono insieme e non possono divergere;
  · la RETE SCELTA e' validata contro le reti di QUEL venditore: chi
    ne dichiara due non puo' ricevere un ordine per una terza —
    sarebbe esattamente il caso che il cantiere esiste per chiudere;
  · il MONDO DI IERI e' intatto: venditore con una rete sola, o senza
    nessuna, si comporta come prima byte per byte.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. LNbits non
viene mai chiamato — le invoice si contano, non si chiedono — quindi
lo script gira anche senza rete e senza chiavi.

USO:  python collaudo_reti.py
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
    messaggio dica la cosa giusta. Il messaggio conta quanto il
    codice — «scegli il corriere» e «quel corriere non ce l'ha» sono
    due problemi diversi per chi legge."""
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
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-reti-"),
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
        """Le notifiche non c'entrano con questo cantiere, ma vanno
        ATTESE: `indica_punto_ritiro` fa `await notifica(...)`, e un
        lambda che torna None non si puo' awaitare."""
        return None

    async def mai_pagata(_hash, _cassaforte=""):
        """La ripresa, quando la richiesta e' DIVERSA, chiede a LNbits
        se la fattura di prima e' stata saldata prima di metterci una
        lapide sopra. Qui nessuno paga mai, quindi la risposta e' no —
        e senza questo stub la domanda uscirebbe davvero sulla rete
        (nessuna prova ci era mai arrivata: il ramo l'ha aperto il
        collaudo della ripresa col tipo corretto)."""
        return False

    server.crea_invoice_escrow = invoice_finta
    server.invoice_pagata = mai_pagata
    server.cambio_btc_eur = cambio_finto
    server.notifica = zitta
    server.polso_ordini_admin = lambda *a, **k: None
    server.verifica_utente = lambda *a, **k: UTENTE
    return db


def chiama(fn, corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(fn(None))


def semina(reti_venditore_txt, prezzo=30_000):
    """Un venditore con le sue reti e un annuncio che si spedisce."""
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute(
        "INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
        "spedizionieri,spedizioniere) VALUES(222,'Vende','neg22222',1,?,?)",
        (reti_venditore_txt,
         [s for s in reti_venditore_txt.split("|") if s][0]
         if reti_venditore_txt else ""))
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(111,'Compra','neg11111',1)")
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
        "spedizione_sats) VALUES(222,'Cosa','desc',?,'Altro',"
        "'Torino (TO)','attivo',1,'spedizione',5,'sats','buono',1000)",
        (prezzo,))
    con.commit()
    aid = cur.lastrowid
    con.close()
    return aid


def compra(aid, corpo_extra):
    corpo = {"annuncio_id": aid, "quantita": 1,
             "consegna": "spedizione", "spedizione_via": "punto"}
    corpo.update(corpo_extra)
    return chiama(SRV.compra, corpo)


def riga_ordine(oid):
    con = SRV.db()
    r = con.execute("SELECT * FROM ordini WHERE id=?", (oid,)).fetchone()
    con.close()
    return r


# ---------------------------------------------------------------
def prove_backfill():
    print("\n── IL BACKFILL: chi aveva una rete la ritrova ──")
    con = SRV.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato,spedizioniere,spedizionieri) "
                "VALUES(777,'Vecchio','neg77777',1,'InPost','')")
    # e uno che una rete non l'ha mai dichiarata: non deve nascere
    # dal nulla una '||' , che sarebbe «dichiarato niente»
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato,spedizioniere,spedizionieri) "
                "VALUES(778,'Mai','neg77778',1,'','')")
    con.commit()
    SRV.riallinea_spedizionieri(con)
    con.commit()
    r = con.execute("SELECT spedizionieri FROM utenti "
                    "WHERE tg_id=777").fetchone()
    prova("la rete di ieri finisce nella colonna nuova, coi pipe",
          "|InPost|", r["spedizionieri"])
    r2 = con.execute("SELECT spedizionieri FROM utenti "
                     "WHERE tg_id=778").fetchone()
    prova("chi non aveva niente resta senza (mai un '||' dal nulla)",
          "", r2["spedizionieri"])
    prova("...e il giudice la legge come una rete sola",
          ["InPost"], SRV.reti_venditore(r["spedizionieri"], ""))

    # IDEMPOTENZA, e non e' una formalita': il backfill gira a OGNI
    # avvio, quindi un secondo giro non deve poter ricoprire una
    # scelta multipla fatta nel frattempo
    con.execute("UPDATE utenti SET spedizionieri='|InPost|Poste Italiane|' "
                "WHERE tg_id=777")
    con.commit()
    SRV.riallinea_spedizionieri(con)
    con.commit()
    r3 = con.execute("SELECT spedizionieri FROM utenti "
                     "WHERE tg_id=777").fetchone()
    prova("un secondo giro NON ricopre la scelta multipla",
          "|InPost|Poste Italiane|", r3["spedizionieri"])
    con.close()


def prove_endpoint():
    print("\n── IL CASSETTO: le due colonne si scrivono INSIEME ──")
    con = SRV.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato) VALUES(222,'Vende','neg22222',1)")
    con.commit()
    con.close()
    UTENTE["id"] = 222
    chiama(SRV.scegli_spedizioniere,
           {"spedizionieri": ["Poste Italiane", "InPost"]})
    con = SRV.db()
    r = con.execute("SELECT spedizionieri, spedizioniere FROM utenti "
                    "WHERE tg_id=222").fetchone()
    con.close()
    prova("le reti vanno in colonna NELL'ORDINE DEL CATALOGO",
          "|InPost|Poste Italiane|", r["spedizionieri"])
    prova("...e la singolare tiene la PRIMA voce (per il client vecchio)",
          "InPost", r["spedizioniere"])

    chiama(SRV.scegli_spedizioniere,
           {"spedizionieri": ["InPost", "InPost", "Poste Italiane"]})
    con = SRV.db()
    r = con.execute("SELECT spedizionieri FROM utenti "
                    "WHERE tg_id=222").fetchone()
    con.close()
    prova("i doppioni si buttano", "|InPost|Poste Italiane|",
          r["spedizionieri"])

    alza("una rete fuori catalogo si rifiuta",
         lambda: chiama(SRV.scegli_spedizioniere,
                        {"spedizionieri": ["Bartolini"]}),
         "sconosciuta")
    alza("e un formato che non e' una lista pure",
         lambda: chiama(SRV.scegli_spedizioniere,
                        {"spedizionieri": "InPost"}),
         "formato")

    # IL CLIENT DI IERI: manda la chiave vecchia, una stringa sola.
    # Deve continuare a funzionare — porta lo stesso significato.
    chiama(SRV.scegli_spedizioniere, {"spedizioniere": "Poste Italiane"})
    con = SRV.db()
    r = con.execute("SELECT spedizionieri, spedizioniere FROM utenti "
                    "WHERE tg_id=222").fetchone()
    con.close()
    prova("il client di IERI (chiave singolare) scrive ancora",
          ("|Poste Italiane|", "Poste Italiane"),
          (r["spedizionieri"], r["spedizioniere"]))

    chiama(SRV.scegli_spedizioniere, {"spedizionieri": []})
    con = SRV.db()
    r = con.execute("SELECT spedizionieri, spedizioniere FROM utenti "
                    "WHERE tg_id=222").fetchone()
    con.close()
    prova("lo spegnimento azzera TUTTE E DUE le colonne",
          ("", ""), (r["spedizionieri"], r["spedizioniere"]))
    UTENTE["id"] = 111


def prove_scelta():
    print("\n── LA RETE LA SCEGLIE CHI COMPRA ──")

    # --- DUE reti: il compratore deve dirlo -----------------------
    aid = semina("|InPost|Poste Italiane|")
    alza("due reti, nessuna scelta: si rifiuta e si dice quali",
         lambda: compra(aid, {"punto_ritiro": "Via Roma 1"}),
         "scegli con quale corriere")
    alza("...e una rete che il venditore NON ha si rifiuta",
         lambda: compra(aid, {"punto_ritiro": "Via Roma 1",
                              "rete_punto": "Altro"}),
         "non spedisce con quel corriere")
    r = compra(aid, {"punto_ritiro": "Via Roma 1",
                     "rete_punto": "Poste Italiane"})
    prova("la rete scelta torna nella risposta",
          "Poste Italiane", r.get("rete_punto"))
    riga = riga_ordine(r["ordine_id"])
    prova("...e finisce in colonna",
          "Poste Italiane", riga["rete_punto"])
    prova("...senza toccare consegna_scelta, che resta 'spedizione'",
          ("spedizione", 1),
          (riga["consegna_scelta"], riga["via_punto"]))

    # --- UNA rete: si fissa alla nascita, senza chiedere ----------
    aid = semina("|InPost|")
    r = compra(aid, {"punto_ritiro": "Locker A"})
    prova("una rete sola: si fissa alla nascita, il client non la manda",
          "InPost", riga_ordine(r["ordine_id"])["rete_punto"])

    # --- ZERO reti: la via punto NON si offre (12 ott 2026) -------
    # Qui c'era «il mondo di ieri, byte per byte»: senza reti la via
    # punto passava lo stesso, col punto scritto alla cieca. L'ha
    # rovesciato il caso dell'ordine 213 (cantiere «punti-ritiro»): un
    # pacco DHL rifiutato dalla tabaccheria scelta cosi'. Il giro
    # intero di quel caso sta in `collaudo_punti_corrieri.py`; qui
    # resta la riga che dice che il mondo di ieri e' finito apposta.
    aid = semina("")
    prima = len(INVOICES)
    alza("nessuna rete dichiarata: la via punto si rifiuta",
         lambda: compra(aid, {"punto_ritiro": "Un punto qualunque"}),
         "non spedisce ai punti di ritiro")
    alza("...anche senza punto scritto, e dice la strada che resta",
         lambda: compra(aid, {}),
         "scegli la spedizione a un indirizzo")
    con = SRV.db()
    nati = con.execute("SELECT COUNT(*) FROM ordini").fetchone()[0]
    con.close()
    prova("...e non nasce nessun ordine, ne' si chiede una fattura",
          (0, 0), (nati, len(INVOICES) - prima))

    # --- la via CASA non si porta dietro nessuna rete -------------
    aid = semina("|InPost|Poste Italiane|")
    r = chiama(SRV.compra, {"annuncio_id": aid, "quantita": 1,
                            "consegna": "spedizione",
                            "spedizione_via": "casa",
                            "indirizzo": {"nome": "Mario Rossi",
                                          "via": "Via Roma 1",
                                          "cap": "10100",
                                          "citta": "Torino",
                                          "provincia": "TO",
                                          "telefono": "3330000000"}})
    riga = riga_ordine(r["ordine_id"])
    prova("la via CASA non scrive nessuna rete",
          ("", 0), (riga["rete_punto"], riga["via_punto"]))


def prove_tipo_punto():
    """LOCKER O PUNTO COL BANCO: la seconda meta' della domanda.
    Un locker e una tabaccheria non sono la stessa consegna — chi
    vende compra un'ETICHETTA DIVERSA, ed e' il costo da cui nasce il
    cantiere."""
    print("\n── LOCKER O PUNTO COL BANCO ──")
    aid = semina("|InPost|")
    r = compra(aid, {"punto_ritiro": "Locker A", "tipo_punto": "locker"})
    prova("il tipo scelto finisce in colonna", "locker",
          riga_ordine(r["ordine_id"])["tipo_punto"])
    prova("...e torna nella risposta", "locker", r.get("tipo_punto"))

    aid = semina("|InPost|")
    r = compra(aid, {"punto_ritiro": "Tabaccheria Rossi",
                     "tipo_punto": "banco"})
    prova("...e vale anche per il banco", "banco",
          riga_ordine(r["ordine_id"])["tipo_punto"])

    aid = semina("|InPost|")
    alza("un tipo inventato si rifiuta",
         lambda: compra(aid, {"punto_ritiro": "X", "tipo_punto": "furgone"}),
         "tipo di punto sconosciuto")

    # IL CLIENT DI IERI non manda il campo: l'ordine nasce lo stesso
    # ('' = non dichiarato) e il venditore legge la forma di prima.
    # E' la stessa tolleranza della rete, e il 400 vive nel client.
    aid = semina("|InPost|")
    r = compra(aid, {"punto_ritiro": "Punto qualunque"})
    prova("il client di ieri non manda il tipo: l'ordine nasce lo stesso",
          "", riga_ordine(r["ordine_id"])["tipo_punto"])

    # LA CORREZIONE DENTRO L'ORDINE, che e' la rete di sicurezza degli
    # ordini nati senza: la chiave ASSENTE conserva quel che c'era
    oid = r["ordine_id"]
    con = SRV.db()
    con.execute("UPDATE ordini SET stato='locked' WHERE id=?", (oid,))
    con.commit()
    con.close()
    UTENTE["id"] = 111
    chiama(lambda _r: SRV.indica_punto_ritiro(oid, _r),
           {"punto_ritiro": "Locker B", "tipo_punto": "locker"})
    prova("nell'ordine il tipo si scrive col punto", ("Locker B", "locker"),
          (riga_ordine(oid)["punto_ritiro"], riga_ordine(oid)["tipo_punto"]))
    chiama(lambda _r: SRV.indica_punto_ritiro(oid, _r),
           {"punto_ritiro": "Locker C"})
    prova("...e la chiave assente CONSERVA il tipo (patto dello stock)",
          ("Locker C", "locker"),
          (riga_ordine(oid)["punto_ritiro"], riga_ordine(oid)["tipo_punto"]))


def punti_di(chi=111):
    con = SRV.db()
    r = [dict(x) for x in con.execute(
        "SELECT rete, tipo, punto, creato FROM punti_ritiro "
        "WHERE tg_id=? ORDER BY rete", (chi,)).fetchall()]
    con.close()
    return r


def salva_punto(corpo):
    return chiama(SRV.salva_punto_ritiro, corpo)


def preventivo(aid, qta=1):
    return chiama(SRV.preventivo_ordine,
                  {"annuncio_id": aid, "quantita": qta, "offerta_id": 0})


def prove_punti_salvati():
    """I PUNTI CHE CHI COMPRA SI TIENE — l'endpoint e il match veri.

    `prove.py` difende la forma; qui si gira la cosa: un punto si salva,
    sostituisce, si toglie, e soprattutto ARRIVA (o non arriva) dentro
    il preventivo secondo le reti che quel venditore ha dichiarato."""
    print("\n── I PUNTI SALVATI: l'endpoint e il match ──")
    con = SRV.db()
    con.execute("DELETE FROM punti_ritiro")
    con.commit()
    con.close()

    r = salva_punto({"rete": "InPost", "tipo": "locker",
                     "punto": "  Locker   Via Roma 1  "})
    prova("si salva, e il testo arriva normalizzato",
          [{"rete": "InPost", "tipo": "locker", "punto": "Locker Via Roma 1"}],
          r["punti"])
    prova("...e in colonna c'e' una riga sola", 1, len(punti_di()))

    salva_punto({"rete": "InPost", "tipo": "banco",
                 "punto": "Tabaccheria Bianchi"})
    prova("ri-salvare sulla stessa rete SOSTITUISCE, non aggiunge",
          [("InPost", "banco", "Tabaccheria Bianchi")],
          [(p["rete"], p["tipo"], p["punto"]) for p in punti_di()])

    salva_punto({"rete": "Poste Italiane", "tipo": "banco",
                 "punto": "Bar dello sport"})
    prova("una rete diversa e' una riga diversa", 2, len(punti_di()))

    alza("una rete fuori catalogo si rifiuta",
         lambda: salva_punto({"rete": "PonyExpress", "tipo": "locker",
                              "punto": "x"}), "sconosciuta")
    alza("...e un punto senza tipo pure, che il tipo qui e' il dato",
         lambda: salva_punto({"rete": "Altro", "tipo": "",
                              "punto": "Il portiere"}), "locker")
    prova("nessuno dei due rifiuti ha scritto niente", 2, len(punti_di()))

    # --- IL MATCH: e' il cuore del cantiere -------------------------
    aid = semina("|InPost|")
    p = preventivo(aid)
    prova("il venditore dichiara InPost: arriva il punto InPost",
          [{"rete": "InPost", "tipo": "banco",
            "punto": "Tabaccheria Bianchi"}], p["punti_salvati"])

    aid = semina("|Poste Italiane|")
    prova("dichiara solo Poste: arriva quello di Poste, non l'altro",
          ["Poste Italiane"],
          [x["rete"] for x in preventivo(aid)["punti_salvati"]])

    aid = semina("|Altro|")
    prova("dichiara una rete per cui non ho niente: niente da "
          "precompilare", [], preventivo(aid)["punti_salvati"])

    aid = semina("")
    prova("non dichiara niente: niente, che li' la rete non si sa",
          [], preventivo(aid)["punti_salvati"])

    # DUE RETI E DUE PUNTI: vince il piu' recente SALVATO, ed e' la
    # domanda a cui il cantiere doveva rispondere.
    # `creato` si invecchia A MANO: i due salvataggi qui sopra cadono
    # nello STESSO secondo, e a parita' comanda il pareggio sulla rete
    # (che ha la sua prova in prove.py). Invecchiare InPost e' l'unico
    # modo di provare l'ordine VERO invece del pareggio.
    con = SRV.db()
    con.execute("UPDATE punti_ritiro SET creato=creato-100 "
                "WHERE tg_id=111 AND rete='InPost'")
    con.commit()
    con.close()
    aid = semina("|InPost|Poste Italiane|")
    prova("due reti: il piu' recente salvato viene per primo",
          ["Poste Italiane", "InPost"],
          [x["rete"] for x in preventivo(aid)["punti_salvati"]])
    salva_punto({"rete": "InPost", "tipo": "locker", "punto": "Il nuovo"})
    prova("...e ri-salvare l'altro lo rimette in testa",
          ["InPost", "Poste Italiane"],
          [x["rete"] for x in preventivo(aid)["punti_salvati"]])

    prova("il criterio dell'ordine non esce mai dal server", False,
          any("creato" in x for x in preventivo(aid)["punti_salvati"]))

    # --- IL PUNTO VUOTO TOGLIE --------------------------------------
    r = salva_punto({"rete": "InPost", "tipo": "", "punto": ""})
    prova("il punto vuoto toglie quella rete, e solo quella",
          ["Poste Italiane"], [x["rete"] for x in r["punti"]])
    prova("...e togliere una rete che non c'e' non e' un errore",
          ["Poste Italiane"],
          [x["rete"] for x in
           salva_punto({"rete": "Altro", "tipo": "", "punto": ""})["punti"]])

    # --- L'ORDINE NON CAMBIA DI UN SAT ------------------------------
    # La prova che il cantiere non tocca il denaro: si compra con lo
    # stesso corpo di sempre e l'ordine nasce identico, punti salvati o
    # no — la tabella conserva una preferenza, non autorizza niente.
    aid = semina("|Poste Italiane|")
    INVOICES.clear()
    oid = compra(aid, {"punto_ritiro": "Bar dello sport",
                       "tipo_punto": "banco"})["ordine_id"]
    o = riga_ordine(oid)
    prova("l'ordine porta il punto e la rete come sempre",
          ("Bar dello sport", "Poste Italiane", "banco", 1),
          (o["punto_ritiro"], o["rete_punto"], o["tipo_punto"],
           o["via_punto"]))
    prova("...e la fattura chiede il totale di sempre",
          [o["prezzo_sats"]], INVOICES)


def prove_ripresa_punto():
    """LA RIPRESA col tipo corretto (il guasto B): correggere «locker»
    in «punto col banco» senza toccare l'indirizzo DEVE fare una
    fattura nuova. Prima tornava quella di prima, col tipo vecchio — e
    il venditore comprava l'etichetta sbagliata."""
    print("\n── LA RIPRESA: correggere il tipo non riusa la fattura ──")
    aid = semina("|InPost|")
    INVOICES.clear()
    a = compra(aid, {"punto_ritiro": "Via Roma 1", "tipo_punto": "locker"})
    prova("il primo acquisto conia una fattura", 1, len(INVOICES))
    b = compra(aid, {"punto_ritiro": "Via Roma 1", "tipo_punto": "locker"})
    prova("la richiesta IDENTICA riprende la sua, senza coniarne",
          (a["ordine_id"], 1), (b["ordine_id"], len(INVOICES)))
    c = compra(aid, {"punto_ritiro": "Via Roma 1", "tipo_punto": "banco"})
    prova("cambiare il TIPO e' una richiesta diversa: fattura nuova",
          2, len(INVOICES))
    prova("...e l'ordine porta il tipo corretto, non quello di prima",
          "banco", riga_ordine(c["ordine_id"])["tipo_punto"])

    # e il gemello sulla rete, che dal profilo si scambia con un tocco
    aid = semina("|InPost|Poste Italiane|")
    INVOICES.clear()
    compra(aid, {"punto_ritiro": "Da Mario", "rete_punto": "InPost",
                 "tipo_punto": "banco"})
    d = compra(aid, {"punto_ritiro": "Da Mario",
                     "rete_punto": "Poste Italiane", "tipo_punto": "banco"})
    prova("cambiare la RETE idem: la stessa tabaccheria su due reti "
          "non e' lo stesso ordine", 2, len(INVOICES))
    prova("...e l'ordine porta la rete nuova", "Poste Italiane",
          riga_ordine(d["ordine_id"])["rete_punto"])


def prove_fusione_punti():
    """La tabella e' una figlia di `utenti`: se la fusione la
    dimenticasse, i punti resterebbero attaccati a una riga morta."""
    print("\n── LA FUSIONE: i punti seguono l'utente ──")
    con = SRV.db()
    con.execute("DELETE FROM punti_ritiro")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato,npub_accesso) VALUES(-7,'Nativo','neg77777',"
                "1,'npub1collaudo')")
    for tg, rete, punto in ((111, "InPost", "Quello di Telegram"),
                            (-7, "InPost", "Quello di Nostr"),
                            (-7, "Poste Italiane", "Solo di Nostr")):
        con.execute("INSERT OR REPLACE INTO punti_ritiro"
                    "(tg_id,rete,tipo,punto,creato) VALUES(?,?,'banco',?,1)",
                    (tg, rete, punto))
    con.commit()
    con.close()

    # la firma e' (chi RESTA, chi muore): invertirla fa scattare la
    # prima guardia e la fusione rifiuta con una frase gentile, cioe'
    # la prova passerebbe per il motivo sbagliato — per questo si
    # guarda anche il valore di ritorno.
    esito = SRV.esegui_fusione(111, -7)
    prova("la fusione e' avvenuta davvero (non un rifiuto gentile)",
          True, not isinstance(esito, str))

    prova("la meta' che muore non lascia righe", [], punti_di(-7))
    prova("...e sulla stessa rete vince la meta' TELEGRAM, dichiarato",
          [("InPost", "Quello di Telegram"),
           ("Poste Italiane", "Solo di Nostr")],
          [(p["rete"], p["punto"]) for p in punti_di(111)])


def prove_libro_mastro():
    print("\n── LA RONDA DEVE TACERE ──")
    guasti = []
    con = SRV.db()
    for nome, _perche, sql in SRV.CONTROLLI_LIBRO_MASTRO:
        righe = con.execute(sql).fetchall()
        if righe:
            guasti.append((nome, [dict(r) for r in righe]))
    con.close()
    prova("nessun controllo del libro mastro ha qualcosa da dire",
          [], guasti)


def main():
    db = avvio()
    print("=" * 66)
    print("COLLAUDO DELLE RETI — database usa-e-getta, LNbits finto")
    print("=" * 66)
    prove_backfill()
    prove_endpoint()
    prove_scelta()
    prove_tipo_punto()
    prove_punti_salvati()
    prove_ripresa_punto()
    prove_fusione_punti()
    prove_libro_mastro()
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
