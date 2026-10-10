#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch 0010 del fork — LA CAUZIONE SUL METODO CHE CHI PRENDE DICHIARA.

Si lancia SUL NODO, dentro ~/nodo/mostro-src sul branch barattolo/v0.19.0
(o piu'), SOPRA la 0008: pretende `taker_bond_required_for` in
`src/app/bond/flow.rs`, e si ferma se manca.
    python3 /percorso/patch-0010-cauzione-metodo-dichiarato.py --secco  # prova e basta
    python3 /percorso/patch-0010-cauzione-metodo-dichiarato.py          # applica
Ogni ancora deve comparire UNA volta: se anche una manca o e' doppia si
ferma SENZA SCRIVERE NIENTE. Poi si committa e si esporta con
`git format-patch -1 --start-number 10` (la 0009 e' la PROPOSTA della fee
per chiavi, in `proposte/`, non applicata: il numero resta suo).

IL DISEGNO (10 ott 2026, cantiere cauzione-metodo-scelto, decisione di
Andrea: la cauzione si chiede SOLO a chi prende scegliendo i contanti).
La 0008 decide la cauzione sull'ORDINE: `bond_applies_to_order` spezza
`order.payment_method` sulle virgole, e su un «SEPA, Contanti» chi prende
pagando con SEPA la bloccava lo stesso — il metodo scelto alla presa non
arrivava mai a mostrod (sul take legge `Payload::Amount` e la bolt11).
Adesso il client lo DICHIARA nel take: `verify()` di mostro-core accetta
qualunque payload su TakeSell/TakeBuy, e un `Payload::Order(SmallOrder)`
porta `payment_method` (e `fiat_amount` per l'intervallo) senza una
fattura da validare (`get_payment_request` legge `buyer_invoice`, che
resta vuoto). Tre pezzi:

A) `util.rs`: `taker_payment_method(&msg)` (il metodo dichiarato, pulito,
   None se assente o vuoto) e `taker_declared_amount(&msg)` (la cifra
   dell'intervallo da `fiat_amount`), e `get_fiat_amount_requested` che
   sull'intervallo legge ANCHE quella — senza, un take con `Payload::Order`
   su un intervallo risponderebbe `OutOfRangeSatsAmount`.
B) `bond/flow.rs`: `bond_applies_to_take_with(offered, declared, allowed)`,
   PURA: il metodo dichiarato conta SOLO se e' uno di quelli dell'ordine
   (parola intera, senza maiuscole, come la 0008) — e allora la cauzione
   c'e' se e solo se sta nella policy; senza una dichiarazione usabile
   decide l'ordine intero, come ieri (un client che dicesse «SEPA» su un
   ordine solo-contanti non la scansa; un client di un'altra app, che non
   dichiara, resta alla regola della 0008). `bond_applies_to_take` legge
   la policy dalle settings; `taker_bond_required_for_take` la mette
   insieme all'interruttore. Un modulo di test in coda.
C) `take_buy.rs` e `take_sell.rs`: `bond_required` passa da
   `taker_bond_required_for_take(&order, taker_payment_method(&msg).as_deref())`.
   `maker_bond_required_for` (chi pubblica, `apply_to = make|both`) non
   cambia: la cauzione di chi pubblica resta dell'ordine.

⚠️ MAI COMPILATA QUI (sul PC non c'e' cargo): le firme sono state LETTE
sul clone del tag v0.19.0 con le otto patch applicate (`git am`), e il
patcher e' stato fatto girare li' a secco e per davvero — il primo
`cargo build` e' quello sul nodo, punto 4 della liturgia, e va guardato.
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


