---
fip: XXXX
title: NI-Porep
author: @lucaniz @Kubuxu @nicola @cryptonemo @vmx @irenegia
discussions-to: https://github.com/filecoin-project/FIPs/discussions/854 
status: Draft
type: Technical
category: Core
created: 2023-12-18
---
# NI-PoRep 

## Simple Summary

This proposal presents a new PoRep protocol (Non-Interactive PoRep) that removes `PreCommit`. As a result, we have

- Flexible onboarding pipeline, unblocking [SupraSeal](https://github.com/supranational/supra_seal)'s full potential
- Trustless separation between storage and computing: the proving tasks associated with sector onboarding can be outsourced.


## Abstract

Non-Interactive PoRep (NI-PoRep) allows to remove on-chain interaction when onboarding sectors by changing the way PoRep challenges are generated.

The protocol allows SP to locally generate PoRep challenges instead of using on-chain randomness.

On one hand, this feature of the protocol allows for drastically simpler onboarding pipeline. On the other hand, it requires an higher number of PoRep challenges (2268 per SDR layer instead of the current 180 per SDR layer) in order to preserve network security.

NI-PoRep is proposed as an *optional* feature, the previously available proofs types will be still supported. 



## Motivation

There are multiple venues where NI-PoRep would be beneficial for Filecoin. 

**Cost reduction thanks to a simplified onboarding pipeline**

PoRep is currently interactive in order to complete sealing an SP has to wait to receive a challenge seed from the chain) and requires an ad-hoc collateral. These feature represent a limitation when considering optimisation for the on-boarding pipeline, such as Sealing-as-a-Service and the new SupraSeal sealing code. With NI-PoRep we have no interaction is needed and this gives:

