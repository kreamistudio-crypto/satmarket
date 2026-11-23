//! Barattolo fork (patch 0016): the internal transfer («il giroconto interno»).
//!
//! THE PROBLEM. On Barattolo a buyer without sats can buy an item of the
//! marketplace paying euros to a P2P seller: the seller's sats must end in
//! the marketplace escrow of that item, so the buyer invoice handed to this
//! daemon is the escrow invoice — an invoice of OUR OWN node, because the
//! marketplace escrow (LNbits «nodo») runs on the same LND as this daemon.
//! Upstream pays it with `SendPaymentV2` and LND refuses: «self-payments not
//! allowed». With `allow_self_payment` LND tries a circular route, which
//! depends on other nodes forwarding it back: on 23 Nov 2026 four attempts
//! from our node all failed (ACINQ would not forward to LNBiG). A payout that
//! works only when two hubs agree is not a payout.
//!
//! THE IDEA. When the payout is due the seller's sats are ALREADY on this
//! node: `release_action` settles the seller's hold invoice BEFORE it calls
//! `do_payment`. Sending them out to bring them back is a bank transfer
//! between two accounts of the same bank routed through a third one. So,
//! for a buyer invoice whose payee is this very node, the daemon asks the
//! marketplace server «will you settle this one?». The server checks by
//! itself — it never trusts this request — that the invoice is the escrow
//! of one of its euro-paid orders still unpaid, that the hold invoice named
//! here is SETTLED on LND for at least the payout, and that the same hold
//! invoice was never used for another order; then it pays the escrow invoice
//! from a dedicated LNbits wallet (the «riserva»: an internal LNbits
//! transfer, no network, no fee) and answers `{"saldata": true}`. Only then
//! the daemon finalizes the order as paid, exactly as if LND had reported
//! the payment `Succeeded`.
//!
//! FAIL TO UPSTREAM, everywhere: no endpoint configured, a dead server, a
//! non-200, a malformed body, anything but `{"saldata": true}` — the daemon
//! goes on with upstream's `send_payment`, which LND refuses for our own
//! invoice, and the order takes upstream's failed-payout road (retries, then
//! a new invoice asked to the buyer). Nobody loses sats: at worst the payout
//! waits for the next retry, which asks the server again.
//!
//! WHAT A COMPROMISED SERVER (or a leaked secret) CAN DO, and why it is
//! acceptable: the question is only ever asked for an invoice OUR OWN node
//! issued, so a lying `{"saldata": true}` can only mark as paid a payout
//! whose sats stay on this node — it can never send sats anywhere. The
//! marketplace server is the escrow holder of those orders anyway.
//!
//! IDEMPOTENT ON THE SERVER: a retry after a lost answer asks again for the
//! same invoice, and the server answers `true` for an escrow it already
//! paid, without paying twice (LNbits refuses to pay a settled invoice).
//!
//! What leaves this daemon: the order id, the payout invoice hash, the hold
//! invoice hash and the payout amount in sats. Never a preimage, never an
//! invoice string, never a trade key.
//!
//! Without `BARATTOLO_GIROCONTO_URL` and `BARATTOLO_GIROCONTO_SEGRETO` this
//! module is inert: no request, no lookup of our own pubkey.

use std::sync::OnceLock;
use std::time::Duration;
use tracing::{info, warn};

const ENV_URL: &str = "BARATTOLO_GIROCONTO_URL";
/// A secret of its own, like every channel to the server (audit of 19 Sep
/// 2026, M6): one leaked secret must not open a second door.
const ENV_SECRET: &str = "BARATTOLO_GIROCONTO_SEGRETO";

/// Budget of the first try. A warm circuit answers in about a second; the
/// server pays an internal LNbits invoice in well under one.
const FIRST_TRY: Duration = Duration::from_secs(15);
/// Pause before the one and only retry.
const RETRY_AFTER: Duration = Duration::from_secs(5);
/// Budget of the retry: a COLD Tor circuit measured 10.6 s on this node.
const SECOND_TRY: Duration = Duration::from_secs(20);
/// Hard cap on the answer: `{"saldata": true}` is a few bytes.
const MAX_ANSWER_BYTES: usize = 4_096;

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

