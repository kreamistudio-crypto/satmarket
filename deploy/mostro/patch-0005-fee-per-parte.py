#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch 0005 del fork — le commissioni PER PARTE, con lo sconto fedelta'
applicato alla fonte.

Si lancia SUL NODO, dentro ~/nodo/mostro-src sul branch barattolo/v0.18.7,
con `barattolo_fee.rs` nella STESSA cartella di questo script:
    python3 /percorso/patch-0005-fee-per-parte.py          # applica
    python3 /percorso/patch-0005-fee-per-parte.py --secco  # prova e basta
Ogni ancora deve comparire UNA volta: se anche una sola manca o e' doppia
si ferma SENZA SCRIVERE NIENTE (prima si controllano tutte, poi si scrive).
Poi si committa e si esporta con `git format-patch -1`, che e' la forma in
cui il fork vive nel repo.

IL DISEGNO (set 2026, deciso con Alan): chi e' pioniere OPPURE ha il
livello 5 su Barattolo paga mezzo punto in meno sulla SUA meta' della
commissione, e lo sconto lo applica mostrod — hold invoice e payout
nascono giusti, nessun rimborso dopo. Upstream ha UNA colonna `order.fee`
per tutt'e due le parti, e `Order` sta in mostro-core (che non si forka):
quindi `order.fee` diventa «la fee del COMPRATORE» — i suoi sei usi
restano intatti — e la fee del VENDITORE va in una tabella a lato,
`barattolo_fees`, letta nei TRE posti dove upstream usa `order.fee` dal
lato di chi vende (il censimento del tag: `show_hold_invoice` in util.rs,
e i due messaggi `BuyerTookOrder` in flow.rs e add_invoice.rs).
Il codice nuovo sta tutto in `src/barattolo_fee.rs`; qui ci sono solo i
sette agganci. `order.rs` NON si tocca: alla pubblicazione chi prende non
esiste, e la fee si riscrive alla presa.

