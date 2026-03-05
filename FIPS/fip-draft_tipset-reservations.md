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

# FIP-XXXX: Multi-Stage Tipset Gas Reservations

## Simple Summary

This FIP reserves each sender's maximum gas spend across a tipset before explicit messages execute. During that reservation session, non-gas transfers are limited to `balance - reserved`, preventing earlier messages from draining funds needed for later gas charges. Executed explicit messages keep legacy receipts and gas accounting.

The FIP also introduces **Strict Sender Partitioning**: once a sender contributes explicit messages from a higher-precedence block in a tipset, that sender contributes none from lower-precedence blocks.

## Abstract

This FIP adds tipset-wide gas reservations for explicit messages. For each tipset, nodes derive the canonical explicit message set `M(T)`, compute `plan_T[s] = Σ gas_limit * gas_fee_cap` over the messages contributed by sender `s` in `M(T)`, and open a tipset-local reservation session in the execution engine. While the session is open, non-gas value transfers are checked against `balance - reserved`.

For executed explicit messages, gas metering, receipts, and `GasOutputs` remain unchanged: the sender is charged only for actual gas consumption and the full reservation for the message is then released. The FIP also adds Strict Sender Partitioning when constructing `M(T)`: once a sender contributes messages from a higher-precedence block, lower-precedence blocks contribute none for that sender. This keeps reservation planning aligned with execution and avoids cross-block aggregation of conflicting sender message sets. The reservation ledger is engine-local, requires no state migration, and activates in a future network upgrade.

## Change Motivation

Under the current protocol, block construction and tipset execution use the sender's balance at different points in time. A message can appear affordable when it is selected into a block, then become underfunded after an earlier message from the same sender executes in the same tipset.

A representative pattern is:

- `m1` at nonce `X` executes logic that transfers or consumes most of the sender's funds.
- `m2` at nonce `X+1` declares a large gas limit and is packed using the sender's pre-tipset balance.

At execution time, `m1` may have already reduced the sender's spendable balance below what `m2` requires. Local packing heuristics can mitigate some cases, but they cannot model arbitrary contract-level value movement, cross-block interactions within a tipset, or the aggregate effect of many messages from the same sender.

This proposal moves the affordability check into the protocol. Before explicit messages execute, the node reserves each sender's maximum possible gas spend across the tipset and treats the sender's remaining spendable balance as `balance - reserved`. That prevents non-gas transfers during execution from consuming funds already committed to gas.

The issue is not specific to delegated execution, but delegated execution patterns such as EIP-7702 (see [FIP-0111](./fip-0111.md)) make it more practical for a single sender to combine arbitrary value-moving logic with additional gas-heavy messages in the same tipset. Networks that intend to enable those patterns should activate this mitigation first or in the same upgrade.

## Specification

This section defines the protocol rules for tipset-wide gas reservations.

### Constants

| Constant | Draft value | Meaning |
| -------- | ----------- | ------- |
| `MAX_RESERVATION_SENDERS` | `65,536` | Maximum number of distinct sender addresses in `plan_T`. |
| `MAX_RESERVATION_PLAN_BYTES` | `8 MiB` | Maximum encoded size of `plan_T` passed to the execution engine. |

These are the proposed consensus values for the draft and remain subject to benchmarking before the FIP leaves Draft.

### Definitions

- `M(T)`: the canonical ordered list of explicit messages executed for tipset `T`. Only messages in `M(T)` execute and produce receipts.
- `ignored message`: an explicit message excluded from `M(T)` by CID deduplication or Strict Sender Partitioning. Ignored messages do not execute, produce no receipt, and do not contribute to `plan_T`.
- `gas_cost(m)`: the maximum possible gas charge for message `m`, defined as `GasLimit(m) * GasFeeCap(m)`.
- `plan_T`: the tipset reservation plan derived from `M(T)`. `plan_T` is keyed by sender address, not by `ActorID`.
- `resolved sender`: the `ActorID` obtained by resolving a sender address in `plan_T` when the reservation session begins.
- `reserved[a]`: the remaining reserved amount for resolved actor `a` while a reservation session is open.
- `free[a]`: the spendable balance of resolved actor `a` during a reservation session, defined as `balance[a] - reserved[a]`.
- `consumption`: the actual gas charge at settlement, equal to `base_fee_burn + over_estimation_burn + miner_tip`.

