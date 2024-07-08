---
fip: "<to be assigned>"
title: Filecoin Common Node Interface V1
author: "David Ansermino (@ansermino), Aatif Syed (@aatifsyed)"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1032
status: Draft
type: FIP - Interface
category (*only required for Standard Track): Interface
created: 2024-06-25

---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->


# FIP-Number: Common Node API

## Simple Summary
Establish an basic specification for the common JSON-RPC API provided by Filecoin node implementations.

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->

Lacking a common API for all node implementations, client diversity is hindered as applications are unlikely to be interoperable with different node implementations. Lotus is the defacto reference implementation, but lacks a sufficiently specified interface for other implementers to replicate.

In this FIP a subset of existing RPC methods are formally specified to enable consistency across implementations, and provide clarity on the methods users can expect when interacting with a node.

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->


The JSON-RPC interface provided by Filecoin node implementations is the primary interaction point for many systems, however a standard interface has yet to be established definitively. Lacking such standards, builders are forced to invest additional time and resources in reverse engineering implementations. Node interoperability is hindered as there are no gurantees about what APIs will be encountered in the wild. A proper specification will enable the development of applications that are implementation-agnostic.

Ultimately the [Lotus RPC API](https://github.com/filecoin-project/lotus/blob/b73d4e0481517b395a0e9aa9af5dab8bedc18285/documentation/en/api-v1-unstable-methods.md#mpoolpushmessage) is the defacto specification currently, which includes 280+ methods. Based on our exploration and discussions with the Lotus team we have established that some methods provide duplicated functionality (eg. `ChainGetGenesis()` is equivalent to`ChainGetTipSetByHeight(0)`). Another subset of methods are related to implementation-specific internals (eg. `ChainHotGC`). And yet another subset are for the purpose of configuring the instance, which could be exposed through other means (eg. CLI, config file) depending on the design principles of a node implementation. This leads us to conclude that the canonical RPC interface should only include a subset of the methods currently supported by Lotus.

The defacto Lotus specification is lacking in several features: complete JSON schemas, descriptions for each method, and reliable consistency with the implementation[^1]. This motivates us to propose a normative OpenRPC schema for the purpose of defining this interface in a machine readable format. This format in turn enables:
1. Compliance checks - enable implementations of the interface to verify the syntax
2. Specificity - it provides a language agnostic format for defining the ABI of the methods in the interface
3. Discoverability - allow consumers to dynamically interact with providers
4. Lack of desire to reinvent the wheel - It's not perfect, but it works...

[^1]: https://github.com/filecoin-project/lotus/issues/12164

Additionally, by establishing a specification we seek to establish a greater responsibility on implementers and encourage more discourse for future iterations and further interfaces. The present API shows signs of rapid iteration and the resulting technical debt.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

Using the OpenRPC specification format we define several groups of methods. These methods are defined in the OpenRPC specification found here: https://github.com/ChainSafe/filecoin-openrpc-spec. A list of the methods is included below for posterity.

All methods are reproduced identically to their present implementation in Lotus 1.26.1.

Categories have been assigned to indicate the identified use case (see Design Rationale).

Node implementers must include all specified methods in their API without any modifications. Implementers may choose to provide additional methods beyond what is included in this specification. The endpoint used to serve RPC requests must be versioned acccording the majo

## Subscription methods
Certain methods like `ChainNotify` are not oneshot request/response exchanges,
but bidirectional method calls and [notifications](https://www.jsonrpc.org/specification#notification).

We intend to provide schemas for these exchanges as an [OpenRPC extension](https://spec.open-rpc.org/#specification-extensions) in a future iteration of this FIP.
The following is an outline of the protocol for subscriptions as a set of
[Method Object](https://spec.open-rpc.org/#method-object) fragments.
Both the `User` and the `Node` act as JSON-RPC [Client and Server](https://www.jsonrpc.org/specification#conventions)
simulataneously, with transport-level correlation agreed out-of-band.

1. Initial subscription (bidirectional JSON-RPC method call).
   `User` acts as a JSON-RPC Client, and `Node` as a JSON-RPC Server.
   ```json
   {
    "name": "<subscriptionMethod>",
    "params": [
      /* <subscriptionParams> */
    ],
    "paramStructure": "by-position",
    "result": {
      "name": "channelID",
      "required": true,
      "schema": {
        "type": "int"
      }
    }
   }
   ```
   `subscriptionMethod` and `subscriptionParams` will vary by method.
2. Subscription item delivery (JSON-RPC notification).
   `User` acts as a JSON-RPC Server, and `Node` as a JSON-RPC Client.
   ```json
   {
    "name": "xrpc.ch.val",
    "params": [
      {
        "name": "channelID",
        "required": true,
        "schema": { "type": "int" }
      },
      {
        "name": "channelContent",
        "required": true,
        "schema": { "$ref": "<notificationSchema>" }
      }
    ],
    "paramStructure": "by-position"
   }
   ```
   `notificationSchema>` will vary by method.
3. Initiate subscription cancellation (JSON-RPC notification).
   `User` acts as a JSON-RPC Client, and `Node` as a JSON-RPC Server.
   ```json
   {
    "name": "xrpc.cancel",
    "params": [
      {
        "name": "channelID",
        "required": true,
        "schema": { "type": "int" }
      }
    ],
    "paramStructure": "by-position"
   }
   ```
4. Complete subscription cancellation (JSON-RPC notification).
   `User` acts as a JSON-RPC Server, and `Node` as a JSON-RPC Client.
   ```json
   {
    "name": "xrpc.ch.close",
    "params": [
      {
        "name": "channelID",
        "required": true,
        "schema": { "type": "int" }
      }
    ],
    "paramStructure": "by-position"
   }
   ```

## Methods

> Working document: https://docs.google.com/spreadsheets/d/1fFkQuEjvFAd2s1dGX5zGmhxsEMLMUZ4uQFnIXgSZA5w/edit?usp=drivesdk


| Method                              | Category         | Description                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ----------------------------------- | ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ChainGetBlock                       | State query      | Returns the block with the specified CID                                                                                                                                                                                                                                                                                                                                                                                                       |
| ChainGetEvents                      | State query      | Returns the events under an event AMT root CID                                                                                                                                                                                                                                                                                                                                                                                                 |
| ChainGetMessage                     | State query      | Returns the message with the specified CID                                                                                                                                                                                                                                                                                                                                                                                                     |
| ChainGetParentMessages              | State query      | Returns the messages included in the blocks of the parent tipset                                                                                                                                                                                                                                                                                                                                                                               |
| ChainGetPath                        | State query      | Returns the path between the specified tipsets                                                                                                                                                                                                                                                                                                                                                                                                 |
| ChainGetTipSet                      | State query      | Returns the tipset with the specified CID                                                                                                                                                                                                                                                                                                                                                                                                      |
| ChainGetTipSetAfterHeight           | State query      | Looks back for a tipset at the specified epoch. If there are no blocks at the specified epoch, the first non-nil tipset at a later epoch will be returned. A fork can be specified, or null for the heaviest chain                                                                                                                                                                                                                             |
| ChainGetTipSetByHeight              | State query      | Returns the tipset at the specified height                                                                                                                                                                                                                                                                                                                                                                                                     |
| ChainHasObj                         | State query      | checks if a given CID exists in the chain blockstore                                                                                                                                                                                                                                                                                                                                                                                           |
| ChainHead                           | State query      | Returns the chain head (ie. the heaviest tipset)                                                                                                                                                                                                                                                                                                                                                                                               |
| ChainNotify                         | State query      | Subscribe to changes to the chain head                                                                                                                                                                                                                                                                                                                                                                                                         |
| ChainPutObj                         |                  | Puts a given object into the block store                                                                                                                                                                                                                                                                                                                                                                                                       |
| ChainReadObj                        | State query      | Reads IPLD nodes referenced by the specified CID from chain blockstore and returns raw bytes.                                                                                                                                                                                                                                                                                                                                                  |
| ChainTipSetWeight                   | State query      | Returns the weight of the specified tipset                                                                                                                                                                                                                                                                                                                                                                                                     |
| GasEstimateFeeCap                   | Transactions     | Returns the estimated fee cap for the given parameters                                                                                                                                                                                                                                                                                                                                                                                         |
| GasEstimateGasLimit                 | Transactions     | Returns the estimated gas limit for the given parameters                                                                                                                                                                                                                                                                                                                                                                                       |
| GasEstimateGasPremium               | Transactions     | Returns the estimated gas premium for the given parameters                                                                                                                                                                                                                                                                                                                                                                                     |
| GasEstimateMessageGas               | Transactions     | Returns the estimated gas for the given parameters                                                                                                                                                                                                                                                                                                                                                                                             |
| GetActorEventsRaw                   | State query      | Returns all user-programmed and built-in actor events that match the given filter. This is a request/response API. Results available from this API may be limited by the MaxFilterResults and MaxFilterHeightRange configuration options and also the amount of historical data available in the node.                                                                                                                                         |
| MinerCreateBlock                    | Miner operations | Fill and sign a block template on behalf of the given miner, returning a suitable block header                                                                                                                                                                                                                                                                                                                                                 |
| MinerGetBaseInfo                    | Miner operations | Looks up the Miner Actor at the given address (and tipset), returning basic information like their power, eligibility to mine etc                                                                                                                                                                                                                                                                                                              |
| MpoolBatchPush                      | Transactions     | Adds a set of signed messages to the message pool                                                                                                                                                                                                                                                                                                                                                                                              |
| MpoolBatchPushUntrusted             | Transactions     | Adds a set of messages to the message pool with additional verification checks                                                                                                                                                                                                                                                                                                                                                                 |
| MpoolGetNonce                       | Transactions     | Returns the current nonce for the specified address                                                                                                                                                                                                                                                                                                                                                                                            |
| MpoolPending                        | Transactions     | Returns the pending messages for a given tipset                                                                                                                                                                                                                                                                                                                                                                                                |
| MpoolPush                           | Transactions     | Adds a signed message into the message pool                                                                                                                                                                                                                                                                                                                                                                                                    |
| MpoolPushMessage                    | Miner Operations | Assigns a nonce, signs, and pushes a message to the mempool                                                                                                                                                                                                                                                                                                                                                                                    |
| MpoolPushUntrusted                  | Transactions     | Adds a message to the message pool with verification checks                                                                                                                                                                                                                                                                                                                                                                                    |
| MpoolSelect                         | Transactions     | returns a list of pending messages for inclusion in the next block                                                                                                                                                                                                                                                                                                                                                                             |
| NetAddrsListen                      | Node operation   | Return list of listening addresses and peer ID                                                                                                                                                                                                                                                                                                                                                                                                 |
| NetAgentVersion                     |                  | Returns agent version string                                                                                                                                                                                                                                                                                                                                                                                                                   |
| NetConnect                          | Node operation   | Connect to a specified peer                                                                                                                                                                                                                                                                                                                                                                                                                    |
| NetDisconnect                       | Node operation   | Disconnect from the specified peer                                                                                                                                                                                                                                                                                                                                                                                                             |
| NetFindPeer                         | State query      | Returns dialable addresses for the specified peer                                                                                                                                                                                                                                                                                                                                                                                              |
| NetPeers                            | Node operation   | Return list of currently connected peers                                                                                                                                                                                                                                                                                                                                                                                                       |
| NetProtectAdd                       | Node operation   |                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| NetProtectList                      | Node operation   |                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| NetProtectRemove                    | Node operation   |                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| StateAccountKey                     | State query      | Returns the public key address of the given ID address for secp and bls accounts                                                                                                                                                                                                                                                                                                                                                               |
| StateCall                           | State query      | Runs the given message and returns its result without any persisted changes. StateCall applies the message to the tipset's parent state. The message is not applied on-top-of the messages in the passed-in tipset.                                                                                                                                                                                                                            |
| StateCirculatingSupply              | State query      | Returns the exact circulating supply of Filecoin at the given tipset.                                                                                                                                                                                                                                                                                                                                                                          |
| StateDealProviderCollateralBounds   | State query      | Returns the min and max collateral a storage provider can issue. It takes the deal size and verified status as parameters.                                                                                                                                                                                                                                                                                                                     |
| StateGetActor                       | State query      | Returns the specified actor's nonce and balance.                                                                                                                                                                                                                                                                                                                                                                                               |
| StateGetAllAllocations              | State query      | returns the all the allocations available in verified registry actor                                                                                                                                                                                                                                                                                                                                                                           |
| StateGetAllClaims                   | State query      | returns the all the claims available in verified registry actor                                                                                                                                                                                                                                                                                                                                                                                |
| StateGetAllocation                  | State query      | Returns the allocation for a given address and allocation ID.                                                                                                                                                                                                                                                                                                                                                                                  |
| StateGetAllocationForPendingDeal    | State query      | Returns the allocation for the specified pending deal. Returns nil if pending allocation is not found.                                                                                                                                                                                                                                                                                                                                         |
| StateGetAllocationIdForPendingDeal  | State query      | Identical to StateGetAllocationForPendingDeal except it returns the allocation ID                                                                                                                                                                                                                                                                                                                                                              |
| StateGetAllocations                 |                  | returns the all the allocations for a given client                                                                                                                                                                                                                                                                                                                                                                                             |
| StateGetBeaconEntry                 | State query      | Returns the claim for a given address and claim ID                                                                                                                                                                                                                                                                                                                                                                                             |
| StateGetClaim                       | State query      | Returns the claim for a given address and claim ID                                                                                                                                                                                                                                                                                                                                                                                             |
| StateGetClaims                      | State query      | returns the all the claims for a given provider                                                                                                                                                                                                                                                                                                                                                                                                |
| StateGetNetworkParams               | State query      | Returns current network params                                                                                                                                                                                                                                                                                                                                                                                                                 |
| StateGetRandomnessDigestFromBeacon  | State query      | samples the beacon for randomness                                                                                                                                                                                                                                                                                                                                                                                                              |
| StateGetRandomnessDigestFromTickets | State query      | sample the chain for randomness                                                                                                                                                                                                                                                                                                                                                                                                                |
| StateGetRandomnessFromBeacon        | State query      | Returns the beacon entry for the given filecoin epoch. If the entry has not yet been produced, the call will block until the entry becomes available                                                                                                                                                                                                                                                                                           |
| StateGetRandomnessFromTickets       | State query      | sample the chain for randomness                                                                                                                                                                                                                                                                                                                                                                                                                |
| StateListActors                     | State query      | returns the addresses of every actor in the state                                                                                                                                                                                                                                                                                                                                                                                              |
| StateListMessages                   | State query      | looks back and returns all messages with a matching to or from address, stopping at the given height.                                                                                                                                                                                                                                                                                                                                          |
| StateListMiners                     | State query      | Returns the addresses of every miner that has claimed power in the Power Actor                                                                                                                                                                                                                                                                                                                                                                 |
| StateLookupID                       | State query      | retrieves the ID address of the given address                                                                                                                                                                                                                                                                                                                                                                                                  |
| StateLookupRobustAddress            | State query      | Returns the public key address of the given ID address for non-account addresses (multisig, miners etc)                                                                                                                                                                                                                                                                                                                                        |
| StateMarketBalance                  | State query      | looks up the Escrow and Locked balances of the given address in the Storage Market                                                                                                                                                                                                                                                                                                                                                             |
| StateMarketDeals                    | State query      | returns information about every deal in the Storage Market                                                                                                                                                                                                                                                                                                                                                                                     |
| StateMarketParticipants             | State query      | returns the Escrow and Locked balances of every participant in the Storage Market                                                                                                                                                                                                                                                                                                                                                              |
| StateMarketStorageDeal              | State query      | returns information about the specified deal                                                                                                                                                                                                                                                                                                                                                                                                   |
| StateMinerActiveSectors             | State query      | Returns info about sectors that a given miner is actively proving                                                                                                                                                                                                                                                                                                                                                                              |
| StateMinerAllocated                 | State query      | Returns info about sectors that a given miner is actively proving                                                                                                                                                                                                                                                                                                                                                                              |
| StateMinerAvailableBalance          | State query      | Returns the portion of a miner's balance that can be withdrawn or spent                                                                                                                                                                                                                                                                                                                                                                        |
| StateMinerDeadlines                 | State query      | Returns all the proving deadlines for the given miner                                                                                                                                                                                                                                                                                                                                                                                          |
| StateMinerFaults                    | State query      | Returns a bitfield indicating the faulty sectors of the given miner                                                                                                                                                                                                                                                                                                                                                                            |
| StateMinerInfo                      | State query      | returns info about the specified miner                                                                                                                                                                                                                                                                                                                                                                                                         |
| StateMinerInitialPledgeCollateral   | State query      | returns the initial pledge collateral for the specified miner's sector                                                                                                                                                                                                                                                                                                                                                                         |
| StateMinerPartitions                | State query      | returns all partitions in the specified deadline                                                                                                                                                                                                                                                                                                                                                                                               |
| StateMinerPower                     | State query      | returns the power of the indicated miner                                                                                                                                                                                                                                                                                                                                                                                                       |
| StateMinerPreCommitDepositForPower  | State query      |                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| StateMinerProvingDeadline           | State query      | calculates the deadline at some epoch for a proving period and returns the deadline-related calculations.                                                                                                                                                                                                                                                                                                                                      |
| StateMinerRecoveries                | State query      | returns a bitfield indicating the recovering sectors of the given miner                                                                                                                                                                                                                                                                                                                                                                        |
| StateMinerSectorAllocated           | State query      | checks if a sector number is marked as allocated                                                                                                                                                                                                                                                                                                                                                                                               |
| StateMinerSectorCount               | State query      | returns the number of sectors in a miner's sector set and proving set                                                                                                                                                                                                                                                                                                                                                                          |
| StateMinerSectors                   | State query      | returns info about the given miner's sectors. If the filter bitfield is nil, all sectors are included                                                                                                                                                                                                                                                                                                                                          |
| StateReadState                      | State query      | Returns the indicated actor's state                                                                                                                                                                                                                                                                                                                                                                                                            |
| StateReplay                         | State query      | [https://github.com/filecoin-project/lotus/blob/286fadaca4d2af81bedf4213daebfbbdbcd5e337/api/api_full.go#L356-L373](https://github.com/filecoin-project/lotus/blob/286fadaca4d2af81bedf4213daebfbbdbcd5e337/api/api_full.go#L356-L373)                                                                                                                                                                                                         |
| StateSearchMsg                      | State query      | [https://github.com/filecoin-project/lotus/blob/286fadaca4d2af81bedf4213daebfbbdbcd5e337/api/api_full.go#L431-L447](https://github.com/filecoin-project/lotus/blob/286fadaca4d2af81bedf4213daebfbbdbcd5e337/api/api_full.go#L431-L447)                                                                                                                                                                                                         |
| StateSectorExpiration               | State query      | Returns the epoch at which given sector will expire                                                                                                                                                                                                                                                                                                                                                                                            |
| StateSectorGetInfo                  | State query      | Returns the on-chain info for the specified miner's sector. Returns null in case the sector info isn't found. NOTE: returned info.Expiration may not be accurate in some cases, use StateSectorExpiration to get accurate expiration epoch.                                                                                                                                                                                                    |
| StateSectorPartition                | State query      | Finds deadline/partition with the specified sector                                                                                                                                                                                                                                                                                                                                                                                             |
| StateSectorPreCommitInfo            | State query      | Returns the PreCommit info for the specified miner's sector. Returns null and no error if the sector isn't precommitted. Note that the sector number may be allocated while PreCommitInfo is nil. This means that either allocated sector numbers were compacted, and the sector number was marked as allocated in order to reduce size of the allocated sectors bitfield, or that the sector was precommitted, but the precommit has expired. |
| StateVerifiedClientStatus           | State query      | Returns the data cap for the given address. Returns nil if there is no entry in the data cap table for the address.                                                                                                                                                                                                                                                                                                                            |
| StateVerifiedRegistryRootKey        | State query      | returns the address of the Verified Registry's root key                                                                                                                                                                                                                                                                                                                                                                                        |
| StateVerifierStatus                 | State query      | Returns the data cap for the given address. Returns nil if there is no entry in the data cap table for the address.                                                                                                                                                                                                                                                                                                                            |
| StateVMCirculatingSupplyInternal    | State query      | returns an approximation of the circulating supply of Filecoin at the given tipset. This is the value reported by the runtime interface to actors code.                                                                                                                                                                                                                                                                                        |
| StateWaitMsg                        | State query      | [https://github.com/filecoin-project/lotus/blob/286fadaca4d2af81bedf4213daebfbbdbcd5e337/api/api_full.go#L448-L466](https://github.com/filecoin-project/lotus/blob/286fadaca4d2af81bedf4213daebfbbdbcd5e337/api/api_full.go#L448-L466)                                                                                                                                                                                                         |
| WalletBalance                       | Miner operations | Returns balance of a wallet                                                                                                                                                                                                                                                                                                                                                                                                                    |
| WalletHas                           | Miner operations | indicates whether the given address is in the wallet                                                                                                                                                                                                                                                                                                                                                                                           |
| WalletList                          | Miner operations | Returns a list of all the addresses in the wallet.                                                                                                                                                                                                                                                                                                                                                                                             |
| WalletSign                          | Miner operations | signs the given bytes using the given address                                                                                                                                                                                                                                                                                                                                                                                                  |
| WalletSignMessage                   | Miner operations | signs the given message using the given address.                                                                                                                                                                                                                                                                                                                                                                                               |



## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->

This interface is contrived from the existing [Lotus RPC V1 interface](https://github.com/filecoin-project/lotus/blob/48287574d82c81ffc50f259134c6596add32a2f5/documentation/en/api-v1-unstable-methods.md). Due to the large number of methods presently supported, we have limited the scope of this specification to include methods with a well established use case. We have observed the requirements of Lotus-miner, Curio, Web3Mine and Boost to inform which methods are actively used. We have also considered insights from Glif based on the usage of their RPC service.

We target two groups of users: *end users* and *node operators*. These each have their own requirements for particular data and access control. While no attempt is made in this FIP to specify considerations  for these groups (eg. access control), these groups are used to justify the need for particular methods.


Methods included in the API fall into one of these categories:

- State Queries
  - These primarily concern the chain state, actor state or network (p2p) state. They are read-only methods that are necessary to expose all elements of global state.

- Miner Operations
  - A small set of specialized methods miner applications require to participate in consensus.

- Transactions
  - Necessary methods to submit new transaction for inclusion in the chain, including inspecting the mempool and estimating gas parameters.

- Node Operation
  - Several methods are included to enable remote management and inspection of a node instance via RPC. These have been restricted to commonly used, implementation-agnostic methods.

### Additional Notes

#### `Eth` Methods
`Eth` methods have been excluded as they are inferred from the [Ethereum JSON-RPC specification](https://ethereum.org/en/developers/docs/apis/json-rpc/), with some changes. We intend for these differences to specified in a later FIP.

### Future Revisions
It is expected that changes to this API will be made at some point in the future. All non-breaking changes should be introduced within the spec repo, at the discretion of node implementation teams (presently Lotus, Forest, Venus). Rough consensus should be followed, with implementation teams that adhere to the specification as the primary decision makers.

Breaking changes must be submitted as an FIP before being introduced to the latest spec.

In all cases valid semantic versioning must be used.

## Backwards Compatibility - Review
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

The methods in this specification are a subset of methods from the existing defacto specification (ie. Lotus API), which all implementation follow, thus backwards compatibility is maintained.

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->

[TODO]

We may want to consider three types of testing:
- Schema conformance (request/response structure in OpenRPC document is valid)
- Implementation conformance (implementation adheres to schemas)
- Functional conformance (request returns expected response values)


## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->

Node implementers must consider the security implications of all methods and ensure sufficient access controls are implemented. This is beyond the scope of this FIP.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->

Not relevant to this FIP.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->

A better API, one that is well defined and carefully constructed, will ease the development of many types of applications. This FIP is only sufficient in ensuring the API is well defined, additional work is needed in future to refine the API.

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->

- [ ] Lotus
  - [ ] Implementation of Common Node API methods
  - [ ] OpenRPC document available
  - [ ] Automated testing of conformance to schema
  - [ ] Common Node API methods conform to schema
- [ ] Forest
  - [ ] Implementation of Common Node API methods
  - [ ] OpenRPC document available
  - [ ] Automated testing of conformance to schema
  - [ ] Common Node API methods conform to schema
- [ ] Venus
  - [ ] Implementation of Common Node API methods
  - [ ] OpenRPC document available
  - [ ] Automated testing of conformance to schema
  - [ ] Common Node API methods conform to schema

## TODO
<!--A section that lists any unresolved issues or tasks that are part of the FIP proposal. Examples of these include performing benchmarking to know gas fees, validate claims made in the FIP once the final implementation is ready, etc. A FIP can only move to a “Last Call” status once all these items have been resolved.-->

- [x] Confirm methods that are included
- [ ] Improve descriptions for included methods
- [ ] Change link to be an issue for the inconsistency
- [ ] Add a note on URIs (eg. `/rpc/v1`)
- [ ] Publish two versions of the document, one per URI
- [x] Make ChainNotify definition more generic
- [ ] Add link to playground
- [ ] Perform proper spellcheck
- [ ] Determine if this should be FIP or FRC
- [ ] Setup discussion forum and add to header
- [ ] Reach out to Venus to establish the state of their RPC
- [ ] Transfer spec repo to filecoin-project and update links above
- [ ] Add examples to all methods in spec

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
