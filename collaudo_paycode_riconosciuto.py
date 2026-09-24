# -*- coding: utf-8 -*-
"""
IL PAYCODE NON PARTE VERSO CHI NON RICONOSCIAMO, SUL SERVER VERO (24 set 2026).

Alla presa di un PayCode il telefono di chi vende manda da solo, cifrati,
PayCode, importo e scadenza verso la chiave di chi ha preso — chiunque
sia. Un ordine del nostro coordinatore lo puo' prendere anche un client
Mostro esterno. La patch al nodo (0008) non si fa: la cura e' dal lato
nostro, e comincia con una domanda al server PRIMA dell'invio:
`/api/p2p/parte-riconosciuta` — «la chiave a cui sto per scrivere e'
l'altra parte di questo scambio come l'ha detta mostrod, e la
riconoscete?».

`prove.py` difende il giudice estratto e il client (`prove_paycode_
riconosciuto`). Qui gira la ROTTA VERA, sul database vero e usa-e-getta,
con gli eventi di mostrod passati dalla rotta degli eventi:

  1. prima che mostrod parli: «ignoto» — e l'ordine che il server non
     conosce affatto e' lo stesso «ignoto», non un errore;
  2. la presa di chi compra, dei nostri: «riconosciuta» dai due lati;
  3. la presa da una chiave che non e' di nessuno dei nostri (un client
     esterno): «esterno»;
  4. un estraneo che chiede: «estraneo», anche a chiave giusta;
  5. una chiave nostra ma non dell'altra parte: «diversa»;
  6. le due forme: 400 a chi le sbaglia;
  7. il ritiro di chi aveva preso: le parti tornano quelle del libro e
     la domanda torna «esterno» per quella chiave (l'ordine non e' piu'
     preso) — e il client, che a ordine tornato in vetrina non ha piu'
     un peer, non la fa nemmeno.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore.

USO:  python collaudo_paycode_riconosciuto.py
"""

import sys
import time

import collaudo_pagamento_p2p as banco

NOSTRO = "5a1e0000-aaaa-4a2b-9c3d-00000000000a"
ESTERNO = "5a1e0000-bbbb-4a2b-9c3d-00000000000b"
MAI_VISTO = "5a1e0000-cccc-4a2b-9c3d-00000000000c"
CHIAVE_ALTRUI = "c3" * 32     # nessuno dei nostri: un altro client
CHIAVE_TERZO = "d4" * 32      # di un nostro utente estraneo allo scambio


def semina_ordini():
    con = banco.con_db()
    adesso = int(time.time())
    for ordine in (NOSTRO, ESTERNO):
        con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,"
                    "maker,sats,euro,metodi) VALUES(?,?,?,'pending','sell',1,"
                    "15000,'10,00 €','[\"Contanti al tabacchino 10.00\"]')",
                    (ordine, banco.VENDE, adesso))
    con.execute("INSERT OR REPLACE INTO chiavi_p2p(pubkey, tg_id, creato) "
                "VALUES(?,?,?)", (CHIAVE_TERZO, banco.ESTRANEO, adesso))
    con.commit()
    con.close()


def chiedi(chi, ordine, chiave):
    banco.come(chi)
    return banco.esito(banco.SRV.parte_riconosciuta_p2p,
                       {"ordine": ordine, "chiave": chiave})