### Canonical Explicit Message Set

For each tipset `T`, implementations MUST derive `M(T)` from the blocks in `T` using legacy CID deduplication plus Strict Sender Partitioning.

To construct `M(T)`:

1. Order the blocks in `T` by ticket precedence, highest precedence first.
2. Initialize `CID_seen := {}`, `S_seen := {}`, and `M(T) := []`.
3. For each block `B` in that order, initialize `B_senders := {}` and iterate the explicit messages in `B` in the same canonical in-block order used by legacy execution.
4. For each explicit message `m` in `B`:
   - if `cid(m) ∈ CID_seen`, `m` is an ignored message;
   - otherwise, add `cid(m)` to `CID_seen`;
   - if `from(m) ∈ S_seen`, `m` is an ignored message due to Strict Sender Partitioning;
   - otherwise, append `m` to `M(T)` and add `from(m)` to `B_senders`.
5. After block `B` has been fully scanned, set `S_seen := S_seen ∪ B_senders`.

This block-scoped update ensures that all messages from a sender are included from the first accepted block for that sender, while lower-precedence blocks for that sender contribute no explicit messages.

System and implicit messages are not members of `M(T)`.

After `M(T)` is constructed, explicit message execution, receipt generation, and reservation planning MUST all use `M(T)` in that order. This FIP does not otherwise change explicit message ordering semantics.

### Reservation Plan

For each message `m ∈ M(T)`, `gas_cost(m)` MUST be computed using the same arithmetic and units as existing gas accounting, with unbounded-integer semantics.

Let `S(T)` be the set of sender addresses that appear in `M(T)`. The reservation plan for tipset `T` is:

`plan_T : S(T) -> TokenAmount`

with

`plan_T[s] = Σ_{m ∈ M(T), from(m) = s} gas_cost(m)`

For a given `M(T)`, all conforming implementations MUST derive the same `plan_T`.

`plan_T` MUST satisfy both of the following bounds:

- the number of distinct senders in `plan_T` MUST NOT exceed `MAX_RESERVATION_SENDERS`;
- the encoded size of `plan_T` passed to the execution engine MUST NOT exceed `MAX_RESERVATION_PLAN_BYTES`.

If either bound is exceeded, the result is a `PlanTooLarge` reservation failure.

### Reservation Session Lifecycle

A reservation session applies only to the explicit messages in `M(T)`. Implicit messages execute after the reservation session has ended.

If `plan_T` is empty, no reservation session is opened and explicit messages execute under legacy semantics.

If `plan_T` is non-empty, the state transition MUST attempt exactly one `Begin` before executing the first message in `M(T)`, and exactly one `End` after processing the last message in `M(T)` and before executing implicit messages.

At `Begin`:

- if a reservation session is already open, this is a node error;
- each sender address in `plan_T` MUST be resolved against the current state tree to an `ActorID`; failure to resolve any sender is a `SenderResolutionFailure` reservation failure;
- for each resolved actor `a`, with reservation amount `amount` taken from the corresponding entry in `plan_T`, the engine MUST check `0 <= amount <= balance[a]`; failure is an `InsufficientFundsAtBegin` reservation failure;
- otherwise, the engine MUST initialize `reserved[a] = amount` for each resolved actor and set `session_open = true`.

Actors not present in `plan_T` are treated as having `reserved[a] = 0`.

At `End`:

- if no reservation session is open, this is a node error;
- every reservation entry MUST have been fully released, i.e. there MUST be no remaining `reserved[a] > 0`; any non-zero remainder is a node error;
- on success, the engine MUST clear the reservation ledger and set `session_open = false`.

### Explicit Message Processing in Reservation Mode

When a reservation session is open, each message in `M(T)` MUST be processed under the following rules.

#### Preflight

Preflight does not deduct on-chain balance. For each explicit message `m`:

- `gas_cost(m)` MUST be recomputed using the same rules used for `plan_T`; inability to represent this value is a node error;
- let `a` be the resolved `ActorID` for `from(m)` obtained at `Begin`; `reserved[a] >= gas_cost(m)` MUST hold, otherwise the result is a `CoverageViolation` node error;
- if `m` fails legacy prevalidation and does not execute, the engine MUST release that message's reservation exactly once by applying `reserved[a] := reserved[a] - gas_cost(m)`.

