---
fip: "0038"
title: Indexer Protocol for Filecoin Content Discovery
author: willscott, gammazero, honghaoq
status: Draft
type: FRC
created: 2022-06-24
discussion: https://github.com/filecoin-project/FIPs/discussions/337
spec-pr: https://github.com/filecoin-project/FIPs/pull/365/files
---

## Simple Summary

Indexers store mappings of content multi-hashes to provider data records. A client that wants to know where a piece of information is stored can query the indexer, using the CID or multi-hash of the content, and receive a provider record that tells where the client can retrieve the content and via which data transfer protocols.

## Abstract

Filecoin stores a great deal of data, but without proper indexing of that data, clients cannot perform efficient retrieval. To improve Filecoin content discoverability, Indexer nodes are developed to store mappings of CID multi-hashes to content provider records, for content lookup upon retrieval request. 

To provide index data to indexer nodes, there is the [Indexer Provider](https://lotus.filecoin.io/storage-providers/operate/index-provider/) that provides a software library for building an index data provider, and an index provider service that can run alongside with Storage Provider. Either of these may be used to tell the Indexer what content is retrievable from a storage provider. The Index Provider library or service sends updates to the Indexer via a series of [Advertisement](https://github.com/filecoin-project/storetheindex/blob/main/api/v0/ingest/schema/schema.ipldsch) messages. Each message references a previous advertisement so that as a whole it forms an advertisement chain. The indexer operates by consuming this chain from the oldest Advertisement not yet consumed, to the latest one. The Indexer fetches new advertisements periodically or in response to a notification from the Index Provider.

Indexer enables content discovery within Filecoin network today, it is also a fundamental component toward the end goal of universal retrieval across IPFS/Filecoin, i.e. to be able to efficiently retrieve Filecoin content from IPFS. Combining Indexer work for content discovery with IPFS/Filecoin interoperability work for content transfer, we aim to reach the end state of efficient and universal retrieval across IPFS and Filecoin network.

## Change Motivation

Primary reasons why Indexer is critical to the success of Filecoin network:

1. **Content Discovery and Retrieval**: 
Running Indexer is required for efficient content discovery and retrieval for Filecoin network, since Filecoin needs a CID to Storage Provider mapping to enable content retrieval. It is also an important step toward retrieval across IPFS and Filecoin, as Indexer will index both IPFS and Filecoin data and support efficient and universal retrieval across IPFS and Filecoin network as the end state.
2. **Better usage and growth of the network**: 
Making data more accessible to the network increases Filecoin data usage. This drives adoption of the network to onboard more data, resulting in more  data being discoverable and retrievable - it is a positive growth flywheel.


## Specification

### Terminology

Before we dive into the design details, here are a list of concepts we need to cover for Indexer:

- **Advertisement**: A record available from a publisher that contains, a link to a chain of multihash blocks, the CID of the previous advertisement, and provider-specific content metadata that is referenced by all the multihashes in the linked multihash blocks. The provider data is identified by a key called a context ID.
- **Announce Message**: A message that informs indexers about the availability of an advertisement. This is usually sent via gossip pubsub, but can also be sent via HTTP. An announce message contains the advertisement CID it is announcing, which allows indexers to ignore the announce if they have already indexed the advertisement. The publisher's address is included in the announce to tell indexers where to retrieve the advertisement from.
- **Context ID**: A key that, for a provider, uniquely identifies content metadata. This allows content metadata to be updated or delete on the indexer without having to refer to it using the multihashes that map to it.
- **Entries:** Represents the list of multihashes the content hosted by the storage provider. The entries are represented as an IPLD DAG, divided across a set of interlinked IPLD nodes, referred to as Entries Chunk.
- **Gossip PubSub**: Publish/subscribe communications over a libp2p gossip mesh. This is used by publishers to broadcast Announce Messages to all indexers that are subscribed to the topic that the announce message is sent on. For production publishers and indexers, this topic is `"/indexer/ingest/mainnet"`.
- **Indexer**: A network node that keeps a mappings of multihashes to provider records.
- **Metadata**: Provider-specific data that a retrieval client gets from an indexer query and passed to the provider when retrieving content. This metadata is used by the provider to identify and find specific content and deliver that content via the protocol (e.g. graphsync) specified in the metadata.
- **Provider**: Also called a Storage Provider, this is the entity from which content can be retrieved by a retrieval client. When multihashes are looked up on an indexer, the responses contain provider that provide the content referenced by the multihashes. A provider is identified by a libp2p peer ID.
- **Publisher**: Also referred to as _Index Provider_, This is an entity that publishes advertisements and index data to an indexer. It is usually, but not always, the same as the data provider. A publisher is identified by a libp2p peer ID.
- **Retrieval Addresses:** A list of addresses included in each advertisement that points to where you can retrieve from the advertised content.
- **Retrieval Client**: A client that queries an indexer to find where content is available, and retrieves that content from a provider.
- **Sync** (indexer with publisher): Operation that synchronizes the content indexed by an indexer with the content published by a publisher. A sync is initiated when an indexer receives and announces message, by an administrative command to sync with a publisher, or by the indexer when there have been no updates for a provider for some period of time (24 hours by default).

### Parties

**Data Providers** store data and make it available for retrieval clients to retrieve. They want to advertise the availability of this content so that any consumers can easily find it. Data providers will also want to revoke advertisements of content that they no longer provide and update their internal location of content.

**Index Providers (Publishers)** maintain a history of changes to content stored by a Data Provider, and present the sequence of changes to Indexers as advertisements.  Index Providers sent notifications to Indexers to announce that new advertisements are available.  Usually a Data Provider is also its own Index Provider, but these can be different entities.   

**Indexer nodes** receive Advertisement announcements published by Index Providers, allowing Indexers to discover Data Providers and to be notified of updates to the Data Provider content. The announcements let Indexers know that new advertisements are available.  Indexers retrieve Advertisements from the Index Providers, to get Data Provider information and associated index multihash data. The Indexer decides if and when to fetch index data from an Index Provider based on the policies the Indexer is configured with. Indexers may reroute client requests to other indexers if they do not handle that content.

**Clients** want to issue query style requests for content to an Indexer node and receive a set of Data Provider records that inform the client how and where to retrieve that content.  The response from an Indexer contains a set of Data Provider records, each having the Provider's ID and addresses.  Each record contains the protocol that the client must use to retrieve the data (e.g. graphsync) as well as other information that the client presents to the Provider.  This additiona data is used by the Provider to retrieve the content, and may consist of a deal ID or other lookup keys specific to the Provider. If multiple Providers provide the same content, the client may choose based on input from a reputation system, network response time, location, or any other information available to the client.


### Data Provier Interface:

Data providers maintain local records of the CIDs of the content they store and the changes to this content. Providers must be able to present this as an ordered series of changes to sets of multihashes over time. For indexing, a multihash extracted from a CID is used identify content, since indexed content does not track how the content is encoded. The source CID is the CID of a merkle-tree of content hosted by the provider.
  
Each addition of content is represented a set of multihashes accompanied by context information (metadata), that is within the domain of interpretation of the Provider, and an unique identifier (context ID) that identifies this context. Therefore a context ID links a set of multihashes to metadata that pertains to that set of multihashes.  Removal of content is done by deletion of a context ID, which represents removing a set of multihashes and metadata identified by that context ID.  Metadata identified by context ID may also be replaced by new metadata, as the information pertaining to the associated set of multihashes changes (change of location, storage deal, etc.).

Each of these changes is a presented as a separate record, that is linked to the previous record, forming an ordered log changes to the Provider's content. Indexers track these changes to keep their view of the Provider's content in sync with the Provider.

### Advertisements:

An Advertisement is a data structure that packages information about a change to Provider content. The Advertisement contains the Provider ID and addresses, content metadata, context ID, a link to a chain of multihash blocks, and a link to the previous Advertisement. The Advertisement is also signed by the Provider or publisher of the Advertisement, using a signature computed over all of these fields.

Each Advertisement is uniquely identified by a content ID (CID) that is used to retrieve that Advertisement from the Index Provider. This makes the advertisement an immutable record.  The link to the chain of multihash blocks and each link in the chain is also a CID, making the chain of multihash blocks immutable as well. The Advertisement is what is communicated from an Index Provider to an Indexer to supply the Indexer with index data.

Advertisement as IPLD schema:
```
# EntryChunk captures a chunk in a chain of entries that collectively contain the multihashes
# advertised by an Advertisement.
type EntryChunk struct {
    # Entries represent the list of multihashes in this chunk.
    Entries [Bytes]
    # Next is an optional link to the next entry chunk. 
    Next optional Link
}

# Advertisement signals availability of content to the indexer nodes in form of a chunked list of 
# multihashes, where to retrieve them from, and over protocol they are retrievable.
type Advertisement struct {
    # PreviousID is an optional link to the previous advertisement.
    PreviousID optional Link
    # Provider is the peer ID of the host that provides this advertisement.
    Provider String
    # Addresses is the list of multiaddrs as strings from which the advertised content is retrievable.
    Addresses [String]
    # Signature is the signature of this advertisement.
    Signature Bytes
    # Entries is a link to the chained EntryChunk instances that contain the multihashes advertised. 
    Entries Link
    # ContextID is the unique identifier for the collection of advertised multihashes.
    ContextID Bytes
    # Metadata captures contextual information about how to retrieve the advertised content.
    Metadata Bytes
    # IsRm, when true, specifies that the content identified by ContextID is no longer retrievalbe from the provider.
    IsRm Bool
}
```

- The ContextID is limited to a maximum of 64 bytes.
- The Metadata is limited to a maximum of 1024 bytes (1KiB).

The metadata field contains provider-specific data that pertains to the set of multihashes being added.  The metadata is prefixed with a protocol ID number followed by data encoded as per the protocol.  The content of the metadata is up to the provider, but if more than the limited size is needed, then the metadata should contain an ID identifying mode complex data stored by the provider.

Graphsync is the most commonly used protocol for retrieving content from a content provider. The filecoin-graphsync transport metadata is currently defined as follows:

Uvarint protcol `0x0910` (TransportGraphsyncFilecoinv1 in the [multicodec table](https://github.com/multiformats/multicodec/blob/master/table.csv#L134)). This is followed by a CBOR-encoded struct of:
```go
type GraphsyncFilecoinV1 struct {
	// PieceCID identifies the piece this data can be found in
	PieceCID cid.Cid
	// VerifiedDeal indicates if the deal is verified
	VerifiedDeal bool
	// FastRetrieval indicates whether the provider claims there is an unsealed copy
	FastRetrieval bool
}

An index entry is always a multihash, extracted from a CID (since indexed content does not track how the content is encoded).  This should be the multihash from the CID of a merkle-tree of content hosted by the provider.

### Announcement

Index Providers announce the availability of new Advertisements by publishing a notification on a known gossipsub pub-sub channel, `/indexer/ingest/mainnet`, that indexer nodes subscribe to. Alternatively, the Index Provider may post an announcement message directly to an indexer over HTTP. Typically, gossip pub-sub is used and is preferred because the Index Providers will not necessarily know how to contact the Indexers, but will know the filecoin chain nodes that will relay gossip pub-sub to Indexers.

After receiving an announcement, the Indexer checkes if it has already retrieved the announced Advertisement, and if so, ignores the announcement.  If the Advertisement has not yet been retrieved, the Indexer contacts the Index Provider, at an address supplied in the announcement, to retrieve the announced Advertisement.  The addresses in the announcement can be libp2p addresses or an HTTP address, and the Indexer uses the addresses to retrieve the Advertisement over graphsync or HTTP respectively. 

Announcement message as golang struct:
```go
{
	Cid:      cid.Cid
	Addrs     [][]byte
	ExtraData []byte `json:",omitempty"`
}
```

The extra data is used by Index Providers to pass identity data to filecoin nodes in order for the filecoin nodes allow the announcement to be forwarded over gossip pub-sub.

### Advertisement Chain
Once the Indexer has received an Advertisement it checks if the previous Advertisement has already been retrieved, and if not, retrieves it. This continues until all previously unseen Advertisements are retrieved or until there are no more Advertisements to retrieve, i.e. the end of the chain is reached.

After the entire chain of unprocessed Advertisements has been retrieved, the Indexer walks the chain in order from oldest to newest and retrieves the chain of multihash blocks linked to by each advertisement.  A multihash block is a chunk of the multihashes in the change set with a link to the next block. Splitting all the total multihashes into blocks enables block-based data transfer mechanisms to fetch the multihash data and servies as a pagination mechanism for other transports.

```
   Oldest                         Newest 
+----------+     +--------+     +--------+
|   Ad A   |     |  Ad B  |     |  Ad C  |
| prev=nil |<----| prev=A |<----| prev=B |
+----+-----+     +---+----+     +---+----+
     |               |              |
     V               V              V
[multihashes]  [multihashes]  [multihashes]
     |               |              |
     V               V              V 
[multihashes]  [multihashes]  [multihashes]
```

### Index Data Storage

All of the multihashes in the multihash blocks are read and stored in the indexer as a mapping of multihashes to a list of providerID-contextID in the Advertisement, and each providerID-contextID is mapped to its metadata record. This allows a multihash to resolve to a multiple provider, context ID, metadata records. It also allows a providerID-contextID to be used to identify metadata records to update and delete.

```
Multihash ---+     +-----------------------+
             |     | ProviderID-ContextID--|----> Metadata
Multihash ---+---> | ProviderID-ContextID--|----> Metadata
             |     +-----------------------+
Multihash ---+
```

The Data Provider addresses from the Advertisement are stored separately, and are updated with each advertisement that has a different retrieval address for the Data Provider. When the Indexer responds to a client query, it adds the current Data Provider addresses to each data Provider record in the response.

When an Advertisement is received that has a ProviderID-ContextID that is already stored in the indexer but different metadata, the indexer updates the metadata that the ProviderID-ContextID maps to.

A Find result has a list of MultihashResults.  Each element of that list contains a Multihash and a list of ProviderResults for that multihash.  Each Provider result has a ContextID, Metadata, and Provider.  The Provider has an ID and a list of Addrs.

## **Backwards Compatibility**

This FIP does not change actors behavior so it does not require any Filecoin network update.

## **Security Considerations**

This FIP does not touch underlying proofs or security.

## **Incentive Considerations**

No change to incentives. In the future this could support retrieval incentive.

## **Product Considerations**

No change to product considerations, except that increased content discoverability and retrieval capability is a net improvement to the Filecoin network.

In the near future, the product should include controls on what contents can be retrieved, so Storage Providers would have the ability to turn off content that they don’t want to be accessible for retrieval.

## **Implementation**

Indexer:

[https://github.com/filecoin-project/storetheindex](https://github.com/filecoin-project/storetheindex)

Index Provider:

[https://github.com/filecoin-project/index-provider](https://github.com/filecoin-project/index-provider)

Indexer Design:

[https://github.com/filecoin-project/storetheindex/blob/main/doc/indexer_ecosys.png](https://github.com/filecoin-project/storetheindex/blob/main/doc/indexer_ecosys.png)

## **Copyright**

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
