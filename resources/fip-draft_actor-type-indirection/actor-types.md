# Builtin actor type names

Actor type names defined by [FIP-XXXX](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-draft_actor-type-indirection.md), used in the `Type` field of actors from state tree version 6 and as keys in the builtin actors manifest. A FIP that adds or retires a type updates this table in the same pull request.

## Rules

- A name is introduced only by a FIP, which adds it to the manifest of the activating actors version.
- Names are lowercase ASCII `[a-z0-9]`, at most 16 bytes.
- A name is never renamed or reused; retired names stay in this table.
- A type is retired only by a migration that removes or converts every actor of that type.

## Types

| Name | Status | Introduced | Retired | Description |
|------|--------|------------|---------|-------------|
| `system` | active | genesis | | System actor (f00) |
| `init` | active | genesis | | Address and actor creation (f01) |
| `cron` | active | genesis | | Per-epoch scheduled calls (f03) |
| `account` | active | genesis | | Secp256k1 and BLS key accounts |
| `storagepower` | active | genesis | | Power table (f04) |
| `storageminer` | active | genesis | | Storage provider |
| `storagemarket` | active | genesis | | Storage deals (f05) |
| `paymentchannel` | active | genesis | | Payment channel |
| `multisig` | active | genesis | | Multisig wallet |
| `reward` | active | genesis | | Block reward (f02) |
| `verifiedregistry` | active | genesis | | Verified registry (f06) |
| `datacap` | active | actors v9, nv17, [FIP-0045](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0045.md) | | DataCap token (f07) |
| `placeholder` | active | actors v10, nv18, [FIP-0048](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0048.md) | | Address placeholder for f4 addresses before deployment |
| `evm` | active | actors v10, nv18, [FIP-0054](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0054.md) | | EVM smart contract |
| `eam` | active | actors v10, nv18, [FIP-0055](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0055.md) | | Ethereum address manager (f010) |
| `ethaccount` | active | actors v10, nv18, [FIP-0055](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0055.md) | | Ethereum-style account |

Before actors v8 (nv16) actors had identity CIDs of the form `fil/<n>/<name>`, with n from 1 (actors v0) to 7 (actors v7), using the same names for the 11 types that existed then.
