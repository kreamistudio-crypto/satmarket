# -*- coding: utf-8 -*-
"""
IL PARACADUTE SUL SERVER VERO, COL PREZZO DI CARTONE E GLI EVENTI FINTI
DEL COORDINATORE (13 ott 2026, cantiere paracadute, decisione di Andrea
con Alan).

Il caso: chi pubblica un ordine lo fa perche' a QUEL prezzo gli sta
bene, ma un ordine resta nel libro per giorni. Pubblicando puo' aprire
il paracadute — «se BTC sale o scende piu' del 5% da adesso,
annullamelo» — e se il prezzo si muove oltre PRIMA che qualcuno lo
prenda, l'ordine esce dal libro da solo, senza penalita', e lui riceve
un avviso col tasto per ripubblicarlo. `prove.py` difende i giudici
estratti (`prove_paracadute_p2p`); qui girano le ROTTE VERE —
`/api/p2p/ordini` (l'intestazione), `/api/p2p/paracadute`,
`/api/p2p/facce`, `/api/p2p/posso-prendere`, `/api/p2p/evento` col
bearer di mostrod, «dimentica il profilo» — e il GIRO VERO dell'orologio
(`_giro_paracadute_p2p`), su un database usa-e-getta. Il prezzo e' la
cache del cambio, scritta dal collaudo: nessuna chiamata a nessuno.

  1. A LEVA SPENTA e' come ieri: la rotta dice `attivo: false`,
     l'intestazione non scrive niente, i volti non ne portano;
  2. l'intestazione: la soglia e il prezzo di partenza (quello del
     SERVER), solo sugli ordini pubblicati da chi dichiara, mai su un
     ordine Barattozon, e la prima resta;
  3. UN DUMP: −6% alla prima lettura non apre; alla seconda di fila
     l'ordine del 5% esce dal libro, «posso prendere?» lo ferma, e chi
     l'aveva pubblicato riceve l'avviso col bottone — quello del 10% no;
  4. UN PUMP, sull'acquisto di chi e' nato su Nostr (id negativo);
  5. LA FONTE MUTA: senza prezzo, o con la stessa lettura che invecchia,
     non si apre niente; quando torna, si';
  6. L'ORDINE PRESO UN ATTIMO PRIMA DELLA SOGLIA non si tocca; tornato
     nel libro e' di nuovo armato;
  7. LA PRESA ARRIVATA DOPO L'APERTURA (da un'altra app): la riga sotto
     l'avviso della presa, e lasciarla scadere non costa niente;
  8. L'EVENTO DELLA PRESA ARRIVATO TARDI: l'apertura si disfa;
  8-bis. L'ORDINE CHE NON E' PIU' NEL LIBRO (13 ott 2026, sera, richiesta
     di Andrea): annullato a mano o scaduto, col libro ancora indietro,
     non si apre e non avvisa — vale la cronaca di mostrod; e col libro
     NON LETTO in quel battito non si giudica nessuno;
  9. «dimentica il profilo» porta via i paracadute.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram (le notifiche finiscono in
una lista), niente relay, niente coordinatore, niente fonte del prezzo.

USO:  python collaudo_paracadute.py
"""

import asyncio
import json
import re
import sys
import time

import collaudo_pagamento_p2p as banco

