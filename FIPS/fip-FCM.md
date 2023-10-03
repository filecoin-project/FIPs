```---
fip: "FIP-XXXX"
title: "Removing Restriction to Access to Multiplier and Allowing Unrestricted Minting of Datacap"
author: Fatman13 (@Fatman13), flyworker (@flyworker), stuberman (@stuberman), Eliovp (@Eliovp), dcasem (@dcasem), and The-Wayvy (@The-Wayvy)
Discussions-to: https://github.com/filecoin-project/FIPs/discussions/844
status: Draft
type: Technical
category: Core
created: 2023-08-22
requires: 
replaces: FIP-0003
```

## Simple Summary
This proposal removes restrictions on access to the 10X multiplier, allowing any actor to mint Datacap.

## Abstract
The Fil+ program intended to compensate miners for storing non-random data on Filecoin. It was hoped that these datasets would increase the utility of the network and thereby attract paying users. Fil+ did succeed in accelerating the development of data-onboarding tools. It also attracted users to experiment with storing their data on Filecoin, and it is possible that even after subsidies run out some of these users will pay miners enough to have their data continue to be stored on Filecoin. However, the notary system used by 3/4 of Fil+ programs is inefficient, not objective, and riddled with perverse incentives. This proposal removes the permissioned, off-chain pathways to the 10x multiplier, and makes it available to all actors who stake the required collateral.

## Change Motivation≠
The current Fil+ implementation, though well-intentioned, has incentivized behaviors that do not drive value to Filecoin. In order to get the 10x multiplier, miners fabricate datasets and source  'real' data regardless of its monetizability. They also lobby gate-keepers of the multiplier, notaries and the governance team, in order to increase the chances of their Fil+ applications getting approved and to get better access to Fil+ deals applied for by other miners. This in turn has led to rent-seeking behaviors on the part of notaries.   

By removing notaries we will instantly eliminate all fraud, bribery and other harmful behavior in Filecoin. Under this proposal, miners can get the 10x multiplier as long as they post the required collateral, regardless of what kind of data they store, so there will be no reason for a miner to pretend their data is something that it's not. We'll also have complete certainty that all storage deals involve a real user and useful storage since no miner would go through the trouble of storing non-random data in a sector unless they were paid to do so, and no user would pay for storage unless they believed in its utility.   

The more transparent, predictable and fair Filecoin that we propose will attract new miners to the network, end malinvestment into the storage of unmonetizable datasets, and free up a large amount of money and man-hours that can be spent on more productive endeavors like improving the tech and business development with paying users. 

## Specification
 **Change in the Datacap Actor's Mint Function**: Alter the DataCap actor's mint() function to remove the restriction that the caller must be the "governor" (the verified registry actor). Allow any actor to mint datacap.

 **Snap Deals**
When an SP only wants to commit capacity, but do so with a high multiplier, the verified allocation they claim must specify a data CID, which must of course match the committed data. (Before direct onboarding, they would do a full-on deal with the built-in market; after direct onboarding, they can just directly commit the data). This would have the effect of giving the sector verified deal weight, and making it not appear to be CC, and therefore not eligible for subsequent snap deal with client data.

We will work around this by detecting explicit commitments to the "Zero" unsealed CID, which is the same unsealed CID that CC sectors use. Even though this unsealed CID is not stored on chain, we can set a flag in sector on-chain info to indicate that the sector data is zero, despite having verified deal weight, and that it's therefore a valid target for snap deals.

## Design Rationale
While more comprehensive solutions might be considered in the future, this FIP offers an immediate, simpler approach. 

Allowing any actor to mint datacap is the simplest change to the current protocol that ends human gating of datacap issuance. Datacap can then be transferred to the verified registry to create a datacap allocation. Storage Providers can claim the allocation assigned to them and get the associated 10x deal multiplier when onboarding the data piece.
After this change, the verified registry and datacap actors will be mostly obsolete. Allowing unlimited datacap does not create any complexity. Future protocol improvements could remove these actors and support direct specification of a multiplier when onboarding to further simplify the protocol and reduce cost.

## Backwards Compatibility
This proposal does not change any chain state or method interfaces so is backwards compatible to all clients. All existing workflows will continue to work, and this change is also compatible with direct onboarding. A network upgrade is required to deploy the new actor code.

After this upgrade, Storage Providers (SPs) can engage with any deal, whether Fil+ or not by minting Datacap. Deals will still need the `verified` flag set to true, but clients will be able to freely do this because they can mint the required datacap.

