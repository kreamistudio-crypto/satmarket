#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch 0009 del fork — PROPOSTA per la -bar7, NON APPLICATA (6 ott 2026).
LA FEE PER PARTE LETTA PER COPPIA DI CHIAVI, e via la seconda domanda al
server quando la cauzione si blocca.

Si lancia SUL NODO, dentro ~/nodo/mostro-src sul branch della -bar7, SOPRA
le otto (la 0008 deve esserci: il suo blocco B e' un'ancora).
    python3 /percorso/patch-0009-fee-per-chiavi.py --secco  # prova e basta
    python3 /percorso/patch-0009-fee-per-chiavi.py          # applica
Ogni ancora deve comparire UNA volta: se anche una manca o e' doppia si
ferma SENZA SCRIVERE NIENTE. Poi si committa e si esporta con
`git format-patch -1 --start-number 9`.

IL PERCHE' (lo studio sta in CANTIERI, «La cauzione e la fee per parte»):
la 0005 scrive UNA riga per ordine in `barattolo_fees` (INSERT OR REPLACE)
a ogni tentativo di presa; con la cauzione accesa i tentativi sono piu'
d'uno e la 0008 (blocco B) al blocco della cauzione RIFA la domanda dello
sconto al server e riscrive la riga del vincitore. Due buchi, provati sul
sorgente della v0.19.0 con le otto applicate e fatti girare in un modello:
1) LA SECONDA DOMANDA PUO' AVERE UN'ALTRA RISPOSTA. Se al blocco il server
   non risponde (un riavvio di barattolo, il circuito Tor, e dalla -bar7
   l'interruttore della cura 9 aperto per 60 s) la riga diventa fee piena
   per tutt'e due, mentre `order.fee` resta quella SCONTATA della presa
   (viene dal bond). `seller_fee` trova la riga che non combacia e ripiega
   su `order.fee`: chi vende paga la quota di chi compra. Compratore
   pioniere e venditore no → il venditore paga l'1% invece dell'1,5%
   (500 sats regalati su 100.000); venditore pioniere e compratore no →
   la riga combacia e il venditore perde lo sconto (500 sats in piu').
2) LA PRESA RIVALE CHE SCRIVE TARDI. Il blocco gira nel task del
   sottoscrittore LND, la presa nel ciclo dei messaggi: una presa rivale
   passata dal cancello PRIMA del blocco, con la domanda al server ancora
   in volo, scrive la sua riga DOPO la rilettura della 0008, sopra quella
   del vincitore. Su un acquisto (chi prende vende) la riga combacia e il
   vincitore paga la quota del rivale; su una vendita ripiega su
   `order.fee`.
Mai un flusso rotto, mai toccato chi COMPRA (il suo payout e' `order.fee`
del bond, sempre giusto): sbaglia solo la quota di chi vende, di mezzo
punto, nei due versi.

LA CURA, tre pezzi:
A) UNA RIGA PER TENTATIVO, per coppia di chiavi. `barattolo_fees_takes`
   (order_id, buyer, seller) accanto alla tabella di prima; la presa scrive
   li' e POI nella riga per ordine (che resta: e' il segno «sconto gia'
   dato» di `has_row` e la lettura degli ordini presi prima della 0009).
B) LA LETTURA PER COPPIA. `seller_fee_of` cerca la riga della coppia che
   l'ordine porta: la riga di un rivale non ci arriva mai, scriva quando
   vuole. Stessa regola di fiducia di prima (stesso importo, stessa fee di
   chi compra); una coppia senza riga su un ordine che ne ha di altri →
   `order.fee` (le altre non sono sue); nessuna riga per coppia → la
   lettura di prima. `show_hold_invoice` legge la fee PRIMA di scrivere le
   chiavi sull'ordine: le riceve dalla chiamata (`seller_fee_for`).
C) VIA LA RILETTURA DELLA 0008: al blocco nessuna domanda e nessuna
   scrittura, solo una riga di journal coi numeri su cui lo scambio gira
   (`log_winner`). `order.fee` (dal bond) e la riga della coppia nascono
   dalla STESSA risposta: non possono piu' scollarsi.

