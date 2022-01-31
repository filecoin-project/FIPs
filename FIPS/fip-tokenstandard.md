---
fip: <to be assigned>
title: Fungible token standard
author: Alex North (@anorth)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/277
status: Draft
type: Technical
category: Interface
created: 2022-01-31 
---

## Simple Summary
A standard interface for tokens. ERC-20 for Filecoin.

## Abstract
This proposal provides a standard API for the implementation of fungible tokens within smart contracts. 
This API provides basic functionality to transfer tokens, 
as well as allow tokens to be approved so they can be spent by another on-chain third party.

This proposal is an adaptation of Ethereum's [ERC-20](https://eips.ethereum.org/EIPS/eip-20) [^erc20] for the Filecoin VM.

## Change Motivation
A standard interface allows any tokens on Filecoin to be re-used by other applications: from wallets to decentralized exchanges.

Following the ERC-20 standard closely simplifies the translation and integration of applications from
Ethereum and other blockchains into Filecoin.
This is especially relevant if an FVM EVM compatibility layer is to support tight integration between
ported EVM contracts and native FVM actors.

## Specification

### Methods

**Notes**
- The following uses a pseudocode syntax to describe method parameter and return types.
The ABI values are CBOR-encoded primitives or tuples.
Types such as `address` are a standardised interpretation of a CBOR byte array.
- Callers MUST handle false from returns (bool success). Callers MUST NOT assume that false is never returned!

#### Name
Returns the name of the token, e.g. `"MyToken"`.

OPTIONAL - This method can be used to improve usability, 
but interfaces and other contracts MUST NOT expect these values to be present.

**Method name**

`name`

**Parameter**

_empty_

**Return**

`symbol: string`

#### Symbol
Returns the symbol of the token, e.g. `"FIL"`.

OPTIONAL - This method can be used to improve usability, 
but interfaces and other contracts MUST NOT expect these values to be present.

**Method name**

`symbol`

**Parameter**

_empty_

**Return**

`symbol: string`

#### Decimals
Returns the number of decimals the token uses - 
e.g. 8, means to divide the token amount by 100000000 to get its user representation.

OPTIONAL - This method can be used to improve usability, 
but interfaces and other contracts MUST NOT expect these values to be present.

**Method name**

`symbol`

**Parameter**

_empty_

**Return**

`decimals: uint8`

#### TotalSupply
Returns the total token supply.

**Method name**

`totalSupply`

**Parameter**

_empty_

**Return**

`supply: uint64`

#### BalanceOf
Returns the account balance of account with an address.

This method MUST succeed with a result of zero if the address has no tokens,
including if it has never owned tokens or has transferred all tokens it once owned to another account.

**Method name**

`balanceOf`

**Parameter**

`address`

**Return**

`balance: uint64`

#### Transfer
Transfers `value` amount of tokens to address `to`. 
The function SHOULD throw if the message caller's account balance does not have enough tokens to spend.

Notes:
1. Transfers of 0 values MUST be treated as normal transfers.
2. Transfers to the caller's own address MUST be treated as normal transfers.

**Method name**

`transfer`

**Parameter**

`{to: address, value: uint64}`

**Return**

`success: bool`

#### TransferFrom
Transfers `value` amount of tokens from address `from` to address `to`.

The `transferFrom` method is used for a withdraw workflow, allowing contracts to transfer tokens on your behalf.
This can be used for example to allow a contract to transfer tokens on your behalf and/or to charge fees in sub-currencies. 
The function SHOULD throw unless the `from` account has deliberately authorized the sender of the message via some mechanism.

Notes:
1. Transfers of 0 values MUST be treated as normal transfers.
2. Transfers where `to` and `from` are the same actor MUST be treated as normal transfers.

**Method name**

`transferFrom`

**Parameter**

`{from: address, to: address, value: uint64}`

**Return**

`success: bool`

#### Approve
Allows `spender` to withdraw from your account multiple times, up to the `value` amount.
If this function is called again it overwrites the current allowance with `value`.

**TODO:** consider compare-and-set to avoid message ordering attacks.

**Method name**

`approve`

**Parameter**

`{spender: address, value: uint64}`

**Return**

`success: bool`

#### Allowance
Returns the amount which `spender` is (still) allowed to withdraw from `owner` via `transferFrom()`.

**Method name**

`allowance`

**Parameter**

`{owner: address, spender: address}`

**Return**

`allowance uint64`

## Design Rationale

**TODO:** why follow ERC-20. Why not match binary compatibility.

**TODO:** whether or not to change approval method to compare-and-set.

## Backwards Compatibility
There are no implementations of tokens yet on Filecoin.

This proposal shares semantics with ERC-20, but is not binary-compatible with ERC-20.
The primary reason for this incompatibility is the different primitive types supported by the underlying VM.
The EVM has a native word size of 256 bits, but the FVM uses 64 bit words.
The simple and efficient operation of FVM-native contracts is taken as more important than binary EVM compatibility.

## Test Cases
N/A.

## Security Considerations
TODO: note the potential approvals exploit of ERC-20?

## Incentive Considerations
N/A.

## Product Considerations
See [Design Rationale](#design-rationale) for discussion of following ERC-20.

## Implementation
None yet.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).

[^erc20]: Fabian Vogelsteller, Vitalik Buterin, "EIP-20: Token Standard," Ethereum Improvement Proposals, no. 20, November 2015.
\[Online serial\]. Available: https://eips.ethereum.org/EIPS/eip-20.