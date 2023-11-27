---
fip: "<to be assigned>" <!--keep the qoutes around the fip number, i.e: `fip: "0001"`-->
title: Add support for upgradable actors
author: Fridrik Asmundsson (@fridrik01), Steven Allen (@stebalien)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/396
status: Draft
type: Technical Core
created: 2023-11-27
---

## Simple Summary

This FIP introduces support for upgradable actors, enabling deployed actors to update their code while retaining their address, state, and balance.

## Abstract

This FIP proposes the integration of upgradable actors into the Filecoin network through the introduction of a new `upgrade_actor` syscall and an optional `upgrade` WebAssembly (WASM) entrypoint.

Upgradable actors provide a framework for seamlessly replacing deployed actor code, significantly enhancing the user experience when updating deployed actor code.

## Change Motivation

Currently, all actors on the Filecoin Network are immutable once deployed. To modify the underlying actor code, such as fixing a security bug, the following steps are required:
1. Deploy a new actor with the corrected code.
2. Migrate all state from the previous actor to the new one.
3. Update all other actors interacting with the old actor to use the new actor.

By adding support for upgradable actors, deployed actors can easily upgrade their code and no longer need to go through the series of steps mentioned above.

This also simplifies the upgrade process for builtin actors. Currently, any changes made to the builtin actors require a network upgrade, a new Lotus version, and collaboration with the network to push the new version to production. This is a time consuming and manual process. However, with upgradable actors, we can instead deploy a new code to the builtin actors allowing the changes to be pushed to production almost instantly and does not require a new network upgrade or new Lotus version.

## Specification

Introducing support for actor upgrades involves the following changes to the FVM:

1. Adding a new `upgrade` WASM entrypoint, which actors must implement in order to be a valid upgrade target.
2. Adding a new `upgrade_actor` syscall, enabling actors to upgrade themselves.

These changes are discussed in detail in the following sections.

### New upgrade WASM Entrypoint

We introduce a new optional `upgrade` WASM entrypoint. Deployed actors must implement this entrypoint to be a valid upgrade target. It is defined as follows:

```rust
pub fn upgrade(params_id: u32, upgrade_info_id: u32) -> u32
```

Parameters:
- `params_id`: An IPLD block handle provided by the caller and sent to the upgrade receiver, or `0` for none.
- `upgrade_info_id`: An IPLD block handle for an `UpgradeInfo` struct provided by the FVM runtime (defined below).

The single `u32` return value is an IPLD block handle, or `0` for none.

The `UpgradeInfo` struct is defined as follows:

```rust
#[derive(Clone, Debug, Copy, PartialEq, Eq, Serialize_tuple, Deserialize_tuple)]
pub struct UpgradeInfo {
    // the old code cid we are upgrading from
    pub old_code_cid: Cid,
}
```

When a target actor's `upgrade` WASM entrypoint is called, it can make necessary state tree changes from the calling if needed to its actor code. The `UpgradeInfo` struct provided by the FVM runtime can be used to check what code CID its upgrading from. A successful return from the `upgrade` entrypoint instructs the FVM that it should proceed with the upgrade. The target actor can reject the upgrade by calling `sdk::vm::exit()`` before returning from the upgrade entrypoint.

### New upgrade_actor syscall

We introduce a new `upgrade_actor` syscall which calls the `upgrade` wasm entrypoint of the calling actor and then atomically replaces the code CID of the calling actor with the provided code CID. It is defined as follows:

```rust
pub fn upgrade_actor(
    new_code_cid_off: *const u8,
    params: u32,
) -> Result<Send>;
```

Parameters:
- `new_code_cid_off`: The code CID the calling actor should be replaced with.
- `params`: The IPLD block handle passed, or `0` for none.

On successful upgrade, this syscall will not return. Instead, the current invocation will "complete" and the return value will be the block returned by the new code's `upgrade` endpoint. If the new code rejects the upgrade (calls `sdk::vm::exit()`) or performs an illegal operation, this syscall will return the exit code plus the error returned by the upgrade endpoint.

This syscall will:
1. Validate that the pointers passed to the syscall are in-bounds.
2. Validate that `new_code_cid_off` is a valid code CID.
3. Validate that the calling actor is not currently executing in "read-only" mode. If so, the syscall fails with a "ReadOnly" (13) syscall error.
4. Checks whether the calling actor is already on the call stack where it has previously been called on its `invoke` entrypoint (note that we allow calling `upgrade` recursively). If so, the syscall fails with a "Forbidden" (11) syscall error.
5. Checks that we have space for storing the return block. If not, the syscall fails with a "LimitExceeded" (3) syscall error.
6. Start a new Call Manager transaction:
    1. Validate that the calling actor has not been deleted. If so, the syscall fails with a "IllegalOperation" (2) syscall error.
    2. Update the actor in the state tree with the new `new_code_cid` keeping the same `state`, `sequence` and `balance`.
    3. Invoke the target actor's `upgrade` entrypoint.
    4. If the target actor does not implement the `upgrade` entrypoint, then return the syscall fails with a `ExitCode::SYS_INVALID_RECEIVER` exit code.
    5. If the target actor aborts the `upgrade` entrypoint by calling `sdk::vm::exit()`, the syscall fails with the provided exit code.
7. Apply transaction, committing changes.
8. Abort the calling actor and return the IPLD block from the `upgrade` entrypoint.

## Design Rationale

### Additional metadata syscall

We considered adding a new `get_old_code_cid` syscall to get the calling actors code CID. That has the benefit of keeping the `upgrade` entrypoint signature consistent with the `invoke` signature. We however rejected that as we felt the benefit didn't outweight the overhead of adding a new syscall. Furthermore, it did not provide the flexibility of passing in a IPLD handle for a `UpgradeInfo` struct where we can easily add more fields if required.

## Backwards Compatibility

Fully backwards compatibility is expected.

## Test Cases

Detailed test cases are provided with the implementation.

## Security Considerations

Upgradable actors pose potential security risks, as users can replace deployed actors' code. However, measures are in place to minimize these risks:

- Upgradable actors are opt-in by default, ensuring no impact on currently deployed actors.
- Actors can only upgrade themselves, preventing one actor from upgrading another actor to a new version.
- We reject re-entrant `upgrade_actor` syscalls, i.e., if some actor `A` is already on the call stack, no "deeper" instance of `A` should be able to call the upgrade syscall.

Detailed tests cover these security considerations and edge cases.

## Incentive Considerations

This FIP does not materially impact incentives in any way.

## Product Considerations

This FIP makes it possible to upgrade deployed actors, for example in cases where a bug or security concern was identified in the deployed code, allowing a simple safe way to addres such issues which significantly improves the user experience from how it is today.

## Implementation

https://github.com/filecoin-project/ref-fvm/pull/1866

## TODO

N/A

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).