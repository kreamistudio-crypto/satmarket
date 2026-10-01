# -*- coding: utf-8 -*-
"""
GLI AVVISI P2P NELL'ORDINE DEI FATTI, SUL SERVER VERO (24 set 2026).

Il caso: un venditore con un PayCode nel libro riceve su Telegram
prima «chi compra ha annullato: il tuo ordine e' tornato in vetrina» e
subito dopo «il tuo PayCode e' stato preso». Qualcuno aveva preso e
ritirato in dodici secondi, e i due POST di mostrod (patch 0007) sono
arrivati in un ordine e sono stati GIUDICATI nell'altro: la frase della
presa respira `P2P_RESPIRO_S` aspettando i numeri del libro, il ritiro
no; e per Tor il POST della presa puo' arrivare al retry, dopo quello
del ritiro.

`prove.py` difende i giudici estratti (`prove_p2p_avvisi_in_ordine`).
Qui gira la ROTTA VERA, `/api/p2p/evento`, coi suoi task e il suo
respiro, su un database usa-e-getta, e si guarda cosa parte davvero e in
che ordine:

  1. la porta: 404 a porta chiusa, 403 a segreto sbagliato;
  2. IL LAMPO: presa e ritiro a dodici secondi, i POST nell'ordine
     giusto — non parte NIENTE (la presa e' superata dal ritiro quando
     finisce di respirare, il ritiro non segue nessuna presa detta);
  3. L'ORDINE CALMO: presa, il respiro passa, poi il ritiro — due
     avvisi, presa e ritorno, in quest'ordine;
  4. TOR: il POST del ritiro arriva PRIMA di quello della presa — non
     parte niente, e le parti dello scambio restano quelle dell'ultimo
     fatto (nessuno ha preso);
  5. il retry di mostrod (stesso corpo) non fa partire niente di nuovo;
  6. LA CAUZIONE (1 ott 2026, l'ordine 82231748): chi compra prende una
     vendita in contanti e paga la cauzione da un wallet esterno;
     mostrod manda la fattura chiesta PRIMA della presa (due POST, due
     task). A chi compra parte subito «Cauzione bloccata ✓: ora indica
     dove ricevere i sats», poi la presa a chi vende; a leva spenta la
     stessa strada resta muta com'era.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram (le notifiche finiscono in
una lista), niente relay, niente coordinatore.

USO:  python collaudo_avvisi_in_ordine_p2p.py
"""

import asyncio
import json
import sys
import time

import collaudo_pagamento_p2p as banco

LAMPO = "5a1e0000-7777-4a2b-9c3d-000000000007"
CALMO = "5a1e0000-8888-4a2b-9c3d-000000000008"
TOR = "5a1e0000-9999-4a2b-9c3d-000000000009"
CAUZ = "5a1e0000-aaaa-4a2b-9c3d-00000000000a"      # la vendita in contanti, con la cauzione
SENZA = "5a1e0000-bbbb-4a2b-9c3d-00000000000b"     # la stessa, a leva spenta
# il 38385 del coordinatore come lo tiene la fotografia del libro: la
# cauzione accesa per chi prende, solo «Contanti», il timeout che non brucia
INFO_38385 = {"kind": 38385, "tags": [["bond_enabled", "true"], ["bond_apply_to", "take"],
                                      ["bond_only_payment_methods", "Contanti"],
                                      ["bond_slash_on_waiting_timeout", "false"]]}
SEGRETO = "collaudo-segreto"
RESPIRO_S = 2            # il respiro vero e' 6: qui si accorcia, non si salta


def semina_ordini():
    """Tre PayCode di chi vende nel libro, in vetrina: i numeri li ha
    gia' scritti il libro (sats, euro, metodi), come in produzione."""
    con = banco.con_db()
    adesso = int(time.time())
    for ordine in (LAMPO, CALMO, TOR):
        con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,"
                    "maker,sats,euro,metodi) VALUES(?,?,?,'pending','sell',1,"
                    "15000,'10,00 €',?)",
                    (ordine, banco.VENDE, adesso,
                     json.dumps(["Contanti al tabacchino 10.00"])))
    # ...e due vendite in CONTANTI di persona (1 ott 2026), per la cauzione
    for ordine in (CAUZ, SENZA):
        con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,"
                    "maker,sats,euro,metodi) VALUES(?,?,?,'pending','sell',1,"
                    "8000,'5,00 €',?)",
                    (ordine, banco.VENDE, adesso, json.dumps(["Contanti"])))
    con.commit()
    con.close()


