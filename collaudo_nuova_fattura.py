# -*- coding: utf-8 -*-
"""
IL COLLAUDO DI «PAGA ORA» (24 set 2026, dal campo — l'ordine #196).

Il compratore chiudeva per sbaglio il foglio del pagamento senza
pagare; riaprendo l'ordine trovava il solo «Ho pagato la invoice —
verifica», e nessun modo di rivedere la fattura: alla scadenza
l'ordine si annullava in silenzio. La cura ha due meta':
  • la fattura VIVA la riapre il client da solo — viaggia gia' nella
    riga di /api/orders, e qui si guarda che ci sia davvero, la stessa;
  • la fattura MORTA si rigenera con `POST /api/orders/{id}/nuova-
    fattura`: stesso importo, stessa riga, una volta sola, e UNA sola
    fattura viva per ordine.

`prove.py` fa girare la rotta estratta su un database di cartone; qui
gira il SERVER VERO — le rotte HTTP di FastAPI, lo schema vero con la
colonna nuova, `compra` con la sua ripresa, l'orologio vero — su un
database usa-e-getta. Di finto c'e' solo LNbits: conia bolt11
sintatticamente vere (`bolt11_finta`, con la scadenza dentro come
quelle di LNbits) e dice «pagata» solo agli hash che il collaudo paga.

  1. l'ordine nasce, e la sua fattura sta nella riga della lista, uguale;
  2. a fattura viva la rotta RIPRESENTA quella, e non conia niente;
  3. a fattura morta ne conia UNA sulla stessa riga: stesso importo,
     stesso numero d'ordine, la prenotazione dello stock intatta;
  4. l'orologio non la tocca, e la ripresa di `compra` la riconosce;
  5. pagata la NUOVA, la verifica chiude l'ordine;
  6. una seconda rigenerazione non c'e'; e l'orologio, a fattura morta,
     mette la lapide come sempre;
  7. la vecchia pagata all'ultimo secondo si incassa invece di rifarla;
  8. LNbits muto: 503, e non si conia niente.

NON TOCCA NIENTE DI VERO: il `config` finto lo installa `avvio()` del
banco, PRIMA dell'import di server. Nessuna rete, nessuna chiave.

USO:  python collaudo_nuova_fattura.py
"""

import asyncio
import sys
import time

import collaudo_lnbits_muto as banco
from prove import bolt11_finta

prova = banco.prova
CONII = []          # (sats, memo, cassaforte) di ogni fattura coniata
CHIESTE = []        # gli hash chiesti a LNbits
PAGATE = set()      # gli hash che il «wallet» ha pagato
LNBITS = {"muto": False}


def invecchia(oid, secondi):
    """Il tempo passa senza aspettarlo: si spostano INDIETRO la nascita
    dell'ordine e quella scritta dentro la sua bolt11 — che e' da li'
    che la scadenza si legge —, come ha fatto il tempo."""
    con = banco.SRV.db()
    o = con.execute("SELECT invoice, prezzo_sats, creato FROM ordini "
                    "WHERE id=?", (oid,)).fetchone()
    letta = banco.SRV.leggi_bolt11(o["invoice"], con_hash=True)
    nuova = bolt11_finta(o["prezzo_sats"], letta["scadenza"],
                         letta["quando"] - secondi,
                         phash=int(letta["hash"] or "0", 16))
    con.execute("UPDATE ordini SET invoice=?, creato=? WHERE id=?",
                (nuova, o["creato"] - secondi, oid))
    con.commit()
    con.close()


