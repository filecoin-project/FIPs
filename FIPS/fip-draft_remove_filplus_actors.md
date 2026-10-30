---
fip: "<to be assigned>"
title: Remove the Fil+ Actors (f06, f07, f080)
author: "Rod Vagg (@rvagg)"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1300
status: Draft
type: Technical
category: Core
created: 2026-10-30
spec-sections:
requires: "0118"
---

# FIP-Number: Remove the Fil+ Actors (f06, f07, f080)

## Simple Summary

[FIP-0118](./fip-0118.md) (Solstice) froze the verified registry (f06), DataCap (f07) and root key holder (f080) actors and said a later upgrade would delete them. This is that upgrade. The three actors and their state leave the state tree; their balances are burned; the `verifiedregistry` and `datacap` actor types leave the bundle.

## Abstract

Since network version 29 every write method on f06 and f07 rejects, the miner and market actors never call them, and f080 exists only to be f06's root key. Nothing on chain reads their state. It is nevertheless still included in every state root, every snapshot and every node's hot blockstore, and every node implementation still ships code to decode and invariant-check it.

At the activation epoch of a network upgrade including this FIP, the state migration removes the three actors from the state tree, sends their balances to the burnt funds actor (f099) and installs an actor bundle without the `verifiedregistry` and `datacap` types. The historical record stays reachable at any pre-activation state root. No actor method, parameter or wire format changes.

## Change Motivation

FIP-0118 Section 1.6 deferred actor removal until no live path touched the actors. That condition held from the activation of nv29. The remaining reasons to act now are weight and maintenance:

- **State and snapshot size.** The frozen claims and allocations tables are included in every snapshot and occupy every node's hot store even though no transaction can ever read them again. Measured on mainnet at epoch 6,501,421 (2026-10-30), counting distinct blocks reachable from each actor's head:

  | Actor | Blocks | Bytes |
  |---|---:|---:|
  | f06 | 13,971,578 | 11.82 GB |
  | f07 | 2,063 | 306 KB |
  | f080 | 2 | 173 B |

  The f06 claims table is 99% of it: 123 million claims across 2,282 provider HAMTs. The claims table compresses to 6.3 GB at zstd-3; the Forest mainnet lite snapshot for the same day is 84.8 GB zstd-compressed, so these actors are roughly 7.5% of a snapshot download. They appear once no matter how many epochs of state the snapshot includes, since the DAG is frozen.

- **Maintenance.** Each implementation carries two actor types, their Go/Rust state mirrors, the claims-against-miners invariant check, and a dozen RPC methods, all of which can only return frozen data.

The removal is deliberately small. There is no new mechanism to design, only a deletion that FIP-0118 already committed to.

## Specification

### Migration

At the upgrade epoch the state migration:

1. Adds the balances of f06, f07 and f080 to the balance of f099. At the time of writing f06 holds 0.00100000666 FIL, f07 holds 0.00000000666 FIL and f080 holds nothing; the rule applies to whatever the balances are at the upgrade epoch.
2. Deletes the actor entries for IDs 6, 7 and 80 from the state tree.
3. Updates the system actor's built-in actor manifest to the new bundle, which no longer includes `verifiedregistry` or `datacap`.

No other actor's state changes. The total of all actor balances is unchanged by the migration.

### Addresses

IDs 6, 7 and 80 remain unassigned forever. The init actor allocates IDs from 100, so none of them can be reallocated. A message or internal send whose receiver resolves to one of them fails with `SYS_INVALID_RECEIVER` (exit code 5), the same as any other nonexistent ID address.

### Actor bundle

The `verifiedregistry` and `datacap` actor types are removed from the built-in actor bundle. The multisig type is unaffected; f080 was an ordinary multisig instance.

### Genesis

A genesis state for the activation network version or later contains none of the three actors. Genesis templates stop requiring a verified registry root key.

### Unchanged

Everything FIP-0118 left serialised but inert stays: `verified_allocation_key` on piece manifests, claim declarations in `ExtendSectorExpiration2` and `DealProposal.verified_deal` are still accepted and still ignored. `GetDealVerified` still returns the stored flag. Sector `verified_deal_weight` is untouched. The FRC-42 method numbers and exit codes of every remaining actor are unchanged.

