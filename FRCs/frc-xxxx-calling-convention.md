---
fip: <to be assigned>
title: Calling convention with hashed method name
author: @anorth, @kubuxu
discussions-to: https://github.com/filecoin-project/FIPs/discussions/382
status: Draft
type: FRC
created: 2022-07-07
---

## Simple Summary
An actor calling convention that derives method numbers by hashing method names.

## Abstract
This proposal describes a convention for the labelling of methods across actors which will 
support the development of standardised APIs, e.g. a token API.
The convention maps human-friendly method names to method numbers by hashing the method name.
This supports the definition of multiple standardized APIs with minimal potential for collision on method numbers.

## Change Motivation
Filecoin messages include a method number and parameter block as the essential payload for method invocation.
The FVM implements internal dispatch: there is a single entry point to each actor for receiving messages.
The FVM does not further constrain dispatch, and the development team wish for the FVM to remain neutral with respect to such conventions.

The built-in actors' methods are numbered sequentially, partly in order to enjoy a dense representation for top-level chain messages.
This scheme is inappropriate for development of standardized APIs to be implemented by many actors, 
as different APIs would need to coordinate to avoid colliding on different meanings for the same method number.
Method _names_ are a more developer-friendly handle on a method, and much more suited to avoiding collisions.

This proposal continues to use method numbers, but provides a deterministic mapping from method names to those numbers.

Goals:
- A familiar dispatch-by-name abstraction for programmers
- Compact, uniform-size on-chain encoding
- No change to blockchain message schema
- Permit specification of standard actor interfaces, including retroactively in recognition of widely-adopted patterns
- Permit extending the interface of a deployed actor to implement methods defined in a new standard
- Independent of programming language

This proposal assumes that method names are defined statically, 
i.e. that actors will have the interface definitions of any other actors they call available at compile-time.
However, it can support dynamic resolution for future reflection capabilities.

## Specification
### Method number computation
The method number for a symbolic method name is calculated as the first four bytes of `hash(method-name)`,
interpreted as an unsigned, big-endian 32-bit integer.

The `hash` function is given as:
- if `method-name == "Constructor` then `1`, else
- if `blake2b(method-name) == 0` then `4294967295` (`0xffffffff`), else
- `blake2b(method-name)`

### Method name conventions
A method is *exported* when a method number is computed for it and the actor will recognise this number for internal dispatch. 
Conventions on exported method names are independent of any programming language conventions. 
Note that these conventions only apply to methods exported to the VM for inter-actor dispatch. 
Actor developers can continue to use relevant programming language conventions for simple internal function calls.

Exported method names *should*:
- Use only the ASCII characters in `[a-zA-Z0-9_]` (the same set as the C programming language). Other characters, including unicode beyond this set, are excluded in order to reduce the opportunity for misleading spelling of names in user interfaces.
- Have an initial capital letter, and use CamelCase to identify word boundaries.
- Capitalize all letters in acronyms.

Examples: `Approve`, `SubmitWindowPoSt`, `MintNFT`, `FRC1234AuthorizeOperator`

## Design Rationale
### Method number computation
The blake2b hash function is already implemented in the VM and available as a syscall.
This permits easy dynamic method number calculation, 
though build tools are expected to compute most method numbers statically at compile time.

Method number `1` is expected as the constructor function by the built-in `Init` actor, 
and user-deployed actors must implement it. This proposal assigns a conventional name.

Method number `0` is treated by the FVM as a special-case bare send of the native Filecoin token, 
and will not invoke an actor's code. 
Rather than have some subset of method names be inaccessible, this proposal maps them to a different method number.

Both the blockchain `Message` structure and FVM support up to 64-bits for a method number.
This proposal restricts values to 32-bits in order to compress the representation for top-level message method numbers
to four bytes (a minor gas saving on every message).

### Collisions
Two different method names will collide on their method number with probability `1/(2^32)`. 
In the rare case of collision within a single actor, build tooling should identify the collision and prompt one of the methods to be renamed.

A harder-to-resolve collision will occur in case of a collision between names in two standard interfaces to be implemented by a single actor. 
The probability of a collision grows with the square root of the number of methods in each interface. 
Two ten-method interfaces will find a collision with probability approximately `(10/2^32)*10 ~= 1/50,000,000`. 
This is judged to be rare enough that developer tooling will be able to detect collision with widely used standard names
before significant adoption makes renaming one a significant burden.

### Conceptual compatibility with Ethereum
This scheme is inspired by the Solidity ABI for the Ethereum VM.
It differs in the choice of hash function and exclusion of method parameter types (no overloading),
so is not transparently compatible.

Note that removing both those differences would *not* automatically make this scheme compatible with the Solidity ABI, 
since method parameter types have fundamentally different schemas between the two environments. 
A future FVM/EVM embedding will need to translate method selectors along with the rest of the EVM ABI.

### Method name conventions
These conventions encode the loose guidelines established by the Filecoin specification and actors at network launch.
Specifics of any convention are less important than there being some clearly-defined convention.

We recognize that prohibiting more Unicode is unfortunate for languages other than English.
However, there is a long history of the use of look-alike characters in DNS names by various fraudulent and malicious schemes.
Since users are likely to have financial value at stake, we restrict their use.

## Backwards Compatibility
This proposal is compatible with the existing built-in actors.
Calls to their existing, sequential method numbers can continue to be supported indefinitely.

The built-in actors can additionally adopt this convention by computing the prescribed method number 
corresponding to each existing method and adding these to their internal dispatch tables.

## Test Cases
Test cases of method names and corresponding numbers to be provided.

## Security Considerations
This proposal is a convention, so has no direct impact on Filecoin network security.

This proposal introduces the remote possibility that a malicious user interface could brute-force 
alternative method names for some actor, misleading a user who both 
inspects those names and verifies their method number as to their true behaviour.

## Incentive Considerations
None.

## Product Considerations
This proposal is conceptually aligned with existing conventions in Ethereum.
We can hope that this alignment makes it easy for developers of actors, as well as wallets and other off-chain software, to adopt.

## Implementation
Example code to be provided.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