SE IL SERVER NON RISPONDE: fee piena per tutt'e due. E senza le tre
variabili d'ambiente (`BARATTOLO_SCONTO_FEE`, `_URL`, `_SEGRETO`) la patch
e' INERTE: nessuna richiesta, nessuna riga scritta, `order.fee` com'era.
"""
import io
import os
import sys

SECCO = "--secco" in sys.argv
QUI = os.path.dirname(os.path.abspath(__file__))


def leggi(p):
    with io.open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()


def scrivi(p, t):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(t)


# (file, ancora, testo nuovo, "dopo" | "al posto")
AGGANCI = [
    # 1. il modulo
    ("src/main.rs", "pub mod app;\n",
     "pub mod app;\npub mod barattolo_fee;\n", "al posto"),
    # 2. la tabella a lato e il battito, appena c'e' il pool
    ("src/main.rs",
     '        tracing::error!("No connection to database - closing Mostro!");\n'
     "        exit(1);\n"
     "    };\n",
     "\n"
     "    // Barattolo fork (patch 0005): side table for the per-party fees and\n"
     "    // the keep-warm loop towards the marketplace server.\n"
     "    barattolo_fee::init().await;\n", "dopo"),
    # 3. take-buy: chi prende VENDE. Le due chiavi sono note da qui.
    ("src/app/take_buy.rs",
     "    let buyer_pubkey = order.get_buyer_pubkey().map_err(MostroInternalErr)?;\n",
     "\n"
     "    // Barattolo fork (patch 0005): per-party fees. From here on `order.fee`\n"
     "    // is the BUYER's fee; the seller's is in the side table. Runs before\n"
     "    // anything reads the fee (bond context, hold invoice).\n"
     "    crate::barattolo_fee::apply_party_fees(\n"
     "        pool,\n"
     "        &mut order,\n"
     "        &buyer_pubkey.to_hex(),\n"
     "        &seller_pubkey.to_hex(),\n"
     "    )\n"
     "    .await;\n", "dopo"),
    # 4. take-sell: chi prende COMPRA. PRIMA di validare la sua fattura,
    #    che si controlla contro amount - order.fee.
    ("src/app/take_sell.rs",
     "    // Validate invoice and get payment request if present\n",
     "    // Barattolo fork (patch 0005): per-party fees. From here on `order.fee`\n"
     "    // is the BUYER's fee; the seller's is in the side table. Must run before\n"
     "    // the buyer's invoice is validated against `amount - order.fee`.\n"
     "    let barattolo_seller_key = order\n"
     "        .get_seller_pubkey()\n"
     "        .map(|k| k.to_hex())\n"
     "        .unwrap_or_default();\n"
     "    crate::barattolo_fee::apply_party_fees(\n"
     "        pool,\n"
     "        &mut order,\n"
     "        &event.sender.to_hex(),\n"
     "        &barattolo_seller_key,\n"
     "    )\n"
     "    .await;\n"
     "\n"
     "    // Validate invoice and get payment request if present\n", "al posto"),
    # 5-7. i tre usi dal lato del VENDITORE
    ("src/util.rs",
     "    let new_amount = order.amount + order.fee;\n",
     "    // Barattolo fork (patch 0005): the SELLER's fee, not `order.fee`.\n"
     "    let new_amount = order.amount + crate::barattolo_fee::seller_fee(&order).await;\n",
     "al posto"),
    ("src/flow.rs",
     "        seller_order_data.amount = order.amount.saturating_add(order.fee);\n",
     "        // Barattolo fork (patch 0005): the SELLER's fee, not `order.fee`.\n"
     "        seller_order_data.amount = order\n"
     "            .amount\n"
     "            .saturating_add(crate::barattolo_fee::seller_fee(&order).await);\n",
     "al posto"),
    ("src/app/add_invoice.rs",
     "        seller_order.amount = active_order.amount.saturating_add(active_order.fee);\n",
     "        // Barattolo fork (patch 0005): the SELLER's fee, not `order.fee`.\n"
     "        seller_order.amount = active_order\n"
     "            .amount\n"
     "            .saturating_add(crate::barattolo_fee::seller_fee(&active_order).await);\n",
     "al posto"),
]

modulo = os.path.join(QUI, "barattolo_fee.rs")
if not os.path.isfile(modulo):
    sys.exit("FERMO: manca barattolo_fee.rs accanto a questo script — niente scritto")
if not os.path.isfile("src/main.rs"):
    sys.exit("FERMO: non sono nella radice di mostro-src — niente scritto")
if os.path.exists("src/barattolo_fee.rs") and leggi("src/barattolo_fee.rs") != leggi(modulo):
    sys.exit("FERMO: src/barattolo_fee.rs esiste gia' ed e' DIVERSO — niente scritto")

# PRIMA si controllano tutte le ancore, su una copia in memoria
testi = {}
for percorso, ancora, nuovo, dove in AGGANCI:
    t = testi.get(percorso)
    if t is None:
        t = leggi(percorso)
    if "barattolo_fee" in nuovo and nuovo in t:
        sys.exit("FERMO: %s porta gia' questo aggancio — la patch e' gia' applicata?" % percorso)
    n = t.count(ancora)
    if n != 1:
        sys.exit("FERMO: in %s l'ancora compare %d volte (attesa 1) — niente scritto:\n%s"
                 % (percorso, n, ancora))
    testi[percorso] = t.replace(ancora, ancora + nuovo if dove == "dopo" else nuovo)

# IL CENSIMENTO: ogni uso di `order.fee` dal lato di chi vende deve essere
# passato di qui. Se upstream ne aggiunge uno, questa riga lo trova — ed e'
# il momento di rileggere il disegno, non di allungare un elenco.
SPIE = ("amount + order.fee", "saturating_add(order.fee)",
        "saturating_add(active_order.fee)")
rimasti = []
for radice, _, nomi in os.walk("src"):
    for nome in nomi:
        if not nome.endswith(".rs"):
            continue
        percorso = os.path.join(radice, nome).replace(os.sep, "/")
        t = testi.get(percorso)
        if t is None:
            t = leggi(percorso)
        rimasti += [(percorso, s) for s in SPIE if s in t]
if rimasti:
    sys.exit("FERMO: resta un uso della fee dal lato del venditore: %r" % rimasti)

if SECCO:
    print("A SECCO: %d agganci in %d file, tutte le ancore uniche. Niente scritto."
          % (len(AGGANCI), len(testi)))
    sys.exit(0)
for percorso, t in testi.items():
    scrivi(percorso, t)
scrivi("src/barattolo_fee.rs", leggi(modulo))
print("FATTO: %d agganci in %d file, piu' src/barattolo_fee.rs" % (len(AGGANCI), len(testi)))
print("Adesso: cargo fmt --check (se c'e'), i test, il commit, git format-patch -1")
