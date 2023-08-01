---
fip: "<to be assigned>" 
title: Allow SPs to move partitions between deadlines 
author: Steven Li (@steven004), Alan Xu (@zhiqiangxu), Mike Li (@hunjixin), Alex North (@anorth), Nicola (@nicola)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/735
status: Draft
type: Technical (Core)
category: Core
created: 2023-06-25
---

## Summary
Add a new method for Miner actor to allow SPs to move a partition of sectors from one deadline to another, so that an SP could have control over their WindowedPoSt schedule. 

## Abstract 
In _WindowPoSt_ every 24-hour period is called a _“proving period”_ and is broken down into a series of 30min, non-overlapping _deadlines_, making a total of 48 deadlines within any given 24-hour proving period. Each sector is assigned to one of these deadlines when proven to the chain by the network, grouped in partitions. The WindowPoSt of a particular partitions in a deadline has to be done in that particular 30min period every 24 hours. 

This proposal is to add a method  `MovePartitions` to move all sectors in one or more partitions from one deadline to another to allow SPs control the WindowPoSt time slot for sectors.

## Change Motivation
When a Storage Provider (SP) maintains storage for Filecoin network, they often encounter various challenges such as system performance degradation, network issues, facility maintenance, and even changes in data center location. While dealing with these challenges, SPs require greater flexibility in controlling the period to prove the data integrity to the chain, while still adhering to the rule of proving once every 24 hours. 

By implementing this proposal, several advantages can be realized: 

- Creation of user-defined maintenance windows: SPs can create designated periods for maintenance activities without the risk of losing power. 
- Set hours of operation for SP infrastructure maintainers: SPs can schedule all WindowPoSts during hours of operation to optimize the maintenance operation resources/on-call schedules. 
- Cost savings for large SPs on WindowPoSt hardware: Balancing the number of partitions across all the deadlines allows large SPs to optimize their hardware usage and reduce WindowPoSt hardware costs.
- Relieving access stress on storage nodes: In scenarios where an excessive number of partitions are concentrated within a single deadline on specific storage nodes, redistributing some partitions to other deadlines can help alleviate access stress and improve overall performance.
- Possibility of partition compaction: By moving partitions from different deadlines into a single deadline, it becomes possible to compact partitions that were originally distributed across multiple deadlines. 

## Specification
We propose adding the following method to the built-in `Miner` Actor. 

``` golang
// Moves sectors in partitions in one deadline to another
// Returns false if failed
// Any non-zero exit code must also be interpreted as a failure of moving
func (a Actor) MovePartitions(rt Runtime, params *MovePartitionsParams) *abi.EmptyValue
```

The params to this method indicate the partitions, their original deadline and destination deadline.
``` rust
type MovePartitionsParams struct {
  OrigDeadline    uint64
  DestDeadline    uint64
  Partitions      bitfield.BitField
} 
```

To adhere to the requirement of conducting a _WindowPoSt_ every 24 hours, the `MovePartitions` function only permits the movement of partitions to a `DestDeadline` whose next proving period is scheduled to occur within 24 hours after the `OrigDeadline`'s last proving period. If the `DestDeadline` falls outside of this time frame, it will fail. This restriction ensures that the sector's period aligns with the required _WindowPoSt_ interval. 

## Design Rationale
The primary objective is to introduce a straightforward mechanism for implementing flexible proving period settings for Storage Providers (SPs). Additionally, there is a consideration to offer greater flexibility by allowing the movement of any selected sectors from one deadline to another. This would enable an SP to align the expiration of sectors within a single partition. However, this approach poses certain risks, such as the potential increase in the cost of managing the bitfield due to non-sequential sector IDs. Moreover, the technical complexity involved in understanding the cost calculation may lead to unnecessary difficulties for SP operators.

## Backwards Compatibility
This proposal introduced a new method to the built-in actors, which needs a network upgrade, but otherwise breaks no backwards compatibility

## Test Cases
Proposed test cases include: 
‒ that the `MovePartitions` can be successful when moving one partition from a deadline to another which proving period is in 24 hours after the partition's last proving period;
‒ that the `MovePartitions` would fail when moving one partition from a deadline to another which proving period is beyond 24 hours after the partition's last proving period;
‒ that the `MovePartitions` can be successful when moving multiple partitions from a deadline to another which proving period is in 24 hours after partitions' last proving period;
‒ that the `MovePartitions` would fail when moving multiple partitions from a deadline to another which proving period is beyond 24 hours after partitions' last proving period;
‒ that the _WindowedPoSt_ works as normal in the `DestDeadline` for partitions moved from its `OrigDeadline`;
‒ that the `CompactPartitions` works as normal for the new moved-in partitions and existing partitions in the `DestDeadline`

## Security Considerations
This proposal is to provide more flexibility for SPs to have full control of proving period of _WindowPoSt_ for partitions. In the design, we still ask the SPs to follow the basic rule that one partition should have one proof every 24 hours, so there is no compromise in this regard. 

There might be a concern that overall _WindowPoSt_ messages in the network might imbalance over the 48 proving periods due to adjustments by SPs. Considering _WindowPoSt_ only takes about 10% of the whole network bandwidth, and the network is decentralized, it should not be a problem, in addition, this mechanism actually provide a way for SPs to move proving period to avoid a expected congestion period. 

## Incentive Considerations
This FIP does not effect incentives in itself and is of only flexibility providing without any impact on economic factors. 

## Product Considerations
There is no any impact on Filecoin ecosystem application or platforms. 

## Implementation
These changes have been implemented in [this PR](https://github.com/filecoin-project/builtin-actors/pull/1326). 

## Copyright
Copyright and related rights waived vis [CC0](https://creativecommons.org/publicdomain/zero/1.0/). 
