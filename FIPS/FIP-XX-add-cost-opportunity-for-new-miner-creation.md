---
fip: "xxxx"
title: Add Cost Opportunity For New Miner Creation
discussions-to: https://github.com/filecoin-project/FIPs/discussions/780
author: "Zac <@remakeZK>"
status: Draft
type: Technical
category: Core
created: 2023-08-21
---

## Simple Summary

- Add opportunity cost (in FIL) to each node creation to prevent the miner ID creation spam.

## Abstract

By imposing a cost, this proposal helps prevent the spamming of creating miner IDs in order to:

1) lighten the network chain storage burden

2) save wasted resources and future increment of gas that caused by wasted storage

3) avoid the malicious attacks achieved by creating a large number of accounts to cause network congestion and unstable gas fees

## Problem Motivation

By August 2023, according to the statistics of Filscan, there are 601,131 Miner IDs have been built with only 4,862 actives. The actual ID usage counts for merely 0.8% and the abuse of ID creation trend continues. The actual ID usage only counts 3.7% for the recent two months (125 Miner IDs are active out of 3,254 newly created). 

<img width="865" alt="total_in_use" src="https://github.com/remakeZK/FIPs/assets/92775781/fc8266ab-4224-49ab-a4a7-6450377d4638">
<img width="913" alt="recent_two_months" src="https://github.com/remakeZK/FIPs/assets/92775781/2b41e3a8-ad5f-481a-bbbb-569fc4533e0b">

  
Many users randomly create numerous nodes just to get preferred IDs, wasting resources and burdening the network for no purpose. Moreover, those wasted nodes occupy the storage of the network; with time elapsed, the waste resource rate will increase, along with increasing the future gas price because of those unnecessary storages of the network. Furthermore, there is a risk of exposure to potential attacks by creating numerous accounts, causing network congestion.  


## Specification

In creating a new node,

- Currently: there is no cost associated with creating new miners, so users spams many new nodes without limit
- Proposed:   
Require spending of a one-time 500FIL to create a new miner ID and deposit the 500FIL into miner account as locked rewards.

## Design Rationale

Adding an opportunity cost will prevent such spammy behavior; moreover, depositing fees as locked rewards does not incur actual costs but will occupy funds and bring opportunity costs. Users need to weigh the opportunity cost of locking funds for 180 days per new node. Also, the more nodes created, the more funds need to be locked. This can prevent users from abusing node creation. Additionally, this mechanism helps determine whether each new node will be fully utilized since idle miners will waste locked funds in vain. 

## Backward Compatibility

The charging fee of node creation might increase the entry barrier of new SPs, but 500FIL is a small amount in terms of initiating. Moreover, the proposed first solution of converting fees to 180-day locked rewards adds no real capital cost, only opportunity cost. This encourages on-demand account creation, as users will create accounts based on actual needs, ensuring practical use of each new account.

## Test Cases

N/A

## Implementation

The change of implementing this proposal is minor and easy to conduct. No impact to any other miner related activities. 

## Security Considerations

There is no security consideration for this proposal; instead, it helps to prevent potential attacks by using a large number of newly created IDs, and the scenarios of network congestion and instability of gas fees that are caused by unnecessary numerous ID creations. 

## Incentive Considerations

Charging for creating new accounts can help prevent abuse, reduce unnecessary storage, and avoid increased gas fees over time caused by such wasteful activities that burden the network with unnecessary storage. 

## Product Considerations

Currently, setting no cost for node creation has no benefits but potential risks and drawbacks to the network, occupying the unnecessary storage will increase the network burden and future gas fees, also expanding the potential attack exposure. Therefore, By charging the creation node fees and later either burning the creation fee or converting the fees to lock rewards will stop the abuse of ID creation since they would consider the worthiness of the opportunity cost if they do so. Moreover, this proposal guides or returns to the normal phenomenon that should supposed to exist - truly implement on-demand account creation, where new accounts are only created when they are actually needed for use, or newly created accounts are put into practical use.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
