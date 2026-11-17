# -*- coding: utf-8 -*-
"""
LA REPUTAZIONE DEL P2P SUL SERVER VERO, CON GLI EVENTI FINTI DEL
COORDINATORE (10 ott 2026, cantiere reputazione-p2p, richiesta di Andrea).

Il caso: il giorno del lancio un venditore ha preso un ordine e non ha
bloccato la garanzia in tempo; lo scambio si e' annullato, e chi aveva
pubblicato e' rimasto ad aspettare. Da qui quattro difese: lo «scambio
non completato» a chi ha preso e non ha fatto il suo gesto (e MAI a chi
ha pubblicato), i tentativi che lo scusano, il filtro di chi pubblica
(«solo chi ha almeno N scambi completati») e il limite di due prese in
attesa. `prove.py` difende i giudici estratti (`prove_reputazione_p2p`).
Qui girano le ROTTE VERE — `/api/p2p/evento` col bearer di mostrod,
`/api/p2p/tentativo`, `/api/p2p/posso-prendere`, `/api/p2p/ordini` con
i filtri, `/api/p2p/facce`, `/api/p2p/controparte`, `/api/negozio/…`,
«dimentica il profilo» — su un database usa-e-getta, e si guarda cosa
resta scritto:

  1. la porta: il segreto sbagliato e' un 403, e non si scrive niente;
  2. chi prende COMPRANDO e non da' la fattura: `taker-timeout` →
     un «mancato» a lui, niente a chi ha pubblicato; il primo si
     tollera (il marchio tace);
  3. chi ci ha provato (la fattura rifiutata, dichiarata dalla rotta)
     non si conta; l'estraneo non puo' dichiarare;
  4. chi prende VENDENDO e non blocca la garanzia: il secondo «mancato»,
     e da due la scritta c'e' — sui volti, sulla card dell'altra parte,
     sul profilo generale (`non_completati`);
  5. il retry di mostrod (`nuovo: false`) non raddoppia niente;
  6. lo scambio concluso: «completato» alle due parti, e le stelline
     restano quelle di prima (nessun feedback, nessuna media);
  7. il filtro: chi pubblica lo dichiara con l'intestazione, la prima
     resta, un altro non la tocca, esce coi volti; un ordine vecchio
     non ha filtro e si prende; chi ha i completati ma due mancati nel
     mese no; con uno solo si';
  8. il limite: due prese in attesa della fattura, e la terza e' «prese»
     su qualunque ordine; data una fattura, si riapre;
  9. «dimentica il profilo» toglie i tentativi e tiene gli esiti.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram (le notifiche finiscono in
una lista), niente relay (il relay morto sul loopback), niente
coordinatore.

USO:  python collaudo_reputazione_p2p.py
"""

import asyncio
import json
import sys
import time

import collaudo_pagamento_p2p as banco

SEGRETO = "collaudo-segreto"
# gli ordini di questo giro (la forma di mostro: uuid)
A = "5a1e0000-0a0a-4a2b-9c3d-00000000000a"      # vendita di 111, presa da 222 comprando: niente fattura
B = "5a1e0000-0b0b-4a2b-9c3d-00000000000b"      # idem, ma 222 ha mandato una fattura (rifiutata)
C = "5a1e0000-0c0c-4a2b-9c3d-00000000000c"      # acquisto di 111, preso da 222 vendendo: niente garanzia
D = "5a1e0000-0d0d-4a2b-9c3d-00000000000d"      # vendita di 111, presa da 222, conclusa
E = "5a1e0000-0e0e-4a2b-9c3d-00000000000e"      # vendita di 111 col filtro «3+»
F = "5a1e0000-0f0f-4a2b-9c3d-00000000000f"      # vendita di 111 di prima, senza filtro
G = "5a1e0000-0101-4a2b-9c3d-000000000010"      # le due prese aperte di 222
H = "5a1e0000-0202-4a2b-9c3d-000000000011"
I = "5a1e0000-0303-4a2b-9c3d-000000000012"      # una vendita PUBBLICATA da 222: il suo volto sul libro
L = "5a1e0000-0404-4a2b-9c3d-000000000013"      # presa da 222, che tocca «Annulla» e l'annullo non arriva
MAKER, TAKER, ESTRANEO, VETERANO = banco.VENDE, banco.COMPRA, banco.ESTRANEO, 444


