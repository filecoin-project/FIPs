---
fip: "xxx"
title: Remove Mining Reserve
author: jnthnvctr (@jnthnvctr)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1030 
status: Draft
type: Technical
category: Core
created: 2024-07-25
---



# FIPXXXX: Set the Mining Reserve to Zero 


## Simple Summary

This proposal aims to remove the mining reserve tokens [282.9m](https://filfox.info/en/address/f090) by setting its value to 0. This does not preclude other FIPs from being proposed to create new tokens (as future incentives, funding iniatives etc).


## Abstract 

The [mining reserve](https://spec.filecoin.io/systems/filecoin_token/token_allocation/) was intended to be a reserve of tokens to incentivize future types of mining. Even in the spec, this is noted to potentially "not be enough" and the "community [will] decide whether this reserve is enough". This proposal seeks to remove the mining reserve. This does not preclude new tokens from being created - rather that any new incentives should be created at the point when new forms of mining are introduced.

## Change Motivation

There are a number of reasons why the mining reserve can be viewed as a net cost: 
1. The role of the mining reserve is non-standard - at the time of authoring, no other L1 has this amount of supply left up to potential release (~50% of the current supply, 15% of the total max supply) which creates a large gap between the FDV and Market Cap.
2. The mining reserve reinforces an anchor around Filecoin being a fixed supply currency. Given there is always the ability for the community to fork to change the supply, this is an unnecessary meme to reinforce - but constricts discussion.
3. The mining reserve requires a FIP to use (the same process for creating new tokens) - in the event these tokens are needed; its unclear there would be any _less_ pushback in the community if were to create new sources of dilution.
4. Filecoin's inflation is already quite high relative to other ecosystems - removing the mining reserve should change the default from creating net new sources of inflation to bring new value flows into the ecosystem (vs optimizing the inflation already in the network)


## Spec

1. Set balance of `f090` to 0.
2. Adjust all circulating supply dependencies and the invariant checks to recognize the total supply is no longer 2b given the mining reserve has been set to 0. 

## Rationale 

The proposal aims to move away from relying a fixed amount of tokens in the mining reserve that might be used for new mining, to having new FIPs be proposed explicitly creating (or redistributing existing) incentives.

## Incentive Considerations

The proposed change requires future explicit proposals (aiming to incentivize new forms of mining) to explicitly mint new tokens. This should not change the difficulty of making such proposals, as both (using the mining reserve, creating new tokens) would have the short term effect of diluting stakeholders. 

## Product Considerations

TODO

## Implementations

1. Set the balance of `f090` to 0.
2. Adjust all circulating supply dependencies and the invariant checks to recognize the total supply is no longer 2b given the mining reserve has been set to 0. 


## Copyright Waiver

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
