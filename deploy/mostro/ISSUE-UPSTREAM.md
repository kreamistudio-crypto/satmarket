# LNURL resolution is unreachable on a Tor-routed coordinator (dev fee stuck forever, trader Lightning addresses rejected)

**Version:** v0.18.7 (`afc39a2`)
**Setup:** coordinator with all egress through a Tor transparent proxy
(`TransPort` + `DNSPort` via iptables REDIRECT). No clearnet exit.

## Summary

Every LNURL call made by the coordinator goes through `lnurl_get` in
`src/lnurl.rs`, bounded by three `const` budgets that cannot be configured:

```rust
LNURL_REQUEST_TIMEOUT = 4s
LNURL_CONNECT_TIMEOUT = 2s
LNURL_DNS_TIMEOUT     = 2s
```

A **cold Tor circuit takes ~10.6 s** to complete one HTTPS request. Every
LNURL resolution over a fresh circuit therefore fails before it can ever
succeed. This is not a slow network: on a warm circuit the same request
takes under one second.

On top of that, the dev-fee path wraps that call in **two further nested
timeouts** (15 s and 20 s, in `src/app/dev_fee.rs`) that are unreachable on a
cold circuit *regardless* of the LNURL budgets — because a single dev-fee
resolution needs **two** HTTPS round-trips on **two different domains**, i.e.
two cold circuits, ~21 s before any of it can complete.

## Measurements

Taken with `curl` from inside the coordinator's network namespace, same proxy,
same host, against the endpoint the dev-fee resolution actually uses:

| circuit | DNS     | connect | TLS      | total     | HTTP |
|---------|---------|---------|----------|-----------|------|
| cold    | 0.138 s | 0.138 s | 10.336 s | 10.601 s  | 200  |
| warm    | —       | —       | —        | 0.953 s   | 200  |
| warm    | —       | —       | —        | 0.831 s   | 200  |

Two things worth noting for anyone reproducing this:

1. **DNS is not the bottleneck** — 0.138 s out of 10.6 s. The cost is the TLS
   handshake, i.e. the circuit build.
2. **`time_connect` is misleading under a transparent proxy.** The kernel
   completes the local TCP handshake as soon as the SYN reaches the listening
   `TransPort` socket, *before Tor looks at the packet*. So `connect` reads as
   near-zero and all the real circuit work shows up in `time_appconnect`.
   Anyone reading only `connect` concludes the network is fine.

## Impact 1 — traders who submit a Lightning address are rejected

This is the more serious half, because it hits users rather than us.

`is_valid_invoice` tries the Lightning address / LNURL branch **first** and
only falls back to BOLT11:

```rust
if LightningAddress::from_str(&payment_request).is_ok()
    || LnUrl::from_str(&payment_request).is_ok()
{
    return validate_lightning_address(&payment_request).await;
}
validate_bolt11_invoice(&payment_request, amount, fee).await
```

`validate_lightning_address` -> `ln_exists` goes through the same `lnurl_get`
helper with the same three constants. On a Tor-routed coordinator a trader
supplying a perfectly valid Lightning address gets

```
MostroInternalErr(ServiceError::InvoiceInvalidError)
```

**at validation time** — they cannot even submit their payout destination, and
nothing tells them why. There is no retry loop here to save them. That path
has no outer timeout of its own, so raising the three constants is enough to
fix it.

## Impact 2 — the dev fee never settles, and floods the journal

`src/scheduler.rs` retries with `let interval = 60u64;` — every 60 seconds,
with no backoff, no attempt counter and no cap. On our node this produced

```
Found 1 orders with unpaid dev fees
... NoAPIResponse
```

roughly **3 lines per minute, ~4,300 per day**, indefinitely.

It settled exactly once, and by accident: a human happened to warm the circuit
with `curl` while debugging, and the next 60 s tick landed inside the warm
window. Without that, it would still be retrying.

Raising only the `lnurl.rs` constants does **not** fix this half. The two
nested caps in `src/app/dev_fee.rs` cut first:

- an inner `15s` around `resolv_ln_address`, and
- an outer `20s` around the whole resolution block.

