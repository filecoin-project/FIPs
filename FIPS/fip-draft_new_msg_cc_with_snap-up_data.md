---
fip: "0066"
title: Add a message for New CC Sector with Snap-up Data
author: Andy Jackson (@snadrus)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/765
status: Draft
type: Technical
category: Core 
created: 2023-07-28
---

## Simple Summary
Allow a new message creating a new sector with data already snapped-up. 

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->
Feeding sealing machines is difficult and complicated, especially as a service. CC is easier, but snap-up costs more. Can we get the best of both?

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->
Today's snap-up allows for late-added deals and growing beyond being a CC provider. But it's **almost** well-suited to simplify sealing. 
Now that Sealing-as-a-Service & large sealing system (like the ones from SupraNational) are in the mix, data-ingest in is a bottleneck. It could also be a 
data-soverignty concern (ex: HIPAA, GDPR). The pre-FIP solution of snap-up partially resolves this except for (1) extra cost, (2) a 30-day window, and (3) sector PoSt while transferring from SaaS to owner.

By allowing a new message to post CC with Data, this solves (2) and (3) by giving unlimited time to introduce the block. An overarching proof may be possible to 
allow the network to do less total work to onboard than with today's snap-up because both proofs are happening at the same time, thereby fixing (1) above.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->
[[ NOTE DRAFT as this area needs more investigation ]]
A single message should announce the sector, which will cut gas costs. 
Today there are 2 proofs involved to make this happen. More investigation is needed to see if a single proof could encompass this case.

## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->
The goals are specified in Change Motivation. These are met by delaying registration of CC sectors AND having registration expense resemble regular sectors.

## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->
This requires a network upgrade to allow this message. This could occur before code that acutally produces these new sectors. 

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->
TEST 1: A CC with snapped-up data must be expressable in a single message defined by the spec (above) and pass concensus. 
TEST 2: TEST 1 with an over_30_day_old sector must also pass concensus.

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->
The 30-day window's reasoning needs to be considered. 
If proofs stay the same, security implications should not change. If they change (discussion ongoing), an evaluation of any new proofs would be needed.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->
This is intended to incentivize the use of this new workflow (CC sector creation without registration followed by snap-up) to reduce the labor necessary in keeping
sealing pipelines fed. This will further incentivize use of "big sealing machines" and Sealing-as-a-service

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->
Products wishing to benefit from this can make their sealing processes not register at the end, but provide those empty sectors to a market tool (eg. Boost).
Complying market tools would need to be able to use these new sectors and initiate a snap-up flow and registration. 

The result would lead to a workflow that is simpler as sealing pipelines (especially those running parallel) will not need input (nor a CC decision) to start.
Workflows with no particular input decision necessary can simply run when there is available resources (storage capacity). 

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->
Not yet available.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
