# -*- coding: utf-8 -*-
"""
CHI E' L'ALTRO, SUL SERVER VERO (12 ott 2026, cantiere chi-e-l-altro,
decisione di Andrea, dal caso ea0af71a).

La regola: chi scambia DA Barattolo e' riconosciuto dalla controparte
con qualunque login (Telegram, nsec, bunker, estensione — per il server
sono due famiglie: id positivo e id negativo, il firmatario non lo vede);
«Fatti riconoscere» e' USCITO (decisione con Alan): per l'anonimato una
chiave Nostr nuova; chi scambia da un'altra app Mostro resta sconosciuto
e si dice quello; gli scambi di prima non si toccano; a chi aveva il
vecchio default un avviso una tantum.

Qui girano le ROTTE VERE sul database usa-e-getta: la presa dichiarata
dal telefono di chi prende (`/api/p2p/ordini` con `presi`), gli eventi
di mostrod (patch 0007), la controparte (`/api/p2p/controparte`), la
recensibilita' (`/api/p2p/recensibile`), l'interruttore
che non c'e' piu', `/api/me` e l'avviso letto.

  1. le quattro coppie di login: chi vende Telegram o nativo, chi compra
     Telegram o nativo — ognuno vede il VOLTO dell'altro, e a scambio
     concluso la recensione ha un posto nei due versi;
  2. l'interruttore non esiste piu': la rotta e' uscita, il giudice dice
     si' a tutti (per l'anonimato c'e' una chiave Nostr nuova);
  3. lo scambio di PRIMA (la presa mai annotata, il nativo col vecchio
     default): «anonimo_prima», il passato non si tocca;
  4. un altro client Mostro: la chiave non e' di nessuno dei nostri —
     «esterno», e la recensione dice quello;
  5. mostrod che non ha ancora detto niente: nessun motivo, nessun volto;
  6. nessun avviso una tantum (nato e tolto il 12 ott 2026, decisione di
     Andrea: la regola sta nel patto «I tuoi dati»): /api/me dice il
     riconoscimento DERIVATO (acceso con la colonna di ieri a zero), non
     porta `avviso_riconosci`, e la rotta «Ho capito» non esiste.

NON TOCCA NIENTE DI VERO: config di cartone, niente Telegram, niente
relay, niente coordinatore.

USO:  python collaudo_chi_e_l_altro.py
"""

import asyncio
import json
import os
import sys
import time

import collaudo_pagamento_p2p as banco

TG_V, TG_C = banco.VENDE, banco.COMPRA           # 111, 222: due Telegram
NA_V, NA_C = -701, -702                           # due nativi Nostr (nsec/bunker/estensione: per il server uguali)
NA_PRIMA = -704                                   # un nativo col vecchio default, mai avvisato
K = {TG_V: "c1" * 32, TG_C: "c2" * 32, NA_V: "d1" * 32, NA_C: "d2" * 32,
     NA_PRIMA: "d4" * 32}
K_EST = "ee" * 32                                 # la chiave di un altro client Mostro
ORD = lambda n: f"5a1e0000-7071-4a2b-9c3d-00000000{n:04x}"


def semina():
    con = banco.con_db()
    adesso = int(time.time())
    for tg, nome in ((NA_V, "Nativo V"), (NA_C, "Nativo C"), (NA_PRIMA, "Nativo di prima")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,ln_address,npub,npub_verificata) "
                    "VALUES(?,?,?,1,'',?,1)", (tg, nome, f"neg{abs(tg)}", f"npub1x{abs(tg)}"))
    for tg, k in K.items():
        con.execute("INSERT OR REPLACE INTO chiavi_p2p(pubkey, tg_id, creato) VALUES(?,?,?)", (k, tg, adesso))
    con.commit()
    con.close()


def pubblica(ordine, maker, lato="sell"):
    con = banco.con_db()
    con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,visto,preso_da,euro) "
                "VALUES(?,?,?,'pending',?,1,?,0,'10,00 €')", (ordine, maker, int(time.time()), lato, int(time.time())))
    con.commit()
    con.close()


def prende(ordine, taker, dichiara=True):
    """Il telefono di chi prende dichiara la presa (rotta vera), se
    `dichiara`; poi mostrod la racconta con le due trade key."""
    if dichiara:
        banco.come(taker)
        banco.esito(banco.SRV.registra_ordini_p2p, {"ordini": [ordine], "presi": True})


def mostrod(ordine, maker, taker, t, taker_key=None, fino="attivo"):
    kb = taker_key or K.get(taker, "")
    banco.evento(ordine, "taken", t + 10, "buyer", "take", buyer=kb, seller=K[maker])
    if fino in ("attivo", "concluso"):
        banco.evento(ordine, "buyer-invoice-added", t + 20, "buyer", "hold-next", buyer=kb, seller=K[maker])
        banco.evento(ordine, "hold-invoice-requested", t + 20, "mostro", "invoice", buyer=kb, seller=K[maker])
        banco.evento(ordine, "hold-invoice-paid", t + 30, "seller", buyer=kb, seller=K[maker])
    if fino == "concluso":
        banco.evento(ordine, "fiat-sent", t + 40, "buyer", buyer=kb, seller=K[maker])
        banco.evento(ordine, "released", t + 50, "seller", None, buyer=kb, seller=K[maker],
                     sats=7300, sats_buyer=7228, sats_seller=7372)
        banco.evento(ordine, "success", t + 60, "mostro", None, buyer=kb, seller=K[maker],
                     sats=7300, sats_buyer=7228, sats_seller=7372)