SEGRETO = "collaudo-segreto"
PUBBLICA, PRENDE, PASSA = banco.VENDE, banco.COMPRA, banco.ESTRANEO
NATIVA = -7301234567890123                      # chi e' nato su Nostr: un id negativo
CHIAVE_NATIVA = "c3" * 32
A = "9a7a0000-0a0a-4a2b-9c3d-00000000000a"      # vendita di 111, soglia 5: il dump
B = "9a7a0000-0b0b-4a2b-9c3d-00000000000b"      # vendita di 111, soglia 10: resta
BZ = "9a7a0000-0c0c-4a2b-9c3d-00000000000c"     # vendita Barattozon di 111: mai
ALTRUI = "9a7a0000-0d0d-4a2b-9c3d-00000000000d"  # vendita di 333: non e' di chi dichiara
N1 = "9a7a0000-0e0e-4a2b-9c3d-00000000000e"     # acquisto della nativa, soglia 10: il pump
M = "9a7a0000-0f0f-4a2b-9c3d-00000000000f"      # vendita di 111, soglia 5: la fonte muta
C = "9a7a0000-1010-4a2b-9c3d-000000000010"      # vendita di 111, soglia 5: presa un attimo prima
D = "9a7a0000-1111-4a2b-9c3d-000000000011"      # vendita di 111, soglia 5: presa dopo l'apertura
E = "9a7a0000-1212-4a2b-9c3d-000000000012"      # vendita di 111, soglia 5: la presa arrivata tardi
F = "9a7a0000-1313-4a2b-9c3d-000000000013"      # vendita di 111, soglia 5: annullata a mano
G = "9a7a0000-1414-4a2b-9c3d-000000000014"      # vendita di 111, soglia 5: scaduta nel libro
H = "9a7a0000-1515-4a2b-9c3d-000000000015"      # vendita di 111, soglia 5: il libro non letto
# (17 nov 2026, cantiere paracadute-su-giu) le due soglie, una per verso
GIU = "9a7a0000-1616-4a2b-9c3d-000000000016"    # vendita di 111, solo «se scende 5%»
SU = "9a7a0000-1717-4a2b-9c3d-000000000017"     # vendita di 111, solo «se sale 10%»
_TAG = re.compile(r"</?[bi]>")
BOTTONI = []                                    # (destinatario, bottone) di ogni notifica


def info(prende=1800, pubblica=10800, limite=2):
    """Il 38385 di cartone: i soli tag che servono."""
    return {"kind": 38385, "tags": [["d", "x"], ["expiration_seconds", str(prende)],
                                    ["maker_expiration_seconds", str(pubblica)],
                                    ["maker_timeout_limit", str(limite)]]}


def busta(ordine, azione, ts, attore, dettaglio, buyer=banco.CHIAVE_COMPRA,
          seller=banco.CHIAVE_VENDE):
    b = banco.Busta({"v": 1, "order": ordine, "action": azione, "ts": ts, "buyer": buyer,
                     "seller": seller, "actor": attore, "detail": dettaglio})
    b.headers = {"authorization": f"Bearer {SEGRETO}"}
    return b


async def posta(b):
    """Il POST di mostrod alla rotta vera, e i suoi avvisi lasciati finire."""
    try:
        r = await banco.SRV.evento_p2p(b)
    except Exception as e:
        return getattr(e, "status_code", type(e).__name__)
    if banco.SRV._TASK_EVENTI_P2P:
        await asyncio.gather(*list(banco.SRV._TASK_EVENTI_P2P), return_exceptions=True)
    return json.loads(r.body)


async def chiama(fn, corpo=None):
    d = corpo if corpo is not None else {}

    async def leggi(_req):
        if not isinstance(d, dict):
            raise banco.SRV.HTTPException(400, "Richiesta malformata")
        return d
    banco.SRV.leggi_json = leggi
    try:
        r = await fn(banco.Busta(d))
    except Exception as e:
        return (getattr(e, "status_code", type(e).__name__),
                str(getattr(e, "detail", e)))
    return json.loads(r.body) if hasattr(r, "body") else r


async def intesta(chi, mappa):
    """«Questi ordini li ho pubblicati io», col paracadute: la rotta vera."""
    banco.come(chi)
    return await chiama(banco.SRV.registra_ordini_p2p,
                        {"ordini": sorted(mappa), "pubblicati": True, "paracadute": mappa})


def miei(chi):
    banco.come(chi)
    return json.loads(banco.SRV.miei_paracadute_p2p().body)


async def posso(chi, ordini):
    banco.come(chi)
    return await chiama(banco.SRV.posso_prendere_p2p, {"ordini": ordini})


async def facce(chi, ordini):
    banco.come(chi)
    return await chiama(banco.SRV.facce_ordini_p2p, {"ordini": ordini})


def prezzo(euro, eta=0):
    """Il cambio di cartone: quel che la fonte «ha appena detto». Ogni
    chiamata e' una LETTURA NUOVA, un secondo dopo la precedente — due
    giri dell'orologio sullo stesso numero non sarebbero due letture."""
    prezzo.n += 1
    banco.SRV._cambio_cache["valori"]["eur"] = float(euro)
    banco.SRV._cambio_cache["quando"] = time.time() - eta + prezzo.n if euro else 0.0


prezzo.n = 0


