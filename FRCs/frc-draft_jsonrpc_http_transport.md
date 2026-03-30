---
fip: "XXXX"
title: JSON-RPC 2.0 HTTP Transport Conventions
author: Hubert Bugaj (@LesnyRumcajs)
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1247
status: Draft
type: FRC
created: 2026-03-30
---

# FRC-XXXX: JSON-RPC 2.0 HTTP Transport Conventions

## Simple Summary

This FRC standardizes how Filecoin JSON-RPC 2.0 endpoints map application-level errors to HTTP status codes. It defines a consistent mapping so that HTTP clients can detect error conditions from the status code alone, without parsing the full JSON response body.

## Abstract

The [JSON-RPC 2.0 specification](https://www.jsonrpc.org/specification) defines application-level error codes but is silent on HTTP transport behavior. [FRC-0104](https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0104.md) specifies the common JSON-RPC API methods but does not address how errors should be represented at the HTTP layer. This gap has led to divergent behavior across Filecoin node implementations: Forest returns HTTP 200 for all JSON-RPC errors, Lotus returns HTTP 500 for some, and third-party RPC providers each follow their own conventions.

This FRC specifies the HTTP transport conventions for Filecoin JSON-RPC endpoints, including HTTP status code mappings for JSON-RPC error codes, Content-Type requirements, HTTP method handling, batch request behavior, and notification responses. The goal is to enable consistent, predictable behavior across all Filecoin node implementations and RPC providers.

## Change Motivation

**Interoperability.** Clients, wallets, and dApps that switch between node implementations encounter different HTTP behavior for identical JSON-RPC errors. A client that checks HTTP status codes to detect failures will behave differently depending on whether it talks to Forest (200), Lotus (500), or a third-party provider. This forces client authors to implement provider-specific error handling or ignore HTTP status codes entirely.

**Pragmatic error detection.** Requiring clients to parse a potentially large JSON response body just to discover a parse error or missing method is wasteful. Mapping well-known JSON-RPC error codes to appropriate HTTP status codes allows lightweight HTTP-level error detection, which is particularly valuable for proxies, load balancers, and monitoring infrastructure.

**Observability.** HTTP-based monitoring tools, APM systems, and load balancers use status codes as a primary signal. When all responses return 200, these tools cannot distinguish healthy traffic from error traffic. When some errors return 500, false alerts are triggered for application-level conditions that do not indicate server failure.

## Specification

The key words "MUST", "MUST NOT", "SHOULD", "SHOULD NOT", and "MAY" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

This specification is based on the [JSON-RPC 2.0 Transport: HTTP](https://www.simple-is-better.org/json-rpc/transport_http.html) community draft.

### HTTP Method Requirements

- Servers MUST accept `POST` requests at their JSON-RPC endpoint(s).
- Servers MUST return `405 Method Not Allowed` for any HTTP method other than `POST` (e.g., `GET`, `PUT`, `DELETE`).

### Content-Type Requirements

- Requests MUST include the header `Content-Type: application/json`.
- Responses MUST include the header `Content-Type: application/json` when the response body contains JSON.
- Servers SHOULD return `415 Unsupported Media Type` when the request `Content-Type` is not `application/json`.

### HTTP Status Code Mapping

The following table defines the REQUIRED mapping between JSON-RPC conditions and HTTP status codes.

| Scenario | HTTP Status Code | JSON-RPC Error Code | Response Body |
|---|---|---|---|
| Successful result | `200 OK` | N/A | JSON-RPC result object |
| Notification (no `id`) | `204 No Content` | N/A | Empty |
| Parse error | `400 Bad Request` | `-32700` | JSON-RPC error object |
| Invalid Request | `400 Bad Request` | `-32600` | JSON-RPC error object |
| Invalid params | `400 Bad Request` | `-32602` | JSON-RPC error object |
| Missing or invalid JWT token | `401 Unauthorized` | N/A | Optional |
| Insufficient JWT permissions | `403 Forbidden` | N/A | Optional |
| Method not found | `404 Not Found` | `-32601` | JSON-RPC error object |
| Unsupported HTTP method | `405 Method Not Allowed` | N/A | Optional |
| Wrong Content-Type | `415 Unsupported Media Type` | N/A | Optional |
| Internal/server error | `500 Internal Server Error` | `-32603`, `-32099` to `-32000` | JSON-RPC error object |
| Application-defined error | `500 Internal Server Error` | Any code outside reserved range | JSON-RPC error object |
| Method not yet implemented | `501 Not Implemented` | `-32601` | JSON-RPC error object |

When the HTTP status code indicates an error (4xx or 5xx) and the error originated from JSON-RPC processing, the response body MUST still contain a valid [JSON-RPC 2.0 Error Object](https://www.jsonrpc.org/specification#error_object).

Application-defined errors (error codes outside the reserved `-32768` to `-32000` range) MUST return HTTP `500 Internal Server Error`. While these errors originate from application logic rather than the JSON-RPC protocol itself, they still represent error conditions that clients should be able to detect at the HTTP layer without parsing the response body.

### Batch Requests

- A batch request containing multiple JSON-RPC calls MUST return HTTP `200 OK` with a JSON array of response objects, regardless of individual success or failure within the batch.
- An empty batch request (`[]`) MUST return HTTP `200 OK` with a JSON-RPC Invalid Request error.

### Notifications

A JSON-RPC notification is a request without an `id` field. The server MUST NOT return a response body for notifications and SHOULD return HTTP `204 No Content`.

In a batch containing a mix of requests and notifications, the notifications MUST NOT produce entries in the response array. The batch response MUST return HTTP `200 OK`.

### Rate Limiting

Servers MAY return HTTP `429 Too Many Requests` to indicate rate limiting. This is an HTTP-layer concern independent of JSON-RPC processing and is not governed by this specification beyond acknowledging its use.

### WebSocket Transport

WebSocket transport is out of scope for this specification. WebSocket is a message-oriented protocol with no per-message status code mechanism analogous to HTTP status codes. JSON-RPC errors over WebSocket are communicated exclusively through the JSON-RPC error object in the message payload. WebSocket close codes ([RFC 6455 Section 7.4](https://www.rfc-editor.org/rfc/rfc6455#section-7.4)) are connection-level and SHOULD NOT be used to signal individual JSON-RPC errors.

## Design Rationale

### Why map errors to HTTP status codes?

The alternative approach — returning HTTP 200 for all JSON-RPC responses, including errors — maintains a clean separation between the transport layer (HTTP) and the application layer (JSON-RPC). Some implementations and libraries (e.g., Parity's `jsonrpsee`) follow this convention, and it is a defensible design choice.

However, the pragmatic benefits of mapping errors to HTTP status codes outweigh the theoretical purity of layer separation:

1. **Lightweight error detection.** An HTTP client can determine that an error occurred from the status code alone, without parsing the response body. This is especially valuable when the response body is large.
2. **Infrastructure compatibility.** Proxies, load balancers, CDNs, and monitoring tools are built around HTTP status codes. Returning 200 for errors makes these tools blind to failure conditions.
3. **Precedent.** The [JSON-RPC 2.0 Transport: HTTP](https://www.simple-is-better.org/json-rpc/transport_http.html) community draft defines this mapping. While not an official standard, it represents the most widely referenced specification for JSON-RPC over HTTP.

### Why not follow the Ethereum ecosystem?

The Ethereum JSON-RPC ecosystem has no consistent standard for HTTP status codes. Alchemy returns 400 for unsupported methods but 200 for parameter errors. Other providers return 200 for everything. Adopting any single provider's behavior as a standard would be arbitrary. By following the community draft specification, Filecoin can establish a principled convention that other ecosystems may also converge toward.

## Alternatives Considered

### Always return HTTP 200

Return HTTP 200 for all JSON-RPC responses, both successful and error. Non-200 codes are reserved exclusively for HTTP-layer failures (405, 415). This is the approach Forest currently follows and is used by libraries like Parity's `jsonrpsee`.

**Pros:** Clean separation between transport and application layers. Simple to implement — no mapping logic needed. Consistent with a strict reading of the JSON-RPC 2.0 specification, which is transport-agnostic.

**Cons:** Clients must always parse the full JSON response body to determine if an error occurred, which is wasteful for large responses. HTTP infrastructure (load balancers, monitoring, proxies) cannot distinguish success from failure traffic. Defeats the purpose of HTTP status codes as a lightweight signal.

### Always return HTTP 500 for all errors

Return HTTP 500 for any JSON-RPC error response, regardless of the specific error code. Successful responses return 200.

**Pros:** Simple binary signal — 200 means success, 500 means error. Easy to implement with no per-error-code mapping. Clients and monitoring tools can immediately detect errors.

**Cons:** Loses granularity — a client typo in a method name (which should be a 404) looks the same as a server crash (which is genuinely a 500). Retry logic that retries on 500 will wastefully retry client errors that can never succeed. Misrepresents client errors as server errors, polluting server error rate metrics. Does not follow the community draft specification or HTTP semantics.

## Backwards Compatibility

This FRC introduces changes to the HTTP status codes returned by Filecoin JSON-RPC endpoints. The impact on each known implementation:

- Lotus currently returns HTTP 500 for some JSON-RPC errors. Adopting this FRC requires mapping specific error codes to their designated HTTP status codes (e.g., -32601 to 404 instead of 500, -32600 to 400 instead of 500). Some cases may already be correct.

- Venus requires an audit of current HTTP status code behavior.

- Forest, currently, returns HTTP 200 for all JSON-RPC errors. Adopting this FRC requires returning non-200 status codes for reserved JSON-RPC error codes (-32700 through -32000). This is a behavior change but the response body (JSON-RPC error object) remains identical.

Clients that rely on specific HTTP status codes (e.g., treating only 200 as success, or expecting 500 for all errors) may need updates.

Implementations SHOULD document their migration timeline and consider a deprecation notice period before changing HTTP status code behavior. Ideally, all implementation changes should be coordinated to minimize confusion for users and developers.

## Security Considerations

This FRC does not introduce new security considerations. It changes which HTTP status codes accompany JSON-RPC error responses but does not alter the content, authentication, or authorization of those responses.

## Incentive Considerations

This FRC has minimal direct impact on storage incentives. Consistent HTTP transport behavior reduces development and integration costs for storage provider tooling, client libraries, and monitoring infrastructure, indirectly supporting network participation by lowering operational overhead.

## Product Considerations

Standardized HTTP status code behavior enables:

- **Portable client libraries** that work identically across Lotus, Forest, Venus, and third-party RPC providers.
- **Better monitoring and alerting** using standard HTTP observability tools without custom JSON parsing.
- **Consistent RPC provider behavior** across hosted providers (Glif, etc.), reducing user confusion.
- **Simpler proxy and load balancer configuration** that can route or retry based on HTTP status codes.

## Implementation

The following implementations will need changes to conform to this specification:

- [Lotus](https://github.com/filecoin-project/lotus): Audit current HTTP status code behavior via [go-jsonrpc](https://github.com/filecoin-project/go-jsonrpc). See related issue: [go-jsonrpc#91](https://github.com/filecoin-project/go-jsonrpc/issues/91).
- [Venus](https://github.com/filecoin-project/venus): Requires audit of current behavior.
- [Forest](https://github.com/ChainSafe/forest): Currently returns 200 for all JSON-RPC errors. Needs to map reserved error codes to appropriate HTTP status codes.

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
