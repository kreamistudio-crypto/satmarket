//! Barattolo fork, patch 0007: order events to the marketplace server.
//!
//! The marketplace used to GUESS what happened in a trade from encrypted gift
//! wraps it cannot read, and told users "something new in your trade". This
//! daemon KNOWS what happened, so at every state transition it tells the
//! server: one small POST per transition, on the same road as the loyalty
//! discount of patch 0005 (same HTTP client, so the same warm Tor circuit;
//! bearer secret in the header).
//!
//! What leaves this daemon, and nothing else: the order id, the action, a
//! timestamp, the two TRADE pubkeys, who made the move (buyer / seller /
//! mostro), a short machine-readable detail for some actions, and — ONLY when
//! the trade closes (`released` / `success`) — three amounts in sats: the
//! order amount, what the buyer is paid and what the seller locked. Never an
//! invoice, a preimage, a payment hash, free text or payment coordinates.
//!
//! Fire and forget, which is the OPPOSITE of patch 0005's fail-closed: the
//! POST runs in its own task, with a short budget and at most one retry, and
//! nothing in the trade ever waits for it. If the server is down the trade
//! goes on exactly as upstream; the server has a fallback on the public order
//! book for the transitions that show there. Every POST logs ONE line with
//! its outcome.
//!
//! Without `BARATTOLO_EVENTI_URL` (and a secret) this module is inert: no
//! task, no request, no log line after the one at startup.

use mostro_core::prelude::*;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tracing::{info, warn};

const ENV_URL: &str = "BARATTOLO_EVENTI_URL";
/// A secret of its own, if set; otherwise the one of patch 0005.
const ENV_SECRET: &str = "BARATTOLO_EVENTI_SEGRETO";
const ENV_SECRET_FALLBACK: &str = "BARATTOLO_SCONTO_SEGRETO";

/// Budget of the first try. A warm circuit answers in about a second.
const FIRST_TRY: Duration = Duration::from_secs(8);
/// Pause before the one and only retry.
const RETRY_AFTER: Duration = Duration::from_secs(5);
/// Budget of the retry: a COLD Tor circuit measured 10.6 s on this node.
/// 8 + 5 + 12 stays well under the 60 s after which the server falls back
/// to the public book.
const SECOND_TRY: Duration = Duration::from_secs(12);
/// Keep-warm, only when patch 0005's own heartbeat is not running.
const HEARTBEAT_EVERY: Duration = Duration::from_secs(60);

/// Every action this daemon may send. The patcher checks each hook against
/// this list, and `event_of` drops anything else: a typo must be loud in the
/// log, never a new kind of event on the wire.
pub const ACTIONS: [&str; 12] = [
    "taken",
    "hold-invoice-requested",
    "hold-invoice-paid",
    "buyer-invoice-requested",
    "buyer-invoice-added",
    "fiat-sent",
    "released",
    "success",
    "cancel-requested",
    "canceled",
    "expired",
    "dispute-opened",
];
/// The thirteenth, with its own entry point because it carries a reason.
pub const PAYOUT_FAILED: &str = "payout-failed";

// THE DETAILS, a closed vocabulary of machine words. Several transitions are
// born in pairs in the same instant (a take AND the hold invoice request; the
// hold paid AND the payout invoice request): the detail says which branch ran,
// so the server sends ONE notice for the pair instead of guessing from the
// order in which two independent POSTs happen to land.
//   taken                   hold-next | invoice-next
//   hold-invoice-requested  take | invoice
//   hold-invoice-paid       active | invoice-next
//   buyer-invoice-added     active | hold-next | new-invoice
//   canceled                cooperative | republished | pending | admin
//   expired                 book | taker-timeout | maker-timeout | escrow-deadline
//   released                admin (a moderator settled a dispute)
//   payout-failed           LND's failure reason (NO_ROUTE, TIMEOUT, …) when the
//                           payment was sent; before the claim (upstream #908
//                           routes every pre-claim failure through one point)
//                           INVOICE_INVALID | INVOICE_EXPIRED | ADDRESS_UNRESOLVED |
//                           LND_UNREACHABLE | INVALID_PUBKEY | DB_ERROR | PRE_CLAIM

