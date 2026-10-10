# -*- coding: utf-8 -*-
"""
I MALUS DOPO LA GARANZIA, SUL SERVER VERO, COL COORDINATORE E TELEGRAM DI
CARTONE (10 ott 2026, cantiere malus-p2p).

Dallo studio sul feedback: le regole della reputazione guardavano solo il
primo gesto di chi prende. A garanzia bloccata non c'era nessuna
conseguenza — chi teneva fermi i sats altrui per giorni, o perdeva una
disputa, restava pulito, e se i sats andavano a chi compra lo scambio gli
valeva perfino «completato».

Le quattro regole approvate da Andrea:
  a) il moderatore, decidendo, puo' segnare la COLPA a chi perde: a lui
     una «disputa persa» (sul profilo per 90 giorni) e niente
     «completato»;
  b) la garanzia arrivata a SCADENZA col recapito detto e senza «pagato»
     si conta come non completato a chi compra;
  c) la SCUSA del tentativo vale una volta ogni 30 giorni;
  d) chi ha gia' due scambi con gli EURO IN SOSPESO da piu' di un'ora non
     ne prende un altro.

`prove.py` difende i giudici estratti e il client (`prove_malus_p2p`).
Qui gira il SERVER VERO sul database usa-e-getta, dalle ROTTE vere:
`/api/p2p/evento` (il coordinatore di cartone, col bearer),
`/api/p2p/recapito`, `/api/p2p/tentativo`, `/api/p2p/posso-prendere`, e
quelle del moderatore (`/api/p2p/moderazione/chiave`, `/prendi`,
`/decisione`) con la disputa nata dall'evento vero. Le lancette del
server vanno avanti (il suo `time`, e solo il suo).

  1. la disputa persa: la spunta, il registro, la chiusura raccontata
     dal coordinatore, il concluso che non vale a chi ha perso;
  2. la stessa disputa SENZA spunta: nessun marchio, completato a tutti;
     la spunta che non e' un `true`, e chi vende che libera da se';
  3. la scusa del tentativo: la prima scusa, la seconda nel mese no;
  4. la garanzia arrivata a scadenza: contata a chi compra, e detta;
  5. gli euro in sospeso: al secondo la presa si spegne, col «pagato»
     si riaccende.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore.

USO:  python collaudo_malus_p2p.py
"""

import asyncio
import json
import re
import sys
import time

import collaudo_pagamento_p2p as banco

SEGRETO = "collaudo-segreto"
V, C, MOD = banco.VENDE, banco.COMPRA, 999
KM = "c0" * 32                       # la chiave PUBBLICA del moderatore
DETTO = []                           # (chi, testo senza tag) di ogni avviso
GIORNALE = []                        # le righe stampate dal server
H, G = 3600, 86400
TAG = re.compile(r"</?[bi]>")


class Orologio:
    """Il `time` del server con le lancette che si spostano: tutto il
    resto e' il modulo vero (strftime, localtime...)."""

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
    return f"3a105000-{n:04d}-4a2b-9c3d-0000000000bb"


def libro(o, metodi='["SEPA"]'):
    con = banco.con_db()
    con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,"
                "preso_da,sats,euro,metodi) VALUES(?,?,?,'in-progress','sell',1,?,"
                "15000,'10,00 €',?)", (o, V, int(time.time()), C, metodi))
    con.commit()
    con.close()


async def evento(o, azione, attore, dettaglio="", **numeri):
    """Il POST del coordinatore alla rotta vera, e il suo invio. Due fatti
    dello stesso ordine stanno in fila di un secondo, come li tiene
    mostrod (`monotonic_order_event_timestamp`)."""
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


async def chiama(fn, corpo=None, come=None):
    """Una rotta dell'app, da dentro il giro (`banco.chiama` apre un loop
    suo): la risposta come dizionario, o il rifiuto come (codice, frase)."""
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


async def attivo(o, metodi='["SEPA"]', recapito=True):
    """Una vendita presa da chi compra, fino alla garanzia bloccata; e chi
    vende dice dove ricevere gli euro."""
    libro(o, metodi)
    await evento(o, "taken", "buyer", "invoice-next")
    await evento(o, "buyer-invoice-added", "buyer", "hold-next")
    await evento(o, "hold-invoice-requested", "mostro", "invoice")
    await evento(o, "hold-invoice-paid", "seller", "active")
    if recapito:
        await chiama(banco.SRV.recapito_p2p, {"ordine": o, "attivo": True}, V)


