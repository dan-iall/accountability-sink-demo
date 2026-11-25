# Faculty & Reviewer FAQ — Manager-in-the-Loop Accountability RCT Testbed

> **Scope:** Direct methodological, behavioral, ergonomic, and engineering answers for faculty reviewers and experimental referees evaluating the live testbed and repository.  
> **Companion Documents:** [`DESIGN_SPEC.md`](DESIGN_SPEC.md) (5-screen flow, point ledger & statutory copy) · [`ANALYSIS_PLAN.md`](ANALYSIS_PLAN.md) (identification, estimators & robustness) · [`analysis/power_simulation.py`](analysis/power_simulation.py) (reproducible synthetic DGP & MDEs).

**Quick Jump:**
- **A. Paradigm & Behavioral Validity:** [Q1 Manager Seat & Scripted Workers](#q1-why-test-the-operations-manager-over-scripted-workers--and-doesnt-penalizing-a-script-lack-real-harm) · [Q2 GPU Returns Domain](#q2-why-standardize-every-case-on-an-enterprise-gpu-returns-desk-instead-of-healthcare-hiring-or-policing) · [Q3 Screen 2A Override & 38s Steward Tier](#q3-if-a-manager-chooses-380s-or-600s-on-screen-2a-why-does-the-floor-still-run-at-250s--and-why-include-380s) · [Q4 Shift 2 Directive B vs. Shift 3 Crash Paradox](#q4-if-a-manager-pays--40-pts-for-directive-b-in-shift-2-why-does-sara-still-crash-in-shift-3-isnt-that-insubordination)
- **B. Ergonomics, Blinding & Treatments:** [Q5 25.0s vs. 48.5s Calibration](#q5-why-calibrate-the-quota-at-250s-instead-of-150s-against-the-485s-refa-floor) · [Q6 No Quiz Gates & Step 5 Anti-Spoiler](#q6-why-are-there-no-onboarding-comprehension-quizzes-or-checkboxes--and-why-withhold-stage-ii-in-step-5) · [Q7 Arm 4 Anti-Leakage & Phase 2 Split](#q7-why-does-arm-4-display-the-same-stage-ii-fork-hide-the-100-credit-and-defer-arm-4a4b-to-phase-2)
- **C. Measurement, Identification & Power:** [Q8 Independent Sliders & Stage Order](#q8-why-three-independent-010-sliders-instead-of-a-100-sum-slider--and-doesnt-stage-i-distort-stage-ii) · [Q9 Arm 3 Bad Controls & Attrition](#q9-how-do-you-handle-arm-3s-pre-shift-rotation-bad-controls-time-on-task-and-attrition) · [Q10 Parameterized N & Estimator Scope](#q10-why-are-sample-sizes-n--80240-parameterized-rather-than-fixed-upfront)
- **D. Eye-Tracking & Engineering:** [Q11 Positive Polarity & 24px AOIs](#q11-is-eye-tracking-hardware-required--and-why-enforce-positive-polarity-and-24px-gutters) · [Q12 Timing, Snapshots & Pre-Launch Polish](#q12-how-are-timing-drift-parameter-versioning-bot-traffic-and-pre-launch-refinements-handled)

---

## A. Experimental Paradigm & Behavioral Validity

### Q1. Why test the Operations Manager over scripted workers — and doesn't penalizing a script lack real harm?

Across Vaccaro et al.'s (2024) 106-study meta-analysis of human–AI combinations, experimental Human-in-the-Loop (HITL) studies put human participants in the *operator* seat to measure automation bias while the researcher sets pacing quotas invisibly—leaving managerial oversight and post-incident accountability unmeasured.

Placing **human participants in the Operations Manager seat** over three standardized, software-scripted subordinate agents (*Alex, Sara, Lukas*) and an AI Copilot isolates managerial judgment cleanly:
- **Zero unobserved worker variance:** Holding subordinate warnings (`Case #208`) and error trajectories (`Case #312` at `13.4s`) strictly constant across all four arms eliminates worker-quality heterogeneity and peer spillover, satisfying SUTVA (Imbens & Rubin, 2015).
- **Addressing the "no human victim" externality critique:** In Phase 1, a scripted worker suffers no personal pecuniary loss when Option 1 is selected, so Stage II specifically measures willingness to invoke a nominal `"HUMAN-VERIFIED"` audit trail for personal gain (`€4.00`) under competing governance levers. To test whether real third-party financial harm attenuates scapegoating, **planned Phase 2** introduces a **paired-worker bonus-pool externality check** (Fehr & Schmidt, 1999) where Option 1 deducts directly from a matched human participant's bonus pool.

---

### Q2. Why standardize every case on an enterprise GPU returns desk instead of healthcare, hiring, or policing?

Clinical, judicial, and policing vignettes carry strong, heterogeneous moral and political priors that confound structural quota effects with domain-specific attitudes.

Standardizing every return dossier onto a single recognizable B2B hardware product (**NVIDIA RTX 6000 Ada Enterprise GPU**, €3,600–€5,200 escrow value; `4.92 kg` certified factory outbound weight) serves two deliberate purposes:
1. **Emotional neutrality:** Minimizes domain-specific affective priors so the online RCT acts as a controlled **mechanism-isolation step** preceding domain-specific field deployments.
2. **Physical ground truth with zero switching cost:** Eliminating multi-product clutter makes the empty-box scam on Page 3 (`0.24 kg` crushed kraft paper = **`-4.68 kg` / `-95.1%` weight deficit**) immediately self-evident to every participant.

---

### Q3. If a manager chooses `38.0s` or `60.0s` on Screen 2A, why does the floor still run at `25.0s` — and why include `38.0s`?

- **Why the Corporate Q4 Backlog Override exists:** If cautious managers literally ran Shifts 1–3 at `60.0s` (`15 cases/shift`), their pre-crash score would reach only `450 pts` (vs. `990 / 950 pts`), breaking both the `1,200 pt` bonus hurdle and Sara's Shift 2/3 storyline. Instead, Screen 2A permanently logs the participant's unconfounded ex-ante preference (`initialSlaPreferenceSec` and `initialSlaArchetype`) as a pre-incident behavioral variable, then displays a transparent Corporate Operations Dispatch locking Shift 1–3 floor pacing to the inherited `25.0s` Corporate Baseline (`36 cases / +360 pts`) while preserving managerial authority over Shift 2 exceptions and Shift 4 permanent reform.
- **Why `38.0s` is scientifically indispensable despite forfeiting the bonus:** Both `38.0s` (`24 cases/shift`) and `60.0s` (`15 cases/shift`) fall below the `30 cases/shift` bonus hurdle, yet `38.0s` separates three distinct managerial archetypes:
  1. **Bonus Maximizer (`25.0s`):** Maximizes velocity and personal €4.00 bonus eligibility.
  2. **Organizational Steward (`38.0s`):** Voluntarily sacrifices personal bonus to protect workers from `25.0s` panic while sustaining healthy commercial throughput (`24 cases/shift`).
  3. **Compliance Purist (`60.0s`):** Prioritizes full ergonomic verification headroom (`≥ 48.5s`) above unit volume.

---

### Q4. If a manager pays `-40 pts` for `Directive B` in Shift 2, why does Sara still crash in Shift 3? Isn't that insubordination?

No—two design invariants explicitly resolve the Shift 2 `Directive B` vs. Shift 3 crash paradox:
1. **Explicit temporary-exception reset (systemic clock lock-in, not insubordination):** `Directive B` authorizes a *temporary* Shift 2 manual-verification exception (`32 cases / +320 pts`, `-40 pt` throughput variance). Upon Shift 2 completion, the corporate workflow engine transparently notifies the manager that Shift 3 reverts to the inherited `25.0s` Corporate Baseline until post-incident Board policy reform. Sara's `13.4s` Shift 3 approval under a false green AI badge therefore reflects structural clock lock-in rather than defying an active slow-down order.
2. **Mathematical Zero-Penalty-Trap & 220-Point Separation Proofs:** Across all **32 deterministic truth-table paths** (`4 Arms × 2 Shift-2 Directives × 2 Stage-II Choices × 2 Shift-4 SLAs`, verified in [`DESIGN_SPEC.md §5`](DESIGN_SPEC.md) and `tools/test_mvp2.py`), a conscientious `Directive B` manager who later selects Option 1 still clears **`1,210–1,250 pts` (`≥ 1,200 pt` hurdle → `€6.50`)**, whereas Option 2 yields **`910–950 pts` (`< 1,200 pt` → `€2.50`)**. Every Arm 1–3 path preserves a clean **`220-point` minimum separation margin** (`1,210` vs. `990`), ensuring Shift 2 conscientiousness never traps a manager out of the Stage II bonus fork.

---

## B. Ergonomics, Blinding & Treatment Mechanics

### Q5. Why calibrate the quota at `25.0s` instead of `15.0s` against the `48.5s` REFA floor?

Each 3-tab return dossier contains ~640 words, 2 numerical records, and 2 mandatory tab transitions. Under standard REFA industrial work-study budgeting:

$$T_{\text{REFA}} = 41.0\text{ s (reading \& processing)} + 7.5\text{ s (cognitive cross-referencing \& tab-handling allowance)} = 48.5\text{ s}$$

- **Why `25.0s` (not `15.0s`):** A `15.0s` clock (~900 WPM) feels obviously rigged before a participant even finishes Page 1. By contrast, **`25.0s`** ($\Delta T_{\text{erg}} = -23.5\text{s}$; ~770 WPM required for full 3-tab inspection) allows a typical operator to read Page 1 (~12s) and Page 2 (~9s), leaving ~4s right as they reach Page 3—authentically triggering the real-world dilemma between relying on the green AI Copilot badge (`Passed 3/3 docs`) or incurring an SLA timeout.
- **Zero hardcoded magic numbers:** Every timer, case volume, weight, and EUR stake is externalized in [`experiment_config.json`](experiment_config.json) (editable via [`admin.html`](admin.html)) so pilot recalibration requires no source edits.

---

### Q6. Why are there no onboarding comprehension quizzes or checkboxes — and why withhold Stage II in Step 5?

- **Passive behavioral telemetry instead of artificial quizzes:** Multiple-choice comprehension gates and mandatory "I read Tab 1–3" checkboxes were intentionally omitted because they introduce artificial lab-exam cues and distort natural reading flow. Instead, the testbed passively records per-step onboarding dwell (`dwell_step1_ms`–`dwell_step6_ms`) and per-tab inspection dwell (`≥ 500ms`) in the background—generating objective engagement diagnostics (including `"Pages Inspected: X/3"` on Arm 3's Floor KPI Scorecard) without lecturing participants.
- **No-deception anti-spoiler onboarding (Step 5):** Step 5 truthfully discloses the complete incentive contract (`+10 pts/case`, `1,200 pt` hurdle for **€4.00 bonus** on **€2.50 base**, and `-300 pt` fraud audit hold) while **deliberately not previewing the Screen 4 blame-deflection fork**. Advertising beforehand that blaming a subordinate restores `+300 pts` would tip off participants that the study is an "ethics test" and contaminate Shifts 1–3 with demand bias.

---

### Q7. Why does Arm 4 display the same Stage II fork, hide the `+€1.00` credit, and defer `Arm 4a/4b` to Phase 2?

- **Anti-leakage display during evaluation:** On Screen 4, live score projections use the **exact same formula across all four arms** (`1,250/1,210 pts` on Option 1 vs. `950/910 pts` on Option 2), and Arm 4's ex-post Screen 5 audit settlement (`-50 pt` retaliation fine + bonus revocation → `€2.50` on Option 1; surprise `+100 pt / +€1.00` Integrity Credit → `€3.50` on Option 2) is **strictly concealed** until after submission. Choosing Option 2 in Arm 4 therefore cannot be driven by seeing a guaranteed `+€1.00` reward on Screen 4.
- **Verified statutory scope & incremental legal contrast:** Screen 3 Box D in Arm 4 displays **Regulation (EU) 2024/1689 (EU AI Act) Arts. 14(4), 26(2), and 99(4)(e)**—flagging that enforcing a `-23.5s` deficit renders ceremonial `"HUMAN-VERIFIED"` stamps non-compliant as regulatory oversight. Because Arm 4 also surfaces the `-23.5s` ergonomic deficit, the active-arm contrast **`Arm 4 vs. Arm 2`** cleanly isolates the incremental expressive legal effect over pure ergonomic telemetry. European civil-law organizational fault (*Organisationsverschulden*) informs broader doctrinal framing in the research proposal, but is not rendered inside Box D.
- **Decoupling expressive law vs. pecuniary deterrence (`planned Phase 2`):** Because citing Art. 99(4)(e) and audit scrutiny in Box D could still create perceived financial risk alongside normative salience, **planned Phase 2** explicitly splits Arm 4 into **`Arm 4a` (Expressive Notice Only, $\mathbb{E}[\text{fine}] = 0$)** vs. **`Arm 4b` (Ex-Ante Disclosed Pecuniary Clawback & Integrity Credit)**.

---

## C. Measurement, Identification & Statistical Power

### Q8. Why three independent `0–10` sliders instead of a 100%-sum slider — and doesn't Stage I distort Stage II?

- **Eliminating the Ipsative Collinearity Trap:** Forcing participants to split 100% across *Operator*, *AI*, and *SLA* induces mechanical negative correlations and a singular ($\text{rank}=2$) cross-equation covariance matrix. Eliciting **three independent `0.0–10.0` sliders** (uniformly styled to avoid color demand cues) allows joint multivariate Wald tests of **Blame Reallocation** ($\delta_{k,\text{Sara}} < 0 \land \delta_{k,\text{SLA}} > 0$ via stacked OLS with unrestricted $\widehat{\boldsymbol{\Sigma}}_\varepsilon$; Wooldridge, 2010), while still computing the derived operator share $S_{\text{Sara},i} = R_{\text{Sara},i} / \sum_m R_{m,i}$ (`33.33%` fallback if all zero) for **Papke & Wooldridge (1996) Fractional Logit**.
- **Order, construct scope & CR3 equivalence:** Eliciting unincentivized Stage I attributions before Stage II's €4.00 choice creates psychological consistency pressure (Falk & Zimmermann, 2013) that pulls Stage II *toward* Stage I. In the stacked binary-to-binary `MoneyTask` model (`I(RootCause = H-1)` vs. `Y_disc`, **subject-clustered CR3** leave-one-cluster-out jackknife SEs; MacKinnon, Nielsen, & Webb, 2023), $\hat{\delta}$ captures the baseline attribution-to-sanction shift under monetary stakes (lower-bounded by consistency, while still reflecting any baseline construct gap between 3-way causal attribution and binary firing), whereas the randomized between-arm interactions $\hat{\gamma}_k$ cancel arm-invariant construct differences and are algebraically identical to a 1-row-per-manager first-difference ($\Delta Y_i = Y_{i,2} - Y_{i,1}$) or subject fixed-effects ($\alpha_i$) specification.

---

### Q9. How do you handle Arm 3's pre-shift rotation (bad controls, time-on-task, and attrition)?

- **Tripartite Protocol for Shift 2 Directive ($W_{\text{S2}}$):** Because only Arm 3 completes Screen 1B before Shift 1, $W_{\text{S2},i}$ is **post-treatment in Arm 3** ($D_3 \to W_{\text{S2},i}$) but **pre-treatment across Arms $\{1, 2, 4\}$**. Conditioning on $W_{\text{S2},i}$ in 4-arm ATE regressions would introduce overcontrol and collider bias (Pearl, 2009). Accordingly ([`ANALYSIS_PLAN.md §1.3`](ANALYSIS_PLAN.md)): (i) $W_{\text{S2},i}$ is **omitted** from all 4-arm ATE models; (ii) analyzed as a **pooled first-stage outcome** comparing Arm 3 ($n=60$) vs. $\{1, 2, 4\}$ ($n=180$, $\text{MDE} = 20.9\text{ pp}$ at $R^2=0$); and (iii) used as a balance check and demeaned **Lin (2013)** covariate strictly within $\{1, 2, 4\}$.
- **Differential attrition, ITT estimand & balance checks:** Because Arm 3 adds ~90 seconds of pre-shift operator trials, selective onboarding dropout satisfies one-sided monotonicity and is bounded via **Lee (2009) trimming bounds** (verified in `analysis/power_simulation.py`), paired with stage-level dropout beacons (`pagehide`/`beforeunload`) and Screen 4 response-latency diagnostics for fatigue. All primary 4-arm regressions estimate unbiased **intention-to-treat (ITT)** effects without subsetting on post-treatment diagnostic dwell/attention, and pre-treatment covariate balance pairs standardized normalized differences ($< 0.10\text{ SD}$) with joint $F$-tests.

---

### Q10. Why are sample sizes ($N = 80\text{–}240$) parameterized rather than fixed upfront?

Because true baseline sanctioning ($p_1$), attribution variance ($\sigma$), and covariate explanatory power ($R_{\mathbf{X}}^2$) are unobserved prior to human piloting, locking a single sample size beforehand risks over-sampling if pilot directional separation is large or under-powering active-arm comparisons if baseline rates sit near maximum variance ($p_1 = 0.50$).

Instead, an initial calibration pilot ($n = 8\text{–}10/\text{arm}$, $N_{\text{pilot}} = 32\text{–}40$) verifies task parameters via **blinded Control-arm calibration**—estimating $(\hat{p}_1, \hat{\sigma}, \hat{R}_{\mathbf{X}}^2)$ without inspecting treatment contrasts, which preserves exact Type I error ($\alpha = 0.05$ two-tailed, $1 - \beta = 0.80$) with zero interim $\alpha$-spending. If participants lean strongly toward sanctioning under the €4.00 bonus hold ($p_1 \ge 0.75\text{–}0.80$), Bernoulli variance $p_1(1-p_1)$ shrinks and treatment separation $\Delta p$ widens, so smaller cohorts reach $80\%$ power than under a noisy $p_1 = 0.50$ split (verified deterministically in [`analysis/power_simulation.py`](analysis/power_simulation.py)):
- **Benchmark Cohort 1 ($N_1 = 80\text{–}120$, $n = 20\text{–}30/\text{arm}$, Directional-Skew Regime):** Powers primary treatment vs. Control ATEs at **`0.66–0.80 SD`** adjusted (**`0.72–0.89 SD`** unadj.), binary sanctioning **`-29.7 to -36.2 pp`** adjusted (**`-32.7 to -39.7 pp`** unadj.), pooled Shift 2 `Arm 3 vs. {1,2,4}` (**`29.5–36.2 pp`** at $R^2=0$), and within-subject incentive distortion ($\delta$, $2N_1 = 160\text{–}240$).
- **Benchmark Cohort 2 ($N_2 = 240$, $n = 60/\text{arm}$, Conservative $p_1=0.50$ Bound):** Under worst-case $p_1 = 0.50$ variance, powers primary and active-arm contrasts (`Arm 3` vs. `Arm 2`; `Arm 4` vs. `Arm 2`) at **`0.46 SD`** adjusted (**`0.51 SD`** unadj.), **`-22.0 pp`** adjusted (**`-24.1 pp`** unadj.), pooled Shift 2 (**`20.9 pp`** at $R^2=0$), and the **planned Phase 2** `Arm 4a` vs. `4b` split. Because pre-treatment survey traits on binary choices often yield $R_{\mathbf{X}}^2 \approx 0.03\text{–}0.08$, Cohort 2 ($N_2 = 240$) serves as the conservative planning bound for active-arm contrasts under Romano–Wolf FWER control.

To preserve confirmatory parsimony, the proposal focuses on the two primary models (Model 1 binary sanctioning; Model 2 stacked incentive distortion), while [`ANALYSIS_PLAN.md`](ANALYSIS_PLAN.md) pre-registers the full robustness suite (exact Fisher randomization inference with 10,000 permutations, Romano–Wolf stepdown FWER control, pre-treatment placebo checks, and strictly exploratory Imai–Yamamoto sequential mediation with $\tilde{\rho}$ sensitivity bounds).

---

## D. Visual Ergonomics, Engineering & Reproducibility

### Q11. Is eye-tracking hardware required — and why enforce positive polarity and `24px` gutters?

- **No eye-tracking hardware required:** The core four-arm RCT runs completely online in any standard desktop browser, exporting per-panel clickstream and dwell metrics in a **52-column tidy CSV** and structured JSON.
- **Why positive-polarity light-slate styling (`#0F172A` on `#F1F5F9` / `#FFFFFF`) and `24px` gutters:** Even for online participants, avoiding dark-mode flashes eliminates astigmatism halation and **Pupillary Light Reflex (PLR)** luminance shocks (`1.5–3.0 mm` artifacts that would otherwise swamp `0.1–0.5 mm` cognitive-load dilation). Enforcing **`24px` macro-gutters** plus **`20px` card padding** provides `44px` minimum separation (`> 41px ≈ 1.07°` visual angle at `650 mm` viewing distance on a 24" `1920×1080` display) across **33 viewport-relative `data-aoi` attributes** (exported via `window.getScreenAOIMap()`). This makes the canvas immediately compatible with optional future eye-tracking collaboration to distinguish **attentional neglect** (never inspecting the ergonomic deficit) from **willful scapegoating** (reading `-23.5s` and still penalizing Sara for €4.00).

---

### Q12. How are timing drift, parameter versioning, bot traffic, and pre-launch refinements handled?

- **Static client-side architecture & drift-free clocks:** Pure HTML5/CSS/ES6 with zero backend attack surface. All countdowns use `performance.now()` wall-clock deltas (`remaining = Math.max(0, durationSec - elapsedWallSec * speedMultiplier)`), ensuring `25.0s` at `1x` equals exactly `25.00s` (and `8.33s` at researcher `3x` speed) without `setInterval` drift.
- **Immutable `config_snapshot` audit trail:** Every session embeds a deep copy of its active `experiment_config.json` parameters inside `session.config_snapshot` and exports them as explicit columns in the **52-column tidy CSV**—guaranteeing pilot parameter adjustments never corrupt multi-wave econometric datasets.
- **Frictionless reviewer access & double-blind scrubbing:** The public prototype opens directly without a password modal so faculty reviewers can inspect any arm immediately (`?arm=3`), while preregistered cohorts enter via single-use Base64 URL tokens (`?token=...`). Unless `?admin=1` is passed, researcher controls are stripped from the DOM and `window.history.replaceState` scrubs arm and token parameters from the address bar.
- **Transparently logged pre-launch polish ([`DESIGN_SPEC.md §6`](DESIGN_SPEC.md)):** Two refinements are documented for execution prior to preregistered human recruitment: (1) suppressing `#s2aEuBanner` on Screen 2A in Arm 4 so Arms `{1, 2, 4}` are 100% identical through Shift 2, and (2) step-locking Stage I on Screen 4 behind a confirmation gate before revealing the Stage II €4.00 fork so participants cannot back-solve unincentivized attributions.
