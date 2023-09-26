---
fip: "00xx"
title: Add ProveReplicaUpdatesAggregated method to reduce on-chain congestion
author: nemo (@cryptonemo), Jake (@DrPeterVanNostrand)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/752
status: draft
type: Technical
category: Core
created: 2023-09-26
spec-sections: 
  - section-systems.filecoin_mining.sector.lifecycle

---

## Simple Summary

Add a method for a miner to submit several sector prove replica updates messages in a single one.

## Abstract

On-chain proofs scale linearly with network growth. This leads to (1) blockchain
being at capacity most of the time leading to high base fee, (2) chain capacity
is currently limiting network growth.

The miner `ProveReplicaUpdates` method only supports committing a single sector update at
a time.  This proposal adds a way for miners to post multiple `ProveReplicaUpdates`s at once in an aggregated fashion
using a `ProveReplicaUpdatesAggregated` method. This method amortizes some of the costs
across multiple sector data updates, and similar to FIP-0013 (ProvedCommitSectorAggregated), verification times can take
advantage of a novel cryptography result. This proposal allows many sectors to have data updates in them activated at once when the aggregated message is posted to the chain.


## Change Motivation

The miner `ProveReplicaUpdates` method only supports committing a single sector at
a time.  While it's not one of the most frequent messages on the chain, it is believed to be the case that it is too expensive in the current form to use.

Aggregated proof verification allows for more sector update commitments to be proven in
less time which will reduce processing time and therefore gas cost per prove
replica update. Verification time and size of an aggregated proof scales logarithmically
with the number of proofs being included.

## Specification

<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

### Actor changes

Add a new method `ProveReplicaUpdatesAggregated` which supports a miner
prove-committing a number of sector updates all at once.  The parameters for this
method are ???:

```
struct ProveReplicaUpdateAggregateParams {
   Sectors:                     []UpdateManifest
   AggregateProof:              []byte // Before aggregation, concatenate proofs
   UpdateProofType:             RegisteredUpdateProof
   AggregateProofType:          RegisteredAggregateProof
   VerifiedAllocationClaims:    []{} // Must be empty
   RequireActivationSuccess:    bool
   RequireNotificationSuccess:  bool
}
```

#### Failure handling

FIXME?

- If any predicate on the parameters fails, the call aborts (no change is persisted).
- If the miner has insufficient balance for all prove-commit pledge, the call aborts.

#### Scale and limits

**TODO:** how should the maximum aggregation limit be determined? 

The number of sectors that may be proven in a single aggregation is a minimum of 3 and a maximum of **TODO**.

#### Gas calculations

Similar to existing PoRep gas charges, gas values are determined from empirical measurements of aggregate proof validation on representative hardware.

