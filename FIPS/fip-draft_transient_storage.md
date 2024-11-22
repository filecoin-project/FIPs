---
fip: "<to be assigned>"  
title: Add Support for EIP-1153 (Transient Storage) in the FEVM  
author: Michael Seiler (@snissn), Steven Allen (@stebalien)  
discussions-to: <URL>  
status: Draft  
type: Technical  
category: Core  
created: 2024-11-19  
---

# FIP-XXXX: Add Support for EIP-1153 (Transient Storage) in the FEVM

## Simple Summary
This proposal introduces support for **[EIP-1153: Transient Storage](https://eips.ethereum.org/EIPS/eip-1153)** in the Filecoin Ethereum Virtual Machine (FEVM). Transient storage provides ephemeral data storage during transaction execution. To maintain compatibility with Ethereum contracts utilizing this feature, the FEVM will implement transient storage with lifecycle validation.

## Abstract
EIP-1153 defines transient storage as temporary data accessible only during the originating transaction, cleared automatically at the end of the transaction. This FIP adapts transient storage to the FEVM using `TLOAD` and `TSTORE` opcodes, ensuring compatibility with Ethereum contracts and libraries that rely on this feature. Lifecycle validation mechanisms enforce the transaction-scoped behavior of transient storage, achieving functional equivalence with Ethereum’s implementation and seamless integration with Filecoin’s architecture.


## Change Motivation
Transient storage offers developers temporary, transaction-scoped storage for managing intermediate states. One key benefit of this feature is its ability to improve the implementation of reentrancy locks, enhancing security by mitigating risks associated with multiple calls to a function within sub-transactions. By introducing transient storage, the FEVM aligns with Ethereum’s tooling and Solidity’s modern features, providing a seamless developer experience while supporting advanced contract use cases and secure computing.

While the FEVM implementation utilizes permanent storage for practical reasons, its lifecycle validation ensures it functionally replicates Ethereum’s ephemeral transient storage. This enables compatibility with contracts and libraries that rely on `TLOAD` and `TSTORE` while supporting transaction-scoped data handling.

## Specification

### Opcode Descriptions

#### `TLOAD`
- **Opcode Hex:** `0x5C`  
- **Stack Input:**  
  - `key`: Location of the transient storage value to load  
- **Stack Output:**  
  - `value`: Stored value or zero if no value exists  
- **Description:** Retrieves the value associated with `key` in the transient storage for the current transaction.

#### `TSTORE`
- **Opcode Hex:** `0x5D`  
- **Stack Input:**  
  - `key`: Location to store the value  
  - `value`: Value to store  
- **Output:** None  
- **Description:** Stores `value` at the specified `key` in the transient storage for the current transaction.

### Lifecycle Management
Transient storage is valid only within the context of a single transaction. A lifecycle mechanism tracks transaction metadata (`origin` and `nonce`) to enforce lifecycle validation. 

### Implementation Details
The FEVM implements transient storage using a lifecycle validation mechanism to ensure data remains accessible only during the originating transaction. This validation enforces the same behavior as Ethereum’s ephemeral transient storage. Internally, transient storage relies on permanent storage to manage lifecycle data and state while ensuring functional adherence to Ethereum’s behavior.

---

## Design Rationale

The design adheres to the intent of EIP-1153 while adapting to Filecoin's architecture. The use of lifecycle validation ensures transient storage behaves as expected within the scope of a single transaction. This approach balances compatibility with Ethereum contracts and simplifies implementation within the existing FEVM architecture. 

Alternative designs, such as purely in-memory storage, were considered but deemed impractical due to technical implementation difficulties.

## Backwards Compatibility
The addition of transient storage is fully backward-compatible. Existing contracts remain unaffected unless they utilize `TLOAD` and `TSTORE`. Contracts compiled with older Solidity versions will continue to execute without changes.

## Test Cases

### Essential Tests
1. **Basic Functionality:**
   - Verify `TLOAD` retrieves the correct value.
   - Verify `TSTORE` writes data to the transient storage correctly.

2. **Lifecycle Validation:**
   - Verify that transient storage is automatically cleared and becomes inaccessible after the transaction ends.
   - Verify that transient storage is properly cleared at the end of each transaction and any out-of-lifecycle data does not interfere with subsequent transaction operations.

---

## Security Considerations
Transient storage introduces minimal additional risk compared to existing state storage. Lifecycle validation ensures storage is inaccessible outside the originating transaction. Security measures include:
- Preventing out-of-bounds memory access.
- Ensuring transient storage clears properly after a transaction ends.

---

## Incentive Considerations
Transient storage supports the management of temporary, transaction-scoped data and enables features outlined in **EIP-1153**, such as reentrancy locks, temporary approvals, on-chain address computation, and enhanced proxy call metadata handling. These capabilities align with Filecoin’s goal of enabling scalable and reliable decentralized applications.

By implementing transient storage, the FEVM ensures compatibility with Ethereum’s tooling and supports developers accustomed to this feature. It also facilitates seamless integration of existing projects utilizing EIP-1153, enriching the Filecoin ecosystem and expanding its appeal to the broader Ethereum developer community.


---

## Product Considerations
Adding transient storage ensures compatibility with modern Ethereum tooling, attracting developers to Filecoin’s ecosystem. This feature supports the development of advanced smart contracts and storage-related services. This addition further solidifies Filecoin’s position as a robust EVM-compatible chain, enhancing its attractiveness to Ethereum developers and expanding its ecosystem of decentralized applications.

---

## Implementation
The reference implementation, including `TLOAD` and `TSTORE`, is available in the following pull request: [filecoin-project/builtin-actors#1588](https://github.com/filecoin-project/builtin-actors/pull/1588). The implementation includes lifecycle validation and persistent backing for ease of use.

---

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).  
