---
fip: "<to be assigned>"
title: Filecoin Encryption Envelope
author: "Jakub Sztandera (@Kubuxu), Natalie Bravo (@bravonatalie)"
discussions-to: https://github.com/filecoin-project/FIPs/discussions/1253
status: Draft
type: FRC
created: 2026-10-13
---

# FRC-XXXX: Filecoin Encryption Envelope

## Simple Summary

A standard format for encrypting data stored on Filecoin, built on COSE (RFC 9052). The envelope encodes encryption metadata (algorithm, nonce, recipient descriptors) separately from the ciphertext, enabling keyless inspection and pluggable key management. Two encryption schemes are defined: a simple AES-256-GCM mode and a seekable chunked mode for large files that supports random-access decryption.

## Abstract

This proposal defines the Filecoin Encryption Envelope (FEE): a COSE-based container that pairs a self-describing metadata envelope with detached ciphertext. The format supports:

- **AES-256-GCM** (IANA algorithm 3) for simple, interoperable encryption.
- **Chunked AES-256-GCM with the STREAM construction** (private-use algorithm -65793) for seekable encryption of large files with O(chunk_size) random-access cost, and an optional authenticated commitment to the exact plaintext length.
- **Multi-recipient descriptors** that decouple key management from the data path, allowing the same encrypted blob to be accessible via different key management systems without re-encryption.

The envelope is independent of any specific key management solution. Possession of the content encryption key (CEK) and knowledge of the algorithm is sufficient to decrypt, regardless of how the key was obtained.

FEE is a profile of COSE: the subset of COSE structures, header rules and options that FEE implementations agree on, so that envelopes written by one implementation are read by another.

## Change Motivation

### Private data on Filecoin needs encryption

Filecoin's Proof of Data Possession (PDP) requires that storage providers have access to the raw data to generate Merkle proofs, and further exposes random 32-byte segments of raw data in public via on-chain proof submission. Client-side encryption is the only way to achieve confidentiality guarantees from both storage providers and the public at large.

### No standard exists

Every application that encrypts data for Filecoin storage today must define its own envelope format, key encoding, and metadata conventions. This leads to:

- **No interoperability**: encrypted data produced by one tool cannot be decrypted by another, even when the same key is available.
- **Key management lock-in**: without a common envelope, switching between key management solutions requires re-encrypting all data.
- **Duplicated effort**: each team implements AEAD, chunking, nonce management, and metadata encoding from scratch.

### Large files need seekable encryption

Filecoin stores large objects. Forcing full download and decryption to read a byte range is impractical. A standard seekable encryption scheme enables HTTP Range-style access patterns over encrypted data, which media streaming, database pages, and incremental synchronization depend on.

### Relationship to broader access controls

This proposal addresses the encryption envelope, one component of a broader access control architecture for Filecoin that also includes gated data propagation and on-chain access policies. The envelope is designed to be composed with these mechanisms: for example, an on-chain policy might govern who can obtain a wrapped CEK, while the envelope format defined here governs how that CEK is used to protect the data. The other components are out of scope for this proposal.

## Specification

The key words MUST, MUST NOT, REQUIRED, SHOULD, SHOULD NOT, RECOMMENDED, MAY and OPTIONAL are to be interpreted as described in RFC 2119 and RFC 8174 when, and only when, they appear in all capitals.

### Terms

- **CBOR and CDDL:** CBOR (RFC 8949) is the binary format used for the envelope. CDDL describes the allowed structure and types. In examples, `bstr` is a byte string, `tstr` is text, and `h''` is a byte string containing no bytes.
- **Headers and labels:** headers are maps of parameters. Their keys are called labels; for example, label `1` means `alg`, the algorithm identifier.
- **Protected and unprotected headers:** both are readable without a key. Protected headers are included in the AEAD calculation, so changes are detected; they are not encrypted. COSE also calls these two maps "buckets".
- **Content and recipient layers:** the content layer encrypts the data with the content encryption key (**CEK**). A recipient record describes how to obtain that CEK, usually by decrypting a wrapped copy with a key-encryption key (**KEK**). Recipient headers have their own rules, separate from content headers.
- **Authentication tag and AAD:** AES-GCM produces encrypted bytes and a tag used to detect tampering. Additional authenticated data (**AAD**) is checked by the tag but is not encrypted. COSE calls the structure used to build content AAD `Enc_structure`.
- **Key derivation:** a key derivation function (**KDF**) produces a key from secret input and context. `COSE_KDF_Context` is COSE's structure for that context. It is different from content AAD.

### Overview

An encrypted blob is the concatenation of two parts:

```
┌─────────────────────────┬───────────────────────┐
│  COSE Envelope (CBOR)   │  Ciphertext (bytes)   │
└─────────────────────────┴───────────────────────┘
```

The COSE envelope is a self-delimiting CBOR value. A parser reads the envelope using CBOR incremental decoding; the remaining bytes are the ciphertext. No length prefix or external framing is needed.

### COSE Envelope Structure

The envelope is a standard COSE encryption structure with a **detached payload**: the `ciphertext` field within the COSE structure is `nil`, and the actual ciphertext follows the envelope as a separate byte sequence.

- Use **COSE_Encrypt0** (CBOR tag 16) when the CEK is supplied without a recipient record.
- Use **COSE_Encrypt** (CBOR tag 96) when one or more recipient records are included. The recipients array MUST be nonempty and MUST NOT contain nested recipient layers.

