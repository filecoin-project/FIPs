---
fip: "XXXX"
title: Add support for legacy Homstead Ethereum Trasnactions 
author: Aarsh (@DharmaBum) 
discussions-to: https://github.com/filecoin-project/FIPs/discussions/962
status: Draft
type: Technical
category: Core
created: 2024-04-17
---

# FIP-00XX: Add support for legacy Homestead Ethereum Transactions 

## Simple Summary
This FIP introduces support for the Ethereum Homestead era's legacy transactions on the Filecoin network, complementing the existing support for EIP-1559 transactions. The main goal of this proposal is to facilitate the use of legacy contracts on Filecoin, which depend on these older transaction formats for both deployment and operation.

It's important to note that this FIP specifically targets the integration of legacy Ethereum Homestead transactions. Unlike their successors, these transactions lack several parameters such as `ChainId`, `AccessList`, `MaxFeePerGas`, and `MaxPriorityFeePerGas`, and they do not conform to a specific "transaction type"—a feature introduced with EIP-2718. The incorporation of EIP-155 and EIP-2930 transactions will be considered in subsequent FIPs.

## Abstract
The Filecoin network already supports EIP-1559 transactions. These transactions have a designated transaction type of `0x02` and have the following parameters:

```go
type EIP1559Tx struct {
	ChainID             int
	Nonce               int
	To                  *EthAddress
	Value               big.Int
	MaxFeePerGas        big.Int
	MaxPriorityFeePerGas big.Int
	GasLimit            int
	Input               []byte
	AccessList          []EthHash
	V                   big.Int
	R                   big.Int
	S                   big.Int
}
```

However, Filecoin does not support legacy Homestead transactions.  These transactions do not have a designated transaction type and have the following parameters:
```go
type LegacyEthTx struct {
	Nonce    int
	To       *EthAddress
	Value    big.Int
	GasPrice big.Int
	GasLimit int
	Input    []byte
	V        big.Int
	R        big.Int
	S        big.Int
}
```

The main distinction relevant to this FIP is that legacy transactions do not contain a `ChainID` and so the transactions are not scoped to a specific chain. This allows replaying the same signed contract creation transaction across multiple chains for deploying a contract and also enables the contract to have the same address across chains.

Support for legacy transactions on Filecoin will be enabled by prepending an extra marker byte `0x01` to the signature of legacy transactions. This will allow Filecoin to detect that a transaction is a legacy transaction and process and execute it accordingly.

The `GasPrice` parameter from the legacy transaction will be utilized to determine both the `GasFeeCap` and `GasPremium` parameters in the Filecoin message, as `GasPrice` encompasses the full cost per unit of gas that the sender is willing to pay.

The `V` parameter from the legacy transaction will be adjusted by subtracting 27 before the signature is verified. This is because the `V` parameter in the signature of a legacy transaction can take a value of either 27 or 28 whereas EIP1559 transactions supported by Filecoin always have a `V` value of 0 or 1 and the current signature verification implementation only supports `V` values of 0 or 1.

## Change Motivation
Legacy transactions are not scoped to a specific chain as they do not have a `ChainID` parameter and so the same signed legacy contract creation transaction can be re-used to deploy the same contract across multiple chains.

Currently, many smart contracts running in the wild on other chains have been deployed through legacy transactions signed by the contract author using ephemeral accounts, after which the keys were discarded. These signed legacy contract deployment transactions have since been made available online. 

Enabling support for legacy ETH transactions with this FIP allows for the straightforward deployment of these contracts on the Filecoin network by replaying the original, signed legacy contract deployment transactions on the Filecoin network.

Numerous popular wallets, including Coinbase Wallet, Trust Wallet, and Phantom, currently facilitate legacy transactions on the Ethereum network. This FIP will extend their capabilities to also support legacy Ethereum transactions on the Filecoin network.

## Specification

Filecoin supports EIP-1559 transactions by converting them into standard Filecoin messages. These messages are distinguished by a unique "delegated" signature type, which encapsulates the original Ethereum transaction signature. The validation process for these messages involves:

1. Identifying the "delegated" signature type.
2. Confirming that the "from" address originates from an Ethereum account (indicated by the prefix `f410f...`).
3. Reconstructing the original EIP-1559 transaction from the Filecoin message and verifying its signature.

