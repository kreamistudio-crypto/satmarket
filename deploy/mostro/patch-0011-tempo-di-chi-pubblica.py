#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch 0011 del fork — IL TEMPO DI CHI PUBBLICA.

Si lancia SUL NODO, dentro ~/nodo/mostro-src sul branch barattolo/v0.19.0,
SOPRA la 0007 (pretende `src/barattolo_eventi.rs`, e si ferma se manca),
con `barattolo_tempo.rs` nella STESSA cartella di questo script:
    python3 /percorso/patch-0011-tempo-di-chi-pubblica.py --secco  # prova e basta
    python3 /percorso/patch-0011-tempo-di-chi-pubblica.py          # applica
Ogni ancora deve comparire UNA volta: se anche una manca o e' doppia si
ferma SENZA SCRIVERE NIENTE. Poi si committa e si esporta con
`git format-patch -1 --start-number 11`.

IL DISEGNO (12 ott 2026, cantiere tempo-di-chi-pubblica, decisioni di
Andrea dopo lo studio). Upstream da' UNA finestra (`expiration_seconds`)
a chi deve fare il gesto, chiunque sia; e se a lasciarla scadere e' chi
ha PUBBLICATO l'ordine, l'ordine muore (`Status::Canceled`). Va bene per
chi PRENDE, che ha il telefono in mano; non per chi ha pubblicato ore o
giorni prima, e che dormiva (i casi veri del lancio: ordini presi di
notte, annullati, da ripubblicare a mano). Quattro cose, tutte spente
finche' nel `[mostro]` del settings.toml non compaiono le due chiavi:

A) IL TEMPO PER RUOLO. `maker_expiration_seconds` e' la finestra di chi
   ha pubblicato quando il dovere e' suo (pagare la garanzia della sua
   vendita, dare la fattura del suo acquisto); chi prende resta a
   `expiration_seconds`. `find_order_by_seconds` sceglie con la PIU' CORTA
   delle due e poi tiene le righe la cui finestra — quella di chi ha il
   dovere — e' davvero scaduta; `reconfirm_timeout_eligibility` giudica
   con la stessa. Senza la chiave i due numeri coincidono.
B) IL RITORNO NEL LIBRO. Se a scadere e' chi ha pubblicato, l'ordine torna
   `Pending` come per il tempo scaduto di chi ha preso (stesso ramo, stessi
   messaggi: `NewOrder` a chi ha pubblicato, `Canceled` a chi ha preso),
   finche' le mancate risposte DI FILA non arrivano a `maker_timeout_limit`
   (2 = la prima rimette nel libro, la seconda annulla). Le conta
   `barattolo_tempo` in una tabella a parte, FUORI dalle migrazioni sqlx
   (`barattolo_maker_lapses`, come `barattolo_fees`): il rollback resta la
   riga dell'immagine nel compose. NON su un nodo che chiede la cauzione
   a chi pubblica (`apply_to = make|both`): li' resta l'annullo upstream.
C) LA PAROLA AL SERVER. L'evento della 0007 diceva `taker-timeout` ogni
   volta che l'ordine tornava `Pending`: col ritorno per colpa di chi ha
   pubblicato il server avrebbe contato un «non completato» a chi ha
   PRESO. Adesso quel ritorno ha la sua parola, `maker-republished`.
   ⚠️ IL SERVER DI BARATTOLO VA AGGIORNATO PRIMA DEL NODO: quello di ieri
   non la conosce, e la leggerebbe come un annullo.
D) LA VENDITA CHE RESTAVA «PENDING». `create_status_tags` pubblicava
   `waiting-payment` come in-progress solo sugli ordini di ACQUISTO: una
   vendita presa con la fattura gia' nel take (un'altra app) saltava
   `waiting-buyer-invoice` e restava `pending` nel libro per tutta
   l'attesa, mentre nessuno poteva prenderla. Con tre ore di attesa era
   un ordine fantasma per tre ore: ora esce in-progress anche lei (una
   riga, e la prova upstream che diceva il contrario emendata).
