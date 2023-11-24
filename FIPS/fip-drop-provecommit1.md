---

fip: "<to be assigned>" <!--keep the qoutes around the fip number, i.e: `fip: "0001"`-->
title:  Deprecate  `ProveCommitSectors`  to Avoid Single PoRep Proof Verification in Cron 
author: Jennifer Wang (@jennijuju)
discussions-to: [<URL>](https://github.com/filecoin-project/FIPs/discussions/689)
status: Draft
type: Technical 
category (*only required for Standard Track): Core
created: 2023-09-03
requires (*optional):  [FIP-0076](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0076.md)

---

## Simple Summary

Deprecate *`ProveCommitSector` (method 7)* in favor of `ProveCommitSectors2` and `ProveCommitAggregate`. This change ensures that single PoRep validations and single sector activations are executed synchronously and billed to the caller, instead of being executed asynchronously via a cron call to the actor.

## Abstract

Currently, `ProveCommitSector` accepts a single PoRep proof for an individual sector, validates the proof, and activates the sector along with the deals inside it via a cron call to the power actor. In contrast, when submitting an aggregated PoRep with `ProveCommitAggregate`, all proof validation and sector activation are executed synchronously and the costs are billed to the caller. This creates an imbalance in the sector activation gas subsidy available to different onboarding methods, and also adds unnecessary work to unpaid network cron jobs.

To address this issue, we propose to deprecate the `ProveCommitSector` method after the network upgrade that includes the `ProveCommitSectors2` method, which is planned as part of [FIP-0076 - Direct Data Onboarding](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0076.md) and is expected to be in scope for upcoming network upgrades.

## Change Motivation

Since the FVM launch, all computations are properly charged and storage providers have started to realize that even below the batch balancer base fee threshold, the per sector commit cost via `ProveCommitAggregate` is higher than `ProveCommitSector`.

As @anorth laid out [here](https://github.com/filecoin-project/FIPs/discussions/689#discussioncomment-5680517):

> "We explicitly charge gas (discounted) for the single proof validation when it is submitted, so it’s both bounded and paid for. However, the **state updates associated with sector activation are not metered**, because they execute in cron. The execution cost of this activation varies significantly with the deal content of the sector, but the storage provider doesn’t pay gas for this. On the other hand, aggregated proof validation also activates the sector synchronously, for which the SP pays the gas cost. Thus, single-sector onboarding is subsidized relative to aggregation, but aggregation would otherwise efficiently support much higher onboarding rates.”

Thus, we would like to resolve the imbalance in sector activation and make proof aggregation financially sensible again.

This change also removes unnecessary yet expensive sector and deal activation work from the network cron, which prevents the network from potential cron blowup in the long term.

## Specification

Drop the `ProveCommitSector` function, https://github.com/filecoin-project/builtin-actors/blob/807630512ba0df9a2d41836f7591c3607ddb0d4f/actors/miner/src/lib.rs#L1775C17-L1828. 

## Design Rationale

There are other ways to achieve our goal, like modifying `ProveCommitSector` to activate sectors and deals asynchronously. However, the required protocol functionality can be achieved by other methods already, so deprecating the `ProveCommitSector` is the simplest way and also reduces the actor code that needs to be maintained.

## Backwards Compatibility

The deprecation of this method MUST happen after `ProveCommitSectors2` is available in the network and being adapted by the client.  

This proposal requires a network upgrade to deploy the new built-in actor code.

## Test Cases

Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.

Calling `ProveCommitSector` will fail with ***USR_UNHANDLED_MESSAGE.***

## Security Considerations

This FIP avoids single PoRep proof verification in cron, which reduces the free computations that are occupying the network bandwidth and the possibility of unexpected network performance issues.

## Incentive Considerations

This FIP will enforce storage activation fees to be paid by the callers rather than having an imbalanced network subsidy. This means storage providers who only onboard sectors via `ProveCommitSector` will start to pay for sector proof validation and sector/deal activation, which is a gas cost increase from ~71M to ~196M based on the current implementation. However, the activation cost is expected to be lower with the direct data onboarding flow via the `ProveCommitSectors2` method, and storage providers and their data clients may choose to opt-out of f05 deal activation, which would result in significantly less gas cost.

## Product Considerations

All features provided by Filecoin continue to function as expected.

## Implementation

The implementation involves dropping the [`ProveCommitSector` function](https://github.com/filecoin-project/builtin-actors/blob/807630512ba0df9a2d41836f7591c3607ddb0d4f/actors/miner/src/lib.rs#L1775C17-L1828). 

## TODO

<!--A section that lists any unresolved issues or tasks that are part of the FIP proposal. Examples of these include performing benchmarking to know gas fees, validate claims made in the FIP once the final implementation is ready, etc. A FIP can only move to a “Last Call” status once all these items have been resolved.-->

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
