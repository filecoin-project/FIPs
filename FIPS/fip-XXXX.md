---
fip: "XXXX"
title: Deprecate FIL+ and Fund Services via Block Reward Split
author: Irene Giacomelli (@irenegia), Axel  Cortes Cubero (@AxCortesCubero), Micheal Madoff (@decentramike)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1249
status: Draft
type: Technical
category: Core
created: 2026-06-03
---

# Solstice: Deprecate FIL+ and Fund Services via Block Reward Split

## Simple Summary

This FIP deprecates the Filecoin Plus (FIL+) datacap minting and allocation system and replaces it with the following 2-step mechanism:

- **At L1 level, all PoRep sectors are the same:** All new sectors onboarded from the activation epoch onward automatically receive 10x QAP over the sector lifetime. The QAP gain will be realized immediately upon sector onboarding, regardless of the sector's content. Initial pledge mechanism is not changed.
- **Block reward split**: At every epoch, block reward minted is explicitly split into three unequal shares:
  - a. *Consensus Reward Share* ((1−α) of block rewards): flows directly to the winning miner, as today. This is the incentive for consensus security.
  - b. *Service Reward Allocation* (α\_floor of block rewards): flows to a new FEVM actor (Service Reward Actor) that funds the Service Orchestrators to support storage services. This replaces the implicit datacap-based split with an explicit, predictable mechanism.
  - c. *Burn* ((α − α\_floor) of block rewards): the gap between the service budget and the proven allocation is burned, creating deflationary pressure and enforcing fiscal discipline.

α (the service budget rate) follows a continuous linear ramp from 5% to 50% over approximately 9 quarters. α\_floor (the allocation rate) is a revenue-gated step function that starts at 10% after a bootstrap quarter and can increase by 5 pp per quarter if on-chain deal revenue clears a public, verifiable, programmatic threshold. If the revenue gate fails, α\_floor stays unchanged and the gap between α and α\_floor burns.

## Abstract

The current incentive system (FIL+) successfully created network capacity but failed to fully support service creation and real demand fit to paying customers bringing revenue into the Filecoin ecosystem. Emerging initiatives such as the services in the recently launched Filecoin Onchain Cloud (FOC) try to act on this and expand the possible demand fit of Filecoin, but can not be supported by the current incentive system. For this we want to propose a change to the block reward and sector valuation mechanism to support the network's evolution from a storage-capacity onboarding phase to a service-oriented economy. How? Via 3 main changes:

1. **Deprecate datacap** minting and the FIL+ allocation system and simply consider all the sectors having the same QAP Power at the L1 (consensus) level. In particular, all sectors onboarded from the activation epoch onward automatically gain 10x QAP for the sector lifetime. The QAP gain will be realized immediately upon sector onboarding, regardless of the sector's content. The initial pledge formula remains unchanged by this FIP, SPs are still required to lock the same amount of FIL for sectors utilizing datacap as they do currently.

2. **Block reward split with gated allocation and burn:** Once datacap is removed, a replacement mechanism reserves part of each block reward for service activity that creates value for the Filecoin economy. At each block reward issuance, a fraction α is removed from the miner's consensus reward. α follows a continuous, deterministic linear ramp from 5 % to 50 %. Of the removed portion, only α_floor, the "allocation rate", is sent to the **Service Rewards Actor** (a new FEVM actor) to fund the service economy; the remainder (α − α_floor) is burned. α_floor starts at 10 % after a bootstrap quarter and can step up by 5 pp per quarter, but only if on-chain deal revenue clears a revenue target. No action is required from the storage provider; the split is unconditional and applies to all new block rewards.

3. **Service Orchestrator model:** The Service Rewards Actor forwards received tokens to the Service Orchestrator, which are the go-to-market layer between Filecoin's on-chain service infrastructure and client demand and deploy funds to generate onchian deal revenue.

## Motivation