async def in_disputa(o, n):
    """Fino alla disputa aperta da chi compra dopo il «pagato», presa dal
    moderatore dalle sue rotte."""
    await attivo(o)
    await evento(o, "fiat-sent", "buyer")
    await evento(o, "dispute-opened", "buyer")
    await chiama(banco.SRV.disputa_dichiarata_p2p,
                 {"ordine": o, "disputa": f"d15b0000-aaaa-4bbb-8ccc-0000000000{n:02x}"}, C)
    await chiama(banco.SRV.moderazione_chiave_p2p, {"chiave": KM}, MOD)
    await chiama(banco.SRV.moderazione_prendi_p2p, {"ordine": o, "chiave": KM}, MOD)
    return await chiama(banco.SRV.moderazione_prendi_p2p,
                        {"ordine": o, "chiave": KM, "fatto": True}, MOD)


def esiti(tg, o=None):
    con = banco.con_db()
    r = [tuple(x) for x in con.execute(
        "SELECT esito, ruolo, dettaglio FROM p2p_esiti WHERE tg_id=? "
        + ("AND ordine=? " if o else "") + "ORDER BY quando, esito",
        (tg, o) if o else (tg,))]
    con.close()
    return r


def registro(o):
    con = banco.con_db()
    r = [(x["gesto"], x["tg_id"], x["esito"]) for x in con.execute(
        "SELECT gesto, tg_id, esito FROM p2p_dispute_registro WHERE ordine=? ORDER BY id", (o,))]
    con.close()
    return r


def a(chi):
    return [t for c, t in DETTO if c == chi]


