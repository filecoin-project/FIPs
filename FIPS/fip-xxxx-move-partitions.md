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
- Relieving access stress on storage nodes: In scenarios where numerous partitions need complete WindowedPoSt within a short period and their sectors located in a specific storage node in a distributed storage system, the excessive read requests in that period can overload the node and degrade its performance. Moving some partitions to other deadlines helps achieve a more balanced workload.
- Increasing possibility of compacting partition: By moving partitions from different deadlines into a single deadline, it becomes possible to compact partitions that were originally distributed across multiple deadlines. 

## Specification
We propose the addition of a new method to the built-in `Miner` Actor, called `MovePartitions`, which allows Storage Providers (Miners) to move sectors within partitions from one deadline to another. 

### Method Signature and Parameters

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

### Constraits and Rules

1. To adhere to the requirement of conducting a _WindowPoSt_ every 24 hours, the `MovePartitions` function only permits the movement of partitions to a `DestDeadline` whose next proving period is scheduled to occur within 24 hours after the `OrigDeadline`'s last proving period. If the `DestDeadline` falls outside of this time frame, it will fail. This restriction ensures that the sector's period aligns with the required _WindowPoSt_ interval.
2. Partitions cannot be moved to or from a deadline during its challenge window or immediately before it, matching existing mutability constraints.
3. A partition containing faulty or unproven sectors cannot be moved. 
4. The partitions are moved as a whole, without any compaction.
5. An empty partition is left behind in the source deadline after the move. This ensures that partition indices do not change.
6. If the original deadline falls within its optimistic WindowPoSt challenge window, the previously submitted WindowPoSt is validated during the MovePartitions method's execution. This validation helps to demonstrate the correctness of the previously submitted WindowPoSt data.

## Design Rationale
The main goal of this proposal is to introduce a straightforward mechanism for enabling flexible proving period scheduling for Storage Providers (SPs). `MovePartitions` means all sectors in the particular partitions are all together moved from the original deadline to the destination deadline if it executed successfully. 

Another aspect to consider is the possibility of allowing the movement of selected sectors from one deadline to another, which would enable Storage Providers (SPs) to align the expiration of sectors within a single partition. However, this approach comes with certain risks, such as potential cost increases in managing the bitfield due to non-sequential sector IDs, leading to unexpected gas usage. Moreover, the technical complexity involved in understanding the gas calculation could create unnecessary difficulties for SP operators. Additionally, implementing this feature introduces a significant level of complexity to the system.

This proposal does not currently adopt the second aspect to ennsure a more straightforward and manageable implementation, leaving the movement of selected sectors for future study. 



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
