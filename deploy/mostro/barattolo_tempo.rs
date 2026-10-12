//! Barattolo fork (patch 0011): the maker's own waiting window, and an order
//! that goes back to the book when its maker lets a take lapse.
//!
//! Upstream gives ONE window (`expiration_seconds`) to whoever holds the
//! waiting duty, and when it is the MAKER who lets it lapse the order is
//! cancelled outright. That fits a taker — he has the phone in his hand —
//! and it does not fit a maker: he published hours or days ago and cannot
//! know when someone will take the order. A maker who was asleep finds
//! the order gone and has to publish it again by hand.
//!
//! Two optional keys in `[mostro]`. With both absent the daemon behaves
//! exactly as upstream, byte for byte on the wire:
//!
//! - `maker_expiration_seconds`: the waiting window of the MAKER, when he
//!   is the one on duty (paying the hold invoice of his sell order, or
//!   giving the invoice of his buy order). The taker keeps
//!   `expiration_seconds`. Absent or 0: the maker has the taker's window.
//! - `maker_timeout_limit`: after how many maker lapses IN A ROW the order
//!   is removed. `2` means the first lapse puts the order back in the
//!   book and the second cancels it. Absent, 0 or 1: upstream (the first
//!   lapse cancels).
//!
//! Both are advertised in the kind 38385 info event, under the same
//! names, only when they are in force — so a client can tell the maker
//! how long he really has, and that the order comes back.
//!
//! THE LAPSES are counted in a side table, `barattolo_maker_lapses`,
//! created with `CREATE TABLE IF NOT EXISTS` and deliberately kept OUT of
//! the sqlx migrations, like `barattolo_fees`: rolling back to an image
//! without this patch needs nothing, and a new upstream migration never
//! collides. The count is idempotent per waiting episode — it is keyed on
//! `taken_at`, which the daemon re-stamps at every take and every duty
//! handoff — so a scheduler tick that retries the same timeout does not
//! count it twice. It never needs a reset: once a maker takes his step
//! the trade is on, and that order does not come back to the book.
//!
//! NOT ON A NODE THAT BONDS THE MAKER (`apply_to = "make" | "both"`): on a
//! maker-responsible timeout the bond code releases every bond on the
//! order — right for the taker's, who is not at fault — and a republished
//! order would sit in the book with its maker bond already released.
//! There the upstream cancel stays, and the limit is not advertised.

use crate::config::types::{AntiAbuseBondSettings, MostroSettings};
use sqlx::SqlitePool;
use tracing::{info, warn};

const WAITING_PAYMENT: &str = "waiting-payment";
const WAITING_BUYER_INVOICE: &str = "waiting-buyer-invoice";

/// The `[mostro]` settings, or `None` where they were never loaded (unit
/// tests of the callers): then every function here is the upstream rule.
fn settings() -> Option<&'static MostroSettings> {
    crate::config::MOSTRO_CONFIG.get().map(|s| &s.mostro)
}

/// Is the party on duty in this waiting state the order's MAKER? A sell
/// order waits for its maker in `waiting-payment` (he pays the hold
/// invoice), a buy order in `waiting-buyer-invoice` (he gives the invoice).
/// It is the complement of the scheduler's republish arm.
pub fn duty_is_makers(status: &str, kind: &str) -> bool {
    matches!(
        (status, kind),
        (WAITING_PAYMENT, "sell") | (WAITING_BUYER_INVOICE, "buy")
    )
}

/// PURE: the maker's window — the configured one when set and positive,
/// otherwise the taker's.
pub fn maker_window_from(configured: Option<u32>, taker_secs: u32) -> u32 {
    configured.filter(|s| *s > 0).unwrap_or(taker_secs)
}

fn maker_window(taker_secs: u32) -> u32 {
    maker_window_from(
        settings().and_then(|s| s.maker_expiration_seconds),
        taker_secs,
    )
}

/// PURE: the window of whoever holds the duty, given both.
pub fn window_with(status: &str, kind: &str, taker_secs: u32, maker_secs: u32) -> u32 {
    if duty_is_makers(status, kind) {
        maker_secs
    } else {
        taker_secs
    }
}

/// The waiting window, in seconds, of whoever holds the duty in this state.
pub fn window_of(status: &str, kind: &str, taker_secs: u32) -> u32 {
    window_with(status, kind, taker_secs, maker_window(taker_secs))
}

/// The shorter of the two windows: the cutoff `find_order_by_seconds`
/// selects with, before each row is judged on its own window.
pub fn shortest_window(taker_secs: u32) -> u32 {
    taker_secs.min(maker_window(taker_secs))
}

/// Has the window of whoever holds the duty really elapsed?
pub fn elapsed(status: &str, kind: &str, taken_at: i64, now: i64, taker_secs: u32) -> bool {
    taken_at < now - window_of(status, kind, taker_secs) as i64
}

