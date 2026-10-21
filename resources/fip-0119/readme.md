# Supporting material for FIP-0119

Discussion: [#1291](https://github.com/filecoin-project/FIPs/discussions/1291)

## Documents

- [`Filecoin_Proof_of_Useful_Space.pdf`](Filecoin_Proof_of_Useful_Space.pdf) — the 2023 security report. Sections 5.1 and 5.2 carry the WindowPoSt cost margin and the WinningPoSt latency margin; section 4.2 carries the PreCommit Deposit bound used in the Security Considerations.

## Papers

- [`Reyzin_ePrint-2023-1530.pdf`](Reyzin_ePrint-2023-1530.pdf) — L. Reyzin, Proofs of Space with Maximal Hardness, [ePrint 2023/1530](https://eprint.iacr.org/2023/1530), Theorem 5. Gives the bound used for the WindowPoSt margin, an 11-fold improvement on the bound the report above uses.

## Hardware and price sources

- Instruction latencies: [uops.info, `SHA256RNDS2`](https://uops.info/html-instr/SHA256RNDS2_XMM_XMM.html)
- Drive prices, checked September 2026 at \$28.33/TB for 24 TB CMR enterprise drives: [diskprices.com](https://diskprices.com/), [harddiskprices.com](https://www.harddiskprices.com/), [price history](https://terabytewise.com/hdd-price-history)
- Sealing configuration and throughput: Supranational, Filecoin sealing cost analysis, 2022 (last updated 2023)

## Related FIPs

- [FIP-0014](../../FIPS/fip-0014.md)
- [FIP-0047](../../FIPS/fip-0047.md)
- [FIP-0052](../../FIPS/fip-0052.md)
- [FIP-0067](../../FIPS/fip-0067.md)
- [FIP-0118](../../FIPS/fip-0118.md)

## Related discussions

- [#313](https://github.com/filecoin-project/FIPs/discussions/313)
- [#475](https://github.com/filecoin-project/FIPs/discussions/475)
