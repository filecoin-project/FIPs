---
fip: "**TODO**"
title: Add BLS Aggregate Signatures to FVM
author: "Jake (@drpetervannostrand)"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/840
status: draft
type: Technical (Core)
category: Core
created: 2023-09-27
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->

This FIP proposes the following changes to FVM:

1. Addition of a syscall for BLS aggregate signature verification (by definition, this also supports non-aggregate BLS signatures).
1. Removal of the syscall currently used for generic signature (i.e. Secp256k1 and non-aggregate BLS) validation, and refactoring its associated SDK function in terms of existing Secp256k1 signature syscalls and the added aggregate BLS syscall.

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->

Non-aggregate signature schemes allow one signer to sign one message, whereas aggregate signatures allow multiple parties to sign multiple messages via a single signature. Currently, FVM supports non-aggregate signature verification for Secp256k1 (ECDSA) and BLS (using curve BLS12-381) schemes. This FIP proposes adding support for BLS aggregate signature validation to FVM. 

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->

Currenty, FVM exclusively supports non-aggregate signatures via its `verify_signature` syscall; the motivation for this FIP being for FVM to additionally support aggregate signatures. The benefits of BLS aggregate signatures being that they allow multiple parties to sign multiple messages via a single constant sized signature (i.e. the size of an aggregate signature is the same as a non-aggregate) and that verification of an aggregate signature is more efficient that verifying each aggregated signature individually.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

### Interfaces

This FIP proposes the following changes to FVM's syscalls:

- Addition of a syscall `verify_bls_aggregate` for verifying a BLS aggregate signature; because the verification algorithm for non-aggregate BLS signatures is identical to that for aggregations of one signature, `verify_bls_aggregate` supports both aggregate and non-aggregate verification. The syscall's API is:

```rust
fn verify_bls_aggregate(
    aggregate_signature: &[u8; 96],
    pub_keys: &[[u8; 48]],
    plaintexts: &[&[u8]],
) -> bool;
```
- Removal of the syscall `verify_signature`, used for generic signature (i.e. Secp256k1 and non-aggregate BLS) verification.

### Actor changes

Due to the addition of a syscall in this FIP, a corresponding FVM SDK function `verify_bls_aggregate` is added to expose the new syscall. The SDK function's API is the same as that of the syscall:

```rust
fn verify_bls_aggregate(
    aggregate_signature: &[u8; 96],
    pub_keys: &[[u8; 48]],
    plaintexts: &[&[u8]],
) -> bool;
```

Due to this FIP's removal of the `verify_signature` syscall, the removed syscall's corresponding FVM SDK function `verify_signature` is refactored in terms of two existing Secp256k1 syscalls (`hash` and `recover_secp_public_key`) and the new aggregate BLS syscall (`verify_bls_aggregate`). Note that this refactor does not change the SDK function's current API, and consequently, the `verify_signature` SDK function is used only for non-aggregate signature.

```rust
// Signature and signer's address (i.e. signing public key) may be either Secp256k1 or BLS.
fn verify_signature(
    signature: &Signature,
    signer: &Address,
    plaintext: &[u8],
) -> bool;
```

### Gas Pricing

The gas pricing for `verify_bls_aggregate` is dependent upon the number of signatures aggregated and the total size (in bytes) of the signed plaintexts. The number of signatures aggregated determines the number of elliptic curve pairing operations performed by the signature verifier, and the total size of plaintexts determines the amount of hashing that a verifier must perform when mapping each plaintext to a curve point.

The gas cost of BLS aggregate signature verification is computed via:

**TODO:** add real gas costs.

```rust
const BLS_GAS_PER_PLAINTEXT_BYTE: usize = 26;
// The gas required to compute one elliptic curve pairing operation for curve BLS12-381.
const BLS_GAS_PER_PAIRING: usize = 8299302;

fn verify_bls_aggregate_gas(plaintexts: &[&[u8]]) -> usize {
    let total_plaintext_len = plaintexts.iter().map(|plaintext| plaintext.len()).sum();
    // A BLS verifier must perform one pairing operation per signature aggregated and an additional
    // pairing to map the aggregate signature to the group `Gt` of curve BLS12-381.
    let num_pairings = plaintexts.len() + 1;
    BLS_GAS_PER_PLAINTEXT_BYTE * total_plaintext_len + BLS_GAS_PER_PAIRING * num_pairings
}
```

## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->

The motivation for using BLS aggregate signatures over an alternative aggregate signature scheme is
that (non-aggregate) BLS are already supported in FVM, the changes required in FVM to support
aggregate BLS are minimal, and BLS is a widely used and well audited signature scheme. Additionally, Filecoin's BLS signatures library [`bls-signatures`](https://github.com/filecoin-project/bls-signatures) was [audited](https://research.nccgroup.com/2020/10/21/public-report-filecoin-bellman-and-bls-signatures-cryptographic-review/) by the [NCC Group](https://www.nccgroup.com) prior to Filecoin's Mainnet launch.

## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

As this FIP proposes the removal of a syscall from FVM, the changes are internally breaking (with respect to FVM), however as all current user-facing interfaces are unchanged; from the perspective of FVM users, the changes are non-breaking and additive (in that one additional syscall and SDK function are added to FVM).

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->

The core implementation of FVM's BLS aggregate signature verification is tested in [`ref-fvm/shared/src/crypto/signature.rs`](https://github.com/filecoin-project/ref-fvm/blob/master/shared/src/crypto/signature.rs) and the syscall SDK in FVM's [syscall actor integration tests](https://github.com/filecoin-project/ref-fvm/blob/master/testing/test_actors/actors/fil-syscall-actor/src/actor.rs).

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->

As FVM currently supports non-aggregate BLS signatures, this FIP does not affect FVM security.

One security consideration in using BLS aggregate signatures is that plaintexts, signed by a single aggregate signature, are required to be unique (i.e. multiple BLS private keys cannot sign the same plaintext, then proceed to aggregate those signatures).

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->

**TODO:** The addition of aggregate signatures to FVM incentivizes the use of aggregate over non-aggregate signatures, as aggregate signature validation is less computationally expensive than verifying multiple signatures individually (and thus has a lower gas cost).

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->

This FIP does not materially impact the product in any way.

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->

Using Rust-like pseudocode, the core implementation of FVM's BLS aggregate signature verification is:

```rust
fn verify_bls_aggregate(
    aggregate_signature: &[u8; 96],
    pub_keys: &[[u8; 48]],
    plaintexts: &[&[u8]],
) -> bool {
    if pub_keys.len() != plaintexts.len() {
        return false;
    }

    // Enforce uniqueness of the signed plaintexts.
    for (i, plaintext) in plaintexts.iter().take(plaintexts.len() - 1).enumerate() {
        for other_plaintext in &plaintexts[i + 1..] {
            if plaintext == other_plaintext {
                return false;
            }
        }
    }

    // Deserialize public keys and aggregate signature bytes into BLS12-381 G1 and G2 points.
    let pub_keys: Vec<G1> = pub_keys.iter().map(G1::from_bytes).collect();
    let aggregate_sig = G2::from_bytes(aggregate_signature);

    // Enforce that no public key is the G1 identity/zero point of curve BLS12-381.
    if pub_keys.iter().any(|pub_key| pub_key == G1::zero()) {
        return false;
    }

    // Hash each signed plaintext to a G2 point of curve BLS12-381.
    let digests: Vec<G2> = plaintexts.iter().map(|msg| hash_to_g2(msg)).collect();

    // Verify the aggregate signature by checking an equality of pairings (`e`):
    // `e(G1::generator(), aggregate_signature) == e(pub_key_1, digest_1) * ... * e(pub_key_n, digest_n)`.
    let mut miller_loop: Fp12 = pub_keys
        .iter()
        .zip(&digests)
        .map(|(pub_key, digest)| miller_loop(pub_key, digest))
        .product();
    miller_loop *= miller_loop(-G1::generator(), aggregate_signature);
    miller_loop.final_exponentiation() == Gt::one()
}
```

FVM uses the Rust crates [`bls-signatures`](https://github.com/filecoin-project/bls-signatures) for making and verifying BLS signatures, and [`blstrs`](https://github.com/filecoin-project/blstrs) for functionality specific to elliptic curve BLS12-381, which FVM uses for BLS signatures.

## TODO
<!--A section that lists any unresolved issues or tasks that are part of the FIP proposal. Examples of these include performing benchmarking to know gas fees, validate claims made in the FIP once the final implementation is ready, etc. A FIP can only move to a “Last Call” status once all these items have been resolved.-->

None.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).

