# -*- coding: utf-8 -*-
"""
LO SWAP, TAPPA 2: IL PREVENTIVO, SUL SERVER VERO (19 ott 2026, cantiere
swap-preventivo).

`prove.py` gira il conto, puro. Qui la STORIA per HTTP (TestClient, la
app vera) contro il SATS ROUTING DI CARTONE (`cartone_satsrouting.py`)
acceso su una porta di questo computer: la lettura delle tariffe passa
davvero da `httpx` e dalla rete di casa, coi numeri veri del 16 ott.

LE SCENE:
  - il cancello: a solo-moderatori acceso il 999 vede lo swap, il 222 no
    (in `/api/me` e alla porta del preventivo);
  - il preventivo di un ordine confermato da 48.000: ricevi 47.154, e il
    codice partner «barattolo» e' arrivato al cartone nell'intestazione;
  - la copia di 30 secondi: due preventivi, una lettura;
  - i rifiuti: sotto il minimo, sopra il massimo, tariffe cambiate (con
    l'impronta di quelle di prima), SATS Routing giu', risposta storta;
  - le porte: l'ordine di un altro, l'ordine non ancora confermato;
  - la leva aperta a tutti e la leva spenta;
  - IN COLLAUDO LA BASE VERA NON SI LEGGE: puntata a SATS Routing vero,
    il preventivo dice «non risponde» e il cartone non vede niente.

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta dal
banco dei pagamenti PRIMA dell'import del server; nessuna rete fuori da
127.0.0.1 (in CI la gabbia di `collaudi_ci.py`); nessuno swap, nessun
sats: la tappa 2 legge e conta, e basta.

USO:  python collaudo_swap_preventivo.py
"""
import contextlib
import io
import json
import urllib.request

import collaudo_lnbits_muto as banco
import cartone_satsrouting

prova = banco.prova
ADMIN = {"X-Tg-Init-Data": "collaudo:999:Admin"}
VENDE = {"X-Tg-Init-Data": "collaudo:222:Venditore"}
PORTA = 0


def cartone(percorso):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORTA}{percorso}",
                                timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))


def modo(m):
    cartone(f"/cartone/modo?m={m}")
    banco.SRV._TARIFFE_SWAP.update(quando=0.0, dati=None)   # niente copia


def semina():
    con = banco.SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    for tg, nome in ((999, "Admin"), (222, "Vende"), (111, "Compra")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, f"neg{tg}0000"))
    ids = {}
    for chi, prezzo in ((999, 48_000), (999, 20_000), (999, 60_000),
                        (999, 48_000), (222, 48_000)):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(?,?,'una cosa',?,'Altro','Pavia (PV)','attivo',1,"
            "'ritiro',5,'sats','nuovo')", (chi, f"Cosa {chi} {prezzo}", prezzo))
        ids.setdefault((chi, prezzo), []).append(cur.lastrowid)
    con.commit()
    con.close()
    return ids


def ordine(annuncio_id, stato="confirmed"):
    oid = banco.ordine_pagato(annuncio_id)
    con = banco.SRV.db()
    con.execute("UPDATE ordini SET stato=? WHERE id=?", (stato, oid))
    con.commit()
    con.close()
    return oid


def preventivo(c, chi, oid, hash_=""):
    banco.come(chi, admin=(chi == 999))
    q = f"?hash={hash_}" if hash_ else ""
    r = c.get(f"/api/swap/preventivo/{oid}{q}",
              headers=ADMIN if chi == 999 else VENDE)
    return r.status_code, (r.json() if r.content else {})


def leve(c, chi):
    banco.come(chi, admin=(chi == 999))
    r = c.get("/api/me", headers=ADMIN if chi == 999 else VENDE)
    return (r.json() or {}).get("swap_leve") or {}