⚠️ MAI COMPILATA QUI (sul PC non c'e' cargo): provata sul clone del tag
v0.19.0 con le otto applicate via `git am` — patcher a secco e per davvero,
e `git am` delle nove su un secondo clone che da' lo stesso albero. Il
primo `cargo build` e `cargo test barattolo_fee` sono quelli del nodo.
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


# ── A, B: il modulo ────────────────────────────────────────────────────
DOC_VECCHIA = r"""//! Not covered: the anti-abuse bond path stashes `order.fee` in the taker
//! context and may race several takers on one order; this coordinator runs
//! with bonds disabled. Revisit before enabling them.
"""
DOC_NUOVA = r"""//! The anti-abuse bond (patch 0009; bonds on since 1 Oct 2026, for the
//! "Contanti" method): several takers may race on one order, each with its
//! own take attempt. Every attempt writes its fees under its PAIR of trade
//! keys (`barattolo_fees_takes`) and the seller's fee is read back by the
//! pair the order carries, so a losing attempt — even one whose write lands
//! after the winner's bond locked — never reaches the winner's numbers. At
//! lock nothing is asked of the server again: `order.fee` is the winner's
//! snapshot from the bond row and must stay paired with the row written
//! from the same answer. `barattolo_fees`, one row per order, is still
//! written at every attempt: it is the "ever discounted" marker of
//! [`apply_party_fees`] and what orders taken before this patch read.
"""

TABELLA_VECCHIA = r"""            created_at INTEGER NOT NULL
        )",
    )
    .execute(pool)
    .await
    .map(|_| ())
}
"""
TABELLA_NUOVA = r"""            created_at INTEGER NOT NULL
        )",
    )
    .execute(pool)
    .await?;
    // Barattolo fork (patch 0009): one row per take ATTEMPT, keyed by the
    // two trade keys, so racing takers under the anti-abuse bond cannot
    // overwrite each other's fees.
    sqlx::query(
        "CREATE TABLE IF NOT EXISTS barattolo_fees_takes (
            order_id TEXT NOT NULL,
            buyer TEXT NOT NULL,
            seller TEXT NOT NULL,
            amount INTEGER NOT NULL,
            fee_buyer INTEGER NOT NULL,
            fee_seller INTEGER NOT NULL,
            discount_buyer INTEGER NOT NULL DEFAULT 0,
            discount_seller INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            PRIMARY KEY (order_id, buyer, seller)
        )",
    )
    .execute(pool)
    .await
    .map(|_| ())
}
"""

PRIMA_DI_FEES_FOR = r"""/// The pure half of [`apply_party_fees`]: given the flags, what each party
"""
STORE_TAKE = r"""/// Trade keys are compared as lowercase hex without blanks (patch 0009):
/// the take handlers pass `to_hex()`, the order carries `to_string()` — the
/// same hex for nostr 0.45 — and this keeps a change of either from
/// silently missing the row.
fn key_of(key: &str) -> String {
    key.trim().to_ascii_lowercase()
}

/// Barattolo fork (patch 0009): the row of THIS take attempt under its two
/// trade keys, then the per-order row as before (the "ever discounted"
/// marker of [`has_row`] and what orders taken before this patch read).
/// Under the anti-abuse bond several attempts write here; the winner's row
/// is the one keyed by the pair its order ends up carrying.
#[allow(clippy::too_many_arguments)]
async fn store_take(
    pool: &SqlitePool,
    order_id: &str,
    buyer: &str,
    seller: &str,
    amount: i64,
    fee_buyer: i64,
    fee_seller: i64,
    flags: (bool, bool),
) -> Result<(), sqlx::Error> {
    ensure_table(pool).await?;
    sqlx::query(
        "INSERT OR REPLACE INTO barattolo_fees_takes
            (order_id, buyer, seller, amount, fee_buyer, fee_seller,
             discount_buyer, discount_seller, created_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, strftime('%s','now'))",
    )
    .bind(order_id)
    .bind(key_of(buyer))
    .bind(key_of(seller))
    .bind(amount)
    .bind(fee_buyer)
    .bind(fee_seller)
    .bind(flags.0 as i64)
    .bind(flags.1 as i64)
    .execute(pool)
    .await?;
    store(pool, order_id, amount, fee_buyer, fee_seller, flags).await
}

"""

