---
fip: "XXXX"
title: Unlock sector content notifications to arbitrary actors
author: "Rod Vagg (@rvagg)"
discussions-to: "<create a discussion link and add it here>"
status: Draft
type: Technical
category: Core
created: 2025-02-05
requires: "FIP-0076"
---

# FIP-XXXX: Unlock sector content notifications to arbitrary actors

## Simple Summary
Remove the restriction that limits _sector content change_ notifications to only the storage market actor (f05), allowing any actor designed to handle the [FRC-42](../FRCs/frc-0042.md) `SectorContentChanged` method to receive notifications when data is onboarded to sectors.

## Abstract
[FIP-0076](./fip-0076.md) introduced Direct Data Onboarding (DDO) with a notification system that allows actors to be notified when data is committed to sectors. However, these notifications are currently restricted to only the built-in storage market actor (f05). This FIP proposes removing this restriction, enabling any actor designed to handle the FRC-42 `SectorContentChanged` method to receive notifications, thereby enabling new data-driven applications on Filecoin, such as custom marketplaces, data DAOs, and data verification services.

## Change Motivation
The current restriction of notifications to only the storage market actor limits the potential applications that can be built on top of Filecoin's data onboarding system. By unlocking notifications to arbitrary actors:

1. Smart contracts can directly track when their data is committed to sectors
2. Custom marketplaces can implement their own deal activation logic
3. Data DAOs can monitor and react to data commitments in real-time
4. Applications can implement complex data availability and verification schemes
5. New types of data-driven DeFi applications become possible

This change continues the evolution of Filecoin toward being a more dynamic and programmable storage network.

## Specification

### Storage Miner Actor Changes

Remove [the check](https://github.com/filecoin-project/builtin-actors/blob/5aad41bfa29d8eab78f91eb5c82a03466c6062d2/actors/miner/src/notifications.rs#L62-L69) in the `notify_data_consumers` function in the miner actor that restricts notifications to only the storage market actor. Specifically, remove this code block:

```rust
// Reject notifications to any actor other than the built-in market.
if notifee != STORAGE_MARKET_ACTOR_ADDR {
    if require_success {
        return Err(
            actor_error!(illegal_argument; "disallowed notification receiver: {}", notifee),
        );
    }
    continue;
}
```

The notification system will continue to operate as before, but without this restriction.

### Notification Success Control

Storage providers have control over whether notification failures should abort the sector commitment process through the `require_notification_success` boolean field in parameters for both:

* `ProveCommitSectors3`: For new sector commitments
* `ProveReplicaUpdates3`: For sector data updates

When set to `true`, any notification failure will cause the entire operation to fail. When `false`, failure will be silent and the remainder of the operation will proceed. This allows storage providers to decide how strictly they want to enforce notification delivery for different use-cases.

### Example Solidity Contract Interface

Smart contracts wishing to receive sector content notifications must implement this interface:

```solidity
// SPDX-License-Identifier: MIT
interface ISectorContentReceiver {
    struct PieceChange {
        bytes data;     // CID of the piece
        uint size;      // Size of the piece
        bytes payload;  // Custom payload sent with notification
    }
    
    struct SectorChange {
        uint64 sector;                  // Sector number
        int64 minimumCommitmentEpoch;   // Minimum epoch until which data is committed
        PieceChange[] added;            // Pieces added to the sector
    }
    
    struct SectorReturn {
        bool[] added;   // Success/failure for each piece
    }

    // Function selector: 0x868e10c4
    function handle_filecoin_method(
        uint64 method,
        uint64 codec,
        bytes calldata params
    ) external returns (uint32 exitCode, uint64 codec, bytes memory returnData);
}
```

When data is committed to a sector and this contract is specified as a notification receiver, the `handle_filecoin_method` function will be called with:
- `method`: The FRC-42 method number for `SectorContentChanged` (2034386435)
- `codec`: 0x51 (CBOR codec)
- `params`: CBOR-encoded `SectorContentChangedParams`

The contract must decode the parameters and respond with:
- `exitCode`: 0 for success
- `codec`: 0x51 (CBOR codec) 
- `returnData`: CBOR-encoded `SectorContentChangedReturn`

See [FIP-0076.md](./fip-0076.md) for the full specification of the `SectorContentChanged` method.

## Design Rationale
The original restriction was put in place as a security precaution to prevent potential issues with untrusted code, particularly:

1. Out-of-gas conditions in notification receivers that could cause entire sector commitment operations to fail
2. The lack of recovery mechanisms when notifications fail
3. The potential for malicious actors to deliberately cause sector activation failures

However, this FIP proposes that these risks can be managed because:

1. Storage providers have full control over which actors receive notifications
2. The `require_notification_success` flag allows storage providers to choose whether notification failures should abort operations
3. Gas limits and other FVM protections provide basic safety boundaries
4. The notification system is already designed to be "untrusted" - the miner actor does not rely on notification results for critical operations
5. Smart contracts receiving notifications can only read the data, not modify sector state

## Backwards Compatibility
This change is backwards compatible:
- Existing sector commitments continue working as before
- The storage market actor continues receiving notifications unchanged
- No state migration is required

## Test Cases
To be provided with implementation.

## Security Considerations
1. **Out-of-gas Protection**: When `require_notification_success=true`, any notification failure, including out-of-gas conditions, will cause the entire sector activation process to fail (including the case of batching sectors, where all sectors will fail to activate). Storage providers must carefully consider this when:
   - Choosing notification receivers
   - Setting gas limits
   - Deciding whether to use `require_notification_success=true`

2. **Notification Failure Handling**:
   - With `require_notification_success=true`: No retry mechanism exists - any failure will abort message processing
   - With `require_notification_success=false`: Failures are ignored and message processing continues

3. **Storage Provider Controls**:
   - Only storage providers can specify notification receivers
   - Storage providers can test notification receivers before deployment
   - The `require_notification_success` flag provides some flexibility in handling failures

4. **Other Considerations**:
   - Malicious notification receivers cannot affect sector commitment when `require_notification_success=false`
   - Gas limits protect against infinite loops or excessive computation
   - The read-only nature of notifications prevents state manipulation

## Incentive Considerations
This change creates new opportunities for economic models around data onboarding while preserving existing incentives:
- Marketplaces can implement custom deal activation logic
- Data DAOs can create incentive systems for specific data types
- Applications can implement proofs of data availability

## Product Considerations
This change enables several new product categories:

1. Custom Storage Markets
   - Implement specialised deal matching and activation
   - Create niche markets for specific data types

2. Data Verification Services
   - Track and verify data availability
   - Implement custom data quality metrics

3. Data DAOs
   - Coordinate decentralised data storage
   - Implement governance around data storage

4. DeFi Applications
   - Create financial products based on data storage
   - Implement data-backed tokens

## Implementation
To be completed.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).