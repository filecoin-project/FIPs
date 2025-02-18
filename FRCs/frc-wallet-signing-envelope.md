---
fip: "<to be assigned>"
title: Wallet-Signing Envelope for Arbitrary Messages
author: "Hugo Dias (@hugomrdias), Bumblefudge (@bumblefudge)"
discussions-to: https://github.com/filecoin-project/lotus/discussions/12761
status: Draft
type: "FRC"
---

# FRC-0XXX: Wallet-Signing Envelope for Arbitrary Messages

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->

Signing arbitrary, non-transaction messages with a Filecoin or FEVM wallet opens a number of attack vectors and error cases, such as malicious message formation or non-transactions being submitted as transactions.
A simple envelope is proposed to minimize these risks and align usage patterns with other ecosystems, which has the added benefit of making decontextualized messages easier to recontextualize.

## Abstract
<!--A short (~200 words) description of the technical issue being addressed.-->

We propose reusing the Ethereum Virtual Machine's envelope for arbitrary signing as defined in [EIP-191], and adding "version bytes" to the registry defined there for new contexts specific to the FVM.
For context on the use-cases targeted by these variations, see [FRC-wallet-signing-user-stories].

## Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->

Current practices can expose users to security risks such as malicious message formation and incorrect classification of non-transaction data as transactions. The proposed wallet-signing envelope aims to mitigate these issues by standardising the signing process.

By aligning with standards from other ecosystems, like the Ethereum Virtual Machine, we enhance cross-platform compatibility and reduce the learning curve for developers and users. The introduction of a versioning system for signing envelopes also ensures adaptability to future requirements, supporting a wider range of decentralised applications while maintaining robust security and user trust.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any current Filecoin implementations. -->

(Adapted from, and extending, the earlier [ERC-191])

We propose the following format for `signed_data` interfaces:

```
0x19 <1 byte version> <version specific data> <data to sign>.
```

The initial `0x19` byte is intended to ensure that the `signed_data` will not be mistaken for a transaction and can be "sniffed" by its first byte like a [multiformats] object or a decontextualized signature. Note that `0x19` is not valid RLP encoding, which helps prevent ambiguity and misuse.

Using `0x19` thus makes it possible to extend the scheme by defining a version `0x45` (`E`) to handle these kinds of signatures.

### Registry of version bytes

Note: this extends the earlier [EIP-191] registry defined in the Ethereum community

| Version byte | Specification  | Description
| ------------ | -------------- | -----------
|    `0x00`    | [EIP-191]      | Arbitary payload with intended-audience prefix
|    `0x01`    | [EIP-712]      | Structured data compatible with EVM execution
|    `0x45`    | [EIP-191]      | `personal_sign` messages from EVM connections
|    `0x46`    | You are here   | `personal_sign` messages from FVM connections

#### Version `0x00`

```
0x19 <0x00> <intended validator address> <data to sign>
```

The version `0x00` has only `<intended validator address>` for the version specific data. In the case of a Multisig wallet that perform an execution based on a passed signature, the validator address is the address of the Multisig itself. The data to sign could be any arbitrary data.

In Ethereum contexts, there is no `chainId` affordance at the envelope layer, and little in the way of adoption.
A separate version byte may be needed for more robust support across FVM contexts, such as chain identifier for L2 contexts, key-type discriminants, etc.

#### Version `0x01`

The version `0x01` is for structured data as defined in [EIP-712], which can be verified on-chain by an Ethereum client.
Using this version byte in FVM contexts is discouraged, but in FEVM contexts, it may be used safely.

Note that in the base [EIP-712] structure, the `domainSeparator` struct includes a mandatory field for the specific `chainId` (314 for Filecoin mainnet, 314159 for Filecoin testnet, 314XXX for L2s and private FEVM networks, expressed in as a binary `uint256`) to protect against crosschain replay attacks.

#### Version `0x45` (E)

```
0x19 <0x45 (E)> <thereum Signed Message:\n" + len(message)> <data to sign>
```

The version `0x45` (E) has `<thereum Signed Message:\n" + len(message)>` for the version-specific data. The data to sign can be any arbitrary data.

> NB: The `E` in `Ethereum Signed Message` refers to the version byte 0x45. The character `E` is `0x45` in hexadecimal which makes the remainder, `thereum Signed Message:\n + len(message)`, the version-specific data.

Using this version byte in FVM contexts is discouraged, but in FEVM contexts, it may be used safely, as FEVM messages and signatures are entirely isomorphic to the EVM.

Note that in the base `0x45` structure defined in [ERC-191], there is no envelope-level affordance for including a `chainId` (314 for Filecoin mainnet, 314159 for Filecoin testnet, 314XXX for L2s and private FEVM networks) to protect against crosschain replay attacks.
For this reason, it is recommended to include this safety mechanism (and others like domain-binding or TTL or nonce) inside the payload, as is required by the standard [Sign-In with Ethereum][ERC-4361] template.

#### Version `0x46` (F)

```
0x19 <0x45 (F)> <ilecoin Signed Message:\n" + len(message)> <data to sign>
```

The version `0x46` (F) has `<ilecoin Signed Message:\n" + len(message)>` for the version-specific data. The data to sign can be any arbitrary data.

> NB: The `F` in `Filecoin Signed Message` refers to the version byte 0x46. The character `F` is `0x46` in hexadecimal which makes the remainder, `ilecoin Signed Message:\n + len(message)`, the version-specific data.

Using this version byte is recommended to discriminate between the contextual assumptions (including the set of valid key types and signature lengths) of FVM and EVM/FEVM.
Otherwise, it works identically to version `0x45` (E).

## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

There are no backward compatibility issues for Filecoin software itself, as this FRC provides a recommendation to clients/applications with no change to the existing consensus mechanism or protocol.

Existing dapps addressing User Story 2 in [FRC-XXXX] with raw/unconstrained message signing are encouraged, if the one defined above does not work for any reason, to migrate to *any* other envelope standard to minimize security risks.

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->


## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->

## Future Work
<!--A section that lists any unresolved issues or tasks that are part of the FIP proposal. Examples of these include performing benchmarking to know gas fees, validate claims made in the FIP once the final implementation is ready, etc. A FIP can only move to a "Last Call" status once all these items have been resolved.-->

Given that the FVM has different security assumptions, as well as different keytypes, reusing EIP712 as-is for FVM structured signing might create more confusion than can be justified by ease of adoption (i.e. piggybacking [EIP-712] support in Ledger and other multichain wallets).
A future FIP that defines an additional entry in the registry above, as well as on-chain verification behavior for that envelope, may be preferable to simply using the [EIP-712] format as-is.
   
## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).

[ERC-191]: https://eips.ethereum.org/EIPS/eip-191
[EIP-712]: https://eips.ethereum.org/EIPS/eip-712
[ERC-4361]: https://eips.ethereum.org/EIPS/eip-4361
[multiformats]: https://github.com/multiformats/multiformats
[FRC-XXXX]: https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-XXXX.md