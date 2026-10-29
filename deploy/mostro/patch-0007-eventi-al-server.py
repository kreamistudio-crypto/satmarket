#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch 0007 del fork — MOSTRO E' L'UNICA FONTE DEGLI AVVISI P2P.

Si lancia SUL NODO, dentro ~/nodo/mostro-src sul branch barattolo/vX.Y.Z (0.19.0 o piu':
dalla 0.19.0 `release_action` chiude la disputa come `Released`, #967, e l'ancora 11 lo dice)
(quindi SOPRA la 0005 e la 0006, che devono esserci gia'), con
`barattolo_eventi.rs` nella STESSA cartella di questo script:
    python3 /percorso/patch-0007-eventi-al-server.py --secco  # prova e basta
    python3 /percorso/patch-0007-eventi-al-server.py          # applica
Ogni ancora deve comparire UNA volta: se anche una sola manca o e' doppia
si ferma SENZA SCRIVERE NIENTE (prima si controllano tutte, poi si scrive).
Poi si committa e si esporta con `git format-patch -1 --start-number 7`.

IL DISEGNO (18 set 2026, deciso con Alan): il server di Barattolo deduceva
cosa succede in uno scambio dalle buste cifrate che non puo' leggere, e ne
uscivano avvisi generici («Novita' in un tuo scambio») e, dal vivo, avvisi
a caso. mostrod invece LO SA: a ogni transizione di stato fa un POST al
server, sulla stessa strada dello sconto della 0005 — stesso client HTTP
(quindi lo stesso circuito Tor tenuto caldo dal battito), segreto in
header. Il codice nuovo sta tutto in `src/barattolo_eventi.rs`; qui ci
sono gli agganci, UNA riga per transizione.

COSA ESCE: id ordine, azione, timestamp, le due TRADE pubkey, chi ha fatto
il gesto (buyer/seller/mostro), un dettaglio-macchina breve, e SOLO alla
chiusura (released/success) tre importi in sats. Mai fatture, preimage,
hash, testi, coordinate: `event_of` e' l'unico lettore di `Order` del
modulo, e una prova Rust guarda che quei campi non escano.

FIRE-AND-FORGET, l'opposto del fail-closed dello sconto: il POST vive in un
task suo (8 s, poi UN retry a 12 s), e nessun gesto dello scambio lo
aspetta. `emit*` sono funzioni SINCRONE che ritornano subito. Se il server
tace mostrod va avanti come upstream, e il server ripiega sul libro.

SENZA `BARATTOLO_EVENTI_URL` LA PATCH E' INERTE: nessun task, nessuna
richiesta. Il segreto e' `BARATTOLO_EVENTI_SEGRETO`; se manca vale quello
della 0005 (`BARATTOLO_SCONTO_SEGRETO`).

⚠️ MAI COMPILATA QUI (sul PC non c'e' cargo). Le firme upstream usate sono
state LETTE sul clone del tag v0.18.7 con le sei patch applicate — ogni
aggancio nomina una variabile `Order` che in quel punto esiste ed e'
ancora viva (dove upstream la MUOVE, l'aggancio sta prima o usa una
copia) — ma il primo `cargo build` e' quello sul nodo, e va guardato.
"""
import io
import os
import re
import sys

SECCO = "--secco" in sys.argv
QUI = os.path.dirname(os.path.abspath(__file__))
E = "crate::barattolo_eventi::"


def leggi(p):
    with io.open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()


def scrivi(p, t):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(t)


# (file, ancora, testo nuovo, "dopo" | "prima" | "al posto")
AGGANCI = [
    # 1-2. il modulo (in ordine alfabetico: rustfmt li riordina) e l'avvio
    ("src/main.rs", "pub mod barattolo_fee;\n",
     "pub mod barattolo_eventi;\npub mod barattolo_fee;\n", "al posto"),
    ("src/main.rs", "    barattolo_fee::init().await;\n",
     "    // Barattolo fork (patch 0007): order events to the marketplace server.\n"
     "    barattolo_eventi::init().await;\n", "dopo"),
    # 3. il client della 0005 si presta: stesso pool di connessioni, quindi
    #    lo stesso circuito tenuto caldo dal suo battito
    ("src/barattolo_fee.rs", "\nfn http() -> &'static reqwest::Client {\n",
     "\n// Shared with patch 0007 (`barattolo_eventi`): one client, one warm circuit.\n"
     "pub(crate) fn http() -> &'static reqwest::Client {\n", "al posto"),
    # 4. show_hold_invoice: la garanzia e' stata chiesta a chi vende. Se ci
    #    si arriva da un take, e' anche la PRESA. `order` qui e' posseduto
    #    dalla funzione e porta gia' le due chiavi.
    ("src/util.rs", "    let _ = invoice_subscribe(hash, request_id).await;\n",
     "    // Barattolo fork (patch 0007): tell the marketplace server. A take and\n"
     "    // its hold invoice request are ONE moment: the detail says so.\n"
     "    if origin == HoldInvoiceOrigin::Take {\n"
     "        " + E + "emit_taken(&order, \"hold-next\");\n"
     "        " + E + "emit_detail(\"hold-invoice-requested\", &order, \"mostro\", \"take\");\n"
     "    } else {\n"
     "        " + E + "emit_detail(\n"
     "            \"hold-invoice-requested\",\n"
     "            &order,\n"
     "            \"mostro\",\n"
     "            \"invoice\",\n"
     "        );\n"
     "    }\n", "prima"),
    # 5. take-sell senza fattura: presa, e a chi compra si chiede la fattura
    ("src/app/take_sell.rs",
     "                        return Err(MostroCantDo(CantDoReason::NotAllowedByStatus));\n"
     "                    }\n"
     "                    Ok(())\n",
     "                        return Err(MostroCantDo(CantDoReason::NotAllowedByStatus));\n"
     "                    }\n"
     "                    // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "                    " + E + "emit_taken(&order_updated, \"invoice-next\");\n"
     "                    " + E + "emit(\n"
     "                        \"buyer-invoice-requested\",\n"
     "                        &order_updated,\n"
     "                        \"mostro\",\n"
     "                    );\n"
     "                    Ok(())\n", "al posto"),
    # 6. la garanzia e' stata pagata; nel ramo senza fattura mostrod la
    #    chiede a chi compra. Dalla 0.20.2 `hold_invoice_paid` scrive e
    #    pubblica PRIMA di avvisare, e se la scrittura fallisce esce senza
    #    dire niente a nessuno: l'evento sta dove partono gli avvisi, cosi'
    #    il server lo riceve solo per un passaggio che e' stato salvato.
    ("src/flow.rs", "    for (action, payload, destination) in pending_msgs {\n",
     "    // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "    " + E + "emit_detail(\n"
     "        \"hold-invoice-paid\",\n"
     "        &order,\n"
     "        \"seller\",\n"
     "        if order.buyer_invoice.is_some() {\n"
     "            \"active\"\n"
     "        } else {\n"
     "            \"invoice-next\"\n"
     "        },\n"
     "    );\n"
     "    if order.buyer_invoice.is_none() {\n"
     "        " + E + "emit(\"buyer-invoice-requested\", &order, \"mostro\");\n"
     "    }\n"
     "\n", "prima"),
    # 7-8. add-invoice: `order` viene MOSSO dentro show_hold_invoice, quindi
    #      se ne tiene una copia e si avvisa solo a gesto riuscito
    ("src/app/add_invoice.rs",
     "    // Get seller pubkey\n"
     "    let seller_pubkey = order.get_seller_pubkey().map_err(MostroInternalErr)?;\n"
     "    // Check if the order has a preimage\n",
     "    // Barattolo fork (patch 0007): `order` is moved below, keep a copy\n"
     "    // to tell the marketplace server once the move has succeeded.\n"
     "    let barattolo_order = order.clone();\n"
     "\n", "prima"),
    ("src/app/add_invoice.rs",
     "        return Err(MostroInternalErr(ServiceError::HoldInvoiceError(\n"
     "            cause.to_string(),\n"
     "        )));\n"
     "    }\n"
     "    Ok(())\n",
     "        return Err(MostroInternalErr(ServiceError::HoldInvoiceError(\n"
     "            cause.to_string(),\n"
     "        )));\n"
     "    }\n"
     "    " + E + "emit_detail(\n"
     "        \"buyer-invoice-added\",\n"
     "        &barattolo_order,\n"
     "        \"buyer\",\n"
     "        if barattolo_order.preimage.is_some() {\n"
     "            \"active\"\n"
     "        } else {\n"
     "            \"hold-next\"\n"
     "        },\n"
     "    );\n"
     "    Ok(())\n", "al posto"),
    # 8b. la fattura NUOVA dopo un payout fallito: non e' un avviso per
    #     nessuno, ma il server deve saperlo — o un secondo fallimento
    #     sullo stesso ordine non suonerebbe piu'
    ("src/app/add_invoice.rs", "    order.payment_attempts = 0;\n",
     "    // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "    " + E + "emit_detail(\n"
     "        \"buyer-invoice-added\",\n"
     "        &*order,\n"
     "        \"buyer\",\n"
     "        \"new-invoice\",\n"
     "    );\n", "dopo"),
    # 9. fiat-sent
    ("src/app/fiat_sent.rs",
     "    // Update order\n"
     "    order_updated\n"
     "        .update(pool)\n"
     "        .await\n"
     "        .map_err(|e| MostroInternalErr(ServiceError::DbAccessError(e.to_string())))?;\n",
     "\n"
     "    // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "    " + E + "emit(\"fiat-sent\", &order, \"buyer\");\n", "dopo"),
    # 10. rilasciato: la transizione e' scritta, la disputa (se c'era) chiusa
    ("src/app/release.rs",
     "    close_dispute_after_user_resolution(ctx, &order, DisputeStatus::Released, my_keys, \"release\")\n"
     "        .await;\n",
     "\n"
     "    // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "    " + E + "emit(\"released\", &order, \"seller\");\n", "dopo"),
    # 11. concluso: il payout a chi compra e' riuscito
    ("src/app/release.rs", "    // Committed by us — notify the buyer now.\n",
     "    // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "    " + E + "emit(\"success\", &order_updated, \"mostro\");\n"
     "\n", "prima"),
    # 12. payout fallito, col motivo che la 0006 scrive nel log
    ("src/app/release.rs",
     "                                    msg.payment.failure_reason,\n"
     "                                    msg.payment.htlcs.len()\n"
     "                                );\n",
     "                                // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "                                " + E + "emit_payout_failed(\n"
     "                                    &order,\n"
     "                                    msg.payment.failure_reason,\n"
     "                                );\n", "dopo"),
    # 12b. (22 set 2026, con la 0.18.8) il payout fallito PRIMA di
    #      arrivare a LND: indirizzo che non si risolve, fattura storta o
    #      scaduta, LND irraggiungibile. Upstream #908 li fa passare TUTTI
    #      dal ramo Err di `do_payment`, quindi un aggancio solo li copre;
    #      il dettaglio nomina la classe (INVOICE_INVALID, LND_UNREACHABLE...),
    #      mai il testo dell'errore.
    ("src/app/release.rs",
     "        Err(e) => {\n"
     "            check_failure_retries_or_log(ctx, &order, request_id, None).await;\n"
     "            Err(e)\n"
     "        }\n",
     "        Err(e) => {\n"
     "            check_failure_retries_or_log(ctx, &order, request_id, None).await;\n"
     "            // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "            " + E + "emit_payout_failed_pre_claim(&order, &e);\n"
     "            Err(e)\n"
     "        }\n", "al posto"),
    # 13-14. annullo cooperativo: la richiesta e l'accordo
    ("src/app/cancel.rs",
     "    // Notify both parties: initiator sees \"initiated by you\" and the counterparty sees\n",
     "    // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "    " + E + "emit_by(\"cancel-requested\", &order, &event.sender.to_string());\n", "prima"),
    ("src/app/cancel.rs",
     "    info!(\"Cancel: Order Id {} canceled cooperatively!\", order.id);\n",
     "    // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "    " + E + "emit_by_detail(\n"
     "        \"canceled\",\n"
     "        &order,\n"
     "        &event.sender.to_string(),\n"
     "        \"cooperative\",\n"
     "    );\n", "dopo"),
    # 15. chi ha preso si ritira: l'ordine torna nel libro. PRIMA che
    #     edit_pubkeys_order azzeri le chiavi di chi aveva preso.
    ("src/app/cancel.rs", "    // Reset api quotes\n    reset_api_quotes(&mut order);\n",
     "    // Barattolo fork (patch 0007): tell the marketplace server, BEFORE the\n"
     "    // taker's keys are wiped from the order below.\n"
     "    " + E + "emit_by_detail(\n"
     "        \"canceled\",\n"
     "        &order,\n"
     "        &event.sender.to_string(),\n"
     "        \"republished\",\n"
     "    );\n"
     "\n", "prima"),
    # 16. chi ha pubblicato annulla a presa in corso
    ("src/app/cancel.rs",
     "    // Phase 1/6: maker cancelled before the trade went active — release any\n",
     "    // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "    " + E + "emit_by(\"canceled\", &order, &event.sender.to_string());\n"
     "\n", "prima"),
    # 17. chi ha pubblicato ritira un ordine ancora nel libro: non c'e'
    #     nessuno da avvisare, ma il server deve SAPERE chi e' stato — o la
    #     rete di sicurezza dal libro avviserebbe lui del suo stesso gesto
    ("src/app/cancel.rs",
     "    bond::release_taker_bonds_for_order_or_warn(pool, order.id, \"pending_maker_cancel\").await;\n",
     "    // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "    " + E + "emit_by_detail(\n"
     "        \"canceled\",\n"
     "        &*order,\n"
     "        &event.sender.to_string(),\n"
     "        \"pending\",\n"
     "    );\n"
     "\n", "prima"),
    # 18. la presa non completata in tempo. `order` porta ancora le chiavi
    #     (quelle di `edited_order` sono gia' azzerate).
    ("src/scheduler.rs",
     "                            // Notify users about order status changes - here order is updated\n"
     "                            notify_users_canceled_order(&order_updated, &order, maker_action).await;\n",
     "                            // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "                            " + E + "emit_detail(\n"
     "                                \"expired\",\n"
     "                                &order,\n"
     "                                \"mostro\",\n"
     "                                if matches!(new_status, Status::Pending) {\n"
     "                                    \"taker-timeout\"\n"
     "                                } else {\n"
     "                                    \"maker-timeout\"\n"
     "                                },\n"
     "                            );\n", "prima"),
    # 19. la garanzia e' arrivata al capolinea del suo CLTV
    ("src/scheduler.rs",
     "                notify_users_canceled_order(&updated, &order, Some(Action::Canceled)).await;\n",
     "                // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "                " + E + "emit_detail(\n"
     "                    \"expired\",\n"
     "                    &order,\n"
     "                    \"mostro\",\n"
     "                    \"escrow-deadline\",\n"
     "                );\n",
     "prima"),
    # 20. l'ordine e' scaduto nel libro senza che nessuno lo prendesse
    ("src/scheduler.rs",
     "                        let order_snapshot = order_updated.clone();\n",
     "                        // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "                        " + E + "emit_detail(\n"
     "                            \"expired\",\n"
     "                            &order_snapshot,\n"
     "                            \"mostro\",\n"
     "                            \"book\",\n"
     "                        );\n",
     "dopo"),
    # 21. disputa aperta
    ("src/app/dispute.rs",
     "    // Publish dispute event to network\n"
     "    publish_dispute_event(ctx, &dispute, my_keys, is_buyer_dispute)\n",
     "    // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "    " + E + "emit(\n"
     "        \"dispute-opened\",\n"
     "        &order,\n"
     "        if is_buyer_dispute { \"buyer\" } else { \"seller\" },\n"
     "    );\n"
     "\n", "prima"),
    # 22-23. le due chiusure del moderatore
    ("src/app/admin_cancel.rs", "    // We create a Message for cancel\n",
     "    // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "    " + E + "emit_detail(\"canceled\", &order, \"mostro\", \"admin\");\n", "prima"),
    ("src/app/admin_settle.rs", "    // we check if there is a dispute\n",
     "    // Barattolo fork (patch 0007): tell the marketplace server.\n"
     "    " + E + "emit_detail(\"released\", &order, \"mostro\", \"admin\");\n"
     "\n", "prima"),
]

modulo = os.path.join(QUI, "barattolo_eventi.rs")
if not os.path.isfile(modulo):
    sys.exit("FERMO: manca barattolo_eventi.rs accanto a questo script — niente scritto")
if not os.path.isfile("src/main.rs"):
    sys.exit("FERMO: non sono nella radice di mostro-src — niente scritto")
if not os.path.isfile("src/barattolo_fee.rs"):
    sys.exit("FERMO: manca src/barattolo_fee.rs — la 0007 sta SOPRA la 0005, che qui non c'e'")
if os.path.exists("src/barattolo_eventi.rs") and leggi("src/barattolo_eventi.rs") != leggi(modulo):
    sys.exit("FERMO: src/barattolo_eventi.rs esiste gia' ed e' DIVERSO — niente scritto")

# LE AZIONI: ogni stringa mandata da un aggancio deve stare nell'elenco del
# modulo. Rust non lo controlla (sono stringhe), quindi lo controlla questo.
sorgente = leggi(modulo)
m = re.search(r"pub const ACTIONS: \[&str; (\d+)\] = \[(.*?)\];", sorgente, flags=re.S)
if not m:
    sys.exit("FERMO: non trovo l'elenco ACTIONS in barattolo_eventi.rs — niente scritto")
note = set(re.findall(r'"([a-z-]+)"', m.group(2)))
if len(note) != int(m.group(1)):
    sys.exit("FERMO: ACTIONS dichiara %s voci e ne elenca %d — niente scritto" % (m.group(1), len(note)))
usate = set()
for _, _, nuovo, _ in AGGANCI:
    usate |= set(re.findall(r'emit(?:_by|_detail|_by_detail)?\(\s*"([a-z-]+)"', nuovo))
ignote = usate - note
if ignote:
    sys.exit("FERMO: azioni negli agganci che il modulo non conosce: %s" % sorted(ignote))
# payout-failed e taken passano da due entrate dedicate, senza stringa
mute = note - usate - {"taken"}
if mute:
    sys.exit("FERMO: azioni dell'elenco che nessun aggancio manda: %s" % sorted(mute))
# I DETTAGLI sono un vocabolario CHIUSO che il server legge per nome: ogni
# parola-macchina di un aggancio dev'essere scritta nel modulo (il blocco
# «THE DETAILS»), o di qua si manda una parola che di la' nessuno conosce.
parole = set()
for _, _, nuovo, _ in AGGANCI:
    if "barattolo_eventi::emit" in nuovo:
        parole |= set(re.findall(r'"([a-z-]+)"', nuovo))
parole -= note | {"buyer", "seller", "mostro", "release"}
blocco = sorgente[sorgente.find("// THE DETAILS"):sorgente.find("pub fn is_known_action")]
sconosciute = sorted(p for p in parole if not re.search(r"\b%s\b" % re.escape(p), blocco))
if sconosciute:
    sys.exit("FERMO: dettagli negli agganci che il modulo non dichiara: %s" % sconosciute)

# PRIMA si controllano tutte le ancore, su una copia in memoria
testi = {}
for percorso, ancora, nuovo, dove in AGGANCI:
    t = testi.get(percorso)
    if t is None:
        if not os.path.isfile(percorso):
            sys.exit("FERMO: manca %s — niente scritto" % percorso)
        t = leggi(percorso)
    # I FINE-RIGA SONO QUELLI DEL FILE: `barattolo_fee.rs` arriva sul nodo
    # con uno scp dal PC, e se e' partito da un checkout Windows porta
    # CRLF — un'ancora scritta con `\n` non lo troverebbe, e direbbe
    # «0 volte» su un file che l'ancora ce l'ha
    if "\r\n" in t:
        ancora = ancora.replace("\n", "\r\n")
        nuovo = nuovo.replace("\n", "\r\n")
    if nuovo in t:
        sys.exit("FERMO: %s porta gia' questo aggancio — la patch e' gia' applicata?" % percorso)
    n = t.count(ancora)
    if n != 1:
        sys.exit("FERMO: in %s l'ancora compare %d volte (attesa 1) — niente scritto:\n%s"
                 % (percorso, n, ancora))
    if dove == "dopo":
        rimpiazzo = ancora + nuovo
    elif dove == "prima":
        rimpiazzo = nuovo + ancora
    else:
        rimpiazzo = nuovo
    testi[percorso] = t.replace(ancora, rimpiazzo)

# NESSUN AGGANCIO DENTRO I TEST: un'ancora finita sotto `#[cfg(test)]`
# compilerebbe, girerebbe nei test e in servizio non direbbe niente.
for percorso, t in testi.items():
    if percorso == "src/main.rs":
        continue
    taglio = t.find("#[cfg(test)]\nmod ")
    if taglio < 0:
        taglio = t.find("#[cfg(test)]")
    if taglio >= 0 and "barattolo_eventi::" in t[taglio:]:
        sys.exit("FERMO: in %s un aggancio e' finito DENTRO i test — niente scritto" % percorso)

if SECCO:
    print("A SECCO: %d agganci in %d file, tutte le ancore uniche, %d azioni note. Niente scritto."
          % (len(AGGANCI), len(testi), len(note) + 1))
    sys.exit(0)
for percorso, t in testi.items():
    scrivi(percorso, t)
scrivi("src/barattolo_eventi.rs", sorgente)
print("FATTO: %d agganci in %d file, piu' src/barattolo_eventi.rs" % (len(AGGANCI), len(testi)))
print("Adesso: i test, il commit, git format-patch -1 --start-number 7")
