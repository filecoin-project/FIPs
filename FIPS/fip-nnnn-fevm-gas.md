---
fip: "<to be assigned>"
title: Update gas charging schedule and system limits for FEVM
author: Steven Allen (@stebalien), Raúl Kripalani (@raulk), Akosh Farkash (@aakoshh)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/588
status: Draft
type: Technical Core
category (*only required for Standard Track): Core
created: 2022-12-12
spec-sections:
  - <section-id>
  - <section-id>
requires: 0032, PR-512 (draft)
---

## Simple Summary

With the introduction of user programmable smart contracts, we need to ensure that the gas model accurately reflects the cost of on-chain computation. In the current network, users can only trigger course-grained behaviors by submitting messages to built-in actors. However, with the introduction of FEVM, users will be able to deploy new smart contracts with fine-grained control over FVM execution. If we don't carefully tune the gas model to accurately charge for computation, an attacker could carefully construct a contract to take advantage that and slow down or even stop chain validation.

## Abstract

This FIP proposes a few adjustments to the gas charging schedule. Specifically:

- Adjustments to some syscall gas:
    - State read and write costs.
    - Internal send costs.
    - Hashing, signature verification, and randomness.
- Variable charges for memory initialization, copying, and allocation.
- New charges for state-tree reads and writes.
- New charges for actor address resolution.

This FIP also introduces overall memory limits. However, these memory limits currently only include Wasm memories and table elements (not IPLD blocks, wasm _code_, and other metadata).

Finally, this FIP reduces the maximum recursive call depth limit from 1025 to 1024 to bring it in-line with the initial intentions of this limit and other blockchain VMs.

## Change Motivation

With the introduction of FEVM, users will be able to trigger operations that were previously priced according to "expected costs". These prices took things caching, overall message execution costs, and size limits imposed by the actors themselves into account. Unfortunately, with the introduction of FEVM, these assumptions no longer hold.

With a FEVM contract, users can:

1. Perform operations that have runtime cost varying in the size of the inputs (bulk memory copies, hashing, etc.). These operations previously had fixed costs.
2. Make state read and write operations that have not been re-priced since network launch. These prices were estimated before the FVM existed, and while the state-tree was quite small.
3. Make syscalls that were previously expected to have their costs amortized over the execution of the transaction as a whole. Unfortunately, with FEVM, prices must assume random pathological access.
4. Allocate arbitrary amounts of memory. Existing built-in actors have explicit limits to avoid running out of memory, but FEVM requires system-imposed global memory limits.

## Specification

Notes:

- Filecoin targets 10 gas/ns. That is, an operation that takes 1 nanosecond should cost 10 gas.
- The FVM supports gas charges with _milligas_ precision. That is, we can charge for gas in increments of 0.001 gas.
- In terms of chain throughput (gas per unit time), there's about 222 Filecoin gas to every 1 Ethereum gas. This ratio should be kept in mind when comparing Filecoin gas costs to Ethereum gas costs.

### Adjustments to FIP-0032

First and foremost, this FIP makes a few adjustments to FIP-0032.

- Memory copy costs `p_memcpy_per_byte` have been reduced from 0.5gas/byte to 0.4gas/byte to more accurately match benchmarks. We're reasonably confident in this number as it exactly matches the expected speed of 3200 MT/s memory.
- The explicit "extern" cost (`p_extern_gas`) of 21,000 gas has been rolled into the various syscall costs themselves to make it easier to reason about the costs of the individual syscalls. This change has no affect on the gas _charged_, it simply makes it easier to benchmark and discuss changes to gas charges.

### System Calls

#### IPLD Reads & Writes

This FIP updates the cost of all 4 IPLD operations according to the latest benchmarks.

##### `ipld::block_open`

1. The flat fee has been increased from 135,617 to 187,440 account for an increased size in the state-tree since network launch.
2. The per-byte fee has been reduced from `10.5 gas/byte` to a flat `10 gas/byte` (`p_memret_per_byte`). This reduction comes from the fact that the "memory retention" cost more than covers the actual per-byte compute cost from loading IPLD blocks.

The new read costs were determined through [benchmarking][read-benchmark]. However, the per-byte costs were ignored as they were already covered by the existing memory retention cost.

[read-benchmark]: https://bafybeifx23obtfhzdomhtlrv5h3lkb4zjnj32kye27q24gvjlkpjva7zre.ipfs.dweb.link/blockstore-read-gas.html

##### `ipld::block_create`

