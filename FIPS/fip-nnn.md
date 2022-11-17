---
fip: "00xx"
title: mproving EC security with Consistent Broadcast
author:  Guy Goren <guy.goren@protocol.ai>, Alfonso de la Rocha <alfonso@protocol.ai>
discussions-to: https://github.com/filecoin-project/FIPs/discussions/501
status: Draft
type: Technical
category: Core
created: 2022-11-07
spec-sections:
---

# FIP: Improving EC security with Consistent Broadcast

## Simple Summary
Modifies client behaviour (in particular the miners) to verify that the sender is not equivocating before accepting a block.

## Abstract
Currently, a block is accepted if it is received before the cutoff time and is the first from its sender in the epoch. Blocks that are received after the cutoff time are ignored. This mechanism enables an attacker to exploit the cutoff in order to send equivocating blocks (i.e., different blocks in the same epoch, with the same "winning ticket") to different miners, causing miners to build upon different tipsets and, hence, damaging the progress of the honest chain.

This proposal suggests a simple fix to the above. A recipient waits a predefined time (e.g. 6 seconds) between receiving a block and accepting it. If, during this time, the recipient detects equivocation, it does not accept the block. By waiting, the recipient can be practically certain that a sender's equivocation will be suppressed since by this time (practically) all other miners would also hear of the block via gossip.


## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->
A [security analysis](https://drive.google.com/file/d/1KFykwDHQxsgbOApbLKDZL6ViOQBQoQBf/view?usp=sharing) shows that, given the current "best effort" broadcast combined with the cutoff time, an attacker with $>20\%$ of the power (storage) can break the security of Filecoin. The proposed improvement essentially replaces the *best effort* broadcast (*beb*) with a variant of *consistent* broadcast (cb). The difference is, in short, that *beb* broadcast allows two honest miners to deliver different blocks published by an equivocating Byzantine miner in the same epoch,  which *cb* does not. The result will be that an attacker [will require $>44\%$](https://hackmd.io/@consensuslab/ByltVcfAc) of the total power (adjusted storage) to successfully mount this particular attack.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->
The following pseudocode describes the consistent broadcast verification algorithm at a high level. Notice that the proposed change affects only the Filecoin miner as a receiver of a tipset; sending (and gossiping) a block remains unchanged. ```Delta``` is a tunable parameter which corresponds to the assumed upper bound on gossip delay (originating from an honest node). The protocol also uses ```block_set```, a dictionary where a key is a tuple ```<round, winning_ticket>``` and a value is a set of blocks (for efficiency, blocks could be represented by their hashes).
``` python= 
Delta = 6 seconds                  # time for gossip to reach all
Upon receiving block B=<source, round, winning_ticket> do:
    propagate B acording to the gossip protocol;
    if B is valid:
        if not block_set[round, winning_ticket]:
            block_set[round, winning_ticket] = {};
        block_set[round, winning_ticket].add(B);    # can use hash of B
        if len(block_set[round, winning_ticket])>1:
            return                 # detected equivoqation
        wait Delta;                # wait the gossip time to ensure reach
        if len(block_set[round, winning_ticket])==1:
            return B
```

Garbage collection is handled orthogonally: ```block_set[round, winning_ticket]``` can be deleted after $k\ge1$ epochs (depending on how long you wish to allow block propagation -- currently $k=1$ in EC).

## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->
The design goal is to introduce a simple change without severe repercussion to other functionalities of the systems. This means approaching the core of the matter (the mechanism that enable equivocation). This allows for orthogonal changes in the incentive design mechanism, since the change does not tie them together.
### Potential strategies
The ConsensusLab team explored potential mitigation strategies and narrowed down the list for the following possible strategies: (for more details see [this document](https://hackmd.io/@consensuslab/HyaNMcMAq))

- Removing tipsets from EC, effectivelly boiling down the protocol to a longest-chain instead of a longest-tipset protocol. By removing tipsets and having a traditional blockchain design (i.e., one block per epoch) the problem is mitigated.

    :+1: Simple to implement -- changing the expected number of blocks from 5 to 1.

    :+1: Easier to analyse theoretically -- trivially follows the existing literature on Proof-of-Stake blockchains.

    :-1: Damages the expected settelment times in the simple case. I.e., it takes longer (more epochs) to achieve 99% settlement certainty against the simple block witholding attack.
    
    :-1: The impact of a change would be substantial and very possibly negatively percieved by the community. Changing the number of blocks per epoch affects the miners economic calculations directly and is very visible to miners and the entire ecosystem. This is a very negative point about this option. 
    <!---Since this is only a quick fix -- the team is working towards a more in-depth consensus protocol improvement -- we should minimize the effect on the community of the quick fix and save our credit for the possible protocol change.--->
    
    :-1: Requires a Filecoin upgrade. Might split the blockchain between adopting miners and not-yet adopting miners.

- Adding an *asynchronous* consistent broadcast layer. By adding a Consistent broadcast (C-BCast) the attacker can no longer equivocate. This solves the problem at its core.

    :+1: Strikes at the core of the issue --- the equivocation of the attacker, by making a very targetted and specific consensus change. 

    :+1: Arguably easier to be accepted by miners. They feel no meaningful difference (same number of expected blocks, same payments, etc.), the change is behind the scenes only.
    
    :+1: Does not depend on timing assumptions.
    
    :-1: Requires a Filecoin upgrade. A miner that adopts the change cannot receive blocks from miners that didn't adopt the change.
        
- **Adding a *synchronous* consistent BCast layer (with the [6 second](https://gist.github.com/jsoares/e34a0f9e387edca003bd039c4579b103) ```magic number```).**

    :+1: Strikes at the core of the issue --- the equivocation of the attacker, by making a very targetted and specific consensus change. 

    :+1: Arguably easier to be accepted by miners. They feel no meaningful difference (same number of expected blocks, same payments, etc.), the change is behind the scenes only.
    
    :+1: Does not require a fork.
    
    :-1: Depends on timing assumptions. That is, gossip propagation within 6 seconds.
    
---
    
**The ConsensusLab research team recommends the use of synchronous consistent broadcast as the mitigation strategy** (i.e., the last of the three proposed mitigations). The benefits of easy adoption due to only "behind the scence changes" and no <!--fork-->Filecoin-upgrade required, outweigh the shortcomings (timing assumptions). Moreover, even if the timing assumptions are violated, the consistency degrades gracefully (that is, a slightly longer than expected gossip delay would lead to only a small amount of equivocating blocks being accepted rather than to a "cliff phenomenon" where all equivocating blocks are accepted). Also, using the synchronous approach does not require significant changes to the [underlying broadcast protocol](https://blog.ipfs.tech/gossipsubv1.1-eval-report-and-security-audit/), which is already well tested and has built-in failure detecting mechnisms. 

## Backwards Compatibility
The proposal does not introduce backward compatibility issues. A miner that adopted the change will still accept blocks from honest non-adopting miners, and non-adopting miners will still accept blocks from adopting miners. The systems' security will improve monotonically with the share of adopting miners.

## Test Cases
The following tests need to be done:
- Demonstrating the attack on the current system (with naive BCast)
    - We have the implementation of the basic attack (for each round independently).
    - No tests in testground were performed. <!--When we attempted to run Testground with more than 3 miners (even with classic lotus) weird forking happend at the genesis block already.-->
- Showing the same attack after the implementation of Consistent BCast
    - We have the implementation of an upgraded lotus client (incorporates consistent BCast).
    - We have the implementation of an attacking node (same as before).
    - No test in testground was performed.
- Showing the performance of the improved protocol in normal test cases
    - We have the implementation of an upgraded lotus client (incorporates consistent BCast).
    - Possibly run a few upgraded miners on mainnet for a while showing that they function correctly. This is possible since the fix does not break consensus.

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->
Replacing the naive best-effort broadcast with consistent broadcast **improves** considerably the security of Filecoin. There is the risk of using the synchronous approach which relies on timing assumptions (in cases of extreme network asynchrony, in which case the modified protocol would not be worse in terms in security than the current protocol). However, the benefits of the synchronous approach outweigh the risks.  
Regarding liveness, we do not forsee problems due to the added delay prior to acceptance. This is because 1) assuming a worst-case propagation delay of 6 secondes, any `cutoff`$>12$ suffices, and 2) the additional 6 seconds waiting period does not require resources, so it may be used to precompute (e.g. winning PoSt) for the mining period.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->
The proposal is intentionally decoupled from incentive considerations. It is neither dependent on them, nor does it limit changes to incentive mechanisms.

A question may arise: isn't equivocation slashable in Filecoin, and therfore should not concern us?
Equivocating is indeed slashable, however, there are 2 issues regarding slashing as a solution.
**tl;dr: 1) conceptually, it is dangerous to rely on rationality that is based only on internal incentives. 2) Slashing/Blacklisting does not solve the problem.**
1) Assuming rationality of the attacker implies that we know their incentives (typically assumed that those incentives are just to maximize their internal profits in Filecoin). In practice, we don't really know the attacker incentives. For example, since performing this attack would severely damage Filecoin's credibility, an attacker that "rationally" gains extra Filecoins from the attack might, actually, lose due to Filecoin's collapse. On the other hand, an attacker that externally benefits from a Filecoin collapse (e.g. short trading) might not care about the slashing. Thus, it is dangerous to rely on rationality that is based only on internal incentives.
2) Slashing/Blacklisting does not solve the problem. In Filecoin, an attacker can spread their power (storage) over multiple identities. For example, a 20% attacker can have as much as $3.6\times10^5$ different identities. Since these identities seem independent to all but the attacker, slashing will only affect the individual identity that equivocated at that epoch. Therefore, the attacker can sacrifice (w.h.p.) one identity per epoch. And even after attacking for ~1000 epochs the attacker will only sacrifice less than 0.03% of her resources.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->
By mitigating attack on Filecoin, the proposal improves the resilience of the system. The proposal does not require any operational changes (besides adopting the protocol update) from the users.

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->
The prototype implementation lives in the following repo: 
- [Upgraded version of Lotus with consistent broadcast](https://github.com/adlrocha/lotus/tree/adlrocha/consistent-bcast): Implementation of the synchronous consistent broadcast fix over Lotus. 

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
