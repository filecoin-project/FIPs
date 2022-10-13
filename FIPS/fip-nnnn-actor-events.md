---
fip: <to be assigned>
title: Actor events
author: Raúl Kripalani (@raulk), Steven Allen (@stebalien)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/484
status: Draft
type: Technical Core
category: Core
created: 2022-10-12
spec-sections: 
  - https://spec.filecoin.io/#section-systems.filecoin_vm.runtime.receipts
requires: N/A
replaces: N/A
---

## Simple Summary

This FIP adds the ability for actors to emit externally observable events during
execution. Events are fire-and-forget, and can be thought of as a side effect
from execution. The payloads of events are self-describing objects signalling
that some important circumstance, action or transition has ocurred. Actor events
enable external agents to observe the activity on chain, and may eventually
become the source of internal message triggers.

## Abstract

This FIP introduces a _minimal_ design for actor events, including their schema,
a new syscall, a new field in the `MessageReceipt` structure, and mechanics to
commit these execution side effects on the chain. By _minimal_ we mean that the
protocol stays largely unopinionated and unprescriptive around higher level
concerns like event indexing, traversal, and proofs (e.g. inclusion proofs for
light clients), and other future higher-level features.

## Change Motivation

Two main motivations warrant the introduction of actor events at this time.

1. They have been long missing from the protocol, complicating observability and
   forcing Filecoin network monitoring or accounting tools resort to creative
   approaches to obtain the data they needed, e.g. forking and instrumenting
   built-in actors code, or replaying messages and performing state tree diffs.
   
   While this may have been tolerable for a limited number of actors, it will no
   longer scale for a world of user-defined actors.
   
   A future FIP could enhance built-in actors to emit events when power changes,
   sectors are onboarded, deals are made, sectors are terminated, penalties are
   incurred, etc.

2. The upcoming introduction of the Filecoin EVM runtime necessitates an event
   mechanism at the protocol layer to handle the LOG{0..4} opcodes, and the
   corresponding Ethereum JSON-RPC methods.

## Specification

### New chain types

We introduce a DAG-CBOR encoded `Event` type to represent an actor event.

```rust
/// Represents an event emitted throughout message execution.
struct Event {
    /// Carries the ID of the actor that emitted this event.
    emitter: ActorID,
    /// Key values making up this event.
    entries: Vec<Entry>,
}

struct Entry {
    /// A bitmap conveying metadata or hints about this entry.
    flags: u8,
    /// The key of this event.
    key: String,
    /// Any DAG-CBOR encodeable type.
    value: any,
}
```

Its main constituent is a list of ordered key-value **entries**. This approach
is inspired by structured logging concepts. **Keys** are strings, while
**values** can be any DAG-CBOR encodeable type.

Every **entry** contains a single-byte **flags** bitmap, which conveys metadata
or hints about the entry. These are the currently supported flags:

| hex    | binary      | meaning |
|--------|-------------|---------|
| `0x01` | `b00000001` | indexed |

Flag `0x80` is currently only used as a client hint. In the future, this flag
and others may lead to consensus-relevant outcomes, such as populating
(adaptable) bloom filters, committing block-level indices, supporting on-chain
event subscriptions, and more.

Future flags may include:
- specialized indexing strategies
- bloom inclusion
- special type indicators (e.g. "this is an address")

> TODO: make flags a varint for extensibility? Can also retype later, if we
> overflow.

Choosing a _list of tuples_ instead of a map representation is deliberate, as it
enables repeatable keys, and, thus, array-like entries, e.g. signers in a
multisig transaction.

Over time, we expect the community to standardise on a set of keys through FRC
proposals.

> TODO:
> - Define maximum lengths for entries, key size, value size?
> - Do we want to introduce standard keys now, e.g. type?

**Event examples**

The following examples demonstrate how to use these structures in practice.

_Fungible token transfer_

```rust
Event {
    emitter: 1260,
    entries: [ // type, sender, receiver indexed
        (0x01, "type", "transfer"),
        (0x01, "sender", <id address>),
        (0x01, "receiver", <id address>),
        (0x00, "amount", <token amount>),
    ],
}
```

_Non-fungible token transfer_

```rust
Event {
    emitter: 101,
    entries: [  // all entries indexed
        (0x01, "type", "transfer"),
        (0x01, "sender", <id address>),
        (0x01, "receiver", <id address>),
        (0x01, "token_id", <identifier>),
    ],
}
```

_Multisig approval_

```rust
Event {
    emitter: 1678,
    entries: [  // type and signers indexed
        (0x01, "type", "approval"),
        (0x01, "signer", <id address>),
        (0x01, "signer", <id address>),
        (0x01, "signer", <id address>),
        (0x00, "callee", <id address>),
        (0x00, "amount", <token amount>),
        (0x00, "msg_cid", <message cid>),
    ],
}
```

### Chain commitment

The existing `MessageReceipt` chain data structure is augmented with a new
`events` field:

```rust
struct MessageReceipt {
    exit_code: ExitCode,
    return_data: RawBytes,
    gas_used: i64,
    events: Cid, // new field; root of AMT<Event>
}
```

During message execution, DAG-CBOR encoded `Event`s are accumulated inside the
FVM inside an AMT, preserving the order. At the end of message execution, the
AMT is flushed into the FVM's (buffered) blockstore, and the root CID of the AMT
is returned in the above `events` field.

