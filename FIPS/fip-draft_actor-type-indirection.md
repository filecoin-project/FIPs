---
fip: "<to be assigned>"
title: Actor Type Indirection in the State Tree
author: "Rod Vagg (@rvagg)"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1090
status: Draft
type: Technical
category: Core
created: 2026-11-09
spec-sections:
---

# FIP-XXXX: Actor Type Indirection in the State Tree

## Simple Summary

Every actor in the state tree records the CID of its WASM code. Nearly every network upgrade ships new WASM, so nearly every upgrade rewrites all 3.85 million mainnet actors, even when only one actor's logic changed. This FIP has each actor record its type name (`storageminer`, `evm`, `account`, ...) instead, with a single name-to-code mapping hanging off the state root. A code-only upgrade then writes that mapping and leaves the actors tree alone.

## Abstract

In state tree version 5 an actor is `[Code, Head, Nonce, Balance, DelegatedAddress]`, where `Code` is the CID of a WASM module in the builtin actors bundle. Builtin code CIDs change at almost every upgrade, so the state migration replaces `Code` in every actor and rebuilds the actors HAMT. On mainnet at nv29 that meant 557,835 HAMT nodes and 445.7 MB of new blocks to change the state of three actors.

State tree version 6 makes the actor `[Type, Head, Nonce, Balance, DelegatedAddress]`, where `Type` is the actor's manifest name. The state root's third field, an empty placeholder since state tree version 1, links an `ActorTypes` block holding the actors version and the bundle manifest. An actor's code CID is the manifest entry for its type, in the state it is read from. The system actor's copy of the manifest is removed. Actor methods, gas and the exit codes messages can reach are unchanged, and nodes keep presenting a resolved code CID on their public APIs.

The existing type names become permanent consensus identifiers. The dormant plans for user-deployed WASM actors and per-actor code upgrades, which depend on each actor having its own code CID, are implicitly retired.

## Change Motivation

### Every upgrade rewrites every actor

Before the FVM, `Code` was an identity CID wrapping a string such as `fil/7/storageminer`. It changed only with the actors ABI version, and several upgrades between nv2 and nv11 changed actor logic without touching it. [FIP-0031](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0031.md) replaced these with content-addressed WASM CIDs while acknowledging the cost: _"any and every change in actor logic will result in different bytecode. In practice this implies that state tree migrations will be more frequent."_ That was a reasonable price while user-deployed WASM actors, each having its own code, were on the roadmap.

Since nv16 every mainnet upgrade except nv20 and nv26 has run a full actors migration, most of them changing every actor's code CID and very few actors' state. Measured on mainnet at the nv28 and nv29 boundaries:

| | nv28 | nv29 |
|---|---:|---:|
| Actors in tree | 3,784,309 | 3,849,060 |
| Actors whose state (not just code) changed | 1 (system: the manifest swap) | 3 (system: the manifest swap; reward; market) |
| HAMT nodes rewritten | 544,217 (100%) | 557,835 (100%) |
| New HAMT blocks written | 438.3 MB | 445.7 MB |
| HAMT nodes written under this FIP | 0 | at most 12 (22.5 KB) |

Under this FIP upgrades leave the system actor alone, so the remaining writes are the `ActorTypes` block, the state root, and the new state and HAMT paths of actors whose state was required to change during that network upgrade.

Of the 18 expensive mainnet migrations since actors v2, 9 wrote only a handful of specific actors (nv22 after reading every miner) and would have skipped the rewrite under this FIP. In the FVM era it is 7 of 12, including 4 of the last 5. The rest rewrote every miner actor or changed the state tree or actor encoding, which costs a large share of the tree regardless.

### What the rewrite costs

On a well-provisioned mainnet Lotus node, nv29's pre-migration took 91.7 s (82 s of it walking the old tree, nearly all cold reads) and the epoch migration 30.5 s, during which the node can't validate the next tipset. Other operators' epoch migrations took 51 to 54 s. An operator benchmark in [lotus#12432](https://github.com/filecoin-project/lotus/issues/12432) reports about 64 s per phase on NVMe with about 6 GiB of daemon memory growth, and over two minutes on ZFS; those runs reuse the previous code CIDs and don't write new blocks, so they understate production cost. Nodes that miss or restart during the pre-migration window do all of it at the epoch. At nv29, blocks arrived 24 to 159 s late and there was a null round while nodes worked through it.