/// PURE: after how many maker lapses in a row the order is removed, or 0
/// when the republish is off — not configured, below 2, or a node that
/// bonds the maker.
pub fn limit_from(configured: Option<u32>, maker_is_bonded: bool) -> u32 {
    match configured {
        Some(n) if n >= 2 && !maker_is_bonded => n,
        _ => 0,
    }
}

fn maker_is_bonded(bond: Option<&AntiAbuseBondSettings>) -> bool {
    bond.is_some_and(|b| b.enabled && b.apply_to.applies_to_maker())
}

/// The two tags of the info event, as `(name, value)`; each one only when
/// it is in force, so a node without the keys publishes what it always did.
pub fn info_pairs(
    mostro: &MostroSettings,
    bond: Option<&AntiAbuseBondSettings>,
) -> Vec<(&'static str, String)> {
    let mut pairs = Vec::new();
    if let Some(secs) = mostro.maker_expiration_seconds.filter(|s| *s > 0) {
        pairs.push(("maker_expiration_seconds", secs.to_string()));
    }
    let limit = limit_from(mostro.maker_timeout_limit, maker_is_bonded(bond));
    if limit > 0 {
        pairs.push(("maker_timeout_limit", limit.to_string()));
    }
    pairs
}

async fn ensure_table(pool: &SqlitePool) -> Result<(), sqlx::Error> {
    sqlx::query(
        "CREATE TABLE IF NOT EXISTS barattolo_maker_lapses (
            order_id TEXT PRIMARY KEY,
            lapses INTEGER NOT NULL,
            taken_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )",
    )
    .execute(pool)
    .await
    .map(|_| ())
}

/// Counts this maker lapse and returns how many the order has had in a
/// row. Idempotent per waiting episode: the same `taken_at` counted again
/// (a tick that retries after a failed persist) leaves the count alone.
pub async fn record_lapse(
    pool: &SqlitePool,
    order_id: &str,
    taken_at: i64,
) -> Result<u32, sqlx::Error> {
    ensure_table(pool).await?;
    sqlx::query(
        "INSERT INTO barattolo_maker_lapses (order_id, lapses, taken_at, updated_at)
         VALUES (?1, 1, ?2, strftime('%s','now'))
         ON CONFLICT(order_id) DO UPDATE SET
            lapses = lapses + (taken_at <> excluded.taken_at),
            taken_at = excluded.taken_at,
            updated_at = excluded.updated_at",
    )
    .bind(order_id)
    .bind(taken_at)
    .execute(pool)
    .await?;
    let row = sqlx::query_as::<_, (i64,)>(
        "SELECT lapses FROM barattolo_maker_lapses WHERE order_id = ?1",
    )
    .bind(order_id)
    .fetch_one(pool)
    .await?;
    Ok(row.0.max(0) as u32)
}