async def giro(euro=None, eta=0):
    """Un giro VERO dell'orologio del paracadute, dopo una lettura nuova
    del prezzo (o sulla stessa di prima, con `euro` None). Torna i
    destinatari avvisati in questo giro."""
    if euro is not None:
        prezzo(euro, eta)
    prima = len(BOTTONI)
    await banco.SRV._giro_paracadute_p2p()
    return [chi for chi, _ in BOTTONI[prima:]]


def detto(a_chi, frammento):
    """L'ultima notifica a quella persona che contiene il frammento, senza tag."""
    for chi, testo in reversed(banco.DETTO):
        t = _TAG.sub("", testo)
        if chi == a_chi and frammento in t:
            return t
    return ""


def riga(ordine):
    con = banco.con_db()
    r = con.execute("SELECT soglia, partenza, oltre, aperto, arrivo, superato "
                    "FROM p2p_paracadute WHERE ordine=?", (ordine,)).fetchone()
    con.close()
    return tuple(r) if r else None


def esiti(tg, ordine):
    con = banco.con_db()
    r = sorted(tuple(x) for x in con.execute(
        "SELECT esito, dettaglio FROM p2p_esiti WHERE tg_id=? AND ordine=?", (tg, ordine)))
    con.close()
    return r


def scusata(ordine):
    con = banco.con_db()
    r = con.execute("SELECT pausa_presa FROM p2p_scambi WHERE ordine=?", (ordine,)).fetchone()
    con.close()
    return int(r[0] or 0) if r else None


def semina_ordini():
    con = banco.con_db()
    adesso = int(time.time())
    for tg, nome, chiave in ((NATIVA, "Nata su Nostr", CHIAVE_NATIVA),):
        con.execute("INSERT OR IGNORE INTO utenti(tg_id,nome,negozio,registrato,ln_address) "
                    "VALUES(?,?,?,1,'')", (tg, nome, "nostrina"))
        con.execute("INSERT OR REPLACE INTO chiavi_p2p(pubkey, tg_id, creato) VALUES(?,?,?)",
                    (chiave, tg, adesso))
    for ordine, chi, lato, metodi in (
            (A, PUBBLICA, "sell", ["SEPA"]), (B, PUBBLICA, "sell", ["SEPA"]),
            (BZ, PUBBLICA, "sell", ["Contanti al tabacchino 23.47"]),
            (ALTRUI, PASSA, "sell", ["SEPA"]), (N1, NATIVA, "buy", ["SEPA"]),
            (M, PUBBLICA, "sell", ["SEPA"]), (C, PUBBLICA, "sell", ["SEPA"]),
            (D, PUBBLICA, "sell", ["SEPA"]), (E, PUBBLICA, "sell", ["SEPA"]),
            (F, PUBBLICA, "sell", ["SEPA"]), (G, PUBBLICA, "sell", ["SEPA"]),
            (H, PUBBLICA, "sell", ["SEPA"]), (GIU, PUBBLICA, "sell", ["SEPA"]),
            (SU, PUBBLICA, "sell", ["SEPA"])):
        con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,sats,euro,"
                    "metodi) VALUES(?,?,?,'pending',?,1,50000,'50,00 €',?)",
                    (ordine, chi, adesso, lato, json.dumps(metodi)))
    con.commit()
    con.close()


