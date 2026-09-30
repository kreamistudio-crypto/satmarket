#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch 0008 del fork — LA CAUZIONE SOLO PER CERTI METODI DI PAGAMENTO
(e le tre cose che la cauzione accesa chiede alle patch di prima).

Si lancia SUL NODO, dentro ~/nodo/mostro-src sul branch barattolo/vX.Y.Z
(0.19.0 o piu'), SOPRA la 0007 (e quindi la 0005): pretende
`src/barattolo_fee.rs` e `src/barattolo_eventi.rs`, e si ferma se mancano.
    python3 /percorso/patch-0008-cauzione-solo-contanti.py --secco  # prova e basta
    python3 /percorso/patch-0008-cauzione-solo-contanti.py          # applica
Ogni ancora deve comparire UNA volta (una sola, dichiarata, DUE): se anche
una manca o e' doppia si ferma SENZA SCRIVERE NIENTE. Poi si committa e si
esporta con `git format-patch -1 --start-number 8`.

IL DISEGNO (1 ott 2026, cantiere B, decisione di Andrea): negli scambi in
CONTANTI di persona chi prende l'ordine blocca una piccola cauzione —
l'`anti_abuse_bond` di mostrod — cosi' chi non si presenta all'incontro la
perde e chi vende non resta coi sats bloccati per niente. Ma upstream la
cauzione e' TUTTO o NIENTE: `taker_bond_required()` e
`maker_bond_required()` non ricevono l'ordine, e `payment_method` e' una
stringa che nessuno guarda. Barattozon e gli altri metodi NON devono
chiederla. Quattro pezzi:

A) LA PORTA PER METODO. Un campo nuovo in `[anti_abuse_bond]`,
   `only_payment_methods = ["Contanti"]` (serde default: assente o vuoto
   = ogni metodo, cioe' upstream). `bond_applies_to_order(&order)` spezza
   `order.payment_method` sulle virgole e confronta la PAROLA INTERA
   senza maiuscole: «Contanti al tabacchino 23.47» resta fuori,
   «Contanti,Revolut» entra (chi prende puo' scegliere proprio il
   contante — la stessa regola del tetto nel client). I tre punti di
   chiamata — take_buy, take_sell, publish_order — passano da
   `*_required_for(&order)`, tutti gia' dentro un `if bond_required`; e
   il 38385 annuncia la lista con `bond_only_payment_methods`, che il
   client legge viva come la fee. Se sbaglia, sbaglia in CHIUSURA: nessuna
   cauzione, cioe' il comportamento di ieri.
B) LA RILETTURA DELLA 0005. `apply_party_fees` gira a OGNI tentativo di
   presa, prima della cauzione, e scrive UNA riga per ordine (INSERT OR
   REPLACE): con due prese in gara l'ultima sovrascrive quella del
   vincitore, e al blocco `seller_fee` non trova i suoi numeri e ripiega
   su `order.fee` (lo sconto dello 0,5% perso o regalato, mai un flusso
   rotto). Qui si riesegue per il VINCITORE al blocco, su una COPIA
   dell'ordine: l'ordine tiene i numeri della sua riga della cauzione,
   contro cui la fattura di chi compra e' gia' stata validata.
C) IL BUCO DELLA 0007. Un ordine sell preso senza fattura riparte da
   `resume_take_after_bond`, che chiama `set_waiting_invoice_status`
   direttamente e NON passa dal ramo di take_sell agganciato dalla 0007:
   il server non riceverebbe `taken`/`invoice-next` ne'
   `buyer-invoice-requested`, e chi vende non avrebbe il Telegram
   «preso». Si copia l'aggancio 5 della 0007 in quel ramo.