# (file, ancora, testo nuovo, "dopo" | "prima" | "al posto", quante volte)
AGGANCI = [
    # ── A) util.rs: il metodo e la cifra dichiarati ─────────────────
    ("src/util.rs",
     "    if order.is_range_order() {\n"
     "        if let Some(amount_buyer) = msg.get_inner_message_kind().get_amount() {\n",
     "    if order.is_range_order() {\n"
     "        // Barattolo fork (patch 0010): a take that carries `Payload::Order`\n"
     "        // (the taker's declared payment method) puts the requested fiat\n"
     "        // amount in `fiat_amount`; `get_amount` reads only `Amount` and\n"
     "        // `PaymentRequest`.\n"
     "        let amount_buyer = msg\n"
     "            .get_inner_message_kind()\n"
     "            .get_amount()\n"
     "            .or_else(|| taker_declared_amount(msg));\n"
     "        if let Some(amount_buyer) = amount_buyer {\n", "al posto", 1),
    ("src/util.rs",
     "        // If order is not a range order return an Option with fiat amount of the order\n"
     "        Some(order.fiat_amount)\n"
     "    }\n"
     "}\n",
     "        // If order is not a range order return an Option with fiat amount of the order\n"
     "        Some(order.fiat_amount)\n"
     "    }\n"
     "}\n"
     "\n"
     "/// Barattolo fork (patch 0010): the payment method the taker declared in\n"
     "/// the take message, when the client sent `Payload::Order`. Trimmed;\n"
     "/// `None` when absent or empty (an upstream client sends `Amount` or\n"
     "/// nothing). The bond policy reads it through\n"
     "/// `bond::taker_bond_required_for_take`.\n"
     "pub fn taker_payment_method(msg: &Message) -> Option<String> {\n"
     "    let inner = msg.get_inner_message_kind();\n"
     "    if inner.action != Action::TakeSell && inner.action != Action::TakeBuy {\n"
     "        return None;\n"
     "    }\n"
     "    match &inner.payload {\n"
     "        Some(Payload::Order(small)) => {\n"
     "            let m = small.payment_method.trim();\n"
     "            if m.is_empty() {\n"
     "                None\n"
     "            } else {\n"
     "                Some(m.to_string())\n"
     "            }\n"
     "        }\n"
     "        _ => None,\n"
     "    }\n"
     "}\n"
     "\n"
     "/// Barattolo fork (patch 0010): the fiat amount a taker asked for on a\n"
     "/// range order when the take carries `Payload::Order`; `None` when the\n"
     "/// payload has another shape or the amount is not positive.\n"
     "pub fn taker_declared_amount(msg: &Message) -> Option<i64> {\n"
     "    let inner = msg.get_inner_message_kind();\n"
     "    if inner.action != Action::TakeSell && inner.action != Action::TakeBuy {\n"
     "        return None;\n"
     "    }\n"
     "    match &inner.payload {\n"
     "        Some(Payload::Order(small)) if small.fiat_amount > 0 => Some(small.fiat_amount),\n"
     "        _ => None,\n"
     "    }\n"
     "}\n", "al posto", 1),
    # ── B) flow.rs: il giudice della presa ──────────────────────────
    ("src/app/bond/flow.rs",
     "/// [`taker_bond_required`] for THIS order (patch 0008).\n"
     "pub fn taker_bond_required_for(order: &Order) -> bool {\n"
     "    taker_bond_required() && bond_applies_to_order(order)\n"
     "}\n",
     "/// [`taker_bond_required`] for THIS order (patch 0008).\n"
     "pub fn taker_bond_required_for(order: &Order) -> bool {\n"
     "    taker_bond_required() && bond_applies_to_order(order)\n"
     "}\n"
     "\n"
     "/// Barattolo fork (patch 0010): [`taker_bond_required`] for THIS take,\n"
     "/// decided on the payment method the taker declared\n"
     "/// (`Payload::Order.payment_method`, read by `util::taker_payment_method`)\n"
     "/// when the order offers it; otherwise, as patch 0008, on the order's\n"
     "/// whole list. A taker who picks an online method on a «SEPA, Contanti»\n"
     "/// order posts no bond; one who picks «Contanti» does.\n"
     "pub fn taker_bond_required_for_take(order: &Order, declared: Option<&str>) -> bool {\n"
     "    taker_bond_required() && bond_applies_to_take(order, declared)\n"
     "}\n"
     "\n"
     "/// [`bond_applies_to_order`] for THIS take (patch 0010): the policy from\n"
     "/// the settings, the rest in [`bond_applies_to_take_with`].\n"
     "pub fn bond_applies_to_take(order: &Order, declared: Option<&str>) -> bool {\n"
     "    Settings::get_bond()\n"
     "        .map(|cfg| {\n"
     "            bond_applies_to_take_with(&order.payment_method, declared, &cfg.only_payment_methods)\n"
     "        })\n"
     "        .unwrap_or(false)\n"
     "}\n"
     "\n"
     "/// Pure (patch 0010): `offered` is the order's comma-separated list,\n"
     "/// `declared` the taker's method, `allowed` the policy's list. The\n"
     "/// declared method counts only when it is one of the offered ones (whole\n"
     "/// word, trimmed, case-insensitive): then the bond applies iff it is in\n"
     "/// the policy. With no usable declaration the order's whole list decides\n"
     "/// (patch 0008): a client cannot dodge the bond by naming a method the\n"
     "/// order does not offer, and a client that declares nothing keeps the\n"
     "/// rule of yesterday.\n"
     "pub fn bond_applies_to_take_with(offered: &str, declared: Option<&str>, allowed: &[String]) -> bool {\n"
     "    if let Some(d) = declared\n"
     "        .map(|d| d.trim().to_lowercase())\n"
     "        .filter(|d| !d.is_empty())\n"
     "    {\n"
     "        let offered_lower: Vec<String> = offered\n"
     "            .split(',')\n"
     "            .map(|m| m.trim().to_lowercase())\n"
     "            .collect();\n"
     "        if offered_lower.contains(&d) {\n"
     "            return payment_method_in(&d, allowed);\n"
     "        }\n"
     "    }\n"
     "    payment_method_in(offered, allowed)\n"
     "}\n", "al posto", 1),
    ("src/app/bond/mod.rs",
     "    bond_applies_to_order, maker_bond_required_for, payment_method_in, taker_bond_required_for,\n",
     "    bond_applies_to_order, maker_bond_required_for, payment_method_in, taker_bond_required_for,\n"
     "    bond_applies_to_take, bond_applies_to_take_with, taker_bond_required_for_take,\n", "al posto", 1),
    # ── C) le due prese ─────────────────────────────────────────────
    ("src/app/take_buy.rs",
     "    // Barattolo fork (patch 0008): only for the payment methods the node's\n"
     "    // policy names (`only_payment_methods`, empty = every method).\n"
     "    let bond_required = bond::taker_bond_required_for(&order);\n",
     "    // Barattolo fork (patch 0008): only for the payment methods the node's\n"
     "    // policy names (`only_payment_methods`, empty = every method) — and\n"
     "    // (patch 0010) on the method the taker declared, when the order offers it.\n"
     "    let bond_required =\n"
     "        bond::taker_bond_required_for_take(&order, taker_payment_method(&msg).as_deref());\n", "al posto", 1),
    ("src/app/take_buy.rs",
     "    get_order, is_order_take_window_closed, show_cashu_escrow_request, show_hold_invoice,\n"
     "    HoldInvoiceOrigin,\n"
     "};\n",
     "    get_order, is_order_take_window_closed, show_cashu_escrow_request, show_hold_invoice,\n"
     "    taker_payment_method, HoldInvoiceOrigin,\n"
     "};\n", "al posto", 1),
    ("src/app/take_sell.rs",
     "    // Barattolo fork (patch 0008): only for the payment methods the node's\n"
     "    // policy names (`only_payment_methods`, empty = every method).\n"
     "    let bond_required = bond::taker_bond_required_for(&order);\n",
     "    // Barattolo fork (patch 0008): only for the payment methods the node's\n"
     "    // policy names (`only_payment_methods`, empty = every method) — and\n"
     "    // (patch 0010) on the method the taker declared, when the order offers it.\n"
     "    let bond_required =\n"
     "        bond::taker_bond_required_for_take(&order, taker_payment_method(&msg).as_deref());\n", "al posto", 1),
    ("src/app/take_sell.rs",
     "    get_order, is_order_take_window_closed, set_waiting_invoice_status, show_cashu_escrow_request,\n"
     "    show_hold_invoice, update_order_event, validate_invoice, HoldInvoiceOrigin,\n"
     "};\n",
     "    get_order, is_order_take_window_closed, set_waiting_invoice_status, show_cashu_escrow_request,\n"
     "    show_hold_invoice, taker_payment_method, update_order_event, validate_invoice,\n"
     "    HoldInvoiceOrigin,\n"
     "};\n", "al posto", 1),
]