def giro(c):
    srv = banco.SRV
    ids = semina()
    o48 = ordine(ids[(999, 48_000)][0])
    o20 = ordine(ids[(999, 20_000)][0])
    o60 = ordine(ids[(999, 60_000)][0])
    o_lock = ordine(ids[(999, 48_000)][1], "locked")
    o_altro = ordine(ids[(222, 48_000)][0])

    print("\n[il cancello per persona]")
    l999, l222 = leve(c, 999), leve(c, 222)
    prova("a solo-moderatori il 999 ha lo swap, coi tetti e il codice",
          (True, 25_000, 50_000, "barattolo"),
          (l999.get("attivo"), l999.get("minimo"), l999.get("massimo"),
           l999.get("referral")))
    prova("...il 222 no", False, l222.get("attivo"))
    prova("...e la porta del preventivo glielo dice", 403,
          preventivo(c, 222, o_altro)[0])

    print("\n[il preventivo da 48.000]")
    modo("normale")
    codice, p = preventivo(c, 999, o48)
    prova("risponde col conto: ricevi 47.154", (200, True, 47_154, 48_000),
          (codice, p.get("ok"), p.get("ricevi"), p.get("dovuto")))
    prova("...riga per riga", [("dovuto", 48_000), ("commissione", -288),
                               ("rete_invio", -324), ("rete_ritiro", -234)],
          [(r["voce"], r["sats"]) for r in p.get("righe", [])])
    prova("...con l'impronta e la durata", ("cartone-tariffa-16ott", 60, False),
          (p.get("hash"), p.get("valido_s"), p.get("cambiata")))
    visto = cartone("/cartone/visto")
    prova("il codice partner e' arrivato a SATS Routing", ("barattolo", 1),
          (visto["referral"], visto["letture"]))
    preventivo(c, 999, o48)
    prova("la copia di 30 secondi: due preventivi, una lettura", 1,
          cartone("/cartone/visto")["letture"])

    print("\n[i rifiuti]")
    _, s = preventivo(c, 999, o20)
    prova("sotto il minimo", (False, "sotto_minimo", 25_000),
          (s.get("ok"), s.get("motivo"), s.get("minimo")))
    _, s = preventivo(c, 999, o60)
    prova("sopra il massimo", (False, "sopra_tetto", 50_000),
          (s.get("ok"), s.get("motivo"), s.get("massimo")))
    modo("cambiata")
    _, s = preventivo(c, 999, o48, "cartone-tariffa-16ott")
    prova("tariffe cambiate: lo dice, col preventivo nuovo (0,7 %)",
          (True, True, -336),
          (s.get("cambiata"), s.get("ok"),
           next((r["sats"] for r in s.get("righe", [])
                 if r["voce"] == "commissione"), None)))
    _, s = preventivo(c, 999, o48, "cartone-tariffa-cambiata")
    prova("...e con l'impronta giusta non lo dice", False, s.get("cambiata"))
    modo("giu")
    _, s = preventivo(c, 999, o48)
    prova("SATS Routing giu': non risponde", (False, "non_risponde"),
          (s.get("ok"), s.get("motivo")))
    modo("storta")
    _, s = preventivo(c, 999, o48)
    prova("una risposta storta non diventa un preventivo",
          (False, "non_risponde"), (s.get("ok"), s.get("motivo")))
    modo("normale")

    print("\n[le porte]")
    prova("l'ordine di un altro: 404", 404, preventivo(c, 999, o_altro)[0])
    prova("l'ordine non ancora confermato: 409", 409,
          preventivo(c, 999, o_lock)[0])

    print("\n[la leva]")
    srv.SWAP_SOLO_MODERATORI = False
    codice, s = preventivo(c, 222, o_altro)
    prova("aperta a tutti: anche il 222 ha il suo preventivo", (200, True),
          (codice, s.get("ok")))
    prova("...e /api/me glielo dice", True, leve(c, 222).get("attivo"))
    srv.SWAP_SOLO_MODERATORI = True
    srv.SWAP_ATTIVO = False
    prova("leva spenta: nessuno, nemmeno il moderatore", (403, False),
          (preventivo(c, 999, o48)[0], leve(c, 999).get("attivo")))
    srv.SWAP_ATTIVO = True

    print("\n[in collaudo la base vera non si legge]")
    srv.SWAP_API_BASE = "https://api.satsrouting.exchange"
    srv._TARIFFE_SWAP.update(quando=0.0, dati=None)
    srv._SWAP_DETTO_SIMULATO.clear()
    prima = cartone("/cartone/visto")["letture"]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _, s = preventivo(c, 999, o48)
    prova("puntato al servizio vero, il preventivo dice «non risponde»",
          (False, "non_risponde"), (s.get("ok"), s.get("motivo")))
    prova("...il journal dice perche'", True,
          "[swap simulato]" in buf.getvalue())
    prova("...e nessuna lettura e' partita", prima,
          cartone("/cartone/visto")["letture"])
    prova("nessun pagamento e' uscito verso LNbits", [], banco.USCITE)


def main():
    global PORTA
    print("=" * 58)
    print("  ₿ LO SWAP, TAPPA 2 — il preventivo, il giro vero")
    print("=" * 58)
    banco.avvio()
    import httpx
    from fastapi.testclient import TestClient

    srv = banco.SRV
    # il banco mette un LNbits finto al posto di httpx: qui serve quello
    # VERO, perche' la lettura delle tariffe va al cartone per HTTP
    srv.httpx = httpx
    _, PORTA = cartone_satsrouting.avvia(0)
    srv.SWAP_ATTIVO = True
    srv.SWAP_SOLO_MODERATORI = True
    srv.SWAP_MIN_SATS = 25_000
    srv.SWAP_MAX_SATS = 50_000
    srv.SWAP_FEE_PERCENTO = 0
    srv.SWAP_API_BASE = f"http://127.0.0.1:{PORTA}"
    srv.SWAP_REFERRAL_ID = "barattolo"
    giro(TestClient(srv.app))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
