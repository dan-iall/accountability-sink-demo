# The Manager-Seat Accountability Sink — 4-Arm RCT Testbed & Simulation Pipeline

> Independent Experimental Prototype & Reproducible Econometric Pre-Analysis Code (Danial Bahrambeygi, 2026)

---

## 1. Overview & Experimental Paradigm

This repository contains an interactive browser-based behavioral economics testbed and accompanying econometric simulation pipeline studying **human-in-the-loop (HITL) accountability attribution and downstream blame shifting** under binding algorithmic throughput pressure.

Participants take the role of an Operations Manager overseeing three standardized, scripted subordinate agents assisted by an AI Copilot under a binding **25.0s SLA pacing quota**, compared against an empirically calibrated **48.5s REFA / ISO 9241-110 reading floor** ($\Delta T_{\text{erg}} = -23.5\text{s}$). Following a Shift 3 fraud clearance incident, participants allocate causal responsibility across the frontline operator, the AI Copilot, and the SLA constraint, then make an incentive-compatible disciplinary sanction decision.

The testbed implements a **4-arm randomized controlled design**:
- **Arm 1 (Control — Status Quo):** Standard administrative audit log displaying carrier manifest, wire hash, and operator sign-off (`Verified by: Specialist Sara`).
- **Arm 2 (`D2_stamp` — STAMP Cognitive Ergonomics Diagnostic):** Surfaces the formal work-study benchmark table ($T_{\text{REFA}} = 48.5\text{s}$ vs. $T_{\text{SLA}} = 25.0\text{s}$, $\Delta T_{\text{erg}} = -23.5\text{s}$) during post-incident evaluation (Leveson, 2011).
- **Arm 3 (`D3_embodied` — Embodied Rotation Experience):** Places the manager on the floor for two onboarding practice cases before Shift 1 and recalls their personal untimed inspection baseline (`46.8s` vs. `25.0s` SLA) alongside deployer working-condition duties during the Shift 3 audit.
- **Arm 4 (`D4_eu_ai_act` — Statutory Regulatory Shield):** Surfaces EU AI Act Arts. 14(4)(b), 26(2), and 99(4)(e) alongside § 254 BGB (*Organisationsverschulden*), flagging that a $-23.5\text{s}$ ergonomic deficit invalidates ceremonial `"HUMAN-VERIFIED"` stamps and triggers regulatory audit clawbacks.

All core UI regions are tagged with **33 viewport-relative Areas of Interest (`data-aoi`)** to support synchronized gaze/pupillometry and clickstream telemetry export (52-column CSV and structured JSON).

---

## 2. Live Interactive Links

- **1x Default Walkthrough (Arm 3):** [https://dan-iall.github.io/accountability-sink-demo/?access=demo2026&arm=3](https://dan-iall.github.io/accountability-sink-demo/?access=demo2026&arm=3)
- **4-Arm Journey Explorer:** [https://dan-iall.github.io/accountability-sink-demo/EXPERIMENT_JOURNEY_EXPLORER.html](https://dan-iall.github.io/accountability-sink-demo/EXPERIMENT_JOURNEY_EXPLORER.html)
- **Experimenter Control Room:** [https://dan-iall.github.io/accountability-sink-demo/admin.html?access=demo2026](https://dan-iall.github.io/accountability-sink-demo/admin.html?access=demo2026)

---

## 3. Repository Structure

```text
.
├── index.html                          # 4-arm participant simulator & telemetry exporter
├── EXPERIMENT_JOURNEY_EXPLORER.html    # Interactive 4-arm journey & payoff explorer
├── admin.html                          # Experimenter control room & Base64 config builder
├── tum_experiment_config.json          # Canonical 37-parameter experiment specification
├── css/enterprise_slate.css            # Enterprise light-slate UI & typography tokens
├── analysis/
│   ├── power_simulation.py             # 52-col DGP, LPM/Logit/FracLogit/Lee bounds & MDEs
│   └── synthetic_cohort_N240.csv       # Deterministic N=240 (n=60/arm) synthetic dataset
├── tools/                              # Structural DOM/AOI, math & E2E verification suites
├── requirements.txt                    # Python verification dependencies
└── README.md
```

---

## 4. Reproducing the Econometric Simulation & Verification Suites

Install Python dependencies (`numpy`, `pandas`, `statsmodels`, `scipy`, `beautifulsoup4`) and run from the repository root:

```bash
# Generate synthetic_cohort_N240.csv and run Models 1–4 (LPM, Logit AME, Fractional Logit, Lee Bounds, MDEs)
python analysis/power_simulation.py

# Verify 165 DOM IDs, 33 AOI attributes, and 48 JavaScript handlers
python tools/verify_index.py

# Run full structural, 32-condition payoff truth table, and telemetry schema checks
python tools/test_mvp2.py
```

Additional behavioral, remediation, adversarial workflow, and explorer checks are located in `tools/` (`test_mvp2_behavioral.py`, `test_remediation_challenge.py`, `test_adversarial_workflows.py`, `test_journey_explorer.py`).
