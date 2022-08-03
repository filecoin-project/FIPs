---
fip: <to be assigned>
title: Standard Authentication Method for Actors
author: Alex North (@anorth), Aayush Rajasekaran (@arajasek)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/413
status: Draft
type: Technical (Interface)
created: 2022-09-02
replaces: [FIP-0035](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0035.md)
---

## Simple Summary

The Filecoin protocol has entities called "actors" that can be involved in computation on the Filecoin blockchain. 
There are various different kinds of actors; among the most common are accounts and multisigs. 
With [the planned introduction of the Filecoin Virtual Machine](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0030.md), there will be many new kinds of user-defined actors.
Unfortunately, today, the only kind of actors that can be asked to verify whether they have authorized a piece of data are account actors -- they do so through a signature validation.
This FIP is the starting point to evolve a convention by which any actor can verify such authorization. It simply proposes adding a special "authorize" message that actors can choose to implement. 
If they do so, it can be used by other actors to validate their authorization of data.

## Abstract

There is a need for arbitrary actors to be able to authorize (to other actors) that they have approved of a piece of data. This need will become more pressing with the Filecoin Virtual Machine.
This FIP proposes adding an `Authorize` message that any actor can choose to implement. This message can be called by any other actor to verify whether the "authorizer"
approves of a piece of data. This is a small change to the existing actors, and allows for user-defined actors to flexibly implement this method according to their needs.

## Change Motivation

We want any actors, including user-defined actors, to be able to confirm that they have authorized some data.
If we don't have this ability, we will need to engineer around it in painful ways. The proposed [FIP-0035](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0035.md)
is a concrete example; it proposes adding several new methods and data types in order to enable
user-defined actors to serve as clients for storage deals. 

It will be infeasible to modify the builtin-actors themselves every time we want to be able to authorize some new kind of information, and doing so will require more total messages 
to be landing on the Filecoin blockchain. Instead, a flexible, universal approach for actors to authorize data would be preferred.

## Specification

We propose adding the following method to the built-in `Account` Actor. 
This method can then be the blueprint for other builtin actors (eg. the multisig actor), 
as well as a template for user-defined actors.

```
    /// Authenticates whether the provided authorization is valid for the provided message.
    /// Errors if the authentication is invalid.
    pub fn verify_authorization(params: VerifyAuthorizationParams) -> Result<(), ActorError>
```

The params to this method is a wrapper over the message and signature to validate:

```
pub struct VerifyAuthorizationParams {
    pub authorization: Vec<u8>,
    pub message: Vec<u8>,
}
```

Further, we propose modifying the StorageMarketActor to call this method when validating `ClientDealProposal`s instead of validating signatures directly.

## Design Rationale

The idea is to create a flexible, lightweight endpoint that actors can expose to callers that might want to
validate its authorization. Some actors will have very obvious implementations: the account actor simply 
performs a signature validation, while an `m/n` multisig need only perform `m` signature validations.
Other actors might opt for creative implementations of such authorization based on their needs. Yet 
others can choose not to support this endpoint at all -- the Filecoin protocol's singleton builtin-actors
such as the Storage Power Actor, the System Actor, the Cron Actor, etc. will likely choose to omit this method.

## Backwards Compatibility

Introducing new methods to the builtin-actors needs a network upgrade, but otherwise breaks no backwards compatibility.

## Test Cases

Proposed test cases include:

- that the `verify_authorization` method on account actors can be called and succeeds with valid input
- that the `verify_authorization` method on account actors can be called, but fails with invalid input
- that storage deals can be made with the changes to the `StorageMarketActor`

## Security Considerations

We need to be careful with the security of the `verify_authorization` implementations of the
builtin-actors. User-defined contracts are free to implement these methods as they see fit.

This FIP only proposes adding the `verify_authorization` method to the account actor, which 
simply invokes the signature validation syscall.

## Incentive Considerations

This proposal is generally well-aligned with the incentives of the network. It can be considered
as a simpler replacement for FIP-0035, with the only drawback being that this proposal as currently written does not allow for multisigs to be storage clients. It would be trivial 
to add a similar `verify_authorization` method to the multisig actor, though.

## Product Considerations

This proposal is the first step towards enabling non-account actors to function as clients for
storage deals, which is a major product improvement. Furthermore, it enables future innovation 
that relies on the ability of non-account actors to authorize data as approved.

## Implementation

Partial implementation [here](https://github.com/filecoin-project/builtin-actors/pull/502)

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
