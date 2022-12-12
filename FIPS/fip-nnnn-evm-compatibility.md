---
fip: <to be assigned>
title: Filecoin EVM compatibility (FEVM)
author: Raúl Kripalani (@raulk), Steven Allen (@stebalien), Dimitris Vyzovitis (@vyzo), Aayush Rajasekaran (@arajasek), 
Akosh Farkash (@aakoshh)
discussions-to: <URL>
status: Draft
type: Technical Core
category: Core
created: 2022-12-02
spec-sections:
requires: N/A
replaces: N/A
---

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Simple Summary](#simple-summary)
- [Abstract](#abstract)
- [Change Motivation](#change-motivation)
- [Specification](#specification)
  - [EVM runtime actor](#evm-runtime-actor)
    - [Deployment](#deployment)
    - [State](#state)
    - [Actor interface (methods)](#actor-interface-methods)
      - [Method number `0` (`Constructor`)](#method-number-0-constructor)
      - [Method number `2` (`InvokeContract`)](#method-number-2-invokecontract)
      - [Method number `3` (`GetBytecode`)](#method-number-3-getbytecode)
      - [Method number `4` (`GetStorageAt`)](#method-number-4-getstorageat)
      - [Method number `5` (`InvokeContractDelegate`)](#method-number-5-invokecontractdelegate)
      - [Method numbers >= 1024**](#method-numbers--1024)
    - [Smart contract deployment](#smart-contract-deployment)
    - [Smart contract execution](#smart-contract-execution)
    - [Cross-contract calls](#cross-contract-calls)
    - [Ethereum addressing](#ethereum-addressing)
    - [Opcode support](#opcode-support)
      - [Opcodes without remarks](#opcodes-without-remarks)
      - [Opcodes with remarks](#opcodes-with-remarks)
    - [Precompiles](#precompiles)
    - [Gas](#gas)
    - [Errors](#errors)
  - [Ethereum Address Manager (EAM)](#ethereum-address-manager-eam)
    - [Deployment](#deployment-1)
    - [Procedure](#procedure)
    - [State](#state-1)
    - [Actor interface (methods)](#actor-interface-methods-1)
      - [Method number `1` (`Create`)](#method-number-1-create)
      - [Method number `2` (`Create2`)](#method-number-2-create2)
  - [Ethereum Externally Owned Account (EEOA)](#ethereum-externally-owned-account-eeoa)
  - [Ethereum JSON-RPC API](#ethereum-json-rpc-api)
  - [Filecoin Virtual Machine changes](#filecoin-virtual-machine-changes)
    - [Added syscalls](#added-syscalls)
    - [Removed syscalls](#removed-syscalls)
    - [Changed syscalls](#changed-syscalls)
    - [New externs](#new-externs)
    - [Memory limits](#memory-limits)
  - [Client changes](#client-changes)
    - [Tipset CID](#tipset-cid)
    - [Actor events](#actor-events)
- [Design Rationale](#design-rationale)
- [Backwards Compatibility](#backwards-compatibility)
- [Test Cases](#test-cases)
- [Security Considerations](#security-considerations)
- [Incentive Considerations](#incentive-considerations)
- [Product Considerations](#product-considerations)
- [Implementation](#implementation)
- [Appendix A: Notable differences between FEVM and EVM for smart contract developers](#appendix-a-notable-differences-between-fevm-and-evm-for-smart-contract-developers)
- [Appendix B: Upgrades](#appendix-b-upgrades)
- [Copyright](#copyright)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Simple Summary

This FIP introduces EVM compatibility to the Filecoin network on top of the
Filecoin Virtual Machine. Such compatibility consists of six elements, all of
which are specified in this FIP:

1. The EVM Runtime built-in actor
2. The Ethereum Address Manager actor
3. The Ethereum Externally Owned Account actor
4. The Ethereum JSON-RPC API
5. Supporting FVM-level changes
6. Supporting client-level changes

This FIP requires [FIP-0048 (f4 Address Class)], [FIP-0049 (Actor events)], and
TODO.

## Abstract

The Filecoin Virtual Machine (FVM) is a Wasm-based blockchain execution
environment designed to host multiple runtimes, drawing inspiration from
virtualization hypervisors.

This FIP introduces the first user-programmable runtime for the FVM: the
Ethereum Virtual Machine runtime. This is complemented by other five elements
necessary to offer seamless compatibility with existing Ethereum contracts,
tools and libraries, albeit incurring in justified departures from original
behaviors where necessary and reasonable.

The central component in this FIP is the EVM runtime built-in actor (1). It
hosts and interprets smart contracts expressed as EVM bytecode compatible with
the Ethereum Paris fork.

Foreign runtimes often make assumptions on the environment. One such assumption
has to do with addressing schemes. To support native Ethereum addressing, this
FIP introduces the Ethereum Address Manager actor (2), which leverages the f4
addressing class introduced in FIP-0048 to assign Ethereum-compatible addresses
to EVM smart contracts.

Validation of native Ethereum transactions is enabled by the Ethereum Account
actor (3), which represents Ethereum Externally-Owned Accounts in Filecoin. It
currently acts like a placeholder for a more sophisticated future version of an
Account Abstraction system.

External-facing compatiblity with existing Ethereum tools and libraries is
achieved by exposing the standardised Ethereum JSON-RPC API (4) from Filecoin
clients.

Finally, smaller changes at the FVM level (5) and the client level (6) are
introduced to back the above components.

## Change Motivation

TODO.

## Specification

### EVM runtime actor

The EVM runtime actor is the Filecoin native actor that _hosts_ and _executes_
EVM bytecode. It contains:

1. An embedded EVM interpreter, which processes EVM bytecode handling every
   instruction according to EVM expectations, with functional departures
   described herein.
2. The integration logic connecting the EVM interpreter with the Filecoin
   environment, chain, and virtual machine (FVM).
3. A collection of Ethereum and Filecoin-specific precompiles, specified later.

**Historical support.** EVM opcode and precompile support is restricted to the
Ethereum Paris fork. Historical Ethereum behaviors are not supported.

**Transactions types.** The only supported Ethereum transaction type is the
EIP-1559 transaction. Such transactions carry a gas fee cap and a gas premium,
both of which map cleanly to Filecoin's message model.

**Native currency.** The native currency of the Filecoin EVM runtime is
filecoin. This environment has no dependence to, or understanding of, Ether as a
currency.

#### Deployment

**Built-in actor.** The Filecoin EVM runtime is deployed on-chain a built-in
actor. Its Wasm bytecode is installed into the network by adding it to the
blockstore and linking it to the System actor's state via its CodeCID.

**Prototype actor.** The EVM runtime is a prototype actor (and not a singleton
actor). At the time of writing, this makes the EVM runtime actor comparable to
the Miner, Payment Channel, and Multisig builtin-actors, and unlike the Storage
Power, Storage Market, Cron, and other singleton actors.

#### State

The state of the EVM runtime actor is as follows:

```rust
pub struct State {
    /// The EVM contract bytecode resulting from calling the
    /// initialization code (init code) by the constructor.
    pub bytecode: Cid,

    /// The EVM contract state dictionary.
    /// All EVM contract state is a map of U256 -> U256 values.
    ///
    /// HAMT<U256, U256>
    pub contract_state: Cid,

    /// The EVM nonce used to track how many times CREATE or
    /// CREATE2 have been called.
    pub nonce: u64,
}
```

**Contract storage.** EVM storage (u256 => u256 map) is backed by a Filecoin
HAMT with special optimizations, rendering it more mechanically sympathetic to
EVM storage read and write patterns. `SLOAD` and `SSTORE` EVM opcodes map to
reads and writes onto this HAMT, respectively, and ultimately to `ipld`
syscalls specified in FIP-0030.

TODO: specify these optimizations, or the KAMT.

#### Actor interface (methods)

The EVM runtime actor handles messages sent with the following method numbers.
The canonical implementation can be found in the executable actors spec
([`filecoin-project/builtin-actors`]).

##### Method number `0` (`Constructor`)

Initializes a new EVM smart contract, whose bytecode is supplied as an input
parameter. Invocable only by the Ethereum Address Manager via the Init actor
(see details under [Smart contract deployment](#smart-contract-deployment)).
This precondition is checked by validating the immediate caller and asserting
that the EVM runtime actor under construction has been assigned an f410 address.

_Input parameters_

```rust
// DAG-CBOR tuple encoded.
pub struct ConstructorParams {
    /// The actor's "creator" (specified by the EAM).
    pub creator: EthAddress,
    /// The EVM initcode that will construct the new EVM actor.
    pub initcode: RawBytes,
}
```

_Return value_

None.

_Errors_

// TODO

##### Method number `2` (`InvokeContract`)

Invokes an EVM smart contract. Loads the bytecode from state and dispatches the
input data to it. Universally callable.

_Input parameters_

Raw bytes, encoded as a DAG-CBOR byte string.

_Return value_

Raw bytes, encoded as a DAG-CBOR byte string.

_Errors_

// TODO

##### Method number `3` (`GetBytecode`)

Returns the CID of the contract's EVM bytecode, adding it to the caller's
reachable set (this is not necessary at the moment with the current FVM version,
but will happen implicitly in the future).

_Input parameters_

None.

_Return value_

CID of the contract's bytecode as stored in state.

_Errors_

// TODO

##### Method number `4` (`GetStorageAt`)

Returns the value stored at the specified EVM storage slot. This method exists
purely for state encapsulation purposes and is only used for external
observability, namely to back the `eth_getStorageAt` JSON-RPC method to keep
clients from having to reach into state in an ad-hoc manner. Cannot be called
on-chain. Filecoin clients should set the caller to be `f00` when using this
method.

_Input parameters_

```rust
// DAG-CBOR tuple encoded.
pub struct GetStorageAtParams {
    pub storage_key: U256, // encoded as a DAG-CBOR byte string
}
```

_Return value_

Storage value (U256), encoded as a DAG-CBOR byte string. If the storage key
doesn't exist, it returns a 0-filled 32-byte array.

_Errors_

- Exit code `USR_FORBIDDEN` (18) when not called by address f00.
- Exit code `USR_ASSERTION_FAILED` (24) on internal errors.

##### Method number `5` (`InvokeContractDelegate`)

Recursive invocation entrypoint backing calls made through the `DELEGATECALL`
opcode. Only callable by self.

_Input parameters_

```rust
// DAG-CBOR tuple encoded.
pub struct DelegateCallParams {
    /// CID of the EVM bytecode to invoke under self's context.
    pub code: Cid,
    /// The contract invocation parameters
    pub input: Vec<u8>, // encoded as a DAG-CBOR byte string
}
```

_Return value_

Same as `invoke_contract`.

_Errors_

- Exit code `USR_FORBIDDEN` (18) when caller is not self.
// TODO

##### Method numbers >= 1024**

Invocation entrypoint for Filecoin native messages carrying a method number
above or equal to 1024 (a superset of the public range of the [FRC42 calling
convention]). Creates synthetic EVM input data satisfying the Solidity call
convention for this method signature:

```solidity
// Function selector: 0x868e10c4
// Args: method number, params codec, raw params
// Returning: bytes
handle_filecoin_method(uint64,uint64,bytes)
```

TODO: specify the input data encoding

_Input parameters_

Raw bytes, assumed to be DAG-CBOR byte string.

_Return value_

Raw bytes, encoded as a DAG-CBOR byte string.

#### Smart contract deployment

**Process.** New EVM smart contracts are deployed to the Filecoin chain by
_instantiating_ the EVM runtime actor through its
[`Constructor`](#method-number-0-constructor), and supplying it the contract's
EVM init code. This action must be performed through the [Ethereum Address
Manager (EAM)](#ethereum-address-manager).

**Result.** The above results in the creation of a new actor on-chain of type
_EVM runtime actor_ with a new set of f0, f2, and f410 addresses, backed by the
CodeCID of the _EVM runtime actor_, holding the above-specified state, and
exposing the aforementioned interface.

#### Smart contract execution

A smart contract can be invoked through one of two entrypoints. Which one is
used depends on the message submission mechanism employed at origin.

1. Ethereum transactions, with the special case of Ethereum value transfers.
2. Native Filecoin messages.

**Ethereum transactions** carry no explicit method number. They may originate
externally or internally:

1. Externally from Ethereum wallets. These are submitted to Filecoin via the
   Ethereum JSON-RPC endpoint through the `eth_sendRawTransaction`, `eth_call`,
   or `eth_estimateGas` operations.
2. Internally from other EVM smart contracts, via the `CALL`, `STATICCALL`, or
   `DELEGATECALL` opcodes.

Ethereum transactions carrying input data are implicitly assigned method number
`2` at the origin site. These messages are handled by the `invoke_contract`
method, which passes on the input data to the EVM bytecode for internal dispatch
after unframing it from its DAG-CBOR envelope (byte string type).

Ethereum transactions carrying no input data are presumed to be **Ethereum value
transfers**. These are converted to Filecoin sends (by setting method number =
0), and unlike in Ethereum, **they have no opportunity to trigger smart contract
logic**. Note that such messages may carry value 0.

**Native Filecoin messages** carry an explicit method number. They may originate
at external or internal sites:

1. Externally at Filecoin wallets.
1. Internally at Filecoin actors via internal sends.
2. Internally from EVM smart contracts using the `callactor` precompile.

Correctly handling these messages requires exposing the method number to the EVM
bytecode, and making no assumptions about the input data, thus exposing the
codec as well.

These messages are handled through the `handle_filecoin_message` method above,
so long as the method number falls in the superset of the FRC42 starting at 2^10
instead of 2^24.

#### Cross-contract calls

TODO.

#### Ethereum addressing

EVM smart contracts implicitly assume they are running in an Ethereum
environment. Ethereum uses 160-bit (20-byte) addresses with no distinction of
classes between EOAs, contracts, or unknowns. Addresses are the Keccak-256 hash
of the public key of an account, truncated to preserve the 20 rightmost bytes.
Solidity and the [Contract ABI spec] represent addresses with the `address`
type, equivalent to `uint160`.

The mechanism to support foreign addressing schemes in Filecoin is proposed in
[FIP-0048 (f4 Address Class)]. The [Ethereum Address
Manager](#ethereum-address-manager), specified later, assigns
Ethereum-compatible f4 addresses to EVM smart contracts deployed through it.

EVM smart contracts deployed on Filecoin can use two types of addresses in
opcodes. Both these addresses fit in a 160-bit (20 bytes) width:

1. Masked Filecoin ID addresses.
2. Ethereum addresses.

**Masked Filecoin ID addresses** are distinguished through a byte mask. The high
byte is 0xff (discriminator), followed by thirteen 0x00s (padding), then the
uint64 ID of the actor.

```
    |----- padding ------|    |----- actor id -----|
0xff0000000000000000000000 || <uint64 ID big endian>
```

All address inputs that do not match this masked form are interpreted as
**Ethereum addresses** and converted to their equivalent f410 address before
performing an FVM syscall.

A special case is the **Ethereum zero address**
(`0x0000000000000000000000000000000000000000`), for whom an Ethereum account
(`TODO`) is created under its corresponding f4 address (`TODO`) in the state
tree during the migration where this FIP goes live.

It is worthy to note that Ethereum and Filecoin precompiles sit at the
**Ethereum address** range. They receive special treatment inside the EVM
runtime actor, and are never converted to f410 addresses.

#### Opcode support

All opcodes from the [Ethereum Paris hard fork] are supported. This section
enumerates all supported opcodes, noting functional departures from their
Ethereum counterparts. Opcodes are referred to by their mnemonic name.

##### Opcodes without remarks

These opcodes are local to the EVM interpreter and have no departures from the
standard behaviour.

- Arithmetic family: ADD, MUL, SUB, DIV, SDIV, MOD, SMOD, ADDMOD, MULMOD, EXP,
  SIGNEXTEND.
- Boolean operators: LT, GT, SLT, SGT, EQ, ISZERO, AND, OR, XOR, NOT.
- Bitwise operations: BYTE, SHL, SHR, SAR.
- Control flow: STOP, JUMPDEST, JUMP, JUMPI, PC, STOP, RETURN, INVALID.
- Parameters: CALLDATALOAD, CALLDATASIZE, CALLDATACOPY, RETURNDATASIZE,
  RETURNDATACOPY.
- Stack manipulation: POP, PUSH{1..32}, DUP{1..32}, SWAP{1..16}.

##### Opcodes with remarks

**Memory: MLOAD, MSTORE, MSTORE8, MSIZE.** EVM memory is modelled as an object
inside the interpreter, ultimately backed by Wasm memory. Usage of of these
instructions incurs in Wasm memory expansion and access costs.

**Accessors: ADDRESS.** Returns the masked Filecoin ID address of the executing
contract.

**Accessors: BALANCE.** Returns the filecoin balance of the contract, in attoFIL
(same precision as Ethereum).

**Accessors: ORIGIN.** Returns the masked Filecoin ID address of the account
where the chain message originated.

**Accessors: CALLER.** Returns the masked Filecoin ID address of the immediate
caller of the contract.

**Accessors: CALLVALUE.** Returns the filecoin value sent in the message, in
attoFIL (same precision as Ethereum).

**Accessors: GASPRICE.** TODO.

**Accessors: BLOCKHASH.** TODO.

**Accessors: COINBASE.** TODO.

**Accessors: TIMESTAMP.** TODO.

**Accessors: NUMBER.** TODO.

**Accessors: DIFFICULTY.** TODO.

**Accessors: GASLIMIT.** TODO.

**Accessors: CHAINID.** TODO.

**Accessors: BASEFEE.** TODO.

**Accessors: SELFBALANCE.** TODO.

**Accessors: GAS.** TODO.

**Control flow: REVERT.** TODO.

**Hashing: KECCAK256.** Makes a syscall to `crypto::hash` with the supplied
preimage and the Keccak-256 multihash.

**Logging: LOG{0..4}.** TODO.

**Storage: SLOAD, SSTORE.** TODO.

**Lifecycle: CREATE.** TODO.

**Lifecycle: CREATE2.** TODO.

**Lifecycle: SELFDESTRUCT.** TODO.

**Calls: CALL.** TODO.

**Calls: CALLCODE.** TODO.

**Calls: DELEGATECALL.** TODO. InvokeContractDelegate.

**Calls: STATICCALL.**  TODO. Read-only mode.

**External code: EXTCODESIZE.**

**External code: EXTCODECOPY.**

**External code: EXTCODEHASH.**

#### Precompiles

**Ethereum precompiles.** The EVM runtime actor supports all Ethereum
precompiles available in the Ethereum Paris fork, sitting at their original
addresses.

| Ethereum Address | Precompile   |
| ---------------- | ------------ |
| `0x01`           | `ecRecover`  |
| `0x02`           | `SHA2-256`   |
| `0x03`           | `RIPEMD-160` |
| `0x04`           | `identity`   |
| `0x05`           | `modexp`     |
| `0x06`           | `ecAdd`      |
| `0x07`           | `ecMul`      |
| `0x08`           | `ecPairing`  |
| `0x09`           | `blake2f`    |

**Filecoin-specific precompiles.** Additionally, the following Filecoin-specific
precompiles are supported:

| Ethereum Address | Precompile           |
| ---------------- | -------------------- |
| `0x0a`           | `resolve_address`    |
| `0x0b`           | `lookup_address`     |
| `0x0c`           | `get_actor_code_cid` |
| `0x0d`           | `get_randomness`     |
| `0x0e`           | `call_actor`         |

**Precompile `0x0a`: `resolve_address`**

// TODO

_Input paramters_

_Return_

_Errors_

**Precompile `0x0b`: `lookup_address`**

// TODO

_Input paramters_

_Return_

_Errors_

**Precompile `0x0c`: `get_actor_code_cid`**

// TODO

_Input paramters_

_Return_

_Errors_

**Precompile `0x0d`: `get_randomness`**

// TODO

_Input paramters_

_Return_

_Errors_

**Precompile `0x0e`: `call_actor`**

// TODO

_Input paramters_

_Return_

_Errors_

#### Gas

Gas metering and execution halt are performed according to the Filecoin gas
model. EVM smart contracts accrue:

- Execution costs: resulting from the handling of Wasm instructions executed
  during the interpretation of the EVM bytecode, _as well as_ the EVM runtime
  actor logic (e.g. method dispatch, payload handling, and more).
- Syscall and extern costs: resulting from the syscalls made by the EVM opcode
  handlers, _and_ the EVM runtime actor logic itself.
- memory expansion costs: resulting from the allocation of Wasm memory pages.
- Storage costs: resulting from IPLD state reads and accesses, directly by the
  smart contract as a result of `SSTORE` and `SLOAD` opcodes, or indirectly by
  the EVM runtime actor during dispatch or opcode handling.

**Gas-related opcodes.** Gas-related opcodes such as `GAS` and `GASLIMIT` return
Filecoin gas, coercing their natural u64 type to u256 (EVM type). The gas limit
supplied to the `CALL`, `DELEGATECALL` and `STATICCALL` opcodes is also Filecoin
gas.

Consequently, contracts ported from Ethereum that use literal gas values (e.g.
the well known 2300 gas price for bare value transfers) may require adaptation,
as these gas values won't directly translate into the Filecoin gas model.

We note that the EVM runtime actor backing EVM smart contracts may be upgraded
over time. Migrations performed at future network upgrades may batch-update all
CodeCID of EVM smart contracts to a new version of the EVM runtime actor. Doing
so would probably cause gas costs for This would result in an alteration of gas
costs with existing contracts upgrading automatically to the new EVM runtime.
This may alter gas costs for the same transactions. For this reason, users are
advised against hardcoding assumptions about gas in their contracts.

#### Errors

TODO.

### Ethereum Address Manager (EAM)

We introduce the **Ethereum Address Manager (EAM) actor** as a singleton
built-in actor sitting at ID address `10`. This actor fulfills two purposes:

1. It manages the f4 address class namespace under its ID address (i.e. f410),
   assigning Ethereum-compatible addresses under it.
2. It acts as the entrypoint for deployment of EVM smart contracts, respecting
   Ethereum rules and semantics.

For the latter, this actor offers two Filecoin methods `Create` and `Create2`,
equivalent to their Ethereum counterparts. In Ethereum, `CREATE` and `CREATE2`
differ in their address generation rules:

- `CREATE` uses the protocol-provided nonce to derive the contract's address,
  and is thus non-deterministic.
- `CREATE2` takes an explicit user-provided salt to compute a deterministic
  address. It is suitable for counterfactual deployments.

#### Deployment

The EAM is deployed as a singleton actor under ID address `10`. The deployment
happens during the state migration where this FIP goes live.

The EAM is allow-listed in the Init Actor as a caller of its `Exec4` method,
specified in FIP-0048.

#### Procedure

The procedure to deploy EVM smart contracts to the Filecoin chain is as follows:

1. The contract deployment message enters the Ethereum Address Manager (EAM)
   through the `Create` or `Create2` method. 
2. The EAM computes an `f410` address according to the heuristics of the invoked
   method (see below). The resulting f410 address is semantically equivalent to
   the one Ethereum would've generated for the same inputs, thus retaining tool
   compatibility.
2. The EAM invokes the Init actor's `Exec4` method (see [FIP-0048 (f4 Address
   Class)]), supplying the CodeCID of the EVM runtime actor, the constructor
   parameters (EVM init code and original creator address), and the assigned
   f410 address.

#### State

None.

#### Actor interface (methods)

##### Method number `1` (`Create`)

Deploys a smart contract taking EVM init bytecode and accepting a nonce from the
user. Refer to [Procedure](#procedure) for a description of the deployment
procedure.

The `create` method is used in two cases:

1. When an EEOA actor deploys a smart contract by submitting a native Ethereum
   transaction containing initcode through the Ethereum JSON-RPC API endpoint.
   The endpoint detects the deployment operation, and translates the Ethereum
   transaction to an `EAM#Create` Filecoin message.
2. When an EVM smart contract calls the `CREATE` opcode.

Note that this differs from Ethereum in that we take a user-provided nonce as a
parameter. This is necessary so that the EVM runtime actor can supply the
contract's nonce when handling `CREATE` to the EAM. This is a mild departure
from Ethereum's behavior as it allows an EEOA to deploy a contract with an
arbitrary nonce. No safety violations are possible because the system guarantees
that we don't deploy over an existing actor anyway (those constraints are
enforced by the init actor and the FVM itself).

_Input parameters_

```rust
// DAG-CBOR tuple encoded.
pub struct CreateParams {
    /// EVM init code.
    pub initcode: Vec<u8>,
    /// Nonce with which to create this smart contract.
    pub nonce: u64,
}
```

_Return value_

```rust
// DAG-CBOR tuple encoded.
pub struct Return {
    /// The ID of the EVM runtime actor that was constructed.
    pub actor_id: ActorID,
    /// Its f2 address.
    pub robust_address: Address,
    /// Its Ethereum address, translatable to an f410 address.
    pub eth_address: [u8; 20],
}
```

_Errors_

TODO.

##### Method number `2` (`Create2`)

Deploys a smart contract taking EVM init bytecode and accepting a user-provided
salt to generate a deterministic Ethereum address (translatable to an f410
address). Refer to [Procedure](#procedure) for a description of the deployment
procedure.

`Create2` is used in a single case: to handle the `CREATE2` opcode while
executing EVM bytecode within the EVM runtime actor.

_Input parameters_

```rust
pub struct Create2Params {
    /// EVM init code.
    pub initcode: Vec<u8>,
    /// User provided salt.
    pub salt: [u8; 32],
}
```

_Return value_

Same as [`Create`](#method-number-1-create).

### Ethereum Externally Owned Account (EEOA)

TODO (@aayush).

### Ethereum JSON-RPC API

TODO (@raulk).

### Filecoin Virtual Machine changes

#### Added syscalls

**`network::context`**

```rust
#[repr(packed, C)]
pub struct NetworkContext {
   /// The current epoch.
   pub epoch: ChainEpoch,
   /// The current time (seconds since the unix epoch).
   pub timestamp: u64,
   /// The current base-fee.
   pub base_fee: TokenAmount,
   /// The network version.
   pub network_version: u32,
}

/// Returns the details about the network.
///
/// # Errors
///
/// None
pub fn context() -> Result<NetworkContext>;
```

**`network::tipset_cid`**

```rust
/// Retrieves a tipset's CID within the last finality, if available
///
/// # Arguments
///
/// - `epoch` the epoch being queried.
/// - `ret_off` and `ret_len` specify the location and length of the buffer into which the
///   tipset CID will be written.
///
/// # Returns
///
/// Returns the length of the CID written to the output buffer.
///
/// # Errors
///
/// | Error               | Reason                                       |
/// |---------------------|----------------------------------------------|
/// | [`IllegalArgument`] | specified epoch is negative or in the future |
/// | [`LimitExceeded`]   | specified epoch exceeds finality             |
pub fn tipset_cid(
   epoch: i64,
   ret_off: *mut u8,
   ret_len: u32,
) -> Result<u32>;
```

**`actor::lookup_address`**

```rust
/// Looks up the "predictable" address of the target actor.
///
/// # Arguments
///
/// `addr_buf_off` and `addr_buf_len` specify the location and length of the output buffer in
/// which to store the address.
///
/// # Returns
///
/// The length of the address written to the output buffer, or 0 if the target actor has no
/// predictable address.
///
/// # Errors
///
/// | Error               | Reason                                                           |
/// |---------------------|------------------------------------------------------------------|
/// | [`NotFound`]        | if the target actor does not exist                               |
/// | [`BufferTooSmall`]  | if the output buffer isn't large enough to fit the address       |
/// | [`IllegalArgument`] | if the output buffer isn't valid, in memory, etc.                |
pub fn lookup_address(
   actor_id: u64,
   addr_buf_off: *mut u8,
   addr_buf_len: u32,
) -> Result<u32>;
```

**`actor::balance_of`**

```rust
/// Returns the balance of the actor at the specified ID.
///
/// # Arguments
///
/// `actor_id` is the ID of the actor whose balance is to be returned.
///
/// # Returns
///
/// The balance of the specified actor, or 0 if the actor doesn't exist.
///
/// # Errors
///
/// TODO
/// 
pub fn balance_of(
   actor_id: u64
)  -> Result<super::TokenAmount>;
```

**`actor::next_actor_address`**

```rust
/// Generates a new actor address for an actor deployed by the calling actor.
///
/// **Privileged:** May only be called by the init actor.
pub fn next_actor_address(obuf_off: *mut u8, obuf_len: u32) -> Result<u32>;
```

**`crypto::recover_secp_public_key`**

```rust
/// Recovers the signer public key from a signed message hash and its signature.
///
/// Returns the public key in uncompressed 65 bytes form.
///
/// # Arguments
///
/// - `hash_off` specify location of a 32-byte message hash.
/// - `sig_off` specify location of a 65-byte signature.
///
/// # Errors
///
/// | Error               | Reason                                               |
/// |---------------------|------------------------------------------------------|
/// | [`IllegalArgument`] | signature or hash buffers are invalid                |
pub fn recover_secp_public_key(
   hash_off: *const u8,
   sig_off: *const u8,
) -> Result<[u8; SECP_PUB_LEN]>;
```

**`event::emit_event`**

See [FIP-0049 (Actor events)].

```rust
/// Emits an actor event to be recorded in the receipt.
///
/// Expects a DAG-CBOR representation of the ActorEvent struct.
///
/// # Errors
///
/// | Error               | Reason                                                              |
/// |---------------------|---------------------------------------------------------------------|
/// | [`IllegalArgument`] | entries failed to validate due to improper encoding or invalid data |
pub fn emit_event(
   evt_off: *const u8,
   evt_len: u32,
) -> Result<()>;
```

**`gas::available`**

```rust
/// Returns the amount of gas remaining.
pub fn available() -> Result<u64>;
```

**`vm::exit`**

```rust
/// Abort execution with the given code and optional message and data for the return value.
/// The code and return value are recorded in the receipt, the message is for debugging only.
///
/// # Arguments
///
/// - `code` is the `ExitCode` to abort with.
///   If this code is zero, then the exit indicates a successful non-local return from
///   the current execution context.
///   If this code is not zero and less than the minimum "user" exit code, it will be replaced with
///   `SYS_ILLEGAL_EXIT_CODE`.
/// - `blk_id` is the optional data block id; it should be 0 if there are no data attached to
///   this exit.
/// - `message_off` and `message_len` specify the offset and length (in wasm memory) of an
///   optional debug message associated with this abort. These parameters may be null/0 and will
///   be ignored if invalid.
///
/// # Errors
///
/// None. This function doesn't return.
pub fn exit(code: u32, blk_id: u32, message_off: *const u8, message_len: u32) -> !;
```

**`vm::message_context`**

```rust
#[repr(packed, C)]
pub struct MessageContext {
   /// The current call's origin actor ID.
   pub origin: ActorID,
   /// The caller's actor ID.
   pub caller: ActorID,
   /// The receiver's actor ID (i.e. ourselves).
   pub receiver: ActorID,
   /// The method number from the message.
   pub method_number: MethodNum,
   /// The value that was received.
   pub value_received: TokenAmount,
   /// The current gas premium
   pub gas_premium: TokenAmount,
   /// The current gas limit
   pub gas_limit: u64,
   /// Flags pertaining to the currently executing actor's invocation context.
   pub flags: ContextFlags,
}

/// Returns the details about the message causing this invocation.
///
/// # Errors
///
/// None
pub fn message_context() -> Result<MessageContext>;
```

#### Removed syscalls

- `vm::abort`: replaced by the more general syscall `vm::exit`, which can accept
  a zero exit code, as well as return data on error.
- `vm::context`: renamed to `vm::mesage_context`.
- `network::base_fee`: integrated into `network::context`.
- `actor::new_actor_address`: replaced by `actor::next_actor_address`.

#### Changed syscalls

- TODO Send takes gas limit and flags.

#### New externs

TODO.

#### Memory limits

TODO, maybe in a separate FIP.

### Client changes

#### Tipset CID

TODO.

#### Actor events

See [FIP-0049 (Actor events)].

## Design Rationale

> TODO:
> - Flat vs nested contract deployment model.
> - ...

## Backwards Compatibility

TODO.

## Test Cases

## Security Considerations

TODO.

## Incentive Considerations

TODO.

## Product Considerations

TODO.

## Implementation

TODO.

## Appendix A: Notable differences between FEVM and EVM for smart contract developers

TODO.

## Appendix B: Upgrades

TODO.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).


[`filecoin-project/builtin-actors`]: https://github.com/filecoin-project/builtin-actors
[FRC42 calling convention]: https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0042.md
[FIP-0048 (f4 Address Class)]: https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0048.md
[Contract ABI spec]: https://docs.soliditylang.org/en/v0.5.3/abi-spec.html
[Ethereum Paris hard fork]: https://github.com/ethereum/execution-specs/blob/master/network-upgrades/mainnet-upgrades/paris.md
[FIP-0049 (Actor events)]: https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0049.md