STORE_VECCHIO = r"""    if let Err(e) = store(pool, &order_id, order.amount, fee_buyer, fee_seller, flags).await {
"""
STORE_NUOVO = r"""    // Barattolo fork (patch 0009): under this take's pair of trade keys too.
    if let Err(e) = store_take(
        pool,
        &order_id,
        buyer,
        seller,
        order.amount,
        fee_buyer,
        fee_seller,
        flags,
    )
    .await
    {
"""

SELLER_FEE_VECCHIO = r"""/// [`seller_fee_with`] on the global pool, for call sites that have none.
pub async fn seller_fee(order: &Order) -> i64 {
    match DB_POOL.get() {
        Some(pool) => seller_fee_with(pool.as_ref(), &order.id.to_string(), order.amount, order.fee).await,
        None => order.fee,
    }
}
"""
SELLER_FEE_NUOVO = r"""/// Barattolo fork (patch 0009): the seller's fee of the take made by THIS
/// pair of trade keys. The pair's row is trusted under the rule of
/// [`seller_fee_with`] (same amount, same buyer fee as the order now). A
/// pair with no row on an order that has rows of other attempts → those
/// are not ours, `order.fee` (a take with no discount writes nothing). No
/// row for any pair → an order taken before this patch: the old reader.
pub async fn seller_fee_of(
    pool: &SqlitePool,
    order_id: &str,
    buyer: &str,
    seller: &str,
    amount: i64,
    order_fee: i64,
) -> i64 {
    let row = sqlx::query_as::<_, (i64, i64, i64)>(
        "SELECT amount, fee_buyer, fee_seller FROM barattolo_fees_takes
         WHERE order_id = ?1 AND buyer = ?2 AND seller = ?3",
    )
    .bind(order_id)
    .bind(key_of(buyer))
    .bind(key_of(seller))
    .fetch_optional(pool)
    .await;
    match row {
        Ok(Some((row_amount, row_fee_buyer, fee_seller))) => {
            if row_amount == amount && row_fee_buyer == order_fee && fee_seller >= 0 {
                fee_seller
            } else {
                order_fee
            }
        }
        Ok(None) => {
            let others = sqlx::query_as::<_, (i64,)>(
                "SELECT 1 FROM barattolo_fees_takes WHERE order_id = ?1 LIMIT 1",
            )
            .bind(order_id)
            .fetch_optional(pool)
            .await;
            match others {
                Ok(None) => seller_fee_with(pool, order_id, amount, order_fee).await,
                _ => order_fee,
            }
        }
        // no table (its creation failed at start): the reader of before
        Err(_) => seller_fee_with(pool, order_id, amount, order_fee).await,
    }
}

/// [`seller_fee_of`] on the global pool, with the trade keys given by the
/// caller: `show_hold_invoice` reads the fee BEFORE it writes them on the
/// order (patch 0009).
pub async fn seller_fee_for(order: &Order, buyer: &str, seller: &str) -> i64 {
    match DB_POOL.get() {
        Some(pool) => {
            seller_fee_of(
                pool.as_ref(),
                &order.id.to_string(),
                buyer,
                seller,
                order.amount,
                order.fee,
            )
            .await
        }
        None => order.fee,
    }
}

/// [`seller_fee_for`] with the trade keys the order carries.
pub async fn seller_fee(order: &Order) -> i64 {
    let buyer = order.buyer_pubkey.clone().unwrap_or_default();
    let seller = order.seller_pubkey.clone().unwrap_or_default();
    seller_fee_for(order, &buyer, &seller).await
}

/// Barattolo fork (patch 0009): a taker bond has just locked and the order
/// carries the winner's snapshot. Nothing is asked again and nothing is
/// written — the winner's fees are the row of their own take attempt. One
/// journal line says which numbers the trade runs on.
pub async fn log_winner(pool: &SqlitePool, order: &Order) {
    let buyer = order.buyer_pubkey.clone().unwrap_or_default();
    let seller = order.seller_pubkey.clone().unwrap_or_default();
    let order_id = order.id.to_string();
    let fee_seller = seller_fee_of(pool, &order_id, &buyer, &seller, order.amount, order.fee).await;
    info!(
        "barattolo_fee: order {order_id}: bond locked, the trade runs on its winning take: amount {} fee buyer {} fee seller {fee_seller}",
        order.amount, order.fee
    );
}
"""

