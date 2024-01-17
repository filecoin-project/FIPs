---
fip: "to be assigned" <!--keep the quotes around the fip number, i.e: `fip: "0001"`-->
title: EC finality calculator
author: "Guy Goren (@guy-goren), Jorge Soares (@jsoares)"
discussions-to: foo.com
status: Draft
type: "FRC"
created: 2024-01-03
---

# FRC-XXXX: A Finality Calculator for Filecoin

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->
Filecoin's Expected Consensus (EC) comes with probabilistic finality, and a 900-epoch soft finality threshold. While network participants (e.g. exchanges, L2 operators, application developers) use different confirmation thresholds, they pessimistically wait between 100-900 epochs before considering a transaction final, leading to delays in the order of hours. Instead of naively counting the number of epochs, we propose a finality calculator that takes into account what takes place during those epochs and, under expected operating conditions, can attain the same level of certainty in fewer epochs. For example, consider two cases: in case A, the chain grew by 5 blocks per epoch over the last 50 epochs; in case B, the chain grew by a mere 2 blocks per epoch over the same 50 epochs. The probability of a chain reconfiguration longer than 50 epochs is much smaller in case A than in case B, thereby allowing us to make a faster finality determination.

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->
We embark on an analysis of Filecoin's finality, i.e., the probabilistic guarantees that a given tipset will always be in the canonical chain. The analysis involves distributed computing and stochastic arguments and provides upper bounds for the error probabilities, i.e., the probability that a reorg would override a given tipset. We do this by using a dynamic evaluation which takes into account the specific observed history of the chain. Unlike a static analysis that considers the worst case conditions, we consider the worst-case conditions in the (unknown) future but do not consider the worst-case past. Instead, we use the observed chain to reason about the (known) past. 

The result is an algorithm that, given a specific chain history, provides an upper bound on the error probabilities. Several key applications of Filecoin currently use a 900-epoch (7.5 hours) settlement period to provide an intended finality guarantee of $2^{-30}$. Our analysis shows that, in real operating conditions, the same error probability  $2^{-30}$ can be achieved in ~30 epochs (15 minutes) -- a x30 improvement. This algorithm is practical and can be implemented by clients or off-chain applications without requiring any changes to the protocol.

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->
The motivation fos this proposal is twofold: 
- To provide theoretical guarantees for Filecoin that are grounded on clear formal arguments. 
- To reduce the delays experienced by users of Filecoin.  

We remark that F3 will also address both of this points (with even faster finality). Nevertheless, this work does not conflict with F3 and independently provides several benefits:
1. It requires no change to client code, and therefore no agreement process. Instead, it is a simple algorithm that any node can run separately from the "mining process". The algorithm takes as input the observed history of the chain and outputs a measure of safety.
2. It does not change the incentive considerations of Filecoin, which remains a longest-chain blockchain similarly to BTC and ETH. Since no extra work is mandatory, the algorithm's execution (or no execution) does not affect the safety of Filecoin.
3. It is an algorithm and not a protocol. That is, its execution is local and the result does not depend on other nodes executing the algorithm as well. For the same reason, it requires no additional communication and is therefore infinitely scalable.
4. In case F3 halts and the network falls back on EC finality, it can reduce the degradation experienced by users.

