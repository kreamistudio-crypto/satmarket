# NIP draft: portable trade reputation

**Status:** draft proposal, not yet submitted to `nostr-protocol/nips`
**Scope:** a new regular kind for reputation earned in a completed trade.
No changes to existing kinds.

---

## Motivation

NIP-99 made the *listing* portable. Nothing made the *seller* portable.

A merchant who has completed two hundred honest trades on one marketplace
arrives at the next one with a rating of zero. The listing is a signed event
that belongs to whoever wrote it and survives the platform that displayed it;
the reputation earned selling that listing is a row in that platform's
database and dies with it. This is the asymmetry the proposal addresses.

The consequence is not only unfair to the seller — it is the main reason
marketplaces stay walled. Reputation is the switching cost. As long as it is
non-portable, every new marketplace starts empty for everyone, and buyers are
correctly reluctant to be the first.

### Why "just publish reviews" is not enough

The obvious shape — *who*, *about whom*, *a score*, *some text* — is easy and
worthless on its own. Reputation is worth exactly what it costs to forge, and
an event anyone can sign for free costs nothing: a thousand keys produce a
thousand five-star reviews in a second. Any proposal that stops at the schema
produces noise that clients will learn to ignore.

The scarce thing is not the opinion. It is **the fact that a trade actually
happened** — that money moved, that an object changed hands, that someone had
something to lose. A reputation NIP is therefore mostly a proposal about
*proof*, and only incidentally about scores.

---

## Design constraints

These are stated up front because they rule out most of the design space.

1. **Immutable.** A review that can be rewritten is a lever: "change your
   rating or I won't ship". The event MUST be a *regular* event, not
   replaceable and not addressable. Correction happens by NIP-09 deletion or
   by a later, separate event — never by silent overwrite.
2. **The traded object stays private.** That a person traded is public; *what*
   they bought is theirs. A naive `a` tag pointing at the listing turns a
   reputation feed into a purchase history for everyone the subject ever
   traded with.
3. **Role-scoped.** Buying well and selling well are different skills.
   Forty ratings earned as a buyer say nothing about a seller.
4. **No aggregation in the protocol.** The NIP defines what a single
   statement looks like. How to combine statements — whose keys to trust, how
   to weight, what to discard — is the reader's business. Specifying an
   average here would smuggle a central authority back in through the
   interpretation layer.
5. **Scale-normalised.** A decimal with no declared range is not comparable:
   `4.0` out of five and `4.0` out of ten are different facts, and anything
   that sums them produces a meaningless number.

---

## The event

Kind: **TBD** (regular, per constraint 1).

```jsonc
{
  "kind": <TBD>,
  "pubkey": "<author: the counterparty making the statement>",
  "created_at": 1755100000,
  "tags": [
    ["p", "<subject pubkey>"],            // about whom
    ["rating", "0.9"],                    // 0..1, decimal, REQUIRED
    ["role", "seller"],                   // subject's role: seller | buyer
    ["settled_at", "1754900000"],         // when the TRADE completed
    ["proof", "<see below>"]              // OPTIONAL but load-bearing
  ],
  "content": "Spedito il giorno dopo, imballato bene."
}
```

### `rating`

A decimal string in `[0, 1]`. Publishers normalise; clients render however
they like — five stars, ten points, a thumb. This is what makes the number
*expressible as you please* without making it incomparable: the freedom
belongs to presentation, not to the wire format.

Absent `rating` is legal and means "I attest to the trade but express no
opinion" — useful for the attestation-only case below.

### `settled_at`

Distinct from `created_at` on purpose. A review written three weeks after
delivery is still a review *of a trade that closed three weeks ago*, and
recency of the trade is what a reader weighs, not recency of the typing.

### `role`

The role of the **subject**, not of the author. `seller` and `buyer` are
defined here; other values are permitted and ignored by clients that do not
know them.

### `content`

Free text, optional. No formatting is specified.

### What is deliberately absent

- **No listing coordinate.** Per constraint 2. Implementations that need the
  link MAY publish a commitment — `["item_hash", "<sha256>"]` — which lets
  the two parties prove later *which* trade a statement refers to, without
  publishing it to everyone. This also blocks a real attack: writing many
  reviews for what was in fact a single trade.
- **No aggregate.** Per constraint 4. A publisher's own summary belongs in
  its profile metadata, not here.
- **No price.** It leaks the object almost as well as a listing link, and
  invites weighting schemes that make small honest trades count for nothing.

---

## The load-bearing part: proof

Without proof this is a review kind and will be treated as noise. Three
approaches, with the trade-offs, because the choice is not obvious and should
be argued in public rather than settled here.

**(A) Third-party attestation.** A marketplace — or an escrow provider —
signs a statement that the trade settled, and the review references it. This
is the only option available today for custodial escrow, where the buyer's
payment goes to the escrow and not to the seller, so the buyer holds no
payment proof naming the seller at all. It does not create a central
authority: the attester is just another pubkey, and readers weigh it by their
own web of trust. Forging costs the attester its own reputation, which is
precisely the scarcity we want. Cost: reputation earned in a market is only
as portable as that market is trusted — real, but strictly better than today,
where it is not portable at all.

**(B) Payment proof.** A Lightning preimage, or a settled on-chain output,
binding the statement to money that moved. Strongest where the buyer pays the
seller directly. Weakest exactly where marketplaces are strongest — under
escrow the counterparty of the payment is the escrow, so the proof attests
that *someone was paid*, not that *this seller delivered*.

**(C) Nothing, and let the web of trust sort it.** Cheapest to specify,
and it is what "just publish reviews" amounts to. Works for people already
inside someone's follow graph; fails for the case reputation exists to solve,
which is trading with a stranger.

**Recommendation:** specify `proof` as an open, typed container — 
`["proof", "<type>", "<value>", ...]` — with (A) and (B) defined and room for
more. A statement without proof stays valid and simply carries less weight.
Requiring proof would exclude honest trades that happened off-protocol; not
defining it at all would make every statement equally cheap, which is the
failure mode of every reputation system that has ever been abandoned.

---

## Non-goals

- **Dispute outcomes.** Who was right in an argument is not a rating, and
  publishing it invites retaliation. Out of scope.
- **Negative-only reporting / blocklists.** A different problem with a
  different threat model (NIP-56 already exists for reports).
- **Identity.** This says nothing about who a pubkey belongs to.

---

## Backwards compatibility

A new kind. Clients that do not know it ignore it. Nothing existing changes
shape or meaning.

---

## Reference implementation

Barattolo (<https://barattolo.store>) — a Lightning-escrow second-hand
marketplace — has the underlying facts in production: every rating is bound
to an order whose escrow actually settled, ratings are immutable by policy
(no editing, only moderator removal), buyer and seller ratings are already
stored separately by role, and the traded object is deliberately never
exposed on the public shop page while the identity of the reviewer is. The
three constraints above are not theoretical: each was arrived at from a real
incident or a real product decision, and each is already enforced there.
