---
fip: "<to be assigned>"
title: Remove cron-based automatic deal settlement
author: "Alex North (@anorth), Alex Su (@alexytsu)"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/800
status: Draft
type: Technical
category: Core
created: 2023-08-24
---

## Simple Summary
Add a method to the built-in market actor to allow storage providers to settle deal payments manually.
Stop performing automatic deal settlement in the built-in market actor's cron handler.
This removes risk that cron-based deal settlement work will overtake the chain's processing capacity.

## Abstract
Filecoin tipset execution includes a facility for scheduled execution of actor code at the end of every epoch. 
This "cron" activity has a real validation cost, which can be accounted in gas units, but is not paid for by any party 
(no tokens are burnt as a gas fee).

The built-in storage market actor uses cron at every epoch to perform maintenance
(mainly the settlement of payments) for active deals.
Since this work is "free" to the deal providers and clients, it is essentially a subsidised service.
The cost of this level of service is unsustainable, and threatens chain progress if utilisation grows. 
Similar subsidised service cannot be made available to user-programmed smart contracts, 
reducing their competitiveness as storage applications or markets.

This proposal instead provides a method for storage providers to settle deal payments manually, 
and disables the automatic settlement for new deals.
Existing deals continue to be settled automatically until they expire.

## Change Motivation
A fast and predictable tipset validation time is important to the ability of validating nodes 
to sync the chain quickly (especially when catching up), 
and critical for block producers to be able to produce new blocks for timely inclusion. 
Cron currently accounts for more than half of the computational cost of tipset validation,
and the built-in market actor accounts for a significant proportion of that.
Although there is significant a buffer in the target tipset validation times to account for 
network delays and the variability of expected consensus, 
extended cron execution can threaten chain quality and minimum hardware specs for validators.

Cron is very convenient for some maintenance operations,
but is essentially a subsidy from the network to whichever actors get the free execution (which is only ever built-in actors). 
Subsidised, automatic daily settlement of deals is far from the kind of critical network service for which cron was intended, 
and of zero value for the 98% of deals today that have zero fee.

The number of deals brokered by the built-in market has increased greatly over the past year. 
There are currently about 45 million active deals (~520 deals per epoch), a number which is growing quickly.

The processing cost of this maintenance nearly caused disaster prior to FIP-0060, 
which extended each deal's update period from 24 hours to 30 days.
However, this change only bought some time to design a more permanent solution.
There remains significant risk that this processing could grow beyond the ability of the chain to safely execute it.

### Impact of direct data onboarding
A concurrent proposal is to support skipping the built-in storage market actor for some data onboarding, 
which provides a cost reduction for arrangements that don’t need on-chain payments. 
As this capability is implemented and adopted, the number of built-in market deals might decrease 
even as total data onboarding increases.
If and when adopted, this would mitigate the risk significantly. 
However, this benefit depends on participants' adoption of the new onboarding methods, which is uncertain. 
The built-in market actor might in any case be host a large number of payment-bearing deals.
Thus, direct data onboarding cannot be relied upon in either the near- or long-term as a final solution.

## Specification
Today, at the end of each epoch, the market actor loads all deals that are scheduled for maintenance.
For each deal, the function:
- removes state for any unactivated deals that have timed out (“expired”);
- settles incremental payments for activated deals; and
- settles payments/refunds/penalties and removes state for any completed or terminated deals.

This proposal is to provide a new, explicit user message to settle payments, 
and provide an explicit method to settle deals.
Cron is still used to time out un-activated deals.

### Explicit deal settlement
A new `SettleDealPayments` method is added to the built-in storage market actor.
This may be invoked by a storage provider (or anyone on their behalf) to settle
incremental payments for a specified list of deals.
Settling the final payment for a completed deal also removes the deal metadata from state.

```
// Note transparent serialization for single-item struct.
struct SettleDealPaymentsParams {
    Deals: []DealID,
}

struct SettleDealPaymentsReturn {
    // Indicators of success or failure for each deal.
    Results: {
        SuccessCount: u32,
        FailCodes: []{
            Index: u32,
            ExitCode: ExitCode,
        },
    }
    // Results for those deals that successfully settled.
    Settlements: []DealSettlementSummary,
}

struct DealSettlementSummary {
    // Incremental amount paid to the provider.
    Payment: TokenAmount,
    // Whether the deal has settled for the final time.
    Completed: bool,
}
```

If the caller specifies a deal which has not yet activated nor expired, settlement succeeds but has no effect.
If the caller specifies a deal which has expired (not activated in time) or already terminated or completed,
settlement fails with the `USR_NOT_FOUND` exit code (regardless of whether cron has removed the deal proposal from state).

