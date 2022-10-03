---
fip: <to be assigned>
title: F4 Address Class
author:  Steven Allen <stebalien@protocol.ai>, Melanie Riise <melanie.riise@protocol.ai>, Rául Kripalani <raul@protocol.ai>
discussions-to: https://github.com/filecoin-project/FIPs/discussions/473
status: Draft
type: Technical
category: Core
created: 2022-10-02
spec-sections:
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->

Support new actor addressing schemes and interactions with addresses that do not yet exist on-chain by introducing a new address type where sub-namespaces within this new address type can be managed by user-deployed actors called "address managers".

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->

This FIP adds a new extensible address class (`f4`) where an address management actor will be able to create new actors with `f4` addresses under a specific `f4` address prefix, in addition to the `f2` address assigned today. This will allow Filecoin to support the native addressing schemes of foreign runtimes like the EVM and support interactions (both actually and counterfactually) with addresses that do not yet exist on-chain..

This FIP achieves this by:

1. Introducing a new extensible address class (`f4`) to support new addressing schemes.
2. Introducing a special "embryo" actor type to hold funds sent to an address before code is deployed to that address to support interactions with addresses that to not yet exist.
3. Introducing a new `Exec4` method on the `Init` actor to create actors with addresses within this address class.

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->

The FVM aims to be a hypervisor with first-class support for runtimes like the EVM. To achieve full compatibility, the FVM must support:

1. The addressing schemes used by said runtimes (e.g., Ethereum addressing) as said runtimes often rely on particular address formats and derivation logic.
    - EVM tooling expects Ethereum addresses.
    - Tools that interact with EVM actors counterfactually expect the addresses of said actors to be derived via the precise method specified in the CREATE2 opcode.
    - Tools like, e.g., Metamask will derive Ethereum addresses for wallets, not Filecoin addresses, and converting between the two is impossible due to the hash functions involved.
2. Interactions with addresses that do not yet exist on-chain.