## Test Cases
Test that an account actor that is not a notary can mint datacap
Test that a non-account actor can mint datacap

## Security Considerations

Substitution Risk refers to the possibility that once DC is available in unlimited quantities, miners might replace all their CC sectors with DC, thereby maintaining their QAP while unplugging 90% of the hardware they had committed to the network.

Such behavior would be equally likely if the distribution of DC and Fil+ deals was more efficient than it is today (even if DC/Fil+ deals were limited to "good" data and "observant" SPs). It won't change the behavior of SPs who already have easy access to FIL+ deals; It could change the behavior of SPs who do not, but it's hard to say in what direction: the risk of substitution is offset by the possibility that SPs who currently can't get FIL+ deals in the quantity they desire will increase their onboarding rates once random data is profitable again. 

Substitution risk is also mitigated by the fact that the expiration of CC sectors is a well-established trend. Substitution may even help to retain some hardware that would otherwise completely drop off the network.

In order to get 20% of QAP, an attacker who only has CC would need about 600 petabytes of RBP and about 40,000,000 FIL. To convert 600 PB of CC to 10x sectors via snap deals would take over 10,000 sealers working non-stop for a week. This is a worst-case analysis that assumes the attacker is the only one to substitute CC for 10x sectors; in reality, this is extremely unlikely.

The effects of this change on RBP, QAP and network security were also analyzed by CEL [in this report](https://hackmd.io/zp-40inqSny5HMqmTSOKxw?view)


## Incentive Considerations
The proposed change removes Fil+'s incentive for the onboarding of non-random data. As a result, it's anticipated that the onboarding rate of non-random data may decrease. It is still uncertain how much of the data currently incentivized by Fil+ is fake.

With the removal of this restriction, effectively-empty sectors can now benefit from a multiplier. This adjustment allows Storage Providers (SPs) to onboard random data at a profit, potentially leading to an increase in such sectors being onboarded and growth in RBP.

Following this amendment, the primary impetus for SPs to onboard data will originate from outside the protocol itself. It could include direct payments from data clients or new incentive models implemented in FVM contracts.

Because all sectors will have the same multiplier, we expect miners to charge more for storing user data. So users whose data is currently stored via Fil+ deals will probably have to pay more for storage after the sector containing their data expires. We suggest existing users discuss pricing changes with their SPs or the intermediary who handled deal-making for them. It is unlikely that user data will be dumped before sector expiry since a miner would have to pay a termination fee and re-seal a new sector. 

Data onboarded after the transition to free multipliers will not face the risk of price hikes or dumping.  

It is hard to estimate how much user demand Filecoin will lose in the short-run, (both demand for data already stored on the network, and data that potentially could have been onboarded in the future). There are two reasons for this: first, we don't know how much of the data stored via Fil+ deals has an actual user behind it, second, because Fil+ distorted price discovery, we don't know what users are willing to pay for Filecoin storage and what miners are willing to accept.  

## Product Considerations

Removing the notary system will streamline data onboarding for users as well as lower costs and uncertainty for miners. 

The Fil+ team and ecosystem participants will be free to build deal markets on the FVM or Filecoin L2s. These can be either permissioned or permissionless, and they will have to compete with one another for users. 

The proposed changes give SPs more flexibility, allowing them to select a pledge-to-hardware ratio best aligned with their operational costs and deal-flow. This enhanced flexibility means SPs can make more rational decisions based on their individual circumstances.

The choices SPs make would largely depend on their comparative cost of obtaining hardware and pledge tokens, combined with their revenue mix between block rewards and storage payments. SPs with clients offering better pay rates may consistently opt for the minimum pledge. This decision could improve their unit economics, particularly when other providers choose to pledge higher amounts to increase their per-TiB rewards. In this landscape, the higher pledge by some becomes an advantage for those opting for a lower pledge.

It is expected that users will now have to pay to get their data stored on Filecoin, meaning the applications and services developed on Filecoin will cater to real demand, rather than the speculation and preferences of a small group of non-users. This should shorten the time it takes for Filecoin to find Product Market Fit.

## Implementation
-Refer to the specific change [here](https://github.com/filecoin-project/builtin-actors/blob/485778aa23f742af1d1aa57a8f6608a0698d8ee7/actors/datacap/src/lib.rs#L161).


## TODO
- Discuss possible deprecation of the Verifreg Actor and Datacap in future updates.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
