---
fip: "<to be assigned>" <!--keep the qoutes around the fip number, i.e: `fip: "0001"`-->
title: Improvements to the FVM randomness syscalls
author: Aayush Rajasekaran (@arajasek), Steven Allen (@stebalien)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/790, https://github.com/filecoin-project/FIPs/discussions/791
status: Draft
type: Technical (Core)
category (*only required for Standard Track): <Core>
created: <2023-28-28>
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->
This is the suggested template for new FIPs.

Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`.

The title should be 44 characters or less.

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->

- Actors/Contracts: Don't expect clients to "hash" randomness for you, do it yourself
- FVM: Don't impose any lookback limit on randomness, but charge proportional to the lookback amount

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->

Contracts can today request randomness from the FVM, which forwards the request to the client.
The client looks up the randomness from the chain (with no lookback limit), hashes it to "draw" the requested value, and returns it.
This FIP proposes:
1. moving the hashing operation out of the FVM/client, and into the calling actor
1. formalizing that no lookback limit is enforced on randomness fetching, and modifying the gas pricing to be based on a skiplist of length 20

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->

The fact that fetching randomness today isn't priced proportional to the lookback is a mild security concern. This isn't a major issue today since only trusted code (the builtin actors) can request unbounded randomness. However, we still want to fix this in order to more accurately charge for costs, and future-proof this operation against both changes to the builtin actors and "native" actors.

The motivation to push the hashing operation into user-space is that the FVM already has a syscall that supports hashing. As a result, the FVM doesn't need to be performing this hashing for the client, and we can allow users (actors) to "draw" their randomness as they please.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

### Hashing

We propose the following changes to the FVM syscalls:
- change get_chain_randomness from X to Y
- change get_beacon_randomness from X to Y
- something about $$$$

### Lookbacks

TODO: look at things like hashing costs, and make argument for why we can ignore it (or just include itL?)

We seek consensus amongst Core Devs that Filecoin clients are expected to be able to support chain walkbacks all the way to genesis, with a performance no _worse_ than that based on a skiplist of length 20. Clients are free to be more performant (eg. constant-time).
Clients can also be less performant, but the gas pricing would not be accurate for such clients.
We propose changing the gas costs of ELEMENT IN PRICELIST from X to Y.

## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->

The hashing change are designed to follow the principle of "anything that doesn't have to be done in the FVM shouldn't be done in the FVM". 
Following this principle makes it easier to version changes, avoids explicit specialized gas charges, and reduces the risk of critical security issues.

The gas changes for the lookback are designed to correctly price operations based on clients as they exist today, which is important for security. While we could simplify and reduce the cost to be a single constant, doing so requires changes in Filecoin clients that are not prioritized today.

## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

These changes are backwards incompatible, and require a network upgrade. Further, clients must: 
- modify their support of the FVM extern to no longer receive Domain Separation Tags and entropy as inputs, and no longer hash the returned value
- confirm their support for chain walkbacks is as good as requested by this FIP, or explicitly decide that they are okay being less performant than the system is priced for

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->
Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->
All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->
All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->
All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->
The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.

## TODO
<!--A section that lists any unresolved issues or tasks that are part of the FIP proposal. Examples of these include performing benchmarking to know gas fees, validate claims made in the FIP once the final implementation is ready, etc. A FIP can only move to a “Last Call” status once all these items have been resolved.-->
A section that lists any unresolved issues or tasks that are part of the FIP proposal. Examples of these include performing benchmarking to know gas fees, validate claims made in the FIP once the final implementation is ready, etc. A FIP can only move to a “Last Call” status once all these items have been resolved.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
