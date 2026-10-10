# -*- coding: utf-8 -*-
"""
I SOLLECITI PER TUTTI I METODI, SUL SERVER VERO, COL COORDINATORE E
TELEGRAM DI CARTONE (10 ott 2026, cantiere «solleciti p2p»).

Il buco, dallo studio sul feedback: le regole a tempo coprivano solo la
prima mezz'ora dello scambio. A garanzia bloccata nessun orologio fino
alle 48 ore: chi compra poteva non mandare gli euro, chi vende non
liberare i sats, e fuori dal PayCode nessuno glielo ricordava.

Le regole approvate da Andrea: a chi deve mandare gli euro un promemoria
a un'ora, sei ore e un giorno dalla garanzia bloccata; a chi deve
liberare, dopo il «pagato», a un'ora, sei e venti — per TUTTI i metodi.
Mai «invia gli euro» a chi non ha ancora un recapito, mai dopo il
«pagato», la disputa o un annullo; niente a chi compra dove c'e' il
contanti di persona; il PayCode tiene le sue parole.

`prove.py` difende i giudici estratti e i testi (`prove_solleciti_p2p`).
Qui gira il SERVER VERO sul database usa-e-getta:
  • IL COORDINATORE DI CARTONE racconta lo scambio dalla rotta vera dei
    suoi eventi (`/api/p2p/evento`);
  • chi vende dichiara il recapito dalla rotta vera (`/api/p2p/recapito`);
  • TELEGRAM DI CARTONE: `notifica` segna a chi, cosa e con quale
    bottone, e passa dal ramo Telegram VERO (`_manda_telegram`, che in
    collaudo stampa invece di bussare);
  • le lancette del server vanno avanti (il suo `time`, e solo il suo) e
    gira il battito vero delle attese, `_giro_attese_p2p`.

  1. il bonifico: a un'ora senza recapito niente; detto il recapito, a
     sei ore il sollecito a chi compra, col bottone;
  2. il «pagato»: via i solleciti degli euro, e a chi vende un'ora dopo
     «controlla il conto»; il rilascio li ferma;
  3. una volta sola, anche dopo un «riavvio»;
  4. la disputa e la richiesta di annullo fermano tutto;
  5. il contanti di persona: a chi compra niente, a chi vende le sue
     parole;
  6. il PayCode: le sue parole a chi compra, e a chi vende tre
     solleciti, non sei;
  7. l'interruttore degli avvisi P2P spento: niente, e non risulta detto;
  8. (10 ott 2026, sera) chi vende non da' il recapito: a un'ora e a sei
     il sollecito e' SUO — «Indica dove ricevere gli euro» —, e a chi
     compra niente finche' il recapito non c'e'.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore.

USO:  python collaudo_solleciti_p2p.py
"""

import asyncio
import contextlib
import io
import re
import sys
import time

import collaudo_pagamento_p2p as banco

SEGRETO = "collaudo-segreto"
V, C = banco.VENDE, banco.COMPRA
DETTO = []          # (chi, testo, bottone) di ogni avviso
STAMPE = []         # le righe del ramo Telegram vero, simulato
H = 3600


class Orologio:
    """Il `time` del server con le lancette che si spostano: tutto il
    resto e' il modulo vero (strftime, localtime...)."""

    def __init__(self, vero):
        self.vero = vero
        self.avanti = 0

    def time(self):
        return self.vero.time() + self.avanti

    def fissa(self, ora):
        """Le lancette su QUELL'ora, adesso: da li' camminano col tempo
        vero (i millisecondi di un battito)."""
        self.avanti = ora - self.vero.time()

    def __getattr__(self, nome):
        return getattr(self.vero, nome)


OROLOGIO = Orologio(time)
TAG = re.compile(r"</?[bi]>")


def ordine(n):
    return f"50ec{n:04d}-c2c2-4a2b-9c3d-0000000000aa"