def busta(ordine, azione, ts, attore, dettaglio, buyer=banco.CHIAVE_COMPRA,
          seller=banco.CHIAVE_VENDE, segreto=SEGRETO, **extra):
    d = {"v": 1, "order": ordine, "action": azione, "ts": ts, "buyer": buyer,
         "seller": seller, "actor": attore, "detail": dettaglio}
    d.update(extra)
    b = banco.Busta(d)
    b.headers = {"authorization": f"Bearer {segreto}"} if segreto else {}
    return b


async def posta(b):
    """Il POST di mostrod alla rotta vera: il corpo della risposta, o il
    codice del rifiuto."""
    try:
        r = await banco.SRV.evento_p2p(b)
        return json.loads(r.body)
    except Exception as e:
        return getattr(e, "status_code", type(e).__name__)


def esiti(tg):
    con = banco.con_db()
    r = [tuple(x) for x in con.execute(
        # (10 ott 2026, malus-p2p) la scusa del tentativo ora si SCRIVE
        # (`scusato`): ha il suo collaudo, e qui resta fuori dal conto
        "SELECT esito, ordine FROM p2p_esiti WHERE tg_id=? AND esito<>'scusato' "
        "ORDER BY quando, esito", (tg,))]
    con.close()
    return r


def tentativi(tg):
    con = banco.con_db()
    r = [tuple(x) for x in con.execute(
        "SELECT gesto, ordine, motivo FROM p2p_tentativi WHERE tg_id=? ORDER BY quando", (tg,))]
    con.close()
    return r


def stelle(tg):
    con = banco.con_db()
    r = con.execute("SELECT rating, n_feedback FROM utenti WHERE tg_id=?", (tg,)).fetchone()
    n = con.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
    con.close()
    return (float(r["rating"] or 0), int(r["n_feedback"] or 0), n)


def semina_ordini():
    con = banco.con_db()
    adesso = int(time.time())
    for ordine, lato in ((A, "sell"), (B, "sell"), (C, "buy"), (D, "sell"), (E, "sell"),
                         (F, "sell"), (G, "sell"), (H, "sell"), (L, "sell")):
        con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,sats,euro,"
                    "metodi) VALUES(?,?,?,'pending',?,1,15000,'10,00 €',?)",
                    (ordine, MAKER, adesso, lato, json.dumps(["SEPA"])))
    # su A chi ha preso l'ha DICHIARATO (e' la riga che la card dell'altra
    # parte legge, `_controparti_p2p`)
    con.execute("UPDATE p2p_ordini SET preso_da=? WHERE ordine=?", (TAKER, A))
    # la vendita pubblicata da 222
    con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,sats,euro,"
                "metodi) VALUES(?,?,?,'pending','sell',1,15000,'10,00 €',?)",
                (I, TAKER, adesso, json.dumps(["SEPA"])))
    # un veterano con tre scambi completati
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,ln_address) "
                "VALUES(?,?,?,1,'')", (VETERANO, "Un veterano", "neg444444"))
    for k in range(3):
        con.execute("INSERT INTO p2p_esiti(tg_id, ordine, giro, esito, ruolo, quando) "
                    "VALUES(?,?,1,'completato','compra',?)",
                    (VETERANO, f"veterano-{k}", adesso - (10 + k) * 86400))
    con.commit()
    con.close()


async def chiama(fn, corpo):
    """Una rotta del P2P dentro il loop: il corpo dalle due porte
    (`leggi_json` e `req.json()`), la risposta come dizionario, un
    rifiuto come coppia (codice, messaggio) — il calco di `banco.esito`,
    che pero' apre un loop suo e qui non si puo'."""
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


async def posso(chi, ordini):
    banco.come(chi)
    return await chiama(banco.SRV.posso_prendere_p2p, {"ordini": ordini})


