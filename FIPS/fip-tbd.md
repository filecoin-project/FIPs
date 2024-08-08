---
fip: "tbd"
title: Export sector termination method from miner acto
author:  @jennijuju, @Schwartz10, @anorth
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1034
status: Draft
type: Technical
category (*only required for Standard Track): <Core>
created: 2024-07-12
---


# FIP-TBD:  Export sector termination method from miner actor

## Simple Summary

Adds a new `TerminateSectors2` (method 37) that allow callers define the max amount of sector termination to execute immediately.
Export additional built-in miner actor methods, including the new `TerminateSectors` method for invocation by user actors, so to enable more decentralized DeFi protocol for Storage Provider (SP) services.

## Abstract

Upon the FEVM launch, [FIP-0050](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0050.md) was also introduced with a list of the builtin actor methods that are exposed as callables from user actors. Since then,  we’ve seen a number of protocols build lending or leasing applications around Miner Actors collateral & rewards. As common practice in DeFi, protocols often introduce a “liquidation” procedure that liquidates a borrower’s collateral to derisk the liquidity providers from losing lent out funds. In the process of Filecoin leasing applications, a liquidation means termination of a miner’s active sectors, facing a penalty, but recovering pledged collateral to return to liquidity providers.  Economic security of applications being built on the FEVM is important for developing trust and attracting outside capital / liquidity / investors, and understanding precise collateral values for any given miner actor is critical for a DeFi protocol’s economic security. 

This FIP aims to introduce more exported APIs in miner actor for supporting onchain liquidation procedure for decentralized staking protocol. The main one, is a method that allows user actors to terminate sectors.

## Change Motivation


As DeFi protocols on Filecoin gain traction and lock larger amounts of value, they will be targets for more attacks. As an ecosystem, we should create the necessary primitives to build secure economic applications that use miner actors as collateral.

There are a few motivations to this change:

Trustless DeFi - it’s important that users of a DeFi protocol can trust code and not humans to protect their assets. When humans are in the loop, there is necessarily a “judgment call zone”, which violates all aspects of DeFi, it also creates personal safety issues for individuals who are known to process liquidations with no plausible deniability. 
Liability concern - from the DeFi protocol creator’s perspective, being an external third party that has to process liquidations off chain (rather than creating a keeper network of liquidators) introduces liability and regulatory concern to the protocol, making it harder to operate in certain jurisdictions 
Incentive design - by designing their own rulesets for liquidations, application developers can incentivize keepers to protect their protocol in a decentralized manner


This FIPs propose builtin actors APIs that can provide information/functionalities that staking protocols often need to build offchain logics/oracles for:
- triggering sector termination. 
- compute collateral/reward values (significantly bloating the surface area of attack vectors for any lending / leasing protocol). 

## Specification

Following the FIP-0050 specification for exported builin actor methods in, we add a set of additional methods.

**TerminateSectors2** In Miner Actor

To allow caller (storage providers, stake pools and etc) to have more precised control over the amount of the sectors to be terminated based on their operational needs, this FIP introduces a new `TerminatedSector2` method. This method follows most of the behaviour of the existing `TerminateSectors` method, notably:
- Only a control address of the miner actor can call this method.
- Terminating sectors that is in the current or the next deadline to prove will fail with `USR_ILLEGAL_ARGUMENT`.
- The method will always process the sector that is already in the `early_termination` queue before processing newly submitted sectors.

It does the following differently:
- Instead of a hardcoded max amount of termination (3000 sectors), It takes a `max_termination` /...
- It will not add sectors to the terminatoon queue.

Export the existing TerminateSectors method with the following change:

```rust
pub struct TerminateSectorsParams {
   pub terminations: Vec<TerminationDeclaration>,
}
```

`Vec<TerminationDeclaration>` can be nullable. When it is null, flush/terminate the sectors that are queued up in the cron for termination.

To prevent the same sectors to be added to the termination queue in the cron and consume block space maliciously, calling this method will immediately terminate the sectors in early_terminations queue first, then execute termination of  the sectors submitted in TerminationDeclaration. 


```rust
pub struct TerminateSectorsReturn {
   pub done_sectors: BitField,
   pub pending_sectors: BitField,
}
```

Update the return value of the method to include sector numbers that are successfully terminated or still pending in the queue.. 

### Read only methods in miner actor

- GetAvailableBalance
- GetLockedReward
- GetLockedInitialPledge
- GetExpectedRewards
<!--TODO: add FRC42 method IDs-->


## Backwards Compatibility

This FIP introduces new builtin actor methods, therefore needs a new actors version shipped in a network upgrade. No breaking changes to existing methods, however.

## Test Cases

- User actors can call all exported methods
- Newly introduced methods are correct


## Security Considerations

No new method is being introduced that can be used to attack the network, and bugs in the implementation will only lead to incorrect behavior being observed by user actors.

## Product and Incentive Considerations

This FIP enables more trustless and decentralized staking and DeFi protocol for token holders to partipate in. Staking and Defi protocol can drive Filecoin onchain activities, improve FIL utilities and enabling more (1) storage providers to get liquidity to join the network and provide storage services & secure the network consensus (2) token holders to put their FIL into use and improve Filecoin GDP. 


## Implementation

TODO

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).


