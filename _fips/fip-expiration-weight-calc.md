---
fip: <to be assigned>
title: Correct quality calculation on expiration
author: @Stebalien, @ZX, @Zenground0
discussions-to: 
status: Draft
type: Technical
category Core
created: 2021-09-20
spec-sections: 
  - specs-actors
  - [Sector Quality](https://spec.filecoin.io/#section-systems.filecoin_mining.sector.sector-quality)
---

<!--You can leave these HTML comments in your merged FIP and delete the visible duplicate text guides, they will not appear and may be helpful to refer to if you edit it again. This is the suggested template for new FIPs. Note that a FIP number will be assigned by an editor. When opening a pull request to submit your FIP, please use an abbreviated title in the filename, `fip-draft_title_abbrev.md`. The title should be 44 characters or less.-->


## Simple Summary
<!--"If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the FIP.-->
Sector quality is defined as a spacetime average of the quality of the deals stored in the sector. The current protocol implementation does not work as expected when sectors are extended because deal spacetime is overcounted.  This leads to minor incentive issues. This FIP fixes the discrepancy.

## Abstract
<!--A short (~200 word) description of the technical issue being addressed.-->
DealWeight and VerifiedDealWeight in a sector's past is no longer included in the quality calculation for the extended sector. Instead the past spacetime of the sectors is "spent" and only the remaining deal spacetime of the sector's original life is counted.

To avoid extending the market actor interface for a small change this FIP proposes getting an approximate value for the remaining spacetime of deals and verified deals. A good approximation is to multiply deal weight by the fraction of sector lifetime remaining.

## Change Motivation
<!--The motivation is critical for FIPs that want to change the Filecoin protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the FIP solves. FIP submissions without sufficient motivation may be rejected outright.-->

@Stebalien proposed this solution after noticing that the following scenario is possible today:
1. A storage provider accepts a 6 month deal and stores it in a sector for 6 months with a 10x multiplier
2. The day before the sector expires the storage provider extends the lifetime for 6 months (the minimum extension). The power will now be 5x.
3. Again, the day before the sector expires again, the storage provider extends the lifetime for 6 months at 3.33x power.

This is problematic because it goes against the design intention of rewarding verified deal weight proportional to the active deals in a sector. This bug encourages complex behavior in order to game the sector quality system. Sector expiration should not have gameable incentives and verified deal weight should not have more relative power than designed compared with cc sectors.


## Specification
<!--The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Filecoin implementations. -->

During sector extension a storage provider specifies the sector to be extended and the new expiration. The sector info on chain contains the activation and current expiration epoch.  It is trivial to compute the spent fraction of the sector's lifetime with arithmetic: `spentFraction = (currentEpoch - activation) / 
(currentExpiration - activation)`. Multiply this number by the `DealWeight` and `VerifiedDealWeight` fields of the sector info before rewriting to the Sectors array. In practice this should be done as a big Int multiplication of the deal weights with the numerator and then a division by the denominator as the last step. All miner actor sector quality calculations first read the sector info so this is a sufficient change to propagate correct sector power information.

## Design Rationale
<!--The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.-->

An alternate approach that would more accurately tie together sector quality and value provided through active verified deals in a sector is to ask the market actor for an updated weight calculation during sector extension. This would require some changes to the market actor since weight calculation and activation checks are currently coupled together in one method and by definition deals in active sectors may have passed their start time and will not in general be valid for activation.

While it is not an exact fix the chosen approach is simple requiring no state or method signature changes. The fix is not exact because it will assign deal weights greater than 0 to sectors with deals that have all finished.  This type of reasoning about average deal spacetime across the sector's life is essential to the concept of deal weight and sector quality. The same tradeoffs are shared by the existing design and are therefore acceptable.


## Backwards Compatibility
<!--All FIPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The FIP must explain how the author proposes to deal with these incompatibilities. FIP submissions without a sufficient backwards compatibility treatise may be rejected outright.-->

This changes specs-actors behavior so will need a network upgrade. No migration is needed -- the new rules will not be applied retroactively only on new expirations.

## Test Cases
<!--Test cases for an implementation are mandatory for FIPs that are affecting consensus changes. Other FIPs can choose to include links to test cases if applicable.-->

* A test should cover the motivating example described in the motivation section. A sector with verified deal weight taking up entire space time for 6 months followed by an extension on the last day of lifetime twice in a row. With one day remaining during extension after the second extension this should be about 512 GiB*epochs of verified deal weight and a sector quality of (10 * 512 GiB * epoch + 1 * 53000 GiB*epoch / 53512 GiB * epoch) ~ 1.08.
* Include both deals and verified deals. Check sector info for propagation of both DealWeight and VerifiedDealWeight changes 
* Start a sector with a low deal weight and extend very close to expiration so that deal weight becomes fractional mathematically. And implementation should set deal weight to 0.


## Security Considerations
<!--All FIPs must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks and can be used throughout the life cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. FIP submissions missing the "Security Considerations" section will be rejected. A FIP cannot proceed to status "Final" without a Security Considerations discussion deemed sufficient by the reviewers.-->

The current bug can be considered as a minor security issue because verified deal weight of extended sectors unfairly inflates storage provider power. There is no significant associated risk today however, allowing this issue to be publically disclosed through a FIP

## Incentive Considerations
<!--All FIPs must contain a section that discusses the incentive implications/considerations relative to the proposed change. Include information that might be important for incentive discussion. A discussion on how the proposed change will incentivize reliable and useful storage is required. FIP submissions missing the "Incentive Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Incentive Considerations discussion deemed sufficient by the reviewers.-->

This FIP should remove the unfair benefits of extending sectors with verified deals. Removing unfair advantage from verified deal data will balance the relative power of verified and unverified/cc data as designed. In the context of the proposed snap deals construction this will strengthen the incentive for miners to store new cc sectors that can be made available for snap deals rather than extending sectors with deals that have completed and cannot add snap deals.

Because this solution does not extend the market actor and instead uses an approximation to recalculate deal weight there will still be a small extra incentive to extend verified deal sectors over adding new cc sectors. But it will be greatly reduced and should be negligible. 


## Product Considerations
<!--All FIPs must contain a section that discusses the product implications/considerations relative to the proposed change. Include information that might be important for product discussion. A discussion on how the proposed change will enable better storage-related goods and services to be developed on Filecoin. FIP submissions missing the "Product Considerations" section will be rejected. An FIP cannot proceed to status "Final" without a Product Considerations discussion deemed sufficient by the reviewers.-->

Assuming the snap deals FIP is accepted Incentive pressure away from extending sectors with expired deals towards new cc sectors available for snap deals should only benefit the experience of data storage users.

Since this change is restoring a fair allocation of power to storage providers it should not degrade storage provider experience either. Sector extension should not be more expensive in terms of gas or state churn as the sector info is already modified at the `Expiration` field and written to state during sector extension.


## Implementation
<!--The implementations must be completed before any core FIP is given status "Final", but it need not be completed before the FIP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.-->
specs-actors PR TODO

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
