---
fip: "nnnn"
title: Filecoin EVM
author: Raúl Kripalani (@raulk), Steven Allen (@stebalien), Dimitris Vyzovitis (@vyzo), Melanie Riise (@mriise)
discussions-to: 
status: Draft
type: FRC
created: 2022-10-15 
---

> Work in progress.

## Simple Summary

A non-normative document providing an architectural overview of how Ethereum
Virtual Machine compatibility works in the Filecoin network.

## Abstract

EVM compatibility in Filecoin involves many moving parts, defined across several
technical FIPs. It is not immediately obvious how those FIPs interconnect as a
cohesive unit to manifest the desired outcome: the ability to deploy and run EVM
smart contracts.

This FRC is a non-normative architectural overview describing the solution as
whole. It serves as an entrypoint and companion to the respective normative
FIPs. It also provides straightforward guidance to various ecosystem
stakeholders on how to adapt to handle EVM smart contract interactions.

## Change Motivation

## Specification

### The Filecoin EVM (FEVM) runtime

**Built-in actor.** The FEVM runtime is a built-in actor, just like all actors
that exist today on the Filecoin chain as of nv16 and nv17. Its Wasm bytecode is
installed on-chain at the corresponding network upgrade, and the bytecode is
linked into the System actor via its CodeCID via the built-in actors manifest,
and can be queried by reading the system actor's state.

**Prototype actor.** It is a prototype actor and not a singleton actor. In other
words, it is like the payment channel, multisig, and miner actors (prototype
actors), and unlike the miner, storage power, and verified registry actors
(singleton actors). The FEVM runtime can be instantiated by users, and that's
precisely how EVM smart contracts are deployed.

**Contents.** The FEVM runtime actor is the environment that _hosts_ and
_executes_ EVM bytecode. To that end, it embeds an EVM interpreter, and contains
the integration logic with the Filecoin environment, chain, and virtual machine.

**EVM interpreter.** The embedded EVM interpreter supports all EVM opcodes
available Ethereum Paris fork. Historical baggage associated with past Ethereum
forks has been eliminated (e.g. activation of specific opcodes at specific
upgrades, support for different transaction types, etc.) It merely supports
EIP-1559 style transactions, specifying a gas fee cap and a gas premium.

**Constructor.** To deploy a smart contract, users must call the constructor of
the FEVM runtime actor, supplying the init EVM bytecode as a constructor
argument. The constructor will run the initcode and save the resulting bytecode
in the actor's state, along with its storage root (see below).

**Precompiles.** All Ethereum precompiles available in the Paris fork are
supported. Some precompiles execute in Wasm space, while others escape to FVM
kernel space. We may add further precompiles to invoke Filecoin-specific
features, such as acquiring randomness, or validating proofs.

**Native token.** The native token of the FEVM runtime is Filecoin. There is no
built-in concept of wrapped Ether, although developers may deploy such tokens in
user space.

**Gas accounting.** Support for Ethereum gas has been dropped entirely. Gas is
metered according to Filecoin rules, and is paid exclusively in filecoin.
Execution halt is determined by Filecoin's gas model.

**Gas costs.** Unlike in Ethereum, EVM opcodes do not have formally-specified
gas costs. EVM is interpreted and therefore dependent on Wasm instructions,
syscalls, and extern calls. Furthermore, the FEVM runtime will evolve over time,
so will its Wasm bytecode, resulting in changes to gas costs. For this reason,
users are advised against hardcoding assumptions about gas.

**Gas in opcodes.** Gas related opcodes such as `GAS` and `GASLIMIT` report
Filecoin gas. The gas limit supplied to `CALL` opcodes is also Filecoin gas. We
do recognize this might require minor adaptation in contracts using literal gas
values, e.g. 21000 gas for bare value transfers.