pub fn is_known_action(action: &str) -> bool {
    action == PAYOUT_FAILED || ACTIONS.contains(&action)
}

/// What goes on the wire. Built from an `Order` by [`event_of`], which is the
/// only place that reads one: the fields NOT copied here never leave.
#[derive(Debug, Clone, PartialEq)]
pub struct Event {
    pub order: String,
    pub action: String,
    pub ts: i64,
    pub buyer: Option<String>,
    pub seller: Option<String>,
    pub actor: String,
    pub detail: Option<String>,
    /// (order amount, paid to the buyer, locked by the seller)
    pub sats: Option<(i64, i64, i64)>,
}

fn is_hex_key(key: &str) -> bool {
    key.len() == 64 && key.bytes().all(|b| b.is_ascii_hexdigit())
}

fn clean_key(key: Option<&str>) -> Option<String> {
    match key {
        Some(k) if is_hex_key(k.trim()) => Some(k.trim().to_ascii_lowercase()),
        _ => None,
    }
}

/// A detail is a short machine word (`taker-timeout`, `NO_ROUTE`): anything
/// longer or stranger is cut, so free text can never ride along.
fn clean_detail(detail: Option<&str>) -> Option<String> {
    let cleaned: String = detail?
        .chars()
        .filter(|c| c.is_ascii_alphanumeric() || *c == '-' || *c == '_')
        .take(40)
        .collect();
    if cleaned.is_empty() {
        None
    } else {
        Some(cleaned)
    }
}

fn now_secs() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs() as i64)
        .unwrap_or(0)
}

/// Who made the move, from the sender's key. A sender that is neither party
/// (an admin, a bonded prospective taker) is reported as `mostro`: the server
/// then tells BOTH parties, which is the safe way to be wrong.
pub fn actor_of(buyer: Option<&str>, seller: Option<&str>, sender: &str) -> &'static str {
    if !sender.is_empty() && buyer == Some(sender) {
        "buyer"
    } else if !sender.is_empty() && seller == Some(sender) {
        "seller"
    } else {
        "mostro"
    }
}

/// Which side TOOK the order: the one that did not create it.
pub fn taker_side(creator: &str, buyer: Option<&str>, seller: Option<&str>) -> &'static str {
    match actor_of(buyer, seller, creator) {
        "buyer" => "seller",
        "seller" => "buyer",
        _ => "mostro",
    }
}

/// LND's `PaymentFailureReason`, by its wire code. Spelled out here so this
/// module does not depend on which prost version generated the enum.
pub fn failure_reason_name(code: i32) -> &'static str {
    match code {
        0 => "NONE",
        1 => "TIMEOUT",
        2 => "NO_ROUTE",
        3 => "ERROR",
        4 => "INCORRECT_PAYMENT_DETAILS",
        5 => "INSUFFICIENT_BALANCE",
        6 => "CANCELED",
        _ => "UNKNOWN",
    }
}

/// (order amount, paid to the buyer, locked by the seller). After patch 0005
/// `order.fee` is the BUYER's fee and the seller's comes from the side table.
pub fn closing_sats(amount: i64, fee_buyer: i64, fee_seller: i64) -> (i64, i64, i64) {
    (
        amount,
        amount.saturating_sub(fee_buyer.max(0)),
        amount.saturating_add(fee_seller.max(0)),
    )
}

/// The ONLY reader of an `Order` in this module. Returns `None` for an action
/// that is not in the list.
pub fn event_of(action: &str, order: &Order, actor: &str, detail: Option<&str>) -> Option<Event> {
    if !is_known_action(action) {
        return None;
    }
    let actor = match actor {
        "buyer" | "seller" => actor,
        _ => "mostro",
    };
    Some(Event {
        order: order.id.to_string(),
        action: action.to_string(),
        ts: now_secs(),
        buyer: clean_key(order.buyer_pubkey.as_deref()),
        seller: clean_key(order.seller_pubkey.as_deref()),
        actor: actor.to_string(),
        detail: clean_detail(detail),
        sats: None,
    })
}

