#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch 0013 del fork — IL TEMPO PER PAGARE, SCELTO DA CHI PUBBLICA.

Si lancia SUL NODO (o nel cloud, dove c'e' cargo), dentro mostro-src sul
branch del fork, SOPRA la 0012 (pretende `src/barattolo_tempo.rs` e
`src/barattolo_eventi.rs`, e si ferma se mancano). Il modulo nuovo,
`barattolo_finestra.rs`, deve stare ACCANTO a questo file:
    python3 /percorso/patch-0013-tempo-per-pagare.py --secco  # prova e basta
    python3 /percorso/patch-0013-tempo-per-pagare.py          # applica
Ogni ancora deve comparire UNA volta: se anche una manca o e' doppia si
ferma SENZA SCRIVERE NIENTE. Poi si committa e si esporta con
`git format-patch -1 --start-number 13`.

IL DISEGNO (18 nov 2026, cantiere tempo-pagamento, scelta di Andrea:
«Tutto insieme, nodo compreso»). Un venditore che scambia tanto (JJ)
vuole la velocita' del SEPA Instant: oggi chi prende un ordine e sparisce
gli tiene i sats fermi fino alla scadenza della garanzia (~92 ore), e
l'annullo d'accordo l'altro non lo manda mai. Su Barattolo chi pubblica
sceglie entro quanto si paga — un timer libero da 15 minuti a 24 ore,
a minuti interi (Andrea, 18 nov 2026: «un orologio con un timer che
decidi tu») — e chi prende lo legge prima di prendere. Allo scadere, con l'ordine ancora `active`
(nessun «pagato», nessuna disputa), il nodo annulla la hold invoice
COME IL GUARDIANO DELLA GARANZIA fa per un `active`: i sats tornano a chi
vende, e il server lo sa (`expired` / `payment-window`).

