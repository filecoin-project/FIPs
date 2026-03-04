---
fip: "<to be assigned>"
title: Multi-Stage Tipset Gas Reservations
author: "Michael Seiler (@snissn)"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1210
status: Draft
type: Technical
category: Core
created: 2025-11-17
spec-sections:
  - section-systems.filecoin_vm.gas_fee
  - section-systems.filecoin_vm.runtime.receipts
  - section-systems.filecoin_vm.interpreter.gas-payments
  - section-systems.filecoin_vm.interpreter.duplicate-messages
---

## Simple Summary

This FIP introduces tipset-wide gas reservations for explicit messages. Before executing the canonical explicit messages in a tipset, nodes reserve enough funds per sender to cover the maximum possible gas cost of that sender’s messages. While the reservation session is open, all non-gas value transfers are enforced against the sender’s free balance (on-chain balance minus remaining reserved gas), preventing intra-tipset “self-drain” patterns from making later messages underfunded. For messages that execute, receipts and gas accounting remain unchanged; the difference is how fund availability is enforced during the tipset.

To make reservations well-defined in multi-block tipsets, this FIP also introduces **Strict Sender Partitioning** during tipset message selection: if a sender’s messages are accepted from a higher-precedence block in the tipset, messages from that sender in lower-precedence blocks are ignored and produce no receipts.

## Abstract

This FIP introduces tipset-scope gas reservations as a consensus rule for Filecoin to eliminate miner exposure to underfunded gas charges within a single tipset. For each tipset, nodes derive the canonical explicit message set `M(T)` (including strict sender partitioning) and construct a per-sender reservation plan equal to the sum, over `M(T)`, of each message’s `gas_limit * gas_fee_cap`. The execution engine maintains an internal reservation session ledger keyed by actor identifier; when a session is open, each sender’s free balance is defined as on-chain balance minus the remaining reserved amount recorded in this ledger.

For messages that execute, gas metering and `GasOutputs` are computed exactly as today. Preflight checks assert that reserved funds cover each message’s maximum gas cost, and all non-gas value transfers are enforced against free balance rather than raw balance, so a sender cannot move away funds needed to pay for reserved gas. Settlement net-charges the sender only for actual consumption (base-fee burn, overestimation burn, and miner tip) while releasing the full reserved amount, realizing refunds by increasing free balance instead of issuing explicit refund transfers. The reservation ledger is tipset-local and requires no new on-chain actors or state migrations. The new rules activate at network version 28 via a chain upgrade.

## Change Motivation

Under the current protocol, tipset execution can expose block producers to miner-charged gas penalties when a sender drains their balance within the same tipset. A common pattern is an intra-tipset “self-drain” sequence: a first message (M1) at nonce X executes contract logic that transfers away most of the sender’s funds, and a second message (M2) at nonce X+1 declares a large gas limit. At block construction time, the packer evaluates M2’s affordability based on the sender’s balance before M1 runs and admits it into the block. At execution time, however, M1 has already moved the funds, so M2 no longer has enough balance; today this shortfall can fall back to a miner penalty, even though the sender initiated both messages.

Existing mitigations rely on local heuristics during block construction, such as tracking declared message value and simple balance checks for individual messages. These techniques are inherently limited: they cannot fully account for arbitrary contract-level value movements, reordering across blocks in the same tipset, or the interaction of many messages from the same sender. As deferred execution and complex contracts become more common, the window in which a sender can pre-commit gas-heavy messages and then drain their account within the same tipset widens, increasing the risk that honest miners are forced to subsidize execution.

This FIP addresses the problem at the protocol level by reserving gas across the entire tipset up-front and enforcing affordability inside the execution engine itself. Rather than introducing a new on-chain actor or escrow mechanism, the engine maintains an internal, tipset-local reservation ledger that locks each sender’s maximum possible gas spend (`Σ(gas_limit * gas_fee_cap)`) before any message executes. Free balance during the tipset is defined as on-chain balance minus the remaining reservation, so any attempt to transfer funds needed to cover reserved gas will fail deterministically across implementations. For messages that are selected for execution, this design preserves existing receipts and gas outputs, avoids state migrations, and provides a consensus-level guarantee that miners are not exposed to underfunded gas charges created by intra-tipset self-drain.

This issue exists today, but becomes materially more important with delegated execution patterns such as EIP-7702 (see [FIP-0111](./fip-0111.md)). EIP-7702 increases the practical likelihood that a single sender can execute arbitrary logic (including value-moving behavior) and then submit additional gas-heavy messages in the same tipset. As part of evaluating EIP-7702 for the FEVM, this FIP was identified as a necessary hardening measure; while it is a general network improvement, it should be treated as a prerequisite for enabling EIP-7702 on any network.

## Specification

### Overview (non-normative)

At a high level, tipset execution changes as follows:

1. Determine the canonical explicit message list `M(T)` for the tipset:
   - Keep legacy CID deduplication across blocks.
   - Additionally apply **Strict Sender Partitioning**: once any message from a sender is taken from a higher-precedence block, that sender’s messages in lower-precedence blocks are ignored (not executed and producing no receipt).
2. Build a per-sender reservation plan `plan_T` from `M(T)` by reserving, for each sender, the sum of `GasLimit * GasFeeCap` over that sender’s messages.
3. Before executing `M(T)`, open a single reservation session seeded with `plan_T`. While the session is open, each sender has a **free balance** equal to `balance − remaining_reserved`.
4. Execute messages in `M(T)` in the same order as legacy, except:
   - All non-gas value transfers must fit within free balance.
   - At message end, the sender is charged only for actual gas consumption and the reservation is released (so the refund is realized by increasing free balance rather than by a dedicated refund transfer).
