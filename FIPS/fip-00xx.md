---
fip: "0061"
title: WindowPoSt Grindability Fix
author: @cryptonemo @Kubuxu  @DrPeterVanNostrand @Nicola @porcuquine @vmx
discussions-to: https://github.com/filecoin-project/FIPs/discussions/656
status: Draft
type: Technical (Core)
category Core
created: 2023-03-09
spec-sections:
  - Specification
---

## Simple Summary

This proposal fixes a potential security issue related to sector ordering during WindowPoSt, with no impact on performance.

## Abstract

It's been recognised that WindowPoSt challenge generation depends on the order of the provided sectors.  This is inherent to the specified challenge generation algorithm, which had been audited but can be viewed as a bug in the protocol. If exploited by a Storage Provider, it would reduce the security guarantees of WindowPoSt.

This proposal eliminates this concern by making the generation of WindowPoSt challenges independent of the order of the provided sectors.

## Motivation

In short, challenge generation is the process by which node (i.e. sector data) challenges are selected for each sector.  Ideally, the challenges are random and equally distributed (both across sector data and across all sealed sectors), so that each sector is challenged uniquely to ensure that all sector data has integrity over time.

Given that there is a relationship between challenge generation and the sector order provided in WindowPoSt, it is feasible for malicious Storage Providers to gain influence over the challenges during WindowPoSt by re-ordering the provided sectors in a way that provides benefits beyond what is allowed in the protocol.

## Specification

This proposal aims to change WindowPoSt challenge generation so that the derivation of each sector's set of challenges is independent of the other sectors challenged during WindowPoSt.

This prevents all avenues of grinding WindowPoSt challenges as long as the sector stays within one deadline.

### New WindowPoSt Proof Type

We propose adding the following types to the defined Registered Proofs types:

```
    StackedDrgWindow2KiBV1_1
    StackedDrgWindow8MiBV1_1
    StackedDrgWindow512MiBV1_1
    StackedDrgWindow32GiBV1_1
    StackedDrgWindow64GiBV1_1
```

These new types will signal to Proofs via the API to use the updated WindowPoSt behaviour.

### Changes to Challenge Generation

Differences between the currently deployed WindowPoSt challenge generation and the proposed updated challenge generation are as follows:

Current algorithm for generating a sector's WindowPoSt challenges:
- Note that `sector_index` and `challenge_index` are across all partitions and sectors of a WindowPoSt.

```rust

let sector_index = partition_index * num_sectors_per_partition + sector_index_in_partition;
let first_challenge_index = sector_index * challenge_count_per_sector + challenge_index_in_sector;
let sector_challenge_indexes = first_challenge_index..first_challenge_index + challenge_count_per_sector;
for challenge_index in sector_challenge_indexes {
    let rand_int = u64::from_le_bytes(sha256(chain_randomness || sector_id || challenge_index)[..8]);
    let challenge = rand_int % sector_nodes;
}

```

Updated algorithm:
- Note that `challenge_index` is now relative to a sector (as opposed across all WindowPoSt partitions and sectors).

```rust

let sector_challenge_indexes = 0..challenge_count_per_sector;
for challenge_index in sector_challenge_indexes {
    let rand_int = u64::from_le_bytes(sha256(chain_randomness || sector_id || challenge_index)[..8]);
    let challenge = rand_int % sector_nodes;
}

```

### Actor Changes

The new WindowPoSt proof will be accepted beginning with network version 19.
The old WindowPoSt proof will continue to be accepted until network version 20 to give Storage Providers ample time to update their storage maintenance systems.
The creation of new miner actors with the old proof type will be disallowed beginning with network version 19.

### Proof Changes

The ability to prove and verify WindowPoSt with the new challenge generation algorithm will be exposed. Since this is a breaking change, a new `ApiVersion` flag is introduced to specify which challenge generation algorithm is used. A new WindowPost proof type will be defined at the proofs API layer, which will use the new challenge generation.

## Design Rationale

This is a subtractive change, removing information about where the sector is placed within the proof from challenge generation, and thus removing a degree of freedom. This additional degree of freedom is what allows for possible grinding on challenges for a given sector.

As it is a subtractive change, it is necessary to explore why `challenge_index` was originally taken to be across all WindowPoSt sectors. The initial design goal of challenge generation was to guarantee uniqueness of challenges; this design also left open the possibility of enforcing WindowPoSt sector ordering at the protocol-level. In addition to `challenge_index`, challenge generation depends on chain randomness and the challenged sector's SectorID. As SectorID is guaranteed to be unique within the scope of a Storage Provider (and consequently within the scope of a WindowPoSt), this FIP's proposed change preserves uniqueness of challenges via the maintained inclusion of SectorID in the challenge generation algorithm.

## Backwards Compatibility

This change would introduce a way to specify which challenge generation method is to be used and accepted on chain.  For some time, the old algorithm would be used and at some point it will no longer be accepted.

## Test Cases

Test cases of proofs are included in the Proofs code.
Test cases for Actors are TBD.

## Security Considerations

While we believe this issue cannot be successfully exploited for gain due to limitations imposed by other parts of the Filecoin system, the security of individual system components (e.g. WindowPoSt) is important for maintaining a secure network.

## Incentive Considerations

This proposal does not affect the current incentive system of the Filecoin network.

## Product Considerations

This proposal has no product implications.

## Implementations

TODO

## Copyright Waiver

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
