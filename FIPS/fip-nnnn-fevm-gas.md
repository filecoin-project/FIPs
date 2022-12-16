---
fip: "<to be assigned>"
title: Update gas charging schedule and system limits for FEVM
author: Steven Allen (@stebalien), Raúl Kripalani (@raulk), Akosh Farkash (@aakoshh)
discussions-to: <URL>
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

1. Adds charges to syscalls that were previously free.
2. Adds charges to externs that were previously free.
3. Adds variable charges (scaling with the input) to some syscalls that previously charged a fixed fee.
4. Exempts some Wasm instructions from execution gas. 
5. Adds bulk memory copy fee to all instructions that initialize and/or copy memory.
6. Adds a memory expansion fee.
7. Introduces memory limits and table limits.
8. Reduces the default instruction cost for execution gas.

## Change Motivation

With the introduction of FEVM, users will be able to trigger these operations:

1. Operations that have runtime cost varying in the size of the inputs (bulk memory copies, hashing, etc.).
2. Syscalls traversing the extern boundary.
3. Syscalls not traversing the extern boundary.
4. Sequences of predefined Wasm instructions backing FEVM opcode handlers.
5. Memory allocation.

We propose gas charges and system limits to Currently, there is a fixed fee but no per-byte charge for hashing, memory copies, fills, etc. Furthermore, all Wasm instructions are priced through execution gas at a flat rate of 4 gas/op with the exception of some control flow instructions. However, recent observations suggest that some incur in no CPU cost, so we propose new gas exemptions for higher accuracy.

## Specification

Notes:

- Filecoin targets 10 gas/ns. That is, an operation that takes 1 nanosecond should cost 10 gas.
- The FVM supports gas charges with _milligas_ precision. That is, we can charge for gas in increments of 0.001 gas.

### System Calls

The following unpriced syscalls begin accruing the following costs.

TODO.

| Syscall | Cost |
| ------- | ---- |
|         |      |

#### Hashing

Before this FIP, hashing cost a flat 31355 gas. This FIP proposes the following gas fee schedule, incurred when calling the `crypto::hash` syscall.

| Hash Function | Flat | Per-Byte           |
| ------------- | ---- | ------------------ |
| SHA2-256      | 0    | 64500 milligas     |
| Blake2b-256   | 0    | 11500 milligas     |
| Blake2b-512   | 0    | 11500 milligas     |
| Keccak256     | 0    | 48500 milligas     |
| Ripemd160     | 0    | 43900 milligas     |

Whether this is a net reduction or increase depends on the length of the preimage. For example, for the Blake2b family, the crossover is at ~2726 bytes.

#### Signature verification

Before this FIP, signature verification had these costs:

- BLS: 16598605 gas.
- secp256k1: 1637292 gas.

We revise these costs and introduce a new fee for secp256k1 public key recovery (syscall introduced in FIP-TODO).

| Concept                          | Flat                  | Per-Byte           |
| -------------------------------  | --------------------- | ------------------ |
| BLS signature verification       | 18719325000 milligas  | 11400 milligas     |   
| secp256k1 signature verification | 2639001000 milligas   | 11400 milligas     |
| secp256k1 signature recovery     | 2643945000 milligas   | 0                  |

This implies a slight base upwards revision of existing fees, which should have minimal impact because these operations aren't frequent.

### Wasm Instructions

This FIP introduces charges for Wasm instructions that operate on variable-sized memory, and exempts execution gas for some no-op instructions.

#### Memory Copy

The memory copy cost was first introduced in FIP-0032 but only applied to memory copying within the FVM itself.

Instructions that operate on variable-sized memory chunks are now charged a per-byte memory copy fee: `{table,memory}.{init,fill,copy,grow}`.

This fee is identical to `p_memcpy_gas_per_byte` as defined in [FIP-0032](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0032.md), currently priced at 500 milligas per byte.

Additionally, these fees are charged for memory and table allocation when the actor is instantiated (started).

#### No-Ops

Costs have been removed from some operations that would have little to no cost on a traditional CPU. These rules are _valid_ under FEVM because the user cannot trigger _specific_ sequences of WebAssembly instructions but must be revisited before introducing full user programmability as some pathologically unoptimized programs may be able to find a way to make these instructions actually take time.