async def giro():
    SRV = banco.SRV
    prova = banco.prova
    SRV.P2P_EVENTI_SEGRETO = SEGRETO
    SRV._p2p_per = lambda *x, **k: {"attivo": True}
    SRV.ADMIN_IDS = [MOD]
    SRV.time = OROLOGIO
    ADESSO = int(time.time())
    stampa_vera = print

    async def notifica_di_cartone(chi, testo, *x, **k):
        DETTO.append((chi, TAG.sub("", testo)))
        return "cartone"
    SRV.notifica = notifica_di_cartone
    SRV.print = lambda *x, **k: GIORNALE.append(" ".join(str(y) for y in x))
    motivo = "Il bonifico risulta arrivato: lo dice la ricevuta della banca."

    stampa_vera("\n1) la disputa persa, con la colpa segnata dal moderatore")
    OROLOGIO.fissa(ADESSO - 5 * G)
    o = ordine(1)
    presa = await in_disputa(o, 1)
    prova("la disputa nasce dall'evento vero e il moderatore la prende dalle sue rotte",
          True, isinstance(presa, dict) and presa.get("ok") is True)
    r = await chiama(SRV.moderazione_decisione_p2p,
                     {"ordine": o, "esito": "compratore", "motivo": motivo, "conferma": True,
                      "chiave": KM, "colpa": True}, MOD)
    prova("la decisione con la spunta: la rotta risponde chi perde",
          (True, "compratore", "venditore"),
          (r.get("ok"), r.get("esito"), r.get("colpa")) if isinstance(r, dict) else r)
    prova("...a registro la decisione, e accanto la colpa di chi perde",
          [("decisione", MOD, "compratore"), ("colpa", MOD, "venditore")], registro(o)[-2:])
    prova("...ma finche' il coordinatore non la esegue, a chi vende non si scrive niente",
          [], esiti(V, o))
    del GIORNALE[:]
    await evento(o, "released", "mostro", "admin", **banco.NUMERI)
    prova("il coordinatore racconta la chiusura del moderatore: «disputa persa» a chi vende",
          ([("disputa_persa", "vende", "admin")], []), (esiti(V, o), esiti(C, o)))
    prova("...il journal lo dice, e non suona nessun allarme", [True, False],
          [any(f"a {V} si segna una disputa persa" in x for x in GIORNALE),
           any("SENZA DECISIONE A REGISTRO" in x for x in GIORNALE)])
    prova("...a chi ha perso il messaggio della chiusura porta in coda la riga, con la "
          "data del blocco; a chi ha vinto no", [True, False],
          [any(x.startswith("⚖️ Un moderatore ha chiuso la disputa: i sats vanno a chi "
                            "compra.\n\nIl moderatore ha segnato la disputa come persa per "
                            "te: comparirà sul tuo profilo per 90 giorni. Fino al ")
               and x.endswith(" non puoi prendere gli ordini con filtro (1+, 3+, 5+); gli "
                              "altri sì.") for x in a(V)),
           any("disputa come persa" in x for x in a(C))])
    del GIORNALE[:]
    await evento(o, "success", "mostro", "", **banco.NUMERI)
    prova("al concluso: «completato» a chi compra, NON a chi ha perso la disputa",
          ([("completato", "compra", "")], [("disputa_persa", "vende", "admin")]),
          (esiti(C, o), esiti(V, o)))
    prova("...e il journal dice perche'", True,
          any(f"a {V} non vale come completato" in x for x in GIORNALE))
    nv = await chiama(SRV.posso_prendere_p2p, {"ordini": []}, V)
    nc = await chiama(SRV.posso_prendere_p2p, {"ordini": []}, C)
    prova("i numeri dalla rotta: una disputa persa e zero completati a chi vende; a chi "
          "compra un completato e nessuna disputa", [(1, 0), (0, 1)],
          [(nv["dispute"], nv["completati"]), (nc["dispute"], nc["completati"])])
    con = banco.con_db()
    marchi = SRV._marchi_dispute_p2p(con, [V, C], int(OROLOGIO.time()))
    con.close()
    prova("...e il marchio per i volti esce a chi vende soltanto", {V: 1}, marchi)
    filtrato = ordine(20)
    con = banco.con_db()
    con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,sats,euro,"
                "metodi,min_completati) VALUES(?,?,?,'pending','buy',1,15000,'10,00 €',"
                "'[\"SEPA\"]',1)", (filtrato, C, ADESSO))
    for k in range(3):                   # coi completati a posto: a fermarlo e' la disputa
        con.execute("INSERT INTO p2p_esiti(tg_id, ordine, giro, esito, ruolo, quando) "
                    "VALUES(?,?,1,'completato','vende',?)", (V, f"vecchio-{k}", ADESSO - 200 * G))
    con.commit()
    con.close()
    r = await chiama(SRV.posso_prendere_p2p, {"ordini": [filtrato]}, V)
    prova("...e la disputa persa lo tiene fuori dagli ordini con filtro: «dispute», con "
          "la data che il riquadro del veto scrive",
          ({"ok": False, "motivo": "dispute", "soglia": 1}, True),
          (r["ordini"][filtrato], r["fino_dispute"] > int(OROLOGIO.time()) + 89 * G))

    stampa_vera("\n2) la stessa disputa SENZA la spunta")
    o = ordine(2)
    await in_disputa(o, 2)
    r = await chiama(SRV.moderazione_decisione_p2p,
                     {"ordine": o, "esito": "compratore", "motivo": motivo, "conferma": True,
                      "chiave": KM}, MOD)
    prova("senza spunta la decisione non porta colpa, e a registro non c'e'",
          ["", []], [r.get("colpa", "") if isinstance(r, dict) else r,
                     [x for x in registro(o) if x[0] == "colpa"]])
    await evento(o, "released", "mostro", "admin", **banco.NUMERI)
    await evento(o, "success", "mostro", "", **banco.NUMERI)
    prova("...nessuna disputa persa: lo scambio vale «completato» a tutti e due",
          ([("completato", "vende", "")], [("completato", "compra", "")]),
          (esiti(V, o), esiti(C, o)))

    stampa_vera("\n2b) la spunta che non e' un true, e chi vende che libera da se'")
    o = ordine(10)
    await in_disputa(o, 3)
    corpo = {"ordine": o, "esito": "compratore", "motivo": motivo, "conferma": True,
             "chiave": KM}
    r = await chiama(SRV.moderazione_decisione_p2p, dict(corpo, colpa="true"), MOD)
    prova("una spunta che non e' un `true` letterale non segna niente",
          ["", []], [r.get("colpa", "") if isinstance(r, dict) else r,
                     [x for x in registro(o) if x[0] == "colpa"]])
    await chiama(SRV.moderazione_decisione_p2p, dict(corpo, colpa=True), MOD)
    await evento(o, "released", "seller", "", **banco.NUMERI)
    await evento(o, "success", "mostro", "", **banco.NUMERI)
    prova("la colpa e' a registro, ma chi vende libera da se' prima che il moderatore firmi: "
          "nessuna disputa persa, completato a tutti e due",
          ([("completato", "vende", "")], [("completato", "compra", "")]),
          (esiti(V, o), esiti(C, o)))

    stampa_vera("\n3) la scusa del tentativo, una ogni 30 giorni")
    OROLOGIO.fissa(ADESSO - 3 * G)

    async def timeout(n):
        o = ordine(n)
        libro(o)
        await evento(o, "taken", "buyer", "invoice-next")
        await evento(o, "buyer-invoice-requested", "mostro")
        t = await chiama(SRV.tentativo_p2p, {"ordine": o, "gesto": "fattura_rifiutata",
                                             "motivo": "invalid-invoice"}, C)
        del DETTO[:]
        await evento(o, "expired", "mostro", "taker-timeout")
        return o, t

    o, t = await timeout(3)
    prova("il tentativo si dichiara dalla rotta vera", True,
          isinstance(t, dict) and t.get("ok") is True)
    prova("il primo timeout con un tentativo: scusato, e la scusa resta scritta",
          [("scusato", "compra", "taker-timeout")], esiti(C, o))
    prova("...a chi ha preso il messaggio lo dice: stavolta non conta, vale una volta ogni "
          "30 giorni", True, any(x.endswith("\n\n" + SRV.P2P_RIGA_SCUSA) for x in a(C)))
    OROLOGIO.fissa(ADESSO - 2 * G)
    o, _ = await timeout(4)
    prova("il giorno dopo, un altro timeout con un tentativo: la scusa e' gia' usata, si conta",
          [("mancato", "compra", "taker-timeout+tentativo")], esiti(C, o))
    prova("...e il messaggio spiega perche', poi la riga del conto", True,
          any(SRV.P2P_RIGA_SCUSA_USATA + "Questo conta come scambio non completato." in x
              for x in a(C)))

    stampa_vera("\n4) la garanzia arrivata a scadenza")
    OROLOGIO.fissa(ADESSO - 95 * H)
    o = ordine(5)
    await attivo(o)
    OROLOGIO.fissa(ADESSO - H)
    del DETTO[:]
    del GIORNALE[:]
    await evento(o, "canceled", "mostro", "escrow-deadline")
    prova("col recapito detto e senza «pagato»: un non completato a chi compra, e solo a lui",
          ([("mancato", "compra", "escrow-deadline")], []), (esiti(C, o), esiti(V, o)))
    prova("...a chi compra il messaggio dice il fatto e il conto", True,
          any(x.startswith("⏰ La garanzia è arrivata a scadenza: lo scambio è annullato.")
              and "\n\nGli euro non risultano inviati. Questo conta come scambio non "
                  "completato" in x for x in a(C)))
    prova("...a chi vende i sats tornati, e nessun conto", [True, False],
          [any("sono tornati a te" in x for x in a(V)),
           any("non completato" in x for x in a(V))])
    o = ordine(6)
    OROLOGIO.fissa(ADESSO - 95 * H)
    await attivo(o, recapito=False)
    OROLOGIO.fissa(ADESSO - H + 60)
    del GIORNALE[:]
    await evento(o, "canceled", "mostro", "escrow-deadline")
    prova("senza il recapito di chi vende non si conta a nessuno, e il journal dice perche'",
          [[], [], True],
          [esiti(C, o), esiti(V, o),
           any("non aveva detto dove ricevere gli euro" in x for x in GIORNALE)])

    stampa_vera("\n5) gli euro in sospeso")
    libero = ordine(9)
    con = banco.con_db()
    con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,sats,euro,"
                "metodi) VALUES(?,?,?,'pending','sell',1,15000,'10,00 €','[\"SEPA\"]')",
                (libero, V, ADESSO))
    con.commit()
    con.close()
    OROLOGIO.fissa(ADESSO - 3 * H)
    p, q = ordine(7), ordine(8)
    await attivo(p)
    await attivo(q)
    OROLOGIO.fissa(ADESSO - 1800)
    r = await chiama(SRV.posso_prendere_p2p, {"ordini": [libero]}, C)
    prova("due scambi con la garanzia bloccata da piu' di un'ora e gli euro non segnati: la "
          "presa e' spenta, «sospesi»", ({"ok": False, "motivo": "sospesi", "soglia": 0}, 2, 2),
          (r["ordini"][libero], r["euro_sospesi"], r["limite_sospesi"]))
    r = await chiama(SRV.posso_prendere_p2p, {"ordini": [libero]}, V)
    prova("...a chi vende, che sta aspettando, la porta resta aperta", (True, 0),
          (r["ordini"][libero]["ok"], r["euro_sospesi"]))
    await evento(p, "fiat-sent", "buyer")
    r = await chiama(SRV.posso_prendere_p2p, {"ordini": [libero]}, C)
    prova("segnato il «pagato» su uno dei due, si riprende", (True, 1),
          (r["ordini"][libero]["ok"], r["euro_sospesi"]))
    OROLOGIO.fissa(ADESSO - 600)
    await attivo(ordine(11))
    # un minuto dopo: gli eventi del banco stanno in fila di un secondo, e
    # senza questo passo la garanzia starebbe nel FUTURO del server
    OROLOGIO.fissa(ADESSO - 540)
    r = await chiama(SRV.posso_prendere_p2p, {"ordini": [libero]}, C)
    prova("uno scambio con la garanzia appena bloccata non conta ancora fra i sospesi: "
          "c'e' un'ora di respiro", (True, 1),
          (r["ordini"][libero]["ok"], r["euro_sospesi"]))
    SRV.time = time
    del SRV.print


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
