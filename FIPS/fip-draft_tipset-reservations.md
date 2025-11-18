---
fip: "<to be assigned>"
title: Multi-Stage Tipset Gas Reservations
author: "Michael Seiler (@snissn)"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1210
status: Draft
type: Technical (Core)
category: Core
created: 2025-11-17
spec-sections:
  - section-systems.filecoin_vm.gas_fee
  - section-systems.filecoin_vm.runtime.receipts
  - section-systems.filecoin_vm.interpreter.gas-payments
  - section-systems.filecoin_vm.interpreter.duplicate-messages
---

## Simple Summary

This FIP introduces multi-stage gas reservations across each Filecoin tipset. Before executing user messages, block-producing nodes reserve enough gas funds to cover each sender’s maximum possible gas spend across all of their messages in the tipset. Messages still execute in the same order and produce the same receipts as today, but gas charges are drawn from these reservations instead of depending solely on the sender’s live balance at execution time. This removes a class of intra-tipset “self-drain” scenarios where underfunded messages would otherwise fall back to miner penalties.

## Abstract

This FIP introduces tipset-scope gas reservations as a consensus rule for Filecoin to eliminate miner exposure to underfunded gas charges within a single tipset while preserving existing receipts and gas accounting. For each tipset, nodes derive the canonical set of explicit messages and construct a per-sender reservation plan equal to the sum, over the tipset, of each message’s `gas_limit * gas_fee_cap`. The execution engine maintains an internal reservation session ledger keyed by actor identifier; when a session is open, each sender’s free balance is defined as on-chain balance minus the remaining reserved amount recorded in this ledger.

Messages execute in the same order and with the same gas metering and `GasOutputs` computation as today. Preflight checks assert that reserved funds cover each message’s maximum gas cost, and all value transfers are enforced against free balance rather than raw balance, so a sender cannot move away funds needed to pay for reserved gas. Settlement is rewritten so that, for each message, the engine net-charges the sender only for actual consumption (base-fee burn, overestimation burn, and miner tip) while releasing the full reserved amount, realizing refunds by increasing free balance instead of issuing explicit refund transfers. The reservation ledger is tipset-local and requires no new on-chain actors or state migrations. The new rules activate at network version 28 via a chain upgrade, with pre-activation feature gating allowing best-effort and strict modes while different client implementations roll out support.

## Change Motivation

Under the current protocol, tipset execution can expose block producers to miner-charged gas penalties when a sender drains their balance within the same tipset. A common pattern is an intra-tipset “self-drain” sequence: a first message (M1) at nonce X executes contract logic that transfers away most of the sender’s funds, and a second message (M2) at nonce X+1 declares a large gas limit. At block construction time, the packer evaluates M2’s affordability based on the sender’s balance before M1 runs and admits it into the block. At execution time, however, M1 has already moved the funds, so M2 no longer has enough balance; today this shortfall can fall back to a miner penalty, even though the sender initiated both messages.

Existing mitigations rely on local heuristics during block construction, such as tracking declared message value and simple balance checks for individual messages. These techniques are inherently limited: they cannot fully account for arbitrary contract-level value movements, reordering across blocks in the same tipset, or the interaction of many messages from the same sender. As deferred execution and complex contracts become more common, the window in which a sender can pre-commit gas-heavy messages and then drain their account within the same tipset widens, increasing the risk that honest miners are forced to subsidize execution.

This FIP addresses the problem at the protocol level by reserving gas across the entire tipset up-front and enforcing affordability inside the execution engine itself. Rather than introducing a new on-chain actor or escrow mechanism, the engine maintains an internal, tipset-local reservation ledger that locks each sender’s maximum possible gas spend (`Σ(gas_limit * gas_fee_cap)`) before any message executes. Free balance during the tipset is defined as on-chain balance minus the remaining reservation, so any attempt to transfer funds needed to cover reserved gas will fail deterministically across implementations. This design keeps receipts and gas outputs identical to today, avoids state migrations, keeps the engine network-version agnostic, and provides a clear, consensus-level guarantee that miners will not be charged for underfunded messages created by intra-tipset self-drain.

