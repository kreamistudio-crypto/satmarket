//! Barattolo fork (patch 0013): the time to pay, chosen by the maker.
//!
//! Upstream gives the buyer of an `active` trade no deadline of its own:
//! the fiat leg may take as long as the escrow lives (`hold_invoice_cltv_delta`,
//! ~92 hours on this node), and only the escrow guardian ends it. A seller
//! who trades a lot and wants SEPA Instant speed has his sats frozen for
//! days by a buyer who took the order and vanished, and the only way out is
//! a cooperative cancel the vanished buyer will never send.
//!
//! On Barattolo the MAKER of an order chooses how long the buyer has to
//! send the fiat once the trade is active: any whole number of minutes
//! from 15 minutes to 24 hours (a timer the maker sets). The choice is shown to the taker BEFORE he takes. When the window ends with
//! the order still `active` (no `fiat-sent`, no dispute) this daemon cancels
//! the hold invoice exactly as the escrow guardian does for an `active`
//! order — the seller's sats come back — and tells the marketplace server
//! (`expired` / `payment-window`, patch 0007's channel).
//!
//! WHERE THE CHOICE COMES FROM. `mostro-core`'s `SmallOrder` has no field
//! for it, and touching the wire format would break every other client. So,
//! like the fee discount of patch 0005, this daemon ASKS the marketplace
//! server, which learned the choice from the maker's phone when the order
//! was published. One POST per tick for the orders whose window is still
//! unknown: `{"ordini": [ids]}` -> `{"finestre": {id: seconds}}`.
//!
//! WHAT A COMPROMISED SERVER CAN DO, and why it is acceptable: only a
//! window between [`MIN_WINDOW`] and [`MAX_WINDOW`], in whole minutes, is
//! accepted (anything else is "no window"),
//! the window is counted from the moment THIS daemon saw the trade become
//! active, and only `active` orders are ever touched. At worst a lying
//! server cancels an active trade 15 minutes after it started and the seller
//! gets his sats back — it can never move sats to anyone else, never touch a
//! trade whose buyer claimed the fiat moved (`fiat-sent`), never one in
//! dispute.
//!
//! WHEN THE WINDOW STARTS: the first scheduler tick that sees the order
//! `active` writes that time in the side table (`seen_active_at`). Upstream
//! keeps no "active since" stamp — `invoice_held_at` can be up to
//! `expiration_seconds` earlier, when the seller paid before the buyer gave
//! his invoice — and a tick is 60 seconds, so the buyer is never shortened:
//! the marketplace shows a deadline a little EARLIER than the one enforced
//! here.
//!
//! Fail OPEN, everywhere: no endpoint configured, a dead server, a non-200,
//! malformed JSON, an order missing from the answer — each one means "no
//! window", which is upstream's behaviour (the escrow guardian still ends
//! the trade at the escrow's horizon). A window is enforced only when the
//! server said it, inside the range, and the row was written.
//!
//! THE SIDE TABLE, `barattolo_payment_windows`, is created with
//! `CREATE TABLE IF NOT EXISTS` and kept OUT of the sqlx migrations, like
//! `barattolo_fees` and `barattolo_maker_lapses`: rolling back to an image
//! without this patch needs nothing.
//!
//! Without `BARATTOLO_FINESTRA_URL` and `BARATTOLO_FINESTRA_SEGRETO` this
//! module is inert: no request, no row, no tag in the info event.

use mostro_core::prelude::*;
use sqlx::SqlitePool;
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::Duration;
use tracing::{info, warn};

const ENV_URL: &str = "BARATTOLO_FINESTRA_URL";
/// A secret of its own, like patch 0007's (audit of 19 Sep 2026, M6): one
/// leaked secret must not open a second door.
const ENV_SECRET: &str = "BARATTOLO_FINESTRA_SEGRETO";

/// The windows a maker can choose: whole minutes from 15 minutes to 24
/// hours (Andrea, 18 Nov 2026: «un orologio con un timer che decidi tu»).
/// The server's answer is checked against this range, never trusted as a
/// bare number. Below 15 minutes a buyer could not even open his banking
/// app; above 24 hours the escrow guardian is the deadline anyway.
pub const MIN_WINDOW: i64 = 900;
pub const MAX_WINDOW: i64 = 86_400;
/// Whole minutes only: the server speaks in minutes, the daemon in seconds.
pub const WINDOW_STEP: i64 = 60;

