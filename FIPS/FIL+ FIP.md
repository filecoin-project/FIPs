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

This proposal aims to reduce complexity and friction in the Filecoin ecosystem, encourage the onboarding of real data, and foster a healthier growth environment for the Filecoin network. It does this by setting the QAP multiplier to 1x for all new deals and sector extensions, so that the network is no longer dependent on a centralized intermediary to pick and choose what data to onboard. It follows decentralization best practices enacted by both Bitcoin and Ethereum, aligns with Filecoin's mission to provide useful storage, and maintains the network's core values of [decentralization](https://github.com/filecoin-project/FIPs/blob/master/mission.md). 

> - The network is not dependent on any one party, e.g., not dependent on a company, foundation, or other organization to continue operating.
> - No centralized parties can control, stop, or censor the network, its operation, or its participants.
> - Users and providers are not controlled or governed by powerful intermediaries (unlike markets like Uber or Airbnb).
> - Refers to the decentralization movement of 2015+, including IPFS, Bitcoin, Ethereum, and more.

## Change Motivation

The Fil+ program's current implementation has created complexities and challenges that hinder the growth trajectory of the Filecoin network. By phasing out the Fil+ multiplier, this proposal seeks to restore the integrity of the Filecoin blockchain and alleviate issues related to consensus overload, complexity, pledge availability, poor UX, loss of privacy/censorship resistance, and other problems. 

Much of the details are outlined in the initial [discussion](https://github.com/filecoin-project/FIPs/discussions/774), which can be summarized as following: by imposing a permissioned layer on top of an already cumbersome core protocol, the network is suffering from a rapid decline of RBP as a result of skewed incentives, which in turn compound the negative impact on network value and creating an environment that encourages SPs to collude and game the network incentives. 

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
    /// >>> Target value <<<
    pub static ref VERIFIED_DEAL_WEIGHT_MULTIPLIER: BigInt = BigInt::from(100);
}
```

2. **Existing Deals**: For sectors with existing Fil+ deals (DC sectors), the current Quality Adjusted Power (QAP) will remain until these deals expire. Nothing technical is expected to be changed for this particular specification.

3. **Sector Extension**: Upon sector extension, the 10x multiplier will no longer be applicable after the upgrade.

## Design Rationale

There are many ways to achieve the stated goal of the FIP discussion. After filtering out some of the less practical ones, it comes down to either prevent DC from being minted or reduce the multiplier for DC deals. Multiplier reduction is chosen not only for its simplicity in implementation but also avoiding the debate of wether turning off DC minting should be governed by Fil+ program or not.

## Incentive & Product Considerations

The proposed change would likely not detour the already downward decline of RBP in short term but would highly likely allow L1 to capture much more value in the long term in terms of tangible resources like hardwares and talents being employed to support RBP of the network. 

The FIP may increase the likelyhood of reduction in power onboarding, consequent loss of RBP meaning further reduced blockrewards due to baseline minting model, the supply inflation resulting from expiring sectors with no onboarding and **significantly** lower initial pledge requirements due to [QAP crossing baseline](https://github.com/filecoin-project/FIPs/discussions/847) until the market finds equilibrium price again with new readjusted mining cost. Before then miners will likely be able to enjoy a higher Fil on Fil return to incentivize the return of RBP to catch up the baseline. The CEL report [here](https://medium.com/cryptoeconlab/resilience-of-the-filecoin-network-d7861ee9986a) shows the resilience properties of the Filecoin network in such case. Though we would like to point out that of course all such models have limitations.

Some of the incentive considerations are very similar to [FIP0078](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0078.md) as the proposed change rooted from same core decentralization value they share. 

The proposed change removes Fil+'s incentive for the onboarding of non-random data. As a result, it's anticipated that the onboarding rate of non-random data may decrease. It remains unclear how much of the data currently incentivized by Fil+ is not in compliance with the program's goals.

Following this proposed change, the primary impetus for SPs to onboard data will originate from outside the protocol itself. It could include direct payments from storage clients or new incentive models implemented in FVM contracts.

Because all sectors will have the same multiplier (1x), we expect miners to charge more for storing user data. So users whose data is currently stored via Fil+ deals will probably have to pay more for storage after the sector containing their data expires. We suggest existing users discuss pricing changes with their SPs or the intermediary who handled deal-making for them. It is unlikely that user data will be dumped before sector expiry since a miner would have to pay a termination fee and re-seal a new sector.

It is hard to estimate how much user demand Filecoin will lose in the short run, (both demand for data already stored on the network and for data that potentially could have been onboarded in the future). There are two reasons for this: first, we don't know how much of the data stored via Fil+ deals has an actual user behind it; second, because Fil+ distorted price discovery, we don't know what users are willing to pay for Filecoin storage and what miners are willing to accept.

## Security Considerations

Depending on which school of thoughts you think blockchain security works for Filecoin network, one may reach different security consideration.

If your views on network consensus seurity aligns with the explorations released [here](https://pl-strflt.notion.site/2023Q3-Cost-of-Consensus-Security-Hardware-bda873f0c8a74387abeccd8c722abd59?pvs=4) and [here](https://pl-strflt.notion.site/2023Q3-Cost-of-Consensus-Security-Pledge-d9374ec5b68244c6b50fcb8c16ec113c?pvs=4). The proposed change may be viewed as lowering network consensus security because lowered pledge cost in the network attack strategy model of HDDCost + StoragePledge + FutureEarnings. However, the risks will likely be mitigated by the fact that **significantly** lowered initial pledge requirements will likely to incentive more hardwares to be onboarded to secure the network, which previously peaked at 17 Eib as opposed to 8 Eib right now increasing the cost to attack. 

There are also views that shared by some who see consensus seurity is POS agnostic as there are already large token holders like Protocol Labs, Filecoin Foundation, big whales that may become single point of failure to attacks. By that token, attack model is reduced to HDDCost + SealingCost + GasCost which the proposed change will likely to boost the network security as explained in the [QAP crossing baseline](https://github.com/filecoin-project/FIPs/discussions/847) scenario.

In the worst case of substantial power dropping, from the same [CEL report](https://medium.com/cryptoeconlab/resilience-of-the-filecoin-network-d7861ee9986a) above Filecoin will likely be resilient to power shocks...

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