async def giro_intero():
    SRV = banco.SRV
    prova = banco.prova
    vera = SRV.notifica

    async def spia(chi, testo, *a, **k):
        BOTTONI.append((chi, a[0] if a else k.get("bottone")))
        return await vera(chi, testo, *a, **k)
    SRV.notifica = spia

    print("\n1) a leva spenta e' come ieri")
    SRV.P2P_PARACADUTE = False
    prezzo(100000)
    prova("la rotta dice `attivo: false` e niente altro", {"attivo": False}, miei(PUBBLICA))
    r = await intesta(PUBBLICA, {A: 5})
    prova("l'intestazione passa, ma del paracadute non scrive niente", (True, None),
          (r.get("ok"), riga(A)))
    prova("...e i volti non ne portano", [], (await facce(PRENDE, [A, B]))["paracadute"])
    prova("...e l'orologio non guarda: nessun avviso", [], await giro(50000))

    print("\n2) l'intestazione, a leva accesa")
    SRV.P2P_PARACADUTE = True
    prezzo(100000)
    await intesta(PUBBLICA, {A: 5, B: 10, BZ: 5, ALTRUI: 5, M: 5, C: 5, D: 5, E: 5})
    prova("la soglia e la PARTENZA al cambio del server; l'ordine Barattozon e quello di un "
          "altro non entrano",
          ((5, 100000.0, 0, 0, 0.0, 0), (10, 100000.0, 0, 0, 0.0, 0), None, None),
          (riga(A), riga(B), riga(BZ), riga(ALTRUI)))
    prezzo(80000)
    await intesta(PUBBLICA, {A: 20})
    prova("LA PRIMA RESTA: rifatta con un'altra soglia e un altro prezzo non si sposta",
          (5, 100000.0, 0, 0, 0.0, 0), riga(A))
    m = miei(PUBBLICA)
    prova("chi ha pubblicato li legge dalla sua rotta: la soglia e il prezzo di partenza, "
          "`no-store` — e non quelli degli altri",
          (True, {"soglia": 5, "su": 5, "giu": 5, "partenza": 100000.0, "aperto": 0,
                  "arrivo": 0.0},
           {"soglia": 10, "su": 10, "giu": 10, "partenza": 100000.0, "aperto": 0,
            "arrivo": 0.0}, False),
          (m["attivo"], m["ordini"].get(A), m["ordini"].get(B), ALTRUI in m["ordini"]))
    prova("...e chi non ne ha riceve la mappa vuota", {"attivo": True, "ordini": {}},
          miei(PRENDE))

    print("\n3) un dump: −6% due volte di fila")
    prova("alla PRIMA lettura oltre soglia non succede niente: nessun avviso, il libro e' "
          "quello di prima", ([], [], 1),
          (await giro(94000), (await facce(PRENDE, [A, B]))["paracadute"], riga(A)[2]))
    prova("lo STESSO numero riletto dall'orologio non conta due volte", ([], 1),
          (await giro(), riga(A)[2]))
    avvisati = await giro(94000)
    prova("alla SECONDA lettura di fila il paracadute del 5% si apre: quattro ordini di chi "
          "pubblica (A, M, C, D, E hanno la stessa soglia) — e quello del 10% no",
          (True, 0, True), (set(avvisati) == {PUBBLICA}, riga(B)[3], riga(A)[3] > 0))
    prova("...la riga porta il prezzo d'arrivo", 94000.0, riga(A)[4])
    f = await facce(PRENDE, [A, B, ALTRUI])
    prova("l'ordine esce coi volti fra quelli col paracadute aperto; gli altri no",
          [A], f["paracadute"])
    p = (await posso(PASSA, [A, B]))["ordini"]
    prova("«posso prendere?» lo ferma col motivo `paracadute`, e quello del 10% si prende",
          ({"ok": False, "motivo": "paracadute", "soglia": 0}, True), (p[A], p[B]["ok"]))
    prova("...ma a chi l'ha pubblicato il SUO ordine non dice «paracadute»", True,
          (await posso(PUBBLICA, [A]))["ordini"][A]["motivo"] != "paracadute")
    prova("L'AVVISO: la frase, i due prezzi, lo scarto, nessuna penalita'",
          "🪂 Il paracadute si è aperto: BTC è passato da 100.000 € a 94.000 € (−6,0%), il tuo "
          "ordine di vendita da 50,00 € è stato annullato. Nessuna penalità.\nApri Barattolo "
          "per toglierlo anche dalle altre app collegate.",
          detto(PUBBLICA, "Il paracadute si è aperto"))
    bott = [b for chi, b in BOTTONI if chi == PUBBLICA and b]
    prova("...col bottone «🔁 Ripubblica al prezzo nuovo», che porta al suo ordine",
          (True, True),
          (("🔁 Ripubblica al prezzo nuovo", SRV.URL_PUBBLICO + "/p2p?scambio=" + A) in bott,
           all(SRV._startapp_da_link(u).startswith("scambio_") for _, u in bott)))
    prova("...e lo legge aperto fra i suoi, con l'ora e il prezzo",
          (True, 94000.0), (miei(PUBBLICA)["ordini"][A]["aperto"] > 0,
                            miei(PUBBLICA)["ordini"][A]["arrivo"]))
    n = len(BOTTONI)
    await giro(90000)
    await giro(90000)
    prova("un paracadute aperto non si riapre e non si riavvisa — ma a −10% netti quello "
          "del 10% resta chiuso (non e' «piu' del 10%»)", ([], 0),
          ([chi for chi, b in BOTTONI[n:]], riga(B)[3]))

    print("\n4) un pump, sull'acquisto di chi e' nato su Nostr")
    prezzo(90000)
    r = await intesta(NATIVA, {N1: 10})
    prova("l'id negativo intesta come tutti, e parte dal prezzo di adesso",
          (True, (10, 90000.0, 0, 0, 0.0, 0)), (r.get("ok"), riga(N1)))
    prova("+12%: alla prima lettura niente, alla seconda si apre e l'avviso va a LEI",
          ([], [NATIVA]), (await giro(100800), await giro(100800)))
    prova("...«in salita» e «di acquisto»", True,
          "da 90.000 € a 100.800 € (+12,0%), il tuo ordine di acquisto da 50,00 €"
          in detto(NATIVA, "Il paracadute si è aperto"))
    prova("...e da li' il suo ordine non si prende piu'", "paracadute",
          (await posso(PASSA, [N1]))["ordini"][N1]["motivo"])

    print("\n5) la fonte del prezzo muta")
    con = banco.con_db()
    con.execute("UPDATE p2p_paracadute SET aperto=0, arrivo=0, oltre=0, lettura=0, "
                "partenza=100000 WHERE ordine=?", (M,))
    con.commit()
    con.close()
    prova("una lettura oltre soglia: il conto va a uno", ([], 1),
          (await giro(93000), riga(M)[2]))
    muti = []
    for _ in range(5):
        muti += await giro(0)
    # ...letture VECCHIE ma ognuna piu' nuova della precedente (da quindici
    # minuti fa a sette), E PIU' NUOVE dell'ultima contata — che si mette
    # a un'ora fa, come dopo un'ora di fonte muta: cosi' a fermarle puo'
    # essere SOLO la freschezza, non «la stessa lettura non si conta due
    # volte» (l'ha chiesto la tortura: tolta la freschezza, qui era verde)
    con = banco.con_db()
    con.execute("UPDATE p2p_paracadute SET lettura=? WHERE ordine=?",
                (int(time.time()) - 3600, M))
    con.commit()
    con.close()
    for k in range(5):
        muti += await giro(93000, eta=900 - 120 * k)
    prova("FONTE MUTA: cinque giri senza prezzo e cinque con letture vecchie di piu' di "
          "cinque minuti (ognuna piu' nuova dell'altra) non aprono niente, e il conto "
          "resta a uno",
          ([], (5, 100000.0, 1, 0, 0.0, 0)), (muti, riga(M)))
    prova("...quando la fonte torna, la seconda lettura oltre soglia apre",
          ([PUBBLICA], True), (await giro(93000), riga(M)[3] > 0))

    print("\n6) l'ordine preso un attimo prima della soglia")
    con = banco.con_db()
    con.execute("UPDATE p2p_paracadute SET aperto=0, arrivo=0, oltre=0, lettura=0 "
                "WHERE ordine IN (?,?,?)", (C, D, E))
    con.commit()
    con.close()
    SRV._P2P_FOTO["info"] = info()
    SRV.P2P_TEMPO_DI_CHI_PUBBLICA = True
    prova("una lettura oltre soglia: il conto di C va a uno", 1,
          (await giro(93000), riga(C)[2])[1])
    del banco.DETTO[:]
    t = int(time.time())
    await posta(busta(C, "taken", t, "buyer", "invoice-next"))
    prova("la presa arriva: l'avviso a chi ha pubblicato e' quello di sempre, senza righe "
          "del paracadute", (True, False),
          (bool(detto(PUBBLICA, "Il tuo ordine è stato preso")),
           "🪂" in detto(PUBBLICA, "Il tuo ordine è stato preso")))
    n = len(BOTTONI)
    con = banco.con_db()
    con.execute("UPDATE p2p_paracadute SET oltre=0 WHERE ordine IN (?,?)", (D, E))
    con.commit()
    con.close()
    await giro(93000)
    await giro(80000)
    await giro(80000)
    prova("...e da li' il paracadute di C NON SI APRE PIU', anche se il libro lo da' ancora "
          "`pending` e il prezzo crolla: uno scambio cominciato va avanti come sempre",
          (0, 0, False), (riga(C)[3], riga(C)[2], C in (await facce(PRENDE, [C]))["paracadute"]))
    prova("...e la presa non e' scusata da niente: e' una presa normale", 0, scusata(C))
    await posta(busta(C, "expired", t + 5, "mostro", "taker-timeout"))
    con = banco.con_db()
    con.execute("UPDATE p2p_ordini SET stato='pending' WHERE ordine=?", (C,))
    con.commit()
    con.close()
    primo = await giro(93000)
    prova("TORNATO NEL LIBRO e' di nuovo armato col prezzo della pubblicazione: servono di "
          "nuovo due letture, e alla seconda si apre",
          (False, True, 100000.0),
          (riga(C)[3] > 0 if PUBBLICA in primo else False,
           (await giro(93000), riga(C)[3] > 0)[1], riga(C)[1]))

    print("\n7) la presa arrivata dopo l'apertura, da un'altra app")
    prova("D e' aperto (il crollo di prima l'ha aperto)", True, riga(D)[3] > 0)
    del banco.DETTO[:]
    td = riga(D)[3] + 2
    await posta(busta(D, "taken", td, "buyer", "invoice-next"))
    prova("l'avviso della presa porta a chi ha PUBBLICATO la riga del paracadute; a chi ha "
          "preso no", (True, False),
          (detto(PUBBLICA, "Il tuo ordine è stato preso").endswith(
              "🪂 Il paracadute di quest'ordine era già aperto: puoi annullare senza "
              "penalità."),
           any("🪂" in x for chi, x in banco.DETTO if chi == PRENDE)))
    prova("...la presa e' scusata come una presa in pausa, e il paracadute resta aperto",
          (1, True), (scusata(D), riga(D)[3] > 0))
    await posta(busta(D, "buyer-invoice-requested", td, "mostro", ""))
    await posta(busta(D, "buyer-invoice-added", td + 1, "buyer", "hold-next"))
    await posta(busta(D, "hold-invoice-requested", td + 1, "mostro", "invoice"))
    await posta(busta(D, "expired", td + 2, "mostro", "maker-republished"))
    prova("...e lasciarla scadere NON COSTA NIENTE a chi ha pubblicato: nessun esito",
          [], esiti(PUBBLICA, D))

    print("\n8) l'evento della presa arrivato tardi")
    aperto_e = riga(E)[3]
    prova("E e' aperto", True, aperto_e > 0)
    del banco.DETTO[:]
    await posta(busta(E, "taken", aperto_e - 3, "buyer", "invoice-next"))
    prova("per mostrod la presa era di tre secondi PRIMA: l'apertura si DISFA, e la riga "
          "ricorda quando", (0, aperto_e, 1), (riga(E)[3], riga(E)[5], scusata(E)))
    prova("...a chi ha pubblicato si dice che il paracadute non vale e lo scambio va avanti",
          True, detto(PUBBLICA, "Il tuo ordine è stato preso").endswith(
              "🪂 Il paracadute non vale: l'ordine era stato preso un attimo prima che si "
              "aprisse. Lo scambio va avanti come sempre."))
    prova("...e lui non lo trova piu' fra gli aperti: il suo telefono non annulla niente",
          (0, False), (miei(PUBBLICA)["ordini"][E]["aperto"],
                       E in (await facce(PRENDE, [E]))["paracadute"]))

    print("\n8-bis) l'ordine che non e' piu' nel libro")
    prezzo(100000)
    await intesta(PUBBLICA, {F: 5, G: 5, H: 5})
    prova("i tre nascono col paracadute chiuso, al prezzo di adesso",
          [(5, 100000.0, 0, 0)] * 3, [riga(o)[:4] for o in (F, G, H)])
    adesso = int(time.time())
    await posta(busta(F, "canceled", adesso, "seller", ""))        # annullato a mano
    await posta(busta(G, "expired", adesso, "mostro", "book"))     # scaduto nel libro
    con = banco.con_db()
    stati = [con.execute("SELECT stato FROM p2p_ordini WHERE ordine=?", (o,)).fetchone()[0]
             for o in (F, G, H)]
    con.close()
    prova("(il libro e' INDIETRO: per `p2p_ordini` sono ancora tutti e tre `pending`)",
          ["pending"] * 3, stati)
    prima = len(BOTTONI)
    SRV._P2P_CONTO["libro"] = "ABBANDONATA"
    await giro(70000)
    await giro(69000)
    await giro(68000)
    prova("COL LIBRO NON LETTO in quel battito, a −30% per tre giri, non si giudica "
          "nessuno: nemmeno H, che nel libro c'e'", [(0, 0)] * 3,
          [riga(o)[2:4] for o in (F, G, H)])
    SRV._P2P_CONTO["libro"] = "3 ordini guardati (0 mai visti), 0 eventi [relay.di.cartone 0]"
    await giro(67000)
    await giro(66000)
    await giro(65000)
    SRV._P2P_CONTO["libro"] = ""
    prova("A LIBRO LETTO: H si apre alla seconda lettura; l'ordine ANNULLATO A MANO e "
          "quello SCADUTO no, nemmeno alla terza — li ha gia' raccontati mostrod",
          (True, 0, 0, 0, 0),
          (riga(H)[3] > 0, riga(F)[3], riga(G)[3], riga(F)[2], riga(G)[2]))
    bottoni = [str(b) for _, b in BOTTONI[prima:]]
    prova("...e l'avviso col bottone parte per H e per lui solo: nessun «🪂 Il paracadute "
          "si è aperto» su un ordine che non e' piu' nel libro", (1, 0, 0),
          (sum(H in b for b in bottoni), sum(F in b for b in bottoni),
           sum(G in b for b in bottoni)))
    f = await facce(PRENDE, [F, G, H])
    prova("...e fra gli ordini «col paracadute aperto» c'e' solo H", [H], f["paracadute"])

    print("\n8-ter) due soglie, una per verso (17 nov 2026)")
    prezzo(100000)
    await intesta(PUBBLICA, {GIU: {"su": 0, "giu": 5}, SU: {"su": 10, "giu": 0}})
    con = banco.con_db()
    versi = [tuple(con.execute("SELECT soglia, su, giu, partenza FROM p2p_paracadute "
                               "WHERE ordine=?", (o,)).fetchone()) for o in (GIU, SU)]
    con.close()
    prova("dalla rotta vera le due soglie si scrivono una per verso, al prezzo di adesso",
          [(5, 0, 5, 100000.0), (10, 10, 0, 100000.0)], versi)
    m = miei(PUBBLICA)["ordini"]
    prova("...e chi le ha pubblicate le rilegge dalla sua rotta",
          [(0, 5), (10, 0)], [(m[GIU]["su"], m[GIU]["giu"]), (m[SU]["su"], m[SU]["giu"])])
    await giro(112000)
    await giro(112000)
    prova("BTC +12% per due giri: si apre «se sale 10%», NON «se scende 5%» — che resta nel "
          "libro e si prende", (True, 0, [SU], True),
          (riga(SU)[3] > 0, riga(GIU)[3],
           [o for o in (await facce(PRENDE, [GIU, SU]))["paracadute"]],
           (await posso(PRENDE, [GIU]))["ordini"][GIU]["ok"]))
    prova("...e l'avviso dice la salita", True,
          "(+12,0%)" in detto(PUBBLICA, "Il paracadute si è aperto"))
    await giro(94000)
    await giro(94000)
    prova("BTC −6% per due giri: ora si apre «se scende 5%»", (True, [GIU, SU]),
          (riga(GIU)[3] > 0, sorted((await facce(PRENDE, [GIU, SU]))["paracadute"])))
    prova("...e l'avviso dice la discesa", True,
          "(−6,0%)" in detto(PUBBLICA, "Il paracadute si è aperto"))

    print("\n9) dimentica il profilo")
    prova("prima ci sono", True, len(miei(PUBBLICA)["ordini"]) > 0)
    banco.come(PUBBLICA)
    SRV.dimentica_chiavi_p2p()
    con = banco.con_db()
    restano = con.execute("SELECT COUNT(*) FROM p2p_paracadute WHERE tg_id=?",
                          (PUBBLICA,)).fetchone()[0]
    altrui = con.execute("SELECT COUNT(*) FROM p2p_paracadute WHERE tg_id=?",
                         (NATIVA,)).fetchone()[0]
    con.close()
    prova("«dimentica il profilo» porta via i suoi paracadute, e solo i suoi", (0, 1),
          (restano, altrui))
    SRV.notifica = vera
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
