## Appendix 

This document describes simulations related to FIPxxxx: "Removing Batch Balancer, Replacing It With a Per-sector Fee and Removing Gas-limited Constraints".

### Simulation Methodology

#### MechaFIL Introduction
Simulations are conducted using the mechafil package, which is a Python implementation of a mechanistic model of the Filecoin economy.  The inputs to the simulation are:
- Raw byte onboarding (PiB/day)
- Renewal Rate (%) - the percentage of expiring power which is renewed
- Fil+ Rate (%) - the percentage of onboarded power which is deal power

Given a trajectory of inputs, the model will forecast the future state of the network, including network power, circulating supply, locked, pledge, and other related metrics.

Fig 1 shows the different onboarding trajectories that are simulated. Various input trajectories are considered - 0.5x, 0.75x, 1x, and 2x the current onboarding, renewal, and FIL+ rates.  
Renewals and FIL+ are capped at their current maximum, since both values are close to 100%. 
<div align="center"">
  <img src="https://github.com/user-attachments/assets/e4ac2327-e1bf-4512-8f7c-cee45a45218b" width="650">
  <p><em>Fig 1: Network state evolution for each input trajectory. 
</em></p>
</div>

### Proof Fees Modeling

#### Circulating Supply (CS) Based Fees
We can describe this fee as follows, for a sector onboarded at time t:

`sectorFee(t) = k1 * CS(t) * sectorDurationDay`

In the simulation, the sector duration is fixed to 540 days.

#### Block Reward (BR) Based Fees
We can describe this fee as follows, for a sector onboarded at time t:

`sectorFee(t) = k2 * (sum_{d=1, ...,540} sectorBlockReward(t,d) * FeeMultiplier(d)) `

In the above formulations: 
- FeeMultiplier represents the following multiplier function. 
<div align="center">
    <img src="https://github.com/user-attachments/assets/3fa1e42d-152b-4654-a20b-caaf7e73840f" width="400">
</div>
- k1 and  k2  represent two different scaling factors
- CS(t) is the circulating supply at time t 
- sectorBlockReward(t,d) is the per sector reward for a sector onboarded at time t during day d

### Simulations

To understand the effect of BR-based vs CS-based fees, we consider the following 4 metrics:
- Onboarding Fee / Sector;
- Onboarding fee per sector / Pledge per sector;
- Onboarding fee per sector / 1 day of BlockReward per sector;
- Cumulative onboarding fees that would be collected.

For each trajectory, we can show the expected fee and derivative metrics as a function of time. 
Fig 2a and 2b shows these metrics for the CS-based fee (with the cap at 50% expected_daily_reward only for Fig 2b). Fig. 3 here shows these metrics for the BR-based fee. 

<div align="center">
    <img src="https://github.com/user-attachments/assets/d74760eb-e5d9-431a-9dc5-5f29c0edcbd6">
    <p><em>Figure 2a: CS-based fee evolution as a function of various network metrics. The scaling factor k1 = 5.56 E-15 in the first row and k1= 7.4 E-15 in the second row.
</em></p>
</div>

<div align="center">
    <img src="https://github.com/user-attachments/assets/d69e6789-0423-4c51-ad0e-1d6a852ae708">
    <p><em>Figure 2b: CS-based fee evolution as a function of various network metrics. The scaling factor k1 = 5.56 E-15 in the first row and k1= 7.4 E-15 in the second row. The daily payment is also capped at 50% of expected_daily_reward  as a safety measure.
</em></p>
</div>

<div align="center">
    <img src="https://github.com/user-attachments/assets/c8387173-dcef-4eb1-bdd1-d84ceeff44a0">
    <p><em>Figure 3:  BR-based fee evolution as a function of various network metrics. The scaling factor k2 =1% in the first row and = 2% in the second row.
</em></p>
</div>




### Conclusions:
The Block Reward (BR, Fig 3) was ruled out because the fee-to-reward ratio did not exhibit the desired behavior—specifically, when network growth slowed, the ratio did not show any slowdown in the increase, which was not optimal. In particular, the total amount of fees burnt over time is less sensitive to the levels of onboarding demand, and there is a risk of fees being high, even when onboarding demand is low. 

Circulating supply (CS, Fig. 2a nad 2b) was chosen. CS is a good basis for the per-sector fee because it normalizes fees relative to the Filecoin economy, ensuring both adaptability and predictability.  More precisely:
- Stable Economic Reference: A fixed percentage of CS functions like a fixed USD fee if market cap remains stable, keeping costs predictable;
- Adapts to Market Conditions: If Filecoin’s valuation rises, fees increase in FIL terms, scaling with the economy. If the market stagnates, fees stay economically consistent.
