---
fip: "<to be assigned>" <!--keep the qoutes around the fip number, i.e: `fip: "0001"`-->
title: Add EVM precompile to fetch beacon digest from chain history 
author: @ZenGround0, @anorth
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1051
status: Draft
type: Technical Core
created: 2024-08-26
---

# FIP-00XX: Add EVM precompile to fetch beacon digest from chain history 

## Simple Summary

Adds a precompile to the EVM actor to allow smart contracts to fetch drand beacon digests from the chain history.

## Abstract
The FVM exposes a syscall for fetching the digest of a drand beacon included in some prior Filecoin chain header.
The built-in actors use this facility to provide randomness for storage proofs.
This proposal introduces an EVM actor precompile exposing this functionality to user-deployed smart contracts
so that they can also use random challenges for other types of proofs.

## Change Motivation
A source of un-biasable randomness is a useful primitive in proofs of service, 
as evidenced by its use in Filecoin's existing proof of storage protocol.
The Filecoin blockchain already embodies all the infrastructure to provide this primitive, 
but is missing the hook-up to where user-deployed smart contracts can use it. 
This proposal provides that hook-up.

The EVM does already provide a PREVRANDAO opcode, but this is limited to access randomness from the immediately prior epoch.
This is primitive is not suited to protocols where the randomness is incorporated into off-chain protocols, 
since the prover must observe the randomness, use it for computation, and submit a message that must be included in the immediate next epoch 
in order for a smart contract to be able to verify that the correct randomness source was used.
Access to values from prior epochs allows for protocols that commit to a challenge before it is used,
take more than one epoch to complete, and/or are robust to short-lived chain instability or forks.

The concrete use case motivating the authors is to make it possible to build a proof-of-data possession in user-deployed smart contracts

## Specification
A new precompile is added to the built-in EVM actor, which implements all user-deployed smart contracts.

The precompile is callable at address `0xfe00..04`.

| Param            | Value                     |
|------------------|---------------------------|
| epoch            | U256 - low i64            |

The call errors with `PrecompileError::InvalidInput` if the epoch is not a valid, prior epoch number.

This calls directly to the FVMs `get_beacon_randomness` syscall, which returns a Blake2b hash digest of the 
randomness value from the drand beacon at the associated Filecoin epoch.

The existing syscall has a gas cost function that scales linearly with the number of epochs that have elapsed since 
the requested epoch.

## Design Rationale
The beacon value is provided in as raw a form as possible, given the FVM already hashes the beacon randomness.
Including further entropy is left to the caller.

Adding a new syscall to return the un-hashed beacon randomness would add complexity without adding fundamental capability.
If a full drand beacon is required (e.g. for time-lock operations), a user-submitted beacon can be validated by hashing it
and comparing with the value returned by the new precompile.

## Backwards Compatibility
This proposal introduces a new precompile available to FEVM smart contracts.

Any existing smart contract which invokes this previously-unbound address will now observe a successful call.

## Test Cases
As part of implementation we should have:
1. Builtin actors tests that the precompile is accessible and returning the correct randomness as specified by the testing runtime.  
2. Integration tests on a lotus devent with a simple solidity contract that uses the precompile.
3. Integration tests that validate that gas costs are as expected
4. Integration tests that validate that very deep lookback has computational cost in proportion to the gas cost (linear).
5. Integration tests that validate that requesting future randomness results in an error.

## Security Considerations
Inspecting early chain history can involve increasing computational cost.
Client implementations with a computational cost that exceeds the gas charged for deep look-backs could face
a denial-of-service attack.

## Incentive Considerations
This proposal has no impact on incentive considerations for the core Filecoin protocol.

Smart contracts using the new precompile will face gas costs that scale linearly with the depth of look-back.
This incentive aligns users to query recent randomness stored in cached blocks, with less burden on the system.

## Product Considerations
Precompiles are a standard feature of the EVM that developers are familiar with.  
The proposed precompile is specific to Filecoin.
Smart contracts that make use of it may not be portable to other EVM environments that don't provide historical randomness.
This proposal thus represents an additional capability that the FEVM environment can offer, 
and one that is specifically useful for proofs of space and storage. 

## Implementation
Draft PR: https://github.com/filecoin-project/builtin-actors/pull/1577

## TODO
<!--A section that lists any unresolved issues or tasks that are part of the FIP proposal. Examples of these include performing benchmarking to know gas fees, validate claims made in the FIP once the final implementation is ready, etc. A FIP can only move to a “Last Call” status once all these items have been resolved.-->

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
