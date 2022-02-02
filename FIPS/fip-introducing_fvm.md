---
fip: <to be assigned>
title: Introducing the Filecoin Virtual Machine (FVM)
authors: Raúl Kripalani (@raulk), Steven Allen (@stebalien)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/287
status: Draft
type: Technical Core
category: Core
created: 2022-01-26
spec-sections: 
  - TBD
requires: N/A
replaces: N/A
---

# Introducing the Filecoin Virtual Machine (FVM)

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Simple Summary](#simple-summary)
- [Abstract](#abstract)
- [Change Motivation](#change-motivation)
- [FVM specification](#fvm-specification)
  - [Reference implementation](#reference-implementation)
  - [Context and VM interface](#context-and-vm-interface)
  - [Technology](#technology)
  - [Responsibilities](#responsibilities)
  - [Core technical design](#core-technical-design)
    - [Machine](#machine)
    - [Call Manager](#call-manager)
    - [Invocation Container](#invocation-container)
    - [Syscalls](#syscalls)
    - [Kernel](#kernel)
    - [Externs](#externs)
  - [Actors](#actors)
    - [Actor types](#actor-types)
      - [Built-in actors](#built-in-actors)
      - [Native actors](#native-actors)
      - [Foreign actors](#foreign-actors)
    - [Actor bytecode representation](#actor-bytecode-representation)
    - [Actor deployment](#actor-deployment)
    - [Actor message dispatch](#actor-message-dispatch)
  - [Syscalls](#syscalls-1)
    - [Namespace: `actor`](#namespace-actor)
    - [Namespace: `crypto`](#namespace-crypto)
    - [Namespace: `gas`](#namespace-gas)
    - [Namespace: `ipld`](#namespace-ipld)
    - [Namespace: `message`](#namespace-message)
    - [Namespace: `network`](#namespace-network)
    - [Namespace: `rand`](#namespace-rand)
    - [Namespace: `send`](#namespace-send)
    - [Namespace: `self`](#namespace-self)
    - [Namespace: `vm`](#namespace-vm)
  - [Externs](#externs-1)
  - [IPLD memory model](#ipld-memory-model)
  - [Module caching](#module-caching)
  - [Gas charging](#gas-charging)
  - [Specific actor coupling](#specific-actor-coupling)
- [Design Rationale](#design-rationale)
- [Backwards Compatibility](#backwards-compatibility)
- [Test Cases](#test-cases)
- [Security Considerations](#security-considerations)
- [Incentive Considerations](#incentive-considerations)
- [Product Considerations](#product-considerations)
- [Implementation](#implementation)
- [Copyright](#copyright)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Simple Summary

User-programmability is the ability to deploy and run arbitrary user-provided
code on some infrastructure, in this case a blockchain network.

Today, the Filecoin blockchain lacks on-chain user-programmability. This FIP is
part of a series that aims to introduce this capability.

A change of this magnitude impacts many components. Concretely:

1. The chain state layer, to store and load user-provided code.
2. The execution layer, to compile/interpret user-provided code, run state
   transitions involving such code, and verify the results.
3. The gas model, to secure the network and modulate chain capacity
   demand/supply dynamics in the face of user-programmable code.
4. The preexisting baseline protocol, to facilitate programmability against
   system functionality.

This FIP focuses on (1) and (2). The remaining points are out of scope of this
FIP, and will be addressed by subsequent proposals.

## Abstract

We specify the Filecoin Virtual Machine (FVM), an IPLD-ready Wasm-based
execution layer capable of running arbitrary user-provided code. The FVM
replaces the [existing non-programmable execution layer][existing
non-programmable VM].

The logic of native actors (the equivalent of smart contracts in Filecoin) is
deployed as Wasm bytecode. Foreign actors targeting non-Filecoin runtimes such
as the Ethereum Virtual Machine are also supported through runtime emulation.

We provide a reference architecture for the FVM, and explain its various
components: (a) Machine, (b) Call Manager, (c) Invocation Container, (d) Kernel,
(e) Syscalls, and (f) Externs. We define the contract that actor code must
adhere to, the catalogue of available syscalls, the mechanics of IPLD state
manipulation, and further technical details

This FIP introduces the technical foundations of the FVM. It will be accompanied
by two subsequent FIPs. They will respectively propose: (1) an atomic switch
from the current VM to a non-programmable version of the FVM, and (2) a new gas
model adequate for on-chain user-programmability.

## Change Motivation

The desire for user-programmability in Filecoin is pronounced and
well-recognized. It is the key to unlock enormous latent potential, as it
enables permissionless community-driven innovation on the Filecoin network.

Some of the envisioned benefits include:

- The proliferation of innovative, trustless solutions in user space.
  - The ability to program behaviors on top of the existing Filecoin primitives
    confers new degrees of freedom to developers and increases the potential for
    innovation.
  - Some examples include: decentralized compute, Data DAOs, Layer 2 networks,
    cross-chain bridges, alternative storage markets, programmable storage,
    collateral loan markets, and more.
- The migration of functionality from system space to user space, thus resulting
  in a lower dependence on built-in actor evolution, which is largely
  bottlenecked on the Core Devs and the FIP process.
- The emergence of an ecosystem of composable and stackable building blocks and
  primitives exposed through standardised interfaces, enabling the construction
  of richer, composite, interconnected solutions.
- Unification of built-in actors across implementations to speed up protocol
  development.
- Ability to conduct protocol upgrades that modify built-in actor logic through
  on-chain governance processes.
- Potential for more areas of the Filecoin protocol to migrate to Wasm space
  (e.g. block validation, fork choice rule, etc.), it becomes possible to deploy
  protocol changes as Wasm modules to all clients, conditional upon on-chain
  voting.

## FVM specification

This section provides a fundamental definition of the Filecoin Virtual Machine
(FVM). It is intended to act as a baseline for future FIPs to enhance and
evolve, as new capabilities, innovations and mechanisms are worked out.

_Writing style_

The FVM is a system under development, and some aspects are still in flux. For
this reason, this spec combines two styles to provide a well-rounded picture:

- Normative style, for concrete behaviors, rules, interfaces and types that we
  propose to introduce imminently. _Conveyed by present tense._
- Directional style: lays out the thinking for upcoming behaviors, rules,
  interfaces, and types, without mandating concrete technical choices yet.
  _Conveyed by future tense and/or speculative language._

### Reference implementation

[filecoin-project/ref-fvm] is a reference implementation to serve as a companion
to this specification.

### Context and VM interface

In the Filecoin blockchain, the virtual machine (VM) is the component in the
execution layer responsible for applying transactions over a state tree. These
transactions are encapsulated in messages. There are two kinds of messages:

- Explicit messages are sent by secp256k1 or BLS account actors, appear on-chain
  when executed, and carry a signature to prove their authenticity. 
- Implicit messages are generated by the system, do not appear on chain, and
  they carry no signature. Examples include cron ticks and reward cycles.

A VM is instantiated with these input parameters:

```rust
/// These code samples are simplified with respect to the actual implementation in ref-fvm.
let machine = Machine::new(
    epoch,             // chain epoch at which to execute messages
    base_fee,          // base fee currently in effect
    base_circ_supply,  // base circulating supply
    nv,                // network version
    state_root,        // root CID of the initial state tree
    blockstore,        // blockstore to load and save state objects during execution
)
```

Messages are then applied to the `machine`. Every application generates a return
object containing at least a message receipt, a miner penalty, and a miner tip.
Implementations may return extra data such as diagnostics info, backtraces, or
gas traces.

```rust
let ApplyRet { receipt, penalty, tip } := machine.apply_message(msg1);
let ApplyRet { receipt, penalty, tip } := machine.apply_message(msg2);
let ApplyRet { receipt, penalty, tip } := machine.apply_message(msg3);
```

The message receipt is recorded on chain. It holds the exit code of the
transaction, the gas used, and (optionally) return data only if successful.

The penalty and the tip are values used by the cryptoeconomic rules of the
protocol to calculate the block reward for the block producer.

Once the caller has finished applying all messages, it flushes the machine. This
computes the final state root. Depending on implementation, this operation may
also commit newly written blocks to the blockstore.

```rust
let final_state_root = machine.flush();
```

With the introduction of the FVM, this VM API is largerly preserved, although
implementations may opt to deviate from it.

### Technology

The proposed FVM execution runtime is [WebAssembly (Wasm)] with 32-bit memories.
64-bit memories are still under development in the [memory64] extension.

Wasm with 32-bit memories supports 64-bit integer types and arithmetic, it just
can't address memory beyond 4GiB. This size is deemed sufficient for blockchain
state transition use cases, but may be limiting for future and more generalised
applications of the FVM.

The FVM requires [multi-value support]. It currently forbids [SIMD
instructions], floating number values and operations, and [threads] to prevent
[Nondeterministic][Nondeterminism] behavior. However, these constraints may vary in the future.

### Responsibilities

The FVM applies messages to the state tree. It is not responsible for advancing
the chain itself. Concretely, it is mainly responsible for:

- Loading on-chain Wasm modules and compiling them to machine code.
- Performing preflight checks on the supplied messages.
- Instantiating the object stack described in the [core technical
  design](#core-technical-design) to apply messages.
- Routing calls across actors, via the Call Manager abstraction.
- Processing syscalls from actors, and delivering the results.
- Interfacing with the outer environment (Filecoin client) when necessary.
- Managing IPLD state read and write operations.

### Core technical design

This diagram serves as a reference for the technical design of the FVM.

![Technical design](./fip-introducing_fvm/technical-design.png)

#### Machine

The Machine is an instantiation of the FVM on a concrete epoch, over a specific
state root, ready to take in messages for execution as explained above.

#### Call Manager

The Call Manager coordinates the call stack involved in processing a given
message. This entails setting up and destroying Invocation Containers.

#### Invocation Container

The Invocation Container (IC) is the environment/sandbox that runs actor code
within the context of a single invocation. That is, reentrancy or recursion on
the same actor will spin off another IC.

The IC is an instance of a Wasm engine/runtime fulfilling the FVM-side of the
contract. The contract consists of:

1. Syscalls available as importable host-provided functions.
2. Shared types to represent data across the FVM boundary.
3. Actor-owned memory to exchange data in syscalls.
4. Transparent gas accounting and automatic execution halting.
5. (Future) Dynamic linkage of popular Wasm modules "blessed" by the community
   through some governance process, in order to reduce actor bytecode size (e.g.
   FVM SDKs, IPLD codecs, etc).

Because this contract may change over time, user-deployed actors may specify an
IC version at [`InitActor#InstallActor` time](#actor-deployment). The strategy
for deprecating IC versions over time has not been yet determined.

#### Syscalls

Syscalls are functions made available to the actor as Wasm imports, allowing it
to interact with the outer environment, and to call complex operations that are
more performant to implement in native land (e.g. cryptographic primitives).

#### Kernel

The Kernel is an object created by the Call Manager and injected into the
Invocation Container. It processes syscalls, and stores invocation-scoped state.

#### Externs

Similar to syscalls being functions provided to the actor by the FVM, Externs
are functions provided by the node to the FVM. They are a logical layer that may
or may not have a physical impact, depending on the programming languages at
play. If the FVM and node languages differ, it's possible that the Externs layer
translates aligns with an FFI boundary.

### Actors

Actors are equivalent to smart contracts in other networks: they are pieces of
logic that live on-chain and can be triggered via messages.

#### Actor types

We distinguish three types of actors:

1. Built-in actors.
2. Native actors.
3. Foreign actors.

![Actor execution](./fip-introducing_fvm/overview.png)

##### Built-in actors

Built-in actors are protocol-defined actors whose Wasm bytecode ships with the
Filecoin client. The recommended approach is to embed a CAR bundle with all the
relevant bytecode, and seeding the blockstore with it on node start.

**Canonical codebase**

With the definition of a universal, portable execution bytecode format, all
Filecoin clients can rely on a single codebase for built-in actors. This speeds
up protocol development, shortens protocol upgrade timelines, and reduces
coordination overhead.

This FIP proposes to promote the [FVM built-in actors] codebase to the status of
**_canonical_ built-in actors**. These actors were forked from the Forest
client, and they currently live in the [filecoin-project/ref-fvm] repo. There
are plans to extract them to a standalone repo.

This decision would have a few practical implications:

1. The canonical actors would become a common-good codebase for the Filecoin
   network, with all implementors collaborating around it.
2. Implementations would embed the canonical Wasm bytecode into their
   binaries. The concrete mechanismsm are implementation-dependent.
3. Network upgrades would agree on the exact CodeCIDs of built-in actors to
   enable at a fork.

##### Native actors

Native actors are user-defined actors targeting the native FVM runtime.

Users can _technically_ write native actors in any programming that compiles to
Wasm. However, language-specific overheads (e.g. runtime, garbage collection,
stdlibs, etc.) may lead to oversized Wasm bytecode and execution overheads,
translating to higher gas costs.

Furthermore, there will likely be hard limits enforced on the sizing of bytecode
deployables before user deployable actors are allowed.

There's a [reference SDK] written in Rust to accompany this FIP. As of today, it
is used by the canonical built-in actors.

We find that Rust is a reasonable choice to writing native actors due to the
lack of a runtime, the ability to elide the stdlib through `no_std`, and its
mature Wasm support.

Exploration of other languages is something we encourage the community to
pursue. Concretely, we believe that AssemblyScript, Swift, Kotlin, and TinyGo
SDK are worth exploring.

##### Foreign actors

Foreign actors are smart contracts or programs targeting non-FVM runtimes,
running inside the Filecoin network through emulation.

The ability to run foreign actors is vital for cross-chain interoperability, and
to enable other chains to access Filecoin storage capabilities more seamlessly.

The first kind of foreign actor we aim to support is **Ethereum smart
contract**, through the deployment of low-level EVM bytecode. This allows for
straightforward and relatively risk-free porting of existing battle-tested
Ethereum smart contracts to the Filecoin network.

Every foreign runtime is in turn an actor type, identified by a `CodeCID`.
Foreign runtimes are installed just like any other actor type. Foreign actors
instances are constructed through the `InitActor`, supplying the source
deployable as a constructor.

In the case of the EVM foreign runtime, we are looking to standardise on either
one of these interpreters:

1. [SputnikVM], or
2. [blueallow/revm] (a fork of the above)

Every foreign runtime will need to specify bindings to map runtime-specific
aspects (e.g. addressing, crypto primitives, gas accounting, etc.) to Filecoin
counterparts. A preliminary [EVM <> FVM binding specification] exists.

Future foreign runtime candidates include Agoric SES, Solana eBPF, and others.
In all cases, compatibility should target the lowest level executable output in
its source form, rather than dealing with high-level languages using
alternative/custom toolchains. This reduces risk surface by increasing execution
fidelity/parity, and makes it tooling reuse possible.

#### Actor bytecode representation

Wasm bytecode payloads will be represented as an IPLD DAG, and will be stored in
the state blockstore, owned by the node implementation.

**The concrete DAG layout, multihash function, and CID codec are yet to be
defined.**

Code will be linked to from the state tree through the existing `code` CID field
in the `ActorState` object:

```rust
pub struct ActorState {
    /// Link to code for the actor.
    pub code: Cid,
    /// Link to the state of the actor.
    pub state: Cid,
    /// Current sequential nonce of the actor.
    pub nonce: u64,
    /// Filecoin tokens available to the actor.
    pub balance: TokenAmount,
}
```

#### Actor deployment

The current `InitActor` (`f00`) will be extended with a (`InstallActor`) method
taking a single input parameter: the actor's Wasm bytecode. As mentioned above,
DAG representation format is to be defined. The actor's Wasm bytecode must
specify the version of the Invocation Container the bytecode requires, inside a
reserved exported global.

The state object of the `InitActor` will be extended with an `ActorRegistry`
HAMT of `CID => ActorSpec`, where `ActorSpec` is:

```rust
/// A simple actor specification/metadata structure, to be extended with
/// additional metadata in the future.
struct ActorSpec {
  /// The version of the invocation container.
  version: int, 
}
```

The logic of `InitActor#LoadActor` is as follows.

1. Validate the Wasm bytecode.
    - Perform syntax validation and structural validation, [as per standard](https://webassembly.github.io/spec/core/valid/index.html).
    - No floating point instructions.
2. Multihash the bytecode and calculate the code CID.
3. Check if the code CID is already registered in the `ActorRegistry`.
4. If yes, charge gas for the above operations and return the existing CID.
5. Insert an entry in the `ActorRegistry`, binding the bytecode CID with the
   actor spec.
6. Return the CID, and charge the cost of the above operations, and potentially
   a price for rent/storage.

At this point, the actor can be instantiated many times through the standard
`InitActor#Exec` method. Parameters provided will be passed through to the
actor's constructor (currently identified by `method_number=1`). This includes
byte streams corresponding to deployables for foreign actors (e.g. EVM
bytecode).

#### Actor message dispatch

With the exception of simple value transfers, messages trigger some actor logic
on the recipient actor. (In the future, value transfers may also trigger
arbitrary logic.)

Today, Filecoin chain messages carry a _method number_. The current VM matches
on recipient actor type and method number to dispatch to the appropriate
handler. This approach is **external method dispatch**.

With the FVM, actors now expose a **single entrypoint** in the form of a
Wasm-exported function, and conduct **internal method dispatch**.

The signature of an actor entrypoint is:

```rust
pub fn invoke(params_block_id: u32) -> u32 { }
```

- The single uint32 argument corresponds to the block ID of the encoded input
  parameters struct, or `0` for none.
- The single uint32 return value corresponds to the block ID of the return data
  struct, or `0` for none.

More information on block IDs can be found in [IPLD memory model](#ipld-memory-model)

This design decouples actors from their runtime, and is more aligned with the
actor model, where actors interact through inboxes. It also awards maximal
degrees of freedom and sophistication to support techniques such as structural
pattern matching, efficient pass-through proxying, interception, and more.

Because internal dispatch logic will rapidly become boilerplate, FVM SDKs should
offer dispatch sugar.

**Backwards compatibility**

The _method number_ field on messages remains unchanged to preserve backwards
compatibility. It may be deprecated and eventually removed later. Built-in
actors continue relying on _method number_, but now perform internal dispatch.

### Syscalls

This section specifies all the syscalls that the IC must make available to the
actor.

Currently, the FVM charges no gas for import linkage. In the future, the FVM may
charge a static or a dynamic cost for linking the concrete functions or
namespaces imported by the module.

**Interface type conventions**

- `off` and `len` in argument names refers to "memory offset" and "buffer
  length". Together, they define the bounds of a slice of memory.
- Syscall arguments prefixed with `o_` represent output parameters.
- The `Result` return type carries a **syscall error number** and the specified
  payload type. The latter only appears when the syscall succeeded (implied by
  error number `0`). These error numbers are ephemeral, and have no meaning
  beyond the FVM syscall boundary. Refer to the [FVM Error Conditions] document
  for more info.

#### Namespace: `actor`

```rust
/// Resolves the ID address of an actor.
pub fn resolve_address(
  addr_off: *const u8,
  addr_len: u32,
) -> Result<ResolveAddress>;

/// Gets the CodeCID of an actor by address.
pub fn get_actor_code_cid(
    addr_off: *const u8,
    addr_len: u32,
    o_cid_off: *mut u8,
    o_cid_len: u32,
) -> Result<i32>;

/// Generates a new actor address for an actor deployed
/// by the calling actor.
pub fn new_actor_address(o_addr_off: *mut u8, o_addr_len: u32) -> Result<u32>;

/// Creates a new actor of the specified type in the state tree, under
/// the provided address.
///
/// NOTE: This syscall with these input parameters is provisional.
/// It is unsafe in an untrusted environment.
pub fn create_actor(actor_id: u64, typ_off: *const u8) -> Result<()>;

#[repr(C)]
pub struct ResolveAddress {
    pub resolved: i32,
    pub value: u64,
}
```

#### Namespace: `crypto`

```rust
/// Verifies that a signature is valid for an address and plaintext.
pub fn verify_signature(
    sig_off: *const u8,
    sig_len: u32,
    addr_off: *const u8,
    addr_len: u32,
    plaintext_off: *const u8,
    plaintext_len: u32,
) -> Result<i32>;

/// Hashes input data using blake2b with 256 bit output.
///
/// The output buffer must be sized to a minimum of 32 bytes.
pub fn hash_blake2b(
    data_off: *const u8,
    data_len: u32,
) -> Result<[u8; 32]>;

/// Computes an unsealed sector CID (CommD) from its constituent piece CIDs
/// (CommPs) and sizes.
///
/// Writes the CID in the provided output buffer, and returns the length of
/// the written CID.
pub fn compute_unsealed_sector_cid(
    proof_type: i64,
    pieces_off: *const u8,
    pieces_len: u32,
    o_cid_off: *mut u8,
    o_cid_len: u32,
) -> Result<u32>;

/// Verifies a sector seal proof.
///
/// It takes the buffer offset and length containing a CBOR-encoded
/// SealVerifyInfo struct, to serve as input. A return payload of 0
/// means verification success; any other value means verification
/// failure.
pub fn verify_seal(info_off: *const u8, info_len: u32) -> Result<i32>;

/// Verifies a window proof of spacetime.
///
/// It takes the buffer offset and length containing a CBOR-encoded
/// WindowPoStVerifyInfo struct, to serve as input. A return payload
/// of 0 means verification success; any other value means verification
/// failure.
pub fn verify_post(info_off: *const u8, info_len: u32) -> Result<i32>;

/// Verifies that two block headers provide proof of a consensus fault.
///
/// A syscall success implies that the logic ran successfully, but it
/// does not imply that a fault was detected. The caller must inspect the
/// return payload. If the fault field equals 0, a consensus fault was
/// recognized at the specified epoch, incurred by the specified actor.
/// Otherwise, no consensus fault was recognized, and the remaining fields
/// must be ignored.
pub fn verify_consensus_fault(
    h1_off: *const u8,
    h1_len: u32,
    h2_off: *const u8,
    h2_len: u32,
    extra_off: *const u8,
    extra_len: u32,
) -> Result<VerifyConsensusFault>;

/// Verifies an aggregated batch of sector seal proofs.
///
/// It takes the buffer offset and length containing a CBOR-encoded
/// AggregateSealVerifyProofAndInfos struct, to serve as input.
/// A return payload of 0 means verification success; any other value
/// means verification failure.
pub fn verify_aggregate_seals(agg_off: *const u8, agg_len: u32) -> Result<i32>;

/// Batch verifies many sector seal proofs within a single syscall.
///
/// It takes the buffer offset and length containing a CBOR-encoded
/// list of SealVerifyInfo structs, to serve as input.
///
/// The return payload is an array of results in the same order as the
/// input sector seal proofs. A value 0 in index i means that proof[i] was
/// verified successfully. Non-zero values denote verification failure.
pub fn batch_verify_seals(batch_off: *const u8, batch_len: u32, o_result_off: *const u8) -> Result<()>;

#[repr(C)]
pub struct VerifyConsensusFault {
    pub fault: u32,
    pub epoch: ChainEpoch,
    pub actor: ActorID,
}
```

#### Namespace: `gas`

```rust
/// Charge the specified amount of gas for the supplied operation name,
/// encoded as an UTF-8 string.
pub fn charge(name_off: *const u8, name_len: u32, amount: u64) -> Result<()>;
```

#### Namespace: `ipld`

```rust
/// Opens a block from the "reachable" set, returning an ID for the block, its codec, and its
/// size in bytes.
///
/// - The reachable set is initialized to the root.
/// - The reachable set is extended to include the direct children of loaded blocks until the
///   end of the invocation.
pub fn open(cid: *const u8) -> Result<IpldOpen>;

/// Creates a new block, returning the block's ID. The block's children must be in the reachable
/// set. The new block isn't added to the reachable set until the CID is computed.
pub fn create(codec: u64, data: *const u8, len: u32) -> Result<u32>;

/// Reads the identified block into o_buf, starting at offset, reading _at most_ len bytes.
/// Returns the number of bytes read.
pub fn read(id: u32, offset: u32, o_buf_off: *mut u8, o_buf_len: u32) -> Result<u32>;

/// Returns the codec and size of the specified block.
pub fn stat(id: u32) -> Result<IpldStat>;

/// Computes the given block's CID, returning the actual size of the CID.
///
/// If the CID is longer than cid_max_len, no data is written and the actual size is returned.
///
/// The returned CID is added to the reachable set.
pub fn cid(
    id: u32,
    hash_fun: u64,
    hash_len: u32,
    o_cid_off: *mut u8,
    o_cid_len: u32,
) -> Result<u32>;

#[repr(C)]
pub struct IpldOpen {
    pub id: u32,
    pub codec: u64,
    pub size: u32,
}

#[repr(C)]
pub struct IpldStat {
    pub codec: u64,
    pub size: u32,
}
```

#### Namespace: `message`

```rust
/// Returns the caller's actor ID.
pub fn caller() -> Result<u64>;

/// Returns the receiver's actor ID (i.e. ourselves).
pub fn receiver() -> Result<u64>;

/// Returns the method number from the message.
pub fn method_number() -> Result<u64>;

/// Returns the value that was received, as little-Endian
/// tuple of u64 values to be concatenated in a u128.
pub fn value_received() -> Result<TokenAmount>;
```

#### Namespace: `network`

```rust
/// Gets the current epoch.
pub fn curr_epoch() -> Result<u64>;

/// Gets the network version.
pub fn version() -> Result<u32>;

/// Gets the base fee for the epoch as little-Endian
/// tuple of u64 values to be concatenated in a u128.
pub fn base_fee() -> Result<TokenAmount>;

/// Gets the circulating supply as little-Endian
/// tuple of u64 values to be concatenated in a u128.
/// Note that how this value is calculated is expected to change in nv15
pub fn total_fil_circ_supply() -> Result<TokenAmount>;
```

#### Namespace: `rand`

```rust
/// Gets 32 bytes of randomness from the ticket chain.
/// The supplied output buffer must have at least 32 bytes of capacity.
/// If this syscall succeeds, exactly 32 bytes will be written starting at the
/// supplied offset.
pub fn get_chain_randomness(
    dst: i64,
    round: i64,
    o_entropy_off: *const u8,
    o_entropy_len: u32,
) -> Result<[u8; 32]>;

/// Gets 32 bytes of randomness from the beacon system (currently Drand).
/// The supplied output buffer must have at least 32 bytes of capacity.
/// If this syscall succeeds, exactly 32 bytes will be written starting at the
/// supplied offset.
pub fn get_beacon_randomness(
    dst: i64,
    round: i64,
    o_entropy_off: *const u8,
    o_entropy_len: u32,
) -> Result<[u8; 32]>;
```

#### Namespace: `send`

```rust
/// Sends a message to another actor, and returns the exit code and block ID of the return
/// result.
pub fn send(
    recipient_off: *const u8,
    recipient_len: u32,
    method: u64,
    params: u32,
    value_hi: u64,
    value_lo: u64,
) -> Result<Send>;

#[repr(C)]
pub struct Send {
    pub exit_code: u32,
    pub return_id: BlockId,
}
```

#### Namespace: `self`

```rust
/// Gets the current state root for the calling actor.
///
/// If the CID doesn't fit in the specified maximum length (and/or the length is 0), this
/// function returns the required size and does not update the cid buffer.
pub fn root(o_cid_off: *mut u8, o_cid_len: u32) -> Result<u32>;

/// Sets the root CID for the calling actor. The new root must be in the reachable set.
pub fn set_root(cid: *const u8) -> Result<()>;

/// Gets the current balance for the calling actor.
pub fn current_balance() -> Result<TokenAmount>;

/// Destroys the calling actor, sending its current balance
/// to the supplied address, which cannot be itself.
pub fn self_destruct(addr_off: *const u8, addr_len: u32) -> Result<()>;
```

#### Namespace: `vm`

```rust
/// Abort execution with the given code and message. The code is recorded in the receipt, the
/// message is for debugging only.
pub fn abort(code: u32, message: *const u8, message_len: u32) -> !;
```

### Externs

```rust
/// Consensus related methods.
pub trait Consensus {
    /// Verify a consensus fault.
    fn verify_consensus_fault(
        &self,
        h1: &[u8],
        h2: &[u8],
        extra: &[u8],
    ) -> Result<Option<ConsensusFault>>;
}

/// Randomness provider trait
pub trait Rand {
    /// Gets 32 bytes of randomness for ChainRand paramaterized by the DomainSeparationTag,
    /// ChainEpoch, Entropy from the ticket chain.
    fn get_chain_randomness(
        &self,
        pers: DomainSeparationTag,
        round: ChainEpoch,
        entropy: &[u8],
    ) -> Result<[u8; 32]>;

    /// Gets 32 bytes of randomness for ChainRand paramaterized by the DomainSeparationTag,
    /// ChainEpoch, Entropy from the latest beacon entry.
    fn get_beacon_randomness(
        &self,
        pers: DomainSeparationTag,
        round: ChainEpoch,
        entropy: &[u8],
    ) -> Result<[u8; 32]>;
}

```

### IPLD memory model

IPLD is the data model of Filecoin. Actors can be construed as logic that
receives an input IPLD graph, performs computation, and returns a new IPLD graph
(which is persisted by saving the root CID of the new graph in the actor's
state).

All state is stored and retrieved as IPLD. The state store lives on the node
side, and it is exposed to the FVM via an Extern. This is important as the VM
itself needs to understand the IPLD so we can do garbage collection, etc.

The FVM must guarantee that actors can only access data that is in their state
tree. This is done through the maintenance of an "accessible set" inside the
kernel.

Because Filecoin IPLD state objects are highly atomized and linked, accessing
and mutating entries in objects like HAMTs and AMT results in multiple
sequential state IO operations, each of which traverses the Extern boundary in a
non-parallelizable way. If the Extern is traversed through FFI, the cost of
operating on ADLs may be non-negligible.

**Block handles**

IPLD blocks are dynamically-sized blobs of data. When loading a block by CID,
the size is unknown, so the actor cannot allocate memory upfront. Moreover,
host-side memory is inaccessible to Wasm code, so it's not possible for the
Kernel to return a pointer to host-side memory for Wasm code to read.

For this reason, the low-level IPLD syscall API revolves around the concept of
"block handles". Block handles are references to blocks, inspired by Unix file
descriptors, and identified by a block ID (`u32`).

Parameters to actors and return data returned from actor calls are modelled as
IPLD blocks too. But since they are not referenced from state or elsewhere, they
aren't referenced by CID but merely by block IDs when invoking the Wasm actor
entrypoint (see [Actor message dispatch](#actor-message-dispatch)).

**Syscall mechanics**

- When accessing a block by CID through `ipld::open`, the Kernel returns a block
  ID, the size, and the codec.
- To read the block data, `ipld::read` takes a block ID and a pointer to a
  Wasm-side buffer.
- To write a block, `ipld::create` takes a buffer and a codec, and returns a
  block ID.
- If the Wasm actor needs to compute the CID for a block, it calls the
  `ipld::cid` syscall passing in the block ID.
- An `ipld::stat` syscall is available to enquire the size and codec of the
  block by ID. This is useful to allocate a buffer for call parameters.

### Module caching

Wasm execution performance is a determining factor in the ability to maintain
blockchain epoch time (30 seconds).

We recommend implementations to compile Wasm bytecode into machine code for
faster execution, instead of relying on interpretation. This incurs in an
upfront CPU-bound compilation cost, in exchange for ongoing operating costs.

Actively or passively-managed module caches could be explored, but such
approaches may introduce vulnerabilities. Instead, we may factor in the
compilation compute cost and the perpetual storage cost, as deployment-time gas.

Any approach will need to account for eventual recompilation costs on events
like Wasm Engine or compiler upgrades.

### Gas charging

The current gas model relies on actor code being static and known ahead of time.
Gas is currently charged at the syscall level and not at the instruction level.

With the ability to run arbitrary code on the network, the gas model must
account for actual execution costs at the instruction level, in addition to
syscall-level charges.

A gas remodelling proposal will follow this FIP.

### Specific actor coupling

Due to how certain parts of the Filecoin protocol work, implicit coupling that
exists between the VM and specific actor types will be carried over. Concretely:

- Account actor: the FVM must create new account actors when processing sends to
  pubkey addresses.
- Init actor: the FVM must load and query the init actor state when resolving
  addresses during message processing, and when the `actor::resolve_address` syscall is
  called. Additionally, a new init actor entry must be added when implicitly
  creating an account, as per above.
- Power actor and Storage Market actor: state is queried when handling the
  `network::total_fil_circ_supply` syscall.
- Burnt funds account and Reserve account: balances are queried when handling
  the `network::total_fil_circ_supply` syscall.

## Design Rationale

Concerning the choice of runtime, various technologies were evaluated, including
EVM, JavaScript/SES, LLVM IR, etc. Wasm was chosen for these reasons:

- It has a strong and promising future in the blockchain space; with room for
  cross-chain collaborations and interest groups
- It has a growing ecosystem of tooling and solutions (e.g. runtimes, package
  managers, language shims)
- It is portable across architectures and operating systems
- has deterministic execution as long as
  [non-deterministic](https://github.com/WebAssembly/design/blob/main/Nondeterminism.md)
  features aren't used (of which we use none)
- It is usually compiled to machine code, but it can also be interpreted
- Bytecode specifies actual execution as opposed to high-level constructions or
  intermediate representations; this makes it suitable for stable
  content-addressing
- It is sandboxed and secure
- Allows for a choice of programming language

## Backwards Compatibility

Existing built-in actor and system functionality will not be affected by the
introduction of the Filecoin Virtual Machine.

## Test Cases

FVM implementations can subject themselves to the FVM-specific test vectors
hosted at: https://github.com/filecoin-project/fvm-test-vectors.

## Security Considerations

This specification entails a complete rearchitecture of the execution layer of
the Filecoin blockchain, and the transition to adopting a new actors codebase.
Such low-level and deep changes comes with non-negligible risks, the extent of
which will be analyzed as network upgrades with concrete scopes are proposed.

## Incentive Considerations

This specification FIP does not affect incentives in itself. However, the
ability to deploy arbitrary on-chain programs may impact chain utilization, gas
expenditures and burn, and the flow of tokens as a result of the use cases that
developers deploy on top of the FVM.

## Product Considerations

> TBD.

## Implementation

A reference implementation of the FVM is provided in the
[filecoin-project/ref-fvm] repository.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).

> Links need tidying up.

[reference SDK]: https://github.com/filecoin-project/ref-fvm/tree/master/sdk
[SputnikVM]: https://github.com/rust-blockchain/evm
[blueallow/revm]: https://github.com/bluealloy/revm
[WebAssembly (Wasm)]: https://webassembly.org/
[multi-value support]: https://github.com/WebAssembly/spec/blob/master/proposals/multi-value/Overview.md
[SIMD instructions]: https://github.com/WebAssembly/simd/blob/master/proposals/simd/SIMD.md
[threads]: https://github.com/WebAssembly/threads
[Nondeterminism]: https://github.com/WebAssembly/design/blob/main/Nondeterminism.md
[actor model]: https://en.wikipedia.org/wiki/Actor_model
[EVM <> FVM binding specification]: https://github.com/filecoin-project/fvm-project/blob/main/04-evm-mapping.md
[FVM Error Conditions]: https://github.com/filecoin-project/fvm-specs/blob/main/07-errors.md
[filecoin-project/ref-fvm]: https://github.com/filecoin-project/ref-fvm
[specs-actors]: https://github.com/filecoin-project/specs-actors
[existing non-programmable VM]: https://spec.filecoin.io/intro/filecoin_vm/
[FVM built-in actors]: https://github.com/filecoin-project/ref-fvm/tree/master/actors
[memory64]: https://github.com/WebAssembly/memory64/blob/main/proposals/memory64/Overview.md