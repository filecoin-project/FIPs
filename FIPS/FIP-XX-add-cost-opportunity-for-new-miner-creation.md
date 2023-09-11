---
fip: "0077"
title: Add Cost Opportunity For New Miner Creation
discussions-to: https://github.com/filecoin-project/FIPs/discussions/780
author: "Zac <@remakeZK>"
status: Draft
type: Technical
category: Core
created: 2023-08-21
---

## Simple Summary

- Add opportunity cost (in FIL) to each miner actor creation to prevent the miner ID creation spam.

## Abstract

By imposing a cost, this proposal helps prevent the spamming of creating miner IDs in order to:

1) lighten the network chain storage burden

2) Prevent wasted resources and incremental increases in gas cost caused by wasted storage, and;

3) Avoid an attack vector whereby an attacker sends a large amount of low cost `CreateMiner` messages, thus causing network congestion and destabilizing gas fees. 

## Problem Motivation

It [was documented](https://github.com/filecoin-project/FIPs/discussions/780#discussioncomment-6787043) that in March 2021, someone had spammed the network by sending thousands of CreateMiner messages.  This caused several issues: 
1) Base fee increases associated with mpool congestion
2) Redirect nodes away from producing blocks
3) Lower overall chain performance, specifically related to cron jobs overload

As of August 2023, according to FilScan statistics, there were 601,131 Miner IDs and only 4,862 actively in use. The actual ID usage counts for merely 0.8% of all existing Miner IDs, and the abuse of ID creation trend continues. In the previous two months, only 3.7% of all newly created Miner IDs (125 Miner IDs are active out of 3,254 newly created) were active. 

<img width="865" alt="total_in_use" src="https://github.com/remakeZK/FIPs/assets/92775781/fc8266ab-4224-49ab-a4a7-6450377d4638">
<img width="913" alt="recent_two_months" src="https://github.com/remakeZK/FIPs/assets/92775781/2b41e3a8-ad5f-481a-bbbb-569fc4533e0b">

  
Users create multiple Minder IDs in order to get preferred IDs, wasting resources and unnecessarily burdening the network. Unused Miner IDs continue to occupy storage on the network.  As time goes on, it is expected that the rate of wasted resources will increase, as will future gas prices.  

Furthermore, allowing network participants to cheaply and easily create numerous accounts introduces a potential attack vector.  Were participants to spam the network with CreateMiner messages, mpool congestion and unstable network fees could potentially affect more useful, critical, and/or time sensitive messages (i.e: SubmitWindowedPoSt, ReportConsensusFault, sector/data onboarding messages) from landing on chain.


## Specification

In creating a new Miner actor,

- Currently: there is no cost associated with creating new miner actors other than the gas cost for the CreateMiner message, so users spam many new miner actors without limit
- Proposed:   
Require spending of a one-time 500FIL to create a new miner ID and deposit the 500FIL into miner account as locked rewards.

## Design Rationale

Adding an opportunity cost will prevent such spammy behavior; moreover, depositing fees as locked rewards does not incur actual costs but will occupy funds and bring opportunity costs. Users need to weigh the opportunity cost of locking funds for 180 days per new miner actor. Also, the more miner actors created, the more funds need to be locked. This can prevent users from abusing miner actor creation. Additionally, this mechanism helps determine whether each new miner actor will be fully utilized since idle miners will waste locked funds in vain. 

## Backward Compatibility

N/A

## Test Cases

N/A

## Implementation

These changes have been implemented in this PR.

https://github.com/filecoin-project/builtin-actors/pull/1398

## Security Considerations

There is no security consideration for this proposal; instead, it helps to prevent potential attacks by using a large number of newly created IDs, and the scenarios of network congestion and instability of gas fees that are caused by unnecessary numerous ID creations. 

## Incentive Considerations

Charging for creating new accounts can help prevent abuse, reduce unnecessary storage, and avoid increased gas fees over time caused by such wasteful activities that burden the network with unnecessary storage. 

## Product Considerations

Currently, setting no cost for miner actor creation has no benefits but potential risks and drawbacks to the network, occupying the unnecessary storage will increase the network burden and future gas fees, also expanding the potential attack exposure. Therefore, By charging the creation miner actor fees and later either burning the creation fee or converting the fees to lock rewards will stop the abuse of ID creation since they would consider the worthiness of the opportunity cost if they do so. Moreover, this proposal guides or returns to the normal phenomenon that should supposed to exist - truly implement on-demand account creation, where new accounts are only created when they are actually needed for use, or newly created accounts are put into practical use.

The charging fee of miner actor creation might increase the entry barrier of new SPs, but 500FIL is a small amount in terms of initiating. Moreover, the proposed first solution of converting fees to 180-day locked rewards adds no real capital cost, only opportunity cost. This encourages on-demand account creation, as users will create accounts based on actual needs, ensuring practical use of each new account.
## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