/// How long one lookup may take. It runs in its own scheduler job, never in
/// the serial message loop, so a dead server stalls nobody; a cold Tor
/// circuit measured 10.6 s on this node.
const LOOKUP_BUDGET: Duration = Duration::from_secs(15);
/// At most this many orders per request (the server caps its lists too).
pub const MAX_PER_REQUEST: usize = 50;
/// Hard cap on the answer: `{"finestre": {...}}` for 50 ids is a few KB.
const MAX_ANSWER_BYTES: usize = 65_536;

fn endpoint() -> Option<(String, String)> {
    endpoint_from(
        std::env::var(ENV_URL).ok().as_deref(),
        std::env::var(ENV_SECRET).ok().as_deref(),
    )
}

/// PURE: the endpoint, only with BOTH the URL and the secret non-empty.
pub fn endpoint_from(url: Option<&str>, secret: Option<&str>) -> Option<(String, String)> {
    let url = url?.trim();
    let secret = secret?.trim();
    if url.is_empty() || secret.is_empty() {
        return None;
    }
    Some((url.to_string(), secret.to_string()))
}

/// Is the feature on? The scheduler job and the info tag ask this.
pub fn enabled() -> bool {
    endpoint().is_some()
}

/// The info-event pair (kind 38385): the range a maker may choose from,
/// `"900-86400"` (seconds, whole minutes in between), only
/// when this daemon enforces them. A client that does not see it must not
/// promise that a trade cancels by itself.
pub fn info_pairs() -> Vec<(&'static str, String)> {
    info_pairs_when(enabled())
}

/// PURE: [`info_pairs`] with the switch passed in.
pub fn info_pairs_when(on: bool) -> Vec<(&'static str, String)> {
    if !on {
        return Vec::new();
    }
    vec![("barattolo_payment_windows", format!("{MIN_WINDOW}-{MAX_WINDOW}"))]
}

/// PURE: a value of the server's answer as a window in seconds, or 0. Only
/// an integer inside [`MIN_WINDOW`]..=[`MAX_WINDOW`] and made of whole
/// minutes counts.
pub fn window_from(value: &serde_json::Value) -> i64 {
    match value.as_i64() {
        Some(secs)
            if (MIN_WINDOW..=MAX_WINDOW).contains(&secs) && secs % WINDOW_STEP == 0 =>
        {
            secs
        }
        _ => 0,
    }
}

/// PURE: the server's answer for the orders asked. Every id asked gets an
/// entry — 0 when the answer does not name it or names something outside
/// the range — so it is not asked again. `None` for an unreadable answer:
/// then nothing is written and the next tick asks again.
pub fn parse_answer(body: &str, asked: &[String]) -> Option<HashMap<String, i64>> {
    let value: serde_json::Value = serde_json::from_str(body).ok()?;
    let table = value.get("finestre")?;
    if !table.is_object() {
        return None;
    }
    Some(
        asked
            .iter()
            .map(|id| (id.clone(), window_from(&table[id.as_str()])))
            .collect(),
    )
}

/// PURE: has the window of a trade seen active at `seen_at` ended at `now`?
/// A zero or negative window never ends (it is "no window").
pub fn window_over(seen_at: i64, seconds: i64, now: i64) -> bool {
    seconds > 0 && seen_at > 0 && now >= seen_at.saturating_add(seconds)
}

pub async fn ensure_table(pool: &SqlitePool) -> Result<(), sqlx::Error> {
    sqlx::query(
        "CREATE TABLE IF NOT EXISTS barattolo_payment_windows (
            order_id TEXT PRIMARY KEY,
            seen_active_at INTEGER NOT NULL,
            seconds INTEGER,
            asked_at INTEGER NOT NULL DEFAULT 0
        )",
    )
    .execute(pool)
    .await
    .map(|_| ())
}

