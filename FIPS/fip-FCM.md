```---
fip: "FIP-XXXX"
title: "Removing Restriction to Access to Multiplier and Allowing Unrestricted Minting of Datacap"
author: Fatman13 (@Fatman13), flyworker (@flyworker), stuberman (@stuberman), Eliovp (@Eliovp), dcasem (@dcasem), and The-Wayvy (@The-Wayvy)
Discussions-to: https://github.com/filecoin-project/FIPs/discussions/774
status: Draft
type: Technical
category: Core
created: 2023-08-22
requires: 
replaces: FIP-0003
```

## Simple Summary
This proposal removes restrictions on access to the 10X multiplier in Fil+ deals, allowing any actor to mint Datacap.

## Abstract
The Fil+ program intended to compensate miners for storing non-random data on Filecoin. It was hoped that these datasets would increase the utility of the network and thereby attract paying users. Fil+ did succeed in accelerating the development of data-onboarding tools. However, the notary system used to execute Fil+ has not brought paying data clients to Filecoin, and is riddled with perverse incentives. This proposal removes the permissioned, off-chain pathways to the 10x multiplier, and makes it available to all actors who stake the required collateral.

## Change Motivation≠
The current Fil+ implementation, though well-intentioned, has incentivized behaviors that do not drive value to Filecoin. The dominant strategy for miners has rested on two pillers: first, the fabrication of datasets and sourcing of 'real' data with no concern for monetizability, and second, developing relationships with gate-keepers of the multiplier, notaries and the governance team, in order to increase the chances that their Fil+ applications get approved and to get access to Fil+ deals applied for by other miners. Decisions about what data to upload to Filecoin have been made exclusively by miners, notaries and the governance team, rather than real, paying users. In fact, the miners themselves have become the 'users', and go to great lengths to secure the power multiplier.  

By removing notaries we will instantly eliminate all fraud, bribery and other harmful behavior in Filecoin. Under this proposal, miners will obtain a 10x multiplier as long as they post the required collateral, regardless of what kind of data they store. So there will be no reason for a miner to pretend their data is something that it's not. We'll also have complete certainty that all storage deals involve a real user and useful storage, since no miner would go through the trouble of storing non-random data in a sector unless they were paid to do so, and no user would pay for storage unless they believed in its utility.   

This proposal also resolves another community concern: the over-centralization of power in the hands of notaries and the Filecoin Plus governance team. It returns the chain to full permissionlessness, giving all investors and miners confidence that they are competing on a level playing-field. This will attract new miners to the network and drive down the price of storage.

Last but not least, by making the permissionless part of the network profitable again, miners and users are freed from the relatively slow, high-friction UX of Filecoin Plus.


## Specification
 **Change in the Datacap Actor's Mint Function**: Alter the DataCap actor's mint() function to remove the restriction that the caller must be the "governor" (the verified registry actor). Allow any actor to mint datacap.

## Design Rationale
While more comprehensive solutions might be considered in the future, this FIP offers an immediate, simpler approach. 

Allowing any actor to mint datacap is the simplest change to the current protocol that removes the Fil+ process restrictions on datacap issuance. Datacap can then be transferred to the verified registry to create a datacap allocation. Storage Providers can claim the allocation assigned to them and get the associated 10x deal multiplier when onboarding the data piece.
After this change, the verified registry and datacap actors will be mostly obsolete. Allowing unlimited datacap does not create any complexity, but does make it possible to remove some. Future protocol improvements could remove these actors and support direct specification of a multiplier when onboarding to further simplify the protocol and reduce cost.

## Backwards Compatibility
This proposal does not change any chain state or method interfaces so is backwards compatible to all clients. A network upgrade is required to deploy the new actor code.

After this upgrade, Storage Providers (SPs) can engage with any deal, whether Fil+ or not by minting Datacap. Deals will still need the `verified` flag set to true, but clients will be able to freely do this because they can mint the required datacap.


## Test Cases
Test that an account actor that is not a notary can mint datacap
Test that a non-account actor can mint datacap

## Security Considerations
This FIP, though providing simplified access, doesn't introduce new security threats. 

## Incentive Considerations
The proposed change removes Fil+'s incentive for the onboarding of non-random data whose utility has been affirmed by off-chain, human notaries. As a result, it's anticipated that the onboarding rate of non-random data may decrease. The extent to which data currently incentivized under this mechanism is fraudulent remains uncertain.

With the removal of this restriction, effectively-empty sectors can now benefit from a multiplier. This adjustment allows Storage Providers (SPs) to onboard more Raw Byte Power (RPB) at a potential profit, potentially leading to an increase in such sectors being onboarded.

Following this amendment, the primary impetus for SPs to onboard data will originate from outside the core protocol. This could include direct payments from real clients or new incentive models implemented in user-defined smart contracts.


## Product Considerations
Clients and Storage Providers will experience a streamlined interaction with the Filecoin network, which could lead to more user-friendly products and services built on top of Filecoin. 

Fil+ team and many more customized deal markets can be developed on L2 of Filecoin in either permissioned or permissionless manners in an open and fair market competition. 

The proposed changes present SPs with a more flexible environment, allowing them to select a pledge-to-hardware ratio best aligned with the specific costs and benefits they encounter. This enhanced flexibility means SPs can make more rational decisions based on their individual circumstances.

The choices would largely depend on each SP’s comparative cost of obtaining hardware and pledge tokens, combined with their revenue mix between block rewards and storage payments. SPs with clients offering better pay rates may consistently opt for the minimum pledge. This decision could improve their unit economics, particularly when other providers choose to pledge higher amounts to increase their per-TiB rewards. In this landscape, the higher pledge by some becomes an advantage for those opting for a lower pledge.



## Implementation
-Refer to the specific change [here](https://github.com/filecoin-project/builtin-actors/blob/485778aa23f742af1d1aa57a8f6608a0698d8ee7/actors/datacap/src/lib.rs#L161).


## TODO
- Discuss possible deprecation of the Verifreg Actor and Datacap in future updates.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
