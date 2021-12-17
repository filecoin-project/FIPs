---
fip: <to be assigned>
title: Storage Ask Protocol v2 Standard 
author: Brenda Lee (@brendalee), @Jiaying Wang (@jennijuju) , Why (@whyrusleeping), Jimmy Lee(@jimmylee)
discussions-to: <https://github.com/filecoin-project/FIPs/discussions/225>
status: Draft
type: Technical
category (*only required for Standard Track): Interface 
created: <2021-12-13>
spec-sections: 
  - 2.7.1 (AskProtocol & Storage Ask)
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->
The goal of AskProtocol v2 is to help with the [discovery](https://spec.filecoin.io/#section-systems.filecoin_markets.storage_market.discovery) between the client and storage providers before making a storage deal proposal. As the first step of the SP discovery, clients can send details of their proposed deal to the storage provider, and the storage provider should be able to respond to the proposal (with accept or reject, price and additional service offer). Note that the ask protocol is **not** designed to handle back and forth deal negotiations. 

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->
AskProtocol v2 aims to improve the existing AskProtocol to help the client understand whether or not a storage provider is likely to accept their deal before they send a signed proposal. 

The proposed flow is simple. The client sends an ask request with information about the storage deal they would like to make. The ask response by the storage provider indicates whether or not the deal will be accepted with specifics on conditions (for example, how long the offer is valid for, and what the price to store is). More details about the AskProtocol v2 request/response can be found in the specification section. 


## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->
Clients need to be able to share details of the storage deal they want to make. Furthermore, they need to know what capabilities and features a Storage Provider supports, so as to understand what Storage Providers they can successfully make a deal with. 

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->
For the ask request, the client provides the following information: 
* Client address
* Peer ID
* PayloadCID
* Deal piece size
* Deal duration
* Deal start epoch
* Verified or unverified deal
* Fast retrieval required or not
* Transfer protocol
  - Need clearly defined transfer protocols (for example, graphsync, physical, etc.)
  - Option for client to specify additional transfer protocols
  - Will have a set of defined protocols, but allow SPs to add more
* Message freeform text 
* Signature by client 

For the response, the provider will respond with the following information: 
* Will accept or reject the deal
* Rejection code
  - Need clearly defined rejection codes
  - Start with HTTP codes and build from there
  - Option for storage provider to specify additional rejection codes
* Price per GB per epoch
  - Single price field
* How long the offer is valid for
  - Expiry time
  - Not binding, just for client convenience
* Start epoch of deal
* Message freeform text

## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->
TBD

## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->
TBD

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->
TBD

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->
TBD

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->
N/A

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->
One of the main experiences we want to improve is storage dealmaking and overall Filecoin storage reliability. Askv2 improvements aim to help with the following: 
- Better information on Storage Provider capabilities before client attempts to make a storage deal
- Easier to filter which Storage Providers will accept a client’s storage deals
- Increase storage deal success rate


## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->
TBD

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