The resolution is two HTTPS requests on two different domains (the
`.well-known/lnurlp/` host, then the callback host returned in the response),
each needing its own circuit: 10.6 + 10.6 ~ 21.2 s. **Neither cap was
reachable on a cold circuit even before any of this was touched.**

The failure log line also carries no step information, so a timeout, a non-200
and a parse error are indistinguishable without reading the source.

## Impact 3 — a coordinator that cannot pay the dev fee cannot say so

`MIN_DEV_FEE_PERCENTAGE` is `0.10` and the guard in `src/config/util.rs` uses a
strict `<`, so `dev_fee_percentage = 0` is rejected at startup. A coordinator
whose dev-fee payments cannot complete has no way to declare that: it must
either keep paying at least 10 % of its own fee or refuse to start.

Zero is already a supported state everywhere else in the code — notably
`find_unpaid_dev_fees` filters `AND dev_fee > 0`, so a zero-fee order never
enters the payment queue at all. Only that one check disagrees.

## Documentation mismatch

`docs/DEV_FEE.md` states `LNURL: 15s`, which matches neither the 4 s request
budget in `src/lnurl.rs` nor the 15 s / 20 s caps in `src/app/dev_fee.rs`. The
code is authoritative; the doc should be corrected either way.

## What we did locally

We run three patches on top of `v0.18.7` on our node, and they are working in
production (image `mostro:v0.18.7-bar1`). Happy to open them as a PR:

1. **`src/lnurl.rs`** — the three budgets from 4 s / 2 s / 2 s to
   30 s / 15 s / 10 s, roughly 3x the measured cold-circuit cost, with the
   comments explaining the trade-off (the bound on how long a silent host can
   stall the serial message loop widens from 4 s to 30 s) instead of simply
   recommending brevity.
2. **`src/config/util.rs`** — `dev_fee_percentage = 0` becomes the explicit
   opt-out. **Only the floor is relaxed, never the ceiling**: negatives stay
   invalid, the band between zero and the minimum stays invalid (whoever pays,
   pays at least 10 % — no grey scale where a coordinator claims to
   participate at 0.1 %), and the maximum is untouched. Ordering comparisons
   only, no float equality.
3. **`src/app/dev_fee.rs`** — the two nested caps from 15 s / 20 s to
   75 s / 90 s. The 75 must clear two 30 s requests; the 90 must stay above the
   75 or it decides instead. Both stay under the 5 minutes after which a
   `PENDING` reservation is released. The timeouts around the LND **payment**
   (50 s, 25 s, 10 s, 5 s) are deliberately **not** touched — the observed
   failure was `NoAPIResponse` during *resolution*.

`cargo test` on the three touched modules: 27 in `lnurl`, 24 in `config::util`,
58 in `dev_fee`, zero failures — including the two pre-existing
`dev_fee_below_minimum_is_rejected` and `dev_fee_above_maximum_is_rejected`,
which are the evidence that relaxing the floor opened neither the floor nor the
ceiling.

## What we would rather see upstream

Raised constants are a workaround; the shape of the fix is yours to choose. Our
preference, in order:

1. **Make the timeouts configurable** in `settings.toml` (e.g. an `[lnurl]`
   section) rather than `const` in the binary. Mostro coordinators are exactly
   the kind of node likely to run Tor-only, and the right budget depends on the
   operator's egress.
2. **Add backoff to the dev-fee retry loop** — exponential up to a ceiling,
   instead of a fixed 60 s forever. The current behaviour makes the journal
   unusable while never converging.
3. **Surface the failure reason** — distinguish timeout from HTTP error from
   parse error in the logged message, and give the trader something more
   specific than `InvoiceInvalidError` when the address could not be *reached*
   rather than being invalid.
4. **Accept `dev_fee_percentage = 0`** as an explicit opt-out.
5. Fix the `docs/DEV_FEE.md` figure.

## Reproducing

It reproduces reliably without any special setup beyond Tor egress: let the
circuit go cold (`MaxCircuitDirtiness` defaults to 600 s), then trigger a
payout, or submit a Lightning address as a payout destination. Do **not** run
`curl` against the same host first — that warms the circuit and hides the bug,
which is how we spent a day believing it was fixed.

## What we have not verified

That our own patches actually carry a dev fee through on a cold circuit. It can
only be proven by the next real trade with no circuit warmed beforehand.
