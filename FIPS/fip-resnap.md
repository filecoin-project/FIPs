# FIP-XXXX: Repeated SnapDeals with Piece-Level Integrity

| fip | <to be assigned> |
| --- | --- |
| title | Repeated SnapDeals (Re-Snap) with Piece-Level Integrity |
| author | @lucaniz (kuba/irene to be added if they want to) |
| discussions-to | [#538](https://github.com/filecoin-project/FIPs/discussions/538) |
| status | Draft |
| type | Core |
| created | 2026-06-18 |
| requires | FIP-0019, FIP-0076, FIP-0083 |

## Simple Summary

Allow a sector already updated by SnapDeals to be updated again, repeatably, and let a verifier confirm on-chain that the subset of pieces the storage provider claims to preserve across an update are genuinely unchanged.

## Abstract

SnapDeals (FIP-0019) lets a storage provider (SP) embed deal data into a CC-sector replica exactly once, by adding a randomized, unpredictable version of the data, and prove it in one message. This FIP makes that update repeatable ("Re-Snap") so an SP can swap data into and out of an already-snapped sector over its lifetime, reusing committed capacity rather than re-sealing.

Repetition raises an integrity requirement the one-shot case did not have: when an SP updates a sector holding several pieces and preserves a subset, a verifier must be able to confirm those pieces survived unchanged. This FIP specifies that mechanism so the check can run on-chain. It records an opt-in commitment to the sector's unsealed data (CommD), stored in a new `SectorOnChainInfo.UnsealedCID` field at update time, against which preserved pieces are checked via Merkle sub-tree (PoDSI) inclusion proofs. Because an FVM actor can read state but not historical events, storing CommD is what makes on-chain verification possible; where only off-chain verification is needed, the same CommD is already carried by the FIP-0083 `sector-updated` event and no new state is required.

As in FIP-0019, this FIP is scoped to CC sectors. Sectors sealed natively with data remain out of scope, for the same reason FIP-0019 excludes them (see Limitations), and are noted only as Future Work.

## Change Motivation

FIP-0019 unlocked committed capacity for a single round of data onboarding. Re-Snap addresses what FIP-0019 explicitly deferred (its Future Work anticipates terminating a deal in place for a new one, and updates to sectors that already hold data). Two concrete needs motivate it:

1. **Capacity reclamation.** An SP that has snapped data into a CC sector has no in-protocol way to free and re-use that sector apart from termination and re-seal. Re-Snap makes the Snap Deals update repeatable, so a sector can cycle through data sets at Snap Deals cost rather than sealing cost. This matters increasingly under on-chain storage-services (FWSS) models, where SPs re-use committed capacity (assuming a PoRep service is in place).
2. **Partial updates with preserved content.** A sector often holds several pieces, and some of them can become inactive or need to be changed. There is currently no protocol-level way to swap out only a portion of the content while proving the rest of the pieces were left intact. Re-Snap with piece-level integrity provides this, and (unlike a scheme that reads piece metadata from market or verifreg state) does so without depending on any piece having a deal or claim (see Design Rationale).

What this FIP does not support (see Future Work):

- Re-Snap of sectors sealed natively with data (non-CC sectors).
- Moving pieces or deals across sectors.
- Sub-piece-granularity updates.

## Specification

### Nomenclature

Refer to FIP-0019 for: **SectorKeyCID** (on-chain commitment of the CC-sector replica), **UnsealedSectorCID** (commitment of the data, i.e. CommD), **SealedSectorCID** (commitment of the replica with data embedded), **EncodingRands**, **Poseidon-128**.

Added here:

**PieceCID (CommP)** — Merkle root commitment of an individual piece.

**Preserved piece** — a piece the SP declares to carry forward unchanged from the pre-update to the post-update sector.

**Inclusion proof** — a Merkle sub-tree proof that a PieceCID sits at a stated offset within a CommD, per the PoDSI construction.

**Re-Snap** — application of the Snap Deals update to a sector whose `SectorKeyCID` is already set.

**UnsealedCID** — the new `SectorOnChainInfo` field introduced by this FIP. It stores CommD (the value FIP-0019 calls `UnsealedSectorCID`). The field name mirrors the existing `SealedCID` field (which stores CommR), following the convention that `SectorOnChainInfo` names commitments by CID role rather than by FIP-0019 nomenclature.

### Parameters

Unchanged from FIP-0019: **ChallengesNumber** = 1376, **HashShards** = 512. Re-Snap introduces no new cryptographic parameters.

### One-message Update Protocol

The protocol is that of FIP-0019, with the difference that it may be initiated on a sector that has already been snapped. The encoding step is unchanged:

```
newReplica[i] = Enc(sectorKey[i], data[i], EncodingRand(i))
```

For a first snap, `sectorKey` is the CC replica, exactly as in FIP-0019. For a Re-Snap, the sector is first decoded back to its CC key (`CommR_D → CommR_zero`) and the new data is then encoded against that same recovered CC key (`→ CommR_{D'}`). The CC key is invariant across re-snaps; the encoding sees the same `sectorKey` it would on a first snap. No step of the FIP-0019 protocol is removed; one precondition is relaxed, as detailed in the actor-method spec below.

### Algorithms

Unchanged from FIP-0019:

- **Encoding Randomness** — `EncodingRand(UnsealedSectorCID, i) = Poseidon-128(UnsealedSectorCID, i*HashShards//NodeSectorSize)`.
- **Encoding** — `Enc(sectorKey[i], data[i]) = sectorKey[i] + data[i] * EncodingRand(i)`.
- **Decoding** — `Dec(sectorKey[i], replica[i]) = (replica[i] - sectorKey[i]) * EncodingRand(i)^{-1}`.

These constitute the cryptographic core, and this FIP changes none of them. Re-Snap is repeated application of exactly these algorithms; the SNARK, the encoding, and the randomness derivation are those of FIP-0019.

### Retrieving updated data from encoded replica

Recovery is as in FIP-0019: regenerate `sectorKey`, then `Dec` each node. Note for Re-Snap that a deal-serving SP already stores the current replica (PoSt proves it), so moving between data sets is a decode/encode against the recovered CC key.

### ProveReplicaUpdates3 Actor Method

The Snap Deals update method has changed name and signature since FIP-0019. FIP-0019's `ProveReplicaUpdates` (method 27) and the explicit-CommD `ProveReplicaUpdates2` (method 29) have both been removed (method 29 by FIP-0076, method 27 by FIP-0106). The live method is `ProveReplicaUpdates3` (method 35), introduced by FIP-0076, which declares sector content as a piece manifest rather than `[]DealID`. Re-Snap extends this method.

FIP-0076 already anticipates this work: its `SectorUpdateManifest.Pieces` field is documented as requiring all-new pieces only because the sector was previously empty, pending re-snap support. This FIP lifts that restriction.

### Params

The parameter shape is the FIP-0076 `SectorUpdateManifest`, which already replaced `Deals []DealID` with a piece manifest. This FIP adds one optional field, `TrackUnsealedCid`:

```
struct SectorUpdateManifest {
    Sector:           SectorNumber,
    Deadline:         u64,
    Partition:        u64,
    NewSealedCid:     Cid,                       // CommR
    Pieces:           []PieceActivationManifest, // ordered declaration of new content
    TrackUnsealedCid: bool,                      // opt-in: persist CommD into SectorOnChainInfo
}
```

The top-level `ProveReplicaUpdates3Params` (carrying `SectorUpdates`, `SectorProofs`/`AggregateProof`, the proof types, and the `Require*Success` flags) and the `ProveReplicaUpdates3Return` (a `BatchReturn`) are unchanged from FIP-0076. `PieceActivationManifest` already provides the per-piece CID and size needed for inclusion proofs and is not modified.

### Spec

Unless stated, each step operates on all input updates in a loop.

1. **Param validation**
    1. Assert proof size is within limits.
    2. Assert batch size is within limits.
    3. Assert the sector's power is active; fail if the sector is in an unproven, faulty, or terminated state.
    4. The sector may already have a non-null `SectorKeyCID` (a previously-snapped sector is a valid update target. This is the one precondition that differs from FIP-0019, which asserts the sector has no deals.)
2. **Data activation and CommD generation**
    1. Activate the supplied `Pieces` per the Direct Data Onboarding activation path.
    2. Compute `NewUnsealedCid` (CommD) from the piece manifest, batched across all updates.
3. **Proof verification**
    1. Verify the replica-update proof for each update against `NewSealedCid`, `NewUnsealedCid`, and the sector key, as in FIP-0019. The proof binds the post-update manifest to the sealed bytes — the fact that makes preserved-piece verification possible without a challenge round.
4. **Update Miner State**
    1. `SectorNumber`, `Expiration`, and `SealProof` remain unchanged.
    2. `SealedCID` and the piece/weight fields are updated to match the new content.
    3. `InitialPledge` is the max of the sector's current value and the value computed with the update power at the update epoch.
    4. `ReplacedDayReward` / `ExpectedDayReward` are recalculated.
    5. `ReplacedSectorAge` and `ExpectedStoragePledge` are recalculated.
    6. If `SectorKeyCID` is null, set it to the `SealedCID` of the CC sector being replaced (first snap). If it is already non-null (re-snap), leave it unchanged — the CC key is invariant across re-snaps, and overwriting it with an intermediate sealed CID would break decoding.
    7. If `TrackUnsealedCid` is true, set `SectorOnChainInfo.UnsealedCID = NewUnsealedCid`. If false, leave it untouched.
    8. `Activation` is set to the current epoch.
    9. Call `ReplaceSectors` on all partitions with updates.
5. **Update Power**
    1. `partition.ReplaceSectors` updates miner deadline state to the correct power.
    2. Call `power.UpdateClaimedPower` to update power-actor state.
6. **Notifications and events**
    1. The `SectorContentChanged` notification flow and the FIP-0083 `sector-updated` event fire as in FIP-0076. This FIP relies on the existing `sector-updated` payload — which already carries `unsealed-cid` plus a `(piece-cid, piece-size)` pair per piece — and requires only that it continue to be emitted on every update, regardless of `TrackUnsealedCid`, since off-chain verification reads CommD from it. No change to the event schema is needed.

### Batching and Error Handling

This method accepts a batch of updates in one message. As much as possible, error handling should ignore updates that fail validation and fail only if all updates fail or if the entire operation fails. The `TrackUnsealedCid` write does not change this: failure to persist CommD for one update must not abort sibling updates that validated.

### Upgrade and State Migration

1. Add `UnsealedCID` as an optional field on `SectorOnChainInfo` — a pointer to a CID serializing to CBOR null. For every existing sector it migrates to null.
2. No data migration beyond the field addition. Historical sectors are not backfilled; the field is prospective-only, populated solely by future opted-in updates.
3. Relaxing the previously-empty-sector precondition in `ProveReplicaUpdates3`, together with the new field, is a behavioural change in the miner actor and requires a new actors version and a network upgrade, as FIP-0019 itself required.

### Piece-level integrity construction

This is the substantive addition relative to FIP-0019. It answers one question: for each piece the SP claims to preserve across an update, was it actually carried forward unchanged?

**Anchor.** CommD is written by the miner actor (step 2 above) and bound by the replica-update proof (step 3). The SP cannot assert a CommD inconsistent with the sealed bytes, so CommD on each side of an update is a trustworthy, SP-unforgeable anchor.

**Check.** For each preserved PieceCID `p`, the SP supplies a PoDSI inclusion proof of `p` into `CommD_old` and into `CommD_new`. If both verify at the declared offset and the PieceCID matches, the piece was preserved. No challenge round is needed: the replica-update proof already binds the manifest to the sealed bytes, so the inclusion check alone is sufficient.

**Note.** If producing an inclusion proof for every kept piece becomes impractical at scale, this can be relaxed to proving a randomized subset of the kept pieces per update — a probabilistic sampling tradeoff, offered as an option rather than part of the base per-piece construction.

**Where CommD is read from.** The verifier needs CommD for both sides of the update. There are two sources:

- **On-chain.** An FVM actor can read current state but not historical events. For a preservation guarantee to be load-bearing on-chain — for an FWSS or market contract, a collateral or SLA actor, or a PDP-style obligation — CommD must be in `SectorOnChainInfo`. This is the purpose of the opt-in `UnsealedCID` field. An actor reads `CommD_old` and `CommD_new` from state, accepts the SP's inclusion proofs as call data, verifies them, and may then gate on-chain logic on the result.
- **Off-chain.** The FIP-0083 `sector-updated` event already exposes CommD to off-chain parties. For pre-activation sectors and SPs who do not opt in, an off-chain verifier reads CommD directly from the event, byte-identical to the stored value. This path cannot serve an on-chain verifier.

**Event payload caveat.** The `sector-updated` event lists `(piece-cid, piece-size)` pairs but not per-piece offsets, and does not commit to ordering — it is an unordered set. The offset a PoDSI proof needs follows from the ordered packing of padded piece sizes, so the SP supplies the claimed ordering and offset, and the inclusion proof against the actor-attested CommD validates it; a wrong ordering fails to prove. CommD is the anchor on both paths, and ordering is checked by the proof, never asserted by state or event.

## Design Rationale

### The cryptographic core is untouched

Re-Snap is repeated application of the FIP-0019 encoding against the recovered CC key. The circuit only ever sees `(OldCommR, NewCommR, CommD)` and verifies `R* = R + D·ρ` against inclusion openings; it has no notion of how many times a sector was snapped. The proof system is therefore identical, and FIP-0019's encoding-function rationale and parameter choices carry over unchanged.

### Why piece metadata is not read from market or verifreg state

After Direct Data Onboarding (FIP-0076), pieces can be activated via raw `PieceActivationManifest` with no deal and no FIL+ claim, so for many pieces there is nothing in market or verifreg state to read; and that state was never keyed by position within the sector, so it could not supply ordering in any case. The CommD-anchored inclusion-proof construction depends on neither deals nor claims existing, which is why it is the durable choice.

### Why CommD is stored in state

The motivating goal is that piece preservation be verifiable on-chain, so the guarantee can be made load-bearing in protocol logic. An FVM actor reads state, not historical events, so on-chain verifiability requires CommD in `SectorOnChainInfo`. That is the reason for the opt-in field; its cost is one optional CID per opted-in sector, written from a value the update already computes, with no migration. If on-chain verification were ruled out of scope, the field could be dropped and verification specified purely against the FIP-0083 event. On the other hand, reading/browsing blockchain history is not a lightweight task. CommD stored in state seems to be the better tradeoff we can think of.

### Why opt-in and prospective-only

Backfilling CommD for all existing sectors would be a large migration for a feature only some sectors use. The objection that storing CommD would roughly double the state tree (raised in Discussion #298) targets retroactive, always-on storage; a prospective, opt-in field avoids it and ties cost to use.

### Why reuse PoDSI

PoDSI (Discussion #512) already proves a PieceCID sits at a given offset within a CommD, with padding and alignment handled. Reusing it avoids a second inclusion-proof scheme and keeps this FIP focused on Re-Snap semantics and the anchor.

### Limitations

As in FIP-0019, and for the identical reason, Re-Snap is limited to CC sectors: the `SectorKeyCID` (the bare CC replica) is only recoverable for sectors sealed without data. A natively-sealed sector's `SealedSectorCID` commits to `CommRLast+Data`, exposing no bare CC key to snap against. Extending to native sectors is a separate track (see Future Work).

## Backwards Compatibility

The new `SectorOnChainInfo.UnsealedCID` field is additive and optional, serializing to null for every existing sector, so no existing sector's serialization or behaviour changes. Permitting `ProveReplicaUpdates3` to run on an already-snapped sector does not change its semantics for the first-update case. As with FIP-0019, the change is not backwards compatible at the actor level and requires a new actors version and a network upgrade.

## Test Cases

TBD, but at a high level (from the protocol-design standpoint):

- Re-Snap a previously-snapped sector; confirm the replica-update proof verifies and state updates correctly.
- On a Re-Snap, confirm `SectorKeyCID` is not overwritten.
- Opt in (`TrackUnsealedCid = true`); confirm `UnsealedCID` is populated with the actor-computed CommD.
- Preserve a piece; produce PoDSI inclusion proofs against `CommD_old` and `CommD_new`; confirm both verify.
- Claim preservation for a piece that was not carried forward; confirm at least one inclusion proof fails.
- Verify a preserved-piece claim off-chain by reading CommD from the FIP-0083 `sector-updated` event; confirm it matches the stored-CommD result.

## Security Considerations

### Inheritance of FIP-0019's epsilon-replication analysis

This FIP does not modify the encoding, randomness derivation, or SNARK, so FIP-0019's two security analyses — the "2 bytes for 1 bit" flipping-adversary argument and the Kolmogorov-complexity bound, with full treatment in FIP-0019's SnapDeals theory report — apply unchanged to each Re-Snap round. Each round is, cryptographically, an independent FIP-0019 update against the recovered CC key, so repetition does not weaken the per-round bound.

### Anchor unforgeability

The integrity guarantee rests on CommD being actor-written and proof-bound, never SP-asserted. A preservation claim that passes the inclusion check cannot be satisfied for a piece that was not actually preserved.

### [minor] Off-chain and on-chain CommD are identical

CommD read from the FIP-0083 event is the same actor-emitted value the opt-in field stores; the two are byte-identical. The event path is only costlier to query and unavailable to on-chain actors, not weaker in trust.

## Incentive Considerations

As in FIP-0019, Re-Snap does not release currently held collateral but allows that collateral to be reused if more is required (verified data/IP increasement). Re-Snap additionally lets collateral and capacity be reused across successive data sets, making capacity reclamation cheaper than terminate-and-reseal.

## Product Considerations

Re-Snap lets SPs treat committed capacity as a reusable resource rather than a one-time onboarding slot, which is central to on-chain storage-services models. The piece-level integrity layer lets clients and auditors (and, with in-state CommD, on-chain actors) obtain a verifiable guarantee that specific pieces survived an update, with no interactive step.

## Implementation

The principal work items are:

- Permit `ProveReplicaUpdates3` to run on an already-snapped sector (the validation change in step 1.d and the `SectorKeyCID` invariant in step 4.f);
- Add the optional `UnsealedCID` field and its prospective population;
- Provide tooling to produce and verify PoDSI inclusion proofs against stored or event-sourced CommD.

**Notes**

1. The miner-actor changes are what this FIP specifies; an FVM actor that consumes in-state CommD to verify preservation on-chain is a separate contract, out of scope here.
2. The `ProveReplicaUpdates3` method, parameter, return, and manifest names used above follow FIP-0076; `UnsealedCID` and `TrackUnsealedCid` are introduced here and named to mirror the existing `SealedCID` field.
3. Exact placement in the current `SectorOnChainInfo` layout should be confirmed against `builtin-actors` at implementation time.

## Future Work

- **Native deals (non-CC) sector Re-Snap.** Modelling the native replica as `R = R_0 + D` and snapping a fresh term on top. `generate_replica_id` binds CommD for all sectors, with no CC-vs-native branch, leaving two open items that gate native support:
    - A formal space-hardness analysis of the cross-term (never investigated, but seems straightforward).
    - Recoverability of / access to the initial replica `R_0 + D`, in order to be able to retrieve the snapped data (ideally without having to pay additional storage cost apart from the replica storage cost, similarly to what happens to the CC sectors case). Some analysis has been done in this sense, but it is out of scope for this FIP.
- **A canonical on-chain verifier actor.** This FIP puts CommD in state so on-chain verification is possible; a natural follow-up is a shared FVM actor (or a method on a storage-services actor) that performs the PoDSI check, so SPs and clients share a single audited implementation.
- **Cross-sector piece movement** and **sub-piece-granularity updates**, both of which FIP-0019 also defers.

## Copyright

Copyright and related rights waived via CC0.
