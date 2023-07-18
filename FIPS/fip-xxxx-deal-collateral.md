---
fip: "<to be assigned>"
title: Declare the built-in market actor as optional
author: Alex North <@anorth>
discussions-to: https://github.com/filecoin-project/FIPs/discussions/719
status: Draft
type: Technical
category: Core
created: 2023-06-16
---

## Simple Summary
Declare that future protocol changes may commit non-zero data into sectors without requiring 
a corresponding deal in the built-in market actor.
Remove the built-in market actor's locked balances from the network circulating supply calculation.

## Abstract
A deal with the built-in storage market actor is currently the only permitted way for a storage provider to commit data into a sector.
The built-in market requires a minimum amount of provider deal collateral,
which thus functions as a network mandatory data assurance mechanism.
This minimum deal collateral amount currently equals about 0.4% of a sector's initial pledge,
or 3% of the sector termination penalty (for Filecoin Plus verified deals).
The built-in market actor is expensive in gas, and offers only basic functionality.
It cannot support the expansion in usage or functionality that network participants hope for. 

This proposal comprises two parts:
1. A decision that this data assurance penalty need not be a network-wide policy, 
    and that future protocol changes can allow storage providers to commit data into sectors without 
    a built-in storage market deal or the associated data collateral.
2. Removal of the built-in market's locked balance from the network circulating supply definition.

## Change Motivation
A built-in market actor deal is the only mechanism today by which storage providers (SPs) can commit data to sectors.
This is both quite expensive, and limits their utility and value.
More efficient and flexible storage functionality could be implemented in smart contracts
if they were not constrained by the built-in market actor.

Because the built-in market deal is a required intermediary, its minimum deal collateral constitutes a network policy for all data.
Making the built-in market optional implies making this deal collateral optional at a network level.
This proposal is to explicitly accept that optionality rather than either
continue to require the built-in storage market as an intermediary for all data onboarding,
or implement a similar data termination penalty in the built-in miner actor, where it would apply to all data.
The primary motivation for this decision is simplicity:
the deal collateral is only a very small part of the penalty charged by the network when a sector is terminated early,
and an even smaller part of the network's locked tokens.
It's not worth the effort to implement a replacement.

As the built-in market becomes considered optional, it doesn't make sense to explicitly account for 
the locked balances it holds in the calculation of the network's circulating supply.
The built-in market may represent only a small fraction of data commitments in the future.
Other storage application contracts may represent much more, yet their balances will be excluded from the calculation.
The motivation is again simplicity:
the built-in market's balances represent only a small fraction of locked tokens,
and the protocol will be simpler if they are ignored.

## Specification

### 1. The built-in market actor is optional
This item requires no technical change to the protocol.
It is a decision to be made in preparation for future changes that add mechanisms to commit data into sectors
without a built-in market deal.

This item is specified in order to be cited by subsequent FIPs that specify such changes.

### 2. Remove built-in market balances from the network circulating supply calculation

The network circulating supply is currently specified as

```
CirculatingSupply = Vested + Mined - Burnt - Locked
  where
Locked = PledgeCollateral + ProviderDealCollateral + ClientDealCollateral + PendingDealPayment 
```

The calculation of `Locked` is changed to account only for pledge collateral (initial pledge plus vesting rewards):
```
Locked = PledgeCollateral
```

## Design Rationale
### 1. The built-in market actor is optional
The built-in market actor constrains the data that storage providers (SPs) can store in sectors, limiting their utility and value.
It supports only a single, simple deal schema and policies, and does not support a range of desirable market features.
The built-in market actor is also expensive to use.
Publishing deals is the largest on-chain cost of QA power onboarding, 
and currently consumes a large fraction of total chain bandwidth (44% of all gas used over the 30 days to 2023-07-18).
Much of this cost is unnecessary in the case of simple verified deals with no client payment,
because the verified registry actor already records information describing the datacap allocation.
The built-in market plays no necessary role in allocating or accounting for QA power.