ULTIMO_TS = {}      # ordine -> l'ora dell'ultimo evento raccontato


async def evento(o, azione, attore, dettaglio="", **numeri):
    # DUE FATTI DELLO STESSO ORDINE STANNO IN FILA DI UN SECONDO, come li
    # tiene mostrod (`monotonic_order_event_timestamp`): senza, due eventi
    # del banco nello stesso secondo — la garanzia chiesta e la garanzia
    # pagata — pesano uguale, e lo stato dello scambio lo decide il caso
    ts = max(int(OROLOGIO.time()), ULTIMO_TS.get(o, 0) + 1)
    ULTIMO_TS[o] = ts
    b = banco.Busta(dict({"v": 1, "order": o, "action": azione,
                          "ts": ts, "buyer": banco.CHIAVE_COMPRA,
                          "seller": banco.CHIAVE_VENDE, "actor": attore,
                          "detail": dettaglio}, **numeri))
    b.headers = {"authorization": f"Bearer {SEGRETO}"}
    await banco.SRV.evento_p2p(b)
    await asyncio.sleep(0.3)
    if banco.SRV._TASK_EVENTI_P2P:
        await asyncio.gather(*list(banco.SRV._TASK_EVENTI_P2P), return_exceptions=True)


def libro(o, metodi='["SEPA"]'):
    con = banco.con_db()
    con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,"
                "preso_da,sats,euro,metodi) VALUES(?,?,?,'in-progress','sell',1,?,"
                "160000,'111,80 €',?)", (o, V, int(time.time()), C, metodi))
    con.commit()
    con.close()


def quando(o, momento):
    """L'ora, per il coordinatore, di quel momento su quell'ordine: e' da
    li' che si contano le ore di ogni battito. Il collaudo e' d'ORDINE e
    non di cronometro: le lancette si mettono a «momento + N» esatti."""
    con = banco.con_db()
    q = con.execute("SELECT MAX(quando) FROM p2p_momenti WHERE ordine=? AND momento=?",
                    (o, momento)).fetchone()[0]
    con.close()
    return int(q or 0)


async def scambio_attivo(o, metodi='["SEPA"]'):
    """Una vendita di chi vende, presa da chi compra: fattura data,
    garanzia chiesta e PAGATA adesso. Lo scambio e' attivo, e a chi
    compra manca solo il recapito."""
    OROLOGIO.avanti = 0
    libro(o, metodi)
    await evento(o, "taken", "buyer", "invoice-next")
    await evento(o, "buyer-invoice-requested", "mostro")
    await evento(o, "buyer-invoice-added", "buyer", "hold-next")
    await evento(o, "hold-invoice-requested", "mostro", "invoice")
    await evento(o, "hold-invoice-paid", "seller", "active")


async def recapito(o):
    """Chi vende dichiara il recapito dalla rotta vera. Dentro un giro
    async `banco.chiama` non si usa (apre un loop suo): la rotta si
    aspetta qui."""
    banco.come(V)
    r = await banco.SRV.recapito_p2p(banco.Busta({"ordine": o, "attivo": True}))
    await asyncio.sleep(0.05)
    return r


async def battito(ora):
    """Le lancette a quell'ora, e un battito vero delle attese. Torna
    (avvisi partiti, journal)."""
    OROLOGIO.fissa(ora)
    del DETTO[:]
    giornale = io.StringIO()
    # la leva accesa SOLO per il battito, come nel collaudo del promemoria:
    # il resto del server resta col P2P spento del config di cartone, e
    # non cerca relay
    vera = banco.SRV._p2p_leve
    banco.SRV._p2p_leve = lambda *a, **k: dict(vera(), attivo=True)
    try:
        with contextlib.redirect_stdout(giornale):
            await banco.SRV._giro_attese_p2p()
    finally:
        banco.SRV._p2p_leve = vera
    return list(DETTO), giornale.getvalue()