def main():
    banco.avvio()
    banco.semina()
    semina_ordini()
    prova = banco.prova
    t0 = int(time.time()) - 300
    NO = {"riconosciuta": False}

    print("\n1) prima che mostrod parli")
    prova("l'ordine in vetrina: ignoto", dict(NO, motivo="ignoto"),
          chiedi(banco.VENDE, NOSTRO, banco.CHIAVE_COMPRA))
    prova("un ordine che il server non conosce: ignoto, non un errore",
          dict(NO, motivo="ignoto"),
          chiedi(banco.VENDE, MAI_VISTO, banco.CHIAVE_COMPRA))

    print("\n2) la presa di chi compra, dei nostri")
    fatto = banco.evento(NOSTRO, "taken", t0, attore="buyer",
                         dettaglio="invoice-next")
    prova("la presa si registra con le due parti", (banco.COMPRA, banco.VENDE),
          ((fatto or {}).get("compratore"), (fatto or {}).get("venditore")))
    prova("chi vende chiede della chiave di chi compra: riconosciuta",
          {"riconosciuta": True, "motivo": "riconosciuta"},
          chiedi(banco.VENDE, NOSTRO, banco.CHIAVE_COMPRA))
    prova("...e chi compra della chiave di chi vende: riconosciuta",
          {"riconosciuta": True, "motivo": "riconosciuta"},
          chiedi(banco.COMPRA, NOSTRO, banco.CHIAVE_VENDE))
    prova("...anche con la chiave in maiuscolo",
          {"riconosciuta": True, "motivo": "riconosciuta"},
          chiedi(banco.VENDE, NOSTRO, banco.CHIAVE_COMPRA.upper()))

    print("\n3) la presa da un client esterno")
    fatto = banco.evento(ESTERNO, "taken", t0 + 10, attore="buyer",
                         dettaglio="invoice-next", buyer=CHIAVE_ALTRUI)
    prova("mostrod nomina una chiave che non e' di nessuno dei nostri",
          (0, banco.VENDE),
          ((fatto or {}).get("compratore"), (fatto or {}).get("venditore")))
    prova("chi vende chiede di quella chiave: esterno", dict(NO, motivo="esterno"),
          chiedi(banco.VENDE, ESTERNO, CHIAVE_ALTRUI))
    prova("...esterno anche se il telefono portasse una chiave nostra",
          dict(NO, motivo="esterno"),
          chiedi(banco.VENDE, ESTERNO, banco.CHIAVE_COMPRA))

    print("\n4) un estraneo")
    prova("chi non e' una delle due parti: estraneo", dict(NO, motivo="estraneo"),
          chiedi(banco.ESTRANEO, NOSTRO, banco.CHIAVE_COMPRA))
    prova("...anche con la chiave di chi vende", dict(NO, motivo="estraneo"),
          chiedi(banco.ESTRANEO, NOSTRO, banco.CHIAVE_VENDE))

    print("\n5) una chiave nostra ma non dell'altra parte")
    prova("la chiave di un terzo nostro sullo scambio preso: diversa",
          dict(NO, motivo="diversa"),
          chiedi(banco.VENDE, NOSTRO, CHIAVE_TERZO))
    prova("...e una chiave di nessuno su uno scambio fra nostri: diversa",
          dict(NO, motivo="diversa"),
          chiedi(banco.VENDE, NOSTRO, CHIAVE_ALTRUI))

    print("\n6) le due forme")
    prova("chiave corta: 400", (400, "Chiave in una forma sconosciuta"),
          chiedi(banco.VENDE, NOSTRO, "abcd"))
    prova("chiave mancante: 400", (400, "Chiave in una forma sconosciuta"),
          chiedi(banco.VENDE, NOSTRO, None))
    prova("ordine storto: 400", (400, "Ordine in una forma sconosciuta"),
          chiedi(banco.VENDE, "ord;drop", banco.CHIAVE_COMPRA))
    prova("ordine mancante: 400", (400, "Ordine in una forma sconosciuta"),
          chiedi(banco.VENDE, None, banco.CHIAVE_COMPRA))

    print("\n7) il ritiro di chi aveva preso")
    banco.evento(NOSTRO, "canceled", t0 + 60, attore="buyer",
                 dettaglio="republished", buyer=None)
    prova("le parti tornano quelle del libro: nessuno ha preso",
          dict(NO, motivo="esterno"),
          chiedi(banco.VENDE, NOSTRO, banco.CHIAVE_COMPRA))
    # e una nuova presa, dei nostri, rimette il si'
    banco.evento(NOSTRO, "taken", t0 + 120, attore="buyer",
                 dettaglio="invoice-next")
    prova("...e una presa nuova, dei nostri, rimette il si'",
          {"riconosciuta": True, "motivo": "riconosciuta"},
          chiedi(banco.VENDE, NOSTRO, banco.CHIAVE_COMPRA))

    print(f"\n{banco.PASSATE} passate, {banco.FALLITE} fallite")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
