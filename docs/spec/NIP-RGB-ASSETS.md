> **Draft, 8 October 2026 — design only.** Written before the *Agentic
> Dollars on Bitcoin* hackathon (Turin, 17-18 October 2026) as a
> declared design; the implementation (the signed announcements, the
> verification in a wallet and in the Barattolo marketplace) is hackathon
> work. Kind numbers are placeholders: maintainers assign them. Intended
> for `nostr-protocol/nips` once the implementation exists.

NIP-XX
======

RGB asset announcements
-----------------------

`draft` `optional`

This NIP defines how the **issuer of an RGB asset** announces the asset on
Nostr, and how clients and wallets verify who the issuer is. An RGB
contract on Bitcoin has an id and metadata (ticker, name, precision,
supply) but, as deployed today, no verifiable identity behind it: a token
can call itself anything, "USDT" included. An announcement signed by a
Nostr key, tied to a NIP-05 name, gives the asset a *declared* issuer; an
issuer field committed in the contract genesis gives it a *committed*
issuer. The announcement is an etiquette: it moves no asset and
authorises nothing.

### The announcement event

An **addressable event** (`kind:3xxxx`, placeholder — NIP-87 uses
38172/38173) published by the **issuer's key**:

```jsonc
{
  "kind": 3xxxx,
  "pubkey": "<hex pubkey of the issuer>",
  "tags": [
    ["d", "<ContractId without the rgb: prefix, e.g. 9N5NpOdN-Qdy418I-xs_gEFy-Wzk1p6X-S33L673-X~lm9iM>"],
    ["i", "rgb:contract:<ContractId>"], ["k", "rgb:contract"],   // NIP-73 external identity, new kind
    ["n", "signet"],                      // network, as in NIP-87: mainnet | testnet | signet | regtest
    ["schema", "nia"],                    // nia | uda | cfa | ifa | pfa
    ["ticker", "MOON"],
    ["name", "Punti To The Mooon"],
    ["precision", "0"],
    ["supply", "1000000"],                // issuedSupply, in the smallest unit
    ["issuer", "nostr:<hex>"],            // ONLY at level 2: the value of the genesis `issuer` field
    ["u", "https://example.com/moon.rgb"], // optional: where the contract consignment can be downloaded
    ["alt", "RGB asset announcement: MOON"]
  ],
  "content": "<free text: what it is, what it is worth, where it is accepted; OR the contract consignment, base64>"
}
```

Why these choices:

- `d` = ContractId makes the announcement **one per contract per key**:
  replaceable, so the issuer can correct metadata without duplicates, and
  queryable with `#d`.
- The `i`/`k` pair of NIP-73 with the new kind `rgb:contract` lets a
  review, a marketplace listing or a Mostro order point at the asset with
  a standard tag.
- `n` is the field name used by NIP-87.
- The metadata tags are **copies** of what the wallet reads from the
  genesis; the wallet MUST compare them (ticker, name, precision, supply)
  and MUST NOT display an announcement whose tags diverge from the
  genesis.
- The **contract consignment**, inline in `content` or behind `u`, lets a
  wallet learn an asset *before* receiving it (the "first invoice must be
  for any asset" problem of rgb-lib wallets). A contract consignment is a
  few KiB and can be encoded like a PGP key or a QR code.

### The recommendation event

`kind:3xxxx+1` (placeholder; the pattern of NIP-87 `kind:38000`),
published by anyone:

```jsonc
{
  "kind": 3xxxx+1,
  "tags": [
    ["k", "3xxxx"],
    ["d", "<ContractId>"],
    ["a", "3xxxx:<hex issuer pubkey>:<ContractId>", "wss://relay.example.com"],  // WHICH announcement is recommended
    ["i", "rgb:contract:<ContractId>"], ["k", "rgb:contract"]
  ],
  "content": "Accepted in my shop: 1 MOON = 1 sat of discount."
}
```

This is where a web of trust forms: a wallet that sees two announcements
for the same contract shows the one recommended by the people the user
follows (`{"kinds":[3xxxx+1], "authors":[<me and my contacts>], "#d":[<id>]}`),
and a shop that "recommends" MOON tells its customers that it accepts it.

### Verification

Five steps, in this order, stopping at the first that fails:

1. The event signature is valid (NIP-01) and `d` is **exactly** the
   ContractId the wallet holds (compare the normalised string, never the
   ticker: RGB rejected tickers as identifiers for security reasons).
2. The tags match the genesis (ticker, name, precision, supply).
3. The author's kind 0 declares a `nip05`.
4. The NIP-05 resolves to the **same key**: `GET
   https://<domain>/.well-known/nostr.json?name=<name>`, without
   following redirects, on a public host, and `names[<name>]` equals the
   event `pubkey`. Without this step the announcement is *declared*, not
   *verified*.
5. (Level 2) The genesis `issuer` field is `nostr:<hex>` and `hex` equals
   the event `pubkey`: the identity is **committed**, and no other key can
   claim the contract.

A client SHOULD display the state reached: *committed* (✓✓), *verified*
(✓), *declared*, *unknown issuer*.

### Security considerations

- NIP-05 is "identification, not verification": clients MUST show the full
  domain and MUST NOT abbreviate it.
- Follow the key, not the address: if the JSON one day answers a different
  key, the announcement stops being verified; it does not change issuer.
- The event's metadata never replace those of the genesis.
- The announcement authorises nothing: it does not move assets, it does
  not open channels. It is a signed label.
- Two announcements for the same contract from different keys are a
  feature (the recommendation layer decides), not an error.

### Open questions for maintainers

- Kind numbers.
- Whether `rgb:contract` should be registered in NIP-73 directly.
- Size limits for an inline contract consignment in `content`; relays may
  reject large events, in which case `u` (or a Blossom blob) is the path.
