---
fip: <to be assigned>
title: Ethereum Address Manager (EAM) and Ethereum Externally Owned Account (EEOA)
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

# Ethereum Address Manager (EAM) and Ethereum Externally Owned Account (EEOA)

## Simple Summary

TODO.

## Abstract

TODO.

## Change Motivation

TODO.


## Specification: Ethereum Address Manager (EAM)

We introduce the **Ethereum Address Manager (EAM) actor** as a singleton
built-in actor sitting at ID address `10`. This actor fulfills two purposes:

1. It manages the f4 address class namespace under its ID address (i.e. f410),
   assigning Ethereum-compatible addresses under it.
2. It acts as the entrypoint for deployment of EVM smart contracts, respecting
   Ethereum rules and semantics.

For the latter, this actor offers two Filecoin methods `Create` and `Create2`,
equivalent to their Ethereum counterparts. In Ethereum, `CREATE` and `CREATE2`
differ in their address generation rules:

- `CREATE` uses the protocol-provided nonce to derive the contract's address,
  and is thus non-deterministic.
- `CREATE2` takes an explicit user-provided salt to compute a deterministic
  address. It is suitable for counterfactual deployments.

### Deployment

The EAM is deployed as a singleton actor under ID address `10`. The deployment
happens during the state migration where this FIP goes live.

The EAM is allow-listed in the Init Actor as a caller of its `Exec4` method,
specified in FIP-0048.

### Procedure

The procedure to deploy EVM smart contracts to the Filecoin chain is as follows:

1. The contract deployment message enters the Ethereum Address Manager (EAM)
   through the `Create` or `Create2` method. 
2. The EAM computes an `f410` address according to the heuristics of the invoked
   method (see below). The resulting f410 address is semantically equivalent to
   the one Ethereum would've generated for the same inputs, thus retaining tool
   compatibility.
2. The EAM invokes the Init actor's `Exec4` method (see [FIP-0048 (f4 Address
   Class)]), supplying the CodeCID of the EVM runtime actor, the constructor
   parameters (EVM init code and original creator address), and the assigned
   f410 address.

### State

None.

### Actor interface (methods)

#### Method number `1` (`Create`)

Deploys a smart contract taking EVM init bytecode and accepting a nonce from the
user. Refer to [Procedure](#procedure) for a description of the deployment
procedure.

The `create` method is used in two cases:

1. When an EEOA actor deploys a smart contract by submitting a native Ethereum
   transaction containing initcode through the Ethereum JSON-RPC API endpoint.
   The endpoint detects the deployment operation, and translates the Ethereum
   transaction to an `EAM#Create` Filecoin message.
2. When an EVM smart contract calls the `CREATE` opcode.

Note that this differs from Ethereum in that we take a user-provided nonce as a
parameter. This is necessary so that the EVM runtime actor can supply the
contract's nonce when handling `CREATE` to the EAM. This is a mild departure
from Ethereum's behavior as it allows an EEOA to deploy a contract with an
arbitrary nonce. No safety violations are possible because the system guarantees
that we don't deploy over an existing actor anyway (those constraints are
enforced by the init actor and the FVM itself).

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

#### Method number `2` (`Create2`)

Deploys a smart contract taking EVM init bytecode and accepting a user-provided
salt to generate a deterministic Ethereum address (translatable to an f410
address). Refer to [Procedure](#procedure) for a description of the deployment
procedure.

`Create2` is used in a single case: to handle the `CREATE2` opcode while
executing EVM bytecode within the EVM runtime actor.

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

## Specification: Ethereum Externally Owned Account (EEOA)

TODO (@aayush).

## Design Rationale

> TODO:
> - Flat vs nested contract deployment model.
> - ...

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

## Appendix A: Notable differences between FEVM and EVM for smart contract developers

TODO.

## Appendix B: Upgrades

TODO.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).


[`filecoin-project/builtin-actors`]: https://github.com/filecoin-project/builtin-actors
[FRC42 calling convention]: https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0042.md
[FIP-0048 (f4 Address Class)]: https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0048.md
[Contract ABI spec]: https://docs.soliditylang.org/en/v0.5.3/abi-spec.html
[Ethereum Paris hard fork]: https://github.com/ethereum/execution-specs/blob/master/network-upgrades/mainnet-upgrades/paris.md
[FIP-0049 (Actor events)]: https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0049.md