async def tentativo(chi, ordine, gesto, motivo=""):
    banco.come(chi)
    return await chiama(banco.SRV.tentativo_p2p, {"ordine": ordine, "gesto": gesto, "motivo": motivo})


async def giro():
    SRV = banco.SRV
    prova = banco.prova
    t0 = int(time.time()) - 600

    print("\n1) la porta")
    prova("col segreto sbagliato: 403", 403,
          await posta(busta(A, "taken", t0, "buyer", "invoice-next", segreto="un-altro")))
    prova("...e nessun esito scritto", ([], []), (esiti(TAKER), esiti(MAKER)))

    print("\n2) chi prende comprando e non da' la fattura")
    prova("la presa entra", True, (await posta(busta(A, "taken", t0, "buyer", "invoice-next")))["nuovo"])
    await posta(busta(A, "buyer-invoice-requested", t0, "mostro", ""))
    prova("il timeout di chi ha preso entra", True,
          (await posta(busta(A, "expired", t0 + 400, "mostro", "taker-timeout")))["nuovo"])
    prova("un «mancato» a chi ha preso, niente a chi ha pubblicato",
          ([("mancato", A)], []), (esiti(TAKER), esiti(MAKER)))
    r = await posso(TAKER, [F])
    prova("...il primo si tollera: il marchio tace, ma il mese lo conta", (0, 1),
          (r["mancati"], r["mancati_30"]))
    prova("...e l'ordine vecchio, senza filtro, si prende lo stesso",
          {"ok": True, "motivo": "", "soglia": 0}, r["ordini"][F])

    print("\n3) chi ci ha provato non si penalizza")
    await posta(busta(B, "taken", t0 + 10, "buyer", "invoice-next"))
    await posta(busta(B, "buyer-invoice-requested", t0 + 10, "mostro", ""))
    prova("la fattura rifiutata si dichiara dalla rotta, e resta scritta",
          ({"ok": True, "motivo": ""}, [("fattura_rifiutata", B, "invalid-invoice")]),
          (await tentativo(TAKER, B, "fattura_rifiutata", "invalid-invoice"), tentativi(TAKER)))
    prova("...l'estraneo non puo' dichiarare, e non sa perche'",
          {"ok": False, "motivo": "ignota"}, await tentativo(ESTRANEO, B, "fattura_inviata"))
    prova("...un gesto fuori catalogo e' un 400", 400,
          (await tentativo(TAKER, B, "ballo"))[0])
    await posta(busta(B, "expired", t0 + 410, "mostro", "taker-timeout"))
    prova("al timeout il «mancato» NON si conta", [("mancato", A)], esiti(TAKER))

    print("\n4) chi prende vendendo e non blocca la garanzia")
    # su un ACQUISTO di 111 chi compra e' 111: le chiavi vanno coi lati
    await posta(busta(C, "taken", t0 + 20, "seller", "hold-next",
                      buyer=banco.CHIAVE_VENDE, seller=banco.CHIAVE_COMPRA))
    await posta(busta(C, "hold-invoice-requested", t0 + 20, "mostro", "take",
                      buyer=banco.CHIAVE_VENDE, seller=banco.CHIAVE_COMPRA))
    await posta(busta(C, "expired", t0 + 420, "mostro", "taker-timeout",
                      buyer=banco.CHIAVE_VENDE, seller=banco.CHIAVE_COMPRA))
    prova("il secondo «mancato» a chi ha preso, niente a chi ha pubblicato",
          ([("mancato", A), ("mancato", C)], []), (esiti(TAKER), esiti(MAKER)))
    r = await posso(TAKER, [F])
    prova("...e da due la scritta c'e'", 2, r["mancati"])
    # (10 ott 2026, l'avviso del blocco): fino a quando, e la riga nell'archivio
    prova("...e il blocco sui filtri ha una data: 30 giorni dal secondo mancato piu' recente",
          t0 + 400 + 30 * 86400, r["fino"])
    banco.come(TAKER)
    arch = (await chiama(SRV.scambi_p2p, {}))["scambi"]
    # (emendata il 10 ott 2026, malus-p2p: sul giro SCUSATO dal tentativo
    # l'archivio ora porta la riga che lo dice — vale una volta ogni 30 giorni)
    prova("...l'archivio porta la riga del conto sul giro contato, e su quello scusato "
          "la riga della scusa",
          [True, SRV.P2P_RIGA_SCUSA],
          ["Fino al " in arch[C]["conto"] and "sono 2 negli ultimi 90 giorni" in arch[C]["conto"],
           arch[B]["conto"]])
    banco.come(MAKER)
    facce = (await chiama(SRV.facce_ordini_p2p, {"ordini": [I, F]}))["facce"]
    prova("il volto di chi ha pubblicato porta il marchio; quello senza marchio non ha la chiave",
          (2, False), (facce[I].get("mancati"), "mancati" in facce[F]))
    c = (await chiama(SRV.controparte_p2p, {"ordini": [A]}))["controparti"]
    prova("...la card dell'altra parte, a chi ha pubblicato, lo porta", 2, c[A].get("mancati"))
    SRV.verifica_utente = lambda *a, **k: (_ for _ in ()).throw(SRV.HTTPException(401, "no"))
    v = SRV.negozio("neg222222")["venditore"]
    prova("...e il profilo generale, dal mercatino, senza sessione: `non_completati`",
          2, v["non_completati"])
    prova("...mentre chi ha pubblicato ne ha 0", 0, SRV.negozio("neg111111")["venditore"]["non_completati"])

    print("\n5) il retry di mostrod")
    prova("lo stesso timeout rimandato: non nuovo", False,
          (await posta(busta(A, "expired", t0 + 400, "mostro", "taker-timeout")))["nuovo"])
    prova("...e gli esiti non raddoppiano", 2, len(esiti(TAKER)))

    print("\n5-bis) l'annullo chiesto e non arrivato (17 nov 2026, annullo-registrato)")
    await posta(busta(L, "taken", t0 + 25, "buyer", "invoice-next"))
    await posta(busta(L, "buyer-invoice-requested", t0 + 25, "mostro", ""))
    prova("chi ha preso tocca «Annulla»: il telefono lo dichiara, e la rotta lo prende",
          {"ok": True, "motivo": ""}, await tentativo(TAKER, L, "annullo_chiesto"))
    await posta(busta(L, "expired", t0 + 425, "mostro", "taker-timeout"))
    con = banco.con_db()
    righe_l = con.execute("SELECT COUNT(*) FROM p2p_esiti WHERE ordine=?", (L,)).fetchone()[0]
    con.close()
    prova("...il `cancel` non e' arrivato e il tempo scade: NON si conta, ne' «mancato» ne' "
          "«scusato»; i suoi esiti restano due", (0, 2), (righe_l, len(esiti(TAKER))))

    print("\n6) lo scambio concluso, e le stelline")
    prima = stelle(TAKER)
    await posta(busta(D, "taken", t0 + 30, "buyer", "invoice-next"))
    await posta(busta(D, "success", t0 + 430, "mostro", "", sats=15000, sats_buyer=14775,
                      sats_seller=15225))
    prova("«completato» alle due parti", ([("completato", D)], 1),
          (esiti(MAKER), sum(1 for x in esiti(TAKER) if x[0] == "completato")))
    prova("...e le stelline sono quelle di prima: nessun feedback, nessuna media",
          (prima, (0.0, 0, 0)), (stelle(TAKER), stelle(TAKER)))
    r = await posso(TAKER, [])
    prova("i numeri di chi chiede: 1 completato, 2 mancati nel mese", (1, 2, 2),
          (r["completati"], r["mancati"], r["mancati_30"]))

    print("\n7) il filtro di chi pubblica")
    SRV.P2P_ATTIVO, SRV.MOSTRO_HEX, SRV.MOSTRO_RELAY = True, "a" * 64, ["ws://127.0.0.1:9"]
    banco.come(MAKER)
    await chiama(SRV.registra_ordini_p2p, {"ordini": [E], "pubblicati": True, "filtri": {E: 3}})
    await chiama(SRV.registra_ordini_p2p, {"ordini": [E], "pubblicati": True, "filtri": {E: 5}})
    banco.come(TAKER)
    await chiama(SRV.registra_ordini_p2p, {"ordini": [E], "pubblicati": True, "filtri": {E: 1}})
    SRV.P2P_ATTIVO = False
    con = banco.con_db()
    prova("l'intestazione scrive il filtro, la prima resta, un altro non la tocca", (3, 0),
          (con.execute("SELECT min_completati FROM p2p_ordini WHERE ordine=?", (E,)).fetchone()[0],
           con.execute("SELECT min_completati FROM p2p_ordini WHERE ordine=?", (F,)).fetchone()[0]))
    con.close()
    banco.come(MAKER)
    prova("...ed esce coi volti", {E: 3}, (await chiama(SRV.facce_ordini_p2p, {"ordini": [E, F]}))["filtri"])
    r = await posso(TAKER, [E, F])
    prova("chi ha 1 completato non prende l'ordine col filtro 3, ma prende quello vecchio",
          ({"ok": False, "motivo": "filtro", "soglia": 3}, {"ok": True, "motivo": "", "soglia": 0}),
          (r["ordini"][E], r["ordini"][F]))
    r = await posso(VETERANO, [E])
    prova("il veterano con tre completati e nessun mancato lo prende",
          {"ok": True, "motivo": "", "soglia": 3}, r["ordini"][E])
    con = banco.con_db()
    con.execute("INSERT INTO p2p_esiti(tg_id, ordine, giro, esito, ruolo, quando) "
                "VALUES(?,'veterano-m1',1,'mancato','compra',?)", (VETERANO, t0 - 5 * 86400))
    con.commit()
    con.close()
    prova("...con UN mancato nel mese ancora si' (si tollera)", True, (await posso(VETERANO, [E]))["ordini"][E]["ok"])
    con = banco.con_db()
    con.execute("INSERT INTO p2p_esiti(tg_id, ordine, giro, esito, ruolo, quando) "
                "VALUES(?,'veterano-m2',1,'mancato','compra',?)", (VETERANO, t0 - 2 * 86400))
    con.commit()
    con.close()
    prova("...con due no: «mancati»", "mancati", (await posso(VETERANO, [E]))["ordini"][E]["motivo"])
    prova("un corpo storto e' un 400", 400, (await posso(TAKER, ["x"]))[0])

    print("\n8) il limite delle prese")
    for o, dt in ((G, 40), (H, 41)):
        await posta(busta(o, "taken", t0 + dt, "buyer", "invoice-next"))
        await posta(busta(o, "buyer-invoice-requested", t0 + dt, "mostro", ""))
    r = await posso(TAKER, [F])
    prova("due prese in attesa della fattura: la terza e' «prese», anche sull'ordine senza filtro",
          ({"ok": False, "motivo": "prese", "soglia": 0}, 2, 2), (r["ordini"][F], r["prese_aperte"], r["limite"]))
    await posta(busta(H, "buyer-invoice-added", t0 + 50, "buyer", "hold-next"))
    r = await posso(TAKER, [F])
    prova("...data una fattura, ne resta una aperta e si prende di nuovo", (True, 1),
          (r["ordini"][F]["ok"], r["prese_aperte"]))

    print("\n9) dimentica il profilo")
    banco.come(TAKER)
    SRV.dimentica_chiavi_p2p()
    prova("i tentativi se ne vanno, gli esiti restano", ([], 3),
          (tentativi(TAKER), len(esiti(TAKER))))
    # i task in volo, se ne restano, finiscono prima di chiudere il loop
    if SRV._TASK_EVENTI_P2P:
        await asyncio.gather(*list(SRV._TASK_EVENTI_P2P), return_exceptions=True)


def main():
    banco.avvio()
    banco.semina()
    semina_ordini()
    banco.SRV.P2P_EVENTI_SEGRETO = SEGRETO
    banco.SRV.P2P_RESPIRO_S = 0.2
    banco.SRV.P2P_RESPIRO_NOME_S = 0.1
    asyncio.run(giro())
    print(f"\n{banco.PASSATE} passate, {banco.FALLITE} fallite")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
