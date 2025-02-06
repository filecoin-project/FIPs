---
fip: "00XX"
title: Removing Batch Balancer, Replacing It With a Per-sector Fee and Removing Gas-limited Constraints
author: irene (@irenegia),  AX (@AxCortesCubero), rvagg (@rvagg), molly (@momack2), kiran (@kkarrancsu)
Discussions-to: https://github.com/filecoin-project/FIPs/discussions/1092 and  https://github.com/filecoin-project/FIPs/discussions/1105 
status: Draft
type: Technical
category: Core
Created: 2025-02-04
---

# FIP-00XX: Removing Batch Balancer, Replacing It With a Per-sector Fee and Removing Gas-limited Constraints


## Simple Summary
This FIP proposes to:
 - Remove the batch fee from all precommit and provecommit methods to incentivize sector batching during the precommit step and proof aggregation during the provecommit step;
 - Introduce a per sector fee to replace the batch balancer cost structure with a more stable mechanism that supports the long-term economic sustainability of the Filecoin network;
 - Remove protocol constraints that are no longer necessary since the introduction of proper gas accounting.


## Abstract
This FIP consists of three changes:
 - First, a straightforward way to reduce gas consumption is through sector batching and proof aggregation. Storage providers (SPs) should be incentivized to batch sectors at precommit and aggregate proofs at prove commit as much as possible. Currently, the efficiency of these processes is governed by the batch balancer mechanism, which is tied to the base fee and comes with several limitations. This FIP proposes the removal of the batch balancer (see details below) to enable full adoption of batching and aggregation, thereby enhancing scalability and onboarding growth.
 - Secondly, the batch balancer was introduced to address a misalignment in the Filecoin economy. Beyond blockchain execution, the Filecoin network provides SPs with a storage-auditing service through on-chain verification of proofs. While gas fees primarily account for execution costs, there is no dedicated system that properly captures the network’s storage-auditing value. The batch balancer partially addressed this gap, although attempted to achieve value capture through the gas mechanism which is primarily a means of constraining chain validation costs. With the removal of the batch balancer, a replacement mechanism is needed. This FIP proposes a better, more effective system to achieve that goal (see details below).
 - Finally, this FIP also includes the removal of gas-limited protocol constraints which are no longer needed. However, these modifications are not the primary focus of the proposal. Eliminating these constraints aims to simplify the protocol, and remove any unintentional network growth constraints.


## Change Motivation

