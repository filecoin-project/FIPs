---
fip: "tbd"
title: Export sector termination method from miner actor
author:  @jennijuju, @stebalien, @anorth, @Schwartz10, 
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1034
status: Draft
type: Technical
category (*only required for Standard Track): <Core>
created: 2024-07-12
---


# FIP-TBD:  Export sector termination method from miner actor

## Simple Summary

Adds a new `TerminateSectors2` (method 37) that allows callers to submit sectors for termination and define the maximum amount of sectors to be terminated immediately.

Expose `TerminateSectors2` method for invocation by user actors, so to enable more decentralized DeFi protocol for Storage Provider (SP) services.

## Abstract

Following FEVM launch, [FIP-0050](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0050.md) introduced a list of builtin actor methods that are exposed as callables from user actors. Since then, we have seen a number of protocols use miner actor collateral and/or rewards to build lending and leasing applications. 

It is a common practice in DeFi applications to manage risk for liquidity providers (i.e., those lending money) by "liquidating" collateral supplied by borrowers. In the Filecoin ecosystem, 'liquidation' is achieved when Storage Providers terminate a miner's active sectors, pay the required penalty, recover their pledged collateral, and repay liquidity providers. This process is a critical part of FEVM economic security, as is understanding the precise value of existing collateral. 


This FIP aims to introduce an exported sector termination method in miner actor to support on-chain liquidation procedures. 

## Change Motivation

As DeFi protocols on Filecoin gain traction and lock larger amounts of value, they will be targets for more attacks. As an ecosystem, we should create the necessary primitives to build secure economic applications that use miner actors as collateral.

There are a few motivations to this change:

- Trustless DeFi - it’s important that users of a DeFi protocol can trust code and not humans to protect their assets. When humans are in the loop, there is necessarily a “judgment call zone”, which violates all aspects of DeFi, it also creates personal safety issues for individuals who are known to process liquidations with no plausible deniability. 
- Liability concern - from the DeFi protocol creator’s perspective, being an external third party that has to process liquidations off chain (rather than creating a keeper network of liquidators) introduces liability and regulatory concern to the protocol, making it harder to operate in certain jurisdictions 
- Incentive design - by designing their own rulesets for liquidations, application developers can incentivize keepers to protect their protocol in a decentralized manner

This FIPs propose a builtin actors APIs that can trigger sector termination in smart contracts that staking protocols often need to build offchain logics/oracles for currently. 

## Specification

Expose the following APIs, following the FIP-0050 specification for exported builtin actor methods.

**TerminateSectors2** In Miner Actor

To allow caller (storage providers, stake pools and etc) to have more precise control over the amount of the sectors to be terminated based on their operational needs, this FIP introduces a new `TerminateSector2` method. This method follows most of the behaviour of the existing `TerminateSectors` method (method 9), notably:
- Only a control address of the miner actor can call this method.
- Attempt to terminate sectors that is in the current or the next proving deadline will fail with `USR_ILLEGAL_ARGUMENT`.
- The method will always process the sector(s) that are already in the `early_termination` queue before processing newly submitted sectors.

This FIP proposes the following behaviour changes:
- Currently, `TerminateSectors` allows callers to submit early termination for at most 3000 sectors in one message. `TerminateSectors2` will remove this hardcoded upper bound. Instead, `TerminateSectors2` takes a `max_termination` parameter for caller to specify the maximum number of sectors to be terminated. 
- `TerminateSectors2` will always first terminate the sectors that are already in the `early_termination` queue (either added through cron or through `TerminateSectors(2)` messages), then process the new sectors submitted in the message. This prevents the same sectors to be added to the termination queue in the cron and consume block space maliciously.
 - A newly submitted sector will be skipped if it was already in the `early_termination` queue and got executed first, so that the sector will not be terminated twice. 
- `TerminateSectors2` will only terminate sectors up to the number caller specified in the `max_termination` parameter. If there are more sectors in `early_termination` queue and the new sectors submitted in the message than the `max_termination` amount, the message will fail with `USR_ILLEGAL_ARGUMENT`. 
  - Caller can query the `early_termination` queue size ahead of submitting the message to determine the maximum number of sectors and/or new sectors it can terminate in one message.
  - That said, `TerminateSectors2` will not add sectors to the termination queue.
- `TerminateSectors2` will fail with `SYS_OUT_OF_GAS` and abort the all execution if the caller doesn't have enough gas to execute the termination and/or the message itself run out of gas.

The `TerminateSectors2Params` follows the existing `TerminateSectorsParams` structure, with an additional `max_termination` parameter.

`Vec<TerminationDeclaration>` can be nullable. When it is null, flush/terminate the sectors that are queued up in the cron for termination.

```rust
pub struct TerminateSectors2Params {
 pub terminations: Option<Vec<TerminationDeclaration>>,
    pub max_termination: u64,
}

pub struct TerminateSectors2Return {
    // Set to true if all early termination work and new sectors termination work have been completed. Set to false otherwise.
    pub done: bool,
}
```

**TerminateSectors2Exported** In Miner Actor

Add `TerminateSectors2Exported` method to Miner builtin actor. The method ID is `2777360141`.  


## Backwards Compatibility

This FIP introduces new builtin actor methods, therefore needs a new actors version shipped in a network upgrade. No breaking changes to existing methods, however, existing methods may be deprecated in future network upgrades.

This FIP does not require a state migration.

## Test Cases

- TODO


## Security Considerations

No new method is being introduced that can be used to attack the network, and bugs in the implementation will only lead to incorrect behavior being observed by user actors.


To prevents the same sectors to be added to the termination queue in the cron and consume block space maliciously with programmatic smart contracts, `TerminateSectors2` will not add any sectors to the cron queue and it will always terminate the sectors that are already in the `early_termination` queue first, then process the new sectors submitted in the message and skip the sectors that are already in the `early_termination` queue. 

While the newly introduced `TerminateSectors2` method allows a smart contract to terminate a sector on SPs behalf, it still requires the SP to add the smart contract as a control address first. When SPs signs and send the message to add smart contract as a control address, this should be considered as a high trust action, as the SP is authorizing the control right to the smart contract. 

## Product and Incentive Considerations

This FIP enables more trustless and decentralized staking and DeFi protocol for token holders to participate in. Staking and Defi protocol can drive Filecoin onchain activities, improve FIL utilities and enabling more (1) storage providers to get liquidity to join the network and provide storage services & secure the network consensus (2) token holders to put their FIL into use and improve Filecoin GDP. 


## Implementation

TODO

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).