LA SCELTA LA CHIEDE AL SERVER, come lo sconto della 0005: `SmallOrder`
non ha un campo per lei, e cambiare il filo romperebbe gli altri client.
Un job suo, ogni minuto, FUORI dal ciclo seriale dei messaggi:
`{"ordini": [ids]}` -> `{"finestre": {id: secondi}}`. Valgono SOLO i
minuti interi da 900 a 86400 secondi; il tempo parte quando il NODO vede lo scambio `active`.
Un server bugiardo puo' al piu' annullare uno scambio attivo dopo un quarto d'ora
e ridare i sats a chi vende: mai spostarli altrove, mai toccare un
`fiat-sent` o una disputa. Senza `BARATTOLO_FINESTRA_URL` e
`BARATTOLO_FINESTRA_SEGRETO` (un segreto SUO, la M6 dell'audit) e' inerte:
nessuna richiesta, nessuna riga, nessun tag nel 38385.

I SETTE AGGANCI: il modulo in `main.rs`; il job in `start_scheduler`
accanto al guardiano; il job e il giro prima del guardiano; tre prove del
giro accanto a quelle del guardiano (usano il suo `StubEscrow`); la riga
del vocabolario e la prova pura del corpo in `barattolo_eventi.rs`; il
tag `barattolo_payment_windows` nel 38385, accanto a quelli della 0011.

PRIMA IL SERVER, POI IL NODO, come per la 0011 e la 0012: col server di
ieri la rotta /api/p2p/finestre non c'e' (404 = nessuna finestra, e il nodo
si comporta come oggi), e un `expired` / `payment-window` il server di
ieri lo leggerebbe come un annullo qualunque.
"""
import io
import os
import shutil
import sys

SECCO = "--secco" in sys.argv
QUI = os.path.dirname(os.path.abspath(__file__))
MODULO = os.path.join(QUI, "barattolo_finestra.rs")


def leggi(p):
    with io.open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()


def scrivi(p, t):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(t)


AZIONE, ATTORE, DETTAGLIO = "expired", "mostro", "payment-window"

GIRO = '''/// Barattolo fork (patch 0013): the time to pay, chosen by the maker (see
/// `barattolo_finestra`). Every minute, OUTSIDE the serial message loop:
/// learn the windows of the trades newly active, then cancel the `active`
/// trades whose window has ended — the same steps as the escrow guardian's
/// `active` branch below. Inert without its two variables.
async fn job_barattolo_payment_window(ctx: AppContext) {
    if !crate::barattolo_finestra::enabled() {
        info!("barattolo_finestra: BARATTOLO_FINESTRA_URL / BARATTOLO_FINESTRA_SEGRETO not set: no time to pay, as upstream");
        return;
    }
    let mut ln_client = if let Ok(client) = LndConnector::new().await {
        client
    } else {
        return error!("Failed to create LND client");
    };

    tokio::spawn(async move {
        loop {
            let now = Utc::now().timestamp();
            crate::barattolo_finestra::refresh(ctx.pool(), now).await;
            if let Err(e) = barattolo_payment_window_pass(&ctx, &mut ln_client, now).await {
                error!("payment window pass failed: {e}");
            }
            tokio::time::sleep(tokio::time::Duration::from_secs(60)).await;
        }
    });
}

/// One tick of [`job_barattolo_payment_window`] after the refresh, split
/// out for testing: cancel the trades whose window ended at `now`.
async fn barattolo_payment_window_pass(
    ctx: &AppContext,
    escrow: &mut dyn EscrowBackend,
    now: i64,
) -> Result<(), MostroError> {
    let pool = ctx.pool();
    let keys = ctx.keys().clone();
    let due = crate::barattolo_finestra::due_orders(pool, now)
        .await
        .map_err(|e| MostroInternalErr(ServiceError::DbAccessError(e.to_string())))?;

    for order in due {
        // Read it again right before acting: the buyer may have said the
        // fiat moved (or opened a dispute) since the query. Only a trade
        // that is STILL `active` loses its escrow.
        let order = match Order::by_id(pool, order.id).await {
            Ok(Some(fresh)) if fresh.status == Status::Active.to_string() => fresh,
            _ => continue,
        };
        let hash = match order.hash.as_ref() {
            Some(hash) => hash.clone(),
            None => continue,
        };
        if let Err(e) = escrow.cancel_hold_invoice(&hash).await {
            match bond::flow::classify_cancel_error(&e) {
                bond::flow::CancelOutcome::AlreadyDone => {
                    info!(
                        "payment_window: order {} hold invoice already canceled at LND; fixing state",
                        order.id
                    );
                }
                bond::flow::CancelOutcome::Transient => {
                    warn!(
                        "payment_window: cancel_hold_invoice failed for order {} ({e}); retrying next tick",
                        order.id
                    );
                    continue;
                }
            }
        }

        let updated = match update_order_event(&keys, Status::Canceled, &order).await {
            Ok(updated) => updated,
            Err(e) => {
                warn!(
                    "payment_window: could not publish cancel for order {} ({e}); retrying next tick",
                    order.id
                );
                continue;
            }
        };
        let updated = match updated.update(pool).await {
            Ok(updated) => updated,
            Err(e) => {
                warn!(
                    "payment_window: persist failed for order {} ({e}); retrying next tick",
                    order.id
                );
                continue;
            }
        };
        info!(
            "payment_window: order {} canceled — the buyer's time to pay ended with no fiat sent",
            order.id
        );
        // Barattolo fork (patch 0007's channel): tell the marketplace server.
        crate::barattolo_eventi::emit_detail(
            "%s",
            &order,
            "%s",
            "%s",
        );
        notify_users_canceled_order(&updated, &order, Some(Action::Canceled)).await;
        bond::resolve_range_maker_bond_at_close_or_warn(pool, &order, "payment_window").await;
    }
    Ok(())
}

''' % (AZIONE, ATTORE, DETTAGLIO)

PROVE = '''    // ── barattolo_payment_window_pass (patch 0013) ──────────────────────

    async fn window_row(ctx: &AppContext, order: &Order, seen_at: i64, seconds: i64) {
        crate::barattolo_finestra::ensure_table(ctx.pool()).await.unwrap();
        sqlx::query(
            "INSERT INTO barattolo_payment_windows (order_id, seen_active_at, seconds) VALUES (?1, ?2, ?3)",
        )
        .bind(order.id)
        .bind(seen_at)
        .bind(seconds)
        .execute(ctx.pool())
        .await
        .unwrap();
    }

    #[tokio::test]
    async fn payment_window_cancels_an_active_trade_when_its_time_ends() {
        let ctx = escrow_guardian_ctx(576, 24).await;
        let now = Utc::now().timestamp();
        let order = escrow_backed_order(Status::Active, now - 4_000)
            .create(ctx.pool())
            .await
            .unwrap();
        window_row(&ctx, &order, now - 3_600, 3_600).await;
        let mut escrow = StubEscrow::ok();

        // one second early: nothing moves
        barattolo_payment_window_pass(&ctx, &mut escrow, now - 1)
            .await
            .unwrap();
        let same = Order::by_id(ctx.pool(), order.id).await.unwrap().unwrap();
        assert_eq!(same.status, Status::Active.to_string());
        assert!(escrow.canceled().is_empty());

        barattolo_payment_window_pass(&ctx, &mut escrow, now)
            .await
            .unwrap();
        let updated = Order::by_id(ctx.pool(), order.id).await.unwrap().unwrap();
        assert_eq!(updated.status, Status::Canceled.to_string());
        assert_eq!(escrow.canceled(), vec![order.hash.clone().unwrap()]);
        let actions = queued_actions_for(order.id).await;
        assert_eq!(actions.len(), 2, "both parties must be told: {actions:?}");
        assert!(actions.iter().all(|a| *a == Action::Canceled));
    }

    #[tokio::test]
    async fn payment_window_never_touches_fiat_sent_or_no_window() {
        let ctx = escrow_guardian_ctx(576, 24).await;
        let now = Utc::now().timestamp();
        let sent = escrow_backed_order(Status::FiatSent, now - 90_000)
            .create(ctx.pool())
            .await
            .unwrap();
        window_row(&ctx, &sent, now - 86_400, 3_600).await;
        let none = escrow_backed_order(Status::Active, now - 90_000)
            .create(ctx.pool())
            .await
            .unwrap();
        window_row(&ctx, &none, now - 86_400, 0).await;
        let mut escrow = StubEscrow::ok();

        barattolo_payment_window_pass(&ctx, &mut escrow, now)
            .await
            .unwrap();

        for id in [sent.id, none.id] {
            let o = Order::by_id(ctx.pool(), id).await.unwrap().unwrap();
            assert_ne!(o.status, Status::Canceled.to_string());
        }
        assert!(escrow.canceled().is_empty());
    }

    #[tokio::test]
    async fn payment_window_retries_when_the_cancel_fails() {
        let ctx = escrow_guardian_ctx(576, 24).await;
        let now = Utc::now().timestamp();
        let order = escrow_backed_order(Status::Active, now - 4_000)
            .create(ctx.pool())
            .await
            .unwrap();
        window_row(&ctx, &order, now - 3_600, 3_600).await;
        let mut escrow = StubEscrow::failing("transport: connection refused");

        barattolo_payment_window_pass(&ctx, &mut escrow, now)
            .await
            .unwrap();

        let same = Order::by_id(ctx.pool(), order.id).await.unwrap().unwrap();
        assert_eq!(same.status, Status::Active.to_string());
        assert!(queued_actions_for(order.id).await.is_empty());
    }

'''

# (file, ancora, testo nuovo, "dopo" | "prima")
AGGANCI = [
    ("src/main.rs",
     "pub mod barattolo_tempo;\n",
     "pub mod barattolo_finestra;\n", "dopo"),

    ("src/scheduler.rs",
     "        job_enforce_escrow_deadline(ctx.clone()).await;\n",
     "        // Barattolo fork (patch 0013): the time to pay chosen by the maker\n"
     "        job_barattolo_payment_window(ctx.clone()).await;\n", "dopo"),

    ("src/scheduler.rs",
     "/// Guardian for the trade escrow's CLTV lifetime.\n",
     GIRO, "prima"),

    ("src/scheduler.rs",
     "    #[tokio::test]\n"
     "    async fn escrow_deadline_cancels_due_active_order_and_refunds_seller() {\n",
     PROVE, "prima"),

    ("src/barattolo_eventi.rs",
     "//                           | maker-republished (patch 0011: the order is back in\n"
     "//                           the book although the lapse was its maker's)\n",
     "//                           | payment-window (patch 0013: the buyer's time to pay,\n"
     "//                           chosen by the maker, ended with the trade `active`)\n",
     "dopo"),

    ("src/barattolo_eventi.rs",
     "    #[test]\n"
     "    fn lnd_failure_reasons_by_code() {\n",
     "    #[test]\n"
     "    fn the_time_to_pay_ends_as_mostros_expiry_and_says_why() {\n"
     "        // patch 0013: the daemon cancels, no user did\n"
     "        let event =\n"
     "            event_of(\"%s\", &order(), \"%s\", Some(\"%s\")).unwrap();\n"
     "        assert_eq!(event.actor, \"mostro\");\n"
     "        let body = payload(&event);\n"
     "        assert_eq!(body[\"action\"], \"expired\");\n"
     "        assert_eq!(body[\"detail\"], \"payment-window\");\n"
     "        assert!(body.get(\"sats\").is_none());\n"
     "    }\n"
     "\n" % (AZIONE, ATTORE, DETTAGLIO), "prima"),

    ("src/nip33.rs",
     "    for (name, value) in crate::barattolo_tempo::info_pairs(mostro_settings, bond_settings) {\n"
     "        tags_vec.push(Tag::custom(name, vec![value]));\n"
     "    }\n",
     "    // Barattolo fork (patch 0013): the times to pay a maker may choose,\n"
     "    // only when this daemon enforces them.\n"
     "    for (name, value) in crate::barattolo_finestra::info_pairs() {\n"
     "        tags_vec.push(Tag::custom(name, vec![value]));\n"
     "    }\n", "dopo"),
]

if not os.path.isfile("src/main.rs"):
    sys.exit("FERMO: non sono nella radice di mostro-src — niente scritto")
for serve, chi in (("src/barattolo_eventi.rs", "0007"), ("src/barattolo_tempo.rs", "0011"),
                   ("src/barattolo_fee.rs", "0005")):
    if not os.path.isfile(serve):
        sys.exit("FERMO: manca %s — la 0013 sta SOPRA la %s, che qui non c'e'" % (serve, chi))
if not os.path.isfile(MODULO):
    sys.exit("FERMO: manca barattolo_finestra.rs accanto al patcher — niente scritto")
if os.path.exists("src/barattolo_finestra.rs"):
    sys.exit("FERMO: src/barattolo_finestra.rs c'e' gia' — la patch e' gia' applicata?")

eventi = leggi("src/barattolo_eventi.rs")
elenco = eventi[eventi.find("pub const ACTIONS"):eventi.find("];", eventi.find("pub const ACTIONS"))]
if '"%s"' % AZIONE not in elenco:
    sys.exit("FERMO: «%s» non e' fra le ACTIONS della 0007 — niente scritto" % AZIONE)
if not all(c.isalnum() or c in "-_" for c in DETTAGLIO) or len(DETTAGLIO) > 40:
    sys.exit("FERMO: «%s» non e' una parola a macchina — niente scritto" % DETTAGLIO)

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
    testi[percorso] = t.replace(ancora, ancora + nuovo if dove == "dopo" else nuovo + ancora)


def taglio_dei_test(t):
    for capo in ("#[cfg(test)]\nmod ", "#[cfg(test)]\r\nmod "):
        if capo in t:
            return t.find(capo)
    return len(t)


# IL GIRO STA NEL CODICE VERO, le prove nei test.
sched = testi["src/scheduler.rs"]
taglio = taglio_dei_test(sched)
if not 0 <= sched.find("async fn barattolo_payment_window_pass(") < taglio:
    sys.exit("FERMO: in src/scheduler.rs il giro non e' nel codice vero — niente scritto")
if not sched.find("async fn payment_window_cancels_an_active_trade_when_its_time_ends") > taglio:
    sys.exit("FERMO: in src/scheduler.rs le prove sono finite FUORI dai test — niente scritto")
chiamata = '"%s",\n            &order,\n            "%s",\n            "%s",' % (AZIONE, ATTORE, DETTAGLIO)
if "\r\n" in sched:
    chiamata = chiamata.replace("\n", "\r\n")
if sched.count(chiamata) != 1 or not 0 <= sched.find(chiamata) < taglio:
    sys.exit("FERMO: in src/scheduler.rs l'evento non e' una volta sola nel codice vero — niente scritto")
modulo = testi["src/barattolo_eventi.rs"]
if not modulo.find("fn the_time_to_pay_ends_as_mostros_expiry_and_says_why") > taglio_dei_test(modulo):
    sys.exit("FERMO: in src/barattolo_eventi.rs la prova e' finita FUORI dai test — niente scritto")

if SECCO:
    print("A SECCO: %d agganci in %d file piu' il modulo, tutte le ancore uniche. Niente scritto."
          % (len(AGGANCI), len(testi)))
    sys.exit(0)
for percorso, t in testi.items():
    scrivi(percorso, t)
shutil.copyfile(MODULO, "src/barattolo_finestra.rs")
print("FATTO: %d agganci in %d file, e src/barattolo_finestra.rs" % (len(AGGANCI), len(testi)))
print("Adesso: cargo test, il commit, git format-patch -1 --start-number 13")
