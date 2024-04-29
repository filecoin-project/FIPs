---
fip: "xxx"
title: Introducing sealerID
author: nicola (@nicola), irene (@irenegia), luca (@lucaniz), kuba (@Kubuxu)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/890 
status: Draft
type: Technical
category: Core
dependency: FIP0090
created: 2023-04-18
---



# FIPXXXX: Introducing sealerID


## Simple Summary

This adds the notion of `sealerID`, which is used in the sealing process of NI-PoRep. In particular:
* We add a new actor, the Sealer Actor so that SealerIDs can be registered;
* `sealerID` can be used to create `ReplicaID` by parting running the SDR labeling algorithm;
* `sealerID` is added to the parameters of the method `ProveCommitSectorsNI`.



## Abstract 

With the current protocol, the party creates the `ReplicaID` needs to use the same `minerID` that will be used for PoRep verifications. This implies that “pre-sealing” sectors is not a viable option: no sector can be sealed (ie, replica created) ahead of time, before knowing the identity of the miner actor who will own it. To enable this scenario, we introduce the concept of `sealerID` to be used in place of the `minerID` only during sealing.


## Motivation

We consider the scenario where Storage Providers want to delegate some of their activities to external parties that offer competitive services at lower costs.

In particular, we call **Sealing-as-a-Service (SaaS) Provider** an entity that runs all PoRep operations (labeling the graph, column commitments, MT generation, vanilla proofs and SNARKs generation) needed to get a replica and onboard the sector that contains it.

The SaaS then transfers the replica and the proofs to a **SaaS Client.** This is an SP that will onboard the sector with the replica R (ie, call a ProveCommit method) and will be responsible for storing R and proving validity of the corresponding sector (ie, running window- and winning-PoSt), and/or adding data to the committed capacity sector via SnapDeals.

### Addressed issues:

1. [solved already] With interactive PoRep the SaaS Provider and Client needs coordination and agreement (therefore trust) about the intermediate interaction with the chain (ie, sending commR on chain) and locking down PCD (PreCommitDeposit). This is resolved by using NI-PoRep [FIP0090](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0090.md) that requires no chain interaction and no deposit.
2. [solved by this FIP] Even with NI-PoRep, some coordination between the SaaS Provider and their client (SP) remains. Indeed during the labeling phase the SaaS Provider creates `ReplicaID` and for this needs to use the `minerID` and `sectorNumber`from the SaaS Client who will receive the replica to be stored. If these values are not correctly used then the SNARK proof will not be valid. This means that a SaaS Provider needs to “wait” for the request (and info) from a SaaS client to seal sectors. In other words, this prevents a SaaS Provider from sealing sectors in advance using its HW at max capacity (and therefore reducing sealing cost for everyone).


## Specification

1. We add a new type of actor: the Sealer Actor (to be used for SaaS Providers);
   - This can be a “disposable” actor, no need for an owner key. If something bad happens, create a new id. This is okay because no tokens are locked for this actor;
2. Add the method to create and register `SealerID`
   - The list of SealerIDs is disjoint from the MinerID list
   - Add a new map `SealerID -> [SectorNumber]` to the chain state (that is, we have a list of used sector numbers for each sealer);
     - ie, the actor needs `SectorNumber` facilities.
3. Modify the method `ProveCommitSectorsNI` to accept the sealerID to create `ReplicaID` .
    - Add the `SealerID` field to `SectorNIActivactionInfo`
     - if empty, use the the minerID
     - if the sealer id is passed, use it for `ReplicaID` (in the place of miner id)
       - the method updates the right map of used sector numbers (note that this is needed only if we want to have onchain info about sectors grouped by miner;
4. [Access control, needed to avoid front-run attacks]
    - Store in the Sealer Actor another address: this is an address to a proxy contract that can be used to implement ACL

When an SP onboards a sector (ie, call to method `ProveCommitSectorsNIParams` in the Miner Actor), then call to the Sealer Actor. If the ACL is enabled, then call the ACL contract.

![Sealer ID](https://github.com/filecoin-project/FIPs/assets/23217773/4852d5eb-6c81-4fc7-9f7e-dd7a351ed943)

## Rationale 

The design aims to 
* Minimize changes with respect to the status quo, particularly maintaining 'ReplicaID' as a unique identifier within the entire Filecoin ecosystem;
* Provide future programmability. In particular, as regards the access control feature we decide to implement it using a proxy contract (instead of implementing it directly in the actor) in order to have the possibility of the final users (ie, SaaS providers) to personalize it. 


## Backwards Compatibility

TODO


## Test Cases

TODO


## Security Considerations

* For Storage Providers, this FIP does not introduce additional security risks compared to the status quo;
* For the SaaS provider: in order to have control on who can “activate” (ie, prove commit) their sealed sectors, SaaS providers use the ACL proxy contract.

## Incentive Considerations

The proposed change (ie, introducing the sealer id to completely decouple computation-heavy tasks for onboarding sector from the sector ownership) allows SaaS providers to seal sectors independently from the current demand and therefore to use their hardware at full capacity. This incentivises the creation of a market for CC sectors and lower the SP cost for onboarding CC sectors, which can later on be upgraded to useful storage via the SnapDeal protocol (`ReplicasUpdate3 `method).


## Product Considerations

Having SaaS providers and CC-sector markets lower the entry barrier for SPs to join the Filecoin network. Indeed, with this service in place SPs do not need to have the HW to run the PoRep step in house. Note that the HW for running winning- and window-PoSt is still needed.


## Implementations

TODO


## Copyright Waiver

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