/// The JSON body. Amounts are written ONLY for the two closing actions, even
/// if a caller filled them in for another one.
pub fn payload(event: &Event) -> serde_json::Value {
    let mut body = serde_json::json!({
        "v": 1,
        "order": event.order,
        "action": event.action,
        "ts": event.ts,
        "buyer": event.buyer,
        "seller": event.seller,
        "actor": event.actor,
    });
    if let Some(detail) = &event.detail {
        body["detail"] = serde_json::json!(detail);
    }
    let closing = event.action == "released" || event.action == "success";
    if let (true, Some((amount, to_buyer, from_seller))) = (closing, event.sats) {
        body["sats"] = serde_json::json!(amount);
        body["sats_buyer"] = serde_json::json!(to_buyer);
        body["sats_seller"] = serde_json::json!(from_seller);
    }
    body
}

/// Pure half of [`endpoint`]: the URL, and the first non-empty secret.
pub fn endpoint_from(
    url: Option<&str>,
    secret: Option<&str>,
    fallback: Option<&str>,
) -> Option<(String, String)> {
    let url = url?.trim();
    let secret = [secret, fallback]
        .into_iter()
        .flatten()
        .map(|s| s.trim())
        .find(|s| !s.is_empty())?;
    if url.is_empty() {
        return None;
    }
    Some((url.to_string(), secret.to_string()))
}

fn endpoint() -> Option<(String, String)> {
    endpoint_from(
        std::env::var(ENV_URL).ok().as_deref(),
        std::env::var(ENV_SECRET).ok().as_deref(),
        std::env::var(ENV_SECRET_FALLBACK).ok().as_deref(),
    )
}

struct Failure {
    retry: bool,
    reason: String,
}

async fn post_once(
    url: &str,
    secret: &str,
    body: &serde_json::Value,
    budget: Duration,
) -> Result<u16, Failure> {
    let response = crate::barattolo_fee::http()
        .post(url)
        .timeout(budget)
        .bearer_auth(secret)
        .json(body)
        .send()
        .await
        .map_err(|e| Failure {
            retry: true,
            reason: format!("request failed: {e}"),
        })?;
    let code = response.status().as_u16();
    if response.status().is_success() {
        Ok(code)
    } else {
        // a 4xx is OUR mistake (wrong secret, bad body): asking again with
        // the same request cannot help
        Err(Failure {
            retry: code >= 500,
            reason: format!("HTTP {code}"),
        })
    }
}

/// One POST and at most one retry. Returns whether the server took it.
/// Logs exactly one closing line, with the outcome.
pub async fn deliver_with(url: &str, secret: &str, event: &Event, retry_after: Duration) -> bool {
    let body = payload(event);
    let started = Instant::now();
    let first = match post_once(url, secret, &body, FIRST_TRY).await {
        Ok(code) => {
            info!(
                "barattolo_eventi: order {} {}: delivered (HTTP {code}, {} ms)",
                event.order,
                event.action,
                started.elapsed().as_millis()
            );
            return true;
        }
        Err(failure) => failure,
    };
    if !first.retry {
        warn!(
            "barattolo_eventi: order {} {}: NOT delivered ({}), no retry",
            event.order, event.action, first.reason
        );
        return false;
    }
    tokio::time::sleep(retry_after).await;
    match post_once(url, secret, &body, SECOND_TRY).await {
        Ok(code) => {
            info!(
                "barattolo_eventi: order {} {}: delivered at the retry (HTTP {code}, {} ms; first try: {})",
                event.order,
                event.action,
                started.elapsed().as_millis(),
                first.reason
            );
            true
        }
        Err(second) => {
            warn!(
                "barattolo_eventi: order {} {}: NOT delivered ({}; retry: {}), giving up",
                event.order, event.action, first.reason, second.reason
            );
            false
        }
    }
}

