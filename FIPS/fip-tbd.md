---
fip: "tbd"
title: More API between user-programmed actors and built-in miner actor for building decentralized staking protocol 
author:  @Schwartz10, @jennijuju
discussions-to: 
status: Draft
type: https://github.com/filecoin-project/FIPs/discussions/1034
category (*only required for Standard Track): <Core>
created: 2024-07-12
---


# FIP-TBD:  More API between user-programmed actors and built-in miner actors for building decentralized staking protocol

## Simple Summary

Export additional built-in miner actor methods for invocation by user actors, so to enable more decentralized DeFi protocol for Storage Provider (SP) services.

## Abstract

Upon the FEVM launch, [FIP-0050](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0050.md) was also introduced with a list of the builtin actor methods that are exposed as callables from user actors. Since then,  we’ve seen a number of protocols build lending or leasing applications around Miner Actors collateral & rewards. As common practice in DeFi, protocols often introduce a “liquidation” procedure that liquidates a borrower’s collateral to derisk the liquidity providers from losing lent out funds. In the process of Filecoin leasing applications, a liquidation means termination of a miner’s active sectors, facing a penalty, but recovering pledged collateral to return to liquidity providers.  Economic security of applications being built on the FEVM is important for developing trust and attracting outside capital / liquidity / investors, and understanding precise collateral values for any given miner actor is critical for a DeFi protocol’s economic security. 

This FIP aims to introduce more exported APIs in miner actor for supporting onchain liquidation procedure for decentralized staking protocol.

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

### Operation 

**TerminateSectors** In Miner Actor

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

This FIP enables more trustless and decentralized staking and DeFi protocol for token holders to partipate in. Staking and Defi protocol can drive Filecoin onchain activities, improve FIL utilities and enabling more (1) storage providers to get liquidity to join the network and prvoide storage services & secure the network consensus (2) token holders to put their FIL into use and improve Filecoin GDP. 


## Implementation

TODO

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).


