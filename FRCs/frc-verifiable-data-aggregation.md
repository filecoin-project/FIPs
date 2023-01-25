---
fip: "<to be assigned>" <!--keep the qoutes around the fip number, i.e: `fip: "0001"`-->
title: Verifiable Data Aggregation
author: Jakub Sztandera (@Kubuxu), Nicola Greco (@nicola), Peter Rabbitson (@ribasushi)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/512
status: Draft
type: FRC
created: 2022-12-11
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->
Enable Clients using data aggregation services to verify correct aggregation of their data and allow proving of this fact to third parties.

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->
This proposal provides a description of a scheme enabling Aggregators to produce
a Proof of Data Segment inclusion certifying proper aggregation of Client's data.
The produced proof assures:
- an inclusion of Client's data within the on-chian deal
- the Client's data can be trivially discovered within the deal to enable retrieval
- malicious behaviour of an Aggregator or another user, whose data was aggregated, does not interfere with retrievability of Client's data

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->
A large majority of users onboard data onto the Filecoin network via an Aggregator. Today the work done by aggregators is unverifiable and unprovable.
The user relies on the Aggregator to perform the work correctly and at the same time, it is impossible to prove to a third party that a given piece of data was included in a deal which is a highly requested functionality for FVM.

This is a critical link in enabling data within aggregated deals to be as useful as deals themselves. 
Without the proposed proof, data within aggregated deals becomes a second class citizen in Filecoin ecosystem.
Significant portion of the F(E)VM use-case is enabling the ability to process and reason about the data stored by Filcoin Storage Providers. 
The Proof of Data Segment Inclusion allows to apply this new capability on segments of data which are too small to be on-boarded in their own deals due to economic constraints.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->
The specification consists of three parts:
- Data Segment Format and alignment
- Data Segment Index and retrieval handling
- Proof of Data Segment Inclusion 

### Data Segments

A Data Segment is an array of bytes the Client requested to be stored after the process of Fr32 bit padding.
Data Segments are identified by the commitment to data (using same algorithm as PieceCID, SHA-256-truncated, 2-ary Merkle Tree) and their size.

Data Segments can then be placed within a deal according to alignment rules of current sectors.

Data Segments have to aligned to the next power of two boundary with NUL trailer up to next power of the boundary.
```
DataSegment size = ceil(original sub-deal size * 128/127) // Fr32 padding
DataSegment alignment = pow(2, ceil(log2(DataSegment size))
DataSegment with trailer size = DataSegment alignment
```

### Data Segment Index

Data Segment Index is an optional region at the end of a deal describing all the data segments contained within that deal.
The index is constant sized depending on the size of the deal but not all entries in the Data Segment Index have to be utilised. Unused entires should be filled out with NUL bytes.

The number of entires in the index is defined as:
```
number of entires = max(4, floor(size of deal / 2048 / 64 [byte/entry] ))
size of index = number of entries * 64 byte
start of the index = (size of deal - size of index) & 0xffffffff_ffffffc0
```

This results in index capable of containing 256Ki entries and using 16MiB with 32GiB deal.

Each entry within the Data Segment Index has size of 64 bytes after Fr32 bit padding resulting in usable space of 508 bits, two 254 bit nodes (two high bits of each 32byte node are set to 0s). Each entry is also aligned to 64 byte boundary after Fr32 bit padding.
The format is designed to be accessible and readable in the Fr32 padded form.

Entires consists of:
 - CommDS - commitment to the data segment, 254 bits, first node
 - Offset - offset in bytes from the start of the deal to the Data Segment, low 64 bits
 - Size - size in bytes of the Data Segment, next 64 bits
 - Checksum - SHA-256 of the `(CommDS, Offset, Size, 0s)` truncated to 126 bits filling out second node.

For the purpose of SHA-256 checksum, data is structured in the same format as Data Segment Index entry with checksum bits filled with 0s.

Data Segment Index entry is defined as valid if it is positioned within the Data Segment Index area, from the `start of the index` to the end of the deal and contains a valid checksum.

#### Retrieval handling 