E i due tag nel 38385 (`maker_expiration_seconds`, `maker_timeout_limit`),
ciascuno solo quando e' in vigore: il client li legge per dire a chi ha
pubblicato quanto tempo ha davvero, e che l'ordine torna.

`slash.rs` NON SI TOCCA, e non e' una dimenticanza: sul tempo scaduto di
chi ha pubblicato `order_republishes_on_timeout` dice ancora «no», quindi
OGNI cauzione sull'ordine viene liberata — giusto per quella di chi ha
preso, che non c'entra; e la cauzione di chi pubblica non esiste, perche'
dove esiste il ritorno e' spento (punto B).

⚠️ MAI COMPILATA QUI (sul PC non c'e' cargo): le firme sono state LETTE sul
clone del tag v0.19.0 con le nove patch applicate (`git am`), e il patcher
e' stato fatto girare li' a secco e per davvero — il primo `cargo build` e
il primo `cargo test` sono quelli sul nodo, e vanno guardati.
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


# (file, ancora, testo nuovo, "dopo" | "prima" | "al posto")
AGGANCI = [
    # ── il modulo ────────────────────────────────────────────────────
    ("src/main.rs",
     "pub mod barattolo_fee;\n",
     "pub mod barattolo_tempo;\n", "dopo"),

    # ── A) le due chiavi di `[mostro]` ───────────────────────────────
    ("src/config/types.rs",
     "    /// Expiration seconds\n"
     "    pub expiration_seconds: u32,\n",
     "    /// Barattolo fork (patch 0011): the waiting window of the order's\n"
     "    /// MAKER when the duty is his (paying the hold invoice of his sell\n"
     "    /// order, giving the invoice of his buy order). The taker keeps\n"
     "    /// `expiration_seconds`. `None` or 0 ⇒ the maker has the taker's\n"
     "    /// window, so existing configs behave exactly as before. Read through\n"
     "    /// `barattolo_tempo`.\n"
     "    #[serde(default, skip_serializing_if = \"Option::is_none\")]\n"
     "    pub maker_expiration_seconds: Option<u32>,\n"
     "    /// Barattolo fork (patch 0011): after how many maker lapses IN A ROW\n"
     "    /// the order is removed. `2` ⇒ the first lapse puts the order back in\n"
     "    /// the book, the second cancels it. `None`, 0 or 1 ⇒ upstream: the\n"
     "    /// first lapse cancels.\n"
     "    #[serde(default, skip_serializing_if = \"Option::is_none\")]\n"
     "    pub maker_timeout_limit: Option<u32>,\n", "dopo"),
    ("src/config/types.rs",
     "            expiration_seconds: 900,\n",
     "            maker_expiration_seconds: None,\n"
     "            maker_timeout_limit: None,\n", "dopo"),
    ("settings.tpl.toml",
     "# Expiration of pending orders\n"
     "expiration_seconds = 900\n",
     "# Barattolo fork (patch 0011). The window above is the one of whoever\n"
     "# holds the waiting duty. Uncomment to give the order's MAKER a window\n"
     "# of his own (he cannot know when the order will be taken), and to put\n"
     "# the order back in the book when he lets a take lapse — until this\n"
     "# many lapses in a row, then the order is cancelled (2 = back to the\n"
     "# book once). Both absent = upstream behaviour.\n"
     "# maker_expiration_seconds = 10800\n"
     "# maker_timeout_limit = 2\n", "dopo"),

    # ── A) chi e' scaduto davvero ────────────────────────────────────
    ("src/db.rs",
     "    let exp_seconds = mostro_settings.expiration_seconds as u64;\n"
     "    let expire_time = Timestamp::now() - exp_seconds;\n"
     "    let order = sqlx::query_as::<_, Order>(\n"
     "        r#\"\n"
     "          SELECT *\n"
     "          FROM orders\n"
     "          WHERE taken_at < ?1 AND ( status == 'waiting-buyer-invoice' OR status == 'waiting-payment' )\n"
     "        \"#,\n"
     "    )\n"
     "    .bind(expire_time.as_secs() as i64)\n"
     "    .fetch_all(pool)\n"
     "    .await\n"
     "    .map_err(|e| MostroInternalErr(ServiceError::DbAccessError(e.to_string())))?;\n"
     "\n"
     "    Ok(order)\n"
     "}\n",
     "    // Barattolo fork (patch 0011): the maker has a waiting window of his\n"
     "    // own. Select with the SHORTER of the two, then keep the rows whose own\n"
     "    // window — the one of whoever holds the duty — has really elapsed.\n"
     "    // Without the new key the two are the same number, and this is\n"
     "    // upstream's query.\n"
     "    let taker_seconds = mostro_settings.expiration_seconds;\n"
     "    let exp_seconds = crate::barattolo_tempo::shortest_window(taker_seconds) as u64;\n"
     "    let expire_time = Timestamp::now() - exp_seconds;\n"
     "    let order = sqlx::query_as::<_, Order>(\n"
     "        r#\"\n"
     "          SELECT *\n"
     "          FROM orders\n"
     "          WHERE taken_at < ?1 AND ( status == 'waiting-buyer-invoice' OR status == 'waiting-payment' )\n"
     "        \"#,\n"
     "    )\n"
     "    .bind(expire_time.as_secs() as i64)\n"
     "    .fetch_all(pool)\n"
     "    .await\n"
     "    .map_err(|e| MostroInternalErr(ServiceError::DbAccessError(e.to_string())))?;\n"
     "\n"
     "    let now = Timestamp::now().as_secs() as i64;\n"
     "    Ok(order\n"
     "        .into_iter()\n"
     "        .filter(|o| {\n"
     "            crate::barattolo_tempo::elapsed(&o.status, &o.kind, o.taken_at, now, taker_seconds)\n"
     "        })\n"
     "        .collect())\n"
     "}\n", "al posto"),
    ("src/scheduler.rs",
     "    let still_expired = fresh.taken_at < Utc::now().timestamp() - exp_seconds as i64;\n",
     "    // Barattolo fork (patch 0011): the window is the one of whoever holds\n"
     "    // the duty — the maker has a window of his own.\n"
     "    let window = crate::barattolo_tempo::window_of(&fresh.status, &fresh.kind, exp_seconds);\n"
     "    let still_expired = fresh.taken_at < Utc::now().timestamp() - window as i64;\n", "al posto"),

    # ── B) il ritorno nel libro ──────────────────────────────────────
    ("src/scheduler.rs",
     "                        let (maker_action, new_status, edited_order) =\n"
     "                            match (order_status, order_kind) {\n",
     "                        // Barattolo fork (patch 0011): when it is the MAKER who\n"
     "                        // let the take lapse, the order goes back to the book\n"
     "                        // instead of being cancelled — until\n"
     "                        // `maker_timeout_limit` lapses in a row. Counted here,\n"
     "                        // after the bond step (a retried tick counts the same\n"
     "                        // `taken_at` once) and on the pre-mutation snapshot,\n"
     "                        // whose waiting status is intact.\n"
     "                        let maker_back_to_book = crate::barattolo_tempo::maker_back_to_book(\n"
     "                            pool,\n"
     "                            &order.id.to_string(),\n"
     "                            &order.status,\n"
     "                            &order.kind,\n"
     "                            order.taken_at,\n"
     "                            Settings::get_bond(),\n"
     "                        )\n"
     "                        .await;\n", "prima"),
    ("src/scheduler.rs",
     "                                (Status::WaitingBuyerInvoice, Kind::Buy)\n"
     "                                | (Status::WaitingPayment, Kind::Sell) => {\n"
     "                                    // Update order status\n"
     "                                    info!(\n"
     "                                        \"Canceled order Id {}, {}\",\n",
     "                                // Barattolo fork (patch 0011): the maker let the\n"
     "                                // take lapse and this is not the lapse that removes\n"
     "                                // the order — back to the book, as for a taker\n"
     "                                // timeout.\n"
     "                                (Status::WaitingBuyerInvoice, Kind::Buy)\n"
     "                                | (Status::WaitingPayment, Kind::Sell)\n"
     "                                    if maker_back_to_book =>\n"
     "                                {\n"
     "                                    let _ = update_order_to_initial_state(\n"
     "                                        pool,\n"
     "                                        order.id,\n"
     "                                        order.amount,\n"
     "                                        order.fee,\n"
     "                                        order.dev_fee,\n"
     "                                    )\n"
     "                                    .await;\n"
     "                                    info!(\n"
     "                                        \"Republishing order Id {}, {}\",\n"
     "                                        order.id,\n"
     "                                        if order_status == Status::WaitingPayment {\n"
     "                                            \"maker (seller) did not pay the hold invoice in time\"\n"
     "                                        } else {\n"
     "                                            \"maker (buyer) did not send their invoice in time\"\n"
     "                                        }\n"
     "                                    );\n"
     "                                    (\n"
     "                                        Some(Action::NewOrder),\n"
     "                                        Status::Pending,\n"
     "                                        edit_pubkeys_order(pool, &order).await,\n"
     "                                    )\n"
     "                                }\n", "prima"),

    # ── C) la parola al server ───────────────────────────────────────
    ("src/scheduler.rs",
     "                                if matches!(new_status, Status::Pending) {\n"
     "                                    \"taker-timeout\"\n"
     "                                } else {\n"
     "                                    \"maker-timeout\"\n"
     "                                },\n",
     "                                // Barattolo fork (patch 0011): a republish that is\n"
     "                                // the MAKER's fault has a word of its own, or the\n"
     "                                // server would read `Pending` as the taker's timeout.\n"
     "                                if maker_back_to_book {\n"
     "                                    \"maker-republished\"\n"
     "                                } else if matches!(new_status, Status::Pending) {\n"
     "                                    \"taker-timeout\"\n"
     "                                } else {\n"
     "                                    \"maker-timeout\"\n"
     "                                },\n", "al posto"),
    ("src/barattolo_eventi.rs",
     "//   expired                 book | taker-timeout | maker-timeout | escrow-deadline\n",
     "//   expired                 book | taker-timeout | maker-timeout | escrow-deadline\n"
     "//                           | maker-republished (patch 0011: the order is back in\n"
     "//                           the book although the lapse was its maker's)\n", "al posto"),

    # ── i due tag del 38385 ──────────────────────────────────────────
    ("src/nip33.rs",
     "    tags_vec.extend(escrow_tags(escrow, ln_settings));\n"
     "    tags_vec.extend(bond_policy_tags(bond_settings));\n",
     "    // Barattolo fork (patch 0011): the maker's own waiting window, and after\n"
     "    // how many maker lapses in a row the order is removed — each tag only\n"
     "    // when it is in force.\n"
     "    for (name, value) in crate::barattolo_tempo::info_pairs(mostro_settings, bond_settings) {\n"
     "        tags_vec.push(Tag::custom(name, vec![value]));\n"
     "    }\n", "dopo"),

    # ── D) la vendita che restava «pending» ──────────────────────────
    ("src/nip33.rs",
     "        Status::WaitingPayment => Ok((order.is_buy_order().is_ok(), Status::InProgress)),\n",
     "        // Barattolo fork (patch 0011): `waiting-payment` is published as\n"
     "        // in-progress on a SELL order too. Upstream emitted it only for buy\n"
     "        // orders, so a sell order taken with the invoice already in the take\n"
     "        // (it skips `waiting-buyer-invoice`) stayed `pending` on the book for\n"
     "        // the whole wait, while nobody could take it.\n"
     "        Status::WaitingPayment => Ok((true, Status::InProgress)),\n", "al posto"),
    # ...e la prova upstream che diceva il contrario (l'UNICO aggancio dentro i test)
    ("src/nip33.rs",
     "        // WaitingPayment on a sell order → not a buy order → don't emit.\n"
     "        order.status = Status::WaitingPayment.to_string();\n"
     "        assert_eq!(\n"
     "            create_status_tags(&order).unwrap(),\n"
     "            (false, Status::InProgress)\n"
     "        );\n",
     "        // Barattolo fork (patch 0011): WaitingPayment on a sell order is\n"
     "        // emitted too (upstream: not a buy order → don't emit).\n"
     "        order.status = Status::WaitingPayment.to_string();\n"
     "        assert_eq!(\n"
     "            create_status_tags(&order).unwrap(),\n"
     "            (true, Status::InProgress)\n"
     "        );\n", "al posto"),
]