For prevalidation failures, gas accounting and receipt behavior remain as in the legacy rules.

#### Transfer Enforcement

For any non-gas transfer of amount `value` from actor `a` while a reservation session is open:

- `free[a]` MUST be computed as `balance[a] - reserved[a]`;
- `value <= free[a]` MUST hold;
- if `value > free[a]`, the transfer MUST fail using the existing insufficient-funds semantics for that operation, and neither on-chain balances nor `reserved[]` may change as a result of that failed transfer.

This rule applies to top-level message value transfers, actor-initiated sends, sub-calls that carry value, actor creation with initial balance, SELFDESTRUCT-like flows, and implicit sends performed by built-in actors. Gas settlement is not subject to the free-balance check.

#### Settlement

For every explicit message that executes, including one that finishes with a failure exit code, the engine MUST compute `GasOutputs` exactly as in the legacy rules, so that:

`gas_cost(m) = base_fee_burn + over_estimation_burn + refund + miner_tip`

with all quantities non-negative and measured in attoFIL.

At settlement:

- the engine MUST deduct `consumption = base_fee_burn + over_estimation_burn + miner_tip` from the sender's on-chain balance;
- the engine MUST credit the burn and reward accounts exactly as in the legacy rules;
- the engine MUST NOT credit `refund` back to the sender as an explicit balance transfer;
- the engine MUST release the message's reservation exactly once by applying `reserved[a] := reserved[a] - gas_cost(m)`, where `a` is the resolved `ActorID` for `from(m)`.

As a consequence, settlement MUST preserve:

- `consumption + refund = gas_cost(m)`;
- `reserved[a] >= 0` throughout the session; and
- `free_post - free_pre = refund` for the sender of the settled message.

### Base Fee

This FIP does not change base fee adjustment. Base fee continues to be computed from the legacy tipset-wide set of unique explicit message CIDs present in the tipset. Strict Sender Partitioning changes execution, receipts, and reservation planning only; it does not change which unique explicit message CIDs contribute to base fee.

### Failure Classes

This specification distinguishes the following outcomes:

- `ignored message`: a message excluded from `M(T)` by CID deduplication or Strict Sender Partitioning;
- `reservation failure`: an input-driven failure while deriving or opening the reservation session. In this specification, `PlanTooLarge`, `SenderResolutionFailure`, and `InsufficientFundsAtBegin` are reservation failures;
- `node error`: a local implementation fault or invariant violation. In this specification, arithmetic overflow, session misuse, unsupported reservation functionality after activation, `CoverageViolation`, and non-zero remainder at `End` are node errors.

### Activation and Validity

This FIP activates at the upgrade epoch assigned by the network version that adopts it.

Before activation, implementations MAY expose reservation mode for testing or telemetry, but reservation failures and node errors MUST NOT affect consensus validity. The canonical state transition remains the legacy behavior.

After activation, conforming implementations MUST:

1. derive `M(T)` as specified above;
2. derive `plan_T` from `M(T)`;
3. open a reservation session if and only if `plan_T` is non-empty;
4. process each explicit message in `M(T)` using the reservation rules above;
5. end the reservation session before executing implicit messages; and
6. execute implicit messages using legacy behavior.

After activation, a candidate tipset that triggers a reservation failure is invalid.

Node errors are outside consensus. A node that encounters a node error while evaluating a candidate tipset MUST treat it as a local fault, not as an alternative valid or invalid state transition, and SHOULD stop following the chain until the fault is investigated.

## Design Rationale

The subsections below explain the execution flow and the main design choices behind the rules in `## Specification`.

### Reservation Flow

Tipset processing under this proposal follows the sequence below:

1. Construct `M(T)` using CID deduplication and Strict Sender Partitioning.
2. Construct `plan_T` from `M(T)`.
3. If `plan_T` is non-empty, call `Begin(plan_T)`.
4. Execute the messages in `M(T)` in order.
5. Release each message's reservation once, either at prevalidation failure or at settlement.
6. If a session was opened, call `End()`.
7. Execute implicit messages after the reservation session has ended.