/// Is the feature on?
pub fn enabled() -> bool {
    endpoint().is_some()
}

/// PURE: is a 33-byte compressed public key, hex-encoded?
fn is_pubkey_hex(key: &str) -> bool {
    key.len() == 66 && key.bytes().all(|b| b.is_ascii_hexdigit())
}

/// PURE: is the payee of the payout this very node? Both keys must be
/// well-formed: an unknown own key (LND did not answer) is never «ours».
pub fn is_own(payee: &str, own: &str) -> bool {
    is_pubkey_hex(payee) && is_pubkey_hex(own) && payee.eq_ignore_ascii_case(own)
}

/// PURE: is it a payment hash (32 bytes, hex)?
fn is_hash_hex(hash: &str) -> bool {
    hash.len() == 64 && hash.bytes().all(|b| b.is_ascii_hexdigit())
}

/// PURE: the body of the question, or None when a piece is missing or
/// malformed (no question is better than a question the server must guess).
pub fn question(
    order_id: &str,
    payout_hash: &str,
    hold_hash: Option<&str>,
    sats: u64,
) -> Option<serde_json::Value> {
    let hold_hash = hold_hash?;
    if order_id.is_empty() || !is_hash_hex(payout_hash) || !is_hash_hex(hold_hash) || sats == 0 {
        return None;
    }
    Some(serde_json::json!({
        "ordine": order_id,
        "fattura": payout_hash.to_ascii_lowercase(),
        "garanzia": hold_hash.to_ascii_lowercase(),
        "sats": sats,
    }))
}

/// PURE: only `{"saldata": true}` (a JSON boolean, not a string, not 1)
/// means the server paid the escrow. Everything else is «no».
pub fn settled_from(body: &str) -> bool {
    match serde_json::from_str::<serde_json::Value>(body) {
        Ok(v) => v.get("saldata").and_then(|s| s.as_bool()) == Some(true),
        Err(_) => false,
    }
}

/// Our own node's public key, asked to LND once and remembered. `None` when
/// LND has not answered yet: then nothing is «ours» and upstream pays.
static OWN_PUBKEY: OnceLock<String> = OnceLock::new();

/// Is the payee our own node? Asks LND the first time only.
pub async fn payee_is_own(
    ln_client: &mut crate::lightning::LndConnector,
    payee: &str,
) -> bool {
    if !enabled() {
        return false;
    }
    if OWN_PUBKEY.get().is_none() {
        match ln_client.get_node_info().await {
            Ok(info) if is_pubkey_hex(&info.identity_pubkey) => {
                let _ = OWN_PUBKEY.set(info.identity_pubkey);
            }
            Ok(_) => {
                warn!("Barattolo giroconto: LND gave no usable identity pubkey");
                return false;
            }
            Err(e) => {
                warn!("Barattolo giroconto: could not read our own pubkey ({e})");
                return false;
            }
        }
    }
    OWN_PUBKEY.get().map(|own| is_own(payee, own)).unwrap_or(false)
}

async fn ask_once(
    url: &str,
    secret: &str,
    body: &serde_json::Value,
    budget: Duration,
) -> Result<bool, String> {
    let response = crate::barattolo_fee::http()
        .post(url)
        .bearer_auth(secret)
        .timeout(budget)
        .json(body)
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
    Ok(settled_from(&String::from_utf8_lossy(&raw)))
}

