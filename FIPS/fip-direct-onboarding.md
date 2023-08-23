---
fip: "<to be assigned>"
title: Direct data onboarding
author: "Alex North (@anorth), @zenground0"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/730
status: Draft
type: Technical
category: Core
created: 2023-08-24
---

## Simple Summary

Adds new prove-commit and replica-update methods to the miner actor which support committing to data
and claiming verified allocations without requiring a deal with the built-in market actor.
Adds a sector→deal mapping in the built-in market actor and deprecates the storage of deal IDs in the miner actor.
Removes the legacy Miner::PreCommitSector (method 6) and Miner::PreCommitSectorBatch (method 25),
in favour of the existing Miner::PreCommitSectorBatch2 (method 28) which requires
the sector unsealed CID to be specified while pre-committing.

Existing onboarding flows that use the built-in market actor remain fully supported, but optional.

## Abstract

The only mechanism today by which storage providers (SPs) are permitted to commit data in sectors is
to make a deal with the built-in storage market actor.
The built-in market actor is expensive in gas, and offers only basic functionality.
Requiring its use raises costs and limits the utility and value of sectors,
and the applications that can be built on Filecoin.

This cost and inconvenience is unnecessary in the common cases of verified deals with no client payments,
and storage arrangements that do not require any on-chain deal.
The verified registry actor already records deal-like information describing DataCap allocation terms.

This proposal adds new onboarding methods which support direct commitment of data into sectors,
without necessary reference to any deal.
This provides gas-cheap data onboarding for many use cases.
It also introduces a new scheme for deal activation which can support deals brokered by user-programmed smart contracts.
This new scheme is initially limited to the built-in market actor, but can be extended to other actors in the future.

## Change Motivation

The built-in market actor is expensive to use but provides very little utility to majority data onboarding use cases.
A vast majority of deals today are simple FIL+ verified deals with no client payment.
Since the verified registry actor already records all relevant information about DataCap allocation terms
(the client and provider, piece commitment, and duration),
the built-in market actor's replication of this data is unnecessary.
The built-in market plays no necessary role in allocating or accounting for QA power.
Publishing deals is the largest on-chain cost of QA power onboarding,
currently consuming a large fraction (about half) of total chain bandwidth.
If the built-in storage market actor were bypassed for the common cases of un-paid or off-chain settled deals,
both verified and unverified data could be onboarded at a significant reduction in gas cost.

The built-in market actor is also very limited.
It supports only a single, simple deal schema and policies, and does not support a range of desirable market features.
User-programmed smart contracts are restricted in the functionality that they can provide by the necessity
of using the built-in market actor as an intermediary for any data commitments.
They are also restricted by the lack of any hooks into the built-in miner actor to be notified of sector data
commitments.

Requiring the built-in market actor raises costs and limits the utility and value of sectors,
and the applications that can be built on Filecoin.
It cannot support the expansion in usage or functionality that network participants hope for.

This proposal aims to:

- Support data onboarding, including Fil+ verified data, with no smart-contract intermediary;
- Provide a new scheme for data activation which can support
  user-programmed smart contracts to function as data storage applications (including as markets);
- Continue supporting existing onboarding methods to give participants time to migrate their workflows.

## Specification

### Overview

Direct data onboarding comprises changes to the built-in miner and market actors
to provide new onboarding methods that do not require a built-in market deal.
These new methods accept additional parameters from the storage provider which specify
the pieces of data activated in the sector, any verified allocations being claimed,
and the address of any actors to notify about the successful activation.
Deals are possible, but not necessary.

In the direct onboarding flow:

- _[for verified data only]_ a client makes a verified allocation directly with the verified registry
  by transferring DataCap tokens to it (this is already possible today),
- _[for on-chain paid deals only]_ an SP publishes storage deals to the built-in market actor (also already possible
  today),
- at pre-commit, an SP must specify a sector’s data commitment (unsealed CID),
  but does not need to specify the structure of that data nor any deals or verified allocations.
- at prove-commit or replica-update, an SP specifies the pieces of data comprising a sector,
  and for each piece may nominate:
    - a verified allocation to claim, and/or
    - an actor to notify of the commitment (e.g. to activate a deal).

The miner actor verifies that the pieces of data claimed by the SP correspond to the data commitment proven.
The verified registry is involved only if verified data is being claimed.
The built-in market actor is involved only if an on-chain-settled deal is required (i.e. if non-zero payment).
Otherwise, the SP simply commits data directly to their sector with no unnecessary overhead.

Existing onboarding methods are retained and remain fully supported, but optional.

### Storage miner actor

No changes to miner state schemas are necessary,
but the deal IDs stored on with each sector's metadata are redundant.
The sector→deal association will be stored in the built-in market actor instead, and
any information that remains in the miner actor state will be incomplete.

