# NIP-99 extension: commerce metadata for classified listings

**Status:** draft proposal, not yet submitted to `nostr-protocol/nips`
**Scope:** adds optional tags to `kind:30402` / `kind:30403`. No breaking changes.

---

## Motivation

NIP-99 standardises how a listing is *presented* (`title`, `summary`, `image`,
`location`, `price`, `status`) but says nothing about the facts a buyer needs in
order to actually complete a purchase:

- can the seller ship it, or is it pickup only?
- how much does shipping cost?
- is the item new or used?
- is there more than one in stock?
- how heavy is it? (needed to quote a courier)

Today every implementation solves this the same way: it writes the information
as **prose inside `content`**. That is fine for a human reader and useless for
everything else — no client can filter by "ships to me", no client can sort by
condition, no client can compute a shipping quote, and any aggregator has to
guess at free text in whichever language the seller wrote it.

The information already exists in every marketplace's database. It is only the
transport that is missing.

### This is not a greenfield proposal

Two facts should shape the outcome:

1. **Unstandardised tags are already in the wild.** Shopstr, the largest Nostr
   marketplace, publishes and parses `shipping`, `condition`, `quantity`,
   `pickup_location`, `size`, `volume`, `weight`, `bulk`, `valid_until`,
   `restrictions` and `required` on `kind:30402`. None of these appear in
   NIP-99. Any listing produced by Shopstr is therefore partly opaque to every
   other client, and vice versa.

2. **There is already a name collision.** Shopstr's `weight` tag means *product
   variant plus its price*:

   ```
   ["weight", "500g", "12.00"]
   ```

   The obvious reading of `weight` — the shipping weight of the parcel — has the
   same arity:

   ```
   ["weight", "1200", "g"]
   ```

   A parser written for one interpretation silently mangles the other
   (`parseFloat("g")` → `NaN`). This will get worse, not better, the longer the
   name stays unclaimed.

The point of this proposal is therefore less "invent vocabulary" and more
"claim the names before they are ambiguous everywhere".

---

## Proposed tags

All tags are **optional**. A listing without them behaves exactly as it does
today.

| Tag | Shape | Meaning |
|---|---|---|
| `delivery` | `["delivery", <method>, <cost>?, <currency>?]` | one accepted delivery method. Repeatable. |
| `condition` | `["condition", <value>]` | wear of the item |
| `stock` | `["stock", <count>]` | units still available |
| `weight` | `["weight", <number>, <unit>]` | shipping weight of the parcel |
| `dim` | `["dim", <length>, <width>, <height>, <unit>]` | parcel dimensions |

### `delivery`

```
["delivery", "shipping", "5.00", "EUR"]
["delivery", "pickup"]
["delivery", "digital"]
```

`<method>` is one of:

- `shipping` — the seller sends the item to the buyer
- `pickup` — the buyer collects it in person
- `digital` — delivered electronically, no parcel exists

The tag is **repeatable**, and this is deliberate. A seller who accepts both
shipping and local pickup emits two `delivery` tags. This avoids the
combinatorial enum that the de-facto vocabulary already ran into: Shopstr needs
the value `Free/Pickup` to express two methods at once, and adding a third
method would require enumerating every subset. Repetition scales; enums of
combinations do not.

`<cost>` and `<currency>` apply to `shipping` only, and follow exactly the
conventions of the existing `price` tag (same currency codes, `sats` included).
They are optional, and their absence is meaningful:

- `["delivery", "shipping", "0", "EUR"]` — shipping is **free**
- `["delivery", "shipping"]` — shipping is offered, cost **not declared**
  (to be agreed, or quoted later from `weight` and destination)

Clients MUST NOT treat a missing cost as zero.

Where pickup happens is already expressible with the standard `location` and
`g` tags; this proposal does not add a second way to say it.

### `condition`

```
["condition", "like-new"]
```

Closed vocabulary, ordered from best to worst:

