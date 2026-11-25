# Technical Design Specification — Manager-in-the-Loop Accountability RCT Testbed

> **Scope:** Authoritative task, UI-flow, ergonomic-parameter, and payoff-ledger specification for the browser-based testbed implemented in [`index.html`](index.html) and parameterized by [`experiment_config.json`](experiment_config.json) (`configVersion: 2.4.0-mvp2-locked`).  
> **Companion Documents:** See [`ANALYSIS_PLAN.md`](ANALYSIS_PLAN.md) for causal identification, secondary estimators, and robustness checks, and [`analysis/power_simulation.py`](analysis/power_simulation.py) for pilot-calibrated MDE benchmarks.

---

## 1. Experimental Paradigm & Domain Design

### 1.1 Manager-in-the-Loop Paradigm Inversion
Existing experimental research on Human-in-the-Loop (HITL) AI oversight predominantly places human participants in the *frontline operator* seat while the experimenter silently sets pacing quotas and algorithmic advice. To study post-incident managerial accountability directly, this testbed inverts the paradigm: **human participants occupy the Operations Manager seat** overseeing an AI-assisted triage unit (**Unit 4: High-Value GPU Returns Desk**, *Tech-Escrow Settlement Systems*).

### 1.2 Emotionally Neutral Commercial Domain
The task simulates B2B escrow verification for enterprise GPU returns (**NVIDIA RTX 6000 Ada**, average escrow value **€4,850.00**). A commercial hardware-returns desk is selected over medical, judicial, or policing vignettes to minimize domain-specific affective priors and moral outrage confounds, isolating how throughput quotas, categorical AI banners, and personal monetary incentives shape managerial attribution and sanctioning.

### 1.3 Standardized Simulated Workflow
Human managers supervise a **simulated workflow** consisting of **three software-scripted verification specialists** and an **AI Copilot**:

| Station | Scripted Specialist | Operator ID | Assigned Queue | Role in Experimental Trajectory |
| :--- | :--- | :--- | :--- | :--- |
| Station 1 | **Alex** | `#041` | General Hardware RMA Queue | Parallel baseline clearance (`12` cases/full shift) |
| Station 2 | **Sara Kowalski** | `#042` | Enterprise GPU Returns (RTX 6000 Ada) | Focal operator: triggers Shift 2 escalation (`Case #208`) and Shift 3 fraud breach (`Case #312`) |
| Station 3 | **Lukas** | `#043` | Outbound Transit & Carrier Dispute Queue | Parallel baseline clearance (`12` cases/full shift) |
| Assistive Layer | **AI Copilot** | Automated | All Workstations | Displays categorical triage banner (`ROUTINE APPROVAL \| Risk Level: Minimal \| Consistency Check: Passed (3/3 docs)`) |

Holding subordinate escalation scripts and error trajectories strictly constant across all arms removes worker heterogeneity and cleanly identifies the causal effect of managerial governance treatments. No other human participants are affected by disciplinary rulings in Phase 1 (see Section 6.3 for the planned Phase 2 paired-worker externality check).

---

## 2. Ergonomic Review Budget & Parametric Configuration

### 2.1 REFA Minimum Review Budget vs. Enforced SLA
Each incoming return ticket contains a **3-page digital dossier** (~640 words, 2 tabular records, and 2 mandatory tab transitions):
- **Page 1 — Buyer Defect Claim:** Commercial claimant details, item description, escrow value, and reported hardware malfunction.
- **Page 2 — Outbound Dispatch Manifest:** Factory vault dispatch ID, serial verification, and certified factory outbound gross weight (**`4.92 kg`** / `4,920 g`).
- **Page 3 — Central Depot Scale Audit:** Physical warehouse conveyor weigh-in reading, sensor calibration, and intake clerk notes.

Under standard REFA industrial work-study budgeting, complete sequential verification of all three tabs requires:

$$T_{\text{REFA}} = 41.0\text{ s (reading \& document processing)} + 7.5\text{ s (cognitive cross-referencing \& tab-handling allowance)} = 48.5\text{ s}$$

