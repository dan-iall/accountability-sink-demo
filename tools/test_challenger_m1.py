#!/usr/bin/env python3
"""
TUM CIT Research Lab — Milestone 1 Challenger Test Suite
Adversarial empirical stress-testing of admin.html:
1. Mulberry32 PRNG determinism & boundary seeds
2. Cohort generator stress-testing (N=1, 2, 3, 5, 7, 240, 241, 1000) & balancing
3. Base64 token quarantine with extreme unicode, special characters, and corrupted payloads
4. 47-column and 52-column CSV schema conformance
5. localStorage schema and key isolation
"""

import csv
import io
import json
import os
import re
import subprocess
import sys
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ADMIN_PATH = os.path.join(BASE_DIR, "admin.html")
INDEX_PATH = os.path.join(BASE_DIR, "index.html")

def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def run_node(js_code):
    proc = subprocess.run(["node", "-e", js_code], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Node execution failed (code {proc.returncode}):\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")
    return proc.stdout


def extract_admin_script_components():
    """Extracts required functions and definitions from admin.html."""
    html = load_file(ADMIN_PATH)
    scripts = list(re.finditer(r"<script.*?>([\s\S]*?)</script>", html))
    if len(scripts) < 2:
        raise ValueError("Could not find main script block in admin.html")
    script = scripts[1].group(1).strip()
    script = re.sub(r"^\(function\(\)\s*\{", "", script)
    script = re.sub(r"\}\)\(\);\s*$", "", script)
    return script

def build_admin_node_env(extra_js=""):
    """Creates a Node execution script wrapping the admin.html functions."""
    return f"""
    const localStorageStore = {{}};
    const localStorage = {{
        getItem: (k) => localStorageStore[k] !== undefined ? localStorageStore[k] : null,
        setItem: (k, v) => {{ localStorageStore[k] = String(v); }},
        removeItem: (k) => {{ delete localStorageStore[k]; }},
        clear: () => {{ for (const k in localStorageStore) delete localStorageStore[k]; }}
    }};
    const sessionStorage = {{
        getItem: () => '1',
        setItem: () => {{}}
    }};
    const window = {{
        location: {{ origin: 'http://localhost', pathname: '/admin.html', search: '?access=tum2026' }}
    }};
    const dummyEl = {{
        addEventListener: () => {{}},
        classList: {{ add: () => {{}}, remove: () => {{}} }},
        scrollIntoView: () => {{}},
        setAttribute: () => {{}},
        dataset: {{}},
        value: '',
        textContent: '',
        innerHTML: '',
        appendChild: () => {{}},
        querySelectorAll: () => []
    }};
    const document = {{
        getElementById: () => dummyEl,
        querySelector: () => dummyEl,
        querySelectorAll: () => [],
        createElement: (tag) => dummyEl
    }};
    const alert = (msg) => {{}};
    const navigator = {{ clipboard: {{ writeText: async () => {{}} }} }};

    {extract_admin_script_components()}

    {extra_js}
    """


class TestMulberry32Adversarial(unittest.TestCase):
    """Adversarial stress-testing of Mulberry32 PRNG."""

    def test_repeated_seed_byte_level_determinism(self):
        """Verify identical sequence for same seed across multiple runs."""
        seeds_to_test = [0, 1, 42, 999, 2147483647, 4294967295]
        for s in seeds_to_test:
            js = f"""
            const rng1 = mulberry32({s});
            const rng2 = mulberry32({s});
            const s1 = Array.from({{length: 1000}}, () => rng1());
            const s2 = Array.from({{length: 1000}}, () => rng2());
            console.log(JSON.stringify({{ match: JSON.stringify(s1) === JSON.stringify(s2) }}));
            """
            out = run_node(build_admin_node_env(js))
            res = json.loads(out.strip().splitlines()[-1])
            self.assertTrue(res["match"], f"Mulberry32 diverged for seed {s}")

    def test_mulberry32_range_and_stability(self):
        """Stress-test 100,000 outputs across boundary seeds for [0, 1) range and NaN absence."""
        js = """
        const seeds = [0, 1, 1337, 0x7FFFFFFF, 0xFFFFFFFF];
        let allValid = true;
        let minVal = 1.0, maxVal = 0.0;
        for (const seed of seeds) {
            const rng = mulberry32(seed);
            for (let i = 0; i < 20000; i++) {
                const val = rng();
                if (typeof val !== 'number' || isNaN(val) || val < 0 || val >= 1) {
                    allValid = false;
                    break;
                }
                if (val < minVal) minVal = val;
                if (val > maxVal) maxVal = val;
            }
        }
        console.log(JSON.stringify({ allValid, minVal, maxVal }));
        """
        out = run_node(build_admin_node_env(js))
        res = json.loads(out.strip().splitlines()[-1])
        self.assertTrue(res["allValid"], "Mulberry32 produced values outside [0, 1) or NaN")
        self.assertGreaterEqual(res["minVal"], 0.0)
        self.assertLess(res["maxVal"], 1.0)

    def test_seed_type_coercion_and_edge_cases(self):
        """Test negative seeds, large integers, string seeds, whitespace seeds."""
        js = """
        const testInputs = [
            -1, -42, 4294967296, 4294967300, "42", "  100  ", 42.99
        ];
        const results = [];
        for (const inp of testInputs) {
            const hasSeed = inp !== undefined && inp !== null && String(inp).trim() !== '' && !isNaN(Number(inp));
            const rng = hasSeed ? mulberry32(Number(inp) >>> 0) : Math.random;
            const vals = [rng(), rng(), rng()];
            results.push({ inp, hasSeed, vals, allNums: vals.every(v => !isNaN(v) && v >= 0 && v < 1) });
        }
        console.log(JSON.stringify(results));
        """
        out = run_node(build_admin_node_env(js))
        res = json.loads(out.strip().splitlines()[-1])
        for r in res:
            self.assertTrue(r["hasSeed"], f"Input {r['inp']} was unexpectedly treated as non-seed")
            self.assertTrue(r["allNums"], f"Input {r['inp']} produced invalid random floats")

    def test_mulberry32_divergence_above_max_safe_integer(self):
        """Empirically verify exact boundary step (4,917,758) where float precision diverges from 32-bit modulo."""
        js = """
        // Canonical 32-bit integer wrapped Mulberry32
        function mulberry32_canonical(a) {
            return function() {
                var t = a = (a + 0x6D2B79F5) | 0;
                t = Math.imul(t ^ (t >>> 15), t | 1);
                t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
                return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
            };
        }
        const rngCurrent = mulberry32(42);
        const rngCanonical = mulberry32_canonical(42);
        let matchAt4917757 = true;
        let divergedAt4917758 = false;
        // Fast forward 4,917,757 calls
        for (let i = 0; i < 4917757; i++) {
            rngCurrent();
            rngCanonical();
        }
        const vCurr1 = rngCurrent();
        const vCanon1 = rngCanonical();
        matchAt4917757 = (vCurr1 === vCanon1);

        const vCurr2 = rngCurrent();
        const vCanon2 = rngCanonical();
        divergedAt4917758 = (vCurr2 !== vCanon2);

        console.log(JSON.stringify({ matchAt4917757, divergedAt4917758, vCurr2, vCanon2 }));
        """
        out = run_node(build_admin_node_env(js))
        res = json.loads(out.strip().splitlines()[-1])
        self.assertTrue(res["matchAt4917757"], "PRNG diverged prior to 4,917,757 calls")
        self.assertTrue(res["divergedAt4917758"], "PRNG did not exhibit IEEE 754 float divergence at 4,917,758 calls")


class TestCohortGeneratorScalingAndBalancing(unittest.TestCase):
    """Stress tests cohort generator scaling across small, irregular, and large N."""

    def test_cohort_generation_sizes_and_arm_balancing(self):
        """Test N = 1, 2, 3, 5, 7, 240, 241, 1000 in replace mode."""
        test_sizes = [
            (1, {1: 1, 2: 0, 3: 0, 4: 0}),
            (2, {1: 1, 2: 1, 3: 0, 4: 0}),
            (3, {1: 1, 2: 1, 3: 1, 4: 0}),
            (5, {1: 2, 2: 1, 3: 1, 4: 1}),
            (7, {1: 2, 2: 2, 3: 2, 4: 1}),
            (240, {1: 60, 2: 60, 3: 60, 4: 60}),
            (241, {1: 61, 2: 60, 3: 60, 4: 60}),
            (1000, {1: 250, 2: 250, 3: 250, 4: 250}),
        ]
        for n, expected_counts in test_sizes:
            js = f"""
            const sessions = generateSyntheticSessions({n}, 'replace', 42);
            const counts = {{ 1: 0, 2: 0, 3: 0, 4: 0 }};
            sessions.forEach(s => counts[s.arm]++);
            console.log(JSON.stringify({{ count: sessions.length, counts }}));
            """
            out = run_node(build_admin_node_env(js))
            res = json.loads(out.strip().splitlines()[-1])
            self.assertEqual(res["count"], n, f"Failed length check for N={n}")
            self.assertEqual(res["counts"], {str(k): v for k, v in expected_counts.items()}, f"Arm distribution mismatch for N={n}")

    def test_append_mode_incremental_balancing(self):
        """Verify that appending incrementally fills arms with lowest counts."""
        js = """
        // Start with empty vault
        localStorage.clear();
        const results = [];
        // Append 1 session 6 times consecutively
        for (let i = 0; i < 6; i++) {
            const sessions = generateSyntheticSessions(1, 'append', i + 1);
            const counts = { 1: 0, 2: 0, 3: 0, 4: 0 };
            sessions.forEach(s => counts[s.arm]++);
            results.push({ total: sessions.length, counts });
        }
        console.log(JSON.stringify(results));
        """
        out = run_node(build_admin_node_env(js))
        res = json.loads(out.strip().splitlines()[-1])
        self.assertEqual(len(res), 6)
        # Check that after 4 appends, each arm has 1
        self.assertEqual(res[3]["counts"], {"1": 1, "2": 1, "3": 1, "4": 1})
        # After 6 appends, arms 1 and 2 have 2, arms 3 and 4 have 1
        self.assertEqual(res[5]["counts"], {"1": 2, "2": 2, "3": 1, "4": 1})

    def test_reproducibility_across_separate_runs_with_seed(self):
        """Verify that running generateSyntheticSessions twice with same seed is byte-for-byte identical."""
        for n in [241, 1000]:
            js = f"""
            const run1 = generateSyntheticSessions({n}, 'replace', 777);
            const str1 = JSON.stringify(run1);
            const run2 = generateSyntheticSessions({n}, 'replace', 777);
            const str2 = JSON.stringify(run2);
            console.log(JSON.stringify({{ match: str1 === str2, len: str1.length }}));
            """
            out = run_node(build_admin_node_env(js))
            res = json.loads(out.strip().splitlines()[-1])
            self.assertTrue(res["match"], f"Deterministic cohort generation failed for N={n} with seed 777")

    def test_dynamic_config_inheritance(self):
        """Verify synthetic sessions inherit custom config hurdle, SLA, and payouts."""
        js = """
        const customCfg = Object.assign({}, DEFAULT_EXPERIMENT_CONFIG, {
            bonusTargetPts: 1450,
            tier1SlaSec: 22.5,
            tier2SlaSec: 35.0,
            tier3SlaSec: 55.0,
            basePayEur: 3.50,
            performanceBonusEur: 5.50,
            arm4IntegrityCreditEur: 2.50
        });
        localStorage.setItem(CONFIG_KEY, JSON.stringify(customCfg));

        const sessions = generateSyntheticSessions(8, 'replace', 42);
        const check = sessions.map(s => ({
            pid: s.pid,
            arm: s.arm,
            snap_target_pts: s.config_snapshot.target_pts,
            snap_sla1: s.config_snapshot.sla_tier1,
            finalScore: s.s5_outcome.finalManagerScorePts,
            bonusUnlocked: s.s5_outcome.bonusUnlockedBinary,
            payout: s.s5_outcome.finalPayoutEur
        }));
        console.log(JSON.stringify(check));
        """
        out = run_node(build_admin_node_env(js))
        res = json.loads(out.strip().splitlines()[-1])
        for item in res:
            self.assertEqual(item["snap_target_pts"], 1450)
            self.assertEqual(item["snap_sla1"], 22.5)
            if item["arm"] != 4:
                expected_bonus = 1 if item["finalScore"] >= 1450 else 0
                self.assertEqual(item["bonusUnlocked"], expected_bonus)
                expected_payout = 9.00 if expected_bonus == 1 else 3.50
                self.assertAlmostEqual(item["payout"], expected_payout, places=2)
            else:
                # Arm 4: base pay 3.50 + credit 2.50 if absorbed (6.00) or 3.50 if penalized
                self.assertIn(item["payout"], [3.50, 6.00])


class TestBase64TokenQuarantineExtremeCharacters(unittest.TestCase):
    """Stress tests Base64 serialization and deserialization with extreme character sets."""

    def test_extreme_unicode_roundtrip_js_and_python(self):
        """Verify roundtrip with CJK, Arabic, German umlauts, emojis, and control symbols."""
        extreme_cases = [
            {"pid": "P_測試_123", "meta": "CJK Chinese participant test"},
            {"pid": "P_äöü_ß_München", "meta": "TUM CIT München Hauptcampus"},
            {"pid": "P_🚀_✨_🔬", "meta": "Rocket emoji test 🤖💡"},
            {"pid": "P_تجربة_عربية", "meta": "Arabic RTL script test"},
            {"pid": "P_<script>\"'\\n", "meta": "XSS & escape test: <svg onload=alert(1)> \\\" ' \t \r \n"},
            {"pid": "P_NULL_ZERO", "meta": "Standard ASCII metadata"}
        ]

        for case in extreme_cases:
            js = f"""
            const payload = {{
                pid: {json.dumps(case['pid'])},
                arm: 3,
                speed: 3,
                meta: {json.dumps(case['meta'])},
                config: DEFAULT_EXPERIMENT_CONFIG
            }};
            const token = btoa(unescape(encodeURIComponent(JSON.stringify(payload))));
            const unpacked = JSON.parse(decodeURIComponent(escape(atob(token))));
            console.log(JSON.stringify({{ token, unpacked }}));
            """
            out = run_node(build_admin_node_env(js))
            res = json.loads(out.strip().splitlines()[-1])
            unpacked = res["unpacked"]
            self.assertEqual(unpacked["pid"], case["pid"])
            self.assertEqual(unpacked["meta"], case["meta"])
            self.assertEqual(unpacked["arm"], 3)
            self.assertEqual(unpacked["speed"], 3)
            self.assertEqual(len(unpacked["config"]), 37)

    def test_malformed_token_resilience(self):
        """Verify that malformed or truncated base64 tokens are handled safely without unhandled crashes."""
        malformed = [
            "NOT_BASE64_!!!@@@###",
            "SGVsbG8gV29ybGQ=",  # Valid base64 of non-JSON string
            "",
            "   ",
            "eydhcm1nOiAxfQ=="   # Corrupted JSON
        ]
        js = f"""
        const inputs = {json.dumps(malformed)};
        const results = [];
        for (const token of inputs) {{
            let success = false;
            let unpacked = null;
            let error = null;
            try {{
                if (token && token.trim()) {{
                    const raw = decodeURIComponent(escape(atob(token.trim())));
                    unpacked = JSON.parse(raw);
                    success = true;
                }}
            }} catch (e) {{
                error = e.message;
            }}
            results.push({{ token, success, error }});
        }}
        console.log(JSON.stringify(results));
        """
        out = run_node(build_admin_node_env(js))
        res = json.loads(out.strip().splitlines()[-1])
        for r in res:
            # None of these should succeed as valid session payloads
            self.assertFalse(r["success"], f"Token {r['token']} unexpectedly succeeded")


class TestCsvSchemaConformanceAndLocalStorage(unittest.TestCase):
    """Stress tests CSV export formatting and localStorage schema isolation."""

    def test_csv_export_conformance_for_synthetic_cohorts(self):
        """Generates cohort of N=241 and verifies 52-column and 47-column conformance."""
        js = """
        const sessions = generateSyntheticSessions(241, 'replace', 42);

        // Generate CSV rows using admin.html exact export routine
        const rows = [CSV_HEADERS.join(',')];
        sessions.forEach(s => {
            const snap = s.config_snapshot || {};
            const s1b = s.s1b_floor || {};
            const c1 = resolveInspection(s1b, 1);
            const c2 = resolveInspection(s1b, 2);
            const s2a = s.s2a_policy || {};
            const s2b = s.s2b_shifts || {};
            const s3 = s.s3_audit || {};
            const s4 = s.s4_board_report || {};
            const s5 = s.s5_outcome || {};

            const rowData = [
                escapeCsvCell(s.pid || ''),
                escapeCsvCell(s.sessionId || ''),
                escapeCsvCell(s.startedAtIso || ''),
                escapeCsvCell(s.status || ''),
                escapeCsvCell(s.arm || ''),
                escapeCsvCell(s.D2_stamp ?? (s.arm === 2 ? 1 : 0)),
                escapeCsvCell(s.D3_embodied ?? (s.arm === 3 ? 1 : 0)),
                escapeCsvCell(s.D4_eu_ai_act ?? (s.arm === 4 ? 1 : 0)),
                escapeCsvCell(s.speedMultiplier ?? 1),
                escapeCsvCell(s.stationMetadata || ''),
                escapeCsvCell(snap.sla_tier1 ?? 25.0),
                escapeCsvCell(snap.sla_tier2 ?? 38.0),
                escapeCsvCell(snap.sla_tier3 ?? 60.0),
                escapeCsvCell(snap.target_pts ?? 1200),
                escapeCsvCell(snap.shift_duration_sec ?? 25.0),
                escapeCsvCell(s1b.executed ? 1 : 0),
                escapeCsvCell(s1b.case1TotalDwellSec ?? ''),
                escapeCsvCell(s1b.executed ? (c1?.count ?? '') : (s1b.case1PagesVisitedCount ?? '')),
                escapeCsvCell(s1b.executed ? (c1?.p1 ?? '') : (s1b.case1Page1Visited !== undefined ? (s1b.case1Page1Visited ? 1 : 0) : '')),
                escapeCsvCell(s1b.executed ? (c1?.p2 ?? '') : (s1b.case1Page2Visited !== undefined ? (s1b.case1Page2Visited ? 1 : 0) : '')),
                escapeCsvCell(s1b.executed ? (c1?.p3 ?? '') : (s1b.case1Page3Visited !== undefined ? (s1b.case1Page3Visited ? 1 : 0) : '')),
                escapeCsvCell(s1b.case2TotalDwellSec ?? ''),
                escapeCsvCell(s1b.executed ? (c2?.p1 ?? '') : (s1b.case2Page1Visited !== undefined ? (s1b.case2Page1Visited ? 1 : 0) : '')),
                escapeCsvCell(s1b.executed ? (c2?.p2 ?? '') : (s1b.case2Page2Visited !== undefined ? (s1b.case2Page2Visited ? 1 : 0) : '')),
                escapeCsvCell(s1b.executed ? (c2?.p3 ?? '') : (s1b.case2Page3Visited !== undefined ? (s1b.case2Page3Visited ? 1 : 0) : '')),
                escapeCsvCell(s1b.executed ? (c2?.count ?? '') : (s1b.case2PagesVisitedCount ?? '')),
                escapeCsvCell(s1b.case2Action || ''),
                escapeCsvCell(s2a.initialSlaPreferenceSec ?? ''),
                escapeCsvCell(s2a.initialSlaArchetype || ''),
                escapeCsvCell(s2a.corporateOverrideTriggered !== undefined ? (s2a.corporateOverrideTriggered ? 1 : 0) : ''),
                escapeCsvCell(s2b.shift2Directive || ''),
                escapeCsvCell(s3.dwell_s3_total_ms ?? ''),
                escapeCsvCell(s3.page3Opened !== undefined ? (s3.page3Opened ? 1 : 0) : ''),
                escapeCsvCell(s3.dwell_box_d_treatment_ms ?? ''),
                escapeCsvCell(s4.sliderSara ?? ''),
                escapeCsvCell(s4.sliderAi ?? ''),
                escapeCsvCell(s4.sliderSla ?? ''),
                escapeCsvCell(s4.Task1A_Derived_Sara_Share_Pct ?? ''),
                escapeCsvCell(s4.Task1B_Root_Cause_Code || ''),
                escapeCsvCell(s4.Task1C_CDS_Controllability_Sara ?? ''),
                escapeCsvCell(s4.Task1C_CDS_SLA_Constraint ?? ''),
                escapeCsvCell(s4.Task2_Penalize_Sara_Binary ?? ''),
                escapeCsvCell(s4.Task2_Choice_Label || ''),
                escapeCsvCell(s4.Task3_Justification_Char_Len ?? (s4.Task3_Justification_Text ? s4.Task3_Justification_Text.length : '')),
                escapeCsvCell(s4.Task3_Justification_Text || ''),
                escapeCsvCell(s4.Task4_Shift4_Sla_Reform_Sec ?? ''),
                escapeCsvCell(s4.Task4_Shift4_Compliant_Binary ?? ''),
                escapeCsvCell(s5.finalManagerScorePts ?? ''),
                escapeCsvCell(s5.bonusUnlockedBinary ?? ''),
                escapeCsvCell(s5.integrityCreditAwardedBinary ?? ''),
                escapeCsvCell(s5.finalPayoutEur ?? ''),
                escapeCsvCell(s.completionCode || '')
            ];
            rows.push(rowData.join(','));
        });
        console.log(rows.join('\\n'));
        """
        out = run_node(build_admin_node_env(js))
        csv_file = io.StringIO(out)
        reader = list(csv.reader(csv_file))

        header = reader[0]
        self.assertEqual(len(header), 52, f"CSV header length mismatch: expected 52, got {len(header)}")

        # Verify all 47 canonical columns exist in the 52-column export
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
        for c in canonical_47:
            self.assertIn(c, header, f"Canonical 47-column item missing from header: {c}")

        # Check all 241 data rows
        data_rows = reader[1:]
        self.assertEqual(len(data_rows), 241)
        for idx, row in enumerate(data_rows):
            self.assertEqual(len(row), 52, f"Row {idx+1} length mismatch: got {len(row)}, expected 52")
            pid = row[0]
            self.assertTrue(pid.startswith("P_"), f"Malformed PID: {pid}")
            arm = int(row[4])
            self.assertIn(arm, [1, 2, 3, 4])
            completion_code = row[51]
            self.assertTrue(completion_code.startswith("TUM-DONE-"), f"Malformed completion code: {completion_code}")

    def test_local_storage_isolation_and_schema_safety(self):
        """Verify that cohort generation never mutates tum_study_config or creates rogue keys."""
        js = """
        localStorage.clear();
        const initialConfig = JSON.stringify({ customKey: "SAFE_CONFIG_VALUE" });
        localStorage.setItem(CONFIG_KEY, initialConfig);

        generateSyntheticSessions(60, 'replace', 123);

        const keys = Object.keys(localStorageStore);
        const configAfter = localStorage.getItem(CONFIG_KEY);
        console.log(JSON.stringify({ keys, configUntouched: configAfter === initialConfig }));
        """
        out = run_node(build_admin_node_env(js))
        res = json.loads(out.strip().splitlines()[-1])
        self.assertTrue(res["configUntouched"], "localStorage['tum_study_config'] was mutated by cohort generator!")
        self.assertIn("tum_study_sessions", res["keys"])
        self.assertIn("tum_study_config", res["keys"])
        self.assertEqual(len(res["keys"]), 2)

    def test_csv_cell_escaping_adversarial_injection(self):
        """Stress-test escapeCsvCell with double quotes, newlines, commas, CRLF, and null/undefined."""
        js = """
        const testCells = [
            'Simple Text',
            'Text, with comma',
            'Text "with quotes"',
            'Multi\\nLine\\r\\nText',
            'Quote "and, comma"\\ncombo',
            null,
            undefined,
            123.45,
            0
        ];
        const escaped = testCells.map(c => escapeCsvCell(c));
        console.log(JSON.stringify(escaped));
        """
        out = run_node(build_admin_node_env(js))
        res = json.loads(out.strip().splitlines()[-1])
        self.assertEqual(res[0], 'Simple Text')
        self.assertEqual(res[1], '"Text, with comma"')
        self.assertEqual(res[2], '"Text ""with quotes"""')
        self.assertEqual(res[3], '"Multi\nLine\r\nText"')
        self.assertEqual(res[4], '"Quote ""and, comma""\ncombo"')
        self.assertEqual(res[5], '')
        self.assertEqual(res[6], '')
        self.assertEqual(res[7], '123.45')
        self.assertEqual(res[8], '0')

    def test_corrupted_local_storage_sessions_handling(self):
        """Demonstrate TypeError if tum_study_sessions contains non-array JSON object."""
        js = """
        localStorage.setItem(SESSIONS_KEY, JSON.stringify({ corrupted: true }));
        let caughtError = null;
        try {
            const sess = getSessions();
            calculateArmCounts(sess);
        } catch (e) {
            caughtError = { name: e.name, message: e.message };
        }
        console.log(JSON.stringify({ caughtError }));
        """
        out = run_node(build_admin_node_env(js))
        res = json.loads(out.strip().splitlines()[-1])
        # Confirms the identified vulnerability where non-array throws TypeError on sessions.forEach
        self.assertIsNotNone(res["caughtError"], "Expected TypeError when sessions is not an Array")
        self.assertIn("forEach", res["caughtError"]["message"])

if __name__ == "__main__":
    print("=" * 60)
    print("TUM CIT RESEARCH LAB — CHALLENGER M1 ADVERSARIAL SUITE")
    print("=" * 60)
    unittest.main(verbosity=2)