The CBOR tag identifies the COSE structure and is separate from the AES-GCM authentication tag. The content AAD context MUST be `Encrypt0` for tag 16 and `Encrypt` for tag 96, so switching between the two structures changes the AAD and requires new authentication tags.

#### CDDL

```cddl
Filecoin-Encryption-Envelope = COSE_Encrypt0_Tagged / COSE_Encrypt_Tagged

COSE_Encrypt0_Tagged = #6.16(COSE_Encrypt0)
COSE_Encrypt0 = [
  protected : bstr .cbor protected_header_map,
  unprotected : unprotected_header_map,
  ciphertext : nil                      ; detached payload
]

COSE_Encrypt_Tagged = #6.96(COSE_Encrypt)
COSE_Encrypt = [
  protected : bstr .cbor protected_header_map,
  unprotected : unprotected_header_map,
  ciphertext : nil,                     ; detached payload
  recipients : [+ COSE_recipient]
]

COSE_recipient = [
  protected : empty_or_serialized_map,  ; form chosen by the recipient algorithm
  unprotected : header_map,
  ciphertext : bstr                     ; wrapped CEK
]

label = int / tstr
header_map = { * label => any }
empty_or_serialized_map = bstr .cbor header_map / bstr .size 0

; --- Content header maps ---

protected_header_map = {
  1 => algorithm_id,                                ; alg (REQUIRED)
  16 => "application/vnd.filecoin-encryption+cose", ; typ (REQUIRED)
  5 => bstr,                                        ; iv (REQUIRED): 12 bytes (scheme 1) or 7 bytes (scheme 2)
  ? 3 => content_type,                              ; content type of the plaintext (OPTIONAL)
  ? -1 => uint,                                     ; chunk_size: REQUIRED for scheme 2, absent for scheme 1
  ? -65789 => uint,                                 ; plaintext_length: scheme 2 only (OPTIONAL)
  ? -65792 => app_metadata,                         ; application metadata (OPTIONAL)
  ? 2 => [+ label],                                 ; crit (OPTIONAL)
  * label => any                                    ; extension parameters
}

unprotected_header_map = {
  * label => any   ; MAY be empty; MUST NOT carry FEE content parameters or crit
}

content_type = tstr / uint

algorithm_id = 3 / -65793
; 3      = AES-256-GCM (IANA registered)
; -65793 = Chunked-AES-256-GCM-STREAM (private-use)

app_metadata = { * tstr => any }
; String-keyed map for application-level metadata.
; Applications define their own keys.
```

The content header maps list the FEE fields explicitly. They MUST NOT be replaced by an unrestricted `header_map`, because the content fields have stricter type and placement rules than COSE in general.

### Protected Headers

Protected headers are serialized as a CBOR byte string and authenticated as part of the AEAD additional authenticated data (AAD). Every content parameter this proposal defines is protected. They MUST NOT be modified after encryption.

| Label  | Name               | Type        | Required                | Description                                              |
| ------ | ------------------ | ----------- | ----------------------- | -------------------------------------------------------- |
| 1      | `alg`              | int         | REQUIRED                | Algorithm identifier                                     |
| 3      | `content_type`     | tstr / uint | OPTIONAL                | Media type of the plaintext (e.g., `"application/pdf"`)  |
| 5      | `iv`               | bstr        | REQUIRED                | 12-byte nonce (scheme 1) or 7-byte base nonce (scheme 2) |
| 16     | `typ`              | tstr        | REQUIRED                | `"application/vnd.filecoin-encryption+cose"`             |
| -1     | `chunk_size`       | uint        | Scheme 2 only           | Plaintext bytes per chunk (algorithm-specific parameter) |
| -65789 | `plaintext_length` | uint        | OPTIONAL, scheme 2 only | Exact plaintext byte count                               |
| -65792 | `app_metadata`     | map         | OPTIONAL                | Application metadata (see below)                         |

