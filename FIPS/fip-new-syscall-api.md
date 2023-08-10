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

The current procedure for emitting an event through the FVM SDK involves sending an ActorEvent structure as input. This structure is encoded into a byte array with CBOR formatting and then sent to the kernel.

Inside the kernel, complete CBOR deserialization is necessary before any validation can occur, which results in an upfront gas charge. However, accurately estimating the gas charge is challenging, as the original size of the `ActorEvent` remains unknown until the CBOR byte array is fully deserialized. Consequently, to ensure sufficient gas, a slightly higher gas fee is imposed, making this process more costly than necessary.

Moreover, the upfront cost of deserialization must be paid before any validation on the `ActorEvent` instance can take place.

## Change Motivation

This proposal aims to optimize the `emit_event` syscall by eliminating the need for CBOR encoding altogether. This change would enable precise gas charging since the original size of the `ActorEvent` is known, and it would allow validation to be performed concurrently during the deserialization of the input.

## Specification

Currently the [`emit_event`](https://docs.rs/fvm_sdk/latest/fvm_sdk/sys/event/fn.emit_event.html) syscall is defined as: 

```rust
pub fn emit_event(
    event_off: *const u8,
    event_len: u32
) -> Result<()>;
```

The syscall takes in `event_off` and `event_len` which refer to a pointer and length in WASM memory where the CBOR encoded `ActorEvent` has been written. An `ActorEvent` structure is defined in `fvm_shared::event` as:

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

We also introduce a new public struct in `fvm_shared::sys` where we will store the fixed fields per `Entry` (24 bytes for each entry):

```rust
// in fvm_shared::sys
pub struct EventEntry {
    pub flags: crate::event::Flags,
    pub codec: u64,
    pub key_len: u32,
    pub val_len: u32,
}
```

In the new `emit_event` syscall instead of taking the whole `ActorEvent` data encoded using CBOR this proposed version splits the `ActorEvent` instance into three different buffers that each refer to a pointer and length in WASM memory where their data has been written and are defined as follows:
- `event_off/event_len`: Pointer to a buffer of all `EventEntry` for all entries. 
- `key_off/key_len`: Pointer to a buffer of all the concatinated keys for all entries.
- `value_off/value_len`: Pointer to a buffer of all the concatenated values for all entries.

### Serialization and validation
The serialization from the syscall to FVM is implemented as follows:

1. Prepare a buffer named `entries` with a size of 24 bytes multiplied by the number of entries.
2. Set up two counters: `total_key_len` and `total_val_len`.
3. For each entry `e`:
    1. Create an `EventEntry` that includes flags, codec, and the size of the key/value for `e`, then add it to buf.
    2. Update the counters `total_key_len` and `total_val_len`.
4. Create a buffer called `keys` with a size of `total_key_len` bytes, and another buffer named `values` with a size of `total_val_len` bytes.
5. For each entry `e`:
    1. Add `e.keys` to the `keys` buffer.
    2. Add `e.values` to the `values` buffer.
6. Cast the raw memory pointed to by `entries` into a `EventEntry` slice of size equal to the number of entries making sure the pointer is aligned and within bounds.

In the FVM we reconstruct the `ActorEvent` as follows:

1. Initial validation:
    1. Confirm that the total number of entries is fewer than 256.
    2. Ensure the total length of combined entry data does not exceed 8KiB.
2. Initialize `key_offset` and `val_offset` counters.
3. Create a vector `v` of `Entry` with capacity matching the size of the `EventEntry` array.
4. For each event entry 'ee':
    1. Validate that the `ee.flag` bits are valid,
    2. Validate that the `ee.key_len` is at most 32 bytes and is a valid UTF-8.
    3. Validate that the `ee.codec` is acceptable. Currently, only `IPLD_RAW` (0x55) is allowed).
    4. Create a new `key` string by reading from the `keys` buffer, starting from `key_offset` and spanning `ee.key_len` bytes.
    5. Create a new `value` byte array by reading from the `values` buffer, starting from `val_offset` and spanning `ee.val_len` bytes.
    6. Create new a `Entry` using `ee.flag`/`ee.codec`/`key`/`value` and append that to `v`.
    7. Update `key_offset` and `val_offset`.
5. Return vector `v`.

### Gas

We combined the gas charges for `OnActorEventValidate` and `OnActorEventAccept` into an upfront `OnActorEvent` gas charge, applied prior to any validation, allocations, or deserialization. 

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
