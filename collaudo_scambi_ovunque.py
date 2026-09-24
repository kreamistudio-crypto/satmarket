# -*- coding: utf-8 -*-
"""
I MIEI SCAMBI SU OGNI DISPOSITIVO, SUL SERVER VERO (24 set 2026).

Dal campo: Andrea pubblica dall'app Android, Alan prende dal tablet; nella
mini app Telegram dello STESSO account di Andrea lo scambio non c'era, e
dal tablet di Alan e' anche sparito. La riga vive nel localStorage del
dispositivo che l'ha aperto; il server invece sa tutto (patch 0007), e
da oggi lo dice: `/api/p2p/scambi`.

`prove.py` difende i giudici estratti e il client (`prove_scambi_
ovunque`). Qui gira la ROTTA VERA, sul database vero e usa-e-getta, con
gli eventi di mostrod passati dai due giudici della rotta degli eventi,
e si cammina uno scambio intero guardandolo dai DUE lati a ogni passo:

  1. l'ordine in vetrina: chi l'ha pubblicato lo vede «pubblicato», chi
     compra e l'estraneo non vedono niente;
  2. la presa di chi compra: «di' dove ricevere» a lui, «aspetta la
     fattura» a chi vende — e le due trade key stanno in `p2p_scambi`,
     ognuna sul suo lato;
  3. fattura data (hold-next) e garanzia chiesta nello stesso secondo:
     tocca a chi vende bloccare; garanzia pagata: attivo per tutt'e due;
  4. euro inviati, liberati, il pagamento non passato (a chi compra la
     fattura nuova, chi vende resta in pagamento e lo sa), la fattura
     nuova, il pagamento riuscito coi tre importi;
  5. un ordine preso e poi TORNATO in vetrina: chi ha pubblicato torna a
     «pubblicato», chi aveva preso non e' piu' una parte e non lo vede;
  6. un ordine preso e poi annullato: annullato per tutt'e due, e con
     `preso` vero — e' storico, non un ritiro;
  7. un annullato di due mesi fa resta fuori (lo storico e' di 30 giorni);
  8. la rotta non guarda la leva del P2P, e risponde `no-store`.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore.

USO:  python collaudo_scambi_ovunque.py
"""

import asyncio
import json
import sys
import time

import collaudo_pagamento_p2p as banco

ATTIVO = "5a1e0000-aaaa-4a2b-9c3d-0000000000a1"
TORNATO = "5a1e0000-bbbb-4a2b-9c3d-0000000000b1"
MORTO = "5a1e0000-cccc-4a2b-9c3d-0000000000c1"
VECCHIO = "5a1e0000-dddd-4a2b-9c3d-0000000000d1"
VETRINA = "5a1e0000-eeee-4a2b-9c3d-0000000000e1"


def semina_ordini():
    con = banco.con_db()
    adesso = int(time.time())
    for ordine, stato in ((ATTIVO, "in-progress"), (TORNATO, "in-progress"),
                          (VETRINA, "pending")):
        con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,"
                    "lato,maker,sats,euro,metodi) VALUES(?,?,?,?,'sell',1,"
                    "15000,'10,00 €','[\"SEPA\", \"Revolut\"]')",
                    (ordine, banco.VENDE, adesso - 3600, stato))
    # il «buy» girato: lo pubblica chi compra, lo prende chi vende
    con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,"
                "lato,maker,sats,euro,metodi) VALUES(?,?,?,'in-progress','buy',1,"
                "15000,'10,00 €','[\"SEPA\"]')",
                (MORTO, banco.COMPRA, adesso - 3600))
    # l'annullato di due mesi fa: fuori dallo storico. Nasce dal
    # database, che la rotta degli eventi non accetta un'ora cosi'
    # lontana (P2P_EVENTO_OROLOGIO_S)
    vecchio = adesso - 70 * 86400
    con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,"
                "lato,maker,euro) VALUES(?,?,?,'canceled','sell',1,'7,00 €')",
                (VECCHIO, banco.VENDE, vecchio))
    con.execute("INSERT OR REPLACE INTO p2p_scambi(ordine,compratore,venditore,"
                "preso_dal,giro,aggiornato,chiave_compratore,chiave_venditore) "
                "VALUES(?,?,?,'buyer',1,?,?,?)",
                (VECCHIO, banco.COMPRA, banco.VENDE, vecchio + 100,
                 banco.CHIAVE_COMPRA, banco.CHIAVE_VENDE))
    con.execute("INSERT OR IGNORE INTO p2p_momenti(ordine,momento,quando,fonte,"
                "giro,attore,dettaglio,arrivato) VALUES(?,'preso',?,'mostro',1,'buyer','',?)",
                (VECCHIO, vecchio + 50, vecchio + 50))
    con.execute("INSERT OR IGNORE INTO p2p_momenti(ordine,momento,quando,fonte,"
                "giro,attore,dettaglio,arrivato) VALUES(?,'annullato',?,'mostro',1,'seller','',?)",
                (VECCHIO, vecchio + 100, vecchio + 100))
    con.commit()
    con.close()