The per-byte fee has been reduced from `10.5 gas/byte` to a flat `10 gas/byte` for the same reasons as `ipld::block_open`.

##### `ipld::block_read`

The per-byte fee has been reduced from `0.5 gas/byte` to `0.4 gas/byte` due to the adjustment to `p_memcpy_per_byte`.

##### `ipld::block_link`

The cost of "linking" a block has been adjusted to take deferred compute costs (the cost of "flushing" blocks at the end of an epoch), hashing, allocating, and copying into account.

Specifically, this FIP proposes the following:

1. A `2.4 gas/byte` fee for to allocate and copy the block into temporary storage.
2. A per-byte hashing fee according to the price list defined in the hashing section below.
3. A fixed per-block fee of 172,000 gas to account for the cost of "flushing" blocks at the end of an epoch.
4. A fixed 130,000 per-block storage fee to account for metadata overhead.
5. A per-byte storage fee of 1,300 gas/byte.

These fees supersede the current prices:

1. A 1,300 gas/byte storage fee.
2. A fixed 353,640 per-block fee.

Overall, blocks under ~4KiB are actually cheeper under this model as the fixed cost is reduced from 353,640 to 302,000.

As with reads, these costs were determined through [benchmarking](write-benchmark).

[write-benchmark]: https://bafkreifhqfbc2scfq6s4roj625y2a4bm5cmo7bs6to56vjbu5cqswdxswe.ipfs.dweb.link/

#### Send

This FIP changes `send` costs to:

1. Account for the cost of instantiating and invoking a Wasm actor.
2. Not account for account  actor state loading and storing as those costs will now be accounted for separately.

Previously, there were four send-related gas fees:

1. A base send cost of 29233 gas.
2. A transfer charge of 27500 gas.
3. A transfer only premium of 159672 gas. This was charged for actors that didn't invoke any actual code.
4. A method invocation (actor instantiation) "rebate"' of 5377 gas. This gas was refunded to actors that actually invoked code.

These costs were designed to "make the numbers work out" in aggregate and took things like actor state loading/storing into account.

This model has been simplified to:

1. A fixed "transfer" fee of 6000 gas for all non-zero value transfers.
2. A fixed "invocation" cost of 75000 for all sends except method 0, to charge for instantiating and calling into an actor.

#### Actor State & Address Lookups

Previously, the FVM relied heavily on caching to reduce the costs of actor state loading and address resolution. Unfortunately, in the presence of user defined actors, it's now possible to trigger random address resolutions and actor state loads.

This FIP introduces:

