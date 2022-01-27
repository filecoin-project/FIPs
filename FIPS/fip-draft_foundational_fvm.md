---
fip: <to be assigned>
title: Foundational FVM
authors: Raúl Kripalani (@raulk), Steven Allen (@stebalien)
discussions-to: <URL>
status: Draft
type: Technical Core
category (*only required for Standard Track): Core
created: 2022-01-26
spec-sections: 
  - TBD
  - 
requires: N/A
replaces: N/A
---

# Foundational FVM

## Simple Summary

This FIP is the first in a series of FIPs aiming to introduce and stabilize
full user-programmability in the Filecoin network.

Ultimately, this will be achieved by replacing the current blockchain execution
layer with the Filecoin Virtual Machine (FVM). The FVM is a WASM-based Virtual
Machine capable of executing arbitrary user-provided code.

This FIP represents the _first step_ towards that objective.

The key proposal herein is for Filecoin clients to atomically switch from the
native, static VMs to a _non-programmable version of the FVM_, termed
**Foundational FVM**. The **Foundational FVM** lays out the elementary
underpinnings for upcoming user-programmability.

## Abstract

TBD after we've finished fleshing everything else out.

## Change Motivation

> Discuss the use cases we want to make possible with the FVM -- synthesise from
> the website. Then kill the buzz by saying that the Foundational FVM spec
> doesn't introduce the ability to do any of that, yet. Then explain why the
> gradual rollout (where the Foundational spec is the first step) is important.

User-deployable actors (equivalent to smart contracts in other blockchains) are
the key to unlock tremendous potential and community-driven innovation on the
Filecoin network. We envision a rich, diverse, and composable ecosystem of apps,
modules, cross-chain bridges, L2s, and more emerging on the Filecoin network as
these features become available.

Today, logic executed on the blockchain is constrained to the built-in actors
defined in the Filecoin specification.


## Specification

> This is the meatiest section. Start inside out, where inside is the WASM
> bytecode, and outside is the node:

0. General overview of what a VM is and how it operates on state (inputs,
   outputs, etc.)
1. Actors are deployed as WASM bytecode.
2. How the bytecode for actors is resolved.
3. Expectations on the bytecode.
4. Invocation container:
  - overview of "execution sandbox"
  - required WASM features; disabled WASM features
  - memory policy (min, max memory pages -- do we have any stats on this?)
  - IPLD block handling.
  - formal specification of every syscall
  - syscall low-level ABI, including how specific datatypes like CIDs,
    TokenAmounts, and others are exchanged
  - syscall errors
  - externs (what the node must provide, noting that _how_ it's done is
    FVM-implementation-dependent)
5. Exit code changes as per new errors spec.
6. Gas charging mechanics, current and hiting at future changes (noting that a
   new FIP will follow with the WASM-specific gas changes).
7. Coupling with specific actor types (init actor, account actor, and
   power/market due to circ supply syscall)

## Design Rationale

> Explain:
- Why WASM as an execution runtime.
- Why the choice to go polyglot and support EVM and future runtimes. Explain how
  this support works (in the case of the EVM).
- ...


## Backwards Compatibility

TBD.

## Test Cases

> https://github.com/filecoin-project/fvm-test-vectors

## Security Considerations

> TBD. Those resulting from a 100% switch of something so low-level as the
> execution layer of the blockchain.

## Incentive Considerations

> Explain that this FIP does not affect incentives in itself, but anticipate the
> introduction of indirect incentive changes in future FIPs, related to gas and
> the ability of FVM use cases to alter the cryptoeconomy.

## Product Considerations

> The Foundational FVM does not introduce user-facing product considerations
> (future FIPs will). However, it does introduce changes in how implementors
> will implement changes on built-in actors going forward (for the better).
> Explain the change in dynamics.

## Implementation

A reference implementation of the FVM is provided in the
filecoin-project/ref-fvm repository.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).