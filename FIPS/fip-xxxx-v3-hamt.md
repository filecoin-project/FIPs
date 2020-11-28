---
fip: <to be assigned>
title: hamt-v3
author: Rod Vagg (@rvagg), Steven Allen (@Stebalien), Alex North (@anorth), Zen Ground0 (@Zenground0)
discussions-to: https://github.com/filecoin-project/FIPs/issues/38
status: Draft
type: Technical
category: Core
created: 2020-11-27
specs-sections:
   - section-appendix.data_structures.hamt

---

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->

Improve the filecoin HAMT in terms of performance and safety with four smaller independent proposals.

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->
The filecoin HAMT does unnecessary Puts and Gets while doing Set and Find operations. Sub proposal `A` eliminates these unnecessary operations improving performance of HAMT calls.

The filecoin HAMT's pointer serialization can be modified to save 3 bytes and a small amount of de/encode time. Sub proposal `B` describes the more efficient serialization.

The filecoin HAMT node's bitfield serialization truncates bytes in a way that does not save much space but makes validation harder and implementation less simple. Sub proposal `C` is to write an untruncated bitfield of size `2^bitwidth` bits for all HAMT nodes.

The filecoin HAMT interface does provide any information on previous set values during a set call. This makes actors safety checks more expensive as they need to do an additional Get/Has. Sub proposal `D` is to add a method `SetIfAbsent` to the HAMT interface in order to do efficient existence checks during set.

## Change Motivation

### A & B
These are unambiguous performance wins. We aren't trading anything off we are strictly reducing ipld operations and serialization size which also corresponds to reduced gas cost.

### C
* Truncation makes it hard to validating canonical block form. From @rvagg's original issue: "The current implementation will (probably) take an arbitrarily long byte array and turn it into a valid big.Int. It'll treat as valid a block that has a byte array 1000 long in the position for the bitfield (I believe big.Int can handle this kind of arbitrary size). But then it should round-trip it back out as just-long-enough if the block was re-serialized."
* Truncation is not as simple as not doing truncation and this complexity is reflected in non-go code.
* Impact on serialization size is small and not worth the complexity. From @rvagg's original issue: "The randomness of the hash algorithm means that the chances of setting the 32nd bit are the same as setting the 1st. There's no bias toward smaller bits built-in here. So we buy some compaction in the serialization by using this truncated format, but it's only going to get us so far in a HAMT that's got more than a few values in it."

### D

Checking key existance during a Set operation is a reasonable operation for code like specs-actors that is wants the safety of invariant checking and efficiency. In particular this interface extension is motivated by setting a sector precommit in the precommit map in the miner actor's PrecommitSector method.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

### A
The existing HAMT loads child tree nodes into in memory cache nodes located on HAMT "link" pointers (not KV pointers). It also clears these cache nodes after writing them to disk during the Flush operation. Finally the current HAMT code writes to the blockstore when it creates new node during bucket overflow as part of setting new values.

This proposal is to (1) track modification of nodes and only Flush these caches to the blockstore when the cache node has been modified (2) stop clearing cache nodes on Flush (3) Move all blockstore writes to occur on Flush.

Concretely (1) can be achieved by adding a `dirty` flag as a sibling to the cahce node on the HAMT pointer. The flag defaults to false when a cache node is loaded for reading and set to true if a set or delete operation traverses through that node. Then during the Flush traversal, a cache node is written to the blockstore and its owning Pointer's Link field assigned to the cid of cache node only if the dirty flag is true at the time of Flush. Otherwise the cache node is skipped.

To achieve (2) implementations only need to stop clearing the cache nodes after flushing pointers during Flush.

Finally for (3) implementations can simply add a new cache node when creating a new child node during bucket overflow and mark this node as dirty so that it gets written during the next flush.

