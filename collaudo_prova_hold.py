# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE HOLD DI PROVA (10 ott 2026, sera, cantiere prova-hold).

La pagina `/prova-wallet` ha due bottoni, G e H, sullo stesso link del
tasto vero (`lightning:` minuscolo) ma su due HOLD invoice da 1 sat del
nostro LND — G con `cltv_expiry` 40, H con 576 come Mostro — per capire
se il wallet dell'utente si incanta sulla hold in se' o sul CLTV lungo.
`prove.py` guarda i giudici puri (il corpo della richiesta, la
freschezza, la pagina) e le sentinelle (mai `settle`); qui gira il
PEZZO VERO contro un LND di cartone su 127.0.0.1: la rotta intera col
TestClient, il conio (`POST /v2/invoices/hodl` col macaroon delle hold
nell'header, l'hash in base64, 1 sat, la scadenza, i due cltv), la
registrazione in `impostazioni`, la fattura fresca che non si riconia,
la cancellazione dopo la vita (`POST /v2/invoices/cancel` con lo stesso
hash), l'«already canceled» che vale come annullata, la leva spenta che
non bussa a nessuno, e LND muto che lascia la pagina in piedi.

Come gli altri: `collaudo_lnbits_muto.avvio()` installa il config di
cartone e importa il server VERO; il ponte verso LND lo si gira verso
il cartone cambiando i globali del modulo (le funzioni li leggono al
momento della chiamata). Nessuna rete fuori dal loopback.

Uso:  python collaudo_prova_hold.py
"""
import asyncio
import base64
import http.server
import json
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collaudo_lnbits_muto as banco  # noqa: E402

PASSATE = FALLITE = 0
MACAROON = "0201036c6e64" + "ab" * 40
VISTI = []          # (percorso, corpo, macaroon)
RISPOSTE = {"hodl": 200}
CANCELLATE = set()


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}\n      avuto:  {avuto!r}")


class FintoLnd(http.server.BaseHTTPRequestHandler):
    """La REST di LND, a memoria della sua API: `hodl` risponde con la
    `payment_request`; `cancel` con un JSON vuoto la prima volta e con
    l'errore «invoice already canceled» (codice 2) le volte dopo."""
    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        corpo = json.loads(self.rfile.read(n) or b"{}")
        mac = self.headers.get("Grpc-Metadata-macaroon", "")
        VISTI.append((self.path, corpo, mac))
        if mac != MACAROON:
            return self._rispondi(401, {"code": 16, "message": "permission denied"})
        if self.path == "/v2/invoices/hodl":
            if RISPOSTE["hodl"] != 200:
                return self._rispondi(RISPOSTE["hodl"], {"code": 2, "message": "cartone muto"})
            h = base64.b64decode(corpo["hash"]).hex()
            return self._rispondi(200, {"payment_request": "lnbc10n1cartone" + h[:20],
                                        "add_index": str(len(VISTI)), "payment_addr": "AA=="})
        if self.path == "/v2/invoices/cancel":
            h = base64.b64decode(corpo["payment_hash"]).hex()
            if h in CANCELLATE:
                return self._rispondi(500, {"code": 2, "message": "invoice already canceled"})
            CANCELLATE.add(h)
            return self._rispondi(200, {})
        return self._rispondi(404, {"code": 5, "message": "Not Found"})

    def _rispondi(self, codice, d):
        dati = json.dumps(d).encode()
        self.send_response(codice)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dati)))
        self.end_headers()
        self.wfile.write(dati)


