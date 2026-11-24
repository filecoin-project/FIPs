# Supporting analysis for FIP-0119

This is the analysis behind FIP-0119, copied from [discussion #1291](https://github.com/filecoin-project/FIPs/discussions/1291) on 30 October 2026 so that the FIP does not depend on a document that can be edited outside this repository's history.

The text is unchanged except that links to files in this directory are relative rather than absolute, so they resolve in a clone.

---

# Overview
Today the maximum sector lifetime is 5 years (`seal_proof_sector_maximum_lifetime` in builtin-actors), which we call the cap below. After that the sector cannot be extended and its data has to be sealed again into a new one. Can we raise maximum sector lifetime to 10 years?

The motivation is retention: keeping committed capacity on the network instead of forcing it off. A bulk of sectors is about to hit the maximum sector lifetime, where today the only option is a mandatory re-seal. There is a cost argument too, since sealing is paid once per lifetime: for data kept ten years, doubling the cap halves the sealing cost per year. As the numbers below show, it is the smaller of the two.

# Numbers

- **Capacity is forced off by the cap alone.** About 42 PiB cannot be extended from December 2026 onwards, whatever the provider wants: those sectors sit at the cap. For a sector at the cap the choice is stark: staying costs one message, where after Solstice a single `UpgradeSectorQuality` call can also move it to 10×, against a full new seal to keep the same bytes. Averaged over time the saving is small, so this is a capacity argument rather than an income one. [1] [3]
- **The standing cost, at the limit.** A 5 year cap means re-sealing 268 PiB a year just to hold capacity flat, 86% of everything onboarded in the last twelve months. Doubling the cap halves the amortized cost. That 268 PiB is an upper bound rather than what the cap forces today: it assumes every sector lives its full 5 years and is then re-sealed, where [1] finds 118 PiB at the cap over the whole horizon out of 1,339 PiB. [2]
- **The change is one constant.** The maximum sector lifetime, 5y → 10y. No new proof type, no pledge formula change, no state migration.

**Timing.** A sector is hard-capped when its scheduled expiry is already at, or within 90 days of, activation + 5 years: extending it is no longer possible, so the data has to be re-sealed or dropped no matter what. 
Summed across all future expiry dates that comes to 118 PiB, as measured via Lily in October 2026. 

Of those, 58 PiB go on 1 November 2026 alone and 76 PiB by the end of that month, before any FIP can ship, so that part can not be extended either way. 

What a change can still reach is the remainder: about 42 PiB if it activates in early December, 40 in January, 31 after March. Everything else expiring in the same window is unaffected, since those sectors can already be extended out to 2028–2030 under today's rules. [1]

# Security Analysis

Such a leap should be carefully analyzed in terms of security. 

From the protocol standpoint, there are two main risks which can harm Filecoin security: 

- A flaw discovered in PoRep
- A drift in cost or latency that makes the SDR security margins too thin.

For a flaw the response is a network upgrade shipping a new sealing algorithm: a broken proof cannot be repaired at proving time. For drift there is also a cheaper response, raising the audit frequency, which works on sectors already sealed because the frequency is evaluated when the proof is made, not when the sector was. We can see both solutions as the shipment of a new proof type.

In both cases, though, what decides how long the "issue” exposure lasts is how long sectors of the old type stay around.

- If the upgrade also forbids extending old-proof sectors, each of them expires at its current expiration, which is at most 3.5 years after the upgrade (as `MAX_SECTOR_EXPIRATION_EXTENSION` = 1278 days, [FIP-0052](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0052.md)), with either cap (i.e. 5y or 10y maximum sector lifetime does not play any role here). [FIP-0067](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0067.md) describes this as the current implicit policy in case of a flaw.
- If in the upgrade extensions stay allowed, old sectors live to the cap: a sector sealed in 2026 until 2031 with a 5 year cap, until 2036 with a 10 year cap. Note that we do not expect this to happen, but we incorporated into the analysis in order to have the full picture.

**Example:** Say the upgrade that retires the old proof type ships in June 2027, and take a sector sealed in January 2026:

- extensions of old-proof sectors forbidden: its expiration can be at most June 2027 + 1278 days = December 2030, so it is gone by then whatever the cap;
- extensions still allowed: it runs to its cap, January 2031 with 5 years, January 2036 with 10;
- replacement sealing in force: deactivated by December 2028, 1.5 years after that upgrade.

Under a 5 year cap the first two land a month apart, so the cap is doing no work. Under a 10 year cap they are five years apart, and that gap is exactly what raising the cap buys the network and what it costs.

FIP-0067, superseding [FIP-0047](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0047.md), also specifies replacement sealing, which would deactivate old sectors within 1.5 years of the upgrade that enables it. Its implementation is "deferred until needed".

As we saw above, the cap (5y Vs 10y) matters for security only when extensions stay allowed. 
Worth making explicit: maintaining the 3.5 year bound needs a decision at the time of the protocol upgrade, while the cap bounds things with nobody having to do anything. 

Practically speaking, this means that raising the maximum sector lifetime from 5 to 10 years does not change the expiration bound in the first upgrade scenario.

This means that what we need to check is the cost side in the worst case (where worst here means extension being the longest possible): how plausible it is that the cost analysis still holds over ten years. In other words, whether a sector sealed in 2026 is still secure in 2036, because a proof made in 2036 is made against 2036 hardware.

## What a cheater could do

We know that every 24h, a provider needs to prove the sectors he holds. He basically has two ways to cheat:

- **Delete everything** and re-seal the sector before each daily WindowPoSt. Costs a full seal every day.
- **Delete more than 20%** and regenerate only the part that gets challenged. Costs a fraction of a seal, on the days it gets caught out.

Filecoin is safe when both cost more than simply storing. The 2023 security report (see reference below) calls that ratio the security margin, $SM = RC/SC$: cost of regenerating over cost of storing, both per sector per day. The comparison is the report's own, section 5.1.2.
## The three parameters cheater's strategy depends on

- **Sealing costs.** Supranational's 2022 cost analysis gives the sealing configuration we assume: an EPYC Genoa box at $23,300 that seals 128 sectors in 5 hours. Spread over the rig's life, that is $0.052 per sector at 2 years, $0.035 at 3, $0.021 at 5. This is the regeneration cost only, hardware with no power and no hosting on either side of the comparison (we could estimate power to add about 3% if considered). The $23,300 breaks down as: $6,000 for the EPYC Genoa 9474F, $2,800 motherboard, $8,800 of NVMe (16 × 7.68 TB Samsung at $550), $1,600 memory, $1,600 GPU, $1,360 adapters, $640 HDD, $500 chassis and power. The same analysis gives the 128 sectors in 5 hours. NVMe is 38% of that bill at 2022 prices, which makes it the oldest input here: repricing it at 2026 NAND raises every margin below by about a quarter.
- **Storage costs.** A September 2026 price check on public trackers ([diskprices.com](https://diskprices.com/), [harddiskprices.com](https://www.harddiskprices.com/)) puts 24 TB CMR enterprise drives at $28.33/TB, so a 32 GiB sector costs $0.00133 a day on a 2 year drive life, $0.00053 at 5 years, $0.00033 at 8.
- **How much a cheater must regenerate.** According to Reyzin's result (Theorem 5): a provider storing less than 80% must redo at least 20.4% of the seal, and gets asked on 65% of proving days. 
Before his paper the provable figure was 1.8% (eleven times worse, consisting in a long path on a 20% fraction of a single layer): that is the bound our own old report uses, and Reyzin cites it as [GN23] in his Appendix C before improving it.

## The WindowPoSt margin, across hardware lifecycles

The cheater chooses how much of the sector to delete, and the choice is a tradeoff: deleting more saves more drive, but it forces more work when a challenge arrives. Reyzin's theorem gives us one point on that tradeoff. Delete more than 20% of the sector and you must redo at least 20.4% of the seal, on the 65% of days when the challenge lands on something you threw away. Delete less than 20% and nothing at all is proven, though the most you could save there is a fifth of the drive. That 20% threshold is what is known as the spacegap, $\varepsilon_{space} = 0.2$.

We refer to $\text{Seal}$ for the cost of sealing one sector, $SC$ for the cost of keeping one sector on disk for a day, and $RC$ for what the cheater pays per sector-day to regenerate:

$$
RC = 0.651 \cdot 0.204 \cdot \text{Seal} = 0.1328 \cdot \text{Seal}
$$

The $0.651$ is the share of days on which the challenge lands on something the cheater threw away, and the $0.204$ is the fraction of the seal it must then redo.

The table below is the **worst scenario** (which is the one we'd take into account, similarly to the old report): the adversary pays only regeneration and no storage at all, so cheating is unprofitable when

$$
RC > SC, \qquad SM = \frac{RC}{SC}
$$

This is deliberately pessimistic, since it charges the cheater the smallest work the theorem can force while crediting it with having thrown the whole sector away. If the margin stays above 1 here, no deletion strategy which exceeds the spacegap pays.

Rows in the table are how many years the sealing machine is used before being replaced, columns how many years a drive lasts. Both turn a one-off purchase into a cost per sector per day: a $23,300 machine used for 3 years costs $7,767 a year, and running continuously it seals 128 sectors every 5 hours, so 224,256 in a year, which puts $0.0346 of machine on each sector. Keep the same machine 5 years and each sector carries only $0.0208, since the same price is spread over more sectors.

Take one cell as an example, the machine used for 3 years against drives replaced every 5.

**Regenerating**: a seal costs $23,300 / (3 × 224,256) = $0.0346 per sector over a 3 year machine life, the cheater is forced to redo 20.4% of it and is asked on 65% of days, so $0.0346 × 0.204 × 0.65 = $0.0046 per sector per day. 

**Storing**: a 32 GiB sector on $28.33/TB drives is $0.97 of drive, spread over five years $0.00053 per sector per day. The margin is the ratio, $0.0046 / $0.00053 = **8.6**. 

Every cell is that same division, and it reduces to $SM = 5.17 \cdot L/R$ with $L$ the drive life and $R$ the rig life in years. 

|  | Drives 2y | Drives 3y | Drives 5y | Drives 8y |
| --- | --- | --- | --- | --- |
| Rig 2y | 5.2 | 7.8 | 12.9 | 20.7 |
| Rig 3y | 3.4 | 5.2 | 8.6 | 13.8 |
| Rig 5y | 2.1 | 3.1 | 5.2 | 8.3 |

Anything above 1 means storing is cheaper than cheating (i.e. regenerating). 

The realistic scenario seems to be a machine used for 3 years against drives replaced every 5, which gives SM = **8.6**. 

The pessimistic corner, a machine kept 5 years against drives replaced every 2, still gives 2.1. 

Now the **other scenario**, which is the cheater's best move: it keeps 80% of the sector and deletes the rest, paying the least work the theorem can force while still saving something. It now carries the storage of what it kept, so cheating is unprofitable when

$$
RC + 0.8 \cdot SC > SC \iff RC > 0.2 \cdot SC, \qquad SM = \frac{RC}{0.2 \cdot SC}
$$

What cheating has to beat is the fifth of the drive it saved, and the margins are:

|  | Drives 2y | Drives 3y | Drives 5y | Drives 8y |
| --- | --- | --- | --- | --- |
| Rig 2y | 25.8 | 38.8 | 64.6 | 103.4 |
| Rig 3y | 17.2 | 25.8 | 43.1 | 68.9 |
| Rig 5y | 10.3 | 15.5 | 25.8 | 41.3 |

The same realistic cell, rig 3 years against drives 5 years, gives **43.1**, and the pessimistic corner 10.3. 

For reference, a provider that deletes everything has to re-seal before every proof, a full seal a day, and faces 65 at that cell, 16 to 156 across the grid.

As a rule, which matches intuition, longer rig life lowers the margin, because it makes cheating cheaper. Accordingly, longer drive life raises it, because it makes honest storage cheaper. Neither is a protocol parameter; they are operator choices.

## Where it goes by 2036

Starting from 8.6. The margin is a ratio, so only relative drift counts: prices moving together, up or down, cancel. Cheaper compute lowers it, since regenerating gets cheaper, and more expensive drives lower it too, since the cheater is the one not buying them.

| Compute per year | Drives per year | Margin in 2036 |
| --- | --- | --- |
| flat | flat | 8.6 |
| −10% | −10% | 8.6 |
| −10% | flat | 3.0 |
| −20% | −10% | 2.7 |
| −20% | flat | 0.9 |
| −20% | +5% | 0.6 |
| +5% | +5% | 8.6 |
| flat | +5% | 5.3 |
| +5% | flat | 14.0 |

Two of these go under 1 inside the life of a sector sealed today, considering 10y sector lifetime. 

Careful with what that means. These are the provable margins: the forced work from Reyzin's bound against the full cost of storing, which is the worst case over how much the adversary deletes. Against the adversary the bound actually describes, one deleting just over 20%, the saving is only a fifth of the storage and the margins are five times these, so 43 today and 2.8 in the worst corner above. A cell below 1 therefore means the bound stops covering the store-nothing case, not that cheating has become profitable. 

Getting there takes a sustained divergence of about 19% a year for a decade, whichever side moves: compute dropping 19% a year with drives flat, drives rising 24% a year with compute flat, or any mix. The 20% in the table is the mining-ASIC rate applied to sealing. 

That is not where we are today: both sides are rising, since a sealing rig is mostly NVMe and NAND prices rose through 2026 along with drives, and parallel increases leave the ratio where it is.

## The WinningPoSt Margin

Block production has a separate check: an elected provider proves one random sector within the block window. This one is about speed, not money. Regenerating takes 34 seconds on the theoretical ASIC the report assumes, and 72 on the fastest CPU you can buy.

What it races against: Lotus gives an elected provider 40 seconds end to end, from the drand beacon that names the challenged sector to the moment peers stop accepting the block. 

Part of that goes on generating the SNARK and propagating the block, so we count 30 seconds as the time left for regeneration, which is also what the report assumes. These figures are for a 32 GiB sector, which is the conservative choice: a 64 GiB sector has twice the labels, so regenerating it takes twice as long and its margin is twice as large. On that basis the margins are 1.14 and 2.41, with instruction latencies from [uops.info](https://uops.info/html-instr/SHA256RNDS2_XMM_XMM.html). If proving and propagation turned out to take less than 10 seconds, the ASIC figure would drop towards 0.85.

That is thin, and it gets thinner: sequential hashing has sped up about **10% a year** across CPU generations. That comes from Zen 2 to Zen 5, 4 cycles at 4.7 GHz down to 3 cycles at 5.7 GHz, a 1.62× gain over five years. Starting from 2026, that puts the CPU margin at **0.93 in 2036**, so it goes under 1 before then; at a more conservative 6.5% a year it would be 1.28. 

Against the theoretical ASIC we start from 1.14, which at 10% a year reaches 1 in about 1.4 years. 

Reyzin's improvement does not help here: his result is about cost, and this is about latency. He says so himself, noting that the older bound he improves on was "proven for parallel hardness, which corresponds to latency, while our result is only for sequential hardness, which corresponds to cost".

Note that nobody sells such an ASIC today. Concretely, market research suggests that Bitcoin miners are built for throughput and need at least 64 ns per hash against the 7.9 ns this hypothetical ASIC would need.

# What this says about 10 years Maximum Lifetime

Nothing in the numbers blocks it, and none of the erosion above is caused by it: in 2036 every sector faces 2036 hardware whatever the cap is.

What the cap decides is how long old-proof sectors stay around once we decide to retire their proof type:

- If we forbid extensions at that upgrade, they are gone within 3.5 years of it, with either cap.
- If we leave extensions allowed, they run to the cap: up to 5 years after the upgrade today, up to 10 if we raise it. This is the only branch where the cap does any work, and the only one that needs no decision from anyone.
- Replacement sealing would shorten the first branch to 1.5 years, counted from the upgrade that turns it on, but it is not in code: FIP-0067 is policy only, so nothing is bounded by it today.

# Suggested path forward

- Raise the maximum sector lifetime to 10y.
- Make margin erosion a trigger for FIP-0067, next to a PoRep flaw.

## On the Margin Erosion Trigger

The margin erosion trigger is the key outcome of this proposal.

Since how long the old-proof sectors stay around is what bounds both risks, the trigger is what decides when that clock starts, and the margin analysis above is what sets it.

Note we would be adding a trigger to something that is not in code yet: FIP-0067 is accepted as policy, with its implementation "deferred until needed".

**Which margin?**

Both, each with its own threshold, because they fail differently. The WindowPoSt margin SM is a cost ratio and can still be repaired on sectors already sealed, by raising audit frequency. The WinningPoSt margin is a latency race inside a fixed window and nothing retrofits it.

**What threshold?**

The trigger has to fire early enough to ship a network upgrade and then let the old sectors expire. Let $\alpha$ be the upgrade time window, meaning the time from the trigger firing to the upgrade activating on mainnet, and let $d$ be the factor by which the margin falls each year. The threshold is then $d^{-(3.5 + \alpha)}$.

Below we take one year for $\alpha$. That is an assumption and not a measurement, and it is the one to argue with: with $\alpha = 2$ the thresholds become 4.5, 1.8 and 1.7 instead.

The 3.5 years is `MAX_SECTOR_EXPIRATION_EXTENSION`, and it holds only if the upgrade that retires the proof type also blocks extensions of old-proof sectors, as it would for a PoRep flaw. Without that the old sectors run to the cap, the exponent becomes 11 under a 10 year lifetime, and the thresholds rise to 20.5, 3.2 and 2.9.

| Margin and drift scenario | $d$ per year | Threshold, $\alpha = 1$ |
| --- | --- | --- |
| SM, −20% compute / +5% drives | 0.76 | 3.4 |
| SM, −10% compute / flat drives | 0.90 | 1.6 |
| WinningPoSt, 10% a year of latency gain | 0.909 | 1.54 |

**Where we currently stand against those thresholds**

SM is 8.6 against 3.4, on the worst-scenario table (which is the one we consider), so there is room. The WinningPoSt margin is

- 1.14 against the 1.54 threshold on the report's hypothetical ASIC, so in that world it is already past its own trigger.
- 2.41 against hardware anyone can buy: at 10% a year that is about 4.7 years before it reaches the 1.54 threshold, and 9 years before it reaches 1.

Note that nobody sells the hypothetical ASIC. Moreover, market research suggests a Bitcoin miner needs at least 64 ns per hash against the 7.9 ns the hypothetical ASIC would need. This means that we currently should not trigger our policy due to that ASIC.

# References

- [Proof of Useful Space report](./Filecoin_Proof_of_Useful_Space.pdf) §5.1–5.2
- [Reyzin, ePrint 2023/1530](./Reyzin_ePrint-2023-1530.pdf) ([eprint.iacr.org](https://eprint.iacr.org/2023/1530)) Thm. 5
- Supranational, Filecoin sealing cost analysis, 2022 (last updated 2023)
- Drive prices: [diskprices.com](https://diskprices.com/), [harddiskprices.com](https://www.harddiskprices.com/), [price history](https://terabytewise.com/hdd-price-history)
- [FIP-0047](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0047.md)
- [FIP-0067](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0067.md)
- [FIP-0052](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0052.md)
- [discussion #313](https://github.com/filecoin-project/FIPs/discussions/313), [discussion #475](https://github.com/filecoin-project/FIPs/discussions/475)
- [uops.info](https://uops.info/html-instr/SHA256RNDS2_XMM_XMM.html)

## Calculations behind the motivation

- **[1] Hard-capped capacity.** 118 PiB hard-capped over the whole horizon, 76 PiB through November 2026, 87 PiB through March 2027, against 1,339 PiB of network raw power. An upgrade activating after a date reaches whatever has not yet expired, so 118 − 76 ≈ 42 PiB in early December. Cohort figures obtained via [Lily](https://lilium.sh/data/dumps/#gcp-bigquery). Spot-checked against chain state on 7 October 2026: `Filecoin.StateMinerActiveSectors` on the largest at-cap fleet returned a truncated sample of 141,114 sectors, about a fifth of that miner's 713,603 active sectors. **All** of them have 90 days or less of headroom against activation + 5 years, with the mode at 0; all are `SealProof: 9`, which is `StackedDrg64GiBV1_1`, so the sample is 8.6 PiB; all were activated in October and November 2021 and expire in October and November 2026. The cliff is therefore cap-driven rather than economic. As a cross-check on the sector size, `Filecoin.StateMinerSectorCount` on the same miner returns 722,801 live sectors, of which 713,603 active and 9,198 faulty; at 64 GiB the live count is 44.1 PiB against the 44.7 PiB the report gives for that fleet. The public Lily dumps stop at December 2022, so only its BigQuery copy or a direct chain read reproduces these figures. Two caveats on the figures: the capacity is concentrated in a handful of providers, and the H2 2021 / H1 2022 cohort that an earlier draft used as the motivation is mostly gone, with 84 PiB still alive of the 12,691 PiB it onboarded.
- **[2] The re-sealing treadmill.** [Filecoin Data Portal](https://filecoindataportal.xyz/datasets) `daily_network_metrics`, read 7 October 2026 for data to 5 October. Raw power 1,339 PiB, so 1,339/5 = 268 PiB a year of sealing to hold capacity flat, and 134 PiB at a 10 year cap. Onboarding over the trailing 365 days was 311 PiB, so 268/311 = 86%.
- **[3] Revenue comparison.** Sealing a 32 GiB sector costs $0.0346 of machine on a 3 year life ($23,300 over 3 × 224,256 sectors), so $1.11 per TiB. Over ten years that is paid twice under a 5 year cap and once under a 10 year cap, hence $0.11 per raw TiB per year. Against the Data Portal's published `block_rewards_usd_per_qap_tib_day`, $1.60 per QAP-TiB-year on a 30 day average: 6.9% for a CC sector and 0.7% for one at the 10× multiplier.

## Past Related Work and Proposals
Sector duration has been proposed, debated and changed repeatedly since Filecoin launch. 
This section collects work and proposal on the same topic and related ones.

### Lifetime cap itself

[Issue #54](https://github.com/filecoin-project/FIPs/issues/54) (Dec 2020) — "Discussion about maximum sector lifetime extending". The earliest request to raise the cap.
[Issue #56](https://github.com/filecoin-project/FIPs/issues/56) (Dec 2020) → [FIP-0014](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0014.md) (Final). Allowed V1 proof sectors to be extended to a maximum of 540 days. 
[Issue #222](https://github.com/filecoin-project/FIPs/issues/222) (Dec 2021) — "Reduce CC Sector Lifetime", a proposal in the opposite direction.

### Commitment window, which is a separate parameter

[Discussion #475](https://github.com/filecoin-project/FIPs/discussions/475) (Oct 2022) → [FIP-0052](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0052.md) (Final). Raised the maximum commitment per extension from 1.5 to 3.5 years, leaving the lifetime cap untouched. 
[FIP-0103](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0103.md) (Final) — removed the ExtendSectorExpiration method, leaving ExtendSectorExpiration2.
[Discussion #1205](https://github.com/filecoin-project/FIPs/discussions/1205) → [FIP-0110](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0110.md) (Draft) — allow shorter deal durations.

### Duration multipliers: three attempts, none adopted
Several proposals aimed to reward longer commitments with extra quality-adjusted power rather than by changing the limits. All were rejected or abandoned.

[Discussion #386](https://github.com/filecoin-project/FIPs/discussions/386) (Jun 2022), [#421](https://github.com/filecoin-project/FIPs/discussions/421) (Jul 2022), [#453](https://github.com/filecoin-project/FIPs/discussions/453) (Sep 2022) → [FIP-0036](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0036.md) (Rejected).
[Discussion #554](https://github.com/filecoin-project/FIPs/discussions/554) (Dec 2022) → [FIP-0056](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0056.md) (Rejected).
[Discussion #636](https://github.com/filecoin-project/FIPs/discussions/636) (Feb 2023) — Capped Duration Multiplier, a superset of FIP-0036 and FIP-0056.
[Discussion #476](https://github.com/filecoin-project/FIPs/discussions/476) — Retroactive sector duration multiplier; [#478](https://github.com/filecoin-project/FIPs/discussions/478) — FIP-0036 follow-up.

### Proof expiration and the security policy that bounds exposure

[Discussion #415](https://github.com/filecoin-project/FIPs/discussions/415) (Jul 2022) → [FIP-0047](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0047.md) (Superseded) — Proof Expiration & PoRep Security Policy.
[Discussion #727](https://github.com/filecoin-project/FIPs/discussions/727) (Jun 2023) → [FIP-0067](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0067.md) (Accepted) — PoRep Security Policy & Replacement Sealing Enforcement, which supersedes FIP-0047 and is the policy this proposal builds on.
[Discussion #290](https://github.com/filecoin-project/FIPs/discussions/290) (Feb 2022) → [FIP-0034](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0034.md) (Final) — set the PreCommit Deposit to a uniform value independent of sector content, which is why the deposit is evaluated at maximum quality-adjusted power.

