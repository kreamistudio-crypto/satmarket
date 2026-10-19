# -*- coding: utf-8 -*-
"""
IL SATS ROUTING DI CARTONE (19 ott 2026, cantiere swap-preventivo).

Un SATS Routing finto, su una porta di questo computer, per provare lo
swap SENZA sats e senza bussare al servizio vero: nel collaudo, nei giri
dal vivo e sulla VM di collaudo (regola di Andrea: ogni tappa dello swap
si prova li' prima di accendere SWAP_ATTIVO in produzione). Il server lo
trova con `SWAP_API_BASE = "http://127.0.0.1:<porta>"`; in MODALITA_COLLAUDO
una base fuori dal computer non si legge mai.

COSA RISPONDE, oggi (tappa 2, il preventivo): `GET /v2/swap/reverse`, le
tariffe dello swap Lightning -> on-chain, coi NUMERI VERI letti
dall'API di SATS Routing il 16 ott 2026 (0,6 %, 324 di rete per il loro
invio, ~234 per il ritiro, da 2.142 a 5.000.000 sats). L'impronta della
tariffa (`hash`) e' INVENTATA e non e' esadecimale: un esadecimale da 64
in un file del repo fa rossa la CI, e qui non serve che sia vera, serve
che CAMBI quando cambiano le tariffe.

I MODI, a comando (`GET /cartone/modo?m=...`):
  - `normale`  le tariffe del 16 ott;
  - `cambiata` stesse tariffe con 0,7 % e un'impronta diversa: e' il
               caso «le tariffe sono cambiate» del preventivo;
  - `giu`      risponde 503, come un servizio che non c'e';
  - `storta`   risponde 200 con una forma che non e' quella vera.
`GET /cartone/visto` dice quante letture ha avuto e l'ultima
intestazione `Referral`: e' cosi' che si prova che il codice partner va
in ogni chiamata.

Le tappe dopo (la creazione dello swap, gli stati, il recupero) si
aggiungeranno QUI, col calco dei documenti di SATS Routing.

USO:  python cartone_satsrouting.py [--porta 9077]
"""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

# Le tariffe lette dall'API vera il 16 ott 2026 (studio swap, voce
# «Gli swap di SATS Routing dentro Barattolo»), con l'impronta finta.
TARIFFE_16_OTT = {
    "BTC": {
        "BTC": {"hash": "cartone-tariffa-16ott", "rate": 1,
                "limits": {"maximal": 5_000_000, "minimal": 2_142},
                "fees": {"percentage": 0.6,
                         "minerFees": {"claim": 234, "lockup": 324}}},
        "L-BTC": {"hash": "cartone-tariffa-liquid-16ott", "rate": 1,
                  "limits": {"maximal": 5_000_000, "minimal": 100},
                  "fees": {"percentage": 0.4,
                           "minerFees": {"claim": 20, "lockup": 27}}}}}

STATO = {"modo": "normale", "letture": 0, "referral": None}
MODI = ("normale", "cambiata", "giu", "storta")


def tariffe_del_modo(modo):
    """La risposta di `/v2/swap/reverse` nel modo chiesto (None = giu)."""
    if modo == "giu":
        return None
    if modo == "storta":
        return {"BTC": {"BTC": {"hash": "x", "fees": "zero"}}}
    dati = json.loads(json.dumps(TARIFFE_16_OTT))
    if modo == "cambiata":
        c = dati["BTC"]["BTC"]
        c["hash"] = "cartone-tariffa-cambiata"
        c["fees"]["percentage"] = 0.7
    return dati


class Sportello(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass        # zitto: il collaudo ha le sue righe

    def _rispondi(self, codice, corpo):
        dati = json.dumps(corpo).encode("utf-8")
        self.send_response(codice)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dati)))
        self.end_headers()
        self.wfile.write(dati)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/v2/swap/reverse":
            STATO["letture"] += 1
            STATO["referral"] = self.headers.get("Referral")
            dati = tariffe_del_modo(STATO["modo"])
            if dati is None:
                return self._rispondi(503, {"error": "cartone giu"})
            return self._rispondi(200, dati)
        if u.path == "/cartone/modo":
            m = (parse_qs(u.query).get("m") or [""])[0]
            if m not in MODI:
                return self._rispondi(400, {"modi": list(MODI)})
            STATO["modo"] = m
            return self._rispondi(200, {"modo": m})
        if u.path == "/cartone/visto":
            return self._rispondi(200, dict(STATO))
        return self._rispondi(404, {"error": "non c'e'"})


def avvia(porta=0):
    """Accende il cartone in un filo suo, su 127.0.0.1. Torna (server,
    porta): porta 0 = la sceglie il sistema, e il collaudo la legge."""
    srv = ThreadingHTTPServer(("127.0.0.1", int(porta)), Sportello)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def main(argv):
    porta = 9077
    if "--porta" in argv:
        porta = int(argv[argv.index("--porta") + 1])
    srv = ThreadingHTTPServer(("127.0.0.1", porta), Sportello)
    print(f"🧃 SATS Routing di cartone su http://127.0.0.1:{porta} "
          f"(modo «{STATO['modo']}»; si cambia con /cartone/modo?m=...)",
          flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
