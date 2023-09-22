---
fip: "0000"
title: Phasing Out Fil+ and Restoring Deal Quality Multiplier to 1x
author: "@Fatman13, @ArthurWang1255, @stuberman, @Eliovp, @dcasem, @The-Wayvy"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/774
status: Draft
type: Technical
category: Core
created: 2023-08-03
---

## Summary

This proposal eliminates the 10X multiplier associated with Fil+ deals, effectively restoring the deal multiplier to its raw byte value.

## Abstract

This proposal aligns with Filecoin's mission to provide useful storage and maintains the network's core values of [decentralization](https://github.com/filecoin-project/FIPs/blob/master/mission.md) like... 

> - The network is not dependent on any one party, e.g., not dependent on a company, foundation, or other organization to continue operating.
> - No centralized parties can control, stop, or censor the network, its operation, or its participants.
> - Users and providers are not controlled or governed by powerful intermediaries (unlike markets like Uber or Airbnb).
> - Refers to the decentralization movement of 2015+, including IPFS, Bitcoin, Ethereum, and more.

It aims to reduce complexity and friction in the ecosystem, encourage the onboarding of real data, and foster a healthier growth environment for the Filecoin network. We will achieve this by cutting down QAP multiplier to 1x for all so that the network is not dependent on a centralized intermediary to pick and choose what kind of data to onboard to the network and follow the best decentralization practices setup by both Bitcoin and Ethereum. 

## Change Motivation

The Fil+ program's current implementation has created complexities and challenges that hinder the growth trajectory of the Filecoin network. By phasing out the Fil+ multiplier, this proposal seeks to restore the integrity of Filecoin blockchain and alleviate issues related to consensus overload, complexity, pledge availability, poor UX, loss of privacy/censorship resistance, and other problems outlined in the initial discussion[LINK].

## Specification

### Elimination of the 10X Multiplier

1. ***Reset DC multiplier***: Set the [power/weight multiplier](https://github.com/filecoin-project/builtin-actors/blob/fe72aa8e14bc566d661d47625dcdbdd960bf4525/actors/miner/src/policy.rs#L33) for verified deals to 1.

```rust
lazy_static! {
    /// Quality multiplier for committed capacity (no deals) in a sector
    pub static ref QUALITY_BASE_MULTIPLIER: BigInt = BigInt::from(10);

    /// Quality multiplier for unverified deals in a sector
    pub static ref DEAL_WEIGHT_MULTIPLIER: BigInt = BigInt::from(10);

    /// Quality multiplier for verified deals in a sector
    /// >>> This value <<<
    pub static ref VERIFIED_DEAL_WEIGHT_MULTIPLIER: BigInt = BigInt::from(100);
}
```

2. **Existing Deals**: For sectors with existing Fil+ deals (DC sectors), the current Quality Adjusted Power (QAP) will remain until these deals expire. Nothing technical is expected to be changed for this particular specification.

3. **Sector Extension**: Upon sector extension, the 10x multiplier will no longer be applicable after the upgrade.

## Design Rationale

There are many ways to achieve the stated goal of the FIP discussion. After filtering out some of the less practical ones, it comes down to either prevent DC from being minted or reduce the multiplier for DC deals. Multiplier reduction is chosen not only for its simplicity in implementation but also avoiding the debate of wether turning off DC minting should be governed by Fil+ program or not.

## Incentive & Product Considerations

The FIP would likely not detour the already downward decline of RBP in short term but would highly likely allow L1 to [capture much more value](https://filecoinproject.slack.com/archives/CEHTVSEG6/p1692722289461299) in the long term. The FIP may increase the likelyhood of reduction in onboarding, consequent loss of RBP meaning further reduced blockrewards due to baseline minting model, the supply inflation resulting from expiring sectors with no onboarding and increasing initial pledge requirements (further compounding unprofitability) until the market finds equilibrium price again with new readjusted mining cost. The CEL report [here](https://medium.com/cryptoeconlab/resilience-of-the-filecoin-network-d7861ee9986a) shows the resilience properties of the Filecoin network in such case. Though we would like to point out that of course all such models have limitations.

- **Storage Providers (SPs)**: SPs need to adjust to the new multiplier rules and consider their strategies for attracting non-Fil+ deals.
- **Data Clients**: The transition may affect existing clients using Fil+. New mechanisms that are not embedded in Filecoin’s core protocol to promote real data storage can be developed.
- **Existing Deals**: Existing Fil+ deals will remain unaffected until their expiration.The extra pledge will be returned once the sector is terminated or expires. 
- **Network Stability**: Care must be taken to ensure network stability during the transition, especially when handling existing deals.

## Security Considerations

This FIP does not introduce new security concerns. From the same [CEL report](https://medium.com/cryptoeconlab/resilience-of-the-filecoin-network-d7861ee9986a) above Filecoin is resilient to power shocks...

> What does resilience mean? Merriam-Webster defines resilience as the ability to recover from or adjust easily to misfortune or change. Resilience is relevant to many aspects of a cryptoeconomy like Filecoin; examples include 51% attacks, Sybil attacks, and Finney attacks, to name a few. 

However, it is critical to ensure that the transition is handled securely, particularly when dealing with existing sectors.

## Afterwards
Fil+ team and many more customized deal markets will be developed on L2 of Filecoin in either permissioned or permissionless manners in an open and fair market competition. 
By way of example. If the community consensus determined the end of multipliers in NFV21 (proposed Nov 2023) upgrade,  then sectors with multipliers would conclude at the end of May 2025.



## References

* [Initial Discussion](https://github.com/filecoin-project/FIPs/discussions/774)
* [FIP-003](link_to_FIP-003)

Why pick option1 over option2:<br> 
-https://github.com/filecoin-project/FIPs/discussions/774#discussioncomment-6656805<br>
-https://github.com/filecoin-project/FIPs/discussions/774#discussioncomment-6664701<br>
-https://github.com/filecoin-project/FIPs/discussions/774#discussioncomment-6677630<br>

Why 10x for all, a soft landing, is not ideal: <br>
-https://github.com/filecoin-project/FIPs/discussions/774#discussioncomment-6677066<br>
-https://github.com/filecoin-project/FIPs/discussions/774#discussioncomment-6654608<br>
-https://github.com/filecoin-project/FIPs/discussions/774#discussioncomment-6655524<br>

Why no more multiplier should be applied in the Filecoin core protocol: <br> 
-https://github.com/filecoin-project/FIPs/discussions/774#discussioncomment-6686571 <br>
-https://github.com/filecoin-project/FIPs/discussions/774#discussioncomment-6686564 <br>
-https://github.com/filecoin-project/FIPs/discussions/774#discussioncomment-6664701 <br>
-https://github.com/filecoin-project/FIPs/discussions/774#discussioncomment-6644045 <br>


## Copyright

This work is licensed under the Apache License, Version 2.0.

---

This FIP provides a detailed and structured plan to phase out Fil+ by changing the deal quality multiplier, adhering to the chosen option and the principles outlined in the initial discussion. Implementing this proposal will need careful planning and consideration to ensure a smooth transition and alignment with Filecoin's long-term objectives.
