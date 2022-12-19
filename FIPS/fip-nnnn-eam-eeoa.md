---
fip: <to be assigned>
title: Supporting Ethereum addresses and transactions
author: Raúl Kripalani (@raulk), Steven Allen (@stebalien)
discussions-to: <URL>
status: Draft
type: Technical Core
category: Core
created: 2022-12-02
spec-sections:
requires: N/A
replaces: N/A
---

# Supporting Ethereum addresses and transactions

## Simple Summary

We introduce two actors: **Ethereum Address Manager (EAM)** and **Ethereum Externally-Owned Account (EEOA)** actors.
Both actors are necessary to attain compatibility with Ethereum tooling.
We also introduce **Ethereum addresses** atop the f4 address class, and a new **Delegated signature type**.

## Abstract

The **Ethereum Address Manager (EAM)** actor manages namespace `10` within the `f4` address class as defined in [FIP-0048].
This namespace hosts **Ethereum addresses** in Filecoin.
These addresses begin with `f410` in textual form.
EVM smart contracts deployed through the EAM acquire an `f410` address.

The **Ethereum Externally Owned Account (EEOA)** actor represents Ethereum identities backed by secp256k1 keys.
It enables authenticating native Ethereum messages sent from Ethereum wallets, within the Filecoin protocol.
These messages are converted to Filecoin messages carrying a **Delegated signature type**.
While baked into the protocol at this stage, these mechanisms are conceived as an extension point to subsequently transition into future fully-fledged Account Abstraction (AA).

## Change Motivation

Foreign runtimes, like the EVM runtime introduced in FIP-TODO, often make assumptions about addressing schemes.
Programs deployed on those runtimes (e.g. EVM smart contracts) also inherit those assumptions.
Such assumptions come in the form of:
- data types expectations
- cryptographic expectations (e.g. addresses derived from public keys)
- address predictability expectations (e.g. upon contract deployment)

Fulfilling these expectations involves making Filecoin aware of Ethereum addresses, in a way that does not bake that awareness in the core protocol.
This is achieved by anchoring **Ethereum addresses** under the newly-introduced `f4` delegated address class.

Furthermore, supporting foreign runtimes in Filecoin is hardly useful if the tools and libraries built for those runtimes were unable to interact with Filecoin without changes.
Such handicap would prevent reuse and retargeting.
Supporting the submission and validation of transactions issued from wallets native to the original ecosystem is a must.
This capability is delivered by the **Ethereum Externally Owned Account (EEOA)** and the **Delegated signature type**, as a stepping stone towards full Account Abstraction (AA).

## Specification

### Ethereum addressing (`f410` addresses)

We allocate namespace `10` (decimal) under the `f4` address class defined in [FIP-0048] to represent Ethereum addresses.
The address payload is the literal Ethereum address in binary form.

```
# Ethereum address in Filecoin
0x04 || 0x10 || <binary Ethereum address>
```

### Ethereum Address Manager (EAM)

We introduce the **Ethereum Address Manager (EAM) actor** as a singleton built-in actor, sitting at ID address `10`.
This actor fulfills two purposes:

1. It manages the f4 address class namespace under its ID address (i.e. f410), assigning Ethereum-compatible addresses under it.
2. It acts like a factory for EVM smart contracts, respecting Ethereum rules and semantics for the `CREATE` and `CREATE2` mechanisms for address generation.

#### Installation and wiring

During migration:

1. The Wasm bytecode of the EAM (referred by its CodeCID) is linked under the System actor's registry under the key `"eam"`.
2. A single copy of the EAM is deployed as a singleton actor under ID address `f010`.

The Init actor statically recognizes the EAM as an _authorized_ delegated address manager, and permits calls to its `InitActor#Exec4` method originating in it.
Address managers like the EAM use the `InitActor#Exec4` method to deploy new actors with delegated addresses under the namespace matching their actor ID (`10` in this case).

#### EVM smart contract deployment via the EAM

The EAM offers two Filecoin methods `Create` and `Create2`, equivalent to their Ethereum counterparts.
In Ethereum, `CREATE` and `CREATE2` differ in their address generation rules:

- `CREATE` uses the protocol-provided nonce to derive the contract's address, and is thus non-deterministic.
- `CREATE2` takes an explicit user-provided salt to compute a deterministic address. It is suitable for counterfactual deployments.

EVM smart contracts are deployed to the Filecoin chain as follows:

1. A contract deployment message is directed to the `Create` or `Create2` methods of the EAM.
2. The EAM computes the `f410` address as per the rules of the invoked method.
   The resulting f410 address is semantically equivalent to the address Ethereum would've generated for the same inputs, thus retaining tool compatibility.
