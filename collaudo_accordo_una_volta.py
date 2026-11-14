# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'ACCORDO CHE VALE UNA VOLTA, E NELLA SUA VALUTA (14 nov
2026, cantiere audit-offerte, dal primo audit di sicurezza).

`prove.py` (`prove_accordo_una_volta`) prova i pezzi estratti; qui gira
il SERVER VERO — l'offerta vera, l'accettazione vera, la cassa vera
(`compra`), il preventivo, l'annullo, il riacciuffo
(`controlla_annullati`), il rimborso — su un database usa-e-getta. Di
finto c'e' solo il nodo (il LNbits di cartone di `collaudo_lnbits_muto`),
la fattura coniata dal Lightning address, le due piazze e il cambio,
che qui e' un numero scritto: 1 euro = 1000 sats.

  1. L'ACCORDO IN SATS, L'ANNUNCIO PASSA AGLI EURO: si paga la cifra
     pattuita (sul codice di prima: 1 sat al pezzo).
  2. L'ACCORDO IN EURO, L'ANNUNCIO PASSA AI SATS: la cifra pattuita al
     cambio (sul codice di prima: zero); senza cambio, 503 e nessun
     ordine.
  3. A VALUTE UGUALI non cambia niente: l'accordo di sempre.
  4. ANNULLA, RICOMPRA CON LA STESSA OFFERTA, PAGA TUTTE E DUE: una
     vendita sola, l'altra fattura torna indietro (sul codice di
     prima: due ordini alla cifra pattuita).
  5. ...NELL'ALTRO ORDINE: il riacciuffo passa prima che la fattura
     nuova sia pagata. Una vendita sola lo stesso.
  6. ANNULLA, PAGA LA VECCHIA, POI RIPROVA CON LA STESSA OFFERTA: il
     saldo tardivo e' una vendita come sempre, e l'offerta e' conclusa
     (sul codice di prima restava buona per un secondo ordine).
  7. I GESTI DI SEMPRE: annulla e ricompra con l'offerta pagando solo la
     nuova; e un ordine SENZA offerta annullato e pagato, col pezzo in
     vetrina, resta un acquisto.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server (lo fa `avvio()` del banco). Nessuna rete.