The interpretation of some fields changes slightly.
No migration is necessary.

TODO: remove PreCommitSector and PreCommitSectorBatch methods

#### State

##### SectorPreCommitInfo

The `DealIDs` field remains in use to support existing onboarding methods.
It is required to be empty by the new `ProveCommitSectors2` method.

Pre-commit deal IDs may be removed in a future FIP when deprecating the old methods.

##### SectorOnChainInfo

The per-sector `DealIDs` field is deprecated and to be ignored.
The miner actor will not write to it.

The `DealWeight` field is interpreted to carry the weight of _any non-zero, unverified data_ in a sector,
not only the weight of deals made via the built-in market actor.
Similarly, the `VerifiedDealWeight` field carries the weight of _any verified data_, regardless of
whether a "deal" was made via the built-in market actor.

Per-sector deal IDs may be removed from state in a future migration.

#### Sector activation

The miner actor exports new methods for sector activation:
`ProveCommitSectors2` (method 33) and `ProveReplicaUpdates3` (method 34).
These new methods both support either batched or aggregated proofs, though aggregated proofs for
replica updates are not yet possible.

##### ProveCommitSectors2

This method rejects sectors that deal IDs specified at pre-commit.
Such sectors must be activated with the existing `ProveCommitSector` or `ProveCommitAggegate` methods.
This method does not fetch deal information from the built-in market actor.
Instead, the pieces of data that comprise a sector are declared as a _manifest_.

Each piece in a manifest _may_ declare a verified data allocation ID that it satisfies.
The method will attempt to claim that allocation directly from the verified registry actor and, if successful,
calculate quality-adjusted power according to the piece’s size.
If unsuccessful, the sector will not be activated.

Each piece in a manifest _may_ specify the address of an actor and a notification payload,
to be notified synchronously when the sector is activated.
After successful activation, the method will invoke the `SectorContentChanged` method
on the target actor with the piece CID and payload.
This functions as a notification that the piece has been committed, e.g. to a marketplace.
`SectorContentChanged` will be invoked just once per recipient actor, with a message body
describing all pieces to be notified to that actor.

In execution of `ProveCommitSectors2`, the miner actor:

1. validates that the pre-committed sectors are eligible for activation, rejecting any that specified deal IDs;
2. verifies the sector seal proofs or aggregate proof, and hence the sealed and unsealed CIDs;
3. computes an unsealed CID from the piece manifests and verifies it matches the proven one;
4. claims any verified allocations specified in the piece manifest;
5. computes weights, pledge, power etc and activates the new sectors in state;
6. notifies any actors specified in the piece manifests.

```
struct ProveCommit2Params {
    // Activation manifest for each sector being proven.
    SectorActivations: []SectorActivationManifest,
    // Proofs for each sector, parallel to activation manifests.
    // Exactly one of sector_proofs or aggregate_proof must be non-empty.
    SectorProofs: [][]byte,
    // Aggregate proof for all sectors.
    // Exactly one of sector_proofs or aggregate_proof must be non-empty.
    AggregateProof: []byte,
    // Whether to abort if any sector activation fails.
    RequireActivationSuccess: bool,
    // Whether to abort if any notification returns a non-zero exit code.
    RequireNotificationSuccess: bool,
}

// Data to activate a commitment to one sector and its data.
// All pieces of data must be specified, whether or not not claiming a verified allocation or being
// notified to a data consumer.
// An implicit zero piece fills any remaining sector capacity.
struct SectorActivationManifest {
    // Sector to be activated.
    Sector: SectorNumber,
    // Pieces comprising the sector content, in order.
    Pieces: []PieceActivationManifest,
}

struct PieceActivationManifest {
    // Piece data commitment.
    CID: Cid,
    // Piece size.
    Size: PaddedPieceSize,
    // Identifies a verified allocation to be claimed.
    VerifiedAllocationKey: Option<VerifiedAllocationKey>,
    // Synchronous notifications to be sent to other actors after activation.
    Notify: []DataActivationNotification,
}

struct VerifiedAllocationKey {
    Client: ActorID,
    ID: AllocationID,
}

struct DataActivationNotification {
    // Actor to be notified.
    Address: Address,
    // Data to send in the notification.
    Payload: []byte,
}

struct ProveCommit2Return {
    // Sector activation results, parallel to input sector activation manifests.
    Sectors: []SectorActivationReturn,
}

struct SectorActivationReturn {
    // Whether the sector was activated.
    Activated: bool,
    // Power of the activated sector (or zero).
    Power: StoragePower,
    // Piece activation results, parallel to input piece activation manifests.
    Pieces: []]PieceActivationReturn,
}

struct PieceActivationReturn {
    // Whether a verified allocation was successfully claimed by the piece.
    Claimed: bool,
    // Results from notifications of piece activation, parallel to input notification requests.
    Notifications: []DataActivationNotificationReturn,
}

struct DataActivationNotificationReturn {
    // Exit code from the notified actor.
    Code: ExitCode,
    // Return value from the notified actor.
    Data: RawBytes,
}


```