def controparte(chi, ordine):
    banco.come(chi)
    r = banco.esito(banco.SRV.controparte_p2p, {"ordini": [ordine]})
    if not isinstance(r, dict):
        return ("ERRORE", r)
    v = (r.get("controparti") or {}).get(ordine)
    return (v["nome"] if v else None, (r.get("motivi") or {}).get(ordine, ""))


def recensibile(chi, ordine):
    banco.come(chi)
    r = banco.esito(banco.SRV.recensibile_p2p, {"ordine": ordine})
    return (r.get("si"), r.get("motivo", "")) if isinstance(r, dict) else ("ERRORE", r)


def me(chi):
    banco.come(chi)
    r = asyncio.run(banco.SRV.mio_profilo())
    d = r if isinstance(r, dict) else json.loads(r.body)
    return d


def main():
    banco.avvio()
    banco.semina()
    semina()
    prova = banco.prova
    SRV = banco.SRV
    SRV.P2P_ATTIVO = True
    SRV.MOSTRO_HEX = "cd" * 32
    SRV.MOSTRO_RELAY = ["ws://127.0.0.1:9"]
    SRV.P2P_PROVA_IDS = []
    t = int(time.time()) - 900
    n = 0

    print("\n1) le quattro coppie di login: ognuno vede l'altro, e a fine scambio la recensione ha un posto")
    for maker, taker, nome in ((TG_V, TG_C, "Telegram vende, Telegram compra"),
                               (TG_V, NA_C, "Telegram vende, nativo compra (il caso ea0af71a, oggi)"),
                               (NA_V, TG_C, "nativo vende, Telegram compra"),
                               (NA_V, NA_C, "nativo vende, nativo compra")):
        n += 1
        o = ORD(n)
        pubblica(o, maker)
        prende(o, taker)
        mostrod(o, maker, taker, t + n * 100, fino="concluso")
        prova(f"[{nome}] chi vende vede il VOLTO di chi compra, e chi compra quello di chi vende",
              [True, "", True, ""],
              [bool(controparte(maker, o)[0]), controparte(maker, o)[1], bool(controparte(taker, o)[0]), controparte(taker, o)[1]])
        prova(f"[{nome}] ...e a scambio concluso la recensione ha un posto nei due versi",
              [(True, ""), (True, "")], [recensibile(maker, o), recensibile(taker, o)])

    print("\n2) l'interruttore non esiste piu'")
    prova("la rotta «riconoscimi» e' uscita dal server", False, hasattr(SRV, "scegli_riconoscimi_p2p"))
    con = banco.con_db()
    giudizi = [SRV._p2p_riconosciuto(con, TG_V), SRV._p2p_riconosciuto(con, NA_PRIMA)]
    con.close()
    prova("...e il giudice dice si' a tutti, anche a un nativo col vecchio zero", [True, True], giudizi)

    print("\n3) lo scambio di PRIMA: la presa mai annotata, il nativo col vecchio default")
    n += 1
    o = ORD(n)
    pubblica(o, TG_V)
    prende(o, NA_PRIMA, dichiara=False)          # com'era: la presa del nativo non si annotava
    mostrod(o, TG_V, NA_PRIMA, t + n * 100, fino="concluso")
    prova("chi vende legge «anonimo_prima»: su Barattolo, ma lo scambio e' di prima della regola",
          (None, "anonimo_prima"), controparte(TG_V, o))
    prova("...e la recensione dice quel motivo, non «non ha un profilo»", (False, "anonimo_prima"), recensibile(TG_V, o))
    # il nativo di prima vede chi ha pubblicato: che sia l'altra parte lo dice
    # mostrod, e quel volto sta gia' sulla card del libro
    prova("...mentre il nativo di prima vede chi vende (il volto gia' pubblico della card)",
          [True, ""], [bool(controparte(NA_PRIMA, o)[0]), controparte(NA_PRIMA, o)[1]])

    print("\n4) un altro client Mostro: la chiave non e' di nessuno dei nostri")
    n += 1
    o = ORD(n)
    pubblica(o, TG_V)
    mostrod(o, TG_V, 0, t + n * 100, taker_key=K_EST, fino="concluso")
    prova("chi vende legge «esterno»: scambia da un'altra app", (None, "esterno"), controparte(TG_V, o))
    prova("...e la recensione dice «esterno»", (False, "esterno"), recensibile(TG_V, o))

    print("\n5) mostrod che non ha ancora detto niente")
    n += 1
    o = ORD(n)
    pubblica(o, TG_V)
    prova("nessun volto e nessun motivo: la pagina dira' «non lo sappiamo ancora»", (None, ""), controparte(TG_V, o))

    print("\n6) il riconoscimento derivato in /api/me, e nessun avviso una tantum")
    d = me(NA_PRIMA)
    prova("al nativo col vecchio default: riconosciuto (derivato), e nessun avviso da mostrare",
          [1, False], [d.get("riconosci_p2p"), "avviso_riconosci" in d])
    prova("a chi entra da Telegram: riconosciuto, nessun avviso", [1, False],
          [me(TG_V).get("riconosci_p2p"), "avviso_riconosci" in me(TG_V)])
    prova("la rotta «Ho capito» non esiste", False, hasattr(SRV, "avviso_riconosci_visto"))
    # il nativo col vecchio default prende: ora e' riconosciuto, senza avvisi
    n += 1
    o = ORD(n)
    pubblica(o, TG_V)
    prende(o, NA_PRIMA)
    mostrod(o, TG_V, NA_PRIMA, t + n * 100, fino="attivo")
    prova("...e da ora la sua presa si annota: chi vende lo vede", True, bool(controparte(TG_V, o)[0]))

    print(f"\n{banco.PASSATE} ok, {banco.FALLITE} NO")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
