#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch 0004 del fork — un prezzo MAI visto risponde invece di tacere.

Si lancia SUL NODO, dentro ~/nodo/mostro-src sul branch barattolo/v0.18.7:
    python3 patch-0004-prezzo-mai-visto.py
Tocca tre file con sostituzioni mirate (ogni ancora deve comparire UNA
volta, o si ferma senza scrivere niente), poi si committa e si esporta
con `git format-patch -1`, che e' la forma in cui il fork vive nel repo.

IL DIFETTO (15 set 2026, l'ordine di Alan): la cache del prezzo e' solo
in RAM e il primo tick dopo un riavvio puo' fallire (Tor freddo, un
provider giu'). Finche' NESSUN prezzo e' mai entrato, `get_bitcoin_price`
torna `NoAPIResponse`, che ai tre confini dell'ordine (`order.rs`,
`take_buy.rs`, `take_sell.rs`) e' un errore INTERNO: un WARN nel log e
nessuna risposta all'utente. Un prezzo VECCHIO invece risponde gia'
`PriceTooStale` come cant-do. Per chi scambia i due casi sono lo stesso
— «adesso non ti so dire il prezzo» — quindi si risponde con lo stesso
motivo. E' un ritocco ai tre confini, non al PriceManager: la
distinzione interna fra «mai visto» e «troppo vecchio» resta com'e', con
i suoi log e i suoi test.
"""
import re, sys, io

def leggi(p):
    with io.open(p, "r", encoding="utf-8", newline="") as f: return f.read()
def scrivi(p, t):
    with io.open(p, "w", encoding="utf-8", newline="") as f: f.write(t)
def una(t, rx, nuovo, dove):
    m = re.findall(rx, t, flags=re.S)
    if len(m) != 1:
        sys.exit("FERMO: in %s l'ancora compare %d volte (attesa 1) — niente scritto" % (dove, len(m)))
    return re.sub(rx, nuovo, t, count=1, flags=re.S)

# ── order.rs: il ramo Err(_) del quote (e il test che lo fissava a NoAPIResponse)
p = "src/app/order.rs"; t = leggi(p)
t = una(t,
    r"            Err\(_\) => \{\n                return Err\(MostroInternalErr\(ServiceError::NoAPIResponse\)\);\n            \}",
    "            // No price at all yet (cold cache after a restart, every\n"
    "            // provider down): for the user this is the same as a stale\n"
    "            // one — \"no usable price right now\" — so answer the same\n"
    "            // cant-do instead of a silent internal error.\n"
    "            Err(_) => {\n"
    "                return Err(MostroCantDo(CantDoReason::PriceTooStale));\n"
    "            }", p)
t = una(t,
    r"        async fn market_priced_order_without_price_data_fails\(\) \{\n"
    r"            let ctx = create_ctx\(\)\.await;\n"
    r"            // No override and no global PriceManager → NoAPIResponse\.\n"
    r"            let order = order_with\(0, \"QUOTE2\"\);\n"
    r"            let err = calculate_and_check_quote\(&ctx, &order, &100\)\n"
    r"                \.await\n"
    r"                \.unwrap_err\(\);\n"
    r"            assert!\(matches!\(\n"
    r"                err,\n"
    r"                MostroInternalErr\(ServiceError::NoAPIResponse\)\n"
    r"            \)\);",
    "        async fn market_priced_order_without_price_data_is_a_cant_do() {\n"
    "            let ctx = create_ctx().await;\n"
    "            // No override and no global PriceManager → the user gets a\n"
    "            // PriceTooStale cant-do, never a silent internal error.\n"
    "            let order = order_with(0, \"QUOTE2\");\n"
    "            let err = calculate_and_check_quote(&ctx, &order, &100)\n"
    "                .await\n"
    "                .unwrap_err();\n"
    "            assert!(matches!(err, MostroCantDo(CantDoReason::PriceTooStale)));", p)
scrivi(p, t); print("order.rs: ok")

# ── take_buy.rs e take_sell.rs: il ramo Err(_) del market amount
for p in ("src/app/take_buy.rs", "src/app/take_sell.rs"):
    t = leggi(p)
    t = una(t,
        r"            Err\(_\) => return Err\(MostroInternalErr\(ServiceError::WrongAmountError\)\),",
        "            // No price at all yet (cold cache): same answer as stale,\n"
        "            // so the taker is told instead of left waiting.\n"
        "            Err(_) => return Err(MostroCantDo(CantDoReason::PriceTooStale)),", p)
    scrivi(p, t); print(p + ": ok")

print("fatto: guarda `git diff`, poi committa e esporta con format-patch")
