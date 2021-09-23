---
fip: <to be assigned>
title: Break ties between tipsets of equal weight
author: Sarah Azouvi (@sa8), Aayush Rajasekaran (@arajasek)
discussions-to: https://github.com/filecoin-project/FIPs/issues/22
status: Draft
type: Technical (Core)
created: 2021-09-07
spec-sections: 4.1.4.2
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->


## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->

The general process by which nodes on the Filecoin network choose between two tipsets is by picking the heavier tipset based on a weight function (see [here](https://spec.filecoin.io/#section-algorithms.expected_consensus.chain-weighting)).

It is not an unlikely event for two tipsets to have the same weight. When this happens, we should have a simple rule to pick one of the tipsets as canonically "heavier" so as to achieve consensus faster. This FIP proposes such a rule.

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->

Filecoin needs a rule to decide between forks of equal weight. Although not critical it would help block producers converge more easily towards a common chain. This means that when two forks with the same weight occur, all the block producers that have received both forks will mine on the same one. Without a tie-breaker they would randomly choose one and may extend the forks for longer.

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->

Implementing such a rule will help the network achieve consensus faster. This has an immediate effect of reducing the number of orphaned blocks, which increases profits for block producers. More importantly, this FIP will reduce the time it takes the network to recover from slowdowns or outages, since nodes will achieve consensus faster.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

For two tipsets with the same weight, we pick the tipset with the smallest winning Ticket. In the case where two Tipsets of equal weight have the same smallest Ticket, we compare the next smallest Ticket in the Tipset (and select the Tipset with the smaller one). This continues until one Tipset is selected. There are 2 interesting cases to consider:

- The tipsets are of unequal size: the larger tipset is almost always gonna be heavier in this case. In the virtually impossible event of a tie, we explicitly leave behaviour undefined.
- The tipsets are of equal size, but all the tickets are identical: This is only possible if a block producer has produced 2 different blocks with the same ticket. We explicitly leave behaviour undefined here too, since the producer will be heavily slashed for this.

## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->

Any solution that is both deterministic and non-biasable (i.e. an adversary may not make their chain more likely to be selected by the chain selection algorithm in the case of forks of equal weight) may work. The ElectionProof is unbiasable and hence is a good candidate for tie-breaker. Any deterministic rule other than minimum ticket would work just as well.

## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

This FIP proposes a "soft" change that maintains full backward compatability. No new network version is needed.

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->

The following test cases should be covered:

- two tipsets with different min tickets
- two tipsets with one min ticket the same
- two tipsets with several min tickets the same
- three heaviest heads

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->

We should be confident that the proposed tiebreaking rule is unbiasable by adversarial block producers. That aside, this FIP is a strict improvement to network security.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->

No change to incentives.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->

No change to product considerations, except that increased overall stability is a net improvement.

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->

TODO in each of the Filecoin implementations.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
