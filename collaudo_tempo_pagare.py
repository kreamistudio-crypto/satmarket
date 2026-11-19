# -*- coding: utf-8 -*-
"""
IL TEMPO PER PAGARE SUL SERVER VERO, COGLI EVENTI FINTI DEL COORDINATORE
(18 nov 2026, cantiere tempo-pagamento; Andrea, da JJ che scambia tanto:
«nel momento in cui lo prendi hai un'ora di tempo», e «Tutto insieme,
nodo compreso»).

Il caso: chi pubblica un ordine di vendita sceglie entro quanto chi lo
prende manda gli euro — un orologio da 15 minuti a 24 ore da quando lo
scambio e' attivo, e sotto le 24 ore solo coi metodi veloci — e
allo scadere senza «Ho inviato» il NODO annulla da solo (patch 0013 del
fork: chiede il tempo a `/api/p2p/finestre`, e racconta `expired` /
`payment-window`). `prove.py` difende i giudici estratti
(`prove_tempo_pagare_p2p`); qui girano le ROTTE VERE — l'intestazione
(`/api/p2p/ordini`), i volti (`/api/p2p/facce`), la porta del nodo col
suo bearer, gli eventi di mostrod (`/api/p2p/evento`), l'archivio
(`/api/p2p/scambi`) — su un database usa-e-getta.

  1. A LEVA SPENTA e' come ieri: l'intestazione non scrive, i volti non
     ne portano, la porta del nodo non esiste;
  2. l'intestazione: solo sulle vendite di chi dichiara, mai col PayCode,
     col contanti di persona o su un acquisto, solo i minuti dell'orologio,
     la prima resta, e col bonifico ordinario l'ora chiesta vale 24 ore;
  3. LA PORTA DEL NODO: 404 senza segreto, 403 col segreto sbagliato, 400
     su un corpo storto, e una risposta per ogni ordine chiesto (dal 19
     nov 2026, la 0014: null = «non ancora», 0 = «mai»);
  4. LO SCAMBIO DI UN'ORA diventa attivo: chi compra lo legge nella frase
     della garanzia, ma il tempo PARTE DAL RECAPITO (19 nov 2026): prima
     il termine e' 0 e il nodo legge null; col recapito l'archivio da' a
     tutt'e due lo stesso termine, i promemoria sono quelli col tempo che
     resta (l'ultimo a dieci minuti dalla fine), e chi vende ha il suo a
     dieci minuti;
  5. IL TEMPO FINISCE col recapito detto presto (il nodo di ieri, la
     0013): un «non completato» a chi compra, e i due messaggi del nodo
     che annulla;
  6. IL RECAPITO DETTO TARDI (piu' di meta' del tempo, col nodo di ieri),
     e la domanda tardiva del nodo (16 minuti dopo il recapito: nessun
     tempo): non si conta a nessuno, e il journal dice perche';
  6b. LA 0014: il tempo finisce e l'ordine TORNA NEL LIBRO
     (`payment-window-republished`): il «non completato» a chi compra, e
     i due messaggi del ritorno nel libro;
  7. la leva spenta CHIUDE ANCHE LA PORTA DEL NODO: l'interruttore
     d'emergenza vale per lui.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram (le notifiche finiscono in
una lista), niente relay, niente coordinatore.

USO:  python collaudo_tempo_pagare.py
"""

import asyncio
import contextlib
import io
import json
import re
import sys
import time

import collaudo_pagamento_p2p as banco