| Value | Meaning |
|---|---|
| `new` | unused, still sealed or with tags |
| `like-new` | used once or twice, no visible wear |
| `good` | normal signs of use, fully functional |
| `fair` | clear wear, still works as intended |
| `poor` | damaged, incomplete, or sold for parts / repair |

Five steps is a deliberate compromise: it is the granularity actually offered by
the mainstream second-hand marketplaces sellers are migrating from, so listings
can be imported without inventing or discarding information. Implementations
that hold a finer scale should round to the nearest value rather than mint new
ones; an unknown value SHOULD be treated as absent.

Condition is meaningless for `digital` deliveries and for services, and SHOULD
simply be omitted there.

### `stock`

```
["stock", "3"]
["stock", "unlimited"]
```

Units still available for sale. **An absent `stock` tag means one**, which is the
overwhelmingly common case for classifieds and keeps single-item listings clean.

`unlimited` is a reserved literal for goods with no scarcity — digital downloads,
services, made-to-order items. It mirrors the `null` quantity of NIP-15's product
schema, expressed as a string because tag values are strings.

`["stock", "0"]` is legal and means temporarily out of stock while the listing
stays up; a listing that is finished SHOULD use `["status", "sold"]` instead.

### `weight` and `dim`

```
["weight", "1200", "g"]
["dim", "30", "20", "10", "cm"]
```

These describe the **parcel**, not the product variant. They exist so that a
client, a courier integration, or the buyer can quote shipping without asking
the seller.

- `weight` units: `g`, `kg`, `oz`, `lb`
- `dim` order is always length, width, height; units: `cm`, `in`

**Disambiguating the existing `weight` tag.** Because the variant-style
`["weight", "<label>", "<price>"]` is already published in the wild, parsers
SHOULD discriminate on the last element: if it is one of the four unit codes
above, the tag is a shipping weight; otherwise it is a legacy variant tag and
SHOULD be handled as before or ignored. New implementations SHOULD NOT emit the
variant form; product variants deserve their own tag and are out of scope here.

### Deliberately left out

- **Parcel size classes** (`envelope`, `small`, `medium`, …). Every carrier and
  every country slices these differently; `weight` and `dim` are the objective
  facts, and a size class is derivable from them locally.
- **Product variants** (size, colour, volume, bulk pricing). Real and needed,
  but a listing with variants has a different shape — it is closer to NIP-15's
  product model — and folding it in here would make a small proposal
  contentious.
- **Escrow, payment rails, buyer protection.** These describe the *venue*, not
  the item. The existing `r` tag already points at a venue that can describe its
  own terms.

---

## Example

```jsonc
{
  "kind": 30402,
  "created_at": 1753900000,
  "tags": [
    ["d", "barattolo-1187"],
    ["title", "Bicicletta da corsa Bianchi"],
    ["summary", "Telaio in acciaio, 10 velocità, revisionata"],
    ["price", "180.00", "EUR"],
    ["status", "active"],
    ["published_at", "1753900000"],
    ["location", "Brescia"],
    ["t", "sport"],
    ["image", "https://barattolo.store/foto/a1187_0.jpg"],

    ["condition", "good"],
    ["stock", "1"],
    ["delivery", "shipping", "12.00", "EUR"],
    ["delivery", "pickup"],
    ["weight", "11000", "g"],
    ["dim", "140", "80", "25", "cm"]
  ],
  "content": "Telaio in acciaio…"
}
```

## Backwards compatibility

Every tag here is additive and optional:

- clients that do not know these tags ignore them, as they already ignore any
  unknown tag, and keep rendering the listing exactly as today;
- publishers SHOULD keep writing the same facts in human language inside
  `content` for as long as adoption is partial — the tags are a machine-readable
  *duplicate*, not a replacement;
- no existing tag changes shape or meaning;
- the one interaction with deployed software is the `weight` collision described
  above, which is why a discrimination rule is specified rather than left open.

## Reference implementation

Barattolo (<https://barattolo.store>) — a Lightning-escrow second-hand
marketplace — publishes and consumes these tags on `kind:30402`. Its importer
also reads the Shopstr de-facto vocabulary, so both dialects are exercised
against real listings.