Aggregate proofs must be generated for a power of two number of Groth16 proofs; because each Sector Upgrade proof contains sixteen Groth16 proofs, aggregated Sector Upgrade proofs are padded to contain the nearest power of two number of Groth16 proofs. See the "Proof scheme changes" section in [FIP-0013](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0013.md#proof-scheme-changes) for a discussion on aggregate proof padding.

The gas cost of aggregate proof verification grows both linearly and step-wise in the number of Sector Upgrade proofs aggregated (counted prior to proof padding). The linear growth occurring for each Sector Upgrade proof aggregated and the step-wise growth occurs when the number of Groth16 proofs aggregated exceeds a power of two.

The gas table below associates ranges of aggregated Sector Upgrade proofs with their total step-wise gas cost. The total gas cost for verifying an aggregate proof of `n` Sector Upgrade proofs is the sum of `n`'s linear and step-wise gas costs: `n * gas_per_proof + gas_table(n)`.

##### 32 GiB Gas Cost

Gas cost per Sector Upgrade proof aggregated: 80,000 gas

Total step-wise gas cost for ranges of Sector Upgrade proofs aggregated:

| SnapDeals Proofs | Groth16 Proofs |    Gas     |
| -----------------|----------------|------------|
|        3-8       |     48-128     | 86,500,000 |
|       11-128     |    144-2048    | 91,300,000 |
|      129-256     |   2064-4096    | 92,500,000 |
|      257-512     |   4112-8192    | 99,000,000 |

##### 64 GiB Gas Cost

Gas cost per Sector Upgrade proof aggregated: 80,000 gas

Total step-wise gas cost for ranges of Sector Upgrade proofs aggregated:

| SnapDeals Proofs | Groth16 Proofs |    Gas     |
| -----------------|----------------|------------|
|       3-8        |     48-128     | 86,500,000 |
|       9-128      |    144-2048    | 92,500,000 |
|     129-256      |   2064-4096    | 94,000,000 |
|     257-512      |   4112-8192    | 99,500,000 |

#### Batch Gas Charge

Currently, **GasUsed * BaseFee** is burned for every message. We can achieve the requirements described in [Incentive Considerations](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0013.md#incentive-considerations) by charging an additional proportional gas cost to an aggregated batch of proofs, and by balancing their gas costs with a minimum gas fee. Three concepts need to be introduced:
- **BatchGasCharge** - the network fee for adding batched proofs
- **BatchBalancer** - a minimum gas fee for BatchGasCharge
- **BatchDiscount** - a heavy discount for aggregated proofs, which also benefits other messages

The following charge is calculated for each **BatchProveCommit** message.

```
func PayBatchGasCharge(numProofsBatched, BaseFee) {
// Cryptoecon Params (need to be updated if verification benchmarks change)
BatchDiscount = 1/20 unitless
BatchBalancer = 2 nanoFIL
SingleProofGasUsage = 65733296.73

// Calculating BatchGasCharge
numProofsBatched = <# of proofs in this batched operation>
BatchGasFee = Max(BatchBalancer, BaseFee)
BatchGasCharge = BatchGasFee * SingleProofGasUsage *  numProofsBatched * BatchDiscount

// Pay for the batch
PayNetFee(BatchGasCharge) // this can be a msg.Send to f99. Does not affect BaseFee
// normal gas for the verification computation is paid as usual (using & affecting BaseFee)
}
```

Implications and rough estimates for this function are described in [Batch Incentive Alignment](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0013.md#batch-incentive-alignment).

#### State Migrations

Neither changes to the state schema of any actors nor changes to the fields of existing actors are required to make this change. Therefore a state migration is not needed.


### Proof scheme changes

See FIP-0013 for more details on the proof scheme changes.


#### Proofs API


##### Aggregation

The proofs aggregation procedure expects the following inputs:

```rust
pub fn aggregate_empty_sector_update_proofs(
    registered_proof: RegisteredEmptySectorUpdateProof,
    registered_aggregation: RegisteredAggregationProof,
    sector_update_proofs: &[EmptySectorUpdateProof],
    sector_update_inputs: &[SectorUpdateProofInputs],
    aggregate_version: groth16::aggregate::AggregateVersion,
) -> Result<AggregateSnarkProof>;
```

The `sector_update_inputs` are a slice of structs logically appearing like this in the rust language.

```
pub struct SectorUpdateProofInputs {
    pub comm_r_old: Commitment,
    pub comm_r_new: Commitment,
    pub comm_d_new: Commitment,
}
```

Within the SectorUpdateProofInputs struct, the elements are as follows:

The `comm_r_old` is the commitment to the sector's previous replica.
The `comm_r_new` is the commitment to the sector's current replica.
The `comm_d_new` is the commitment to the sector's current data.

Since the `sector_update_inputs` are a slice, they are ordered to match the order of the proofs slice provided.  However, this does NOT mean that they are required to be vectors of the same length.  For test sector sizes, they may end up being the same length because they are proven in a single partition -- but for production sector sizes, the partition count will not be one.  Instead, the number of elements in the `sector_update_proofs` vector will be the number of partitions * the number of the proofs.

**Requirements**: The scheme can only aggregate a power of two number of proofs
currently. Although there might be some ways to alleviate that requirement, we
currently pad the number of input proofs to match a power of two. Thanks to the
logarithmic nature of the scheme, performance is still very much acceptable.

Padding is currently _naive_ in the sense that if the passed in count of seal proofs is not a power of 2, we arbitrarily take the last proof and duplicate it until the count is the next power of 2.  The single exception is when the proof count is 1.  In this case, we duplicate it since the aggregation algorithm cannot work with a single proof.

##### Verification

The proofs verification procedure expects the following inputs:

pub fn verify_aggregate_sector_update_proofs(
    registered_proof: RegisteredEmptySectorUpdateProof,
    registered_aggregation: RegisteredAggregationProof,
    aggregate_proof_bytes: AggregateSnarkProof,
    inputs: &[SectorUpdateProofInputs],
    sector_update_inputs: Vec<Vec<Fr>>,
    aggregate_version: groth16::aggregate::AggregateVersion,
) -> Result<bool>;
```

The `inputs` are an ordered list of SectorUpdateProofInputs (described above)..

The `sector_update_inputs` are an ordered list of inputs which *must* match the order of the `sector_update_inputs` passed into `aggregate_empty_sector_update_proofs`, but in a flattened manner.  First, to retrieve the `sector_update_inputs` for a single sector, you can call this:

```rust
pub fn get_sector_update_inputs(
    registered_proof: RegisteredEmptySectorUpdateProof,
    registered_aggregation: RegisteredAggregationProof,
    comm_r_old: Commitment,
    comm_r_new: Commitment,
    comm_d_new: Commitment,
) -> Result<Vec<Vec<Fr>>> { 
```

As an example, if `aggregate_empty_sector_update_proofs` is called with the `sector_update_inputs` of Sector 1 and Sector 2 (where that order is important), we would want to compile the `sector_update_inputs` for verification as follows (pseudo-code for readability):

```rust
let sector_update_inputs: Vec<Vec<Fr>> = Vec::new();
sector_update_inputs.extend(get_sector_update_inputs(..., comm_r_old_sector_one, ...));
sector_update_inputs.extend(get_sector_update_inputs(..., comm_r_old_sector_two, ...));
```

What this example code does is flattens all of the individual proof sector update inputs into a single list, while properly maintaining the exact ordering matching the `sector_update_inputs` order going into `aggregate_empty_sector_update_proofs`.  When compiled like this, the `sector_update_inputs` will be in the exact format required for the `verify_aggregate_sector_update_proofs` API call.

Similar to aggregation, padding for verification is currently also _naive_. If the passed in count of proof input sets (while noting that the inputs are a linear list of equally sized input sets) is not a power of 2, we arbitrarily take the last set of inputs and duplicate it until the count is the next power of 2.  Again, the single exception is when the input count is 1.  In this case, we duplicate it since the verification algorithm cannot work with a single proof or input.


#### Proofs format 

See FIP-0013 for more details about the proofs format, as it is the same in this case.

## Design Rationale

The existing `ProveReplicaUpdates` method will not become redundant, since
aggregation of smaller batches may not be efficient in terms of gas cost (proofs
too big or too expensive to verify).  The method is left intact to support
smooth operation through the upgrade period.

### Failure handling

Aborting on any precondition failure is chosen for simplicity. 
Submitting an invalid prove commitment should never happen for correctly-functioning miners.  Aborting on failure will provide
a clear indication that something is wrong, which might be overlooked by an operator otherwise.

### Scale and limits

Each aggregated proof is bounded at 819 sector updates. The motivation for the bound on aggregation size is as follows:

- to limit the impact of potentially mistaken or malicious behaviour.  
- to gradually increase the scalability, to have time to observe how the network
  is growing with this new method.
- to ensure the gas savings are equally accessible to small miners with a sealing rate as low as 1TB/day

A miner may submit multiple batches in a single epoch to grow faster.

## Backwards Compatibility

This proposal introduces a new exported miner actor method, and thus changes the
exported method API.  While addition of a method may seem logically backwards
compatible, it is difficult to retain the precise behaviour of an invocation to
the (unallocated) method number before the method existed.  Thus, such changes
must be delivered through a major version upgrade to the actors.

This proposal retains the existing non-batch `ProveReplicaUpdates` method, so
mining operations need not change workflows due to this proposal (but _should_
in order to enjoy the reduced gas costs).

## Test Cases

Test cases will accompany implementation. Suggested scenarios include:

TBD

## Security Considerations

All significant implementation changes carry risk.

The core cryptographic techniques come from the [Bunz et
al.](https://eprint.iacr.org/2019/1177.pdf) paper from 2019 with strong security
proofs.  Our protocol is a derivation of this paper that is able to use the
already existing powers of tau and with increased performance. The paper is also
accompanied by formal security proofs in the same framework as the original
paper. The trusted setup used is the Filecoin Powers of Tau and the ZCash Powers
of Tau: the full key is generated thanks to this
[tool](https://github.com/nikkolasg/taupipp). The cryptographic implementation
is being audited and a report will be made available soon.

It should be noted that all use of SnarkPack aggregation referenced is
limited to [SnarkPack
V2](https://github.com/filecoin-project/core-devs/blob/master/Network%20Upgrades/v16.md)
and not the initial implementation of SnarkPack.  SnarkPack V2 is the
only version of SnarkPack still used in the protocol today.

## Incentive Considerations

Requirements. The cryptoeconomics of this FIP are similar to that of FIP-0013 require balancing a number of different goals and constraints.  Please consult FIP-0013 for more information.

### Batch Incentive Alignment

FIXME:

Given the implementation described in [Batch Gas Charge](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0013.md#batch-gas-charge), we achieve the following benefits:

- **BatchDiscount** and **BatchBalancer** are set to balance the power between small and large miners, and align participants' incentives with the long term health and success of the network. 
- By adding a **BatchGasCharge**, large players are paying proportional network transaction fees to the network based on the amount of storage that they are adding without affecting the underlying **GasUsage** or **BaseFee**. 
- By using a separate gas lane, the gas savings are passed as a big cost reduction to other messages, likely reducing the **BaseFee**.
- **BatchBalancer** establishes a regulating feedback process in the gas market to keep the **BaseFee** low for other operations but still meaningful in network transaction fees for batch commits. When the **BaseFee** is lower than **BatchBalancer * BatchDiscount**, some miners may find it more attractive to submit commit messages for individual proofs. When the **BaseFee** approaches **BatchBalancer * BatchDiscount**, miners may switch to batch commit messages to take advantage of the cost savings. In turn, this reduces load on the **BaseFee**.
- **BaseFee** spiking attacks are not neutralized, but are more expensive to mount, as (a) most of the chain throughput will move into aggregation, making it much more expensive for an attacker to increase and sustain the base fee, and (b) it is even more expensive for large miners to mount such an attack while growing their own storage.

**Rough Estimates.** (these are ballpark estimates and are likely wrong -- make your own models and measurements)

- With **BatchDiscount = 1/20** and **BatchBalancer = 2 nFIL**, we hope **BaseFee** will reduce from current avg **(1-2 nFIL)** to ~ **0.15 nFIL** with present message distributions plus the increases in storage onboarding throughput.
- With **BaseFee ~ 0.15 nFIL**, **PublishStorageDeals** could cost about **7 mFIL**. (down from 182 mFIL)
- Amortized unit **ProveCommit** gas costs may drop below **5 - 10 mFIL** (down from **50 - 100 mFIL**).

To illustrate the balancing dynamic of **BatchBalancer** and **BatchDiscount** at work, here are the unit network fees for a 32GiB sector at different BaseFee levels. Note that unit storage network fees may be halved when 64GiB sectors are used.

At a network BaseFee of 0.01 nanoFIL, unit economics is in favor of adding single proofs to the network.

<img width="681" alt="0.01nFIL" src="https://user-images.githubusercontent.com/16908497/119754607-5944f380-bed3-11eb-80c3-2082197efb3b.png">

As BaseFee increases to 0.1 nFIL, unit sector network fee for a single proof catches up to that of aggregated proofs.

<img width="680" alt="0.1nFIL" src="https://user-images.githubusercontent.com/16908497/119754633-6366f200-bed3-11eb-9a1c-ef86bfa57d92.png">

A crossover in the unit economics happens at around 0.15nFIL where miners are incentivized to take advantage of proof aggregation to free up more chain capacity. This will thus create a damping force on the BaseFee. 

<img width="685" alt="0.15nFIL" src="https://user-images.githubusercontent.com/16908497/119754760-7c6fa300-bed3-11eb-806a-c59f70941298.png">

In the hypothetical event when the BaseFee continues to rise to 1 nFIL or 2 nFIL (which is considered low today), miners are strongly incentivized to aggregate and take advantage of the savings that proof aggregation brings.

<img width="675" alt="1nFIL" src="https://user-images.githubusercontent.com/16908497/119754793-872a3800-bed3-11eb-9b0b-7e0fafe54d13.png">
<img width="692" alt="2nFIL" src="https://user-images.githubusercontent.com/16908497/119754857-a1641600-bed3-11eb-910b-37dcfa1e4787.png">

In aggregate, daily network fee spend grows as the network grows in size. With Single Proofs, it is impossible for the network to grow at >40PiB/day and maintain a 0.2nFIL BaseFee due to the constraint on chain capacity. Batch Proofs, however, enable the network to grow at > 800PiB/day.

 
## Product Considerations

This proposal reduces the aggregate cost of committing new sector data to the
Filecoin network. 

This will reduce miner costs overall, as well as reduce contention for chain
transaction bandwidth that can crowd out other messages. It unlocks a
larger data update rate for the Filecoin network.

## Implementation

* Cryptographic implementation is currently located on the `feat-ipp2` of the bellperson [repo](https://github.com/filecoin-project/bellperson/tree/feat-ipp2/src/groth16/aggregate)
* Integration between Lotus and crypto-land can be found in [rust-fil-proofs](https://github.com/filecoin-project/rust-fil-proofs/tree/agg-snapdeals) and the FFI [here](TBD).
* Actors changes are in progress here: TBD
* Lotus integration putting everything together is in progress here: TBD

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
