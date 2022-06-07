---
fip: FIP-0035
title: Support actors as built-in storage market clients
author: Alex North (@anorth)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/271
status: Draft
type: Technical
category: Core
created: 2022-02-17
---

## Simple Summary
Extend the built-in storage market actor to support deal proposal by clients 
without the need to submit a signed message.
This allows non-account actors (which have no signing key) to act as deal clients.

## Abstract
The built-in storage market actor does not support other actors as deal clients.
When the FVM enables user-programmable actors, this would be a big limitation on their functionality.
This limitation arises from the market actor's requirement for a client signature on a deal proposal,
but only externally-owned accounts can make signatures.

This proposal adds new methods to the storage market actor for a client to propose a deal on-chain,
and then a provider to confirm that deal. This complements the existing one-step publishing of storage
deals that is suitable for externally-owned accounts.

## Change Motivation
Interacting with storage markets is likely to be a significant use case for FVM actors.
Examples of contracts that might act as deal clients include actors representing a group (multisig), 
more complex DAOs, decentralised replication/repair services, 
or brokering actors such as auction or bounty contracts built on top of the built-in market.

Without making a change like this, storage deals will remain restricted to external account owners, 
which is a significant barrier to automation and trust-minimised systems.

## Specification
Add new state and methods to the built-in storage market actor.

The existing code already uses the term "proposals" to describe the collection of deals
that both parties have already committed to,
and "pending" to describe any deal that has not yet completed.
To avoid confusion, the on-chain proposals are termed "offers".

### State
```go
type State struct {
    // Existing state remains as-is.
    
    // Offers by clients for specific deal terms, not yet accepted by the provider.
    // The first key is the client actor ID.
    // Offers are grouped by client so the client bears costs of traversing the 
    // deals collection if it gets large.
    Offers cid.Cid // HAMT[ActorID]HAMT[abi.DealID]DealProposal
}
```

Offers are identified by integers in the same namespace as other deals, so that the identifier
remains constant across the phases of offer and acceptance by the storage provider.

### Methods

```go
 type OfferStorageDealsParams struct {
 	Offers []DealProposal
 	AllowPartialSuccess bool
 }
type OfferStorageDealsReturn struct {
	Success []bool // Array of success indicators, parallel to parameters
	IDs []abi.DealID // Array of IDs for the proposals, parallel to parameters
}

// Offers a set of storage deals from a client to specific providers.
// Each proposal offered must specify the client as the calling actor, but may specify different providers.
// A proposal fails if it is internally invalid or expired.
// A proposal fails if an identical proposal already exists as a pending proposal (submitted here or via PublishStorageDeals).
// The call aborts if AllowPartialSuccess is false and any proposal is invalid.
// Client collateral and payment are locked immediately; the call aborts if 
// insufficient client funds are available for all otherwise-valid offers.
func (Actor) OfferStorageDeals(params *OfferStorageDealsParams) *OfferStorageDealsReturn {
    // Validate proposals.
    // Allocates IDs by incrementing state.NextID.
    // Transfers client collateral and prepayment from escrow to locked.
    // Deducts data cap for verified deals.
    // Records each proposal in state.Offers.
    // Records the CID of each proposal in state.PendingProposals.
    // Schedules a deal op for the deal start epoch (for expiration), with jitter.
}

type AcceptStorageDealsParams struct {
    DealIDs []abi.DealID
}
type AcceptStorageDealsReturn struct {
    Accepted []abi.DealID
    Failed []abi.DealID
}

// Accepts a set of storage deals by a provider, committing both parties.
// Each ID must reference a proposal currently offered and specifying as the provider a 
// miner actor for which the caller is the owner, worker, or control address.
// All offers must specify the same provider.
// Offers that specify a different provider or have already expired fail individually.
// Provider collateral is locked immediately; the call aborts if insufficient provider funds are
// available to accept all offers that would otherwise succeed. 
func (Actor) AcceptStorageDeal(params *AcceptStorageDealsParams) *AcceptStorageDealsReturn {
    // Validate offers match the provider.
    // Transfers provider collateral from escrow to locked.
    // Removes proposals from state.Offers, adds to state.Proposals
    // CID remains in state.PendingProposals, and there's already a deal op scheduled.
}

type CleanupOffersParams struct {
    Client ActorID
    Offers Bitfield
}
type CleanupOffersReturn struct {
}

// Deletes offers for a client that have passed their start epoch without being accepted by the provider.
// If the `Offers` bitfield is not empty, loads only proposals with IDs specified by that parameter.
// If `Offers` is empty, loads all proposals for the client.
// A proposal that is loaded but not yet expired is left intact.
// Cleaning up expired offers will reduce the gas cost of future operations by the client.
func (Actor) CleanupOffers(params *CleanupOffersParams) *CleanupOffersReturn {
    // If offers is not empty, load each proposal specified by it in turn, and remove if expired.
    // If offers is empty, traverse the full collection.
}
```

A client cannot retract an offer, but must wait for its start epoch to pass.

## Design Rationale
This proposal demonstrates a pattern of ad-hoc account abstraction, 
providing a means for an actor to do something without providing a signed message.
We will likely see this kind of pattern repeated in other actors until Filecoin offers
a first-class account abstraction primitive.

An alternative to this proposal is implementing account abstraction, 
and then altering the built-in market actor to delegate signature checking to the client actor.

### Partial failure
The client can choose whether to offer a collection of deals atomically, or allow only some offers
to succeed.
This route is chosen to provide flexibility to client contracts.

The provider's call to accept deals can partially succeed.
The reasons for this are similar to the reasons partial success was added to `PublishStorageDeals`.
Publishing or accepting deals is often part of a complex sector commitment workflow that will
roll forward regardless of individual deal failures.

Calls always fail completely if insufficient collateral is available, so that the caller can
choose to either select some offers to make/accept or to top up collateral to make progress.
Any offer selection policy implemented on-chain would be unsuitable to some providers,
or unnecessary complexity.

### Future extensions
This mechanism can be extended in the future to allow clients to authorize other addresses to
offer deals on their behalf (similar to Ethereum ERC-20/721 token authorizations).
This would change the behaviour but not the type signature of `OfferStorageDeals`.
(First-class account abstraction primitives would make such an extension unnecessary).

A similar extension could be made to allow providers to nominate addresses to accept deals on their behalf.

This mechanism may be easily extended to support offers that do not specify a provider.
Such an offer would be available to any storage provider to accept (like a storage bounty).

## Backwards Compatibility
This proposal leaves all existing methods intact. 
Clients and storage providers that do not wish to use the new functionality need not make any changes.

This proposal changes the state schema for the storage market actor, 
and so requires migration as part of a network upgrade.

## Test Cases
To be provided during implementation.

## Security Considerations
None.

## Incentive Considerations
None.

## Product Considerations
The primary motivation for this proposal is the product benefit of supporting contracts acting as deal clients.

Non-contract deal clients can use these new methods too, if they wish. 
As compared with `PublishStorageDeals`, the `OfferStorageDeals` flow:
- involves the client to posting a message on chain, rather than sending it to the provider out of band;
- uses slightly more total gas, split between the client and the provider, 
rather than provider paying all gas fees;
- is cheaper in gas for providers;
- uses significantly _less_ total gas if the client is a BLS address.

In both flows, an offer cannot be retracted by a client, and thus may be relied upon by the provider.

## Implementation
To be provided before "Final" status.

Implementation of this proposal will likely target the WASM actors running in the FVM.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
