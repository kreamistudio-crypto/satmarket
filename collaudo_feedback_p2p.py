# -*- coding: utf-8 -*-
"""
IL FEEDBACK RIFINITO, SUL SERVER VERO, COL COORDINATORE E TELEGRAM DI
CARTONE (10 ott 2026, cantiere feedback-p2p).

Il pacchetto C dello studio sul feedback P2P. La recensione a fine
scambio c'era gia'; mancavano tre cose, approvate da Andrea:
  a) UN promemoria, un giorno dopo, a chi puo' ancora recensire e non
     l'ha fatto;
  b) il numero degli scambi COMPLETATI accanto alle stelline (lo vedeva
     solo l'interessato);
  c) la recensione anche dopo una disputa CHIUSA DA UN MODERATORE coi
     sats tornati a chi vende — fin qui si recensiva solo lo scambio
     andato in porto.

`prove.py` difende i giudici estratti e il client (`prove_feedback_p2p`).
Qui gira il SERVER VERO sul database usa-e-getta, dalle ROTTE vere:
`/api/p2p/evento` (il coordinatore di cartone, col bearer),
`/api/p2p/recensibile`, `/api/p2p/recensione`, `/api/p2p/facce`,
`/api/p2p/controparte`, il negozio, e quelle del moderatore; il battito
vero delle attese (`_giro_attese_p2p`) con le lancette che avanzano.

  1. lo scambio concluso: il promemoria a un giorno, a tutti e due, col
     bottone; chi ha gia' recensito non lo riceve;
  2. gli scambi completati: sui volti del libro, nella card dell'altra
     parte, nel negozio;
  3. la disputa chiusa da un moderatore coi sats a chi vende: la
     recensione si puo' lasciare (e conta nella media), il promemoria
     parte;
  4. l'annullo d'accordo: niente recensione, niente promemoria.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore.

USO:  python collaudo_feedback_p2p.py
"""

import asyncio
import contextlib
import io
import json
import re
import sys
import time

import collaudo_pagamento_p2p as banco

SEGRETO = "collaudo-segreto"
V, C, MOD = banco.VENDE, banco.COMPRA, 999
KM = "c0" * 32
DETTO = []                           # (chi, testo senza tag, bottone)
H, G = 3600, 86400
TAG = re.compile(r"</?[bi]>")


class Orologio:
    """Il `time` del server con le lancette che si spostano."""

    def __init__(self, vero):
        self.vero = vero
        self.avanti = 0

    def time(self):
        return self.vero.time() + self.avanti

    def fissa(self, ora):
        self.avanti = ora - self.vero.time()

    def __getattr__(self, nome):
        return getattr(self.vero, nome)


OROLOGIO = Orologio(time)
ULTIMO_TS = {}


def ordine(n):
    return f"fe3d0000-{n:04d}-4a2b-9c3d-0000000000cc"


def libro(o):
    con = banco.con_db()
    con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,"
                "preso_da,sats,euro,metodi) VALUES(?,?,?,'in-progress','sell',1,?,"
                "15000,'10,00 €','[\"SEPA\"]')", (o, V, int(time.time()), C))
    con.commit()
    con.close()


async def evento(o, azione, attore, dettaglio="", **numeri):
    """Il POST del coordinatore alla rotta vera. Due fatti dello stesso
    ordine stanno in fila di un secondo, come li tiene mostrod."""
    ts = max(int(OROLOGIO.time()), ULTIMO_TS.get(o, 0) + 1)
    ULTIMO_TS[o] = ts
    b = banco.Busta(dict({"v": 1, "order": o, "action": azione, "ts": ts,
                          "buyer": banco.CHIAVE_COMPRA, "seller": banco.CHIAVE_VENDE,
                          "actor": attore, "detail": dettaglio}, **numeri))
    b.headers = {"authorization": f"Bearer {SEGRETO}"}
    await banco.SRV.evento_p2p(b)
    await asyncio.sleep(0.3)
    if banco.SRV._TASK_EVENTI_P2P:
        await asyncio.gather(*list(banco.SRV._TASK_EVENTI_P2P), return_exceptions=True)
    return ts


async def chiama(fn, corpo=None, come=None):
    """Una rotta dell'app, da dentro il giro: la risposta come dizionario,
    o il rifiuto come (codice, frase)."""
    if come is not None:
        banco.come(come)
    d = corpo if corpo is not None else {}

    async def leggi(_req):
        return d
    banco.SRV.leggi_json = leggi
    try:
        r = await fn(banco.Busta(d))
    except Exception as e:
        return (getattr(e, "status_code", type(e).__name__), str(getattr(e, "detail", e)))
    return json.loads(r.body) if hasattr(r, "body") else r


async def fino_al_pagato(o):
    libro(o)
    await evento(o, "taken", "buyer", "invoice-next")
    await evento(o, "buyer-invoice-added", "buyer", "hold-next")
    await evento(o, "hold-invoice-requested", "mostro", "invoice")
    await evento(o, "hold-invoice-paid", "seller", "active")
    await evento(o, "fiat-sent", "buyer")