This keeps reservation planning aligned with the same message set used for explicit execution and receipt generation.

### Worked Example

Consider a tipset `T` containing two blocks, `B_1` (higher precedence) and `B_2` (lower precedence). In canonical in-block order, `B_1` contains two explicit messages `m1` from sender `A` and `m2` from sender `B`, and `B_2` contains `m3` from sender `A` and `m4` from sender `C`. Assume all message CIDs are unique.

Under Strict Sender Partitioning, `m3` is an ignored message because sender `A` already contributed messages from `B_1`. The resulting canonical explicit message list is `M(T) = [m1, m2, m4]`.

If `plan_T[A] = gas_cost(m1) = 30` and `balance[A] = 35` at `Begin`, then `reserved[A] = 30` and `free[A] = 5`. During execution of `m1`, any non-gas transfer larger than `5` from `A` fails. If settlement later computes `consumption = 12` and `refund = 18`, then the sender's on-chain balance decreases by `12`, `reserved[A]` decreases by `30`, and `free[A]` increases by `18` without any explicit refund transfer.

### Strict Sender Partitioning

The definition of `M(T)` is updated to partition senders by block precedence: if a sender contributes messages from a higher-precedence block, that sender contributes no explicit messages from lower-precedence blocks. This keeps reservation planning aligned with the explicit messages that will actually execute.

Without this rule, a sender could broadcast two sets of messages: set A (affordable) included in Block A, and set B (affordable) included in Block B. If both blocks are included in a tipset, the aggregate reservation `plan_T` would sum the costs of A and B. If this sum exceeds the sender's balance, the tipset would fail the reservation check and be invalid. This creates an asymmetric advantage for an attacker: they can invalidate a tipset (and deny rewards to all miners in it) by broadcasting valid individual blocks that conflict only when aggregated.

With strict partitioning, the reservation for a sender in the tipset is taken from a single accepted block for that sender rather than from a cross-block merge. That removes the aggregate-overflow case.

### Reserving `gas_limit * gas_fee_cap`

The reservation amount for each message is defined as `gas_limit * gas_fee_cap`, matching the existing definition of the maximum possible gas charge for that message. This choice ensures that:

- The reservation ledger uses the same `gas_cost` already implicit in the gas accounting rules, rather than introducing a new notion of "reserved price".
- The existing invariant `base_fee_burn + over_estimation_burn + refund + miner_tip = gas_cost` continues to hold exactly, with `gas_cost` unchanged.
- For messages in `M(T)` that execute, receipts and `GasOutputs` remain identical to legacy behavior; the only difference is the internal path by which funds are prevented from being spent elsewhere during the tipset.

An alternative would have been to reserve only the "effective" gas price (for example, `gas_limit * min(gas_fee_cap, base_fee + premium)`). That would complicate refund accounting, tie reservations directly to fee dynamics, and make the release rules less direct. Reserving `gas_limit * gas_fee_cap` keeps settlement aligned with the existing `gas_cost` identity.

### Sender- and tipset-scoped reservations

Reservations are keyed by sender and tipset, not by individual message. The plan aggregates all explicit messages from the same sender in a tipset into a single per-sender amount `plan_T[s] = Σ gas_cost(m)`. This design:

- Ensures that affordability is independent of the intra-tipset execution order: once `plan_T` is established, any scheduling of messages from the same sender within the tipset is safe, because all messages draw from the same reserved total.
- Avoids the need to track per-message reservations or to expose message identifiers to the reservation API, simplifying the engine and host interface.
- Naturally handles deduplication by CID across blocks: a message that appears multiple times still contributes only once to `plan_T`, matching the canonical execution set.
- Keeps the ledger small and bounded by the number of distinct senders rather than the number of messages, which is important for both DoS resistance and FFI surfaces in existing implementations.

Per-message reservations were considered but rejected because they would not materially improve safety (the total reserved per sender must already cover all messages) while complicating the interface and increasing per-message bookkeeping.

### Reservation plan bounds

`MAX_RESERVATION_SENDERS` and `MAX_RESERVATION_PLAN_BYTES` bound worst-case resource usage for plan construction, FFI handoff, plan decoding, and per-tipset reservation bookkeeping. Without explicit bounds, an attacker could attempt to create tipsets with extremely large sender sets or oversized plans, turning reservation planning into a denial-of-service vector.