5. After all explicit messages complete, end the session; the tipset is only valid if all reservations have been fully released.

Base fee computation is unchanged.

### Tipset-wide reservation plan

This section defines (1) the canonical explicit message set `M(T)` for a tipset and (2) the reservation plan `plan_T` derived from that set.

#### Canonical explicit message set `M(T)`

For each tipset `T` at height `h`, let `M(T)` denote the canonical ordered list of explicit messages used for explicit message execution, receipt generation, and reservation planning at that height.

`M(T)` is derived from the blocks in `T` by applying:

- legacy CID deduplication across blocks; and
- **Strict Sender Partitioning** to prevent conflicting reservations (at most one block contributes messages for a given sender).

Let `B_1, B_2, ..., B_n` be the blocks in `T`, ordered by ticket precedence (where `B_1` has the highest precedence/lowest ticket).
Let `S_seen` be the set of senders whose messages have been accepted in previous blocks, initially empty.
Let `CID_seen` be the set of message CIDs seen so far, initially empty.

Conforming implementations MUST construct `M(T)` according to the following pseudocode (or any equivalent procedure):

```text
M := []
CID_seen := ∅
S_seen := ∅

for each block B_i in T ordered by ticket precedence:
    S_i := ∅
    for each explicit message m in B_i in legacy in-block order:
        if cid(m) ∈ CID_seen:
            continue  # legacy CID deduplication; no receipt
        CID_seen := CID_seen ∪ {cid(m)}
        if from(m) ∈ S_seen:
            continue  # strict sender partitioning; no receipt
        M := M ++ [m]
        S_i := S_i ∪ {from(m)}
    S_seen := S_seen ∪ S_i

return M
```

Strict Sender Partitioning is block-scoped: `S_seen` is updated only after an entire block is processed, so all messages from a sender within the first accepted block for that sender are included as normal.

System / implicit messages (for example block rewards and cron) are not members of `M(T)`.

After `M(T)` is constructed, explicit messages are executed in the order they appear in `M(T)` and receipts are produced for those messages in the same order; this FIP does not otherwise change message ordering semantics.

#### Reservation plan `plan_T`

For each message `m ∈ M(T)` with sender address `from(m)`, gas limit `GasLimit(m)`, and gas fee cap `GasFeeCap(m)`, define its maximum gas cost

`gas_cost(m) = GasLimit(m) * GasFeeCap(m)`

using the same arithmetic and units as the existing gas accounting rules. Let `S(T)` be the set of senders that appear in `M(T)`. The tipset reservation plan for `T` is a mapping

`plan_T : S(T) → TokenAmount`

given by

`plan_T[s] = Σ_{m ∈ M(T), from(m) = s} gas_cost(m).`

Each message contributes to `plan_T` exactly once. All conforming implementations MUST derive an equivalent plan from the same canonical message set `M(T)` and gas cost definition.

Implementations MUST bound the size of `plan_T` to mitigate denial-of-service risk. In particular:

- The number of distinct senders in `plan_T` MUST NOT exceed a network parameter `MAX_RESERVATION_SENDERS` (default: 65,536).
- The serialized size of `plan_T`, when encoded for handoff to the execution engine, MUST NOT exceed a network parameter `MAX_RESERVATION_PLAN_BYTES` (default: 8 MiB).

If either bound would be exceeded, a conforming implementation MUST treat this as a reservation plan failure (see “Activation and consensus rules”).

### Base fee computation (unchanged)

This FIP does not change base fee computation. Base fee adjustment for a tipset continues to be computed from the sum of `GasLimit` for all unique explicit messages in the tipset (deduplicated by CID across blocks), regardless of whether a message is later ignored for execution due to Strict Sender Partitioning.

### Reservation session API and lifecycle

The Filecoin state transition at a tipset with non-empty `plan_T` operates in two phases around message execution:

1. **Begin reservation session**: before executing any explicit message in `M(T)`, the node attempts to open exactly one reservation session for the tipset, parameterized by `plan_T`.
2. **End reservation session**: after processing all explicit messages in `M(T)`, and before executing any implicit messages for `T`, the node closes the reservation session.

The reservation session is maintained inside the execution engine as an ephemeral ledger:

- For each sender `s` (resolved to `ActorID`) the engine stores a non-negative reserved amount `reserved[s]`.
- A boolean flag `session_open` indicates whether a session is active.

#### Begin

- If `plan_T` is empty, Begin MUST be a no-op: `session_open` remains false and the engine MUST NOT enter reservation mode for this tipset.
- If `plan_T` is non-empty and `session_open` is already true, Begin MUST fail with a single-session violation.
- For each entry `(address, amount)` in `plan_T`, the engine resolves the address to an `ActorID` using the current state tree. Resolution MUST succeed for all entries; failure to resolve any sender is a reservation failure.
- For each resolved actor `a`, with on-chain balance `balance[a]` at the start of the tipset, the engine MUST check:

  `0 ≤ amount ≤ balance[a].`

  If this condition fails for any actor, Begin MUST fail with an insufficient-funds reservation failure.
- When all entries pass these checks, the engine sets:

  - `reserved[a] = amount` for each resolved sender `a` in `plan_T`;
  - `session_open = true`.

  Actors not present in `plan_T` are treated as having `reserved[a] = 0`.

#### In-session invariants