FINE_TEST_VECCHIA = r"""        store(&pool, id, 100_000, 1_500, 1_500, (false, false)).await.unwrap();
        assert_eq!(seller_fee_with(&pool, id, 100_000, 1_500).await, 1_500);
    }
}
"""
FINE_TEST_NUOVA = r"""        store(&pool, id, 100_000, 1_500, 1_500, (false, false)).await.unwrap();
        assert_eq!(seller_fee_with(&pool, id, 100_000, 1_500).await, 1_500);
    }

    // patch 0009: a buy order, two sellers race under the bond; A
    // (discounted) wins, B (full fee) writes AFTER A's bond locked
    #[tokio::test]
    async fn a_late_losing_take_never_reaches_the_winner() {
        let pool = pool().await;
        let id = "33333333-3333-3333-3333-333333333333";
        let (m, a, b) = (key('1'), key('2'), key('3'));
        store_take(&pool, id, &m, &a, 100_000, 1_500, 1_000, (false, true)).await.unwrap();
        store_take(&pool, id, &m, &b, 100_000, 1_500, 1_500, (false, false)).await.unwrap();
        // the per-order row is B's now: the reader of before says 1_500
        assert_eq!(seller_fee_with(&pool, id, 100_000, 1_500).await, 1_500);
        // the pair reader says A's own number
        assert_eq!(seller_fee_of(&pool, id, &m, &a, 100_000, 1_500).await, 1_000);
        // keys compare without case or blanks
        let a_loud = format!(" {} ", a.to_uppercase());
        assert_eq!(seller_fee_of(&pool, id, &m, &a_loud, 100_000, 1_500).await, 1_000);
    }

    #[tokio::test]
    async fn the_pair_row_is_trusted_only_for_this_take() {
        let pool = pool().await;
        let id = "44444444-4444-4444-4444-444444444444";
        let (s, c, d) = (key('4'), key('5'), key('6'));
        store_take(&pool, id, &c, &s, 100_000, 1_000, 1_000, (true, true)).await.unwrap();
        assert_eq!(seller_fee_of(&pool, id, &c, &s, 100_000, 1_000).await, 1_000);
        // the order carries another buyer fee: fall back to it
        assert_eq!(seller_fee_of(&pool, id, &c, &s, 100_000, 1_500).await, 1_500);
        // another amount: fall back
        assert_eq!(seller_fee_of(&pool, id, &c, &s, 90_000, 1_350).await, 1_350);
        // a pair with no row of its own, on an order with rows of other
        // attempts: those are not ours
        assert_eq!(seller_fee_of(&pool, id, &d, &s, 100_000, 1_500).await, 1_500);
    }

    #[tokio::test]
    async fn an_order_taken_before_0009_reads_the_old_row() {
        let pool = pool().await;
        let id = "55555555-5555-5555-5555-555555555555";
        let (c, s) = (key('7'), key('8'));
        store(&pool, id, 100_000, 1_500, 1_000, (false, true)).await.unwrap();
        assert_eq!(seller_fee_of(&pool, id, &c, &s, 100_000, 1_500).await, 1_000);
        // and with no row anywhere, upstream
        assert_eq!(seller_fee_of(&pool, "other", &c, &s, 100_000, 1_500).await, 1_500);
    }
}
"""

# ── C: il blocco della cauzione ────────────────────────────────────────
RILETTURA_0008 = r"""    // Barattolo fork (patch 0008): re-apply the per-party fees for the
    // WINNER. Patch 0005 writes one side row per order at every take
    // attempt; with concurrent bonds the last attempt's row overwrites the
    // winner's. The order keeps the numbers of its bond row (the buyer's
    // invoice was validated against them): only the side row is refreshed.
    {
        let mut ricalcolo = order.clone();
        let buyer = order.buyer_pubkey.clone().unwrap_or_default();
        let seller = order.seller_pubkey.clone().unwrap_or_default();
        crate::barattolo_fee::apply_party_fees(pool, &mut ricalcolo, &buyer, &seller).await;
    }
"""
SOLO_LA_RIGA = r"""    // Barattolo fork (patch 0009, in place of 0008's re-apply): the winner's
    // fees are the row of their own take attempt, keyed by the two trade
    // keys the order now carries. No second question to the server — an
    // answer that changed, or no answer, would split the seller's fee from
    // the buyer's snapshot above — and no write a losing attempt could undo.
    crate::barattolo_fee::log_winner(pool, &order).await;
"""

