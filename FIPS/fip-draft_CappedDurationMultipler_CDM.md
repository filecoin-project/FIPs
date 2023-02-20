---
fip: "to be assigned"
title: "Capped Duration Multiplier (CDM)"
author: Peter R (@ribasushi)☨  Patrick D (@f8-ptrk)  (via superset) Fip36/56 authors
discussions-to: https://github.com/filecoin-project/FIPs/discussions/636
status: Draft
type: Technical
created: 2022-02-20
requires: "FIP-0047"
replaces: "FIP-0056, FIP-0052, FIP-0036"
---

☨ The original genius who came up with the idea seems to have chosen to remain anonymous at this time.

## Simple Summary

- A Capped Duration Multiplier (CDM) policy is introduced for all new and existing sectors on the filecoin network.
- A sector committed for a longer time receives progressively higher Quality Adjusted Power, compared to a sector with shorter commitment, all else being equal.
- The Duration Multiplier is a capped multiplicative on the existing Quality Multiplier incentive (Filecoin Plus incentive).
- The maximum Quality Multiplier available to any sector **remains 10x**. This FIP merely introduces an additional source of multiplication, which can be combined with the existing one, up to a limit.
- Sectors with higher Quality Adjusted Power will require higher initial pledge collateral.
- The termination fee cap will scale with the duration multiplier.
- The minimum sector duration time will increase from 6 months to 1 year and the maximum sector duration will increase from 1.5 years to a little over 10 years. The upper bound of [Deal Duration Bounds](https://github.com/filecoin-project/builtin-actors/blob/b5c101ab94f562ba43c1eca31bd1e73c6fc35794/actors/market/src/policy.rs#L33-L35) will increase to a little over 10 years as well.
- The CDM policy will apply at sector commitment, extension, and replica update

## Change Motivation

The excitement around [Filecoin's foray into smart contracts, starting with direct EVM support on its L1 chain](https://www.coindesk.com/business/2023/02/17/filecoins-fil-token-jumps-more-than-30-sparking-interest-in-virtual-machine-launch/) can not be overstated. At the same time [the network continues losing RawBytePower](https://medium.com/cryptoeconlab/filecoin-network-crosses-baseline-from-above-585b696083af), driven by the confluence of multiple external and internal factors. [FIP56](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0056.md) and its older twin [FIP36](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0036.md) are proposals put forward by CryptoEcon Lab @ PL designed to enhance and stabilize the Filecoin economy. We propose a **superset** of the ideas developed during SDM research, resulting in the "Capped Duration Multiplier" (CDM). We believe CDM allows for a radically more balanced and fair Filecoin network, unlocking more use cases and as a result requiring fewer adjustments in the future.

Unlike virtually any other major L1, the Filecoin "proof of probability"-driven consensus derives from a SNARK-based, energy-efficient account of posession of physical goods: storage space. The primary authors of this FIP hold a strong belief that this unique feature of the Filecoin consensus is extremely valuable. This proposal provides a solution to allowing for two coexisting business models:
  1. Storage Providers can continue to specialize in the evolution of decentralized data services, thus maximizing their Fil+ exposure.
  2. Storage Providers also have the rational option to specialize in securing the consensus of a smart-contract-capable L1 blockchain, while also providing [sealing as a service](https://github.com/filecoin-project/lotus/discussions/9079) and potentially discovering novel ways to monetize the security substrate itself (reminder: what counts is how much capacity there is, not what is stored in it).

Additionally SPs are able to mix and match the two business models, which in turn creates a viable market for **small piece-size storage contracts**. This eliminates one of the significant hurdles data DAOs face at present.

## Incentive Considerations

The [solution space of combining the two modes of operation](https://www.wolframalpha.com/input?i=3d+plot&assumption=%7B%22F%22%2C+%223DPlot%22%2C+%223dplotupperrange2%22%7D+-%3E%221%22&assumption=%7B%22F%22%2C+%223DPlot%22%2C+%223dplotupperrange1%22%7D+-%3E%2210.15%22&assumption=%7B%22MC%22%2C+%223d+plot%22%7D+-%3E+%7B%22Calculator%22%7D&assumption=%7B%22F%22%2C+%223DPlot%22%2C+%223dplotfunction%22%7D+-%3E%22%3D+MIN%28+10%2C+%28+max%281%2C+y-1.5%29+*+%28+1-x+%2B+10*x+%29+%29+%29%22&assumption=%7B%22F%22%2C+%223DPlot%22%2C+%223dplotvariable1%22%7D+-%3E%22y%22&assumption=%7B%22F%22%2C+%223DPlot%22%2C+%223dplotlowerrange1%22%7D+-%3E%221%22&assumption=%7B%22F%22%2C+%223DPlot%22%2C+%223dplotvariable2%22%7D+-%3E%22x%22&assumption=%7B%22F%22%2C+%223DPlot%22%2C+%223dplotlowerrange2%22%7D+-%3E%220%22) is illustrated by the following simplified table: an approximation of the optimal behavior of a rational SP with variable access/exposure to Fil+ data-holders.

|Fil+ Exposure|Min Rational Duration|Effective QAP|
|---|---|---|
|100%|MIN_SECTOR_DURATION|10x|
|80%|2.72 years|10x|
|75%|2.80 years|10x|
|50%|3.32 years|10x|
|33%|4.02 years|10x|
|25%|4.58 years|10x|
|20%|5.08 years|10x|
|15%|5.76 years|10x|
|10%|6.77 years|10x|
|5%|8.40 years|10x|
|2%|9.98 years|10x|
|1%|MAX_SECTOR_DURATION|9.43x|
|0%|MAX_SECTOR_DURATION|8.65x|

The table demonstrates a **path to sustainable CC operations** even in face of the enormous gravity of Fil+, revitalizing the no longer viable CC business model, and preserving the current Fil+ centric business-model at the same time. This in turn reverses the trend of raw-power loss bringing us back above the baseline (crossed on Feb 9th) and simultaneously dramatically relieves pressure on Fil+ abuse and governance.

## Design Rationale

The core insights about Fil+ leading to the CDM are:

- The Fil+ multiplier was introduced at network genesis as an efficient mechanism incentivizing storage provider engagement with an independent data owner. While the 10x parameter was justified at launch, it is extremely overpowered in the current state of the network. The use of Fil+ at about 5% of the overall capacity has already set off a race to the bottom, leading to rampant abuse of the Fil+ system [as amply documented in recent Fil+ disputes.](https://github.com/filecoin-project/notary-governance/issues/819) Giving Fil+ the ability to potentially be further SDM-boosted by an effective **45x factor** compared to a plain Data/CC sector, would make the network completely uneconomical and irrational for anything but Fil+, which in turn severely weakens the incentive's original purpose.

- Engagement between SPs and legitimate Fil+ holders remains extraordinarily difficult. About 80% of the hurdles are technological, in the form of inefficient or outright non-existent software and nascent-at-best playbooks and brokers that a medium-to-large data-holder could leverage. By most optimistic estimates the status quo will persist for at least the remainder of 2023. The remaining 20% are economic in nature. It is believed that many of the liquidity problems can be alleviated by smart contracts, but until the F(E)VM is widely available and stable it is difficult to predict an outcome.

- Even if the current state of tooling was not a factor, converting the current capacity-carrying part of the network to data-carriers would require an enormous movement of data between holders and SPs. The majority of the raw power securing the network is not physically equipped to host high volume market nodes, placing further pressure to seek out schemes abusing Fil+, just to stay afloat.

- As use, legitimate and otherwise, of Fil+ grows, the network will continue losing raw capacity, posing a risk to the security required of a F(E)VM-capable L1 blockchain. It is a strong belief of the CDM proponents that consensus-pledge staking as implemented in Filecoin is insufficient to provide the required level of security, posing a significant challenge to the future of the F(E)VM.

Additionally sourcing ⨎ for pledge collateral remains difficult, contrary to what one would expect at current circulating supply levels. We believe this is caused to a large extent by the presence of multiple circulation spheres: one aligned with decentralized storage, while another aligned with traditional consensus block-producers. Provided this hypothesis is correct, this would add another avenue to increased network TVL, and thus increased price stability.

## Specification

This proposal is a strict superset of the specification outlined in https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0056.md. Common parts are not reproduced here during the discussion period to simplify things. The only additions are:

1. Increase [MAX_SECTOR_EXPIRATION_EXTENSION](https://github.com/filecoin-project/builtin-actors/blob/v9.0.3/runtime/src/runtime/policy.rs#L367), and the corresponding [max_prove_commit_duration](https://github.com/filecoin-project/builtin-actors/blob/v9.0.3/actors/miner/src/policy.rs#L84-L85) to 3700 fildays (~10.13 years)

2.  Cap the maximum QAP available to a sector, by defining CDM as:

```
    FILP_QAP_FACTOR=10          // same as mainnet
    MAX_SECTOR_QAP=10           // !!!NEW!!!
    SDM_SLOPE=1x-per-360days    // same as FIP56/36
    SDM_LAG=540days             // same as FIP56
    MIN_SECTOR_DURATION=360days // same as FIP56

    SECTOR_QAP = MIN(
      MAX_SECTOR_QAP,
      (
        MAX( MIN_SECTOR_DURATION, ( SECTOR_DURATION - SDM_LAG ) )
          *
        SDM_SLOPE
          *
        (
          SECTOR_SIZE - FILP_PIECES_SIZE      // CC or Data
              +
          FILP_QAP_FACTOR * FILP_PIECES_SIZE  // Fil+ client data
        )
      )
    )
```

TODO: copy/fill in [the rest](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0056.md#specification) if FIP receives viable community support.

## Product Considerations

The CDM exponentially increases the experimentation space just in time to be able to support the opportunities afforded by the F(E)VM. It provides space for complementary business models, with ability to transition between them [by design](https://github.com/filecoin-project/FIPs/discussions/538). A short summary of benefits from discussion above:

- Providing capacity (filled with data or CC), and associated expertise remains a viable business model
- Ability to compete with Fil+ on near-equal footing **instantly opens doors to paid storage contracts**
- Avenue to rationally grow the consensus security and TVL of the network until data-transfer technology catches up
- **Enhances decentralization** by making it viable to operate an SP in a space-rich yet bandwidth-constrained environment
- Pressure on the **Fil+ program reputation** and governance is drastically reduced (both from legitimate clients and otherwise)
- Archival needs of business clients worldwide are adequately met (🇺🇸 IRS: 7y, 🇬🇧 legal: 6y, 🇩🇪 business records: 10y)
- The partially-Fil+ sector model becomes very lucrative, creating a viable market for **small piece-size storage contracts**

## Backwards Compatibility

Same as [FIP56](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0056.md#backwards-compatability)

TODO: copy/fill in [the rest](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0056.md#backwards-compatability) if FIP receives viable community support.

## Test Cases

N/A

## Security Considerations

The [security considerations from FIP56](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0056.md#security-considerations) apply in full, mainly based on the innovation of https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0047.md. Additionally having groups with variable source of consensus makes it even less likely that one group will be able to dominate the others.

TODO: copy/fill in [the rest](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0056.md#security-considerations) if FIP receives viable community support.

## Implementation

See Specifiation Section

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
