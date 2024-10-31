---
fip: "00XX" 
title: Convert fundraising remainder address(es) to keyless account actor(s) 
author: Fatman13 (@fatman13)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1033
status: Draft
type: Technical
category: Core
created: 2024-07-10
---

# Convert fundraising remainder address(es) to keyless account actor(s) 

## Simple Summary

Similar to [#901](https://github.com/filecoin-project/FIPs/discussions/901), covert fundraising remainder address(es) type from a multisig to account(s) that is keyless (like f099).


## Abstract

At the moment, the actor holding the fundraising remainder is a _multisig_ actor. All signers are _secp256k1 account_ actors, secured by corresponding wallet keys. This setup leaves the ownership and control over the fundraising remainder to signers of the _multisig_ actor, which undermines the decentralized governance principle over network funds, and creates potential security leaks.

This FIP proposes to alter the type of the fundraising remainder actor from the aforementioned multisig to a keyless account actor, and further transfer the ownership, control and governance of the funds reserved from the signers of the multisig back to the network's participants via community governance.


## Change Motivation

Like how mining reserve is made into a keyless account and ready to be [potentially burned](https://github.com/filecoin-project/FIPs/discussions/1030), fundraising remainder address(es) is also in the linger troubled by similar dilemma described in motivation section of [#901](https://github.com/filecoin-project/FIPs/discussions/901). We compiled the following 4 motivations for the proposal...

### 1. follow the spec

Mining reserve in the Filecoin spec is described as the following...

> It will be up to the community to determine in the future how to distribute those tokens, through Filecoin improvement proposals (FIPs) or similar decentralized decision-making processes.
> -- excerpts from #901

[fundraising remainder](https://spec.filecoin.io/#section-systems.filecoin_token.token_allocation) in the Filecoin spec is described as the following...

> Of the Filecoin genesis block allocation, 10% of FIL_BASE were allocated for fundraising, of which 7.5% were sold in the 2017 token sale, and the 2.5% remaining were allocated for ecosystem development and potential future fundraising.

Though paragraph about fundraising remainder didn't specifically articulate "up to the community to determine" as in mining reserve, by virtue of us being a crypto / blockchain community it can be assumed **by default** it is up to the community, ie FIP process, when no governance body was mentioned to oversight the distribution.

### 2. governance

> It is worth noting that when the spec was written and when the network was first launched, the FIP process was not yet well-designed or matured to support network governance, and significant improvements have been made since then. 
> -- excerpts from #901

Similar to the point #901 made, this proposal is to amend the inadequacy that network in its early days has neglected. 

### 3. security

> This also creates a security black hole in the network where if 2 out of the 3 signer keys of f090 are compromised by malicious actors, they may cause serious economic damage to the Filecoin network. 
> -- excerpts from #901

fundraising remainder address(es) face identical security challenges as mining reserve too.

### 4. operation

> In addition, having the reserve holds in a multisig also means changes toward the mining reserve..., may need to be managed by the msig signers via signed transactions which is a huge operational overhead (and again against the principle).
> -- excerpts from #901

fundraising remainder address(es) face identical operation challenges as mining reserve too.

## Specification

Convert fundraising remainder actor type from a _multisig_ to _account_ type. The new account actor should be keyless, like `f099`.

```rust
pub struct State {
  pub address: Address,
}
```

The new fundraising remainder actor will contain a self-reference to its ID address in the `address` field.

## Design Rationale

The choice of making fundraising remainder actor to be a keyless account type is to ensure that no single actor/entity owns the control over fundraising remainder. The use of fundraising remainder will be proposed and governed by the FIP process, and further adopted by the network via network upgrades. 

## Backwards Compatibility

This change is not backwards compatible. Upon the activation of this FIP in a network upgrade:
- the actor type of fundraising remainder will be migrated from _multisig_ to _account_.
- the existing signers of the fundraising remainder multisig will no longer be able to perform operations on the actor

## Test Cases

- Get actor cid of fundraising remainder should return actor code cid of an `account`

## Security Considerations

This proposal improves the network security by removing the ownership and control of 2.5% of the total network token supply from individuals and putting it under the control of network participants via the appropriate governance processes.


## Product Considerations

This proposal places governance of the fundraising remainder funds entirely in hands of the network participants rather than key owners, thus providing greater transparency and assurance of community consultation and deliberation in appropriate future disbursement of the funds.

## Implementation

TODO 

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