## Specification

### Tipset-wide reservation plan

For each tipset `T` at height `h`, let `M(T)` denote the canonical set of explicit messages used by the Filecoin state transition at that height. `M(T)` is formed from user-signed messages contained in the blocks of `T`, deduplicated by CID across all blocks, and ordered as defined by the existing message processing rules. System / implicit messages (for example block rewards and cron) are not members of `M(T)`.

For each message `m ∈ M(T)` with sender address `from(m)`, gas limit `GasLimit(m)`, and gas fee cap `GasFeeCap(m)`, define its maximum gas cost

`gas_cost(m) = GasLimit(m) * GasFeeCap(m)`

using the same arithmetic and units as the existing gas accounting rules. Let `S(T)` be the set of senders that appear in `M(T)`. The tipset reservation plan for `T` is a mapping

`plan_T : S(T) → TokenAmount`

given by

`plan_T[s] = Σ_{m ∈ M(T), from(m) = s} gas_cost(m).`

Each message contributes to `plan_T` exactly once, even if it appears in multiple blocks in the tipset. All conforming implementations MUST derive an equivalent plan from the same canonical message set and gas cost definition.

Implementations MUST bound the size of `plan_T` to mitigate denial-of-service risk. In particular:

- The number of distinct senders in `plan_T` MUST NOT exceed a network parameter `MAX_RESERVATION_SENDERS` (with a default value of 65,536).
- The serialized size of `plan_T`, when encoded for handoff to the execution engine, MUST NOT exceed a network parameter `MAX_RESERVATION_PLAN_BYTES` (with a default value of 8 MiB).

If either bound would be exceeded, a conforming implementation MUST treat this as a reservation plan failure (see “Activation and consensus rules”).

### Reservation session API and lifecycle

The Filecoin state transition at a tipset with non-empty `plan_T` operates in two phases around message execution:

1. **Begin reservation session**: before executing any explicit message in `M(T)`, the node attempts to open exactly one reservation session for the tipset, parameterized by `plan_T`.
2. **End reservation session**: after processing all explicit messages in `M(T)`, and before executing any implicit messages for `T`, the node closes the reservation session.

The reservation session is maintained inside the execution engine as an ephemeral ledger:

- For each sender `s` (resolved to `ActorID`) the engine stores a non-negative reserved amount `reserved[s]`.
- A boolean flag `session_open` indicates whether a session is active.

The Begin operation has the following semantics:

- If `plan_T` is empty, Begin MUST be a no-op: `session_open` remains false and the engine MUST NOT enter reservation mode for this tipset.
- If `plan_T` is non-empty and `session_open` is already true, Begin MUST fail with a single-session violation.
- For each entry `(address, amount)` in `plan_T`, the engine resolves the address to an `ActorID` using the current state tree. Resolution MUST succeed for all entries; failure to resolve any sender is a reservation failure.
- For each resolved actor `a`, with on-chain balance `balance[a]` at the start of the tipset, the engine MUST check:

  `0 ≤ amount ≤ balance[a].`

  If this condition fails for any actor, Begin MUST fail with an insufficient-funds reservation failure.
- When all entries pass these checks, the engine sets:

  `reserved[a] = amount  for each sender a,`

  `reserved[a] = 0      for all other actors,`

  `session_open = true.`

The following invariants MUST hold whenever `session_open` is true:

- For every actor `a`, `reserved[a] ≥ 0`.
- For every sender `a` in `plan_T`, `reserved[a] ≤ balance[a]`.

The End operation has the following semantics:

- If `session_open` is false, End MUST fail with a session-closed violation.
- If `session_open` is true, the engine MUST verify that `reserved[a] == 0` for all actors `a`. Any non-zero entry is a reservation remainder failure.
- On success, the engine clears all `reserved` entries and sets `session_open = false`.

A conforming implementation MUST NOT open more than one reservation session per tipset, and MUST ensure that any successful Begin with a non-empty `plan_T` is paired with exactly one End before processing implicit messages for that tipset.