USO:  python collaudo_accordo_una_volta.py
"""

import asyncio
import sys
import time
import traceback

import collaudo_lnbits_muto as banco
from prove import bolt11_finta

prova = banco.prova
SRV = None
ANNA, VENDE = 111, 222
CAMBIO = 100_000.0      # euro per bitcoin: 1 euro = 1000 sats
CONIATE = []            # (address, sats) di ogni fattura di rimborso
FATTURE = {}            # payment_hash -> sats della fattura d'ingresso


# ------------------------------------------------------------ attrezzi
def db_esegui(sql, *args):
    con = SRV.db()
    con.execute(sql, args)
    con.commit()
    con.close()


def db_uno(sql, *args):
    con = SRV.db()
    r = con.execute(sql, args).fetchone()
    con.close()
    return r


ORA = [CAMBIO]          # il cambio che il server riceve quando lo chiede


def cambio(valore=CAMBIO):
    """Il cambio che risponde al server: un numero scritto. A zero e'
    la fonte muta."""
    ORA[0] = valore


def nuovo_annuncio(titolo, valuta="sats", sats=100_000, eur=0.0, quantita=3):
    con = SRV.db()
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "prezzo_eur,categoria,zona,stato,creato,consegna,quantita,"
        "quantita_max,valuta,condizione,foto) VALUES(?,?,'una cosa',?,?,"
        "'Altro','Pavia (PV)','attivo',1,'ritiro',?,?,?,'nuovo',"
        "'[\"cosa.jpg\"]')",
        (VENDE, titolo, sats, eur, quantita, quantita, valuta))
    con.commit()
    aid = cur.lastrowid
    con.close()
    return aid


def passa_a(aid, valuta, sats=0, eur=0.0):
    """Chi vende cambia la valuta dell'annuncio. Si scrive la colonna,
    come fanno la sincronizzazione dell'import Nostr e la modifica
    firmata, che le offerte non le guardano affatto."""
    db_esegui("UPDATE annunci SET valuta=?, prezzo_sats=?, prezzo_eur=? "
              "WHERE id=?", valuta, sats, eur, aid)


def accordo(aid, importo):
    """Proposta di Anna, accettata da chi vende: la strada vera."""
    banco.come(ANNA)
    off = banco.chiama(SRV.fai_offerta, aid, None,
                       corpo={"importo": str(importo)})["offerta_id"]
    banco.come(VENDE)
    banco.chiama(SRV.rispondi_offerta, off, None, corpo={"azione": "accetta"})
    return off


def offerta(off):
    r = db_uno("SELECT stato, ordine_id FROM offerte WHERE id=?", off)
    return (r["stato"], r["ordine_id"])


def compra(aid, off=0):
    banco.come(ANNA)
    corpo = {"annuncio_id": aid, "consegna": "ritiro"}
    if off:
        corpo["offerta_id"] = off
    return banco.chiama(SRV.compra, None, corpo=corpo)["ordine_id"]


def tenta_compra(aid, off=0):
    try:
        return compra(aid, off)
    except SRV.HTTPException as e:
        return (e.status_code, str(e.detail))


def preventivo(aid, off):
    banco.come(ANNA)
    return banco.chiama(SRV.preventivo_ordine, None,
                        corpo={"annuncio_id": aid, "offerta_id": off})


def articolo(oid):
    """Quanto si paga per la merce: il totale meno spedizione e
    protezione, piu' lo sconto (qui zero): l'unitario lordo."""
    o = banco.riga(oid)
    return (o["prezzo_sats"] - (o["spedizione_sats"] or 0)
            - (o["protezione_sats"] or 0) + (o["sconto_sats"] or 0))


def annulla(oid):
    banco.come(ANNA)
    return banco.chiama(SRV.annulla_ordine, oid)


def paga(oid):
    banco.PAGAMENTI[banco.riga(oid)["payment_hash"]] = "success"


def verifica(oid):
    banco.come(ANNA)
    return banco.chiama(SRV.verifica_pagamento, oid)


def orologio(rimborsa=0):
    """Il giro del riacciuffo. `rimborsa`: l'ordine che ci si aspetta
    torni indietro — il nodo di cartone decodifica la fattura del
    rimborso alla SUA cifra, come farebbe quello vero."""
    if rimborsa:
        banco.NODO["sats"] = banco.riga(rimborsa)["prezzo_sats"]
    asyncio.run(SRV.controlla_annullati())


def stato(oid):
    return banco.riga(oid)["stato"]


def pezzi(aid):
    return db_uno("SELECT quantita FROM annunci WHERE id=?", aid)["quantita"]


def detti_a(chi):
    return [t for d, t in banco.DETTO if d == chi]


def venduti():
    return sum("Hai venduto" in t for t in detti_a(VENDE))


def scena(nome, fn):
    """Una scena che ESPLODE e' una scena rossa, non un collaudo morto."""
    print(f"\n[{nome}]")
    banco.DETTO.clear()
    banco.USCITE.clear()
    CONIATE.clear()
    banco.NODO.update(codice=200, sats=50_000, esito="success")
    cambio()
    # le fatture rimaste aperte nelle scene di prima diventano lapidi
    # vecchie: il tetto degli ordini in attesa non e' in prova qui
    db_esegui("UPDATE ordini SET stato='annullato', creato=1 "
              "WHERE stato='creato'")
    db_esegui("UPDATE offerte SET ordine_id=0 WHERE stato='accettata'")
    try:
        fn()
    except Exception as e:
        traceback.print_exc()
        prova(f"la scena «{nome}» arriva in fondo", "senza eccezioni",
              f"{type(e).__name__}: {e}")


# -------------------------------------------------------------- scene
def scena_sats_poi_euro():
    aid = nuovo_annuncio("Bici da corsa")
    off = accordo(aid, 90_000)
    passa_a(aid, "eur", sats=0, eur=80.0)
    p = preventivo(aid, off)
    unit_prev = [s for s in p.get("strade", [p]) if s][0]
    oid = compra(aid, off)
    prova("accordo a 90.000 sats, annuncio passato a 80 euro: l'ordine "
          "nasce alla cifra PATTUITA (era 1 sat)", 90_000, articolo(oid))
    prova("...e il preventivo della pagina dice la stessa cifra", 90_000,
          p.get("articolo_sats", unit_prev.get("articolo_sats")))
    paga(oid)
    verifica(oid)
    prova("...pagato: nel deposito, e l'offerta e' conclusa",
          ("locked", ("conclusa", oid)), (stato(oid), offerta(off)))