The cost grows with the actor count, and the actor count grows mostly from accounts and Ethereum accounts, which upgrades rarely touch.

Every upgrade also adds a full copy of the actors HAMT to archival nodes (445.7 MB at nv29, equivalent to around 12 hours of ordinary actors HAMT churn) and to any snapshot spanning the boundary. Indexers that diff state see around 3.78 million changed actors at the upgrade, against 34 to 55 in an ordinary epoch.

The cost also leaks into the RPC, as an Ethereum incompatibility. Lotus marks these upgrades expensive and refuses explicit calls (`eth_call`, `eth_estimateGas`, `StateCall`, gas estimation) that would have to run the migration on demand: `eth_call` pinned to an upgrade epoch returns EIP-1474 error -32002, "resource unavailable", and `StateCall` quietly executes against the parent tipset instead. Ethereum clients have no equivalent gap. At nv28, a code-only upgrade, the refusal stalled subgraph indexers such as The Graph and Goldsky ([lotus#13642](https://github.com/filecoin-project/lotus/issues/13642)). An upgrade that only writes `ActorTypes` and a handful of actors needn't be marked expensive, so calls at its epoch behave as at any other.

### Why not just make the migration faster?

Migrations can be made much faster without a protocol change, and some of that is worth doing anyway (see Faster migrations instead, under Design Rationale). But a faster rewrite still reads and writes the whole tree, still adds 445 MB of state per upgrade, and still marks every actor changed. Avoiding the epoch work by carrying pre-migration results forward adds path-dependent consensus risk. Removing the reason for the rewrite is simpler.

## Specification

### State root

State tree version 6 keeps the version 5 state root shape:

```
StateRoot = [Version: 6, Actors: Link, ActorTypes: Link]
```

`Actors` links the actors HAMT, unchanged in structure and parameters from version 5. `ActorTypes` takes the place of version 5's `Info`, which links an empty CBOR array.

### ActorTypes

```
ActorTypes = [ActorsVersion: uint, Manifest: Link]
```

- `Manifest` links the root block of the builtin actors bundle manifest, `[ManifestVersion: uint, Data: Link]`, where `Data` links `[[Name: string, Code: Link], ...]`. These are blocks the bundle already contains, and the root CID is the one that nodes already use to identify bundles by. `ManifestVersion` must be 1; any other value makes the state invalid, and a new manifest version needs a FIP.
- Names within a manifest are unique, and so are code CIDs. A manifest must include `system`, `init`, `account`, `placeholder`, `eam` and `ethaccount`, which the FVM requires.
- `ActorsVersion` is the major version of the builtin actors bundle (e.g. 20), fixed for each network upgrade. The FVM doesn't read it; state readers use it to choose decoders instead of inferring the version from code CIDs. Every migration that performs a bundle install also writes a new `ActorTypes`, even when the manifest is identical to the previous version's.

All CIDs are DAG-CBOR links (tag 42), so the bundle's WASM modules stay reachable from the state root and garbage collecting DAG walks (e.g. Lotus' Splitstore) will include them.

### Actor

```
Actor = [Type: string, Head: Link, Nonce: uint, Balance: bytes, DelegatedAddress: bytes | null]
```

Fields other than `Type` are as in version 5. `Type` is a definite-length CBOR text string (major type 3), byte-equal to the `Name` of the actor's manifest entry. Any other CBOR type in that position makes the actor invalid.

### Resolving code

An actor's code CID is the `Code` of the manifest entry keyed by its `Type`, and the manifest is linked from the `ActorTypes` of the state root it is read from. A migration must not produce an actor whose `Type` is missing from the manifest, and loading such an actor is a fatal state error.

The FVM loads the manifest from `ActorTypes` when it is constructed on a state root, where today it loads it from the system actor. Behaviour visible to actors:

- `get_actor_code_cid` returns the resolved code CID.
- `get_builtin_actor_type` and `get_code_cid_for_type` behave as today, against the manifest from `ActorTypes`.
- `create_actor` records the name of the manifest entry matching the given code CID. A code CID with no entry fails with the `IllegalArgument` syscall error, checked after the existing placeholder check and before the actor lookup. Only the init actor can call `create_actor` and it creates only builtin types, so no message reaches this failure on a Filecoin network.
- Promotion of a placeholder actor, to `ethaccount` by the executor or to another type through `create_actor`, writes the new type name.

Gas accounting is unchanged. Actor reads and writes are charged flat amounts regardless of encoded size, and the manifest is loaded once per machine, as today.

### System actor

The system actor's `builtin_actors` field is removed and its state becomes the empty tuple `[]`. Only the system actor's constructor writes the field and the actor never reads it; the FVM and node implementations read it to find the current manifest, which `ActorTypes` now provides.

### Migration

At the activation epoch the state migration:

1. Rewrites every actor from the version 5 encoding to version 6, setting `Type` to the name of the manifest entry whose code CID matches the actor's `Code` in the pre-activation manifest.
2. Applies any other actor state changes scheduled for the same upgrade.
3. Sets the system actor's state to `[]`.
4. Writes `ActorTypes` for the activation bundle and a version 6 state root.

The conversion rewrites the whole actors tree, as a normal upgrade does today. It also shrinks the tree: the 43-byte `Code` becomes a name of around 10 bytes, taking the nv29 actors HAMT from 445.7 MB to 317.6 MB.

After activation, an upgrade writes a new `ActorTypes` and rewrites only the actors whose state changes. Actors of a type removed from the bundle must be deleted or converted in the same migration, as [FIP-0121](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0121.md) does for `verifiedregistry` and `datacap`.

### Genesis

A genesis state at or after the activation network version is a version 6 state: its state root links an `ActorTypes` for the genesis bundle, the system actor's state is `[]`, and every actor's `Type` is its manifest key.

### Type names

From activation, type names are permanent consensus identifiers:

- The names in use are those of the bundle manifest at activation, recorded in [the actor type registry](https://github.com/filecoin-project/FIPs/blob/master/resources/fip-draft_actor-type-indirection/actor-types.md).
- A new type needs a FIP, which adds the name to the registry and to the manifest of the bundle that introduces it. A FIP that retires a type marks it retired in the registry.
- Names are lowercase ASCII letters and digits, at most 16 bytes (shorter is better).
- A name is never renamed or reused from the registry, even when removed from the state tree (such as in the FIP-0121 example above).

### Retired features

These ref-fvm features exist for actors that have their own code, and have never been enabled on a Filecoin network. This FIP retires them:

- User-deployed WASM actors: the `install_actor` syscall, the init actor's `installed_actors` list and the `m2-native` feature.
- Per-actor code upgrades: the `upgrade_actor` syscall and `upgrade-actor` feature (draft FIP-0088, [FIPs#873](https://github.com/filecoin-project/FIPs/pull/873), closed unmerged in 2024).

Retired means that no Filecoin network enables them; under state tree version 6 they could not work as designed, since `create_actor` rejects code with no manifest entry. To avoid breaking API changes, implementations may deprecate them or leave them disabled until their next major release, rather than remove them immediately (i.e. to avoid a ref-fvm v5).

User-defined actors on Filecoin are EVM actors, which share the `evm` type and keep their bytecode in actor state.

## Design Rationale

### Back to type identifiers

Identity CIDs like `fil/7/storageminer` were, in practice, type-and-ABI identifiers. Raúl Kripalani described them in [ref-fvm#756](https://github.com/filecoin-project/ref-fvm/issues/756) (2021) as "a routing/dispatch table" that "does not strictly represent the actual code to run". So this FIP is closer to pre-FVM semantics than it looks. FIP-0031 moved to content-addressed code as "an important preparatory step in the trajectory towards full on-chain user-programmability", and per-actor code CIDs suit that world, where each user actor brings its own code.

That world didn't arrive. User-deployable WASM actors were partly implemented in ref-fvm in 2022 behind `m2-native`, then stalled on gas pricing for adversarial WASM and unpredictable compile times. The last design discussion, [FIPs#779](https://github.com/filecoin-project/FIPs/discussions/779), is from 2023, and its motivating user, Fluence, withdrew in September 2023 ([FIPs#769](https://github.com/filecoin-project/FIPs/discussions/769)). The FEVM became the programmability path instead. [FIP-0118](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0118.md) puts its governed, frequently changing parameters in two FEVM contracts, the Stream Weights Actor and the Service Rewards Actor, which can be upgraded outside network upgrades, while consensus enforcement stays in the builtin reward and miner actors. Meanwhile every node pays a full actors rewrite at every upgrade for per-actor code CIDs, and every actor on the network has one of the 16 code CIDs in the current manifest. If that changes (say, Ethereum adopts a WASM execution environment), a future FIP can design for it then.

### Strings, not integers

ref-fvm already numbers builtin actor types 1 to 16 for `get_builtin_actor_type`, but the numbers are positions in the manifest list, and removing a type from the bundle (FIP-0121) renumbers everything after it. Filecoin also has more integer namespaces than anyone enjoys: network versions, actors versions, state tree versions, manifest versions, and singleton actor IDs (`f00` to `f099`) that look like they might be type numbers. Another integer scheme isn't worth the ~9 bytes per actor it would save.

Manifest names already exist as the manifest's keys, and they are what node APIs and block explorers show users. Removing a type is deleting its entry. A CBOR text string is also distinguishable from a link, which leaves room for a type-or-CID field if one is ever needed.

### The state root, not the system actor

Earlier discussion in [FIPs#1090](https://github.com/filecoin-project/FIPs/discussions/1090) considered keeping the mapping in the system actor. An actor is the right home for a mapping that actors change at runtime, as the init actor would have under `install_actor`. Without that, an actor-held mapping means that decoding any actor (system actor included) first requires reading the system actor's state. That can be special-cased, but the state root already has an unused slot whose structure the state tree version defines, and the state tree version has to change anyway.

### An explicit actors version

Node implementations map code CIDs to actors versions to choose state decoders, and that mapping is already ambiguous: the `placeholder` code CID is identical in every actors version from v10 to v20, and consecutive bundles can share some or all of their code (the current nv30 development bundle is byte-identical to v19). Decoders mostly don't care, since identical code means identical state layout, but some node logic keys on actors version alone: Lotus selects the [FIP-0081](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0081.md) pledge formula by reward actor version, and reward state is identical in v14 and v15. Recording the version in `ActorTypes` makes state self-describing. One version per bundle matches how upgrades work: all actors move together.

### Faster migrations instead

Two migration runner improvements that don't need a protocol change were prototyped:

- A parallel structural rewrite. A HAMT's shape depends only on its keys, so a migration that only changes _values_ can rewrite the tree node by node across many workers instead of reinserting 3.85M entries into a new tree one at a time. It can speed up the rewrite considerably, but writes the same volume, and the gain depends on how much read concurrency the node's storage allows.
- An incremental epoch run, which diffs the tree the pre-migration started from against the tree at the epoch and patches the pre-migration result. It was considered in 2025 as a scaled-back alternative to this FIP, and cuts the epoch work substantially. But it is brittle: it relies on every migration author correctly declaring which actors' results depend only on their own state, and a wrong declaration splits nodes that took the incremental path from those that didn't. This is a footgun for future migration authors. Nodes that restarted or had pre-migration disabled still still do the full migration at the epoch.

The parallel rewrite stays useful under this FIP for migrations that touch a whole actor type, such as any future trimming of inactive miner actors.

## Backwards Compatibility

This changes the encoding of every actor and of the system actor's state. Lotus, Forest and Venus need state tree version 6, and FVM consumers need a ref-fvm release that is able to read it.

### Node APIs

Node APIs that return actors (in Lotus: `StateGetActor`, `StateReadState`, `StateChangedActors`, and actor state in `StateCall`, `StateReplay` and `StateCompute` traces) should keep returning `Code`, resolved from the state the actor was read from. The open-source consumers surveyed that classify actors read `Code` and map it to a type through a per-version table: their own (Beryx through fil-parser, Lily), the node's via `StateActorCodeCIDs` (the FIDL scraper), or Lotus's when used as a library (Curio, Boost). All of these keep working with a resolved `Code`. Blockscout takes type names from the Beryx and Filfox APIs, and wallets surveyed don't read `Code`. Filfox is closed source; its public API returns manifest names. Nodes should also return the type name, so consumers can drop their code CID tables, and add a state-keyed method returning `ActorTypes` to replace reading the system actor's state for the current manifest.

Across a code-only upgrade, `StateChangedActors` and other state diffs report only the actors whose state changed.

### Raw state readers

Anything that decodes the actors HAMT or state root directly (CAR snapshot parsers, `ChainReadObj` walkers, Lily, Lantern, alternative node implementations) must handle state tree version 6. A version 5 decoder fails on a version 6 actor, finding a string where it expects a link.

### Other

- Init actor `Exec` still takes a code CID and resolves it against the current manifest. Tools that hardcode a multisig code CID still go stale whenever the multisig code changes; a type-named variant of `Exec` could be considered separately.
- IPC subnets embed ref-fvm with custom actor bundles, today through a second manifest alongside the system one. They are unaffected until they adopt a ref-fvm release with state tree version 6. From then each state has one manifest, the one its `ActorTypes` links, and custom actor types are entries in it.
- The FVM's integer type numbers remain an implementation detail of ref-fvm and builtin-actors and do not appear in state.

## Test Cases

- Conversion of mainnet and calibration network state at a recent epoch: every version 6 actor has the same head, nonce, balance and delegated address as in version 5, and its `Type` resolves to its version 5 `Code`. The two trees have the same HAMT shape, so this can be checked node by node.
- A code-only upgrade after activation changes only `ActorTypes`, the state root and the HAMT paths of actors with migrated state.
- An upgrade whose manifest is identical to the previous version's still writes a new `ActorTypes` with the new `ActorsVersion`.
- Placeholder promotion to `ethaccount` and to `evm` writes the correct type.
- `get_actor_code_cid` returns the resolved code CID for every builtin type.
- Genesis at the activation network version produces a version 6 state with system actor state `[]`.
- Loading an actor whose `Type` is absent from the manifest, or is not a text string, is a state error.
- A state tree version 5 decoder rejects a version 6 actor.

## Security Considerations

The FVM resolves the same code for every actor as it does today, and every syscall reachable on Filecoin networks returns the same values. The new failure modes are in decoding and migration. An implementation that resolves `Type` against the wrong manifest, such as one cached from another state, would execute the wrong code, so implementations must resolve against the `ActorTypes` of the state being executed or read.

Taking the full rewrite out of routine upgrades reduces risk: shorter, more predictable upgrades, less memory pressure, and fewer nodes falling behind at the boundary.

## Incentive Considerations

None.

## Product Considerations

For node operators, code-only upgrades lose the pre-migration, the epoch pause, the memory spike and the full copy of the actors tree in archives and snapshots. Indexers see only real state changes at upgrades and can make calls at the upgrade epoch, and consumers get stable type names in place of per-version code CID tables. The actors HAMT is around 29% smaller after conversion.

## Implementation

- **ref-fvm:** state tree version 6 encoding and decoding at the state tree boundary, keeping the resolved code in the in-memory actor; manifest loaded from `ActorTypes`; `create_actor` records the type name; `install_actor`, `upgrade_actor` and their features deprecated, with removal at the next major release. The current major can carry this alongside version 5, since the new paths are reached only from a version 6 state root.
- **builtin-actors:** system actor state becomes `[]`.
- **go-state-types:** version 6 actor and state root types, the conversion migration, and a migration runner keyed by type name that only visits actors of types with state changes.
- **Lotus:** version 6 state tree reading and writing, resolution at the state tree boundary, upgrade wiring, the API changes above, genesis at the activation network version.
- **Forest, Venus:** equivalent state tree and migration changes.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