def main():
    print("=" * 58)
    print("  «PAGA ORA» — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    from fastapi.testclient import TestClient

    async def conia(sats, memo, expiry=SRV.INVOICE_EXPIRY, cassaforte=""):
        CONII.append((sats, memo, cassaforte))
        n = len(CONII)
        return {"payment_request": bolt11_finta(sats, expiry,
                                                int(time.time()), phash=n),
                "payment_hash": f"hash-{n}", "cassaforte": cassaforte}

    async def pagata(h, cassaforte):
        CHIESTE.append((h, cassaforte))
        if LNBITS["muto"]:
            raise RuntimeError("LNbits non risponde")
        return h in PAGATE

    SRV.crea_invoice_escrow = conia
    SRV.invoice_pagata = pagata
    # l'ultimo pezzo venduto annuncia il «sold» su Nostr e sul canale:
    # qui non esce niente, e il banco non deve nemmeno provarci
    async def zitto(*a, **k):
        return None
    SRV.annuncio_su_nostr = zitto
    SRV.promo_venduto = zitto
    c = TestClient(SRV.app)

    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    for tg, nome in ((222, "Vende"), (111, "Compra"), (333, "Altro")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato) VALUES(?,?,?,1)", (tg, nome, f"neg{tg}"))
    ann = []
    for n in range(3):
        # un pezzo solo per annuncio: la prenotazione si vede subito
        ann.append(con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(222,?,'una cosa',25000,'Altro','Pavia (PV)','attivo',1,"
            "'ritiro',1,'sats','nuovo')", (f"Pesto {n}",)).lastrowid)
    con.commit()
    con.close()

    def riga(oid):
        con = SRV.db()
        r = dict(con.execute("SELECT * FROM ordini WHERE id=?",
                             (oid,)).fetchone())
        con.close()
        return r

    def compra(annuncio, tg=111):
        banco.come(tg)
        return c.post("/api/orders", json={"annuncio_id": annuncio,
                                           "consegna": "ritiro"})

    def nuova(oid, tg=111):
        banco.come(tg)
        return c.post(f"/api/orders/{oid}/nuova-fattura")

    # ---- 1) l'ordine nasce, e la fattura sta nella riga ------------
    print("\n[la fattura viaggia nella riga dell'ordine]")
    r = compra(ann[0])
    prova("l'ordine nasce 'creato' con la sua fattura", 200, r.status_code)
    d = r.json()
    oid, prima = d["ordine_id"], d["invoice"]
    banco.come(111)
    lista = {o["id"]: o for o in c.get("/api/orders").json()}
    prova("nella lista c'e' LA STESSA fattura: il client la riapre da li'",
          (prima, "creato", 0),
          (lista[oid].get("invoice"), lista[oid]["stato"],
           lista[oid].get("fattura_rinnovata_il")))

    # ---- 2) fattura viva: si ripresenta quella ---------------------
    print("\n[fattura viva: la stessa, e niente conio]")
    n0 = len(CONII)
    r = nuova(oid)
    prova("la rotta risponde con la STESSA fattura, dichiarata non nuova",
          (200, prima, False), (r.status_code, r.json().get("invoice"),
                                r.json().get("nuova")))
    prova("...e non ne conia un'altra, ne' chiede niente a LNbits",
          (n0, 0), (len(CONII), len(CHIESTE)))

    # ---- 3) fattura morta: una nuova sulla stessa riga -------------
    print("\n[fattura morta: una nuova, stesso importo, stesso ordine]")
    invecchia(oid, 1000)
    vecchio = riga(oid)
    r = nuova(oid)
    d = r.json()
    dopo = riga(oid)
    prova("la rotta conia UNA fattura nuova", (200, True, n0 + 1),
          (r.status_code, d.get("nuova"), len(CONII)))
    prova("...per lo STESSO importo, e col memo nostro",
          (25000, True), (CONII[-1][0],
                          CONII[-1][1].startswith(f"Barattolo escrow #{ann[0]}:")))
    prova("...dopo aver chiesto a LNbits della vecchia",
          [(vecchio["payment_hash"], vecchio["cassaforte"])], CHIESTE)
    prova("...sulla STESSA riga: numero, stato e importo fermi",
          (oid, "creato", 25000), (dopo["id"], dopo["stato"],
                                   dopo["prezzo_sats"]))
    prova("...con fattura e hash nuovi, e la nascita rinfrescata",
          (d.get("invoice"), f"hash-{len(CONII)}", True, True),
          (dopo["invoice"], dopo["payment_hash"],
           dopo["creato"] > vecchio["creato"],
           dopo["fattura_rinnovata_il"] > 0))
    prova("...e la scadenza detta e' quella dentro la bolt11 nuova",
          SRV.leggi_bolt11(d["invoice"])["scade"], d.get("scade_il"))
    # la prenotazione non si e' mossa: un altro non lo compra
    r = compra(ann[0], tg=333)
    prova("il pezzo resta prenotato a chi l'ha ordinato", 409, r.status_code)
    # UNA fattura viva per ordine: chiedere di nuovo ripresenta questa
    n1 = len(CONII)
    r = nuova(oid)
    prova("chiedere ancora ripresenta LA NUOVA, e non ne conia una terza",
          (dopo["invoice"], False, n1),
          (r.json().get("invoice"), r.json().get("nuova"), len(CONII)))

    # ---- 4) l'orologio e la ripresa --------------------------------
    print("\n[l'orologio non la tocca, la ripresa la riconosce]")
    asyncio.run(SRV.controlla_abbandonati())
    prova("l'orologio lascia 'creato' l'ordine con la fattura appena nata",
          ("creato", dopo["invoice"]), (riga(oid)["stato"],
                                        riga(oid)["invoice"]))
    r = compra(ann[0])
    prova("«Acquista» di nuovo ritrova la stessa fattura, sullo stesso "
          "ordine (niente gemelli)", (oid, dopo["invoice"], True),
          (r.json().get("ordine_id"), r.json().get("invoice"),
           r.json().get("ripresa")))

    # ---- 5) pagata la nuova, l'ordine si chiude --------------------
    print("\n[pagata la nuova: la verifica chiude l'ordine]")
    PAGATE.add(dopo["payment_hash"])
    banco.come(111)
    r = c.post(f"/api/orders/{oid}/verifica-pagamento")
    prova("la verifica vede il pagamento della fattura NUOVA", "locked",
          r.json().get("stato"))
    prova("...e l'ordine e' andato avanti", "locked", riga(oid)["stato"])

    # ---- 6) una volta sola, e l'orologio a fattura morta -----------
    print("\n[una volta sola; e a fattura morta l'orologio chiude]")
    r = compra(ann[1])
    oid2 = r.json()["ordine_id"]
    invecchia(oid2, 1000)
    prova("la prima rigenerazione passa", True, nuova(oid2).json().get("nuova"))
    invecchia(oid2, 1000)
    n2 = len(CONII)
    r = nuova(oid2)
    prova("la seconda no: 400, e dice di ricomprare dall'annuncio",
          (400, True, n2), (r.status_code,
                            "ricompralo dall'annuncio" in r.json().get("detail", ""),
                            len(CONII)))
    asyncio.run(SRV.controlla_abbandonati())
    prova("a fattura morta l'orologio mette la lapide, come sempre",
          "annullato", riga(oid2)["stato"])
    r = nuova(oid2)
    prova("...e dopo la lapide la rotta non resuscita niente", 400,
          r.status_code)

    # ---- 7) la vecchia pagata all'ultimo secondo -------------------
    print("\n[la vecchia pagata all'ultimo secondo: si incassa]")
    r = compra(ann[2])
    oid3 = r.json()["ordine_id"]
    invecchia(oid3, 1000)
    PAGATE.add(riga(oid3)["payment_hash"])
    n3, fattura3 = len(CONII), riga(oid3)["invoice"]
    r = nuova(oid3)
    prova("niente fattura nuova: l'ordine si incassa",
          ("locked", n3, fattura3),
          (r.json().get("stato"), len(CONII), riga(oid3)["invoice"]))
    prova("...ed e' andato avanti davvero", "locked", riga(oid3)["stato"])

    # ---- 8) LNbits muto --------------------------------------------
    print("\n[LNbits muto: niente conio]")
    con = SRV.db()
    ann4 = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
        " VALUES(222,'Pesto 4','una cosa',25000,'Altro','Pavia (PV)',"
        "'attivo',1,'ritiro',1,'sats','nuovo')").lastrowid
    con.commit()
    con.close()
    oid4 = compra(ann4).json()["ordine_id"]
    invecchia(oid4, 1000)
    LNBITS["muto"] = True
    n4, fattura4 = len(CONII), riga(oid4)["invoice"]
    r = nuova(oid4)
    LNBITS["muto"] = False
    prova("LNbits muto: 503, nessuna fattura, la riga ferma",
          (503, n4, fattura4, "creato"),
          (r.status_code, len(CONII), riga(oid4)["invoice"],
           riga(oid4)["stato"]))
    prova("...e la rotta non e' di nessun altro: chi non ha comprato "
          "prende il 400", 400, nuova(oid4, tg=333).status_code)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
