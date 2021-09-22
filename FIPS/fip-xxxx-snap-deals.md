---
fip: XXXX
title: Snap Deals
author: @Kubuxu, @lucaniz, @nicola, @rosariogennaro, @irenegia
discussions-to: https://github.com/filecoin-project/FIPs/issues/145
status: Draft
type: Core
created: 2021-08-24
spec-sections: 
  - miner actors
  - lotus mining

---

## Simple Summary

A one-message protocol for updating any sector with new data without re-sealing.

## Abstract

Storage provider embeds deal data into existing sector replica with some unpredictable randomness by "xor"-ing.

The miner generates one message which proves that sector was updated with new data.

## Change Motivation

Since 90+% of sectors in the Filecoin Network are CC sectors, having a protocol that allows for updating CC sectors to store real data without incurring in a full re-sealing would massively improve our network in terms of the amount of real data stored through it. 

1. It would allow **decoupling sealing latency from deal-making speed** - offering storage clients an improved experience for how quickly their data can land in on-chain deals
2. It would **unlock the 8EiB of storage already committed to the Filecoin network** to be quickly used for deals - enabling a 100PiB+ client to make deals for their entire dataset with a single miner like [f0127595](https://filfox.info/en/address/f0127595) which already has 120PiB of committed capacity.
3. It makes **utilizing existing committed capacity much cheaper for miners** (since they’ve already invested the sealing cost), increasing the chances they pay clients to add FIL+ data to these sectors.

What this FIP does not support (see Future Work section):
* Deal updates
* Moving deals across sectors

## Specification

### Nomenclature
**SectorKeyCID** - on-chain commitment of CC sector replica

**UnsealedSectorCID** - commitment of deal data generated from PieceCIDs

**SealedSectorCID** - commitment of sector replica with deals embedded in it

**EncodingRands** - collection of **HashShards** randomness values used for encoding process

**Poseidon-128** - SNARK friendly hash function


### Parameters

**ChallengesNumber** = 1376 - number of challenges to be proven

**HashShards* = 512 - number of hashes used for randomness in encoding process


### One-messages Update Protocol
1. **Miner accepts and publishes storage deals (using PublishStorageDeals)**
2. **Miner updates an existing replica with deals**:
	1. Generate `EncodingRand = Poseidon-128(ComputeUnsealedCID(P1, P2, P3, ...), i)` for `i in [0, HashShards)`
	where `P1, P2, P3, ...` are pieces corresponding to deals that will included in this sector.
	2. Encode the deal data into existing replica using `newReplica[i] = Enc(sectorKey[i], data[i], EncodingRand[i * HashShards // NodeSectorSize)` function:
		- `newReplica` is the vector of `Fr` elements of the new replica
		- `sectorKey` is the vector of `Fr` elements of the CC sector replica data
		- `data` is the vector of `Fr` elements of the deals data ordered and padded as done in the sealing subroutine
		- `NodeSectorSize` is size of the sector in nodes (32 byte chunks)
	3. Compute SealedSectorCID of the `newReplica`.
3. **Miner produces a proof of sector update.**
	Generate a SNARK that proves:
	1. Generation of ChallengesNumber challenges in batches of 8:
		1. For `j=0..ChallengesNumber//8`, `[_, c[8*j+7], c[8*j+6], ..., , c[8*j] = Split-31bit(Poseidon-128(SealedSectorCID, j)`.
		The `Split-31bit` splits the 255bit output of Poseidon-128 hash into 8 31 bit chunks and discards 7 high bits.
		2. `c[i] = c[i] mod NodeSectorSize`
	2. For each challenge `i=0..ChallengesNumber`,  `c = c[i]`
		1. Encoding: the following we correcty computed: `newReplica[c] = Enc(sectorKey[c], data[c], Poseidon-128(UnsealedSectorCID, c*HashNumber//NodeSectorSize)`
		2. Inclusion proofs:
			1. `newReplica[c]` is the opening of `UpdatingSectorCID` at position `c`
			2. `sectorKey[c]` is the opening of `CommRLast` from `SealedSectorCID` at position `c`
			3. `data[c]` is the opening of `UnsealedSectorCID` at position `c`

4. **Miner publishes `Miner.ReplicaUpdate(SectorID, NewSealedSectorCID, deals []DealID, Proof)`**:
	1. Verify the proof of correct data update:
		1. Check that `SectorID` was originally CC sector, and fetch `SectorKey` or if that is null use `SealedSectorCID`.
		2. Check that `SectorID` has no deals active that are not included in the `deals` param.
		3. Check that all `deals` are either already in `SectorID` or are to be activated.
		3. Compute `NewUnsealedSectorCID` (CommD) based on DealIDs and deal table.
		6. Verify that `proof` is valid for using inputs: `NewSealedSectorCID`, `NewUnsealedSectorCID`, `SectorKey`.
	2. Activate new deals in `deals` array.
	3. If `SectorKeyCID` is null, set it to `SealedSectorCID`
	4. Update `SealedSectorCID` to `NewSealedSectorCID`
	5. Update `UnsealedSectorCID` to `NewUnsealedSectorCID`


### Algorithms

#### Encoding

The current encoding algorithm is the following:

`Enc(sectorKey[i], data[i], EncodingRand) = sectorKey[i] + data[i] * EncodingRand`

The Encoding function is cheap and allows for parallel encoding. 

#### Decoding

`Dec(sectorKey[i], replica[i], EncodingRand) = (replica[i] - sectorKey[i]) * (EncodingRand<sup>-1</sup>)`

The modular inverse of `dataRand` is computed only once per whole operation.

### Retrieving updated data from encoded replica

1. From the `replica`:
   2. Regenerate `sectorKey` by re-sealing the sector
   3. For each `i`: `Dec(sectorKey[i], replica[i], EncodingRand)`

#### Decoding replica to facilitate subsequent updates

`Dec2(replica[i], data[i], EncodingRand) = replica[i] - data[i] * EncodingRand`

## Design Rationale

### Parameters choice

* `ChallengeNumber`: 2220 - to facilitate required security factor with Fiat-Shamir (TODO expand in Security Considerations).
* `HashNumber`: 512 - to reach required spacegap fraction without neadlessly increasing the cost of conducting protocol (TODO explanation).

### Limitations

The update protocol is limited to CC sectors as the `SectorKey` commitment is only avaliable for sectors with no data. The SectorKey commitment is currently included as `CommRLast` commitment inside the on-chain `SealedSectorCID`  when the sector is CC. When the sector contains deals natively the `SealedSectorCID` includes only `CommRLast+Data` commitment.

## Backwards Compatibility


### Breaking immutability of sectors and deals

## Test Cases

TODO

## Security Considerations

### Loosing epsilon-Replication guarantees

This changes changes the security property of Filecoin. Retrievability of the files and space-hardness are still guaranteed. TODO: expand on this.

### Poseidon-128

Poseidon-128 is zk-SNARK friendly hash function which is already widely used in Filecoin protocol.
Both uses of Poseidon-128 include Domain Separation Tags such that the usage here does not clash with possible future usecases.

Domain Separation Tags used:
 - Encoding Randomness Generation: `XXXX`
 - Challenge Generation: `XXXX`

## Incentive Considerations

TODO

## Product Considerations

Snap Deals protocol significantly reduces the time needed for data to be included in a sector
and confirmed on-chian. The process was designed with cost for storage proviers in mind, 

## Implementation

- TODO: Initial Pledge should be updated in one of the new methods, we believe it should be PreCommit.
- TODO: How do we best represent deals in Declare update? Do we relist all the deals or we show a diff of deals?

## Future work

* DeclareDeals to support deal transfer: allow moving deals from sector to sector
* CapacityDeals: allow purchasing a capacity of the storage of a miner instead of the storage of a specific deal
* Update protocol that does not require to perform an operation on a full sector.
* DealUpdates: a license to terminate a deal in place for a new one (e.g. a user wants to update a portion of their files)

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