SEGRETO = "collaudo-segreto"                  # la porta degli eventi
SEGRETO_FINESTRA = "collaudo-segreto-finestre"  # la porta del tempo per pagare
PUBBLICA, PRENDE, PASSA = banco.VENDE, banco.COMPRA, banco.ESTRANEO
UNA = "7e3a0000-0a0a-4a2b-9c3d-00000000000a"    # vendita SEPA Instant di 111, 1 ora
QUATTRO = "7e3a0000-0b0b-4a2b-9c3d-00000000000b"  # vendita Revolut di 111, 4 ore
LENTO = "7e3a0000-1111-4a2b-9c3d-000000000011"  # vendita SEPA ordinario di 111, 1 ora chiesta: 24
BZ = "7e3a0000-0c0c-4a2b-9c3d-00000000000c"     # vendita Barattozon di 111: mai
CONT = "7e3a0000-0d0d-4a2b-9c3d-00000000000d"   # vendita SEPA + Contanti di 111: mai
COMPRO = "7e3a0000-0e0e-4a2b-9c3d-00000000000e"  # acquisto di 111: mai
ALTRUI = "7e3a0000-0f0f-4a2b-9c3d-00000000000f"  # vendita di 333: non e' di chi dichiara
STORTO = "7e3a0000-1010-4a2b-9c3d-000000000010"  # vendita di 111, «20 minuti»: fuori dall'orologio
TORNA = "7e3a0000-1212-4a2b-9c3d-000000000012"  # vendita Revolut di 111, 1 ora: torna nel libro (0014)
_TAG = re.compile(r"</?[bi]>")


def busta(ordine, azione, ts, attore, dettaglio):
    b = banco.Busta({"v": 1, "order": ordine, "action": azione, "ts": ts,
                     "buyer": banco.CHIAVE_COMPRA, "seller": banco.CHIAVE_VENDE,
                     "actor": attore, "detail": dettaglio})
    b.headers = {"authorization": f"Bearer {SEGRETO}"}
    return b


async def posta(ordine, azione, ts, attore="mostro", dettaglio=""):
    """Il POST di mostrod alla rotta vera, e i suoi avvisi lasciati finire.
    Torna (risposta, journal)."""
    uscita = io.StringIO()
    with contextlib.redirect_stdout(uscita):
        try:
            r = await banco.SRV.evento_p2p(busta(ordine, azione, ts, attore, dettaglio))
            r = json.loads(r.body)
        except Exception as e:
            r = getattr(e, "status_code", type(e).__name__)
        if banco.SRV._TASK_EVENTI_P2P:
            await asyncio.gather(*list(banco.SRV._TASK_EVENTI_P2P), return_exceptions=True)
    return r, uscita.getvalue()


async def chiama(fn, corpo=None, autorizzazione=None):
    d = corpo if corpo is not None else {}

    async def leggi(_req):
        if not isinstance(d, dict):
            raise banco.SRV.HTTPException(400, "Richiesta malformata")
        return d
    banco.SRV.leggi_json = leggi
    b = banco.Busta(d)
    if autorizzazione is not None:
        b.headers = {"authorization": autorizzazione}
    try:
        r = await fn(b)
    except Exception as e:
        return (getattr(e, "status_code", type(e).__name__),
                str(getattr(e, "detail", e)))
    return json.loads(r.body) if hasattr(r, "body") else r


async def intesta(chi, mappa):
    """«Questi ordini li ho pubblicati io», col tempo per pagare: la rotta vera."""
    banco.come(chi)
    return await chiama(banco.SRV.registra_ordini_p2p,
                        {"ordini": sorted(mappa), "pubblicati": True, "minuti_pagare": mappa})


async def facce(chi, ordini):
    banco.come(chi)
    return await chiama(banco.SRV.facce_ordini_p2p, {"ordini": ordini})


async def finestre(ordini, segreto=SEGRETO_FINESTRA):
    return await chiama(banco.SRV.finestre_p2p, ordini, f"Bearer {segreto}")


async def scambio(chi, ordine):
    """La riga dell'archivio di `chi` per quell'ordine, dalla rotta vera."""
    banco.come(chi)
    r = await banco.SRV.scambi_p2p("", "")
    return (json.loads(r.body).get("scambi") or {}).get(ordine) or {}


def codice_di(r):
    """Il codice di un rifiuto; 200 se la rotta ha risposto (un rifiuto
    mancato diventa una rossa col suo nome, non un'eccezione)."""
    return r[0] if isinstance(r, tuple) else 200