- [Gas cost reduction] Current PoRep iscomposed by two steps: PreCommit and ProveCommit. With NI-PoRep there is no more `PreCommit` method and message, only `ProveCommit` will stay (only one step with one chain message needed to onboard sectors to the network).  This translates in a possible gas cost reduction when considering  aggregated sectors (i.e., according to [our estimation](https://cryptonet.org/notebook/interactivenon-interactive-porep-gas-cost-comparison), when aggregating 6 sectors current PoRep is 2.1x more expensive than NI-PoRep per sector).
- [Lower HW requiremnts] With NI-PoRep there is no more waiting time between `PreCommit` and `ProveCommit`. This helps when using sealing software (like SupraSeal) that seals more sectors at the same time. Currently, the memory requirments are given by the fact that some data need to be stored during the waiting time. Having no waiting time implies lower memory requirments. 


**Trustless Sealing-as-a-Service (SaaS) Enabled**

NI-PoRep enables the full separation between computation and storage task (in particular, no `PCD` (PreCommit Deposit) is needed), which brings the following benefits:
- SaaS would be possible in a trustless manner (low risk-low trust: sealer does not need to put down collateral that will need to be re-paid by buyers or buyer does not need to pre-pay this amount)
- SaaS providers can delegate proving tasks. In particular, proving can be split into specialized subtasks which get outsourced to specialized entities (labeling the graph, Snarks, …)
- Enabling HDD wholesale: it would be possible to receive brand new drives with Sector-Keys pre-generated in your name

**PoRep Secured Cryptographically and not Rationally**

Chain cryptographic security gets increased: NI-PoRep would make misbehaving cryptographically infeasible rather than irrational.

**PoRep Security Now Independent from Consensus**

Current PoRep is interactive and needs to get randomness from the chain. Moreover, in order to be secure, 150 epochs are needed between `PreCommit` and `ProveCommit`. This is due to the fact that some Consensus attacks need to be infeasible (as putting those attacks in place would allow for faking storage).

In NI-PoRep, since randomness is derived locally, there is no link anymore between PoRep and consensus attacks. This means that

- Consensus attacks are not a concern anymore for PoRep security
- PoRep can now work “agnostically” with any consensus protocol

**Backward compatibility**

- NI-PoRep would be a separate proof type with a different on-chain flow as current PoRep. Anyone can decide whether use NI-PoRep or not.
- No need for a new trusted setup

## Specification

NI-PoRep protocol can be summarized as follows:

**Graph labelling and commitments** (similar to the current `PC1` and `PC2` computation)

1. Using `ReplicaID` (which contains `CommD`), SP computes the labels for all layers and the replica R;
2. SP computes the column commitments `CommC` , `CommRLast` and finally computes `CommR = Poseidon_2(CommC, CommRLast)`;

**Storage Provider locally generates `NI_ChallengesNumber` challenges and vanilla proofs;**

1. Each challenge is of the form `ch_i = H(tag, ReplicaID, commR, i)`;
2. SP computes responses for all the `NI_ChallengesNumber` challenges, which result in `NI_ChallengesNumber` vanilla proofs;

**Storage Provider publishes the new `NI_ProveCommitSector` proof**

1. SP takes the `NI_ChallengesNumber` vanilla proofs and computes the corresponding SNARK proofs for these challenges.
2. SP publishes the snark and commitment `CommR` (either in individual or aggregated form).
    1. Note in this step the SP will, by default, use the SnarkPack aggregation technique to prove even only one sector (see “product considerations” section for the motivation).

**Chain verifies proof**

1. Using `CommR` as a seed, the chain generates `NI_ChallengesNumber` challenges and these are fed into proof verification

### Actor changes

- Add two new proof types to the list of proof types that can be used when submitting a new sector
    - `RegisteredSealProof_NIStackedDrg32GiBV1`
    - `RegisteredSealProof_NIStackedDrg64GiBV1`
- Introduce a new method `ProveSector`, combining the functionalities of `PreCommitSector` and `ProveCommitSector` taking the following parameters (assuming the implementation of FIP-0076):
    
    ```go
    struct ProveSectorParams {
    		// carries information which previously was passed in PreCommit
    		sector_infos: []SectorPreCommitInfo
    		// Activation manifest for each sector being proven.
        SectorActivations: []SectorActivationManifest,
        // Proofs for each sector, parallel to activation manifests.
        // Exactly one of sector_proofs or aggregate_proof must be non-empty.
        SectorProofs: [][]byte,
        // Aggregate proof for all sectors.
        // Exactly one of sector_proofs or aggregate_proof must be non-empty.
        AggregateProof: []byte,
        // Whether to abort if any sector activation fails.
        RequireActivationSuccess: bool,
        // Whether to abort if any notification returns a non-zero exit code.
        RequireNotificationSuccess: bool,
    }
    ```
    
- The `ProveSector` performs all the checks of `PreCommitSector`, omitting PreCommitDeposit and then continues to perform `ProveCommitSector` checks and verifies the proof.

### Proof changes

- Add two new proof types to the list of proof types that can be used when pre-committing a new sector
    - `RegisteredSealProof::FeatureNIStackedDrgWindow32GiBV1_2`
    - `RegisteredSealProof::FeatureNIStackedDrgWindow64GiBV1_2`
- Related constants
    - `NI_porep_min_challenges` set to 2253; That’s the theoretical minimum number for 128 bits of security, for practical reasons the number of challenges will be 2268.
- New challenge generation function:
    
    ```rust
    // That's the sector size in bytes divided by the node size (32 bytes).
    const SECTOR_NODES: u32
    const NUM_CHALLENGES = 2268
    // The `tag` is a domain separation tag, which is just a list of bytes.
    fn gen_porep_challenges(tag: [u8], ReplicaID: [u8; 32], CommR: [u8; 32]):
    for i in 0..NUM_CHALLENGES {
        digest: [u8; 32] = sha256(tag || le_bytes(ReplicaID) || le_bytes(CommR) || le_bytes(i))
        bigint = u256::from_le_u32s(digest)
        challenge: u32 = (bigint % (SECTOR_NODES - 1)) + 1
    }
    ```
    

NI-PoRep is an *optional* feature that can be opt-in for those interested. The previously available proofs types can be used to continue the PoRep behavior.

## Rationale

Current PoRep is interactive and it is composed by two steps: PreCommit and ProveCommit. At PreCommit SP puts down a collateral (PCD) and wait 150 epochs in order to receive a challenge seed from the chain which enables the ProveCommit step. 

A first step to mitigate the waiting time downsides was the introduction of Synthetic PoRep (See [FIP-0059](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0059.md)), which that reduces the size of the temporary data stored between PreCommit and ProveCommit. 

NI-PoRep is the step forward, indeed it completely removes on-chain interaction (ie, the waiting time) and the need of PCD by allowing SP to locally generate challenges instead of using on-chain randomness. 
NI-PoRep has little downside with respect to the status quo: it removes PreCommit at the cost of augmenting C2 (ie SNARK generation) costs (which would result in a limited cost increase looking at onboarding costs as a whole). Indeed, NI-PoRep requires 12.8x more PoRep Challenges, this translates into an 12,8x Snark proving overhead. We analyzed how this snark computation overhead affects overall costs. The conclusion is that considering PC1+PC2+C1+C2 and storage costs (i.e. not considering maintenance costs), a 128 bits of security NI-PoRep sector is 5% more expensive overall than a Interactive PoRep sector when sector duration is 3y. See full analysis [here](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0059.md).

## Backwards Compatibility

NI-PoRep would become a new proof type with a different on-chain flow as current PoRep (due to the removal of the `PreCommit` step).

## Test Cases

Will be included with implementation to be presented.

## Security Considerations

**Fiat-Shamir Heuristic and its effects**

NI-PoRep is based on the well-known Fiat-Shamir Heuristic, which allows for having a non interactive protocol starting from any 3-message interactive protocol. However, the heuristic requires the interactive protocol to have at least 80 [bits of security](https://en.wikipedia.org/wiki/Security_level) (instead of the current 10), and preferably 128. In order to have long term security we propose to opt for 128 bits: this means that for NI-PoRep we need  `NI_ChallengesNumber128bit` = 2268.

**How to take `SealRandomness` for ensuring sectors are anchored to the chain**

The epoch in which sealing took place is identified by the corresponding chain reference, called `SealRandomness` which is the anchor of the sector to the chain. `SealRandomness` must be taken from the VRF chain, in order to ensure that no other fork can replay the Seal.

On one hand, `SealRandomness` needs to be taken from finalized blocks, but on the other hand it can not be taken farther back than necessary (in order to protect against long-range attacks). This means that `SealRandomness` needs to be verified.

Given NI-PoRep removes onchain interaction, `SealRandomness` verification becomes more difficult, but still necessary to protect the chain against the same class of attacks mentioned above.

We set up a validity time window which holds for all the sectors committed onchain together. We set this time window to be  `sealChallengeEarliest` = 30 days, which is coherent with the current `MaxProveCommitDuration` as per FIP-0013.

This means that, if PC1, PC2, C1, C2 happen locally over time resulting into different sectors sealed in different moments in time and committed on-chain at the end of the process, all sectors committed together should have a randomness which is not older than  `sealChallengeEarliest` epochs in the past. As a result, a NI-PoRep step needs to be completed within `sealChallengeEarliest` epochs overall to be valid.

## Addressing concerns **due to interaction removal**

One point to take into account when dealing with NI-PoRep, compared with the status quo, is that a malicious party willing to take over the network could potentially keep accumulating sectors locally onboarding them to the network all in a sudden.

Our analysis shows that in terms of security there is no substantial difference with the case of Interactive PoRep and no additional security risks are introduced.

As a result of our analysis we propose to decouple power table lookback from consensus and set it to 7 days.
See discussion [#854](https://github.com/filecoin-project/FIPs/discussions/854) for full details.

## Incentive Considerations

NI-PoRep will implement the batch balancer currently in place. See [FIP-0013](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0013.md) for details.

## Product Considerations

NI-PoRep represent the ultimate step forward after the introduction of Synthetic PoRep (see [FIP-0059](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0059.md)). 

As already mentioned above, NI-PoRep is a prerequisite to unblock new use cases like trustless SaaS and HDD wholesale as well as allowing for SupraSeal software employment at full potential. 

## Benchmarks

In order to have a good cost estimation benchmarks on different systems were run. It’s consistent that the difference in the total runtime of the SNARK phase between interactive PoRep and non-interactive PoRep is the expected 12.5-13x.

This phase consists of two distinct steps. The synthesis, which is a memory and CPU heavy operation and the proving, which is GPU heavy. The SupraSeal implementation only target the proving. There we see speedups between 6-10x. It depends on the GPU, while newer generations see higher speedups.

When the synthesis is also taken into account, then the overall improvements are 3-5x. There older GPU generations see higher speeds as the proving time dominates over the synthesis time.

For exemplary results of the benchmarks see: [SupraSeal C2 benchmarks](https://www.notion.so/SupraSeal-C2-benchmarks-9739face18a9448e8b6de1a1fcc9c0e3?pvs=21).

## Implementations

Implementation in progress (TODO).

## Copyright Waiver

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
