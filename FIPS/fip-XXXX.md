---
fip: "XXXX"
title: Size the miner actor's reward-derived charges (faults) by the consensus weight
author: "Luca Nizzardo (@lucaniz)"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1302
status: Draft
type: Technical (Core)
category: Core
created: 2026-11-03
requires:
  - FIP-0118
---

# FIP-XXXX: Size the miner actor's reward-derived charges (faults) by the consensus weight

## Simple Summary

Size the charges a storage provider pays from the share of the block reward it actually receives after the Solstice split, rather than from the whole minted amount. Initial pledge and the PreCommit Deposit do not change.

## Abstract

[FIP-0118](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0118.md) splits each block reward into streams. An elected leader receives `allocation.miner = floor(w1 * BR)`, where $`w_1`$ is the weight of the implicit consensus stream, ramping down from 95% to a floor of 50%.

The reward actor's `this_epoch_reward` is unchanged by that split. It is still the whole minted value for the epoch, and both the reward actor and the power actor pass its smoothed estimate on unchanged. The miner actor sizes the fault penalties and the consensus-fault penalty from that estimate, with no $`w_1`$ anywhere. Those charges are defined as multiples of what a sector earns, so each now overstates a provider's income by $`1/w_1`$, reaching a factor of two at the floor of the ramp.

This proposal carries the consensus weight to the miner actor and applies it where such a charge is computed. `this_epoch_reward` keeps its present meaning and value, so the reward actor's issuance accounting is untouched. Initial pledge, the PreCommit Deposit and the termination-fee constants do not change, and no state migration is needed.

## Change Motivation

Solstice lowers the block reward paid to storage providers, and lowers it gradually: the consensus weight starts at 95% and ramps down to a floor of 50%. A provider's income per win falls with it, by design.

The charges a provider pays do not fall with it, because they are still computed from the whole block reward. The fault fee states its own intent in the actor code, where the projection period exists so that "a miner pays back at least the expected block reward earned since the last successful PoSt", in the code's own words ([`monies.rs`](https://github.com/filecoin-project/builtin-actors/blob/dbba8a0/actors/miner/src/monies.rs#L72-L80)). Computed from the whole reward while the provider collects $`w_1`$ of it, the fee takes back $`1/w_1`$ times what the sector earned, which is 3.51 days of income for every faulty day before the split and 7.02 once the weight reaches its floor.

The overpayment widens as the ramp advances, and it widens for every provider at once. FIP-0118 is silent on it. The words "penalties are assessed as today" refer to the `penalty` argument of `AwardBlockReward` and point at Section 2.4, and the FIP does not discuss the fault fee, the consensus-fault penalty or the FIP-0100 cap anywhere. The effect follows from leaving `this_epoch_reward` whole, so this proposal decides the question rather than inferring an answer from FIP-0118.

Two charges are affected materially.

**Fault penalties.** The continued-fault fee and the invalid-WindowPoSt penalty are both projections of a faulty sector's earnings. This is the largest continuous exposure, charged per sector per day at the weight in force that day.

It is worth being clear about the size. Over the last 365 days the fault fee came to about 214,000 FIL, 0.93% of minted rewards, from the Filecoin Data Portal's `storage_provider_cron_penalty_assessed_fil`, which Lily computes from the fault fee function rather than from traced burns. Scaling it at $`w_1 = 0.5`$ would return at most about 107,000 FIL a year to providers, against roughly 11.5M FIL of reduced receipts over the same period. The correction is small beside the reduction that prompts it, and the case for making it is that the charge should mean what it says.

**The consensus-fault penalty and its reporter reward.** The penalty is five per-winner rewards, one whole epoch of issuance, and the reporter is paid a twentieth of the epoch reward, from the `BlockReward / 4` that FIP-0011 set. Both are taken from the unsplit estimate, while the revenue an equivocating SP collects is $`w_1`$ of it.

A third quantity, the cap FIP-0100 places on the daily fee, reads the same estimate and is scaled here for consistency. It is not a motivation for this proposal, for the reason given in the Design Rationale.

## Specification

Let $`w_1(t)`$ be the weight of the implicit reward stream at epoch $`t`$, expressed over `DENOM` $`= 10^{18}`$. The stream invariants allow at most one implicit stream, so this is a single value. It is identified by being the implicit stream, not by its position in the stream list.