The following invariants MUST hold whenever `session_open` is true:

- For every actor `a`, `reserved[a] ≥ 0`.
- For every sender `a` in `plan_T`, `reserved[a] ≤ balance[a]`.

#### End

- If `session_open` is false, End MUST fail with a session-closed violation.
- If `session_open` is true, the engine MUST verify that all reservations have been released (i.e., there is no remaining `reserved[a] > 0`). Any non-zero entry is a reservation remainder failure.
- On success, the engine clears all `reserved` entries and sets `session_open = false`.

A conforming implementation MUST NOT open more than one reservation session per tipset, and MUST ensure that any successful Begin with a non-empty `plan_T` is paired with exactly one End before processing implicit messages for that tipset.

### Worked example (non-normative)

Assume a tipset `T` contains two blocks `B_1` (higher precedence) and `B_2` (lower precedence) with the following explicit messages (in in-block execution order), and assume all message CIDs are unique:

- `B_1`: `m1` from `A`, `m2` from `B`
- `B_2`: `m3` from `A`, `m4` from `C`

Under **Strict Sender Partitioning**, `m3` is ignored because sender `A` already contributed messages from the higher-precedence block `B_1`. Therefore `M(T) = [m1, m2, m4]`; `m3` produces no receipt and does not contribute to reservations.

The reservation plan `plan_T` is then computed by summing `gas_cost(m) = GasLimit(m) * GasFeeCap(m)` per sender over the messages in `M(T)`. Begin succeeds only if each sender has sufficient on-chain balance to cover its plan entry, and initializes `reserved[s] = plan_T[s]`.

While the session is open, a sender’s **free balance** is `free[s] = balance[s] − reserved[s]`. This means a sender can spend (transfer) at most its free balance on non-gas value transfers during the tipset, even though its raw on-chain balance may be higher. When a message finishes, the sender is charged only for actual gas consumption and the reservation is released; the refund effect is realized by an increase in free balance when `reserved[s]` is decremented.

For example, if `plan_T[A] = gas_cost(m1) = 30` and `balance[A] = 35` at Begin, then `reserved[A] = 30` and `free[A] = 5`. Any attempt during `m1` execution to transfer more than `5` units of value from `A` (other than gas settlement) fails deterministically. If at settlement `consumption = 12` and `refund = 18` (so `consumption + refund = gas_cost(m1)`), then after settlement `balance[A]` decreases by `12` while `reserved[A]` decreases by `30`, causing `free[A]` to increase by `18` (the refund) without any explicit refund transfer.

### Reservation mode and legacy mode

When `session_open` is true, the engine operates in **reservation mode** for all explicit messages in `M(T)`. When `session_open` is false, the engine operates in **legacy mode**, preserving existing preflight, transfer, and settlement behavior.

- In reservation mode, the rules in the following subsections apply.
- In legacy mode, the rules prior to this FIP continue to apply; `reserved[a]` is treated as zero for all actors, and Begin/End are not invoked.

Reservation mode applies only to explicit messages in `M(T)`. Implicit messages (including block rewards and cron) do not participate in the reservation plan and execute in legacy mode after End has succeeded.

### Preflight behaviour and coverage

Preflight does not change on-chain balances. It checks that each message’s reservation coverage is consistent with `plan_T` and, if a message fails prevalidation (and therefore will not execute), releases that message’s reservation immediately.

For each explicit message `m` from sender `s` processed while `session_open` is true, preflight MUST:

1. Compute

   `gas_cost(m)` (as defined above)

   using the same arithmetic and units as existing gas accounting, defined over unbounded integers. If an implementation cannot represent this value (for example due to numeric overflow), it MUST treat this as an implementation error, not as an alternative consensus outcome.
2. Check that `reserved[s] ≥ gas_cost(m)`. Violation of this condition indicates that the host has constructed an inconsistent `plan_T`; this MUST be treated as an implementation error.
3. MUST NOT deduct `gas_cost(m)` from the sender’s on-chain balance as part of preflight.
4. If the message fails prevalidation (for example, due to bad syntax, invalid nonce, or other legacy preflight failures) and is classified as a prevalidation failure, then before returning, the engine MUST decrement

   `reserved[s] := reserved[s] − gas_cost(m),`

   which is well-defined because step 2 ensures `reserved[s] ≥ gas_cost(m)`. The message’s gas accounting (including any miner penalty) remains as specified in the legacy rules. After this decrement, the engine MUST NOT make any additional changes to `reserved[]` for this message.

If preflight succeeds and the message proceeds to execution, `reserved[s]` is left unchanged until settlement in `finish_message` (see below).

### Transfer enforcement via free balance

While `session_open` is true, the engine MUST enforce all value transfers against a sender’s **free balance** rather than its raw on-chain balance.

For any value-moving operation that transfers an amount `value` from actor `a` to some recipient, other than gas settlement itself:

- Let `balance[a]` denote `a`’s current on-chain balance.
- Let `reserved[a]` denote the current reservation entry for `a` (0 if not present).
- Define the free balance

  `free[a] = balance[a] − reserved[a].`

The engine MUST require:

- `free[a] ≥ 0` at all times while `session_open` is true; and
- `value ≤ free[a]` as a precondition for the transfer.

If `value > free[a]`, the transfer MUST fail with the existing insufficient-funds semantics for that operation, and no balances or `reserved[]` entries are updated as a result of that transfer.

This affordability rule MUST be applied uniformly to all value-moving paths during message execution, including but not limited to:

