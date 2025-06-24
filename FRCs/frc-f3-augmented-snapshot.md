---
fip: "####"
title: "Augment Filecoin Snapshot with F3 data"
author: "Hailong Mu (@hanabi1224)"
discussions-to: https://github.com/filecoin-project/go-f3/issues/480
status: Draft
type: "FRC"
created: 2025-06-25
---

# FRC-####: Augment Filecoin Snapshot with F3 data

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->

Downloading F3 finality certificates from scratch takes a long time and increases the p2p network bandwidth usage.
An F3 snapshot is proposed to be included in the Filecoin CAR snapshot to reduce F3 catchup time and p2p network bandwidth usage on bootstrapping
a Filecoin node with a Filecoin snapshot.

## Abstract
<!--A short (~200 words) description of the technical issue being addressed.-->

We propose extending the Filecoin CAR snapshot with an F3 snapshot as a raw data block, and changing CAR roots to be a CID that points to a CBOR-encoded Filecoin snapshot header struct.

## Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->

The time cost and the network bandwidth usage for a new Filecoin node to catch up with all F3 finality certificates grow over time, which delays the readiness of the F3-aware V2 RPC APIs. By embedding an F3 snapshot into the current Filecoin CAR snapshot, both can be vastly reduced at the cost of a slightly increased Filecoin CAR snapshot size.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any current Filecoin implementations. -->

We propose the blow changes to the Filecoin CAR snapshot format.

- Change CAR roots to be a CID that points to a CBOR-encoded [`SnapshotMetadata`](#snapshotmetadata) struct that is stored as the first data block in the CAR.
- Store the raw [`F3Snapshot`](#f3snapshot) bytes as the second data block in the CAR when `F3Data != nil` in the metadata.

### SnapshotMetadata

```go
type SnapshotMetadata {
    HeadTipsetKey []Cid // required
    F3Data        *Cid  // optional
}
```

### F3Snapshot

An F3 snapshot contains one header block and N(N>0) data blocks in the below format:

`[Header block] [Data block] [Data block] [Data block] ...`

A header block is a CBOR-encoded [`F3SnapshotHeader`](#f3snapshotheader) with a length prefix in the below format:

`[varint-encoded length] [CBOR-encoded F3SnapshotHeader]`

### F3SnapshotHeader

```go
type SnapshotHeader struct {
	Version           uint64
	FirstInstance     uint64
	LatestInstance    uint64
	InitialPowerTable gpbft.PowerEntries
}
```

A data block is a CBOR-encoded [`FinalityCertificate`](#finalitycertificate) with a length prefix in the below format:

`[varint-encoded length] [CBOR-encoded FinalityCertificate]`

### FinalityCertificate

```go
// FinalityCertificate represents a single finalized GPBFT instance.
type FinalityCertificate struct {
	// The GPBFT instance to which this finality certificate corresponds.
	GPBFTInstance uint64
	// The ECChain finalized during this instance, starting with the last tipset finalized in
	// the previous instance.
	ECChain *gpbft.ECChain
	// Additional data signed by the participants in this instance. Currently used to certify
	// the power table used in the next instance.
	SupplementalData gpbft.SupplementalData
	// Indexes in the base power table of the certifiers (bitset)
	Signers bitfield.BitField
	// Aggregated signature of the certifiers
	Signature []byte
	// Changes between the power table used to validate this finality certificate and the power
	// used to validate the next finality certificate. Sorted by ParticipantID, ascending.
	PowerTableDelta PowerTableDiff `json:"PowerTableDelta,omitempty"`
}
```

Notes:
- `FinalityCertificate`s should be ordered by `GPBFTInstance` in ascending order, thus they can be validated and intermediate power tables can be generated while data blocks are being read in a stream.
- The first and last `FinalityCertificate` instances should match those in the header, respectively.

## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

- A filecoin node should try to read a snapshot CAR in the proposed format, and fallback to the old format to maintain backward compatibility.
- CLI options should remain unchanged to make it transparent to the node users.
- The code change in all Filecoin nodes should be shipped with a network upgrade, and the Filecoin snapshot providers should only start publishing with the new format after the mainnet upgrade finishes to avoid potential errors during snapshot import for node users.

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->

This change has minimal security implications as the additional F3 data are also stored in the node database, unencrypted. Key considerations:

- **Integrity**: The F3 snapshot can be validated.
- **Performance** The F3 snapshot data blocks can be read, validated and imported in a stream.

The change does not introduce new attack vectors or modify existing security properties of the protocol.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->

Node users should experience faster F3 bootstrapping time and less network bandwidth usage.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->

Nodes starting from a snapshot should not rely on the certificate exchange protocol to catch up with the F3 data because we expect this will get slower over time. A slow F3 catchup time leads to, e.g.

- delay in the readiness of F3-aware RPC APIs

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->

## Future Work
<!--A section that lists any unresolved issues or tasks that are part of the FIP proposal. Examples of these include performing benchmarking to know gas fees, validate claims made in the FIP once the final implementation is ready, etc. A FIP can only move to a "Last Call" status once all these items have been resolved.-->
   
## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