1. An actor-state lookup cost of 400,000 gas (`p_actor_lookup`. This covers an expected 2 IPLD block loads, decodes, etc.
2. An address resolution cost of 1,000,000 gas (`p_address_lookup`). This covers the expected 5 IPLD block loads, decodes, etc.

As these costs are significant, this FIP proposes two mechanisms to reduce these costs:

1. First, this FIP takes caching into account and only charges for the _first_ time, during a single transaction, that an address is _successfully_ resolved or an actor's state is loaded.
2. Second, this FIP will not charge to load builtin singleton actor states (actors 0-7, 10, and 99).

#### Actor State Updates

Currently, the cost for actor-state updates is bundled into the cost of calling an actor. This FIP breaks these costs out to more accurately charge for state changes. As with actor state reads, these fees are only charged the first time an actor is updated during a transaction.

When an actor's state is updated (e.g., when transferring funds or calling `sself::set_root`) for the first time during a transaction:

1. If the actor state has not yet been loaded, `p_actor_lookup` is charged.
2. If the actor state has not yet been updated, TODO (`p_actor_update`) is charged to cover not only the cost of updating the state-tree, but the cost of the expected state churn resulting from the update.

TODO:

- It's unclear what the update fee here should be.

#### Actor Creation

The explicit "actor creation" compute cost of 1108454 is removed while the actor creation _storage_ cost of `(36+40) * 1300` remains.

Instead:

- Whenever a new actor is created, we charge `p_actor_update + p_actor_lookup` (in addition to the storage fee above).
- When implicitly creating an actor (e.g., implicitly creating an account and/or a FIP-0048 placeholder), we also charge `p_address_lookup` to cover the cost of assigning an address.

TODO:

- Ideally we'd just execute the init actor when implicitly creating an actor.
- We should likely charge an explicit fee when assigning an address to an implicitly created actor, in addition to the address lookup fee.

#### Hashing

Before this FIP, hashing cost a flat 31355 gas. This FIP proposes the following gas fee schedule, incurred when calling the `crypto::hash` syscall.

| Hash Function | Per-Byte |
| ------------- | -------- |
| SHA2-256      |  7 gas   |
| Blake2b-256   | 10 gas   |
| Blake2b-512   | 10 gas   |
| Keccak256     | 33 gas   |
| Ripemd160     | 35 gas   |

Whether this is a net reduction or increase depends on the length of the preimage. For example, for the Blake2b family, the crossover is at ~3135 bytes.

#### Signature verification

Before this FIP, signature verification had these costs:

- BLS: 16598605 gas.
- secp256k1: 1637292 gas.

This FIP adds a per-byte cost as well:

- 10 gas/byte for secp256k1.
- 26 gas/byte for BLS.

Note: the new `crypto::recover_secp_public_key` only charges the base 1637292 gas as it doesn't have to hash any messages.

This implies a slight base upwards revision of existing fees, which should have minimal impact because:

1. These operations aren't frequent.
2. The base cost dwarfs the cost of hashing.

#### Randomness

Previously, retrieving randomness only costed the flat `p_extern_gas` fee (FIP-0032). This FIP proposes an additional charge to cover the hashing involved. Specifically,  `(seed_size + entropy_size) * blake2b_hashing + p_extern_gas` where:

1. `seed_size` is 48 (the size of the randomness "seed").
2. `entropy_size` is the size of the entropy passed by the actor (usually 8).
3. `blake2b_hashing` is 10 (as defined above in the hashing section.

This should usually come out to about 560 gas which will increase the cost of this operation by about 2% in most cases. However, this additional charge prevents an attacker from potentially tricking the system into hashing a large amount of data for free.

### Memory Gas

This FIP introduces charges for Wasm instructions that operate on variable-sized memory.

The memory copy cost (`p_memcpy_gas_per_byte`) was first introduced in FIP-0032 but only applied to memory copying within the FVM itself.

This FIP:

1. Reduces this fee from 500 milligas to 400 milligas. This reduction applies to the relevant
   syscalls as well (e.g., block reads and writes).
2. Charges this fee (per byte) for instructions that operate on variable-sized memory:
   `{table,memory}.{init,fill,copy,grow}`. Table operations charge for 8 bytes per table entry (3.2
   gas/entry).
3. Charges this fee (again, per byte) for memory initialized when instantiating an actor. This includes both the Wasm memory and Wasm any tables initialized.
4. Removes the "one free page of memory" rule from FIP-0032. The FVM now charges for every page of memory allocated, even on initialization.

### Memory limits

A call stack is entitled to allocate a maximum of 2GiB in cumulative Wasm memory across all active invocation containers, and 512MiB for any given actor instance.

- If an actor attempts to exceed either of these limits at runtime, the Wasm container will return `-1` to the actor (as per the Wasm spec). All current built-in actors will then abort immediately with the `SYS_ILLEGAL_INSTRUCTION` exit code.
- If instantiating an actor would exceed either of these limits, the instantiating actor will immediately exit with the `SYS_ILLEGAL_INSTRUCTION` exit code.

## Design Rationale

Execution fidelity, accuracy, and security are the overarching principles that motivates this FIP. Fees have been revised to deliver a more accurate gas model while preserving the security properties of the network, which revolve around the baseline cost of 10 gas/ns.

The rationale backing each decision has been documented in the specification section.

## Backwards Compatibility

This FIP is consensus breaking, but should have no other impact on backwards compatibility. However, agents making assumptions about gas (e.g. setting hardcoded gas limits) may need to adapt.

## Test Cases

TODO: Will be covered by conformance tests.

## Security Considerations

This FIP exists to improve the security of the Filecoin network, but has intentionally skipped over a few cases:

- This FIP does not charge variable amounts for different types of mathematical operations. For example, in the future, we'll likely want to charge more for floating point operations, and significantly more for the "sqrt" operation.
- This FIP does not make any explicit charges to account for memory latency.

However, the proposed gas schedule should be "good enough" for FEVM because:

1. There's enough overhead in FEVM to "drown out" the effects of memory latency.
2. Floating point instructions, including the square-root instruction, are not available in the EVM.

## Incentive Considerations

As with all gas schedule changes, this FIP introduces changes to the operation costs of built-in actors which may alter operational cost structures for network stakeholders affective incentive structures.

## Product Considerations

This FIP will likely increase gas fees in some cases and needs to be carefully benchmarked.

## Implementation

TODO in progress in ref-fvm.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
