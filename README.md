# Manager-in-the-Loop Accountability RCT — Testbed & Analysis Hub

> Independent Experimental Prototype, Design Specification, and Reproducible Pre-Analysis Pipeline (Danial Bahrambeygi, 2026)

This repository serves as the unified public hub for a browser-based, four-arm randomized controlled testbed and econometric pre-analysis pipeline. The study tests whether ergonomic diagnostics, embodied task rotation, or statutory oversight disclosures alter managerial causal attribution and downstream disciplinary sanctioning when human-in-the-loop (HITL) review operates under binding algorithmic throughput pressure.

---

## Quick Navigation

1. **Interactive Testbed**
   - **Live 1x Walkthrough (Arm 3):** [https://dan-iall.github.io/accountability-sink-demo/?arm=3](https://dan-iall.github.io/accountability-sink-demo/?arm=3) *(opens directly; includes a `3x` speed toggle in the top bar)*
   - **60-Second 4-Arm Journey Explorer:** [https://dan-iall.github.io/accountability-sink-demo/EXPERIMENT_JOURNEY_EXPLORER.html](https://dan-iall.github.io/accountability-sink-demo/EXPERIMENT_JOURNEY_EXPLORER.html)
   - **Experimenter Control Room:** [https://dan-iall.github.io/accountability-sink-demo/admin.html](https://dan-iall.github.io/accountability-sink-demo/admin.html)

2. **Technical & Econometric Documentation**
   - [**`DESIGN_SPEC.md`**](DESIGN_SPEC.md) — Complete 5-screen participant flow, point-ledger arithmetic, REFA `48.5s` vs. `25.0s` SLA timing parameters, and 4-arm randomization specification.
   - [**`ANALYSIS_PLAN.md`**](ANALYSIS_PLAN.md) — Primary identification equations, secondary econometric estimators, and robustness suite (Lee attrition bounds, exact Fisher randomization inference, Romano–Wolf FWER correction).
   - [**`FAQ.md`**](FAQ.md) — 12-question reviewer & faculty methodological FAQ covering experimental validity, ergonomics, identification, and deployment.

3. **Reproducible Power Simulation**
   - [**`analysis/power_simulation.py`**](analysis/power_simulation.py) — Deterministic synthetic cohort generator and pilot-calibrated MDE benchmarks for $N_1 = 80\text{–}120$ ($n = 20\text{–}30/\text{arm}$, directional-skew regime) and $N_2 = 240$ ($n = 60/\text{arm}$, conservative $p_1 = 0.50$ bound).

---

## 1. Experimental Paradigm & 4-Arm Design

Participants assume the role of an Operations Manager supervising three standardized, scripted subordinate agents assisted by an AI Copilot under a binding **25.0s SLA pacing quota**, compared against an empirically calibrated **48.5s REFA industrial work-study reading floor** ($\Delta T_{\text{erg}} = -23.5\text{s}$). Following a Shift 3 fraud clearance incident, managers allocate causal responsibility across the frontline operator, the AI Copilot, and the SLA constraint, then make an incentive-compatible disciplinary sanction decision affecting their bonus payout.

The current testbed implements four randomized experimental arms:

- **Arm 1 (Control — Status Quo):** Standard administrative audit log displaying the carrier manifest, wire hash, and operator sign-off (`Verified by: Specialist Sara`).
- **Arm 2 (`D2_stamp` — STAMP Cognitive Ergonomics Diagnostic):** Surfaces the formal work-study benchmark table ($T_{\text{REFA}} = 48.5\text{s}$ vs. $T_{\text{SLA}} = 25.0\text{s}$, $\Delta T_{\text{erg}} = -23.5\text{s}$) during post-incident evaluation (Leveson, 2011).
- **Arm 3 (`D3_embodied` — Embodied Rotation Experience):** Places the manager on the operational floor for two onboarding practice cases prior to Shift 1 and recalls their personal untimed inspection baseline (`46.8s` fallback vs. `25.0s` SLA) alongside deployer working-condition duties during the Shift 3 audit.
- **Arm 4 (`D4_eu_ai_act` — Statutory Regulatory Shield):** Displays EU AI Act Arts. 14(4), 26(2), and 99(4)(e) in the post-incident audit box, indicating that enforcing a $-23.5\text{s}$ ergonomic deficit invalidates ceremonial `"HUMAN-VERIFIED"` stamps and returns liability to management. Decoupling expressive legal norms from pecuniary audit clawbacks (`Arm 4a/4b`) and pairing managers with live worker pools are reserved for **planned Phase 2**.

All primary UI regions carry **33 viewport-relative Areas of Interest (`data-aoi`)** for structured clickstream export (52-column CSV and JSON) and modular compatibility with optional future eye-tracking studies.

---

## 2. Repository Map

```text
.
├── README.md                           # Unified public hub & quick navigation
├── DESIGN_SPEC.md                      # 5-screen flow, point-ledger math, REFA/SLA & 4-arm spec
├── ANALYSIS_PLAN.md                    # Identification strategy, estimators & robustness suite
├── FAQ.md                              # 12-question reviewer & faculty methodological FAQ
├── index.html                          # 4-arm participant testbed & telemetry exporter
├── EXPERIMENT_JOURNEY_EXPLORER.html    # 60-second interactive 4-arm journey & payoff explorer
├── admin.html                          # Experimenter control room & Base64 config builder
├── experiment_config.json              # Canonical experiment parameter configuration
├── css/enterprise_slate.css            # Enterprise light-slate UI & typography styles
├── analysis/
│   ├── power_simulation.py             # Synthetic DGP, primary/robustness estimators & MDEs
│   └── synthetic_cohort_N240.csv       # Deterministic N=240 (n=60/arm) synthetic cohort
├── tools/                              # Structural DOM/AOI, payoff-table & behavioral tests
└── requirements.txt                    # Python verification dependencies
```

---

## 3. Local Run & Verification

Install the Python dependencies listed in `requirements.txt` (`numpy`, `pandas`, `statsmodels`, `scipy`, `beautifulsoup4`), then run the simulation and test suites from the repository root using `./env/bin/python` (or `python3` in your local virtual environment):

```bash
# 1. Run synthetic cohort generation, estimators, and conservative p1=0.50 MDE calibration
./env/bin/python analysis/power_simulation.py
# (or: python3 analysis/power_simulation.py)

# 2. Verify DOM IDs, 33 viewport-relative AOI attributes, and JavaScript event handlers
./env/bin/python tools/verify_index.py

# 3. Run structural, payoff truth-table, and telemetry schema checks
./env/bin/python tools/test_mvp2.py

# 4. Optional: serve the interactive testbed locally
python3 -m http.server 8000
# Open http://localhost:8000/?arm=3
```

Additional behavioral, remediation, adversarial workflow, and journey-explorer tests are available in `tools/` (`test_mvp2_behavioral.py`, `test_remediation_challenge.py`, `test_adversarial_workflows.py`, `test_journey_explorer.py`).
