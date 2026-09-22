#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch 0002 del fork — `dev_fee_percentage = 0` diventa valido.

Si lancia SUL NODO, dentro ~/nodo/mostro-src sul branch barattolo/vX.Y.Z:
    python3 patch-0002-dev-fee-zero.py --secco   # prova e basta
    python3 patch-0002-dev-fee-zero.py           # scrive
Tocca UN file, `src/config/util.rs`, con due sostituzioni mirate (la
guardia e un test nuovo): ogni ancora deve comparire UNA volta, o si
ferma senza scrivere niente.

IL DIFETTO: `MIN_DEV_FEE_PERCENTAGE` e' 0.10 e la guardia usa `<`
stretto, quindi lo zero veniva rifiutato — un coordinator che non riesce
a pagare la dev fee non aveva nessun modo di dirlo. Lo zero e' gia' uno
stato supportato nel resto del codice (`find_unpaid_dev_fees` ha
`AND dev_fee > 0` nella query) tranne in quel controllo.

LA CURA allenta SOLO il minimo, mai il massimo: i negativi restano
invalidi, la fascia fra zero e il minimo resta invalida, il tetto non si
tocca. Confronti di ordinamento, nessuna uguaglianza fra float. Da
proporre a monte. Il valore lo decide il config (`0.0`, non `0`: il campo
e' un f64 e il TOML distingue).

Fino al 22 set 2026 esisteva solo come `.patch`: il patcher e' nato con la
salita alla 0.18.8, perche' tutte e sette abbiano la stessa forma.
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
    # la guardia
    ("    // Validate dev_fee_percentage range\n"
     "    if dev_fee < MIN_DEV_FEE_PERCENTAGE {\n"
     "        return Err(MostroInternalErr(ServiceError::IOError(format!(\n"
     "            \"dev_fee_percentage ({}) is below minimum ({})\",\n",
     "    // Validate dev_fee_percentage range. `0` is the explicit opt-out, i.e.\n"
     "    // no dev fee at all, so only negatives and the band between zero and the\n"
     "    // minimum are rejected. Ordering comparisons only, no float equality.\n"
     "    if dev_fee < 0.0 || (dev_fee > 0.0 && dev_fee < MIN_DEV_FEE_PERCENTAGE) {\n"
     "        return Err(MostroInternalErr(ServiceError::IOError(format!(\n"
     "            \"dev_fee_percentage ({}) is below minimum ({}); use 0 to disable the dev fee\",\n"),
    # il test nuovo, fra i due vecchi che provano fondo e tetto
    ("        assert!(err.to_string().contains(\"below minimum\"));\n"
     "    }\n"
     "\n"
     "    #[test]\n"
     "    fn dev_fee_above_maximum_is_rejected() {\n",
     "        assert!(err.to_string().contains(\"below minimum\"));\n"
     "    }\n"
     "\n"
     "    #[test]\n"
     "    fn dev_fee_zero_is_accepted_as_opt_out() {\n"
     "        let mut settings = base_settings();\n"
     "        settings.mostro.dev_fee_percentage = 0.0;\n"
     "        assert!(validate_mostro_settings(&settings).is_ok());\n"
     "    }\n"
     "\n"
     "    #[test]\n"
     "    fn dev_fee_above_maximum_is_rejected() {\n"),
]

p = "src/config/util.rs"
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
print("Adesso: cargo test -- config::util, il commit, git format-patch")
