# -*- coding: utf-8 -*-
"""
IL RECAPITO AGGIORNATO, SUL SERVER VERO (7 ott 2026).

La richiesta di Andrea: quando chi vende AGGIORNA il recapito dopo
averlo gia' mandato, chi compra riceve «📮 X ha aggiornato il recapito.
Controlla il nuovo prima di inviare gli euro.»; se gli euro risultano
gia' inviati, la frase gli dice di scriverlo nella chat dello scambio e
di non inviarli una seconda volta. Il recapito non passa dal server:
sa solo che e' cambiato. OGNI CAMBIO AVVISA, anche a raffica (Andrea:
la finestra di cinque minuti, provata per un giro, lasciava muto un
cambio arrivato presto); il tetto di tre e' tolto e ne resta uno alto,
dieci, che quando scatta scrive nel journal una riga col ⛔.

`prove.py` difende il giudice estratto (`prove_recapito_aggiornato`) e
il client in node (`prove_p2p_recapito_passo`). Qui girano le ROTTE
VERE — `/api/p2p/recapito` e, per lo scambio, `/api/p2p/evento` — su un
database usa-e-getta:

  1. il primo invio: «ti ha indicato dove inviare», come prima;
  2. l'aggiornamento subito dopo: «📮 … Controlla il nuovo»;
  3. la raffica: tre cambi di fila, tre avvisi;
  4. il journal di un aggiornamento partito;
  5. dopo «Ho inviato gli euro» (detto da mostrod): la frase dei gia'
     inviati;
  6. il tetto alto: dieci avvisi, poi la riga ⛔ nel journal;
  7. un recapito messo nel corpo apposta non arriva da nessuna parte.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore.

USO:  python collaudo_recapito_aggiornato.py
"""

import asyncio
import contextlib
import io
import json
import sys
import time

import collaudo_pagamento_p2p as banco

SEGRETO = "collaudo-segreto"
V, C = banco.VENDE, banco.COMPRA
# (12 ott 2026, chi-e-l-altro) chi ha preso vede chi ha pubblicato appena
# mostrod nomina le due parti: la frase dice il NOME di V, che il banco
# semina come «Vera» (senza un nome direbbe «Chi ti vende i sats»)
AGG = ("📮 <b>Vera ha aggiornato il recapito.</b> Controlla il "
       "nuovo prima di inviare gli euro.")
GIA = ("📮 <b>Vera ha aggiornato il recapito dopo che hai segnato "
       "gli euro come inviati.</b> Se li hai già inviati al recapito precedente, "
       "scrivilo nella chat dello scambio: non inviarli una seconda volta.")


def adesso():
    return int(time.time())


def ordine(n):
    return f"5a1e0000-c2c2-4a2b-9c3d-{n:012d}"


async def evento(o, azione, attore, dettaglio=""):
    b = banco.Busta({"v": 1, "order": o, "action": azione, "ts": adesso(),
                     "buyer": banco.CHIAVE_COMPRA, "seller": banco.CHIAVE_VENDE,
                     "actor": attore, "detail": dettaglio})
    b.headers = {"authorization": f"Bearer {SEGRETO}"}
    await banco.SRV.evento_p2p(b)
    await asyncio.sleep(0.6)


async def scambio(o):
    """Una vendita di chi vende, presa da chi compra, con la garanzia
    pagata: e' il momento in cui il recapito si manda."""
    con = banco.con_db()
    con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,"
                "sats,euro,metodi) VALUES(?,?,?,'pending','sell',1,15000,"
                "'10,00 €','[\"SEPA\"]')", (o, V, adesso()))
    con.commit()
    con.close()
    await evento(o, "taken", "buyer", "invoice-next")
    await asyncio.sleep(banco.SRV.P2P_RESPIRO_S + 0.8)
    await evento(o, "hold-invoice-paid", "seller", "active")
    del banco.DETTO[:]


async def recapito(o, extra=None):
    """Il telefono di chi vende dice «ho mandato il recapito»: la rotta
    vera, col suo journal catturato. Torna (avvisi partiti, journal)."""
    del banco.DETTO[:]
    banco.come(V)
    corpo = {"ordine": o, "attivo": True}
    corpo.update(extra or {})
    giornale = io.StringIO()
    with contextlib.redirect_stdout(giornale):
        r = await banco.SRV.recapito_p2p(banco.Busta(corpo))
    return list(banco.DETTO), giornale.getvalue(), r


async def giro():
    SRV = banco.SRV
    prova = banco.prova
    SRV.P2P_EVENTI_SEGRETO = SEGRETO
    SRV._p2p_per = lambda *a, **k: {"attivo": True}

    print("\n1) il primo invio")
    o = ordine(1)
    await scambio(o)
    detti, _, r = await recapito(o)
    prova("risponde ok, e a chi compra parte la frase di sempre", ({"ok": True}, C, True),
          (r, detti[0][0] if detti else 0, (detti[0][1] if detti else "").startswith(
              "💶 <b>Vera ti ha indicato dove inviare 10,00 €: tocca a te.</b>")))

    print("\n2) l'aggiornamento SUBITO DOPO")
    detti, giornale, _ = await recapito(o)
    prova("parte, con le parole di Andrea", [(C, AGG)], detti)

    print("\n3) LA RAFFICA: tre cambi di fila")
    raffica = [(await recapito(o))[0] for _ in range(3)]
    prova("tre avvisi, uno a cambio", [[(C, AGG)]] * 3, raffica)

    print("\n4) il journal")
    prova("l'aggiornamento partito ha la sua riga, come il primo invio", True,
          f"💶 Recapito P2P: {V} ha indicato dove ricevere gli euro, avvisato {C}"
          in giornale)

    print("\n5) dopo «Ho inviato gli euro»")
    del banco.DETTO[:]
    await evento(o, "fiat-sent", "buyer")
    prova("chi vende sente il «pagato», come sempre", [V], [chi for chi, _ in banco.DETTO])
    detti, _, _ = await recapito(o)
    prova("l'aggiornamento dopo il pagato: la frase dei gia' inviati", [(C, GIA)], detti)

    print("\n6) IL TETTO ALTO")
    o = ordine(2)
    await scambio(o)
    partiti = []
    for _ in range(SRV.P2P_RECAPITO_MAX):
        partiti.append(len((await recapito(o))[0]))
    prova("dieci avvisi di fila, uno a cambio", [1] * 10, partiti)
    detti, giornale, r = await recapito(o)
    prova("l'undicesimo non parte, e la rotta risponde ok lo stesso",
          ([], {"ok": True}), (detti, r))
    prova("...il journal ha la sua riga col ⛔", True,
          f"⛔ Recapito P2P: da {V}, sull'ordine {o[:8]}: TETTO ANTI-ABUSO: gia' "
          "10 avvisi del recapito su questo scambio (tetto 10)" in giornale)

    print("\n7) il recapito non passa di qui")
    o = ordine(3)
    await scambio(o)
    await recapito(o)
    detti, giornale, _ = await recapito(o, {"recapito": "IT60X0542811101000000123456",
                                            "testo": "IBAN SEGRETO"})
    prova("un recapito messo nel corpo apposta: l'avviso parte, senza di lui",
          ([(C, AGG)], False, False),
          (detti, "IT60" in json.dumps(detti) + giornale, "SEGRETO" in json.dumps(detti) + giornale))
    if SRV._TASK_EVENTI_P2P:
        await asyncio.gather(*list(SRV._TASK_EVENTI_P2P), return_exceptions=True)


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