See go-hamt-ipld implementation [here](https://github.com/filecoin-project/go-hamt-ipld/pull/74) for a concrete example.

### B
HAMT pointers are union types. A pointer can be one of a link to a HAMT node or a KV bucket containing HAMT key value pairs. To achieve this pointers are currently serialized as a cbor map with at most one key. A key of "0" means link, a key of "1" means bucket.

This proposal is to only serialize the link or bucket of kvs and use the different cbor major types (tag major type or array major type) to distinguish which type populates the union on decode.

Succinctly from @rvagg, this proposal is to change from:
```
type Pointer union {
	&Node "0"
	Bucket "1"
} representation keyed
```
i.e. `{"0": CID}` or `{"1": [KV...]}`

to:
```
type Pointer union {
	&Node link
	Bucket list
} representation kinded
```
i.e. `CID` or `[KV...]`

See @rvagg's original proposal in go-hamt-ipld [here](https://github.com/filecoin-project/go-hamt-ipld/issues/53#issue-663418352) and the open PR implementing this in go-hamt-ipld [here](https://github.com/filecoin-project/go-hamt-ipld/pull/60) for more information.

### C
The existing HAMT bitmap does not serializes all bytes of the bitmap, only those higher order bytes up to and including the lowest non-zero byte in order to compactly represent the bitfield as a bigendian byte slice. The serialized size of the byte slice is not checked against HAMT paramters during node load which means a serialized bitmap with low order zero bytes can be reserialized differently.

This proposal is to (1) serialize all 2^bitwidth / 8 bytes of the bitmap of HAMT nodes (2) error when loading HAMT nodes with a serialized bitmap of a length that does not exactly match 2^bitwidth / 8 bytes.

See the open go-hamt-ipld PR implementing this change [here](https://github.com/filecoin-project/go-hamt-ipld/pull/63/commits/7eb4d1d2b32ef9a6b5ff5327c8b3252a07ca2f09). This is likely a more involved change than other implementations will have since in golang this change requires moving from builtin big.Int to an explicit byte slice.

### D
This proposal is to create a new method `SetIfAbsent` which takes a string key and a cbor marshalable value and returns a boolean and an error. The boolean return should be true if the key is unset in the HAMT before calling `SetIfAbsent` and false otherwise.

## Design Rationale

### A & B
These designs follow directly from understanding the inefficiencies of the current HAMT. They have only not been introduced sooner because they are breaking changes and carry implementation risk.

### C
Larger changes were considered to decouple the HAMT bitfield from the builtin go big.Int type's serialization. However these were dropped since go big.Int serialization is pervasive in filecoin chain state beyond HAMT data.

The expected value of bytes added to a node when a single bit is set is (4-1)/2 = 1.5 bytes, and only goes down as more bits are set.
As the bytes added are small there is consensus that the simplicity and canonicalization concerns outweight the small overhead.

To see more of the discussion look at the thread in the go-hamt-ipld issue [here](https://github.com/filecoin-project/go-hamt-ipld/issues/54)

### D
The go-hamt-ipld issue [here](https://github.com/filecoin-project/go-hamt-ipld/issues/75) examines several variants of the `SetIfAbsent` method. We could alternatively modify `Set` instead of adding a new call, however this would require changing every existing `Set` caller when moving to the new HAMT interface. Orthogonally we could also make the `Set`/`SetIfAbsent` interface more expressive either accepting a receiving parameter to fill with the previous value for a key as in `Get` or adding a callback parameter that could operate over the previous value for a key. These are reasonable changes but are more complex and the current motivating specs-actors use case does not need the additional expressiveness. They may make for good future changes.

## Backwards Compatibility

### A
This change is consensus breaking because it reduces the gas cost of HAMT Set and possibly Find operations. So running HAMT code with this feature will not result in the same state transitions as the existing hamt code. Therefore this change requires a network version update.

### B & C
These changes require modifying the serialized bytes of all HAMT nodes. This will require a state tree migration migrating all HAMT data.

### D
Adding this change to the HAMT is backwards compatible. Using it in actors code will require a network version upgrade.

## Test Cases

Test cases are / will be accompanying implementation

## Security Considerations
All significant implementation changes carry risk. On their own each sub proposal is a simple well understood change. Increased HAMT tests as well as existing validation practices are expected to be sufficient safeguards. 

## Incentive Considerations
On the whole this change should directly and indirectly decrease both real validation time and state storage cost as well as gas cost while otherwise maintaining the same behavior. It should be incentive compatible to accept this change for all parties in the network. It should not introduce changes to the protocol's incentive structure.

## Product Considerations
This change should directly and indirectly decrease the costs of state machine operations. This will not change any aspect of the network as a product other than the positive impacts of improved performance of existing behavior.

## Implementation
Sub proposal A implemented and optimistically merged to go-hamt-ipld [here](https://github.com/filecoin-project/go-hamt-ipld/pull/74)

Sub proposal B implemented and up for review in go-hamt-ipld [here](https://github.com/filecoin-project/go-hamt-ipld/pull/60)

Sub proposal C implemented and up for review in go-hamt-ipld [here](https://github.com/filecoin-project/go-hamt-ipld/pull/63)

Sub proposal D implementation pending