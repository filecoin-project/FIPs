---
fip: <to be assigned>
title: Explicit subsidy for FIL+ verified deals
author: Alex North (@anorth)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/243
status: Draft
type: Technical (Core)
created: 2022-01-12
---

This FIP is not yet 100% complete, but is substantial enough to warrant community involvement prior to completion.

Outstanding items:
- A scheme for withholding deal reward from faulty sectors and enacting penalties
- Implementation details for pledge and penalties
- Devise an asymptote function for deal reward as share of total network reward
- Validation of the reward, pledge, and penalty function behaviour and ~equivalence with existing implementation.
- More detailed spec of migration logic
- Decide what to do with unclaimed rewards


## Simple Summary
Removes the concept of quality-adjusted power from the storage powered consensus and instead 
redirects part of the block reward as an explicit subsidy paid to providers of Filecoin Plus verified deals.
The rewards paid remain the same, though with timing more advantageous to the provider.

## Abstract
The Filecoin network is secured by continually proven storage capacity, for which providers (miners) earn block reward.
To incentivise the storage of useful data, the Filecoin Plus program rewards the storage of verified deals
by causing such committed space to count for 10 times the storage power of other capacity. 
This is the quality-adjusted power mechanism.
The increased power increases the possibility of winning block rewards by a factor of 10.

QA power couples the storage deal market and the content of individual sectors to consensus.
This coupling greatly constrains the design space of both storage accounting and deal markets, and
- delays rewards for hosting verified deals, and makes those rewards uneven and unreliable;
- confuses FIL+ performance and reputation with raw capacity;
- prevents the flexible use of sector space to serve deals, restricting storage semantics to "write-once";
- will impede the development of alternative storage markets once the FVM enables user-programmable contracts; and
- impedes the design of more scalable sector accounting mechanisms.

The proposal breaks the coupling by accounting for and rewarding Filecoin Plus verified deals explicitly,
rather than piggybacking on the storage power block reward. In brief:

- Remove per-sector on-chain sector quality information from state; use raw-byte power for consensus power.
- Account for verified deal space-time directly in the market actor.
- Split the block reward into consensus reward and verified deal subsidy, paid separately.
- Add pledge and penalty mechanisms to verified deals to retain the existing economic incentives.