- top-level message value transfers,
- actor-initiated transfers,
- sub-calls that send value,
- actor creation that includes an initial balance,
- SELFDESTRUCT-like flows that send remaining balance to a beneficiary,
- implicit sends performed by built-in actors as part of their logic.

Gas settlement at the end of a message (burning base fee, overestimation burn, and crediting miner tips) is handled separately and is exempt from the free-balance affordability check, as described below.

### Settlement behaviour and invariants

Note (non-normative): Under legacy rules, the sender effectively front-loads a maximum gas charge and later receives a refund for unused gas. In reservation mode, `reserved[s]` plays the role of that front-loaded amount (by reducing free balance during execution), and the refund is realized when `reserved[s]` is decremented at settlement.

For each explicit message `m` from sender `s` that passes preflight and runs to completion (including messages that exit with failure codes), the engine computes `GasOutputs` exactly as in the legacy rules. In particular:

- `gas_cost(m) = base_fee_burn + over_estimation_burn + refund + miner_tip`,

with all quantities non-negative and measured in attoFIL.

In reservation mode, settlement for `m` MUST satisfy the following steps and invariants:

1. Define

   `consumption = base_fee_burn + over_estimation_burn + miner_tip.`

2. Deduct `consumption` from the sender’s on-chain balance:

   `balance[s] := balance[s] − consumption.`

   This MUST be implemented so that the sender’s net balance change over the message matches the legacy behavior.
3. Credit the existing system accounts as in the legacy rules:

   - increase the burn account balance by `base_fee_burn + over_estimation_burn`;
   - increase the appropriate reward account balance by `miner_tip`.

4. Do NOT transfer `refund` back to the sender as an explicit balance credit.
5. Decrement the reservation ledger by the full maximum gas cost:

   `reserved[s] := reserved[s] − gas_cost(m),`

   which is well-defined because preflight has ensured `reserved[s] ≥ gas_cost(m)`. If the result is zero, the entry for `s` MAY be removed from the ledger.

These rules imply the key invariants:

- For every message `m` in reservation mode, `consumption + refund = gas_cost(m)`.
- Let `(balance_pre, reserved_pre)` be the sender’s on-chain balance and reservation entry immediately before settlement for `m`, and `(balance_post, reserved_post)` be the values immediately after settlement. Then:

  - `balance_post = balance_pre − consumption`
  - `reserved_post = reserved_pre − gas_cost(m)`

  so the sender’s free balance `free = balance − reserved` increases by exactly `refund` at settlement:

  `free_post − free_pre = gas_cost(m) − consumption = refund.`

  This matches the legacy intuition where the sender is net-charged `consumption` and the unused portion is returned as a refund; in reservation mode the refund is realized entirely by reducing `reserved[s]`.
- Each `reserved[s]` remains non-negative throughout, and is reduced by `gas_cost(m)` exactly once per message `m` from `s`.

For messages that terminate during preflight as prevalidation failures, settlement follows the legacy rules for burn and miner penalties, but MUST still apply:

- `reserved[s] := reserved[s] − gas_cost(m),`

with no changes to the sender’s on-chain balance. This ensures that, for a correctly constructed `plan_T`, all reservations are fully released by the end of the tipset.

### Activation and consensus rules

This FIP introduces a new consensus rule that becomes mandatory from network version 28 onward.

- **Pre-activation (network versions < 28):**

  - Clients MAY implement reservation mode as a best-effort or testing feature, optionally gated by local configuration.
  - Any reservation failures (including Begin/End failures, overflow, or invariant violations) MUST NOT cause a tipset to be considered invalid under consensus. Pre-activation, the canonical state transition for block validity remains the legacy semantics without reservations.

- **Post-activation (network versions ≥ 28):**

  - For any tipset at or after the configured upgrade epoch for network version 28, the state transition MUST behave as if a reservation session were applied to explicit messages in `M(T)` according to this specification.
  - A tipset is valid only if there exists a reservation plan `plan_T` and an execution in reservation mode that:

    - successfully calls Begin with `plan_T` (no sender-resolution failures, no insufficient-funds, no size-limit violations, no arithmetic overflow), and
    - processes all explicit messages in `M(T)` while maintaining the invariants above, and
    - successfully calls End with all reservations fully released (no `reserved[a] > 0`).

  - If a node cannot start, maintain, or end a reservation session for a candidate tipset without violating these invariants, that tipset MUST NOT be considered valid.

Implementations remain free to expose different operational modes (for example, non-strict or strict pre-activation reservation checks), but from network version 28 onward, all conforming implementations MUST converge on the reservation mode semantics described here for consensus validity.

## Design Rationale

### Strict Sender Partitioning

The definition of `M(T)` is updated to strictly partition senders by block precedence: if a sender has messages executed in a higher-precedence block, their messages in any lower-precedence block are ignored. This is necessary to preserve tipset validity properties.

Without this rule, a sender could broadcast two sets of messages: set A (affordable) included in Block A, and set B (affordable) included in Block B. If both blocks are included in a tipset, the aggregate reservation `plan_T` would sum the costs of A and B. If this sum exceeds the sender's balance, the tipset would fail the reservation check and be invalid. This creates an asymmetric advantage for an attacker: they can invalidate a tipset (and deny rewards to all miners in it) by broadcasting valid individual blocks that conflict only when aggregated.

By enforcing strict partitioning, the protocol ensures that `plan_T` is composed of non-overlapping sets of messages that have already passed individual block-level validity checks (at least for the highest-precedence block). The reservation for a sender in the tipset becomes identical to their reservation in the single block where they are accepted, preventing the aggregate-overflow exploit.

