---
fip: "00XX"
title: Remove Batch Fee For Precommit, Lower BatchBalancer and Remove Gas-limited Constraints
author: irene (@irenegia), ZX (@zixuanzh), AX (@AxCortesCubero), rvagg (@rvagg)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1092
status: Draft
type: Technical
category: Core
created: 2024-12-19
---

# FIP-00XX: Remove Batch Fee For Precommit, Lower BatchBalancer and Remove Gas-limited Constraints

## Simple Summary
This FIP proposes to:
- Remove the batch fee from `PreCommitSectorBatch2` to incentivize batching during the precommit step;
- Revert `BATCH_BALANCER` to the original value of 2 nanoFIL to make aggregation rational for a larger range of base fee value with respect to today's network conditions.
- Remove some protocol constraints that are no longer necessary since the introduction of proper gas accounting.

## Abstract
BatchBalancer and the batch gas fee were introduced in [FIP13](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0013.md) for provecommit and later updated in [FIP24](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0024.md), where the fee was added to the precommit step as well. 
This mechanism makes batching precommit multiple sectors in one `PreCommitSectorBatch2` message and aggregating proofs for multiple sectors and post in one `ProveCommitSectors3` message rational (i.e., cost-effective) only when the base fee is above a given threshold (which depends on `batchBalancer`, other parameters used in the mechanism and the gas used). This FIP proposes to revert to no fee for precommit and lower the value of `batchBalancer` to 2 nanoFIL in order to have no BaseFee threshold for batching precommit of mutiple sectors in one `PreCommitSectorBatch2` message and a lower BaseFee threshold for aggregating proofs for provecommit.

