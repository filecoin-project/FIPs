---
fip: "FIP-xxx"
title: Add built-in Actor events
author: "Aarsh Shah"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/754
status: Draft
type: Technical (Core)
category: Core
created: 2023-11-27
---

## Summary
This FIP defines and proposes the implementation of a meaningful subset of fire-and-forget externally observable events that should be emitted by the built-in Verified Registry, Storage Market and Storage Miner Actors. These enable external agents (henceforth referred to as *“clients”*) to observe and track a specific subset of on-chain data-cap allocation/claims, deal lifecycle and sector lifecycle state transitions.

While this FIP explicitly delineates the implementation of events tied to specific transitions, it does not encompass the full spectrum of potential built-in actor events. The introduction and integration of additional built-in actor events will be addressed in subsequent FIPs.

## Abstract
[#FIP 0049](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0049.md) introduced and implemented the ability for actors to emit fire-and-forget externally observable events during execution.

This FIP aims to be the first of many for implementing events in the built-in Actors. This specific FIP enumerates, defines and proposes the implementation of a subset of events for data-cap allocation/claims, deal lifecycle and sector life cycle transitions in the Verified Registry, Market and Miner Actors.

The events introduced in this FIP will enable *clients* such as network monitoring tools, block explorers, SP <> client deal brokering systems, browser clients, filecoin blockchain oracles etc. to rely on these events as a source of truth for sourcing information about the specific subset of on-chain activity and transitions captured by these events.

Events are emitted by the Verified Registry Actor for each verifier balance update, each allocation created, expired or claimed and for each claim that is updated or removed.

Events are emitted by the Market Actor for each deal that is published, activated, terminated or completed successfully.

Events are emitted by the Miner Actor for each sector that is precommitted, activated, updated (SnapDeals) or terminated by an SP.

## Change Motivation
While FEVM smart contracts can already emit events, built-in actors are still eventless. This FIP is the first step towards fixing the external observability of built-in actors.

Filecoin network observability tools, Block explorers, SP monitoring dashboards, deal brokering software etc need to rely on complex low-level techniques such as State tree diffs to source information about on-chain activity and state transitions. Emitting the select subset of built-in  actor events defined in this FIP will make it easy for these clients to source the information they need by simply subscribing to the events and querying chain state.

## Specification
```
Please see FIP-0049 for a detailed explanation of the FVM event schema and the possible values each field in the event schema can take. The interpretation of the flags field in each event entry is as follows:

1. {"flags": "0x03”} ⇒ Index both key and value of the event entry
2. {"flags": "0x02”} ⇒ Index only the value of the event entry
3. {"flags": "0x01”} ⇒ Index only the key of the event entry

```
```
All values in the event payloads defined below are encoded with CBOR and so the codec field for each event entry will be set to 0x51.  The codec field is left empty in the payloads defined below only for the sake of brevity.
```
```
As specified in FIP-0049, events emitted by Actor methods are not persisted to message receipts and rolled back if the Actor method emitting the event itself aborts and rolls back.
```

### FVM should support CBOR encoding
The FVM currently only supports event values encoded with the `raw` encoding. It will now have
to support CBOR encoding as well as built-in actor event values will be encoded with CBOR.

### Verified Registry Actor Events

#### Verifier Balance Updated
This event is emitted when the balance of a verifier is updated in the Verified Registry Actor.

The event payload is defined as:

| flags                | key | value |
|----------------------| --- | --- |
| Index Key + Value    | “$type” | “verifier-balance” |
| Index Key + Value    | “verifier” | $VERIFIER_ACTOR_ID |
| Index Key            | “balance” | $VERIFIER_DATACAP_BALANCE |


#### Datacap Allocated
This event is emitted when a verified client allocates datacap to a specific data set and storage provider.  

The event payload is defined as:

| flags | key | value |
| --- | --- | --- |
| Index Key + Value | “$type” | “allocation” |
| Index Key + Value | “id” | $ALLOCATION_ID |
| Index Key + Value | “client” | $CLIENT_ACTOR_ID |
| Index Key + Value | “provider” | $SP_ACTOR_ID |

#### Datacap Allocation Removed
This event is emitted when an expired datacap allocation that is past it’s expiration epoch is removed.

The event payload is defined as:

| flags | key | value |
| --- | --- | --- |
| Index Key + Value | “$type” | “allocation-removed” |
| Index Key + Value | “id” | $ALLOCATION_ID |
| Index Key + Value | “client” | $CLIENT_ACTOR_ID |
| Index Key + Value | “provider” | $SP_ACTOR_ID |

#### Allocation Claimed
This event is emitted when a client allocation is claimed by a storage provider after the corresponding verified data is provably committed to the chain.

The event payload is defined as:

| flags | key | value |
| --- | --- | --- |
| Index Key + Value | “$type” | “claim-updated” |
| Index Key + Value | “id” | $CLAIM_ID |
| Index Key + Value | “client” | $CLIENT_ACTOR_ID |
| Index Key + Value | “provider” | $SP_ACTOR_ID |

#### Allocation Claim Removed
This event is emitted when an expired claim is removed by the Verified Registry Actor.

The event payload is defined as:

| flags | key | value |
| --- | --- | --- |
| Index Key + Value | “$type” | “claim-removed” |
| Index Key + Value | “id” | $CLAIM_ID |
| Index Key + Value | “client” | $CLIENT_ACTOR_ID |
| Index Key + Value | “provider” | $SP_ACTOR_ID |

### Market Actor Events
The Market Actor emits the following deal lifecycle events:

#### Deal Published
This event is emitted for each new deal that is successfully published by a storage provider. 

The event payload is defined as:

| flags | key | value |
| --- | --- | --- |
| Index Key + Value | “$type” | "deal-published" |
| Index Key + Value | "id" | ${DEAL_ID} |
| Index Key + Value | "client" | ${STORAGE_CLIENT_ACTOR_ID} |
| Index Key + Value | "provider" | ${STORAGE_PROVIDER_ACTOR_ID} |

#### Deal Activated
The deal activation event is emitted for each deal that is successfully activated. 

The event payload is defined as:

| flags | key | value |
| --- | --- | --- |
| Index Key + Value | “$type” | "deal-activated" |
| Index Key + Value | “id” | ${DEAL_ID} |

#### Deal Terminated
```
FIP-0074 will ensure that terminated deals are processed immediately in the OnMinerSectorsTerminate method rather than being 
submitted for deferred processing to the market actor cron job. That change will make this event available to clients.
```

The deal termination event is emitted by the market actor cron job when it processes deals that were marked as terminated by the OnMinerSectorsTerminate method. 

The event payload is defined as:

| flags | key | value |
| --- | --- | --- |
| Index Key + Value | “$type” | "deal-terminated" |
| Index Key + Value | “id” | ${DEAL_ID} |

#### Deal Completed Successfully 
This event is emitted when a deal is marked as successfully complete by the Market Actor cron job. The cron job will deem a deal to be successfully completed if it is past it’s end epoch without being slashed.

This event is not usable as it is emitted from a cron job. However, we still emit the event here for completeness. FIP-0074  will ensure that processing of completed deals is done as part of a method called by the Storage Provider thus making this event available to clients and also to ensure that SPs pay the gas costs of processing deal completion and event emission.


The event payload is defined as:

| flags | key | value |
| --- | --- | --- |
| Index Key + Value | “$type” | "deal-completed" |
| Index Key + Value | “id” | ${DEAL_ID} |

### Miner Actor Events
The Miner Actor emits the following sector lifecycle events:

#### Sector Pre-committed
The sector pre-committed event is emitted for each new sector that is successfully pre-committed by an SP.

The event payload is defined as:

| flags | key | value |
| --- | --- | --- |
| Index Key + Value | “$type" | "sector-precommitted" |
| Index Key + Value | “sector” | $SECTOR_NUMER |

#### Sector Activated
```
A new ProveCommitSectors2 method will be added as part of FIP-0076  post which we will have to update 
that method to emit the sector activation events as well.
```

This event is emitted for each pre-committed sector that is successfully activated by a storage provider. For now, sector activation corresponds 1:1 with prove-committing a sector but this can change in the future.

The event payload is defined as:

| flags | key | value |
| --- | --- | --- |
| Index Key + Value | “$type" | "sector-activated" |
| Index Key + Value | “sector” | $SECTOR_NUMER |

#### Sector Updated
This event is emitted for each CC sector that is updated to contained actual sealed data.

The event payload is defined as:

| flags | key | value |
| --- | --- | --- |
| Index Key + Value | “$type" | "sector-updated" |
| Index Key + Value | “sector” | $SECTOR_NUMER |

#### Sector Terminated
The sector termination event is emitted for each sector that is marked as terminated by a storage provider. 

The event payload is defined as:

| flags | key | value |
| --- | --- | --- |
| Index Key + Value | “$type" | "sector-terminated" |
| Index Key + Value | “sector” | $SECTOR_NUMER |