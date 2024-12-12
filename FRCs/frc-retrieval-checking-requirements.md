---
fip: "<to be assigned>"
title: Retrieval Checking Requirements
author: "Miroslav Bajtoš (@bajtos)"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1086
status: Draft
type: FRC
created: 2024-12-02
# spec-sections:
#   - <section-id>
#   - <section-id>
# requires (*optional): <FIP number(s)>
# replaces (*optional): <FIP number(s)>
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->

# FIP-Number: Retrieval Checking Requirements

## Simple Summary

<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->

To make Filecoin a usable data storage offering, we need the content to be retrievable. It's difficult to improve what you don't measure; therefore, we need to measure the quality of retrieval service provided by each storage provider. To allow 3rd-party networks like [Spark](https://filspark.com) to sample active deals from the on-chain activity and check whether the SP is serving retrievals for the stored content, we need SPs to meet the following requirements:

1. Link on-chain MinerId and IPNI provider identity ([spec](#link-on-chain-minerid-and-ipni-provider-identity)).
2. Provide retrieval service using the [IPFS Trustless HTTP Gateway protocol](https://specs.ipfs.tech/http-gateways/trustless-gateway/).
3. Advertise retrievals to IPNI.
4. In IPNI advertisements, construct the `ContextID` field from `(PieceCID, PieceSize)` ([spec](#construct-ipni-contextid-from-piececid-piecesize))

Meeting these requirements needs support in software implementations like Boost, Curio & Venus Droplet but potentially also updates in settings configured by the individual SPs.

## Abstract

<!--A short (~200 word) description of the technical issue being addressed.-->

When we set out to build [Spark](https://filspark.com), a protocol for testing whether _payload_ of Filecoin deals can be retrieved back, we designed it based on how [Boost](https://github.com/filecoin-project/boost) worked at that time (mid-2023). Soon after FIL+ allocator compliance started to use Spark retrieval success score (Spark RSR) in mid-2024, we learned that [Venus](https://github.com/filecoin-project/venus) [Droplet](https://github.com/ipfs-force-community/droplet), an alternative miner software, is implemented slightly differently and requires tweaks to support Spark. Things evolved quite a bit since then. We need to overhaul most of the Spark protocol to support Direct Data Onboarding deals. We will need all miner software projects (Boost, Curio, Venus) to accommodate the new requirements imposed by the upcoming Spark v2 release.

This FRC has the following goals:
1. Document the retrieval process based on IPFS/IPLD.
2. Specify what Spark needs from miner software.
3. Collaborate with the community to tweak the requirements to work well for all parties involved.
4. Let this spec and the building blocks like [IPNI Reverse Index](https://github.com/filecoin-project/devgrants/issues/1781) empower other builders to design & implement their own retrieval-checking networks as alternatives to Spark.

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->

At the moment, the retrieval process for downloading (public) data stored in Filecoin deals is lacking specification and there is very little documentation for SPs on how to correctly configure their operation to provide a good retrieval service.

The current architecture of Filecoin components does not expose enough data to enable independent 3rd-party networks to sample all data stored in Filecoin deals and check the quality of retrieval service provided by storage providers for data they are persisting.

Our motivation is to close these gaps by documenting the current IPFS/IPLD-based retrieval process and the additional requirements needed by checker networks to measure retrieval-related service level indicators.

> [!IMPORTANT]
> We fully acknowledge that the current IPFS/IPLD-based retrieval process may not be sufficient to support all kinds of retrieval clients. For example, warm-storage/CDN offerings may prefer to retrieve a range of bytes in a given Piece CID instead.
>
> Documenting alternative retrieval processes and the requirements for checking service level indicators of such alternatives is out of scope of this FRC.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

### Retrieval Process

Let's say we have a public dataset stored on Filecoin, packaged as UnixFS archive with CID `bafybei(...)` and stored on Filecoin in a piece with `PieceCID=baga...` and some `PieceSize`.

The scope of this document is to support the following retrieval process:

1. A client wanting to download the dataset identified by CID `bafybei(...)` queries an IPNI instance like [cid.contact](https://cid.contact) to find the nodes providing retrievals service for this dataset.

2. The client picks a retrieval provider that supports the [IPFS Trustless HTTP Gateway protocol](https://specs.ipfs.tech/http-gateways/trustless-gateway/).

3. The client requests the content for CID `bafybei(...)` at the URL (multiaddr) specified by the [IPNI provider result](https://github.com/ipni/specs/blob/12482e4e1bd92a7c6c079bf23f2533a4ddb9e363/IPNI.md#json-find-response) of the selected provider.

Example IPNI `ProviderResult` describing retrieval provider offering IPFS Trustless HTTP Gateway retrievals:

```json
{
  "MultihashResults": [{
    "Multihash": "EiAT38UKZPlJfhyZQH8cAMNjUPeKBfQn6HMdiqGZ2xJicA==",
    "ProviderResults": [{
      "ContextID": "ZnJpc2JpaQ==",
      "Metadata": "oBIA",
      "Provider": {
        "ID": "12D3KooWC8gXxg9LoJ9h3hy3jzBkEAxamyHEQJKtRmAuBuvoMzpr",
        "Addrs": [
          "/dns/frisbii.fly.dev/tcp/443/https"
        ]
      }
    }]
  }]
}

```

### Retrieval Requirements

1. Whenever a deal is activated, the SP MUST advertise all IPFS/IPLD payload block CIDs found in the Piece to IPNI. See the [IPNI Specification](https://github.com/ipni/specs/blob/main/IPNI.md) and [IPNI HTTP Provider](https://github.com/ipni/specs/blob/main/IPNI_HTTP_PROVIDER.md) for technical details.

2. Whenever SP stops storing a Piece (e.g. because the last deal for the Piece has expired or was slashed), the SP SHOULD advertise removal of all payload block CIDs included in this Piece.

3. The SP MUST provide retrieval of the IPFS/IPLD payload blocks via the [IPFS Trustless HTTP Gateway protocol](https://specs.ipfs.tech/http-gateways/trustless-gateway/).

### Retrieval Checking Requirements

In addition to the above [retrieval requirements](#retrieval-requirements), SPs are asked to meet the following:

#### Link on-chain MinerId and IPNI provider identity

Storage providers are requires to use the same libp2p peer ID for their block-chain identity as returned by `Filecoin.StateMinerInfo` and for the index provider identity used when communicating with IPNI instances like [cid.contact](https://cid.contact).

In particular, the value in the IPNI CID query response field `MultihashResults[].ProviderResults[].Provider.ID` must match the value of the `StateMinerInfo` response field `PeerId`.

> [!NOTE]
> This is open to extensions in the future, we can support more than one form of linking
index-provides to filecoin-miners. See e.g. [ipni/spec#33](https://github.com/ipni/specs/issues/33).

**Example: miner `f01611097`**

MinerInfo state:

```json5
{
  // (...)
  "PeerId": "12D3KooWPNbkEgjdBNeaCGpsgCrPRETe4uBZf1ShFXStobdN18ys",
  // (...)
}
```

IPNI provider status ([query](https://cid.contact/providers/12D3KooWPNbkEgjdBNeaCGpsgCrPRETe4uBZf1ShFXStobdN18ys)):

```json5
{
  // (...)
  "Publisher": {
    "ID": "12D3KooWPNbkEgjdBNeaCGpsgCrPRETe4uBZf1ShFXStobdN18ys",
    "Addrs": [
      "/ip4/76.219.232.45/tcp/24887/http"
    ]
  },
  // (...)
}
```

Example CID query response for IPFS/IPLD payload block stored by this miner ([query](https://cid.contact/cid/bafyreiat37cquzhzjf7bzgkap4oabq3dkd3yubpue7uhghmkugm5wetcoa)):

```json5
{
  "MultihashResults": [
    {
      "Multihash": "EiAT38UKZPlJfhyZQH8cAMNjUPeKBfQn6HMdiqGZ2xJicA==",
      "ProviderResults": [
        // (...)
        {
          "ContextID": "AXESIFVcxmAvWdc3BbQUKlYcp2Z2DuO2w5Fo4jmIC8IbMX00",
          "Metadata": "oBIA",
          "Provider": {
            "ID": "12D3KooWPNbkEgjdBNeaCGpsgCrPRETe4uBZf1ShFXStobdN18ys",
            "Addrs": [
              "/dns/cesginc.com/tcp/443/https"
            ]
          }
        }
      ]
    }
  ]
}
```

#### Construct IPNI `ContextID` from `(PieceCID, PieceSize)`

The advertisements for IPNI must deterministically construct the `ContextID` field from the public deal metadata - the tuple `(PieceCID, PieceSize)` - as follows:

- Use DAG-CBOR encoding ([DAG-CBOR spec](https://ipld.io/specs/codecs/dag-cbor/spec/))
- The piece information is serialised as an array with two items:
   1. The first item is the piece size represented as `uint64`
   2. The second item is the piece CID represented as a custom tag `42`
- In places where the ContextID is represented as a string, convert the CBOR bytes to string using the hex encoding.
   _Note: the Go module https://github.com/ipni/go-libipni handles this conversion automatically._

A reference implementation of this serialization algorithm in Go is maintained in [https://github.com/filecoin-project/go-state-types/](https://github.com/filecoin-project/go-state-types/blob/32f613e4d4450b09da3c81982dd6d7dba9c6f6f2/abi/cbor_gen.go#L23-L48).

**Example**

Input:

```json5
{
  "PieceCID": "baga6ea4seaqpyzrxp423g6akmu3i2dnd7ymgf37z7m3nwhkbntt3stbocbroqdq",
  "PieceSize": 34359738368 // 32 GiB
}
```

Output - ContextID (hex-encoded, split into two lines for readability):

```
821B0000000800000000D82A5828000181E203922020FC66377F35
B3780A65368D0DA3FE1862EFF9FB36DB1D416CE7B94C2E1062E80E
```

Annotated version as produced by https://cbor.me:

```
82                                      # array(2)
   1B 0000000800000000                  # unsigned(34359738368)
   D8 2A                                # tag(42)
      58 28                             # bytes(40)
         000181E203922020FC66377F35B3780A65368D0DA3FE1862EFF9FB36DB1D416CE7B94C2E1062E80E
```

## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->

The major challenge of sampling data stored on Filecoin is how to discover the payload CIDs. By
convention, clients making StorageMarket (`f05`) deals should put the payload root CID into
`DealProposal.Label` field. After the introduction of direct data onboarding that's optimized for
low gas fees, there is no longer such a field.

Secondly, the information about the root CID is not sufficient. It allows retrieval checkers have to either
fetch the root IPLD block only or the entire content. Downloading the entire content is impractical
for light clients and puts too much load on the storage/retrieval provider. We want checkers to sample the data, not perform stress testing of SPs.

To meet the above requirements, we need a solution for sampling from payload blocks in a given deal.

The natural option is to scan the piece bytes to find individual CARv1 blocks and extract payload
block CIDs. This requires the checker node to fetch the piece and implement a CAR scanner. Storage
providers are already scanning pieces for payload CIDs to be advertised to IPNI, running another
scan in every retrieval checker node is redundant and wasteful. It also makes it more involved to
implement alternate retrieval checker networks.

IPNI already contains a list of payload CIDs contained in every advertised Filecoin deal, therefore
we propose leveraging this existing infrastructure.

- Storage Providers keep advertising payload CIDs to IPNI as they do now.
- IPNI implements reverse index lookup allowing retrieval checkers to sample CIDs in a given deal.
- Retrieval checkers can easily get a sample of payload CIDs and then retrieve only the selected CID(s).
- Retrieval checking does not add any extra network bandwidth overhead to SPs beyond the actual retrieval.

### Alternatives considered

Assuming there is a limit on the size of any CAR block in a Piece, it's possible to sample one payload block using the following algorithm:

1. Let's assume the maximum CAR block size is 4 MB and we have deal's `PieceCID` and `PieceSize`.
2. Pick a random offset $o$ in the piece so that $0 <= o <= PieceSize - 2*4 MB$.
3. Send an HTTP range-retrieval request to retrieve the bytes in the range`(o, o+2*4MB)`.
4. Parse the bytes to find a sequence that looks like a CARv1 block header.
5. Extract the CID from the CARv1 block header.
6. Hash the block's payload bytes and verify that the digest equals to the CID.

The reasons why we rejected this approach:

 1. It's inefficient.

    1. Each retrieval check requires two requests - one to download ~8MB chunk of a piece, the second one to download the payload block found in that chunk.

    1. Spark typically repeats every retrieval check 40-100 times. Scanning CAR byte range 40-100 times does not bring enough value to justify the network bandwidth & CPU cost.

 1. It's not clear how can retrieval checkers discover the address where the SP serves piece retrievals.


## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

[Retrieval Requirements](#retrieval-requirements) document the current status and remove Graphsync and Bitswap protocols. Existing miner operations need to enable/configure [IPFS Trustless HTTP Gateway protocol](https://specs.ipfs.tech/http-gateways/trustless-gateway/) retrievals to meet the new requirements.

|Miner Software|Supports HTTP retrievals|Notes
|-|:-:|-|
|Boost|✅| Manual setup required: [docs](https://boost.filecoin.io/retrieving-data-from-filecoin/http-retrieval#payload-retrievals-car-and-raw).
|Curio|✅| Works out of the box
|Venus Droplet| ? | TODO: OOTB or manual setup?

[Retrieval Checking Requirements](#retrieval-checking-requirements) introduce the following breaking changes:
- Miner software must construct IPNI `ContextID` values in a specific way.
- Because such ContextIDs are scoped per piece (not per deal), miner software must de-duplicate advertisements for deals storing the same piece.

## Test Cases

<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->

Not applicable, but see the examples in [Specification](#specification).

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->



We trust SPs to honestly advertise Piece payload blocks to IPNI. Attack vector: a malicious SP can always advertise the same payload block for all pieces persisted.

TODO: describe our plan to mitigate this risk.

Free-rider problem when a piece is stored with more than one SP.
Attack vector: When a piece is stored with SP1 and SP2, then SP1 can advertise retrievals with metadata pointing to SP2's multiaddr.

We don't view this as a problem. Spark is testing that the provider is able to serve the content
from a deal on behalf of the network. IPFS and Filecoin is based on content addressing, which is
about the network’s ability to serve content, not about the ability to fetch it from a specific
location. However, clients need to know which node to at least ask for the hot copy. This is what we
can get from IPNI. What's more, this fact leaves space for SPs to try to save costs on hot storage -
they can cooperate with other SPs to guarantee that at least one hot copy is available nearby that
can be served back to the client.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->

Reliable retrieval (data availability) is a necessary condition for Filecoin to reach product-market fit. We need tools to measure and report service-level indicators related to data availability (retrieval success rate, time to first byte, and so on) to allow storage deal clients understand the quality of service offered by different SPs (and Filecoin in general).

The data produced by retrieval checker networks like Spark can be integrated into existing and new incentive mechanisms like FIL+, Filecoin Web Services, paid storage deals, and more.

In mid-2024, the FIL+ allocator compliance process started to require SPs to meet a certain threshold in Spark Retrieval Success Rate score. Since then, we have seen a steady increase in the retrieval success rate as measured by Spark. In May 2024, less than 2% of retrieval requests performed by the Spark network succeeded. In early December 2024, more than 15% retrievals succeeded. The number of SPs that are serving payload retrievals has increased from 60 in June 2024 to more than 200 in early December 2024.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->

To make Filecoin a usable data storage offering, we need the content to be retrievable. It's difficult to improve what you don't measure; therefore, we need to measure the quality of retrieval service provided by each storage provider.

This FRC enables retrieval checks based on payload sampling with support for all kinds of storage deals (f05, direct data onboarding, etc.).

The service-level indicators produced by retrieval checker networks can be integrated into incentive mechanisms like FIL+ or paid storage deals to drive improvements in the availability and reliability of retrieval service offered by individual SPs and Filecoin as a whole.


## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->

### Storage Provider Software

|Requirement|Boost|Curio|Venus
|-|:-:|:-:|:-:
|Advertises payload retrieval to IPNI|✅|✅|✅
|Trustless HTTP GW retrievals|✅|✅|?|
|Link on-chain MinerId and IPNI provider identity|✅|❌|✅
|Construct IPNI ContextID from (PieceCID, PieceSize)|❌|✅|❌

### IPNI Reverse Index

- Status: design phase
- Progress tracking: https://github.com/ipni/roadmap/issues/1

### Spark Retrieval Checkers

- Status: design phase
- Progress tracking: https://github.com/space-meridian/roadmap/issues/115

## TODO
<!--A section that lists any unresolved issues or tasks that are part of the FIP proposal. Examples of these include performing benchmarking to know gas fees, validate claims made in the FIP once the final implementation is ready, etc. A FIP can only move to a “Last Call” status once all these items have been resolved.-->

How do we want to mitigate the following attack vector(s):
- We trust SPs to honestly advertise Piece payload blocks to IPNI.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