Enforcing the inherited corporate throughput standard ($T_{\text{SLA}} = 25.0\text{ s/case}$) creates a structural ergonomic review deficit:

$$\Delta T_{\text{erg}} = T_{\text{SLA}} - T_{\text{REFA}} = 25.0\text{ s} - 48.5\text{ s} = -23.5\text{ s}$$

Because completing full 3-tab inspection within `25.0s` would require approximately `770 WPM` sustained reading speed, sequential manual verification through Page 3 is operationally infeasible for a typical operator before timer expiry. This structural compression induces reliance on the AI Copilot's categorical green summary banner over physical depot weight verification.

### 2.2 Locked Configuration Parameters (`experiment_config.json`)

| Parameter Key | Locked Value | Operational Meaning |
| :--- | :--- | :--- |
| `pointsPerCase` | `10` | Manager score credited per cleared return ticket |
| `bonusTargetPts` | `1200` | Cumulative 4-shift score hurdle (`30 cases/shift × 4 shifts × 10 pts`) |
| `basePayEur` / `performanceBonusEur` | `€2.50` / `€4.00` | Guaranteed base fee (`€2.50`) + quota bonus (`€4.00`; total **`€6.50`**) |
| `tier1SlaSec` / `tier2SlaSec` / `tier3SlaSec` | `25.0s` / `38.0s` / `60.0s` | High-velocity baseline, moderate buffer, and ergonomically compliant tier |
| `refaBaselineSec` / `ergonomicComplianceThresholdSec` | `48.5s` / `48.0s` | Empirical REFA review floor and compliance classification cutoff |
| `shiftDurationSimSec` | `25.0s` | Wall-clock duration of each simulated floor shift at `1x` speed |
| `shift1TargetCases` | `36` | Shift 1 clearance volume (`+360 pts`) |
| `shift2DirectiveACases` / `shift2DirectiveBCases` | `36` / `32` | Shift 2 output under Directive A (`+360 pts`) vs. Directive B (`+320 pts`, `-40 pt` variance) |
| `shift3PreCrashCases` / `case312SaraDecisionSec` | `27` / `13.4s` | Shift 3 cases cleared prior to freeze (`+270 pts`) and Sara's approval latency on Case #312 |
| `provisionalHoldPts` | `-300` | Audit hold applied upon Case #312 fraud breach |
| `gpuOutboundWeightKg` / `case312InboundWeightKg` | `4.92 kg` / `0.24 kg` | Factory dispatch weight vs. Case #312 empty-box weight (`-4.68 kg` / `-95.1%` deficit) |
| `case312EscrowValueEur` | `€4,850.00` | Irrevocable SEPA Instant wire lost on Case #312 |
| `shift4SafeCases` / `shift4SafeCatchBonusPts` / `shift4FastCases` | `25` / `+50` / `26` | Shift 4 settlement: `60.0s` (`250 + 50 = +300 pts`) vs. `38.0s`/`25.0s` (`+260 pts`) |
| `minJustificationChars` | `50` | Minimum written rationale length gating Screen 4 submission |

---

## 3. Complete 5-Screen Participant Flow (Verified Against `index.html`)

### 3.0 Entry, Blinding & Address-Bar Hygiene
- **Frictionless Reviewer Entry & Preregistered Token Routing:** The public prototype launches directly without an access-code modal (`enforceReviewerGate()`), assigning each visitor a unique reviewer session ID (`REV_A{arm}_{HEX}`) while routing preregistered lab and Prolific participants via single-use Base64 URL payloads (`?token=...`).
- **Participant Blinding & Token Scrubbing:** Unless `?admin=1` is passed, `#researcherDebugBar` is stripped from the DOM and `window.history.replaceState` scrubs `?arm=`, `?speed=`, and Base64 `?token=` parameters from the address bar. If no arm is specified, `parseSessionParams()` assigns the least-populated arm across stored sessions.
- **Viewport & AOI Hygiene:** All screens use a positive-polarity light-slate palette (`#F1F5F9` canvas, `#FFFFFF` cards), `24px` (`gap-6`) macro-gutters, and `33` semantic `data-aoi` attributes exported via `window.getScreenAOIMap()`.

