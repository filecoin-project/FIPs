# FIP-100 Monitoring Committee Charter

### Origin
This committee was established following extensive community feedback during FIP-100's Last Call period, in response to legitimate concerns about real-world economic impacts that economic modeling alone could not address.  
The committee exists to monitor real-world network behavior, surface unintended consequences, and recommend appropriate action in a timely, transparent, and community-centered manner.

### Mission
To pioneer responsive governance by demonstrating that decentralized protocols can be both innovative and deeply responsive to community needs — making data-driven decisions that put ecosystem health and community voice at the center of Filecoin's evolution.

### Core Authority
This independence ensures authentic expertise rather than corporate messaging.  
The committee has explicit authority to recommend that Core Developers:

- Revert FIP-100 entirely if it demonstrably harms the ecosystem  
- Amend it through follow-up proposals based on empirical data  
- Continue monitoring if impacts align with predictions  

---

## Article I: Committee Composition

The committee includes diverse members across Filecoin roles:

- **Luca Nicoli** – CryptoEconLab (Research)  
- **Beck** – Storage Provider / DevOps  
- **Danny O'Brien** – Filecoin Foundation  
- **David Gasquez** – Data Engineer  
- **Henry Moon** – Storage Provider  
- **Irene Giacomelli** – FilOz (FIP-100 proposer)  
- **Ørjan Røren** – Ecosystem Contributor  
- **rvagg** – Core Developer  

This diversity is intentional to ensure technical, economic, operational, and community views are represented — including both supporters and critics of FIP-100.

### Section 1.2: Individual Capacity Service
Members serve in their individual professional capacity, not as organizational representatives.

- Members cannot be instructed by their employers/organizations on how to vote or what positions to take  
- Organizations cannot replace or rotate their "representative" on the committee  
- Members' reports and positions reflect their individual assessment, not organizational policy  
- No member can claim to speak on behalf of their organization through committee activities  

### Section 1.3: Committee Stability
During the initial formation phase of the FIP-100 Monitoring Committee (Phase 1), no removal mechanism exists except voluntary withdrawal.  
This design ensures that members can raise controversial concerns without fear of retaliation. Members act as independent watchdogs rather than representatives, promoting candid oversight and data-driven accountability.

In later phases of Filecoin’s progressive decentralization, governance mechanisms may introduce community-driven selection and removal processes for committee membership.

The committee shall remain active until completion of its designated review mandate — specifically until the FIP-100 review and monitoring functions can responsibly be transitioned to community governance.

It shall be dissolved upon unanimous agreement of all active members that the following conditions are satisfied:

- **Operational Stability:** Monitoring has remained stable for at least six (6) months, with no major alerts or deviations.  
- **Community Handover Readiness:** The dashboard and escalation protocols can be transitioned to community stewardship with documentation for continuity.

---

## Article II: Operating Principles

### Section 2.1: Sentinel Model
The committee operates on a *sentinel model* — each member acts as an independent watchdog rather than seeking collective consensus.  
Consensus is **not required**. Any single member may publish concerns and trigger escalation.

### Section 2.2: Independence
Members may submit different or even contradictory reports.  
This ensures minority concerns reach decision-makers without being silenced by majority opinion.

### Section 2.3: Transparency
Commitment to radical transparency:

- All meeting notes and reports are public on GitHub  
- Summaries are shared openly with the community  
- Emergency meetings may be called by any member with 48-hour transparency reports  

---

## Article III: Reporting and Escalation

### Section 3.1: Report Authority
Any member may publish a public report at any time detailing concerns about FIP-100's ecosystem impact.

### Section 3.2: Escalation Process

#### Urgent Concerns
1. Member identifies concern  
2. Publishes public report with findings and recommendations  
3. Report scheduled for next Core Devs call  
4. Core Developers must publicly address and explain their response  

#### External Stakeholders
External stakeholders (SPs, clients, developers, or community participants) may escalate issues as follows:

1. **Raise a GitHub Issue:** Describe the concern with supporting data.  
2. **Notify via Public Channel:** Share the GitHub issue link in `#fip-100` Slack channel.  
3. **Committee Response:** A member determines if it requires investigation.  
4. **Transparency:** All escalations remain public and are logged in transparency reports.

#### Regular Monitoring
If no major issues arise:

- Monthly asynchronous check-ins  
- Published summaries and data snapshots  
- Cadence may evolve as community voting matures  

### Section 3.3: Committee Transparency Report