### Reserving `gas_limit * gas_fee_cap`

The reservation amount for each message is defined as `gas_limit * gas_fee_cap`, matching the existing definition of the maximum possible gas charge for that message. This choice ensures that:

- The reservation ledger uses the same `gas_cost` already implicit in the gas accounting rules, rather than introducing a new notion of "reserved price".
- The existing invariant `base_fee_burn + over_estimation_burn + refund + miner_tip = gas_cost` continues to hold exactly, with `gas_cost` unchanged.
- For messages in `M(T)` that execute, receipts and `GasOutputs` remain identical to legacy behavior; the only difference is the internal path by which funds are prevented from being spent elsewhere during the tipset.

An alternative would have been to reserve only the "effective" gas price (for example, `gas_limit * min(gas_fee_cap, base_fee + premium)`). This would complicate reasoning about refunds, tie reservations directly to fee dynamics, and risk breaking the existing invariants when base fees or premiums change. By reserving `gas_limit * gas_fee_cap` instead, the reservation ledger can be reduced by exactly `gas_cost` per message while net-charging only the actual consumption, preserving existing accounting while providing stronger safety guarantees.

### Sender- and tipset-scoped reservations

Reservations are keyed by sender and tipset, not by individual message. The plan aggregates all explicit messages from the same sender in a tipset into a single per-sender amount `plan_T[s] = Σ gas_cost(m)`. This design:

- Ensures that affordability is independent of the intra-tipset execution order: once `plan_T` is established, any scheduling of messages from the same sender within the tipset is safe, because all messages draw from the same reserved total.
- Avoids the need to track per-message reservations or to expose message identifiers to the reservation API, simplifying the engine and host interface.
- Naturally handles deduplication by CID across blocks: a message that appears multiple times still contributes only once to `plan_T`, matching the canonical execution set.
- Keeps the ledger small and bounded by the number of distinct senders rather than the number of messages, which is important for both DoS resistance and FFI surfaces in existing implementations.

Per-message reservations were considered but rejected because they would not materially improve safety (the total reserved per sender must already cover all messages) while complicating the interface and increasing per-message bookkeeping.

### Reservation plan bounds

`MAX_RESERVATION_SENDERS` and `MAX_RESERVATION_PLAN_BYTES` bound worst-case resource usage for plan construction, FFI handoff, plan decoding, and per-tipset reservation bookkeeping. Without explicit bounds, an attacker could attempt to create tipsets with extremely large sender sets or oversized plans, turning reservation planning into a denial-of-service vector.

The default values (65,536 senders; 8 MiB encoded plan) are intended to be conservatively high—well above expected sender diversity in normal tipsets—while still keeping per-tipset memory and decoding costs bounded. These SHOULD be treated as initial values and tuned via benchmarking and mainnet observations.

### Engine-local reservation ledger with no new on-chain actor

The reservation ledger is kept entirely inside the execution engine and exists only for the duration of a tipset. No new on-chain actor or persistent state is introduced. This design was chosen to:

- Avoid any state migration or actor registry changes: the Burn, Reward, and other built-in actors continue to function exactly as today.
- Keep the engine network-version agnostic: from the engine’s perspective, reservation mode is an internal option that can be enabled or disabled by the host without changing on-chain code.
- Ensure that all value-moving paths are covered: because the ledger lives in the engine that executes all calls and implicit sends, every transfer can be checked against free balance, including those triggered deep in call stacks or by built-in actors.
- Minimize surface area for consensus divergence: all conforming clients need only implement the same Begin/End semantics and free-balance checks; the ledger itself does not interact with other on-chain actors.

An alternative design based on an on-chain escrow actor was rejected because it would require new actor code, migration of existing balances or gas flows, and more complex interactions with existing reward and burn logic. It would also expose the reservation ledger to user-visible manipulation, increasing the attack surface. Keeping reservations engine-local achieves the desired safety properties while keeping the ledger invisible and ephemeral.

### Settlement via net charge and reservation release

The settlement rules net-charge the sender only for actual consumption (`base_fee_burn + over_estimation_burn + miner_tip`) and realize refunds by decreasing `reserved[s]` by the full `gas_cost`. This approach:

- Preserves the external behavior of gas accounting: receipts, `GasOutputs`, and miner/burn flows are unchanged.
- Realizes refunds by increasing free balance, not by issuing new balance credits, which keeps the on-chain balance evolution identical to the legacy path while preventing misuse of reserved funds mid-tipset.
- Guarantees the invariant `consumption + refund = gas_cost` and enforces that reservations return to zero by session end, because each message’s full `gas_cost` is released exactly once.

If the protocol instead refunded the sender by explicitly crediting `refund` and reduced `reserved[s]` only by the consumed portion, it would become harder to maintain the simple invariants on `reserved[s]` and free balance, and to argue receipt parity. The chosen design keeps the ledger and invariants straightforward.

### Activation and rollout strategy

Making reservations a consensus rule only from network version 28 provides a clear activation point while allowing a smooth rollout:

- Before activation, nodes can opt in to reservation mode under feature flags or configuration without affecting consensus validity, enabling testing against mainnet traffic and performance tuning.
- At activation, the rule "every valid tipset must admit a successful reservation session with zero remainder" becomes part of consensus, eliminating miner exposure to underfunded gas while ensuring all conforming implementations agree on block validity.
- Because the ledger is engine-local and gas accounting for executed messages is unchanged, older nodes that have not implemented this FIP will simply be unable to validate post-activation tipsets and will clearly fail, rather than silently disagree on balances or rewards.