## Change Motivation
Since August 2024, gas used for onboarding methods has been higher than in the past year (see [#1092](https://github.com/filecoin-project/FIPs/discussions/1092) for more details on data and causes).  A simple mechanism to reduce gas consumption is batching: at times of high demand for network gas, storage providers (SPs) should be incentivized to batch as much as possible for both precommit and provecommit.

Removal of gas-limited protocol constraints within this FIP is also proposed as a related set of changes; however, these changes are not the primary focus of this FIP. The removal of these constraints is proposed to simplify the protocol and allow the gas mechanism to be the primary constraint for the network.

### Precommit
Due to the batch fee, currently precommit batching is only rational when the base fee exceeds 0.09 nanoFIL. Removing this fee will eliminate this obstacle, enabling more batching and therefore gas saving. To have a rough estimate of the saving, we can compare two PreCommitSector messages posted by the same miner actor with little difference in the number of sectors when the message landed.
- [Msg 1](https://www.filutils.com/en/message/bafy2bzacebzacw3b7ymcwukk2uimahiebpke65utbfn3srgslzj5w3hh234x6): PreCommiSectorBatch2 for 1 sector : 16.7 M gas used
- [Msg 2](https://www.filutils.com/en/message/bafy2bzacebdqgivdbxzj25exae55j7vjasos45lvj4bzi6fj5oaya4rqwxrf6): PreCommitSectorBatch2 for 4 sectors):  18.6 M/ 4 =  4.6 M per sector (3.6x smaller)

### Provecommit
There are two options for `ProveCommitSector3`: (1) "simple" batching as in precommit (ie, one message for ≥ 2 sectors) where there is a porep proof for each sector in the batched message, and (2) aggregating proofs of multiple sectors and post in one message. 
Batching for provecommit is already rational (cost-effective), as the batch fee applies only to aggregated proofs (opposed to precommit, where the batch balancer applies to batching). 

On the other hand, aggregation is rational only when the base fee exceeds 0.065 nanoFIL. Lowering the value of BatchBalancer from 5 to 2 nanoFIL will reduce the crossover point to 0.026 nanoFIL, making the aggregation rational across a broader range of base fee values.

To have a rough estimate of the saving, we can compare these `ProveCommitSector3` messages posted by the same miner actor with little difference in the number of sectors when the message landed.
- [Msg 1](https://www.filutils.com/en/message/bafy2bzacebshpv7afwnxph6l4jnbpwpqnss3cboyfvlualfrjbox76hojjnlo): ProveCommitSectors3 for 1 sector: 225.5 M 
- [Msg 2](https://www.filutils.com/en/message/bafy2bzacebd7ftq5lk4ikuif4j3xfwiabmla5bek3kuhn3k6x3obufxyzrs6y): ProveCommitSectors3 for 4 sectors, batched (no aggregation): 412 M/4 = 103 M per sector (2.2x smaller)
- [Msg 3](https://www.filutils.com/en/message/bafy2bzacedezi6lm4warrfq2n6dxvpokowzt5isacbq2kojkz462yfpfq7lxm): ProveCommitSectors3 for 4 sectors, aggregated[^*]: 517.4 M/4 = 129.3 M per sector (1.7x smaller)

[^*]: In practice, aggregation is currently giving less gas saving respect to batching due to a bug causing single proofs to be charged an incorrect amount of gas units. So currently, batching is to be preferred with respect to aggregation. Once this code bug is fixed, batching will cost more gas units and aggregation would be the option with the largest gas unit saving per sector. 

### Gas-limited constraints

Various protocol constraints that were previously necessary when there was no gas applied on actor computation are no longer necessary since the introduction of proper gas accounting with FVM (see [FIP-0032](./fip-0032.md)). This FIP proposes to remove the following constraints as they are no longer necessary in practice due to the gas mechanism being the primary constraint for computation:

* `PRE_COMMIT_SECTOR_BATCH_MAX_SIZE`: The maximum number of sector pre-commitments in a single batch.
* `PROVE_REPLICA_UPDATES_MAX_SIZE`: The maximum number of sector replica updates in a single batch.
* `DECLARATIONS_MAX`: Maximum number of unique "declarations" in batch operations (i.e. terminations, faults, recoveries).

In most cases, users will be limited by the gas limit rather than these constraints ([`message execution failed: exit SysErrOutOfGas`](https://github.com/filecoin-project/lotus/issues/10612)). Removing these constraints will simplify the protocol and allow the gas mechanism to be the primary constraint for the network.

## Specification
- Remove the burning `aggregate_fee` from `PreCommitSectorBatch2`.
- Decrease `BATCH_BALANCER` value to 2 nanoFIL.
- Remove the following gas-limited constraints:
  - `PRE_COMMIT_SECTOR_BATCH_MAX_SIZE`
  - `PROVE_REPLICA_UPDATES_MAX_SIZE`
  - `DECLARATIONS_MAX`

## Design Rationale
Long-term solutions for reducing onboarding gas will focus on decreasing state storage gas costs (we estimated that state storage gas may get to  ~66% of the total cost for pcs3 messages with no deals) and optimizing state updates.  
This FIP takes an orthogonal approach by enhancing support for batching and aggregation at times of high demand, which are simple yet effective ways to free chain bandwidth immediately.  

This FIP also reduces state storage cost by batching. Much of this cost comes from updating state over and over, batching helps alleviate that significantly.

In the future, we envision stronger support for aggregation by potentially replacing the batch balancer mechanism from provecommit with alternate fees that align all participants  with the network's long-term health. For additional context, see https://github.com/filecoin-project/FIPs/discussions/557 and https://github.com/filecoin-project/FIPs/discussions/587.

## Backwards Compatibility
This FIP modifies actor behavior and will require a new Filecoin network version.

## Test Cases
- Certain test cases (similar to as FIP24)  may need to be adjusted when changing the BatchBalancer value.

## Security Considerations
This FIP does not affect underlying proofs or protocol security.

## Incentive Considerations
This proposal is expected to enhance the incentives for batching and aggregation, thereby reducing gas costs and improving the network's overall efficiency.

The current BatchBalancer of 5 nanoFIL was set in FIP24 more than three years ago and a lot has changed since then. With the current network parameters, the crossover network BaseFee when aggregating becomes rational for ProveCommit is around 0.065 nanoFIL. At equilibrium 0.065 nanoFIL, it is estimated that to onboard a 32GiB sector full of deals, it will cost around 3-5% of initial pledge in gas burn to onboard.

By lowering the BatchBalancer value, the network is incentivizing more aggregation at a lower equilibrium BaseFee value, thus freeing up more chain bandwidth. By reverting to the original BatchBalancer of 2 nanoFIL, the equilibrium network crossover BaseFee for ProveCommit (when aggregating for ProveCommit becomes rational) is at around 0.025 nanoFIL, incentivizing ProveCommit aggregation at a broader range of BaseFee values. In the medium term, however, BatchBalancer is intended to be replaced with an explicit proof fee at the time of onboarding.

Removal of gas-limited constraints will simplify the protocol and allow the gas mechanism to be the primary constraint for the network. This will allow the network to be more flexible and adapt to changing conditions.

## Product Considerations
From a product perspective, this FIP is expected to:
- Lower onboarding costs for SPs by removing barriers to precommit batching (e.g., precommit batch fee);
- Encouraging batching and aggregation reduces block space consumption, reducing the risk of higher base fee values;
- Simplify analysis and cost calculations for SPs by removing of precommit batch fee.
- Simplify the protocol by removing gas-limited constraints that are no longer necessary.

## Implementation
builtin-actors PRs:
* Remove batch fee for precommit and lower BatchBalancer (TBD)
* [Remove gas-limited constraints](https://github.com/filecoin-project/builtin-actors/pull/1586)

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
