```---
fip: "FIP-XXXX"
title: "Removing Restriction to Access to Multiplier and Allowing Unrestricted Minting of Datacap"
author: Fatman13 (@Fatman13), ArthurWang1255 (@ArthurWang1255), flyworker (@flyworker), stuberman (@stuberman), Eliovp (@Eliovp), dcasem (@dcasem), and The-Wayvy (@The-Wayvy)
Discussions-to: https://github.com/filecoin-project/FIPs/discussions/774
status: Draft
type: Technical
category: Core
created: 2023-08-22
requires: 
replaces:
```

## Simple Summary
This proposal aims to remove restrictions associated with the 10X multiplier in Fil+ deals and allow any actor to mint Datacap, promoting decentralization and simplifying the Filecoin ecosystem.

## Abstract
The Fil+ program was designed to encourage high-quality storage on the Filecoin network. The current proposal intends to remove complexities that have arisen from its initial conception, thereby ensuring the Filecoin mission is better represented and uncomplicated.

## Change Motivation≠
The current Fil+ implementation, though well-intentioned, has added complexities that deviate from Filecoin's core mission. Simplifying this system will encourage the onboarding of genuine data and uphold the integrity of the Filecoin blockchain.

## Specification
 **Change in the Datacap Actor's Mint Function**: Alter the DataCap actor's mint() function to remove the restriction that the caller must be the "governor" (the verified registry actor). Allow any actor to mint datacap.

## Design Rationale
While more comprehensive solutions might be considered in the future, this FIP offers an immediate, simpler approach. 

Allowing any actor to mint datacap is the simplest change to the current protocol that removes the Fil+ process restrictions on datacap issuance. This datacap can then be transferred to the verified registry to create a verified allocation and claim the associated multiplier when onboarding data.
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
The proposed change effectively removes a significant incentive for the onboarding of data that was previously determined as valuable by the off-chain notaries under the Fil+ mechanism. As a result, it's anticipated that the overall rate of data onboarding may decrease. The extent to which the currently incentivized data under this mechanism is fraudulent remains uncertain.

With the removal of the restriction, effectively-empty sectors can now benefit from a multiplier. This adjustment allows Storage Providers (SPs) to onboard more Raw Byte Power (RPB) at a potential profit, potentially leading to an increase in such sectors being onboarded.

Following this amendment, primary motivations for SPs to onboard data will still need to originate from outside the core protocol. This could encompass direct client payments or potential incentive models established within upcoming user-defined smart contracts.


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
