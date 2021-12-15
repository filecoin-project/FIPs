---
fip: <to be assigned>
title: Allow storage provider to revert deal back to CC
author:  @nicola, Fatman13 (@Fatman13),
discussions-to: https://github.com/filecoin-project/FIPs/issues/143
status: Draft
type: Technical (Core, Networking, Interface, Informational)
category (*only required for Standard Track): <Core | Networking | Interface >
created: 2021-09-28
spec-sections: 
  - <section-id>
requires (*optional): <FIP number(s)>

---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->

## Summary

Allow storage providers to revert a deal back to CC.

## Abstract

Given legal consequences a storage provider can face when storing sensitive data, on protocol level, maybe we should allow storage provider to revert a deal to CC to avoid potential prosecution/scrutiny. Basically the reverse of [lightweight CC upgrade](https://github.com/filecoin-project/FIPs/issues/131) (now called [snap deal](https://github.com/filecoin-project/FIPs/issues/145)). 

## Change Motivation

From a discussion [thread](https://filecoinproject.slack.com/archives/C023PAQ5SJV/p1629383994084200) in SPWG, concerns were raised as there is currently no means for storage providers (SP) to remove undesired data from their own storage systems without invoking "terminate" command, which may cause financial losses to SPs.

## Specification

Quoting [@nicola](https://github.com/nicola)'s [comments](https://github.com/filecoin-project/FIPs/issues/143#issuecomment-910154394)...

> Currently, the rational guarantees of a deal are also tied to the guarantee of a sector. If a miner were to remove a deal, they might have to lose more than the deal collateral.
>
> If we simplify the proposal to the bare minimum, this proposal can be implemented via a new method called `TerminateDeals(dealIds []Deal)` in the miner actor.
>
> If a deal is terminated (or expired), you can use the `ProveReplicaUpdate` skipping the deals you want to stop storing - which effectively allow you to remove the data.

## Design Rationale

<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->
TBD

## Backwards Compatibility

<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->
Should current deals be allowed to revert back to CC, or should it only concern new deals made after this potential FIP?

## Test Cases

<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->
TBD

## Security Considerations

<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->

Again quoting [@nicola](https://github.com/nicola)'s [comments](https://github.com/filecoin-project/FIPs/issues/143#issuecomment-910154394)...

> Technically it's not hard, the hard part will be the cryptoeconomic guarantee of the storage market - for which [@zixuanzh](https://github.com/zixuanzh) is an expert.

## Incentive Considerations

<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->

Assume rational storage provider who maximize profits from deals. It should always honour the deal unless there are legal interventions. Market would stop payments once the deal is reverted back to CC. Or for more conservative design, storage provider could be stripped away with all profits they made with the deal thus far, from, for example, locked funds.

## Product Considerations

<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->

Using [@ZX](https://github.com/ZX)'s Airbnb analogy, landlord should be able to evict tenant any time they want just like storage provider should be able to revert deal back to CC. Like allowing setting deals to negatives, this also can be seen as a mechanic to grant more flexibility at protocol level.

Quote from one of the SPWG members...

> To actually adapt to the real work, filecoin storage providers will need a tool to handle government requests to remove illegal content. Just like cloud providers are today. This is just a matter of Filecoin only being at the stage of proving its technology, and not moved into the area of handling real life application.

## Implementation

<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->

TBD

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).