Filecoin Plus was designed to direct a fraction of block rewards toward storage service, and in particular toward storage in PoRep sectors of genuinely useful data. At the high level, Fil+ and datacap are a mechanism to implicitly create a dynamic split of the block reward (storage mining allocation) between consensus incentives and service incentives based on market forces (ie, driven by the demand from clients).

In practice, its fundamental limitation (ie, the impossibility of programmatically detecting "*useful data*") forced the system to rely on an extensive human-review pipeline: root key holders, allocators, datacap minting, compliance checks, and ongoing governance. This dependency creates several problems: it slows down the onboarding process for new clients, increases governance overhead, and makes the system vulnerable to gaming, where high Fil+ activity does not correlate with a high volume of legitimate data in deals (ie, fake client demand). See [Discussion #1176](https://github.com/filecoin-project/FIPs/discussions/1176). Therefore, today the implicit block reward split via datacap causes substantial network resources to be spent on sectors delivering limited ongoing client value.

This proposal resolves that tension by **shifting the signal** from upfront data and demand classification to demonstrated service delivery and demand response. Rather than trying to predict which data/service is valuable and when demand is real to allocate block reward, a fraction α of each block reward is removed from the miner's consensus reward. Of that, only α_floor is sent to the Service Rewards Actor, which forwards the allocation to the Service Orchestrator to deploy those funds and generate on-chain deal revenue. The gap (α − α_floor) is burned. α_floor can grow only when on-chain revenue clears a target, tying the allocation directly to demonstrated demand rather than upfront classification

This initiative also represents a significant opportunity to **simplify the L1** protocol over the long term. While deprecating the existing Fil+ system may require up to 18 months, the final outcome will be a simpler and more predictable L1 and tokenomics. By decoupling consensus and service economics, we get a system where PoRep can exist for consensus security and services can use whatever proving system the market demands rather than requiring PoRep as the only pathway to block reward-linked service provision.

#### Could we just remove FIL+ and let the market work?

Removing FIL+ would support more onboarding and allow the block reward to function as an indirect subsidy for service provision (e.g., a SP can offer lower prices because they earn from mining). However, this action would eliminate a crucial **protocol-level mechanism for encouraging the transition to a service-oriented economy**. While one might argue that genuine paying clients negate the need for this support, the reality is that current *client payments are often too small compared to the cost gap* of storing real data versus engaging in pure mining activities. Without an incentive exclusively dedicated to service, SPs would naturally prioritize pure consensus mining without providing value-creating services. Therefore, reserving a portion of the block reward for services is not merely an economic lever; it is a way to define the **network's identity**. Filecoin's fundamental mission is to be a storage service network, differentiating it from a generic network that simply uses storage. Achieving this mission will ultimately benefit all participants.

#### Why a continuous ramp up for alpha?

Why not pick a single fixed α and leave it there? The main reason is to create headroom for a growing service allocation. α sets the ceiling: the maximum that can flow to services once demand is proven. Starting at 5 % and ramping to 50 % ensures the protocol makes room gradually rather than forcing a single large cut to consensus rewards. If α were fixed too low, α_floor would eventually hit the ceiling and the service economy could not grow further; if fixed too high from the start, miners face an unnecessarily large immediate reduction in consensus rewards. The ramp balances both risks, and as a side effect, a predetermined schedule gives builders a known trajectory to invest against, rather than hoping for future governance votes to expand the ceiling.

#### Why the Revenue Gate and Burn Mechanism?

α determines how much leaves consensus, but how much actually funds services is governed by α_floor and the revenue gate.

- *Don’t spend without proof*. The Service Orchestrators receive what the service economy has proven it deserves. The allocation rate (α_floor) can only step up when on-chain deal revenue clears a verifiable target. If revenue falls short, α_floor stays unchanged and the Orchestrators continue receiving at the previously proven rate.

- *Burn what isn’t allocated*. The gap between α (what leaves consensus) and α_floor (what is actually allocated) burns. Why burn rather than leaving it in the consensus share? Because continuing to reduce the consensus share has meaningful benefits for the broader Filecoin economy: both through deflationary pressure and as a signal to attract serious service providers. 

## Specification (WIP)

WARNING: This section is currently a WIP, not ready for review! It contains the math formulans and parameters for alpha and alplha_floor but not the actual spec for the acot code changes!

### 1. Datacap Deprecation

The deprecation path for datacap will follow these simple transition rules. After the upgrade epoch:

1. No new datacap will be minted (→ revert `addVerifiedClients`);
2. Existing datacap is not touched:
   - Existing (ie, minted before the upgrade and currently owned by a client) datacap can still be transformed in allocations and these can still be claimed by an SP to get 10x QAP;
   - Existing (ie, created before the upgrade) allocations can still be claimed by SPs;
3. Extensions of allocations (existing or new) will not be permitted;
4. Existing sectors with allocations/QAP will not be touched;

**Actor code changes:**

The rules written above translate at the actor code level in this way:

- Disable minting facilities for DataCap
  - Revert methods: `add_verifier`, `remove_verifier`, `add_verified_client`, `extend_claim_terms` (maybe)
  - In a migration set `state.root_key = f099` and `state.verifiers = {}`
  - Revert `mint` on the DataCap actor
  - Set up test-only Allocation creation facilities to allow for continued testing of Allocation → Claim system (as it remains).
- Remove RKH
  - Less necessary as we are removing the authorisation of RKH in the above task
  - In migration, remove signers for RKH multisig
- All new sectors get assigned 10x QAP by default.
- Snapdeal (TODO)

### 2. Block Reward Split

#### 2.1 Alpha Ramp (ComputeAlpha)

α follows a continuous linear ramp from `ALPHA_START` to `ALPHA_CAP` over `RAMP_DURATION_QUARTERS` quarters. The ramp is deterministic and not gated.

**Constants:**

```
ALPHA_START              = 0.05       // 5%, initial service budget rate
ALPHA_CAP                = 0.50       // 50%, maximum service budget rate
ALPHA_FLOOR_STEP         = 0.05       // 5 pp step-up per gate pass
ALPHA_FLOOR_INITIAL      = 0.10       // 10%, alpha_floor set at end of Q1
RAMP_DURATION_QUARTERS   = 9          // quarters to reach ALPHA_CAP
EPOCHS_PER_QUARTER       = 259_200    // 90 * EPOCHS_PER_DAY
```

**Function:**

```
func ComputeAlpha(e Epoch, e0 Epoch) -> Rational:
    elapsed = e - e0
    ramp_epochs = RAMP_DURATION_QUARTERS * EPOCHS_PER_QUARTER    // 2,332,800

    if elapsed >= ramp_epochs:
        return ALPHA_CAP

    return ALPHA_START + (ALPHA_CAP - ALPHA_START) * elapsed / ramp_epochs
```

This is equivalent to: α(e) = min(0.50, 0.05 + 0.45 × (e − e₀) / (9 × 259,200))

| Quarter | Epoch offset | α (approx.) |
| ------: | -----------: | ----------: |
| Launch  |            0 |          5% |
| End Q1  |      259,200 |         10% |
| End Q2  |      518,400 |         15% |
| End Q3  |      777,600 |         20% |
| End Q4  |    1,036,800 |         25% |
| End Q5  |    1,296,000 |         30% |
| End Q6  |    1,555,200 |         35% |
| End Q7  |    1,814,400 |         40% |
| End Q8  |    2,073,600 |         45% |
| End Q9  |    2,332,800 |    50% (cap)|

#### 2.2 Alpha\_floor and Revenue-Gated Allocation

α\_floor is the fraction of block reward actually allocated to the Service Orchestrator. The gap (α − α\_floor) is burned. α\_floor is a step function that can only increase at quarter boundaries, and only if on-chain deal revenue clears a target.

**Constants:**

```
ALPHA_FLOOR_STEP         = 0.05       // 5 pp step-up per gate pass
ALPHA_FLOOR_INITIAL      = 0.10       // 10%, alpha_floor set at end of Q1
BETA_BASE                = [TBD]      // revenue target multiplier at initial alpha_floor
BETA_CAP                 = [TBD]      // revenue target multiplier at terminal alpha_floor
BETA_K                   = [TBD]      // ramp shape exponent (1 = linear)
```

**ComputeAlphaFloor**

α\_floor evolves differently in Q1 (bootstrap) vs. Q2 onward:

```
func ComputeAlphaFloor(e Epoch, state RewardState) -> Rational:
    quarter = (e - state.service_activation_epoch) / EPOCHS_PER_QUARTER

    if quarter == 0:
        // Q1 bootstrap: alpha_floor tracks alpha (no burn during Q1)
        return ComputeAlpha(e, state.service_activation_epoch)

    // Q2 onward: alpha_floor is a step function,
    // updated only by QuarterlyGateCheck (see below).
    return state.alpha_floor
```

At the end of Q1, alpha\_floor is set to `ALPHA_FLOOR_INITIAL` (0.10). From Q2 onward, it can step up by `ALPHA_FLOOR_STEP` (5 pp) per quarter if the revenue gate passes.

**ComputeBeta (Revenue Target Multiplier)**

β is the revenue target multiplier in the gate formula: `DealRevenue(Q) >= β × Allocation(Q-1)`. It determines how much on-chain deal revenue the service economy must generate per unit of allocation to unlock the next alpha\_floor step-up.

```
BETA_BASE = [TBD]      // starting multiplier (at alpha_floor = ALPHA_FLOOR_INITIAL)
BETA_CAP  = [TBD]      // terminal multiplier (at alpha_floor = ALPHA_CAP)
BETA_K    = [TBD]      // ramp shape exponent
```

```
func ComputeBeta(alpha_floor Rational) -> Rational:
    t = (alpha_floor - ALPHA_FLOOR_INITIAL) / (ALPHA_CAP - ALPHA_FLOOR_INITIAL)
    t = clamp(t, 0, 1)
    return BETA_BASE + (BETA_CAP - BETA_BASE) * t^BETA_K
```

**QuarterlyGateCheck**

Triggered once per quarter from Q2 onward. Compares on-chain deal revenue against the target and either steps up alpha\_floor or leaves it unchanged:

```
func QuarterlyGateCheck(Q uint64):
    // 1. Read on-chain deal revenue for the quarter just ended
    measured = MeasuredDealRevenue(Q)   // TODO

    // 2. Read current alpha_floor from the reward actor
    alpha_floor = rt.send(REWARD_ACTOR_ADDR, GET_ALPHA_FLOOR_METHOD).alpha_floor

    // 3. Compute the revenue target
    prev_allocation = alpha_floor * TotalBlockRewards(Q - 1)
    target = ComputeBeta(alpha_floor) * prev_allocation

    // 4. Gate decision
    if measured >= target:
        new_floor = min(alpha_floor + ALPHA_FLOOR_STEP,
                        ComputeAlpha(rt.curr_epoch(), activation_epoch))
        rt.send(REWARD_ACTOR_ADDR, UPDATE_ALPHA_FLOOR_METHOD,
                UpdateAlphaFloorParams { new_alpha_floor: new_floor })
    // else: gate fails, alpha_floor unchanged
```

`MeasuredDealRevenue(Q)`: sum of all deal payments settled through Filecoin Pay during quarter Q. TODO

`TotalBlockRewards(Q-1)`: sum of all block rewards minted during quarter Q-1. Computable in the reward actor.

**Trigger mechanism.** `QuarterlyGateCheck` must execute exactly once per quarter boundary via an automated, time-bound mechanism.TODO

#### 2.3 Actor Code Changes and BR-split Mechanism

At every epoch, the reward actor computes three values from `alpha` and `alpha_floor` and sends each to a different destination:

| Value | Formula | Sent to |
| ----- | ------- | ------- |
| Consensus reward | (1 − α) × BR | Winning miner |
| Service allocation | α\_floor × BR | Service Rewards Actor |
| Burn | (α − α\_floor) × BR | Burnt Funds Actor |

```
func DistributeBlockReward(e Epoch, BR TokenAmount, state RewardState):
    // 1. Compute alpha and alpha_floor
    alpha       = ComputeAlpha(e, state.service_activation_epoch)
    alpha_floor = ComputeAlphaFloor(e, state)

    // 2. Three-way split
    consensus_reward = (1 - alpha) * BR
    allocation       = alpha_floor * BR
    burn_amount      = (alpha - alpha_floor) * BR

    // 3. Send to three destinations
    rt.send_simple(BURNT_FUNDS_ACTOR_ADDR, METHOD_SEND, burn_amount)

    err = rt.send_simple(ServiceRewardsActorAddress, METHOD_SEND, allocation)
    if err != nil:
        // Fallback: burn allocation too. Funds never revert to consensus.
        rt.send_simple(BURNT_FUNDS_ACTOR_ADDR, METHOD_SEND, allocation)

    rt.send_simple(miner_addr, APPLY_REWARDS_METHOD,
                   ApplyRewardParams { reward: consensus_reward, penalty })
```

**Failure fallback:** If the Service Rewards Actor send fails, the allocation is burned — matching the existing pattern where miner send failure also burns. The three-way split is unconditional: a failing Service Rewards Actor cannot inflate consensus rewards.

### 3. Service Reward Actor

The Service Reward Actor is implemented as a SAFE wallet deployed as an FEVM actor (f4/f40 address), rather than a new built-in system actor. Its state schema is defined in Section 2 above. 

TODO

### 4. Service Rewards Allocation

Sections 2.1 to 2.4 fix how much of each block reward reaches the Service Reward Actor and how the quarterly gate and the burn discipline that share. This section specifies the other half: who controls the actor, what they are accountable for, and how control evolves from a single named operator to competitive and then permissionless entry.

#### 4.1 The Service Orchestrator Role

A Service Orchestrator is the go-to-market layer between Filecoin's on-chain service infrastructure and client demand. It controls the Service Reward Actor, the FEVM wallet that receives the allocation each epoch (Section 3), and deploys those funds to convert protocol subsidy into on-chain paid deal revenue.

The Orchestrator originates storage deals across one or more FOC service operators, structures pricing including subsidized rates during bootstrapping, matches clients with qualified storage providers, and manages client relationships through the deal lifecycle. FOC operators run the on-chain contracts and handle technical delivery. The Orchestrator owns commercial conversion.

Its authority stops at the wallet. The Orchestrator does not set consensus parameters, change the block reward split, or run the quarterly gate. Those are fixed in Sections 2 and 3. Its one protocol-level obligation is to generate the on-chain deal revenue that clears the gate.


#### 4.2 Accountability

The Orchestrator is measured on a single outcome: on-chain paid deal revenue settled through Filecoin Pay during the quarter, the `MeasuredDealRevenue` defined in Section 2.2. The gate there sets the bar as a multiple of the previous quarter's allocation, lenient while the allocation rate is small and rising toward the cap as it grows. Outperformance near the cap requires a service economy that is genuinely scaling.

Spending scope is outcome-defined. Any activity that drives on-chain deal revenue is eligible, and the protocol does not enumerate permitted line items. The gate is the only constraint: if deployed funds do not clear the target, the allocation rate holds and the unallocated share burns, as specified in Sections 2.2 and 2.3. The protocol measures outcomes. The Orchestrator chooses tactics.

The Orchestrator commits to weekly spend disclosure by category, an opening operating plan published before the bootstrap quarter, and an end-of-quarter retrospective covering pipeline volume, client acquisition, deal diversity, and the ratio of subsidized to organic revenue. These reports inform community evaluation and calibrate Phase 2. They do not feed the gate, which reads only settled revenue.

#### 4.3 Phased Deployment

Control evolves over three phases. Each transition requires its own FIP.

**Phase 1 (this FIP).** A single Orchestrator is named and given control of the Service Reward Actor. The Phase 1 Orchestrator is a purpose-built service function drawing on contributors from across Filecoin ecosystem organizations, with the Filecoin Foundation as fiscal agent for operational expediency. The first quarter is the ungated bootstrap quarter described in Section 2.2: the allocation rate tracks the budget rate, the full budget reaches the actor, and nothing burns. This gives the Orchestrator runway to stand up operations and build deal flow before the gate activates at the second-quarter boundary. Because there is only one Orchestrator, settled network revenue and the Orchestrator's output are the same thing, so no per-deal attribution is needed yet.

**Phase 2 (competitive).** Multiple Orchestrators each control a share of the allocation and are independently accountable for converting it into deal revenue. Phase 2 depends on capabilities that do not exist at launch: on-chain attribution that links revenue back to a specific Orchestrator, allocation accounting at the Orchestrator level, an application path that does not rely on incumbent cooperation, and a community audit process. The Phase 2 FIP must also decide whether the gate stays system-level or adds a gate per Orchestrator. A system-level gate is simpler but lets a strong Orchestrator carry a weak one. Per-Orchestrator gates sharpen accountability at the cost of parallel attribution and more complex burn logic.

**Phase 3 (permissionless).** Registration opens to any entity that meets published deposit and capability thresholds, with no further FIP approval and allocation driven by on-chain performance. Phase 3 becomes viable once the service economy sustains itself: when Filecoin Pay fee revenue exceeds the service allocation, the allocation formula has held stable for an extended period, and the on-chain registration and deposit contracts are deployed and tested. At that point the allocation behaves as a rebate against fees the network already collects. The protocol supplies the funding and the metric; the market supplies the operators.

**Recommended Transition Criteria** (to be confirmed in future FIPs)

| Transition | Prerequisites | Metrics |
| ---------- | ------------- | ------- |
| Phase 1 → Phase 2 | On-chain deal attribution, standardized reporting, application path, community audit process | Gate cleared 2+ consecutive quarters; 3+ qualified Orchestrator candidates |
| Phase 2 → Phase 3 | Allocation formula stable, on-chain registration contracts deployed, per-Orchestrator gating resolved | Filecoin Pay fee revenue exceeds α\_floor × BR; formula stable 4+ quarters |

## Design Rationale

### Alternative Approaches Considered

The design process focused on finding a simpler and more effective replacement for datacap as a mechanism for splitting storage mining block rewards into two parts: a consensus incentive component and a service incentive component. Key questions shaped the decision.

**Question 1: Should the split be opt-in or universal?**

Datacap is historically an opt-in feature, nominally client-demand driven. We evaluated whether to preserve that opt-in nature or move to a universal split:

- **Option A, Opt-in fee:** An SP pays an optional fee, proportional to the per-sector block reward, to earn enhanced QAP. Paying the fee also confers a small advantage in the market.[^1] The fee funds the subsidy mechanism (ie, the fevm actor). The key advantage is a *dynamic* split: the fund grows proportionally to SP willingness to participate in the market, creating a market-responsive feedback loop. The disadvantages, ultimately decisive, are implementation complexity (sectors that paid the fee must be tracked and the flag used in market incentive logic), reduced flexibility, and fund size uncertainty (harder to model expected inflows for network and pool planning).

- **Option B, Block Reward split (this FIP):** A fixed fraction α of every block reward is automatically diverted to the fevm actor. This is simpler to implement, universally applicable across all proving systems, and cleanly decouples consensus economics from service economics. The known trade-off is a more static split, it does not self-adjust in response to market activity. This is accepted as a reasonable trade-off for the gains in simplicity, predictability, and implementability.

[^1]: For example, in Option A the fevm actor could implement the rule that says that paying the fee is a prerequisite to be considered for an SPs eligible to the subsidized deals.

**Question 2: Should the split apply to all sectors or only newly onboarded ones?**

Once the BR-redirect approach was chosen, a second question arose: should the split apply to block rewards from all active sectors, or only from sectors onboarded after the activation epoch?

- **New sectors only:** Given the current low onboarding rate, limiting the split to new sectors would require differentiating sectors at minting time, add implementation complexity, and produce a very slow ramp-up. The network would wait a long time to see any meaningful effect on the subsidy fund. Given that the network needs clear and visible signals of directional change quickly, this was deemed insufficient.

- **All sectors (chosen approach):** Applying the split to all active sectors is faster to take effect, simpler to implement, and produces an immediate, predictable subsidy fund inflow. The main concern raised was fairness to existing CC sectors; however, CC sectors currently represent less than 15% of the network, and SnapDeals remains available as a path for those operators to transition into deal-carrying sectors and benefit from market activity.

**Question 3: Why not use the f090 mining reserve (~283M FIL)?**

The mining reserve (f090) is intended for "growth of the Filecoin economy" and is technically available. However, f090 is a finite, non-renewable pool. Once depleted, the service economy would need an alternative funding source anyway. A block reward split creates a sustainable, ongoing mechanism tied directly to protocol issuance: as long as the network mints, the service economy is funded. It also avoids the governance overhead of unlocking reserve draws and does not require expanding total issuance beyond what the protocol already emits. The BR split addresses the incentive problem at the existing issuance layer itself — the mining allocation was always implicitly intended to fund both consensus security and storage utility; this FIP makes that distinction explicit.

**Question 4: Why not a per-deal sales commission instead of a BR split?**

Commission and rebate models were evaluated. They work well once a strong customer pipeline exists, they're reactive, rewarding deals after they happen. However, Filecoin is still in the phase where ecosystem teams need proactive funding to bootstrap demand: client acquisition, POCs, migrations, and infrastructure investment that precedes deal flow. A commission model also partially reinvents datacap, you need some kind of voucher or token associated with the sales pipeline to attach to deals, reintroducing complexity. Once the pipeline is self-sustaining, moving toward simpler commission/rebate mechanisms is the intended direction (see Phase 3: Permissionless).

### Parameter Choices and Calibration

**Starting α = 5%.** We start small. At 5%, the daily cost for SP mining blocks (~0.00175 FIL for 10 TiB) is less than the cost of purchasing datacap at 5 FIL/TiB amortized over 5 years (~0.0025 FIL/day).

**Cap at 50%.** The cap ensures that half of block rewards always flow to consensus incentives. This is a pragmatic compromise: ambitious enough to signal long-term commitment, conservative enough to guarantee consensus security funding.

**Ramp duration = 9 quarters (~2.25 years).** This gives the service economy enough time to prove itself through the gate mechanism before α reaches meaningful levels. At quarter 4, α ≈ 25%, by then, the gate must have passed at least 3 times to keep α\_floor tracking, providing a natural check.

**Step size = 5 pp per gate pass.** Matches the quarterly α increment (~5 pp per quarter). If every gate passes, α\_floor tracks α with at most a one-quarter lag. If a gate fails, the gap (and burn) grows by 5 pp that quarter.

**β range (0.5x → 3.0x).** At early α\_floor (10%), the revenue target is lenient: 0.5× the previous quarter's allocation. As α\_floor grows and the Orchestrator receives more funds, the bar rises to 3× — demanding increasing capital efficiency. Linear interpolation avoids cliff effects.

Live explorer to test parameters: https://irenegia.github.io/FIP-discussion-1249-design-explorer/

### Why 10x to New Sectors

Currently, ~83% of sectors have datacap, meaning 10x power. Giving 10x to all new sectors is the smoothest way to transition to a world where, at the L1 level, every sector counts equally for block reward purposes.

The alternatives are:

1. Give 1x to new sectors and wait for existing 10x sectors to expire (no extensions allowed). This is slow and unfair to new sectors during the transition period (in practice, nobody would onboard new sectors under these conditions).

2. Give 1x to new sectors and simultaneously collapse QAP by reassigning 1x to all existing 10x (datacap) sectors. From a power distribution perspective, the outcome is similar to what this FIP proposes. However, this feels like a harder hit on SPs, and it also carries unknown side effects on pledge and circulating supply (eg, what happens to locked tokens when a sector's QAP is forcibly reduced?). These unknowns make this option harder to reason about and riskier to implement.

3. Daybreak proposal [Discussion #1238](https://github.com/filecoin-project/FIPs/discussions/1238), linearly decreasing multiplier. Similar to point 2 with the cons of reducing total locked FIL in the short/medium term.

## Backwards Compatibility

TODO

## Test Cases

TODO

## Security Considerations

This proposal does not materially alter Filecoin's consensus security model.

**Sustainability of consensus mining.** The initial value of α=0.05 is not expected to materially threaten L1-PoRep SP profitability. The continuous ramp provides predictability. At higher α values, the burn mechanism maintains discipline: unproven funds burn rather than accumulating. The consensus share reduction is predictable and cannot be halted.

**Revenue gate manipulation.** Potential gaming via wash trading is mitigated by Filecoin Pay fees, community monitoring, Orchestrator accountability, and Phase 2 per-Orchestrator attribution.

## Incentive Considerations

**Client incentives:** Clients gain access to subsidised, verifiable, real-time deal infrastructure without waiting for datacap allocation.

**SP incentives:** All SPs experience a reduction in direct block reward income. SPs who participate in market deals recover this through deal payments. SPs who do not serve clients see a permanent block reward reduction (ie, the intended outcome).

A) SPs primarily focused on consensus rewards (no direct client services)

- *Direct effect*: block reward received per epoch decreases by α.
- *Offset*: reduced strategic pressure to "pretend to be a service provider" and reduced governance/externality burden created by FIL+ gaming and review overhead.
- *Long-term rationale*: this model remains valid, but contributes a predictable share toward building the service economy that supports Filecoin's long-term legitimacy.

B) SPs offering onchain storage services (PoRep-based business)

- *Direct effect*: block rewards decrease by α.
- *Compensating opportunity*: access to treasury-funded subsidy, plus increased client-paid flows.
- *Long-term rationale*: if Filecoin succeeds as a service economy, these SPs are positioned to earn more than α via client payments.

C) SPs focused on retrieval / warm or hot storage services (PDP / FWSS)

