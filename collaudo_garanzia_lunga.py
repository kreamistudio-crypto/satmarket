# -*- coding: utf-8 -*-
"""
LA GARANZIA LUNGA, SUL SERVER VERO, CON L'OROLOGIO SPOSTATO (7 ott 2026).

Le regole di Andrea: dall'ora in cui il coordinatore ha detto «garanzia
pagata», a 48 ore un avviso a ciascuna delle due parti (col testo del
punto in cui stanno), a 72 e a 88 ore un avviso ai moderatori — sempre,
anche con l'interruttore degli avvisi P2P spento —, massimo due per
scambio; niente doppioni, nemmeno dopo un riavvio, perche' il timbro sta
nel database e si scrive PRIMA dell'invio; una riga nel journal per ogni
avviso mandato.

`prove.py` difende i testi e il giudice estratto (`prove_garanzia_lunga`).
Qui gira il SERVER VERO: lo scambio nasce dalla rotta vera degli eventi
del coordinatore (`/api/p2p/evento`), poi le lancette del server vanno
avanti (il suo `time`, e solo il suo) e gira il battito vero,
`_giro_garanzie_p2p`, sul database usa-e-getta:

  1. a 47 ore niente;
  2. a 48 ore un avviso a chi vende e uno a chi compra, e il journal;
  3. ripassando, niente; un «riavvio» (il giudice non tiene niente in
     memoria: un battito nuovo sul database e' quel che fa un server
     ripartito) niente;
  4. a 72 ore il moderatore, a 88 il secondo, poi basta;
  5. il riavvio tardivo: un secondo scambio guardato la prima volta a 90
     ore — solo l'88 al moderatore, le parti niente, e il journal dice
     perche';
  6. il «pagato» e l'interruttore spento: la parte che l'ha spento non
     riceve, il moderatore che l'ha spento si'.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore.

USO:  python collaudo_garanzia_lunga.py
"""

import asyncio
import contextlib
import io
import sys
import time

import collaudo_pagamento_p2p as banco

SEGRETO = "collaudo-segreto"
V, C, MOD = banco.VENDE, banco.COMPRA, 999
H = 3600


class Orologio:
    """Il `time` del server con le lancette che si spostano: tutto il
    resto e' il modulo vero (strftime, localtime...)."""

    def __init__(self, vero):
        self.vero = vero
        self.avanti = 0

    def time(self):
        return self.vero.time() + self.avanti

    def __getattr__(self, nome):
        return getattr(self.vero, nome)


OROLOGIO = Orologio(time)
# (13 ott 2026, notifica-porta-allo-scambio) i bottoni degli avvisi
# dell'ultimo battito, nell'ordine: `(chi, bottone)`
BOTTONI = []


def ordine(n):
    return f"6a1e0000-c2c2-4a2b-9c3d-{n:012d}"


async def evento(o, azione, attore, dettaglio=""):
    b = banco.Busta({"v": 1, "order": o, "action": azione,
                     "ts": int(OROLOGIO.time()), "buyer": banco.CHIAVE_COMPRA,
                     "seller": banco.CHIAVE_VENDE, "actor": attore,
                     "detail": dettaglio})
    b.headers = {"authorization": f"Bearer {SEGRETO}"}
    await banco.SRV.evento_p2p(b)
    await asyncio.sleep(0.6)


async def scambio(o):
    """Una vendita di chi vende, presa da chi compra, con la garanzia
    pagata ADESSO (le lancette tornano a zero prima)."""
    OROLOGIO.avanti = 0
    con = banco.con_db()
    con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,"
                "sats,euro,metodi) VALUES(?,?,?,'pending','sell',1,72000,"
                "'50,00 €','[\"SEPA\"]')", (o, V, int(time.time())))
    con.commit()
    con.close()
    await evento(o, "taken", "buyer", "invoice-next")
    await asyncio.sleep(banco.SRV.P2P_RESPIRO_S + 0.8)
    await evento(o, "hold-invoice-paid", "seller", "active")
    if banco.SRV._TASK_EVENTI_P2P:
        await asyncio.gather(*list(banco.SRV._TASK_EVENTI_P2P), return_exceptions=True)
    del banco.DETTO[:]