Because the network agrees on the content of the receipts through the
`ParentMessageReceipts` on the `BlockHeader`, the events are implicitly
committed to the chain state with no futher structural changes needed.

### Client handling

Honouring indexing hints is optional but highly encouraged at this stage.
Clients may offer new JSON-RPC operations to subscribe to and query events.

Clients may prefer to store and track event data in a dedicated store,
segregated from the chain store, potentially backed by a different database
engine more suited to the expected write, query, and indexing patterns for this
data.

Note that there's a timing difference between the moment the client receives the
events AMT root CID (after message execution), and the moment that the event
data (IPLD blocks) is effectively made available in the client's blockstore (at
Machine flush time). Consequently, events cannot be viewed/logged/inspected
until the Machine is flushed.

FVM implementations may accept a separate events store, and offer an "early
events flush" Machine option to instruct the FVM to flush events on every
message execution.

### New `vm::emit_event` syscall

We define a new syscall under the `vm` namespace so that actors can emit events.

```rust
/// Emits a block as an actor event. It takes the block ID of a block created via
/// ipld::block_create. The block must be a DAG-CBOR encoded Vec<Entry>.
/// 
/// The FVM will validate the structural, syntatic, and semantic correctness of the
/// supplied payload, and will error with `IllegalArgument` if the payload was invalid.
///
/// Calling this syscall may immediately halt execution with an out of gas error, if
/// such condition arises.
fn emit_event(entries_id: u32) -> Result<()>;
```

This syscall will create an `Event` object, stamp it with the current ActorID,
and store it in the events accumulator.

We expect FVM SDKs to offer utilities, macros, and sugar to ergonomically
construct event payloads and handle the IPLD block creation task.

**Gas costs**

In addition to the [syscall gas cost], emitting an event carries the following
dynamic costs:

- Per non-indexed entry: <<TODO>> gas per <<TODO>>.
- Per indexed entry: <<TODO>> gas per <<TODO>>.

> TODO need to make syscall gas dynamic based on param length

The following limits apply. Exceeding these limits will result in the event not
being emitted, and the call failing with `IllegalArgument`:

> - Total event payload size: <<TODO, if any; may be bound by gas, once syscall
>   gas varies based on param length?>>
> - Maximum number of keys: <<TODO, if any; may be bound by gas>>
> - Maximum number of indexed keys: <<TODO, if any; may be bound by gas>>

### Mapping to EVM logs

> This is defined here for convenience, and will be moved to the upcoming
> Filecoin EVM FIP once submitted.

Logs in the Ethereum Virtual Machine are emitted through `LOG{0..4}` opcodes.
Each variant takes the specified number of topics (indexed). All variants take a
single memory slice referring to the data (non indexed).

We define `LOG{0..4}` opcodes to emit events conforming to the following
template:

```rust
Event {
    emitter: <actor id>,
    entries: [
        (0x01, "topic1", <first topic word>),   // when LOG1, LOG2, LOG3, LOG4
        (0x01, "topic2", <second topic word>),  // when LOG2, LOG3, LOG4
        (0x01, "topic3", <third topic word>),   // when LOG3, LOG4
        (0x01, "topic4", <fourth topic word>),  // when LOG4
        (0x00, "data", <data>),
    ],
}
```

## Design Rationale

A large part of the architectural discussion has been documented in issue
[filecoin-project/ref-fvm#728]. Some ideas we considered along the way included:

- Keeping events away from the protocol and in actor land, by tracking them in
  an Events actor.
- Populating event indices and committing them on the block header.
- Adaptable bloom filters, advertised on the block header.
- Wrapping events in a broader concept of "execution artifacts", which in the
  future could be extended to include callbacks, futures, and more.

We shelved these ideas and kept this initial proposal simple, yet extensible,
focusing only on the fundamentals. A particular area to conduct further research
into is Filecoin light clients and the kinds of proofs that could endorse
queries for events, including inclusion, non-inclusion, and completeness proofs.

In terms of the technical design, we considered making the event payload an
opaque IPLD blob accompanied by some form of a type discriminator. However, that
would require an IDL upfront to interpret the payload. We posit that the
unwrapped data model we've proposed enables straightforward introspection and
comprehension by chain explorers, developer tools, and monitoring tools.

Concerning the concept of `flags`, we had initially considered a top-level
`indexed` bitmap, but later generalised it to a `flags` field for extensibility.
We consider the consequent size tradeoff to be acceptable.

## Backwards Compatibility

We are adding a new field to the `MessageReceipt` type. While this type is not
serialized over the wire nor gossiped, it is returned from JSON-RPC calls.
Hence, users of Filecoin clients may notice a new field, which could in turn
break some of their code.

## Test Cases

TODO.

## Security Considerations

TODO.

## Incentive Considerations

N/A.

## Product Considerations

TODO.

## Implementation

TODO.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).


[`MessageReceipt` type]: https://spec.filecoin.io/#section-systems.filecoin_vm.message.message-semantic-validation
[syscall gas cost]: https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0032.md#syscall-gas
[filecoin-project/ref-fvm#728]: https://github.com/filecoin-project/ref-fvm/issues/728