def scena_euro_poi_sats():
    aid = nuovo_annuncio("Macchina fotografica", valuta="eur", sats=0,
                         eur=100.0)
    off = accordo(aid, 60)
    passa_a(aid, "sats", sats=100_000, eur=0.0)
    cambio(0.0)
    prima = db_uno("SELECT COUNT(*) AS n FROM ordini")["n"]
    r = tenta_compra(aid, off)
    prova("accordo a 60 euro, annuncio passato ai sats, cambio muto: 503 "
          "con le parole di sempre, e nessun ordine",
          (503, True, 0),
          (r[0] if isinstance(r, tuple) else "comprato",
           "cambio euro non è disponibile" in str(r),
           db_uno("SELECT COUNT(*) AS n FROM ordini")["n"] - prima))
    cambio()
    oid = compra(aid, off)
    prova("...col cambio: l'ordine nasce a 60 euro in sats (era ZERO)",
          60_000, articolo(oid))
    prova("...e il preventivo dice la stessa cifra", 60_000,
          preventivo(aid, off).get("articolo_sats"))


def scena_valute_uguali():
    aid = nuovo_annuncio("Lampada")
    off = accordo(aid, 90_000)
    oid = compra(aid, off)
    prova("sats su sats: la cifra pattuita, come sempre", 90_000,
          articolo(oid))
    aid2 = nuovo_annuncio("Poltrona", valuta="eur", sats=0, eur=100.0)
    off2 = accordo(aid2, 70)
    oid2 = compra(aid2, off2)
    prova("euro su euro: la cifra pattuita al cambio, come sempre", 70_000,
          articolo(oid2))
    oid3 = compra(nuovo_annuncio("Sedia"))
    prova("senza offerta: il listino, come sempre", 100_000, articolo(oid3))


def scena_due_fatture():
    aid = nuovo_annuncio("Giradischi")
    off = accordo(aid, 90_000)
    x1 = compra(aid, off)
    annulla(x1)
    prova("chi compra annulla: lapide, e l'offerta resta accettata e "
          "libera (si puo' ripagare, come sempre)",
          ("annullato", ("accettata", 0)), (stato(x1), offerta(off)))
    x2 = compra(aid, off)
    prova("ricompra con la stessa offerta: un ordine nuovo alla cifra "
          "pattuita", (True, 90_000, ("accettata", x2)),
          (x2 != x1, articolo(x2), offerta(off)))
    paga(x1)
    paga(x2)
    verifica(x2)
    orologio(rimborsa=x1)
    prova("pagate TUTTE E DUE: una vendita sola (erano due ordini alla "
          "cifra pattuita)", ("locked", True, 2),
          (stato(x2), stato(x1) in ("refund", "refunded"), pezzi(aid)))
    prova("...la fattura vecchia torna indietro per intero, col timbro",
          (True, banco.riga(x1)["prezzo_sats"]),
          (int(banco.riga(x1).get("pagata_da_annullata_il") or 0) > 0,
           sum(s for _, s in CONIATE)))
    prova("...a chi vende UN «Hai venduto!»", 1, venduti())
    prova("...e chi ha pagato legge che l'oggetto e' gia' nella sua "
          "fattura piu' recente", True,
          any("già nella tua fattura più recente" in t
              for t in detti_a(ANNA)))
    prova("...l'offerta e' conclusa, con l'ordine nuovo",
          ("conclusa", x2), offerta(off))


def scena_orologio_prima():
    aid = nuovo_annuncio("Chitarra")
    off = accordo(aid, 90_000)
    x1 = compra(aid, off)
    annulla(x1)
    x2 = compra(aid, off)
    paga(x1)
    orologio(rimborsa=x1)
    prova("la vecchia pagata mentre la nuova e' viva e non ancora "
          "pagata: non diventa una vendita", (True, "creato", 3),
          (stato(x1) in ("refund", "refunded"), stato(x2), pezzi(aid)))
    paga(x2)
    verifica(x2)
    prova("...poi la nuova si paga: la vendita e' quella, una",
          ("locked", 2, 1, ("conclusa", x2)),
          (stato(x2), pezzi(aid), venduti(), offerta(off)))


