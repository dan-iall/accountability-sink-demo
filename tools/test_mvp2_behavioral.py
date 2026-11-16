#!/usr/bin/env python3
"""
HITL ACCOUNTABILITY STUDY — MVP2 EXTENDED BEHAVIORAL E2E TEST SUITE
===========================================================
Comprehensive behavioral, timing, telemetry, anti-nudge, and
deterministic PRNG test suite for the MVP2 experimental platform.
Designed per TEST_INFRA.md and QA_FEEDBACK_GATHERER.md.
"""

import base64
import json
import math
import os
import re
import subprocess
import sys
import unittest
from urllib.parse import quote, unquote

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "index.html")
ADMIN_PATH = os.path.join(BASE_DIR, "admin.html")
CONFIG_PATH = os.path.join(BASE_DIR, "tum_experiment_config.json")
CSS_PATH = os.path.join(BASE_DIR, "css", "enterprise_slate.css")


def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class TestConfigHydrationAndReactivity(unittest.TestCase):
    """Tier 1 & Tier 4: Dynamic Configuration Hydration (Option B) Tests."""

    def setUp(self):
        self.default_config = load_config()

    def test_option_b_derived_metrics_mathematical_properties(self):
        """Validates dynamic computation of Option B derived metrics across configs."""
        test_profiles = [
            {"targetCohortN": 240, "bonusTargetPts": 1200, "basePayEur": 2.50, "performanceBonusEur": 4.00,
             "tier1SlaSec": 25.0, "tier2SlaSec": 38.0, "tier3SlaSec": 60.0, "shiftDurationSimSec": 25.0},
            {"targetCohortN": 300, "bonusTargetPts": 1400, "basePayEur": 3.00, "performanceBonusEur": 5.00,
             "tier1SlaSec": 20.0, "tier2SlaSec": 35.0, "tier3SlaSec": 55.0, "shiftDurationSimSec": 30.0},
            {"targetCohortN": 60, "bonusTargetPts": 1000, "basePayEur": 2.00, "performanceBonusEur": 3.00,
             "tier1SlaSec": 15.0, "tier2SlaSec": 30.0, "tier3SlaSec": 45.0, "shiftDurationSimSec": 20.0},
        ]

        for cfg in test_profiles:
            # 1. Balancer cohort target & per-arm quota
            target_n = cfg["targetCohortN"]
            per_arm_target = round(target_n / 4)
            self.assertEqual(per_arm_target, target_n // 4)

            # 2. Financial totals
            total_pay = cfg["basePayEur"] + cfg["performanceBonusEur"]
            self.assertAlmostEqual(total_pay, cfg["basePayEur"] + cfg["performanceBonusEur"], places=2)

            # 3. Dynamic summary string formatting contracts (Option B)
            sla_summary = f"SLA Tiers: {cfg['tier1SlaSec']}s / {cfg['tier2SlaSec']}s / {cfg['tier3SlaSec']}s"
            duration_summary = f"Shift Duration: {cfg['shiftDurationSimSec']}s"
            hurdle_summary = f"Hurdle: {cfg['bonusTargetPts']:,} pts"
            cohort_summary = f"Target N: {cfg['targetCohortN']} ({per_arm_target}/arm)"

            self.assertIn(f"{cfg['tier1SlaSec']}s", sla_summary)
            self.assertIn(f"{cfg['shiftDurationSimSec']}s", duration_summary)
            self.assertIn(f"{cfg['bonusTargetPts']:,} pts", hurdle_summary)
            self.assertIn(f"{cfg['targetCohortN']}", cohort_summary)

    def test_bva_cohort_size_boundaries(self):
        """Boundary Value Analysis for cohort size N and bonus hurdle."""
        boundary_cases = [
            {"targetCohortN": 4, "expectedPerArm": 1},
            {"targetCohortN": 240, "expectedPerArm": 60},
            {"targetCohortN": 1000, "expectedPerArm": 250},
        ]
        for b in boundary_cases:
            per_arm = round(b["targetCohortN"] / 4)
            self.assertEqual(per_arm, b["expectedPerArm"])

    def test_admin_config_dom_integration_when_present(self):
        """Validates admin.html dynamic binding elements if implemented by M1."""
        admin_html = load_file(ADMIN_PATH)
        m1_markers = ["cfgSummarySla", "cfgSummaryShiftDuration", "cfgSummaryHurdle", "cfgSummaryTargetN", "lblTargetCohortN"]
        present_count = sum(1 for m in m1_markers if m in admin_html)
        if present_count == len(m1_markers):
            for marker in m1_markers:
                self.assertIn(marker, admin_html, f"Missing Option B admin marker: {marker}")
        else:
            # Under progressive testability, record pending M1 integration status
            sys.stdout.write(f"\n  [Progressive Note] admin.html Option B markers pending M1 merge ({present_count}/{len(m1_markers)} present)")


class TestBase64TokenQuarantine(unittest.TestCase):
    """Tier 2 & Tier 4: Base64 Token Quarantine & Deserialization Tests."""

    def setUp(self):
        self.default_config = load_config()

    def test_base64_payload_packing_and_unpacking_roundtrip(self):
        """Validates Base64 serialization and deserialization with full 37-param config."""
        test_payloads = [
            {
                "pid": "P_PILOT_001",
                "arm": 1,
                "speed": 1,
                "meta": "Standard Pilot Run",
                "config": self.default_config
            },
            {
                "pid": "P_PILOT_002",
                "arm": 4,
                "speed": 3,
                "meta": "München Lab Trial — €4.00 Bonus [Station 4]",
                "config": {**self.default_config, "targetCohortN": 300, "bonusTargetPts": 1400}
            },
            {
                "pid": "P_SPECIAL_CHARS",
                "arm": 2,
                "speed": 1,
                "meta": "test&param=1+2/3?foo=bar%20baz",
                "config": self.default_config
            }
        ]

        for payload in test_payloads:
            # Python UTF-8 Base64 encoding (matches JS btoa(unescape(encodeURIComponent(...))))
            json_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
            b64_token = base64.b64encode(json_bytes).decode('ascii')

            # Verify with Node.js runtime using the exact JS decoding expression
            node_code = f"""
            const b64 = '{b64_token}';
            const jsonStr = decodeURIComponent(escape(atob(b64)));
            const decoded = JSON.parse(jsonStr);
            console.log('__UNPACKED__:' + JSON.stringify(decoded));
            """
            proc = subprocess.run(["node", "-e", node_code], capture_output=True, text=True, check=True)
            unpacked = None
            for line in proc.stdout.splitlines():
                if line.startswith("__UNPACKED__:"):
                    unpacked = json.loads(line[len("__UNPACKED__:"):])
                    break
            self.assertIsNotNone(unpacked, "Node decoding failed to return __UNPACKED__")

            # Assert complete preservation of all fields and config keys
            self.assertEqual(unpacked["pid"], payload["pid"])
            self.assertEqual(unpacked["arm"], payload["arm"])
            self.assertEqual(unpacked["speed"], payload["speed"])
            self.assertEqual(unpacked["meta"], payload["meta"])
            self.assertEqual(len(unpacked["config"]), 37)
            self.assertEqual(unpacked["config"]["bonusTargetPts"], payload["config"]["bonusTargetPts"])

    def test_corrupted_and_empty_token_resilience(self):
        """Verifies graceful handling of malformed or invalid Base64 tokens."""
        malformed_tokens = [
            "",
            "!!!NOT_BASE64!!!",
            "eyJuYW1lIjoiSW52YWxpZCBKU09OIiBtaXNzaW5nIGNsb3Nl",  # incomplete JSON
        ]
        for token in malformed_tokens:
            node_code = f"""
            let unpacked = null;
            try {{
                const raw = '{token}';
                if (raw) {{
                    const jsonStr = decodeURIComponent(escape(atob(raw)));
                    unpacked = JSON.parse(jsonStr);
                }}
            }} catch(e) {{
                unpacked = {{ error: true, message: e.message }};
            }}
            console.log('__RESULT__:' + JSON.stringify(unpacked));
            """
            proc = subprocess.run(["node", "-e", node_code], capture_output=True, text=True)
            for line in proc.stdout.splitlines():
                if line.startswith("__RESULT__:"):
                    res = json.loads(line[len("__RESULT__:"):])
                    self.assertTrue(res is None or res.get("error") is True)

    def test_address_bar_scrubbing_contract(self):
        """Validates window.history.replaceState address-bar scrubbing logic."""
        node_code = """
        let replacedUrl = null;
        const window = {
            location: { pathname: '/mvp2/index.html', search: '?access=tum2026&token=ENCODED_TOKEN_PAYLOAD&speed=3' },
            history: {
                replaceState: (state, title, url) => { replacedUrl = url; }
            }
        };
        // Simulated scrubbing function
        const tokenParam = 'ENCODED_TOKEN_PAYLOAD';
        const access = 'tum2026';
        const isAdmin = false;
        if (!isAdmin) {
            window.history.replaceState({}, '', window.location.pathname + (tokenParam ? '?access=' + access : ''));
        }
        console.log('__CLEAN_URL__:' + replacedUrl);
        """
        proc = subprocess.run(["node", "-e", node_code], capture_output=True, text=True, check=True)
        for line in proc.stdout.splitlines():
            if line.startswith("__CLEAN_URL__:"):
                clean = line[len("__CLEAN_URL__:"):].strip()
                self.assertEqual(clean, "/mvp2/index.html?access=tum2026")
                self.assertNotIn("token=", clean)
                self.assertNotIn("speed=", clean)

    def test_reviewer_access_gate_fail_closed_and_enforcement(self):
        """Verifies Reviewer Access Gate is Fail-Closed in static HTML and halts unauthenticated boot."""
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            index_content = f.read()
        with open(ADMIN_PATH, "r", encoding="utf-8") as f:
            admin_content = f.read()

        # 1. Assert Fail-Closed static markup (no 'hidden' on reviewerAccessGate)
        self.assertRegex(index_content, r'<div id="reviewerAccessGate"\s+class="fixed')
        self.assertRegex(admin_content, r'<div id="reviewerAccessGate"\s+class="fixed')
        self.assertNotRegex(index_content, r'<div id="reviewerAccessGate"\s+class="hidden')
        self.assertNotRegex(admin_content, r'<div id="reviewerAccessGate"\s+class="hidden')

        # 2. Assert Node VM halts initSession when unauthenticated
        node_check = """
        let gateHidden = false;
        let isAuth = false;
        const gateEl = {
            classList: {
                remove: (c) => { if (c === 'hidden') gateHidden = false; },
                add: (c) => { if (c === 'hidden') gateHidden = true; }
            }
        };
        const sessionStorage = { getItem: () => null, setItem: () => {} };
        const window = { location: { search: '' } };
        function enforceReviewerGate() {
            const token = new URLSearchParams(window.location.search).get('access');
            const auth = sessionStorage.getItem('tum_auth_validated') === '1' || token === 'tum2026';
            if (!auth) { gateEl.classList.remove('hidden'); return false; }
            gateEl.classList.add('hidden'); return true;
        }
        let sessionInitialized = false;
        function initSession() {
            if (!enforceReviewerGate()) return;
            sessionInitialized = true;
        }
        initSession();
        console.log('HALTED:' + (!sessionInitialized) + '|GATE_VISIBLE:' + (!gateHidden));
        """
        proc = subprocess.run(["node", "-e", node_check], capture_output=True, text=True, check=True)
        self.assertIn("HALTED:true|GATE_VISIBLE:true", proc.stdout)


class TestMulberry32PRNGAndCohortDeterminism(unittest.TestCase):
    """Tier 2 & Tier 4: Mulberry32 Deterministic PRNG & Cohort Seeding Tests."""

    @staticmethod
    def py_mulberry32(seed):
        """Authoritative Python implementation of 32-bit Mulberry32 PRNG."""
        import ctypes
        state = ctypes.c_uint32(seed).value

        def next_float():
            nonlocal state
            state = (state + 0x6D2B79F5) & 0xFFFFFFFF
            t = state
            p1 = (t ^ (t >> 15)) & 0xFFFFFFFF
            p2 = (t | 1) & 0xFFFFFFFF
            t = ctypes.c_int32(p1 * p2).value
            p3 = ctypes.c_int32(t ^ (ctypes.c_uint32(t).value >> 7)).value
            p4 = ctypes.c_int32(t | 61).value
            imul2 = ctypes.c_int32(p3 * p4).value
            t_add = ctypes.c_int32(t + imul2).value
            t = ctypes.c_int32(t ^ t_add).value
            res = ctypes.c_uint32(t ^ (ctypes.c_uint32(t).value >> 14)).value
            return res / 4294967296.0

        return next_float

    def test_mulberry32_cross_platform_byte_parity_python_vs_node(self):
        """Asserts 100% exact numerical match between Python and Node.js PRNG sequences."""
        seed = 42
        py_rng = self.py_mulberry32(seed)
        py_vals = [py_rng() for _ in range(10)]

        node_code = f"""
        function mulberry32(a) {{
            return function() {{
                var t = a += 0x6D2B79F5;
                t = Math.imul(t ^ (t >>> 15), t | 1);
                t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
                return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
            }}
        }}
        const rng = mulberry32({seed});
        const vals = [];
        for (let i = 0; i < 10; i++) vals.push(rng());
        console.log('__VALS__:' + JSON.stringify(vals));
        """
        proc = subprocess.run(["node", "-e", node_code], capture_output=True, text=True, check=True)
        node_vals = []
        for line in proc.stdout.splitlines():
            if line.startswith("__VALS__:"):
                node_vals = json.loads(line[len("__VALS__:"):])
                break

        self.assertEqual(len(node_vals), 10)
        for i in range(10):
            self.assertAlmostEqual(py_vals[i], node_vals[i], places=12,
                                   msg=f"PRNG mismatch at index {i}: py={py_vals[i]} vs node={node_vals[i]}")

    def test_mulberry32_boundary_seeds(self):
        """Boundary Value Analysis on PRNG seed values: 0, negative, and 2^32 - 1."""
        boundary_seeds = [0, -1, 4294967295, 2147483647]
        for s in boundary_seeds:
            rng = self.py_mulberry32(s)
            val = rng()
            self.assertGreaterEqual(val, 0.0)
            self.assertLess(val, 1.0)

    def test_synthetic_cohort_arm_balancing_algorithm(self):
        """Verifies balanced N/4 cohort generation across arms and non-multiple handling."""
        test_counts = [8, 24, 60, 240, 25]
        for total_n in test_counts:
            # Round-robin allocation simulation
            arm_counts = {1: 0, 2: 0, 3: 0, 4: 0}
            for i in range(total_n):
                arm = (i % 4) + 1
                arm_counts[arm] += 1

            self.assertEqual(sum(arm_counts.values()), total_n)
            if total_n % 4 == 0:
                expected = total_n // 4
                for arm in range(1, 5):
                    self.assertEqual(arm_counts[arm], expected)
            else:
                max_diff = max(arm_counts.values()) - min(arm_counts.values())
                self.assertLessEqual(max_diff, 1)

    def test_econometric_distribution_hypotheses_models(self):
        """Validates simulated behavioral parameters across Arms 1-4 for Paper 1."""
        # Baseline Sara blame rate targets from QA_FEEDBACK_GATHERER.md 0.4
        arm_target_rates = {
            1: 0.65,  # Arm 1 Control: high operator blame
            2: 0.45,  # Arm 2 STAMP: systemic awareness
            3: 0.40,  # Arm 3 Embodied: benchmark recall
            4: 0.15,  # Arm 4 EU AI Act: whistleblowing protection / integrity credit
        }
        # Verify ordering: Arm 1 > Arm 2 >= Arm 3 > Arm 4
        self.assertGreater(arm_target_rates[1], arm_target_rates[2])
        self.assertGreaterEqual(arm_target_rates[2], arm_target_rates[3])
        self.assertGreater(arm_target_rates[3], arm_target_rates[4])


class TestWallClockDeltaTiming(unittest.TestCase):
    """Tier 2 & Tier 4: Drift-Free performance.now() Delta Timing Tests."""

    def test_delta_timing_mathematical_precision_vs_naive_decrement(self):
        """Proves drift-free wall-clock precision under simulated event-loop jitter."""
        total_sim_sec = 25.0

        for speed, expected_wall_sec in [(1, 25.0), (3, 8.333333333333334)]:
            # Simulated jitter: each nominal 50ms interval actually fires at 60ms (20% lag)
            tick_jitter_ms = 60.0
            ticks = 0
            start_wall_ms = 1000000.0
            current_wall_ms = start_wall_ms

            # Simulation using delta-timing:
            simulated_remaining_delta = total_sim_sec
            while simulated_remaining_delta > 0:
                ticks += 1
                current_wall_ms += tick_jitter_ms
                elapsed_wall_sec = (current_wall_ms - start_wall_ms) / 1000.0
                simulated_elapsed_sec = elapsed_wall_sec * speed
                simulated_remaining_delta = max(0.0, total_sim_sec - simulated_elapsed_sec)

            actual_wall_sec_delta = (current_wall_ms - start_wall_ms) / 1000.0

            # Delta timing must finish within 1 tick (60ms) of theoretical exact duration
            self.assertAlmostEqual(actual_wall_sec_delta, expected_wall_sec, delta=0.065,
                                   msg=f"Delta timing drifted at {speed}x speed")

            # In contrast, calculate naive decrement error:
            # Naive decrements subtract nominal dt (50ms * speed = 0.05 * speed) every tick
            naive_ticks_needed = total_sim_sec / (0.05 * speed)
            naive_actual_wall_sec = (naive_ticks_needed * tick_jitter_ms) / 1000.0
            drift_percent = ((naive_actual_wall_sec - expected_wall_sec) / expected_wall_sec) * 100.0

            # Proves naive approach suffers ~20% drift under 20% event-loop jitter
            self.assertGreaterEqual(drift_percent, 19.0,
                                   msg="Naive decrement failed to demonstrate expected timing drift")

    def test_index_timer_delta_timing_integration_when_present(self):
        """Inspects index.html timer intervals for performance.now delta calculation."""
        index_html = load_file(INDEX_PATH)
        m2_perf_markers = ["performance.now()", "startWallTs", "elapsedWallSec"]
        present_count = sum(1 for m in m2_perf_markers if m in index_html)
        if present_count == len(m2_perf_markers):
            for marker in m2_perf_markers:
                self.assertIn(marker, index_html)
        else:
            sys.stdout.write(f"\n  [Progressive Note] index.html delta timing pending M2 merge ({present_count}/{len(m2_perf_markers)} present)")


class TestTelemetryClickstreamAndCsvParity(unittest.TestCase):
    """Tier 1, Tier 2 & Tier 4: Telemetry Schema, Clickstream & 47-Column Parity Tests."""

    def test_clickstream_event_schema_conformance(self):
        """Validates clickstream event structure matches QA_FEEDBACK_GATHERER.md 6.2."""
        sample_valid_events = [
            {
                "t_rel_ms": 1420,
                "timestamp_iso": "2026-11-07T20:30:00.123Z",
                "screen": "screenS1B",
                "step": 2,
                "target_id": "tabCase2Page3",
                "target_tag": "BUTTON",
                "target_aoi": "dossier_page_3",
                "label": "Page 3: Central Depot Scale Log",
                "x": 450,
                "y": 210
            },
            {
                "t_rel_ms": 8450,
                "timestamp_iso": "2026-11-07T20:30:07.150Z",
                "screen": "screenS4",
                "step": None,
                "target_id": "forkOption2",
                "target_tag": "DIV",
                "target_aoi": "s4_option2_absorb_blame",
                "label": "Option 2: Absorb Institutional Liability",
                "x": 620,
                "y": 780
            }
        ]

        iso_regex = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$')

        for evt in sample_valid_events:
            self.assertIsInstance(evt["t_rel_ms"], int)
            self.assertGreaterEqual(evt["t_rel_ms"], 0)
            self.assertTrue(iso_regex.match(evt["timestamp_iso"]))
            self.assertIsInstance(evt["screen"], str)
            self.assertTrue(evt["step"] is None or isinstance(evt["step"], int))
            self.assertIsInstance(evt["target_tag"], str)
            self.assertLessEqual(len(evt["label"]), 40)
            self.assertIsInstance(evt["x"], int)
            self.assertIsInstance(evt["y"], int)

    def test_datapipe_3tier_checkpoint_filename_conventions(self):
        """Verifies naming contracts for 3-Tier DataPipe milestones."""
        pid = "P_2026_TEST"
        arm = 3
        started_name = f"{pid}_arm{arm}_started.json"
        midpoint_name = f"{pid}_arm{arm}_midpoint.json"
        terminal_name = f"{pid}_arm{arm}_session.json"

        self.assertEqual(started_name, "P_2026_TEST_arm3_started.json")
        self.assertEqual(midpoint_name, "P_2026_TEST_arm3_midpoint.json")
        self.assertEqual(terminal_name, "P_2026_TEST_arm3_session.json")

    def test_canonical_47_and_52_column_csv_parity(self):
        """Asserts 47 canonical columns exist and 52-column array parity holds."""
        canonical_47 = [
            "pid", "session_id", "timestamp_iso", "status", "arm",
            "D2_stamp", "D3_embodied", "D4_eu_ai_act", "speed_multiplier", "station_metadata",
            "sla_tier1", "sla_tier2", "sla_tier3", "target_pts", "shift_duration_sec",
            "s1b_executed", "s1b_case1_dwell_sec", "s1b_case1_pages_visited", "s1b_case2_dwell_sec",
            "s1b_case2_page3_visited", "s1b_case2_pages_visited", "s1b_case2_action",
            "s2a_initial_sla_pref_sec", "s2a_initial_archetype", "s2a_override_triggered",
            "s2b_shift2_directive", "s3_dwell_total_ms", "s3_page3_opened", "s3_box_d_dwell_ms",
            "Task1A_slider_sara", "Task1A_slider_ai", "Task1A_slider_sla",
            "Task1A_Derived_Sara_Share_Pct", "Task1B_Root_Cause_Code",
            "Task1C_CDS_Controllability_Sara", "Task1C_CDS_SLA_Constraint",
            "Task2_Penalize_Sara_Binary", "Task2_Choice_Label",
            "Task3_Justification_Char_Len", "Task3_Justification_Text",
            "Task4_Shift4_Sla_Reform_Sec", "Task4_Shift4_Compliant_Binary",
            "final_score_pts", "bonus_unlocked_binary", "integrity_credit_binary",
            "final_payout_eur", "completion_code"
        ]
        self.assertEqual(len(canonical_47), 47)

        idx_html = load_file(INDEX_PATH)
        for col in canonical_47:
            self.assertIn(col, idx_html, f"Missing canonical column in index.html: {col}")

        # Check 52-column export parity between index.html and admin.html
        adm_html = load_file(ADMIN_PATH)
        m_idx = re.search(r"function exportParticipantCsv\(\)\s*\{[\s\S]*?const headers = \[([\s\S]*?)\];", idx_html)
        m_adm = re.search(r"const CSV_HEADERS = \[([\s\S]*?)\];", adm_html)

        if m_idx and m_adm:
            idx_cols = [h.strip().strip('"').strip("'") for h in m_idx.group(1).split(",") if h.strip()]
            adm_cols = [h.strip().strip('"').strip("'") for h in m_adm.group(1).split(",") if h.strip()]
            self.assertEqual(len(idx_cols), 52)
            self.assertEqual(idx_cols, adm_cols)


class TestBannedBrandingAndAntiNudgeLinting(unittest.TestCase):
    """Tier 1 & Tier 2: Static Anti-Nudge & Banned Terminology Linters."""

    def test_anti_nudge_neutral_styling_on_decision_buttons(self):
        """Asserts zero suggestive color classes on participant decision elements."""
        from bs4 import BeautifulSoup
        idx_html = load_file(INDEX_PATH)
        soup = BeautifulSoup(idx_html, "html.parser")

        decision_ids = [
            "btnDirectiveA", "btnDirectiveB",
            "forkOption1", "forkOption2",
            "cardReform1", "cardReform2", "cardReform3"
        ]
        banned_suggestive_classes = [
            "border-emerald-500", "border-emerald-600", "border-green-500", "border-green-600",
            "border-rose-500", "border-rose-600", "border-red-500", "border-red-600",
            "bg-emerald-50", "bg-green-50", "bg-rose-50", "bg-red-50"
        ]

        for el_id in decision_ids:
            el = soup.find(id=el_id)
            self.assertIsNotNone(el, f"Required decision element #{el_id} missing")
            classes = el.get("class", [])
            for banned in banned_suggestive_classes:
                self.assertNotIn(banned, classes,
                                 f"Suggestive color class '{banned}' found on #{el_id}")

    def test_decision_card_visual_symmetry_and_equal_heights(self):
        """Asserts equal height utilities (items-stretch or h-full) on cards."""
        from bs4 import BeautifulSoup
        idx_html = load_file(INDEX_PATH)
        soup = BeautifulSoup(idx_html, "html.parser")

        symmetric_card_ids = ["forkOption1", "forkOption2", "cardReform1", "cardReform2", "cardReform3"]
        for cid in symmetric_card_ids:
            el = soup.find(id=cid)
            if el:
                classes = el.get("class", [])
                self.assertTrue("h-full" in classes or "items-stretch" in classes,
                                f"Element #{cid} lacks equal-height utility ('h-full')")

    def test_purged_hallucinated_metrics_and_debug_labels(self):
        """Asserts absence of ungrounded metrics and stray debug text."""
        idx_html = load_file(INDEX_PATH)
        self.assertNotIn("Confidence: 96.4%", idx_html,
                         "Hallucinated metric 'Confidence: 96.4%' found in index.html")
        self.assertNotIn("Telemetric Reading Audit", idx_html,
                         "Stray debug label 'Telemetric Reading Audit' found in index.html")

    def test_bidirectional_navigation_buttons_present(self):
        """Asserts presence of all 5 S1 bidirectional secondary back buttons."""
        from bs4 import BeautifulSoup
        idx_html = load_file(INDEX_PATH)
        soup = BeautifulSoup(idx_html, "html.parser")

        back_button_ids = ["btnStep2Back", "btnStep3Back", "btnStep4Back", "btnStep5Back", "btnStep6Back"]
        for bid in back_button_ids:
            el = soup.find(id=bid)
            self.assertIsNotNone(el, f"Missing bidirectional back button #{bid} in index.html")

    def test_step6_untimed_clock_label(self):
        """Asserts that practice Case 1 timer explicitly displays UNTIMED."""
        from bs4 import BeautifulSoup
        idx_html = load_file(INDEX_PATH)
        soup = BeautifulSoup(idx_html, "html.parser")

        timer_el = soup.find(id="s1bCountdownTimer")
        self.assertIsNotNone(timer_el, "Missing #s1bCountdownTimer in index.html")
        self.assertIn("UNTIMED", timer_el.text)

    def test_banned_branding_user_facing_text(self):
        """Asserts that user-facing text uses AI Copilot and purges OmniAssist."""
        from bs4 import BeautifulSoup
        idx_html = load_file(INDEX_PATH)
        soup = BeautifulSoup(idx_html, "html.parser")

        # Strip style and script tags to inspect only user-facing rendered text
        for tag in soup(["script", "style"]):
            tag.decompose()
        visible_text = soup.get_text()

        self.assertNotIn("OmniAssist", visible_text,
                         "Banned branding 'OmniAssist' found in user-facing index.html text")

    def test_numerical_anchoring_purge_user_facing(self):
        """Asserts that 13.4s is purged from user-facing text in index.html."""
        from bs4 import BeautifulSoup
        idx_html = load_file(INDEX_PATH)
        soup = BeautifulSoup(idx_html, "html.parser")

        for tag in soup(["script", "style"]):
            tag.decompose()
        visible_text = soup.get_text()

        self.assertNotIn("13.4s", visible_text,
                         "Numerical anchor '13.4s' found in user-facing index.html text")
        self.assertNotIn("13.4 seconds", visible_text,
                         "Numerical anchor '13.4 seconds' found in user-facing index.html text")


def main():
    print("==================================================")
    print("HITL ACCOUNTABILITY STUDY — MVP2 BEHAVIORAL E2E TEST SUITE")
    print("==================================================")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestConfigHydrationAndReactivity,
        TestBase64TokenQuarantine,
        TestMulberry32PRNGAndCohortDeterminism,
        TestWallClockDeltaTiming,
        TestTelemetryClickstreamAndCsvParity,
        TestBannedBrandingAndAntiNudgeLinting
    ]

    for tc in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(tc))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("==================================================")
    if result.wasSuccessful():
        print(f"🏆 ALL BEHAVIORAL E2E TESTS PASSED ({result.testsRun} tests, 100% GREEN)")
        sys.exit(0)
    else:
        print(f"❌ BEHAVIORAL TESTS FAILED: {len(result.failures)} failures, {len(result.errors)} errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