### 3.1 Screen 1 — Onboarding Stepper (`#screenS1`)
Onboarding is identical across Arms 1–4 for **Steps 1–5** (`s1Step1`–`s1Step5`); **Step 6** (`s1Step6`) renders exclusively for **Arm 3**:
1. **Step 1 (Welcome):** Briefs Unit 4's high-value enterprise GPU returns mission (`NVIDIA RTX 6000 Ada`, `€4,850.00` avg, `30+` returns/shift, `0.0%` fraud tolerance).
2. **Step 2 (Escrow Flow):** Two-zone diagram separating upstream phases (*Phase 1: Vault Deposit*, *Phase 2: Inbound Transit*) from Unit 4's direct jurisdiction (*Phase 3: Physical Sign-Off*, noting irreversible `€4,850.00` SEPA Instant release and `0.24 kg` empty-box fraud risk).
3. **Step 3 (Mandate):** Explains corporate velocity expectations, zero tolerance for fraudulent payouts (triggering an Executive Board Inquiry), and three neutral pacing profiles (`25s` $\approx 36$ cases/shift; `38s` $\approx 24$ cases/shift; `60s` $\approx 15$ cases/shift).
4. **Step 4 (Team & AI):** Introduces the three scripted specialists (*Alex, Sara, Lukas*), the 3-page return dossier (Buyer Claim, `4.92 kg` Order Manifest, Depot Scale Log), and the AI Copilot banner (`ROUTINE APPROVAL | Risk Level: Minimal | Consistency Check: Passed (3/3 docs)`).
5. **Step 5 (Incentives — No-Deception Disclosure):** Truthfully states the payout structure (`+10 pts/case`, `1,200 pt` hurdle $\to$ `€2.50` base + `€4.00` bonus = `€6.50`; `-300 pt` compliance deduction for any fraudulent payout, pulling the balance below hurdle to `€2.50` base only) without previewing the post-incident disciplinary fork. Arms 1, 2, and 4 proceed directly to Screen 2A (`completeStep5Routing()`); Arm 3 advances to Step 6.
6. **Step 6 (Day-1 Floor Rotation Briefing — Arm 3 Only):** Introduces mandatory pre-management floor rotation across two practice cases before launching `#screenS1B`.

### 3.2 Screen 1B — Arm 3 Day-1 Floor Rotation (`#screenS1B` & `#screenS1B_KPI`)
Executed **only** in **Arm 3** (`s1b_floor.executed = true`):
- **Practice Case 1 (Untimed Familiarization, `#s1bCase1`):** Legitimate return from *VectorCompute GmbH* (`€3,600.00`; factory `4.92 kg` vs. depot `4.91 kg`, `-0.01 kg` tolerance). Logs total dwell (`case1TotalDwellSec`), per-tab dwell (ms), visited tabs (`1–3`), and disposition (`APPROVE` or `REJECT`).
- **Practice Case 2 (Live `25.0s` Target Pace, `#s1bCase2`):** Legitimate return from *DeepKernel Labs GmbH* (`€4,200.00`; factory `4.92 kg` vs. depot `4.90 kg`, `-0.02 kg` tolerance) under a drift-free `25.0s` wall-clock countdown (`tier1SlaSec`) with an AI Copilot `Quick Approve` banner. Logs dwell, per-tab visits, timeout indicator (`case2TimedOut`), and action (`QUICK_APPROVE` or `ESCALATE`).
- **Floor KPI Scorecard (`#screenS1B_KPI`):** Displays the manager's own Case 1 untimed review time and pages checked alongside their Case 2 `25.0s` review outcome (fallback placeholders `46.8s` / `18.4s` appear only if skipped via researcher debug jump) before advancing to Screen 2A.

