---
fip: "\<to be assigned\>"
title: Add Support for EIP-7702 (Set Code for EOAs) in the FEVM
author: "Michael Seiler (@snissn), Aarav Mehta (@aaravm)"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1143
status: Draft
type: Technical
category: Core 
created: 2025-10-30
---

# FIP-XXXX: Add Support for EIP-7702 (Set Code for EOAs) in the FEVM

## Simple Summary

This proposal integrates [EIP-7702: Set Code for EOAs](https://eips.ethereum.org/EIPS/eip-7702) into the Filecoin Ethereum Virtual Machine (FEVM). EIP-7702 introduces a new transaction type that allows Externally Owned Accounts (EOAs, standard user wallets) to delegate execution capabilities to a smart contract. This enables EOAs to utilize smart contract wallet features, such as batching multiple operations (e.g., "approve and spend" in one transaction) and sponsored transactions, improving user experience and compatibility with modern Ethereum tooling.

## Abstract

EIP-7702 defines a new EIP-2718 transaction type (`0x04`) that includes an `authorization_list`. Each authorization is a signed tuple from an EOA (the "authority") designating a smart contract (the "delegate") to execute on its behalf.

This FIP adapts EIP-7702 to the FEVM architecture. The implementation introduces a new method, `ApplyAndCall`, in the EVM actor. This method atomically processes the authorization list—validating signatures, updating the delegation mapping, and incrementing authority nonces—and then executes the outer transaction call. The FEVM interpreter is updated to recognize these delegations: when a `CALL` targets a delegated EOA, the interpreter executes the delegate's code within the authority's context. This implementation ensures that delegation mappings and nonce increments persist even if the outer transaction call reverts, adhering to the EIP's specified atomicity model.

## Change Motivation

Despite advancements in smart contract wallets and Account Abstraction, EOAs remain the dominant account type in the EVM ecosystem. The limitations of EOAs often hinder user experience improvements, requiring multiple transactions for common workflows and complicating the implementation of advanced features.

EIP-7702 aims to enhance EOA functionality by allowing them to adopt smart contract behavior through delegation. Adopting this EIP in the FEVM is crucial for several reasons:

1.  **Improved User Experience (Batching):** Enabling atomic batching simplifies multi-step operations (like ERC-20 approval followed by a swap) into single transactions, reducing friction and latency for users interacting with decentralized applications on Filecoin.
2.  **Ethereum Compatibility:** As the Ethereum ecosystem adopts EIP-7702, supporting it in FEVM ensures that tooling, wallets, and SDKs designed for modern Ethereum UX standards function seamlessly on Filecoin.
3.  **Feature Parity:** It allows FEVM developers to leverage the same account abstraction primitives available on Ethereum, fostering innovation in wallet design, sponsorship mechanisms, and privilege de-escalation.

## Specification

This specification details the integration of EIP-7702 into the FEVM, focusing on the new transaction type, the EVM actor modifications, and the required interpreter semantics.

### Constants

| Constant                      | Value  | Description                                     |
| ----------------------------- | ------ | ----------------------------------------------- |
| `SET_CODE_TX_TYPE`            | `0x04` | EIP-2718 transaction type identifier.           |
| `SET_CODE_AUTHORIZATION_MAGIC`| `0x05` | Domain separator for authorization signatures.  |
| `EIP7702_BYTECODE_MAGIC`      | `0xEF01`| Prefix for the delegation indicator bytecode.   |
| `EIP7702_BYTECODE_VERSION`    | `0x00` | Version byte for the delegation indicator.      |
| `MAX_AUTHORIZATION_TUPLES`    | `64`   | Maximum number of tuples allowed per transaction (Filecoin specific placeholder). |

### Transaction Type (0x04)

A new EIP-2718 transaction type `0x04` is introduced. The `TransactionPayload` is the RLP serialization as defined in EIP-7702, including the `authorization_list`.

In the FEVM context, a `0x04` transaction is converted by the client (e.g., Lotus) into a Filecoin message targeting the EVM actor's `ApplyAndCall` method.

### EVM Actor Modifications

The EVM actor is modified to manage delegation state and process `0x04` transactions.

#### On-Chain State

The EVM actor's state is extended with three new HAMTs to manage EIP-7702 delegations:

1.  **`delegations`**: A HAMT mapping the 20-byte authority address (EOA) to the 20-byte delegate address (contract).
2.  **`delegation_nonces`**: A HAMT mapping the 20-byte authority address to a `u64` nonce, used for authorization replay protection. An absent entry implies a nonce of 0.
3.  **`delegation_storage`**: A HAMT mapping the 20-byte authority address to a storage root CID (KAMT root). This provides isolated, persistent storage for the authority when executing delegated code.

#### New Method: `ApplyAndCall`

A new FRC-42 method, `ApplyAndCall`, is introduced in the EVM actor. This is the exclusive entry point for `0x04` transactions.

**Parameters (`ApplyAndCallParams`):**

The parameters are CBOR-encoded as a tuple containing the authorization list and the outer call details: `[authorization_list, call_tuple]`.

```rust
// CBOR Tuple Structure: [ [tuple, ...], [to, value, input] ]
pub struct ApplyAndCallParams {
    pub list: Vec<DelegationParam>,
    pub call: ApplyCall,
}

// [chain_id, address(20b), nonce, y_parity, r(bytes), s(bytes)]
pub struct DelegationParam {
    pub chain_id: u64,
    pub address: EthAddress, // The delegate contract address
    pub nonce: u64,
    pub y_parity: u8,
    pub r: Vec<u8>, // <= 32 bytes
    pub s: Vec<u8>, // <= 32 bytes
}

// [to(20b), value(bytes), input(bytes)]
pub struct ApplyCall {
    pub to: EthAddress,
    pub value: Vec<u8>, // Big-endian magnitude
    pub input: Vec<u8>,
}
```

**Return Value (`ApplyAndCallReturn`):**

The method always returns with `ExitCode::OK`. The result of the outer call is embedded in the return data, CBOR-encoded as `[status, output_data]`.

```rust
// CBOR Tuple Structure: [status, output_data]
pub struct ApplyAndCallReturn {
    pub status: u8, // 1 if the outer call succeeded, 0 if it reverted/failed.
    pub output_data: Vec<u8>, // Return data or revert data from the outer call.
}
```

**Behavior:**

`ApplyAndCall` executes in two phases: authorization processing and outer call execution.

##### 1\. Authorization Processing

The method iterates through the `authorization_list` and performs the following validations and state updates for each tuple:

1.  **List Validation:** The `authorization_list` must be non-empty and must not exceed `MAX_AUTHORIZATION_TUPLES` (64). Duplicate authorities within a single message are rejected.
2.  **Tuple Validation:**
      * `chain_id` must be `0` or the local Filecoin Chain ID.
      * `y_parity` must be `0` or `1`.
      * `r` and `s` must be non-zero.
      * `r` and `s` lengths must be `<= 32` bytes. The implementation accepts shorter lengths (1-31 bytes) and left-pads them to 32 bytes internally for signature recovery.
      * Low-s enforcement (EIP-2) is applied to the padded `s` value.
3.  **Authority Recovery:** The `authority` address (the EOA signing the tuple) is recovered using `ecrecover`. The message hash preimage is `keccak256(0x05 || rlp([chain_id, address, nonce]))`.
4.  **Pre-existence Policy:** The implementation resolves the `authority` address. If it resolves to an existing EVM contract actor, the authorization is rejected.
5.  **Nonce Verification:** The `nonce` in the tuple must match the current nonce stored in the `delegation_nonces` HAMT for the `authority`.
6.  **State Update:**
      * The `delegations` HAMT is updated to map the `authority` to the `address` (the delegate). If the delegate address is zero, the mapping is cleared.
      * The `delegation_nonces` HAMT is updated to increment the `authority`'s nonce by 1.

**Persistence and Atomicity:** Crucially, the changes to the `delegations` and `delegation_nonces` HAMTs are flushed and persisted **before** the outer call is executed. This ensures that the nonce bump and delegation mapping remain in effect even if the outer call reverts, as required by EIP-7702.

##### 2\. Outer Call Execution

After processing all authorizations, the outer call (`ApplyCall`) is executed.

  * If the `to` address is an EVM contract, `InvokeContract` is called.
  * If the `to` address is an EOA, the implementation checks the `delegations` map. If a delegation exists, the delegate's code is executed in the context of the EOA via the internal `InvokeAsEoa` trampoline.

The result of the outer call determines the `status` and `output_data` returned by `ApplyAndCall`.

#### New Internal Method: `InvokeAsEoa`

An internal method, `InvokeAsEoa`, is used by the `CALL` instruction pathway and `ApplyAndCall` to execute delegated code.

  * It is only callable by the EVM actor itself.
  * It loads the delegate's bytecode.
  * It mounts the authority's dedicated storage root from `delegation_storage` (creating an empty root if none exists).
  * It sets the `in_authority_context` flag to true, enforcing the delegation depth limit.
  * It executes the bytecode with the specified caller, receiver (the authority EOA), value, and input.
  * Upon successful return, it flushes the updated authority storage root and persists it back to `delegation_storage`.

### Interpreter Semantics

The FEVM interpreter is modified to handle delegated execution contexts.

#### Delegation Indicator

When a delegation is active, the EOA is virtually associated with a 23-byte delegation indicator bytecode:

`0xEF 0x01 0x00 || <20-byte delegate address>`

#### CALL Opcodes (`CALL`, `STATICCALL`, etc.)

When a `CALL` targets an EOA (Account/Placeholder actor type), the interpreter checks the EVM actor's internal `delegations` map.

1.  **Delegation Found:** If a mapping exists, the interpreter executes the delegate's code using `InvokeAsEoa`.
      * The execution occurs in the context of the authority (EOA), using the authority's balance and dedicated storage root.
      * A `Delegated(address)` event is emitted (see Event Emission).
2.  **Depth Limit:** Nested delegations are not followed. If the interpreter is already executing within an authority context (`in_authority_context` is true), further delegations are ignored, enforcing a maximum delegation depth of 1.
3.  **Revert Propagation:** If the delegated execution reverts, the `CALL` opcode returns `0` (failure), and the revert data is propagated to the caller's memory and `RETURNDATA*` buffers.

#### EXTCODE Opcodes (`EXTCODESIZE`, `EXTCODECOPY`, `EXTCODEHASH`)

These opcodes operate on the virtual delegation indicator itself when querying a delegated EOA, rather than the delegate's code.

  * `EXTCODESIZE`: Returns `23`.
  * `EXTCODECOPY`: Returns the 23-byte delegation indicator bytecode.
  * `EXTCODEHASH`: Returns the `keccak256` hash of the 23-byte delegation indicator bytecode.

#### SELFDESTRUCT

If `SELFDESTRUCT` is executed within a delegated context (`InvokeAsEoa`), it is treated as a no-op. Funds are not transferred, and the actor state is not marked for deletion. This ensures that delegated code cannot destroy the host EVM actor or illicitly move the authority's funds.

### Event Emission

When a delegated execution occurs, the EVM actor emits an Ethereum-style event for attribution:

  * **Event Signature:** `Delegated(address)`
  * **Topic 1 (Hash):** `keccak256("Delegated(address)")`
  * **Data (Indexed):** The 20-byte address of the **authority** (the EOA), not the delegate contract.

This event allows off-chain indexers and clients (like Lotus) to attribute the delegated activity to the correct EOAs.

## Design Rationale

### EVM-Only Implementation

The Filecoin implementation routes EIP-7702 entirely through the EVM actor. By centralizing the logic in the EVM actor, we simplify the architecture, ensure atomic state management between delegation updates and execution, and maintain a single source of truth for EVM-related state. This avoids the complexity of a separate "Delegator" actor or modifications to the core Filecoin account actors.

### State Management via HAMTs

Storing delegation mappings, nonces, and storage roots as HAMTs within the EVM actor state is idiomatic for the FEVM architecture. This achieves the functional goal of EIP-7702 without altering the fundamental nature of Filecoin account actors. The interpreter simulates the presence of the "pointer code" when required by `EXTCODE*` opcodes, maintaining compatibility.

### Dedicated Storage Roots

To ensure isolation and persistence of state when executing under an EOA authority, dedicated storage roots are maintained per authority (`delegation_storage`). When `InvokeAsEoa` is called, the EVM actor temporarily swaps its own storage root for the authority's storage root. This guarantees that delegated code writes to the authority's isolated storage, and this storage persists across transactions and delegate changes.

### Persistence on Revert (Atomicity Semantics)

EIP-7702 mandates that authorization processing (nonce bumps and delegation setting) must persist even if the outer transaction call reverts. This is critical for security, as it prevents the replay of authorizations. The `ApplyAndCall` implementation achieves this by flushing the state changes before executing the outer call, and by ensuring `ApplyAndCall` itself always returns `ExitCode::OK`, embedding the outer call's status in its return data.

## Backwards Compatibility

This FIP is largely backwards compatible.

  * It introduces a new transaction type (`0x04`), which does not affect the processing of existing transaction types.
  * It introduces a new method (`ApplyAndCall`) to the EVM actor, which does not conflict with existing methods.
  * It modifies the behavior of EOAs that explicitly opt-in via signed authorizations. EOAs that do not participate in EIP-7702 transactions remain unchanged.
  * The changes to the EVM actor state structure (adding new HAMTs) require a state migration during the network upgrade to initialize the empty HAMTs.

## Test Cases

The implementation includes comprehensive test coverage across the client (Lotus) and actors (builtin-actors) repositories.

### Client-Side (Lotus) Tests

  * **RLP Parsing:** Round-trip encoding/decoding of `0x04` transactions, including negative tests for invalid RLP structure, wrong tuple arity, invalid `yParity`, and non-canonical integer encodings (leading zeros). RLP fuzzing harnesses are included.
  * **CBOR Parameters:** Validation of the `ApplyAndCallParams` CBOR structure and interoperability tests.
  * **Authorization Hash:** Test vectors for `AuthorizationKeccak` (`keccak256(0x05 || rlp(...))`).
  * **Receipt Attribution:** Unit tests verifying that `delegatedTo` is correctly populated in receipts, sourced either from the `authorizationList` or the synthetic `Delegated(address)` event log.
  * **Gas Estimation:** Behavioral tests asserting that intrinsic overhead is applied based on the tuple count.

### Actor/FVM (builtin-actors) Tests

  * **`ApplyAndCall` Validation (`apply_and_call_invalids.rs`):**
      * Rejection of invalid `chainId`, `yParity > 1`, zero R/S, high-S signatures.
      * Nonce mismatch detection.
      * Rejection of duplicate authorities and exceeding the 64-tuple cap.
      * Pre-existence policy violation (authority is an EVM contract).
      * R/S padding interoperability (accepting 1-32 bytes, rejecting \>32 bytes).
  * **Atomicity and Persistence (`apply_and_call_atomicity_*.rs`):**
      * Verification that nonce bumps and delegation mappings persist even if the outer call reverts (including failures during `InvokeContract` or `InvokeAsEoa`).
      * Verification that `ApplyAndCall` returns `ExitCode::OK` with embedded status=0 on outer call failure.
  * **Interpreter Semantics:**
      * `eoa_call_pointer_semantics.rs`: Verification of `EXTCODESIZE` (23), `EXTCODECOPY` (pointer bytecode), and `EXTCODEHASH` for delegated EOAs.
      * `delegated_call_revert_data.rs`: Verification that revert data from delegated calls is correctly propagated to `RETURNDATA*` buffers.
      * `apply_and_call_selfdestruct.rs`: Verification that `SELFDESTRUCT` is a no-op in a delegated context.
      * Depth Limit enforcement (depth=1).
  * **Event Emission:** Tests asserting the correct topic hash for `Delegated(address)` and that the emitted address is the authority (EOA).
  * **Storage Isolation:** Tests verifying that delegated execution uses the authority's dedicated storage root and that this storage persists across transactions and delegate changes.

## Security Considerations

### Signature Validation and Robustness

The implementation enforces strict validation of authorization signatures:

  * **Low-S Enforcement (EIP-2):** All signatures must adhere to the low-s requirement to prevent malleability.
  * **Non-Zero R/S:** `r` and `s` values must be non-zero.
  * **R/S Padding:** The implementation accepts `r` and `s` values between 1 and 32 bytes, left-padding them to 32 bytes for recovery. Values exceeding 32 bytes are rejected. This ensures compatibility with clients that use minimally-encoded big-endian values while maintaining strict length validation.

### Replay Protection

  * **Domain Separation:** The use of the `0x05` magic prefix in the signature preimage ensures that authorization signatures cannot be replayed as standard transaction signatures (or vice-versa).
  * **Per-Authority Nonces:** The dedicated `delegation_nonces` mapping ensures that each authorization is used exactly once.
  * **Persistence on Revert:** The requirement that nonce bumps persist even if the outer call fails is critical. If state were rolled back on revert, authorizations could be replayed, compromising account security.

### Pre-existence Policy

The implementation enforces a policy that rejects authorizations if the authority address resolves to an existing EVM contract. This prevents EIP-7702 from being used to overwrite or alter the behavior of already deployed smart contracts.

### Delegation Depth Limit

To prevent infinite recursion or complex re-entrancy loops via delegation chains, the implementation enforces a strict depth limit of 1. When executing within a delegated context (`InvokeAsEoa`), further delegations are not followed.

### SELFDESTRUCT Behavior

Making `SELFDESTRUCT` a no-op within a delegated context prevents malicious or accidental destruction of the host EVM actor state and ensures that delegated code cannot bypass expected semantics to transfer the authority's funds.

## Implementation

The implementation for this FIP is developed across the following repositories:

  * **FVM Reference Implementation (ref-fvm) and Builtin Actors:** Implementation of the EVM actor state changes (HAMTs), the `ApplyAndCall` and `InvokeAsEoa` methods, and the necessary modifications to the FEVM interpreter semantics.
  * **Filecoin Clients (e.g., Lotus):** Implementation of `0x04` transaction parsing, Filecoin message construction targeting `EVM.ApplyAndCall`, RPC updates for receipts and transaction views, and gas estimation logic.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
