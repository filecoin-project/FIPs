## Filecoin Improvement Protocol

The Filecoin Improvement Protocol contains the set of fundamental governing principles for the Filecoin Network. It outlines the vision for Filecoin and the principles, processes, and parties involved in making decisions that affect the future of the network. It also describes how improvements to these rules can be proposed and ratified.


## The Filecoin Vision

Filecoin is a peer-to-peer network that stores files, with built-in economic incentives to ensure that files are stored reliably over time. Its mission is to create a decentralized, efficient and robust foundation for humanity’s information. To advance that mission, Filecoin has created a decentralized storage network that lets anyone in the world store or retrieve files.

In Filecoin, users pay to store their files on storage miners. Storage miners are computers responsible for storing files and proving they have stored the files correctly over time. Anyone who wants to store their files or get paid for storing other users’ files can join Filecoin. Available storage and pricing are not controlled by any single entity. Instead, Filecoin facilitates open markets for storing and retrieving files that anyone can participate in, thereby providing storage to billions of people who are currently locked out of the web.

## Filecoin Design Principles

The design of Filecoin is intended to follow a set of principles. The community will help define these principles in the coming months.


## Filecoin Improvement Principles

When making decisions about how to improve Filecoin, we will follow a set of principles. The community will help define these principles in the coming months.

## Making changes to the Filecoin network

[Filecoin Improvement Proposals (FIPs)](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0001.md) are the primary mechanism by which the Filecoin community can submit, discuss, and approve changes relevant to the Filecoin network. These discussions and decisions should be guided by the governance and design principles above.

FIPs are classified into three categories:

