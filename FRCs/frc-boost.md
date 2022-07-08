---
title: New Markets Protocol for Storage Deals (Boost)
author: dirkmc, nonsense, jacobheun, brendalee
status: Draft
type: FRC
created: 2022-07-07
dependency: none
---

## Simple Summary

[Boost](https://github.com/filecoin-project/boost) is a tool for Storage Providers to manage data onboarding and retrieval on the Filecoin network. Boost replaces the go-fil-markets package in lotus with a standalone binary that runs alongside a Lotus daemon and Lotus miner. Currently, it supports the same protocols as the existing lotus markets subsystem, and adds new versions of the protocols used to propose a storage deal and check the deal’s status. 

## Abstract

Filecoin is a decentralized storage network consisting of many individual storage providers (SP). These SPs operate independently and take storage deals from the Filecoin network. As we see the amount of storage deals being made increasing, there are limitations making it difficult for SPs to handle large volumes of deals. 

Boost addresses these issues by introducing two new libp2p protocols, specifically for storage deals. The goals of Boost are the following: 

- **Improve the storage deal flow**: 
- **Improve visibility for Storage Providers into their systems**: Better visibility of fund allocation, deal states including data transfer, and sealing pipelines via a simple web interface to leverage the new markets APIs
- **Extensible data transfer**: online deals support fetching a CAR file over HTTP

The Boost module is still in development.  In the future, additional protocols will also be added which support market retrieval capabilities. 

## Change Motivation

The purpose of Boost is to become the reference implementation for Filecoin Markets (which will eventually replace the current version of Lotus Markets as the reference implementation). It is currently being developed as a standalone repository to allow the team to iterate quickly on a redesign of the system, prove the merit of the new design early and often through internal and community facing demos, and to be releasable as a standalone binary that can run alongside the existing Lotus process.
Planning for Boost was initiated after deep user research with Storage Providers.  This research sought to understand challenges and limitations that they faced as service providers on the Filecoin network.  For more information, see <https://www.notion.so/pl-strflt/Resulting-Bedrock-Ignite-Team-Epics-0973e4ee4db14a9c9e1837cb3c6ef27e>
## Specification

Boost introduces new versions of two libp2p protocols. The specifications are linked: 

[Propose Storage Deal Protocol](https://boost.filecoin.io/boost-architecture/libp2p-protocols#propose-storage-deal-protocol)

[Storage Deal Status Protocol](https://boost.filecoin.io/boost-architecture/libp2p-protocols#storage-deal-status-protocol)


## **Backwards Compatibility**

Boost is currently backwards compatible with go-fil-markets package. It supports the same endpoints for making storage and retrieval deals, getting the storage and retrieval ask, and getting the status of ongoing deals.

In the future, there is a possibility that we will move towards deprecating go-fil-markets in favor of the capabilities being built out in Boost. 

## **Security Considerations**

No changes to underlying proofs or security.

## **Incentive Considerations**

No change to incentives.

## **Product Considerations**

Additional libp2p protocols were introduced for storage deal proposal protocol and storage deal status protocol. 

## **Implementation**

[https://github.com/filecoin-project/boost](https://github.com/filecoin-project/boost)

## **Copyright**

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
