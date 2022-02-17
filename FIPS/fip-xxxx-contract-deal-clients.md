---
fip: <to be assigned>
title: Support actors as storage market clients
author: Alex North (@anorth)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/271
status: Draft
type: Technical
category: Core
created: 2022-02-17
---

## Simple Summary
Extend the storage market actor to support deal proposal by clients without the need to submit a signed message.
This allows actors (which have no signing key) to act as deal clients.

## Abstract
The built-in storage market actor does not support other actors as deal clients.
When the FVM enables user-programmable actors, this would be a big limitation on their functionality.
This limitation arises from the market actor's requirement for a client signature on a deal proposal,
but only externally-owned accounts (EOAs) can make signatures.

This proposal adds new methods to the storage market actor for a client to propose a deal on-chain,
and then a provider to confirm that deal. This complements the existing one-step publishing of storage
deals that is suitable for EOAs.

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
    // TODO: consider structuring as HAMT[Address]AMT[abi.DealID]DealProposal,
    // indexing first by client address and then ID.
    // This could provide cheaper access if/when the collection becomes very large.
    Offers cid.Cid // AMT[abi.DealID]DealProposal
}
```

Offers are identified by integers in the same namespace as other deals, so that the identifier
remains constant across the phases of offer and acceptance by the storage provider.

### Methods

```go
 type OfferStorageDealsParams struct {
 	Deals []DealProposal
 }
type OfferStorageDealsReturn struct {
	IDs []abi.DealID // Parallel array of IDs for the proposals.
}

// Offers a set of storage deals from a client to specific providers.
// Each deal proposal must specify the client as the calling actor, but may specify different providers.
// Client collateral and payment are locked immediately; the call fails if 
// insufficient client funds are available for all offers.
// Fails if any of the proposals are internally invalid or expired.
// Fails if an identical proposal already exists as a pending proposal (submitted here or via PublishStorageDeals).
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
// Provider collateral is locked immediately; the call fails if insufficient provider funds are
// available to accept all offers that would otherwise succeed. 
func (Actor) AcceptStorageDeal(params *AcceptStorageDealsParams) *AcceptStorageDealsReturn {
    // Validate offers match the provider.
    // Transfers provider collateral from escrow to locked.
    // Removes proposals from state.Offers, adds to state.Proposals
    // CID remains in state.PendingProposals, and there's already a deal op scheduled.
}
```

### Offer expiration
This design uses the existing `state.DealOpsByEpoch` event queue to schedule clean-up of offers
that have passed their start epoch without being accepted by the provider.
The `CronTick` handler is changed so that if a deal ID is not found in `state.DealProposals`,
it also checks the `state.Offers` collection for an un-accepted offer.
If found, refund the client's pre-payment and remove the proposal from `state.Offers` and `state.PendingProposals`.

A client cannot retract an offer, but must wait for this expiration.

## Design Rationale
This proposal demonstrates a pattern of ad-hoc account abstraction, 
providing a means for an actor to do something without providing a signed message.
We will likely see this kind of pattern repeated in other actors until Filecoin offers
a first-class account abstraction primitive
(see discussion in [Ethereum](https://docs.ethhub.io/ethereum-roadmap/ethereum-2.0/account-abstraction/)).

### Partial failure
The client's call to offer deals always succeeds completely or fails. 
It never succeeds at making only some offers.
This route is chosen to provide the simplest UX to client contracts,
which can rely on the atomic operation for their own logic.
It is unfortunate that there is no mechanism to provide data to the caller about which offers failed, or why,
beyond the exit code. Implementations should consider using a variety of custom error codes.

The provider's call to accept deals can partially succeed.
The reasons for this are similar to the reasons partial success was added to `PublishStorageDeals`.
Publishing or accepting deals is often part of a complex sector commitment workflow that will
roll forward regardless of individual deal failures.

Calls always fail completely if insufficient collateral is available, so that the caller can
choose to either select some offers to make/accept, or top up collateral, to make progress.
Any offer selection policy implemented on-chain would be unsuitable to some providers,
or unnecessary complexity.

### Future extensions
This mechanism can be extended in the future to allow clients to authorize other addresses to
offer deals on their behalf (similar to Ethereum ERC-20/721 token authorizations).
This would change the behaviour but not the type signature of `OfferStorageDeals`.

A similar extension could be made to allow providers to nominate addresses to accept deals on their behalf.

This mechanism may be easily extended to support offers that do not specify a provider.
Such an offer would be available to any storage provider to accept (like a storage bounty).

## Backwards Compatibility
This proposal leaves all existing methods intact. 
Clients and storage providers that do not wish to use the new functionality need not make any changes.

This proposal changes the state schema for the storage market actor, and so requires migration as part of a network upgrade.

## Test Cases
To be provided during implementation.

## Security Considerations
### Offer spam
A call to `OfferStorageDeals` may be made by any address, and stores the offer in the market actor state.
It also schedules a clean-up item in the deal op event queue.
This could possibly be abused to spam offers and cause the chain to do lots of clean-up work in cron.
The existing `PublishStorageDeals` method has the same property.
In both cases, the caller must pay gas for the initial call, but the clean-up work is a cost to the network.
The clean-up work is distributed over a period of 100 epochs from the offer/deal's start epoch, 
so this cannot be used to target a specific epoch, but a 100-epoch-long period.
A very large number of offers expiring in the same period could increase block validation times for that period.
This problem arises because actors do not pay for the gas consumption of calls from the Cron actor.

Differences between `OfferStorageDeals` and `PublishStorageDeals` include:
- `PublishStorageDeals` can only be called by a miner actor (but these are trivial to create)
- `PublishStorageDeals` requires non-zero (but tiny) provider collateral to be posted, 
which is lost if the deal is not activated
- `OfferStorageDeals` is significantly cheaper in gas up front (much of the work is deferred to `AcceptStorageDeals`)

This proposal does not include a specific mitigation for this issue.
For both `OfferStorageDeals` and `PublishStorageDeals`, 
the gas cost of posting the offer/deal is far larger than the avoided cost of cleanup. 
That is, the client is paying _most_ of the cost anyway. 
This cost increases slightly the more offers/deals target the same expiration period.

Some mitigations considered but rejected:

**Constrain offer and deal start epochs to be
within a fixed epoch duration from the current epoch.** 
This would limit the amount of time during which an attacker could spam offers targeting a single
expiration window.
However, any such constraint that would be reasonable for deal clients and providers (say a week or more)
would not significantly constrain an attacker.

**Require the deal client to post collateral**, 
to be redeemed when the offer expires or is accepted. 
The client would never lose the collateral, but it would create opportunity cost.
This would be an unfortunate burden to place on legitimate deal clients.

**Add an explicit gas burn** when offering deals.
This would make calls more expensive, but would not address the amplification possible by 
targeting many offers to the same expiration period.
An attacker would not pay the implied high gas price during that overloaded period.

## Incentive Considerations
None.

## Product Considerations
The primary motivation for this proposal is the product benefit of supporting contracts acting as deal clients.

Non-contract deal clients can use these new methods too, if they wish. 
As compared with `PublishStorageDeals`, the `OfferStorageDeals` flow:
- involves the client to posting a message on chain, rather than sending it to the provider out of band;
- uses slightly more total gas, split between the client and the provider;
- is cheaper in gas for providers;
- uses significantly _less_ total gas if the client is a BLS address.

In both flows, an offer cannot be retracted by a client, and thus may be relied upon by the provider.

## Implementation
To be provided before "Final" status.

Implementation of this proposal will likely target the WASM actors running in the FVM.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
