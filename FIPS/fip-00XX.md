---
fip: "<to be assigned>" <!--keep the qoutes around the fip number, i.e: `fip: "0001"`-->
title: Arbitrary Message Fallback for Multisig Actors
author: Dimitris Vyzovitis (@vyzo)
discussions-to: https://github.com/filecoin-project/ref-fvm/issues/1689
status: Draft
type: Technical (Core, Networking, Interface, Informational)
created: 2023-03-20
spec-sections:
  - <section-id>
  - <section-id>
requires (*optional): <FIP number(s)>
replaces (*optional): <FIP number(s)>
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->

Default Method Handlers for multisig and paych actors.

## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->


Adds default (no-op) handlers for methods numbers above 2^24 (the
minimum exported method) to the multisig and payment channel
actors. Such calls are now no longer rejected. This change enables
multisig and payment channel actors to receive value from EVM smart
contracts, Eth accounts, and placeholders. It also brings them in line
with the equivalent behaviour of account actors, as of FIP-0050.


## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->

We introduce a default method handler for the multisig and payment
channel builtin actors, which voidly handles all exported methods.

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->

To match the behavior of accounts, multisig and payment channel actors
should default-accept arbitrary messages in the public method range.
See how "fallback" is handled in the account & ethaccount actors.

## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

A default (fallback) method handler is added to the multisig and payment channel
actors that voidly handles all publicly exported methods.
Non-exported methods are rejected with an error.

## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->

This is the simplest possible solution to the problem of account-like
behaviour for multisig and payment channel actors.

## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

Messages with method number over the minimum exported method number (2^24),
that would previously be rejected, are now accepted.  This is a change
in behaviour.

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->

- Send an arbitrary message, with method number equal to the minimum exported
method number, which should be accepted returning an empty value.
- Send an arbitrary message, with method number over the minimum exported
method number, which should be accepted returning an empty value.
- Send an arbitrary message, with method number below the minimum exported method number, which should be rejected.

## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->

None.

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->

None.

## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->

Improves the interoperability of multisigs and payment channel actors with fevm contracts.

## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->

https://github.com/filecoin-project/builtin-actors/pull/1252

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
