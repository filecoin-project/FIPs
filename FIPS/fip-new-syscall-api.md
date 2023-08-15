---
fip: "<to be assigned>"
title: Improved Event Syscall API
author: Fridrik Asmundsson (@fridrik01), Steven Allen (@stebalien)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/775
status: Draft
type: Technical Core
created: 2023-08-10
---

## Simple Summary

Revise the internal [`emit_event`](https://docs.rs/fvm_sdk/latest/fvm_sdk/sys/event/fn.emit_event.html) syscall by replacing the single CBOR encoded `ActorEvent` parameter with three separate fixed-sized byte arrays. This change enhances gas charge accuracy and eliminates the need for parsing.

## Abstract

The current procedure for emitting an event through the FVM SDK involves sending an `ActorEvent` structure as input. This structure is encoded into a byte array with CBOR formatting and then sent to the kernel.

Inside the kernel, complete CBOR deserialization is necessary before any validation can occur, which results in an upfront gas charge. However, accurately estimating the gas charge is challenging, as the original size of the `ActorEvent` remains unknown until the CBOR byte array is fully deserialized. Consequently, to ensure sufficient gas, a slightly higher gas fee is imposed, making this process more costly than necessary.

Moreover, the current gas charge is estimated based on the cost of emitting EVM events and won't be accurate for general events emitted by Wasm actors. Thus, we propose a new approach to calculating the gas cost, which should account for any type of emitted events.

## Change Motivation

This proposal aims to optimize the `emit_event` syscall by eliminating the need for CBOR encoding altogether. This change enables precise gas charging since the original size of the `ActorEvent` is known including total sizes of key and value lenghts allowing us to charge them separately in addition to fixed overhead of each event entry. Moreover, this proposal allows validation to be performed concurrently during the deserialization of the input.

## Specification

Currently the [`emit_event`](https://docs.rs/fvm_sdk/latest/fvm_sdk/sys/event/fn.emit_event.html) syscall is defined as:

```rust
pub fn emit_event(
    event_off: *const u8,
    event_len: u32
) -> Result<()>;
```

The syscall takes in `event_off` and `event_len` which refer to a pointer and length in WASM memory where the CBOR encoded `ActorEvent` has been written. An `ActorEvent` structure is defined as:

```rust
pub struct ActorEvent {
    pub entries: Vec<Entry>,
}

pub struct Entry {
    pub flags: Flags,
    pub key: String,
    pub codec: u64,
    pub value: Vec<u8>,
}
```
### Proposed change
We propose changing the `emit_event` syscall shown above to the following:

```rust
pub fn emit_event(
    event_off: *const EventEntry,
    event_len: u32,
    key_off: *const u8,
    key_len: u32,
    value_off: *const u8,
    value_len: u32,
) -> Result<()>;
```

We also introduce a new struct `EventEntry` which is encoded as a packed tuple in field order `(u64, u64, u32, u32)` where `flags`/`codec` fields are copied from `Entry` directly and `key_len`/`value_len` are the length of their respective `key`/`value` fields in `Entry`:

```rust
#[repr(C, packed)]
pub struct EventEntry {
    pub flags: u64,   // copy of Entry::flags
    pub codec: u64 ,  // copy Entry::codec
    pub key_len: u32, // Entry::key.len()
    pub val_len: u32, // Entry::value.len()
}
```

In the new `emit_event` syscall instead of taking the whole `ActorEvent` data encoded using CBOR this proposed version splits the `ActorEvent` instance into three different buffers that each refer to a pointer and length in WASM memory where their data has been written and are defined as follows:
- `event_off/event_len`: Pointer to an array of `EventEntry` where `event_len` is the number of elements in the array.
- `key_off/key_len`: Pointer to a buffer of size `key_len` bytes of all the keys from each entry are concatinated.
- `value_off/value_len`: Pointer to a buffer of size `value_len` bytes of all the values from each entry are concatenated.

### Serialization
The serialization from the syscall to FVM is implemented as follows:

Given a `ActorEvent` with _N_ number of `Entry` elements, declare three buffer:
- `entries` an array of `EventEntry` of size _N_.
- `keys` a byte buffer of size equal to the total number of keys in all entries.
- `values` a buffer of size equal to the total number of values in all entries.

Then for each entry `e` in `ActorEvent`:
- Create `EventEntry` from `e` and add it to `entries`.
- Add `e.keys` to the `keys` buffer.
- Add `e.values` to the `values` buffer.

Deserialiaztion in FVM is done in a similar fashion where we read each `EventEntry` from `entries` and create a new `Entry` object by using the flags/codec from `EventEntry` and reconstructing its keys/values by reading exactly `key_len`/`val_len` from `keys`/`values` respectively.

### Validation
In the FVM we perform the following valdidation while deserializing the input:

1. Initial validation:
    1. Validate that the size of `entries` is 255 or less. Previously 256 entries was accepted but reducing it by 1 ensures that the resulting CBOR encoding can store the length in a single byte.
    2. Validate that the size of `values` does not exceed 8KiB.
2. For each event entry `ee` in `entries`:
    1. Validate that the `ee.flags` bits are valid (see [FIP-0049](https://github.com/filecoin-project/FIPs/blob/6c2be9a09a7f03f16aa5f635e4beadeaa9c4fb3b/FIPS/fip-0049.md#new-chain-types) for more details).
    2. Validate that the `ee.key_len` is 31 bytes or less and is a valid UTF-8. Previously 32 byte sized keys was accepted but we reduce it by 1 to ensure more compact CBOR encoding.
    3. Validate that the `ee.val_len` is 8Kib or less.
    4. Validate that the `ee.codec` is acceptable. Currently, only `IPLD_RAW` (0x55) is allowed).

### Gas

This FIP makes an adjustment to the gas cost when emitting an event as originally defined in [FIP-0049#Gas costs](https://github.com/filecoin-project/FIPs/blob/6c2be9a09a7f03f16aa5f635e4beadeaa9c4fb3b/FIPS/fip-0049.md#gas-costs). Instead of having a separate gas fee for validation and processing of an event, we instead charge an upfront gas fee. This fee is applied after checking for read-only but before any other validation, allocation, or deserialization is performed as described in the specification above.

Notable changes from previous gas fee is that we:
- Removed the indexing cost associated with specifying flags that indicate that keys/values should be indexed by the client. This was not used and therefore removed here.
- We charge an additional memory allocation per event.
- Refactored the gas charges allowing us to tune gas for entry and key validation separately.


The proposed processing fee is:

```
// cost for processing each entry
p_gas_per_entry_flat := 1750
p_gas_per_entry_per_byte := 25

// cost for UTF-8 decoding per byte, set to zero for now
p_gas_per_key_flat = 0
p_gas_per_key_per_byte = 0

p_memcpy_gas_per_byte = 400
p_block_alloc_cost_per_byte = 2
p_hashing_cost_per_byte = 10

nr_entries = <number of entries>
key_len = <total size of keys in all entries>
value_len <total size of values in all entries>

// gas cost for validation of entries (including utf-8 parsing)
gas_validate_entries = p_gas_per_entry_flat + p_gas_per_entry_per_byte * nr_entries;
gas_validate_utf8 = p_gas_per_key_flat + p_gas_per_key_per_byte * key_len;

// estimated size (in bytes)
estimated_size = 12 + // event overhead
    9 * nr_entries + // entry overhead
    key_len +
    value_len

// calculate the gas for making a copy
copy_and_alloc = p_memcpy_gas_per_byte * estimated_size +
    p_block_alloc_cost_per_byte * estimated_size

// calculate the gas for hashing on AMT insertion
hash = p_hashing_cost_per_byte * estimated_size

processing_fee = copy_and_alloc +
    gas_validate_entries +
    gas_validate_utf8 +
    copy_and_alloc * 2 +
    hash
```

## Design Rationale

### Serialize a single buffer instead of using three
We considered serializing the `ActorEvent` using a single buffer (as with CBOR) for simplicity but decided against that since it required _some_ parsing if we wanted to charge gas for keys/values separately.

## Backwards Compatibility

This FIP is consensus breaking, but should have no other impact on backwards compatibility.

## Test Cases

Provided with implementation.

## Security Considerations

TODO

## Implementation

https://github.com/filecoin-project/ref-fvm/pull/1807

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
