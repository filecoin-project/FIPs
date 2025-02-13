## Appendix 

This document describes simulations related to FIP-0100: "Removing Batch Balancer, Replacing It With a Per-sector Fee and Removing Gas-limited Constraints".

### Simulation Methodology

#### MechaFIL Introduction
Simulations are conducted using the mechafil package, which is a Python implementation of a mechanistic model of the Filecoin economy.  The inputs to the simulation are:
- Raw byte onboarding (PiB/day)
- Renewal Rate (%) - the percentage of expiring power which is renewed
- Fil+ Rate (%) - the percentage of onboarded power which is deal power

Given a trajectory of inputs, the model will forecast the future state of the network, including network power, circulating supply, locked, pledge, and other related metrics.

Figure 1 shows the different onboarding trajectories that are simulated. Various input trajectories are considered - 0.5x, 0.75x, 1x, and 2x the current onboarding, renewal, and FIL+ rates.  
Renewals and FIL+ are capped at their current maximum, since both values are close to 100%. 
<div align="center"">
  <img src="https://github.com/user-attachments/assets/e4ac2327-e1bf-4512-8f7c-cee45a45218b" width="650">
  <p><em>Figure 1: Network state evolution for each input trajectory. 
</em></p>
</div>

### Proof Fees Modeling

#### Circulating Supply (CS) Based Fees
We can describe this fee as follows, for a sector onboarded at time `t`:

`sectorFee(t) = k1 * CS(t) * sectorDurationDay`

In the simulation, the sector duration is fixed to 540 days.

#### Block Reward (BR) Based Fees
We can describe this fee as follows, for a sector onboarded at time `t`:

`sectorFee(t) = k2 * (sum_{d=1, ...,540} sectorBlockReward(t,d) * FeeMultiplier(d)) `

In the above formulations: 
- `k1` and  `k2`  represent two different scaling factors;
- `CS(t)` is the circulating supply at time `t`;
- `sectorBlockReward(t,d)` is the per sector reward for a sector onboarded at time `t` during day `d`;
- `FeeMultiplier` represents the following multiplier function. 
<div align="center">
    <img src="https://github.com/user-attachments/assets/3fa1e42d-152b-4654-a20b-caaf7e73840f" width="400">
</div>

### Simulations

#### Methodology 
To understand the effect of BR-based vs CS-based fees, we consider the following 4 metrics:
- Onboarding Fee / Sector;
- Onboarding fee per sector / Pledge per sector;
- Onboarding fee per sector / 1 day of BlockReward per sector;
- Cumulative onboarding fees that would be collected;
- Fil-on-FIL Returns (FoFR[^*]) estimate before the per sector fee; 
- FoFR after the per sector fee (including a savings estimate for removing batch balancer);
- The percentage change in FoFR from before per sector fee to after per sector fee.

[^*]:Note: FoFR is defined as `(Returns - Fees)/Pledge`

To account for the savings that will result from the removal of the batch balancer, we first must simulate the per-sector gas fee that SPs incur for onboarding sectors under the status-quo (i.e. no onboarding fee), and the expected savings from replacing the batch-balancer with the per sector fee. Predicting future network gas fees is extremely difficult, so projecting relative savings by switching to a more predictable fee structure is challenging. Our methodology is as follows, and we note that this is an approximation that can’t take into account the intricacies of how base_fee fluctuates, since our modeling is aggregated at the daily level rather than the epoch level. 

1. First, we estimate the per-sector gas fees under the status quo to be as follows: 
   - PreFip: `PreFIPPerSectorGasFee[d] = (x % CurrentDailyBurn)* feeRegimeScalar / (NumSectorsOnboarded[d]+NumSectorsRenewed[d])`
   - PostFIP: `PostFIPPerSectorGasFee[d] = F * PreFIPPerSectorGasFee[d]`

    The `feeRegimeScalar` models the effect of both base fee and economic bounds (ex limited FIL to onboard) and `x` models the fraction of total gas fees due to onboarding in the pre and post fip scenarios at different levels of onboarding.   `F` is the ratio of pre vs post-FIP gas savings that would be achieved. 