2. The EAM invokes the Init actor's `Exec4` method (see [FIP-0048]), supplying:
      - The CodeCID of the EVM runtime actor.
      - The EVM runtime actor's constructor parameters, concretely the EVM init code and original creator address.
      - The assigned f410 address.

#### State

None.

#### Actor interface (methods)

##### Method number `1` (`Constructor`)

The Constructor asserts that:

1. It is being called by the System actor (f00).
2. It has been deployed on address `f10`.

These checks prevent instantiation by users.

_Input parameters_

None.

_Return value_

None.

_Errors_

- `USR_FORBIDDEN` (18) when attempts to instantiate this actor are made, or if deployed at an address other than f010.

##### Method number `2` (`Create`)

Deploys a smart contract taking EVM init bytecode and accepting a nonce from the user.
The Ethereum address (and therefore the f410 address) is calculated from these parameters.

The `Create` method is to be used in two cases:

1. When an EEOA deploys an EVM smart contract by submitting a native Ethereum message.
2. When a smart contract (running within the EVM runtime actor) calls the `CREATE` opcode.

Note that this differs from Ethereum in that we take a user-provided nonce as a parameter.
This is necessary for the EAM to learn the nonce of a contract, when the `CREATE` opcode is used.
Technically, this allows an EEOA to deploy a contract with an arbitrary nonce, potentially using nonces in a non-contiguous manner.

_Input parameters_

```rust
// DAG-CBOR tuple encoded.
pub struct CreateParams {
    /// EVM init code.
    pub initcode: Vec<u8>,
    /// Nonce with which to create this smart contract.
    pub nonce: u64,
}
```

_Return value_

```rust
// DAG-CBOR tuple encoded.
pub struct Return {
    /// The ID of the EVM runtime actor that was constructed.
    pub actor_id: ActorID,
    /// Its f2 address.
    pub robust_address: Address,
    /// Its Ethereum address, translatable to an f410 address.
    pub eth_address: [u8; 20],
}
```

_Errors_

TODO.

##### Method number `3` (`Create2`)

The deployment procedure is the same as `Create`, but this method takes a user-provided salt.
A deterministic Ethereum address (and therefore the f410 address) is calculated from these parameters.

`Create2` only used when a smart contract (running within the EVM runtime actor) calls the `CREATE2` opcode.

_Input parameters_

```rust
pub struct Create2Params {
    /// EVM init code.
    pub initcode: Vec<u8>,
    /// User provided salt.
    pub salt: [u8; 32],
}
```

_Return value_

Same as [`Create`](#method-number-1-create).

### Delegated signature type

We introduce a new `Delegated` signature type for Filecoin messages with serialized value `3`.
Delegated signatures are intended to be used in combination with abstract account senders, once Account Abstraction (AA) is fully realisd.
Delegated signatures are opaque to the protocol, and will eventually be validated by the actor logic of the abstract account actor.

However, during this transitory period, Delegated signatures are assumed to be secp256k1 signatures over the RLP representation of the message.

### Ethereum Externally-Owned Account (EEOA)

We introduce the **Ethereum Externally-Owned Account (EEOA) actor**, a non-singleton actor representing an external Ethereum identity backed by a secp256k1 key.

#### Installation and wiring

During migration, the Wasm bytecode of the EEOA (referred by its CodeCID) is linked under the System actor's registry under the key `"ethaccount"`.

#### Instantiation via promotion

At this stage, the creation of instances of this actor is a privileged action.
The FVM, and only the FVM, can instantiate the EEOA through a special pathway.

The FVM instantiates this actor when an Embryo actor with an `f410` address sends its first Delegated-signature message.
The CodeCID of the Embryo actor is set to that of the EEOA, and the EEOA acts like a regular sender insofar the FVM is concerned.

TODO: message failure, OOG, nonce.

#### Signature

TODO.

## Design Rationale

> TODO:
> - Flat vs nested contract deployment model.
> - Deployment ethaccount.

## Backwards Compatibility

TODO.

## Test Cases

## Security Considerations

TODO.

## Incentive Considerations

TODO.

## Product Considerations

TODO.

## Implementation

TODO.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).


[`filecoin-project/builtin-actors`]: https://github.com/filecoin-project/builtin-actors
[FRC42 calling convention]: https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0042.md
[FIP-0048]: https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0048.md
[Contract ABI spec]: https://docs.soliditylang.org/en/v0.5.3/abi-spec.html
[Ethereum Paris hard fork]: https://github.com/ethereum/execution-specs/blob/master/network-upgrades/mainnet-upgrades/paris.md
[FIP-0049 (Actor events)]: https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0049.md