# ── B: show_hold_invoice ───────────────────────────────────────────────
HOLD_VECCHIO = r"""    let new_amount = order.amount + crate::barattolo_fee::seller_fee(&order).await;
"""
HOLD_NUOVO = r"""    // Barattolo fork (patch 0009): by the two trade keys of THIS take; the
    // order does not carry them yet (they are written further down).
    let barattolo_fee_seller = crate::barattolo_fee::seller_fee_for(
        &order,
        &buyer_pubkey.to_hex(),
        &seller_pubkey.to_hex(),
    )
    .await;
    let new_amount = order.amount + barattolo_fee_seller;
"""

AGGANCI = [
    ("src/barattolo_fee.rs", DOC_VECCHIA, DOC_NUOVA),
    ("src/barattolo_fee.rs", TABELLA_VECCHIA, TABELLA_NUOVA),
    ("src/barattolo_fee.rs", PRIMA_DI_FEES_FOR, STORE_TAKE + PRIMA_DI_FEES_FOR),
    ("src/barattolo_fee.rs", STORE_VECCHIO, STORE_NUOVO),
    ("src/barattolo_fee.rs", SELLER_FEE_VECCHIO, SELLER_FEE_NUOVO),
    ("src/barattolo_fee.rs", FINE_TEST_VECCHIA, FINE_TEST_NUOVA),
    ("src/app/bond/flow.rs", RILETTURA_0008, SOLO_LA_RIGA),
    ("src/util.rs", HOLD_VECCHIO, HOLD_NUOVO),
]

if not os.path.isfile("src/main.rs"):
    sys.exit("FERMO: non sono nella radice di mostro-src — niente scritto")
if not os.path.isfile("src/barattolo_fee.rs"):
    sys.exit("FERMO: manca src/barattolo_fee.rs — prima la 0005 (e le altre) — niente scritto")
if "barattolo_fees_takes" in leggi("src/barattolo_fee.rs"):
    sys.exit("FERMO: src/barattolo_fee.rs porta gia' la 0009 — niente scritto")

# PRIMA si controllano tutte le ancore, su una copia in memoria
testi = {}
for percorso, ancora, nuovo in AGGANCI:
    t = testi.get(percorso)
    if t is None:
        t = leggi(percorso)
    if "\r\n" in t:
        sys.exit("FERMO: %s e' in CRLF (checkout con autocrlf?) — niente scritto" % percorso)
    n = t.count(ancora)
    if n != 1:
        sys.exit("FERMO: in %s l'ancora compare %d volte (attesa 1) — niente scritto:\n%s"
                 % (percorso, n, ancora))
    testi[percorso] = t.replace(ancora, nuovo)

# IL CENSIMENTO: dopo la 0009 nessuno chiama piu' apply_party_fees fuori
# dalle due prese, e il blocco della cauzione non scrive fee.
for radice, _, nomi in os.walk("src"):
    for nome in nomi:
        if not nome.endswith(".rs"):
            continue
        percorso = os.path.join(radice, nome).replace(os.sep, "/")
        t = testi.get(percorso)
        if t is None:
            t = leggi(percorso)
        if "apply_party_fees(" in t and percorso not in (
                "src/barattolo_fee.rs", "src/app/take_buy.rs", "src/app/take_sell.rs"):
            sys.exit("FERMO: %s chiama ancora apply_party_fees — niente scritto" % percorso)

if SECCO:
    print("A SECCO: %d agganci in %d file, tutte le ancore uniche. Niente scritto."
          % (len(AGGANCI), len(testi)))
    sys.exit(0)
for percorso, t in testi.items():
    scrivi(percorso, t)
print("FATTO: %d agganci in %d file" % (len(AGGANCI), len(testi)))
print("Adesso: cargo fmt --check, cargo test barattolo_fee, il commit, "
      "git format-patch -1 --start-number 9")