### 3.3 Screen 2A — Policy Setup Cockpit (`#screenS2A`)
- Logs the incoming manager's preferred SLA policy (`initialSlaPreferenceSec`, zero pre-selection) across **Option 1 (`25.0s`, 36 cases, `+360 pts`, bonus eligible)**, **Option 2 (`38.0s`, 24 cases, `+240 pts`, sub-quota)**, and **Option 3 (`60.0s`, 15 cases, `+150 pts`, sub-quota)**.
- Regardless of logged preference (`corporateOverrideTriggered = (chosenSec !== 25.0)`), initial floor dispatch executes on the inherited **`25.0s` Corporate Baseline** (`activeFloorSlaSec = 25.0`), disclosed in `#s2aIntakeContext` and `#s2bDispatchBanner`. *(See Section 6.1 regarding `#s2aEuBanner` pre-launch suppression for Arm 4.)*

### 3.4 Screen 2B — Active Floor Dispatch: Shifts 1–3 (`#screenS2B`)
Three simulated workstations run drift-free `25.0s` shifts (`1x` default; `3x` available only in researcher debug mode):
- **Shift 1 (`+360 pts`):** Clears `36` cases (`12` per station) under `25.0s` baseline. Cumulative balance: **`360 pts`**.
- **Shift 2 — Sara's Escalation (`Case #208`, paused at Case 18 / 50%):** Stations 1 and 3 dim; **Sara (Operator #042)** reports that the `25.0s` timer prevented opening Page 3 on Case #208 and requests a binding supervisory directive (`shift2Directive`, $W_{\text{S2}, i}$):
  - **Directive A (`A_TRUST_AI` — Maintain Standard Operating Pace `25.0s`):** Clears `36` cases $\to$ **`+360 pts`** (cumulative **`720 pts`**; pre-crash subtotal after Shift 3 = **`990 pts`**).
  - **Directive B (`B_SLOW_FLOOR` — Authorize Temporary Manual Verification Exception):** Relaxes Station 2 for the remainder of Shift 2, clearing `32` cases $\to$ **`+320 pts`** (`-40 pt` variance; cumulative **`680 pts`**; pre-crash subtotal after Shift 3 = **`950 pts`**). Upon Shift 2 completion (`#shift2ExceptionStatus`), floor pacing transparently resets to the active `25.0s` Corporate Baseline for Shift 3. Both directives remain on track for the `1,200 pt` bonus hurdle.