def busta(ordine, azione, ts, attore, dettaglio, buyer=banco.CHIAVE_COMPRA,
          segreto=SEGRETO):
    b = banco.Busta({"v": 1, "order": ordine, "action": azione, "ts": ts,
                     "buyer": buyer, "seller": banco.CHIAVE_VENDE,
                     "actor": attore, "detail": dettaglio})
    b.headers = {"authorization": f"Bearer {segreto}"} if segreto else {}
    return b


async def posta(b):
    """Il POST di mostrod alla rotta vera: torna il corpo della risposta
    (la rotta lancia l'invio in un task, che le pause qui sotto lasciano
    finire) o il codice del rifiuto."""
    try:
        r = await banco.SRV.evento_p2p(b)
        return json.loads(r.body)
    except Exception as e:
        return getattr(e, "status_code", type(e).__name__)


def detti_per(ordine_testo=None):
    return [(chi, t) for chi, t in banco.DETTO]


def timbri(ordine):
    con = banco.con_db()
    r = [tuple(x) for x in con.execute(
        "SELECT momento, tg_id FROM p2p_avvisi WHERE ordine=? ORDER BY quando, momento",
        (ordine,))]
    con.close()
    return r


def parti(ordine):
    con = banco.con_db()
    r = con.execute("SELECT compratore, venditore, preso_dal FROM p2p_scambi "
                    "WHERE ordine=?", (ordine,)).fetchone()
    con.close()
    return tuple(r) if r else None


