---
fip: "<to be assigned>" <!--keep the qoutes around the fip number, i.e: `fip: "0001"`-->
title: Caller-specified proving deadline for NI-PoRep
author: "Alex North (@anorth)"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1007
status: Draft
type: Technical (Core)
created: 2024-05-14
requires (*optional): FIP-0090
---

# FIP-XXXX: Caller-specified proving deadline for NI-PoRep

## Simple Summary
Allows storage providers to specify the Window PoST proving deadline for sectors onboarded with NI-PoRep.

## Abstract
Storage providers (SPs) cannot currently control the allocation of sectors to Window PoST deadlines.
Sectors are automatically spread out over the full 24-hour proving period.

This proposal allows SPs to select a deadline when onboarding sectors with the new NI-PoRep method.

## Change Motivation
SPs would benefit from greater operational flexibility than being required to spread Window PoST workload over 24 hours.
[FIP-0070](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0070.md)
attempted to allow moving of sectors between deadlines after onboarding, 
but the scheduling system has proven too complex to easily accommodate the change.

Allowing SPs to specify the proving deadline when onboarding is not quite as powerful, but much simpler.
Such a change is most easily made by introducing a new onboarding method.
Attaching it to the new method introduced by FIP-0090 is an expedient way to get this functionality.

## Specification
The parameters for the miner actor method `ProveCommitSectorsNI` (number 36) are changed:

```go
  struct ProveCommitSectorsNIParams {
     // Information about sealing of each sector.
     Sectors: []SectorNIActivationInfo
     // Proof type for each seal (must be an NI-PoRep variant)
     SealProofType: RegisteredSealProof,
     // Proofs for each sector, parallel to activation manifests.
     // Exactly one of sector_proofs or aggregate_proof must be non-empty.
     SectorProofs: [][]byte,
     // Aggregate proof for all sectors.
     // Exactly one of sector_proofs or aggregate_proof must be non-empty.
     AggregateProof: []byte,
     // Proof type for aggregation, if aggregated
     AggregateProofType: Option<RegisteredAggregateProof>
     // Whether to abort if any sector activation fails.
     RequireActivationSuccess: bool,
     
     // NEW! The Window PoST deadline index at which to schedule the new sectors.
     ProvingDeadline uint64 
   }
```

The proving deadline must be between 0 and 47, inclusive.
It corresponds to the Window PoST deadline index at which all the new sectors must be regularly proven.
The proving deadline must not be the current or next deadline to be proven by the receiving actor.

## Design Rationale
Specifying a proving deadline when onboarding is simple, though less powerful than supporting rescheduling afterwards.
The implementation may simply skip the existing calculation of the target deadline, 
but then make use of existing code to assign the new sectors to that deadline.

This change does not exclude the potential to support re-scheduling existing sectors in the future.

## Backwards Compatibility
This proposal must be implemented at the same time as FIP-0090.
It includes a backwards-incompatible change to `ProveCommitSectorsNI`.
Since FIP-0090 is not yet final, these two can be implemented concurrently without introducing any further compatibility issues.

## Test Cases
To be implemented:
- All sectors are scheduled in the requested deadline
  - with 1 sector
  - with > 1 partition of sectors
- Invalid proving deadline is rejected
- Current/next proving deadline is rejected

## Security Considerations
The existing automatic scheduling was motivated by a caution about overloading the network at particular times of day 
with too many Window PoSTs due at the same time.
However, since the introduction of the FVM and a robust gas model,
the network itself is not at much risk from this anymore.
We might reasonably expect SPs to make reasonable scheduling decisions to optimize their own cost and risk profile,
given knowledge and expectations about the scheduling of other SPs.

A Window PoST for every sector must still be submitted every 24 hours.

The Window PoST dispute window is 1800 epochs (15 hours).
The worst case impact on the minimum cost to dispute a Window PoST is thus when
all partitions are scheduled uniformly across a 15-hour period: then a dispute for the first deadline 
must compete with PoST submissions in the last (or some prior deadline).
This would affect gas availability only if the network were above 67% of capacity for Window PoST throughput.
Window PoST today is <10% of gas utilisation.

## Incentive Considerations
This proposal provides flexibility to SPs without any significant changes to incentives.

## Product Considerations
Granting SPs flexibility in their WindowedPost Schedule allows them to establish maintenance windows etc.
While this might appear to degrade service availability slightly, this impact is limited:
- Any individual sector is only required for WindowPoST at one moment per day in either case.
- All sectors must be continually available for Winning PoST in order to earn block rewards.
- Services such as retrieval are usually served from data that is separate from the sealed sectors.
- Clients typically store multiple copies with different SPs, ensuring data availability even if one SP is temporarily unavailable.

## Implementation
TBC

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