D) L'EVENTO `bond-slashed` AL SERVER. Senza, chi VINCE meta' cauzione lo
   sa solo se apre l'app entro quindici giorni. `notify_bond_slashed` e'
   chiamata dai tre posti dove la bruciatura e' CONFERMATA (timeout,
   admin-settle, admin-cancel): da li' parte un evento con chi l'ha persa
   nel dettaglio (`buyer` | `seller`), `sats` = la cauzione, `sats_buyer`
   e `sats_seller` = quanto riceve ognuno.

⚠️ MAI COMPILATA QUI (sul PC non c'e' cargo): le firme upstream sono state
LETTE sul clone del tag v0.19.0 con le sette patch applicate (`git am`),
e il patcher e' stato fatto girare li' a secco e per davvero — il primo
`cargo build` e' quello sul nodo, punto 4 della liturgia, e va guardato.
Le due literal complete di `AntiAbuseBondSettings` nei test di nip33.rs
ricevono il campo nuovo (senza, i TEST non compilerebbero).
"""
import io
import os
import re
import sys

SECCO = "--secco" in sys.argv


def leggi(p):
    with io.open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()


def scrivi(p, t):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(t)


BF = "crate::barattolo_fee::"
BE = "crate::barattolo_eventi::"

# (file, ancora, testo nuovo, "dopo" | "prima" | "al posto", quante volte)
AGGANCI = [
    # ── A) la porta per metodo ──────────────────────────────────────
    ("src/config/types.rs",
     "    pub maker_bond_payment_timeout_seconds: u64,\n}\n",
     "    pub maker_bond_payment_timeout_seconds: u64,\n"
     "    /// Barattolo fork (patch 0008): the payment methods the bond applies\n"
     "    /// to. Each comma-separated entry of the order's `payment_method` is\n"
     "    /// compared whole-word, trimmed, case-insensitively. Empty (the\n"
     "    /// default) = every method, i.e. upstream behaviour.\n"
     "    #[serde(default)]\n"
     "    pub only_payment_methods: Vec<String>,\n"
     "}\n", "al posto", 1),
    ("src/config/types.rs",
     "            maker_bond_payment_timeout_seconds: default_maker_bond_payment_timeout_seconds(),\n",
     "            only_payment_methods: Vec::new(),\n", "dopo", 1),
    ("src/config/types.rs",
     "    #[test]\n    fn toml_apply_to_both() {\n",
     "    #[test]\n"
     "    fn toml_only_payment_methods_barattolo() {\n"
     "        // Barattolo fork (patch 0008): the list parses, and its absence\n"
     "        // is the empty list (= every method).\n"
     "        #[derive(serde::Deserialize)]\n"
     "        struct Stub {\n"
     "            anti_abuse_bond: AntiAbuseBondSettings,\n"
     "        }\n"
     "        let parsed: Stub = toml::from_str(\n"
     "            \"[anti_abuse_bond]\\nenabled = true\\nonly_payment_methods = [\\\"Contanti\\\", \\\"SEPA\\\"]\",\n"
     "        )\n"
     "        .expect(\"toml parses\");\n"
     "        assert_eq!(\n"
     "            parsed.anti_abuse_bond.only_payment_methods,\n"
     "            vec![\"Contanti\".to_string(), \"SEPA\".to_string()]\n"
     "        );\n"
     "        let bare: Stub = toml::from_str(\"[anti_abuse_bond]\\nenabled = true\").expect(\"parses\");\n"
     "        assert!(bare.anti_abuse_bond.only_payment_methods.is_empty());\n"
     "        assert!(AntiAbuseBondSettings::default().only_payment_methods.is_empty());\n"
     "    }\n\n", "prima", 1),
    ("src/app/bond/flow.rs",
     "pub fn maker_bond_required() -> bool {\n"
     "    Settings::get_bond()\n"
     "        .filter(|cfg| cfg.enabled)\n"
     "        .is_some_and(|cfg| cfg.apply_to.applies_to_maker())\n"
     "}\n",
     "\n"
     "/// Barattolo fork (patch 0008): does the node's bond policy cover this\n"
     "/// order's payment methods? `only_payment_methods` empty = every order.\n"
     "pub fn bond_applies_to_order(order: &Order) -> bool {\n"
     "    Settings::get_bond()\n"
     "        .map(|cfg| payment_method_in(&order.payment_method, &cfg.only_payment_methods))\n"
     "        .unwrap_or(false)\n"
     "}\n"
     "\n"
     "/// Pure half of [`bond_applies_to_order`]: `payment_method` is the order's\n"
     "/// comma-separated list, `allowed` the policy's. Whole word, trimmed,\n"
     "/// case-insensitive; an empty policy covers everything.\n"
     "pub fn payment_method_in(payment_method: &str, allowed: &[String]) -> bool {\n"
     "    let allowed: Vec<String> = allowed\n"
     "        .iter()\n"
     "        .map(|a| a.trim().to_lowercase())\n"
     "        .filter(|a| !a.is_empty())\n"
     "        .collect();\n"
     "    if allowed.is_empty() {\n"
     "        return true;\n"
     "    }\n"
     "    payment_method\n"
     "        .split(',')\n"
     "        .map(|m| m.trim().to_lowercase())\n"
     "        .any(|m| allowed.contains(&m))\n"
     "}\n"
     "\n"
     "/// [`taker_bond_required`] for THIS order (patch 0008).\n"
     "pub fn taker_bond_required_for(order: &Order) -> bool {\n"
     "    taker_bond_required() && bond_applies_to_order(order)\n"
     "}\n"
     "\n"
     "/// [`maker_bond_required`] for THIS order (patch 0008).\n"
     "pub fn maker_bond_required_for(order: &Order) -> bool {\n"
     "    maker_bond_required() && bond_applies_to_order(order)\n"
     "}\n", "dopo", 1),
    ("src/app/bond/mod.rs",
     "    request_taker_bond, resubscribe_active_bonds, taker_bond_required,\n",
     "    bond_applies_to_order, maker_bond_required_for, payment_method_in, taker_bond_required_for,\n",
     "dopo", 1),
    ("src/app/take_buy.rs",
     "    let bond_required = bond::taker_bond_required();\n",
     "    // Barattolo fork (patch 0008): only for the payment methods the node's\n"
     "    // policy names (`only_payment_methods`, empty = every method).\n"
     "    let bond_required = bond::taker_bond_required_for(&order);\n", "al posto", 1),
    ("src/app/take_sell.rs",
     "    let bond_required = bond::taker_bond_required();\n",
     "    // Barattolo fork (patch 0008): only for the payment methods the node's\n"
     "    // policy names (`only_payment_methods`, empty = every method).\n"
     "    let bond_required = bond::taker_bond_required_for(&order);\n", "al posto", 1),
    ("src/util.rs",
     "    let maker_bond_required = crate::app::bond::maker_bond_required();\n",
     "    // Barattolo fork (patch 0008): only for the payment methods the node's\n"
     "    // policy names (`only_payment_methods`, empty = every method).\n"
     "    let maker_bond_required = crate::app::bond::maker_bond_required_for(&new_order_db);\n",
     "al posto", 1),
    ("src/nip33.rs",
     "            tags.push(Tag::custom(\n"
     "                \"bond_payout_claim_window_days\",\n"
     "                vec![bond.payout_claim_window_days.to_string()],\n"
     "            ));\n",
     "            // Barattolo fork (patch 0008): which payment methods the bond\n"
     "            // applies to; absent = every method.\n"
     "            if !bond.only_payment_methods.is_empty() {\n"
     "                tags.push(Tag::custom(\n"
     "                    \"bond_only_payment_methods\",\n"
     "                    vec![bond.only_payment_methods.join(\",\")],\n"
     "                ));\n"
     "            }\n", "dopo", 1),
    # le due literal complete nei test di nip33: senza il campo non compilano
    ("src/nip33.rs",
     "            maker_bond_payment_timeout_seconds: 900,\n",
     "            only_payment_methods: Vec::new(),\n", "dopo", 2),
    ("settings.tpl.toml",
     "# maker_bond_payment_timeout_seconds = 900\n",
     "# Barattolo fork (patch 0008): the bond applies only to orders whose\n"
     "# payment_method lists one of these (whole word, case-insensitive).\n"
     "# Empty or absent = every method, i.e. upstream.\n"
     "# only_payment_methods = [\"Contanti\"]\n", "dopo", 1),
    # ── B) la rilettura della 0005: la riga del vincitore ───────────
    ("src/app/bond/flow.rs",
     "    let order = promote_taker_context_to_order(pool, order, &current).await?;\n",
     "    // Barattolo fork (patch 0008): re-apply the per-party fees for the\n"
     "    // WINNER. Patch 0005 writes one side row per order at every take\n"
     "    // attempt; with concurrent bonds the last attempt's row overwrites the\n"
     "    // winner's. The order keeps the numbers of its bond row (the buyer's\n"
     "    // invoice was validated against them): only the side row is refreshed.\n"
     "    {\n"
     "        let mut ricalcolo = order.clone();\n"
     "        let buyer = order.buyer_pubkey.clone().unwrap_or_default();\n"
     "        let seller = order.seller_pubkey.clone().unwrap_or_default();\n"
     "        " + BF + "apply_party_fees(pool, &mut ricalcolo, &buyer, &seller).await;\n"
     "    }\n", "dopo", 1),
    # ── C) il buco della 0007: il ramo senza fattura dopo la cauzione ─
    ("src/app/bond/flow.rs",
     "                if !won {\n"
     "                    crate::util::republish_winning_state_after_cas_miss(\n"
     "                        pool,\n"
     "                        my_keys,\n"
     "                        order_updated.id,\n"
     "                    )\n"
     "                    .await;\n"
     "                    return Err(MostroCantDo(CantDoReason::NotAllowedByStatus));\n"
     "                }\n"
     "                Ok(())\n",
     "                if !won {\n"
     "                    crate::util::republish_winning_state_after_cas_miss(\n"
     "                        pool,\n"
     "                        my_keys,\n"
     "                        order_updated.id,\n"
     "                    )\n"
     "                    .await;\n"
     "                    return Err(MostroCantDo(CantDoReason::NotAllowedByStatus));\n"
     "                }\n"
     "                // Barattolo fork (patch 0008): the bonded take of a sell order\n"
     "                // without a buyer invoice resumes here and never passes through\n"
     "                // take_sell's hook (patch 0007): the same two events, so the\n"
     "                // server tells the maker what comes next.\n"
     "                " + BE + "emit_taken(&order_updated, \"invoice-next\");\n"
     "                " + BE + "emit(\"buyer-invoice-requested\", &order_updated, \"mostro\");\n"
     "                Ok(())\n", "al posto", 1),
    # ── D) l'evento bond-slashed ────────────────────────────────────
    ("src/app/bond/slash.rs",
     "        Action::BondSlashed,\n"
     "        Some(Payload::Order(small)),\n"
     "        recipient,\n"
     "        None,\n"
     "    )\n"
     "    .await;\n",
     "    // Barattolo fork (patch 0008): tell the marketplace server, so it warns\n"
     "    // the loser and reminds the winner to claim their share.\n"
     "    " + BE + "emit_bond_slashed(\n"
     "        order,\n"
     "        &slashed.pubkey,\n"
     "        slashed.amount_sats,\n"
     "        slashed.node_share_sats.unwrap_or(0),\n"
     "    );\n", "dopo", 1),
    ("src/barattolo_eventi.rs",
     "pub const ACTIONS: [&str; 12] = [\n",
     "pub const ACTIONS: [&str; 13] = [\n", "al posto", 1),
    ("src/barattolo_eventi.rs",
     "    \"dispute-opened\",\n];\n",
     "    \"dispute-opened\",\n"
     "    // patch 0008: a bond was slashed (detail = whose)\n"
     "    \"bond-slashed\",\n];\n", "al posto", 1),
    ("src/barattolo_eventi.rs",
     "//   released                admin (a moderator settled a dispute)\n",
     "//   bond-slashed            buyer | seller (whose bond was slashed; `sats` = the\n"
     "//                           bond, `sats_buyer` / `sats_seller` = what each receives)\n",
     "dopo", 1),
    ("src/barattolo_eventi.rs",
     "    let closing = event.action == \"released\" || event.action == \"success\";\n",
     "    let closing = matches!(\n"
     "        event.action.as_str(),\n"
     "        \"released\" | \"success\" | \"bond-slashed\"\n"
     "    );\n", "al posto", 1),
    ("src/barattolo_eventi.rs",
     "    emit_detail(\"taken\", order, taker, next);\n}\n",
     "\n"
     "/// A bond was slashed (patch 0008): `slashed` is the bonded party's trade\n"
     "/// key, `amount` the bond, `node_share` what the node keeps; the rest goes\n"
     "/// to the counterparty, and the server reminds them to claim it. Sent only\n"
     "/// when the order still names the side, which is where the three callers\n"
     "/// stand (the timeout path notifies BEFORE clearing the taker's keys).\n"
     "pub fn emit_bond_slashed(order: &Order, slashed: &str, amount: i64, node_share: i64) {\n"
     "    if endpoint().is_none() {\n"
     "        return;\n"
     "    }\n"
     "    let side = actor_of(\n"
     "        order.buyer_pubkey.as_deref(),\n"
     "        order.seller_pubkey.as_deref(),\n"
     "        slashed,\n"
     "    );\n"
     "    if side == \"mostro\" {\n"
     "        warn!(\n"
     "            \"barattolo_eventi: order {}: slashed key names no side, bond-slashed not sent\",\n"
     "            order.id\n"
     "        );\n"
     "        return;\n"
     "    }\n"
     "    let share = amount.saturating_sub(node_share.max(0)).max(0);\n"
     "    let (to_buyer, to_seller) = if side == \"buyer\" { (0, share) } else { (share, 0) };\n"
     "    match event_of(\"bond-slashed\", order, \"mostro\", Some(side)) {\n"
     "        Some(mut event) => {\n"
     "            event.sats = Some((amount, to_buyer, to_seller));\n"
     "            spawn_delivery(event, None);\n"
     "        }\n"
     "        None => warn!(\n"
     "            \"barattolo_eventi: order {}: bond-slashed is not a known action, nothing sent\",\n"
     "            order.id\n"
     "        ),\n"
     "    }\n"
     "}\n", "dopo", 1),
]

# i test della porta per metodo, in coda a flow.rs (un modulo suo)
TEST_FLOW = (
    "\n"
    "#[cfg(test)]\n"
    "mod barattolo_bond_methods {\n"
    "    // Barattolo fork (patch 0008): the bond only for the payment methods\n"
    "    // the policy names, compared whole-word and case-insensitively.\n"
    "    use super::{bond_applies_to_order, maker_bond_required_for, payment_method_in, taker_bond_required_for};\n"
    "\n"
    "    fn v(a: &[&str]) -> Vec<String> {\n"
    "        a.iter().map(|s| s.to_string()).collect()\n"
    "    }\n"
    "\n"
    "    #[test]\n"
    "    fn empty_policy_covers_every_method() {\n"
    "        assert!(payment_method_in(\"SEPA\", &v(&[])));\n"
    "        assert!(payment_method_in(\"\", &v(&[])));\n"
    "        assert!(payment_method_in(\"SEPA\", &v(&[\"\", \"  \"])));\n"
    "    }\n"
    "\n"
    "    #[test]\n"
    "    fn whole_word_case_insensitive() {\n"
    "        let p = v(&[\"Contanti\"]);\n"
    "        assert!(payment_method_in(\"Contanti\", &p));\n"
    "        assert!(payment_method_in(\"contanti\", &p));\n"
    "        assert!(payment_method_in(\"Revolut, Contanti\", &p));\n"
    "        assert!(payment_method_in(\" CONTANTI ,SEPA\", &p));\n"
    "        // Barattozon has its own exact name: a prefix is not a match\n"
    "        assert!(!payment_method_in(\"Contanti al tabacchino 23.47\", &p));\n"
    "        assert!(!payment_method_in(\"SEPA,Revolut\", &p));\n"
    "        assert!(!payment_method_in(\"\", &p));\n"
    "    }\n"
    "\n"
    "    #[test]\n"
    "    fn policy_entries_are_trimmed_and_lowercased() {\n"
    "        assert!(payment_method_in(\"contanti\", &v(&[\" Contanti \"])));\n"
    "        assert!(payment_method_in(\"SEPA\", &v(&[\"\", \"sepa\"])));\n"
    "    }\n"
    "\n"
    "    #[test]\n"
    "    fn gates_are_off_without_config() {\n"
    "        // No global config in unit tests: every gate stays inert, as the\n"
    "        // upstream ones do.\n"
    "        let order = mostro_core::order::Order {\n"
    "            payment_method: \"Contanti\".to_string(),\n"
    "            ..Default::default()\n"
    "        };\n"
    "        assert!(!bond_applies_to_order(&order));\n"
    "        assert!(!taker_bond_required_for(&order));\n"
    "        assert!(!maker_bond_required_for(&order));\n"
    "    }\n"
    "}\n")

TEST_NIP33 = (
    "\n"
    "#[cfg(test)]\n"
    "mod barattolo_bond_methods_tag {\n"
    "    // Barattolo fork (patch 0008): the info event names the payment\n"
    "    // methods the bond applies to, and only when there are some.\n"
    "    use super::bond_policy_tags;\n"
    "    use crate::config::types::AntiAbuseBondSettings;\n"
    "\n"
    "    fn valore(tags: &[nostr_sdk::Tag], nome: &str) -> Option<String> {\n"
    "        tags.iter().find_map(|tag| {\n"
    "            let vec = tag.clone().to_vec();\n"
    "            if vec.first().map(String::as_str) == Some(nome) {\n"
    "                vec.get(1).cloned()\n"
    "            } else {\n"
    "                None\n"
    "            }\n"
    "        })\n"
    "    }\n"
    "\n"
    "    #[test]\n"
    "    fn only_payment_methods_tag_when_set() {\n"
    "        let bond = AntiAbuseBondSettings {\n"
    "            enabled: true,\n"
    "            only_payment_methods: vec![\"Contanti\".to_string(), \"SEPA\".to_string()],\n"
    "            ..AntiAbuseBondSettings::default()\n"
    "        };\n"
    "        let tags = bond_policy_tags(Some(&bond));\n"
    "        assert_eq!(\n"
    "            valore(&tags, \"bond_only_payment_methods\").as_deref(),\n"
    "            Some(\"Contanti,SEPA\")\n"
    "        );\n"
    "    }\n"
    "\n"
    "    #[test]\n"
    "    fn no_tag_when_empty_or_disabled() {\n"
    "        let ogni = AntiAbuseBondSettings {\n"
    "            enabled: true,\n"
    "            ..AntiAbuseBondSettings::default()\n"
    "        };\n"
    "        assert!(valore(&bond_policy_tags(Some(&ogni)), \"bond_only_payment_methods\").is_none());\n"
    "        let spenta = AntiAbuseBondSettings {\n"
    "            enabled: false,\n"
    "            only_payment_methods: vec![\"Contanti\".to_string()],\n"
    "            ..AntiAbuseBondSettings::default()\n"
    "        };\n"
    "        assert!(valore(&bond_policy_tags(Some(&spenta)), \"bond_only_payment_methods\").is_none());\n"
    "        assert!(valore(&bond_policy_tags(None), \"bond_only_payment_methods\").is_none());\n"
    "    }\n"
    "}\n")

if not os.path.isfile("src/main.rs"):
    sys.exit("FERMO: non sono nella radice di mostro-src — niente scritto")
for serve, chi in (("src/barattolo_fee.rs", "0005"), ("src/barattolo_eventi.rs", "0007")):
    if not os.path.isfile(serve):
        sys.exit("FERMO: manca %s — la 0008 sta SOPRA la %s, che qui non c'e'" % (serve, chi))

# LE AZIONI: la stringa nuova deve stare nell'elenco del modulo DOPO la
# patch, e l'elenco deve contare quante voci dichiara (Rust conta le
# voci, non i nomi: e' la lista del server a leggerli per nome).
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

for percorso, coda in (("src/app/bond/flow.rs", TEST_FLOW), ("src/nip33.rs", TEST_NIP33)):
    t = testi[percorso]
    if "\r\n" in t:
        coda = coda.replace("\n", "\r\n")
    if "mod barattolo_bond_methods" in t:
        sys.exit("FERMO: %s porta gia' i test della 0008 — la patch e' gia' applicata?" % percorso)
    testi[percorso] = t + coda

# l'elenco delle azioni del modulo, DOPO la patch
sorgente = testi["src/barattolo_eventi.rs"]
m = re.search(r"pub const ACTIONS: \[&str; (\d+)\] = \[(.*?)\];", sorgente, flags=re.S)
if not m:
    sys.exit("FERMO: non trovo l'elenco ACTIONS in barattolo_eventi.rs — niente scritto")
note = set(re.findall(r'"([a-z-]+)"', m.group(2)))
if len(note) != int(m.group(1)):
    sys.exit("FERMO: ACTIONS dichiara %s voci e ne elenca %d — niente scritto" % (m.group(1), len(note)))
if "bond-slashed" not in note:
    sys.exit("FERMO: «bond-slashed» non e' entrata nell'elenco ACTIONS — niente scritto")
blocco = sorgente[sorgente.find("// THE DETAILS"):sorgente.find("pub fn is_known_action")]
if not re.search(r"\bbond-slashed\b", blocco):
    sys.exit("FERMO: il vocabolario dei dettagli non nomina bond-slashed — niente scritto")
usate = set(re.findall(r'emit(?:_by|_detail|_by_detail)?\(\s*"([a-z-]+)"', "".join(n for _, _, n, _, _ in AGGANCI)))
ignote = usate - note
if ignote:
    sys.exit("FERMO: azioni negli agganci che il modulo non conosce: %s" % sorted(ignote))

# NESSUN AGGANCIO DENTRO I TEST (i due moduli in coda sono test loro,
# e non chiamano barattolo_fee/barattolo_eventi)
for percorso, t in testi.items():
    taglio = t.find("#[cfg(test)]\nmod ")
    if taglio < 0:
        taglio = t.find("#[cfg(test)]\r\nmod ")
    if taglio >= 0 and ("barattolo_eventi::" in t[taglio:] or "barattolo_fee::" in t[taglio:]):
        sys.exit("FERMO: in %s un aggancio e' finito DENTRO i test — niente scritto" % percorso)

if SECCO:
    print("A SECCO: %d agganci in %d file, tutte le ancore al loro conto, %d azioni note, i due moduli di test in coda. Niente scritto."
          % (len(AGGANCI), len(testi), len(note) + 1))
    sys.exit(0)
for percorso, t in testi.items():
    scrivi(percorso, t)
print("FATTO: %d agganci in %d file, piu' i test in coda a flow.rs e nip33.rs" % (len(AGGANCI), len(testi)))
print("Adesso: i test, il commit, git format-patch -1 --start-number 8")
