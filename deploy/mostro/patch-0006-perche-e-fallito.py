#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch 0006 del fork — «has failed!» dice PERCHE'.

Si lancia SUL NODO, dentro ~/nodo/mostro-src sul branch barattolo/v0.18.7:
    python3 patch-0006-perche-e-fallito.py
Tocca UN file con UNA sostituzione mirata (l'ancora deve comparire una
volta, o si ferma senza scrivere niente), poi si committa e si esporta
con `git format-patch -1`, come le sorelle.

IL DIFETTO (17 set 2026, lo scambio 3fcdb207: 14.837 sats fermi): il
payout a chi compra e' fallito tre volte e il log diceva solo
«Invoice with hash: … has failed!» + «has 3 failed payments retries».
Quella riga nasce in UN posto solo — il watcher di `do_payment` in
`src/app/release.rs` — e SOLO quando lo stream di `SendPaymentV2` (gRPC,
non REST) consegna un aggiornamento con `status = FAILED`. Cioe' LND il
pagamento l'ha preso in carico e l'ha fallito LUI, e nello stesso
messaggio c'e' scritto il motivo: `payment.failure_reason`
(NO_ROUTE, INSUFFICIENT_BALANCE, TIMEOUT, INCORRECT_PAYMENT_DETAILS,
ERROR). mostrod quel campo non lo legge in NESSUN punto del sorgente —
censiti `release.rs` e `lightning/mod.rs` — e ci ha fatto tirare a
indovinare.

LA CURA: la stessa riga, col motivo (nome e codice grezzo, cosi' un
valore che questa versione di prost non conosce si vede lo stesso) e
quanti tentativi HTLC sono partiti — zero vuol dire che LND non ha
nemmeno provato una strada, che e' la meta' della diagnosi.
Solo log: nessun comportamento cambia.

⚠️ MAI COMPILATA QUI (sul PC non c'e' cargo): la forma e' ricalcata
sulla riga accanto, che fa gia' `PaymentStatus::try_from(i32)` con lo
stesso prost — ma il primo `cargo build` e' quello sul nodo, e va
guardato.
"""
import re, sys, io


def leggi(p):
    with io.open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()


def scrivi(p, t):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(t)


def una(t, rx, nuovo, dove):
    m = re.findall(rx, t, flags=re.S)
    if len(m) != 1:
        sys.exit("FERMO: in %s l'ancora compare %d volte (attesa 1) — niente scritto" % (dove, len(m)))
    return re.sub(rx, lambda _: nuovo, t, count=1, flags=re.S)


SECCO = "--secco" in sys.argv

p = "src/app/release.rs"
t = leggi(p)
t = una(t,
    r"                                warn!\(\n"
    r"                                    \"Order Id \{\}: Invoice with hash: \{\} has failed!\",\n"
    r"                                    order\.id, msg\.payment\.payment_hash\n"
    r"                                \);",
    "                                // LND says WHY in the same update: surface it, or a\n"
    "                                // failed payout is a guessing game (no route? balance?\n"
    "                                // timeout?). Zero HTLC attempts means LND never even\n"
    "                                // tried a route.\n"
    "                                warn!(\n"
    "                                    \"Order Id {}: Invoice with hash: {} has failed! reason: {:?} (code {}), htlc attempts: {}\",\n"
    "                                    order.id,\n"
    "                                    msg.payment.payment_hash,\n"
    "                                    fedimint_tonic_lnd::lnrpc::PaymentFailureReason::try_from(\n"
    "                                        msg.payment.failure_reason\n"
    "                                    )\n"
    "                                    .ok(),\n"
    "                                    msg.payment.failure_reason,\n"
    "                                    msg.payment.htlcs.len()\n"
    "                                );", p)
if SECCO:
    print("a secco: l'ancora c'e', UNA volta — niente scritto")
else:
    scrivi(p, t)
    print("scritto:", p)
