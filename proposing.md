---
title: Proposing FIPs
layout: page
permalink: /proposing/
---

Filecoin Improvement Proposals (FIPs) describe standards for the Filecoin platform, including core protocol specifications, client APIs, and other changes to the project.

# Contributing

 1. Review [FIP-1](/FIPS/fip-0001/).
 2. Fork the repository by clicking "Fork" in the top right.
 3. Add your FIP to your fork of the repository. There are [template FIPs here](/templates).
 4. Submit a Pull Request to Filecoin's [FIPs repository](https://github.com/filecoin-project/FIPs).
 5. Draft and submit a Pull Request to the [Filecoin Specification repository](https://github.com/filecoin-project/specs) to update the spec with the changes that your FIP brings.

Your first PR should be a first draft of the final FIP. It must meet the formatting criteria enforced by the build (largely, correct metadata in the header). An editor will manually review the first PR for a new FIP and assign it a number before merging it. Make sure you include a `discussions-to` header with the URL to a discussion forum or open GitHub issue where people can discuss the FIP as a whole.

If your FIP requires images, the image files should be included in a subdirectory of the `assets` folder for that FIP as follow: `assets/fip-X` (for fip **X**). When linking to an image in the FIP, use relative links such as `../assets/fip-X/image.png`.

Once your first PR is merged, we have a bot that helps out by automatically merging PRs to draft FIPs. For this to work, it has to be able to tell that you own the draft being edited. Make sure that the 'author' line of your FIP contains either your Github username or your email address inside `<triangular brackets>`. If you use your email address, that address must be the one publicly shown on [your GitHub profile](https://github.com/settings/profile).

When you believe your FIP is mature and ready to progress past the draft phase, you should do one of two things:

 - **For a Standards Track FIP of type Core**:
 	- ask to have your issue added to [the agenda of an upcoming All Core Devs meeting](https://github.com/filecoin-project/tpm/issues), where it can be discussed for inclusion in a future chain upgrade. If implementers agree to include it, the FIP editors will update the state of your FIP to 'Accepted'.
 	- prepare the changes to the spec text necessary to describe the protocol modifications that your FIP brings. Submit a PR to the [Filecoin Specification repository](https://github.com/filecoin-project/specs). These changes will also be discussed in the "All Core Devs" meeting and the editor will assign a reviewer.
 - **For all other FIPs**, open a PR changing the state of your FIP to 'Final'. An editor will review your draft and ask if anyone objects to its being finalised. If the editor decides there is no rough consensus - for instance, because contributors point out significant issues with the FIP - they may close the PR and request that you fix the issues in the draft before trying again.

# FIP Status Terms
* **Draft** - a FIP that is undergoing rapid iteration and changes.
* **Last Call** - a FIP that is done with its initial iteration and ready for review by a wide audience.
* **Accepted** - a core FIP that has been in Last Call for at least 2 weeks and any technical changes that were requested have been addressed by the author. The process for Core Devs to decide whether to encode a FIP into their clients as part of a hard fork is not part of the FIP process. If such a decision is made, the FIP wil move to final.
* **Final (non-Core)** - a FIP that has been in Last Call for at least 2 weeks and any technical changes that were requested have been addressed by the author.
* **Final (Core)** - a FIP that the Core Devs have decided to implement and release in a future chain upgrade or has already been released in a chain upgrade. 
* **Deferred** - a FIP that is not being considered for immediate adoption. May be reconsidered in the future for a subsequent chain upgrade.

# Preferred Citation Format

TODO: 
The canonical URL for a FIP that has achieved draft status at any point will be on the Filecoin website. For example, the canonical URL for FIP-00001 will be https://filecoin.io/TODO.