fn spawn_delivery(event: Event, with_closing_sats: Option<Order>) {
    let (url, secret) = match endpoint() {
        Some(pair) => pair,
        None => return,
    };
    let handle = match tokio::runtime::Handle::try_current() {
        Ok(handle) => handle,
        Err(_) => {
            warn!(
                "barattolo_eventi: order {} {}: no runtime here, event dropped",
                event.order, event.action
            );
            return;
        }
    };
    handle.spawn(async move {
        let mut event = event;
        if let Some(order) = with_closing_sats {
            let fee_seller = crate::barattolo_fee::seller_fee(&order).await;
            event.sats = Some(closing_sats(order.amount, order.fee, fee_seller));
        }
        deliver_with(&url, &secret, &event, RETRY_AFTER).await;
    });
}

/// Tells the server about a transition. Never blocks, never fails: it
/// returns at once and the POST lives in its own task.
pub fn emit(action: &str, order: &Order, actor: &str) {
    emit_detail(action, order, actor, "");
}

/// [`emit`] with a short machine-readable detail (`taker-timeout`, `book`…).
pub fn emit_detail(action: &str, order: &Order, actor: &str, detail: &str) {
    if endpoint().is_none() {
        return;
    }
    let detail = if detail.is_empty() { None } else { Some(detail) };
    match event_of(action, order, actor, detail) {
        Some(event) => {
            let closing = action == "released" || action == "success";
            spawn_delivery(event, if closing { Some(order.clone()) } else { None });
        }
        None => warn!(
            "barattolo_eventi: order {}: unknown action {action:?}, nothing sent",
            order.id
        ),
    }
}

/// [`emit`] when what is known is the SENDER's key, not the side.
pub fn emit_by(action: &str, order: &Order, sender: &str) {
    emit_by_detail(action, order, sender, "");
}

pub fn emit_by_detail(action: &str, order: &Order, sender: &str, detail: &str) {
    let actor = actor_of(
        order.buyer_pubkey.as_deref(),
        order.seller_pubkey.as_deref(),
        sender,
    );
    emit_detail(action, order, actor, detail);
}

/// The order was taken: the actor is whoever did NOT create it. `next` says
/// which step the take opened (`hold-next`: the seller pays the hold invoice
/// now; `invoice-next`: the buyer gives the payout invoice first), so the
/// server can tell the maker what comes next in ONE notice.
pub fn emit_taken(order: &Order, next: &str) {
    let taker = taker_side(
        &order.creator_pubkey,
        order.buyer_pubkey.as_deref(),
        order.seller_pubkey.as_deref(),
    );
    emit_detail("taken", order, taker, next);
}

/// The payout to the buyer failed; `reason_code` is LND's
/// `payment.failure_reason`, the same number patch 0006 logs.
pub fn emit_payout_failed(order: &Order, reason_code: i32) {
    emit_detail(
        PAYOUT_FAILED,
        order,
        "mostro",
        failure_reason_name(reason_code),
    );
}

/// A payout that failed BEFORE anything reached LND: the destination did not
/// resolve, the invoice did not decode or was expired, LND itself was
/// unreachable. Upstream (#908, 0.18.8) funnels every such exit through the
/// `Err` branch of `do_payment`, so one hook there covers them all; the word
/// names the class, never the error text.
pub fn pre_claim_failure_name(e: &MostroError) -> &'static str {
    match e {
        MostroInternalErr(ServiceError::InvoiceInvalidError)
        | MostroInternalErr(ServiceError::ParsingInvoiceError) => "INVOICE_INVALID",
        MostroInternalErr(ServiceError::InvoiceExpiredError) => "INVOICE_EXPIRED",
        MostroInternalErr(ServiceError::LnAddressParseError)
        | MostroInternalErr(ServiceError::LnAddressWrongAmount) => "ADDRESS_UNRESOLVED",
        MostroInternalErr(ServiceError::LnNodeError(_)) => "LND_UNREACHABLE",
        MostroInternalErr(ServiceError::InvalidPubkey) => "INVALID_PUBKEY",
        MostroInternalErr(ServiceError::DbAccessError(_)) => "DB_ERROR",
        _ => "PRE_CLAIM",
    }
}