modulo = os.path.join(QUI, "barattolo_tempo.rs")
if not os.path.isfile(modulo):
    sys.exit("FERMO: manca barattolo_tempo.rs accanto a questo script — niente scritto")
if not os.path.isfile("src/main.rs"):
    sys.exit("FERMO: non sono nella radice di mostro-src — niente scritto")
if not os.path.isfile("src/barattolo_eventi.rs"):
    sys.exit("FERMO: manca src/barattolo_eventi.rs — la 0011 sta SOPRA la 0007, che qui non c'e'")
sorgente = leggi(modulo)
if os.path.exists("src/barattolo_tempo.rs") and leggi("src/barattolo_tempo.rs").replace("\r\n", "\n") \
        != sorgente.replace("\r\n", "\n"):
    sys.exit("FERMO: src/barattolo_tempo.rs esiste gia' ed e' DIVERSO — niente scritto")

testi = {}
for percorso, ancora, nuovo, dove in AGGANCI:
    t = testi.get(percorso)
    if t is None:
        if not os.path.isfile(percorso):
            sys.exit("FERMO: manca %s — niente scritto" % percorso)
        t = leggi(percorso)
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

# LE PAROLE AL SERVER: quelle che questo script manda devono essere parole
# a macchina (lettere e trattini) — `clean_detail` le taglierebbe in silenzio.
for parola in ("maker-republished", "taker-timeout", "maker-timeout"):
    if not all(c.isalnum() or c in "-_" for c in parola) or len(parola) > 40:
        sys.exit("FERMO: «%s» non e' una parola a macchina — niente scritto" % parola)

# UN SOLO AGGANCIO DENTRO I TEST, ed e' l'emenda di nip33: gli altri devono
# stare nel codice vero, o compilerebbero, girerebbero nei test e in servizio
# non farebbero niente.
for percorso, t in testi.items():
    taglio = t.find("#[cfg(test)]\nmod ")
    if taglio < 0:
        taglio = t.find("#[cfg(test)]\r\nmod ")
    if taglio >= 0 and "barattolo_tempo::" in t[taglio:]:
        sys.exit("FERMO: in %s un aggancio e' finito DENTRO i test — niente scritto" % percorso)

if SECCO:
    print("A SECCO: %d agganci in %d file, tutte le ancore uniche, piu' src/barattolo_tempo.rs. Niente scritto."
          % (len(AGGANCI), len(testi)))
    sys.exit(0)
for percorso, t in testi.items():
    scrivi(percorso, t)
scrivi("src/barattolo_tempo.rs", sorgente.replace("\r\n", "\n"))
print("FATTO: %d agganci in %d file, piu' src/barattolo_tempo.rs" % (len(AGGANCI), len(testi)))
print("Adesso: i test, il commit, git format-patch -1 --start-number 11")