def scena_vecchia_poi_riprova():
    aid = nuovo_annuncio("Tastiera")
    off = accordo(aid, 90_000)
    x1 = compra(aid, off)
    annulla(x1)
    paga(x1)
    orologio()
    prova("annulla e paga la vecchia, col pezzo in vetrina: e' una "
          "vendita, come sempre", ("locked", 2, 1),
          (stato(x1), pezzi(aid), venduti()))
    prova("...e l'offerta e' CONCLUSA, legata a quell'ordine (restava "
          "accettata)", ("conclusa", x1), offerta(off))
    r = tenta_compra(aid, off)
    prova("riprovare con la stessa offerta: 404, non e' piu' valida (era "
          "un secondo ordine alla cifra pattuita)", (404, True),
          (r[0], "non più valida" in r[1]) if isinstance(r, tuple)
          else ("comprato", r))
    prova("...e al listino si compra ancora, come chiunque", 100_000,
          articolo(compra(aid)))


def scena_gesti_di_sempre():
    aid = nuovo_annuncio("Zaino")
    off = accordo(aid, 90_000)
    x1 = compra(aid, off)
    annulla(x1)
    x2 = compra(aid, off)
    paga(x2)
    verifica(x2)
    orologio()
    prova("annulla, ricompra con l'offerta, paga solo la nuova: una "
          "vendita, la lapide resta lapide, niente rimborsi",
          ("locked", "annullato", [], ("conclusa", x2)),
          (stato(x2), stato(x1), list(CONIATE), offerta(off)))
    aid2 = nuovo_annuncio("Tenda")
    y1 = compra(aid2)
    annulla(y1)
    paga(y1)
    orologio()
    prova("un ordine SENZA offerta annullato e pagato, col pezzo in "
          "vetrina: resta un acquisto, come ieri", ("locked", 2),
          (stato(y1), pezzi(aid2)))


def main():
    global SRV
    print("=" * 62)
    print("  L'ACCORDO VALE UNA VOLTA, E NELLA SUA VALUTA — il giro vero")
    print("=" * 62)
    banco.avvio()
    SRV = banco.SRV

    async def fattura_da_address(addr, sats):
        CONIATE.append((addr, sats))
        return bolt11_finta(sats, 3600, int(time.time()),
                            phash=1000 + len(banco.PAGAMENTI))

    vera_invoice = SRV.crea_invoice_escrow

    async def invoice_contata(sats, memo, *a, **k):
        inv = await vera_invoice(sats, memo, *a, **k)
        # un hash che non si ripete nemmeno a due fatture nello stesso
        # microsecondo
        inv["payment_hash"] = f"{inv['payment_hash']}-{len(FATTURE)}"
        FATTURE[inv["payment_hash"]] = sats
        return inv

    async def niente(*a, **k):
        return None

    async def cambio_scritto():
        return ORA[0]

    SRV.cambio_btc_eur = cambio_scritto
    SRV.invoice_da_ln_address = fattura_da_address
    SRV.crea_invoice_escrow = invoice_contata
    SRV.annuncio_su_nostr = niente
    SRV.promo_venduto = niente
    SRV.polso_ordini_admin = niente
    SRV.premia_xp = niente
    SRV.premia_distintivi = niente
    SRV._frena = lambda *a, **k: None
    banco.semina()
    db_esegui("UPDATE utenti SET ln_address='anna@wallet.tld' WHERE tg_id=?",
              ANNA)

    scena("1. l'accordo in sats, l'annuncio passa agli euro",
          scena_sats_poi_euro)
    scena("2. l'accordo in euro, l'annuncio passa ai sats",
          scena_euro_poi_sats)
    scena("3. a valute uguali non cambia niente", scena_valute_uguali)
    scena("4. annulla, ricompra con la stessa offerta, paga tutte e due",
          scena_due_fatture)
    scena("5. ...il riacciuffo passa prima", scena_orologio_prima)
    scena("6. annulla, paga la vecchia, poi riprova con la stessa offerta",
          scena_vecchia_poi_riprova)
    scena("7. i gesti di sempre", scena_gesti_di_sempre)

    print("\n" + "=" * 62)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 62)
    sys.exit(1 if banco.FALLITE else 0)


if __name__ == "__main__":
    main()