## Change Motivation
The [FVM](https://github.com/filecoin-project/FIPs/issues/113) will enable
user-defined contracts to execute in the Filecoin state machine.
Our hopes for these contracts include innovations on storage markets beyond the built-in one,
supporting novel types of storage deals and functionality including
deal extension, multi-sector deals, re-negotiation, deal transfer, capacity deals, auction markets,
repair markets, insurance, and derivatives.
But today, individual sector content is coupled to consensus (through QA power) and
the storage miner actor is tightly coupled to the built-in storage market actor
(e.g. the miner actor calls the market actor to compute deal weight).
Such coupling is a significant barrier to feature development in storage markets,
preventing straightforward implementation of even simple features like time-extension of deals or moving deal data between sectors.
Even if we had the FVM, most of this functionality would be either impossible or very complex to
design and build within the current architecture.

### Improvements to Filecoin Plus
This proposal enhances Filecoin Plus by improving the timing, predictability, and reliability of rewards. 

- With QA power, the reward for hosting verified deals is uneven (lottery), unreliable (need blocks included), and delayed.
- FIL+ subsidy will be **more reliable**, especially for small providers, because payment doesn’t depend on 
winning the consensus lottery or, after winning, getting a block included in the chain.
- FIL+ subsidy **pays sooner, aligned with the storage deal**. 
The QAP mechanism spreads reward out over the whole sector lifespan. 
This delays rewards, sometimes far after the deal has completed. 
E.g. today, there are ~7.3 PiB of active verified deals, but *providers are earning rewards as if there were only 1.03 PiB*! (but will keep earning after after those deals expire).
- The FIL+ subsidy pay-out period is smooth, no lottery, and aligned with the deal lifespan.

It also improves the transparency of Filecoin Plus performance
- With QA power, providers hosting deals compete with capacity-maximising providers on the same leaderboard, 
and are completely overshadowed.
- With this proposal, a provider’s verified deal hosting performance is directly observable on chain.
The “useful data provider” is a distinct leaderboard upon which the deal-seeking providers can compete, 
without being overshadowed by capacity-maximising providers who take no deals.
- The QAP mechanism *diminishes* the apparent contribution by spreading it out over time.
Today’s ~7.3 PiB of active verified deals contribute only 9.2 PiB of power despite a 10x multiplier!
Our 0.39% of storage as verified deals is being treated like 0.05%.

### Improvements to programmability and utility
Decoupling sector content from consensus power makes storage much more flexible.
The ideal storage API would be a big fungible “disk”, where providers can add/remove/update storage freely to satisfy new deals.
QAP opposes altering data, because mechanism spreads out the deal’s influence on power over the sector’s lifetime, 
regardless of deal term.

- With QAP, we can add new data to a sector, but cannot remove or replace data.
The provider would be either overpaid or underpaid, depending on deal term.
- Expired data cannot be removed from a sector.
- Data cannot be replaced even if the deal is complete.
- QAP restricts storage to **write-once**. A provider cannot utilise the full space-time of committed storage for deals; they can only use each byte of space once, regardless of deal duration.

This inflexible storage limits feature development:
- Extending deal by transferring to new sector: only possible exactly at end of original sector lifespan
- Transferring deal to another provider: not possible except at sector expiration
- Taking new deals (”snap-on-snap”): not possible to re-use storage that was already used for one deal, even if the deal is complete.
Cannot have a short, full-sector deal, and then replace with another full-sector deal.
- Capacity deals: client cannot remove or replace data at will, though there might be specific cases that work.

Storage that is more flexible is more valuable. 
After decoupling, a provider can extract more reward per sector because they can use the full space-time for verified deals,
even if those deals are not known when the sector is committed.
- QAP inflexibility incentivises short sector commitments, because FIL+ rewards are delayed until sector expiration and
space-time after deal expiration cannot be re-used
- QAP disincentivizes extending sector lifespan because miner needs to re-seal in order to take new deals for the space.

This proposal removes all such restrictions, making sector storage fungible and removing disincentives to long commitments.

### Enabling innovation
The built-in storage market actor is privileged as the arbiter of deal weight, and hence QA power.
The market is consensus-critical, inefficient, and very slow/hard to change (requires network upgrade).
The miner actor is tightly coupled to this market actor:
e.g. the miner invokes and trusts the built-in market to compute weight/power.

This privilege precludes alternative markets built on the FVM from competing.
Alternative markets might be more efficient, offer different features, make different trade-offs, integrate with other chains, etc.
But if they can't serve Filecoin Plus deals, they will not be competitive.

By decoupling markets from consensus, this proposal
- reduces consensus-critical, slow-moving, network-level code,
- reduces miner actor complexity,
- moves code out of the network-critical trust base,
- reduces the privilege of the built-in market actor, as a step towards realising markets as pure smart contracts,
evolving as fast as their independent development teams desire.

We must enable flexible storage and remove market actor privilege in order to support rapid ecosystem development of
actually-useful storage-related applications and features.

See [discussion #241](https://github.com/filecoin-project/FIPs/discussions/241) for discussion of the
more general motivations behind the innovation-enabling motivation for this and related upcoming proposals.

### Scale and security
The concept of quality-adjusted power incurs blockchain state storage and processing costs
linear in the number of sectors proven.
Such linear data will eventually limit the capacity of the chain to account for proven storage.
Removal of quality-adjusted power opens up scalable representations of homogeneous sectors as aggregates.
While the scalability of committed storage is not a pressing problem today, reducing coupling will
set us on stronger footing for solving it in the future.

QA power also slightly undermines economic-cost arguments for network security. 
Decoupling Filecoin Plus rewards from consensus will restore the property that consensus power requires 
a linear investment in storage hardware, and prevent collusion with FIL+ notaries from potentially
subverting consensus (though this is not a practical concern today).

### Summary of motivations

This proposal aims to:
- improve Filecoin Plus attractiveness to providers through more reliable rewards and transparent on-chain performance metrics;
- enable flexible, freely-programmable storage, increasing the utility and value of committed sectors, 
and supporting basic storage deal features;
- remove some coupling and privilege which will prevent future innovation in storage markets;
- simplify and reduce consensus-critical network code, enabling faster iteration; and
- reduce limitations on the scale and efficiency of maintaining exponentially larger amounts of capacity

These goals are sought within existing product and crypto-economic constraints around sound storage and economic security.
The proposal aims to preserve existing reward, pledge, and penalty behaviour as far as remains sensible
given the conceptual separation.

## Specification

### Uniform sector power
Every sector has uniform power corresponding to its raw committed storage size, regardless of the presence of deals. 
This **removes the concepts of sector quality and quality-adjusted power**, 
and makes all bytes equal in the eyes of the power table. 
Network power and committed storage are now the same concept and need not be tracked separately by the power actor.

- Remove `DealWeight` and `VerifiedDealWeight` fields from `miner.SectorOnChainInfo`.
- Remove call from miner to storage market actor `VerifyDealsForActivation` during sector pre-commitment
  or replica update (the method is misnamed: it actually computes deal weight, and real verification happens later).
  Remove the method itself from the storage market actor.
- Remove `TotalQualityAdjPower`, `TotalQABytesCommitted`, `ThisEpochQualityAdjPower`, `ThisEpochQAPowerSmoothed` from `power.State`.
- Add `ThisEpochRawBytePowerSmoothed` to power.State and maintain it in a similar fashion to `ThisEpochQAPowerSmoothed`.
- Remove `QualityAdjPower` from `power.Claim`.
- Remove all calculations leading to these values, and replace their use as inputs to calculations 
  with the equivalent raw byte size/power values.

With uniform sector power, the power of groups of sectors may be trivially calculated by multiplication.
Window PoSt deadline and partition metadata no longer need to maintain values for live, unproven, 
faulty and recovering power, but the sector number bitfields remain.
The complexity of code and scope for error in these various derived data is reduced.

- Remove `LivePower`, `UnprovenPower`, `FaultyPower` and `RecoveringPower` from `miner.Partition`, 
  along with the code paths that calculate these values.
- Re-code accesses of these memoized power values to instead multiply a sector count by sector size.

_Note:_ this proposal does leave per-sector metadata on chain, including activation/expiration epochs and deal IDs. 
It will still be necessary to load sector metadata when processing faults in order to schedule sector expiration. 
This might be removed by future changes toward fungible sectors.

_Note:_ Uniform power also means that all similarly-sized sectors committed at the same epoch would require the same initial pledge. 
Similarly, the expected day reward and storage pledge metadata values depend only on activation epoch. 
The per-sector values maintained to track penalties for replaced CC sectors (from pre-SnapDeals) become technically redundant. 
We could maintain historical pledge/reward values for the network just in the power and reward actors 
(instead of storing each of these numbers in chain state hundreds of times per epoch).
Removing these per-sector values would improve scalability of sector accounting, but this proposal excludes those changes
in the name of making a smaller total change while still achieving the decoupling of deals from consensus.

### Storage market actor accounts for verified deal space-time
The storage market actor becomes responsible for accounting for providers' storage of verified deals, 
and providing metrics to the reward actor to guide reward distribution.

To the storage market actor:
- Add `TotalVerifiedSpace`, a total of active verified deal space at the end of the last epoch. 
  Maintain this value during processing of deal activation and termination, 
  and when the market actor is notified of temporary faults of the sectors hosting verified deals.
- Add `TotalVerifiedSpaceDeltas`, a queue (AMT of epoch -> BigInt) to deltas to 
  the total verified space indexed by the current or future epoch at which they take effect.
- Add `VerifiedRewardsHistory` (AMT of epoch -> pair), a fixed-size queue of pairs of `TotalVerifiedSpace` 
  and the verified deal reward amount paid to the market actor (see below) from the end of each epoch.
  The window may be quite large, say 30-60 days. 
  TODO: consider whether a different structure might be more efficient for fixed-size, dense array
- Add `ProviderVerifiedClaims` a map (HAMT) of per-provider verified deal metadata. For each provider, maintain:
  - `LastClaimEpoch`: the epoch up until which rewards were last processed for the provider.
  - `VerifiedSpace`: the provider's active verified deal space at the end of LastClaimEpoch.
  - `VerifiedSpaceDeltas`: a queue of deltas since LastClaimEpoch, the provider's version of TotalVerifiedSpaceDeltas.
- Add `MigratedVerifiedDeals`, a map of deal ID to the size and start/end epoch as computed by the 
  (deprecated) quality-adjusted power mechanism for each existing verified deal.
  This is populated once at migration and will eventually become redundant.

When a verified deal is activated (on or before its start epoch), 
the deal's size is added to the `TotalVerifiedSpaceDeltas` queue entry for the start epoch, 
and subtracted from the entry for the end epoch. 
Similarly, the deltas are recorded in the provider's `VerifiedSpaceDeltas` queue. 
During cron at the end of each epoch, the queue entry for that epoch is removed and the value (which may be negative) 
added to `TotalVerifiedSpace`. The sum of `TotalVerifiedSpace` plus all deltas should always equal zero, 
the rolling sum never dipping below zero.

Note that it is important that the `TotalVerifiedSpaceDeltas` queue entries are fixed size (a single big integer). 
This allows us to schedule the deltas exactly on the deal start/end epoch, 
retaining an exact calculation for `TotalVerifiedSpace`, without exposing the potential for some party to
overload cron processing at a single epoch by stacking deals with the same start or end epoch.

See the section on faults for an explanation of `MigratedVerifiedDeals`.

To the storage market actor:
- Add a `ClaimRewards` method which traverses a provider's verified space deltas since last claim,
  along with the `VerifiedRewardsHistory`, and accumulates the reward due to a specific miner.
  It then invokes `miner.ApplyRewards` with that amount to transfer it to the miner's locked funds.

Each provider's claim of their share of verified space, and hence rewards, 
is processed manually by an invocation from the provider, rather than by cron. 
For each epoch since `LastClaimEpoch`, pop and add the corresponding delta to the provider's verified space,
then compute the fraction of total verified space at that epoch which the provider provided, and thus their share of the epoch's reward.
Accumulate these rewards up to the penultimate epoch, and pay to the provider via `miner.ApplyRewards`.

Note that since the `VerifiedRewardsHistory` window is fixed, a provider which does not claim rewards within that window will forfeit them.

Parameter: verified reward history length: 60 days?

TODO: Track total claimed reward, and burn unclaimed?

TODO: Should we fiddle with the vesting date for claimed rewards? Backdate half way?

### Reward distribution
The block reward at each epoch is divided into two shares:
- Consensus reward, proportional to raw byte power; and
- Verified deal subsidy, proportional to verified deal space.

A miner's chance of winning the election at each epoch is proportional to their share of the raw byte power 
(no quality-adjusted power) committed to the network and non-faulty.
Winning the consensus reward remains a lottery, and is paid directly to the miner actor.

The verified deal subsidy is paid to market actor, for subsequent distribution to providers. 
This reward is not a lottery, and is claimable by providers whether or not they produce blockchain blocks.

To the reward actor:
- Add `ClaimVerifiedDealReward`, to be invoked by the market actor, 
  which records the current total verified space for the next epoch, and remits the reward for the previous one.
- Rework the `UpdateNetworkKPI` implementation to compute the share of the next epoch's reward to be reserved for verified deal subsidy.

In cron at the end of each epoch, the market actor calls `ClaimVerifiedDealReward`. 
This serves two purposes. 
(1) It provides the reward actor with the total verified space value for this epoch,
which will be used to compute the share of reward for the next epoch (similar to the current storage power from the power actor). 
(2) In response, the reward actor pays to the market actor the share of total mining reward due to verified deals from the epoch just passed.

After receiving both the storage power and verified space values, 
the reward actor splits the total block reward to be paid in the next epoch into 
the consensus reward and the verified deal subsidy.
The block reward is paid as usual, and the deal subsidy retained for the market actor to claim.
This mechanism will generalise to multiple market actors in the future (on the assumption they can use cron).

The reward split function is given by:
```
ConsensusReward = EpochReward * NetworkRawPower / (NetworkRawPower + 9 * TotalVerifiedSpace)
VerifiedDealReward = EpochReward - ConsensusReward = 9 * NetworkRawPower * TotalVerifiedSpace / (NetworkRawPower + 9 * TotalVerifiedSpace)
```

This reward distribution results in the *same total reward* profile as the current implementation,
both for the system as a whole and for individual miners, with the exception of a change in the timing
of verified deal rewards. This proposal has no intention of altering the ultimate incentives to storage providers,
only of providing them by a more transparent mechanism.

TODO: demonstrate how change in reward timing adds up to same total reward.

### Sector pledge
The current sector initial pledge held by each miner actor comprises two parts:
- Sector storage pledge: a multiple of the reward expected to be earned by newly-committed power
- Sector consensus pledge: a pro-rata (by QA power) fraction of the circulating money supply when the sector is committed

For each of these parts, reduce the sector pledge proportionally with the ratio of consensus reward to total reward,
so that the sector pledge is aligned with the sector's rewards. 
Pledge corresponding to the verified deal reward will be held by the market actor (see below) 
so that the total pledge amount remains consistent with the QA-power approach.

The sector storage pledge becomes a multiple of the projected consensus block reward for the sector (i.e. excluding verified deal reward). 
The smaller network power denominator is balanced by a reduced share of total reward allocated to consensus rewards.

For a sector with no verified deals, this should yield approximately the same storage pledge amount as before this proposal 
(and continue to function if the consensus reward ratio changes smoothly).

Approximately (the real version uses an alpha/beta smoothing function):
```
SectorStoragePledge := ProjectionPeriod * ExpectedReward
where
ExpectedReward := ConsensusRewardEstimate * SectorPower / NetworkPower
ConsensusRewardEstimate := TotalRewardEstimate * ConsensusRewardRatio
```

TODO: demonstrate the near-equivalence in behaviour using real network values.

For sector consensus pledge, the “lock target” of which the sector takes a pro-rata share is multiplied (i.e. reduced)
by ratio of consensus reward to total block reward. The calculation must include as input the current reward split function, 
and set as pledge the pro-rata share of money supply according to the instantaneous share of total reward to be earned by the raw byte power.
The remainder of the total consensus pledge will be met by a verified deal pledge.

Approximately:
```
SectorConsensusPledge := LockTarget * PledgeShare
where
LockTarget := 0.3 * ConsensusRewardRatio
PledgeShare := SectorPower / NetworkPower
```

As at present, the sector pledge is forfeit when a sector terminates ahead of schedule.

### Verified deal pledge
In order to maintain the current money supply relationships, storage providers must pledge collateral
with the storage market as a function of their expected deal subsidy rewards, as well as sector rewards.
This pledge secures verified deals, rather than sectors.

We wish to maintain approximately the same total pledge requirement for a sector+deals,
meaning the deal pledge should match the reduction in sector pledge caused by removing QA power.
Thus, it takes a very similar form:
- Deal storage pledge: a multiple of rewards expected to be earned by the deal subsidy
- Deal consensus pledge: a pro-rata fraction of the circulating supply when the deal is activated

For the deal storage pledge, a projection function similar to that used to project sector rewards may be used
to project a multiple of the expected reward to be earned by a verified deal.

Approximately
```
DealStoragePledge := ProjectionPeriod * ExpectedReward
where
ExpectedReward := DealRewardEstimate * DealSpace / TotalDealSpace
DealRewardEstimate := TotalRewardEstimate * (1 - ConsensusRewardRatio)
```

Similarly, the deal consensus pledge is a pro-rata share of the money supply, moderated by the 
instantaneous share of total reward emissions that the deal can claim.

Approximately:
```
DealConsensusPledge := LockTarget * PledgeShare
where
LockTarget := 0.3 * (1 - ConsensusRewardRatio)
PledgeShare := DealSpace / TotalDealSpace
```

TODO: describe market state changes for tracking pledge

The deal pledge is forfeit (burned) if a provider fails to carry a deal to completion.

### Faults and penalties
TODO!

Notify the market of deal faults.
Add penalties to match the existing penalty scheme.

## Design Rationale

### Separation of security from reward distribution
The current mechanism of quality-adjusted power is a means of incentivising useful storage, 
delegating the definition of “useful” to an off-chain notary.
The incentive for storing verified deals is the increased block reward that may be earned from the increased power of those sectors,
despite constant physical storage and infrastructure costs. 
In essence, **the network subsidises useful storage by taxing the other power**.

Storage power thus has two roles, currently coupled:
- to secure the network through raising the economic cost of some party maintaining a significant fraction of the total power, and
- to determine the distribution of block rewards.

The block reward currently both rewards security and subsidises useful storage. 
This coupling theoretically means the verified deal power boost reduces the hardware cost to attack the network by a factor of 10,
if colluding notaries would bless all of a malicious provider's storage (this is an impractical attack today, though).

This proposal **makes the subsidy direct**, reducing complexity and coupling between the storage market and individual sectors,
and clearly separating security from reward distribution policy.

This means that verified deals no longer contribute to consensus power, though they continue to earn the 
same (in fact, more reliable and sooner) rewards as the QA-power mechanism. This could constitute a reduction
in incentive to maintain verified deals to the extent that consensus power is desirable for reasons _other
than the reward_. Such reasons might include 
(a) reputation, if providers memetically attach to consensus power rather than storage of useful data, or 
(b) control, if providers manipulate the blockchain outside the "honest" protocol, for self-interested reasons. 
To the extent that this proposal reduces the ability to stack consensus power through 
defeating the Filecoin Plus notary process, it confers a chain security benefit.

### Change in reward smoothness
A storage provider's consensus reward is earned via a repeated lottery, so it is not smooth.
In the long run, the expected value is quite stable, but in the short run may vary a lot.

This proposal makes the deal reward smooth.
A provider earns deal reward consistently, without regard to the consensus lottery.
A provider need not mine any blockchain blocks to earn the deal reward, even if they do win the lottery.

This is an improvement in the economics for small providers, 
who account for only a tiny fraction of network power but tend to disproportionately focus on providing
high quality storage for verified deals. 
Such providers very rarely win the consensus lottery in any case,
and their smaller scale permits less sophisticated blockchain node infrastructure and connectivity to capitalize on those infrequent wins.
A provider focussing on sectors with high verified deal content can thus earn 90% of their total reward smoothly and predictably.

### Change in reward timing
This proposal effects a change in the timing of deal rewards.
In the quality-adjusted power model, the reward attributable to an individual verified deal is 
spread out over the whole lifetime of the sector supporting that deal. 
If a deal occupies a small fraction of a sector's lifetime, much of the reward is delayed well past the deal's expiration.

This is a positive change in aligning providers' cash flow with value provided to the network.
The rewards for a verified deal are earned during its lifetime.
After a deal expires, the sector continues to earn storage power rewards only, like a committed-capacity sector.
This is a necessary step towards enabling more flexible assignment of deals to sectors,
permitting deal extension and the transfer of deal data to new sectors, including those that previously hosted other deals.

TODO: Note reward starts paying from deal activation, rather than first WPoSt after PoRep

## Backwards Compatibility

This proposal introduces changes to actor state and method parameters, 
and also directly changes consensus election rules to use raw byte power instead of QA power.
It thus requires a network-wide consensus upgrade.

Tools which inspect on-chain state directly may need to introduce a new schema in order to operate smoothly across the upgrade epoch.

### Migration
This proposal requires a point-in-time migration of chain state involving the miner, storage market, power, and reward actors.

The primary challenge is moving the pledge requirements and rewards associated with quality-adjusted power from 
miner per-sector information into the market per-deal accounting records.

#### Market actor
Initialise total verified space and per-miner verified space.
For each migrated deal, multiply space by the fraction (<=1) of sector lifetime the deal occupied 
in order to replicate exactly the same reward schedule as QA-power did.
Old deals pay out over sector lifetime, new ones over deal lifetime.

Initialise the MigratedVerifiedDeals metadata with these values.

Initialise the total and per-provider verified space delta queues with the expirations of the migrated deals at the expiration of their sectors.

TODO during draft phase: Spec out the migration more fully

#### Miner actor
Migrate the sectors!

#### Reward actor
Changes to baseline and realised cumsum if necessary. 
Initialise verified deal space for the reward calculation immediately subsequent to migration.

## Test Cases
TODO during draft phase:
- Equivalence of total reward for CC sectors, sectors with deals, varying deal/sector expirations etc
- Equivalence of total reward through migration
- Equivalence of pledge functions and penalties

## Security Considerations
TODO during draft phase. Mostly about incentives (below).

## Incentive Considerations

### Incentive to block producers
Earning the verified deal subsidy doesn't depend on winning blocks.
This is a deviation from the current protocol that requires a miner to win a block 
(with a Winning PoSt) in order to claim any rewards. 
This may reduce the incentive for providers with a very high proportion of verified deals to mine blocks.

When network-wide storage utilisation is low, such providers will account for a very small proportion of consensus power.
Most network reward will be earned by block producers.

When network-wide storage utilisation is high (>10%), the network may pay more reward to deal providers than block producers.
One mitigation for this could be to cap the fraction of network total reward that the deal subsidy may draw.
An asymptotic upper bound may be implemented in the reward split function by changing a constant. 
For example, to impose an upper bound of 30% of reward for deal subsidies:
```
VerifiedDealReward = 9 * NetworkRawPower * TotalVerifiedSpace / (NetworkRawPower + 29 * TotalVerifiedSpace)
ConsensusReward = EpochReward - VerifiedDealReward
```

### Incentive to maintain deals
No change: the same total collateral is at risk for reneging on a deal.

### Incentive to maintain healthy storage
No change: the same total penalties are applied for reneging on a deal.

Maybe a change after the deal expires, and sector rewards revert to CC.

### Incentive to select sector lifetimes and maintain CC sectors
Reward timings are changed, deal reward earned during deal instead of spread out over sector.

Current incentive to select minimal sector life, since longer delays rewards.
Longer lifespan no longer delays rewards, so may see marginal incentive to longer commitments.


## Product Considerations
TODO during draft phase: better reward profile for small, deal-focussed SPs

## Implementation
A draft implementation is in progress at https://github.com/filecoin-project/specs-actors/pull/1560. 
As a technical FIP, the proposal is expected to be accepted before implementation is completed, 
in order to motivate and direct that implementation.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).