- *Direct effect*: service incentives expand initial demand covering the cost of setting new infra.
- *Long-term rationale*: aligns Filecoin incentives with services that many clients actually buy at higher price.

**Orchestrator incentives:** Funding only grows when revenue gates pass. Strong incentive to produce results. Phased transition ensures competitive pressure.

**Token holder incentives:** Burn mechanism creates deflationary pressure when service economy underperforms.

## Product Considerations

Service incentive allocation is a tool to stimulate demand and to support and enforce network-aligned activity.

For storage providers, the long-term case rests on a simple observation: SP returns depend not only on block rewards but on whether Filecoin becomes a durable service economy with repeatable demand and credible client-facing products. Today, no single SP can efficiently fund the go-to-market layer, product pathways, and service infrastructure the network needs: that is a collective action problem. The service budget solves it at the protocol level.

This FIP also removes the largest operational drag of the current system. FIL+ created capacity but came with unpredictable datacap access, continuous governance overhead, and persistent reputational risk. Under this proposal, SPs who want to earn from services have a clear, measurable path: participate in service, meet service requirements, earn from real client demand. SPs who prefer to focus on consensus security keep earning block rewards, mining remains a valid mode. No one is blocked by human gatekeeping, and no one is forced into a service role they do not want.

Finally, by decoupling service incentives from datacap and from any single proof system, this FIP makes SP businesses more future-proof. The market layer can support PoRep, PDP, or whatever proving system clients actually demand, reducing the risk that SP investments become stranded on a single incentive path.

## Implementation

TODO

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