def main():
    print("\n[le hold di prova G e H, dal vivo contro un LND di cartone]")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FintoLnd)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    porta = srv.server_address[1]

    banco.avvio()
    S = banco.SRV
    # il banco mette un httpx di cartone al posto di quello vero (e' il
    # suo LNbits muto): le hold vogliono quello VERO, verso il cartone
    # di LND su 127.0.0.1 — la fattura normale resta al doppio del banco
    import httpx as httpx_vero
    S.httpx = httpx_vero
    from fastapi.testclient import TestClient
    client = TestClient(S.app)   # senza `with`: niente startup, niente giro

    # la fattura normale la conia il doppio di LNbits del banco: qui si
    # guarda solo che G e H non la disturbino
    S.LND_PONTE_URL = f"http://127.0.0.1:{porta}"

    # --- 1) la leva spenta: «non attive», e nessuno bussa a LND --------
    S.LND_PONTE_MACAROON_HOLD = ""
    r = client.get("/prova-wallet")
    prova("leva spenta: 200, la pagina dice «non attive» e nessun link G/H",
          (200, True, 0, 0),
          (r.status_code, "G e H (hold invoice) non attive su questo server." in r.text,
           r.text.count('class="b hold"'), len(VISTI)))
    prova("...e il giudice della leva lo dice", False, S._hold_prova_configurata())
    prova("...e la pulizia con la leva spenta non fa niente", [],
          asyncio.run(S.ripulisci_hold_prova()))

    # --- 2) la leva accesa: due hold coniate, con la forma giusta --------
    S.LND_PONTE_MACAROON_HOLD = MACAROON
    prova("leva accesa", True, S._hold_prova_configurata())
    r = client.get("/prova-wallet")
    hodl = [v for v in VISTI if v[0] == "/v2/invoices/hodl"]
    prova("la pagina: 200, i due link G e H col lightning: minuscolo sulla bolt11 della hold",
          (200, 2, True, True),
          (r.status_code, r.text.count('class="b hold"'),
           'href="lightning:lnbc10n1cartone' in r.text, "come Mostro" in r.text))
    prova("...e LND ha visto DUE hodl, col macaroon delle hold nell'header",
          [2, {MACAROON}], [len(hodl), {v[2] for v in hodl}])
    corpi = [v[1] for v in hodl]
    prova("...1 sat, scadenza 600, memo che dice di NON pagare, cltv 40 e 576",
          [("1", "600", True, "40"), ("1", "600", True, "576")],
          [(c["value"], c["expiry"], "NON pagare" in c["memo"], c["cltv_expiry"]) for c in corpi])
    hashes = [base64.b64decode(c["hash"]) for c in corpi]
    prova("...l'hash: 32 byte in base64, diverso fra G e H", [32, 32, True],
          [len(hashes[0]), len(hashes[1]), hashes[0] != hashes[1]])
    regG, regH = S._hold_prova_registrata("G"), S._hold_prova_registrata("H")
    prova("...e le due righe in impostazioni: hash, bolt11, quando, non annullate",
          [True, True],
          [bool(regG and regG["hash"] == hashes[0].hex() and regG["bolt11"].startswith("lnbc10n1cartone")
                and regG.get("quando") and not regG.get("annullata")),
           bool(regH and regH["hash"] == hashes[1].hex() and not regH.get("annullata"))])
    prova("nel corpo del hodl non viaggia nessun preimage: solo l'hash",
          [{"hash", "value", "memo", "expiry", "cltv_expiry"}] * 2, [set(c) for c in corpi])

    # --- 3) fresche: una seconda apertura non riconia e non cancella -----
    r = client.get("/prova-wallet")
    prova("una seconda apertura entro tre minuti: stesse hold, nessuna chiamata in piu'",
          (2, 0, True),
          (len([v for v in VISTI if v[0] == "/v2/invoices/hodl"]),
           len([v for v in VISTI if v[0] == "/v2/invoices/cancel"]),
           regG["bolt11"] in r.text and regH["bolt11"] in r.text))
    prova("...la pulizia adesso non annulla niente (sono fresche)", [],
          asyncio.run(S.ripulisci_hold_prova()))

    # --- 4) passati tre minuti: la pulizia cancella tutt'e due ----------
    dopo = regG["quando"] + S.PROVA_HOLD_VITA_S + 1
    fatte = asyncio.run(S.ripulisci_hold_prova(adesso=dopo))
    canc = [v for v in VISTI if v[0] == "/v2/invoices/cancel"]
    prova("la pulizia annulla G e H con i LORO hash (in base64), una cancel ciascuna",
          (["G", "H"], 2, True),
          (fatte, len(canc),
           {base64.b64decode(v[1]["payment_hash"]).hex() for v in canc} == {h.hex() for h in hashes}))
    prova("...e le righe lo ricordano", [True, True],
          [bool(S._hold_prova_registrata("G").get("annullata")),
           bool(S._hold_prova_registrata("H").get("annullata"))])
    prova("...una seconda pulizia non bussa piu'", ([], 2),
          (asyncio.run(S.ripulisci_hold_prova(adesso=dopo + 60)),
           len([v for v in VISTI if v[0] == "/v2/invoices/cancel"])))

    # --- 5) l'«already canceled» di LND vale come annullata --------------
    prova("annullare di nuovo un hash gia' annullato: LND dice «already canceled» e per noi e' ok",
          True, asyncio.run(S._annulla_hold_prova(hashes[0].hex())))
    prova("...un hash che non e' esadecimale: falso, senza bussare",
          (False, 3), (asyncio.run(S._annulla_hold_prova("zz")),
                       len([v for v in VISTI if v[0] == "/v2/invoices/cancel"])))

    # --- 6) la pagina dopo la pulizia: hold nuove, senza ricancellare ----
    prima = len(VISTI)
    r = client.get("/prova-wallet")
    nuove = [v for v in VISTI[prima:]]
    prova("dopo la pulizia una nuova apertura conia due hold nuove e non cancella niente",
          (2, 0, True),
          (len([v for v in nuove if v[0] == "/v2/invoices/hodl"]),
           len([v for v in nuove if v[0] == "/v2/invoices/cancel"]),
           S._hold_prova_registrata("G")["hash"] != hashes[0].hex()))

    # --- 7) una hold vecchia NON annullata (il server e' morto prima):
    #        l'apertura la cancella prima di coniare la nuova ------------
    regG = S._hold_prova_registrata("G")
    regG["quando"] = regG["quando"] - S.PROVA_HOLD_VITA_S - 5
    S._scrivi_hold_prova("G", regG)
    prima = len(VISTI)
    client.get("/prova-wallet")
    nuove = VISTI[prima:]
    prova("una hold scaduta e mai annullata: prima la cancel del suo hash, poi il hodl nuovo",
          ["/v2/invoices/cancel", "/v2/invoices/hodl"],
          [v[0] for v in nuove])
    prova("...con l'hash giusto", regG["hash"],
          base64.b64decode(nuove[0][1]["payment_hash"]).hex())

    # --- 8) LND muto sul conio: la pagina resta in piedi e lo dice -------
    RISPOSTE["hodl"] = 500
    for l in ("G", "H"):
        rr = S._hold_prova_registrata(l)
        rr["annullata"] = True
        S._scrivi_hold_prova(l, rr)
    r = client.get("/prova-wallet")
    prova("LND che non conia: 200, G e H «non pronta» con il perche', nessun link hold",
          (200, 2, 0, True),
          (r.status_code, r.text.count("non pronta: LND ha risposto 500"),
           r.text.count('class="b hold"'), "cartone muto" in r.text))
    RISPOSTE["hodl"] = 200

    # --- 9) il macaroon di lettura non apre le hold -----------------------
    S.LND_PONTE_MACAROON_HOLD = "0201036c6e64" + "cd" * 40
    for l in ("G", "H"):
        rr = S._hold_prova_registrata(l)
        if rr:
            rr["annullata"] = True
            S._scrivi_hold_prova(l, rr)
    r = client.get("/prova-wallet")
    prova("un macaroon che non apre: «non pronta: LND ha risposto 401: permission denied», pagina in piedi",
          (200, 2), (r.status_code, r.text.count("LND ha risposto 401: permission denied")))

    srv.shutdown()
    srv.server_close()
    print(f"\n  {PASSATE} passate, {FALLITE} fallite")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
