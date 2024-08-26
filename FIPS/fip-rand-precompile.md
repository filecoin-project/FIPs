---
fip: "<to be assigned>" <!--keep the qoutes around the fip number, i.e: `fip: "0001"`-->
title: get_randomness filecoin precompile for EVM actor 
author: @anorth, @ZenGround0
status: Draft
type: Technical Core
created: 2024-08-26
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->


# FIP-00XX: get_randomness filecoin precompile for EVM actor 

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->
Add a filecoin precompile to the EVM actor to allow user actors to read randomness from the drand beacon at a specified epoch.

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->
The FVM exposes a syscall for reading randomness from the drand beacon at a specified epoch. The core filecoin protocol uses this randomness facility to validate proofs.  This FIP introduces a precompile exposing this FVM functionality to the fevm builtin actor allowing user contracts to make use of the same functionality.

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->
In order to build Proof of Data Possession we need a good source of randomness with a lookback. It is likely that many other applications have similar needs.



## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->
This precompile was previously implemented before the FeVM upgrade but was removed here: https://github.com/filecoin-project/builtin-actors/pull/995/files.  

We propose a simpler variant of the previous implementation.

```rust
/// Params:
///
/// | Param            | Value                     |
/// |------------------|---------------------------|
/// | randomness_epoch | U256 - low i64             |
/// | entropy_length   | U256 - low u32             |
/// | entropy          | input\[32..] (right padded)|
///
/// any bytes in between values are ignored
///
/// Returns empty array if invalid randomness type
/// Errors if unable to fetch randomness
```

This will be defined at precompile address `0xfe00..06` and named get_randomness

## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->
Since an almost complete design and (abandoned) implementation already exist  a precompile calling the fvm syscall was the obvious choice to get per-epcoh randomness exposed to user actors.

We are dropping the personalization tag and the randomness type parameter from the interface.  With respect to the randomness type param for our motivating application we only need one source of randomness and the unbiasable beacon is the best choice.  If other applications want VRF randomness it makes sense to leave this for another precompile and another FIP.

The personalization tag is redundant for user purposes.  The entropy parameter already allows users to include however many extra bits they want to be mixed with the beacon randomness.  Internally we will set a new personalization tag `EvmRandPrecompile` for all queries to system randomness through this precompile.  



## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->
n/a

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->
As part of implementation we should have 
1. Builtin actors tests that the precompile is accessible and returning the correct randomness as specified by the testing runtime.  
2. Integration tests on a lotus devent with a simple solidity contract that uses the precompile.
3. Integration tests that validate that gas costs are as expected
4. Integration tests that validate that lookbacks to very far back parts of the chain do not cause issues.  In particular we should calculate the furthest past epoch that fits in the block limit and test out querying randomness at that epoch.  This should run on a longstanding testnet like calibration, or make use of artificially generated chains with on the order of mainnet epochs (~10^6)

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->
A gas price function for querying randomness at previous epochs was devised and implemented upon FVM launch.  It was designed to be user facing and increase in cost linearly with the lookback parameter.  This should prevent this feature from opening up a DOS vector against syncing nodes by hitting randomness outside of cached blocks.  We should confirm that randomness queries back to the early history of the chain don’t cause problems with implementations as part of testing. 


## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->
A gas price function for querying randomness at previous epochs was devised and implemented upon FVM launch.  The price function increases linearly with lookback parameter making recent randomness cheap and randomness from the distant past expensive. This incentive aligns users to query recent randomness stored in cached blocks with less burden on the system.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->
Precompiles are a standard feature of the EVM that developers are familiar with.  By simplifying the precompile interface from the previous implementation we can give a powerful new feature without unnecessary complexity overhead.

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->
Previous implementation here: https://github.com/filecoin-project/builtin-actors/pull/995/files
Draft PR: https://github.com/filecoin-project/builtin-actors/pull/1576

## TODO
<!--A section that lists any unresolved issues or tasks that are part of the FIP proposal. Examples of these include performing benchmarking to know gas fees, validate claims made in the FIP once the final implementation is ready, etc. A FIP can only move to a “Last Call” status once all these items have been resolved.-->


## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