For legacy transactions, the validation process is similar, with a crucial modification in the third step. To differentiate legacy transactions from EIP-1559 transactions and to accurately reconstruct the original legacy Ethereum transaction from the Filecoin message, this FIP introduces a method to mark legacy transactions uniquely. Specifically, it proposes prepending a distinct marker byte `0x01` to the signature of a legacy ETH transaction. This adjustment occurs after the legacy transaction is submitted to a Filecoin node but before it is broadcast across the network. Consequently, the signature length of a legacy ETH transaction extends to 66 bytes, compared to 65 bytes for an EIP-1559 transaction. This modified signature is also stored in the chain state for legacy transactions.

The revised steps for processing and validating a Filecoin message representing an Ethereum transaction are:

1. Recognize the "delegated" signature type, indicating an Ethereum transaction.
2. Verify that the "from" address is an Ethereum account (starting with `f410f...`).
3. Distinguish the transaction type based on the signature length:
   - If the signature is 66 bytes long and starts with `0x01`, it is translated to a legacy ETH transaction.
   - If the signature is 65 bytes long, it corresponds to an EIP-1559 transaction.
4. Validate the transaction parameters and signature (after ignoring the first marker byte `0x01` for legacy ETH transactions as that is not part of the signature created by the user).

Note that this FIP does not need any changes to the EVM/FVM runtime and to built-in Actors.

### Handling the `GasPrice` parameter of the legacy transaction

The Filecoin & FVM gas fee market follows a model similar to EIP-1559 and so expect Filecoin messages to contain both `GasFeeCap` and a `GasPremium` parameters on the transaction. 

For EIP-1559 transactions, `GasFeeCap` and `GasPremium` parameters for the Filecoin message are derived from the `MaxFeePerGas` and `MaxPriorityFeePerGas` parameters on the EIP-1559 transaction respectively.

However, legacy ETH transactions only have a `GasPrice` parameter. To convert a legacy ETH transaction to a Filecoin message, both the `GasFeeCap` and `GasPremium` parameters will be set to the `GasPrice` set on the legacy transaction. This is because `GasPrice` already represents the full price per unit of gas that the user is willing to pay. See the `Incentive Considerations` section below for a detailed explanation.

### Specific Handling of the `V` Parameter in Signatures

The use of the `V` parameter in the signature of an Ethereum transaction and the values it can contain has gone through several iterations over the years. Here are the important points to note for the purpose of this FIP:

For EIP-1559 transactions that are supported by Filecoin, the `V` parameter in the signature can take a value of either 0 or 1. This helps determine which of the two possible Y coordinates is correct for the elliptic curve point that corresponds to the R part of the signature. This is necessary because the ECDSA signature produces an R value and an S value, but two possible Y coordinates can be derived from the X coordinate (R).

However, for legacy Homestead Ethereum transactions, the value of `V` was arbitrarily set to 27 (corresponds to `0` in EIP-1559 transactions) or 28 (corresponds to `1` in EIP-1559 transactions) and serves the same purpose of being able to specifically determine the parity of the Y coordinate corresponding to the R component of the signature.

Given that the current signature verification implementation for the delegated signature type(which is the signature type that will be used for legacy ETH transactions in addition to EIP1559 transactions) only recognizes `V` values of 0 or 1, it is necessary to adjust the `V` value in the signature of legacy transactions by subtracting 27. This adjustment must be made prior to the authentication and verification of the message's signature, as well as before extracting the public key and sender's address from the legacy transaction's signature.

Note that this is only a temporary transformation for the purpose of a validating the signature of a legacy transaction and for extracting the public key of the sender from the signature. The `V` value that gets persisted in the chain state for the legacy transaction will be the original `V` value set on the legacy transaction by the user.

The `go-ethereum` implementation also uses the same method for handling the `V` value of legacy transactions before validating the signature as can be seen at https://github.com/ethereum/go-ethereum/blob/74e8d2da97aacc2589d39584f6af74cb9d62ee3f/core/types/transaction_signing.go#L543

## Design Rationale

To facilitate support for legacy transactions in Filecoin, several approaches were evaluated:

