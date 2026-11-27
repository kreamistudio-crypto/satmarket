# -*- coding: utf-8 -*-
"""
L'INTERVALLO «DA… A…» ANCHE ON-CHAIN (27 nov 2026, cantiere
intervallo-onchain, Andrea: «Ordini p2p ad intervalli anche su onchain»)
— il giro col SERVER VERO, per HTTP: l'ordine a intervallo pubblicato a
mercato coi suoi due capi (e dove resta a cifra unica: a prezzo fisso, a
leva spenta), il libro e il 38383 coi due capi, la presa che vuole la
cifra dentro la fascia e conta i sats su quella, la rinascita con
l'intervallo intero, e la cauzione del contanti contata sulla cifra
scelta (decisione di Andrea) contro un LND di cartone: mai superata alla
presa. La stessa gabbia di collaudo_p2p_onchain (relay muti, mempool di
cartone).

USO:  python collaudo_intervallo_onchain.py
"""
import base64
import hashlib
import http.server
import json
import os
import sys
import threading
import time
import urllib.parse

import collaudo_lnbits_muto as banco

prova = banco.prova


def main():
    print("=" * 58)
    print("  L'INTERVALLO ANCHE ON-CHAIN — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    import httpx as httpx_vero
    from embit import bip32, bip39, script
    from embit.networks import NETWORKS
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    N = NETWORKS["signet"]
    vett = json.load(open(os.path.join(banco.QUI, "vendor",
                                       "vettori-bip.json"), encoding="utf-8"))
    semi = {999: vett["bip39_english"][0]["parole"],
            888: vett["bip39_english"][1]["parole"],
            "wallet": vett["bip39_english"][2]["parole"]}

    def radice(tg):
        return bip32.HDKey.from_seed(bip39.mnemonic_to_seed(semi[tg]),
                                     version=N["xprv"])

    def conto(tg):
        return radice(tg).derive("m/48h/1h/0h/2h").to_public().to_string(
            version=N["xpub"])

    def dal_wallet(i):
        k = radice("wallet").derive(f"m/84h/1h/0h/0/{i}")
        return script.p2wpkh(k.key.get_public_key()).address(N)

    def firma_dest(tg, tipo, valore):
        msg = SRV.onchain_messaggio_destinazione(tipo, valore)
        der = radice(tg).derive("m/48h/1h/0h/2h/2/0").key.sign(
            hashlib.sha256(msg).digest()).serialize()
        lr = der[3]
        r, s_ = der[4:4 + lr], der[6 + lr:]
        return (r[-32:].rjust(32, b"\0") + s_[-32:].rjust(32, b"\0")).hex()

    # --- mempool di cartone: nessuna rete vera -----------------------
    async def utxo_finte(indirizzo):
        return []

    async def tariffa_finta():
        return 2.0

    async def scheda_vuota(indirizzo):
        return {"chain_stats": {"tx_count": 0}, "mempool_stats": {"tx_count": 0}}
    SRV.onchain_mempool_utxo = utxo_finte
    SRV.onchain_mempool_tariffa = tariffa_finta
    SRV.onchain_mempool_indirizzo = scheda_vuota

    con = SRV.db()
    for tg, nome in ((999, "Andrea"), (888, "Alan"), (777, "Terzo")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, f"neg{tg}{tg}"))
    con.commit()
    con.close()
    SRV.ADMIN_IDS = [999, 888, 777]
    SRV.ONCHAIN_ATTIVO = True
    SRV.P2P_ATTIVO = True
    SRV.P2P_ONCHAIN_ATTIVO = True
    SRV._P2P_INFO["fee"] = 0.0
    SRV.MOSTRO_HEX = "cd" * 32
    SRV.MOSTRO_RELAY = ["ws://127.0.0.1:9"]
    SRV.P2P_PROVA_IDS = []
    SRV.P2P_ONCHAIN_APERTI_MAX = 100
    for nome in ("p2p_onchain_pubblica", "p2p_onchain_prendi", "onchain_firma",
                 "onchain_controlla", "p2p_onchain_controlla", "p2p_onchain_cauzione"):
        SRV.FRENI[nome] = (1000, 3600)
    # il cambio di adesso, fresco: 50.000 € per bitcoin
    SRV._cambio_cache["valori"]["eur"] = 50000.0
    SRV._cambio_cache["quando"] = time.time()

    def come(tg):
        banco.come(tg, admin=tg in SRV.ADMIN_IDS)

    def pubblica(tg=888, **d):
        come(tg)
        base = {"lato": "sell", "tipo": "mercato", "premio": 0, "euro_min_cent": 2000,
                "euro_cent": 10000, "metodi": ["Revolut"], "recapito": "IT00 X 1234"}
        base.update(d)
        return c.post("/api/p2p/onchain/pubblica", json=base)

    def gesto(tg, oid, cosa, **d):
        come(tg)
        return c.post(f"/api/p2p/onchain/{oid}/{cosa}", json=d)

    def libro(tg=0):
        SRV._chi_guarda_p2p = lambda *a, **k: int(tg)
        SRV._p2p_onchain_rifai_foto()
        return c.get("/api/p2p/libro").json()

    def riga(oid):
        con = SRV.db()
        try:
            return dict(con.execute("SELECT * FROM p2p_onchain_ordini WHERE id=?",
                                    (oid,)).fetchone())
        finally:
            con.close()

    for tg in (999, 888):
        come(tg)
        c.post("/api/onchain/xpub", json={"xpub": conto(tg)})
    dove = dal_wallet(50)
    come(999)
    c.post("/api/onchain/incasso", json={"tipo": "indirizzo", "valore": dove,
                                         "firma": firma_dest(999, "indirizzo", dove)})

    # ---- 1) la pubblicazione ------------------------------------------------
    print("\n[la pubblicazione coi due capi]")
    r = pubblica()
    prova("un ordine 20–100 € a mercato: 200", 200, r.status_code)
    oid = r.json()["id"]
    o = riga(oid)
    prova("la riga: il massimo in `euro_cent`, i due capi nelle loro colonne, sats a zero",
          [10000, 2000, 10000, 0, "mercato"],
          [o["euro_cent"], o["fascia_min_cent"], o["fascia_max_cent"], o["prezzo_sats"],
           o["prezzo_tipo"]])
    fisso = riga(pubblica(tipo="fisso", sats=100000).json()["id"])
    SRV.P2P_ONCHAIN_INTERVALLO = False
    spenta = riga(pubblica().json()["id"])
    SRV.P2P_ONCHAIN_INTERVALLO = True
    prova("a prezzo fisso e a leva spenta il primo capo non conta: cifra unica, 100 €",
          [(10000, 0, 0), (10000, 0, 0)],
          [(fisso["euro_cent"], fisso["fascia_min_cent"], fisso["fascia_max_cent"]),
           (spenta["euro_cent"], spenta["fascia_min_cent"], spenta["fascia_max_cent"])])
    r = pubblica(euro_min_cent=1)
    prova("un primo capo che al cambio di adesso fa meno sats del minimo: 400 con la frase",
          (400, True), (r.status_code, "il minimo" in r.json().get("detail", "")))

    # ---- 2) il libro e Nostr -----------------------------------------------
    print("\n[il libro e Nostr]")
    busta = libro(999)["onchain"]
    ev = [e for e in busta["eventi"] if int(e["id"]) == oid]
    prova("la busta dice la leva; la card ha i due capi e la stima di tutti e due "
          "(40.000 e 200.000 sats a 50.000 €)",
          [True, 20.0, 100.0, 40000, 200000],
          [busta.get("intervallo"), ev[0].get("euro_min") if ev else None,
           ev[0].get("euro") if ev else None, ev[0].get("stima_min") if ev else None,
           ev[0].get("stima") if ev else None])
    prova("...e il 38383 porta i due capi nel `fa`, come gli ordini di Mostro",
          ["fa", "20", "100"], [t for t in SRV.p2p_onchain_tags(riga(oid)) if t[0] == "fa"][0])
    ev_f = [e for e in busta["eventi"] if int(e["id"]) == fisso["id"]]
    prova("un ordine a cifra unica resta senza primo capo", False, "euro_min" in (ev_f[0] if ev_f else {"euro_min": 1}))

    # ---- 3) la presa ------------------------------------------------------
    print("\n[la presa: la cifra dentro la fascia]")
    no_cifra = gesto(999, oid, "prendi")
    no_fuori = gesto(999, oid, "prendi", euro_cent=15000)
    prova("senza cifra, o fuori dalla fascia: 400 con la frase del foglio «Quanto»",
          [(400, "Scegli una cifra fra 20,00 e 100,00 €"), 400],
          [(no_cifra.status_code, no_cifra.json().get("detail")), no_fuori.status_code])
    r = gesto(999, oid, "prendi", euro_cent=3000)
    prova("30 € scelti: 200", 200, r.status_code)
    o = riga(oid)
    prova("la riga: `euro_cent` e' la cifra scelta, i sats contati su quella (60.000), i "
          "capi restano per la rinascita",
          ["preso", 3000, 60000, 2000, 10000],
          [o["stato"], o["euro_cent"], o["prezzo_sats"], o["fascia_min_cent"], o["fascia_max_cent"]])
    prova("...e il libro non la mostra piu'", False,
          any(int(e["id"]) == oid for e in libro(999)["onchain"]["eventi"]))

    # ---- 4) la rinascita ----------------------------------------------------
    print("\n[la rinascita: torna l'intervallo intero]")
    r = gesto(999, oid, "annulla")
    prova("chi ha preso annulla prima del deposito: 200", 200, r.status_code)
    con = SRV.db()
    nuovo = con.execute("SELECT * FROM p2p_onchain_ordini WHERE rinato_da=?", (oid,)).fetchone()
    con.close()
    prova("l'ordine rinasce coi suoi due capi, non coi 30 € di chi l'aveva preso",
          ["pending", 10000, 2000, 10000],
          [nuovo["stato"], nuovo["euro_cent"], nuovo["fascia_min_cent"], nuovo["fascia_max_cent"]]
          if nuovo else None)
    ev = [e for e in libro(999)["onchain"]["eventi"] if nuovo and int(e["id"]) == int(nuovo["id"])]
    prova("...e nel libro la card dice di nuovo «da 20 a 100»", [20.0, 100.0],
          [ev[0].get("euro_min"), ev[0].get("euro")] if ev else None)

    # ---- 5) la cauzione sulla cifra scelta, contro un LND di cartone --------
    print("\n[la cauzione del contanti sulla cifra scelta]")
    MAC_C = "0201036c6e64" + "cd" * 40
    LND = {"fatture": {}, "visti": []}

    class FintoLnd(http.server.BaseHTTPRequestHandler):
        """La REST di LND per le hold: `hodl` conia, GET dice lo stato."""
        def log_message(self, *a):
            pass

        def _rispondi(self, codice, d):
            dati = json.dumps(d).encode()
            self.send_response(codice)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(dati)))
            self.end_headers()
            self.wfile.write(dati)

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            f = LND["fatture"].get(u.path.rsplit("/", 1)[1])
            if self.headers.get("Grpc-Metadata-macaroon", "") != MAC_C or not f:
                return self._rispondi(404, {"code": 5, "message": "no"})
            return self._rispondi(200, {"state": f["state"], "value": str(f["value"])})

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            corpo = json.loads(self.rfile.read(n) or b"{}")
            LND["visti"].append((self.path, corpo))
            if self.headers.get("Grpc-Metadata-macaroon", "") != MAC_C:
                return self._rispondi(401, {"code": 16, "message": "permission denied"})
            if self.path == "/v2/invoices/hodl":
                h = base64.b64decode(corpo["hash"]).hex()
                LND["fatture"][h] = {"state": "OPEN", "value": int(corpo["value"])}
                return self._rispondi(200, {"payment_request": "lnbc1cauzione" + h[:24]})
            if self.path == "/v2/invoices/cancel":
                h = base64.b64decode(corpo["payment_hash"]).hex()
                if h in LND["fatture"]:
                    LND["fatture"][h]["state"] = "CANCELED"
                return self._rispondi(200, {})
            return self._rispondi(404, {"code": 5, "message": "Not Found"})

    lnd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FintoLnd)
    lnd.daemon_threads = True
    threading.Thread(target=lnd.serve_forever, daemon=True).start()
    SRV.httpx = httpx_vero
    SRV.LND_PONTE_URL = f"http://127.0.0.1:{lnd.server_address[1]}"
    SRV.P2P_ONCHAIN_CAUZIONE, SRV.LND_PONTE_MACAROON_CAUZIONE = True, MAC_C
    SRV.P2P_ONCHAIN_CAUZIONE_SOLO_ADMIN = True     # 999 e' un moderatore

    def cauz(tg, oc, **d):
        come(tg)
        return c.post(f"/api/p2p/onchain/{oc}/cauzione", json={"metodo": "Contanti", **d})

    oc = pubblica(metodi=["Contanti"], recapito="", zona="Milano centro").json()["id"]
    no = cauz(999, oc)
    prova("la cauzione senza cifra: 400 con la frase, e LND non conia niente",
          (400, True, 0), (no.status_code, "Scegli una cifra" in no.text, len(LND["visti"])))
    r = cauz(999, oc, euro_cent=3000)
    cz = r.json().get("cauzione") or {}
    con = SRV.db()
    rc = dict(con.execute("SELECT * FROM p2p_onchain_cauzioni WHERE ordine_id=? ORDER BY id DESC",
                          (oc,)).fetchone())
    con.close()
    # 30 € a 50.000 €/BTC = 60.000 sats, il 3% = 1.800 (sui 100 € sarebbero 6.000)
    prova("30 € scelti: la cauzione e' il 3% di 60.000 sats (1.800, non i 6.000 del massimo), "
          "e la riga si ricorda la cifra",
          (200, 1800, "1800", 3000),
          (r.status_code, cz.get("sats"), LND["visti"][-1][1].get("value"), rc["base_cent"]))
    LND["fatture"][rc["hash"]]["state"] = "ACCEPTED"     # il wallet ha pagato
    su = cauz(999, oc, euro_cent=5000)
    prova("con la cauzione tenuta su 30 €, chiederla per 50 €: 409 con la frase, nessuna "
          "seconda hold",
          (409, "La tua cauzione su quest'ordine copre fino a 30,00 €: scegli una cifra fino a 30,00 €", 1),
          (su.status_code, su.json().get("detail"),
           sum(1 for p, _ in LND["visti"] if p == "/v2/invoices/hodl")))
    oltre = gesto(999, oc, "prendi", metodo="Contanti", euro_cent=5000)
    prova("...e prendere a 50 €: 409, la stessa frase; l'ordine resta nel libro",
          (409, True, "pending"),
          (oltre.status_code, "copre fino a 30,00" in oltre.text, riga(oc)["stato"]))
    r = gesto(999, oc, "prendi", metodo="Contanti", euro_cent=2500)
    o = riga(oc)
    prova("a 25 € (sotto la cifra della cauzione) si prende: 200, 25 € e 50.000 sats",
          (200, "preso", 2500, 50000), (r.status_code, o["stato"], o["euro_cent"], o["prezzo_sats"]))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