### Reservation mode and legacy mode

When `session_open` is true, the engine operates in **reservation mode** for all explicit messages in `M(T)`. When `session_open` is false, the engine operates in **legacy mode**, preserving existing preflight, transfer, and settlement behavior.

- In reservation mode, the rules in the following subsections apply.
- In legacy mode, the rules prior to this FIP continue to apply; `reserved[a]` is treated as zero for all actors, and Begin/End are not invoked.

Reservation mode applies only to explicit messages in `M(T)`. Implicit messages (including block rewards and cron) do not participate in the reservation plan and execute in legacy mode after End has succeeded.

### Preflight behaviour and coverage

For each explicit message `m` from sender `s` processed while `session_open` is true, preflight MUST:

1. Compute

   `gas_cost(m) = GasLimit(m) * GasFeeCap(m)`

   using the same big-integer arithmetic and units as existing gas accounting. Conceptually this multiplication is performed over unbounded integers; conforming implementations MUST ensure that `gas_cost(m)` is representable in their chosen numeric type. If an implementation detects that computing `gas_cost(m)` would overflow its representation, this condition MUST be treated as a node error (an implementation bug or misconfiguration), not as an alternative consensus outcome.
2. Assert that `reserved[s] ≥ gas_cost(m)`. Violation of this condition indicates that the host has constructed an inconsistent `plan_T` and is a reservation invariant failure. A conforming implementation MUST treat such a condition as a node error; it MUST NOT accept a chain that requires violating this invariant.
3. MUST NOT deduct `gas_cost(m)` from the sender’s on-chain balance as part of preflight. The sender's actor balance remains unchanged by preflight regardless of whether the message is later accepted or rejected.
4. If the message fails prevalidation (for example, due to bad syntax, invalid nonce, or other existing preflight failures) and is classified as a prevalidation failure, then before returning, the engine MUST decrement

   `reserved[s] := reserved[s] − gas_cost(m),`

   which is well-defined because step 2 ensures `reserved[s] ≥ gas_cost(m)`. The message’s gas accounting (including any miner penalty) remains as specified in the legacy rules. After this decrement, no further changes to actor balances or `reserved[]` entries are made for this message.

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

For each explicit message `m` from sender `s` that passes preflight and runs to completion (including messages that exit with failure codes), the engine computes `GasOutputs` exactly as in the legacy rules. In particular:

- `gas_cost(m) = GasLimit(m) * GasFeeCap(m)`,
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
- The sender’s free balance after settlement is

  `free_after[s] = balance[s] − reserved[s],`

  and differs from the pre-message free balance by exactly `−consumption`, matching the legacy net charge, while the "refund" effect is realized entirely by reducing `reserved[s]`.
- Each `reserved[s]` remains non-negative throughout, and is reduced by `gas_cost(m)` exactly once per message `m` from `s`.

For messages that terminate during preflight as prevalidation failures, settlement follows the legacy rules for burn and miner penalties, but MUST still apply:

- `reserved[s] := reserved[s] − gas_cost(m),`

with no changes to the sender’s on-chain balance. This ensures that, for a correctly constructed `plan_T`, all reservations are fully released by the end of the tipset.

### Session end invariants

Let `plan_T[s]` denote the total reservation amount for sender `s` in `plan_T`, and `gas_cost(m)` the maximum gas cost for each explicit message `m ∈ M(T)`. For a correctly constructed reservation plan and conforming execution:

- For each sender `s`,

  `plan_T[s] = Σ_{m ∈ M(T), from(m) = s} gas_cost(m),`

  and

  `reserved[s]` starts at `plan_T[s]`,

  `reserved[s]` decreases by `gas_cost(m)` once for each message `m` from `s`,

  `reserved[s]` is always ≥ 0.

At End, the engine MUST enforce:

- For all actors `a`, `reserved[a] == 0`.