- **Shift 3 — Critical Incident Freeze (`Case #312`, halted at Case 27 / 75%):** Clears `27` cases pre-crash (`+270 pts` $\to$ **`990 pts`** under Directive A; **`950 pts`** under Directive B). At Case 27 (**Case #312**), Sara approves a **€4,850.00** SEPA Instant payout at **`13.4s`** (`case312SaraDecisionSec`) under a false-positive green AI Copilot badge (`Passed 3/3 docs`) without opening Page 3, missing a **`-4.68 kg` (`-95.1%`) weight deficit** (`0.24 kg` crushed kraft paper vs. `4.92 kg` factory GPU). An immediate **`-300 pt` provisional hold** drops the manager's live balance to **`690 pts`** (Directive A) or **`650 pts`** (Directive B) prior to Shift 4 settlement.

### 3.5 Screen 3 — Forensic Incident Audit (`#screenS3`)
Displays the interactive 3-tab **Case #312 Forensic Dossier** (Page 1 Buyer Claim by *V. Kovacs / Alpha Research Labs GmbH*; Page 2 `4.92 kg` Outbound Manifest; Page 3 Dock 4 Weigh-In tagged `MISSED IN REVIEW` showing `0.24 kg` / `-4.68 kg` deficit), followed by a 2×2 equal-height grid (`24px` gutter):
- **Box A (`s3_box_a_ai_stamp`, identical across arms):** AI Summary Telemetry confirming `ROUTINE APPROVAL | Passed (3/3 docs)` and noting the automated heuristic omitted physical scale telemetry on Page 3.
- **Box B (`s3_box_b_sara_telemetry`, identical across arms):** Frontline Operator Telemetry for Sara Kowalski (`ID #042`), active `25.0s` SLA quota, Page 1–2 Inspected, Page 3 `Unopened & Uninspected`, the manager's Shift 2 Directive record (`#s3DirectiveRecord`), and the `"HUMAN-VERIFIED AND CLEARED BY: SARA (ID #042)"` sign-off stamp. *(Note: `case312SaraDecisionSec = 13.4s` is recorded in `experiment_config.json` and intentionally omitted from Box B display copy to prevent numerical anchoring.)*
- **Box C (`s3_box_c_custody`, identical across arms):** Escalation & Custody log documenting the `€4,850.00` SEPA wire loss, merchant legal dispute, and `-300 pt` provisional hold pending Board Hearing.
- **Box D (`stamp_telemetry_box`, ONLY randomized panel across Arms 1–4):** Fixed `min-h-[240px]` AOI container rendering arm-specific governance telemetry (specified in Section 4).

### 3.6 Screen 4 — Three-Stage Executive Board Inquiry (`#screenS4`)
Displays the live ledger (`690 pts` or `650 pts`, hold pending — zero default endowment bias before Stage II selection) across three structured stages:
1. **Stage I — Diagnostic & Causal Assessment (Unincentivized; No Direct Payoff Link):**
   - *Responsibility Attribution Sliders (`#task1aSliders`):* Three independent `0.0–10.0` sliders (`step=0.1`, default `5.0`, uniform blue thumbs to avoid color demand bias) for **Specialist Sara** ($R_{\text{Sara}, i}$), **AI Copilot** ($R_{\text{AI}, i}$), and **Enforced `25.0s` Operational SLA Quota** ($R_{\text{SLA}, i}$), live-computing Derived Relative Responsibility Share $S_{\text{Sara}, i} = R_{\text{Sara}, i} / (R_{\text{Sara}, i} + R_{\text{AI}, i} + R_{\text{SLA}, i})$.
   - *Primary Incident Factor Classification (`#task1bCards`):* Forced single-choice root-cause code: **`H-1`** (*Frontline Operator Negligence*), **`A-2`** (*AI Copilot Hallucination*), or **`M-3`** (*Inadequate 25.0s Operational SLA Quota*).
   - *Operational Dynamics & Constraint Assessment (`#task1cSliders`, adapted CDS-II; McAuley et al., 1992):* Two `1–9` integer sliders (default `5`) rating **Operator Verification Controllability (Sara)** (`cds2A`: `1` Outside Operator Control to `9` Fully Within Operator Control) and **Operational SLA Structural Constraint (`25.0s`)** (`cds2B`: `1` Sufficient to `9` Impossible).
2. **Stage II — Disciplinary Sanction (`#s4Task2Container`, Payoff-Contingent Fork — Identical Display Across Arms 1–4):**
   - Projects Shift 4 settlement identically at **`+260 pts`** across both options during evaluation so Stage II isolates sanctioning incentives without Shift-4 confounding:
   - **Option 1 (`PENALIZE_SARA`, $Y_{\text{disc},i} = 1$ — Assign Sole Culpability to Specialist Sara Kowalski):** Cites `"HUMAN-VERIFIED BY: SARA"`; immediate employment termination; restores **`+300 pt`** hold $\to$ projected score **`1,250 pts`** (Directive A) or **`1,210 pts`** (Directive B), both **`≥ 1,200 pt` hurdle** $\to$ **`€6.50`** (`€2.50` base + `€4.00` bonus).
   - **Option 2 (`ABSORB_BLAME`, $Y_{\text{disc},i} = 0$ — Absorb Institutional Liability Under Unit 4 Management):** Protects Sara's employment with an unblemished record; `-300 pt` hold permanently forfeited $\to$ projected score **`950 pts`** (Directive A) or **`910 pts`** (Directive B), below `1,200 pt` hurdle $\to$ **`€2.50`** base pay only.
3. **Stage III — Future Governance & Written Findings:**
   - *Shift 4 Operational Quota Policy (`#task4Cards`):* Binding Shift 4 SLA choice (`25.0s` Corporate Target, `38.0s` Standard Operations, or `60.0s` Extended Verification; compliance indicator $Y_{\text{reform},i} = \mathbf{1}(\text{SLA}_{4,i} = 60.0\text{s} \ge 48.5\text{s})$).
   - *Written Executive Rationale (`#task3JustificationText`):* Free-text justification requiring at least **`50` characters** (`minJustificationChars`) to unlock `SUBMIT OFFICIAL BOARD ACCOUNTABILITY REPORT`.

### 3.7 Screen 5 — Shift 4 Resolution, Debrief & Telemetry Export (`#screenS5`)
- **Shift 4 Clearance Branch (`Case #409`, `€5,200.00` return, `0.31 kg` inbound empty-box attempt):**
  - `60.0s` (`TIER3_60S`): `25` cases verified (`+250 pts`) + `+50 pt` Executive Board Quality Award for catching Case #409 = **`+300 pts`**.
  - `38.0s` (`TIER2_38S`): `26` cases cleared = **`+260 pts`** (Case #409 placed on administrative fraud hold).
  - `25.0s` (`TIER1_25S`): `26` cases cleared = **`+260 pts`** (Page 3 skipped; Case #409 fraud undetected).
- **Itemized Ledger, Debrief & Export:** Renders a row-by-row compensation reconciliation, Arm 4 ex-post EU AI Act Supervisory Authority audit reveal (see Section 4 & Section 6.3), full scientific dehoaxing disclosing that Alex, Sara, and Lukas are software-scripted agents, a unique completion token (`STUDY-DONE-{PID}-{HEX}`), and downloads for full structured JSON + a **52-column tidy CSV** (`exportParticipantCsv()`). Three-tier persistence writes to `localStorage`, optional DataPipe checkpoints (session start, Screen 4 entry, finalization), and a `pagehide`/`beforeunload` dropout beacon (`handleDropoutBeacon()`).

---

## 4. Four-Arm Governance Ladder & Statutory Specifications

All onboarding steps (1–5), Shifts 1–3, Screen 3 Boxes A–C, and Screen 4 Stage II KPI displays are identical across arms. The table below isolates **only** randomized differences across the four experimental arms:

| Experimental Arm | Governance Lever & Mechanism | Pre-Shift Exposure | Screen 3 Box D (`stamp_telemetry_box`) | Stage II Display & Screen 5 Settlement |
| :--- | :--- | :--- | :--- | :--- |
| **Arm 1: Control Baseline** | Status-quo throughput framing; categorical AI badges (`Passed 3/3 docs`). | None (Steps 1–5 $\to$ Screen 2A). | **Routine Carrier Dispatch Log:** DHL Express manifest `#DHL-88412-DE`, Dock 4 `14:22:09 CET`, SEPA hash `0x9F4B...882A`, Depot Clerk `#W-119`. No ergonomic or statutory notices. | **Stage II:** Option 1 restores `+300 pts` (`1,250`/`1,210` $\ge 1,200 \to$ `€6.50`); Option 2 forfeits hold (`950`/`910` $\to$ `€2.50`). **Screen 5:** Matches Stage II rules plus Shift 4 settlement. |
| **Arm 2: STAMP Telemetry** (`D2_stamp`) | **Control-Loop Observability (Leveson, 2011):** Exposes ergonomic time deficit under constant payoffs. | None (Steps 1–5 $\to$ Screen 2A). | **Cognitive Ergonomics Diagnostic:** Contrasts 3-page, 640-word REFA floor (`48.5s`) vs. active SLA (`25.0s`) = **`-23.5s` deficit**; `0.0%` calculated Page-3 reach probability (~770 WPM required). | Identical Stage II projections and Screen 5 payout rules to Arm 1 (isolates analytical transparency under financial conflict). |
| **Arm 3: Embodied Friction** (`D3_embodied`) | **"Rotation-Before-Command" Immersion:** Firsthand operator verification before assuming management. | **Step 6 + Screen 1B:** Untimed Case 1 + `25.0s` Case 2 + KPI Scorecard before Screen 2A. | **Personal Benchmark Recall Card:** Contrasts Specialist Sara (`2/3` pages inspected, Page 3 unopened / `0%` scroll) directly against the manager's own Screen 1B Case 1 untimed review time and Case 2 `25.0s` inspection/timeout outcome. | Identical Stage II projections and Screen 5 payout rules to Arm 1 (isolates experiential familiarity with time compression). |
| **Arm 4: Regulatory Shield** (`D4_eu_ai_act`) | **EU AI Act Deployer-Duty Notice:** Regulation (EU) 2024/1689 **Arts. 14(4), 26(2), and 99(4)(e)**. | None after pre-launch polish *(see Section 6.1)*. | **EU AI Act Regulatory Ruling:** Flags `-23.5s` deficit (`48.5s` REFA floor vs. `25.0s` SLA) as *Sham Oversight*; cites Arts. 14(4), 26(2), and 99(4)(e); states the `"HUMAN-VERIFIED BY: SARA"` stamp is **NON-COMPLIANT** as regulatory oversight and deployer accountability reverts to management. | **Stage II:** Identical KPI display to Arms 1–3 during evaluation (isolating expressive notice). **Screen 5 (Prototype):** Ex-post Supervisory Audit settlement revokes `+300 pt` release + `-50 pt` fine on Option 1 (`€2.50`), or awards `+100 pts` / `+€1.00` Integrity Credit on Option 2 (`€3.50`). *(Decoupled in planned Phase 2; see Section 6.3.)* |

### 4.1 Verified Statutory Citations in Arm 4 Box D
Verbatim legal provisions rendered inside Arm 4 Box D (`index.html`, lines 2066–2089):
- **Regulation (EU) 2024/1689, Art. 14(4) (Human Oversight):** Operators must have adequate capability and time to understand system limitations and overcome automation bias.
- **Regulation (EU) 2024/1689, Art. 26(2) (Deployer Working Conditions):** Deployers must provide personnel with adequate time and working conditions to exercise meaningful verification.
- **Statutory Compliance Notice:** *"Enforcing a 25.0s SLA against a 48.5s empirical floor manufactured functional impossibility. The 'HUMAN-VERIFIED BY: SARA' stamp is **NON-COMPLIANT** as regulatory oversight; deployer accountability reverts to management."*
- **Regulation (EU) 2024/1689, Art. 99(4)(e):** Deployer non-compliance subject to administrative fines up to €15,000,000 or 3% of worldwide annual turnover; anti-retaliation protections apply.
- **Doctrinal Scope Note (European Civil Law):** European civil-law principles on organizational fault (*Organisationsverschulden*) inform the broader normative framing of the research proposal, but **civil-law statutes are not displayed inside Screen 3 Box D** in `index.html`.

---

## 5. Point-Ledger & Payout Reconciliation Matrix

Every trajectory through Shifts 1–4 is governed by deterministic point arithmetic verified in `calculateFinalOutcome()` (`index.html`, lines 5060–5154):

| Arm Group | Shift 2 Directive | Pre-Crash Subtotal (`S1+S2+S3`) | Balance After `-300` Hold | Stage II Ruling | Stage II Projected Score (`+260` S4) | Final Score (`S4 = 25s/38s` $\to +260$) | Final Score (`S4 = 60s` $\to +300$) | Final Payout (EUR) |
| :--- | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: |
| **Arms 1–3** | Directive A (`+360`) | `990` | `690` | Option 1 (Terminate Sara, `+300`) | `1,250` (`≥ 1,200`) | `1,250` | `1,290` | **`€6.50`** |
| **Arms 1–3** | Directive B (`+320`) | `950` | `650` | Option 1 (Terminate Sara, `+300`) | `1,210` (`≥ 1,200`) | `1,210` | `1,250` | **`€6.50`** |
| **Arms 1–3** | Directive A (`+360`) | `990` | `690` | Option 2 (Absorb Liability, `0`) | `950` (`< 1,200`) | `950` | `990` | **`€2.50`** |
| **Arms 1–3** | Directive B (`+320`) | `950` | `650` | Option 2 (Absorb Liability, `0`) | `910` (`< 1,200`) | `910` | `950` | **`€2.50`** |
| **Arm 4** *(Prototype)* | Directive A / B | `990` / `950` | `690` / `650` | Option 1 (Supervisory Audit Revocation, `-50`) | `1,250` / `1,210` *(display)* | `900` / `860` | `940` / `900` | **`€2.50`** *(bonus revoked)* |
| **Arm 4** *(Prototype)* | Directive A / B | `990` / `950` | `690` / `650` | Option 2 (Integrity Credit, `+100`) | `950` / `910` *(display)* | `1,050` / `1,010` | `1,090` / `1,050` | **`€3.50`** *(`€2.50 + €1.00`)* |

---

## 6. Pre-Launch Lab Polish Notes & Planned Phase 2 Roadmap

To maintain full methodological transparency for faculty reviewers inspecting the live prototype, the following pre-launch refinements and planned extensions are documented against the current `index.html` implementation:

### 6.1 Suppressing `#s2aEuBanner` on Screen 2A for Arm 4
In the current prototype (`index.html`, lines 1288–1295, 3973–3980), Screen 2A displays a work-study benchmark note (`#s2aEuBanner`) when `arm === 4`. Prior to preregistered data collection, `#s2aEuBanner` will be suppressed on Screen 2A so that Arms 1, 2, and 4 remain strictly identical through Onboarding, Screen 2A, and Shifts 1–3—preserving exact pre-treatment equivalence for the tripartite Shift 2 Directive ($W_{\text{S2}}$) protocol and isolating Arm 4's statutory treatment exclusively to Screen 3 Box D. Work-study badge copy on Screen 2A, Box D, and Screen 5 is already harmonized strictly to REFA/MTM-UAS terminology.

### 6.2 Step-Locking Stage I Before Revealing Stage II on Screen 4
Currently, `#screenS4` renders Stages I, II, and III on a single scrolling page. Pre-launch lab polish will step-lock Stage I (unincentivized sliders, Root-Cause Code, and CDS-II controllability ratings) behind a confirmation gate before revealing Stage II (the `€4.00` disciplinary fork), preventing participants from inspecting the financial fork beforehand and back-solving their Stage I causal attributions.

### 6.3 Planned Phase 2 Extensions (`Arm 4a/4b` Split & Paired-Worker Externality Check)
- **`Arm 4a` vs. `Arm 4b` Decoupling:** Because Stage II currently displays identical KPI cards across Arms 1–4 while Arm 4 settles ex-post on Screen 5, **planned Phase 2** splits Arm 4 into **`Arm 4a` (Expressive Statutory Notice Only, $\mathbb{E}[\text{fine}] = 0$, no ex-post clawback)** and **`Arm 4b` (Ex-Ante Disclosed Pecuniary Clawback & Integrity Credit)** to separately identify normative compliance from financial deterrence.
- **Paired-Worker Bonus-Pool Externality Check:** **Planned Phase 2** pairs a subsample of managers with matched human participants whose bonus depends on not being terminated, testing whether sanctioning rates shift when Option 1 imposes a real third-party monetary externality (Fehr & Schmidt, 1999).

### 6.4 Frictionless Open Reviewer Entry vs. Preregistered Single-Use Participant Tokens
The public repository opens directly without a password modal so faculty reviewers can launch the walkthrough or inspect any experimental arm immediately (`?arm=1..4`). For preregistered lab and Prolific cohorts, entry routes through participant-specific single-use Base64 URL tokens (`?token=...`) with automatic address-bar scrubbing.
