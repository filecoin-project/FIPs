---
fip: <to be assigned>
title: Fix pre-commit deposit independent of sector content
author: Alex North (@anorth), Jakub Sztandera (@Kubuxu)
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
Expected reward depends on power, which in turn depends on the presence of verified deals hosted by the sector.

This proposal sets the pre-commit deposit to a value independent of sector content:
the estimated storage pledge of a sector with space-time that is exactly filled by verified deals.
This breaks coupling between storage power mechanics and the built-in (privileged) storage market actor, 
which is necessary as a prerequisite to a larger re-architecture supporting alternative deal markets on the FVM.
It also presents an opportunity to reduce deal-related gas costs.

## Change Motivation
Using the sector-specific storage pledge as PCD is inefficient and constrains the design space of APIs
for moving to a programmable storage and market architecture for the FVM.
The proposal at https://github.com/filecoin-project/FIPs/discussions/298 outlines an
architectural change to the built-in miner, market, and verified registry APIs which will 
support the deployment of alternative, equally-capable marketplace actors as user-programmed actors 
on the FVM by removing  the privileged place of the built-in storage market actor as a mediator of storage quality.

This proposal is a step towards that architecture, changing the sector onboarding process to:
- calculate a fixed PCD regardless of sector content, and
- commit to the sector's unsealed CID (aka CommD) at pre-commit time.

This will establish the pre-commit on-chain state schema matching that required by subsequent
removal of the market actor from the pre-commit flow entirely (simplifying future changes). 
It also presents an opportunity to resolve some redundant loading of deal metadata from state during prove-commit,
and so reduces the total gas consumed when onboarding sectors with deals.

This change also resolves a reduction in security buffers inadvertently introduced in 
[FIP-0019](./fip-0019.md) SnapDeals. 
The PCD should be calculated according to the expected reward of a sector, 
but when a committed-capacity sector is subsequently upgraded with verified deals, 
its reward increases from that for which its PCD was calculated.
There is sufficient buffer in the PCD calculation that no practical risk was introduced, 
but setting the PCD to a fixed value based on the _maximum_ reward a sector might earn restores that security buffer.   

The specific mechanism for implementing this change is driven by goals of:
- retaining the current exported API, to minimise integration/operational effort,
- retaining the current operator-friendly safety checks that prevent most instances of invalid deals
from costing a provider their pre-commit deposit.

Note that it would be possible to reduce gas costs even further by sacrificing the safety checks but,
since those gains will be realised anyway without sacrificing ergonomics by subsequent re-architecture, 
this proposal retains the checks (while still providing a net gas usage reduction).

The architecture for programmable markets on the FVM relies on this change to pre-commit deposit as a pre-requisite.
If the pre-commit deposit is not changed to be independent of content,
then further state and interactions would need to be added to compute the verified deal weight
during sector pre-commit.

## Specification
Calculate pre-commit deposit as the 20-day projection of expected reward earned by a sector with a 
sector quality of 10 (i.e. full of verified deals), _regardless of sector content_.
Leave the initial pledge value, due when the sector is proven, unchanged.

Change the `miner.SectorPreCommitOnChainInfo` structure to
- remove the `DealWeight` and `VerifiedDealWeight` fields, and
- add an `UnsealedCID` field.

During sector pre-commit change the call to `market.VerifyDealsForActivation` to 
- validate the deals, and
- compute and return each sector's unsealed CID, and
- no longer compute or return deal weight.

Store the unsealed CID in the `SectorPreCommitOnChainInfo`.
(This mechanism matches the future schema and flow of committing to the unsealed CID during pre-commit,
while retaining the ergonomic deal-validity checks, which will be removed later).

During sector prove-commit, remove the invocation to `market.ComputeDataCommitment`, 
and deprecate that method. The data commitment was calculated while validating deals during pre-commit.
This provides a net gas saving.

Change the parameters and return type of `market.ActivateDeals` to match the prior types of
`market.VerifyDealsForActivation`, so that the market actor returns the deal weights to the miner while
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
This proposal changes the behaviour of the built-in storage miner and storage market actors,
and so requires a network upgrade.

This proposal changes the schema of `miner.SectorPreCommitInfo`, and so requires a state migration
for in-flight pre-commits at the time of the upgrade.
This migration must calculate the unsealed CID for those sectors by loading the relevant deal proposals
in the same way that the new code will do so at sector pre-commit.

This proposal changes only APIs for inter-actor calls, not those invoked by top-level messages,
so APIs remain backwards compatible with existing external callers.

## Test Cases
To be provided with implementation.

## Security Considerations
The pre-commit deposit provides as a disincentive to providers to attempt to cheat proof of replication.
This proposal makes the pre-commit deposit for committed-capacity sectors larger than the current value,
which restores the buffers to security inadvertantly reduced in FIP-0019.
This deposit is still smaller than the sector initial pledge due at PoRep.

## Incentive Considerations
A larger pre-commit deposit increases the funds at risk in case a provider fails to follow through
with a sector commitment, such as in case of an operational failure.
If a provider expects failed pre-commitments of committed-capacity sectors to be a significant part of operational costs,
this proposal will increase that cost by up to a factor of 10.
This proposal retains ergonomic validity checks on deals at pre-commit in order to minimise the possibility
of operator error in specifying deals to result in loss of pre-commit deposit.

## Product Considerations
As noted above, this proposal slightly increases the amount of time that some funds are locked by the miner actor.
In practise, we expect most providers deposit at least the expected initial pledge value
up front when pre-commiting a sector, in which case this proposal requires no operational change.

## Implementation
Provided in Go in https://github.com/filecoin-project/specs-actors/pull/1575.

If this FIP is implemented after the FVM, we will port the changes to the Rust built-in actors.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