async def concluso(o):
    await fino_al_pagato(o)
    await evento(o, "released", "seller", "", **banco.NUMERI)
    return await evento(o, "success", "mostro", "", **banco.NUMERI)


async def battito(ora):
    """Le lancette a quell'ora, e un battito vero delle attese: gli avvisi
    del promemoria della recensione, e il journal."""
    OROLOGIO.fissa(ora)
    del DETTO[:]
    giornale = io.StringIO()
    vera = banco.SRV._p2p_leve
    banco.SRV._p2p_leve = lambda *a, **k: dict(vera(), attivo=True)
    try:
        with contextlib.redirect_stdout(giornale):
            await banco.SRV._giro_attese_p2p()
    finally:
        banco.SRV._p2p_leve = vera
    return sorted(x for x in DETTO if x[1].startswith("⭐ Com'è andata")), giornale.getvalue()


def in_attesa(o):
    con = banco.con_db()
    r = [(x["momento"], x["tg_id"]) for x in con.execute(
        "SELECT momento, tg_id FROM p2p_attese WHERE ordine=? AND fonte='recensione' "
        "ORDER BY tg_id", (o,))]
    con.close()
    return r


def recensioni(o):
    con = banco.con_db()
    r = [(x["da_tg_id"], x["per_tg_id"], x["voto"]) for x in con.execute(
        "SELECT da_tg_id, per_tg_id, voto FROM feedback WHERE scambio=? ORDER BY da_tg_id", (o,))]
    con.close()
    return r


def media(tg):
    con = banco.con_db()
    r = con.execute("SELECT rating, n_feedback FROM utenti WHERE tg_id=?", (tg,)).fetchone()
    con.close()
    return (float(r["rating"] or 0), int(r["n_feedback"] or 0))


