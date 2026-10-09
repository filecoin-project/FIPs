---
fip: "XXXX"
title: Increase maximum sector lifetime to 10 years
author: "Luca Nizzardo (@lucaniz)"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1291
status: Draft
type: Technical (Core)
category: Core
created: 2026-10-09
spec-sections:
  - section-systems.filecoin_mining.sector.lifecycle
requires: FIP-0067
---

# FIP-XXXX: Increase maximum sector lifetime to 10 years

## Simple Summary

Raise the maximum total lifetime of a sector from 5 to 10 years, for sectors sealed with PoRep v1.1, SyntheticPoRep and NI-PoRep.

## Abstract

A sector's total lifetime is capped at 5 years by `seal_proof_sector_maximum_lifetime`, a per proof type constant checked whenever a sector's expiration is set or extended. A sector that reaches it cannot be extended: its data must be sealed again into a new sector, or dropped.

This proposal changes that constant to 10 years for the affected proof types. Nothing else changes: not the maximum commitment per extension, not the market deal bounds, not pledge, fees or the proofs themselves. It also ratifies an addition to the FIP-0067 policy, so that erosion of the PoRep security margins, and not only a discrete flaw, can trigger replacement sealing.

## Change Motivation

The cap bounds how long a sector keeps proving under the cost and latency assumptions that held when it was sealed. Raising it is a request to extend that horizon, and [discussion #1291](https://github.com/filecoin-project/FIPs/discussions/1291) carries the analysis that supports doing so.

The reason to want it is retention. A sector at the cap cannot be extended at all: keeping its data and storage commitment into Filecoin means doing a new seal.

From per-sector on-chain records in September 2026, roughly 118 PiB sits at the cap across all future expiry dates, out of about 1,339 PiB of network raw byte power. For that capacity the maximum lifetime is the only lever, and it is the cheapest one, since extending is a single message where re-sealing is full capital expenditure for storage the network already holds.

A PoRep flaw is a separate matter, and is handled by retiring the proof type rather than by the cap. When that happens, an upgrade that also forbids extending old-proof sectors removes them within `MAX_SECTOR_EXPIRATION_EXTENSION` (3.5 years) whatever the maximum lifetime is; [FIP-0067](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0067.md) describes this as the current implicit policy.

## Specification

In `builtin-actors`, `seal_proof_sector_maximum_lifetime` returns `EPOCHS_IN_YEAR * 5` for one group of registered seal proof types. For that group it shall return `EPOCHS_IN_YEAR * 10`, that is **10,512,000 epochs** instead of 5,256,000.

The affected proof types are the fifteen that return 5 years today:

- `StackedDRG{2KiB,8MiB,512MiB,32GiB,64GiB}V1P1`
- `StackedDRG{2KiB,8MiB,512MiB,32GiB,64GiB}V1P1_Feat_SyntheticPoRep`
- `StackedDRG{2KiB,8MiB,512MiB,32GiB,64GiB}V1P2_Feat_NiPoRep`

The `StackedDRG*V1` proof types are **unchanged** and keep the 540 day lifetime set by [FIP-0014](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0014.md).

The following are **unchanged** by this proposal:

- `MAX_SECTOR_EXPIRATION_EXTENSION`, which stays at 1278 days (3,680,640 epochs). A provider therefore reaches 10 years through repeated extensions, each committing at most 3.5 years ahead, exactly as it reaches 5 years today.
- The built-in market's deal duration bounds, initial pledge, termination fees and fault fees.
- The proofs, their parameters, and the sealing process.

The constant is read in a single place, `validate_expiration` in the miner actor, which is reached from `ProveCommit`, from `ExtendSectorExpiration` and `ExtendSectorExpiration2`, and from `UpgradeSectorQuality`, the Solstice call that can also set a new expiration. The new value therefore applies to every sector of an affected proof type, including sectors already active at the upgrade epoch. No state migration is required.

Sectors carrying legacy FIL+ claims extend like any other. [FIP-0118](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0118.md) removed claim validation from the extension path, so `MAXIMUM_VERIFIED_ALLOCATION_TERM` is not a constraint on reaching the new ceiling.

This proposal additionally ratifies two points of policy:

1. Replacement sealing under FIP-0067 may be invoked not only on a flaw in the theory or implementation of PoRep, but also when a PoRep security margin falls below a threshold agreed by the community.
2. If either trigger leads to retiring a proof type, the upgrade that does so also blocks extensions of sectors of that proof type. This bounds their remaining life at `MAX_SECTOR_EXPIRATION_EXTENSION` and is what makes the thresholds in #1291 meaningful.

## Design Rationale

Raising only the lifetime is the smallest change that delivers longer commitments, and it reuses a path providers already follow. We propose to

- Pick 10 years rather than a smaller increase: the analysis in #1291 runs to 2036 and finds no binding constraint before then, so a staged increase would mean repeating the exercise without changing its conclusion.
- Apply the new 10 year maximum sector lifetime to existing sectors, so that sectors of the same proof type are treated alike. Restricting it to sectors sealed after the upgrade would add per sector state without improving security, since a sector's security does not depend on its age.

## Backwards Compatibility

The change requires a network upgrade, since it changes the validation of sector expirations. It is a relaxation: every expiration valid before the upgrade remains valid after it, and no sector becomes invalid.

No state migration is required. Sectors of the v1 proof types are unaffected.

Any tooling that hard-codes a 5 year ceiling when displaying or validating expirations needs updating. The likely cases are explorers, SP tooling, and any off-chain validation of `ExtendSectorExpiration2` messages.

## Test Cases

1. A sector of an affected proof type can be extended to an expiration of `activation + 10,512,000` epochs; a request for `activation + 10,512,001` is rejected.
2. A sector already active at the upgrade epoch, whose expiration sits at the old 5 year ceiling, can be extended under the new bound.
3. Reaching the new ceiling requires at least two extensions, because each remains bounded by `MAX_SECTOR_EXPIRATION_EXTENSION` from the current epoch.
4. A sector of a `StackedDRG*V1` proof type still cannot be extended beyond 540 days after activation.
5. A sector whose expiration is set through `UpgradeSectorQuality` is bounded by the same new ceiling as one extended through `ExtendSectorExpiration2`.
6. A sector carrying a legacy FIL+ claim can be extended to the new ceiling without the claim being consulted.

## Security Considerations

The full analysis is in [discussion #1291](https://github.com/filecoin-project/FIPs/discussions/1291). Three points to recall:

- **A longer lifetime does not weaken any individual sector.** A sector's security depends on the hardware available when its proofs are produced, not on when it was sealed. A nine year old sector and a new one are proved against the same hardware and have the same margins.
- **Both margins currently clear their thresholds on hardware that can be bought.** The WindowPoSt cost margin stands at 8.6 against a trigger threshold of 3.4; the WinningPoSt latency margin at 2.41 against 1.54, roughly 4.7 years of headroom at the measured rate of latency improvement. Against the hypothetical ASIC assumed by the 2023 security report the latency margin is 1.14, below its threshold, but no such device is sold. We therefore propose that the trigger be evaluated on hardware that can be purchased and measured, with the appearance of a latency-optimised design treated as an event that calls the review off-cycle.
- **The exposure after eventually retiring a proof type is bounded by `MAX_SECTOR_EXPIRATION_EXTENSION`**, not by the cap on maximum lifetime, provided the retiring upgrade blocks extensions, which this proposal makes explicit in the Specification section.

One further point, on PreCommit Deposit (PCD):

- **The PreCommit Deposit does not need to change, but its margin halves.**

  We know that an SP that passes the sealing with a malformed replica gains consensus power for the entire sector duration faking storage. For that reason, in the security report we require $PCD > BR \cdot D / (2^{10}-1)$, with $D$ being the maximum sector duration in days and $BR$ the sector's daily block reward.

  In code the deposit carries no duration term: [`pre_commit_deposit_for_power`](https://github.com/filecoin-project/builtin-actors/blob/master/actors/miner/src/monies.rs#L222-L235) returns the projected block reward for the sector over a 20 day window, from [`PRE_COMMIT_DEPOSIT_FACTOR = 20`](https://github.com/filecoin-project/builtin-actors/blob/master/actors/miner/src/monies.rs#L20-L31), evaluated at maximum quality-adjusted power ([see here](https://github.com/filecoin-project/builtin-actors/blob/master/actors/miner/src/lib.rs#L1307-L1308)). We can simplify that into $20 \cdot BR$ whenever the reward estimate is flat across the window.

  Substituting it into the bound, $BR$ cancels on both sides and the condition reduces to a statement about the cap alone: $D < 20 \cdot (2^{10}-1) = 20{,}460$ days, about 56 years. Raising the cap from 5 to 10 years halves the margin, from 11.2x to 5.6x, and leaves the condition satisfied with room.

  This concerns the interactive proof types only. NI-PoRep has no PreCommit Deposit and its 2268 challenges per layer give 128 bits of security, so the bound has no force there ([FIP-0092](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0092.md)). For these reasons we propose to leave the PreCommit Deposit untouched.

## Incentive Considerations

Pledge, the PreCommit Deposit, termination fees and fault fees are unchanged, and none of them depends on committed duration. The Security Considerations section explains why the PreCommit Deposit remains sufficient under the longer cap.

The change removes a recurring cost rather than adding a reward: a provider keeping the same data no longer pays for a second seal at the five year mark. At 2026 prices that is roughly \$0.11 per raw TiB per year, under 1% of block reward for a sector carrying verified data, so the effect on provider income is small and the case rests on capacity retention.

Providers committing for longer lock pledge for longer and take on the risk of having to perform replacement sealing, or terminate, if the FIP-0067 policy is invoked. Committing longer remains optional.

## Product Considerations

SPs can commit storage to the network for up to 10 years through repeated sector extensions, and this can happen without re-sealing.

## Implementation

A one line change to [`seal_proof_sector_maximum_lifetime`](https://github.com/filecoin-project/builtin-actors/blob/master/actors/miner/src/policy.rs#L89-L108) in `builtin-actors`, plus tests. No migration.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
