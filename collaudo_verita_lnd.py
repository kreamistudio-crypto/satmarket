# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA DOMANDA A LND (set 2026, cantiere dei pagamenti in volo).

`prove.py` fa girare il giudice, la ronda e la rotta del moderatore con
un LND di cartone messo DIETRO `_chiedi_lnd`: quindi l'unica funzione
che non vede mai girare e' proprio `_chiedi_lnd`, cioe' quella che parla
davvero col nodo — il TLS col certificato guardato, il macaroon
nell'header, il payment hash che nell'URL viaggia in base64 e non in
esadecimale, e una risposta che e' uno STREAM (su un pagamento in volo
LND la tiene aperta finche' non finisce). In CI httpx non c'e', e per
questo il collaudo vive qui e non la'.

Qui `_chiedi_lnd`, `_lnd_stato_da_riga` e `_lnd_configurato` sono quelli
VERI, presi da server.py con `ast` (mai `import server`: vorrebbe il
config e mezzo mondo). Di finto c'e' un LND che parla HTTPS su
127.0.0.1 con un certificato fatto al momento, e risponde come la REST
di LND risponde a `/v2/router/track/{hash}`.

⚠️ NON SOSTITUISCE IL DRILL SUL NODO VERO: la forma delle risposte di
LND qui dentro l'ho scritta IO, a memoria della sua API. Questo collaudo
prova che il nostro lato della conversazione e' giusto (e che ogni
guasto finisce in «muto», mai in un falso «assente»); che LND risponda
davvero cosi' lo dice solo il drill — vedi docs/PRODUZIONE.md, «I
PAGAMENTI DA VERIFICARE».