### 1. Carrying the consensus weight to the miner actor

The miner actor obtains the reward estimate by two routes, and both of them need the weight.

On the direct route the miner actor asks the reward actor, which replies with [`ThisEpochRewardReturn`](https://github.com/filecoin-project/builtin-actors/blob/dbba8a0/runtime/src/builtin/reward/mod.rs#L12-L18). This route covers pre-commit, prove-commit, replica update, sector upgrade, the WindowPoSt dispute, the consensus-fault report, `TerminateSectors`, which prices the fault fee that feeds the termination fee, and the exported `MaxTerminationFee` method, which prices the same quantity on behalf of a caller.

On the cron route the miner actor is called by the power actor, which supplies the estimate inside [`DeferredCronEventParams`](https://github.com/filecoin-project/builtin-actors/blob/dbba8a0/actors/miner/src/types.rs#L99-L105). The power actor takes the value from the reward actor and forwards it ([`power/src/lib.rs`](https://github.com/filecoin-project/builtin-actors/blob/dbba8a0/actors/power/src/lib.rs#L401-L404)). This route covers deadline advance and early-termination processing, which is where the continued-fault fee and the daily fee are charged.

Both structs shall carry $`w_1(t)`$ alongside the estimate they already carry, and the power actor shall forward the value it receives. Neither route gains a new message.

Two behaviours of the read have to be pinned down. The award path pays gas only and does not abort when it rejects the stream state, so the weight read shall return the weight last in force rather than failing, and `ThisEpochReward` shall not abort: an abort there would stop the power actor's `on_epoch_tick_end` before deferred cron and the network KPI update, and would fail direct miner and market calls. A read applies no due writes, so the value returned is the weight in force at the epoch of the read. `this_epoch_reward` and `this_epoch_reward_smoothed` keep their present meaning and value.

### 2. The weight used for sizing

Charges shall be sized with

$`w_{1,\text{eff}}(t) = \max\big(w_1(t),\ W_{1,\min}\big)`$

Stream governance can set the consensus weight to zero, and can remove the implicit stream altogether, in which case $`w_1(t)`$ reads as zero. $`W_{1,\min}`$ is set to 0.5, the floor of the weight schedule FIP-0118 publishes, so these charges follow that schedule down and stop where it stops. FIP-0118 requires a published and accepted FIP for every discretionary SWA write, so a decision to take the weight below its published floor arrives as a FIP, and that FIP is where these charges are revisited.

Write $`BR(t,d)`$ for the existing projection of a sector's reward over $`d`$ epochs and define

$`\widehat{BR}(t,d) = w_{1,\text{eff}}(t)\cdot BR(t,d)`$

Write $`R(t)`$ for `this_epoch_reward`, which is the whole epoch's reward and of which a win with `win_count` of one pays a fifth. The charges in section 4 read the smoothed estimate of that value rather than the stored value itself, and the two differ by well under a percent, 20.03 FIL against 20.05 FIL at the time of writing, so $`R(t)`$ here means the smoothed estimate the miner actor actually reads. Define $`\widehat{R}(t) = w_{1,\text{eff}}(t)\cdot R(t)`$.

Each product is taken in big integers and divided with floor, as FIP-0118 specifies for the award split. The floor on the weight is applied before the product, so a charge is never sized from a weight below $`W_{1,\min}`$.

### 3. Fault penalties

The following shall be computed from $`\widehat{BR}`$ in place of $`BR`$:

| Quantity | Definition today | Function |
| --- | --- | --- |
| Continued-fault fee, $`FF(t)`$ | $`BR(t,\ 3.51\text{d})`$ | `pledge_penalty_for_continued_fault` |
| Invalid-WindowPoSt penalty | $`BR(t,\ 5.51\text{d}) + 20`$ FIL | `pledge_penalty_for_invalid_windowpost` |

The projection periods, the two-day margin between them and the 20 FIL dispute base do not change.

### 4. Consensus-fault penalty and reporter reward

The following shall be computed from $`\widehat{R}`$ in place of $`R`$:

| Quantity | Definition today | Function |
| --- | --- | --- |
| Consensus-fault penalty | five per-winner rewards, $`R(t)\cdot 5/5`$ | `consensus_fault_penalty` |
| Reporter reward | $`R(t)/20`$, from `BlockReward / 4` in FIP-0011 | `reward_for_consensus_slash_report` |

Both move together. The reporter reward is a separate decision rather than a consequence. FIP-0011 set it to `BlockReward / 4` in order, in its own words, to untie it from the consensus-fault penalty, so the 5% the two formulas share today is a coincidence of their inputs and not a rule. Scaling the penalty alone would double that share. Scaling both holds it and takes the reward from about 1 FIL to 0.5 FIL, and whether that still buys the prompt reporting FIP-0011 was written for is the question to settle before adopting this section.

### 5. The FIP-0100 daily-fee cap

The `estimated_day_reward` supplied to [`daily_proof_fee_payable`](https://github.com/filecoin-project/builtin-actors/blob/dbba8a0/actors/miner/src/policy.rs#L226-L236) at the deadline-advance site shall be computed from $`\widehat{BR}(t,\ 1\text{d})`$.

The daily fee itself, `daily_proof_fee`, is a fraction of circulating supply and does not change. `DAILY_FEE_BLOCK_REWARD_CAP_DENOM` stays at 2.

### 6. Unchanged

- **Initial pledge**, both the storage-pledge term `IPBase` and the circulating-supply term `AdditionalIP`.
- **The PreCommit Deposit**, $`BR(t,\ 20\text{d})`$ via `pre_commit_deposit_for_power`.
- **The termination fee's own constants:** the 8.5% percentage, the 2% floor, the 1.05 fault-fee floor and `TERMINATION_LIFETIME_CAP = 140`.
- **The daily fee itself.** Only the cap applied to it is in scope, so the amount payable would move only if that cap bound, which it does not at current values.
- **The termination fee computed from those constants** does read the scaled fault fee through the 1.05 floor. Backwards Compatibility shows that branch is about nine times below the 2% pledge floor, so the fee does not move at current values.
- **The values and schedule of** $`w_0, w_1, w_2`$, which remain governed as FIP-0118 specifies.
- **The reward actor's issuance accounting**, including `this_epoch_reward`, `FilMined` and the circulating-supply inputs.
- **The proofs, their parameters and the sealing process.**

The lower-bound termination penalty, `pledge_penalty_for_termination_lower_bound`, is reward-derived but has no caller outside its own tests. It is not scaled, and removing it is suggested as a separate cleanup.

## Design Rationale

**What is in scope, and why.** The charges scaled here are the ones whose size is a projection of a sector's block reward: the fault penalties, the consensus-fault penalty with its reporter reward, and the input to the FIP-0100 cap. The termination fee and the daily fee are charges too and are both excluded, because neither is a reward projection: the termination fee is a percentage of pledge, and the daily fee is a share of circulating supply. Pledge and the PreCommit Deposit are reward projections, and are excluded as collateral, returned rather than spent.

**Why initial pledge is out.** `IPBase` is a reward projection, and the actor code calls it "a multiple of the reward expected to be earned by newly-committed power", so the reasoning that scales the fault fee would reach it too. `AdditionalIP` is a share of circulating supply and is not a reward projection at all. Pledge is excluded because pledge is collateral rather than a charge: locked against the sector, returned, and there to stand behind the charges rather than to be one. Scaling the fault fee without scaling pledge widens that cover instead of narrowing it, since `IPBase` covers 5.7 days of fault fees at $`w_1 = 1`$ and 11.4 days at $`w_1 = 0.5`$. The termination fee is a percentage of pledge and follows it out of scope, and total FIL locked is the aggregate of pledge and does not move either.

**Why the PreCommit Deposit is out.** It is collateral on the same reading as pledge, and a lock rather than a charge: released at prove-commit into the initial pledge, burned only when a pre-commit expires unproven, and held for days rather than for a sector's lifetime. What it deters is also priced off-chain. Abandoning a pre-commit to re-draw seal randomness, or occupying the pre-commit queue, pays off in sealing compute and chain state, and those payoffs do not fall when $`w_1`$ falls.

One bound on the deposit is worth addressing, because it will come up. The malformed-replica condition $`PCD > BR \cdot D / (2^{10}-1)`$ compares the deposit against the expected gain from passing sealing with a bad replica. Under the split that gain becomes $`w_1 \cdot BR \cdot D / (2^{10}-1)`$. With the deposit left unscaled the condition becomes $`D < 20\,(2^{10}-1)/w_1`$, which is 20,460 days at $`w_1 = 1`$ and 40,920 at the floor, so leaving the deposit alone loosens the bound rather than tightening it. The condition itself is stated in the Security Considerations of [FIP-0119](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0119.md#security-considerations).

**Why the daily-fee cap is scaled but is not a motivation.** The cap binds only when the daily fee approaches half a sector's block reward. The fee is currently around 3.4% of block reward, so the cap is far from binding, and scaling it changes nothing a provider would notice until circulating supply reaches a degenerate case. It is scaled because it reads the same estimate and the same argument applies to it, not because it has an effect today.

**Why the floor sits at the published schedule floor.** Stream governance can set the consensus weight to zero and can remove the implicit stream, so the case has to be decided rather than left implicit. Setting $`W_{1,\min}`$ to 0.5 makes these charges follow the schedule FIP-0118 publishes and stop where it stops, which asks for no judgement of its own. Going below that floor requires a published and accepted FIP, so what the charges should then be arrives with that FIP rather than having to be answered in advance here. An earlier draft argued for a lower floor on the grounds that a provider could otherwise hold power without storing data and pay nothing. That argument does not hold: a sector detected as faulty loses its power whatever the fee is, and the service stream is paid to registered Orchestrators rather than by PoRep power.

**Why the weight is applied at the point of use.** Scaling `this_epoch_reward` at the source would reach every consumer indiscriminately, pledge and the deposit included, and would break the reward actor's issuance accounting and the invariant pinning it to `compute_reward(...)`. Carrying the weight as a separate value keeps the issuance record exact and makes the set of affected charges explicit.

**Why the consensus weight alone, and not the consensus and service weights together.** The charges in scope project what a sector earns, and the service stream is paid to registered Service Orchestrators rather than to the elected leader. An SP's receipts from a win are $`w_1 \cdot BR`$ and nothing more.

**The changes are independent.** Sections 3, 4 and 5 can each be adopted without the others. They share the mechanism in section 1, which is the whole cost of the proposal.

## Backwards Compatibility

Two replies between actors carry one more value than before. Both are positional lists rather than named records, so a reader identifies each value by its place and cannot skip one it does not recognise. Every reader of `ThisEpochRewardReturn` and of `DeferredCronEventParams` has to be updated. The impact falls on node implementations, since both of those methods sit at low method numbers and are not reachable from FEVM. Chain state is unaffected, and `ThisEpochRewardReturn` has lost a value once before, so there is precedent for versioning the change.

One exported method changes its answer without changing its shape. `MaxTerminationFee`, added by FIP-0098 and dispatched through FRC-42, prices a sector's fault fee and returns the termination fee derived from it, but it evaluates that formula at the maximum sector age, so its result is 8.5% of pledge unless the fault fee rises above about 8.1% of pledge, and the fault fee is roughly 38 times below that today. The method should read the scaled fault fee for consistency with the termination path, but its answer does not move on current values.

No state migration is required. Every charge in scope is computed when it is charged and takes the new value as soon as the change is active. Nothing recorded against existing sectors changes, since pledge is untouched and no sector's stored state carries any of these values.

Termination fees do not move at all on current values. The minimum is $`\max(0.02\,IP,\ 1.05\,FF)`$, and the 2% branch is already far the larger of the two. For one 32 GiB sector, read from current reward and power state: at 1x, pledge 0.267 FIL, so 2% of pledge is $`5.34\times10^{-3}`$ FIL against $`1.05\,FF = 5.95\times10^{-4}`$ FIL; at 10x, pledge 2.669 FIL, so $`5.34\times10^{-2}`$ against $`5.95\times10^{-3}`$. As a check against chain state, a recently onboarded 10x sector, SP f03573579 sector 341139, carries an `InitialPledge` of 2.669 FIL. The pledge floor is about nine times the fault-fee floor before any scaling, so lowering the fault fee never brings the fault-fee branch into play.

## Test Cases

1. With the implicit stream at 100%, every charge in scope is unchanged from its current value.
2. At the floor of the ramp, the continued-fault fee for a given faulty power is half the value computed from the unsplit estimate, and equals one projection period of what the sector's wins pay.
3. The invalid-WindowPoSt penalty scales the same way, with the 20 FIL dispute base added after scaling rather than before.
4. The consensus-fault penalty tracks five times the per-WinCount reward a win pays, up to the gap between the smoothed estimate the penalty reads and the unsmoothed value a win is paid from, and the reporter reward stays a fixed fraction of the penalty at every weight.
5. An SP charged the continued-fault fee through the cron route is charged the same amount as the direct route would give for the same power and weight.
6. With the consensus weight set to zero, and separately with the implicit stream removed, every charge in scope is sized at $`W_{1,\min}`$ rather than at zero.
7. The PreCommit Deposit and initial pledge are unchanged under every weight schedule.
8. A sector whose termination fee is set by the 2% pledge floor is unaffected by the weight, and `MaxTerminationFee` prices its fault fee at the same weight as the termination path while still returning 8.5% of pledge for that sector, since it evaluates at the maximum sector age.
9. A sector onboarded through NI-PoRep, which has no pre-commit and no deposit, pays the same scaled fault fee as one onboarded through pre-commit and prove-commit.
10. The reward actor's stored `this_epoch_reward` still equals `compute_reward(...)` exactly, and its issuance counters are unaffected.

## Security Considerations

Every charge in scope is reduced and none is raised, so the question for each is whether it still covers what it was set to cover.

**Fault penalties.** The fee exists so that holding power without storing the data is not profitable. The comparison is between the fee and what the sector earns while faulty, and both sides move by $`w_1`$, so the ratio is preserved exactly. The calibration that held before Solstice is restored rather than altered.

**Consensus faults.** The penalty and the revenue an equivocating SP collects both move by $`w_1`$, so that part of the comparison is held. Two caveats. The factor of 5 in the penalty has no stated justification in FIP-0011, in the 2020 economics paper or in the actor code, so there is no documented ratio being preserved, only the one the formulas happen to produce. And the gain from equivocating need not be bounded by the block reward: whatever an attacker gains outside it does not fall with $`w_1`$, so the deterrent weakens against that part. The reporter reward is addressed in section 4 rather than here, since FIP-0011 untied it from the penalty.

**The floor on the weight.** The reduction is bounded below by $`W_{1,\min} = 0.5`$, so these charges cannot fall further than the published schedule takes them. Stream governance can set the consensus weight lower, but FIP-0118 requires a published and accepted FIP for any such write, so the floor is less a defence against a hostile write than a statement that this proposal sizes charges against the schedule it can see, and leaves anything beyond it to the FIP that proposes it.

**Termination.** Pledge is unchanged, so the 8.5% branch is unchanged and FIP-0098's calibration is left intact. The $`1.05\,FF`$ floor falls with the fault fee, but it already sits about nine times below the 2% pledge floor, so the larger of the two is unaffected and the invariant that terminating is never cheaper than remaining faulty continues to hold.

**Pre-commit.** The deposit is untouched, so every bound resting on it holds unchanged, and the malformed-replica margin improves by $`1/w_1`$ rather than degrading.

## Incentive Considerations

Providers currently pay fault, dispute and consensus-fault penalties sized to a reward they receive only a fraction of, and that fraction is scheduled to shrink further. This proposal returns each charge to the ratio it held relative to provider income before Solstice, and no charge rises.

The effect is largest where exposure is continuous, since a faulty sector's daily penalty falls to one projection period of its real income. The change to the daily-fee cap has no practical effect at current values.

Onboarding capital is unaffected. Neither pledge nor the PreCommit Deposit changes, so the FIL a provider must lock to onboard a sector is what it is today.

## Product Considerations

Fault cost returns to a stated multiple of what a sector earns, rather than a multiple that grows as the consensus weight falls. Tooling that projects fault cost from the reward estimate has to apply the consensus weight, or it will overstate that cost by up to a factor of two. Tooling that projects pledge, the PreCommit Deposit or termination cost needs no change.

## Implementation

One value added to `ThisEpochRewardReturn` and one to `DeferredCronEventParams`, populated by the reward actor from the evaluated weight schedule and forwarded by the power actor; the floor applied once where the weight is read; one multiplication in the miner actor at the sites listed in sections 3, 4 and 5; the pre-commit and pledge sites left alone. No migration, no new inter-actor message, and no change to the reward actor's issuance accounting.

One cost is worth measuring before implementation. The weight sits in the block behind `streams_root`, which `ThisEpochReward` does not load today, so carrying it adds a block load to every call that reads the epoch reward, including the pledge and deposit calls that make no use of it. The gas cost of that load has not been measured.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