def ore(ordine):
    """I minuti scritti sulla riga (il nome e' di quando erano ore)."""
    con = banco.con_db()
    r = con.execute("SELECT minuti_pagare FROM p2p_ordini WHERE ordine=?", (ordine,)).fetchone()
    con.close()
    return int(r[0] or 0) if r else None


def attese(ordine, chi):
    con = banco.con_db()
    r = sorted((x["momento"], x["fonte"]) for x in con.execute(
        "SELECT momento, fonte FROM p2p_attese WHERE ordine=? AND tg_id=? AND fonte LIKE "
        "'sollecito%'", (ordine, chi)))
    con.close()
    return r


def scadenze(ordine, chi, fonte):
    con = banco.con_db()
    r = [(x["scade"], x["testo"]) for x in con.execute(
        "SELECT scade, testo FROM p2p_attese WHERE ordine=? AND tg_id=? AND fonte=? "
        "ORDER BY scade", (ordine, chi, fonte))]
    con.close()
    return r


def esiti(tg, ordine):
    con = banco.con_db()
    r = sorted(tuple(x) for x in con.execute(
        "SELECT esito, dettaglio FROM p2p_esiti WHERE tg_id=? AND ordine=?", (tg, ordine)))
    con.close()
    return r


def detto(a_chi, frammento, dopo=0):
    """L'ultima notifica a quella persona, fra quelle dopo `dopo`, che contiene
    il frammento, senza tag."""
    for chi, testo in reversed(banco.DETTO[dopo:]):
        t = _TAG.sub("", testo)
        if chi == a_chi and frammento in t:
            return t
    return ""


def recapito(ordine, quando):
    """Chi vende dice dove ricevere gli euro: il giudice vero."""
    con = banco.con_db()
    try:
        r = banco.SRV._avviso_recapito_p2p(con, ordine, PUBBLICA, quando)
        con.commit()
    finally:
        con.close()
    return r


def indietro(ordine, secondi):
    """Il tempo che passa: la cronaca dello scambio si sposta indietro."""
    con = banco.con_db()
    con.execute("UPDATE p2p_momenti SET quando=quando-? WHERE ordine=?", (secondi, ordine))
    con.commit()
    con.close()


def semina_ordini():
    con = banco.con_db()
    adesso = int(time.time())
    for ordine, chi, lato, metodi in (
            (UNA, PUBBLICA, "sell", ["SEPA Instant"]), (QUATTRO, PUBBLICA, "sell", ["Revolut"]),
            (LENTO, PUBBLICA, "sell", ["SEPA Instant", "SEPA"]),
            (BZ, PUBBLICA, "sell", ["Contanti al tabacchino 23.47"]),
            (CONT, PUBBLICA, "sell", ["SEPA", "Contanti"]),
            (COMPRO, PUBBLICA, "buy", ["SEPA"]), (ALTRUI, PASSA, "sell", ["SEPA"]),
            (STORTO, PUBBLICA, "sell", ["SEPA"]), (TORNA, PUBBLICA, "sell", ["Revolut"])):
        con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,sats,euro,"
                    "metodi) VALUES(?,?,?,'pending',?,1,50000,'50,00 €',?)",
                    (ordine, chi, adesso, lato, json.dumps(metodi)))
    con.commit()
    con.close()


async def attivo(ordine, t):
    """Una vendita presa da chi compra, fino alla garanzia bloccata (t+30)."""
    await posta(ordine, "taken", t, "buyer", "invoice-next")
    await posta(ordine, "buyer-invoice-added", t + 10, "buyer", "hold-next")
    await posta(ordine, "hold-invoice-requested", t + 11, "mostro", "invoice")
    return await posta(ordine, "hold-invoice-paid", t + 30, "seller", "active")


