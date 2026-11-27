# FIPs agent guide

This repository holds Filecoin Improvement Proposals (`FIPS/`) and Filecoin Requests for Comments (`FRCs/`). A Core FIP is a specification that several independent clients implement: [Lotus](https://github.com/filecoin-project/lotus) and [Forest](https://github.com/ChainSafe/forest) must compute identical state from it, and [builtin-actors](https://github.com/filecoin-project/builtin-actors), [ref-fvm](https://github.com/filecoin-project/ref-fvm) and [go-state-types](https://github.com/filecoin-project/go-state-types) carry the reference implementation. Write it so an implementer working from the text alone reaches the same result. FRCs are standards outside consensus; the actor and migration rules below apply to them only where relevant.

## Process

- A FIP starts as a Discussion that lays out the problem, the approaches and their tradeoffs; `discussions-to` links it. The PR description is the FIP's Abstract plus that link (`.github/pull_request_template.md`).
- Start from `templates/template.md` and keep its frontmatter, headings and order; extra sections go before Copyright. Core FIPs use `type: Technical` and `category: Core`; FRCs use `type: FRC`.
- Editors allocate numbers; don't pick one. Name a draft `fip-<short_title>.md` with `fip: "<to be assigned>"`, a `# FIP-XXXX: <title>` heading and `XXXX` in the README row. FIPs and FRCs share one sequence, and the next number after master's highest may already belong to an open PR. Once assigned, update the filename, frontmatter, heading and README row together.
- Add the README table row in the same PR, in numeric order, linking the file on master.
- A status change edits the frontmatter `status` and the README row in one PR. The author may propose Last Call once no material changes are expected and the TODO items are resolved. Accepted follows a clean Last Call of about two weeks, and Final follows mainnet activation.
- A behaviour change to a FIP in Last Call or later is material and can send it back to Draft; say in the PR whether a change alters behaviour. A Final FIP changes only for errata.
- Supporting material goes in `resources/fip-NNNN/` (or `resources/fip-<short_title>/` until numbered), and the FIP links and explains each file. The FIP must stand on its own: Discussions are editable and external links decay, so anything the argument rests on belongs in the repository. Summarise and cite external papers rather than committing them; commit only what can be licensed CC0. FIP-0001 and `proposing.md` describe an `assets/` directory and PR-number numbering; follow this file.
- Inside a FIP, link other FIPs and FRCs relatively (`./fip-0054.md`, `../FRCs/frc-0042.md`). Revise a large FIP through small, focused PRs.

## Specifying a change

- Define every value, unit, encoding and rounding rule the change introduces. Params, returns and state are DAG-CBOR tuples, so give field order; for events give each entry's key, codec and index flags. Say which CID or address form a byte string holds. Consensus arithmetic is integer-only: state the precision and rounding, never floating point.
- Cover the edges an implementer will hit: empty inputs, terminated, faulty or expired sectors, sectors not yet proven, the first and last epoch of a window, repeated calls.
- Name methods with their number (`CurrentTotalPower (power method 9)`) and exit codes with name and number. A method that users or contracts can call keeps its params and return shape forever. A new shape, even one optional trailing field, is a new method with a new number (as miner `ExtendSectorExpiration2` followed `ExtendSectorExpiration`); don't specify a method that accepts both shapes or switches behaviour on tuple length. New exported methods take FRC-0042 numbers. A method whose caller check admits only built-in actors may change shape if the FIP says so and names the callers.
- State whether a state migration is required, and if so what it changes, field by field. An optional trailing field on a state struct, written as entries are rewritten, is a lazy migration: it leaves two shapes on chain for good. It is a last resort; a FIP that uses one names it as such and justifies it.
- Cron and other implicit-message work must be bounded per epoch, and the FIP says what happens when it fails.
- Say how new work is charged for. An EVM FIP states that gas follows Filecoin metering (FIP-0054), not Ethereum's schedule, and lists every deviation from the upstream EIP.
- For the upgrade that ships the change, write "the activation network version" or "the activation actors version" rather than guessing a number; name past versions by number.
- Where readers might assume a change spreads (other actors, method numbers, exit codes, events), list what stays unchanged.
- Specify protocol behaviour. Lotus or Curio code paths belong in Implementation.

The builtin-actors `AGENTS.md` ("Methods and callers", "Encoding and state layout", "Versions and network upgrades") and the ref-fvm `AGENTS.md` hold the rules behind these points; read them before specifying an actor or VM change.

## Writing

FIPs are read by people who don't have all day: implementers, SPs, client developers and governance participants. Optimise for brevity: the shortest text that specifies the change completely. Prefer a table to prose for parameters and a list to paragraphs for rules, and move supporting analysis to `resources/`.

- The Simple Summary and Abstract differ; don't paraphrase one into the other.
- Say each thing once, plainly; Design Rationale explains choices without restating the Specification. Cut preamble, text written to pre-empt a reviewer, and promises the protocol doesn't enforce. A required section with nothing to report gets one sentence saying so.
- A FIP entering Last Call with an open question is incomplete. Resolve it, cut the scope that raises it, or keep it in TODO.
- Don't invent discussion links, measurements, benchmarks, test vectors or implementation PRs; put the gap in TODO. Change Motivation is quantified where it can be, with sourced, dated measurements in `resources/`.
- Outside Implementation, avoid text that goes stale: "currently", "after the recent fix", live network statistics stated as permanent, links to in-flight PRs.
- Pick a term, define it once and use only it. Check quantifiers ("all", "at most once", "never") against every case.
- Backwards Compatibility names who breaks (tooling that decodes state, params or events; contracts; wallets) and whether a network upgrade is required. Security Considerations cover what a hostile caller, SP or contract can do with the change.
- Test Cases enumerate distinct behaviours, each a scenario and its expected result; drop cases another already covers.
- Incentive Considerations state the economic effect on each party, with numbers where they exist. Product Considerations cover what clients, SPs and tooling must do.
- Implementation lists every repository with its work: builtin-actors, go-state-types (types and migration), ref-fvm and filecoin-ffi if the VM changes, Lotus, Forest, and Venus or Curio where affected. Mark optional follow-ups as optional.

## Reviewing a FIP

Read the actors, VM or client code the FIP changes, and verify its claims (method numbers, state fields, EIP behaviour, measurements) against code and sources. Comment on concrete defects: an undefined value, an unspecified edge, a contradiction, a changed caller contract, a missing migration or failure path, text that will go stale. Skip wording preferences unless they create ambiguity.

## Pull requests

- Title PRs `FIP-NNNN: <change>` (or `FRC-NNNN:`), using the assigned number once there is one.
- Report suspected vulnerabilities as the [Filecoin security policy](https://github.com/filecoin-project/community/blob/master/SECURITY.md) describes, never in a public issue, Discussion or FIP.

## Maintaining agent context

Fix this file in the same PR as a change that makes it wrong. `CLAUDE.md` contains only `@AGENTS.md`, so Claude Code loads this file.
