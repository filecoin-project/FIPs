---
fip: "0008"
title: Add ProveCommitSectorAggregated method to reduce on-chain congestion
author: Nicola (@nicola), Add others
discussions-to: https://github.com/filecoin-project/FIPs/issues/50
status: Draft
type: Technical
category: Core
created: 2021-17-02
spec-sections: 
  - section-systems.filecoin_mining.sector.lifecycle

---

## Simple Summary

<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->
Add a method for a miner to submit several sector prove commit messages in a single one.

## Abstract

<!--A short (~200 word) description of the technical issue being addressed.-->
On-chain proofs scale linearly with network growth. This leads to (1) blockchain being at capacity most of the time leading to high base fee, (2) chain capacity is currently limiting network growth.

The miner `ProveCommitSector` method only supports committing a single sector at a time.
It is both frequently executed and expensive.
This proposal adds a `ProveCommitSectorAggregated` method to amortize some of the costs across multiple sectors, removes some redundant but costly checks and drastically reduces per-sector proof size and verification times taking advantage of a novel cryptography result.


## Change Motivation

<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->

The miner `PreCommitSector` method only supports committing a single sector at a time. 
It's one of the two highest frequency methods observed on the chain at present (the other being `PreCommitSector`). 
High-growth miners commit sectors at rates exceeding 1 per epoch. 
It's also a relatively expensive method, with multiple internal sends and loading and storing state including:

- TODO: Add list of operations that could be batched

If miner operators implemented a relatively short aggregation period (a day), the `ProveCommitAggregated` method has the potential to reduce gas costs for:

- State operations: some of the costs listed above can be amortized across multiple sectors
- Proof verification: the gas used for proofs can scale sub-linearly with the growth of the network using a novel proof aggregation scheme.

## Specification

<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

### Actor changes

Add a new method `ProveCommitSectorAggregated` which supports a miner prove-committing a number of sectors all at once.
The parameters for this method are a list of prove-commit infos:

```
type ProveCommitSectorAggregatedParams {
    Sectors []*SectorPreCommitInfo
}
```

For the most part, semantics should be equivalent to invoking `ProveCommitSector` with each sector info in turn. Some notable changes include:

- TODO: list here the important changes

#### Failure handling

- If any predicate on the parameters fails, the call aborts (no change is persisted).
- If the miner has insufficient balance for all prove-commit pledge, the call aborts.

#### Scale and limits

The number of sectors that may be pre-committed in a single aggregation starts from 50 (TODO) and a maximum of 819 (TODO)

### Proof scheme changes

Protocol Labs research teams in collaboration with external researchers have worked on an improvement of the Inner Product Pairing result from [Bunz et al.](https://eprint.iacr.org/2019/1177.pdf).

In high level, the idea is the following: given some Groth16 proofs, one can generate a single proof that these were correctly aggregated.

Note the this type of aggregation sits on top of the existing SNARKs  that we do. In other words, there is no need for a new trusted setup.

A more detailed technical report on the new constructions can be found here (TODO).

#### Proofs API

TODO

#### Trusted Setup change

## Design Rationale

The existing `ProveCommitSector` method will not become redundant, since aggregation of smaller batches may not be efficient in terms of gas cost (proofs too big or too expensive to verify).
The method is left intact to support smooth operation through the upgrade period.

### Failure handling

Aborting on any precondition failure is chosen for simplicity. 
There is no good reason for submitting an invalid pre-commitment, so this should never happen for correctly-functioning miners. 
Aborting on failure will provide a clear indication that something is wrong, which might be overlooked by an operator otherwise.

An alternative could be to allow sectors in the aggregation to succeed or fail independently. 
In this case, the method should return a value indicating which sectors succeeded and which failed.
This would complicate both the actor and node implementations somewhat, though not unduly.

### Scale and limits

The bound on aggregation size is not intended to actually constrain a miner's behaviour, but limit the impact of potentially mistaken or malicious behaviour.
A miner may submit multiple batches in a single epoch to grow faster.


## Backwards Compatibility

This proposal introduces a new exported miner actor method, and thus changes the exported method API. 
While addition of a method may seem logically backwards compatible, it is difficult to retain the precise behaviour of an invocation to the (unallocated) method number before the method existed.
Thus, such changes must be delivered through a major version upgrade to the actors.

This proposal retains the existing non-batch `ProveCommitSector` method, so mining operations need not change workflows due to this proposal (but _should_ in order to enjoy the reduced gas costs).

## Test Cases

Test cases will accompany implementation.

## Security Considerations

All significant implementation changes carry risk.

The cryptography used is novel and is audited by TODO.

The trusted setup used is the Filecoin Powers of Tau and the ZCash Powers of Tau (TODO: add links)

## Incentive Considerations

This proposal amortizes per-sector costs for high-growth miners, providing an economy of scale. This same economy cannot be enjoyed by miners growing more slowly.

This may present a minor incentive against splitting a single physical operation into many miner actors (aka Sybils).

## Product Considerations

This proposal reduces the aggregate cost of committing new sectors to the Filecoin network. 

This will reduce miner costs overall, as well as reduce contention for chain transaction bandwidth that can crowd out other messages.

## Implementation

Implementation to follow discussion and acceptance of this proposal.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