Any non-zero remainder indicates a protocol invariant violation and is treated as a reservation remainder failure.

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
    - successfully calls End with `reserved[a] == 0` for all actors `a`.

  - If a node cannot start, maintain, or end a reservation session for a candidate tipset without violating these invariants, that tipset MUST NOT be considered valid.

Implementations remain free to expose different operational modes (for example, non-strict or strict pre-activation reservation checks), but from network version 28 onward, all conforming implementations MUST converge on the reservation mode semantics described here for consensus validity.

## Design Rationale

### Reserving `gas_limit * gas_fee_cap`

The reservation amount for each message is defined as `gas_limit * gas_fee_cap`, matching the existing definition of the maximum possible gas charge for that message. This choice ensures that:

- The reservation ledger uses the same `gas_cost` already implicit in the gas accounting rules, rather than introducing a new notion of "reserved price".
- The existing invariant `base_fee_burn + over_estimation_burn + refund + miner_tip = gas_cost` continues to hold exactly, with `gas_cost` unchanged.
- Receipts and `GasOutputs` remain identical to legacy behavior; the only difference is the internal path by which funds are prevented from being spent elsewhere during the tipset.

An alternative would have been to reserve only the "effective" gas price (for example, `gas_limit * min(gas_fee_cap, base_fee + premium)`). This would complicate reasoning about refunds, tie reservations directly to fee dynamics, and risk breaking the existing invariants when base fees or premiums change. By reserving `gas_limit * gas_fee_cap` instead, the reservation ledger can be reduced by exactly `gas_cost` per message while net-charging only the actual consumption, preserving existing accounting while providing stronger safety guarantees.

### Sender- and tipset-scoped reservations

Reservations are keyed by sender and tipset, not by individual message. The plan aggregates all explicit messages from the same sender in a tipset into a single per-sender amount `plan_T[s] = Σ gas_cost(m)`. This design:

- Ensures that affordability is independent of the intra-tipset execution order: once `plan_T` is established, any scheduling of messages from the same sender within the tipset is safe, because all messages draw from the same reserved total.
- Avoids the need to track per-message reservations or to expose message identifiers to the reservation API, simplifying the engine and host interface.
- Naturally handles deduplication by CID across blocks: a message that appears multiple times still contributes only once to `plan_T`, matching the canonical execution set.
- Keeps the ledger small and bounded by the number of distinct senders rather than the number of messages, which is important for both DoS resistance and FFI surfaces in existing implementations.

Per-message reservations were considered but rejected because they would not materially improve safety (the total reserved per sender must already cover all messages) while complicating the interface and increasing per-message bookkeeping.

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
- Because the ledger is engine-local and receipts are unchanged, older nodes that have not implemented this FIP will simply be unable to validate post-activation tipsets and will clearly fail, rather than silently disagree on balances or rewards.

This staged rollout balances the need for safety (eliminating miner penalties from intra-tipset self-drain) with the operational need to test and tune implementations before the consensus rule becomes mandatory.

### Alternatives considered

Several alternative designs were considered and rejected:

- **On-chain escrow actor:** A dedicated actor holding reserved funds could have enforced affordability by moving balances on-chain. This was rejected due to the need for state migrations, actor registry changes, more complex reward/burn plumbing, and increased attack surface. Engine-local reservations achieve the same protection without changing the on-chain actor set.
- **Per-message reservations:** Tracking reservations per message would require exposing message identifiers through the reservation API and maintaining a larger ledger. Because safety is determined by the total reserved per sender, per-message granularity adds complexity without improving guarantees and is unnecessary once the canonical message set is fixed.
- **Host-side enforcement only:** Relying solely on block-construction heuristics or host-side balance tracking cannot fully account for contract-level value transfers, complex call graphs, or cross-block reordering within a tipset. Such approaches are inherently advisory and cannot provide consensus guarantees. Moving enforcement into the execution engine, which sees all value movements, is necessary to guarantee that reserved gas cannot be spent elsewhere.
- **Changing gas pricing or receipt formats:** Designs that altered the definition of `gas_cost`, changed how refunds are represented in receipts, or modified miner reward calculations were rejected in order to minimize consensus risk and to keep existing tools and analytics compatible. By preserving gas pricing and receipts exactly, this FIP isolates its changes to intra-tipset fund availability and tipset validity rules.

