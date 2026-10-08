#!/usr/bin/env python3
"""rgb_http.py — la faccia HTTP di rgb.py, sulla VM «rgb-prova», SOLO sul
loopback (127.0.0.1:8787). Il portatile ci arriva dal tunnel SSH
(`-L 8787:127.0.0.1:8787`), cosi' il server di Barattolo in collaudo puo'
chiedere al wallet mercante una fattura o lo stato senza fare `ssh` da
dentro una rotta. Nient'altro: niente invio, niente chiavi, niente
emissione — quelli restano comandi di rgb.py, a mano.

Un wallet solo, quello che RICEVE i pagamenti (RGB_HTTP_WALLET, default
`barattolo`). Ogni richiesta apre il wallet, fa la sua cosa e chiude,
come rgb.py; un lucchetto serializza le richieste. Mentre gira, niente
`rgb.py <comando> barattolo` a mano (rgb-lib: «never instantiate a wallet
in multiple places») — e alle 03:30 il backup lo apre da solo: in
quell'ora il servizio si ferma.

Rotte (JSON):
  GET  /salute                      {"ok": true, "wallet": "barattolo", "rete": "signet"}
  GET  /saldo                       sats e asset del wallet
  POST /fattura                     {"asset_id": "rgb:…"|null, "quantita": 480|null, "witness": false}
                                    → {"invoice", "recipient_id", "expires_at", "witness"}
  POST /aggiorna                    refresh: ACK, broadcast, conferme → {"trasferimenti": {idx: {...}}}
  GET  /trasferimenti[?asset_id=]   la storia

Avvio (sulla VM, in ~/rgb):  ./venv/bin/python rgb_http.py
"""
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rgb_lib  # noqa: E402
import rgb      # noqa: E402  (rgb.py accanto: _wallet, PROXY, SCADENZA, CONFERME)

WALLET = os.environ.get("RGB_HTTP_WALLET", "barattolo")
PORTA = int(os.environ.get("RGB_HTTP_PORTA", "8787"))
LUCCHETTO = threading.Lock()


def _saldo():
    w, on = rgb._wallet(WALLET)
    b = w.get_btc_balance(on, False)
    asset = []
    for a in w.list_assets([]).nia:
        asset.append({"ticker": a.ticker, "name": a.name, "asset_id": a.asset_id,
                      "precision": a.precision, "issued_supply": a.issued_supply,
                      "settled": a.balance.settled, "spendable": a.balance.spendable,
                      "future": a.balance.future})
    utxo_liberi = sum(1 for u in w.list_unspents(on, False, True)
                      if u.utxo.colorable and not u.rgb_allocations)
    return {"vanilla": b.vanilla.settled, "colored": b.colored.settled,
            "utxo_colorabili_liberi": utxo_liberi, "asset": asset}


def _fattura(corpo):
    aid = corpo.get("asset_id") or None
    q = corpo.get("quantita")
    assegnazione = rgb_lib.Assignment.FUNGIBLE(int(q)) if q else rgb_lib.Assignment.ANY()
    scade = int(time.time()) + rgb.SCADENZA
    w, _ = rgb._wallet(WALLET)
    if corpo.get("witness"):
        r = w.witness_receive(aid, assegnazione, scade, [rgb.PROXY], rgb.CONFERME)
    else:
        r = w.blind_receive(aid, assegnazione, scade, [rgb.PROXY], rgb.CONFERME)
    return {"invoice": r.invoice, "recipient_id": r.recipient_id,
            "expires_at": r.expiration_timestamp, "witness": bool(corpo.get("witness"))}


def _aggiorna():
    w, on = rgb._wallet(WALLET)
    esito = w.refresh(on, None, [], False)
    return {"trasferimenti": {
        str(idx): {"stato": str(r.updated_status) if r.updated_status else None,
                   "errore": r.failure}
        for idx, r in (esito or {}).items()}}


def _trasferimenti(asset_id):
    w, _ = rgb._wallet(WALLET, online=False)
    return {"trasferimenti": [
        {"idx": t.idx, "stato": str(t.status), "tipo": str(t.kind),
         "txid": t.txid, "aggiornato": t.updated_at,
         "assegnazioni": [str(a) for a in t.assignments]}
        for t in w.list_transfers(asset_id or None)]}


class Rotte(BaseHTTPRequestHandler):
    def _json(self, codice, dati):
        corpo = json.dumps(dati, default=str).encode()
        self.send_response(codice)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _corpo(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 65536:
            raise ValueError("corpo troppo grande")
        corpo = json.loads(self.rfile.read(n) or b"{}")
        if not isinstance(corpo, dict):
            raise ValueError("il corpo deve essere un oggetto JSON")
        return corpo

    def _esegui(self, f, *a):
        if not LUCCHETTO.acquire(timeout=120):
            return self._json(503, {"errore": "il wallet e' occupato"})
        try:
            self._json(200, f(*a))
        except rgb_lib.RgbLibError as e:
            self._json(502, {"errore": f"rgb-lib dice: {e}"})
        except Exception as e:  # noqa: BLE001 — il server di prova dice cosa non va
            self._json(500, {"errore": str(e)})
        finally:
            LUCCHETTO.release()

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/salute":
            return self._json(200, {"ok": True, "wallet": WALLET, "rete": "signet"})
        if u.path == "/saldo":
            return self._esegui(_saldo)
        if u.path == "/trasferimenti":
            return self._esegui(_trasferimenti, (parse_qs(u.query).get("asset_id") or [None])[0])
        self._json(404, {"errore": "rotta sconosciuta"})

    def do_POST(self):
        u = urlparse(self.path)
        try:
            corpo = self._corpo()
        except (ValueError, json.JSONDecodeError) as e:
            return self._json(400, {"errore": f"corpo non valido: {e}"})
        if u.path == "/fattura":
            return self._esegui(_fattura, corpo)
        if u.path == "/aggiorna":
            return self._esegui(_aggiorna)
        self._json(404, {"errore": "rotta sconosciuta"})

    def log_message(self, fmt, *a):
        print(time.strftime("%H:%M:%S"), self.command, self.path, a[1] if len(a) > 1 else "")


if __name__ == "__main__":
    rgb._chiavi(WALLET)   # muore subito se il wallet non esiste
    print(f"🟪 rgb_http su 127.0.0.1:{PORTA}, wallet «{WALLET}» — Ctrl-C per fermare")
    HTTPServer(("127.0.0.1", PORTA), Rotte).serve_forever()
