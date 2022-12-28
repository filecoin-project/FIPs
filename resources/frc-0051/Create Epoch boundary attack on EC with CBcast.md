# Epoch boundary attack on EC with CBcast

This document proposes and analyzes an epoch boundary attack on expected consensus with consistent broadcast.


## Epoch boundary attack
Consistent broadcast is [proposed by Guy](https://hackmd.io/l07vRuHvTzWF8zG3kEEQuQ) as a mitigation to the epoch boundary attack on EC. With consistent broadcast, the adversary is prevented from equivocating (i.e., creating two blocks with the same leader election proof). 

However, the adversary is still able to split the network to some extent. When the adversary is elected, say $\ell \geq 1$ times in one epoch (here we assume that the adversary controls many different participants). Then the adversary could send each of its blocks (with different election proofs) to a selected number of nodes at the right time (i.e., close to the cutoff) to ensure that only part of the nodes accept each block. The network is then split in $2^\ell$ ways (all the combination of accept vs reject for each of the $\ell$ blocks). The adversary needs to smartly divide all honest nodes into $2^\ell$ subsets to make sure that all the forks have almost equal weights in the next epoch (the difference is at most one). To make the analysis easier, we assume the adversary always makes the best decision as if it knows the future.

In addition, when the adversary is elected for many times (e.g., $\ell \geq 3$), releasing all $\ell$ blocks might not be a good idea because all honest nodes will receive all blocks by the end of next epoch. Therefore, let $\ell_{max}$ be the maximum number of adversarial blocks that will be used to split the network in one epoch.

While trying the best to split the network, the adversary can also reuse all its blocks to build a private chain. Note that CBcast only prevents equivocation in the current epoch. If a node receives a heavier chain which contains a block previously rejected by the CBcast protocol, it should still accept this heavier chain.

## Threshold analysis

We calculate the threshold of this epoch boundary attack. We do this by comparing the chain growth (per epoch) of the honest chain and the private chain. Here are some parameters:
- $m$: expected number of blocks per epoch;
- $\beta$: fraction of adversarial power;
- $\ell_{max}$: the maximum number of adversarial blocks that will be used to split the network in one epoch;
- $A$: number of adversarial blocks in epoch $r-1$, $A \sim Poisson(\beta m)$;
- $H$: number of adversarial blocks in epoch $r$, $H \sim Poisson((1-\beta) m)$.

Then the chain growth of the private chain is just $\mathbb{E}[A]$. Next, we look at the honest chain growth:
- When $A=0$, the views of all honest nodes at the end of epoch $r-1$ converge. So, the honest chain growth is $H$.
- When $A=1$ (i.e., there is one adversarial block $B$),  all honest nodes are split into two subsets (receiving $B$ or not receiving $B$). And the minimum honest chain growth is $\lfloor H/2 \rfloor +1$. Note that here we count adversarial blocks in epoch $r-1$ and honest blocks in epoch $r$. All blocks in the honest chain are counted exactly once.
- When $A=2$ (i.e., there are two adversarial block $B_1, B_2$),  all honest nodes are split into four subsets ($\emptyset, \{B_1\}, \{B_2\}, \{B_1,B_2\}$). One can check that the minimum honest chain growth is $\max(\lceil H/4 \rceil +1, 2)$. Note that the goal of the adversary is to make sure that the four forks have almost equal weights (the difference is at most one).

Let $X_{\ell_{max}}$ be the honest chain growth. When $\ell_{max} = 1$, we have
$$\mathbb{E}[X_1] = \mathbb{P}(A=0)\mathbb{E}[H] + \mathbb{P}(A>0)\mathbb{E}[\lfloor H/2 \rfloor +1].$$

When $\ell_{max} = 2$, we have
$$\mathbb{E}[X_2] = \mathbb{P}(A=0)\mathbb{E}[H] + \mathbb{P}(A=1)\mathbb{E}[\lfloor H/2 \rfloor +1] + \mathbb{P}(A>1)\mathbb{E}[\max(\lceil H/4 \rceil +1, 2)].$$

By comparing $\mathbb{E}[X_{\ell_{max}}]$ with $\mathbb{E}[A]$, we can derive the threshold for this epoch boundary attack. Numerically, when $\ell_{max} = 1,2$, the threshold is ~44%. Therefore, so far we know the true security threshold of EC with CBcast is in [20%, 44%]. However, this would be hard to prove that the is the threshold for every attack in EC (and hence the tight threshold) although we know it is the threshold corresponding the the worst attack we know.