async def giro_intero():
    SRV = banco.SRV
    prova = banco.prova

    print("\n1) a leva spenta e' come ieri")
    SRV.P2P_TEMPO_PER_PAGARE = False
    SRV.P2P_FINESTRA_SEGRETO = SEGRETO_FINESTRA
    r = await intesta(PUBBLICA, {UNA: 60})
    prova("l'intestazione passa, ma del tempo per pagare non scrive niente", (True, 0),
          (r.get("ok"), ore(UNA)))
    prova("...e i volti non ne portano", {}, (await facce(PRENDE, [UNA]))["minuti_pagare"])
    prova("...e la porta del nodo non c'e', nemmeno col segreto giusto",
          404, codice_di(await finestre({"ordini": [UNA]})))
    prova("...e nella busta delle leve la pagina lo legge spento", False,
          SRV._p2p_leve()["tempoPagare"])

    print("\n2) l'intestazione, a leva accesa")
    SRV.P2P_TEMPO_PER_PAGARE = True
    lim = SRV._p2p_leve()["minutiPagareLimiti"]
    prova("nella busta delle leve: acceso, l'orologio da 15 minuti a 24 ore a quarti "
          "d'ora, i metodi veloci, 24 ore di serie",
          (True, 15, 1440, 15, ["SEPA Instant", "Revolut", "Satispay", "PayPal"], 1440),
          (SRV._p2p_leve()["tempoPagare"], lim["min"], lim["max"], lim["passo"],
           lim["veloci"], SRV._p2p_leve()["minutiPagareDiSerie"]))
    await intesta(PUBBLICA, {UNA: 60, QUATTRO: 240, LENTO: 60, BZ: 60, CONT: 60, COMPRO: 60,
                             ALTRUI: 60, STORTO: 20, TORNA: 60})
    prova("si scrive sulle sue vendite; «20 minuti» e' fuori dall'orologio e quella di un "
          "altro non entra", (60, 240, 60, 0, 0),
          (ore(UNA), ore(QUATTRO), ore(LENTO), ore(ALTRUI), ore(STORTO)))
    await intesta(PUBBLICA, {UNA: 1440})
    prova("LA PRIMA RESTA: rifatta con 24 ore, l'ora scelta non si sposta", 60, ore(UNA))
    f = await facce(PRENDE, [UNA, QUATTRO, LENTO, BZ, CONT, COMPRO, ALTRUI, STORTO])
    prova("chi guarda il libro lo legge dai volti, e SOLO dove ha senso: niente col "
          "PayCode, col contanti di persona, sugli acquisti; e col bonifico ordinario fra i "
          "metodi l'ora chiesta esce come 24 ore",
          {UNA: 60, QUATTRO: 240, LENTO: 1440}, f["minuti_pagare"])

    print("\n3) la porta del nodo")
    SRV.P2P_FINESTRA_SEGRETO = ""
    prova("senza segreto nel config la porta non c'e'", 404,
          codice_di(await finestre({"ordini": [UNA]})))
    SRV.P2P_FINESTRA_SEGRETO = "INCOLLA_QUI_UN_SEGRETO_CASUALE"
    prova("...e nemmeno col segnaposto di config_esempio", 404,
          codice_di(await finestre({"ordini": [UNA]}, "INCOLLA_QUI_UN_SEGRETO_CASUALE")))
    SRV.P2P_FINESTRA_SEGRETO = SEGRETO_FINESTRA
    prova("col segreto sbagliato: 403", 403,
          codice_di(await finestre({"ordini": [UNA]}, "altro")))
    prova("...e il segreto degli EVENTI non apre questa porta (la M6 dell'audit)", 403,
          codice_di(await finestre({"ordini": [UNA]}, SEGRETO)))
    prova("un corpo storto: 400", 400, codice_di(await finestre({"ordini": "tutti"})))
    r = await finestre({"ordini": [UNA, QUATTRO, LENTO, BZ, CONT, COMPRO, ALTRUI, STORTO]})
    prova("col segreto giusto (dal 19 nov 2026, la 0014): OGNI ordine chiesto ha la sua "
          "risposta — chi ha un tempo ma nessuno scambio col recapito detto ha null («non "
          "ancora», il nodo richiede), chi non ha un tempo 0 («mai»)",
          {UNA: None, QUATTRO: None, LENTO: None, BZ: 0, CONT: 0, COMPRO: 0, ALTRUI: 0,
           STORTO: 0}, r.get("finestre"))
    prova("...e nient'altro esce: ne' chi ha pubblicato ne' chi ha preso", ["finestre", "ok"],
          sorted(r))

    print("\n4) lo scambio di un'ora diventa attivo")
    t = int(time.time()) - 120
    prima = len(banco.DETTO)
    await attivo(UNA, t)
    prova("chi compra lo legge nella frase della garanzia, con la conseguenza", True,
          "⏱ Hai 1 ora per inviarli e toccare «Ho inviato gli euro»"
          in detto(PRENDE, "ha bloccato i sats in garanzia", prima))
    sc, sv = await scambio(PRENDE, UNA), await scambio(PUBBLICA, UNA)
    prova("IL TEMPO NON PARTE SENZA IL RECAPITO (19 nov 2026, Andrea: «nel momento in cui io "
          "ho indicato dove ricevere gli euro, non prima»): l'archivio da' i minuti, e il "
          "termine 0 a tutt'e due", (60, 0, 60, 0),
          (sc.get("minuti_pagare"), sc.get("paga_entro"), sv.get("minuti_pagare"),
           sv.get("paga_entro")))
    prova("...a chi compra ancora nessun promemoria (ne' quelli del tempo ne' i tre di "
          "sempre), e il nodo legge «non ancora»", ([], {UNA: None}),
          (attese(UNA, PRENDE), (await finestre({"ordini": [UNA]})).get("finestre")))
    v = scadenze(UNA, PUBBLICA, "sollecito_recapito")
    prova("a chi vende UN promemoria del recapito, a dieci minuti, che dice che il tempo di "
          "chi compra parte da lui", (1, True),
          (len(v), bool(v) and "Chi compra ha 1 ora per pagarti, da quando gli dici dove "
           "mandarti gli euro" in v[0][1]))
    recapito(UNA, t + 60)
    sc, sv = await scambio(PRENDE, UNA), await scambio(PUBBLICA, UNA)
    prova("COL RECAPITO il tempo parte: lo STESSO termine a tutt'e due, un'ora dal recapito, "
          "e il nodo riceve i secondi", (t + 60 + 3600, t + 60 + 3600, {UNA: 3600}),
          (sc.get("paga_entro"), sv.get("paga_entro"),
           (await finestre({"ordini": [UNA]})).get("finestre")))
    prova("a chi compra i promemoria col tempo che resta, dal recapito, e NON i tre di sempre",
          [("euro_tempo1", "sollecito_euro"), ("euro_tempo2", "sollecito_euro")],
          attese(UNA, PRENDE))
    sca = scadenze(UNA, PRENDE, "sollecito_euro")
    testi = [x[1] for x in sca]
    prova("...il primo dice i 40 minuti che restano, l'ULTIMO a dieci minuti dalla fine chiede "
          "«hai già mandato gli euro?» e dice che scade anche se ha pagato",
          [True, True, True, [t + 60 + 1200, t + 60 + 3000]],
          ["Hai ancora 40 minuti" in testi[0],
           testi[1].startswith("⏰ Mancano 10 minuti: hai già mandato gli euro?"),
           "anche se hai già pagato" in testi[1], [x[0] for x in sca]]
          if len(testi) == 2 else testi)

    # IL CONTO ALLA ROVESCIA NEL BOT (19 nov 2026, regole-sulla-card): nasce
    # insieme ai promemoria, con la stessa fine, e il giro lo manda
    con = banco.con_db()
    conto = con.execute("SELECT tg_id, fine, messaggio FROM p2p_conto_rovescia WHERE "
                        "chiave LIKE ?", (f"ln:{UNA}:%",)).fetchall()
    con.close()
    prova("col recapito nasce anche il conto alla rovescia di chi compra, con la stessa "
          "fine, non ancora mandato", [(PRENDE, t + 60 + 3600, 0)],
          [tuple(x) for x in conto])
    await SRV._giro_conto_p2p()
    con = banco.con_db()
    conto = con.execute("SELECT messaggio, detto, finito FROM p2p_conto_rovescia WHERE "
                        "chiave LIKE ?", (f"ln:{UNA}:%",)).fetchone()
    con.close()
    prova("...il giro lo manda (un id salvato) col tempo che resta, e corre ancora",
          (True, True, 0), (bool(conto and conto[0]), bool(conto) and "Tempo per pagare: "
                            "mancano" in conto[1], conto[2] if conto else -1))

    print("\n5) il tempo finisce col recapito detto presto (il nodo di ieri, che annulla)")
    # passa l'ora (la rotta vuole eventi di adesso: si sposta la cronaca)
    indietro(UNA, 3600)
    prima = len(banco.DETTO)
    r, journal = await posta(UNA, "expired", int(time.time()) - 5, "mostro", "payment-window")
    prova("mostrod racconta l'annullo del tempo per pagare, e la rotta lo prende", True,
          isinstance(r, dict) and r.get("ok") is True)
    prova("un «non completato» a chi compra, col dettaglio del tempo per pagare, e a chi "
          "vende niente", ([("mancato", "payment-window")], []),
          (esiti(PRENDE, UNA), esiti(PUBBLICA, UNA)))
    prova("...il journal dice a chi e perche'", True,
          f"a {PRENDE} si conta uno scambio non completato" in journal
          and "tempo per pagare finito" in journal)
    c = detto(PRENDE, "Il tempo per pagare è finito", prima)
    prova("a chi compra: il fatto, la strada se aveva pagato davvero, e la riga del conto",
          [True, True, True],
          [c.startswith("⏰ Il tempo per pagare è finito: lo scambio è annullato."),
           "scrivi subito all'assistenza dall'app" in c, "non completat" in c.split("\n\n")[-1]])
    vv = detto(PUBBLICA, "Il tempo per pagare è finito", prima)
    prova("a chi vende: i sats tornano, e se gli euro arrivano lo stesso si rimandano",
          [True, True, False],
          [vv.startswith("⏰ Il tempo per pagare è finito senza gli euro segnati"),
           "rimandali a chi li ha inviati" in vv, "non completat" in vv])
    prova("lo scambio chiuso non ha piu' promemoria", ([], []),
          (attese(UNA, PRENDE), attese(UNA, PUBBLICA)))

    print("\n6) il recapito detto tardi")
    t4 = int(time.time()) - 120
    await attivo(QUATTRO, t4)
    sq = await scambio(PRENDE, QUATTRO)
    prova("lo scambio di quattro ore, senza recapito: i minuti si', il termine non ancora",
          (240, 0), (sq.get("minuti_pagare"), sq.get("paga_entro")))
    prova("...e anche a quattro ore chi vende ha il promemoria del recapito a dieci "
          "minuti, al posto di quelli a una e a sei ore", 1,
          len(scadenze(QUATTRO, PUBBLICA, "sollecito_recapito")))
    indietro(QUATTRO, 2 * 3600 + 600)    # la garanzia e' di 2 ore e 10 minuti fa
    prova("due ore dopo l'attivo, senza recapito, il nodo legge ancora «non ancora»",
          {QUATTRO: None}, (await finestre({"ordini": [QUATTRO]})).get("finestre"))
    recapito(QUATTRO, int(time.time()))
    prova("...il recapito detto adesso: i secondi interi, dal recapito", {QUATTRO: 14400},
          (await finestre({"ordini": [QUATTRO]})).get("finestre"))
    indietro(QUATTRO, 960)
    prova("LA DOMANDA TARDIVA NON HA TEMPO: il nodo che chiede 16 minuti dopo il recapito (la "
          "porta era chiusa) riceve 0, e lo scambio non gli torna nel libro in mano",
          {QUATTRO: 0}, (await finestre({"ordini": [QUATTRO]})).get("finestre"))
    r, journal = await posta(QUATTRO, "expired", int(time.time()) - 5, "mostro",
                             "payment-window")
    prova("la rotta prende anche questo annullo", True, isinstance(r, dict) and r.get("ok") is True)
    prova("detto a piu' di meta' del tempo, il recapito non fa contare niente a nessuno",
          ([], []), (esiti(PRENDE, QUATTRO), esiti(PUBBLICA, QUATTRO)))
    prova("...e il journal dice perche'", True,
          "passata piu' di meta' del tempo per pagare" in journal)

    print("\n6b) LA 0014: il tempo finisce e l'ordine TORNA NEL LIBRO")
    t5 = int(time.time()) - 120
    await attivo(TORNA, t5)
    recapito(TORNA, t5 + 40)
    indietro(TORNA, 3600)
    prima = len(banco.DETTO)
    r, journal = await posta(TORNA, "expired", int(time.time()) - 5, "mostro",
                             "payment-window-republished")
    prova("il nodo racconta il ritorno nel libro, e la rotta lo prende", True,
          isinstance(r, dict) and r.get("ok") is True)
    prova("un «non completato» a chi compra, col dettaglio del ritorno nel libro, e a chi "
          "vende niente", ([("mancato", "payment-window-republished")], []),
          (esiti(PRENDE, TORNA), esiti(PUBBLICA, TORNA)))
    c = detto(PRENDE, "Il tempo per pagare è finito", prima)
    prova("a chi compra: scaduto e tornato nel libro, la strada se aveva pagato, la riga del "
          "conto", [True, True, True],
          [c.startswith("⏰ Il tempo per pagare è finito: lo scambio è scaduto e l'ordine è "
                        "tornato nel libro."),
           "scrivi subito all'assistenza dall'app" in c, "non completat" in c.split("\n\n")[-1]])
    vv = detto(PUBBLICA, "Il tempo per pagare è finito", prima)
    prova("a chi vende: l'ordine e' tornato nel libro, la garanzia si blocca alla presa dopo, "
          "gli euro tardivi si rimandano, e come ritirarlo",
          [True, True, True, True, False],
          [vv.startswith("⏰ Il tempo per pagare è finito senza gli euro segnati: il tuo "
                         "ordine è tornato nel libro."),
           "Alla prossima presa la garanzia si blocca di nuovo" in vv,
           "rimandali a chi li ha inviati" in vv, "apri l'ordine e ritiralo" in vv,
           "non completat" in vv])
    prova("lo scambio finito non ha piu' promemoria", ([], []),
          (attese(TORNA, PRENDE), attese(TORNA, PUBBLICA)))

    print("\n7) la leva spenta chiude anche la porta del nodo")
    SRV.P2P_TEMPO_PER_PAGARE = False
    prova("col segreto giusto, a leva spenta: 404 — nessuno scambio si annulla da solo",
          404, codice_di(await finestre({"ordini": [UNA]})))
    SRV.P2P_TEMPO_PER_PAGARE = True
    if SRV._TASK_EVENTI_P2P:
        await asyncio.gather(*list(SRV._TASK_EVENTI_P2P), return_exceptions=True)


def main():
    banco.avvio()
    banco.semina()
    semina_ordini()
    banco.SRV.P2P_EVENTI_SEGRETO = SEGRETO
    banco.SRV.P2P_RESPIRO_S = 0.2
    banco.SRV.P2P_RESPIRO_NOME_S = 0.1
    banco.SRV._p2p_per = lambda *a, **k: {"attivo": True}
    asyncio.run(giro_intero())
    print(f"\n{banco.PASSATE} passate, {banco.FALLITE} fallite")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