Reports should be submitted before each network upgrade cycle.  
They may include:

#### Quantitative Analysis
- Network onboarding rates (pre/post FIP-100)  
- Gas cost reductions  
- SP revenue impacts  
- Sector extension vs. onboarding ratios  
- Network value metrics  

#### Qualitative Assessment
- SP operational feedback  
- Ecosystem sentiment  
- Lending market impacts  
- Entry barriers and regional effects  

#### Stakeholder Input
- SP interviews and surveys  
- Client and developer feedback  
- Token holder economic impacts  

#### Recommendations
- **Continue:** Maintain trajectory  
- **Amend:** Adjust parameters (with proposed values)  
- **Revert:** Recommend rollback if harm detected  

When a recommendation is issued:
- It’s presented at the next Core Devs call with data and rationale.  
- If warranted, changes proceed through the FIP process.  
- Emergency recommendations may be implemented immediately.  
- All notes, reports, and implementation updates must be published on GitHub.  

**Report Template:**
- Executive Summary  
- Key Findings  
- Supporting Data  
- Community Feedback  
- Risk Assessment  
- Recommendation  
- Timeline / Urgency  

---

## Article IV: Data Access and Analysis

The committee uses live network metrics to monitor economic, operational, and behavioral outcomes of FIP-100.  
All analyses and datasets are public.

### Section 4.1: Key Monitoring Metrics

| S.No | Category | Data Points Tracked | Rationale / Purpose |
|------|-----------|--------------------|---------------------|
| 1 | **Sector-Onboarding Economics & Throughput** | • Daily QAP added (GiB, raw & FIL+)<br>• Average gas per sector (PreCommitBatch2, ProveCommitSectors3, ProveCommitAggregate, etc.)<br>• Mean/median batch size<br>• Count of irrationally small batches<br>• FIL-on-FIL return per sector | Measures whether reduced onboarding costs unlocked additional supply and detects inefficiencies or behavioral frictions. |
| 2 | **New Daily-Fee Burden** | • Total daily fee burn (FIL/day) vs baseline<br>• Per-sector lifetime cost by SP type | Evaluates distributional impacts and alignment with modeled expectations. |
| 3 | **Base-Fee & Blockspace Health** | • Base fee percentiles (p50/p95)<br>• Gas-limit utilization vs maximum onboarding rate | Checks for gas pricing efficiency and non-technical constraints. |
| 4 | **Network Burn & Token Economics** | • Burn composition over time<br>• Circulating-supply growth vs fee burn (%) | Ensures intended distribution of burns and supply effects. |
| 5 | **Grace-Period Behavior** | • Extensions per day during 90-day window<br>• Renewal rate before/during/after grace period | Detects front-loading or liquidity stress during fee transitions. |

---

## Article V: Success Metrics

### Section 5.1: Committee Effectiveness
- Early identification of network issues  
- Timeliness and quality of reports  
- Community trust and confidence  
- Core Dev responsiveness  

### Section 5.2: FIP-100 Assessment Criteria
- Storage provider economic health  
- Network onboarding rates  
- Ecosystem stability and growth  
- Alignment with modeled outcomes  

---

## Article VI: Amendment and Evolution

### Section 6.1: Charter Changes
This constitution may be amended by majority agreement of committee members, with 30 days' public notice.

### Section 6.2: Progressive Decentralization
This committee represents Phase 1 of Filecoin’s decentralized governance oversight.  
In future phases, responsibilities will transition to the community.

Eventually, monitoring becomes open and community-driven:

- Anyone can access on-chain data and dashboards  
- Raise issues via FIPs  
- Engage directly in transparent discussions  

The long-term goal is **not** to expand governance structures but to responsibly dissolve them once community ownership is achieved.

---

## Article VII: Final Provisions

### Section 7.1: Effective Date
This constitution takes effect upon publication and remains active throughout FIP-100 monitoring.

### Section 7.2: Contact and Questions
- **Primary contact:** Danny O'Brien (Filecoin Foundation)  
- **Secondary contact:** Tanisha Katara  
- **Community discussions:** `#fip-100` Slack channel  

### Section 7.3: Foundational Commitment
This committee recognizes that community stakeholders are the foundation of Filecoin's success.  
FIP-100 sparked discourse because protocol economics directly affect participant sustainability.

Filecoin governance commits to evolving responsively when empirical evidence demands correction.  
This committee ensures accountability to real-world data and the lived experiences of participants.

---
