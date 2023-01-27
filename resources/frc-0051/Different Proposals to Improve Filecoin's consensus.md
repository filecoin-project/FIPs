###### tags: `Y4` `Y`

# Different Proposals to Improve Filecoin's consensus

Xuechao did some great work and showed that the security threshold of EC is **at least** 20%, i.e., we can show that EC is secure for any adversary that has <20% of the power, i.e., for any adversary with less than 20%, there exists a parameter `k` such that no adversary can create a fork of length at more than `k` epochs.
Furthermore he also showed that the security threshold of one of the [epoch boundary attacks](https://docs.google.com/document/d/1xenxMKxCnUfMz5PGFV7QK8wyUl0rIDUQR2LVHc8-WeU/edit#bookmark=id.xex16bi5qakf) that we proposed a long time ago is also 20%, meaning that the attack will succeed with constant probability for any adversary that has at least 20% of the total power. We thus conclude that the true security threshold of EC is 20%.
We propose mitigations against epoch boundary attacks below, and we present their pros and cons.
We also provide a concise comparison (i.e., table) of the different proposals.
We finish by making a recommendation.



## Longest-chain (LC)
The first mitigation is to remove tipsets, i.e., enforce the size of each tipset to be equal to exactly one. This will also imply changing the value of the expected number of leaders from 5 to 1.
In this case we can have a full security proofs for Filecoin (reusing existing work) for any adversary with less than 50% of the power.
Note that due to some efficiency constraints on some of our parameters (`WindowPostDelay` and `PreCommitChallengeDelay` parameters) in practice we will downgrade our adversary, i.e., we will consider an adversary with ~20-30% of the power.

Some numbers:
- For a 20% adversary the probability of private forks of length:
    - 60 (`WindowPostDelay`) is $10^{-6}$
    - 150 (`PreCommitChallengeDelay`) is $10^{-12}$
- For a 30% we have the following:
    - 60 (`WindowPostDelay`) is $10^{-3}$
    - 150 (`PreCommitChallengeDelay`) is $10^{-6}$
    - 350 is $10^{-12}$
    
If we want to consider a 30% adversary, we may need to update `WindowPostDelay` from 60 to 150 and `PreCommitChallengeDelay` from 150 to 350.
All these probabilities were computed using [this code](https://github.com/filecoin-project/consensus/blob/finality/code/finality/SSLE_project/pmf_ssle_vs_ple.py).

## Completely change the protocol
Another mitigation against epoch boundary is to use a completely different protocol that is not vulnerable to this attack. We propose a few different options below.
A longer discussion can be found [here](https://github.com/protocol/ConsensusLab/discussions/117). 

### Algorand

[Algorand](https://github.com/protocol/ConsensusLab/discussions/114) was proposed in a proof-of-stake setting and we believe we could adapt to the proof-of-space setting without effort (including reusing the proof). It has the advantage of providing instant finality and is provably secure against a 33% adversary.

### Prism
[Prism](https://github.com/protocol/ConsensusLab/discussions/106#discussion-4159980) was proposed in a proof-of-work context but could easily be extended to a proof-of-storage setting. The proof would require some work to be adapted but we believe this is doable with a bit of work. This improves on longest-chain protocols by adding a voting mechanism.

### Bobtail 
[Bobtail](https://github.com/protocol/ConsensusLab/discussions/152) was proposed in a proof-of-work setting. [Guy proposed](https://docs.google.com/document/d/19GirH1sB3GXHaXEna2dClQvmofVWVQJCkLBrH8v-g8M/edit?usp=sharing) to apply it to the proof-of-space settings.
There does not currently exist any security proof but Xuechao and Sarah started writting some argument.


## Consistent Broadcast (CBcast)
This solution, [proposed by Guy](https://hackmd.io/@consensuslab/SJXp9Glp5), consist in changing EC's broadcast protocol to a *consistent broadcast* (CBcast) that effectively prevents an adversary from equivocating, i.e., the adversary cannot send two different blocks with the same election proof (such blocks will not be accepted by any other honest online miners).
This proposal effectively mitigates the worst attack that we found on EC but we do not know what would be the worst attack in this case.
We found [another attack](https://hackmd.io/8Lu4POvKTnWeTMHtbtgI6w) that has a security threshold of 44% but we do not know if any worse attack exist. Furthermore the security threshold for CBcast is around 33% anyway (TBD). We can thus conclude that the security threshold of EC with CBcast is between 20% and ~33% but we cannot conclude more than this at the moment.

## Comparison
:green_heart:: pro
:large_orange_diamond:: neither a pro nor a con
:red_circle: : con
:question: unknown
| |EC | LC | EC with CBcast | PoStBobtail | Algorand | Prism |
|-------- |-------- | -------- | -------- |-------- |-------- |-------- |
| Security threshold |:large_orange_diamond: 20%    |:large_orange_diamond: Although LC's security threshold is 1/2, due to our proof-of-space requirements, we will need to downgrade this to ~20-30% and/or increase `WindowPostDelay` and `PreCommitChallengeDelay`   parameters  |:large_orange_diamond: We do not know but between 20% and 33%     | :question: TBD but at least 20% | :large_orange_diamond: 33% for provable security, 20% for perfomance requirements | :large_orange_diamond: 50% for provable security, 20-30% for realistic use case |
|Change in code |:green_heart: none | :green_heart: medium (change the form of tipsets and the `ExpectedNumberOfLeaders` parameter) | :large_orange_diamond: TBD (Probably medium to hard)|:large_orange_diamond: TBD (Probably medium to hard)| :red_circle: Complete change|:red_circle: Complete change|
|Security proof |:green_heart: Done by Xuechao |:green_heart: Easy (reuse work already done) |:red_circle:  hard (we do not know if this is possible/ long-term open problem)|:question: may be hard to prove |:green_heart: done |:green_heart: could be extended from the Prism paper (using results from PoS LC)|
|Finality computation|:red_circle: hard to compute (based on simulation of the worst attack, no formal analysis)  |:green_heart:Easy to compute (will depend on the security threshold we choose) | :red_circle: Hard to compute | :question: Probably hard to compute| :green_heart:instant finality |:green_heart: good (better than LC) |
|Finality parameter|:large_orange_diamond: comparable to LC (probably a bit worse) |:large_orange_diamond: OM 300 | :question: ? | :question: ? | :green_heart: 1 |:green_heart: better than LC |
|Incentives | :green_heart: no change |:red_circle: Miners may be unhappy about being elected leader less often so the rewards of blocks should probably be increased (e.g. x5)|:green_heart: No change| :large_orange_diamond: can be inherited from Bobtail/eth2.0|:large_orange_diamond: will  need some work | :large_orange_diamond: need more work |
| attacks | :red_circle: epoch boudaries |:large_orange_diamond: Private attacks are the worse attacks | :large_orange_diamond: weaker form of epoch boundary attacks | :green_heart: no efficient attack found | :green_heart: no attack | :green_heart: no attack |
|Chain quality|:red_circle: 1 block every `finality` |:red_circle: 1 block every `finality`  | :red_circle: 1 block every `finality`  | :question: Probably better than LC and co. | :green_heart: 1 |:red_circle: 1 block every `finality`  |
<!---
### 20% threshold
Question: what is the price of corrupting 20% of the network?

As of today (Aug. 25 2022) the total storage in filecoin is 18.257 EiB.
Corrupting 20% of this corresponds roughly to 3.6 EiB.
According to [this link](https://www.techtarget.com/searchstorage/definition/exbibyte-EiB#:~:text=An%20exbibyte%20of%20storage%20will,%24146%2C000%2C000%20as%20of%20mid%2D2018.): 1 EiB of storage costs ~100M USD or 4M a month on Amazon glacier (hence 14.4M a month for an attack with 20% of the power).
That's ignoring the FIL collateral.


### Discussion Sarah/Guy:
EC with Cbcast: it's "just" a patch.
LC: familiar, easy but not perfect
PostBobtail: interesting protocol, no obvious attack, good concept. More research oriented.

- Guy's: do the patch for EC (i.e., CBcast) and continue with researching PostBobtail.
- Sarah: agrees but prefers LC as a patch.
- Guy: community may not like the LC approach.
- Sarah: LC gives us a full security proof. EC with CBcast, only Xuechao's proof, do not know what's the worst attack now.
- Guy does not like Algorand. $\epsilon$ proba of breaking the system. treat eery block as final,d do not allow for errors. Recovery mechanism.
-->

## Decision
During our team week, we discussed the proposals above and we decided to choose the consistent broadcast solution. Our reasoning was as follows.
First implementing a completely new protocol is not completely ruled out but will be investigated as a long-term research problem. We believe that in the meantime, while more research is being conducted, a "quick" solution should be implemented regardless to mitigate the worst attack in EC. For this reason, the two following proposals were short-listed: EC with consistent broadcast and longest-chain protocols (LC).
The main advantage of using LC is that its security has been extensively studied and thus this is known territory. We know what we are getting: provable security against a <50% adversary. We also know what the issues are: long finality which means that in practice we will have to consider a weaker adversary (e.g., with 20-30% of the total power). Furthermore, we believe that the changes in code are quite trivial. The main issue with LC is that, philosophically, it looks like a big change to the protocol and we expect to receive an important pushback from the community making this solution impossible to deploy in the short-term.
Consistent broadcast, on the other hand, does not fundamentally change the protocol, i.e., we only replace a small, black-box, part of the protocol. Furthermore, although the security guarantees that we get from this are hard to formalize, it is easy to see that it does not make the protocol worse, hence it can only improve it.  We believe in the short-term this is the best path forward although we will keep working on long-term solutions.