The draft values (65,536 senders; 8 MiB encoded plan) are intended to be conservatively high while still bounding memory and decode costs. They should be benchmarked and finalized before the FIP advances beyond Draft.

### Engine-local reservation ledger with no new on-chain actor

The reservation ledger is kept entirely inside the execution engine and exists only for the duration of a tipset. No new on-chain actor or persistent state is introduced. This design was chosen to:

- Avoid any state migration or actor registry changes: the Burn, Reward, and other built-in actors continue to function exactly as today.
- Keep the engine network-version agnostic: from the engine’s perspective, reservation mode is an internal option that can be enabled or disabled by the host without changing on-chain code.
- Ensure that all value-moving paths are covered: because the ledger lives in the engine that executes all calls and implicit sends, every transfer can be checked against free balance, including those triggered deep in call stacks or by built-in actors.
- Minimize surface area for consensus divergence: all conforming clients need only implement the same Begin/End semantics and free-balance checks; the ledger itself does not interact with other on-chain actors.

An alternative design based on an on-chain escrow actor was rejected because it would require new actor code, migration of existing balances or gas flows, and more complex interactions with existing reward and burn logic. It would also expose the reservation ledger to user-visible manipulation, increasing the attack surface. Keeping reservations engine-local achieves the desired safety properties while keeping the ledger invisible and ephemeral.

### Settlement via net charge and reservation release

The settlement rules net-charge the sender only for actual consumption (`base_fee_burn + over_estimation_burn + miner_tip`) and realize refunds by decreasing `reserved[s]` by the full `gas_cost`. This approach:

- Preserves the external behavior of gas accounting for executed explicit messages: receipts, `GasOutputs`, and miner/burn flows are unchanged.
- Realizes refunds by increasing free balance, not by issuing new balance credits, which keeps the on-chain balance evolution identical to the legacy path while preventing misuse of reserved funds mid-tipset.
- Guarantees the invariant `consumption + refund = gas_cost` and enforces that reservations return to zero by session end, because each message’s full `gas_cost` is released exactly once.

If the protocol instead refunded the sender by explicitly crediting `refund` and reduced `reserved[s]` only by the consumed portion, it would become harder to maintain the simple invariants on `reserved[s]` and free balance, and to argue receipt parity. The chosen design keeps the ledger and invariants straightforward.

### Activation and rollout strategy

Making reservations a consensus rule only at a future network upgrade provides a clear activation point while allowing a smooth rollout:

- Before activation, nodes can opt in to reservation mode under feature flags or configuration without affecting consensus validity, enabling testing against mainnet traffic and performance tuning.
- At activation, the rule "every valid tipset must admit a successful reservation session with zero remainder" becomes part of consensus, eliminating miner exposure to underfunded gas while ensuring all conforming implementations agree on block validity.
- Because the ledger is engine-local and gas accounting for executed messages is unchanged, older nodes that have not implemented this FIP will simply be unable to validate post-activation tipsets and will clearly fail, rather than silently disagree on balances or rewards.

This staged rollout balances the need for safety (eliminating miner penalties from intra-tipset self-drain) with the operational need to test and tune implementations before the consensus rule becomes mandatory.

### Alternatives considered

Several alternative designs were considered and rejected:

- **On-chain escrow actor:** A dedicated actor holding reserved funds could have enforced affordability by moving balances on-chain. This was rejected due to the need for state migrations, actor registry changes, more complex reward/burn plumbing, and increased attack surface. Engine-local reservations achieve the same protection without changing the on-chain actor set.
- **Per-message reservations:** Tracking reservations per message would require exposing message identifiers through the reservation API and maintaining a larger ledger. Because safety is determined by the total reserved per sender, per-message granularity adds complexity without improving guarantees and is unnecessary once the canonical message set is fixed.
- **Host-side enforcement only:** Relying solely on block-construction heuristics or host-side balance tracking cannot fully account for contract-level value transfers, complex call graphs, or cross-block reordering within a tipset. Such approaches are inherently advisory and cannot provide consensus guarantees. Moving enforcement into the execution engine, which sees all value movements, is required to ensure reserved gas cannot be spent elsewhere.
- **Changing gas pricing or receipt formats:** Designs that altered the definition of `gas_cost`, changed how refunds are represented in receipts, or modified miner reward calculations were rejected in order to minimize consensus risk and to keep existing tools and analytics compatible. By preserving gas pricing and receipts exactly, this FIP isolates its changes to intra-tipset fund availability and tipset validity rules.