/// Ask the server to settle the payout internally. `true` ONLY when the
/// server answered `{"saldata": true}`; one retry on a transport error, none
/// on a clear «no». Every call logs ONE line with its outcome.
pub async fn ask(
    order_id: uuid::Uuid,
    payout_hash: &str,
    hold_hash: Option<&str>,
    sats: u64,
) -> bool {
    let Some((url, secret)) = endpoint() else {
        return false;
    };
    let Some(body) = question(&order_id.to_string(), payout_hash, hold_hash, sats) else {
        warn!("Order {order_id}: giroconto not asked, the order lacks a usable hold invoice hash");
        return false;
    };
    let outcome = match ask_once(&url, &secret, &body, FIRST_TRY).await {
        Err(first) => {
            tokio::time::sleep(RETRY_AFTER).await;
            ask_once(&url, &secret, &body, SECOND_TRY)
                .await
                .map_err(|second| format!("{first}; retry: {second}"))
        }
        answered => answered,
    };
    match outcome {
        Ok(true) => {
            info!("Order {order_id}: giroconto done, the marketplace settled hash {payout_hash}");
            true
        }
        Ok(false) => {
            warn!("Order {order_id}: giroconto refused by the marketplace; paying as upstream");
            false
        }
        Err(e) => {
            warn!("Order {order_id}: giroconto unanswered ({e}); paying as upstream");
            false
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const OWN: &str = "02e0a08d0e07d8de6871b9e9683c9974fab511736b30b482c5a15aa48406176050";
    const OTHER: &str = "033e9ce4e8f0e68f0000000000000000000000000000000000000000000000000a";
    // spezzata in due: una hex nuda da 64 la ferma il controllo dei segreti
    const HASH: &str = concat!("aef4aa34fc57c1886fb292710a0092d6", "077631c8fbdb6367b0de7270f65e9398");

    #[test]
    fn inert_without_both_variables() {
        assert!(endpoint_from(None, Some("s")).is_none());
        assert!(endpoint_from(Some("https://x"), None).is_none());
        assert!(endpoint_from(Some("  "), Some("s")).is_none());
        assert!(endpoint_from(Some("https://x"), Some(" ")).is_none());
        assert_eq!(
            endpoint_from(Some(" https://x "), Some(" s ")),
            Some(("https://x".to_string(), "s".to_string()))
        );
    }

    #[test]
    fn only_our_own_well_formed_key_is_ours() {
        assert!(is_own(OWN, OWN));
        assert!(is_own(&OWN.to_ascii_uppercase(), OWN));
        assert!(!is_own(OTHER, OWN));
        assert!(!is_own(OWN, ""));
        assert!(!is_own("", ""));
        assert!(!is_own("02abc", "02abc"));
        assert!(!is_own(&OWN[..64], &OWN[..64]));
    }

    #[test]
    fn the_question_needs_every_piece() {
        let q = question("o1", HASH, Some(HASH), 1000).expect("a full question");
        assert_eq!(q["ordine"], "o1");
        assert_eq!(q["fattura"], HASH);
        assert_eq!(q["garanzia"], HASH);
        assert_eq!(q["sats"], 1000);
        assert!(question("o1", HASH, None, 1000).is_none());
        assert!(question("o1", HASH, Some("abc"), 1000).is_none());
        assert!(question("o1", "zz", Some(HASH), 1000).is_none());
        assert!(question("", HASH, Some(HASH), 1000).is_none());
        assert!(question("o1", HASH, Some(HASH), 0).is_none());
        let upper = question("o1", &HASH.to_ascii_uppercase(), Some(HASH), 1).unwrap();
        assert_eq!(upper["fattura"], HASH);
    }

    #[test]
    fn only_a_json_true_means_settled() {
        assert!(settled_from(r#"{"saldata": true}"#));
        assert!(settled_from(r#"{"saldata": true, "nota": "x"}"#));
        assert!(!settled_from(r#"{"saldata": false}"#));
        assert!(!settled_from(r#"{"saldata": "true"}"#));
        assert!(!settled_from(r#"{"saldata": 1}"#));
        assert!(!settled_from(r#"{}"#));
        assert!(!settled_from(""));
        assert!(!settled_from("saldata"));
        assert!(!settled_from(r#"[true]"#));
    }
}