##### ProveReplicaUpdates3

As for `ProveCommitSectors2`, this method does not fetch deal information from the built-in market actor.
Instead, the pieces of data that comprise the updated sector content are declared as a _manifest_.
This manifest is similar to the manifest for `ProveCommitSectors2`, with differences being to specify
the existing sector state to be updated rather than a new one.

The specification and semantics of pieces, including verified allocation IDs and notifications,
is the same as for `ProveCommitSectors2`.

In execution of `ProveReplicaUpdates3`, the miner actor:

1. validates that the existing sectors are eligible for update;
2. computes an unsealed CID from the piece manifests;
3. verifies the sector update proofs or aggregate proof, and hence the new sealed and unsealed CIDs
   match the values declared and computed respectively;
4. claims any verified allocations specified in the piece manifest;
5. computes weights, pledge, power etc and activates the new sectors in state;
6. notifies any actors specified in the piece manifests.

```
struct ProveReplicaUpdates3Params {
    SectorUpdates: []SectorUpdateManifest,
    // Proofs for each sector, parallel to activation manifests.
    // Exactly one of sector_proofs or aggregate_proof must be non-empty.
    SectorProofs: [][]byte,
    // Aggregate proof for all sectors.
    // Exactly one of sector_proofs or aggregate_proof must be non-empty.
    AggregateProof: []byte,
    // The proof type for all sector update proofs, individually or before aggregation.
    UpdateProofsType: RegisteredUpdateProof,
    // The proof type for the aggregate proof (ignored if no aggregate proof).
    AggregateProofType: RegisteredAggregateProof,
    // Whether to abort if any sector update activation fails.
    RequireActivationSuccess: bool,
    // Whether to abort if any notification returns a non-zero exit code.
    RequireNotificationSuccess: bool,
}

pub struct SectorUpdateManifest {
    Sector: SectorNumber,
    Deadline: u64,
    Partition: u64,
    NewSealedCid: Cid, // CommR
    // Declaration of all pieces that make up the new sector data, in order.
    // Until we support re-snap, pieces must all be new because the sector was previously empty.
    // Implicit "zero" piece fills any remaining capacity.
    // These pieces imply the new unsealed sector CID.
    Pieces: []PieceActivationManifest,
}

type ProveReplicaUpdates3Return = ProveCommit2Return;
```

#### SectorContentChanged

When a piece manifest specifies one or notification receivers,
the storage miner invokes these receivers after activating the sector or replica update.
The receiving actor must accept the `SectorContentChanged` method number and parameter schema.
`SectorContentChanged` is an FRC-0046 method, intended to be implemented by other actors.
The miner actor will invoke each receiver address only once, with a batch of notification payloads.

The miner actor will reject attempts to notify any actor other than the built-in storage market actor (`f05`).
This restriction may be lifted in a future FIP once the security considerations of calls into
untrusted code are better understood and mitigated.

```
// Notification of change committed to one or more sectors.
// The relevant state must be already committed so the receiver can observe any impacts
// at the sending miner actor.
// Note transparent serialization of single-element struct.
struct SectorContentChangedParams {
    // Distinct sectors with changed content.
    Sectors: []]SectorChanges,
}

// Description of changes to one sector's content.
struct SectorChanges {
    // Identifier of sector being updated.
    Sector: SectorNumber,
    // Minimum epoch until which the data is committed to the sector.
    // Note the sector may later be extended without necessarily another notification.
    MinimumCommitmentEpoch: ChainEpoch,
    // Information about some pieces added to (or retained in) the sector.
    // This may be only a subset of sector content.
    // Inclusion here does not mean the piece was definitely absent previously.
    // Exclusion here does not mean a piece has been removed since a prior notification.
    Added: []PieceChange,
}

// Description of a piece of data committed to a sector.
struct PieceChange {
    Data: Cid,
    Size: PaddedPieceSize,
    // A receiver-specific identifier.
    // E.g. an encoded deal ID which the provider claims this piece satisfies.
    Payload: []byte],
}

// For each piece in each sector, the notifee returns an exit code and
// (possibly-empty) result data.
// The miner actor will pass through results to its caller.
// Note transparent serialization of single-element struct.
struct SectorContentChangedReturn {
    // A result for each sector that was notified, in the same order.
    Sectors: []]SectorReturn,
}

// Note transparent serialization of single-element struct.
struct SectorReturn {
    // A result for each piece for the sector that was notified, in the same order.
    Added: []]PieceReturn,
}

struct PieceReturn {
    // Indicates whether the receiver accepted the notification.
    // The caller (miner) is free to ignore this, but may chose to abort and roll back.
    Code: ExitCode,
    // Receiver-specific result data about the piece, to be passed back to top level caller.
    Data: []byte,
}
```