This staged rollout balances the need for safety (eliminating miner penalties from intra-tipset self-drain) with the operational need to test and tune implementations before the consensus rule becomes mandatory.

### Alternatives considered

Several alternative designs were considered and rejected:

- **On-chain escrow actor:** A dedicated actor holding reserved funds could have enforced affordability by moving balances on-chain. This was rejected due to the need for state migrations, actor registry changes, more complex reward/burn plumbing, and increased attack surface. Engine-local reservations achieve the same protection without changing the on-chain actor set.
- **Per-message reservations:** Tracking reservations per message would require exposing message identifiers through the reservation API and maintaining a larger ledger. Because safety is determined by the total reserved per sender, per-message granularity adds complexity without improving guarantees and is unnecessary once the canonical message set is fixed.
- **Host-side enforcement only:** Relying solely on block-construction heuristics or host-side balance tracking cannot fully account for contract-level value transfers, complex call graphs, or cross-block reordering within a tipset. Such approaches are inherently advisory and cannot provide consensus guarantees. Moving enforcement into the execution engine, which sees all value movements, is necessary to guarantee that reserved gas cannot be spent elsewhere.
- **Changing gas pricing or receipt formats:** Designs that altered the definition of `gas_cost`, changed how refunds are represented in receipts, or modified miner reward calculations were rejected in order to minimize consensus risk and to keep existing tools and analytics compatible. By preserving gas pricing and receipts exactly, this FIP isolates its changes to intra-tipset fund availability and tipset validity rules.

Overall, the chosen design adds a minimal, engine-managed reservation layer that preserves existing gas economics and user-facing behavior while closing the specific class of intra-tipset self-drain exploits that expose miners to unintended penalties.

## Backwards Compatibility

This FIP is a consensus-breaking change that activates via a network upgrade (network version 28).

- **No state migration or new actors.** The reservation ledger is engine-local and tipset-local. No new on-chain actor is introduced and no state migration is required.
- **Canonical message selection changes.** Strict Sender Partitioning changes the canonical explicit message set `M(T)`. In particular, some messages included in lower-precedence blocks may be ignored and therefore produce no receipts and no gas charges. Tooling MUST correlate receipts to the canonical tipset message set rather than assuming that “in a block” implies “executed in the tipset”.
- **Pre-activation behaviour (network versions < 28).** Before activation, the canonical state transition remains the legacy semantics without reservations. Implementations MAY expose reservation mode for testing/telemetry, but any Begin/End failure, invariant violation, or overflow MUST NOT affect consensus validity.
- **Post-activation requirements.** After activation, nodes MUST run a reservation-aware implementation. Nodes that do not upgrade will be unable to validate post-activation tipsets and will diverge from the canonical chain.

## Test Cases

Implementations of this FIP MUST be accompanied by targeted tests and fuzzing that validate reservation behaviour, gas accounting invariants, and activation semantics. The concrete test suites will differ across clients, but should cover at least the following categories.

- **Engine unit tests (reservation session and preflight).**
  - Session lifecycle: opening and closing a single session; empty-plan no-op semantics; enforcing single-session invariants; rejecting plans that exceed affordability, sender-count (`MAX_RESERVATION_SENDERS`), or size (`MAX_RESERVATION_PLAN_BYTES`) limits; rejecting unknown senders or resolution failures.
  - Preflight under reservations: computing `gas_cost = gas_fee_cap * gas_limit` with checked arithmetic; asserting coverage (`reserved[sender] ≥ gas_cost`) without pre-deducting funds; on prevalidation failures (invalid sender, nonce, or inclusion gas limit), decrementing the reservation by `gas_cost` so that the ledger can end at zero.
- **Engine unit tests (transfer enforcement and settlement).**
  - Transfer enforcement: ensuring all value-moving operations (including message value sends, actor creation, EVM CALL/DELEGATECALL, SELFDESTRUCT, and built-in implicit sends) route through a transfer primitive that enforces affordability against free balance `free = balance − reserved_remaining`, and reject `value > free` with an appropriate `InsufficientFunds` error.
  - Settlement invariants: in reservation mode, net-charging the sender only for `consumption = base_fee_burn + over_estimation_burn + miner_tip`, preserving the invariant `base_fee_burn + over_estimation_burn + refund + miner_tip = gas_cost`, never depositing refunds explicitly, and ensuring that reservation decrements by exactly `gas_cost` per message lead to a zero remainder at End.
- **Integration tests (engine + host, intra-tipset scenarios).**
  - Intra-tipset self-drain: a tipset where a first message drains a sender’s balance via contract logic and a second message with the next nonce declares a large gas limit. Under reservations, the second message must either execute with gas fully covered from the reserved amount (no miner penalty) or be rejected as invalid at reservation time; baseline behaviour without reservations can be reproduced as a regression check.
  - Interleaved transfers: scenarios with multiple messages and nested calls from the same sender that perform value transfers while gas is reserved, confirming that transfers cannot dip into reserved funds and that later messages still see sufficient free balance when expected.
  - Multi-block tipsets with duplicates: tipsets where the same message appears in multiple blocks, verifying that the plan dedupes by CID, that messages are reserved exactly once, and that receipts and gas rewards remain consistent with the canonical execution set.
  - Prevalidation failures: messages that fail during preflight (e.g., bad nonce or insufficient inclusion gas), confirming that miner penalties are accounted as today, no sender funds are moved, reservations are decremented by `gas_cost`, and the session can still end with zero remainder.