/// Stamps the first time each `active` trade is seen. Idempotent: a row
/// already there keeps its stamp, so a restart or a retried tick never
/// moves the start of a window.
pub async fn record_seen(pool: &SqlitePool, now: i64) -> Result<u64, sqlx::Error> {
    ensure_table(pool).await?;
    sqlx::query(
        "INSERT OR IGNORE INTO barattolo_payment_windows (order_id, seen_active_at)
         SELECT id, ?1 FROM orders
         WHERE status = 'active' AND invoice_held_at != 0 AND hash IS NOT NULL",
    )
    .bind(now)
    .execute(pool)
    .await
    .map(|r| r.rows_affected())
}

/// The trades whose window the server has not told yet, oldest first, as
/// the hyphenated ids the server knows them by. The id column is read with
/// the type the daemon wrote it with (`Uuid`), whatever its encoding.
pub async fn unknown_windows(pool: &SqlitePool) -> Result<Vec<String>, sqlx::Error> {
    ensure_table(pool).await?;
    let rows = sqlx::query_as::<_, (uuid::Uuid,)>(
        "SELECT w.order_id FROM barattolo_payment_windows w
         JOIN orders o ON o.id = w.order_id
         WHERE w.seconds IS NULL AND o.status = 'active'
         ORDER BY w.seen_active_at LIMIT ?1",
    )
    .bind(MAX_PER_REQUEST as i64)
    .fetch_all(pool)
    .await?;
    Ok(rows.into_iter().map(|r| r.0.to_string()).collect())
}

/// Writes what the server said. A row already answered is never rewritten:
/// the window a buyer was shown does not change under his feet.
pub async fn store_windows(
    pool: &SqlitePool,
    windows: &HashMap<String, i64>,
    now: i64,
) -> Result<(), sqlx::Error> {
    ensure_table(pool).await?;
    for (order_id, seconds) in windows {
        // bound as a `Uuid`, like every query of the daemon on `orders.id`
        let Ok(id) = uuid::Uuid::parse_str(order_id) else {
            continue;
        };
        sqlx::query(
            "UPDATE barattolo_payment_windows SET seconds = ?2, asked_at = ?3
             WHERE order_id = ?1 AND seconds IS NULL",
        )
        .bind(id)
        .bind(*seconds)
        .bind(now)
        .execute(pool)
        .await?;
        if *seconds > 0 {
            info!(
                "barattolo_finestra: order {order_id}: the buyer has {} minutes to send the fiat",
                seconds / 60
            );
        }
    }
    Ok(())
}

/// The `active` trades whose window has ended at `now`.
pub async fn due_orders(pool: &SqlitePool, now: i64) -> Result<Vec<Order>, sqlx::Error> {
    ensure_table(pool).await?;
    sqlx::query_as::<_, Order>(
        "SELECT o.* FROM orders o
         JOIN barattolo_payment_windows w ON w.order_id = o.id
         WHERE o.status = 'active' AND o.hash IS NOT NULL
           AND w.seconds > 0 AND w.seen_active_at + w.seconds <= ?1",
    )
    .bind(now)
    .fetch_all(pool)
    .await
}

async fn ask_server(ids: &[String]) -> Result<HashMap<String, i64>, String> {
    let (url, secret) = endpoint().ok_or_else(|| "not configured".to_string())?;
    let response = crate::barattolo_fee::http()
        .post(&url)
        .bearer_auth(&secret)
        .timeout(LOOKUP_BUDGET)
        .json(&serde_json::json!({ "ordini": ids }))
        .send()
        .await
        .map_err(|e| format!("request failed: {e}"))?;
    if !response.status().is_success() {
        return Err(format!("HTTP {}", response.status()));
    }
    if response.content_length().unwrap_or(0) > MAX_ANSWER_BYTES as u64 {
        return Err("answer too large".to_string());
    }
    let mut response = response;
    let mut raw: Vec<u8> = Vec::new();
    while let Some(chunk) = response
        .chunk()
        .await
        .map_err(|e| format!("unreadable body: {e}"))?
    {
        if raw.len() + chunk.len() > MAX_ANSWER_BYTES {
            return Err("answer too large".to_string());
        }
        raw.extend_from_slice(&chunk);
    }
    parse_answer(&String::from_utf8_lossy(&raw), ids)
        .ok_or_else(|| "unreadable answer".to_string())
}