Overall, the chosen design adds a minimal, engine-managed reservation layer that preserves existing gas economics and user-facing behavior while closing the specific class of intra-tipset self-drain exploits that expose miners to unintended penalties.

## Backwards Compatibility

This FIP is a consensus-breaking change that is rolled out via a network upgrade, but it is designed to preserve on-chain state and receipts as much as possible.

- **No state migration or new actors.** The reservation ledger is entirely engine-local and tipset-local. No new on-chain actor is introduced, no existing actor is modified, and no state migration is required. The Burn, Reward, and other built-in actors continue to receive funds exactly as they do today.
- **Pre-activation behaviour (network versions < 28).** Before the network version 28 upgrade epoch, the canonical Filecoin state transition remains the legacy semantics without reservations. Implementations MAY expose reservation mode as a best-effort or testing feature gated by local configuration or feature flags, but any Begin/End failure, invariant violation, or overflow MUST NOT change consensus validity: a tipset that is valid under legacy semantics MUST continue to be considered valid, regardless of whether a particular node attempted reservations. Nodes that choose to enable “strict” pre-activation behaviour (treating some reservation failures as tipset-invalid) are effectively running with a local consensus override and risk forking away from the canonical chain; this is an operator choice, not part of the FIP’s pre-activation consensus rules.
- **Activation at network version 28.** At the configured upgrade epoch for network version 28 on each network, the reservation rules become part of consensus. From that point onward, a tipset is valid only if it admits a successful reservation session around the canonical explicit message set as described in this FIP (Begin succeeds with an affordable, size-bounded plan; all messages execute while preserving invariants; End observes zero remaining reservations). Clients MUST treat this behaviour as the unique canonical state transition for tipsets at or after the upgrade height.
- **Post-activation engine requirements.** After activation, nodes MUST run an execution engine that implements reservation sessions. Engines that do not implement reservations and simply return a “not implemented” reservation failure (for example, an engine-level “reservations not supported” status) cannot validate post-activation tipsets. Hosts MUST treat such responses as node errors (misconfiguration or outdated engine), not as signals to silently fall back to legacy behaviour.
- **Impact on non-upgraded nodes.** Nodes that do not implement this FIP, or that continue to run engines without reservation support, will diverge at the activation epoch. They will either:
  - Fail to validate post-activation tipsets (e.g., by treating messages as invalid or encountering unhandled errors), or
  - Continue applying legacy semantics and accept blocks that upgraded nodes reject (or vice versa), leading them onto a non-canonical fork.
  In either case, non-upgraded nodes cannot remain on the canonical chain beyond the activation epoch and MUST be upgraded to a reservation-aware implementation to remain in consensus.

Because receipts (`ExitCode`, `GasUsed`, events) and `GasOutputs` are defined to remain identical to legacy behaviour, the chain history prior to activation remains valid without change, and tooling that interprets receipts and gas accounting does not need to be updated for the new rule.

## Test Cases

Implementations of this FIP MUST be accompanied by targeted tests and fuzzing that validate reservation behaviour, gas accounting invariants, and activation semantics. The concrete test suites will differ across clients, but should cover at least the following categories.

- **Engine unit tests (reservation session and preflight).**
  - Session lifecycle: opening and closing a single session; empty-plan no-op semantics; enforcing single-session invariants; rejecting plans that exceed affordability, sender-count (`MaxSenders`), or size (`MaxPlanBytes`) limits; rejecting unknown senders or resolution failures.
  - Preflight under reservations: computing `gas_cost = gas_fee_cap * gas_limit` with checked arithmetic; asserting coverage (`reservations[sender] ≥ gas_cost`) without pre-deducting funds; on prevalidation failures (invalid sender, nonce, or inclusion gas limit), decrementing the reservation by `gas_cost` so that the ledger can end at zero.
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