Notably, (1) implies that our proposal can be used as an interim solution for Filecoin until F3 goes live on the network.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->
The analysis detailing how we bound the finality of a given input can be found [here](https://docs.google.com/document/d/1QpIpOLaabvieTrbgXzOSg3p1Z5SbNInGNqzBNFrCgXQ/edit#heading=h.c5olklehxrdn). We will be providing a more digestible version soon.

### Preliminary

### Analyzing the probability of errors

### EC finality for users

<!-- You have some errors, warnings, or alerts. If you are using reckless mode, turn it off to see inline alerts.
* ERRORs: 1
* WARNINGs: 2
* ALERTS: 100 -->

Our analysis is based on the two lemmas below. Roughly, they establish that a validator/user has visibility to all chains that end with an honest block. Recall that the fork choice rule in Filecoin is based on chain weight and validity, where “weight” incorporates the number of blocks together with the approximated storage space required to create them, and “validity” is determined by a set of rules that govern the correct construction of blocks. For simplicity, we shall ignore the subtleties of the two and refer to the “best” tipset as the tipset at the end of the heaviest valid chain, as well as conflate the weight of a chain to the number of blocks it contains.

**Lemma 1**: Let $B_h$ be a block produced by an honest validator at round $r$, then the tipset chain ending at $\texttt{parent}(B_h)$ is known to all honest validators by round $r+1$.

**Lemma 2**: Let $r_{curr}$ be the current round. Let $tipset_A[v_i]$ be the “best” tipset of which validator $v_i$ is aware (and would choose as parent) which ends in round $r_A$, and let $competingTipset_B[v_i]$ be the “second-best” tipset of which $v_i$ is aware and which ends in round $r_B$. Then, in the interval $[r_b,r_{curr}-1]$, the tipset chain of $competingTipset_B[v_i]$ could have been extended only with malicious blocks (blocks proposed by malicious validators).

TODO: What do we mean by a tipset "ending" in a round? Should these be tipset chains rather than tipsets?

We can now start the derivation of the probabilities.

#### Step 1

TODO: consider using r_s and r_c, in line with lemma 2

Denote by $s$ the epoch for which the finality probability is being evaluated, and by $c$ the current epoch ($c>s$). The random variable $L_f$ describes the adversarial (secret) lead gained from the last final tipset (e.g., the tipset at epoch $c-900$) until epoch $s$. It behaves as a biased random walk whenever $L_f>0$ but does not decrease when $L_f=0$. For each epoch $i \in [c-900+1,s]$, the “random walk” step’s expectation is $f \cdot e - chain[i]$, where chain[i] is the number of blocks at the tipset of the lh-chain that was constructed at epoch $i$ and $f \cdot e$ is the expected number of adversarial blocks at an epoch (i.i.d).

TODO: What's the "lh" chain?

To account for the distribution of $L_f$ we can look at a reverse process ($L_f'$) that starts at the tipset of interest of epoch $s$ and moves backwards in time. (This is possible because the steps are i.i.d.) In this case we get that $L_f'$ is distributed according to the following: 

$Pr[L_f' = k] = \max{\lbrace Pr[L_{f1}'=k_1],Pr[L_{f2}'=k_2],... \rbrace}$, where, for simplification we replace the binomial distributions of the steps by a poisson distribution. We get $L_{fi} \sim Pois(\sum_{j=s}^{j=s-i} f \cdot e)$, and $k_i=k+\sum_{j=s}^{j=s-i} chain[j]$. We conclude that $L_f \triangleq \max{\lbrace L_f',0 \rbrace}$.

TODO: the variable of the sum is not indexed on j

For example, let's use the values $e=5$, $f=0.3$ and the following observed history
![drawing](https://docs.google.com/drawings/d/12345/export/png)

In this example, we have $L_{fi}' \sim \texttt{Pois}(\sum_{j=s}^{j=s-i} 1.5)$ and $\lbrace k_0=5,k_1=8,k_2=14,... \rbrace$. Notice that with each additional step of our random process (adding a previous epoch to the calculation), the expectation of $L_{fi}'-\sum chain[j]$ is reduced. Specifically:

|$E[L_{f0}-\sum_{j=s}^{j=s-0}chain[j]]$|$E[L_{f1}-\sum_{j=s}^{j=s-1}chain[j]]$|$E[L_{f2}-...]$|$E[L_{f3}-...]$|$E[L_{f4}-...]$|$E[L_{f5}-...]$|
|---|---|---|---|---|---|
|$-3.5$|$-3.5-1.5=-5$|$-9.5$|$-12$|$-16.5$|$-20$|

#### Step 2

The random variable $B_f$ is independent from $L_f$ and follows a simple binomial distribution as explained previously for $X_f$. That is, $B_f \sim \texttt{Bin}(N=\sum_{i=s+1}^{i=c-1} f \cdot n, p=\frac{e}{n})$. For ease of computation, we again estimate the binomial distribution by a Poisson one. Specifically, by $B_f \sim \texttt{Bin}(\sum_{i=s+1}^{i=c} f \cdot e)$

TODO: Where is X_f?

#### Step 3

Lastly, we calculate the random variable $M_f$, the adversary’s “catching up” in the future. The production of honest blocks follows a binomial distribution. However, it might be that not all honest blocks are added to the same tipset (due to pointing to different parent tipsets). This is only achieved by the adversary splitting the honest chain. Specifically, the adversary must be able to provide parent tipsets which are “better” than the currently available lh-chain one (with tie-breaking in the adversary’s favor). We calculate a lower bound on the public chain growth rate based on the following two assumptions:

* Using the blocks of epoch $i$, the adversary can optimally split the network power for epoch $i+1$ (the next epoch), however, 
* only (adversarial) blocks from epoch  may be used to split the power at epoch $i+1$.

The first assumption considerably favors the adversary, while the latter moderately favors us by somewhat limiting the adversary’s capabilities. We conjecture that these assumptions correspond to a lower bound without them since, compared to without them, they seem to favor the adversary more than us. This is due to the practical difficulty of coordinating a perfect split (not just in expectation), which significantly benefits the adversary. While, on the other hand, using only recent blocks for the split (the assumption that benefits us), probably has a smaller effect due to the diminishing probability of them maintaining relevance.


With Consistent Broadcast, we have that for $b[i]$ and $h[i+1]$ being the number of ADV blocks and honest blocks in epochs $i$ and $i+1$, respectively, the honest chain grows by at least $\min{\lbrace\frac{h[i+1]+b[i]}{e^{b[t]}},h[i+1]\rbrace}$


We therefore have that at step  the random variable $M_f$ changes according to the sum: $b[i]-\min{\lbrace}$. Since  and  are both i.i.d variables that are uncorrelated, we get an expected step (per epoch) of 

~~.~~

To simplify the calculations, we replace the random variable  by  In particular, 



~~.~~

We define the random process  recursively to be   with .  That is, . Moreover, for each  we have that  and that . Thus, we conclude that . As a difference of two independent Poisson-distributed random variables, each  follows a [Skellam distribution](https://en.wikipedia.org/wiki/Skellam_distribution) with parameters  and .

<span style="text-decoration:underline;">Final step</span>:

In summary, for an observed good addition , the safety violation event  happens only if one of the three mutually exclusive events occur:



1. 
2.  but 
3.  but 

We get that 



## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->
There are no backward compatibility issues, as this FRC provides a recommendation to clients/applications with no change to the existing consensus mechanism or protocol. 

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->
We have run our algorithm on past chain data from Filecoin mainnet. The periods analyzed are heights 3,356,200 to 3,356,700, which represent a typical healthy state, and heights 2,764,600 to 2,766,000, which was a less healthy period for Filecoin. The figures below show the results of quantifying the finality of tipsets after a 30-epoch delay. The potential adversarial power we considered is 30%. We note that one may choose other questions to analyze, such as, when does a specific tipset reach a given finality threshold.

The figure below shows the results of applying the analysis on a typical healthy chain period, when tipsets are almost full (5 blocks) on average. On the $x$-axis we have the epoch numbers. We have a double $y$-axis: on the right axis, we have the number of blocks in tipsets (plotted in green, with the moving average in red), and on the left axis we have the error probabilities after 30 epochs (plotted in blue). One can see that it is mostly below $10^{-10}$, implying that a reorg of this tipset is a "once in 10,000 years" event. It is clear how a higher number of blocks per epoch typically results in better finality measurement (smaller error probability).

![Good times](../resources/frc-xxxx/err_prob_and_block_count_november.png "Good times")

The figure below shows the results of applying the analysis on a period when the Filecoin blockchain was less healthy (around the end of March 2023). The tipset are less than full on average --- often falling to below 4 blocks per tipset when averaged over 30 epochs. The plots and axis are analogous to before, though note the different vertical range. As expected, the finality measurement is worse than in the typical "good case", that is, the error probabilities are higher by several orders of magnitude at times.
![Bad times](../resources/frc-xxxx/err_prob_and_block_count_march.png "Bad times")

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->
* From the perspective of the network, the proposed algorithms provides more transparency on the security guarantees provided by Filecoin, without impacting them in any form. 
* From the perspective of the client/adopter, accepting a transaction as final after fewer epochs, while *prima facie* more risky, only equalizes the level of certainty across different network conditions and provides the same security.
* It is possible to misuse the algorithm and accept an error probability that is too high in attempting to over-optimize for latency. This is akin to picking an insufficient number of epochs in the current paradigm, with the key difference that the error probability can be easily interpreted, whereas the number of epochs cannot.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->
There are no substantive incentive considerations. 

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->
* Applications built on FVM (e.g., IPC) do not need to wait for 900 epochs and can instead benefit from faster finalization times, further tuned to their own requirements.
* Other users of Filecoin (e.g., exchanges) can provide faster finality (e.g. on withdrawals) without compromising security.

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->
A Python prototype of the algorithm is available [here](https://github.com/consensus-shipyard/ec-finality-calculator). This implementation tries to translate the specification with minimal changes rather than optimize for performance. As an application-side optimization with no interoperability requirement, implementers in different clients and languages may freely diverge from the prototype. 

## TODO
<!--A section that lists any unresolved issues or tasks that are part of the FIP proposal. Examples of these include performing benchmarking to know gas fees, validate claims made in the FIP once the final implementation is ready, etc. A FIP can only move to a “Last Call” status once all these items have been resolved.-->
N/A

   
## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).