#### Failure handling

Each batched sector activation or update comprises multiple sectors, each with multiple data pieces.
Each data piece can have a single verified claim and multiple notifications.
Any of these items might fail, but only limited ability to handle individual failures in a group is practical.

**The activation of each sector is independent**.
A failed activation will not cause the method to abort, unless all activations fail.
An SP can specify `RequireActivationSuccess=true` to instead require every sector activation to succeed,
aborting the operation if one fails.

**Sector activation includes claiming of any verified allocations**.
If a claim fails for one piece, no claims will be made for any piece in the sector and the sector will not be activated.
An SP cannot choose to have activation proceed despite an invalid claim;
they can instead resubmit the failed sector with only the remaining valid claims.

**Sector activation does not include notifications**.
Notifications are sent strictly _after_ activation, and only for successfully activated sectors.
If a notification call returns a non-zero exit code, sector activation will be committed regardless.
An SP can specify `RequireNotificationSuccess=true` to instead require every notification to succeed,
aborting the entire operation if one fails.
There is no ability to roll back the activation of only some sectors in response to failed notifications.

This is a change in sequencing and semantics from the existing onboarding methods flow,
where deal activation happens first and failure leads to an individual sector failing,
and verified claims happen second and must all succeed.

#### ProveCommitSector

The existing `ProveCommitSector` method (method 7) remains,
and continues to activate deals in the built-in market actor and claim verified allocations using
the current algorithm.
The method no longer writes deal IDs into per-sector chain state.

#### Deprecation of legacy methods

TODO:

- PreCommitSector
- PreCommitSectorBatch
- ProveReplicaUpdates2 (name taken by new method)

### Storage market actor

The built-in storage market actor retains all existing state and functionality,
but gains a new collection mapping provider addresses to sector numbers and deal IDs.
The per-deal state structure is extended to include the sector number in which the deal is stored,
thus providing a reverse mapping from deal ID to sector number.
It also implements the new `SectorContentChanged` method to activate deals in response to notifications
from the miner actor's new activation methods.

#### State

A new field maps sector numbers to the deal IDs that the market has been notified are stored in those sectors.

```
// New structure storing per-sector deal information.
struct SectorDeals {
    Deals: []DealID
}

// Existing deal state structure get a new field with sector number.
struct DealState {
    // All existing fields as today.
    // ...

    // 0 if not yet included in proven sector (0 is also a valid sector number)
    SectorNumber: SectorNumber,
}

struct State {
    // All existing state as today.
    // ...

    // Existing mapping of deal state by ID.
    // Since deal state now includes sector number, this gives deal->sector index.
    // AMT[DealID]DealState
	States: Cid 

    // New mapping of sector IDs to deal IDs, grouped by storage provider.
    // HAMT[Address]HAMT[SectorNumber]SectorDeals
    ProviderSectors: Cid 
}
```

#### ActivateDeals
When an SP activates a piece with the existing activation methods,
deals are activated with the `BatchActivateDeals` method.
This method returns the necessary verified allocation IDs to the miner actor.
The `BatchActivateDeals` method parameters are expanded to include the sector ID for each deal,
in order to update the new `ProviderSectors` mapping.

```
struct BatchActivateDealsParams {
    /// Deals to activate, grouped by sector.
    /// A failed deal activation will cause other deals in the same sector group to also fail,
    /// but allow other sectors to proceed.
    Sectors: []SectorDeals,
    /// Requests computation of an unsealed CID for each sector from the provided deals.
    ComputeCid: bool,
}

struct SectorDeals {
    SectorNumber: SectorNumber,
    SectorType: RegisteredSealProof,
    SectorExpiry: ChainEpoch,
    DealIDs: []DealID,
}
```

#### SectorContentChanged
When an SP activates a piece with the new onboarding methods,
any deals are activated by the `SectorContentChanged` method instead of ActivateDeals.

The implementation checks that the piece CID and size match the deal ID nominated in the notification topic, 
and considers the deal active if so. 
If piece fails to meet the conditions to activate a deal.

TODO: sketch algorithm


## Design Rationale

<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->
TODO:

- why requiring CommD at pre-commit
- why notifications are limited to built-in market
- moving sector-deal mapping to market
- implementing new sectorcontentchanged in market
- future: verified allocatino vouchers
- gas impacts

## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->

## TODO
- Determine whether we will migrate to remove SectorOnChainInfo.Deals, or merely deprecate its use.
- Determine whether to deprecate ProveReplicaUpdates2 (and claim its name for PRU3)

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