/// One refresh: stamp the trades newly active, ask the server the windows
/// still unknown, write the answer. Never errors: a failure is one log line
/// (on change only, the journal must stay readable) and the next tick
/// tries again.
pub async fn refresh(pool: &SqlitePool, now: i64) {
    static WAS_OK: AtomicBool = AtomicBool::new(true);
    if let Err(e) = record_seen(pool, now).await {
        warn!("barattolo_finestra: could not stamp the active trades ({e})");
        return;
    }
    let ids = match unknown_windows(pool).await {
        Ok(ids) if !ids.is_empty() => ids,
        Ok(_) => return,
        Err(e) => {
            warn!("barattolo_finestra: could not read the side table ({e})");
            return;
        }
    };
    let answer = match tokio::time::timeout(LOOKUP_BUDGET, ask_server(&ids)).await {
        Ok(Ok(windows)) => Some(windows),
        Ok(Err(reason)) => {
            if WAS_OK.swap(false, Ordering::Relaxed) {
                warn!("barattolo_finestra: windows NOT known ({reason}): those trades have no time to pay until the server answers");
            }
            None
        }
        Err(_) => {
            if WAS_OK.swap(false, Ordering::Relaxed) {
                warn!("barattolo_finestra: windows NOT known (no answer in {}s)", LOOKUP_BUDGET.as_secs());
            }
            None
        }
    };
    if let Some(windows) = answer {
        if !WAS_OK.swap(true, Ordering::Relaxed) {
            info!("barattolo_finestra: marketplace server answering again");
        }
        if let Err(e) = store_windows(pool, &windows, now).await {
            warn!("barattolo_finestra: could not write the windows ({e}): asking again next tick");
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use sqlx::sqlite::SqlitePoolOptions;

    async fn pool() -> SqlitePool {
        // one connection: every connection to `sqlite::memory:` is its own db
        let pool = SqlitePoolOptions::new()
            .max_connections(1)
            .connect("sqlite::memory:")
            .await
            .unwrap();
        sqlx::migrate!().run(&pool).await.unwrap();
        pool
    }

    #[test]
    fn only_whole_minutes_inside_the_range_count() {
        assert_eq!(window_from(&json!(900)), 900);
        assert_eq!(window_from(&json!(2700)), 2700);
        assert_eq!(window_from(&json!(3600)), 3600);
        assert_eq!(window_from(&json!(14400)), 14400);
        assert_eq!(window_from(&json!(86400)), 86400);
        // a lying or confused server cannot invent a window
        assert_eq!(window_from(&json!(60)), 0);
        assert_eq!(window_from(&json!(840)), 0);
        assert_eq!(window_from(&json!(86460)), 0);
        assert_eq!(window_from(&json!(3601)), 0);
        assert_eq!(window_from(&json!(0)), 0);
        assert_eq!(window_from(&json!(-3600)), 0);
        assert_eq!(window_from(&json!("3600")), 0);
        assert_eq!(window_from(&json!(3600.5)), 0);
        assert_eq!(window_from(&json!(null)), 0);
    }

    #[test]
    fn every_id_asked_gets_an_answer_and_a_bad_body_none() {
        let asked = vec!["a".to_string(), "b".to_string(), "c".to_string()];
        let got = parse_answer(r#"{"finestre": {"a": 3600, "c": 7}}"#, &asked).unwrap();
        // "c": 7 seconds is below the range
        assert_eq!(got["a"], 3600);
        assert_eq!(got["b"], 0, "missing from the answer = no window, not asked again");
        assert_eq!(got["c"], 0, "outside the range = no window");
        assert_eq!(got.len(), 3);
        // ids the daemon did not ask are ignored
        let got = parse_answer(r#"{"finestre": {"zzz": 3600}}"#, &asked).unwrap();
        assert!(!got.contains_key("zzz"));
        // unreadable: nothing is written, the next tick asks again
        assert!(parse_answer("not json", &asked).is_none());
        assert!(parse_answer(r#"{"sconti": {}}"#, &asked).is_none());
        assert!(parse_answer(r#"{"finestre": [1]}"#, &asked).is_none());
    }

    #[test]
    fn the_window_ends_at_its_second_and_never_without_one() {
        assert!(!window_over(1000, 3600, 4599));
        assert!(window_over(1000, 3600, 4600));
        assert!(!window_over(1000, 0, 999_999));
        assert!(!window_over(0, 3600, 999_999));
    }

    #[test]
    fn inert_without_both_variables() {
        assert!(endpoint_from(None, Some("s")).is_none());
        assert!(endpoint_from(Some("https://x"), None).is_none());
        assert!(endpoint_from(Some(" "), Some("s")).is_none());
        assert!(endpoint_from(Some("https://x"), Some("")).is_none());
        assert!(endpoint_from(Some("https://x"), Some("s")).is_some());
        assert!(info_pairs_when(false).is_empty());
        assert_eq!(
            info_pairs_when(true),
            vec![("barattolo_payment_windows", "900-86400".to_string())]
        );
    }

    async fn insert(pool: &SqlitePool, status: &str, held_at: i64) -> String {
        use mostro_core::db::Crud;
        let order = Order {
            id: uuid::Uuid::new_v4(),
            kind: "sell".to_string(),
            status: status.to_string(),
            creator_pubkey: "c".repeat(64),
            fiat_code: "EUR".to_string(),
            payment_method: "SEPA".to_string(),
            hash: Some("ab".repeat(32)),
            invoice_held_at: held_at,
            ..Default::default()
        }
        .create(pool)
        .await
        .unwrap();
        order.id.to_string()
    }

    #[tokio::test]
    async fn the_start_is_stamped_once_and_only_for_active_trades() {
        let pool = pool().await;
        let active = insert(&pool, "active", 500).await;
        let sent = insert(&pool, "fiat-sent", 500).await;
        let not_held = insert(&pool, "active", 0).await;
        assert_eq!(record_seen(&pool, 1000).await.unwrap(), 1);
        // a later tick does not move the start
        assert_eq!(record_seen(&pool, 2000).await.unwrap(), 0);
        let ids = unknown_windows(&pool).await.unwrap();
        assert_eq!(ids, vec![active.clone()]);
        assert!(!ids.contains(&sent) && !ids.contains(&not_held));

        let mut answer = HashMap::new();
        answer.insert(active.clone(), 3600);
        store_windows(&pool, &answer, 1000).await.unwrap();
        assert!(unknown_windows(&pool).await.unwrap().is_empty());
        // an answered row is never rewritten
        answer.insert(active.clone(), 86400);
        store_windows(&pool, &answer, 1100).await.unwrap();
        assert!(due_orders(&pool, 4599).await.unwrap().is_empty());
        let due = due_orders(&pool, 4600).await.unwrap();
        assert_eq!(due.len(), 1);
        assert_eq!(due[0].id.to_string(), active);
    }

    #[tokio::test]
    async fn no_window_and_other_states_are_never_due() {
        let pool = pool().await;
        let none = insert(&pool, "active", 500).await;
        record_seen(&pool, 1000).await.unwrap();
        let mut answer = HashMap::new();
        answer.insert(none.clone(), 0);
        store_windows(&pool, &answer, 1000).await.unwrap();
        assert!(due_orders(&pool, 10_000_000).await.unwrap().is_empty());

        // a trade whose buyer said the fiat moved is never touched
        let sent = insert(&pool, "active", 500).await;
        record_seen(&pool, 1000).await.unwrap();
        let mut answer = HashMap::new();
        answer.insert(sent.clone(), 3600);
        store_windows(&pool, &answer, 1000).await.unwrap();
        let sent_id = uuid::Uuid::parse_str(&sent).unwrap();
        sqlx::query("UPDATE orders SET status = 'fiat-sent' WHERE id = ?1")
            .bind(sent_id)
            .execute(&pool)
            .await
            .unwrap();
        assert!(due_orders(&pool, 10_000_000).await.unwrap().is_empty());
        sqlx::query("UPDATE orders SET status = 'dispute' WHERE id = ?1")
            .bind(sent_id)
            .execute(&pool)
            .await
            .unwrap();
        assert!(due_orders(&pool, 10_000_000).await.unwrap().is_empty());
    }
}