## Design Rationale

**Burn the balances.** The FIL in f06 and f07 arrived by plain value sends to actors that have no method that could spend it. Lotus already classes both actors' balances as uncirculating for supply accounting, so moving them to f099 leaves the reported circulating supply exactly where it is. Returning dust to senders would mean reconstructing senders from message history for about a thousandth of a FIL. f080 has no balance; if it acquires one before activation it is burned under the same rule rather than special-cased.

**Remove f080 as well.** It was created at genesis to hold f06's root key and has never had another purpose. It is the only key-owned actor this FIP touches (f06 and f07 are the protocol cleaning up after itself, f080 is a multisig with signers). The only call it could ever usefully make now rejects, and it sits at a reserved ID that appears as protocol infrastructure.

**Don't keep a read-only stub.** Keeping the actors with empty state would preserve the code CIDs and the `GetClaims`/`Balance` read methods at the cost of keeping both actor types in every bundle and every implementation forever. Nothing on chain needs those reads; anything off chain that does can read a pre-activation state root.

## Backwards Compatibility

The on-chain record of Fil+ (verifiers, allocations, claims, DataCap balances and allowances, the root key multisig) is reachable only at state roots before activation after this upgrade. Archival nodes and pre-activation snapshots will continue to include it. Anyone who wants the final state of Fil+ in a convenient form should export it before activation; the data does not change between now and then.

Node RPC methods that read these actors (in Lotus: the `StateGetAllocation*`, `StateGetClaim*`, `StateVerifierStatus`, `StateVerifiedClientStatus` and `StateVerifiedRegistryRootKey` families) return an actor-not-found error for post-activation tipsets.

Block explorers and indexers that decode state by actor code CID will no longer see actors with the `verifiedregistry` or `datacap` code after activation and must not treat the absence as an error.

## Test Cases

- Migration: an input tree with f06, f07 and f080 at known balances yields an output tree without them, with f099 increased by exactly the sum, every other actor's balance and head unchanged, and the system actor pointing at the new manifest. Run against the mainnet and calibration network state at a recent epoch.
- Post-activation: a message to f06, f07 or f080 fails with `SYS_INVALID_RECEIVER`; the state invariant checker passes without a verified registry or DataCap summary.
- Genesis at the activation network version: no actor exists at ID 6, 7 or 80, and the init actor's address map does not mention them.
- Bundle: the manifest for the activation actors version has no `verifiedregistry` or `datacap` entry.

## Security Considerations

Every change is in the migration. After activation the runtime executes the same code it executes today, minus two actor types, which shrinks the surface that implementations need to keep correct. The only funds affected are the trivial balances above, which are unspendable before this FIP anyway.

A migration that forgets to reassign a balance would silently reduce the sum of balances in the tree; the migration test must assert conservation. A migration that leaves a stale manifest entry would leave an unreachable code CID in the system actor's table; the test must assert the manifest contents.

## Incentive Considerations

None. Since nv29 the miner actor computes power, pledge and reward from sector state alone. About 140 PiB of minted-but-unallocated DataCap and the ~126 million allocation IDs ever issued become unreadable on chain; they were already unusable.

## Product Considerations

Nodes get a smaller state tree and smaller snapshots, so a faster initial sync and less hot-store churn. Archival nodes keep what they already have. Fil+ tooling that still points at these actors must be retired or pointed at historical state.

## Implementation

- **builtin-actors:** remove the `verifreg` and `datacap` crates from the bundle, the `VerifiedRegistry` and `DataCap` entries from the actor type enum, the singleton address constants, the verifreg policy constants and the verifreg/datacap arms of the state invariant checker.
- **go-state-types:** migration for the activation actors version (balance transfer, actor deletion, manifest update; the migration runner needs the ability to drop an actor rather than copy it), removal of the two manifest keys from the new version's registry, invariant checker arms removed.
- **Lotus:** wire the migration in the upgrade schedule; remove the verifreg and DataCap actor adapters for the new version; genesis stops creating the three actors at or after the activation network version; remove the remaining read-only `filplus` and `lotus-shed verifreg` commands (the write commands were removed for nv29); RPC methods return actor-not-found after activation.
- **Forest:** equivalent migration and decoder changes.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