1. Attempt dual validation by converting the Filecoin message into both an EIP1559 transaction and a legacy transaction, and then validating the signature for both formats. If either validation succeeds, the message would be accepted. However, this method would double the cost of signature validation, making it inefficient and cumbersome.
2. Introduce a new signature type and rename the existing "delegated" type to "eip1559" or similar. This approach, however, conflicts with our plans for future account abstraction, which we are not prepared to compromise.
3. Prepend a transaction type byte exclusively to the signature field of Ethereum transactions. This solution is optimal as it introduces minimal complexity and is straightforward to implement. 
4. Utilize the consistent 65-byte length of the EIP1559 transaction signature in Filecoin messages by appending a "type" byte only for non-EIP1559 transactions. 

After careful consideration, we selected the third option. It offers a balance of simplicity, efficiency, and minimal impact on existing systems.

## Backwards Compatibility
This proposal adds support for a new transaction type to Filecoin. Since transactions form part of the chain state, this is a consensus breaking change and so all nodes will have to upgrade to support legacy Ethereum transactions.

The ETH RPC APIs will be augmented to add support for reading/writing legacy transactions. However, all changes to the existing ETH RPC APIs will be backward compatible so as not break existing users and tooling.

## Test Cases
All pre-existing unit tests for the ETH RPC API and ETH transactions should continue working as before. Comprehensive new unit tests will be written for legacy transactions.

Existing integration tests for the ETH RPC API and ETH transactions should continue working as before. Comprehensive new integration tests will be written for legacy transactions.

Deployment & Execution of contracts with signed legacy transactions will be tested rigorously on a devnet/butterfly/calibnet networks.

## Security Considerations
This proposal does not introduce any reductions in security.

## Incentive Considerations
Filecoin and the Filecoin Virtual Machine (FVM) adopt a gas fee market similar to Ethereum's EIP-1559 model. This model introduces two key parameters to manage gas fees for transactions:

1. `GasFeeCap`: This parameter determines the maximum amount of attoFIL a user is prepared to pay per gas unit for executing a transaction. It serves as a cap on the total transaction fee, ensuring that the sum of the base fee and the priority fee paid to miners does not exceed the `GasFeeCap`.

2. `GasPremium`: This parameter determines the highest attoFIL a user is willing to pay per gas unit as a priority fee to miners for including their transaction in a block. It effectively limits the priority fee, especially when the `GasFeeCap` is higher than the base fee.

For EIP-1559 transactions, the values for `GasFeeCap` and `GasPremium` in Filecoin messages are directly derived from the `MaxFeePerGas` and `MaxPriorityFeePerGas` parameters of the EIP-1559 transaction.

However, legacy Ethereum transactions only have a single `GasPrice` parameter, which specifies the gas price a sender is willing to pay per unit of gas to process the transaction. 

Under the FVM fee market framework, when processing legacy transactions, `GasPrice` is adapted to simultaneously fulfill the roles of both `GasFeeCap` and `GasPremium`. In this adaptation, both `GasFeeCap` and `GasPremium` are set equal to `GasPrice`. Initially, the base fee is subtracted, and any remaining attoFIL from the `GasPrice`, after this deduction, is allocated entirely as a priority fee to the miner. This arrangement ensures that the total fee (base fee plus priority fee) paid by the user for a legacy transaction does not surpass the `GasPrice` set by the user on the legacy ETH transaction. However, note that this does incentivise SPs to hoard legacy user transactions and only include them in blocks when the base fee is low so that they can earn more priority fees.

## Product Considerations
This FIP enhances the Filecoin network by facilitating the execution of legacy Ethereum transactions, thereby bolstering Filecoin's interoperability with pre-existing Ethereum tools, libraries, contract suites, and frameworks, which assume such transactions.

A notable number of smart contracts on various chains were initially deployed using legacy transactions, signed by the contract authors through ephemeral accounts. Subsequently, these keys were discarded, and the signed transactions for deploying these contracts became publicly accessible online. This FIP enables users to deploy these pre-signed contracts on the Filecoin network by directly replaying the existing legacy contract creation transactions.

Moreover, some contracts _rely_ on legacy transactions so that they can be deployed at the same address no matter what chain they're deployed to. Specifically, they rely on the fact that the transaction is _not_ scoped to a specific chain so that the same message can be re-used to deploy the same contract across multiple chains. This FIP enables deployment and execution of such smart contracts on Filecoin as legacy transactions do not have a `ChainID` parameter and are thus not scoped to a specific chain. 

## Implementation
Implementation of this proposal is in progress on the following integration branch:
https://github.com/filecoin-project/lotus/tree/integrate/add-eth-legacy-call.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).