/// [`emit_payout_failed`] for the pre-claim exits of `do_payment`.
pub fn emit_payout_failed_pre_claim(order: &Order, e: &MostroError) {
    emit_detail(PAYOUT_FAILED, order, "mostro", pre_claim_failure_name(e));
}

fn fee_heartbeat_runs() -> bool {
    let set = |key: &str| {
        std::env::var(key)
            .map(|v| !v.trim().is_empty())
            .unwrap_or(false)
    };
    set("BARATTOLO_SCONTO_URL")
        && set("BARATTOLO_SCONTO_SEGRETO")
        && crate::barattolo_fee::parse_discount(
            std::env::var("BARATTOLO_SCONTO_FEE").ok().as_deref(),
        ) > 0.0
}

async fn heartbeat(url: reqwest::Url) {
    loop {
        let _ = crate::barattolo_fee::http().get(url.clone()).send().await;
        tokio::time::sleep(HEARTBEAT_EVERY).await;
    }
}

/// Says in the log whether the feature is on. The keep-warm loop of patch
/// 0005 already serves this module too (same client, same host); a loop of
/// its own starts only when that one is not running.
pub async fn init() {
    match endpoint() {
        Some((url, _)) => {
            info!("barattolo_eventi: order events go to {url}");
            if fee_heartbeat_runs() {
                return;
            }
            match reqwest::Url::parse(&url).and_then(|u| u.join("/api/salute")) {
                Ok(beat) => {
                    tokio::spawn(heartbeat(beat));
                }
                Err(e) => warn!("barattolo_eventi: no keep-warm, bad URL ({e})"),
            }
        }
        None => info!("barattolo_eventi: not configured, no event leaves this daemon"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::{Arc, Mutex};
    use tokio::io::{AsyncReadExt, AsyncWriteExt};

    // Trade keys made at run time: a 64-hex literal in the repo trips the
    // secret scanner, and rightly so.
    fn key(c: char) -> String {
        std::iter::repeat(c).take(64).collect()
    }

    fn order() -> Order {
        Order {
            creator_pubkey: key('a'),
            buyer_pubkey: Some(key('a')),
            seller_pubkey: Some(key('b')),
            amount: 15_000,
            fee: 225,
            ..Default::default()
        }
    }

    #[test]
    fn without_a_url_or_a_secret_it_is_inert() {
        assert_eq!(endpoint_from(None, Some("s"), Some("f")), None);
        assert_eq!(endpoint_from(Some(""), Some("s"), None), None);
        assert_eq!(endpoint_from(Some("  "), Some("s"), None), None);
        assert_eq!(endpoint_from(Some("http://x"), None, None), None);
        assert_eq!(endpoint_from(Some("http://x"), Some(" "), Some("")), None);
    }

    #[test]
    fn its_own_secret_wins_and_the_0005_one_is_the_fallback() {
        let both = endpoint_from(Some(" http://x "), Some("own"), Some("fee"));
        assert_eq!(both, Some(("http://x".to_string(), "own".to_string())));
        let fallback = endpoint_from(Some("http://x"), None, Some(" fee "));
        assert_eq!(fallback, Some(("http://x".to_string(), "fee".to_string())));
        let empty_own = endpoint_from(Some("http://x"), Some(""), Some("fee"));
        assert_eq!(empty_own, Some(("http://x".to_string(), "fee".to_string())));
    }

    #[test]
    fn who_made_the_move() {
        let (a, b, c) = (key('a'), key('b'), key('c'));
        let (buyer, seller) = (Some(a.as_str()), Some(b.as_str()));
        assert_eq!(actor_of(buyer, seller, &a), "buyer");
        assert_eq!(actor_of(buyer, seller, &b), "seller");
        // neither party: both get told
        assert_eq!(actor_of(buyer, seller, &c), "mostro");
        assert_eq!(actor_of(None, None, ""), "mostro");
        assert_eq!(actor_of(None, seller, &b), "seller");
    }

    #[test]
    fn the_taker_is_whoever_did_not_publish() {
        let (a, b) = (key('a'), key('b'));
        let (buyer, seller) = (Some(a.as_str()), Some(b.as_str()));
        assert_eq!(taker_side(&a, buyer, seller), "seller");
        assert_eq!(taker_side(&b, buyer, seller), "buyer");
        assert_eq!(taker_side(&key('c'), buyer, seller), "mostro");
    }

    #[test]
    fn only_listed_actions_become_events() {
        let o = order();
        for action in ACTIONS {
            assert!(event_of(action, &o, "buyer", None).is_some(), "{action}");
        }
        assert!(event_of(PAYOUT_FAILED, &o, "mostro", Some("NO_ROUTE")).is_some());
        assert!(event_of("takne", &o, "buyer", None).is_none());
        assert!(event_of("", &o, "buyer", None).is_none());
    }

    #[test]
    fn an_unknown_actor_is_mostro() {
        let o = order();
        assert_eq!(event_of("taken", &o, "admin", None).unwrap().actor, "mostro");
        assert_eq!(event_of("taken", &o, "seller", None).unwrap().actor, "seller");
    }

    #[test]
    fn the_body_has_these_fields_and_no_other() {
        let o = order();
        let event = event_of("taken", &o, "seller", None).unwrap();
        let body = payload(&event);
        let mut names: Vec<&str> = body.as_object().unwrap().keys().map(|k| k.as_str()).collect();
        names.sort();
        assert_eq!(names, ["action", "actor", "buyer", "order", "seller", "ts", "v"]);
        assert_eq!(body["order"], o.id.to_string());
        assert_eq!(body["buyer"], key('a'));
        assert_eq!(body["seller"], key('b'));
        assert_eq!(body["actor"], "seller");
        assert!(body["ts"].as_i64().unwrap() > 1_700_000_000);
    }

    #[test]
    fn amounts_travel_only_when_the_trade_closes() {
        let o = order();
        for action in ACTIONS {
            let mut event = event_of(action, &o, "seller", None).unwrap();
            // even if a caller fills them in for the wrong action
            event.sats = Some(closing_sats(15_000, 225, 225));
            let body = payload(&event);
            let closing = action == "released" || action == "success";
            assert_eq!(body.get("sats").is_some(), closing, "{action}");
            assert_eq!(body.get("sats_buyer").is_some(), closing, "{action}");
            assert_eq!(body.get("sats_seller").is_some(), closing, "{action}");
        }
        let mut event = event_of("success", &o, "mostro", None).unwrap();
        event.sats = Some(closing_sats(15_000, 225, 150));
        let body = payload(&event);
        assert_eq!(body["sats"], 15_000);
        assert_eq!(body["sats_buyer"], 14_775);
        assert_eq!(body["sats_seller"], 15_150);
    }

    #[test]
    fn closing_sats_never_go_the_wrong_way() {
        assert_eq!(closing_sats(15_000, 225, 225), (15_000, 14_775, 15_225));
        // one side discounted (patch 0005): the two fees differ
        assert_eq!(closing_sats(100_000, 1_000, 1_500), (100_000, 99_000, 101_500));
        // a negative fee is a bug elsewhere: it must not PAY anybody
        assert_eq!(closing_sats(1_000, -50, -50), (1_000, 1_000, 1_000));
    }

    #[test]
    fn invoices_preimages_and_hashes_never_leave() {
        let o = Order {
            buyer_invoice: Some("lnbc1SECRETINVOICE".to_string()),
            preimage: Some("PREIMAGESECRET".to_string()),
            hash: Some("HASHSECRET".to_string()),
            payment_method: "IBAN-IT60X".to_string(),
            master_buyer_pubkey: Some("MASTERBUYER".to_string()),
            master_seller_pubkey: Some("MASTERSELLER".to_string()),
            ..order()
        };
        for action in ACTIONS {
            let mut event = event_of(action, &o, "buyer", Some("book")).unwrap();
            event.sats = Some(closing_sats(o.amount, o.fee, o.fee));
            let text = payload(&event).to_string();
            for secret in [
                "SECRETINVOICE",
                "PREIMAGESECRET",
                "HASHSECRET",
                "IBAN",
                "MASTERBUYER",
                "MASTERSELLER",
            ] {
                assert!(!text.contains(secret), "{action} leaks {secret}");
            }
        }
    }

    #[test]
    fn a_key_that_is_not_64_hex_is_sent_as_null() {
        let o = Order {
            buyer_pubkey: Some("npub1notahexkey".to_string()),
            seller_pubkey: None,
            ..order()
        };
        let body = payload(&event_of("canceled", &o, "buyer", None).unwrap());
        assert!(body["buyer"].is_null());
        assert!(body["seller"].is_null());
        let upper = Order {
            buyer_pubkey: Some(key('A')),
            ..order()
        };
        let body = payload(&event_of("canceled", &upper, "buyer", None).unwrap());
        assert_eq!(body["buyer"], key('a'));
    }

    #[test]
    fn a_detail_is_a_short_machine_word() {
        let o = order();
        let of = |d: &str| event_of("expired", &o, "mostro", Some(d)).unwrap().detail;
        assert_eq!(of("taker-timeout"), Some("taker-timeout".to_string()));
        assert_eq!(of("NO_ROUTE"), Some("NO_ROUTE".to_string()));
        // free text cannot ride along: spaces and symbols go, and it is cut
        assert_eq!(of("IBAN: IT60 X054"), Some("IBANIT60X054".to_string()));
        assert_eq!(of(&"x".repeat(200)).unwrap().len(), 40);
        assert_eq!(of("  "), None);
        assert_eq!(event_of("expired", &o, "mostro", None).unwrap().detail, None);
    }

    #[test]
    fn lnd_failure_reasons_by_code() {
        assert_eq!(failure_reason_name(2), "NO_ROUTE");
        assert_eq!(failure_reason_name(1), "TIMEOUT");
        assert_eq!(failure_reason_name(5), "INSUFFICIENT_BALANCE");
        assert_eq!(failure_reason_name(4), "INCORRECT_PAYMENT_DETAILS");
        assert_eq!(failure_reason_name(99), "UNKNOWN");
        assert_eq!(failure_reason_name(-1), "UNKNOWN");
    }

    #[test]
    fn pre_claim_failures_by_class() {
        let of = pre_claim_failure_name;
        assert_eq!(
            of(&MostroInternalErr(ServiceError::InvoiceInvalidError)),
            "INVOICE_INVALID"
        );
        assert_eq!(
            of(&MostroInternalErr(ServiceError::InvoiceExpiredError)),
            "INVOICE_EXPIRED"
        );
        assert_eq!(
            of(&MostroInternalErr(ServiceError::LnAddressParseError)),
            "ADDRESS_UNRESOLVED"
        );
        assert_eq!(
            of(&MostroInternalErr(ServiceError::LnNodeError("down".into()))),
            "LND_UNREACHABLE"
        );
        assert_eq!(
            of(&MostroInternalErr(ServiceError::InvalidPubkey)),
            "INVALID_PUBKEY"
        );
        assert_eq!(
            of(&MostroInternalErr(ServiceError::DbAccessError("x".into()))),
            "DB_ERROR"
        );
        assert_eq!(
            of(&MostroCantDo(CantDoReason::InvalidAmount)),
            "PRE_CLAIM"
        );
        // the word goes through the same cleaner as every detail
        let o = order();
        assert_eq!(
            event_of(PAYOUT_FAILED, &o, "mostro", Some("LND_UNREACHABLE"))
                .unwrap()
                .detail
                .as_deref(),
            Some("LND_UNREACHABLE")
        );
    }

    // ── the wire ─────────────────────────────────────────────────────────
    // A tiny HTTP/1.1 server: answers each connection with the next status
    // code of the list and keeps what it was sent.

    async fn read_request(socket: &mut tokio::net::TcpStream) -> String {
        let mut buf: Vec<u8> = Vec::new();
        let mut chunk = [0u8; 4096];
        loop {
            let n = match socket.read(&mut chunk).await {
                Ok(0) | Err(_) => break,
                Ok(n) => n,
            };
            buf.extend_from_slice(&chunk[..n]);
            let text = String::from_utf8_lossy(&buf).to_string();
            if let Some(head_end) = text.find("\r\n\r\n") {
                let wanted = text[..head_end]
                    .lines()
                    .find_map(|line| {
                        let line = line.to_ascii_lowercase();
                        line.strip_prefix("content-length:")
                            .map(|v| v.trim().parse::<usize>().unwrap_or(0))
                    })
                    .unwrap_or(0);
                if buf.len() >= head_end + 4 + wanted {
                    break;
                }
            }
        }
        String::from_utf8_lossy(&buf).to_string()
    }

    async fn fake_server(replies: Vec<u16>) -> (String, Arc<Mutex<Vec<String>>>) {
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let url = format!("http://{}/api/p2p/evento", listener.local_addr().unwrap());
        let seen = Arc::new(Mutex::new(Vec::new()));
        let seen_by_server = seen.clone();
        tokio::spawn(async move {
            for code in replies {
                let (mut socket, _) = match listener.accept().await {
                    Ok(pair) => pair,
                    Err(_) => return,
                };
                let request = read_request(&mut socket).await;
                seen_by_server.lock().unwrap().push(request);
                let reply =
                    format!("HTTP/1.1 {code} X\r\ncontent-length: 0\r\nconnection: close\r\n\r\n");
                let _ = socket.write_all(reply.as_bytes()).await;
                let _ = socket.shutdown().await;
            }
        });
        (url, seen)
    }

    const SOON: Duration = Duration::from_millis(20);

    #[tokio::test]
    async fn one_post_with_the_secret_in_the_header() {
        let (url, seen) = fake_server(vec![200]).await;
        let event = event_of("fiat-sent", &order(), "buyer", None).unwrap();
        assert!(deliver_with(&url, "s3gr3to", &event, SOON).await);
        let seen = seen.lock().unwrap();
        assert_eq!(seen.len(), 1);
        let request = seen[0].to_ascii_lowercase();
        assert!(request.starts_with("post /api/p2p/evento "), "{request}");
        assert!(request.contains("authorization: bearer s3gr3to"), "{request}");
        assert!(request.contains("\"action\":\"fiat-sent\""), "{request}");
        assert!(request.contains("\"actor\":\"buyer\""), "{request}");
    }

    #[tokio::test]
    async fn a_server_error_gets_one_retry() {
        let (url, seen) = fake_server(vec![503, 200]).await;
        let event = event_of("taken", &order(), "seller", None).unwrap();
        assert!(deliver_with(&url, "s", &event, SOON).await);
        assert_eq!(seen.lock().unwrap().len(), 2);
    }

    #[tokio::test]
    async fn and_never_a_second_one() {
        let (url, seen) = fake_server(vec![503, 503, 200]).await;
        let event = event_of("taken", &order(), "seller", None).unwrap();
        assert!(!deliver_with(&url, "s", &event, SOON).await);
        assert_eq!(seen.lock().unwrap().len(), 2);
    }

    #[tokio::test]
    async fn a_refusal_is_not_retried() {
        let (url, seen) = fake_server(vec![401, 200]).await;
        let event = event_of("taken", &order(), "seller", None).unwrap();
        assert!(!deliver_with(&url, "wrong", &event, SOON).await);
        assert_eq!(seen.lock().unwrap().len(), 1);
    }

    #[tokio::test]
    async fn a_dead_server_is_a_false_not_a_hang() {
        // bind, learn the port, close: nobody listens there any more
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let url = format!("http://{}/api/p2p/evento", listener.local_addr().unwrap());
        drop(listener);
        let event = event_of("taken", &order(), "seller", None).unwrap();
        let started = Instant::now();
        assert!(!deliver_with(&url, "s", &event, SOON).await);
        assert!(started.elapsed() < Duration::from_secs(25));
    }
}