**Storage.** EVM storage (u256 => u256 map) is backed by a Filecoin HAMT with
special optimizations to be more mechanically sympathetic to EVM read and write
patterns. SLOAD and SSTORE opcodes map to reads and writes, respectively, on
this HAMT, and ultimately to `ipld` syscalls.

**Addresses.** The FEVM runtime supports two types of addresses: f0 addresses
(ID addresses) and f410f addresses (foreign Ethereum addresses; see Addressing
below). In order to distinguish between these two, f0 addresses adhere to a
mask. The mask is `0xff00....<id address>`, with all middle padding and unused
uvarint bytes set to 0.

### Addressing

Ethereum uses 160-bit (20-byte) addresses. Addresses are the keccak-256 hash of
the public key of an account, truncated to preserve the 20 rightmost bytes.
Solidity and the [Contract ABI
spec](https://docs.soliditylang.org/en/v0.5.3/abi-spec.html) represent addresses
with the `address` type, equivalent to `uint160`. Even though EVM words are 32
bytes long, it's important to preserve the 20-byte semantics for compatibility
with Ethereum tools that produce and use addresses.

In Filecoin, there are four recognized address classes, with structure: `class
(1 byte) || payload (n bytes)`. The address classes are as follows:

| Class | Desc                              | Actor types   | Payload width | Total width | Payload value                                          | Usage                                                                                | Universal? | Stable? |
| ----- | --------------------------------- | ------------- | ------------- | ----------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------ | ---------- | ------- |
| 0     | ID address                        | Universal     | 1-9 bytes     | 2-10 bytes  | [multiformats-flavored uvarint64] ordinal              | Internal, compact representation in state tree; unsafe to use externally until final | Y          | N       |
| 1     | secp256k1 address                 | Only accounts | 20 bytes      | 21 bytes    | blake2b-160 hash of secp256k1 pubkey                   | Externally, to refer to an account actor with its pubkey                             | N          | Y       |
| 2     | aliased universal actor address   | Non-accounts  | 20 bytes      | 21 bytes    | protocol-derived from relevant identification material | Externally and internally to refer to any actor                                      | N          | Y       |
| 3     | bls pubkey (account actor)        | Only accounts | 48 bytes      | 49 bytes    | inlined bls public key                                 | Externally, to refer to an account actor with its pubkey                             | N          | Y       |

**f4 address class.** With FEVM, we introduce an [extensible address class `4`]
that delegates address assignment to an address manager actor. This allows us to
support foreign addressing schemes in Filecoin through namespacing. f4 addresses
follow this format (in textual form):

```
f4<id address in decimal>f<subaddress in base32>
```

Explorers must recognize this new address class, showing users how it
decomposes into its parts.

**EAM.** We introduce the Ethereum Address Manager (EAM) actor as a built-in
singleton actor sitting at ID address `32`. The EAM supports assigning
Ethereum-equivalent addresses to externally owned accounts (backed by secp256k1
keys), deploying contracts from an EOA, and deploying contracts via `CREATE` and
`CREATE2` opcodes. Explorers must recognize the 

**Ethereum address translation.** An Ethereum address `0x1234..ff` translates to
f4 address `f410f<1234..ff as base32>`. We expect explorers to:

1. recognize Ethereum addresses and resolve them to f4 addresses
2. show the corresponding checksummed Ethereum address for an f410f address.

## Ethereum externally-owned accounts (EOA)

### Counterfactual interactions

### Deploying an EVM smart contract

FEVM smart contracts receive three addresses:
- an f0 address (ID address)
- an f2 address (actor address, because they are actors)
- an f410f address (Ethereum address, acquired by instantiating the smart
  contract through the EAM)

### Invoking smart contracts

### Logs and events

### Ethereum wallets

### Ethereum JSON-RPC API

## Design Rationale

## Backwards Compatibility

## Test Cases

## Security Considerations

## Incentive Considerations

## Product Considerations

## Implementation

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).

[multiformats-flavored uvarint64]: https://github.com/multiformats/unsigned-varint
[extensible address class `4`]: https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0048.md