Overall, the chosen design adds an engine-managed reservation layer that changes intra-tipset fund availability without changing gas accounting for executed explicit messages.

## Backwards Compatibility

This FIP is a consensus-breaking change that activates via a future network upgrade.

- **No state migration or new actors.** The reservation ledger is engine-local and tipset-local. No new on-chain actor is introduced and no state migration is required.
- **Canonical message selection changes.** Strict Sender Partitioning changes the canonical explicit message set `M(T)`. In particular, some messages included in lower-precedence blocks may be ignored and therefore produce no receipts and no gas charges. Tooling MUST correlate receipts to the canonical tipset message set rather than assuming that “in a block” implies “executed in the tipset”.
- **Pre-activation behaviour.** Before activation, the canonical state transition remains the legacy semantics without reservations. Implementations MAY expose reservation mode for testing or telemetry, but reservation failures and node errors MUST NOT affect consensus validity.
- **Post-activation requirements.** After activation, nodes MUST run a reservation-aware implementation. Nodes that do not upgrade will be unable to validate post-activation tipsets and will diverge from the canonical chain.

## Test Cases

Implementations of this FIP MUST be accompanied by targeted tests and fuzzing that validate reservation behaviour, gas accounting invariants, and activation semantics. The concrete test suites will differ across clients, but should cover at least the following categories.

- **Engine unit tests (reservation session and preflight).**
  - Session lifecycle: opening and closing a single session; empty-plan no-op semantics; enforcing the single-session invariant; rejecting plans that exceed affordability, sender-count (`MAX_RESERVATION_SENDERS`), or size (`MAX_RESERVATION_PLAN_BYTES`) limits; rejecting unknown senders or resolution failures.
  - Preflight under reservations: computing `gas_cost = gas_fee_cap * gas_limit` with unbounded-integer semantics; asserting coverage for the resolved sender without pre-deducting funds; on prevalidation failures (invalid sender, nonce, or inclusion gas limit), decrementing the reservation by `gas_cost` so that the ledger can end at zero.
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
    - Reservations reach zero at End; any non-zero remainder is treated as a node error.
  - Gas accounting property tests (for example, quickcheck-based tests of `GasOutputs` and settlement) that continue to hold under reservation mode as they do under legacy mode.

The exact filenames and test harnesses will differ across implementations (e.g., Lotus, ref-fvm, filecoin-ffi, and other clients), but implementers SHOULD construct suites that cover the same behavioural properties. In particular, engines and hosts SHOULD include tests that exercise both pre-activation (legacy and best-effort reservation) configurations and post-activation consensus behaviour to ensure correct activation, gating, and error handling.

## Security Considerations

This FIP is motivated by a security problem: under current semantics, miners can be exposed to gas penalties from underfunded messages created by intra-tipset “self-drain” patterns. Tipset-wide reservations eliminate this exposure when correctly implemented, but they also introduce new invariants and error classes that must be handled carefully.