Uso:  python collaudo_verita_lnd.py
"""
import ast
import asyncio
import base64
import datetime
import http.server
import ipaddress
import json
import os
import re
import ssl
import sys
import tempfile
import threading
import time

import httpx
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

QUI = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(QUI, "server.py"), encoding="utf-8").read()
ALBERO = ast.parse(SRC)
PASSATE = FALLITE = 0


def pezzo(nome):
    for n in ALBERO.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and n.name == nome:
            return ast.get_source_segment(SRC, n)
    raise KeyError(nome)


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}\n      avuto:  {avuto!r}")


def certificato(cartella, nome):
    """Un certificato usa-e-getta per 127.0.0.1, come il tls.cert di LND
    copiato sul VPS (SAN `127.0.0.1`)."""
    chiave = ec.generate_private_key(ec.SECP256R1())
    chi = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "lnd finto")])
    ora = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(chi).issuer_name(chi)
            .public_key(chiave.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(ora - datetime.timedelta(minutes=5))
            .not_valid_after(ora + datetime.timedelta(hours=1))
            .add_extension(x509.SubjectAlternativeName(
                [x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), False)
            .add_extension(x509.BasicConstraints(ca=True, path_length=None),
                           True)
            .sign(chiave, hashes.SHA256()))
    pc, pk = (os.path.join(cartella, nome + ".cert"),
              os.path.join(cartella, nome + ".key"))
    open(pc, "wb").write(cert.public_bytes(serialization.Encoding.PEM))
    open(pk, "wb").write(chiave.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()))
    return pc, pk


MACAROON = "0201036c6e64" + "ab" * 40      # di cartone: non apre niente
H_OK, H_VOLO, H_NO, H_MAI = ("11" * 32, "22" * 32, "33" * 32, "44" * 32)
PAGAMENTI = {H_OK: "SUCCEEDED", H_VOLO: "IN_FLIGHT", H_NO: "FAILED"}
VISTI = []       # (percorso, macaroon ricevuto)


class FintoLnd(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"     # corpo chiuso dalla connessione

    def log_message(self, *a):
        pass

    def do_GET(self):
        VISTI.append((self.path, self.headers.get("Grpc-Metadata-macaroon")))
        if self.headers.get("Grpc-Metadata-macaroon") != MACAROON:
            return self._rispondi(500, {"error": {
                "code": 2, "message": "verification failed: signature "
                "mismatch after caveat verification"}})
        m = re.fullmatch(r"/v2/router/track/([A-Za-z0-9_=-]+)", self.path)
        if not m:
            # quel che il gateway REST dice di una ROTTA che non c'e'
            return self._rispondi(404, {"code": 5, "message": "Not Found",
                                        "details": []})
        try:
            h = base64.urlsafe_b64decode(m.group(1)).hex()
        except Exception:
            return self._rispondi(400, {"code": 3, "message": "bad hash"})
        stato = PAGAMENTI.get(h)
        if not stato:
            return self._rispondi(404, {"error": {
                "code": 5, "message": "payment isn't initiated",
                "details": []}})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write((json.dumps({"result": {
            "payment_hash": h, "status": stato, "htlcs": []}}) + "\n")
            .encode())
        self.wfile.flush()
        if stato == "IN_FLIGHT":
            # LND tiene aperto lo stream finche' il pagamento non finisce
            time.sleep(6)

    def _rispondi(self, codice, corpo):
        self.send_response(codice)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write((json.dumps(corpo) + "\n").encode())


def main():
    print("\n[la domanda a LND, dal vivo contro un LND di cartone]")
    with tempfile.TemporaryDirectory() as tmp:
        cert, chiave = certificato(tmp, "lnd")
        altro_cert, _ = certificato(tmp, "un-altro")
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FintoLnd)
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.load_cert_chain(cert, chiave)
        srv.socket = tls.wrap_socket(srv.socket, server_side=True)
        srv.daemon_threads = True
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        porta = srv.server_address[1]

        detto = []
        amb = {"base64": base64, "ssl": ssl, "httpx": httpx, "json": json,
               "re": re, "LND_ATTESA_S": 8,
               "LND_PONTE_URL": f"https://127.0.0.1:{porta}",
               "LND_PONTE_CERT": cert,
               "LND_PONTE_MACAROON_LETTURA": MACAROON,
               "LND_SUCCEEDED": "SUCCEEDED", "LND_IN_FLIGHT": "IN_FLIGHT",
               "LND_FAILED": "FAILED", "LND_ASSENTE": "assente",
               "LND_MUTO": "muto", "LND_SPENTO": "spento",
               "print": lambda *a, **k: detto.append(" ".join(map(str, a)))}
        for nome in ("_lnd_configurato", "_lnd_stato_da_riga", "_chiedi_lnd"):
            exec(pezzo(nome), amb)
        chiedi = lambda h: asyncio.run(amb["_chiedi_lnd"](h))

        prova("SUCCEEDED si legge", "SUCCEEDED", chiedi(H_OK))
        prova("...e l'hash nell'URL viaggia in base64url, non in hex",
              "/v2/router/track/" + base64.urlsafe_b64encode(
                  bytes.fromhex(H_OK)).decode(), VISTI[-1][0])
        prova("FAILED si legge", "FAILED", chiedi(H_NO))
        t0 = time.time()
        prova("IN_FLIGHT si legge", "IN_FLIGHT", chiedi(H_VOLO))
        prova("...senza aspettare che lo stream finisca (LND lo tiene "
              "aperto)", True, time.time() - t0 < 3)
        prova("un hash mai visto: «assente»", "assente", chiedi(H_MAI))
        prova("un hash che non e' esadecimale: muto, senza bussare",
              ("muto", len(VISTI)), (chiedi("non-e-hex"), len(VISTI)))

        amb["LND_PONTE_URL"] = f"https://127.0.0.1:{porta}/rotta-sbagliata"
        prova("una ROTTA sbagliata (404 «Not Found»): muto, MAI assente",
              "muto", chiedi(H_MAI))
        amb["LND_PONTE_URL"] = f"https://127.0.0.1:{porta}"

        amb["LND_PONTE_MACAROON_LETTURA"] = "0201036c6e64" + "cd" * 40
        prova("un macaroon che non apre: muto", "muto", chiedi(H_OK))
        amb["LND_PONTE_MACAROON_LETTURA"] = MACAROON

        visti = len(VISTI)
        amb["LND_PONTE_CERT"] = altro_cert
        prova("un certificato che non e' quello guardato: muto", "muto",
              chiedi(H_OK))
        prova("...e il macaroon NON e' partito", visti, len(VISTI))
        amb["LND_PONTE_CERT"] = os.path.join(tmp, "non-c-e.cert")
        prova("il tls.cert che manca: muto, non un'eccezione", "muto",
              chiedi(H_OK))
        amb["LND_PONTE_CERT"] = cert

        amb["LND_PONTE_MACAROON_LETTURA"] = ""
        prova("senza macaroon nel config: spento, senza bussare",
              ("spento", len(VISTI)), (chiedi(H_OK), len(VISTI)))
        amb["LND_PONTE_MACAROON_LETTURA"] = "INCOLLA_QUI_IL_MACAROON"
        prova("col segnaposto dell'esempio: spento", "spento", chiedi(H_OK))
        amb["LND_PONTE_MACAROON_LETTURA"] = MACAROON

        srv.shutdown()
        srv.server_close()
        prova("il ponte giu': muto", "muto", chiedi(H_OK))
        prova("nel journal non finisce MAI il macaroon", [],
              [r for r in detto if MACAROON in r or "cd" * 40 in r])
        prova("...ma il tipo del guasto si'", True,
              any("LND non ha risposto" in r for r in detto))

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
