---
fip: "TBD"
title: Piece Multihash
author: "Adin Schmahmann (@aschmahmann), Peter Rabbitson (@ribasushi), ..."
discussions-to: https://github.com/filecoin-project/FIPs/discussions/759
status: Draft
type: FRC
created: 2023-MM-DD
---

# Piece Multihash and v2 Piece CID

## Simple Summary

Introduce an alternative CID representation for the FR32 padded sha256-trunc254-padded binary merkle trees used in Filecoin Piece Commitments (i.e. CommP). In it we use the [Raw codec](https://github.com/multiformats/multicodec/blob/566eaf857a9d20573d3910221db7b34d98e8a0fc/table.csv#L41) and a new [sha2-256-trunc254-padded-binary-tree multihash (or piece multihash)](https://link.tld) rather than the [Fil-commitment-unsealed codec](https://github.com/multiformats/multicodec/blob/566eaf857a9d20573d3910221db7b34d98e8a0fc/table.csv#L517) and the [sha2-256-trunc254-padded multihash](https://github.com/multiformats/multicodec/blob/566eaf857a9d20573d3910221db7b34d98e8a0fc/table.csv#L149).


## Abstract
This specification describes a new way to reference Pieces using CIDs.

While the current way of describing Piece CIDs (i.e. with the fil-commitment-unsealed codec and sha2-256-trunc254-padded multihash) has been useful for some purposes in practice it turns out to be much more useful to be able to express the tuple of (Root hash, size of tree) than just the root hash.

For example, in much of the relevant portions of the Filecoin spec and lotus' Go code Piece CIDs are not used on their own, but rather combined with the piece size in the [Piece Info](https://pkg.go.dev/github.com/filecoin-project/go-state-types@v0.11.0/abi#PieceInfo) type. For example in the [Storage Proving Subsystem](https://github.com/filecoin-project/specs/blob/e5d44e1bdac4635997f3aaa917511016842a50e5/content/systems/filecoin_mining/storage_proving/storage_proving_subsystem.id#L10-L11).

Similarly this makes it much more natural to work with new concepts like [Deal Aggregates](https://pkg.go.dev/github.com/filecoin-project/go-data-segment@v0.0.0-20230605095649-5d01fdd3e4a1/datasegment#NewAggregate) proposed in [FRC-0058](https://github.com/filecoin-project/FIPs/blob/7e499523c9c7ed2c48c6a36967f7f011cee1fefd/FRCs/frc-0058.md).

To resolve this we introduce a new multihash type [fr32-sha2-256-trunc254-padded-binary-tree multihash](https://link.tld) which combines the root hash with the tree height (which in the full and balanced binary trees used in Piece commitments is equivalent to size).

## Specification

A CIDv1 requires a:
- codec
- multihash

### fr32-sha2-256-trunc254-padded-binary-tree multihash

The core component introduce in this specification is a new multihash type fr32-sha2-256-trunc254-padded-binary-tree multihash.

The multihash code for this type is 0x1011 as identifier in the [multicodec code table](https://link.tld).

The digest for the multihash is 33 bytes. The first byte defines the height of the tree. For example if the first byte is 0 the tree is a single 32-byte leaf. Similarly, if the first byte is 30 then the tree is 30 levels deep which, since the leaves must be 32 bytes, represents a piece of size 32*2^30 bytes = 32GiB.

Note that the data processed by this hash function must be of size `N = 2^i * 127/128` where `i` is any positive integer >=7 and <=255. This means that the minimum hashable amount of data is 127 bytes.

### Raw codec

There is currently no specific semantics associated with what data must go into a Piece. Therefore, we use the [Raw codec](https://github.com/multiformats/multicodec/blob/566eaf857a9d20573d3910221db7b34d98e8a0fc/table.csv#L41).

## Design Rationale
The overall design rationale was guided by the desire to:
1. have a CID (Content IDentifier) that contains enough information to work with a Piece
2. be an easy conversion with major uses of Piece CIDs today (which tend to move along with sizes)
3. be simple to understand and implement
4. have a Piece CID that reasonably fits the IPLD Data Model

The first criteria is met by embedding size information in the CID (via the multihash digest). The second is met by being able to convert between v1 and v2 Piece CIDs. The third is met by the spec implementation being tiny. The fourth is met by using the codec to note that the bytes in the Piece are of an unknown type, but can be verified with the given multihash.

## Backwards Compatibility

This FRC describes an alternative CID format for referencing Pieces. However, this is not a FIP for changing how CommPs are stored or used on chain, but rather a more user-friendly way of referencing Pieces which can be used in various non-chain interactions (e.g. piece-based retrieval, smart contract interactions, etc.).

A tuple of (v1 Piece CID, Piece size) can be converted into a valid v2 Piece CID and similarly a v2 Piece CID can be converted into the tuple of (v1 Piece CID, Piece size).

## Test Cases

Take data of size 127*4 bytes where the first 127 bytes are 0, the next 127 are 1, the next 127 are 2, and the last 127 are 3. The v1 piece CID of this data would be `baga6ea4seaqes3nobte6ezpp4wqan2age2s5yxcatzotcvobhgcmv5wi2xh5mbi`. The multihash-based piece CID would be `bafkzcibbarew3lqmzhrgl37fuadoqbrguxofyqe6luyvlqjzqtfpnsgvz7lak`. With a base16 multibase this would be `f015591202104496dae0cc9e265efe5a006e80626a5dc5c409e5d3155c13984caf6c8d5cfd605` or equivalently (`(multibase = f) | (CIDv1 prefix = 0x01) | (Raw codec = 0x55) | (fr32-sha2-256-trunc254-padded-binary-tree multihash encoded varint = 0x9120) | (length of digest = 0x21) | (tree height = 0x04) | (underlying hash digest = 496...605)`)

Given the piece CID v1 of the empty 32 GiB piece `baga6ea4seaqao7s73y24kcutaosvacpdjgfe5pw76ooefnyqw4ynr3d2y6x2mpq` the corresponding mutlihash piece CID would be `bafkzcibbdydx4x66gxcqveyduviaty2jrjhl5x7ttrbloefxgdmoy6whv6td4`

Given the piece CID v1 of the empty 64 GiB piece `baga6ea4seaqomqafu276g53zko4k23xzh4h4uecjwicbmvhsuqi7o4bhthhm4aq` the corresponding piece mutlihash piece CID would be `bafkzcibbd7teabngx7rxo6ktxcww56j7b7fbasnsaqlfj4vech3xaj4zz3hae`

## Security Considerations
Does not impact core Filecoin security.

## Incentive Considerations
Does not impact current incentive systems.

## Product Considerations
Using Piece Multihash CIDs as defined in this FRC would be used when working with Piece CIDs including in the [Piece Retrieval FRC](https://github.com/filecoin-project/FIPs/blob/10e1b3ea52416bfad85152698f86353d11c29d57/FRCs/piece-gateway.md).

This also enables the use of IPFS-based tooling for moving around Pieces, with the same guarantees around content-addressing, verifiability, etc. In this way the new Piece multihash operates in effectively the same way as Blake3 (another merkle-tree based hash) does.

## Implementation

- There is a Go implementation in a [fork of go-fil-commcid](https://github.com/filecoin-project/go-fil-commcid/pull/5) which can get merged [upstream](https://github.com/filecoin-project/go-fil-commcid) upon acceptance of the FRC.
- There is a JavaScript implementation in https://github.com/web3-storage/data-segment/

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/)