def in_attesa(o, fonte):
    con = banco.con_db()
    r = [(x["momento"], x["tg_id"]) for x in con.execute(
        "SELECT momento, tg_id FROM p2p_attese WHERE ordine=? AND fonte=? "
        "ORDER BY scade, id", (o, fonte))]
    con.close()
    return r


def timbri(o, come_):
    con = banco.con_db()
    n = con.execute("SELECT COUNT(*) FROM p2p_avvisi WHERE ordine=? AND momento LIKE ?",
                    (o, come_)).fetchone()[0]
    con.close()
    return n


async def giro():
    SRV = banco.SRV
    prova = banco.prova
    SRV.P2P_EVENTI_SEGRETO = SEGRETO
    SRV._p2p_per = lambda *a, **k: {"attivo": True}
    SRV.time = OROLOGIO
    telegram_vero = SRV._manda_telegram

    async def notifica_di_cartone(chi, testo, bottone=None):
        DETTO.append((chi, TAG.sub("", testo), bottone))
        riga = io.StringIO()
        with contextlib.redirect_stdout(riga):
            if bottone:
                await telegram_vero(chi, testo, bottone)
            else:
                await telegram_vero(chi, testo)
        STAMPE.append(riga.getvalue())
        return "cartone"
    SRV.notifica = notifica_di_cartone
    link = SRV.LINK_LIBRO_P2P
    EURO, RIL = SRV.SOLLECITO_EURO_TESTI, SRV.SOLLECITO_RILASCIO_TESTI

    def bottone(o):
        return ("⚡ Apri lo scambio", f"{link}?scambio={o}")

    print("\n1) il bonifico: la garanzia e' bloccata, tocca a chi compra")
    a = ordine(1)
    await scambio_attivo(a)
    G = quando(a, "garanzia_pagata")
    prova("la garanzia bloccata mette in attesa i tre solleciti degli euro, a chi compra",
          [("euro_sollecito1", C), ("euro_sollecito2", C), ("euro_sollecito3", C)],
          in_attesa(a, "sollecito_euro"))
    prova("...e a chi vende, per ora, niente", [], in_attesa(a, "sollecito"))
    detti, _ = await battito(G + H - 60)
    prova("a 59 minuti niente", [], detti)
    detti, giornale = await battito(G + H + 5)
    # (emendata la sera del 10 ott 2026, cantiere recapito-e-riga: a quel
    # battito adesso parte il sollecito del RECAPITO, a chi vende)
    prova("a un'ora, SENZA recapito, a chi compra non arriva niente: non ha dove "
          "mandare gli euro", [], [x for x in detti if x[0] == C])
    prova("...e a chi VENDE arriva il sollecito del recapito, col bottone dello scambio",
          [(V, SRV.SOLLECITO_RECAPITO_TESTI[1], bottone(a))], detti)
    prova("...e il journal dice perche'", True,
          f"Sollecito P2P: {a[:8]} «euro_sollecito1» a {C} non parte: chi vende non ha "
          "ancora detto dove ricevere gli euro" in giornale)
    prova("...e non risulta detto", 0, timbri(a, "euro_sollecito%"))
    OROLOGIO.fissa(G + 2 * H)
    await recapito(a)
    del STAMPE[:]
    detti, giornale = await battito(G + 6 * H + 5)
    prova("detto il recapito, a sei ore il sollecito arriva a chi compra, col bottone "
          "che apre QUELLO scambio", [(C, EURO[2], bottone(a))], detti)
    prova("...e il ramo Telegram vero lo manda col suo bottone", True,
          f"[bottone «⚡ Apri lo scambio» → {link}?scambio={a}]" in "".join(STAMPE))
    prova("...e il journal lo conta fra le attese partite", True,
          "📬 Attese P2P: avvisati 1" in giornale and "(sollecito_euro)" in giornale)

    print("\n2) il «pagato»: adesso tocca a chi vende")
    OROLOGIO.fissa(G + 7 * H)
    await evento(a, "fiat-sent", "buyer")
    F = quando(a, "fiat")
    prova("il «pagato» porta via subito il sollecito del giorno dopo", [],
          in_attesa(a, "sollecito_euro"))
    prova("...e mette in attesa i tre del rilascio a chi vende, anche col bonifico",
          [("fiat_sollecito1", V), ("fiat_sollecito2", V), ("fiat_sollecito3", V)],
          in_attesa(a, "sollecito"))
    detti, _ = await battito(F + H - 60)
    prova("a 59 minuti dal «pagato» niente", [], detti)
    detti, _ = await battito(F + H + 5)
    prova("a un'ora, a chi vende: controlla il conto, libera solo se gli euro ci sono — "
          "col suo bottone", [(V, RIL[1], bottone(a))], detti)
    OROLOGIO.fissa(F + 2 * H)
    await evento(a, "released", "seller", **banco.NUMERI)
    await evento(a, "success", "mostro", **banco.NUMERI)
    prova("il rilascio porta via gli altri due", [], in_attesa(a, "sollecito"))
    detti, giornale = await battito(F + 21 * H)
    prova("...e a venti ore non arriva niente", [], detti)
    prova("...ne' una riga di sollecito nel journal", False, "Sollecito P2P" in giornale)

    print("\n3) una volta sola")
    b = ordine(2)
    await scambio_attivo(b)
    G = quando(b, "garanzia_pagata")
    await recapito(b)
    detti, _ = await battito(G + H + 5)
    prova("a un'ora il primo, a chi compra", [(C, EURO[1], bottone(b))], detti)
    prova("un minuto dopo, niente", [], (await battito(G + H + 65))[0])
    prova("un battito nuovo sul database (quel che fa un server ripartito): niente",
          [], (await battito(G + 2 * H))[0])
    prova("il timbro dell'anti-doppione e' uno", 1, timbri(b, "euro_sollecito1"))
    detti, _ = await battito(G + 21 * H)
    prova("a ventun ore e' partito solo il secondo: il terzo aspetta il giorno intero",
          [(C, EURO[2], bottone(b))], detti)
    detti, _ = await battito(G + 24 * H + 5)
    prova("a un giorno, se gli euro non risultano ancora inviati, il terzo",
          [(C, EURO[3], bottone(b))], detti)

    print("\n4) la disputa e la richiesta di annullo")
    c = ordine(3)
    await scambio_attivo(c)
    G = quando(c, "garanzia_pagata")
    await recapito(c)
    OROLOGIO.fissa(G + 600)
    await evento(c, "dispute-opened", "seller")
    prova("aperta la disputa, i solleciti degli euro se ne vanno", [],
          in_attesa(c, "sollecito_euro"))
    detti, _ = await battito(G + H + 5)
    prova("...e a chi compra non arriva nessun «invia gli euro»", [],
          [d for d in detti if d[1] in EURO.values()])
    d = ordine(4)
    await scambio_attivo(d)
    G = quando(d, "garanzia_pagata")
    await recapito(d)
    OROLOGIO.fissa(G + 600)
    await evento(d, "cancel-requested", "buyer")
    detti, giornale = await battito(G + H + 5)
    prova("chi ha chiesto di annullare non si sollecita a pagare", [],
          [x for x in detti if x[1] in EURO.values()])
    prova("...e il journal dice in che stato e' lo scambio", True,
          f"Sollecito P2P: {d[:8]} «euro_sollecito1» a {C} non parte: lo scambio non "
          "aspetta gli euro" in giornale)
    e = ordine(5)
    await scambio_attivo(e)
    G = quando(e, "garanzia_pagata")
    OROLOGIO.fissa(G + 300)
    await evento(e, "fiat-sent", "buyer")
    F = quando(e, "fiat")
    OROLOGIO.fissa(F + 600)
    await evento(e, "dispute-opened", "buyer")
    prova("la disputa dopo il «pagato» porta via anche i solleciti di chi vende", [],
          in_attesa(e, "sollecito"))
    detti, _ = await battito(F + H + 5)
    prova("...e a chi vende non arriva nessun «controlla il conto»", [],
          [x for x in detti if x[1] in RIL.values()])

    print("\n5) il contanti di persona")
    f = ordine(6)
    await scambio_attivo(f, '["Contanti"]')
    G = quando(f, "garanzia_pagata")
    await recapito(f)
    prova("a chi compra nessun sollecito in attesa: ci si da' appuntamento", [],
          in_attesa(f, "sollecito_euro"))
    prova("...e a un giorno non gli e' arrivato niente", [],
          [x for x in (await battito(G + 24 * H + 5))[0] if x[0] == C])
    OROLOGIO.fissa(G + 25 * H)
    await evento(f, "fiat-sent", "buyer")
    F = quando(f, "fiat")
    detti, _ = await battito(F + H + 5)
    prova("dopo «Ho consegnato i contanti», a chi vende, le parole dei contanti",
          [(V, SRV.SOLLECITO_RILASCIO_CONTANTI_TESTI[1], bottone(f))], detti)

    print("\n6) il PayCode")
    g = ordine(7)
    await scambio_attivo(g, '["Contanti al tabacchino 111.80"]')
    G = quando(g, "garanzia_pagata")
    await recapito(g)
    detti, _ = await battito(G + H + 5)
    prova("a chi compra si dice di pagarlo al tabacchino",
          [(C, SRV.SOLLECITO_EURO_PAYCODE_TESTI[1], bottone(g))], detti)
    OROLOGIO.fissa(G + 2 * H)
    await evento(g, "fiat-sent", "buyer")
    F = quando(g, "fiat")
    prova("dopo il «pagato» a chi vende restano TRE solleciti, non sei",
          [("fiat_sollecito1", V), ("fiat_sollecito2", V), ("fiat_sollecito3", V)],
          in_attesa(g, "sollecito"))
    detti, _ = await battito(F + H + 5)
    prova("...e sono quelli del PayCode: «controlla su Amazon»",
          [(V, SRV.SOLLECITO_PAYCODE_TESTI[1], bottone(g))], detti)

    print("\n7) l'interruttore degli avvisi P2P spento")
    h = ordine(8)
    await scambio_attivo(h)
    G = quando(h, "garanzia_pagata")
    await recapito(h)
    con = banco.con_db()
    con.execute("UPDATE utenti SET avvisi_p2p=0 WHERE tg_id=?", (C,))
    con.commit()
    con.close()
    detti, giornale = await battito(G + H + 5)
    prova("chi li ha spenti non lo riceve", [], [x for x in detti if x[0] == C])
    prova("...e il journal lo dice", True,
          f"🔕 Attese P2P: {C} ha gli avvisi P2P SPENTI" in giornale)
    n = timbri(h, "euro_sollecito%")
    con = banco.con_db()
    con.execute("UPDATE utenti SET avvisi_p2p=1 WHERE tg_id=?", (C,))
    con.commit()
    con.close()
    prova("...e non risulta detto", 0, n)

    print("\n8) chi vende non da' il recapito")
    k = ordine(9)

    def di(o, detti):
        """I soli avvisi di QUELLO scambio: nei battiti di qui scadono anche
        le attese rimaste dai casi di prima (l'ora di partenza e' la stessa)."""
        return [x for x in detti if x[2] and x[2][1].endswith(o)]
    await scambio_attivo(k)
    G = quando(k, "garanzia_pagata")
    prova("la garanzia bloccata mette in attesa i due solleciti del recapito, a chi vende",
          [("sollecito_recapito1", V), ("sollecito_recapito2", V)],
          in_attesa(k, "sollecito_recapito"))
    detti, _ = await battito(G + H - 60)
    prova("a 59 minuti niente, a nessuno", [], di(k, detti))
    detti, _ = await battito(G + H + 5)
    prova("a un'ora: a chi vende «Indica dove ricevere gli euro», a chi compra niente",
          [(V, SRV.SOLLECITO_RECAPITO_TESTI[1], bottone(k))], di(k, detti))
    detti, _ = await battito(G + 5 * H)
    prova("a cinque ore niente: il secondo aspetta le sei", [], di(k, detti))
    detti, giornale = await battito(G + 6 * H + 5)
    prova("a sei ore, ancora senza recapito: a chi vende il secondo, a chi compra niente",
          [(V, SRV.SOLLECITO_RECAPITO_TESTI[2], bottone(k))], di(k, detti))
    prova("...e il journal dice perche' a chi compra no — il sollecito a chi vende NON "
          "vale come recapito detto", True,
          f"Sollecito P2P: {k[:8]} «euro_sollecito2» a {C} non parte: chi vende non ha "
          "ancora detto dove ricevere gli euro" in giornale)
    OROLOGIO.fissa(G + 7 * H)
    await recapito(k)
    detti, _ = await battito(G + 24 * H + 5)
    prova("dato il recapito a sette ore, il giorno dopo tocca a chi compra: il terzo "
          "degli euro, e a chi vende piu' niente", [(C, EURO[3], bottone(k))], di(k, detti))
    m = ordine(10)
    await scambio_attivo(m)
    G = quando(m, "garanzia_pagata")
    OROLOGIO.fissa(G + 1800)
    await recapito(m)
    prova("il recapito dato a mezz'ora porta via subito i solleciti di chi vende", [],
          in_attesa(m, "sollecito_recapito"))
    detti, giornale = await battito(G + H + 5)
    prova("...a un'ora a chi vende niente, e a chi compra il primo degli euro",
          [(C, EURO[1], bottone(m))], di(m, detti))
    prova("...e nessuna riga «non parte» nel journal per il recapito", False,
          "sollecito_recapito" in giornale)
    # chi ha davanti una richiesta di annullo non si sollecita: lo ferma il giudice
    n1 = ordine(11)
    await scambio_attivo(n1)
    G = quando(n1, "garanzia_pagata")
    OROLOGIO.fissa(G + 600)
    await evento(n1, "cancel-requested", "buyer")
    detti, giornale = await battito(G + H + 5)
    prova("con una richiesta di annullo davanti, a chi vende il recapito non si "
          "sollecita, e il journal dice in che stato e' lo scambio", [[], True],
          [di(n1, detti), f"Sollecito P2P: {n1[:8]} «sollecito_recapito1» a {V} non parte: "
                          "lo scambio non aspetta il recapito" in giornale])
    # il «pagato» porta via subito i solleciti del recapito
    n2 = ordine(12)
    await scambio_attivo(n2)
    G = quando(n2, "garanzia_pagata")
    OROLOGIO.fissa(G + 600)
    await evento(n2, "fiat-sent", "buyer")
    prova("se chi compra segna «pagato» lo stesso, i solleciti del recapito se ne vanno",
          [], in_attesa(n2, "sollecito_recapito"))
    # le parole: il contanti di persona e il PayCode
    for n, metodi, testi, nome in (
            (13, '["Contanti"]', SRV.SOLLECITO_RECAPITO_CONTANTI_TESTI,
             "col solo Contanti: «Indica dove e quando vedervi»"),
            (14, '["Contanti al tabacchino 111.80"]', SRV.SOLLECITO_RECAPITO_PAYCODE_TESTI,
             "col PayCode non partito: «mandaglielo da li'»")):
        o = ordine(n)
        await scambio_attivo(o, metodi)
        G = quando(o, "garanzia_pagata")
        detti, _ = await battito(G + H + 5)
        prova(f"a un'ora, {nome}", [(V, testi[1], bottone(o))], di(o, detti))
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
