> **Draft, 8 October 2026 — design only.** Written before the *Agentic
> Dollars on Bitcoin* hackathon (Turin, 17-18 October 2026) as a
> declared design; the implementation (the four methods in a WDK wallet
> and their use from a marketplace checkout) is hackathon work. The
> extension number (`XX.md`) is assigned by the maintainers of
> `nostr-wallet-connect/nwc` on the issue, per their CONTRIBUTING ("open
> an issue first"). The name is ours: **NWC-RGB**.
> **9 October 2026**: added `rgb_get_budget` and the *Authorization
> levels* section (a per-connection policy in the wallet, phrased in the
> terms of WDK's `registerPolicy`). Design only, as the rest.

# NWC-RGB: RGB assets over Nostr Wallet Connect

"An NWC on WDK": the wallet is a WDK wallet with the RGB module, the wire
is Nostr Wallet Connect (NIP-47), the extension adds RGB assets.

## Summary

Five request methods and two notifications that let an application ask a
remote wallet to list its RGB assets, create an RGB invoice to receive,
pay an RGB invoice (with the user's confirmation, or within a budget the
user set in the wallet), read that budget, and look a transfer up.
Field names follow the WebRGB provider specification so that an
application written for `window.rgb` can be ported to a remote wallet by
changing the transport only.

## Motivation

WebRGB is a provider in the same page as the application; this extension
brings the same methods to a wallet that lives somewhere else — a desktop
wallet, a WDK wallet in a service, a mobile wallet — over the channel
NIP-47 already gives to Lightning. A marketplace that accepts a merchant's
loyalty points or a stablecoin on RGB does not need to know which wallet
the customer uses.

## Dependencies

- NIP-47 (core).
- Extension 02 (notifications) for `rgb_transfer_received` /
  `rgb_transfer_settled`.
- Extension 06 (metadata) for the optional `metadata` field in requests.
- WebRGB SPEC v1 for method and field names.
- rgb-lib for the transfer states.

## Discovery

The methods appear in the `content` of the info event (kind 13194) and in
`get_info.result.methods`; the info event carries `["extensions", "XX"]`.
`get_info.result` gains one field:

```json
"rgb": { "network": "signet", "protocol": "RGB_L1", "extension": "NWC-RGB" }
```

`protocol` is `RGB_L1` (on-chain RGB transfers) or `RGB_LN` (RGB over
Lightning channels; not covered by this draft).

## Methods

Names carry the `rgb_` prefix because the NIP-47 core has no namespace and
`pay` / `receive` are taken by extension 321.

### `rgb_list_assets`

```jsonc
{"method": "rgb_list_assets", "params": {"schema": "nia"}}   // schema optional: nia | uda | cfa
→ {"result_type": "rgb_list_assets", "result": {"assets": [
     {"asset_id": "rgb:…", "schema": "nia", "ticker": "MOON", "name": "Punti To The Mooon",
      "precision": 0,
      "balance": {"settled": 60, "future": 60, "spendable": 60},
      "issuer": "ssi:anonymous"}                            // the genesis issuer field, when the wallet knows it
   ]}}
```

Balances are in the smallest unit (`precision` tells how to display).

### `rgb_make_invoice`

An RGB invoice to **receive** (blind or witness).

```jsonc
{"method": "rgb_make_invoice", "params": {
   "asset_id": "rgb:…",            // optional: absent = "any asset" (first contact with an asset)
   "amount": 100,                   // smallest unit; optional
   "witness": false,                // true: the payer funds the output (receiver may have no sats)
   "min_confirmations": 1,
   "expiry": 3600,
   "metadata": {}}}
→ {"result_type": "rgb_make_invoice", "result": {
   "invoice": "rgb:…/…/…", "recipient_id": "<utxob or address>",
   "expires_at": 1760000000, "witness": false, "min_confirmations": 1}}
```

### `rgb_pay_invoice`

Pay an RGB invoice. **The wallet decides whether to ask the user**: by
default it MUST ask for confirmation before paying — "it proposes, you
approve" lives in the wallet, not in the application that asks — and it
MAY pay without asking only inside a policy the user set in the wallet
itself (see *Authorization levels*). The result says which happened.

```jsonc
{"method": "rgb_pay_invoice", "params": {
   "invoice": "rgb:…",
   "amount": 5,                     // only if the invoice does not carry one
   "fee_rate": 2,                   // sat/vB, optional
   "metadata": {"order": "203"}}}
→ {"result_type": "rgb_pay_invoice", "result": {
   "transfer_id": "<id of the transfer in the wallet>",
   "txid": "<hex>" | null,
   "state": "waiting_counterparty",  // waiting_counterparty | waiting_confirmations | settled | failed
   "asset_id": "rgb:…", "amount": 5, "created_at": 1760000000,
   "authorization": "confirmed"}}     // confirmed (the user said yes) | auto (within the policy, no question asked)
```

An RGB transfer is not a synchronous call like `pay_invoice`: the payer
builds the PSBT and the consignment, posts it to the proxy, waits for the
receiver's ACK, then broadcasts; "paid" arrives in three steps. The
response therefore returns **immediately** with `transfer_id` and
`waiting_counterparty`; the receiver sees the consignment arrive on its
own side and accepts it, and does not need to trust the wallet's answer.
The states are those of rgb-lib.

### `rgb_lookup_transfer`

```jsonc
{"method": "rgb_lookup_transfer", "params": {"transfer_id": "…"}}   // or {"txid": "…"}
→ {"result_type": "rgb_lookup_transfer", "result": {
   "transfer_id": "…", "txid": "…", "state": "settled",
   "asset_id": "rgb:…", "amount": 5, "confirmations": 1,
   "created_at": 1760000000, "settled_at": 1760000600}}
```

### `rgb_get_budget`

What this connection may spend **without asking**, per asset: the shape
of NIP-47 `get_budget` (`used_budget`, `total_budget`, `renews_at`,
`renewal_period`) with the asset added, plus the per-payment threshold.
Amounts are in the asset's smallest unit. The application reads it to
tell the user in advance ("this payment will go through by itself", the
*simulate* of a policy) and to show the limits in its wallet page; it
cannot change it — the policy is set in the wallet, by the user.

```jsonc
{"method": "rgb_get_budget", "params": {}}
→ {"result_type": "rgb_get_budget", "result": {"budgets": [
     {"asset_id": "rgb:…USDB", "per_payment": 300, "total_budget": 2000, "used_budget": 480,
      "renewal_period": "daily", "renews_at": 1760054400},
     {"asset_id": "rgb:…MOON", "per_payment": null, "total_budget": 200, "used_budget": 0,
      "renewal_period": "daily", "renews_at": 1760054400}
   ]}}
```

An asset absent from `budgets` has no automatic allowance: every
`rgb_pay_invoice` for it asks the user. `per_payment: null` means no
per-payment cap inside the daily total.

## Notifications (extension 02)

Declared in the `notifications` tag of the info event, same generic
payload as the transfer object above:

- `rgb_transfer_received` — the consignment has been validated and
  accepted (state `waiting_confirmations`).
- `rgb_transfer_settled` — the transfer has the required confirmations.

They mirror the `transferReceived` / `transferSettled` events of WebRGB.
A notification is a convenience, not the proof: the receiver's own
refresh is.

## Errors

The core codes (`NOT_IMPLEMENTED`, `RESTRICTED`, `INSUFFICIENT_BALANCE`,
`INTERNAL`, `UNAUTHORIZED`) plus:

| Code | When |
|---|---|
| `ASSET_NOT_FOUND` | the wallet does not know `asset_id` (it has never received the asset: use a "any asset" invoice first) |
| `INVALID_INVOICE` | the invoice does not parse or has expired |
| `UNSUPPORTED_NETWORK` | the invoice is for another network (same error as extension 321) |
| `TRANSFER_FAILED` | the transfer could not be built, posted or broadcast |
| `USER_REJECTED` | the user did not confirm `rgb_pay_invoice` |

## Authorization levels (policy)

The question "may the wallet pay without asking?" is answered by a
**policy** that lives in the wallet, per connection (per application),
set by the user there and never by the application. We phrase it in the
terms of the WDK transaction policies (`wdk.registerPolicy`: rules with an
`operation`, an `action` ALLOW/DENY and `conditions` over the call's
arguments, default-deny, `simulate` to ask "would this pass?") so that a
WDK-native wallet can express the same policy with its own engine; a
wallet that is not WDK keeps the same shape in its own storage. Three
levels, from the most to the least autonomous:

| Level | Rule (operation `rgb_pay_invoice`) | What the user sees |
|---|---|---|
| 0 — points only | ALLOW if `asset_id` ∈ the user's *points* allowlist (e.g. the shop's MOON) and `used_budget + amount ≤ total_budget` for that asset | a notification after the fact ("25 MOON → To The Mooon, your free coffee"); no question |
| 1 — small amounts of a stablecoin | ALLOW if `asset_id` ∈ the *dollars* allowlist, `amount ≤ per_payment` and `used_budget + amount ≤ total_budget` | a notification after the fact ("paid 2.50 USDB, within your 3 USDB threshold; 2.50 of 20 today") |
| 2 — everything else | default-deny → the wallet asks the user and pays only on an explicit yes (`USER_REJECTED` otherwise) | the confirmation prompt, as in the core method |

A DENY rule always wins (e.g. `asset_id` outside both allowlists → level
2 regardless of amounts). `used_budget` resets at `renews_at`; the wallet
persists it. The application learns the levels from `rgb_get_budget`
and MAY say in advance which level a payment will take; the wallet's
answer (`authorization` in the `rgb_pay_invoice` result) is the truth.
Example policy, as a WDK rule set (illustrative):

```jsonc
{"scope": "account", "rules": [
  {"name": "points-only", "operation": "rgb_pay_invoice", "action": "ALLOW",
   "conditions": ["asset_id in points_allowlist", "used + amount <= 200"]},
  {"name": "small-dollars", "operation": "rgb_pay_invoice", "action": "ALLOW",
   "conditions": ["asset_id in dollars_allowlist", "amount <= 300", "used + amount <= 2000"]},
  {"name": "unknown-asset", "operation": "rgb_pay_invoice", "action": "DENY",
   "conditions": ["asset_id not in points_allowlist + dollars_allowlist"]}
]}   // anything unmatched → default-deny → ask the user (level 2)
```

## Security considerations

- `rgb_pay_invoice` MUST require an explicit user confirmation in the
  wallet unless a policy the USER set in the wallet allows it (levels 0
  and 1 above); a wallet MUST NOT pay silently by default, and MUST NOT
  let the application set or raise the policy.
- `rgb_get_budget` is read-only and reveals only limits and usage, never
  balances beyond what `rgb_list_assets` already gives.
- A wallet MUST NOT expose seeds, stash or consignments through this
  extension; only ids, states and amounts travel.
- A wallet SHOULD show the asset's announced and verified issuer (see the
  companion NIP draft) when asking for confirmation, so that "pay 4.80
  USDB" names who issued USDB.
- Amounts are in the smallest unit; applications MUST use `precision`
  from `rgb_list_assets` to display them (4.80 = 480 units at precision 2).

## Example: a checkout

1. The shop calls `rgb_list_assets` → the customer holds 60 MOON and
   50,000 units of USDB (precision 2).
2. The shop makes its own receiving invoice on its side (not through
   this extension) and shows "or 4.80 USDB".
3. The customer accepts; the shop calls `rgb_pay_invoice` with the shop's
   invoice; the wallet asks the customer (level 2: 4.80 USDB is above
   the 3 USDB per-payment threshold the customer set), pays, answers
   `waiting_counterparty` with `authorization: "confirmed"`. A 2.50 USDB
   order would have gone through at level 1, `authorization: "auto"`,
   with a notification; the 25 MOON for a reward at level 0.
4. The shop refreshes its own wallet, sees the consignment, ACKs; the
   wallet broadcasts; the shop marks the order paid at its chosen
   confirmation depth; `rgb_transfer_settled` reaches the customer.