async def battito(ore, o=None):
    """Le lancette a `ore` dalla garanzia, e un battito vero delle
    garanzie lunghe. Torna (avvisi partiti, journal); con `o`, solo
    quelli di quello scambio."""
    OROLOGIO.avanti = int(ore * H)
    del banco.DETTO[:]
    del BOTTONI[:]
    giornale = io.StringIO()
    # la leva accesa SOLO per il battito: il resto del server (la
    # fotografia del libro dopo un evento) resta col P2P spento del
    # config di cartone, e non cerca relay
    vera = banco.SRV._p2p_leve
    banco.SRV._p2p_leve = lambda *a, **k: dict(vera(), attivo=True)
    try:
        with contextlib.redirect_stdout(giornale):
            await banco.SRV._giro_garanzie_p2p()
    finally:
        banco.SRV._p2p_leve = vera
    detti = list(banco.DETTO)
    if o:
        corto = o[:8]
        righe = [r for r in giornale.getvalue().splitlines() if corto in r]
        return detti, "\n".join(righe)
    return detti, giornale.getvalue()


async def giro():
    SRV = banco.SRV
    prova = banco.prova
    SRV.P2P_EVENTI_SEGRETO = SEGRETO
    SRV._p2p_per = lambda *a, **k: {"attivo": True}
    SRV.time = OROLOGIO

    print("\n1) lo scambio nasce dagli eventi veri, e a 47 ore non succede niente")
    a = ordine(1)
    await scambio(a)
    con = banco.con_db()
    g = con.execute("SELECT COUNT(*) FROM p2p_momenti WHERE ordine=? AND "
                    "momento='garanzia_pagata' AND fonte='mostro'", (a,)).fetchone()[0]
    con.close()
    prova("il coordinatore ha detto «garanzia pagata»: c'e' il momento", 1, g)
    detti, _ = await battito(47)
    prova("a 47 ore niente a nessuno", [], detti)

    print("\n2) a 48 ore: chi vende e chi compra")
    detti, giornale = await battito(48)
    prova("un avviso a testa", sorted([V, C]), sorted(chi for chi, _ in detti))
    testi = dict(detti)
    prova("chi vende legge che chi compra non ha ancora segnato il pagamento", True,
          testi.get(V, "").startswith("⏳ <b>Il tuo scambio da 50,00 € è fermo da 2 giorni</b>"
                                       " e i sats sono ancora in garanzia: chi compra non ha "
                                       "ancora detto di averti inviato gli euro."))
    prova("chi compra legge «dillo con Ho inviato gli euro»", True,
          "con «Ho inviato gli euro»; se non li invii più, annullate d'accordo."
          in testi.get(C, ""))
    prova("il journal ha una riga per ogni avviso mandato", [True, True],
          [f"⏰ Garanzia lunga P2P: {a[:8]} 48h → {V} (vende; pagato: no, disputa: no): mandato"
           in giornale,
           f"⏰ Garanzia lunga P2P: {a[:8]} 48h → {C} (compra; pagato: no, disputa: no): mandato"
           in giornale])

    # (13 ott 2026, notifica-porta-allo-scambio)
    prova("...e sotto, a tutti e due, «⚡ Apri lo scambio» con l'id di QUESTO scambio",
          sorted([(V, ("⚡ Apri lo scambio", f"https://barattolo.store/p2p?scambio={a}")),
                  (C, ("⚡ Apri lo scambio", f"https://barattolo.store/p2p?scambio={a}"))]),
          sorted(BOTTONI))

    print("\n3) niente doppioni: ripassando, e dopo un «riavvio»")
    prova("un minuto dopo, niente", [], (await battito(48 + 1 / 60))[0])
    prova("un battito nuovo sul database (quel che fa un server ripartito): niente",
          [], (await battito(49))[0])

    print("\n4) i moderatori: 72 e 88 ore, poi basta")
    detti, giornale = await battito(72)
    prova("a 72 ore il moderatore, e solo lui", [MOD], [chi for chi, _ in detti])
    prova("...SENZA il bottone dello scambio: quello e' delle due parti",
          [(MOD, None)], list(BOTTONI))
    prova("...col testo delle 72", True, bool(detti) and detti[0][1].startswith(
        f"⏰ <b>Scambio P2P in garanzia da 72 ore</b> (ordine <code>{a[:8]}</code>)"))
    prova("...e la riga nel journal", True,
          f"⏰ Garanzia lunga P2P: {a[:8]} 72h → {MOD} (moderatore; pagato: no, disputa: no): mandato"
          in giornale)
    detti, _ = await battito(88)
    prova("a 88 ore il secondo, urgente", [(MOD, True)],
          [(chi, x.startswith("🚨 <b>Scambio P2P in garanzia da 88 ore: restano circa 4 ore</b>"))
           for chi, x in detti])
    prova("...e poi basta, fino a 100 ore e oltre", [[], [], []],
          [(await battito(o))[0] for o in (89, 99, 101)])

    print("\n5) il riavvio tardivo: guardato la prima volta a 90 ore")
    b = ordine(2)
    await scambio(b)
    detti, giornale = await battito(90, b)
    prova("solo l'88, al moderatore, con le ore vere; le parti niente", [(MOD, True)],
          [(chi, "da 90 ore" in x) for chi, x in detti])
    prova("...e il journal dice perche' gli altri non sono partiti", [True, True, True],
          [f"Garanzia lunga P2P: {b[:8]} 48h a {V} (vende) saltato" in giornale,
           f"Garanzia lunga P2P: {b[:8]} 48h a {C} (compra) saltato" in giornale,
           f"Garanzia lunga P2P: {b[:8]} 72h a {MOD} (moderatore) saltato: e' gia' a 90 ore, "
           "parte quello delle 88" in giornale])
    prova("...e rilanciato, niente", [], (await battito(90.1, b))[0])

    print("\n6) il «pagato», e l'interruttore spento")
    c = ordine(3)
    await scambio(c)
    await evento(c, "fiat-sent", "buyer")
    if SRV._TASK_EVENTI_P2P:
        await asyncio.gather(*list(SRV._TASK_EVENTI_P2P), return_exceptions=True)
    con = banco.con_db()
    con.execute("UPDATE utenti SET avvisi_p2p=0 WHERE tg_id=?", (C,))
    con.execute("INSERT OR REPLACE INTO utenti(tg_id, nome, registrato, avvisi_p2p) "
                "VALUES(?, 'Il moderatore', 1, 0)", (MOD,))
    con.commit()
    con.close()
    detti, giornale = await battito(48, c)
    prova("chi compra ha gli avvisi spenti: riceve solo chi vende, col testo del «pagato»",
          [(V, True)], [(chi, "chi compra dice di averti inviato gli euro" in x)
                        for chi, x in detti])
    prova("...e il journal lo dice", True,
          f"🔕 Garanzia lunga P2P: {c[:8]} 48h a {C} (compra) non parte" in giornale)
    detti, _ = await battito(72, c)
    prova("il moderatore ha gli avvisi P2P spenti, e il suo arriva lo stesso, col «sì»",
          [(MOD, True)], [(chi, "«Ho inviato gli euro»: <b>sì</b>" in x) for chi, x in detti])
    SRV.time = time


def main():
    banco.avvio()
    banco.semina()
    banco.SRV.P2P_RESPIRO_S = 1
    banco.SRV.P2P_RESPIRO_NOME_S = 1

    # (13 ott 2026) la notifica di cartone tiene anche il BOTTONE: il
    # testo va dove andava (`banco.DETTO`), il bottone in `BOTTONI`
    async def notifica_col_bottone(chi, testo, bottone=None, *a, **k):
        banco.DETTO.append((chi, testo))
        BOTTONI.append((chi, bottone))
    banco.SRV.notifica = notifica_col_bottone
    asyncio.run(giro())
    print(f"\n{banco.PASSATE} passate, {banco.FALLITE} fallite")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