- **Partial orphan spam.** Strict Sender Partitioning introduces a spam vector: a sender can broadcast different valid message sets to different miners, causing lower-precedence blocks to carry messages that become ignored at execution time. The miner of the lower-precedence block bears propagation and storage cost but receives no gas reward for those ignored messages. This trades a tipset invalidation risk for a block-level bandwidth and inclusion-cost risk.
- **Miner exposure to underfunded gas.** By reserving `Σ(gas_limit * gas_fee_cap)` per sender before execution and enforcing non-gas transfers against free balance, the protocol prevents explicit messages in `M(T)` from losing gas backing because earlier value-moving execution drained the sender's account mid-tipset.
- **Complete coverage of value-moving paths.** Security depends on every value-moving operation being checked against free balance. Implementations MUST ensure that all paths that move FIL, including message value transfers, actor creation sends, EVM calls that carry value, SELFDESTRUCT-like flows, and built-in implicit sends, route through the reservation-aware transfer primitive. Any missing path would allow reserved funds to be spent and would invalidate the model.
- **Reservation invariants and node errors.** The safety of this design relies on strict invariants:
  - `gas_cost = gas_fee_cap * gas_limit` is defined over unbounded integers; conforming implementations MUST compute it without overflow for all messages admitted by the protocol.
  - Preflight in reservation mode MUST enforce `reserved[a] >= gas_cost` for the resolved sender `a`; any violation indicates host/engine inconsistency.
  - `End` MUST observe a zero remainder; any non-zero reservation at End is a node error.
  Implementations MUST treat overflow and reservation invariant violations as node errors, not as alternate consensus outcomes. A node that encounters such conditions should stop following the chain and alert operators rather than attempting to continue on an alternative fork.
- **Risks from partial or incorrect implementations.** Incomplete implementations—such as failing to decrement reservations on prevalidation failure, neglecting to clear reservations at End, or mishandling “not implemented” status codes—can lead to stuck reservation sessions, inconsistent free-balance checks, or silent fallback to legacy semantics when reservations should be enforced. These bugs can undermine the protection this FIP is intended to provide and, in the worst case, cause nodes to accept or reject tipsets differently. Implementers SHOULD rely on the test categories described above (especially integration and fuzz tests) to detect such partial behaviour.
- **Denial-of-service and performance considerations.** Reservation plans and the associated ledger create a new surface for resource exhaustion. To mitigate DoS risks:
  - Hosts and engines MUST enforce reasonable bounds on plan size, including a maximum number of distinct senders (`MAX_RESERVATION_SENDERS`) and a maximum encoded plan size (`MAX_RESERVATION_PLAN_BYTES`); exceeding these bounds MUST produce a dedicated “plan too large” reservation failure.
  - Plan aggregation in the host SHOULD remain O(n) in the number of explicit messages, and engine checks SHOULD remain O(1) per message, so that Stage-1 reservation overhead remains a small fraction of total tipset application time.
  - FFI surfaces should avoid unbounded allocations when decoding plans or exporting telemetry, and implementations SHOULD monitor reservation-related metrics to detect abnormal workloads.
- **Activation and configuration risks.** Because reservations become consensus rules only after activation, misconfigured pre-activation nodes that enable strict reservation enforcement can fork away from the canonical chain by rejecting tipsets that other nodes accept. Operators SHOULD treat strict pre-activation modes as testing tools and ensure production nodes match the network's agreed activation and gating policies. Post-activation, nodes MUST treat unsupported reservation functionality as a node error, not as a consensus signal.

Overall, this FIP prevents a class of intra-tipset gas-underfunding exploits while relying on explicit invariants (coverage for the resolved sender, zero remainder at session end, non-negative reservations) and resource limits (`MAX_RESERVATION_SENDERS`, `MAX_RESERVATION_PLAN_BYTES`) to bound the new surfaces it introduces. Careful implementation, testing, and error handling across engines and hosts is essential to avoid new consensus divergence risks.

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

This FIP is in Draft. Prototype implementations have been explored (see links below), but further spec review and benchmarking are required before activation decisions. Networks that intend to enable EIP-7702 ([FIP-0111](./fip-0111.md)) should activate this FIP first or in the same upgrade.

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
  - standardize error typing and reporting for reservation failures and node errors.

Prototype work has been explored in:

- https://github.com/filecoin-project/ref-fvm/pull/2236
- https://github.com/filecoin-project/lotus/pull/13427
- https://github.com/filecoin-project/filecoin-ffi/pull/554

Other clients (Forest, Venus, etc.) will need equivalent changes.

## TODO

- Benchmark and finalize the draft values for `MAX_RESERVATION_SENDERS` and `MAX_RESERVATION_PLAN_BYTES`.
- Specify client-facing UX expectations for “included but ignored” messages (explorers, indexers, RPCs).
- Produce shared cross-implementation test vectors/fuzzing targets for reservation sessions and Strict Sender Partitioning.
- Assign the activating network version and upgrade epoch, including coordination with [FIP-0111](./fip-0111.md) (EIP-7702) where relevant.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