Label `-1` is algorithm-specific ([RFC 9052 §3.1](https://www.rfc-editor.org/rfc/rfc9052#section-3.1)), so its meaning depends on the `alg` of the header it appears in.

- In the content header with `alg = -65793` (`Chunked-AES-256-GCM-STREAM`), `-1` means `chunk_size`.
- In the content header with `alg = 3` (`AES-256-GCM`), `-1` MUST NOT be present.
- In ECDH-ES recipient headers, `-1` holds the ephemeral public key, as the COSE registry defines. The `chunk_size` meaning is not registered; it relies on `alg` alone.

The content `iv` parameter (label 5) MUST appear in the protected header and MUST NOT appear in the unprotected header. Protected headers are readable before authentication, so the decryptor obtains the IV before checking the tag. Placing the IV in the protected header makes it part of the content AAD.

`plaintext_length` is defined in [Plaintext Length](#plaintext-length).

All protected values are unverified until an AEAD tag succeeds. See [What authentication proves](#what-authentication-proves).

#### Application Metadata

The `app_metadata` field is a CBOR map with string keys, carried in the protected headers so that its integrity is guaranteed by the AEAD authentication. Applications MAY use this field to store metadata about the plaintext, such as how the CEK was derived.

Applications define their own string keys. Implementations MUST ignore keys they do not understand. A decoder MUST reject an `app_metadata` value that is not a map, or a map with a key that is not a text string.

### Unprotected Headers

The content unprotected header MAY be empty. The FEE content parameters (`alg`, `typ`, `iv`, `chunk_size`, `plaintext_length` and `app_metadata`) MUST appear in the protected header, and a decoder MUST reject an envelope that carries any of them in the content unprotected header. `crit` MUST NOT appear in an unprotected header. A Partial IV (label 6) MUST be rejected in either content header; nonces are never reconstructed from it. Unknown non-critical parameters in either header are ignored.

### Header Validation

Decoders MUST apply these rules:

- Tags 16 and 96 MUST use their matching array structures. The content ciphertext field MUST be `nil`.
- Content protected bytes MUST contain exactly one CBOR map with no trailing data. Content protected headers cannot be empty, because FEE requires `alg`, `typ` and `iv`.
- Recipient protected bytes MUST follow the selected recipient algorithm's empty-or-map rule; an encoded map MUST also contain no trailing data. The zero-length byte string `h''` contains no CBOR item and is different from the encoded empty map `h'a0'`.
- Header parameters MUST have the types, values and locations required by FEE and by the recipient algorithm. Content-header requirements do not automatically apply to recipient headers.
- The protected `typ` value MUST be `application/vnd.filecoin-encryption+cose`. `chunk_size` MUST be present for scheme 2 and absent for scheme 1. The protected IV MUST have the length required by the selected scheme.
- Encoders MUST NOT produce duplicate map keys, and decoders MUST reject them. A header label appearing in both the protected and unprotected maps at the same layer MUST also be rejected. Header labels are compared by their decoded values, not by their encoded bytes.

#### Critical headers

Header maps MAY include extension parameters. Processors MUST handle `crit` (label 2) and other standard COSE headers per RFC 9052. If present, `crit` MUST be protected, and every listed label MUST also be protected, understood and processed. Otherwise, the message MUST be rejected.

FEE-required parameters do not need to appear in `crit`, since FEE readers already process them. This restates the COSE rule so that readers reject messages containing critical extensions they do not understand, rather than silently ignoring them.

### Additional Authenticated Data (AAD)

Both schemes construct the AAD using the COSE `Enc_structure` as defined in [RFC 9052 §5.3](https://www.rfc-editor.org/rfc/rfc9052#section-5.3):

```
Enc_structure = [
  context : "Encrypt0" / "Encrypt",   ; "Encrypt" for tag 96, "Encrypt0" for tag 16
  protected : bstr,                   ; the protected header bytes as received
  external_aad : bstr                 ; empty (h'')
]
```

The protected headers are authenticated together with the ciphertext. Any change to them causes authentication to fail.

Processors MUST use each protected-header byte string exactly as received in the envelope. They MUST NOT decode and re-encode, normalize, or otherwise reconstruct it. Different CBOR encodings can represent the same values with different bytes, and those differences would break authentication or derive a different recipient key.

`Enc_structure` MUST be constructed from the received protected-header bytes as specified in RFC 9052 §§5.3 and 9. When a recipient algorithm uses `COSE_KDF_Context`, it MUST be constructed according to RFC 9053 §§5.2 and 9 and the rules of that recipient algorithm.

### Parser Requirements

Envelope parsing happens before content authentication, so decoders MUST treat the input as untrusted.

- Encoders MUST use definite-length arrays, maps, byte strings and text strings throughout the envelope and serialized protected maps, including nested values. This rule does not interpret the contents of opaque byte strings as CBOR and does not apply to the detached ciphertext.
- Encoders MUST encode every integer and length argument in its shortest form.
- Encoders MUST NOT use CBOR floating-point values anywhere in the envelope.
- Decoders SHOULD reject indefinite-length items, non-minimal encodings and floating-point values in those locations.
- Decoders MUST reject malformed CBOR and values that violate the FEE structure or field types.
- Decoders MUST NOT reject an otherwise valid envelope only because map keys use a different order. FEE does not require one deterministic encoding of the whole envelope.
- Implementations MUST apply resource limits during parsing, before excessive allocation or recursion, and SHOULD document their limits on envelope size, nesting depth and collection sizes.

Whether these limits are shared interoperability limits is an open question (see [Open Questions](#open-questions)).

### Scheme 1: AES-256-GCM (Algorithm 3)

Standard AES-256-GCM as registered in the IANA COSE Algorithms registry.

- **Algorithm ID**: 3
- **Key size**: 256 bits (32 bytes)
- **IV**: 12 bytes, randomly generated, stored in the protected header `iv` (label 5)
- **Tag size**: 128 bits (appended to the ciphertext by the AEAD operation)
- **Ciphertext**: `AES-256-GCM(key, iv, plaintext, AAD)`, a single AEAD operation over the entire plaintext

The ciphertext following the envelope is:

```
[encrypted_data || authentication_tag]
```

where `authentication_tag` is 16 bytes. This scheme is not seekable and is limited to 2^32 - 2 blocks (about 64 GiB) of plaintext by AES-GCM. A decoder cannot release any plaintext before verifying the single tag, so implementations typically apply a much lower limit; scheme 2 is intended for large objects. `chunk_size` and `plaintext_length` MUST NOT appear in a scheme 1 envelope.

### Scheme 2: Chunked AES-256-GCM with STREAM (Algorithm -65793)

A seekable encryption scheme that splits plaintext into fixed-size chunks, each independently encrypted with AES-256-GCM. The construction follows the STREAM design from Hoang, Reyhanitabar, Rogaway, and Vizár (2015), adapted by projects such as age and Google Tink.

- **Algorithm ID**: -65793 (private-use range)
- **Key size**: 256 bits (32 bytes)
- **Base nonce**: 7 bytes, randomly generated, stored in the protected header `iv` (label 5)
- **Chunk size**: stored in the protected header `chunk_size` (label -1). Default: 262,144 bytes (256 KiB).
- **Plaintext length**: optionally committed in the protected header `plaintext_length` (label -65789) when the length is known before encryption.

#### Chunk Size Constraints

`chunk_size` MUST be an integer from 4,096 bytes (4 KiB) through 16,777,216 bytes (16 MiB). Implementations MUST support 262,144 bytes (256 KiB), the default and interoperability baseline. Other sizes within those bounds MAY be supported; unsupported sizes MUST fail explicitly.

| Constraint | Value                     | Rationale                                                                                                       |
| ---------- | ------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Minimum    | 4,096 bytes (4 KiB)       | Below this, per-chunk overhead (16-byte tag) becomes significant and nonce space is consumed rapidly.           |
| Maximum    | 16,777,216 bytes (16 MiB) | Larger chunks reduce seekability benefit and increase memory requirements.                                      |
| Default    | 262,144 bytes (256 KiB)   | Balances seek granularity, overhead ratio (about 0.006%), and memory use. Aligned with common I/O buffer sizes. |

#### Per-Chunk Nonce Derivation

Each chunk is encrypted with a unique 12-byte nonce:

```text
nonce = base_nonce || chunk_index || last_flag
         7 bytes      4 bytes BE    1 byte
```

Where:

- `base_nonce` is the 7-byte value from the protected `iv` header.
- `chunk_index` is the zero-based chunk index, encoded as a 4-byte big-endian unsigned integer.
- `last_flag` is `0x01` for the final chunk and `0x00` for every other chunk.

Every chunk uses the same AAD, the envelope-level `Enc_structure`. The nonce is what binds each chunk to its position and to whether it is final, so reordering, insertion and truncation fail authentication.

For example, if the final chunk is removed, the preceding chunk was encrypted with `last_flag = 0x00`. Treating it as final requires `last_flag = 0x01`, which gives a different nonce, so authentication fails.

The chunk index MUST NOT wrap. The number of chunks MUST be between `1` and `2^32 - 1`, inclusive. With the default chunk size of 256 KiB, this allows plaintext of approximately 1 PiB.

#### Ciphertext Layout

The ciphertext is the concatenation of independently authenticated chunks:

```text
[chunk_0_ciphertext || tag_0]
[chunk_1_ciphertext || tag_1]
...
[chunk_(chunk_count - 1)_ciphertext || tag_(chunk_count - 1)]
```

Each authentication tag is 16 bytes. Every chunk except the final one contains exactly `chunk_size` plaintext bytes, so its ciphertext is `chunk_size + 16` bytes.

The final chunk has one valid form for each plaintext length:

| Plaintext                      | Final chunk                                                            |
| ------------------------------ | ---------------------------------------------------------------------- |
| Empty                          | One chunk at index `0`, containing only the 16-byte authentication tag |
| Exact multiple of `chunk_size` | A full chunk of exactly `chunk_size` plaintext bytes                   |
| Any other nonempty length      | The remaining `1` through `chunk_size - 1` plaintext bytes             |

An extra empty final chunk MUST NOT be emitted for plaintext whose length is an exact multiple of `chunk_size`, and decoders MUST reject such an encoding.

These rules give every plaintext length, including zero, exactly one valid ciphertext length.

#### Length Derivation

The encoder computes the chunk count from the plaintext size:

```text
chunk_count = max(1, ceil(plaintext_size / chunk_size))
```

The decoder derives the layout from the ciphertext length alone:

```text
stride            = chunk_size + 16
chunk_count       = ceil(ciphertext_length / stride)
last_chunk_length = ciphertext_length - (chunk_count - 1) × stride
plaintext_size    = ciphertext_length - 16 × chunk_count
```

Before attempting decryption, the decoder MUST:

- require `ciphertext_length >= 16`;
- derive a `chunk_count` from `1` through `2^32 - 1`;
- reject a final ciphertext chunk shorter than 16 bytes;
- accept a 16-byte final chunk only when `chunk_count = 1`, where it represents empty plaintext.

These checks validate the layout only. Each chunk's authentication tag MUST still be verified during decryption.

#### Plaintext Length

`plaintext_length` (label -65789) is the exact number of plaintext bytes and may be zero. It is optional and appears only in the protected header of scheme 2. Every chunk authenticates the protected header, so verifying any one chunk also verifies the intended total length. A range read can then detect a shortened or extended blob without reading the final chunk.

An encoder MAY write `plaintext_length` when it knows the length before emitting the envelope; otherwise it omits it. If the plaintext it consumes has a different length, the encoder MUST fail and MUST NOT emit the final chunk. Earlier chunks may already have been emitted.

When `plaintext_length` is present, the decoder MUST compute:

```text
expected_chunk_count       = max(1, ceil(plaintext_length / chunk_size))
expected_ciphertext_length = plaintext_length + 16 × expected_chunk_count
```

and reject the object if `expected_ciphertext_length` differs from the actual ciphertext length of the same object version. The decoder still derives the layout from the actual ciphertext length and applies the checks in [Length Derivation](#length-derivation). The value is unverified until a chunk's tag verifies.

#### Range Decryption

Range decryption needs the envelope length and the exact blob length of the same object version. For data stored with PDP, the blob length comes from the piece's PieceCIDv2, which encodes the exact size of the stored bytes ([FRC-0069](https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0069.md)); this is trustworthy when the PieceCID itself comes from a trusted source, such as the on-chain data set. A length from elsewhere, such as an HTTP response, is unverified. Decoders MUST NOT release a chunk's plaintext before its tag verifies.

To find the envelope length, a reader can fetch a prefix of the blob and parse it. A 4 KiB first read covers typical envelopes, which are a few hundred bytes. Only a prefix that ends before the envelope does is worth extending: the reader fetches more, for example doubling the read each time, up to a fixed limit such as 1 MiB, and rejects the object beyond it. Any other decode error fails at once, since more bytes cannot change it.

To decrypt a plaintext byte range `[offset, offset + length)`:

1. Parse the envelope to get `envelope_length`, `chunk_size`, the base nonce and, if present, `plaintext_length`.
2. Set `ciphertext_length = blob_length - envelope_length`. Derive the layout and apply the checks in [Length Derivation](#length-derivation) and, when `plaintext_length` is present, [Plaintext Length](#plaintext-length).
3. Require a nonempty range within `[0, plaintext_size)`. An empty range authenticates nothing.
4. Compute the affected chunks:
   - `first_chunk = floor(offset / chunk_size)`
   - `last_chunk = floor((offset + length - 1) / chunk_size)`
5. For each chunk `i` from `first_chunk` through `last_chunk`:
   1. Fetch from offset `envelope_length + i × (chunk_size + 16)`: `chunk_size + 16` bytes, or `last_chunk_length` bytes when `i = chunk_count - 1`.
   2. Derive `nonce_i`, with `last_flag = 0x01` only when `i = chunk_count - 1`.
   3. Decrypt with AES-256-GCM using `nonce_i` and the envelope AAD.
6. Concatenate the decrypted chunks and slice to the requested range.

Only the affected chunks are fetched and decrypted, so a fixed-size range costs O(chunk_size). A range read authenticates only the chunks it reads. With `plaintext_length` present and an exact ciphertext length for the same object version, a verified chunk confirms the declared length, so a shortened or extended blob is rejected. Without it, a range that does not include the final chunk cannot detect truncation. In neither case does a range read authenticate unread chunks or prove that a remote source holds the unread bytes.

### Multi-Recipient Support

When multiple parties should be able to decrypt, the envelope uses **COSE_Encrypt** (tag 96) with a recipients array. Each recipient entry carries a wrapped copy of the content encryption key (CEK).

Each recipient MUST identify its key-distribution algorithm using `alg`, in exactly one of its two header maps. Header placement and processing MUST follow that algorithm's COSE requirements. A key identifier `kid` (label 4, a byte string) is RECOMMENDED wherever a decryptor may hold more than one key, since without it the only way to find the right recipient is to attempt every unwrap.

Two recipient algorithms are profiled here. Other recipient algorithms MAY be used, provided their identifiers, key derivation and header rules are specified. FEE implementations do not need to support every recipient algorithm.

#### A256KW (algorithm -5)

AES Key Wrap (RFC 3394) under a 256-bit key-encryption key shared in advance.

- The recipient protected field MUST be a zero-length byte string (RFC 9053 §6.2.1), and `alg = -5` MUST be in the unprotected map.
- The wrapped CEK is exactly 40 bytes. Any other length is malformed.
- AES Key Wrap is deterministic: two recipients wrapping the same CEK under the same KEK produce identical wrapped keys.

#### ECDH-ES + A256KW (algorithm -31) over X25519

Ephemeral-static key agreement with the recipient's X25519 public key, followed by A256KW.

- `alg` MUST be in the recipient protected map and MUST NOT be in its unprotected map. Encoders MUST emit the protected header `{1: -31}`, encoded as `h'a101381e'`.
- The unprotected header carries `kid` and the sender's ephemeral public key at label -1 as a `COSE_Key`: `{1: 1 (kty: OKP), -1: 4 (crv: X25519), -2: x}`.
- Encoders MUST NOT include the salt (label -20) or the PartyU and PartyV parameters (labels -21 through -26). FEE fixes the salt as empty and the party information as `nil`, and decoders derive the key with those values.
- The key-encryption key is derived with HKDF-SHA-256 (RFC 5869), as RFC 9053 §§5.1 and 6.3.1 require. The X25519 shared secret is the input keying material, the salt is empty, and the info parameter is the `COSE_KDF_Context` (RFC 9053 §5.2) `[-5, [nil, nil, nil], [nil, nil, nil], [256, h'a101381e']]`, giving a 32-byte KEK.
- The CEK is wrapped under that KEK with A256KW, giving a 40-byte wrapped key.
- The `COSE_KDF_Context` MUST use the recipient's original serialized protected bytes, as required by RFC 9052 §8.5.5 and RFC 9053 §5.2. The content envelope's protected bytes cannot be used in their place.

JOSE derives ECDH-ES keys with the NIST SP 800-56A single-step KDF (RFC 7518 §4.6), which produces a different KEK, so JOSE implementations cannot be reused for this step unchanged.

#### Recipient examples

The two recipient forms look like this in CBOR diagnostic notation:

```
[h'', {1: -5, 4: key_identifier}, wrapped_cek]
[h'a101381e', {-1: ephemeral_public_key, 4: recipient_key_identifier}, wrapped_cek]
```

Here `h''` means no bytes, not an encoded empty map. In the second example, `h'a101381e'` is the serialized map `{1: -31}`. The ephemeral public key is a `COSE_Key`; identifiers and the wrapped CEK are byte strings.

The A256KW placement comes from COSE. Protected `alg = -31` is a FEE profile choice: COSE requires `alg` in the recipient layer and uses that layer's protected bytes in the KDF context, but does not require `alg` to be protected. Fixing its location makes those KDF bytes unambiguous across implementations.

#### Key Management Considerations

This proposal does not mandate a specific key wrapping or key agreement algorithm. The choice depends on the application's key management infrastructure:

- **AES Key Wrap (A256KW, algorithm -5)**: suitable when a shared symmetric wrapping key exists between parties.
- **ECDH-ES + AES Key Wrap (algorithm -31)**: appropriate for public-key-based recipient schemes where the sender knows each recipient's public key.

Recipients within a single envelope MAY use different key wrapping algorithms. For example, the same encrypted blob could have one recipient using AES Key Wrap for a centralized KMS and another using ECDH-ES for a public-key scheme. COSE natively supports heterogeneous recipient arrays.

### Content Encryption Key (CEK) Requirements

- The CEK MUST be exactly 32 bytes (256 bits).
- A CEK MUST NOT be used for more than one encryption. Each encryption, including a retry of the same plaintext or an aborted attempt, needs a new CEK. Wrapping one CEK for several recipients of the same encryption is not reuse. CEK generation and derivation are left to the key-management system (see [Nonce uniqueness and CEK reuse](#nonce-uniqueness-and-cek-reuse)).
- Implementations MUST reject an all-zero CEK, including one recovered by unwrapping.
- Encoders MUST generate a fresh IV or base nonce from a cryptographically secure random source for every encryption. Libraries SHOULD NOT let applications supply one; test tooling that needs reproducible output can fix it through an interface that is not exposed to applications.
- Implementations SHOULD zeroize key material from memory after use.

## Design Rationale

### Why COSE?

Several container formats were considered:

| Format              | Pros                                                                                                   | Cons                                                                                                        |
| ------------------- | ------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| **COSE (RFC 9052)** | IETF standard, CBOR-native, built-in multi-recipient, IANA algorithm registry, compact binary encoding | Less tooling than JOSE in web ecosystems                                                                    |
| **JOSE/JWE**        | Widespread web adoption                                                                                | JSON overhead, no binary payload support without Base64, less natural fit for content-addressed binary data |
| **CMS (RFC 5652)**  | Mature, widely deployed                                                                                | ASN.1/DER complexity, heavyweight for this use case                                                         |
| **Custom format**   | Maximum flexibility                                                                                    | No ecosystem, no review, interop from scratch                                                               |

COSE was chosen because:

1. CBOR is the natural encoding for Filecoin/IPLD ecosystems.
2. The multi-recipient model maps directly to decoupled key management.
3. The algorithm registry provides a clear path for registering the chunked scheme.
4. Detached payloads are a first-class concept in COSE.

COSE supports message forms and options that FEE does not need. FEE therefore defines a small, explicit profile, so that implementations agree on the envelope structure, headers and authenticated bytes.

### Why detached payload?

In standard COSE, the ciphertext is carried inside the COSE structure. This proposal uses detached mode (ciphertext = nil) with the actual ciphertext concatenated after the envelope. This enables:

- **Streaming**: the envelope can be parsed before the (potentially very large) ciphertext is available.
- **Independent storage**: the envelope and ciphertext could, in principle, be stored or transmitted separately.
- **Seekable access**: for the chunked scheme, the ciphertext must be byte-addressable relative to the envelope boundary. Concatenation makes offset arithmetic trivial.

### Why the STREAM construction for seekable encryption?

COSE defines no seekable or chunked encryption format. All IANA-registered COSE AEAD algorithms operate on the payload as a single unit. Industry precedent for seekable authenticated encryption consistently uses the STREAM construction:

- **Google Tink Streaming AEAD**: per-segment AES-GCM with derived nonces
- **age (C2SP)**: ChaCha20-Poly1305 with 64 KiB chunks
- **STREAM (Hoang et al., 2015)**: the theoretical foundation

The STREAM nonce construction (base_nonce || chunk_index || last_flag) provides:

- **Chunk independence**: any chunk can be decrypted without processing preceding chunks
- **Order enforcement**: reordering chunks produces wrong nonces, so authentication fails
- **Truncation detection**: removing the last chunk means a non-final chunk is treated as final, producing a nonce mismatch
- **Insertion detection**: inserted chunks shift indices, breaking all subsequent nonces

### Why is the IV protected?

COSE permits the IV in either header. Protected headers are readable before authentication, so placing the IV there costs the decryptor nothing: it can read the IV, then verify the tag. In exchange, the IV becomes part of the content AAD, and every FEE content parameter lives in one authenticated location. A decoder can reject any FEE parameter found in the unprotected header instead of deciding which copy to trust.

### Why one final-chunk form?

If a plaintext that is an exact multiple of `chunk_size` could end either in a full chunk or in a full chunk followed by an empty one, the same plaintext would have two valid ciphertext lengths. A single form gives every plaintext length exactly one ciphertext length, which is what makes the `plaintext_length` check exact.

### Why a plaintext length instead of a chunk count?

`plaintext_length` determines both the chunk count and the exact size of the final chunk, while a stored chunk count determines only the final chunk's index. A count cannot detect a final chunk that was shortened without being removed. Because `plaintext_length` is protected, any authenticated chunk also authenticates it, so a range reader detects a truncated object without fetching the final chunk. The parameter is optional because streaming encoders often do not know the length before writing the header.

### Why app_metadata in protected headers?

Application metadata, such as an application-defined identifier, is integrity-sensitive: if an attacker could swap it without detection, a consumer might associate the encrypted blob with the wrong content. Placing `app_metadata` in the protected headers covers it with the AEAD authentication.

The trade-off is that all metadata values must be known at encryption time and are immutable. For content-addressed storage, where the data itself is immutable, this is the appropriate default.

### Why private-use algorithm and header IDs?

The chunked AEAD scheme uses a private-use algorithm ID, and `app_metadata` and `plaintext_length` use private-use header labels. These values are in the COSE private-use range (less than -65536), offset from -65536 to reduce collision risk with other private-use allocations:

| Value  | Range                 | Purpose                    |
| ------ | --------------------- | -------------------------- |
| -65793 | Private-use algorithm | Chunked-AES-256-GCM-STREAM |
| -65792 | Private-use header    | `app_metadata`             |
| -65789 | Private-use header    | `plaintext_length`         |

Label -65789 is used rather than redefining -65791, which existing experimental formats use for a chunk count. Giving that label a second meaning would make the two formats indistinguishable on the wire.

The `chunk_size` parameter uses algorithm-specific header label -1 (the COSE-standard mechanism for per-algorithm parameters), requiring no registry allocation. Label -1 is registered as the ECDH-ES ephemeral key, so this use relies on the meaning being scoped by `alg`; registering the chunked scheme would allow its parameters to be registered too.

## Backwards Compatibility

This proposal defines a new format; there is no earlier FEE standard to remain compatible with.

Experimental formats that preceded this proposal are not compatible with it.

## Test Cases

Cross-implementation test vectors are maintained alongside the implementations listed below. They cover scheme 2 envelopes with a direct CEK (tag 16) and with recipients (tag 96), including:

- an empty plaintext (one tag-only final chunk)
- a single-chunk and a multi-chunk plaintext
- a plaintext that is an exact multiple of `chunk_size`
- A256KW and ECDH-ES+A256KW recipients in one envelope
- whole-object decryption, range decryption and recipient unwrapping in both implementations

Scheme 1 is implemented only in the TypeScript library, so no cross-implementation vectors cover it yet.

## Security Considerations

### What authentication proves

Envelope metadata is unverified until a relevant AEAD tag succeeds. Before then, fields such as `chunk_size`, `plaintext_length`, content type and application metadata MAY guide bounded parsing and retrieval but MUST NOT be trusted. After authentication, application metadata is still only a claim by a CEK holder; an application that relies on a content identifier in it needs to check it against the decrypted plaintext.

Content tags do not cover the recipient array, so reordering or removing recipients does not invalidate them. Successful decryption proves knowledge of the CEK, not sender identity or an authenticated access-control policy; those properties require a separate mechanism.

Authentication failures are indistinguishable: a wrong CEK and a modified header, ciphertext or tag produce the same error.

### Nonce uniqueness and CEK reuse

AES-GCM requires a distinct key/nonce pair for each encryption operation. All chunks of one FEE encryption use the same CEK with distinct per-chunk nonces; the counter MUST NOT wrap.

Scheme 1 uses a random 12-byte nonce. Scheme 2 uses a random 7-byte base nonce and derives each chunk's nonce from it, so the per-object randomness of scheme 2 is 56 bits. If one CEK were used for many scheme 2 objects, the chance of two objects sharing a base nonce would reach about 50% after about 2^28 encryptions. A shared nonce under the same key exposes the XOR of the two plaintexts and allows tag forgery. Scheme 1 has more margin but the same failure mode. This is why FEE forbids CEK reuse.

A fresh CEK can be generated at random, or derived from a master key and a context that changes for every encryption, such as a random salt carried in `app_metadata`. A derived CEK is recoverable by anyone holding the master key and the context; a random one must be wrapped or stored. A CEK derived from an object identifier alone, such as `KDF(master_key, plaintext_CID)`, repeats when the same object is encrypted again, so it does not meet this requirement.

Retransmitting stored ciphertext is not another encryption. A counter that can address about 1 PiB does not make that a safe workload for one key; see RFC 9053 §4.1.1 for AES-GCM usage limits.

### Streaming decryption

Each chunk is released as soon as its tag verifies, so a truncated or tampered stream can yield valid leading plaintext followed by an error. Callers MUST treat any error from a streaming decryption as invalidating the whole object, and discard any plaintext already received.

### Key commitment

AES-GCM does not commit to its key: a sender can construct a ciphertext that authenticates under two different CEKs. In a multi-recipient envelope, a malicious sender could therefore give different recipients different CEKs that each decrypt the same object to different plaintexts. Successful decryption proves possession of a CEK and nothing about who produced the object or what other recipients see.

### Chunk size and authentication granularity

Smaller chunk sizes increase authentication granularity (less data processed before detecting tampering) but also increase per-chunk overhead and reduce maximum plaintext size for a given nonce counter width. The 4-byte counter supports up to `2^32 - 1` chunks; with the default 256 KiB chunk size this allows approximately 1 PiB of plaintext.

### Untrusted parsing

The envelope is parsed before any tag is checked. Decoders MUST reject malformed or non-conforming CBOR and MUST bound envelope size, nesting depth and collection sizes before allocating (see [Parser Requirements](#parser-requirements)). Header labels duplicated within a map or across buckets are rejected so that two implementations cannot read different values from the same envelope.

### Metadata confidentiality

Protected and unprotected headers are visible without the decryption key. This is by design (enabling keyless inspection) but means:

- The encryption algorithm and parameters are disclosed.
- The plaintext length is disclosed when `plaintext_length` is present; it is also approximately derivable from the ciphertext length.
- The plaintext content type, if present, is disclosed.
- Application metadata is disclosed. A content hash such as the plaintext CID links the encrypted object to any public copy of the same bytes and shows when two uploaders stored the same file, so applications SHOULD NOT put one in `app_metadata`. A hash of the CID prevents browsing but still lets anyone holding a candidate CID confirm a match.
- The number and type of recipients are disclosed.

Applications that require metadata confidentiality should either omit sensitive fields from `app_metadata` or apply an outer encryption layer.

## Incentive Considerations

This proposal does not change storage provider incentives. Storage providers store and prove possession of the encrypted blob exactly as they would any other data; PDP and payment flows are unaffected. A standard format lets clients store confidential data without relying on provider trust, which may increase demand for storage of private data.

## Product Considerations

### Developer experience

The format is designed so that a developer with access to a CBOR library and a platform AES-256-GCM implementation can build a compatible encryptor/decryptor without specialized cryptographic libraries.

### Storage overhead

| Component                   | Overhead                                                                                                                          |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| COSE envelope               | About 75 bytes without recipients; about 265 bytes with one A256KW and one ECDH-ES recipient. Grows with metadata and recipients. |
| Scheme 1 authentication tag | 16 bytes                                                                                                                          |
| Scheme 2 per-chunk tags     | 16 bytes per chunk; 64 KiB per 1 GiB of plaintext at 256 KiB chunks                                                               |

```
1 GiB / 256 KiB = 4,096 chunks
4,096 × 16 bytes = 65,536 bytes = 64 KiB
65,536 / 1,073,741,824 × 100 = 0.006103515625%
```

For a 1 GiB plaintext with 256 KiB chunks, authentication tags add approximately 0.0061%, plus the encoded envelope size.

## Implementation

- [`filecoin-encryption-envelope`](https://github.com/FilOzone/synapse-sdk/tree/master/packages/filecoin-encryption-envelope) (TypeScript, Node.js and browsers): schemes 1 and 2, A256KW recipients, range decryption. It does not implement ECDH-ES key recovery yet.
- [`go-fee`](https://github.com/filecoin-project/go-fee) (Go): scheme 2, A256KW and ECDH-ES+A256KW (X25519) recipients, range decryption. It does not implement scheme 1.

The two are pinned against each other by cross-implementation test vectors in [`go-fee/vectors`](https://github.com/filecoin-project/go-fee/tree/main/vectors).

## Open Questions

1. **Should a minimum set of recipient algorithms be required?** A256KW and ECDH-ES+A256KW over X25519 are profiled above, but implementations may support either. Requiring one would guarantee that any two implementations can exchange wrapped keys.
2. **How should applications signal chunk size preference?** When an application re-encrypts data or produces encrypted content for a known consumer, should there be a negotiation mechanism for chunk size, or is the default sufficient?
3. **Media type registration:** the `typ` header uses `application/vnd.filecoin-encryption+cose`. Should this be registered as an IANA media type, or is the COSE `typ` header sufficient for identification?
4. **Algorithm registration:** should Chunked-AES-256-GCM-STREAM be registered with IANA, so that it and `chunk_size` get registered identifiers?
5. **Parser limits:** should limits on envelope size, nesting depth and collection sizes be shared interoperability limits, or implementation-specific limits that each implementation documents?
6. **Key commitment:** should a future scheme add key commitment, for example the [C2SP chunked encryption](https://c2sp.org/chunked-encryption) construction?
7. **Final-chunk flag width:** moving from a final-chunk flag byte to a single flag bit would add 7 bits to the chunk counter. It is not proposed here, for simplicity.

## TODO

- [ ] Gather feedback from storage application developers and key management providers.
- [ ] Resolve the open questions above.

## References

- [RFC 2119 — Key words for use in RFCs to Indicate Requirement Levels](https://www.rfc-editor.org/rfc/rfc2119)
- [RFC 3394 — Advanced Encryption Standard (AES) Key Wrap Algorithm](https://www.rfc-editor.org/rfc/rfc3394)
- [RFC 5869 — HMAC-based Extract-and-Expand Key Derivation Function (HKDF)](https://www.rfc-editor.org/rfc/rfc5869)
- [RFC 7518 — JSON Web Algorithms (JWA)](https://www.rfc-editor.org/rfc/rfc7518)
- [RFC 8174 — Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words](https://www.rfc-editor.org/rfc/rfc8174)
- [RFC 8949 — Concise Binary Object Representation (CBOR)](https://www.rfc-editor.org/rfc/rfc8949)
- [RFC 9052 — CBOR Object Signing and Encryption (COSE): Structures and Process](https://www.rfc-editor.org/rfc/rfc9052)
- [RFC 9053 — CBOR Object Signing and Encryption (COSE): Initial Algorithms](https://www.rfc-editor.org/rfc/rfc9053)
- [RFC 9596 — COSE "typ" (type) Header Parameter](https://www.rfc-editor.org/rfc/rfc9596)
- [Hoang, Reyhanitabar, Rogaway, Vizár — Online Authenticated-Encryption and its Nonce-Reuse Misuse-Resistance (2015)](https://eprint.iacr.org/2015/189)
- [C2SP age — STREAM encryption](https://age-encryption.org/v1)
- [Google Tink — Streaming AEAD](https://developers.google.com/tink/streaming-aead)

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