def scambi(chi):
    """La rotta vera, come la vede `chi`: `{ordine: {...}}` piu' il
    Cache-Control sotto `__cache`."""
    banco.come(chi)
    r = asyncio.run(banco.SRV.scambi_p2p())
    fuori = json.loads(r.body)
    fuori["__cache"] = r.headers.get("cache-control", "")
    return fuori


def voce(chi, ordine, *campi):
    s = scambi(chi).get("scambi", {}).get(ordine)
    if s is None:
        return None
    return [s.get(c) for c in campi] if campi else s


def main():
    banco.avvio()
    banco.semina()
    semina_ordini()
    prova = banco.prova
    t = int(time.time()) - 600
    V, C, E = banco.VENDE, banco.COMPRA, banco.ESTRANEO
    KV, KC = banco.CHIAVE_VENDE, banco.CHIAVE_COMPRA

    print("\n1) l'ordine in vetrina")
    prova("chi l'ha pubblicato lo vede «pubblicato», suo, mai preso, senza chiavi",
          ["pubblicato", "vendo", True, False, "", ""],
          voce(V, VETRINA, "stato", "lato", "mio", "preso", "chiave_mia", "chiave_peer"))
    prova("...con cifra, sats e metodi del libro", [10.0, 15000, ["SEPA", "Revolut"]],
          voce(V, VETRINA, "euro", "sats", "metodi"))
    prova("chi compra non lo vede", None, voce(C, VETRINA))
    prova("l'estraneo non vede niente di niente", {}, scambi(E)["scambi"])
    prova("la risposta e' no-store", "no-store", scambi(V)["__cache"])

    print("\n2) la presa di chi compra")
    banco.evento(ATTIVO, "taken", t + 10, "buyer", "take")
    prova("a chi compra: di' dove ricevere i sats", ["attesa_mia_fattura", "compro", False, True],
          voce(C, ATTIVO, "stato", "lato", "mio", "preso"))
    prova("a chi vende: aspetta la fattura", ["attesa_fattura_compratore", "vendo", True, True],
          voce(V, ATTIVO, "stato", "lato", "mio", "preso"))
    prova("le due trade key, ognuna sul suo lato", [[KV, KC], [KC, KV]],
          [voce(V, ATTIVO, "chiave_mia", "chiave_peer"), voce(C, ATTIVO, "chiave_mia", "chiave_peer")])
    con = banco.con_db()
    r = con.execute("SELECT chiave_compratore, chiave_venditore FROM p2p_scambi "
                    "WHERE ordine=?", (ATTIVO,)).fetchone()
    con.close()
    prova("...e stanno in p2p_scambi", [KC, KV], [r["chiave_compratore"], r["chiave_venditore"]])
    prova("l'estraneo continua a non vedere", None, voce(E, ATTIVO))

    print("\n3) la fattura, la garanzia")
    banco.evento(ATTIVO, "buyer-invoice-added", t + 20, "buyer", "hold-next")
    banco.evento(ATTIVO, "hold-invoice-requested", t + 20, "mostro", "invoice")
    prova("fattura data e garanzia chiesta insieme: chi vende blocca, chi compra aspetta",
          ["attesa_mia_hold", "attesa_hold_venditore"],
          [voce(V, ATTIVO, "stato")[0], voce(C, ATTIVO, "stato")[0]])
    banco.evento(ATTIVO, "hold-invoice-paid", t + 30, "seller")
    prova("garanzia pagata: attivo per tutt'e due, con l'ora di mostrod",
          [["attivo", t + 30], ["attivo", t + 30]],
          [voce(V, ATTIVO, "stato", "quando"), voce(C, ATTIVO, "stato", "quando")])
    prova("la cronaca viaggia intera", ["take", "hold-next", "invoice", ""],
          [voce(V, ATTIVO, "momenti")[0][0]["d"]] + [m["d"] for m in voce(V, ATTIVO, "momenti")[0][1:]])

    print("\n4) euro inviati, liberati, il pagamento che non passa, riuscito")
    banco.evento(ATTIVO, "fiat-sent", t + 40, "buyer")
    prova("euro inviati", ["euro_inviati", "euro_inviati"],
          [voce(V, ATTIVO, "stato")[0], voce(C, ATTIVO, "stato")[0]])
    banco.evento(ATTIVO, "released", t + 50, "seller", None,
                 sats=7300, sats_buyer=7228, sats_seller=7372)
    prova("liberati: in pagamento per tutt'e due", ["rilasciato", "rilasciato"],
          [voce(V, ATTIVO, "stato")[0], voce(C, ATTIVO, "stato")[0]])
    prova("...coi tre importi, ognuno il suo", [[7300, 7372], [7300, 7228]],
          [voce(V, ATTIVO, "sats_ordine", "sats_miei"), voce(C, ATTIVO, "sats_ordine", "sats_miei")])
    banco.evento(ATTIVO, "payout-failed", t + 60, "mostro", "NO_ROUTE")
    prova("pagamento non passato: a chi compra la fattura nuova, chi vende in pagamento — e il fatto lo leggono tutt'e due",
          [["fattura_nuova", True], ["rilasciato", True]],
          [voce(C, ATTIVO, "stato", "payout_fallito"), voce(V, ATTIVO, "stato", "payout_fallito")])
    banco.evento(ATTIVO, "buyer-invoice-added", t + 70, "buyer", "new-invoice")
    prova("la fattura nuova: di nuovo in pagamento, e chi vende non lo legge piu' fallito",
          [["rilasciato"], ["rilasciato", False]],
          [voce(C, ATTIVO, "stato"), voce(V, ATTIVO, "stato", "payout_fallito")])
    banco.evento(ATTIVO, "success", t + 80, "mostro", None,
                 sats=7300, sats_buyer=7228, sats_seller=7372)
    prova("riuscito: concluso per tutt'e due, datato al success",
          [["concluso", t + 80], ["concluso", t + 80]],
          [voce(V, ATTIVO, "stato", "quando"), voce(C, ATTIVO, "stato", "quando")])

    print("\n5) preso e poi tornato in vetrina")
    banco.evento(TORNATO, "taken", t + 100, "buyer", "take")
    prova("preso: chi compra e' una parte", "attesa_mia_fattura", voce(C, TORNATO, "stato")[0])
    banco.evento(TORNATO, "canceled", t + 110, "buyer", "republished", buyer=None)
    prova("tornato: chi ha pubblicato torna a «pubblicato», con l'ora del ritorno",
          ["pubblicato", True, t + 110], voce(V, TORNATO, "stato", "mio", "quando"))
    prova("...e chi aveva preso non e' piu' una parte: non lo vede", None, voce(C, TORNATO))
    prova("...ne' la chiave dell'altra parte resta a chi vende", "", voce(V, TORNATO, "chiave_peer")[0])

    print("\n6) preso e poi annullato: storico, non ritiro")
    banco.evento(MORTO, "taken", t + 200, "seller", "take")
    banco.evento(MORTO, "hold-invoice-requested", t + 200, "mostro", "take")
    prova("preso da chi vende (un buy girato): tocca a lui bloccare, e chi compra — che l'ha pubblicato — aspetta",
          [["attesa_mia_hold", "vendo", False], ["attesa_hold_venditore", "compro", True]],
          [voce(V, MORTO, "stato", "lato", "mio"), voce(C, MORTO, "stato", "lato", "mio")])
    banco.evento(MORTO, "canceled", t + 220, "buyer")
    prova("annullato per tutt'e due, e PRESO: e' storico, non un ritiro",
          [["annullato", True], ["annullato", True]],
          [voce(V, MORTO, "stato", "preso"), voce(C, MORTO, "stato", "preso")])

    print("\n7) lo storico e' di trenta giorni")
    prova("l'annullato di due mesi fa resta fuori, per tutt'e due", [None, None],
          [voce(V, VECCHIO), voce(C, VECCHIO)])
    miei = {ATTIVO, TORNATO, MORTO, VECCHIO, VETRINA}
    prova("chi vende vede quattro di questi scambi, chi compra due",
          [sorted([ATTIVO, MORTO, TORNATO, VETRINA]), sorted([ATTIVO, MORTO])],
          [sorted(o for o in scambi(V)["scambi"] if o in miei),
           sorted(o for o in scambi(C)["scambi"] if o in miei)])

    print("\n8) la leva non c'entra")
    banco.SRV.P2P_ATTIVO = False
    prova("a leva spenta la rotta risponde lo stesso: chi ha uno scambio a meta' lo vede",
          "concluso", voce(V, ATTIVO, "stato")[0])

    print(f"\n{banco.PASSATE} ok, {banco.FALLITE} NO")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