# il modulo di test, in coda a flow.rs (sotto quello della 0008)
TEST_FLOW = (
    "\n"
    "#[cfg(test)]\n"
    "mod barattolo_bond_take {\n"
    "    // Barattolo fork (patch 0010): the bond decided on the method the\n"
    "    // taker declares, only when the order offers it.\n"
    "    use super::bond_applies_to_take_with;\n"
    "\n"
    "    fn v(a: &[&str]) -> Vec<String> {\n"
    "        a.iter().map(|s| s.to_string()).collect()\n"
    "    }\n"
    "\n"
    "    #[test]\n"
    "    fn declared_method_decides_when_the_order_offers_it() {\n"
    "        let p = v(&[\"Contanti\"]);\n"
    "        assert!(!bond_applies_to_take_with(\"SEPA, Contanti\", Some(\"SEPA\"), &p));\n"
    "        assert!(!bond_applies_to_take_with(\"Satispay,PayPal,Contanti\", Some(\" paypal \"), &p));\n"
    "        assert!(bond_applies_to_take_with(\"SEPA, Contanti\", Some(\"Contanti\"), &p));\n"
    "        assert!(bond_applies_to_take_with(\"SEPA, Contanti\", Some(\"contanti\"), &p));\n"
    "        assert!(bond_applies_to_take_with(\"Contanti\", Some(\"Contanti\"), &p));\n"
    "    }\n"
    "\n"
    "    #[test]\n"
    "    fn a_declaration_the_order_does_not_offer_falls_back_to_the_order() {\n"
    "        let p = v(&[\"Contanti\"]);\n"
    "        // naming «SEPA» on a cash-only order does not dodge the bond\n"
    "        assert!(bond_applies_to_take_with(\"Contanti\", Some(\"SEPA\"), &p));\n"
    "        // naming «Contanti» on a SEPA-only order does not create one\n"
    "        assert!(!bond_applies_to_take_with(\"SEPA\", Some(\"Contanti\"), &p));\n"
    "        assert!(bond_applies_to_take_with(\"SEPA, Contanti\", Some(\"Revolut\"), &p));\n"
    "        assert!(bond_applies_to_take_with(\"SEPA, Contanti\", Some(\"\"), &p));\n"
    "        assert!(bond_applies_to_take_with(\"SEPA, Contanti\", Some(\"   \"), &p));\n"
    "        // no declaration at all: the rule of patch 0008\n"
    "        assert!(bond_applies_to_take_with(\"SEPA, Contanti\", None, &p));\n"
    "        assert!(!bond_applies_to_take_with(\"SEPA\", None, &p));\n"
    "        // Barattozon keeps its own exact name: never the cash bond\n"
    "        assert!(!bond_applies_to_take_with(\"Contanti al tabacchino 23.47\", Some(\"Contanti al tabacchino 23.47\"), &p));\n"
    "    }\n"
    "\n"
    "    #[test]\n"
    "    fn an_empty_policy_still_covers_every_take() {\n"
    "        assert!(bond_applies_to_take_with(\"SEPA, Contanti\", Some(\"SEPA\"), &v(&[])));\n"
    "        assert!(bond_applies_to_take_with(\"SEPA\", None, &v(&[])));\n"
    "    }\n"
    "}\n")