### Precommit batch fee removed
Due to the batch fee, currently precommit batching is only rational (ie, cost-effective) when the base fee exceeds 0.09 nanoFIL. Removing this fee will eliminate this obstacle, enabling more batching and therefore gas saving. 
To have a rough estimate of the saving, we can compare two PreCommitSector messages posted by the same miner actor with little difference in the number of sectors when the message landed.
- [Msg 1](https://www.filutils.com/en/message/bafy2bzacebzacw3b7ymcwukk2uimahiebpke65utbfn3srgslzj5w3hh234x6): PreCommiSectorBatch2 for 1 sector : 16.7 M gas used
- [Msg 2](https://www.filutils.com/en/message/bafy2bzacebdqgivdbxzj25exae55j7vjasos45lvj4bzi6fj5oaya4rqwxrf6): PreCommitSectorBatch2 for 4 sectors):  18.6 M/ 4 =  4.6 M per sector (3.6x smaller)


### Provecommit batch fee removed
There are two options for `ProveCommitSector3`: (1) "simple" batching as in precommit (ie, one message for ≥ 2 sectors) where there is a PoRep proof for each sector in the batched message, and (2) aggregating proofs of multiple sectors and post in one message. 
Batching for provecommit is already rational, as the batch fee applies only to aggregated proofs (opposed to precommit, where the batch balancer applies to batching). 
On the other hand, aggregation is rational only when the base fee exceeds 0.065 nanoFIL due to the batch fee applied to aggregation. Removing this fee too will eliminate this obstacle, enabling more proof aggregation and therefore gas saving. 

To have a rough estimate of the saving, we can compare these `ProveCommitSector3` messages posted by the same miner actor with little difference in the number of sectors when the message landed[^*].
- [Msg 1](https://www.filutils.com/en/message/bafy2bzacebshpv7afwnxph6l4jnbpwpqnss3cboyfvlualfrjbox76hojjnlo): ProveCommitSectors3 for 1 sector: 267.5 M 
- [Msg 2](https://www.filutils.com/en/message/bafy2bzacebd7ftq5lk4ikuif4j3xfwiabmla5bek3kuhn3k6x3obufxyzrs6y): ProveCommitSectors3 for 4 sectors, batched (no aggregation): 580 M/4 = 145 M per sector (1.85x smaller)
- [Msg 3](https://www.filutils.com/en/message/bafy2bzacedezi6lm4warrfq2n6dxvpokowzt5isacbq2kojkz462yfpfq7lxm): ProveCommitSectors3 for 4 sectors, aggregated: 517.4 M/4 = 129.3 M per sector (2x smaller)

[^*]:  A bug is currently causing single proofs to be charged an incorrect amount of gas units. So we added the missing units (42M per proof) to msg1 and msg2 in order to provide the future correct estimates (the bug is planned to be fixed in nv25).  See [here](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0076.md)


### Per-sector fee added
The batch balancer mechanism had several goals and effects. Among them, two key aspects were: (1) Creating a linear cost for onboarding storage in the presence of batching/aggregation and (2) Burning tokens to balance new token supply with network burn, ensuring value distribution among FIL holders and earners.
We propose a replacement mechanism that preserves these effects while adhering to the following design principles:
 - Simplify the system to improve predictability.
 - Preserve and align network value accrual.
 - Avoid additional onboarding rate limits.
 - Enable future optimizations in the network’s execution layer.

**Proposal Details**: We introduce a per-sector fee, whose value is proportional to a fixed fraction of the circulating supply and to the sector duration. To prevent this fee from becoming a significant upfront cost that could hinder onboarding, we propose daily payments instead of an upfront fee. Moreover, as a safety measure for the high-growth scenarios, we propose capping the daily payment at a fixed percentage of the daily expected per-sector block reward.

More in details: at provecommit time we compute the value 

				 dailyFee = k * CS(t)
where `k = 7.4 E-15` is a system constant and `t` is the sector activation epoch. Then, we cap it using the  `expected_day_reward` value that is currently already computed as part of the onchain sector info [link](https://github.com/filecoin-project/builtin-actors/blob/5aad41bfa29d8eab78f91eb5c82a03466c6062d2/actors/miner/src/types.rs#L447). That is, we compute:  

			dailyPayment = min (dailyFee,  m * expected_day_reward) 
where `m= 0.5` is another system constant. Then the daily payment is due everyday until sector expirationfor each new sector onboarded after this FIP is deployed. In particular:
- Even if a sector becomes faulty for the day, the payment is due. In other words, the dailyPayment is paid at windowPoSt time for all sectors in one the following state: active, faulty, recovered;
- The total fee per sector over its full sector lifetime is: `sectorFee = dailyPayment * sectorDurationInDays`. If a sector is terminated, the remaining of `sectorFee` gets computed and paid at termination (paid together with termination fee); 
- If a sector is extended or updated, the dailyFee is not changed but the cap is recompute considering the upated value of `expected_day_reward` (and therefore the dailyPayment is updated). The sector will keep paying dailyPayment for the extended lifetime.

### Gas-limited constraints

Various protocol constraints that were previously necessary when there was no gas applied on actor computation are no longer necessary since the introduction of proper gas accounting with FVM (see [FIP-0032](./fip-0032.md)). This FIP proposes to remove the following constraints as they are no longer necessary in practice due to the gas mechanism being the primary constraint for computation:

* `PRE_COMMIT_SECTOR_BATCH_MAX_SIZE`: The maximum number of sector pre-commitments in a single batch.
* `PROVE_REPLICA_UPDATES_MAX_SIZE`: The maximum number of sector replica updates in a single batch.
* `DECLARATIONS_MAX`: Maximum number of unique "declarations" in batch operations (i.e. terminations, faults, recoveries).

In most cases, users will be limited by the gas limit rather than these constraints ([`message execution failed: exit SysErrOutOfGas`](https://github.com/filecoin-project/lotus/issues/10612)). Removing these constraints will simplify the protocol and remove any unintentional network growth constraints.

## Specification

This FIP makes three main changes to the protocol:
1. Removes the batch balancer fee mechanism from sector pre-commit and prove-commit operations
2. Removes certain gas-limited protocol constraints that are no longer necessary
3. Introduces a new per-sector daily fee mechanism based on circulating supply and block rewards


### Storage power actor

The storage power actor will be used to record a daily average of the circulating supply. This is achieved by incrementing a running total of circulating supply per epoch through the existing cron call. Once every 2880 epochs this will be divided and recorded in an AMT as the average circulating supply for that day period. Records will be indexed starting from `0` and incrementing `1` per day (creating an optimal AMT structure).

The power actor will also store a new field, set on activation of this FIP to the activation epoch, to record the collection start epoch. This value will be used to quantise down any requested epoch to the daily average value.

```rust
pub struct State {
  // existing fields ...

  /// The epoch when average daily supply started being recorded. This is the activation epoch of
  /// FIP-XXXX and is used for quantising epochs to their daily average record in the daily_supply
  /// array.
  pub daily_supply_record_start: i64,

  /// A running total for the current 24 hour period, incremented on each call from cron, and used
  /// to record the average value for the previous 24 hour period once a day.
  pub daily_supply_total: TokenAmount,

  /// Average circulating supply for each 24 hour period since the start of recording as defined by
  /// daily_supply_record_start, indexed by day, starting from 0 as the first 24 hour period
  /// recorded after daily_supply_record_start and incrementing by 1 each day.
  pub daily_supply: Cid, // Array (AMT[TokenAmount])
}
```

In addition, a new method will be exposed to access the current root CID of the AMT so that another actor can load one or more arbitrary historical records. As the storage miner actor may need to look up many separate records when dealing with batches of sectors, it will be more efficient to pass the data structure rather than answer specific queries.

```rust
fn daily_supply_root(rt: &impl Runtime) -> Result<Cid, ActorError>
```

A helper wrapper for the AMT that can be shared amongst actors to easily convert arbitrary epochs to daily average values is suggested.

### Storage miner actor

#### Removal of gas-limited constraints

The following constants and their use will be removed:
  - `PRE_COMMIT_SECTOR_BATCH_MAX_SIZE` - used by `PreCommitSectorBatch2`
  - `PROVE_REPLICA_UPDATES_MAX_SIZE` - used by both `ProveReplicaUpdates` and `ProveReplicaUpdates3`
  - `DECLARATIONS_MAX` - used by `TerminateSectors`, `DeclareFaults` and `DeclareFaultsRecovered`

#### Removal of aggregate fee

- Remove the burning of `aggregate_fee` from `PreCommitSectorBatch2`.
- Remove the burning of `aggregate_fee` from `ProveCommitAggregate`, `ProveCommitSectorsNI`, `ProveCommitSectors3`
- Removal of `aggregate_fee` calculation methods and associated constants, including `ESTIMATED_SINGLE_PROVE_COMMIT_GAS_USAGE` and `ESTIMATED_SINGLE_PRE_COMMIT_GAS_USAGE`

#### Fee implementation

Fees are payable daily at WindowPoSt for the sectors being proven. As this operation aims to be gas-efficient, the introduction of a fee mechanism should not add unnecessary additional load `SubmitWindowedPoSt`. Since WindowPoSt addresses sectors grouped by partition, a total daily fee amount for an entire partition will be stored in the root of the partition's state. This value is summed across the partitions included in a successful `SubmitWindowedPoSt` message and deducted from the miner actor. No special handling is added for skipped sectors in a WindowPoSt.

TODO (should we do it here?): It is within WindowPoSt that the cap on the daily fee is enforced. The cap is calculated as a fixed percentage of the expected daily block reward. This is calculated by using the total power from storage power actor, and current epoch block reward from the reward actor combined with the QaP recorded for the partition.

```rust
pub struct Partition {
  // existing fields ...

  /// The total fee payable per day for this partition, this represents a sum of the daily fee
  /// amounts for all sectors in this partition.
  pub daily_fee: TokenAmount,
}
```

Fees are calculated for each sector at various points in their lifecycle and the `daily_fee` value in their assigned partition is updated accordingly. The fee is calculated as a fixed fraction of the circulating supply at the time of sector activation. The circulating supply value is taken from the record in the power actor for the day of sector activation; the last average circulating supply value recorded before the sector activation epoch is used. This same value can be looked up at any future point in time to calculate the fee for potential adjustments.

For each of `ProveCommitSectors3`, `ProveCommitAggregate` and `ProveCommitSectorsNI` the fee is for each sector committed is calculated at the time of the message and added to the existing `daily_fee` total recorded in the partition the sector is assigned to.

Faults have no impact on a partition's `daily_fee` value.

Early terminations, both automatic and manual, will result in a reduction of the partition's `daily_fee` value for the sectors being terminated. `daily_fee` is reduced by the daily fee recalculated for the sector by using the activation epoch and average circulating supply value for that epoch as described above. In this way, addition and removal of sectors from a partition will adjust the daily fee by the correct amount, resulting in no over or undercharging.

#### Alternative fee implementation

_This section is provided temporarily for discussion purposes and will either be removed or used to rework the above section once the final fee implementation is decided. Acceptance of this design will result in the removal of proposed changes to the storage power actor above._

_Description of `daily_fee` accumulation in the partition and its use on WindowPoSt remains the same._

The `SectorOnChainInfo` struct will be extended to include a new field `daily_fee` which will be used to store the daily fee for the sector. This value will be updated at the time of sector activation and will be used to calculate the daily fee for the sector for the duration of its lifetime. Due to the number of sectors already on chain and the expense of migrating to a new format to add this field, the existing block layout will continue to be supported, which is represented as a 15 element array, with one element per field of the struct. The new field will be added as the 16th element of the array. Loading and decoding any `SectorOnChainInfo` block will be able to handle both the old and new formats. Any writes by the builtin actors will strictly use the new format.

A future migration will be proposed to unify the format, however this is deferred until additional sector clean-up activities can take place to reduce the number of unused sectors on chain, thereby reducing the cost of migration.

```rust
pub struct SectorOnChainInfo {
  // existing fields ...

  /// The total fee payable per day for this sector. The value of this field is set at the time of
  /// sector activation and is used to calculate the daily fee for the sector for the duration of
  /// its lifetime.
  /// This field is not included in the serialised form of the struct prior to the activation of
  /// FIP-XXXX, and is added as the 16th element of the array after that point only for new sectors
  /// or sectors that are updated after that point. For old sectors, the value of this field will
  /// always be zero.
  pub daily_fee: TokenAmount,
}
```

Fees are calculated for each sector at various points in their lifecycle and the `daily_fee` value is stored in the sector's `SectorOnChainInfo` and the `daily_fee` value in their assigned partition is updated accordingly. The fee is calculated as a fixed fraction of the circulating supply at the time of sector activation. The circulating supply value is available at the time of sector onboarding as it is used for pledge calculation.

For each of `ProveCommitSectors3`, `ProveCommitAggregate` and `ProveCommitSectorsNI` the fee is for each sector committed is calculated at the time of the message.

Faults have no impact on a partition's `daily_fee` value.

Early terminations, both automatic and manual, will result in a reduction of the partition's `daily_fee` value for the sectors being terminated. `daily_fee` is reduced by the daily fee recalculated for the sector by using the activation epoch and average circulating supply value for that epoch as described above. In this way, addition and removal of sectors from a partition will adjust the daily fee by the correct amount, resulting in no over or undercharging.

## Design Rationale
We aimed for a design that is simple to understand and model, and relatively simple to implement. With this in mind, we explored the following fee structures:

- **Upfront Payment vs. Ongoing Payment**: The first offers better predictability, while the second reduces the risk of creating an entry barrier. With this FIP, we chose a hybrid approach that captures the benefits of both by computing the fee upfront for predictability, but allowing it to be paid daily over sector lifetime instead of as a lump sum upfront.

- **Flat Fee vs. Dynamic Fee**: A fixed per-sector fee provides predictability and consistency, while a fluctuating fee based on network congestion, onboarding rate, or other variables better captures value when the network is actively providing a service. We chose a model where the fee is a fixed fraction of a quantity that adjusts to economic conditions. We evaluated the following economic indicators for determining the per-sector fee: Initial Pledge (IP), per-sector Block Reward (BR) and Circulating Supply (CS). 
  - The IP-based fee was discarded to avoid complex system dependencies, as changes to IP in future FIPs could unintentionally impact the per-sector fee. 
  - The BR-based fee was discarded because the fee-to-reward ratio did not adjust properly to network growth, leading to high fees even when onboarding demand was low. See [here](https://github.com/filecoin-project/FIPs/blob/irenegia-removeBatchBalancer/resources/fip-replaceBatchBalancer/FIPxxxxAppendix.md) for more details.
  - CS was ultimately chosen because it normalizes fees relative to the Filecoin economy, ensuring both adaptability and predictability.  

We reached this conclusion through simulation-based analysis, modeling the impact of fees under different network conditions. Specifically, we evaluated multiple input trajectories: 0.5×, 0.75×, 1×, and 2× the current onboarding, renewal, and FIL+ rates. Since both renewals and FIL+ are near 100%, we capped them at their current maximum (see Fig. 1).
<div align="center"">
  <img src="https://github.com/user-attachments/assets/e4ac2327-e1bf-4512-8f7c-cee45a45218b" width="650">
  <p><em>Fig 1: Network state evolution for each input trajectory. 
</em></p>
</div>

For each trajectory, we analyzed the expected fee and related metrics over time. Fig. 2 presents these results for the CS-based fee, incorporating a cap at 50% of `expected_day_reward` as a safety measure in high-growth scenarios. Notably, Fig. 2 confirms that the CS-based fee proposed in this FIP offers the following key advantages:
- **Stable Economic Reference**: A fixed percentage of CS functions like a fixed USD fee if market cap remains stable, keeping costs predictable;
- **Adapts to Market Conditions**: If Filecoin’s valuation rises, fees increase in FIL terms, scaling with the economy. If the market stagnates, fees stay economically consistent.
<div align="center">
    <img src="https://github.com/user-attachments/assets/018fb429-de90-4a86-9c15-6c244a699487">
    <p><em>Figure 2: CS-based fee evolution as a function of various network metrics. Here we considered a daily payment that is a fixed % of CS-based and capped at 50% of `expected_day_reward` as a safety measure in high-growth scenarios.
</em></p>
</div>


## Backwards Compatibility
This FIP modifies actor behavior and will require a new Filecoin network version.

## Test Cases
TODO


## Security Considerations
This FIP does not affect underlying proofs or protocol security.

## Incentive Considerations

Filecoin’s network revenue model is currently tied to the gas usage, and the most amount of gas is used by storage onboarding methods. This creates an incentive misalignment, where economic considerations lead to an incentive to not optimize the gas usage of onboarding methods, as this could hurt overall network revenue. 

The Batch Balancer mechanism exemplifies this concept: batching and aggregating abilities were introduced to increase gas efficiency of onboarding methods, but the batch balancer mechanism restricted use of these abilities to when the network demand was high, to protect Filecoin’s economic interests.

This FIP fixes this incentive misalignment by disconnecting the network revenue from gas usage. The removal of the batch balancer allows for aggregation to occur at any level of demand regardless of network utilization rate (such as current levels of demand). We expect this to lead to a reduction of about ~30% in per-sector onboarding gas. This would in turn result in a drop in base fee, and therefore a drop in gas-based network revenue. 

The explicit per-sector fee introduced by this FIP allows us to remove the batch balancer, and support other future gas usage optimizations, without adding macroeconomic risk. 

The removal of batch balancer and associated reduction in gas fees are up-front improvements to SP costs designed to unblock and support faster data onboarding. This up-front cost-reduction is balanced by the per-sector fee that is charged gradually over the sector lifetime, starting at a small fraction of daily block rewards and adjusting dynamically based on network economic growth rate. 


## Product Considerations 
From a product perspective, this FIP is expected to:
- Decouple gas fees (blockspace costs) from service fees (storage-auditing costs): This separation creates a more resilient system, reducing sensitivity to base fee spikes and ensuring predictable and fair costs for SPs.
- Simplify cost analysis and calculations for SPs: The network will provide a smoother user experience by clearly distinguishing between congestion control (managed via base fees) and payments for services unrelated to congestion.
- Capture value for the storage-auditing service: By introducing a per-sector fee burn, the network can proportionally capture value based on storage demand.
- Ensure economic stability amid future optimizations: Improvements in proof mechanisms or onboarding throughput will no longer risk destabilizing the network’s economic alignment. This ensures the Filecoin protocol can lower costs for SPs while still capturing value for the network.
- Remove gas-limited constraints: Eliminating these unnecessary constraints simplifies the protocol and allows gas mechanisms to serve as the primary network constraint, making the system more adaptive and flexible to changing conditions.

## Implementation
builtin-actors PRs:
* Remove batch fee for precommit and lower BatchBalancer (TBD)
* Implement windowPoSt per sector fee (TBD)
* [Remove gas-limited constraints](https://github.com/filecoin-project/builtin-actors/pull/1586)

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).



