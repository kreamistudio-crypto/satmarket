#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch 0003 del fork — i due cappelli della dev fee da 15s e 20s a 75s e 90s.

Si lancia SUL NODO, dentro ~/nodo/mostro-src sul branch barattolo/vX.Y.Z:
    python3 patch-0003-dev-fee-cappelli.py --secco   # prova e basta
    python3 patch-0003-dev-fee-cappelli.py           # scrive
Tocca UN file, `src/app/dev_fee.rs`, con tre sostituzioni mirate: ogni
ancora deve comparire UNA volta, o si ferma senza scrivere niente.

IL DIFETTO: sopra la risoluzione LNURL della dev fee ci sono DUE timeout
esterni — 15 s attorno a `resolv_ln_address`, 20 s attorno a tutto il
blocco — e la risoluzione sono due richieste HTTPS su due domini diversi
(`walletofsatoshi.com` per il `.well-known`, `livingroomofsatoshi.com`
per il callback), ognuna col suo circuito Tor da scaldare: 10,6 + 10,6
secondi. Senza questa patch la 0001 non cura la dev fee: i suoi 30 s
restano invisibili dietro il 15 che taglia per primo.

LA CURA: 75 supera due richieste da 30; 90 resta sopra i 75 o tornerebbe
a decidere lui. Entrambi sotto i 5 minuti dopo i quali una prenotazione
`PENDING` viene liberata. I timeout attorno al PAGAMENTO via LND non si
toccano: il guasto era in risoluzione. Da proporre a monte.

Fino al 22 set 2026 esisteva solo come `.patch`: il patcher e' nato con la
salita alla 0.18.8, perche' tutte e sette abbiano la stessa forma.
⚠️ Dalla 0.18.8 upstream tocca questo file per una riga (lo stato
`Initiated` di LND, lontana dai cappelli): le ancore restano uniche.
"""
import io
import os
import sys

SECCO = "--secco" in sys.argv


def leggi(p):
    with io.open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()


def scrivi(p, t):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(t)


SOSTITUZIONI = [
    # il cappello esterno, da 20 a 90
    ("        let (payment_request, payment_hash_hex) = match tokio::time::timeout(\n"
     "            std::time::Duration::from_secs(20),\n"
     "            resolve_dev_fee_invoice(&order, keys),\n",
     "        // Outer bound on the whole resolution. Must stay above the inner cap\n"
     "        // in resolve_dev_fee_invoice, otherwise this one decides instead.\n"
     "        let (payment_request, payment_hash_hex) = match tokio::time::timeout(\n"
     "            std::time::Duration::from_secs(90),\n"
     "            resolve_dev_fee_invoice(&order, keys),\n"),
    # ...e la riga di log che lo nomina
    ("                    \"Dev fee invoice resolution timeout (20s) for order {}\",\n",
     "                    \"Dev fee invoice resolution timeout (90s) for order {}\",\n"),
    # il cappello interno, da 15 a 75
    ("    let payment_request = tokio::time::timeout(\n"
     "        std::time::Duration::from_secs(15),\n"
     "        resolv_ln_address(\n"
     "            DEV_FEE_LIGHTNING_ADDRESS,\n",
     "    // Two HTTPS round-trips on two different domains (.well-known, then the\n"
     "    // callback), each bounded by LNURL_REQUEST_TIMEOUT. A Tor-routed\n"
     "    // coordinator pays a cold-circuit cost of ~10.6s per domain, so this cap\n"
     "    // must clear twice the per-request budget or it truncates a resolution\n"
     "    // that was about to succeed.\n"
     "    let payment_request = tokio::time::timeout(\n"
     "        std::time::Duration::from_secs(75),\n"
     "        resolv_ln_address(\n"
     "            DEV_FEE_LIGHTNING_ADDRESS,\n"),
]

p = "src/app/dev_fee.rs"
if not os.path.isfile(p):
    sys.exit("FERMO: non sono nella radice di mostro-src — niente scritto")
t = leggi(p)
for ancora, nuovo in SOSTITUZIONI:
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
print("Adesso: cargo test -- dev_fee, il commit, git format-patch")
