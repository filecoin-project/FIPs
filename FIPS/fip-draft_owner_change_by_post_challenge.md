---
fip: "0027"
title: Owner key change by random PoSt challenge
author: Lion (@lionsoul2014), Rock (@yangjian102621)
discussions-to: <URL>
status: Draft
type: Technical
category Networking
created: 2022-01-13
spec-sections: 
  - miner actors
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->
Data service first - The real owner of a miner should be the one providing the sector data service not the one just own the owner key.

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->
For the current FIL network, miners lose their owner key and they lost everything and they have to keep providing service for the data access but without rewards even thought it keeps winning(This is really a terrible story). The FIL network will be more secure and consistent with the original intention of data storage if we provide a mechanism that the owner key could be changed by random PoSt challenge.

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->
There are some unavoidable situations where we may lose the owner key (and what actually happened):
1. Hacker attach: the lotus server may be hacked cuz of weak network protection (or operation without security awareness) and the owner key was stolen.
2. Hardware errors: Hardware errors like disk corruption before operator backup the owner key or the keystore files.
3. Operating errors: the operator may delete the owner key or the keystore files by mistake without backup.
4. Stolen by operators: we need professional technicians to manage a miner and they may stolen it and control everything by changing the owner key after they quit.

Miners simple can't do anything when they lost their owner key they lost their collateral and all the future rewards. This is a bad investment experience and many participants really care about this "owner key stolen" issue.
Stressing the importance of owner key and admonishing miners to backup their keys is a recurring thing. Miners realizes the importance of the owner key and form a security awareness requires a process and a certain amount of time. 

Filecoin is a decentralized storage network and key is to provide data storage and access serivce so the real miner should be the one keep providing data storage service not the one just own the owner key. What if the network provide a mechanism that allow miners to change their owner key even though they lost it as long as they could provide valid proof for random deadlines or partitions challenge.

That is to say the most important thing to do for a miner is to protect its data and make sure all the data it stored could provide stable service. Miner staking pledged storage space to get rewards and the key is still the storage and storage is a kind of service not a kind of control. So, Will the FIL network be better to make the stable data service as the first thing which means the give the rewards and collateral to the person who provides the data service instead of the person who ONLY owns the owner key ?

Protecting the data is already a hard work, but also we need pay more attension to protect "the most important owner key" that shouldn't be that important. That's really what happened now every day for all the miners. With this implementation the network can give those miners who made this mistake chances to make up for it WITHOUT affecting the reliability of the whole Filecoin network.


## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->
The implementation steps/pseudo is as follows:
1. Register a new bls wallet and active it (named A).
    ```
    var nWallet    // a new actived bls wallet generate by cmd 'lotus wallet new bls'
    ```
2. Submit a owner key change proposal signed by the new wallet A with random partitions PoSt challenge.
    ```golang
    type RandomPoStChallenge struct {
        // Challenge deadline
        Deadline *dline.Info

        // partitions to challenge
        Partitions []int
    }

    type OwnerChangePoStChallenge struct {
        // random from network
        Random abi.Randomness

        // challenges produce according to the random
        Challenge []RandomPoStChallenge

        // PoSt submit deadline epoch
        CloseEpoch abi.ChainEpoch
    }

    // challenge window post result
	type SubmitOwnerChangePoStParams{
		Deadline    *dline.Info
		Partitions: []miner.PostPartition
		Proofs:     nil,
	}
    ```
3. Generate window post for the challenged partitions (ONLY the data owner could do this).
    ```golang
    // extend the api to generate self-define window PoSt
    // Merge to Get Partitions
    challenge := OwnerChangePoStChallenge{}  // from challenge message
    var paritions []api.Partition = MergeAndGetParitions(&challenge) 

    partitionBatches := s.batchPartitions(partitions, NetworkVersion)
    posts := make([]SubmitOwnerChangePoStParams, len(partitionBatches))
    for batchIdx, batch := range partitionBatches {
        sInfos := getSectorInfo(batch)
        proof, ps, err := prover.GenerateWindowPoSt(ctx, actorId, sinfos, append(abi.PoStRandomness{}, challenge.Random...))
        posts = append(posts, SubmitOwnerChangePoStParams{
            Deadline:   di,
            Partitions: getPartitions(partition),
            Proofs:     proof.Proof
        })
    }
    ```
4. Submit the PoSt result signed by the new wallet A and waiting for network verification (ONLY the data owner could pass this verification).
    ```golang
    // Submit the above posts result signed by wallet A
    msg := SubmitMessage(nWallet, posts)

    // Submit the message before challenge.CloseEpoch
    ```
5. Use the new wallet A to submit a proposal to change the owner key to a specified new key if PoSt result is verified.
    ```bash
    # provide a api to make a owner key change proposal by the verified wallet A
    lotus-miner actor change-owner-key-proposal --proposal-key=wallet A --owner-key=new owner key
    ```
6. Use the new owner key to confirm the owner key change proposal.
    ```bash
    // use the new owner key to confirm the proposal
    lotus-miner actor confirm-owner-key-proposal --proposal-key=new owner key --owner-key=new owner key
    ```


## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->
See the section Specification

## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->
This proposer require a new actor version and a network upgrade.

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->
N/A

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->
For this implementation a miner with the owner key lost requires a new key to submit a change owner key proposal and we use random PoSt challenge to verify the new key before it could make the owner key proposal. 

ONLY the miner own the real sector data could generate and submit a valid PoSt proof for the random challenge, If the number of partitions or deadlines challenged are enough(Challenge over 50% of its power ?) and the whole operation is very safe and also means the data owner owns everything like collateral and rewards not just the owner key control everything.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->
This is a proposal for all miners's benefit and have no impact on existing incentives.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->
This implementation will strengthen the network security and bring better engagement and investment experience, also reduce unnecessary operation and maintenance pressure.

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->
TODO

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
