---
fip: "0027"
title: Change type of DealProposal Label field from String to byte array
author: Laudiacay (@laudiacay)
discussions-to: https://github.com/filecoin-project/FIPs/issues/187
Status: Draft
type: Technical
category: Core
created: 2021-09-29
spec-sections: 
  - specs-actors
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->


## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->
DealProposal's Label field is currently a String, but is not enforced to be UTF-8. This is not only outside the CBOR string specification, but can also be a source of bugs and difficulties in client implementations due to variations in String libraries. Rather than enforce it as UTF-8 everywhere, this FIP changes the type to be raw bytes for ease of implementation, bug avoidance, and CBOR compliance.

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->
String libraries differ in implementation of UTF-8. For maximum standardization and ease of bug-free client implementations, the DealProposal label should be raw bytes. Further, non-UTF-8 CBOR strings are technically outside of the CBOR specification, so the current implementation is outside of CBOR spec.

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->

Discussion is here: https://github.com/filecoin-project/specs-actors/issues/1248

Summary: @ec2 noted that the non-UTF8 strings in this field are causing problems for the client implementations like ChainSafe. @ribasushi noticed that the Label field takes user input more or less directly, so enforcing UTF-7 might be difficult and pointless. Finally, @mikeal posted notes from an IPLD call saying that the source of the problem is that some programming languages enforce UTF-8 on Strings, while others don't, so the most widely compatible type for any on-chain data like this would be to just use a byte array.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

The Label field of DealProposal should be CBOR bytes with arbitrary data allowed inside.

## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->

Design decisions are in above sections.

## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

This changes specs-actors. All deal proposals on chain will need to change the encoding of the label field.

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->

Test that v0-v6 proposals' String labels become CBOR bytes with the same raw byte payload after migration, and that new proposals have labels encoded as CBOR bytes.

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->

Implementations that were previously validating that Label strings were valid UTF-8 should validate where else they might be parsed or used. Checking UTF-8 encoding could potentially reject an otherwise-potentially-dangerous attack payload that could exploit other code that interacts with this data.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->

This should have a positive effect on reliable and useful storage, because implementations of the protocol will be more correct and easier to maintain.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->

This should have a positive effect on the ecosystem as a whole, because implementations of the protocol will be more correct and easier to maintain.

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->

[Here](https://github.com/filecoin-project/specs-actors/pull/1496)

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