2. Next, we estimate how this factor `F` changes as a result of the onboarding fees and the removal of the batch balancer, as a function of the onboarding rate. The table below shows this.
  
  | Onboarding Rate (PiB/day) | Pre-FIP base fee | `x` | `feeRegimeScalar` | Post-FIP base fee | `F` | Justification |
  | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
  | **0 \- 2.5 PiB** | 100-1000 attoFil  | 50% | 1 | 100 \- 1000 attoFIL | 1 | When the daily RB onboarding is below 2.5PiB/day, no base fee spikes are caused in both scenarios (per and post FIP) |
  | **\> 2.5 PiB** | 0.01-0.1 nanoFIL  | 95% | 2 | 100 \-1000 attoFIL  | 0.0001 | When onboarding increases beyond 2.5PiB/day, base fee spikes from current levels, but the maximum burned will be limited by the available pledge to onboard new   sectors. We estimate that this factor will not exceed 2x. |

  Comments:
   - When onboarding increases beyond 2.5PiB/day, base fee spikes from current levels, but the maximum burned will be limited by the available pledge to onboard new sectors. We estimate that this factor will not exceed 2x.
   - Onboarding above 3.5 PiB can only happen through batching with current network conditions. In the Pre-FIP case, this means that >3.5 PiB onboarding can only happen if the base fee is equal or higher than the Batch Balancer crossover base fee (0.25 nanoFIL in the code).
   - Flag: the 2.0x growth case (the red line modeled below - equivalent to ~6 PiB daily onboarding) is likely *over-estimating* 1Y Sector ROI due to underestimating current gas costs during high-growth network onboarding, and therefore over-estimates the reduction in 1Y Sector ROI Delta.

#### Results      

For each trajectory, we can show the expected fee and derivative metrics as a function of time[^**]. 
Figure 2 shows these metrics for the CS-based fee (with the cap at 50% expected_daily_reward). Figure 3 here shows these metrics for the BR-based fee. 


<div align="center">
    <img src="https://github.com/user-attachments/assets/3f34e8df-74ff-457c-986d-3c7e50e2a7df">
    <p><em>Figure 2: CS-based fee evolution as a function of various network metrics. The scaling factor k1 = 5.56 E-15 in the first row and k1= 7.4 E-15 in the second row. The daily payment is also capped at 50% of expected_daily_reward  as a safety measure.
</em></p>
</div>

<div align="center">
    <img src="https://github.com/user-attachments/assets/dbbe4789-0412-48bc-a722-bc687fab8820">
    <p><em>Figure 3:  BR-based fee evolution as a function of various network metrics. The scaling factor k2 =1% in the first row and = 2% in the second row.
</em></p>
</div>


[^**]: The link to the code which generated the plots is here: https://github.com/CELtd/cel/blob/kiran/notebooks/proof_fees/fees10.ipynb

### Conclusions:
The Block Reward (BR, Figure 3) was ruled out because the fee-to-reward ratio did not exhibit the desired behavior—specifically, when network growth slowed, the ratio did not show any slowdown in the increase, which was not optimal. In particular, the total amount of fees burnt over time is less sensitive to the levels of onboarding demand, and there is a risk of fees being high, even when onboarding demand is low. 

Circulating supply (CS, Figure 2) was chosen. CS is a good basis for the per-sector fee because it normalizes fees relative to the Filecoin economy, ensuring both adaptability and predictability.  More precisely:
- Stable Economic Reference: A fixed percentage of CS functions like a fixed USD fee if market cap remains stable, keeping costs predictable;
- Adapts to Market Conditions: If Filecoin’s valuation rises, fees increase in FIL terms, scaling with the economy. If the market stagnates, fees stay economically consistent.
