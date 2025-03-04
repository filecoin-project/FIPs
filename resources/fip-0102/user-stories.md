---
fip: "0102-bis"
title: Wallet-Signing User-Stories
author: "Hugo Dias (@hugomrdias), Bumblefudge (@bumblefudge)"
discussions-to: https://github.com/filecoin-project/lotus/discussions/12761
status: Draft
type: "FRC"
created: 2025-02-10
---

# FRC-0102bis: Wallet-Signing User-Stories

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->

An enumeration of distinct user stories about end-users signing transactions and arbitrary messages with various forms of "wallet"/key-management software (browser extensions, hardware wallets, distinct agents, etc.).

## Abstract
<!--A short (~200 words) description of the technical issue being addressed.-->

This non-normative user-stories documentation is provided simply for clarity to readers and authors of future FRCs. The user stories provided and annotated (for now) are:

1. Simple Transaction Signing by a Wallet on a Website
2. Arbitrary Message Signing on a Website
3. Structured Message Signing on a Website

## Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->

Industry standards for user experience and signer safety are steadily maturing and hardening over time, and new form factors are emerging (like Passkey-controlled or conventional-wallet-controlled onchain wallets, particularly in the EVM space) which require a solid foundation of wallet-based signing standards to adopt.
For both reasons, having more consistent and explicit signing standards across today's wallets will minimize end-user risks and better position FeVM and FVM alike for developer adoption.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any current Filecoin implementations. -->

By analogy to other blockchain ecosystems, we can think of transactions as heterogenous, and we can think of additional contexts where arbitrary messages need to be signed (for authentication, for attestations, etc.)

### User Story 1: Simple Transaction Signing by a Wallet on a Website

1. Alice decides to send Bob 1Fil.
2. Alice's "hot" wallet creates the transaction internally.
3. Alice authorizes the wallet to sign it interactively.
4. Alice's hot wallet sends the transaction to a node, where it sits in the mempool, is executes, and reaches finality.

### User Story 2: Arbitrary Message Signing on a Website

1. Alice visits bob.com
2. Alice connects a FIL-supporting wallet to bob.com, exposing address C
3. bob.com wants Alice to prove control over address C that it queries over said live connection, so provides a message containing a nonce (e.g. a "sign in with Fil" message)
4. Alice's wallet parses said message, displays its contents to Alice for approval.
5. Once Alice approves, the wallet returns a valid signature over a digest of that message effectively authenticating its control over the address.
6. bob.com can check the signature against the digest of the message and verify Alice's control over C.

Notes:

1. In theory, this flow should work for any wallet, though mobile apps and browser extensions are the easiest to pipe through a browser to create a secure wallet<>dapp connection. Many mobile and browser wallets allow one to connect to dapps on behalf of an external wallet, e.g. a hardware wallet or even a CLI wallet, but ideally this pass-through would not need to be exposed to the dapp, which should be able to use the same message format and get back the same valid signature regardless.
2. Adoption of `personal_sign` has been widespread for years in the Ethereum community, while protocol-wide multisignature signing standards of the type proposed in [ERC-191] have not gained ground, displaced largely by user-space/application-level multisignature conventions.
3. The most common usecase for `personal_sign` messages was authentication, but bespoke implementations lacked basic security guarantees taken for granted in Web2, so [ERC-4361] extended the `personal_sign` envelope from [ERC-191] with a verbose ABNF-validated message template including information such as `chainId`, dapp domain-binding, and nonce requirements, as well as defining a uniform authentication receipt for better auditing of off-chain interactions.

### User Story 3: Structured Message Signing on a Website

1. Alice visits bob.com
2. Alice connects a FIL-supporting wallet to bob.com, exposing address C
3. bob.com wants Alice to make a complex attestation agreeing to terms and creating a non-repudiable receipt, so bob.com provides a complex structured message in JSON format containing fields, links, and a timestamp.
4. Alice's wallet parses this JSON and identifies one key's value as a template, replacing the template value with a user-agent string to identify itself.
5. Alice's wallet presents this updated message to Alice in the form of a specially-formated, structure-aware "invoice" modal for approval.
6. Once Alice approves, the wallet returns a valid signature over a digest of that (modified) message back to bob.com.
7. bob.com can check the signature against the digest of the message and can onchain or archive this record as a self-contained datum.

Notes:

1. EIP-712, which has significant support among EVM wallets and dapps, if less than the `personal_sign` convention used for user story #2, is fully supported by Ledger.
2. The primary adoption driver for EIP-712

### Possible standards

In the Ethereum community, user story #2 and user story #3 use specified formats ([ERC-191] and [EIP-712], respectively) to avoid messages from any of these user stories being mistaken for messages from another out of context.

For FEVM contexts, i.e. contexts where EVM wallet and dapp standards are being used to communicate with a Solidity-compatible node over EVM chainId 314 or 314159, it is recommended that user story #2 simply use [ERC-191] full-stop; a dapp that wants to authenticate an `F4` address can simply send a Sign-In With Ethereum message (see [ERC-4361]) with the appropriate chainId, which extends the [ERC-191] standard with an ABNF profile of the message content.
Similarly, a FEVM dapp can use [EIP-712] to send a structured message.

For FVM wallet-dapp connections, an FVM equivalent of `personal_sign` is defined in [FRC-XXXX].

## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

There are no backward compatibility issues for Filecoin software itself, as this FRC provides a recommendation to clients/applications with no change to the existing consensus mechanism or protocol.

Existing dapps often use "raw signing" (without any kind of safety envelope) for use cases 2 and 3 today, including today's Ledger adapter.
Deprecating these may require some coordination if a safety envelope is proposed for either or both use-cases.

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->

## Security Considerations

Security considerations should be provided separately for each FRC that addresses one or more of these user stories.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->

Incentive considerations should be provided separately for each FRC that addresses one or more of these user stories.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->

Product considerations should be provided separately for each FRC that addresses one or more of these user stories.

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->

N/a.

## Future Work
<!--A section that lists any unresolved issues or tasks that are part of the FIP proposal. Examples of these include performing benchmarking to know gas fees, validate claims made in the FIP once the final implementation is ready, etc. A FIP can only move to a "Last Call" status once all these items have been resolved.-->

Specific FIPs/FRCs may be needed for outlining new interfaces and deprecation timelines for old interfaces for:

* Lotus
* IPC L2s
* Ledger signing integration(s)

Future FIPs/FRCs may be needed to establish:

* FEVM and FVM dapp best-practice to interact with these interfaces, ideally with usable test vectors and instructions on how to test against the above signers

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).

[EIP-191]: https://eips.ethereum.org/EIPS/eip-191
[ERC-712]: https://eips.ethereum.org/EIPS/eip-712
[ERC-4361]: https://eips.ethereum.org/EIPS/eip-4361
[FRC-XXXX]: https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-XXXX.md