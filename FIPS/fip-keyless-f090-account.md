---
fip: "TBD" 
title: Convert f090 Mining Reserve actor to a keyless account actor
author: Jennifer Wang (@jennijuju), Jon Victor (@jnthnvctr)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/901
status: Draft
type: Technical
category: Core
created: 2024-01-04
---

# Convert f090 Mining Reserve actor to a keyless account actor

## Simple Summary

Covert f090 (FIL mining reserve) actor type from a _multisig_ to an _account_ that is keyless (like `f099`).


## Abstract

At the moment, the actor holding the FIL mining reserve is a _multisig_ actor sitting at address `f090`. It has 3 signers and an approval threshold of 2. All three signers are _secp256k1 account_ actors, secured by corresponding wallet keys. This setup leaves the ownership and control over the mining reserve funds to signers of the _multisig_ actor, which undermines the decentralized governance principle over network funds, and creates potential security leaks.

This FIP proposes to alter the type of the FIL mining reserve actor from the aforementioned multisig to a keyless account actor, and further transfer the ownership, control and governance of the funds reserved from the signers of the multisig back to the network's participants via community governance.


## Change Motivation

As documented in the spec [here](https://spec.filecoin.io/#section-systems.filecoin_token.token_allocation), upon network launch, a pool of tokens was allocated as a Mining Reserve to support the maintenance of a robust Filecoin economy. It also mentions, "It will be up to the community to determine in the future how to distribute those tokens, through Filecoin improvement proposals (FIPs) or similar decentralized decision-making processes." It is worth noting that when the spec was written and when the network was first launched, the FIP process was not yet well-designed nor matured to support network governance, and significant improvements have been made since then.

At the moment, the actor holding the FIL mining reserve is `f090`, which is a multisig actor with 3 signers and an approval threshold of 2. All three signers are account actors, with wallet keys to those accounts. This means three individuals hold the keys to three wallets and can move funds and change the terms of f090, as long as 2 out of 3 signers approve the same transactions. They can do so without anyone else's approval, speaking protocol-wise. This opposes the decentralized governance principle as quoted in the above paragraph from the spec. This also creates a security gap in the network where if 2 out of the 3 signer keys of f090 are compromised by malicious actors, they may cause serious economic and reputational damage to the Filecoin network.

In addition, having the reserve held in a multisig also means changes regarding use the reserve may need to be managed by the msig signers via signed transactions which is a huge operational overhead (and again against the principle).

The proposal here is rather simple: to convert the f090 actor type from a *multisig* to an *account* type (without any keys, like `f099`), and any changes to the mining reserve must be proposed via FIPs, governed by the FIP and network upgrade process.

## Specification

Convert f090 actor type from a _multisig_ to _account_ type. The new account actor should be keyless, like `f099`.

```rust
pub struct State {
  pub address: Address,
  
}
```

The new f090 account actor will contain a self-reference to its ID address in the `address` field.

## Design Rationale

The choice of making f090 actor to be a keyless account type is to ensure that no single actor/entity owns the control over Filecoin mining reserves. The use of the mining reserves will be proposed and governed by the FIP process, and further adopted by the network via network upgrades. 

## Backwards Compatibility

This change is not backwards compatible, upon the activation of this FIP in network upgrade:
- the actor type of f090 will be migrated from a _multisig_ to _account_.
- the existing signers of f090 multisig will no longer be able to perform multisig operations of the actor

## Test Cases

- Get actor cid of f090 it should return actor code cid of an `account`

## Security Considerations

This proposal improves the network security by removing the ownership and control of 15% of the total network token supply from 3 individuals to the network participants.


## Product Considerations

This proposal places governance of the reserved funds entirely in hands of the network participants rather than 3 key owners, thus providing greater transparency and assurance of community consultation and deliberation in appropriate future disbursement of the funds.

## Implementation

TODO 

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