/// Does this waiting-state timeout put the order BACK IN THE BOOK although
/// the party at fault is its maker? Counts the lapse while answering, so
/// call it once per timeout, after the bond step and before the
/// cancel/republish decision. `false` whenever the duty is the taker's
/// (upstream already republishes), the feature is off, this lapse reaches
/// the limit, or the count cannot be written — then upstream's cancel runs.
pub async fn maker_back_to_book(
    pool: &SqlitePool,
    order_id: &str,
    status: &str,
    kind: &str,
    taken_at: i64,
    bond: Option<&AntiAbuseBondSettings>,
) -> bool {
    if !duty_is_makers(status, kind) {
        return false;
    }
    let limit = limit_from(
        settings().and_then(|s| s.maker_timeout_limit),
        maker_is_bonded(bond),
    );
    if limit == 0 {
        return false;
    }
    match record_lapse(pool, order_id, taken_at).await {
        Ok(lapses) if lapses < limit => {
            info!("barattolo_tempo: order {order_id}: maker lapse {lapses} of {limit}, back to the book");
            true
        }
        Ok(lapses) => {
            info!("barattolo_tempo: order {order_id}: maker lapse {lapses} of {limit}, the order is removed");
            false
        }
        Err(e) => {
            warn!("barattolo_tempo: could not count the maker lapse of {order_id} ({e}): cancelling as upstream does");
            false
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use sqlx::sqlite::SqlitePoolOptions;

    async fn pool() -> SqlitePool {
        // one connection: every connection to `sqlite::memory:` is its own db
        SqlitePoolOptions::new()
            .max_connections(1)
            .connect("sqlite::memory:")
            .await
            .unwrap()
    }

    #[test]
    fn the_duty_is_the_makers_in_the_two_states_upstream_cancels() {
        // the maker of a sell order pays the hold invoice
        assert!(duty_is_makers("waiting-payment", "sell"));
        // the maker of a buy order gives the invoice
        assert!(duty_is_makers("waiting-buyer-invoice", "buy"));
        // the other two are the taker's, and upstream republishes them
        assert!(!duty_is_makers("waiting-buyer-invoice", "sell"));
        assert!(!duty_is_makers("waiting-payment", "buy"));
        // nothing else is a waiting duty
        assert!(!duty_is_makers("active", "sell"));
        assert!(!duty_is_makers("pending", "buy"));
    }

    #[test]
    fn without_the_key_the_maker_has_the_takers_window() {
        assert_eq!(maker_window_from(None, 1800), 1800);
        assert_eq!(maker_window_from(Some(0), 1800), 1800);
        assert_eq!(maker_window_from(Some(10_800), 1800), 10_800);
        // a maker window SHORTER than the taker's is the operator's choice
        assert_eq!(maker_window_from(Some(600), 1800), 600);
    }

    #[test]
    fn each_party_is_judged_on_its_own_window() {
        // sell order: the buyer (taker) gives the invoice in 30 minutes...
        assert_eq!(window_with("waiting-buyer-invoice", "sell", 1800, 10_800), 1800);
        // ...then the seller (maker) pays the hold invoice in three hours
        assert_eq!(window_with("waiting-payment", "sell", 1800, 10_800), 10_800);
        // buy order: the seller (taker) pays in 30 minutes, the buyer
        // (maker) gives the invoice in three hours
        assert_eq!(window_with("waiting-payment", "buy", 1800, 10_800), 1800);
        assert_eq!(window_with("waiting-buyer-invoice", "buy", 1800, 10_800), 10_800);
    }

    #[test]
    fn with_no_settings_loaded_the_rule_is_upstreams() {
        // unit tests of the callers never load `MOSTRO_CONFIG` with the new
        // keys: there the window is the one they pass in, for both parties
        if settings().is_some_and(|s| s.maker_expiration_seconds.is_some()) {
            return;
        }
        assert_eq!(window_of("waiting-payment", "sell", 900), 900);
        assert_eq!(shortest_window(900), 900);
        assert!(elapsed("waiting-payment", "sell", 1_000, 1_901, 900));
        assert!(!elapsed("waiting-payment", "sell", 1_000, 1_900, 900));
    }

    #[test]
    fn the_limit_is_off_unless_it_can_put_the_order_back_at_least_once() {
        assert_eq!(limit_from(None, false), 0);
        assert_eq!(limit_from(Some(0), false), 0);
        // 1 = the first lapse removes the order: that is upstream
        assert_eq!(limit_from(Some(1), false), 0);
        assert_eq!(limit_from(Some(2), false), 2);
        assert_eq!(limit_from(Some(3), false), 3);
        // a node that bonds the maker keeps upstream's cancel
        assert_eq!(limit_from(Some(2), true), 0);
    }

    #[test]
    fn the_info_event_carries_only_what_is_in_force() {
        let off = MostroSettings::default();
        assert!(info_pairs(&off, None).is_empty());

        let on = MostroSettings {
            maker_expiration_seconds: Some(10_800),
            maker_timeout_limit: Some(2),
            ..MostroSettings::default()
        };
        assert_eq!(
            info_pairs(&on, None),
            vec![
                ("maker_expiration_seconds", "10800".to_string()),
                ("maker_timeout_limit", "2".to_string()),
            ]
        );

        // a limit of 1 is upstream's rule: it is not advertised
        let window_only = MostroSettings {
            maker_expiration_seconds: Some(10_800),
            maker_timeout_limit: Some(1),
            ..MostroSettings::default()
        };
        assert_eq!(
            info_pairs(&window_only, None),
            vec![("maker_expiration_seconds", "10800".to_string())]
        );
    }

    #[tokio::test]
    async fn a_lapse_is_counted_once_per_waiting_episode() {
        let pool = pool().await;
        // first take, the maker lets it lapse
        assert_eq!(record_lapse(&pool, "order-a", 1_000).await.unwrap(), 1);
        // the tick retries the same timeout: same `taken_at`, same count
        assert_eq!(record_lapse(&pool, "order-a", 1_000).await.unwrap(), 1);
        // the order went back to the book and was taken again: a new episode
        assert_eq!(record_lapse(&pool, "order-a", 5_000).await.unwrap(), 2);
        assert_eq!(record_lapse(&pool, "order-a", 5_000).await.unwrap(), 2);
        // another order has its own count
        assert_eq!(record_lapse(&pool, "order-b", 5_000).await.unwrap(), 1);
    }

    #[tokio::test]
    async fn the_takers_duty_never_touches_the_count() {
        let pool = pool().await;
        // whatever the settings, a taker-responsible timeout is not ours:
        // upstream republishes it, and no row is written
        assert!(
            !maker_back_to_book(&pool, "order-c", "waiting-buyer-invoice", "sell", 1_000, None)
                .await
        );
        assert!(!maker_back_to_book(&pool, "order-c", "waiting-payment", "buy", 1_000, None).await);
        ensure_table(&pool).await.unwrap();
        let rows = sqlx::query_as::<_, (i64,)>("SELECT COUNT(*) FROM barattolo_maker_lapses")
            .fetch_one(&pool)
            .await
            .unwrap();
        assert_eq!(rows.0, 0);
    }
}
