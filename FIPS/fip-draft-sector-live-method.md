---
fip: "<to be assigned>" 
title: Export Sector Status to FEVM 
author: "@Kubuxu @lordshashank @ZenGround0"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1108
status: Draft
type: Technical (Core)
category: Core
created: 2025-11-26
spec-sections: 
  - System Actors (miner actor) 
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->

# FIP-Number: Export Sector Status  to FEVM

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->
We propose exporting a new method `validate_sector_status` from the builtin miner actor for creating user space FEVM smart contracts that can check the status of filecoin sectors, either live or dead, on chain.  An additional exported method `generate_sector_status_info` can be used in an offchain call to generate inputs to `validate_sector_status`.

Combined with the recent changes to ProveCommitSectors3 in FIP 109 allowing smart contract notifications upon sector commitent, this FIP establishes a minimally useful interface for a rich set of programmable storage applications.

Additionally this FIP proposes exposing a helper method `get_sector_expiration` which takes as input the output of `generate_sector_status_info`. It returns the expiration epoch for live sectors and fails for dead sectors.

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->
We propose exporting a new method `validate_sector_status` from the builtin miner actor for creating user space FEVM smart contracts that can check the status of filecoin sectors, either live or dead, on chain.  An additional exported method `generate_sector_status_info` can be used in an offchain call to generate inputs to `validate_sector_status`.

Combined with the recent changes to ProveCommitSectors3 in FIP 109 allowing smart contract notifications upon sector commitent, this FIP establishes a minimally useful interface for a rich set of programmable storage applications.

Additionally this FIP proposes exposing a helper method `get_sector_expiration` which takes as input the output of `generate_sector_status_info`. It returns the expiration epoch for live sectors and fails for dead sectors.


## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->

This FIP is motivated by efforts to experiment with programmable storage systems built with smart contracts.  It is essential to have the basic information of sector liveness to do anything interesting with sector storage.  Examples include custom storage payments, badbit insurance systems and markets for sector repair.

Sector expiration epoch information has also been identified by previous attempts to build smart contract secured storage systems.


## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->


## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->


## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->
This FIP only adds methods to the builtin miner actor.  No backwards compatiblity concerns need to be considered.

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->

* Test that when `generate_sector_status_info` is input sector number of a terminated sector that is compacted via `compact_partitions` is computed to have deadline, partition index (NO_DEADLINE, NO_PARTITION) without error
*
*
*


## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->
Adding view methods to the builtin miner actor does not have any implications for filecoin's L1 security model.

This FIP is ensuring a security model for FEVM user contracts.  It must be the case that 
1) all live sectors can be validated as live 
2) no sectors that are not live can be validated as live

These conditions are satisfied by the invariants governing the `sectors` and `terminated` bitfields in the miner actors `Partition` state object.  All live sectors satisfy:
a) sector number recorded in the `sectors` bitfield of some `Partition`
b) sector number NOT recorded in the `terminated` bitfield of the same `Partition`

Furthermore the separation of the search for the partition and deadline index into the offchain call `generate_sector_status_info` ensures that gas costs and miner state size have no impact on a user's ability to make this call.  Hence there is no provide practical denial of service to make the call and condition (1) is satisfied both in principle and in practice.


## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->
This FIP is not concerned with existing incentives.  This work can be used to create a foundation for new applications that rely on its security model to spend incentives productively.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->
The interface with the filecoin sector storage system was chosen to support the authors' concept of a minimally viable FEVM sector storage service.  Periodically checking liveness of a sector onchain is a simple way to create a storage system verified in user space.  And it is not too onerous on participating storage providers.

There has been some discussion of exposing finer grained sector status details, i.e. the unproven and faulty states. This would add complexity to the interface for limited benefit.  While exposing Filecoin internal states might be useful for power users wishing to essentially extend the core filecoin protocol in specific ways, i.e. add additional fault fees for certain sectors, this FIP is focused on user applications that can be served by a simpler model of filecoin storage.  By way of internal incentives and proofs filecoin sectors are considered live until they are terminated or expired.  Removing internal hints such as faults from the user's view creates a model that is easier to reason about and design against.

There has also been discussion on not inlcuding sector expiration information.  Expiration information has limitations in usefullness given that early termination can happen at any time and invalidate expiration.  However the cost is low and the interface is simple especially with a decoupled method specifically for retrieving expirations.

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->
WIP builtin actors PR here: https://github.com/filecoin-project/builtin-actors/pull/1707/files

## TODO
<!--A section that lists any unresolved issues or tasks that are part of the FIP proposal. Examples of these include performing benchmarking to know gas fees, validate claims made in the FIP once the final implementation is ready, etc. A FIP can only move to a “Last Call” status once all these items have been resolved.-->

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
