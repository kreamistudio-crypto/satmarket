#!/usr/bin/env python3
"""Una REQ sola a un relay, e gli eventi in uscita uno per riga (JSONL),
pronti per `strfry import`. Solo libreria standard: gira nel container
del relay, che ha python3 per il plugin e niente altro.

PERCHE' ESISTE (17 nov 2026, cantiere relay-zapstore, letto nel sorgente
di strfry, `cmd_router.cpp`): lo specchio (`strfry router`) manda ai
relay una REQ con `"limit": 0`, cioe' chiede SOLO quel che arriva da
quel momento in poi. Niente storico: quel che era stato pubblicato prima
che il flusso esistesse non arriva da solo, e `strfry sync` non serve
perche' relay.zapstore.dev non parla negentropy (provato: «the message
type must be one between EVENT, REQ, CLOSE, COUNT and AUTH»). Questo
file fa quel che il router non fa, una volta.

USO, dalla macchina del relay (il file nel container, poi la pesca):
  sudo docker cp deploy/relay/pesca-eventi.py relay:/tmp/pesca-eventi.py
  cd /opt/relay && sudo docker compose exec -T relay sh -c \
    "python3 /tmp/pesca-eventi.py wss://relay.zapstore.dev '{\"kinds\":[32267],\"authors\":[\"HEX\"]}' | /app/strfry import"
Il filtro e' quello del flusso in `router.conf`; a schermo esce
«pescati N eventi» e il conto dell'import. Un doppione non fa danno.
"""
import base64
import json
import os
import socket
import ssl
import struct
import sys
from urllib.parse import urlparse


def main():
    if len(sys.argv) != 3:
        sys.exit("uso: pesca-eventi.py wss://relay '{filtro json}'")
    url, filtro = sys.argv[1], json.loads(sys.argv[2])
    u = urlparse(url)
    host, porta = u.hostname, u.port or (443 if u.scheme == "wss" else 80)
    s = socket.create_connection((host, porta), timeout=20)
    if u.scheme == "wss":
        s = ssl.create_default_context().wrap_socket(s, server_hostname=host)
    chiave = base64.b64encode(os.urandom(16)).decode()
    s.sendall((f"GET {u.path or '/'} HTTP/1.1\r\nHost: {host}\r\n"
               "Upgrade: websocket\r\nConnection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {chiave}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
    testa = b""
    while b"\r\n\r\n" not in testa:
        pezzo = s.recv(1)
        if not pezzo:
            sys.exit("il relay ha chiuso durante la stretta di mano")
        testa += pezzo
    if b" 101 " not in testa.split(b"\r\n")[0]:
        sys.exit("stretta di mano rifiutata: " + testa.split(b"\r\n")[0].decode(errors="replace"))

    def manda(testo):
        b = testo.encode()
        m = os.urandom(4)
        intesta = bytes([0x81])
        if len(b) < 126:
            intesta += bytes([0x80 | len(b)])
        elif len(b) < 65536:
            intesta += bytes([0x80 | 126]) + struct.pack(">H", len(b))
        else:
            intesta += bytes([0x80 | 127]) + struct.pack(">Q", len(b))
        s.sendall(intesta + m + bytes(c ^ m[i % 4] for i, c in enumerate(b)))

    def leggi_esatto(n):
        d = b""
        while len(d) < n:
            pezzo = s.recv(n - len(d))
            if not pezzo:
                raise EOFError
            d += pezzo
        return d

    def ricevi():
        """Un messaggio di testo intero (frammenti compresi)."""
        corpo = b""
        while True:
            h = leggi_esatto(2)
            fine, op, ln = h[0] & 0x80, h[0] & 0x0F, h[1] & 0x7F
            if ln == 126:
                ln = struct.unpack(">H", leggi_esatto(2))[0]
            elif ln == 127:
                ln = struct.unpack(">Q", leggi_esatto(8))[0]
            dati = leggi_esatto(ln)
            if op == 0x8:
                raise EOFError
            if op == 0x9:          # ping → pong
                manda_grezzo = bytes([0x8A, 0x80]) + b"\x00\x00\x00\x00"
                s.sendall(manda_grezzo)
                continue
            corpo += dati
            if fine:
                return corpo.decode("utf-8", errors="replace")

    manda(json.dumps(["REQ", "pesca", filtro]))
    quanti = 0
    try:
        while True:
            m = json.loads(ricevi())
            if m[0] == "EVENT" and m[1] == "pesca":
                print(json.dumps(m[2], separators=(",", ":"), ensure_ascii=False))
                quanti += 1
            elif m[0] == "EOSE":
                break
            elif m[0] in ("NOTICE", "CLOSED"):
                print("relay:", m[1:], file=sys.stderr)
                if m[0] == "CLOSED":
                    break
    except EOFError:
        print("il relay ha chiuso prima dell'EOSE", file=sys.stderr)
    manda(json.dumps(["CLOSE", "pesca"]))
    print(f"pescati {quanti} eventi", file=sys.stderr)


if __name__ == "__main__":
    main()