if not os.path.isfile("src/main.rs"):
    sys.exit("FERMO: non sono nella radice di mostro-src — niente scritto")
flow = leggi("src/app/bond/flow.rs") if os.path.isfile("src/app/bond/flow.rs") else ""
if "pub fn taker_bond_required_for(order: &Order) -> bool {" not in flow:
    sys.exit("FERMO: in src/app/bond/flow.rs manca `taker_bond_required_for` — la 0010 sta SOPRA la 0008, che qui non c'e'")

testi = {}
for percorso, ancora, nuovo, dove, volte in AGGANCI:
    t = testi.get(percorso)
    if t is None:
        if not os.path.isfile(percorso):
            sys.exit("FERMO: manca %s — niente scritto" % percorso)
        t = leggi(percorso)
    if "\r\n" in t:
        ancora = ancora.replace("\n", "\r\n")
        nuovo = nuovo.replace("\n", "\r\n")
    if nuovo in t and dove != "al posto":
        sys.exit("FERMO: %s porta gia' questo aggancio — la patch e' gia' applicata?" % percorso)
    if dove == "al posto" and nuovo in t:
        sys.exit("FERMO: %s porta gia' questa modifica — la patch e' gia' applicata?" % percorso)
    n = t.count(ancora)
    if n != volte:
        sys.exit("FERMO: in %s l'ancora compare %d volte (attese %d) — niente scritto:\n%s"
                 % (percorso, n, volte, ancora))
    if dove == "dopo":
        rimpiazzo = ancora + nuovo
    elif dove == "prima":
        rimpiazzo = nuovo + ancora
    else:
        rimpiazzo = nuovo
    testi[percorso] = t.replace(ancora, rimpiazzo)

t = testi["src/app/bond/flow.rs"]
coda = TEST_FLOW.replace("\n", "\r\n") if "\r\n" in t else TEST_FLOW
if "mod barattolo_bond_take" in t:
    sys.exit("FERMO: src/app/bond/flow.rs porta gia' i test della 0010 — la patch e' gia' applicata?")
testi["src/app/bond/flow.rs"] = t + coda

# NESSUN AGGANCIO DENTRO I TEST (il modulo in coda e' test suo)
for percorso, t in testi.items():
    taglio = t.find("#[cfg(test)]\nmod ")
    if taglio < 0:
        taglio = t.find("#[cfg(test)]\r\nmod ")
    if taglio >= 0 and "taker_bond_required_for_take(&order" in t[taglio:]:
        sys.exit("FERMO: in %s un aggancio e' finito DENTRO i test — niente scritto" % percorso)

if SECCO:
    print("A SECCO: %d agganci in %d file, tutte le ancore al loro conto, il modulo di test in coda a flow.rs. Niente scritto."
          % (len(AGGANCI), len(testi)))
    sys.exit(0)
for percorso, t in testi.items():
    scrivi(percorso, t)
print("FATTO: %d agganci in %d file, piu' i test in coda a flow.rs" % (len(AGGANCI), len(testi)))
print("Adesso: i test, il commit, git format-patch -1 --start-number 10")