- **Consensus-layer tests (plan build, FFI, and activation).**
  - Plan construction and deduplication: tests that build the reservation plan from the canonical explicit message set across a tipset, ensuring deduplication by CID across blocks, correct aggregation of `Σ(gas_limit * gas_fee_cap)` per sender, and empty-plan skip semantics (no Begin/End).
  - FFI encoding/decoding and error mapping: tests that exercise CBOR encoding of the plan as `[(Address, TokenAmount)]`, round-trip decoding inside the engine, and mapping of raw FFI status codes into host-visible error classes (including optional engine-provided error messages) without changing the consensus-level taxonomy.
  - Activation and gating: tests that cover pre- and post-activation behaviour, including feature-flag combinations (best-effort vs strict modes pre-activation), and that exercise the main reservation failure classes (engine does not support reservations, insufficient funds at Begin, plan-too-large failures, and node-error classes such as session misuse, overflow, and reservation invariant violations).
  - Mempool pre-pack (where implemented): tests that validate reservation-aware pre-pack heuristics, including pruning of chains that would over-reserve a sender’s balance and accumulation of `Σ(gas_limit * gas_fee_cap)` across chains for the same sender.
- **Property and fuzz tests.**
  - Randomized multi-message tipsets with varying balances, gas limits, fee caps, and duplicate messages, asserting that:
    - Only gas charging consumes reserved amounts; arbitrary value transfers may reduce free balance but cannot reduce `reserved_remaining`.
    - For every message, `consumption + refund == gas_cost` and all gas components are non-negative.
    - Free balance never becomes negative; aggregate free balance across all actors equals the initial total minus the sum of net gas consumption.
    - Reservations reach zero at End; any non-zero remainder produces a reservation remainder failure.
  - Gas accounting property tests (for example, quickcheck-based tests of `GasOutputs` and settlement) that continue to hold under reservation mode as they do under legacy mode.

The exact filenames and test harnesses will differ across implementations (e.g., Lotus, ref-fvm, filecoin-ffi, and other clients), but implementers SHOULD construct suites that cover the same behavioural properties. In particular, engines and hosts SHOULD include tests that exercise both pre-activation (legacy and best-effort reservation) configurations and post-activation consensus behaviour to ensure correct activation, gating, and error handling.

## Security Considerations

This FIP is motivated by a security problem: under current semantics, miners can be exposed to gas penalties from underfunded messages created by intra-tipset “self-drain” patterns. Tipset-wide reservations eliminate this exposure when correctly implemented, but they also introduce new invariants and error classes that must be handled carefully.

- **Partial Orphan Spam.** Strict Sender Partitioning introduces a specific spam vector: a malicious sender can broadcast different sets of valid messages to different miners. If Block A and Block B are both mined and included in a tipset, and the sender appears in both, the messages in the lower-precedence block (say Block B) are ignored. The miner of Block B incurs the cost of propagating and storing these bytes but receives no gas reward for them. This "partial orphan" risk is an accepted trade-off to prevent the critical "tipset invalidation" attack described above. It is similar in nature to existing risks where duplicate messages (same CID) are included in multiple blocks, but extends to excluding distinct messages from the same sender.
- **Miner exposure to underfunded gas.** By reserving `Σ(gas_limit * gas_fee_cap)` per sender before any message executes, and enforcing all value transfers against free balance `balance − reserved_remaining`, the protocol ensures that senders cannot move away funds required to pay for gas. A message either executes with its gas fully funded from the reserved amount or the tipset fails reservation checks and is considered invalid (post-activation), removing a class of exploits where miners are forced to subsidize underfunded gas.
- **Complete coverage of value-moving paths.** Security depends on the guarantee that every value-moving operation is checked against free balance. Implementations MUST ensure that all paths that move FIL (including message value transfers, actor creation sends, FEVM/ EVM CALL and DELEGATECALL, SELFDESTRUCT, and built-in implicit sends) route through the reservation-aware transfer primitive. Any missing path would allow reserved funds to be spent, potentially re-introducing miner exposure or breaking reservation invariants. Tests should explicitly cover SELFDESTRUCT and implicit sends to guard against regressions.
- **Reservation invariants and node errors.** The safety of this design relies on strict invariants:
  - `gas_cost = gas_fee_cap * gas_limit` is defined over unbounded integers; conforming implementations MUST compute it without overflow for all messages admitted by the protocol.
  - Preflight in reservation mode MUST enforce `reserved[sender] ≥ gas_cost`; any violation indicates host/engine inconsistency (a reservation invariant failure).
  - `end_reservation_session` MUST observe a zero remainder; any non-zero reservation at End is a reservation remainder failure.
  Implementations MUST treat overflow and reservation invariant failures as node errors (implementation bugs or misconfiguration), not as consensus-level exceptions. A node that encounters such conditions should stop following the chain and alert operators rather than attempting to continue on an alternative fork, to avoid consensus splits based on buggy behaviour.