async def giro():
    SRV = banco.SRV
    prova = banco.prova
    SRV.P2P_EVENTI_SEGRETO = SEGRETO
    SRV._p2p_per = lambda *x, **k: {"attivo": True}
    SRV.ADMIN_IDS = [MOD]
    SRV.time = OROLOGIO
    ADESSO = int(time.time())
    link = SRV.LINK_LIBRO_P2P

    async def notifica_di_cartone(chi, testo, bottone=None, *x, **k):
        DETTO.append((chi, TAG.sub("", testo), bottone))
        return "cartone"
    SRV.notifica = notifica_di_cartone

    def promemoria(chi, o):
        """Quel che deve arrivare a `chi`: la frase vera, col nome
        dell'altra persona come la pagina lo mostra, e il bottone."""
        con = banco.con_db()
        nome = SRV._nome_altro_p2p(con, o, chi, int(OROLOGIO.time()))
        con.close()
        return (chi, TAG.sub("", SRV._testo_promemoria_recensione_p2p(nome)),
                ("⚡ Apri lo scambio", f"{link}?scambio={o}"))

    print("\n1) lo scambio concluso, e il promemoria un giorno dopo")
    OROLOGIO.fissa(ADESSO - 5 * G)
    a = ordine(1)
    t = await concluso(a)
    prova("a scambio concluso c'e' un promemoria in attesa per ciascuna delle due parti",
          [("recensione_promemoria", V), ("recensione_promemoria", C)], in_attesa(a))
    detti, _ = await battito(t + 24 * H - 60)
    prova("a un'ora dalla fine del giorno, niente", [], detti)
    detti, giornale = await battito(t + 24 * H + 5)
    prova("a un giorno, a tutti e due: la frase col nome dell'altro e il bottone dello scambio",
          sorted([promemoria(V, a), promemoria(C, a)]), detti)
    prova("...e il journal lo conta fra le attese partite", True,
          "📬 Attese P2P: avvisati 2" in giornale and "(recensione)" in giornale)
    prova("una volta sola: un'ora dopo, niente", [], (await battito(t + 25 * H))[0])

    b = ordine(2)
    OROLOGIO.fissa(ADESSO - 3 * G)
    t = await concluso(b)
    r = await chiama(SRV.recensione_p2p, {"ordine": b, "voto": 5, "commento": "Preciso"}, C)
    prova("chi compra lascia la recensione dalla rotta vera", [(C, V, 5)],
          recensioni(b) if isinstance(r, dict) else r)
    detti, giornale = await battito(t + 24 * H + 5)
    prova("un giorno dopo il promemoria arriva solo a chi NON l'ha lasciata",
          [promemoria(V, b)], detti)
    prova("...e il journal dice perche' all'altro no", True,
          f"Promemoria recensione P2P: {b[:8]} a {C} non parte: la recensione l'ha gia' "
          "lasciata" in giornale)

    print("\n2) gli scambi completati accanto al nome")
    con = banco.con_db()
    fatti = SRV._completati_p2p(con, [V, C, banco.ESTRANEO])
    con.close()
    prova("due scambi conclusi: due completati a testa, e niente a chi non c'entra",
          {V: 2, C: 2}, fatti)
    c = ordine(3)
    con = banco.con_db()
    con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,sats,euro,"
                "metodi) VALUES(?,?,?,'pending','sell',1,15000,'10,00 €','[\"SEPA\"]')",
                (c, V, ADESSO))
    con.commit()
    con.close()
    facce = (await chiama(SRV.facce_ordini_p2p, {"ordini": [c]}, C))["facce"]
    prova("il volto di chi ha pubblicato, sul libro, porta i suoi completati", 2,
          facce.get(c, {}).get("completati"))
    altra = (await chiama(SRV.controparte_p2p, {"ordini": [a]}, C))["controparti"]
    prova("...la card dell'altra parte, nella pagina dello scambio, pure", 2,
          altra.get(a, {}).get("completati"))
    prova("...e il negozio; chi non ha mai scambiato non ha il numero", [2, 0],
          [SRV.negozio(f"neg{V}{V}")["venditore"]["scambi_completati"],
           SRV.negozio(f"neg{banco.ESTRANEO}{banco.ESTRANEO}")["venditore"]["scambi_completati"]])

    print("\n3) la disputa chiusa da un moderatore, coi sats tornati a chi vende")
    OROLOGIO.fissa(ADESSO - 2 * G)
    d = ordine(4)
    await fino_al_pagato(d)
    await evento(d, "dispute-opened", "seller")
    await chiama(SRV.disputa_dichiarata_p2p,
                 {"ordine": d, "disputa": "d15b0000-aaaa-4bbb-8ccc-0000000000f1"}, V)
    await chiama(SRV.moderazione_chiave_p2p, {"chiave": KM}, MOD)
    await chiama(SRV.moderazione_prendi_p2p, {"ordine": d, "chiave": KM}, MOD)
    await chiama(SRV.moderazione_prendi_p2p, {"ordine": d, "chiave": KM, "fatto": True}, MOD)
    r = await chiama(SRV.recensibile_p2p, {"ordine": d}, V)
    prova("a disputa aperta la recensione non c'e' ancora", (False, "non_conclusa"),
          (r.get("si"), r.get("motivo")) if isinstance(r, dict) else r)
    await chiama(SRV.moderazione_decisione_p2p,
                 {"ordine": d, "esito": "venditore", "conferma": True, "chiave": KM,
                  "motivo": "Nessun bonifico è arrivato: lo dice l'estratto conto."}, MOD)
    t = await evento(d, "canceled", "mostro", "admin")
    r = [await chiama(SRV.recensibile_p2p, {"ordine": d}, chi) for chi in (V, C)]
    prova("chiusa dal moderatore: la recensione si puo' lasciare, da tutte e due le parti",
          [True, True], [x.get("si") if isinstance(x, dict) else x for x in r])
    prima = media(C)
    r = await chiama(SRV.recensione_p2p, {"ordine": d, "voto": 1,
                                          "commento": "Non ha mai pagato"}, V)
    prova("chi vende recensisce chi non ha pagato: la rotta la accetta, e conta nella media",
          [[(V, C, 1)], True],
          [recensioni(d) if isinstance(r, dict) else r,
           media(C)[1] == prima[1] + 1 and media(C)[0] < 5])
    prova("...due promemoria in attesa anche qui", 2, len(in_attesa(d)))
    detti, _ = await battito(t + 24 * H + 5)
    prova("...e un giorno dopo arriva solo a chi non ha ancora recensito",
          [promemoria(C, d)], detti)

    print("\n4) l'annullo d'accordo non apre niente")
    OROLOGIO.fissa(ADESSO - G)
    e = ordine(5)
    libro(e)
    await evento(e, "taken", "buyer", "invoice-next")
    await evento(e, "buyer-invoice-added", "buyer", "hold-next")
    await evento(e, "hold-invoice-requested", "mostro", "invoice")
    await evento(e, "hold-invoice-paid", "seller", "active")
    await evento(e, "canceled", "mostro", "cooperative")
    r = await chiama(SRV.recensibile_p2p, {"ordine": e}, V)
    prova("uno scambio annullato d'accordo non si recensisce", (False, "non_conclusa"),
          (r.get("si"), r.get("motivo")) if isinstance(r, dict) else r)
    r = await chiama(SRV.recensione_p2p, {"ordine": e, "voto": 1, "commento": ""}, V)
    prova("...e la rotta che scrive la rifiuta", 400, r[0] if isinstance(r, tuple) else r)
    prova("...e non c'e' nessun promemoria in attesa", [], in_attesa(e))
    SRV.time = time


def main():
    banco.avvio()
    banco.semina()
    banco.SRV.P2P_RESPIRO_S = 1
    banco.SRV.P2P_RESPIRO_NOME_S = 1
    asyncio.run(giro())
    print(f"\n{banco.PASSATE} passate, {banco.FALLITE} fallite")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
