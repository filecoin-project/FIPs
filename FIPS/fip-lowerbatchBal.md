---
fip: "00XX"
title: Remove Batch Fee For Precommit and Lower batchBalancer
author: irene, ZX, AX
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1092
status: Draft
type: Technical
category: Core
created: 2024-12-19
---

# FIP-00XX:Remove Batch Fee For Precommit and Lower batchBalancer

## Simple Summary
This FIP proposes to:
- Remove the batch fee from `PreCommitSectorBatch2` to incentivize batching during the precommit step;
- Revert `batchBalancer` to the original value of 2 nanoFIL to make aggregation rational for a larger range of base fee value with respect to today.


## Abstract
`batchBalancer` and the batch gas fee were introduced in [FIP13](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0013.md) for provecommit and later updated in [FIP24](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0024.md), where the fee was added to the precommit step as well. 
This mechanism makes batching in precommit and aggregation in provecommit rational (ie, cost-effective) only when the base fee is above a given threshold (which depends on `batchBalancer`, other parameters used in the mechanism and the gas used). This FIP proposes to revert to no fee for precommit and lower the value of `batchBalancer` to 2 nanoFIL in order to have no BaseFee threshold for batching precommit and a lower BaseFee threshold for aggregating provecommit.


## Change Motivation
Since August, gas used for onboarding methods has been higher than in the past year (see [#1092](https://github.com/filecoin-project/FIPs/discussions/1092) for more details on data and causes).  A simple mechanism to reduce gas consumption is batching: at times of high demand for network gas, storage providers (SPs) should be incentivized to batch as much as possible for both precommit and provecommit.  

### Precommit
Due to the batch fee, currently precommit batching is only rational when the base fee exceeds 0.09 nanoFIL. Removing this fee will eliminate this obstacle, enabling more batching and therefore gas saving. To have a rough estimate of the saving, we can compare two recent messages (no deal)
- [Msg 1](https://www.filutils.com/en/message/bafy2bzacedrbvzzcea3uwtqmas7zp5moxxpbceywukxux5fvgnbi2pj25hkjs): PreCommiSectorBatch2 for 1 sector : 16.5 M gas used
- [Msg 2](https://www.filutils.com/en/message/bafy2bzacebbc5pdzweouhvopgfvlc4trlips4ynszut774fxkv5omz3cicd3e): PreCommitSectorBatch2 for 4 sectors):  177 M/ 4 =  ~4.5 gas used (per sector)

Which indicates that batching can bring a ~70% of gas saving.



### Provecommit
At precommit there are two options: (1) "simple" batching as in precommit (ie, one message for ≥ 2 sectors) where there is a porep proof for each sector in the batch, and (2) batching with aggregation, where there is one unique aggregated porep proof.
Batching for provecommit is already rational (cost-effective), as the batch fee applies only to aggregated proofs (opposed to precommit, where the batch balancer applies to batching). 

On the other hand, aggregation is rational only when the base fee exceeds 0.065 nanoFIL. Lowering the value of `batchBalancer` from 5 to 2 nanoFIL will reduce the crossover point to 0.026 nanoFIL, making the aggregation rational across a broader range of base fee values.

To have a rough estimate of the gas saving, we compared these messages (no deals)
- [Msg 1](https://www.filutils.com/en/message/bafy2bzaceaddryxumxg35givyt7pe745wlsmrlrx7bj4sdb56nho4akyi5tzu): ProveCommitSectors3 for 1 sector (no deals): 78.5M 
- [Msg 2](https://www.filutils.com/en/message/bafy2bzaceah7m6jzravjoswo2pljzit36euu3sgz5jzbnpkcfp23b76texiv6): ProveCommitSectors3 for 4 sectors, batched (no aggregation): 96.M/4 = 24M per sector 
- [Msg 3](https://www.filutils.com/en/message/bafy2bzacedeh74ds4x4l5nlfahmlvwn4obfukhgqnf6rxlaargvsm56sljune): ProveCommitSectors3 for 4 sectors, aggregated[^*]: 217M/4 = 54M per sector 

[^*]: In practice, aggregation is currently giving less gas saving respect to batching due to a bug causing single proofs to be charged an incorrect amount of gas units. So currently, batching is to be preferred with respect to aggregation. Once this code bug is fixed, batching will cost more gas units and aggregation would be the option with the largest gas unit saving per sector. 


## Specification
- Remove the burning `aggregate_fee` from `PreCommitSectorBatch2`.
- Decrease **BatchBalancer** value to 2 nanoFIL.


## Design Rationale
Long-term solutions for reducing onboarding gas will focus on decreasing state storage gas costs (we estimated that state storage gas may get to  ~66% of the total cost for pcs3 messages with no deals) and optimizing state updates.  
This FIP takes an orthogonal approach by enhancing support for batching and aggregation at times of high demand, which are simple yet effective ways to free chain bandwidth immediately.  

This FIP also reduces state storage cost by batching. Much of this cost comes from updating state over and over, batching helps alleviate that significantly.

In the future, we envision stronger support for aggregation by potentially replacing the batch balancer mechanism from provecommit with alternate fees that align all participants  with the network's long-term health. For additional context, see https://github.com/filecoin-project/FIPs/discussions/557 and https://github.com/filecoin-project/FIPs/discussions/587.



## Backwards Compatibility
This FIP modifies actor behavior and will require a new Filecoin network version.



## Test Cases
- Certain test cases (similar to as FIP24)  may need to be adjusted when changing the batchBalancer value.



## Security Considerations
This FIP does not affect underlying proofs or protocol security.



## Incentive Considerations
This proposal is expected to enhance the incentives for batching and aggregation, thereby reducing gas costs and improving the network's overall efficiency.

The current batchBalancer of 5 nanoFIL was set in FIP24 more than three years ago and a lot has changed since then. With the current network parameters, the crossover network BaseFee when aggregating becomes rational for ProveCommit is around 0.065 nanoFIL. At equilibrium 0.065 nanoFIL, it is estimated that to onboard a 32GiB sector full of deals, it will cost around 3-5% of initial pledge in gas burn to onboard.

By lowering the BatchBalancer value, the network is incentivizing more aggregation at a lower equilibrium BaseFee value, thus freeing up more chain bandwidth. By reverting to the original batchBalancer of 2 nanoFIL, the equilibrium network crossover BaseFee for ProveCommit (when aggregating for ProveCommit becomes rational) is at around 0.025 nanoFIL, incentivizing ProveCommit aggregation at a broader range of BaseFee values. In the medium term, however, BatchBalancer is intended to be replaced with an explicit proof fee at the time of onboarding. 


## Product Considerations
From a product perspective, this FIP is expected to:
- By removing barriers to precommit batching (e.g., precommit batch proof fees), SPs will have lower onboarding costs;
- Encouraging batching and aggregation reduces block space consumption, reducing the risk of higher base fee values;
- The removal of precommit aggregated proof fees simplifies analyst and cost calculations for SPs.



## Implementation
Specs-actors PR: TODO

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
