---
fip: "<to be assigned>"
title: Exclude built-in market balances from circulating supply calculation
author: Alex North <@anorth>
discussions-to: https://github.com/filecoin-project/FIPs/discussions/719
status: Draft
type: Technical
category: Core
created: 2023-06-16
---

## Simple Summary
Exclude the built-in market actor's locked balances from the network circulating supply calculation,
in preparation for direct commitment of data into sectors without a corresponding built-in market deal.

## Abstract
A deal with the built-in storage market actor is currently the only permitted way for a storage provider to commit data into a sector.
The built-in market requires a minimum amount of provider deal collateral,
which thus functions as a network mandatory data assurance mechanism.
The minimum deal collateral amounts are tiny compared to the sector's initial pledge or termination penalty, 
so have minimal impact on network security or data assurance.
The market's collateral and deal payment balances are subtracted from the network circulating supply calculation.
The built-in market actor is expensive in gas, and offers only basic functionality.
It cannot support the expansion in usage or functionality that network participants hope for,
and may eventually be replaced by superior user-programmed actors.

This proposal is to exclude the built-in market's locked balance from the network circulating supply definition.
This is logical support for subsequent protocol changes that would allow storage providers to 
commit data into sectors without a built-in market deal or the associated collateral.
With such change, the built-in market would not be a privileged actor and does not warrant special treatment
in the circulating supply calculations.

## Change Motivation
A built-in market actor deal is the only mechanism today by which storage providers (SPs) can commit data to sectors.
This is both quite expensive, and limits their utility and value.
Work is in progress to permit SPs to commit data directly into sectors without a built-in market deal,
upon which more efficient and flexible storage functionality could be implemented in smart contracts.
This proposal is preparation for such changes, after which the built-in market actor would no longer occupy
a privileged position as a required intermediary.

The built-in market's minimum deal collateral amount currently equals about 0.4% of a sector's initial pledge,
or 3% of the sector termination penalty (for Filecoin Plus verified deals).

The primary motivation for this proposal is simplicity:
the built-in market's deal collateral is only a very small part of the penalty charged by the network when a sector is terminated early,
and an even smaller part of the network's locked tokens.
It has trivial impact on network security or data assurance.
It is not justified to treat as a special case in the circulating supply calculation,
especially as the built-in market may represent only a small fraction of data commitments in the future.
Other storage application contracts may represent much more, yet their balances would be excluded from the calculation.
The built-in market's balances represent a small and likely decreasing fraction of locked tokens,
and the protocol will be simpler if they are ignored.

## Specification
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
### Preparation for direct data commitments without built-in market deals
The built-in market actor constrains the data that storage providers (SPs) can store in sectors, limiting their utility and value.
It supports only a single, simple deal schema and policies, and does not support a range of desirable market features.
The built-in market actor is also expensive to use.
Publishing deals is the largest on-chain cost of QA power onboarding, 
and currently consumes a large fraction of total chain bandwidth (44% of all gas used over the 30 days to 2023-07-18).
Much of this cost is unnecessary in the case of simple verified deals with no client payment,
because the verified registry actor already records information describing the datacap allocation.
The built-in market plays no necessary role in allocating or accounting for QA power.
The cost is also unnecessary in the case of (future) deals with a user-programmed actor intermediary,
which could subsume and extend the functionality of the built-in market.

As an alternative to supporting direct data commitments, protocol designers could invest in the built-in market actor long term,
implementing a wide range of flexible functionality in the network core, and optimising to reduce costs (these goals will often conflict).
This path would be expensive and slow, being subject to prudent conservatism and network governance processes.
Instead, this proposal prepares for such innovation to occur in user-programmed smart contracts,
unconstrained by the built-in market's functionality or cost.

One option to retain mandatory data assurance independently of the built-in market actor would be 
to implement an equivalent data termination penalty in the built-in miner actor, where it would apply to all data.
This is rejected because the collateral for a verified deal only amounts to about 3% of the termination penalty
that is also charged when a FIL+ verified sector is prematurely terminated.
The amount is too small to make a significant difference to SP incentives.
Thus, it does not seem worth the effort to retain such a small change in penalty.
Smart contracts can implement application-appropriate data assurance mechanisms, 
and in particular the built-in market will continue to require a minimum provider deal collateral when it is used.
A network-wide data termination penalty could be implemented at the miner actor in the future if desired.

For deals that are not FIL+ verified (a tiny minority today), the impact of allowing data commitments without deal collateral is 10x larger,
relative to block rewards, because the deal collateral calculation does not account for QA power.
This is a disproportionate cost/disincentive to storing data for clients that have not undergone Filecoin Plus allocation processes,
which raises the amount that SPs must charge those clients in order to break even on storage services.
A further motivation for direct data commitments is to remove this disproportionate cost in relation to block rewards for alternative storage applications.

### Remove built-in market balances from the network circulating supply calculation
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
This proposal changes the calculation of the network's circulating supply, which forms part of the consensus rules.
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
but does imply that the minimum network penalty for early termination of a sector with data committed directly will be reduced by about 3%.

## Product Considerations
The product considerations of the unnecessary costs of onboarding data, and the inflexibility of requiring built-in market deals,
are the primary motivations for this proposal.

This proposal, or some alternative, is logical preparation for clients and providers arranging
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