As an alternative to declaring the built-in market optional, protocol designers could invest in it long term,
implementing a wide range of flexible functionality in the network core, and optimising to reduce costs (these goals will often conflict).
This path would be expensive and slow, being subject to prudent conservatism and network governance processes.

Instead, this proposal prepares for such innovation to occur in user-programmed smart contracts.
This decision is a pre-requisite to future changes to provide the technical means for storage providers to commit
data into sectors on the terms of some other smart contract, unconstrained by the built-in market's functionality or cost.
One immediate possibility will be support for onboarding Filecoin Plus verified data at a fraction of the current gas costs,
without any smart-contract intermediary.

Another alternative would be to implement an equivalent data termination penalty in the built-in miner actor,
where it would apply to all data.
This is rejected because the collateral for a verified deal only amounts to about 3% of the termination penalty
that is also charged when a sector is prematurely terminated.
The amount is too small to make a significant difference to SP incentives.
Thus, it does not seem worth the effort to retain such a small change in penalty.
Smart contracts can implement application-appropriate data assurance mechanisms, 
and in particular the built-in market will continue to require a minimum provider deal collateral when it is used.
A data termination penalty could easily be implemented at the miner actor in the future if desired.

For deals that are not FIL+ verified (a tiny minority today), the impact of allowing data commitments without deal collateral is 10x larger,
relative to block rewards, because the deal collateral calculation does not account for QA power.
This is a disproportionate cost/disincentive to storing data for clients that have not undergone Filecoin Plus allocation processes,
which raises the amount that SPs must charge those clients in order to break even on storage services.
A further motivation for this proposal is to remove this disproportionate cost in relation to block rewards for alternative storage applications.

### 2. Remove built-in market balances from the network circulating supply calculation
Given its cost and limitations, it is unlikely that the built-in market actor will account for 
a large share of the network's data commitments in the future, if made optional.
In this case, there is little justification for including its balances in the network circulating supply calculation,
as its impact on that calculation will decrease from today's already-trivial level to almost nothing.
We can simplify the network's specification and implementation by removing them.

As of epoch 2911690, the built-in market's locked balances are:
- TotalClientLockedCollateral: 0 FIL
- TotalProviderLockedCollateral: 317,498 FIL
- TotalClientStorageFee: 38 FIL

This amounts to 0.21% of the total locked amount (150,981,531 FIL), 
and 0.067% of the circulating supply (473,321,502 FIL)

Removing them from the calculation will thus have negligible effect on downstream calculations 
such as the sector initial pledge requirement.

Removing these balances from the calculation of network circulating supply will not actually unlock any tokens,
it will only add them to the collection of tokens that are locked in ways that the network core does not account for.

## Backwards Compatibility
Item 2 of this proposal changes the calculation of the network's circulating supply, which forms part of the consensus rules.
It thus requires a coordinated network upgrade.

No on-chain interfaces or state are altered.

## Test Cases
The only relevant test is that the circulating supply calculation excludes balances locked in the built-in market actor.

## Security Considerations
None.

## Incentive Considerations
This proposal will increase the calculated circulating supply by approximately 320,000 FIL (0.067%, or ~7/10,000).
This will in turn increase the sector initial pledge requirement by a slightly smaller fraction.
This is considered inconsequential.

This proposal does not change any incentives associated with accepting or completing a deal with the built-in storage market actor,
but does imply that the minimum network penalty for early termination of a sector with data arranged by some other,
future mechanism, will be reduced by about 3%.

## Product Considerations
The product considerations of the unnecessary costs of onboarding data, and the inflexibility of requiring built-in market deals,
are the primary motivations for this proposal.

This proposal, or some alternative, is a prerequisite to support for clients and providers arranging
Filecoin Plus storage directly with the verified registry actor (at a significant cost reduction),
and to support for smart contract data applications that can avoid the costs and limitations associated with
mandatory use of the built-in market actor.

The built-in market actor will continue to require minimum deal collateral, so in the near term all deals will as well.
Participants and developers will need to explicitly alter their arrangements should they wish to make 
arrangements that uses a lesser amount.

## Implementation
TBA.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