This FIP supersedes [Predictable actor address generation for wallet contracts, state channels (aka CREATE2)](https://github.com/filecoin-project/FIPs/discussions/379).

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

This FIP adds a new extensible address class (`f4`) where an address management actor will be able to create new actors with `f4` addresses under a specific `f4` address prefix, in addition to the `f2` address assigned today.

For now, this FIP proposes that address management actors be limited to built-in "singleton" actors, but expect users to be able to deploy their own address management actors in the future.

There are three key parts to the design:

1. The introduction of the new `f4` address class. Tooling will need to be adapted to parse and handle said addresses.
2. The introduction of embryo actors.
3. A new `Exec4` method on the init actor to support the `f4` address class.

**Parameters**

| Parameter              | Value | Rational                      |
|------------------------|-------|-------------------------------|
| `MAX_SUBADDRESS_BYTES` | 54    | fits in 64 bytes when encoded |

### The f4 Address Class

An address manager will own `f4` addresses (in the binary representation) starting with the leb128-encoded actor ID and followed by an arbitrary (chosen by the address management actor, up to `MAX_SUBADDRESS_BYTES` bytes) sub-address: `[0x4 (f4 address class)] || {leb128(actor-id)} || {sub-address}`.

In text, this address will be formatted as `f4{decimal(actor-id)}-{base32(sub-address || checksum)}` where `checksum` is the blake2b-32 (32bit/4byte blake2b) hash of the address in its binary representation (protocol included). This is the same checksumming approach used in the textual representation of f1-f3 addresses.

For example, an address management actor at `f010` will be able to assign addresses starting with `f410-` in text or `[4, 10, ...]` in binary. [^1]

**NOTE**: The textual format defined here is the *universal* textual format for `f4` addresses. We expect that chain explorers and client implementations will understand specific well-known address types and will format these addresses according to their "native" representation. For example, tooling should transparently convert Ethereum addresses in the `0x...` to and from the equivalent `f4` address. [^2]

### Embryo Actors

To support interactions with addresses that do not yet exist on-chain, the FVM must support sending funds to an address before an actor is deployed there. It's already possible to automatically create an account (f1 or f3) on send, but it's not possible to do the same for arbitrary actors.

On `send` to an unassigned `f4` address `f4{actor-id}{subaddress}`, the FVM will:

1. Validate that an actor with ID `actor-id` exists.
2.  Create a new "embryo actor" with a placeholder code CID to hold the received funds, assigning the `f4` address to that new actor.

Sending to an unassigned `f2` address will not be supported as `f2` addresses are designed to protect against reorgs and aren't designed to for this use-case (see [`f2` versus `f4`](#f2-versus-f4)).

Specifically, the FVM will:

1. Create a new embryo actor with a well-known embryo code CID and a zero nonce.
5. Deposited the funds in said actor.
6. Assign the target `f4` address to that actor (but don't yet assign an `f2` address).

### Exec4

To support the `f4` address class, this FIP adds an `Exec4` method to the `Init` actor to create new actors with an `f4` address (in addition to an `f2` address) under the *caller's* `f4` sub-namespace. The `f4` to actor-id to address mappings are stored alongside the `f1-f3` to actor-id address mappings in the `Init` actor's `address_map` requiring no additional state or state migrations.

Specifically, given the parameters:

```rust
struct Exec4Params {
    subaddress: Bytes, // limited to MAX_SUBADDRESS_BYTES
    code: Cid,
    constructor_params: Bytes,
}
```

`Exec4` will:

1. Compute the `f4` address as `4{leb128(caller-actor-id)}{subaddress}` where `{caller-actor-id}` is the actor ID of the actor invoking the init actor and `{subaddress}` is the sub-address specified in the `Exec4` parameters.
2. If an actor exists at that address:
    1. If it's an embryo, it will be overwritten.
    2. Otherwise, abort. `f4` addresses MUST NOT be reassigned once code has been deployed.
7. If an actor does not exist at that address, create a new actor (with a new actor ID) and assign the `f4` address to that actor.
8. Assign an `f2` (stable) address to the actor (the `f4` address may not be reorg stable).
9. Set the actor's code CID to `code` and invoke the actor's constructor.
10. Finally, `Exec4` will return the actor's ID and `f2` (stable) address. It will not return the `f4` address as the caller should be able to compute that locally.

**NOTE**: For now, `Exec4` will be restricted to _singleton_ actors (actors in the f00-f099 address range). Once users are able to deploy custom WebAssembly actors, this restriction should be relaxed (in a future FIP).

## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->

This FIP meets the design goals by:

- Supporting interactions with addresses that do not yet exist on-chain by allowing user-defined address management actors to assign addresses based on arbitrary properties.
- Supporting arbitrary addressing schemes (e.g., Ethereum addressing) by carving out address "namespaces".

In this section, we discuss some of the tradeoffs and alternatives considered.

### Init Actor State

As this FIP stores f4 addresses alongside f2 addresses in the same map, actors with f4 addresses will have _two_ entries in this map. We could, alternatively, put these addresses in a separate map but the current FIP lets us avoid changing the Init actor's state layout (for now).

### Hashing v. Prefixing

An alternative to prefixing (`f4{actor-id}-{subaddress}`) would be to define a namespace via a hash function. I.e., an actor would own `f4{hash(actor-id || subaddress)}`.

The primary benefit of this approach is that addresses have a predictable size. The primary *downside* is that:

- This is *slightly* more expensive to compute and EVM actors will have to convert Ethereum addresses into `f4` addresses on-chain.
- It's not reversible. This makes tooling and debugging significantly more painful.

### Control Inversion

One drawback with the current "factory" approach is that the newly created actor's constructor will see the factory (the address manager) as the sender, not the *real* sender. An alternative would be to invert the flow and have:

1. The "creating" actor call `Exec4` on the init actor with the address of the address manager.
2. Have the init actor call some `GenerateAddress` method on the address manager.

However, the current approach gives the address manager more control as it effectively gets to act as a user-defined "init" actor, sitting between the user and the real init actor.

### Bind4

The original proposal included a `Bind4` method on the `Init` actor to bind an `f4` address to an _existing_ actor (allowing actors to have more than one `f4` address). This would have allowed one to, for example:

1. Receive funds at some `f1` address (A) (e.g., from some existing Filecoin user).
2. Receive funds at the equivalent Ethereum `f4` address (B) (e.g., from some existing Metamask user).
3. Later deploy a Filecoin account to A, then `Bind4` B to said account, merging them into a single account.

Unfortunately, by step 3, both accounts would have been assigned separate `f0` addresses. Merging these accounts would have required either removing or re-assigning one of the `f0` addresses which would have violated existing assumptions on how ID addresses behave.

### Textual Format

The *universal* textual format of f4 addresses, `f4{decimal(actor-id)}-{base32(sub-address || checksum)}`, is a trade-off between verbosity, readability, and determinism.

- We split the actor-assigned "sub-address" with a dash for easy readability. We could have encoded this address as `f4{base32(leb-encoded-actor-id || sub-address || checksum)}`, but that would have been impossible for a human to read.
- We chose to encode the actor-id as a decimal to mirror `f0`.
- We chose to `base32` encode the sub-address because it may be long. The main downside is that converting to/from an Ethereum address may require re-encoding from hex to base32 (but this point is somewhat moot given the checksum anyways).
- We chose to require a specific checksum format and to not support multiple bases (e.g., multibase) in this address format to ensure that two `f4` addresses are equivalent if and only if they have the same textual representation. This unfortunately means that converting to and from external addressing schemes like Ethereum/EVM addresses cannot be done by hand.

### F2 Versus F4

This FIP makes a few interesting decisions with respect to `f2` addresses:

1. While it allows sending to unassigned `f4` addresses, it does not allow the same for `f2` addresses.
2. It assigns _both_ an `f2` and an `f4` address to new actors.
4. It does not assign an `f2` address until the actor actually _exists_ on-chain.

The key distinction is that `f2` addresses are designed to stable and that `f4` addresses are designed to be "user-programmable".

- An `f2` address allows a user to create a chain of messages where a later message refers to an actor created in an earlier message. An `f2` address refers to _the_ actor created by a _specific_ message.
- An `f4` address allows an actor (an address manager) to "control" an address-space. This allows the address manager to implement foreign addressing schemes (e.g., Ethereum's) and allows users to refer to addresses that _could_ contain an actor with a set of properties enforced by an address manager.

Circling back to the design decisions:

1. A send to an unassigned `f2` address must fail because that means a prior message in a message chain failed for some reason and didn't create the expected actor. If the send were to succeed and create an embryo (as happens with an unassigned `f4` address) the funds would be lost forever.
2. Assigning an `f2` address along with an `f4` address allows a message chain to safely refer to an actor deployed in a prior message even if a prior message in the chain _fails_ because, e.g., someone else successfully deployed an actor at the target `f4` address.
3. We delay assigning an `f2` address until an actor is deployed for the same reason.


## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

This FIP aims to minimize backwards incompatible changes to the chain state and will not require a state migration. However, it will still introduce new features and behavior changes:

- The address map in the init actor may now map multiple addresses to the same actor. Clients (especially dashboards) that aggregate/parse chain state will need to handle this case.
- The code CID of a deployed actor may now change from the "embryo" code CID to an actual code CID. Implementations that cache code CIDs will need to handle this case.
- This FIP introduces a new address class (`f4`). Implementations of the Filecoin addressing standard will need to handle parsing of this new address class.
- Method 0 sends may now invoke the constructor of an _arbitrary_ actor, which may be costly relative to invoking the constructor of the account actor. This could break assumptions that sends are "basically free" in terms of gas and clients will have to handle this case appropriately.

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->
### Address Format

TODO: ...

### Behavior

TODO: Test vectors will be extracted from the reference implementation once completed.

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->

### Address Stability

Unlike `f1-f3` addresses, `f4` addresses may not be stable across reorgs (depending on the address management actor). This could be used to confuse users who may be conditioned to assume "short addresses are unstable, long addresses are 'secure'".

The only real solution here is to educate users that "`f4` means user defined".

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->

### Actor Churn

By relying on ID addresses to distinguish between different `f4` address sub-namespaces, this FIP may encourage ID address "churn" by those seeking "vanity" addresses.

However, we have mitigated one aspect of this: `f4` addresses may not be used to _reward_ ID address churn  by deploying to an `f4` address managed by a non-existent address management actor.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->

There are two main product goals in this FIP:

1. Support Ethereum tooling and the EVM. This will allow users to deploy user-defined actors on the Filecoin network without having to create an entirely new ecosystem, tooling, etc.
2. Support interactions with addresses that do not yet exist on-chain (required for many counterfactual interactions).

### Ethereum Support

In a future FIP, we will propose a Ethereum Address Manager (EAM) actor, likely at the address `f032`. This actor will be responsible for assigning all "Ethereum-style" addresses on the Filecoin network (EVM actor addresses and Ethereum account addresses).

#### Ethereum Addresses

With this FIP, the full Ethereum address would be preserved inside the `f432-` address sub-namespace making it easy to:

1. Recognize Ethereum addresses (likely displaying them in their usual `0x...` format).
2. Convert back and forth between the Ethereum address format (`0x...`) and the Filecoin (`f4...`) format.

#### CREATE

To support `CREATE1`, the  EAM will export a `Create` method taking:

```rust
struct CreateParams {
    initcode: Bytes,
}
```

It will then create an address per the Ethereum yellowpaper and call `Init.Exec4` with:

```rust
Exec4Params {
    address: b"<computed address>",
    code: EVM_ACTOR_CID,
    params: initcode,
}
```

#### CREATE2

To support `CREATE2`, the  EAM will export a `Create2` method taking:

```rust
struct Create2Params {
    initcode: Bytes,
    salt: [u8; 32],
}
```

It will then create an address per [EIP-1014](https://eips.ethereum.org/EIPS/eip-1014) and call `Init.Exec4` with:

```rust
Exec4Params {
    address: b"<computed address>",
    code: EVM_ACTOR_CID,
    params: initcode,
}
```

#### Abstract Accounts

This highly depends on how code will be deployed to an [abstract account](https://github.com/filecoin-project/FIPs/discussions/388). It will likely involve a `CreateAccount` method on the ETH Address Manager, and will also likely involve the ability to automatically deploy an abstract account to an embryo actor in some cases.

### Interactions With Unassigned Addresses

`f4` addresses support interactions addresses that do not yet exist on-chain by delegating address assignment (within some `f4` prefix) to a (potentially user-defined) address management actor. These interactions may be _actual_ (a user may send to an address that has not yet been defined) or counterfactual (a user may specify such an address in a payment channel voucher, but never actually _create_ an actor at said address).

For example, let's say we needed to be able to refer to an actor that *could* exist with some specific code CID and some specific constructor parameters (effectively, `CREATE2`).

To achieve this, we'd deploy an address manager actor with a single `Exec(code_cid, constructor_params)` method (i.e., identical to `Init.Exec`). Internally, this function would call `Init.Exec4(subaddress=hash(code_cid || constructor_params, code=code_cid, params=constructor_params).` In practice, this actor will likely already exist on-chain from day one.

With this address manager actor, we can refer to an actor that *might* exist constructed with some `code` and `params` as `f4{decimal(address-management-actor)}{hash(code || params)}`.

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->

TODO: IN PROGRESS

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).

[^1]: Where address manager ID address is `f01111` and the sub-address is `0xeff924032365F51a36541efA24217bFc5B85bc6B` the resulting textual format would be `f41111-574siazdmx2runsud35ciil37rnylpdl`

[^2]: Example of a (not being proposed here) address manager (`f01112`) that manages a namespace of raw ascii addresses (`hello world` for example), the standard format would be `f41112-nbswy3dpeb3w64tmmqqq` though clients might recognize the address manager and display it as text: `f41112-hello world`