**Technical FIPs, or Filecoin Technical Proposals (FTPs)** are designed to gather community feedback on technical Filecoin issues. These include changes to the Filecoin protocol, a change in block or transaction validity rules, and proposed application standards or conventions. They are then reviewed by the Filecoin community and the technical steering committee. They are normally followed by a PR to the [Filecoin Specification repository](https://github.com/filecoin-project/specs) to update the protocol's spec.

**Organizational FIPs, or Filecoin Organization Proposals (FOPs)** allow the Filecoin community to propose, discuss, and achieve consensus on Filecoin governance. This includes procedures, guidelines, decision-making processes, and changes to FIP processes.

**Recovery FIPs, or Filecoin Recovery Proposals (FRPs)** are intended to provide the Filecoin community with a forum to raise, discuss, and achieve consensus on fault recovery and chain rewrites, under a very limited, clearly-defined set of criteria (ex, in the case of protocol bugs destroying network value). The community will help define this process as needed in the coming months.

## A decentralized, global network

Filecoin is still in its infancy, but it has the potential to play a central role in the storage and distribution of humanity’s information. To help the network grow and evolve, it is critical for the community to collectively be engaged in proposing, discussing, and implementing changes that improve the network and its operations.

This improvement protocol helps achieve that objective for all members of the Filecoin community (developers, miners, clients, token holders, ecosystem partners, and more).

## FIPs

| FIP #                                                                         | Title | Type | Author | Status |
|-------------------------------------------------------------------------------|-------|------|--------|--------|
| [0001](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0001.md) | FIP Purpose and Guidelines | FIP | @Whyrusleeping | Active |
| [0002](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0002.md) | Free Faults on Newly Faulted Sectors of a Missed WindowPoSt | FIP | @anorth, @davidad, @miyazono, @irenegia, @lucaniz, @nicola, @zixuanzh | Final |
| [0003](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0003.md) | Filecoin Plus Principles | FIP | @feerst, @jbenet, @jnthnvctr, @tim-murmuration, @mzargham, @zixuanzh | Active |
| [0004](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0004.md) | Liquidity Improvement for Storage Miners | FIP | @davidad, @jbenet, @zenground0, @zixuanzh, @danlessa | Final |
| [0005](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0005.md) | Remove ineffective reward vesting | FIP | @anorth, @Zenground | Final |
| [0006](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0006.md) | No repay debt requirement for DeclareFaultsRecovered | FIP | @nicola, @irenegia | Deferred |
| [0007](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0007.md) | h/amt-v3 | FIP | @rvagg, @Stebalien, @anorth, @Zenground0 | Final |
| [0008](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0008.md) | Add miner batched sector pre-commit method | FIP | @anorth, @ZenGround0, @nicola | Final |
| [0009](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0009.md) | Exempt Window PoSts from BaseFee burn | FIP | @Stebalien, @momack2, @magik6k, @zixuanzh | Final |
| [0010](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0010.md) | Off-Chain Window PoSt Verification | FIP | @Stebalien, @anorth | Final |
| [0011](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0011.md) | Remove reward auction from reporting consensus faults | FIP | @Kubuxu | Final |
| [0012](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0012.md) | DataCap Top up for FIL+ Client Addresses | FIP | @dshoy, @jnthnvctr, @zx | Final |
| [0013](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0013.md) | Add ProveCommitSectorAggregated method to reduce on-chain congestion | FIP | @ninitrava @nicola | Final |
| [0014](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0014.md) | Allow V1 proof sectors to be extended up to a maximum of 540 days | FIP | @deltazxm, @neogeweb3 | Final |
| [0015](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0015.md) | Revert FIP-0009(Exempt Window PoSts from BaseFee burn) | FIP | @jennijuju, @arajasek | Final |
| [0016](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0016.md) | Pack arbitrary data in CC sectors | FIP | donghengzhao (@1475) | Deferred |
| [0017](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0017.md) | Three-messages lightweight sector updates | FIP | @nicole, @lucaniz, @irenegia | Deferred |
| [0018](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0018.md) | New miner terminology proposal | FIP | @Stefaan-V | Final |
| [0019](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0019.md) | Snap Deals | FIP | @Kubuxu, @lucaniz, @nicola, @rosariogennaro, @irenegia | Final |
| [0020](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0020.md) | Add return value to WithdrawBalance | FIP | @Stefaan-V | Final |
| [0021](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0021.md) | Correct quality calculation on expiration | FIP | @Steven004, @Zenground0 | Final |
| [0022](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0022.md) | Bad deals don't fail PublishStorageDeals | FIP | @Zenground0 | Final |
| [0023](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0023.md) | Break ties between tipsets of equal weights | FIP | @sa8, @arajasek | Final |
| [0024](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0024.md) | BatchBalancer & BatchDiscount Post -Hyperdrive adjustment | FIP | @zx, @jbenet, @zenground0, @momack2 | Final |
| [0025](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0025.md) | Handle expired deals in ProveCommit | FIP | @ZenGround0 | Deferred |
| [0026](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0026.md) | Extend sector fault cutoff period from 2 weeks to 6 weeks | FIP | @IPFSUnion | Final |
| [0027](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0027.md) | Change type of DealProposal Label field from a (Golang) String to a Union | FIP | @laudiacay, @Stebalien, @arajasek | Final |
| [0028](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0028.md) | Remove DataCap and verified client status from client address | FIP | @jennijuju, @dkkapur | Final |
| [0029](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0029.md) | Beneficiary address for storage providers | FIP | @steven004 | Final |
| [0030](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0030.md) | Introducing the Filecoin Virtual Machine (FVM) | FIP | @raulk, @stebalien | Final |
| [0031](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0031.md) | Atomic switch to non-programmable FVM | FIP | @raulk, @stebalien | Final |
| [0032](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0032.md) | Gas model adjustment for non-programmable FVM | FIP | @raulk, @stebalien | Final |
| [0033](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0033.md) | Explicit premium for FIL+ verified deals | FIP | @anorth | Deferred |
| [0034](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0034.md) | Fix pre-commit deposit independent of sector content | FIP | @anorth, @Kubuxu | Final |
| [0035](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0035.md) | Support actors as built-in storage market clients | FIP | @anorth | Withdrawn |
| [0036](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0036.md) | Introducing a Sector Duration Multiple for Longer Term Sector Commitment | FIP | @AxCortesCubero, @jbenet, @misilva73, @momack2, @tmellan, @vkalghatgi, @zixuanzh | Rejected |
| [0037](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0037.md) | Gas model adjustment for user programmability | FIP | @raulk, @stebalien | Withdrawn |
| [0038](https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0038.md) | Indexer Protocol for Filecoin Content Discovery | FRC | @willscott, @gammazero, @honghaoq | Draft |
| [0039](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0039.md) | Filecoin Message Replay Protection | FIP | @q9f | Draft |
| [0040](https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0040.md) | Boost - Filecoin Storage Deals Market Protocol | FRC | @dirkmc, @nonsense, @jacobheun, @brendalee | Draft |
| [0041](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0041.md) | Forward Compatibility for PreCommit and ReplicaUpdate | FIP | @Kubuxu | Final |
| [0042](https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0042.md) | Calling Convention for Hashed Method Name | FRC | @Kubuxu, @anorth | Draft |
| [0044](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0044.md) | Standard Authentication Method for Actors | FIP | @arajasek, @anorth | Final |
| [0045](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0045.md) | De-couple verified registry from markets | FIP | @anorth, @zenground0 | Final |
| [0046](https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0046.md) | Fungible token standard | FRC | @anorth, @jsuresh, @alexytsu | Draft |
| [0047](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0047.md) | Proof Expiration & PoRep Security Policy | FIP | @Kubuxu, @irenegia, @anorth | Superseded |
| [0048](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0048.md) | f4 Address Class | FIP | @stebalien, @mriise, @raulk | Final |
| [0049](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0049.md) | Actor Events | FIP | @stebalien, @raulk | Final |
| [0050](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0050.md) | API Between User-Programmed Actors and Built-In Actors | FIP | @anorth, @arajasek | Final |
| [0051](https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0051.md) | Synchronous Consistent Block Broadcast for EC Security | FRC | Guy Goren <guy.goren@protocol.ai>, Alfonso de la Rocha <alfonso@protocol.ai> | Draft |
| [0052](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0052.md) | Increase max sector commitment to 3.5 years | FIP | @anorth | Final |
| [0053](https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0053.md) | Non-Fungible Token Standard | FRC | @alexytsu, @abright, @anorth | Draft |
| [0054](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0054.md) | Filecoin EVM Runtime (FEVM) | FIP | @raulk, @stebalien | Final |
| [0055](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0055.md) | Supporting Ethereum Accounts, Addresses, and Transactions | FIP | @raulk, @stebalien | Final |
| [0056](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0056.md) | Sector Duration Multiplier | FIP | @AxCortesCubero, @jbenet, @misilva73, @momack2, @tmellan, @vkalghatgi, @zixuanzh | Rejected |
| [0057](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0057.md) | Update Gas Charging Schedule and System Limits for FEVM | FIP | @raulk, @stebalien, @aakoshh, @kubuxu| Final |
| [0058](https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0058.md) | Verifiable Data Aggregation | FRC | Jakub Sztandera (@Kubuxu), Nicola Greco (@nicola), Peter Rabbitson (@ribasushi)| Draft |
| [0059](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0059.md) | Synthetic PoRep | FIP | @Kubuxu @Luca @Rosario Gennaro @Nicola @Irene| Final |
| [0060](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0060.md) | Set market deal maintenance interval to 30 days | FIP | Jakub Sztandera (@Kubuxu), @Zenground0, Alex North (@anorth)| Final |
| [0061](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0061.md) | WindowPoSt Grindability Fix | FIP | @cryptonemo @Kubuxu @DrPeterVanNostrand @Nicola @porcuquine @vmx @arajasek| Final |
| [0062](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0062.md) | Fallback Method Handler for the Multisig Actor | FIP | Dimitris Vyzovitis (@vyzo), Raúl Kripalani (@raulk)| Final |
| [0063](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0063.md) | Switching to new Drand mainnet network | FIP | @yiannisbot, @CluEleSsUK, @AnomalRoil, @nikkolasg, @willscott | Final |
| [0065](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0065.md) | Ignore built-in market locked balance in circulating supply calculation | FIP | @anorth | Final |
| [0066](https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0066.md) | Piece Retrieval Gateway | FRC | @willscott, @dirkmc | Draft |
| [0067](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0067.md) | PoRep Security Policy & Replacement Sealing Enforcement | FIP | @Kubuxu, @anorth, @irenegia, @lucaniz | Accepted |
| [0068](https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0068.md) | Deal-Making Between SPs and FVM Smart Contracts | FRC | @aashidham, @raulk, @skottie86, @jennijuju, @nonsense, @shrenujbansal | Draft |
| [0069](https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0069.md) | Piece Multihash and v2 Piece CID | FRC | @aschmahmann, @ribasushi | Draft |
| [0070](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0070.md) | Allow SPs to move partitions between deadlines | FIP | Steven Li (@steven004), Alan Xu (@zhiqiangxu), Mike Li (@hunjixin), Alex North (@anorth), Nicola (@nicola)| Rejected |
| [0071](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0071.md) | Deterministic State Access (IPLD Reachability) | FIP | @stebalien| Final |
| [0072](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0072.md) | Improved event syscall API | FIP | @fridrik01, @Stebalien | Final |
| [0073](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0073.md) | Remove beneficiary from the self_destruct syscall | FIP | @Stebalien | Final |
| [0074](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0074.md) | Remove cron-based automatic deal settlement | FIP | @anorth, @alexytsu| Final |
| [0075](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0075.md) | Improvements to the FVM randomness syscalls | FIP | @arajasek, @Stebalien | Final |
| [0076](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0076.md) | Direct data onboarding | FIP | @anorth, @zenground0 | Final |
| [0077](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0077.md) | Add Cost Opportunity For New Miner Creation | FIP | Zac (@remakeZK), Mike Li (@hunjixin)| Draft |
| [0078](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0078.md) | Remove Restrictions on the Minting of Datacap | FIP | Fatman13 (@Fatman13), flyworker (@flyworker), stuberman (@stuberman), Eliovp (@Eliovp), dcasem (@dcasem), and The-Wayvy (@The-Wayvy)| Draft |
| [0079](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0079.md) | Add BLS Aggregate Signatures to FVM | FIP | Jake (@drpetervannostrand) | Final |
| [0080](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0080.md) | Phasing Out Fil+ and Restoring Deal Quality Multiplier to 1x | FIP | @Fatman13, @ArthurWang1255, @stuberman, @Eliovp, @dcasem, @The-Wayvy | Draft |
| [0081](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0081.md) | Introduce lower bound for sector initial pledge | FIP | @anorth, @vkalghatgi | Final |
| [0082](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0082.md) | Add support for aggregated replica update proofs | FIP | nemo (@cryptonemo), Jake (@drpetervannostrand), @anorth | Accepted |
| [0083](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0083.md) | Add built-in Actor events in the Verified Registry, Miner and Market Actors | FIP | Aarsh (@aarshkshah1992)| Final |
| [0084](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0084.md) | Remove Storage Miner Actor Method `ProveCommitSectors` | FIP | Jennifer Wang (@jennijuju)| Final |
| [0085](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0085.md) | Convert f090 Mining Reserve actor to a keyless account actor | FIP | Jennifer Wang (@jennijuju), Jon Victor (@jnthnvctr)| Final |
| [0086](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0086.md) | Fast Finality in Filecoin (F3) | FIP | @stebalien, @masih, @mb1896, @hmoniz, @anorth, @matejpavlovic, @arajasek, @ranchalp, @jsoares, @Kubuxu, @vukolic, @jennijuju | Accepted |
| [0087](https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0087.md) | FVM-Enabled Deal Aggregation | FRC | @aashidham, @honghao, @raulk, @nonsense | Draft |
| [0089](https://github.com/filecoin-project/FIPs/blob/master/FRCs/frc-0089.md) | A Finality Calculator for Filecoin | FRC | @guy-goren, @jsoares | Draft |
| [0090](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0090.md) | Non-Interactive PoRep | FIP | luca (@lucaniz), kuba (@Kubuxu), nicola (@nicola), nemo (@cryptonemo), volker (@vmx), irene (@irenegia) | Superseded by [FIP0092](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0092.md) |
| [0091](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0091.md) | Add support for Homestead and EIP-155 Ethereum Transactions ("legacy" Ethereum Transactions) | FIP | Aarsh (@aarshkshah1992)| Final |
| [0092](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0092.md) | Non-Interactive PoRep | FIP | luca (@lucaniz), kuba (@Kubuxu), nicola (@nicola), nemo (@cryptonemo), volker (@vmx), irene (@irenegia), Alex North (@anorth), orjan (@Phi-rjan) | Final |
| [0094](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0094.md) | Add Support for EIP-5656 (MCOPY Opcode) in the FEVM | FIP | Michael Seiler (@snissn), Raúl Kripalani (@raulk), Steven Allen (@stebalien) | Final |
| [0095](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0095.md) | Add FEVM precompile to fetch beacon digest from chain history | FIP | @ZenGround0, Alex North (@anorth) | Final |
| [0096](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0096.md) | Convert fundraising remainder address(es) to keyless account actor(s) | FIP | @Fatman13 | Draft |
| [0097](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0097.md) | Add Support for EIP-1153 (Transient Storage) in the FEVM | FIP | Michael Seiler (@snissn), Steven Allen (@stebalien) | Accepted |
| [0098](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0098.md) | Simplify termination fee calculation to a fixed percentage of initial pledge | FIP | Jonathan Schwartz (@Schwartz10), Alex North (@anorth), Jim Pick (@jimpick) | Last Call |
