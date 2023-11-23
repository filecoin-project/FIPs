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

<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->

Deprecate *`ProveCommitSectors` (method 7)* in favour of `ProveCommitSectors2` and `ProveCommitAggregate` to enforce single PoRep validations and single sector activations are synchronously executed and billed to the caller, rather than executed asynchronously via a cron call to the actori.

## Abstract

<!--A short (~200 word) description of the technical issue being addressed.-->
A short (~200 word) description of the technical issue being addressed.

Currently, `ProveCommitSectors` takes single PoRep proof for individual sectors, validates the proof and activate the sectors along with the deals inside of the sectors via a cron call to the power actor. By contrast, when submitting an aggregated PoRep, all of the proof validation and sector activation are executed synchronously and billed to the caller. We want to resolve this imbalance in the improper sector activation gas subsidy available to the different onboarding methods, and also removes unnecessary work from unpaid network cron jobs.

To address this issue, we propose to drop `ProveCommitSectors` method after the upgrade that introduces `ProveComitSectors2` ’s inclusion.

## Change Motivation

<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->

Since FVM launch, all computation are properly charged and storage providers started to realize that even below the batch balancer base fee threshold, per sector commit cost via  `ProveCommitAggregate`  is still much higher than `ProveCommitSectors` .

As @anorth laid out [here](https://github.com/filecoin-project/FIPs/discussions/689#discussioncomment-5680517),”We explicitly charge gas (discounted) for the single proof validation when it is submitted, so it’s both bounded and paid for. However, the **state updates associated with sector activation are not metered**, because they execute in cron. The execution cost of this activation varies significantly with the deal content of the sector, but the storage provider doesn’t pay gas for this. On the other hand, aggregated proof validation also activates the sector synchronously, for which the SP pays the gas cost. Thus single-sector onboarding is subsidised relative to aggregation, but aggregation would otherwise efficiently support much higher onboarding rates.”

Thus, we would like to resolve the imbalance in the sector activation and make proof aggregation financially make sense again.

This change also removes unnecessary yet expensive sector and deal activation work out of the network cron, in which prevent the network from potential cron blowup in the long term. 

## Specification

<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

Drop `ProveCommitSectors` function, https://github.com/filecoin-project/builtin-actors/blob/807630512ba0df9a2d41836f7591c3607ddb0d4f/actors/miner/src/lib.rs#L1775C17-L1828. 

## Design Rationale

<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->

There are other ways to achieve our goal, like modify `ProveCommitSectors` to active sectors and deals asynchronously. However, the required protocol functionality can be achieved by other methods already, so deprecating the `ProveCommitSectors` is the simplest way and also reduce the actor code needs to be maintained.

## Backwards Compatibility

<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

The deprecation of this method MUST happen after `ProveCommitSectors2` is available in the network and being adapted by the client.  

This proposal requires a network upgrade to deploy the new built-in actor code.****

## Test Cases

<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->
Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.

Calling `ProveCommitSectors` will fail with ***USR_UNHANDLED_MESSAGE.***

## Security Considerations

<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->

This FIP avoids single PoRep proof verification in cron, which reduces the free computations that occupying the network bandwidth  and the possibility of unexpected network performance issue.  

## Incentive Considerations

<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->

This FIP will enforce storage activation fees to be paid by the callers rather than having imbalanced network subsidy. This means storage providers who only onboard sectors via `ProveCommitSectors` will start to pay for sector proof validation and sector/deal activation, which is a gas cost increase from ~71M to ~196M based on the current implementation. However, the activation cost is expected to be lower with the direct data onboarding flow via `ProveCommitSectors2` method, and storage providers and their data clients may chose to opt-out f05 deal activation, which also means way less gas usage.

## Product Considerations

<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->

All functionalities of Filecoin remains with this change. 

## Implementation

<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->
The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.

Drop `ProveCommitSectors` function, https://github.com/filecoin-project/builtin-actors/blob/807630512ba0df9a2d41836f7591c3607ddb0d4f/actors/miner/src/lib.rs#L1775C17-L1828. 

## TODO

<!--A section that lists any unresolved issues or tasks that are part of the FIP proposal. Examples of these include performing benchmarking to know gas fees, validate claims made in the FIP once the final implementation is ready, etc. A FIP can only move to a “Last Call” status once all these items have been resolved.-->

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
