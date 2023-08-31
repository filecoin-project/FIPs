---
fip: "<to be assigned>" <!--keep the qoutes around the fip number, i.e: `fip: "0001"`-->
title: On Chain CommD
author: <a list of the author's or authors' name(s) and/or username(s), or name(s) and email(s), e.g. (use with the parentheses or triangular brackets): @zenground0, Alex North (@anorth), ...
discussions-to: https://github.com/filecoin-project/FIPs/discussions/496, https://github.com/filecoin-project/FIPs/discussions/760
status: Draft
type: Technical
category: Core
created: 2023-08-30
requires: Draft: https://github.com/filecoin-project/FIPs/pull/804
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->


## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->
Allow optional storage of CommD within a new field of the sector info.  Adding CommD is specified by a field in the parameters of the new ProveCommit and ProveReplicaUpdate methods proposed in [Direct data onboarding](https://github.com/filecoin-project/FIPs/pull/804).

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->
Today there is no way to directly prove that sectors contain particular content after activation.  This is a useful pattern for smart contracts operating over data.  Putting CommD on chain unlocks  this feature as CommD can be accessed by miner actor code and serve as an onchain witness of sector content for inclusion proofs. 

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->
The filecoin development community has a demonstrated interest in enabling innovation in smart contracts that interact with verifiable storage.  It is the FVM's main differentiator when compared with other blockchain runtimes.  Two different groups have arrived at similar conclusions on a particular useful direction for the miner actor in relation to these goals:  myself [here](https://github.com/filecoin-project/FIPs/discussions/496) and venus dev team [here](https://github.com/filecoin-project/FIPs/discussions/760).  The first step in this direction is to allow SPs to keep CommD on chain in the sector info.

Adding CommD to sector info requires a sector info migration which on its own is a costly in terms of network development and risk.  Similarly it will require changes to parameters being introduced in ongoing [direct data onboarding (DDO) work](https://github.com/filecoin-project/FIPs/pull/804). Doing this work at the same time as DDO (which also needs a full sector info migration) makes the upgrade risk and development cost overhead much smaller.


## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

### Add *CommD to SectorInfo 

Add an optional Cid field to the sector info on chain: 

```rust
pub struct SectorOnChainInfo {
    pub sector_number: SectorNumber,
   ...
    pub unsealed_cid: Option<Cid>,  // NEW
   ...
    // Flag for QA power mechanism introduced in fip 0045
    pub simple_qa_power: bool,
}
```

The migration to achieve this will simply set `UnsealedCid = nil`.  Only new sectors will be able to set CommD.

### Add flag for setting CommD to new DDO proving methods

```go
struct SectorActivationManifest {
    // Sector to be activated.
    Sector: SectorNumber,
    // Pieces comprising the sector content, in order.
    Pieces: []PieceActivationManifest,
    KeepCommD: bool, // NEW
}
```


New ProveCommit and PRU messages will then parse this new bool flag and store CommD if specified.
If CommD is the zero data CommD then the system will always avoid storing even if KeepCommD is true.

## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->

### Implementing CommD on chain
Since CommD is a property of an individual sector if it is onchain it belongs on the sector info.

Specifying inclusion as part of the DDO sector activation manifest allows for user control over which specific sectors can store CommD.

Storing CommD as a pointer/option type in sector info mirrors the storage of sector key in sector info to support snap deals.  This allows optional storage of the field while minimizing overhead when no storage is needed

### Rationale for CommD on chain
See [this discussion](https://github.com/filecoin-project/FIPs/discussions/760#discussioncomment-6558186) for the need to keep CommD on chain to unlock the possibility of onchain verification of sector data inclusion.


## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->
To be included with implementation:
1. When setting keep_commd=true parameter flag the CommD is kept in sector info
2. When setting keep_commd=false parameter flag the CommD is not kept in sector info
3. Test that when CommD == zero data CommD then no value of keep_commd will allow CommD to be kept on chain

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->
There are no known or expected security issues with this design.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->
There are no known or expected incentive changes with this design.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->
Sector infos are the datatype that dominate space used by the filecoin state and therefore blockchain syncing storage costs. Adding a potentially large field to this data type therefore has a risk of significantly increasing the data storage needed to sync the filecoin chain.  To understand this risk I measured sector info stats and reported findings [here](https://github.com/filecoin-project/FIPs/discussions/795).

The results are encouraging.  CommR, which is the same size as CommD, takes up about 47% of all of sector info space.  Looking at the number of sectors that have deals vs total live sectors we see that all deal bearing sectors (living and dead) are < 14 percent of all currently live sectors.  So in the worst (for space usage) case we would see a 6-7% increase in space usage of state if we retroactively added CommD on chain for all existing non-CC sectors.  In practice the state impact will be lower. Only a fraction of users will opt into the new data onboarding flow adding CommD on chain and it will only apply to new deals.

Beyond the relatively small expected state growth from CommD on chain the report on sector infos is also encouraging because it points to concrete plans we could adopt to cleanup unused sector info space.  The two most promising strategies are finding a way to remove dead sectors (half of all sectors are dead) and simplifying the termination fee calculation (10% or 20% state savings).  With this in mind there are good paths forward to keep state size manageable even with unexpectedly rapid on chain CommD growth. And therefore the benefit of adding CommD on chain is worth the risk.  


## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->
TODO
- builtin actors
    - add keep_commd to sector_activation parameter type
    - add commd to sector info
    - tests
- migration
    - set commd to nil

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