### Immediate clean-up on termination
The existing built-in market actor `OnMinerSectorsTerminate` method is changed to 
immediately make a final payment settlement, charge penalties, and clean up state.
It behaves as if `SettleDealPayments` was invoked immediately after marking deals as terminated.
This replaces the current technique of merely recording the termination epoch and then 
waiting for cron to do the work.

### No automatic settlement for new deals
When a deal is first published, it is added to the cron queue after its start epoch. 
If it is not activated prior to that epoch, it is expired and cleaned up in cron. 
This remains as it works today.

However, when the cron handler finds deal to have been newly-activated (i.e. has not been settled previously),
it is _not_ re-scheduled for subsequent automatic settlement.
Future settlements must be manual.

### Continued automatic settlement for existing deals
Deals that are already activated prior to this change continue to be settled automatically in cron.

### Transition
This proposal changes termination processing from deferred to immediate.
For a short period after this new code is deployed, it will be possible for a deal to have been marked as terminated
by the old code, but not yet cleaned up by the scheduled cron handler.

Deals that are marked as terminated are not eligible for manual settlement.
Specifying a terminated deal will cause `SettleDealPayments` to abort with `USR_ILLEGAL_ARGUMENT`.

## Design Rationale
An explicit settlement message aligns the gas cost of settling payments with the party deriving the benefit.
It also bounds the cost, like most other state transitions, by the block gas limit.
Providers might settle payments quite infrequently,
reflecting the relatively low utility of doing so, and will prefer periods of low gas demand.
Less frequent updates result in a lower system-wide amount of computation performed.

Storage providers are not expected to invoke settlement for deals that carry no payment.
The metadata for such newly-created but no-payment deals will thus remain in state indefinitely.
However, with direct data onboarding, there is little benefit and some cost to
involving the built-in market actor in new unpaid deals.
Relatively few additional unpaid deals might be accumulated after that is possible.
Stale blockchain state poses a much lesser risk to blockchain execution than continual processing.
If a large amount does accumulate, it could be dealt with independently.

Since no _new_ deals are scheduled for automatic settlement, 
the cron cost of settlement will gradually decline until there are no active deals scheduled.
At that point, a future simplification can remove the code for automatic payment settlement from the cron handler.
The scheme proposed involves no state migration.

Since sector termination may be invoked by the miner actor’s cron handler,
this will sometimes still do settlement work in cron.
This may be resolved by future changes to reduce miner actor's use of cron for terminations.
Explicit sector termination by the SP will account for the cost of settlement to their gas usage.

## Backwards Compatibility
This proposal does not remove or change any exported APIs, nor change any state schemas.
It is backwards compatible for all callers.
Since it requires a change to actor code, a network upgrade is required to deploy it.

The proposal does remove a subsidised function that some parties may have relied upon.
SPs who host paid-for deals with the built-in market actor must now settle payments manually.

## Test Cases
To be provided with implementation.

- Settlement is no-op for un-activated, expired, terminated, completed, or non-existent deal
- Settling a deal remits appropriate payment
- Repeated settlement at same epoch doesn't repeat payment
- Same total payment results from single or multiple settlements.
- No rounding errors result from frequent settlement

## Security Considerations
This proposal improves the progress of blockchain computation by reducing the amount of unnecessary processing,
and placing the necessary part under the block gas limit and market for computation.

This proposal does not introduce any reductions in security.

## Incentive Considerations
This proposal has some impact on the incentives to use the built-in storage market actor for deals by
placing the cost of settling those deals on the storage provider, rather than being subsidised by the network.
By subjecting deal settlement to gas marketplace, SPs are incentivised to use block space efficiently.
For example, SPs may settle payments less frequently, and thus incur less cost.

Note that a concurrent proposal to support direct data onboarding will remove the key incentive
to use the built-in market actor at all,
being that it is currently the only permitted way to commit data to the network.
Thus participants will have incentive to use the built-in market actor only when on-chain payments need settlement,
and a disincentive (cost) otherwise.

## Product Considerations
This proposal reduces the (unsustainable) level of service provided by the network to deal participants.
The level of service poses a critical risk to blockchain progress.

However, it also removes a subsidy to the built-in market actor that could never be provided to user-programmed smart contracts.
This change thus supports the future development of user-programmed markets to compete on a more level playing field.

## Implementation
Implementation of this proposal is in progress in https://github.com/filecoin-project/builtin-actors/pull/1377.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
