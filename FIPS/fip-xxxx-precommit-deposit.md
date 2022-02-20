---
fip: <to be assigned>
title: Fix pre-commit deposit independent of sector content
author: Alex North (@anorth)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/290
status: Draft
type: Technical
category: Core
created: 2022-0218
---

## Simple Summary
Set the pre-commit deposit to a fixed value regardless of sector content.

## Abstract
The sector pre-commit deposit (PCD) is currently set equal to an estimate of the _storage pledge_ for a sector.
The storage pledge is a 20-day projection of the expected reward to be earned by the sector.
This reward depends on power, which depends on the presence of verified deals hosted by the sector.
This dependency means the miner actor must consult the market actor, which intermediates verified data cap,
to determine the pre-commit deposit (and then again to compute initial pledge when the sector is proven).

This proposal sets the pre-commit deposit to a value independent of sector content:
the estimated storage pledge of a sector with space-time that is exactly filled by verified deals.

## Change Motivation
Using the storage pledge as PCD is inefficient and constrains the design space of APIs for
moving to a programmable storage and market architecture for the FVM.
- The PCD calculation requires the loading of deal metadata to compute deal weight (for sectors with deals).
This is somewhat expensive.
This data load and computation is mostly repeated at prove-commit in order to activate deals and calculate initial pledge.
- The PCD calculation requires a sectors deal's to be specified at pre-commit, 
and the deal IDs and weights to be memoized for subsequent prove-commit.
- This only works today because the market actor is a trusted network built-in. 
This pattern cannot work for user-programmed storage markets, 
because they cannot be trusted to calculate deal weight.
As we decouple the accounting for verified data cap from the built-in market,
these interactions must change anyway.

Refer to the proposal at https://github.com/filecoin-project/FIPs/discussions/298 for an
example architectural change to the built-in miner, market, and verified registry APIs to support
programmable storage markets on the FVM.
That proposal relies on this change to pre-commit deposit as a pre-requisite.
If the pre-commit deposit is not changed to be independent of content,
then further state and interactions would need to be added to compute the verified deal weight 
during sector pre-commit.

## Specification
Calculate pre-commit deposit as the 20-day projection of expected reward earned by a sector with a 
sector quality of 10 (i.e. full of verified deals), _regardless of sector content_.
Leave the initial pledge value, due when the sector is proven, unchanged.

Remove the call to `market.VerifyDealsForActivation` during sector pre-commit, 
and deprecate that method from the market actor.

Change the parameters and return type of `market.ActivateDeals` to match those of the deprecated
`market.VerifyDealsForActivation`, so that the market actors returns the deal weights to the miner while
activating deals (and also [supports batching](https://github.com/filecoin-project/specs-actors/issues/474)).

## Design Rationale
This value for the pre-commit deposit is simple to calculate, 
and is always less than the value due for the sector's initial pledge.
This means that the provider will have to lock at least this much anyway by the time the sector is proven.
Since the window between pre-commit and prove-commit is only just over 1 day,
this represents a very small additional opportunity cost of locked funds for the provider.

As of January 2022, the calculations are roughly:
```
EpochReward := 22.54 * 5 = 112.25
NetworkPower := 16.0954 * 10^9
CirculatingSupply := 229 * 10^6

// Sector quality = 1
StoragePledge := 0.0128
ConsensusPledge := 0.1365
PreCommitDeposit := StoragePledge = 0.0128
InitialPledge := StoragePledge + ConsensusPledge = 0.1494

// Sector quality = 10 (values are appox 10x greater)
StoragePledge := 0.1285
ConsensusPledge := 1.3658
PreCommitDeposit := StoragePledge = 0.1285
InitialPledge := StoragePledge + ConsensusPledge = 1.4944
```

Note that the pre-commit deposit for sector quality = 10 is less than (86% of) the initial pledge
for a sector with quality = 1, so PCD is always less than initial pledge.

This relationship depends on the consensus pledge (a function of the circulating money supply)
being much larger than the storage pledge (a function of per-sector expected rewards).
We expect this relationship to continue to hold, as
(1) the money supply is expands over time with long-term vesting and emissions, and
(2) the expected reward per sector falls over time with growth in network capacity and decaying block reward.

## Backwards Compatibility
This proposal changes the behaviour and APIs of the built-in storage miner and storage market actors,
and so requires a network upgrade.

This proposal does not change any state, so does not require any state migration.

The market actor's `VerifyDealsForActivation` call is deprecated, but may be removed in a subsequent upgrade.
Implementations should consider adding replacement read-only methods to query and validate pending deals
for use by clients and smart contracts on the FVM.

The `DealWeight` and `VerifiedDealWeight` fields in the `miner.SectorPreCommitOnChainInfo`
become redundant. This proposal is only to set them to zero; they may be removed in a future state migration.

## Test Cases
To be provided with implementation.

## Security Considerations
The pre-commit deposit provides as a disincentive to providers to attempt to cheat proof of replication.
This proposal makes the pre-commit deposit for committed-capacity sectors larger than the prior value,
thus providing even more disincentive than necessary.
This deposit is still smaller than the sector initial pledge due at PoRep.

## Incentive Considerations
A larger pre-commit deposit increases the funds at risk in case a provider fails to follow through
with a sector commitment, such as in case of an operational failure.
If a provider expects failed pre-commitments of committed-capacity sectors to be a significant part of operational costs,
this proposal will increase that cost by up to a factor of 10.

Deferring deal weight calculation to PoRep will slightly reduce the gas cost of pre-committing a sector
that specifies deals, bringing it on par with committed-capacity sectors.

These two changes both make committing deals into a sector during PoRep incrementally more attractive,
than introducing them later with a replica update ("snap deal").

## Product Considerations
As noted above, this proposal slightly increases the amount of time that some funds are locked by the miner actor.
In practise, we expect most providers deposit at least the expected initial pledge value
up front when pre-commiting a sector, in which case this proposal requires no operational change.

## Implementation
To be provided.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
