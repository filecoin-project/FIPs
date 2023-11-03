---
fip: "**TODO**"
title: On-chain Retrieval Expectations
author: "Will Scott (@willscott)"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/
status: draft
type: Technical (Core)
category: Core
created: 2023-10-10
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->

Today, a mish-mash of heuristics have emerged to attempt to identify client intentions about the retrievability of data stored in filecoin.
This FIP proposes a simple on-chain mechanism to allow clients to express those expectations at deal time.
This proposal should be thought of as two distinct sub-components: A concretization of the expectations that clients have about the retrievability of data into a defined set of SLAs, and a mechanism to express those SLAs on-chain.

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->

This FIP defines a set of retrieval SLA ‘tiers’.
These tiers identify the ‘category’ of data - if it is fully offline, meant for low-volume-retrieval archival usage, or for more regular retrieval.
The consensus part of this FIP is a proposal to encode the retrieval SLA tier as part of a deal proposal.
Standardizing retrieval expectations in this way allows storage providers to apply appropriate policies and pricing to deals.

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->

There are already several fields which touch on this issue. 

* `FastRetrieval`  - part of `ClientStartDeal` API calls and stored in provider state.

* `Label`  - part of a `DealProposal` on chain.

* `VerifiedDeal` - part of `DealProposal` on chain

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

### Overview

### Tiers

The proposed tiers are:

1. *Offline* - Data that is transferred via physical media. This data is not expected to be retrieved over the network.
2. *Archival* - Data that is expected to be retrieved infrequently. This data is only expected to need enough network bandwidth to be able to ensure replication. The most common data replication policies on filecoin today at 5x and 10x copy replication, to ensure that data remains even when some copies are unavailable. In order for contracts or users to ‘heal’ data replication policies in the face of failures, they would potentially need (n-1) copies of the data to be re-replicated.
3. *Online Data* - Data that is expected to have periodic retrieval by an ACLed list of users. This tier allows for negotiation of higher retrieval service levels without committing to make the data available to the network at large.
4. *Public* - Data that is expected to be openly retrievable by anyone. This tier allows for negotiation of higher bandwidth and low latency provisioning.
5. *CDN* - The details of this tier are still being worked out, but we reserve this nomenclature for a higher tier of retrieval service that equates to the expectations for bandwidth and latency that would be found at CDN service offerings.

| Tier | Offline | Archival | Online | Public |
| --- | --- | --- | --- | --- |
| Example of data | Large datasets onboarded with physical disks | Long term private data storage & backups | Research Datasets | Files, Documents, Images |
| Amortized anticipated retrieval volume | 0 | 1x / month | 1x / week | 1x / day |
| Expected resilience to burstiness | n/a | 2x | 3x | 5x |
| User-expected Latency | n/a | < 6hr | < 1min | < 5sec |



### Deal flow change (current)

The `DealProposal` [struct](https://github.com/filecoin-project/go-state-types/blob/master/builtin/v12/market/deal.go#L200) is extended to include an additional, optional, field:

```go
    RetrievalTier abi.RetrievalTier
```

An undefined or empty value of this field is interpreted using the following logic: 

* If the `VerifiedDeal` flag is set, the tier interpreted as `Archival` 

* Otherwise the tier is interpreted as `Offline`

### Deal flow change (in conjunction with direct data onboarding)

In the network with Direct Data Onboarding (FIP 0076), there will not always be a `DealProposal` for a deal.
In this case, where no market deal is present, the `RetrievalTier` is encoded as an extension of the `PieceActivationManifest` from the storage provider.

The negotiation of storage deals may contain a client request for which Retrieval Tier to specify, but that process in Direct Data Onboarding occurs off chain.
What inclusion of this field in the `PieceActivationManifest` allows is that the chain may react and that contracts can be written to monitor and respond to these advertisements.

### FVM extensions

`publishStorageDeals` will retain its existing signature, and will take on the ‘empty’ definition of the `RetrievalTier` field as described in (“Tiers”)[#tiers].
A parallel method can be implemented allowing for the additional specification of the `RetrievalTier`.

A new method `GetDealRetrievalTier` would be added as with other deal property accessors.

## Design Rationale

We cannot fully predict what tiers will be optimal for each provider, but concrete tiers will reduce the design space, which will reduce uncertainty of other components and provide reasonable service tier recommendations for providers to offer.
We expect further tier definitions to emerge over time, but that their inclusion into the registry introduced here will serve as an efficiency mechanism, rather than one needed for enabling new types of service.
The tier definitions here provide a shorthand encoding of common levels of service that can be efficiently communicated on chain, and which measurement and evaluation services can be designed against.
Additional agreements can take place in smart contracts on an opt-in basis to provide more complex policy agreements.
Since we cannot predict the needed common language for these policies in a way for arbitrary other components to enforce against, we defer that to future work.

## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

The added field, both in and out of a direct data onboarding network, is optional. As such, any current deal, and any future deal not specifying the added field will take on the specified default behavior. 

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->

To be provided with [implementation](#implementation).

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->

This proposal has no impact on consensus or blockchain security.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->

This FIP does not itself change incentives. It does provide a hook by which providers can set different pricing and policies for different tiers of service.
This is a necessary component for enabling a market for different tiers of service. There is sufficient flexibility in other structures built on top of filecoin that we can expect some amount of incentive shift to occur as a result of this FIP.
The expected direction of this shift is towards an increased incentivization of retrievals.

### Gameability of tiers

Reporting that content is available at a higher tier does not directly help clients or storage providers.
In fact, it primarily raises costs as the sum of all deal retrievals will lead to a direct calculation of expected network bandwidth provisioning of an SP.
Failure to provision at the  level indicated by existing deals could lead to future clients having less confidence that subsequent deals would be able to be retrieved with their intended SLA.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->

Including a negotiated field of the expected retrieval properties of each deal will allow retrievability and retrieval incentives to be programmed in smart contracts. This will allow for the creation of a market for different tiers of service, and will allow for the creation of measurement and evaluation services that can be used to enforce these contracts.



### Why should we believe this direction will do more for retrieval than the existing fast retrieval flag?

- More developed ecosystem, with multiple entities ([retrieval bot](https://github.com/data-preservation-programs/RetrievalBot), [spark](https://sites.google.com/protocol.ai/spark)) measuring retrievability today.
- The expected definition of what `FastRetrieval` meant, as a signal to ‘store an unsealed copy’, but without a strict SLA or other user visible implication was unenforceable. In contrast, the definitions and tiers proposed here can be measured and incentivized today.

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->

To Come

## TODO
<!--A section that lists any unresolved issues or tasks that are part of the FIP proposal. Examples of these include performing benchmarking to know gas fees, validate claims made in the FIP once the final implementation is ready, etc. A FIP can only move to a “Last Call” status once all these items have been resolved.-->

* Implementation of the extended data structures
* Determine the appropriate interleaving of this FIP with Direct Data Onboarding (FIP 0076)
* Determine if an additional structure should be created for the registry of retrieval tiers besides this FIP process (e.g. of the form of the multicodec registry)

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).