This is in addition to no-op equivalent instructions that were already exempted in FIP-0032 (`nop`, `block`, `loop`, `unreachable`, `return`, `else`, `end`, `drop`).

##### Locals & Globals

Setting/getting locals and globals is now free because these instructions are mostly just telling other instructions which registers to use. Furthermore, in FEVM, the user cannot directly control and/or create new locals/globals.

The newly exempt instructions are:

- `local.{get,set,tee}`
- `global.{get,set}`

##### Casts

Logic-less casts have been made free as they generally don't turn into actual instructions (or, when they do, these instructions basically free and tied to some other more expensive operation).

The newly exempt instructions are:

1. `i64.extend32_u` - re-interprets the input as a u64 (without sign extension).
2. `i32.wrap_i64`- casts an i64 to an i32.
3. `$t.reinterpret_$t` - bitwise casts.

##### Bulk memory drops

The `{data,elem}.drop` bulk memory drop instructions are now exempt from execution gas.

##### Constants

All operations that push constants onto the WebAssembly stack (`$t.const`) have been made free. In most cases, these will compile down to "immediate" arguments, or, in the worst case, _very_ predictable loads from read-only memory.

### Memory expansion gas

We define two fees for memory expansion:

- A flat fee per operation to cover the base cost of the allocation operation.
- A dynamic per-byte fee, which is effectively applied in increments of 64KiB (Wasm memory page size).

Their prices are:

```
p_memory_fill_base_cost := TODO
p_memory_fill_per_byte_cost := TODO
```

These fees are applied in three scenarios:

1. On initialization of an invocation container, we charge both fees, with the dynamic fee charging for the number of Wasm memory bytes preallocated by the environment before control is handed to the actor.
2. On initialization of an invocation container, we charge both fees if the module exports a table. The dynamic fee charging for the memory required to hold the minimum table size (8 bytes per element).
3. During execution, we charge both fees for every `memory.grow` operation carried out.

Note: (1) and (2) may be wasmtime-dependent at this stage.

### Memory limits

A call stack is entitled to allocate a maximum of 2GiB in cumulative Wasm memory across all active invocation containers. If an actor triggers an allocation that breaches this limit, execution will be interrupted and:

- The `SYS_ILLEGAL_INSTRUCTION` (4) exit code will be returned to the caller if the offending actor was called through an internal send, or
- The `SYS_ILLEGAL_INSTRUCTION` (4) exit code will be stamped on the receipt if the offending actor was the top of the stack.

### Default instruction cost reduction

We reduce the default instruction cost from 4 gas/op to TODO gas/op. This reduction is made possible thanks to the specific memory expansion modelling. Previously, memory allocation overheads were averaged and smoothed into the default instruction cost.

## Design Rationale

Execution fidelity, accuracy, and security are the overarching principles that motivates this FIP. Fees have been revised to deliver a more accurate gas model while preserving the security properties of the network, which revolve around the baseline cost of 10 gas/ns.

The rationale backing each decision has been documented in the specification section.

## Backwards Compatibility

This FIP is consensus breaking, but should have no other impact on backwards compatibility. However, agents making assumptions about gas (e.g. setting hardcoded gas limits) may need to adapt.

## Test Cases

TODO: Will be covered by conformance tests.

## Security Considerations

This FIP charges zero for some operations. These operations should consume no CPU time, but this should be rigorously verified before allowing users to deploy arbitrary WebAssembly contracts.

Furthermore, this FIP does not charge variable amounts for different types of mathematical operations. For example, in the future, we'll likely want to charge more for floating point operations, and significantly more for the "sqrt" operation.

However, the proposed gas schedule should be "good enough" for FEVM because:

1. Users cannot deploy new WebAssembly contracts, so there's no way to write custom WebAssembly that creates sequences of "free" instructions that actually have runtime costs.
2. Floating point instructions, including the square-root instruction, is not available in the EVM.

## Incentive Considerations

As with all gas schedule changes, this FIP introduces changes to the operation costs of built-in actors which may alter operational cost structures for network stakeholders affective incentive structures.

## Product Considerations

This FIP will likely increase gas fees in some cases and needs to be carefully benchmarked.

## Implementation

TODO in progress in ref-fvm.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
