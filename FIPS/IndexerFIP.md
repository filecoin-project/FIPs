# Indexer FIP

[Indexer FIP](https://www.notion.so/7d156be0cd5643269241cf2d2e13f25e)

## **Simple Summary**

Indexers store mappings of content multi-hashes to provider data records. A client that wants to know where a piece of information is stored can query the indexer, using the CID or multi-hash of the content, and receive a provider record that tells where the client can retrieve the content and via which data transfer protocols.
Content can be queried at [cid.contact](http://cid.contact).

## **Abstract**

Filecoin stores a great deal of data, but without proper indexing of that data, clients cannot perform efficient retrieval. To improve Filecoin content discoverability, Indexer nodes are developed to store mappings of CIDs to content providers for content lookup upon retrieval request. 

To provide index to indexer node, there is an [Indexer Provider](https://lotus.filecoin.io/storage-providers/operate/index-provider/) service that runs alongside with Storage Provider, which tells the Indexer what contents this storage provider has. Index Provider sends updates to the Indexer via a series of [Advertisement](https://github.com/filecoin-project/storetheindex/blob/main/api/v0/ingest/schema/schema.ipldsch) messages. Each message references a previous advertisement so that as a whole it forms an advertisement chain. The state of the indexer is a function of consuming this chain from the initial Advertisement to the latest one, and delta of indexer content is updated periodically.

Indexer enables content discovery within Filecoin network today, it is also a fundamental component toward the end goal of universal retrieval across IPFS/Filecoin, i.e. to be able to efficiently retrieve Filecoin content from IPFS. Combining Indexer work for content discovery with IPFS/Filecoin interoperability work for content transfer, we aim to reach the end state of efficient and universal retrieval across IPFS and Filecoin network.

## **Change Motivation**

There are many reasons why Indexer is critical to the success of Filecoin network:

1. **Content Discovery and Retrieval**: 
Running Indexer is required for efficient content discovery and retrieval for Filecoin network, since Filecoin needs a CID to Storage Provider mapping to enable content retrieval. It is also an important step toward retrieval across IPFS and Filecoin, as Indexer will index both IPFS and Filecoin data and support efficient and universal retrieval across IPFS and Filecoin network as the end state.
2. **Better usage and growth of the network**: 
By making data more accessible to the network, we could increase Filecoin data usage, which helps drive up adoption of the network to onboard more data, and then make more  data discoverable and retrievable - it is a positive growth flywheel.

## **Terminology**

Before we dive into the design details, here are a list of concepts we need to cover for Indexer:

- **Advertisement**: A record available from a publisher that contains, a link to a chain of multihash blocks, the CID of the previous advertisement, and provider-specific content metadata that is referenced by all the multihashes in the linked multihash blocks. The provider data is identified by a key called a context ID.
- **Announce Message**: A message that informs indexers about the availability of an advertisement. This is usually sent via gossip pubsub, but can also be sent via HTTP. An announce message contains the advertisement CID it is announcing, which allows indexers to ignore the announce if they have already indexed the advertisement. The publisher's address is included in the announce to tell indexers where to retrieve the advertisement from.
- **Context ID**: A key that, for a provider, uniquely identifies content metadata. This allows content metadata to be updated or delete on the indexer without having to refer to it using the multihashes that map to it.
- **Entries:** Represents the list of multihashes the content hosted by the storage provider. The entries are represented as an IPLD DAG, divided across a set of interlinked IPLD nodes, referred to as Entries Chunk.
- **Gossip PubSub**: Publish/subscribe communications over a libp2p gossip mesh. This is used by publishers to broadcast Announce Messages to all indexers that are subscribed to the topic that the announce message is sent on. For production publishers and indexers, this topic is `"/indexer/ingest/mainnet"`.
- **Indexer**: A network node that keeps a mappings of multihashes to provider records.
- **Metadata**: Provider-specific data that a retrieval client gets from an indexer query and passed to the provider when retrieving content. This metadata is used by the provider to identify and find specific content and deliver that content via the protocol (e.g. graphsync) specified in the metadata.
- **Provider**: Also called a Storage Provider, this is the entity from which content can be retrieved by a retrieval client. When multihashes are looked up on an indexer, the responses contain provider that provide the content referenced by the multihashes. A provider is identified by a libp2p peer ID.
- **Publisher**: This is an entity that publishes advertisements and index data to an indexer. It is usually, but not always, the same as the data provider. A publisher is identified by a libp2p peer ID.
- **Retrieval Addresses:** A list of addresses included in each advertisement that points to where you can retrieve from the advertised content.
- **Retrieval Client**: A client that queries an indexer to find where content is available, and retrieves that content from a provider.
- **Sync** (indexer with publisher): Operation that synchronizes the content indexed by an indexer with the content published by a publisher. A sync is initiated when an indexer receives and announces message, by an administrative command to sync with a publisher, or by the indexer when there have been no updates for a provider for some period of time (24 hours by default).

## **Specification**

**Data providers** have local indices of their content. They want to advertise the availability of this content so that any consumers can easily find it. Data providers will also want to revoke advertisements of content that they no longer provide.

**Indexer nodes** want to discover data providers and to track updates provided by the data providers.  They also want to handle incoming content requests and resolve them to providers who have that content.  Indexers may reroute client requests to other indexers if they do not handle that content.

**Clients** want to issue query style requests for content to an indexer node and receive a set of providers that have that content.  The response should include any other information about how to choose between providers as well as information that the provider may have requested to present to them to authenticate the request? (e.g. deal ID)

Indexer nodes discover new data providers and receive notification of content updates, by receiving notifications published on a known gossip pub-sub topic.  Indexers can also discover this by looking at on-chain storage provider activity.  The notifications let indexers know that new data is *available* and that index entries can be fetched from an existing or a new provider. The indexer decides if and when to pull the actual index data, and which kind of index, from a provider, based on its own policies pertaining to the data provider.

**Overview design:**

![](https://s3.us-west-2.amazonaws.com/secure.notion-static.com/44c88146-a25c-4732-92df-1c98b814bf63/Untitled.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=AKIAT73L2G45EIPT3X45%2F20220419%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20220419T012946Z&X-Amz-Expires=86400&X-Amz-Signature=0f8321e348f5a6a8a275b069d179460f51ef208a7c1ef0987e149e6eda34055e&X-Amz-SignedHeaders=host&response-content-disposition=filename%20%3D%22Untitled.png%22&x-id=GetObject)

**Data Provier Interface:**

Data providers will have local indices of their content. Abstractly, we can think of the resources exposed by a data provider as a tree of the following:

```jsx
Catalog (List of Indexes)
Catalog/<id> (Individual Index)
Catalog/<id>/multihashes (list of multihashes in the Index)

Catalog/<id>/TBD (semantic for selection)
```

A provider has a Catalog of one or more indices, where the current index is the set of all multihashes known to the provider, and the other indices are past versions of it, each representing the multihashes at some previous time. Semantically, changes to the catalog of indexes by the provider are seen as happening in a globally ordered log of additions and revocations, each referencing the previous action.  lndexers are able to track these changes to keep their view of a provider's Index current.

**Advertisements:**

Index providers will publish advertisements on new indices on the `ContentIndex` gossipsub pub-sub channel, which indexer nodes can subscribe to. The format of these advertisement messages of catalog entries looks like this:

```jsx
{ Index: <multihash of current index manifest>,
  Previous: <multihash of previous index manifest>,
  Provider: <libp2p.PeerID>,
  Signature: <signature over index, previous>
}
```

When an indexer sees an advertisement, the indexer checks to see if it already has the latest Index ID.  If it does, then the advertisement is ignored. Otherwise, the indexer sends a request to the data provider to get the set of changes starting from the previous Index ID in the advertisement up to the current index ID in the advertisement.  The indexer internally resolves the libp2p.PeerID to current libp2p endpoints.

Besides receiving advertisements over pub-sub, the indexer can request the latest advertisement directly from a data provider. This is useful when indexing for a discovered data provider that is not publishing advertisements.

Note: The signature is computed over the current and the previous ID in each entry.  This guarantees that the order is correct according to the signing provider.

An index ID is always a multihash, extracted from a CID (since indexed content does not track how the content is encoded).  This should be the multihash from the CID of a merkle-tree of content hosted by the provider.

**Advertisement Chain:**

The indexer keeps a record of the advertised Index multihashes it has received data for.  The indexer continues walking the chain of Index multihashes backward until it receives a response containing an Advertisement with the `Previous` multihash being the last one the indexer has already seen, or when the end of the chain is reached (no Previous).  When all the missing links in the chain of Indexes have been received, these are applied, in order, to update the indexer's records of multihashes and providers. 

**Index Request-Index Provider Response:**

Over the Provider-Indexer protocol, an indexer requests the following:

```
{ "prev_index_id": <get changes starting at this index>,
  "index_id": <get changes up to this index>,
  "start": n, // optional - start at this record (for pagination)
  "count": n, // optional - maximum number of records to fetch
}
```

And indexer receives a possibly paginated response that has a subset of the change logs and the associated advertisement message:

```
{ "totalEntries": n, // size of provider's catalog
  "error": "",       // optional. indicate the request could not be served
  "advertisement": {
    Index: n3 <ID of index manifest>,
    Previous: n2 <ID of previous index manifest>,
    Provider: <libp2p.AddrInfo>, Signature: <signature(index, previous)>
  },
  "start": n,         // starting entry number
  "entries": [
    {"add_multihashes": [<multihash>, ...], "metadata": "???",
     "del_multihashes": [<multihash>, ...]}, 
    {"add_multihashes": [<multihash>, ...], "metadata": "???"},
}
```

This is a set of changes that are applied to the index data, to go from the `prev_multihash` to the multihash in the request.  Each entry contains a set of new multihashes that the provider provides, and possibly a set of multihashes to remove that are no longer provided.  A limited-size (≤ 100 bytes) metadata field contains provider-specific data that pertains to the set of multihashes being added.  The metadata is prefixed with a protocol ID number followed by data encoded data as per the protocol.  The content of the meta data is up to the provider, but if more then the limited size is needed, then the metadata should contain an ID identifying mode complex data stored by the provider.

It is worth noting that the same multihash may appear in entries of several different advertisements of a provider. For instance, if a Filecoin Storage Provider receives a new deal that includes a CID, that has a multihash, of some content it is already indexing, it may notify this update to the indexer node by including an entry for that multihash with new metadata (e.g. the new expiration date of the deal) in the next advertisement.
When the indexer node comes across an advertisement that includes a multihash that it is already indexing for the provider, it will simply update the metadata with that of the latest advertisement. Finally, if all the deals that include that multihash in a Storage Provider expire, it can notify the indexer of this by simply adding that multihash in the list of `del_multihashes` for the next advertisement.

The response may be paginated either by the client requesting a maximum number of entries or by the server delivering up to a configured maximum number of entries.  To get the remaining entries, a subsequent request is made with its `start` set to the number of entries from the previous response.  So, if `totalEntries` equals `100` and the response contained 50 entries, the follow-up request should specify `50` for `start` to get the remaining entries.  This continues until the indexer has the complete response.

**Client Interface:**

The client interface is what indexer clients use to ask an indexer which providers are able to provide content identified by multihashes. Queries for a multihash should locate the providers within 10s of milliseconds.

A client sends a request containing a set of multihashes. The indexer responds with a list of provider_ids for each multihash that was requested. 

Response data:

```
{
  "multihash_providers": {
    <multihash_from_req>: [
      {"provider_id": <libp2p_peer_id>, "metadata": {???} }, ..],
    <multihash_from_req>: [
      {"provider_id": <libp2p_peer_id>, "metadata": {???} }, ..],
    <multihash_from_req>: null,
    ...
  },
  "providers": [
    { "ID": <libp2p_peer_id>,
      "Addrs": [<libp2p_multiaddr>, ..]
    },
    ...
  ],
  "providers_signature": <signature_over_providers">
}
```

Response data contains encoded values returned from the in-memory cache.  Responses may be paginated if there are a large number of values.

## **Design Rationale**

Key design considerations are:

- **Indexer uses multihashes, not entire CIDs, to refer to indexed content**
The codec in a CID is independent of the content that is indexed or how the content is retrieved from a provider.
- **Indexer keeps an in-memory cache of multihashes that have been asked for by clients, unless configured for in-memory only operation**
Most multihashes in an index will not be requested, since clients will generally only ask for the top-level multihash for any object. Therefore only the set that is actually requested by clients is kept in memory. The remaining will be kept in space-efficient secondary storage.  A generation cache eviction mechanism for the in-memory cache prevents unbounded growth.
- **[storethehash](https://github.com/ipld/go-storethehash) will serve as persistent storage**
Designed to efficiently store hash data, requires only two disk reads to get any data stored for a multihash.  This is being evaluated against more mature systems because of a high confidence assumption that it will save significant space.  However, that savings needs to be very significant to outweigh the risk and development cost of a new storage facility.  The indexer will be constructed to allow different implementations to be chosen as appropriate for different deployments.  Having an embedded storage implementation may reduce admin work and allow the indexer to be used more easily as a library.
- **Indexer will track multihash distribution and usage**
The indexer will keep statistics on multihashes that can be used to predict the growth rate of data stored and cached as well as the distribution of multihashes over different providers.  The usage of multihashes will also be tracked and will show the demand (by clients) for various multihahses.
- **Indexer will not index `IDENTITY` Multihashes**
The Indexer will not index `IDENTITY` multihashes and filters out any such multihash from the received advertisements. See: [Appendix C, Handling of `IDENTITY` Multihashes](https://www.notion.so/Indexer-Node-Design-fbd1e7d3110c4b1fb154b31f2585e6ff).
- **Load minimization for Storage Provider**
    
    The indexer updates over graphsync, meaning once a day indexer connects and ask for delta of new CIDs found available on the nodes since last day, and store them to multiple providers, while indexer only need to get it from one of them. This saves bandwidth by deduping when CIDs are provided from multiple providers, so it will only take relatively small amount of bandwidth compared to actual data (Storage Provider can expect minimal bandwidth impact), with at most one or two additional connections that are short-lived for indexing.
    

## **Backwards Compatibility**

This FIP does not change actors behavior so it does not require any Filecoin network update.

## **Test Cases**

The following test cases should be covered:

- Index Provider functionality test:
    - Ability to index storage deals
    - Storage Provider able to publish index to an Indexer node
- Scalability test: indexer need to be able to handle index storage at scale (hundreds of billions of index)
- Availability test:
    - 3-9s node uptime
    - Responsiveness to indexer advertisement queries
- Latency test:
    - Indexer query response latency: <300ms p95
    - Indexer ingestion latency: <60 sec p95

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

## **Copyright**

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).