- **Risks from partial or incorrect implementations.** Incomplete implementations—such as failing to decrement reservations on prevalidation failure, neglecting to clear reservations at End, or mishandling “not implemented” status codes—can lead to stuck reservation sessions, inconsistent free-balance checks, or silent fallback to legacy semantics when reservations should be enforced. These bugs can undermine the protection this FIP is intended to provide and, in the worst case, cause nodes to accept or reject tipsets differently. Implementers SHOULD rely on the test categories described above (especially integration and fuzz tests) to detect such partial behaviour.
- **Denial-of-service and performance considerations.** Reservation plans and the associated ledger create a new surface for resource exhaustion. To mitigate DoS risks:
  - Hosts and engines MUST enforce reasonable bounds on plan size, including a maximum number of distinct senders (`MAX_RESERVATION_SENDERS`) and a maximum encoded plan size (`MAX_RESERVATION_PLAN_BYTES`); exceeding these bounds MUST produce a dedicated “plan too large” reservation failure.
  - Plan aggregation in the host SHOULD remain O(n) in the number of explicit messages, and engine checks SHOULD remain O(1) per message, so that Stage-1 reservation overhead remains a small fraction of total tipset application time.
  - FFI surfaces should avoid unbounded allocations when decoding plans or exporting telemetry, and implementations SHOULD monitor reservation-related metrics to detect abnormal workloads.
- **Activation and configuration risks.** Because reservations become consensus rules only from network version 28 onward, misconfigured pre-activation nodes that enable “strict” reservation enforcement can fork away from the canonical chain by rejecting tipsets that other nodes accept. Operators SHOULD treat strict pre-activation modes as testing tools and ensure production nodes match the network’s agreed activation and gating policies. Post-activation, nodes MUST treat “not implemented” reservation responses as node errors, not as consensus signals, to avoid silently diverging back to legacy behaviour.

Overall, this FIP strengthens miner and network security by preventing a class of intra-tipset gas underfunding exploits, while relying on well-specified invariants (coverage `reserved[sender] ≥ gas_cost`, zero remainder at session end, non-negative reservations) and resource limits (`MAX_RESERVATION_SENDERS`, `MAX_RESERVATION_PLAN_BYTES`) to bound the new surfaces it introduces. Careful implementation, testing, and error handling across engines and hosts is essential to avoid new consensus divergence risks.

## Incentive Considerations

- **Reduced miner exposure to underfunded gas.** Tipset-wide reservations prevent senders from making later messages underfunded via intra-tipset balance changes, reducing miner exposure to edge cases where included messages become uneconomical or unpaid.
- **Ignored-message economics.** Under Strict Sender Partitioning, excluded messages do not execute and do not generate gas revenue for the miner that included them. This shifts the cost of propagating/storing these bytes onto the block producer (similar in nature to existing duplicate-message inclusion risk).
- **Mempool and packing implications.** Implementations will likely want to adjust packing heuristics to reduce inclusion of messages that are likely to be ignored and to avoid constructing blocks/tipsets that exceed reservation plan bounds.
- **Base fee and congestion.** This FIP does not change base fee computation. Because base fee adjustment is computed from unique message CIDs across blocks, Strict Sender Partitioning may cause some messages to be ignored for execution while still contributing to base fee congestion.

## Product Considerations

- **More predictable execution.** Users and applications no longer face intra-tipset “self-drain” failure modes where later messages unexpectedly become underfunded due to earlier execution in the same tipset.
- **Safer rollout for delegated execution.** Delegated execution patterns (e.g., EIP-7702 / [FIP-0111](./fip-0111.md)) increase the practical likelihood of intra-tipset value movement; reservations provide a protocol-level guardrail for those patterns.
- **Tooling updates.** Because Strict Sender Partitioning can cause some messages included in blocks to be ignored, explorers/indexers and client APIs may need to present “included but not executed” messages and correlate receipts to canonical tipset message selection.

## Implementation

This FIP is in Draft. Prototype implementations have been explored (see links below), but further spec review and benchmarking are required before activation decisions. Given the motivation described above, activation of EIP-7702 ([FIP-0111](./fip-0111.md)) SHOULD NOT precede activation of this FIP.

Implementing this FIP requires coordinated changes across clients and the execution engine:

- **Client layer (e.g., Lotus):**
  - implement Strict Sender Partitioning in the canonical tipset message selection/deduplication pipeline;
  - build `plan_T` from `M(T)` and invoke the reservation session lifecycle in the execution engine;
  - update mempool packing heuristics to reduce inclusion of messages likely to be ignored and to respect plan size limits.
- **Execution engine (ref-fvm):**
  - implement Begin/End reservation sessions and an ephemeral `reserved[ActorID]` ledger;
  - enforce free-balance checks on all non-gas value-moving paths;
  - update settlement to net-charge consumption and release reservations.
- **FFI boundary (filecoin-ffi):**
  - plumb reservation plans and session lifecycle calls between client and engine;
  - standardize error typing and reporting for reservation failures.

Prototype work (non-normative) has been explored in:

- https://github.com/filecoin-project/ref-fvm/pull/2236
- https://github.com/filecoin-project/lotus/pull/13427
- https://github.com/filecoin-project/filecoin-ffi/pull/554

Other clients (Forest, Venus, etc.) will need equivalent changes.

## TODO

- Benchmark and tune the default values for `MAX_RESERVATION_SENDERS` and `MAX_RESERVATION_PLAN_BYTES`.
- Confirm that base fee computation remains unchanged and document any interactions between base fee accounting and Strict Sender Partitioning.
- Specify client-facing UX expectations for “included but ignored” messages (explorers, indexers, RPCs).
- Produce shared cross-implementation test vectors/fuzzing targets for reservation sessions and Strict Sender Partitioning.
- Coordinate activation sequencing with [FIP-0111](./fip-0111.md) (EIP-7702) so delegated execution is not enabled ahead of this mitigation.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
