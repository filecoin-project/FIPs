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
 Please see FIP-0049 for a detailed explanation of the FVM event schema and the possible values each field 
 in the event schema can take. The interpretation of the flags field in each event entry is as follows:

 1. {"flags": "0x03”} ⇒ Index both key and value of the event entry
 2. {"flags": "0x02”} ⇒ Index only the value of the event entry
 3. {"flags": "0x01”} ⇒ Index only the key of the event entry
```

```
 All values in the event payloads defined below are encoded with CBOR and so the codec field for each event 
 entry will be set to 0x51.  The codec field is left empty in the payloads defined below only for the 
 sake of brevity.
```

```
 As specified in FIP-0049, events emitted by Actor methods are not persisted to message receipts and 
 rolled back if the Actor method emitting the event itself aborts and rolls back.
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
FIP-0074 will ensure that terminated deals are processed immediately in the OnMinerSectorsTerminate method 
rather than being submitted for deferred processing to the market actor cron job. That change will make 
this event available to clients.
```

The deal termination event is emitted by the market actor cron job when it processes deals that were marked
as terminated by the `OnMinerSectorsTerminate` method. 

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


## Design Rationale
Richer and more detailed payloads for the events were initially considered. However, a large event payload 
increases the event emission gas costs and the gas costs are borne by the users of the built-in actor 
methods. If clients want more information after receiving an event, they can query the state to do so.

The payload of an event should be as minimal as possible to minimise the event emission gas costs to users 
of built-in Actor methods. However, the event payloads should still have enough information for most 
clients consuming the events to determine if they are interested in reacting to the event 
(e.g. by querying chain state to obtain extra information about the transition).

### Verified Registry Events
The Verified Registry Event payloads have the allocation/claim IDs and client and provider Actor IDs. 
This enables users to filter the events by the client/provider whose claim/allocation they are interested 
in and then query the chain state with the corresponding allocation/claim ID to get more information.

### Market Actor Events
Once a deal is published, clients have access to the `dealId` of the deal. All Market Actor events except 
for the “deal published” event have the dealId in their payload which clients can use to filter for events
they are interested in and then query the chain state for more information.

The `dealId` is not known to the storage client before the deal is actually published as it is generated by 
the storage provider during the call to `PublishStorageDeals`. Therefore, to make the `deal published` 
event useful to subscribers and storage clients, the payload for that event also includes the `client` 
and `provider` Actors IDs so that listeners can filter this event by specific deal making parties they are
interested in.

Note that cron jobs do not return message receipts containing the emitted events back to the user. 
Therefore, the Market Actor  `deal-terminated` event will not be usable as it stands today as the deals 
are terminated by the cron job and so the event is also emitted from the cron job. 
However, once FIP-0074 is implemented as mentioned in the call out above, this event will be emitted from 
the `OnMinerSectorsTerminate` method itself. This will make the event available to clients and the 
gas cost for this event will then be paid by the `OnMinerSectorsTerminate` method.

The above is also true for the `deal-completed` event.  Deal completion is currently processed by a 
cron job and so the event will not be usable by clients. 
FIP-0074 will ensure that the processing of completed deals is done as part of a method called by the 
Storage Provider thus making this event available to clients

### Miner Actor Events
All Miner Actor Events will already have the Miner Actor ID in the `emitter` field of the event.

So, we only need to include the `sector number` in the event payload for Miner Actor events to enable 
clients to filter Miner Actor events by the Miner/Sector they are interested in.

An SP can activate a single sector by using the `ProveCommitSector` method. As of today, this method 
schedules a cron job to actually activate the sector which means that the sector activation event will be 
emitted by the cron job. This makes the event un-usable as events emitted by a cron job are not included 
in the message receipt. However, we still emit the sector activation event in the Miner Actor for 
completeness. A future FIP can ensure that sector activation is actually done as part of the 
`ProveCommitSector` method thus making this event available to clients and also to ensure that SPs 
actually pay the cost of sector activation and event emission.

There is an edge case we need to consider for the `sector-terminated` event in the Miner Actor. 
Some sectors can also be marked as terminated by the Miner Actor cron job as the number of terminations 
that can be processed immediately by the `TerminateSectors` method are rate-limited. 
The events emitted for these terminations will not be available to the client because they are 
emitted from a cron job.

## Backwards Compatibility
This proposal does not remove or change any exported APIs, nor change any state schemas. 
It is backwards compatible for all callers. Since it requires a change to actor code, a network upgrade is 
required to deploy it.

The actor events introduced in this FIP are fire and forget. No event is persisted in the Actor state and 
clients can choose not to consume any/all of the events.

Events emitted by built-in Actors do form a part of the `MessageReceipt` chain data structure  via 
the existing `events_root` field on `MessageReceipt`. While this field is set to empty today for 
built-in actor method calls, this field will contain a value once built-in actors start emitting events.

This FIP proposes adding CBOR encoding for encoding event values and clients that are interested in 
built-in Actor events will have to upgrade to understand CBOR.

However, this FIP does not propose changing the existing event schema or changing any of the chain 
data structures including the `MessageReceipt` structure. So, this change should be completely backward 
compatible.

## Test Cases
All pre-existing unit tests in the Verified Registry, Market and Miner Actors should expect and observe the emission of the events defined in this proposal wherever applicable.

Existing Integration tests should also expect and observe the emission of events defined in this proposal wherever applicable.

## Security Considerations
This proposal does not introduce any reductions in security.

## Incentive Considerations
Even though the event payloads have been kept minimal to minimise the gas costs for emitting events, 
this proposal does increase the gas cost of methods in the Verified Registry, Miner and Market Actors that 
emit the events defined in this FIP.

While this increased gas cost is borne by the users of the methods, the benefit of the emitted events 
is enjoyed by networking monitoring tools, network accounting tools, block explorer tools and other 
external agents that provide some sort of value added service to the Filecoin network.  However, 
improved implementation of these tools should indirectly benefit the network users.

One other important incentive consideration to callout here is that this FIP increases the gas cost of 
the `ProveCommitAggregate` method vis a vis the `ProveCommitSector` method even more as the former will 
have to pay the gas costs for emitting the sector activation events whereas for the latter, the event 
will be emitted in the corresponding sector activation cron job. We already have a pre-existing 
*“protocol bug”* wherein storage providers are sometimes incentivised to use the `ProveCommitSector` 
method to active a sector so that their sector activation gas costs get subsidised by the cron job and 
this FIP slightly exacerbates the problem. However, we are well aware of this problem and there are plans 
to fix this gas cost discrepancy by deprecating the `ProveCommitSector` 
method once [FIP-0076](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0076.md) lands.

## Product Considerations
This FIP will enable tools dedicated to network observability, monitoring, and accounting, as well as 
other external agents, to transition away from depending on highly-coupled, internal and low-level 
mechanisms such as state tree diffs/message-replays to source information about built-in actors activity 
and state transitions. They can instead use the events defined in this FIP as a source of truth to 
obtain the information they need (*for information captured by the specific subset of built-in actor 
events defined in this FIP).

Clients will still have to rely on pre-existing mechanisms for observability of transitions not captured 
by events defined in this FIP. However, we will propose and implement FIPs in the future to capture the 
entire spectrum of meaningful built-in actor events to enable clients to completely move away from 
pre-existing introspection mechanisms.

Validating nodes will have to store event data to make that data available to clients just as they store 
message receipts. This will increase the storage requirements for the validating nodes but event payloads 
have been design to be as minimal as possible to keep the storage requirement to a bare minimum.

## Implementation
Implementation of this proposal is in progress on the following feature branch: https://github.com/filecoin-project/builtin-actors/tree/integration/actor-events

## Copyright
Copyright and related rights waived via CC0.