async def giro():
    SRV = banco.SRV
    prova = banco.prova
    t0 = int(time.time()) - 60

    print("\n1) la porta")
    SRV.P2P_EVENTI_SEGRETO = ""
    prova("a porta chiusa la rotta non c'e': 404", 404,
          await posta(busta(LAMPO, "taken", t0, "buyer", "invoice-next")))
    SRV.P2P_EVENTI_SEGRETO = SEGRETO
    prova("col segreto sbagliato: 403", 403,
          await posta(busta(LAMPO, "taken", t0, "buyer", "invoice-next",
                            segreto="un-altro")))
    prova("...e finora non e' partito niente", [], list(banco.DETTO))

    print("\n2) IL LAMPO: presa e ritiro a dodici secondi, nell'ordine giusto")
    del banco.DETTO[:]
    r1 = await posta(busta(LAMPO, "taken", t0, "buyer", "invoice-next"))
    prova("la presa entra: nuova", {"ok": True, "nuovo": True}, r1)
    await asyncio.sleep(0.4)          # la presa sta respirando
    prova("...e mentre respira non e' partito niente", [], list(banco.DETTO))
    r2 = await posta(busta(LAMPO, "canceled", t0 + 12, "buyer", "republished",
                           buyer=None))
    prova("il ritiro entra: nuovo", {"ok": True, "nuovo": True}, r2)
    await asyncio.sleep(RESPIRO_S + 1.5)   # la presa finisce di respirare
    prova("NON PARTE NIENTE: ne' il ritorno (presa mai detta), ne' la presa "
          "(superata dal ritiro)", [], list(banco.DETTO))
    prova("...nessun timbro", [], timbri(LAMPO))
    con = banco.con_db()
    cronaca = [tuple(x) for x in con.execute(
        "SELECT momento, quando FROM p2p_momenti WHERE ordine=? ORDER BY quando",
        (LAMPO,))]
    con.close()
    prova("...ma la cronaca ha tutt'e due i fatti", [("preso", t0), ("tornato", t0 + 12)],
          cronaca)

    print("\n3) L'ORDINE CALMO: presa, poi il ritiro dopo il respiro")
    del banco.DETTO[:]
    await posta(busta(CALMO, "taken", t0 + 100, "buyer", "invoice-next"))
    await asyncio.sleep(RESPIRO_S + 1.5)
    prova("la presa, a chi vende, col PayCode", [banco.VENDE],
          [chi for chi, _ in banco.DETTO])
    frase = banco.DETTO[0][1] if banco.DETTO else ""
    prova("...con la frase di oggi", (True, True),
          (frase.startswith("🧾 <b>Il tuo PayCode è stato preso"),
           "Vendi 15.000 sats per 10,00 €" in frase))
    await posta(busta(CALMO, "canceled", t0 + 220, "buyer", "republished",
                      buyer=None))
    await asyncio.sleep(0.6)
    prova("poi il ritiro: il ritorno in vetrina, DOPO la presa", 2, len(banco.DETTO))
    prova("...con la frase del ritorno", True,
          (banco.DETTO[1][1] if len(banco.DETTO) > 1 else "").startswith(
              "🔄 <b>Chi compra ha annullato lo scambio.</b> Il tuo ordine è "
              "tornato in vetrina"))
    prova("...e i timbri nell'ordine dei fatti",
          [("preso", banco.VENDE), ("tornato", banco.VENDE)], timbri(CALMO))

    print("\n4) TOR: il POST del ritiro arriva prima di quello della presa")
    del banco.DETTO[:]
    await posta(busta(TOR, "canceled", t0 + 312, "buyer", "republished", buyer=None))
    await asyncio.sleep(0.6)
    prova("il ritiro per primo: non parte (nessuna presa detta)", [], list(banco.DETTO))
    await posta(busta(TOR, "taken", t0 + 300, "buyer", "invoice-next"))
    await asyncio.sleep(RESPIRO_S + 1.5)
    prova("la presa al retry, con l'ora di prima: superata, non parte", [],
          list(banco.DETTO))
    prova("...e le parti dello scambio sono quelle dell'ULTIMO fatto: nessuno "
          "ha preso", (0, banco.VENDE, ""), parti(TOR))

    print("\n5) il retry di mostrod")
    del banco.DETTO[:]
    r = await posta(busta(CALMO, "taken", t0 + 100, "buyer", "invoice-next"))
    prova("lo stesso corpo di prima: gia' registrato", {"ok": True, "nuovo": False}, r)
    await asyncio.sleep(0.4)
    prova("...e non parte niente", [], list(banco.DETTO))

    print("\n6) LA CAUZIONE: la fattura chiesta arriva PRIMA della presa")
    del banco.DETTO[:]
    SRV.P2P_CAUZIONE = True
    SRV._P2P_FOTO["info"] = INFO_38385
    r = await posta(busta(CAUZ, "buyer-invoice-requested", t0 + 400, "mostro", ""))
    prova("la fattura chiesta entra: nuova", {"ok": True, "nuovo": True}, r)
    await asyncio.sleep(0.6)
    prova("...e parte SUBITO a chi compra, senza aspettare la presa: «indica dove ricevere i sats»",
          [(banco.COMPRA, "🔐 <b>Cauzione bloccata ✓:</b> ora indica dove ricevere i sats.")],
          list(banco.DETTO))
    await posta(busta(CAUZ, "taken", t0 + 401, "buyer", "invoice-next"))
    await asyncio.sleep(RESPIRO_S + 1.5)
    prova("poi la presa, a chi vende, in contanti", (2, banco.VENDE, True),
          (len(banco.DETTO), banco.DETTO[-1][0] if banco.DETTO else 0,
           (banco.DETTO[-1][1] if banco.DETTO else "").startswith(
               "⚡ <b>Il tuo ordine è stato preso!</b> Vendi 8.000 sats per 5,00 € via Contanti.")))
    prova("...due timbri, due persone, nessun doppione",
          [("fattura_chiesta", banco.COMPRA), ("preso", banco.VENDE)], timbri(CAUZ))
    SRV.P2P_CAUZIONE = False
    del banco.DETTO[:]
    await posta(busta(SENZA, "buyer-invoice-requested", t0 + 500, "mostro", ""))
    await asyncio.sleep(0.6)
    prova("a leva spenta la stessa strada resta muta com'era", [], list(banco.DETTO))
    await posta(busta(SENZA, "taken", t0 + 501, "buyer", "invoice-next"))
    await asyncio.sleep(RESPIRO_S + 1.5)
    prova("...e la presa parla a chi vende e basta", [banco.VENDE], [chi for chi, _ in banco.DETTO])
    SRV._P2P_FOTO["info"] = None
    # i task in volo, se ne restano, finiscono prima di chiudere il loop
    if banco.SRV._TASK_EVENTI_P2P:
        await asyncio.gather(*list(banco.SRV._TASK_EVENTI_P2P), return_exceptions=True)


def main():
    banco.avvio()
    banco.semina()
    semina_ordini()
    banco.SRV.P2P_RESPIRO_S = RESPIRO_S
    banco.SRV.P2P_RESPIRO_NOME_S = 1
    asyncio.run(giro())
    print(f"\n{banco.PASSATE} passate, {banco.FALLITE} fallite")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