After receiving a deal data, a Storage Provider should process the index area to discover any valid Data Segment Index entries within that area.
When a valid entry is discovered the SP should queue up a task of computing the commitment of referenced Data Segment.
If the commitment in the index matches the referenced Data Segment, the Storage Provider should make in possible to retrieve the Data Segment via its Data Segment commitment (equivalent to PieceCID).

Apart from that Storage Provider should enable retrieval of PieceCIDs computed based on implicit data segments:
```
offset: 0, size: deal size / 2
offset: deal size / 2, size: deal size / 2
```

### Proof of Data Segment Inclusion

The proof consists of two inclusion proofs:

- An inclusion proof of a sub-tree corresponding to the tree of the client’s data, optionally this sub-tree can be miss-aligned with the proving tree.
- An inclusion proof of the double leaf data segment descriptor within the data segment index.

The client possesses the following information: Commitment to their data $\mathrm{CommDS}$ and size of their data $|{\mathrm{DS}}|$.

The aggregator inserts client’s data into the sector or deal, and also adds the data segment descriptor into data segment index.

Following that, the aggregator produces the data commitment and two inclusion proofs and provides them to the client:

- $\mathrm{CommD}_ A$ - a commitment to the data created by the aggregator
- $|\mathrm{D}_ A|$ - size of the aggregator’s data, corresponding to deal/sector size.
- $\mathrm{pos}_ D$ - position of client’s data within the aggregator’s data
- $\mathrm{idx}_ {ds}$ - index of data segment descriptor within the data segment index
- $\pi_ {st}$ - sub-tree proof, proving the inclusion of $\mathrm{DS}$ in $\mathrm{D}_ A$ at position $\mathrm{pos}_ D$
- $\pi_ {ds}$- leaf inclusion proof, proving the inclusion of $(\mathrm{CommD}_ A, \mathrm{pos}_ D, |\mathrm{D}_ C|, \mathrm{checksum})$ within $\mathrm{D}_ {A}$ at $f(\mathrm{idx}_ {ds}, |\mathrm{D}_ A|)$

The $f(\mathrm{idx}, \mathrm{size})$ is a pre-agreed function mapping position within the data segment index to position within the container. 

Auxiliary information provided by the aggregator to the client are: `DealID` of the deal which contains Client's data.

To complete the verification of the proof, the client has to verify the two inclusion proofs as well as check that a given sector was on-boarded and $\mathrm{CommD}_ A$ was size $|\mathrm{D}_ A|$:

- $\mathrm{VerifyInclusion}(\mathrm{CommDS}, |\mathrm{DS}|, \mathrm{CommD}_ A, |\mathrm{D}_ A|, \pi_{st}, \mathrm{pos}_ D)$
- $\mathrm{VerifyInclusion}(\mathrm{Comm}(\mathrm{CommDS}, \mathrm{pos}_ D, |\mathrm{D}_ C|, \mathrm{checksum}), 2, \mathrm{CommD}_ A, |\mathrm{D}_ A|, \pi_ {ds}, f(\mathrm{idx}_ {ds}, |\mathrm{D}_ A|))$
- Verify that `DealID` is active on chain
- Verify that `DealID` has data commitmetn of $\mathrm{CommD}_ A$ and size $|\mathrm{D}_A|$.



## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->

The design of this proposal is guided by three main goals: to ensure the provable inclusion of the client's data within the aggregator's on-chain data deal, to make it easy for the storage provider to find the user's data within the larger data segment, and to prevent malicious behavior of the aggregator or other users whose data was aggregated from causing irrecoverable problems with retrieval.

To achieve the first goal, the proposal includes a mechanism for producing an inclusion proof. This proof allows the client or a third party to verify that their data is properly included within the on-chain deal.

Additionally, the proposal includes a Data Segment Index which provides discoverability of data within the sector. This feature allows the storage provider to easily locate the client's data and prevents malicious behavior from influencing the retrieval of data. By including this mechanism, the proposal ensures that the client's data is retrievable, even if there is malicious behavior from the aggregator or other users.

## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->
Not applicable

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->
Pending

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->
Does not impact core Filecoin security.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->
Does not impact incentive systems.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->
TODO

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->
WIP

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
