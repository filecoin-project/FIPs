---
fip: <to be assigned>
title: Rebalance Gas Charges 1
author: Jakub Sztandera (@Kubuxu)
discussions-to: https://github.com/filecoin-project/FIPs/issues/31
status: Draft
type: Core
category Core
created: 2020-11-11
spec-sections: 
  - n/a
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.
This is the suggested template for new FIPs.

Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`.

The title should be 44 characters or less.-->

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->
Rebalance gas charges for proof verifications and storage due to changes in software and network itself.

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->
Decrease amount of gas charged for PoSt Verification and increase gas charged for storage based operations.
This will reduce the gas consumption of SubmitWindowPoSt and result in a small increase of gas used by other methods.

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->
Gas is mechanism that governs chain bandwidth and base fee. We are trying to maintain close relation
between resources used by on chain operations and their gas prices.

Given optimizations done for proofs verification and real-world price of the SubmitWindowPoSt,
decreasing its gas price is the correct step.

The size and growth rate of the Filecoin state tree is causing few issues. To better represent its effect,
increase the gas price of on chain storage and the gas price of accessing this storage.
This will hopefully guide future development by reducing storage footprint.



The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

Costs of following Syscall gas changes change:

| Call Name | Old Gas | New Gas | Change |
|---|---|---|---|
|OnVerifyPostBase|374296768 *|117680921|-68%|
|OnVerifyPostPerSector|42819 *|43780|+2%|
|OnIpldGet|75242|114617|+52%|
|OnIpldPutBase|84070|353640| +320%|

\* - OnVerifyPost currently has arbitrary 2x discount applied, Old Gas numbers are including this discount, New Gas do not

`StorageGasMultiplier` which governs gas cost of byte of storage changes from `1000` to `1300`.

## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->

There are few issues this FIP addresses:
	- Storage access cost is too low based on real world performance.
	- On chain storage per byte is under-priced. Size of the state tree grows too fast.
	- WindowPoSt is too expensive.

The first point is addressed by balancing OnIpldGet and OnIpldPutBase to correspond to 10gas/ns of execution on benchmark hardware. 
The significant increase in OnIpldPutBase is due to previous omission of time needed to flush data to disk, which now is counted in.

The on chain storage is addressed by 30% increase in the per byte price. It is large enough change to
guide future development and increase the attractiveness of performing actions like compacting AllocatedSectors bitfield.
The increase cannot be too large to cause issues before rest of the system can adapt.
The 30% increase was choose as a medium sized step toward correct cost of on chain storage when weighting above factors.

Proofs verification was optimized reducing the runtime of these routines by close to 84%.
The gas cost is adjusted to include these optimizations. The arbitrary 2x discount for PoSt verification is disabled resulting in net reduction of 68% in the flat cost of OnVerifyPost and small change in the per sector cost.


## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

The change must be implemented as a network upgrade. It should only take effect after a designated upgrade epoch.

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->
N/A

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->
Gas mechanism serves a role in preventing DoS attacks on the network.
As changes performed here decrease the cost of only the WindowPoSt, and the value there is derived for a complete chain benchmark, the security risk of DoS attack using this syscall is minimal.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->
The change to incentives is minimal.
This proposal should reduce the cost of WindowPoSt reducing the flat cost of maintaining miners.



## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->
This proposal should enable more smaller miners to exist and prove storage due to reduced cost of WindowPoSt

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->

Draft PR changing the price table in Lotus: https://github.com/filecoin-project/lotus/pull/4830

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
