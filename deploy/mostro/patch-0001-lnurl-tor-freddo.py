#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch 0001 del fork — i tre budget LNURL da 4s/2s/2s a 30s/15s/10s.

Si lancia SUL NODO, dentro ~/nodo/mostro-src sul branch barattolo/vX.Y.Z:
    python3 patch-0001-lnurl-tor-freddo.py --secco   # prova e basta
    python3 patch-0001-lnurl-tor-freddo.py           # scrive
Tocca UN file, `src/lnurl.rs`, con tre sostituzioni mirate: ogni ancora
deve comparire UNA volta, o si ferma senza scrivere niente. Poi si
committa e si esporta con `git format-patch`, come le sorelle.

IL DIFETTO (7 set 2026, la dev fee che si impianta): un coordinator che
esce solo da Tor misura 10,6 secondi per la prima richiesta LNURL su
circuito freddo — `dns 0.138s`, `connect 0.138s`, `tls 10.336s` — contro
0,9 a circuito caldo. I tre budget sono `const` nel binario: 4s la
richiesta, 2s la connessione, 2s il DNS. Nessuno dei tre e' raggiungibile
a freddo, e `connect` MENTE sotto il proxy trasparente (il kernel chiude
la stretta di mano locale prima che Tor guardi il pacchetto: tutto il
costo compare nel TLS).

LA CURA: circa 3x il costo misurato, e i commenti dicono il prezzo
invece di raccomandare la brevita'. Da proporre a monte.

Fino al 22 set 2026 questa patch esisteva solo come `.patch` (era un
ritocco a mano sul nodo): il patcher e' nato con la salita alla 0.18.8,
perche' tutte e sette abbiano la stessa forma — ancore uniche, `--secco`.
"""
import io
import sys

SECCO = "--secco" in sys.argv


def leggi(p):
    with io.open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()


def scrivi(p, t):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(t)


# (ancora, testo nuovo): sempre "al posto"
SOSTITUZIONI = [
    ("/// Cap on a single LNURL HTTP round-trip (connect + response).\n"
     "/// Kept short so a silent/hanging host cannot stall the serial message\n"
     "/// loop for long (DoS bound, not elimination).\n"
     "const LNURL_REQUEST_TIMEOUT: Duration = Duration::from_secs(4);\n",
     "/// Cap on a single LNURL HTTP round-trip (connect + response).\n"
     "/// Bounds how long a silent/hanging host can stall the serial message\n"
     "/// loop (DoS bound, not elimination). Sized for coordinators whose\n"
     "/// egress is Tor: a cold circuit measured 10.6s to first byte, nearly\n"
     "/// all of it in the TLS handshake, so a 4s budget failed every LNURL\n"
     "/// resolution until some unrelated request happened to warm the circuit.\n"
     "const LNURL_REQUEST_TIMEOUT: Duration = Duration::from_secs(30);\n"),
    ("/// Cap on establishing the TCP/TLS connection alone, so an unroutable or\n"
     "/// filtered host fails before burning the full request budget.\n"
     "const LNURL_CONNECT_TIMEOUT: Duration = Duration::from_secs(2);\n",
     "/// Cap on establishing the TCP/TLS connection alone, so an unroutable or\n"
     "/// filtered host fails before burning the full request budget.\n"
     "/// Behind a transparent Tor proxy this one barely bites: the local SYN\n"
     "/// completes at once and the circuit build shows up inside the TLS\n"
     "/// handshake, i.e. inside the request budget above.\n"
     "const LNURL_CONNECT_TIMEOUT: Duration = Duration::from_secs(15);\n"),
    ("/// loop longer than the HTTP timeouts below.\n"
     "const LNURL_DNS_TIMEOUT: Duration = Duration::from_secs(2);\n",
     "/// loop longer than the HTTP timeouts below.\n"
     "const LNURL_DNS_TIMEOUT: Duration = Duration::from_secs(10);\n"),
]

p = "src/lnurl.rs"
if not __import__("os").path.isfile(p):
    sys.exit("FERMO: non sono nella radice di mostro-src — niente scritto")
t = leggi(p)
for ancora, nuovo in SOSTITUZIONI:
    # i fine-riga sono quelli del file che si trova
    if "\r\n" in t:
        ancora, nuovo = ancora.replace("\n", "\r\n"), nuovo.replace("\n", "\r\n")
    if nuovo in t:
        sys.exit("FERMO: %s porta gia' questa modifica — la patch e' gia' applicata?" % p)
    n = t.count(ancora)
    if n != 1:
        sys.exit("FERMO: in %s l'ancora compare %d volte (attesa 1) — niente scritto:\n%s"
                 % (p, n, ancora))
    t = t.replace(ancora, nuovo)
if SECCO:
    print("A SECCO: %d sostituzioni in %s, tutte le ancore uniche. Niente scritto."
          % (len(SOSTITUZIONI), p))
    sys.exit(0)
scrivi(p, t)
print("FATTO: %d sostituzioni in %s" % (len(SOSTITUZIONI), p))
print("Adesso: cargo test -- lnurl, il commit, git format-patch")