- **Miner exposure to underfunded gas.** By reserving `Σ(gas_limit * gas_fee_cap)` per sender before any message executes, and enforcing all value transfers against free balance `balance − reserved_remaining`, the protocol ensures that senders cannot move away funds required to pay for gas. A message either executes with its gas fully funded from the reserved amount or the tipset fails reservation checks and is considered invalid (post-activation), removing a class of exploits where miners are forced to subsidize underfunded gas.
- **Complete coverage of value-moving paths.** Security depends on the guarantee that every value-moving operation is checked against free balance. Implementations MUST ensure that all paths that move FIL (including message value transfers, actor creation sends, FEVM/ EVM CALL and DELEGATECALL, SELFDESTRUCT, and built-in implicit sends) route through the reservation-aware transfer primitive. Any missing path would allow reserved funds to be spent, potentially re-introducing miner exposure or breaking reservation invariants. Tests should explicitly cover SELFDESTRUCT and implicit sends to guard against regressions.
- **Reservation invariants and node errors.** The safety of this design relies on strict invariants:
  - `gas_cost = gas_fee_cap * gas_limit` is defined over unbounded integers; conforming implementations MUST compute it without overflow for all messages admitted by the protocol.
  - Preflight in reservation mode MUST enforce `reservations[sender] ≥ gas_cost`; any violation indicates host/engine inconsistency (a reservation invariant failure).
  - `end_reservation_session` MUST observe a zero remainder; any non-zero reservation at End is a reservation remainder failure.
  Implementations MUST treat overflow and reservation invariant failures as node errors (implementation bugs or misconfiguration), not as consensus-level exceptions. A node that encounters such conditions should stop following the chain and alert operators rather than attempting to continue on an alternative fork, to avoid consensus splits based on buggy behaviour.
- **Risks from partial or incorrect implementations.** Incomplete implementations—such as failing to decrement reservations on prevalidation failure, neglecting to clear reservations at End, or mishandling “not implemented” status codes—can lead to stuck reservation sessions, inconsistent free-balance checks, or silent fallback to legacy semantics when reservations should be enforced. These bugs can undermine the protection this FIP is intended to provide and, in the worst case, cause nodes to accept or reject tipsets differently. Implementers SHOULD rely on the test categories described above (especially integration and fuzz tests) to detect such partial behaviour.
- **Denial-of-service and performance considerations.** Reservation plans and the associated ledger create a new surface for resource exhaustion. To mitigate DoS risks:
  - Hosts and engines MUST enforce reasonable bounds on plan size, including a maximum number of distinct senders (`MaxSenders`) and a maximum encoded plan size (`MaxPlanBytes`); exceeding these bounds MUST produce a dedicated “plan too large” reservation failure.
  - Plan aggregation in the host SHOULD remain O(n) in the number of explicit messages, and engine checks SHOULD remain O(1) per message, so that Stage-1 reservation overhead remains a small fraction of total tipset application time.
  - FFI surfaces should avoid unbounded allocations when decoding plans or exporting telemetry, and implementations SHOULD monitor reservation-related metrics to detect abnormal workloads.
- **Activation and configuration risks.** Because reservations become consensus rules only from network version 28 onward, misconfigured pre-activation nodes that enable “strict” reservation enforcement can fork away from the canonical chain by rejecting tipsets that other nodes accept. Operators SHOULD treat strict pre-activation modes as testing tools and ensure production nodes match the network’s agreed activation and gating policies. Post-activation, nodes MUST treat “not implemented” reservation responses as node errors, not as consensus signals, to avoid silently diverging back to legacy behaviour.

Overall, this FIP strengthens miner and network security by preventing a class of intra-tipset gas underfunding exploits, while relying on well-specified invariants (coverage `reservations[sender] ≥ gas_cost`, zero remainder at session end, non-negative reservations) and resource limits (`MaxSenders`, `MaxPlanBytes`) to bound the new surfaces it introduces. Careful implementation, testing, and error handling across engines and hosts is essential to avoid new consensus divergence risks.
