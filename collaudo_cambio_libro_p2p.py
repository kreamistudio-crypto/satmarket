# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL CAMBIO DA SOLO (10 ott 2026, cantiere «cambio-libro-p2p»).

Il libro P2P fa le stime in sats degli ordini a mercato e i badge % di
quelli a sats fissi col cambio del bitcoin, e quel cambio arrivava solo
nella busta di prima pagina di `/api/listings`: chi restava sul libro lo
leggeva vecchio, anche tirando giu' per aggiornare. Adesso il client lo
chiede a `/api/cambio`, alla tirata e ogni minuto.

`prove.py` fa girare il CLIENT (la tirata, il battito, il ridisegno) con
un server di cartone; qui risponde il SERVER VERO, ed e' la domanda che
la' non si puo' fare:
- la rotta c'e', aperta a chi non ha una sessione, in sola GET;
- dice LO STESSO numero della busta della vetrina — una fonte, non due;
- segue la cache: cambia lei, cambia la risposta, senza un giro in mezzo
  (`no-store`);
- non bussa MAI a CoinGecko e non apre il database: e' una rotta aperta,
  e nemmeno con la cache piu' vecchia della sua soglia calda
  (`CAMBIO_TTL`) si mette a rileggere — che e' la differenza con
  `cambio_btc_eur`, quello delle invoice;
- un cambio troppo vecchio vale 0, «non disponibile», come nella busta.

NON TOCCA NIENTE DI VERO: il `config` finto lo installa `avvio()` del
banco, PRIMA dell'import di server. Nessuna rete (e la gabbia della CI
la segnerebbe).

USO:  python collaudo_cambio_libro_p2p.py
"""

import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
VIA = "/api/cambio"


def main():
    print("=" * 58)
    print("  IL CAMBIO DA SOLO — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    S = banco.SRV
    # senza `with`: gli startup non girano, quindi l'orologio del cambio
    # non parte e la cache la muove solo il collaudo
    c = TestClient(S.app)
    cache = S._cambio_cache

    # LE DUE SPIE: la rete (la lettura vera da CoinGecko) e il database
    bussate, aperture = [], []

    async def rileggi_spia():
        bussate.append(time.time())
        return False

    db_vero = S.db

    def db_spia(*a, **k):
        aperture.append(1)
        return db_vero(*a, **k)

    S._rileggi_cambio = rileggi_spia

    def metti(valore, eta_s=0):
        cache["valori"]["eur"] = float(valore)
        cache["quando"] = time.time() - eta_s
        cache["tentato"] = 0.0     # nessuna scusa per non riprovare

    print("\n[la rotta: aperta, in GET, col numero della cache]")
    metti(0)
    r = c.get(VIA)
    prova("senza cambio in mano risponde 200 con 0, «non disponibile»",
          [200, {"cambio_eur": 0.0}], [r.status_code, r.json()])
    metti(98765.5)
    r = c.get(VIA)
    prova("col cambio in cache dice quello, a chi non ha una sessione",
          [200, {"cambio_eur": 98765.5}], [r.status_code, r.json()])
    prova("...e non si tiene in nessuna cache", "no-store",
          r.headers.get("cache-control"))
    prova("...in sola GET: una POST e' 405", 405, c.post(VIA).status_code)

    print("\n[una fonte sola: la busta della vetrina dice lo stesso numero]")
    v = c.get("/api/listings?limit=20")
    prova("la prima pagina della vetrina risponde", 200, v.status_code)
    prova("...e il suo `cambio_eur` e' quello di /api/cambio",
          r.json()["cambio_eur"], v.json().get("cambio_eur"))

    print("\n[segue la cache, senza un giro in mezzo]")
    metti(101234.0)
    prova("cambia la cache, cambia la risposta alla domanda dopo",
          101234.0, c.get(VIA).json()["cambio_eur"])
    prova("...e la busta con lei", 101234.0,
          c.get("/api/listings?limit=20").json().get("cambio_eur"))
    prova("un parametro non le fa dire altro: non ne ha",
          101234.0, c.get(VIA + "?valuta=usd").json()["cambio_eur"])

    print("\n[mai la rete, mai il database]")
    del bussate[:]
    # piu' vecchio della soglia CALDA (quella a cui `cambio_btc_eur` va
    # a rileggere) ma ancora buono per la vetrina
    metti(99000.0, eta_s=S.CAMBIO_TTL + 600)
    S.db = db_spia
    try:
        letti = [c.get(VIA).json()["cambio_eur"] for _ in range(5)]
    finally:
        S.db = db_vero
    prova("cinque domande con la cache «fredda»: sempre l'ultimo noto",
          [99000.0] * 5, letti)
    prova("...e nessuna lettura da CoinGecko e' partita", 0, len(bussate))
    prova("...ne' si e' aperto il database", 0, len(aperture))
    # il controllo: la spia della rete funziona, e il percorso delle
    # invoice — che NON e' il nostro — li' ci passa davvero
    # (il banco ha messo un cambio finto al posto di `cambio_btc_eur`:
    # quello vero si rifa' dal sorgente del modulo, coi suoi globali)
    import asyncio
    import inspect
    testo = inspect.getsource(S)
    i = testo.index("async def cambio_btc_eur() -> float:")
    amb = {}
    exec(testo[i:testo.index("\n\n\n", i)], S.__dict__, amb)
    cambio_caldo = amb["cambio_btc_eur"]
    asyncio.run(cambio_caldo())
    prova("il controllo: sulla stessa cache il percorso delle invoice "
          "invece va a rileggere", 1, len(bussate))

    print("\n[troppo vecchio = non disponibile]")
    if S.ORE_CAMBIO_VALIDO:
        metti(99000.0, eta_s=S.ORE_CAMBIO_VALIDO * 3600 + 60)
        prova("oltre ORE_CAMBIO_VALIDO la rotta dice 0", 0.0,
              c.get(VIA).json()["cambio_eur"])
        prova("...come la busta", 0.0,
              c.get("/api/listings?limit=20").json().get("cambio_eur"))
        metti(99000.0, eta_s=S.ORE_CAMBIO_VALIDO * 3600 - 60)
        prova("...e un minuto prima del filo lo dice ancora", 99000.0,
              c.get(VIA).json()["cambio_eur"])
    else:
        print("    (ORE_CAMBIO_VALIDO a 0: il cambio non scade mai)")

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
