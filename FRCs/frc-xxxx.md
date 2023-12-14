---
fip: "**TODO**" 
title: "FVM-Enabled Deal Aggregation"
author: "@aashidham, @raulk, @nonsense, @honghao"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/866
status: Draft
type: FRC
created: 2023-10-07
---

# FVM-Enabled Deal Aggregation

## Simple Summary 

Filecoin deal-making flows for small files previously required trusted offchain aggregators to consolidate small files into a storage deal with a Filecoin Storage Provider. This FRC proposes a robust standard for an FEVM smart contract to act abstractly as an aggregator, enabing use cases for trustless aggregation, storage of small files on Filecoin, and composibility with other onchain data organiations on FEVM (including dapps and DataDAOs).

## Introduction

This proposal presents the `I*DataAggregator` set of interfaces for the Filecoin Virtual Machine (FVM) along with its reference implementation. This family of interfaces manages storage deal creation requests and (optionally) stores relevant deal metadata, including `deal_id` and`provider_id`. 

These also ensures data inclusion through PoDSI inclusion proof verification. PoDSI is described in [FRC-58 Verifiable Data Aggregation](https://github.com/filecoin-project/FIPs/blob/e913fea0f32cf412474f48600f29dbe9753b3d0c/FRCs/frc-0058.md), which allows aggregators to produce an Proof of Data Segment Inclusion (PoDSI) certifying that the client’s data is being accurately aggregated.

This proposal additionally supports Renew/Replication/Repair-as-a-Service (RaaS) full interface, where clients can specify flexible RaaS term deals with aggregator to define the renew period, replication factor, and repair threshold. Aggregator would then honor the provided deal terms with associated Storage providers, and perform the callback/emit event when the job is completed. More details on aggregator-implemented RaaS full interface workflow can be found [here](https://docs.google.com/presentation/d/11wurlsTFo7ojtDI3UKzU1JA9Ploy3-VduuJ5dJciW80/edit#slide=id.g253ed1e380a_1_122).

Standardizing these interfaces allows various aggregators to offer a set of uniform methods for submitting storage deal creation requests and storing the deal metadata. This enhances community portability across different aggregators and promotes compatibility among tools and libraries. 

Note that this FRC can be built on both FVM mainnet as well as IPC subnets. The latter can be more gas efficient, but may not feature the variety of SPs available on SP mainnet. Over time, we expect that gas costs may push more SPs and builders for this standard to IPC subnets. 

Note that currently this FRC does not cover paid deals, as well as managing escrow for paid deals. However we expect that future versions of this FRC may incorporate these flows.

## Motivation / Context

This standard makes it possible for a client to transact with an aggregator in a trustless manner. That is, the user can be sure that the aggregated file contains the submitted subpiece through PoDSI (in the case of aggregators that implement `IOffchainDataAggregator`) or through commPa computation happening onchain (in the case of aggregators that implement `IOnchainDataAggregator`). Through this trustless aggregation, this standard also enables richer interactions with Dapps, DataDAOs, and other onchain organizations present on FVM or IPC subnets. These can now store small pieces of data through FVM / IPC.

The main audience of this standard is aggregators running in the PLN that want to leverage onchain primitives to trustlessly aggregate data. They should leverage this approach when they want to make their operations transparent to clients, SPs and other onchain indexers. They should also leverage this standard when they want to make their aggregation composable with other data organizations (such as Dapps and DataDAOs) being built on FVM / IPC. We expect substantial adoption of this standard across these aggregators. 

## **Specification**

### `IOffchainDataAggregator` **Interface**

Outlined below is the `IOffchainDataAggregator` interface, which has to be implemented by each smart contract that stores aggregators’ deal information. Each aggregator can deploy their own smart contract to have full control, or multiple aggregators can share one smart contract and put their data under the same one. 

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

/**
 * @title IOffchainDataAggregator Interface
 * @notice Interface for an aggregator oracle on the Filecoin Virtual Machine (FVM)
 */
interface IOffchainDataAggregator {
    
    /**
     * @notice A structure referensing a deal representation in the Filecoin network
     */
    struct Deal {
        uint64 dealId;   // A unique identifier for the deal.
        uint64 providerId;  // The storage provider that is storing the data for the deal.
				uint64 marketActorId; // The actor ID of the storage market in which the deal representation is stored. dealId is scoped by marketActorId
    }

    /**
     * @notice Emitted when a new request is submitted with an ID and content identifier (CID)
     * @param id Identifier for the request
     * @param cid Content identifier for the request
     */
    event SubmitAggregatorRequest(uint256 indexed id, bytes cid);

    /**
     * @notice Emitted when a new request is submitted with an ID, content identifier (CID), and RaaS parameters
     * @param id Identifier for the request
     * @param cid Content identifier for the request
     * @param _replication_target The number of copies this file should be replicated to
     * @param _repair_threshold The number of epochs the deal should be repaired after being inactive for
     * @param _renew_threshold The number of epochs the deal should be renewed before its expiration date
     */
    event SubmitAggregatorRequestWithRaaS(uint256 indexed id, bytes cid,
																					uint256 _replication_target, uint256 _repair_threshold,
																					uint256 _renew_threshold);

    /**
     * @notice Emitted when a request is completed, marking it with the request ID and deal ID
     * @param id Identifier for the request
     * @param dealId Identifier for the deal associated with the request
     */
    event CompleteAggregatorRequest(uint256 indexed id, uint64 indexed dealId);

    /**
     * @notice Function to submit a new file (as denominated by a piece CID) to the aggregator
     * @param _cid The piece CID to be stored
     * @param _fetchLink A link to he piece CID to allow the aggregators to fetch the data in the piece CID.
     * @return The identifier for the submitted request
     */
    function submit(bytes memory _cid, bytes memory _fetchLink) external returns (uint256);

		/**
     * @notice Function to submit a new file to the aggregator, specifing the raas parameters
     * @param _cid The piece CID of the file to be stored
     * @param _replication_target The number of copies this file should be replicated to
     * @param _repair_threshold The number of epochs the deal should be repaired after being inactive for
     * @param _renew_threshold The number of epochs the deal should be renewed before its expiration date
     * @return 
     */
		function submitRaaS(bytes memory _cid, bytes memory _fetchLink,
												 uint256 memory _replication_target, uint256 memory _repair_threshold,
									       uint256 memory _renew_threshold);

    /**
     * @notice Callback function that is called by the aggregator once data has been stored
     * @param _id The identifier for the request
     * @param _dealId The deal's unique identifier
     * @param _providerId The provider's unique identifier
     * @param _proof Inclusion proof for the stored data segment
     * @param _verifierData Additional data needed to verify the inclusion proof
     * @return Additional auxiliary data
     */
    function complete(
        uint256 _id,
				uint64 _marketActorId,
        uint64 _dealId,
        uint64 _providerId,
        InclusionProof memory _proof,
        InclusionVerifierData memory _verifierData
    ) external returns (InclusionAuxData memory);
}
```

Aggregators who want to provide RaaS features should implement the `submitRaaS` and monitor the `SubmitAggregatorRequestWithRaaS` as well. Aggregators should take the RaaS parameters in the `SubmitAggregatorRequestWithRaaS` and register the corresponding RaaS functions for the deal. 

`InclusionProof` , `InclusionVerifierData`, and `InclusionAuxData` are defined as follows (all the code related to verifying the PoDSI is provided in the reference implementation) 

```solidity
// ProofData is a Merkle proof
struct ProofData {
    uint64 index;
    bytes32[] path;
}

// InclusionPoof is produced by the aggregator (or possibly by the SP)
struct InclusionProof {
    // ProofSubtree is proof of inclusion of the client's data segment in the data aggregator's Merkle tree (includes position information)
    // I.e. a proof that the root node of the subtree containing all the nodes (leafs) of a data segment is contained in CommDA
    ProofData proofSubtree;
    // ProofIndex is a proof that an entry for the user's data is contained in the index of the aggregator's deal.
    // I.e. a proof that the data segment index constructed from the root of the user's data segment subtree is contained in the index of the deal tree.
    ProofData proofIndex;
}

// InclusionVerifierData is the information required for verification of the proof and is sourced
// from the client.
struct InclusionVerifierData {
    // Piece Commitment CID to client's data
    bytes commPc;
    // SizePc is size of client's data
    uint64 sizePc;
}

// InclusionAuxData is required for verification of the proof and needs to be cross-checked with the chain state
struct InclusionAuxData {
    // Piece Commitment CID to aggregator's deal
    bytes commPa;
    // SizePa is padded size of aggregator's deal
    uint64 sizePa;
}
```

### `IOnchainDataAggregator` **Interface**

For building **onchain** **aggregators** (aggregators that compute CommPa within smart contract onchain) , the user interface is very similar. The only difference is the `complete()` callback function that aggregator calls: since the CommP aggregation happens within the onchain contract, PoDSI is entirely optional and thus the above fields (`InclusionProof` , `InclusionVerifierData`, and `InclusionAuxData`) are not required. 

In this case, the function `onchain_complete` would only needs to include `uint256 _id`, `uint64 _marketActorIduint64 _dealId`, and `uint64 _providerId` fields, as shown below:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

/**
 * @title IOnchainDataAggregator Interface
 * @notice Interface for an aggregator oracle on the Filecoin Virtual Machine (FVM)
 */
interface IOnchainDataAggregator {
    
    /**
     * @notice A structure referencing a deal representation in the Filecoin network
     */
    struct Deal {
        uint64 dealId;   // A unique identifier for the deal.
        uint64 providerId;  // The storage provider that is storing the data for the deal.
				uint64 marketActorId; // The actor ID of the storage market in which the deal representation is stored. dealId is scoped by marketActorId
    }

    /**
     * @notice Emitted when a new request is submitted with an ID and content identifier (CID)
     * @param id Identifier for the request
     * @param cid Content identifier for the request
     */
    event SubmitAggregatorRequest(uint256 indexed id, bytes cid);

    /**
     * @notice Emitted when a new request is submitted with an ID, content identifier (CID), and RaaS parameters
     * @param id Identifier for the request
     * @param cid Content identifier for the request
     * @param _replication_target The number of copies this file should be replicated to
     * @param _repair_threshold The number of epochs the deal should be repaired after being inactive for
     * @param _renew_threshold The number of epochs the deal should be renewed before its expiration date
     */
    event SubmitAggregatorRequestWithRaaS(uint256 indexed id, bytes cid,
																					uint256 _replication_target, uint256 _repair_threshold,
																					uint256 _renew_threshold);

    /**
     * @notice Emitted when a request is completed, marking it with the request ID and deal ID
     * @param id Identifier for the request
     * @param dealId Identifier for the deal associated with the request
     */
    event CompleteAggregatorRequest(uint256 indexed id, uint64 indexed dealId);

    /**
     * @notice Function to submit a new file to the aggregator
     * @param _cid The piece CID of the file to be stored
     * @return The identifier for the submitted request
     */
    function submit(bytes memory _cid, bytes memory _fetchLink) external returns (uint256);

		/**
     * @notice Function to submit a new file to the aggregator, specifing the raas parameters
     * @param _cid The piece CID of the file to be stored
     * @param _replication_target The number of copies this file should be replicated to
     * @param _repair_threshold The number of epochs the deal should be repaired after being inactive for
     * @param _renew_threshold The number of epochs the deal should be renewed before its expiration date
     * @return 
     */
		function submitRaaS(bytes memory _cid, bytes memory _fetchLink,
												 uint256 memory _replication_target, uint256 memory _repair_threshold,
									       uint256 memory _renew_threshold);

    /**
     * @notice Callback function that is called by the onchain aggregator once data has been stored
     * @param _id The identifier for the request
     * @param _dealId The deal's unique identifier
     * @param _providerId The provider's unique identifier
     */
    function onchain_complete(
        uint256 _id,
				uint64 _marketActorId,
        uint64 _dealId,
        uint64 _providerId,
    ) external returns ();

}
```

### `IDataAggregatorEnumerable` **Interface**

Outlined below is the `IDataAggregatorEnumerable` Interface, which can be optionally implemented by aggregators if they want to maintain a mapping of pieceCIDs and deals on chain. This makes the subpieces enumerable onchain and will allow third party observers of aggregators (chain indexers, block explorers and other SPs and clients interested in aggregation) to understand more in detail what data each aggregator is aggregating.

Note: on FVM mainnet, maintaining this mapping onchain for a high volume aggregator can become unscalable. Therefore, we recommend implementing this optional interface either on an IPC subnet or if the aggregator does not have a large volume of deals that are being aggregated.

```solidity
interface IDataAggregatorEnumerable {
    /**
     * @notice Fetches an array of all piece CIDs processed by the aggregator
     * @param _startIndex The index at which to include the result in the response
     * @param _count The number of items to include in the response
     * @return Array of piece CIDs
     */
    function getAllCIDs(uint64 _startIndex, uint64 _count) external view returns (bytes[] memory);

    /**
     * @notice Retrieves all deal IDs associated with a specified piece CID
     * @param _cid The piece CID to query
     * @param _startIndex The index at which to include the result in the response
     * @param _count The number of items to include in the response
     * @return Array of deals corresponding to the piece CID
     */
    function getAllDeals(bytes memory _cid, uint64 _startIndex, uint64 _count) external view returns (Deal[] memory);
}
```

### Reference Implementation

Provided [here](https://github.com/filecoin-project/raas-starter-kit/blob/main/contracts/DealStatus.sol). 

### **Rationale**

The `I*DataAggregator` interfaces serve as a foundational blueprint for offchain aggregators in the Filecoin ecosystem. By prescribing a consistent set of methods and structures, we standardize the process of data submission across any aggregator that wants to create Filecoin storage deals.

Specifically:

- **getAllCIDs**: Ensures third parties can transparently assess the content that has been aggregated. This can be used to access all the piece CIDs that have been written to chain from the current aggregator standard, which (in turn) can be used to get all deals from the aggregator.
- **getAllDeals**: The **`getAllDeals`** function returns all the **`dealId`** and `providerId` for a given CID. Users can utilize this information to check deal status via FVM or Filecoin APIs and perform necessary actions like repair or renewal.
- Two-step **submit and complete process**:
    - **Submission of Data Request:**
        - Any user can initiate the process by using the **`submit()`** function to request the aggregation of specific data into a storage deal. The aggregator then actively monitors the event emitted by the smart contract, known as **`SubmitAggregatorRequest`**. Once this event occurs, the aggregator begins the process of aggregating the data, which is represented by the CID, into an onchain deal.
    - **Verification and Completion:**
        - Once the data has been successfully aggregated into a deal, the aggregator proceeds to call the **`complete()`** function. This critical step serves to verify that the data has been correctly included within the aggregated bundle. If any issues are detected during this verification process, the **`complete()`** function reverts, ensuring that only deals that can be verified via PoDSI passes this step.
        - As a user, you can have confidence that your data has been included into the deal when you observe the occurrence of the **`CompleteAggregatorRequest`** event emitted by the `complete()` step associated with the corresponding **`dealId`** . This event confirms the successful completion of the data aggregation process.

![Untitled](https://github.com/aashidham/FIPs/assets/782153/043e0a39-97e2-4b23-8dcc-ed95be857f79)

### **Backwards Compatibility**


This proposal introduces a new standard and does not alter or disrupt existing interfaces or implementations. However, aggregators wishing to conform to this standard will need to adopt this interface.

### **Test Cases**

Testing for the implementation of the `I*DataAggregator` family of interfaces should focus on:

- Successful data submission and completion.
- Correct PoDSI proof.
- Accurate tracking of CIDs and deals’ metadata.
- Proper event emissions during submission and completion of the aggregator request.

### Data Retrieval

Aggregators maintain a copy of the data and serve it via an HTTP endpoint. Aggregators should provide an HTTP endpoint and a IPFS endpoint for users to retrieve the data for a certain period, e.g. 30 days. Client can make an HTTP call to the aggregator they uploaded the data to to download the file by providing the data’s CID. 

Recommended API interface for the two retrieval methods mentioned above:

- Retrieval endpoint for Filecoin retrieval: GET /data/<pieceCID>
- Retrieval gateway for IPFS retrieval: https://gateway/ipfs/<pieceCID>

### **Security Considerations**

Data to be aggregated is considered to be open. No security concerns at this time. 

### **Copyright Waiver**

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).

---
