---
fip: <to be assigned>
title: Support for NIST P-256 keys
author: @whyrusleeping
discussions-to: <URL>
status: Draft
type: Technical (Core)
category: Core
created: Mar 13 2022
spec-sections: 
---


## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->
Add a new address type backed by NIST p256 keys, allowing the majority of existing secure enclaves (including iPhones and most android phones). This would allow very easy interactions with the Filecoin network by (for example) allowing users to send FIL securely using apple faceID or other secure enclave methods

## Abstract
Filecoin ramps should be as simple and available as possible, adding p256 opens up a whole new set of solutions for developers to integrate with.

## Change Motivation

## Specification
Add a new `f4` address prefix which uses p256 elliptic curve cryptography for signatures and verification. Everything should be treated the same as secp256k1 (`f1`) addresses, signatures are not aggregated like they would be for bls keys, and the messages on chain should include signatures and remain in the second field of the `MsgMeta` struct (which should be renamed from `SecpkMessages` to `SignedMessages`, which is a non-breaking change in the code given how encoding works).

## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->
The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.

## Backwards Compatibility
After an upgrade to this FIP, old clients will not be able to verify new blocks using the new address type.

## Test Cases

## Security Considerations
Some concerns exist about the security of p256, with some people being
suspicious that the NSA has it backdoored. I think this is unlikely, but those
who are worried about it can simply not use the new key type.


## Product Considerations
Makes the product better by allowing easy signing of transactions from your
phone, securely, without the need for an external hardware wallet.

## Implementation

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
