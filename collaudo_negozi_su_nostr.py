# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEI PRODOTTI DEI NEGOZI COLLEGATI SU NOSTR (18 nov 2026,
cantiere negozi-su-nostr).

Da Andrea, davanti ai numeri di Nostrology (395 annunci di Barattolo in
piazza, 2.387 prodotti dei negozi collegati mai usciti): «le varianti
no, però un articolo sì», e «quando uno importa con il connettore
dovrebbe in automatico prenderli».

`prove.py` guarda la forma; qui gira il SERVER VERO su un database
usa-e-getta — il giro dell'ora con `_un_connettore`, la traduzione e la
riconciliazione vere — con un WooCommerce di cartone e i relay finti
(`_spedisci_ai_relay` raccoglie gli eventi invece di spedirli). Le
domande:
  · a fine giro esce UN evento per prodotto: l'articolo singolo col suo,
    la famiglia di varianti con uno solo, intestato alla variante piu'
    vecchia, col titolo del prodotto e il prezzo «da» della piu'
    economica disponibile;
  · un giro che non cambia niente non manda niente (l'impronta);
  · l'esaurito di una variante aggiorna l'evento della famiglia, sullo
    stesso `d`; tutte esaurite = «sold»;
  · un ordine su una variante non dice «sold» per la famiglia;
  · un prodotto tolto dal negozio prende la lapide NIP-09;
  · il tetto per giro manda gli arretrati a scaglioni;
  · la leva spenta ferma tutto;
  · scollegare il negozio cancella dai relay tutto cio' che c'era.

La chiave della piattaforma e' quella di coincurve dove c'e', se no un
calco che firma con schnorr_puro (come `collaudo_annunci_sul_profilo`).

NESSUNA RETE: il negozio e i relay sono di cartone, e in CI lo
garantisce la gabbia di `collaudi_ci.py`.

USO:  python collaudo_negozi_su_nostr.py
"""

import asyncio
import os
import sys
import time

import collaudo_lnbits_muto as banco
import schnorr_puro

prova = banco.prova
VENDE = 444
NEGOZIO = "https://maglie.test"
CATALOGO = []
VARIAZIONI = {}
SPEDITI = []          # gli eventi che sarebbero andati ai relay


def nuova_chiave() -> bytes:
    while True:
        sk = os.urandom(32)
        if 1 <= int.from_bytes(sk, "big") < schnorr_puro.N:
            return sk


class ChiaveDiCalco:
    """La chiave della piattaforma dove coincurve non c'e'."""

    def __init__(self, sk: bytes):
        self.secret = sk

    def sign_schnorr(self, msg: bytes) -> bytes:
        return schnorr_puro.firma(self.secret, msg, os.urandom(32))


def semplice(pid, nome, prezzo, stock=4):
    return {"id": pid, "name": nome, "description": "<p>Buono</p>",
            "type": "simple", "status": "publish",
            "catalog_visibility": "visible",
            "price": prezzo, "regular_price": prezzo, "manage_stock": True,
            "stock_quantity": stock,
            "stock_status": "instock" if stock else "outofstock",
            "images": [{"src": f"https://maglie.test/{pid}.jpg"}],
            "categories": [{"id": 1, "name": "Abbigliamento"}]}


def variabile(pid, nome):
    p = semplice(pid, nome, "20.00")
    p.update(type="variable", manage_stock=False, stock_quantity=None)
    return p


def variazione(vid, prezzo, taglia, stock):
    return {"id": vid, "price": prezzo, "regular_price": prezzo,
            "status": "publish", "manage_stock": True,
            "stock_quantity": stock,
            "stock_status": "instock" if stock else "outofstock",
            "virtual": False, "downloadable": False,
            "attributes": [{"id": 0, "name": "Taglia", "option": taglia}],
            "image": None}


def api_finta(metodo, url, intestazioni):
    import re
    if url.endswith("/settings/general"):
        return 200, {"lista": [{"id": "woocommerce_calc_taxes",
                                "value": "yes"}]}, {}
    if url.endswith("/settings/tax"):
        return 200, {"lista": [{"id": "woocommerce_prices_include_tax",
                                "value": "yes"}]}, {}
    m = re.search(r"/products/(\d+)/variations", url)
    if m:
        return 200, {"lista": list(VARIAZIONI.get(int(m.group(1)), []))}, {}
    pagina = 1 if "page=1" in url.split("per_page")[-1] else 2
    return 200, {"lista": list(CATALOGO) if pagina == 1 else []}, \
        {"X-WP-Total": str(len(CATALOGO))}


def connettore(cid):
    con = banco.SRV.db()
    r = dict(con.execute("SELECT * FROM connettori WHERE id=?",
                         (cid,)).fetchone())
    con.close()
    return r


def righe(cid):
    con = banco.SRV.db()
    r = [dict(x) for x in con.execute(
        "SELECT id, origine_chiave, famiglia, stato, nostr_event_id "
        "FROM annunci WHERE connettore_id=? ORDER BY id", (cid,))]
    con.close()
    return r


def giro(cid):
    """Il giro dell'ora sul solo collegamento `cid`, col modulo vero;
    torna gli eventi che sarebbero partiti in quel giro."""
    import importa_negozio
    prima = len(SPEDITI)
    asyncio.run(banco.SRV._un_connettore(connettore(cid),
                                         {"EUR": 100_000.0},
                                         importa_negozio))
    return SPEDITI[prima:]


def tag(ev, nome):
    return next((t[1] for t in ev["tags"] if t[0] == nome), None)


def main():
    print("=" * 58)
    print("  I PRODOTTI DEI NEGOZI COLLEGATI SU NOSTR — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    SRV.CONNETTORI_NEGOZIO_APERTI = True
    SRV.chiama_api_negozio = api_finta
    SRV._salva_foto_connettore = lambda annuncio_id, indice, url: \
        f"negozio_{annuncio_id}_{indice}.jpg"

    async def lotto_finto(voci):
        return {}
    SRV.moderazione_ai_lotto = lotto_finto
    SRV.PAUSA_NOSTR = 0

    sk = nuova_chiave()
    piattaforma = (SRV.ChiavePrivataNostr(sk)
                   if SRV.ChiavePrivataNostr is not None
                   else ChiaveDiCalco(sk))
    SRV._NOSTR = (piattaforma, schnorr_puro.pubblica(sk).hex())

    async def spedisci_finto(evento, relays=None):
        SPEDITI.append(evento)
        return 1
    SRV._spedisci_ai_relay = spedisci_finto

    con = SRV.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato) VALUES(?,?,?,1)", (VENDE, "Vende", "maglie"))
    cid = con.execute(
        "INSERT INTO connettori(tg_id,fonte,url_negozio,credenziali,"
        "consegna,zona,creato) VALUES(?,'woo',?,"
        "'plain:{\"consumer_key\": \"ck_x\", \"consumer_secret\": \"cs_x\"}',"
        "'ritiro','Pavia (PV)',?)", (VENDE, NEGOZIO, int(time.time()))
    ).lastrowid
    con.commit()
    con.close()
    banco.come(VENDE)

    # ---------------------------------------------------------------
    print("\n[un evento per prodotto, a fine giro]")
    CATALOGO[:] = [semplice(1, "Miele di castagno", "7.50"),
                   variabile(2, "Maglietta Bitcoin")]
    VARIAZIONI[2] = [variazione(21, "20.00", "S", 3),
                     variazione(22, "18.00", "M", 2),
                     variazione(23, "20.00", "L", 1)]
    ev = giro(cid)
    rr = righe(cid)
    miele = next(r for r in rr if r["origine_chiave"] == "1")
    maglie = [r for r in rr if r["famiglia"]]
    prova("il negozio di cartone e' entrato: un singolo e tre varianti",
          (4, 3), (len(rr), len(maglie)))
    testa = min(r["id"] for r in maglie)
    prova("due eventi, uno per prodotto (non quattro)", 2, len(ev))
    prova("...tutti NIP-99", {30402}, {e["kind"] for e in ev})
    per_d = {tag(e, "d"): e for e in ev}
    prova("...col d del singolo e quello della testa della famiglia",
          {f"barattolo-{miele['id']}", f"barattolo-{testa}"}, set(per_d))
    fam = per_d[f"barattolo-{testa}"]
    prova("la famiglia parla col nome del prodotto",
          "Maglietta Bitcoin", tag(fam, "title"))
    prova("...col prezzo della variante disponibile piu' economica",
          ["price", "18.00", "EUR"],
          next(t for t in fam["tags"] if t[0] == "price"))
    prova("...e il «da» lo legge la persona", True,
          "Prezzo: da 18.00 EUR" in fam["content"])
    prova("...coi disponibili di tutte le varianti", "6",
          tag(fam, "stock"))
    prova("il singolo non ha il «da»", True,
          "Prezzo: 7.50 EUR" in per_d[f"barattolo-{miele['id']}"]["content"])
    prova("entrambi portano il nome di Barattolo (Nostrology)",
          {"Barattolo"}, {tag(e, "client") for e in ev})
    prova("le varianti che non sono la testa non hanno un evento",
          [""] * 2, [r["nostr_event_id"] for r in maglie if r["id"] != testa])

    # ---------------------------------------------------------------
    print("\n[un giro che non cambia niente non manda niente]")
    prova("zero eventi", 0, len(giro(cid)))

    # ---------------------------------------------------------------
    print("\n[l'esaurito di una variante aggiorna la famiglia]")
    VARIAZIONI[2][1] = variazione(22, "18.00", "M", 0)
    ev = giro(cid)
    prova("un evento solo, sullo stesso d della famiglia",
          [f"barattolo-{testa}"], [tag(e, "d") for e in ev])
    prova("...col prezzo nuovo e i disponibili nuovi",
          ("20.00", "4", "active"),
          (tag(ev[0], "price"), tag(ev[0], "stock"), tag(ev[0], "status")))

    # ---------------------------------------------------------------
    print("\n[un ordine su una variante parla per la famiglia]")
    var_s = next(r["id"] for r in maglie if r["id"] != testa)
    prima = len(SPEDITI)
    asyncio.run(SRV.annuncio_su_nostr(var_s, "sold",
                                      solo_aggiornamento=True))
    ev = SPEDITI[prima:]
    prova("il gancio di sempre ripubblica la FAMIGLIA, attiva",
          [(f"barattolo-{testa}", "active")],
          [(tag(e, "d"), tag(e, "status")) for e in ev])

    # ---------------------------------------------------------------
    print("\n[tutte esaurite: la famiglia e' venduta]")
    VARIAZIONI[2] = [variazione(21, "20.00", "S", 0),
                     variazione(22, "18.00", "M", 0),
                     variazione(23, "20.00", "L", 0)]
    ev = giro(cid)
    prova("un evento, «sold», sullo stesso d",
          [(f"barattolo-{testa}", "sold")],
          [(tag(e, "d"), tag(e, "status")) for e in ev])
    VARIAZIONI[2][0] = variazione(21, "20.00", "S", 5)
    ev = giro(cid)
    prova("...e il rifornimento la riaccende",
          [(f"barattolo-{testa}", "active")],
          [(tag(e, "d"), tag(e, "status")) for e in ev])

    # ---------------------------------------------------------------
    print("\n[tolto dal negozio: la lapide]")
    CATALOGO[:] = [variabile(2, "Maglietta Bitcoin")]
    ev = giro(cid)
    prova("un kind 5 sul miele, e nient'altro",
          [(5, f"30402:{SRV._NOSTR[1]}:barattolo-{miele['id']}")],
          [(e["kind"], tag(e, "a")) for e in ev])
    prova("...e la riga dimentica il suo evento", "",
          next(r for r in righe(cid) if r["id"] == miele["id"])
          ["nostr_event_id"])

    # ---------------------------------------------------------------
    print("\n[il tetto per giro: gli arretrati a scaglioni]")
    SRV.MAX_NOSTR_NEGOZIO_PER_GIRO = 2
    CATALOGO.extend([semplice(5, "Tazza", "9.00"),
                     semplice(6, "Adesivo", "1.00"),
                     semplice(7, "Cappello", "15.00")])
    prova("al primo giro ne escono due", 2, len(giro(cid)))
    prova("...e l'ultimo al giro dopo", 1, len(giro(cid)))
    prova("...poi piu' niente", 0, len(giro(cid)))
    SRV.MAX_NOSTR_NEGOZIO_PER_GIRO = 100

    # ---------------------------------------------------------------
    print("\n[la leva spenta ferma tutto]")
    SRV.NEGOZI_SU_NOSTR = False
    CATALOGO.append(semplice(8, "Spilla", "3.00"))
    CATALOGO[1] = semplice(5, "Tazza", "11.00")
    prova("niente eventi nuovi e niente aggiornamenti", 0, len(giro(cid)))
    prima = len(SPEDITI)
    asyncio.run(SRV.annuncio_su_nostr(testa, "active"))
    prova("...nemmeno dai ganci di sempre", 0, len(SPEDITI) - prima)
    SRV.NEGOZI_SU_NOSTR = True
    ev = giro(cid)
    prova("riaccesa, il giro dopo recupera: la spilla nasce e la tazza "
          "cambia prezzo", 2, len(ev))

    # ---------------------------------------------------------------
    print("\n[scollegare cancella dai relay tutto cio' che c'era]")
    in_piazza = {r["id"] for r in righe(cid) if r["nostr_event_id"]}
    # col tetto piu' basso dei prodotti in piazza: lo scollegamento non
    # ha un giro dopo, quindi le lapidi devono partire TUTTE adesso
    SRV.MAX_NOSTR_NEGOZIO_PER_GIRO = 2
    prova("(in piazza ci sono piu' prodotti del tetto)", True,
          len(in_piazza) > SRV.MAX_NOSTR_NEGOZIO_PER_GIRO)
    prima = len(SPEDITI)
    r = c.post(f"/api/me/connettori/{cid}/scollega")
    prova("lo scollegamento risponde", 200, r.status_code)

    async def aspetta():
        for _ in range(100):
            if len(SPEDITI) - prima >= len(in_piazza):
                break
            await asyncio.sleep(0.05)
    asyncio.run(aspetta())
    lapidi = {tag(e, "a").rsplit("-", 1)[1] for e in SPEDITI[prima:]
              if e["kind"] == 5}
    prova("una lapide per ogni prodotto che era in piazza",
          {str(x) for x in in_piazza}, lapidi)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
