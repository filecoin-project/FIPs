---
fip: <to be assigned>
title: Handle Expired Deals in ProveCommit
author: ZenGround0 (@ZenGround0)
discussions-to: https://github.com/filecoin-project/FIPs/issues/152
status: Draft
type: Technical 
category (*only required for Standard Track): Core
created: 2021-09-06
spec-sections: 
  - specs-actors
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->
Add a new parameter to ProveCommitSector and ProveCommitAggregate so that storage providers can commit sectors with some expired deals.

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->

Today storage providers are unable to commit sectors with expired deals because the sector's data commitment cannot be determined on chain with deal PieceCID and PieceSize info removed from state.  To make this possible the ProveCommit and ProveCommitAggregate messages can be adapted to take in the PieceInfos of the expired deals.  Then the data committment can be computed from the provided expired piece info and the market actor's data.

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->
Occasionally deals expire between PreCommit and ProveCommit and in these cases sectors containing these deals will fail to commit. This is bad for storage providers committing sectors with deals and bad for the non-expired deals that would become active if the sector were committed. While offchain logic can help in many cases there is always a small risk of deals expiring even with optimal offchain logic as long as there is a delay between precommit and provecommit.


## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

### ProveCommitSector

- args change to include ExpiredDeals map: a cbor map {dealID: PieceInfo}.

```golang
type PieceInfo struct {
     PieceCID  cid.Cid
     PieceSize abi.PaddedPieceSize
}
```
- ComputeDataCommitment is extended to take in ExpiredDeals map.  Validation that all expired deals are actually expired: dealID is less than next dealID and deal not found on chain

### ConfirmSectorProofsValid

- Only send ActivateDeals messages for non expired deals
- Only include DealIDs of non-expired deals in the newly created SectorOnChainInfo
- Recompute DealWeight and VerifiedDealWeight for sectors at prove commit to stay accurate even with expired deals

### ProveCommitAggregate

ProveCommitAggregate params now include a map from sector id to the ExpiredDeals map datastructures defined above.

All ConfirmSectorProofsValid changes directly apply to ProveCommitAggregate.


## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->
The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.

## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->
All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->
Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->
There are no security implications to this proposal.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->
- Although this construction can't prevent using different PieceCids then originally specified in PublishStorageDeals for a DealID it is not rational to do this so it is not a problem for the protocol.
- After this proposal deal clients will not have a guaranteed burn of precommit deposit by the miner if their deal id is included in precommit but not activated.  This removes a stronger disincentive for storage providers to not let deals expire before committment.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->
Storage provider software will need to change slightly to create correct parameters for sector committment methods. Storage provider software will be able to use this new argument to provide more cost efficient error handling by explicitly listing deals as expired and committing the sector instead of letting the sector drop and burning precommit deposit.

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->
specs-actors PR: TODO

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
