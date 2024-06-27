---
fip: "<to be assigned>"
title: Filecoin Common Node Interface V1
author: "David Ansermino (@ansermino), Aatif Syed (@aatifsyed)"
discussions-to: <URL>
status: Draft
type: FTP
category (*only required for Standard Track): Interface
created: 2024-06-25

---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->


# FIP-Number: Common Node API

## Simple Summary
Establish an basic specification for the common JSON-RPC API provided by Filecoin node implementations.

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->

Lacking a common API for all node implementations, client diversity is hindered as applications are unlikely to be interoperable with different node implementations. Lotus is the defacto reference implementation, but lacks a sufficiently specified interface for other implementers to replicate.

In this FIP a subset of existing RPC methods are formally specified to enable consistency across implementations, and provide clarity on the methods users can expect when interacting with a node.

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->


The JSON-RPC interface provided by Filecoin node implementations is the primary interaction point for many systems, however a standard interface has yet to be established definitively. Lacking such standards, builders are forced to invest additional time and resources in reverse engineering implementations. Node interoperability is hindered as there are no gurantees about what APIs will be encountered in the wild. A proper specification will enable the development of applications that are implementation-agnostic.

Ultimately the [Lotus RPC API](https://github.com/filecoin-project/lotus/blob/b73d4e0481517b395a0e9aa9af5dab8bedc18285/documentation/en/api-v1-unstable-methods.md#mpoolpushmessage) is the defacto specification currently, which includes 280+ methods. Based on our exploration and discussions with the Lotus team we have established that some methods provide duplicated functionality (eg. `ChainGetGenesis()` is equivalent to`ChainGetTipSetByHeight(0)`). Another subset of methods are related to implementation-specific internals (eg. `ChainHotGC`). And yet another subset are for the purpose of configuring the instance, which could be exposed through other means (eg. CLI, config file) depending on the design principles of a node implementation. This leads us to conclude that the canonical RPC interface should only include a subset of the methods currently supported by Lotus.

The defacto Lotus specification is lacking in several features: complete JSON schemas, descriptions for each method, and reliable consistency with the implementation. This motivates us to propose a normative OpenRPC schema for the purpose of defining this interface in a machine readable format. This format in turn enables:
1. Compliance checks - enable implementations of the interface to verify the syntax
2. Specificity - it provides a language agnostic format for defining the ABI of the methods in the interface
3. Discoverability - allow consumers to dynamically interact with providers
4. Lack of desire to reinvent the wheel - It's not perfect, but it works...

Additionally, by establishing a specification we seek to establish a greater responsibility on implementers and encourage more discourse for future iterations and further interfaces. The present API shows signs of rapid iteration and the resulting technical debt.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

Using the OpenRPC specification format we define several groups of methods. These methods are defined in the OpenRPC specification found here: https://github.com/ChainSafe/filecoin-openrpc-spec. A list of the methods is included below for posterity.

All methods are reproduced identically to their present implementation in Lotus 1.26.1.

Categories have been assigned to indicate the identified use case (see Design Rationale).

Node implementers must include all specified methods in their API without any modifications. Implementers may choose to provide additional methods beyond what is included in this specification. The endpoint used to serve RPC requests must be versioned acccording the majo

## Subscription methods
The `ChainNotify` method is not a simple request/response, but rather a bidirectional exchange of JSON-RPC-like messages as follows:

1. Caller sends a JSON-RPC request to the endpoint, with no parameters.
    ```json
    { "jsonrpc": "2.0", "id": 1, "method": "Filecoin.ChainNotify" }
    ```
2. Callee sends a JSON-RPC response with an integer Channel ID
    ```json
    { "jsonrpc": "2.0", "id": 1, "result": 2}
    ```
3. Callee sends JSON-RPC notifications, with a pair of positional parameters. The first is the Channel ID, the second is the actual payload
    ```json
    { "jsonrpc": "2.0", "method": "xrpc.ch.val", params: [2, {}] }
    ```
4. Caller sends a JSON-RPC request to cancel the subscription, with their Channel ID
    ```json
    { "jsonrpc": "2.0", "id": 1, "method": "xrpc.cancel", params: [2] }
    ```
5. Callee responds with a JSON-RPC notification of cancellation
    ```json
    { "jsonrpc": "2.0", "id": 1, "method": "xrpc.ch.close", params: [2] }
    ```


## Methods

> Current list here (TBC): https://docs.google.com/spreadsheets/d/1fFkQuEjvFAd2s1dGX5zGmhxsEMLMUZ4uQFnIXgSZA5w/edit?usp=drivesdk

| Method | Tag | Description |
|---|---|---|
|MethodName|Tags | Description of method|



## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->

This interface is contrived from the existing [Lotus RPC V1 interface](https://github.com/filecoin-project/lotus/blob/48287574d82c81ffc50f259134c6596add32a2f5/documentation/en/api-v1-unstable-methods.md). Due to the large number of methods presently supported, we have limited the scope of this specification to include methods with a well established use case. We have observed the requirements of Lotus-miner, Curio, Web3Mine and Boost to inform which methods are actively used. We have also considered insights from Glif based on the usage of their RPC service.

We target two groups of users: *end users* and *node operators*. These each have their own requirements for particular data and access control. While no attempt is made in this FIP to specify considerations  for these groups (eg. access control), these groups are used to justify the need for particular methods.


Methods included in the API fall into one of these categories:

- State Queries
  - These primarily concern the chain state, actor state or network (p2p) state. They are read-only methods that are necessary to expose all elements of global state.

- Miner Operations
  - A small set of specialized methods miner applications require to participate in consensus.

- Transactions
  - Necessary methods to submit new transaction for inclusion in the chain, including inspecting the mempool and estimating gas parameters.

- Node Operation
  - Several methods are included to enable remote management and inspection of a node instance via RPC. These have been restricted to commonly used, implementation-agnostic methods.

### Additional Notes

#### `Eth` Methods
`Eth` methods have been excluded as they are inferred from the [Ethereum JSON-RPC specification](https://ethereum.org/en/developers/docs/apis/json-rpc/), with some changes. We intend for these differences to specified in a later FIP.

### Future Revisions
It is expected that changes to this API will be made at some point in the future. All non-breaking changes should be introduced within the spec repo, at the discretion of node implementation teams (presently Lotus, Forest, Venus). Rough consensus should be followed, with implementation teams that adhere to the specification as the primary decision makers.

Breaking changes must be submitted as an FIP before being introduced to the latest spec.

In all cases valid semantic versioning must be used.

## Backwards Compatibility - Review
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

The methods in this specification are a subset of methods from the existing defacto specification (ie. Lotus API), which all implementation follow, thus backwards compatibility is maintained.

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->

[TODO]

We may want to consider three types of testing:
- Schema conformance (request/response structure in OpenRPC document is valid)
- Implementation conformance (implementation adheres to schemas)
- Functional conformance (request returns expected response values)


## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->

Node implementers must consider the security implications of all methods and ensure sufficient access controls are implemented. This is beyond the scope of this FIP.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->

Not relevant to this FIP.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->

A better API, one that is well defined and carefully constructed, will ease the development of many types of applications. This FIP is only sufficient in ensuring the API is well defined, additional work is needed in future to refine the API.

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->

- [ ] Lotus
  - [ ] Implementation of Common Node API methods
  - [ ] OpenRPC document available
  - [ ] Automated testing of conformance to schema
  - [ ] Common Node API methods conform to schema
- [ ] Forest
  - [ ] Implementation of Common Node API methods
  - [ ] OpenRPC document available
  - [ ] Automated testing of conformance to schema
  - [ ] Common Node API methods conform to schema
- [ ] Venus
  - [ ] Implementation of Common Node API methods
  - [ ] OpenRPC document available
  - [ ] Automated testing of conformance to schema
  - [ ] Common Node API methods conform to schema

## TODO
<!--A section that lists any unresolved issues or tasks that are part of the FIP proposal. Examples of these include performing benchmarking to know gas fees, validate claims made in the FIP once the final implementation is ready, etc. A FIP can only move to a “Last Call” status once all these items have been resolved.-->

- [ ] Confirm methods that are included
- [ ] Improve descriptions for included methods
- [ ] Change link to be an issue for the inconsistency
- [ ] Add a note on URIs (eg. `/rpc/v1`)
- [ ] Publish two versions of the document, one per URI
- [ ] Describe ChainNotify in OpenRPC
- [ ] Make ChainNotify definition more generic
- [ ] Add link to playground
- [ ] @ansermino look into contentdescriptors
- [ ] Perform proper spellcheck
- [ ] Review https://github.com/filecoin-
- [ ] Setup discussion forum and add to header
- [ ] Reach out to Venus to establish the state of their RPC
- [ ] Transfer spec repo to filecoin-project and update links above
- [ ] Add examples to all methods in spec

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).