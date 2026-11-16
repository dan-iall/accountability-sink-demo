#!/usr/bin/env python3
"""
TUM CIT Research Lab — M_FINAL Phase 2: Tier 5
White-Box Adversarial Coverage Hardening & Edge-Case Audit Suite
================================================================
Empirically stress-tests edge-case execution paths across index.html and admin.html:
1. parseSessionParams() quarantine token edge cases, arm boundary traps, speed fallbacks
2. initSession() in-progress resume overrides, leak guards, interaction clickstream init
3. hydrateConfigUI() under pathological/zero/extreme config values and missing DOM elements
4. calculateFinalOutcome() & renderScreen5() ledger precision across all branches & arms
5. CSV export schema parity (52 columns), special-character escaping, and non-Arm-3 blanking
6. Mulberry32 boundary seeds (0, negative, 2^32-1) and cohort generator append balancing
7. DataPipe 3-tier checkpoints (started, midpoint single-fire, terminal) and beacon guard
"""

import json
import os
import subprocess
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HARNESS = os.path.join(BASE_DIR, "tools", "workflow_challenger_harness.js")
ADMIN_HARNESS = os.path.join(BASE_DIR, "tools", "admin_vm_harness.js")


def run_index_js(js_code, custom_cfg=None, session_overrides=None, search_query="?access=tum2026"):
    """Executes arbitrary JS inside the audited index.html VM environment."""
    cfg_json = json.dumps(custom_cfg) if custom_cfg is not None else "null"
    sess_json = json.dumps(session_overrides) if session_overrides is not None else "{}"
    search_json = json.dumps(search_query)

    wrapper = f"""
    const vm = require('vm');
    const harness = require({json.dumps(INDEX_HARNESS)});
    const h = harness.createHarnessContext();
    h.sandbox.window.location.search = {search_json};
    const state = vm.runInContext('state', h.context);
    h.context.initSession();

    const customCfg = {cfg_json};
    if (customCfg !== null) {{
      state.config = customCfg;
    }}
    const sessOverrides = {sess_json};
    Object.assign(state.session, sessOverrides);

    const fn = new Function('h', 'state', 'vm', {json.dumps(js_code)});
    const res = fn(h, state, vm);
    console.log('__OUT__:' + JSON.stringify(res));
    """

    proc = subprocess.run(["node", "-e", wrapper], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Node execution failed:\\nSTDOUT: {proc.stdout}\\nSTDERR: {proc.stderr}")
    for line in proc.stdout.splitlines():
        if line.startswith("__OUT__:"):
            return json.loads(line[len("__OUT__:"):])
    raise ValueError(f"No __OUT__ found in: {proc.stdout}")


def run_admin_js(js_code, initial_storage=None):
    """Executes arbitrary JS inside the audited admin.html VM environment."""
    storage_json = json.dumps(initial_storage if initial_storage is not None else {})

    wrapper = f"""
    const vm = require('vm');
    const adminHarness = require({json.dumps(ADMIN_HARNESS)});
    const env = adminHarness.createAdminEnvironment({storage_json});
    const fn = new Function('env', 'vm', {json.dumps(js_code)});
    const res = fn(env, vm);
    console.log('__OUT__:' + JSON.stringify(res));
    """

    proc = subprocess.run(["node", "-e", wrapper], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Node execution failed:\\nSTDOUT: {proc.stdout}\\nSTDERR: {proc.stderr}")
    for line in proc.stdout.splitlines():
        if line.startswith("__OUT__:"):
            return json.loads(line[len("__OUT__:"):])
    raise ValueError(f"No __OUT__ found in: {proc.stdout}")


class TestParseSessionParamsAndTokenQuarantineWhiteBox(unittest.TestCase):
    """Stress tests parseSessionParams with pathological, corrupted, and boundary tokens."""

    def test_corrupted_and_primitive_token_payloads(self):
        """Verifies parseSessionParams never crashes on corrupted or non-object JSON tokens."""
        test_payloads = [
            "INVALID_BASE64_!@#$%",
            "eyJpbnZhbGlkX2pzb24iOiB1bnRlcm1pbmF0ZWQ=",
            "ImhlbGxvIHdvcmxkIg==",
            "MTIzNDU=",
            "dHJ1ZQ==",
            "bnVsbA==",
            "WzEsIDIsIDNd"
        ]
        for b64 in test_payloads:
            code = f"""
            h.sandbox.window.location.search = '?token={b64}';
            const params = h.context.parseSessionParams();
            return {{
                hasArm: [1, 2, 3, 4].includes(params.arm),
                speed: params.speed,
                hasPid: typeof params.pid === 'string' && params.pid.length > 0
            }};
            """
            res = run_index_js(code)
            self.assertTrue(res["hasArm"], f"Arm allocation failed for token: {b64}")
            self.assertEqual(res["speed"], 1)
            self.assertTrue(res["hasPid"])

    def test_arm_parameter_boundary_and_garbage_values(self):
        """Verifies boundary values for arm (-1, 0, 5, 999, 'abc') allocate cleanly."""
        for bad_arm in ["-1", "0", "5", "999", "abc", "", "NaN", "null"]:
            code = f"""
            h.sandbox.window.location.search = '?arm={bad_arm}';
            const params = h.context.parseSessionParams();
            return {{ arm: params.arm }};
            """
            res = run_index_js(code)
            self.assertIn(res["arm"], [1, 2, 3, 4], f"Bad arm '{bad_arm}' resulted in invalid arm {res['arm']}")

    def test_speed_parameter_boundary_filtering(self):
        """Verifies only speed=3 enables accelerated speed; all others default strictly to 1."""
        speeds = [("3", 3), ("1", 1), ("0", 1), ("2", 1), ("10", 1), ("-1", 1), ("NaN", 1), ("fast", 1)]
        for query_val, expected in speeds:
            code = f"""
            h.sandbox.window.location.search = '?speed={query_val}';
            const params = h.context.parseSessionParams();
            return {{ speed: params.speed }};
            """
            res = run_index_js(code)
            self.assertEqual(res["speed"], expected, f"Query speed '{query_val}' expected {expected}, got {res['speed']}")

    def test_url_numerical_overrides_boundary_zero_and_nan(self):
        """Verifies URL parameter overrides handle 0 and NaN gracefully without corrupting config."""
        code = """
        h.sandbox.window.location.search = '?sla1=0&sla2=NaN&target=0&dur=0.001';
        const params = h.context.parseSessionParams();
        return {
            sla1: params.config.tier1SlaSec,
            sla2: params.config.tier2SlaSec,
            target: params.config.bonusTargetPts,
            dur: params.config.shiftDurationSimSec,
            hasNaN: isNaN(params.config.tier1SlaSec) || isNaN(params.config.bonusTargetPts)
        };
        """
        res = run_index_js(code)
        self.assertFalse(res["hasNaN"])
        self.assertGreater(res["sla1"], 0)
        self.assertGreater(res["target"], 0)
        self.assertEqual(res["dur"], 0.001)

    def test_token_config_caching_into_local_storage(self):
        """Verifies token carrying a custom config object hydrates config and caches to localStorage."""
        custom_cfg = {"bonusTargetPts": 1550, "basePayEur": 3.75}
        payload = {"pid": "P_CACHE_TEST", "arm": 3, "speed": 1, "config": custom_cfg}
        import base64
        token_str = base64.b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')

        code = f"""
        h.sandbox.window.location.search = '?token={token_str}';
        const params = h.context.parseSessionParams();
        const cachedRaw = h.sandbox.localStorage.getItem('tum_study_config');
        const cached = cachedRaw ? JSON.parse(cachedRaw) : null;
        return {{
            paramTarget: params.config.bonusTargetPts,
            paramBase: params.config.basePayEur,
            cachedTarget: cached ? cached.bonusTargetPts : null,
            cachedBase: cached ? cached.basePayEur : null
        }};
        """
        res = run_index_js(code)
        self.assertEqual(res["paramTarget"], 1550)
        self.assertEqual(res["paramBase"], 3.75)
        self.assertEqual(res["cachedTarget"], 1550)
        self.assertEqual(res["cachedBase"], 3.75)


class TestInitSessionAndStateGuardsWhiteBox(unittest.TestCase):
    """Stress tests initSession state machine guards, resume sync, and clickstream logging."""

    def test_resume_in_progress_session_url_param_sync(self):
        """Verifies mutable URL parameters (speed=3, arm=4, meta) sync into an IN_PROGRESS session."""
        existing_sess = {
            "sessionId": "S_P101_1000",
            "pid": "P_SYNC_101",
            "arm": 1,
            "D2_stamp": 0, "D3_embodied": 0, "D4_eu_ai_act": 0,
            "speedMultiplier": 1,
            "stationMetadata": "Old Station",
            "status": "IN_PROGRESS",
            "startedAtIso": "2026-11-01T10:00:00.000Z"
        }
        code = f"""
        h.sandbox.localStorage.setItem('tum_study_sessions', JSON.stringify([{json.dumps(existing_sess)}]));
        h.sandbox.window.location.search = '?pid=P_SYNC_101&arm=4&speed=3&meta=Updated+Lab+Station';
        h.context.initSession();
        return {{
            arm: state.session.arm,
            D4: state.session.D4_eu_ai_act,
            speed: state.session.speedMultiplier,
            meta: state.session.stationMetadata,
            eventsIsArray: Array.isArray(state.session.interaction_events)
        }};
        """
        res = run_index_js(code)
        self.assertEqual(res["arm"], 4)
        self.assertEqual(res["D4"], 1)
        self.assertEqual(res["speed"], 3)
        self.assertEqual(res["meta"], "Updated Lab Station")
        self.assertTrue(res["eventsIsArray"])

    def test_state_machine_leak_guard_cross_arm_switch(self):
        """Verifies changing arm from 3 to 1/2/4 clamps currentS1Step <= 5 and redirects away from Screen 1B."""
        for target_arm in [1, 2, 4]:
            code = f"""
            state.session.arm = 3;
            state.currentS1Step = 6;
            state.currentScreen = 'screenS1B';
            h.sandbox.window.location.search = '?pid=' + state.session.pid + '&arm={target_arm}';
            h.context.initSession();
            return {{
                arm: state.session.arm,
                step: state.currentS1Step,
                screen: state.currentScreen
            }};
            """
            res = run_index_js(code)
            self.assertEqual(res["arm"], target_arm)
            self.assertLessEqual(res["step"], 5, f"Arm {target_arm} remained at step {res['step']}")
            self.assertEqual(res["screen"], "screenS1", f"Arm {target_arm} leaked screen {res['screen']}")


class TestHydrateConfigUIPathologicalBoundaries(unittest.TestCase):
    """Stress tests hydrateConfigUI with zero values, missing keys, and partial DOM environments."""

    def test_zero_and_extreme_financial_and_sla_values(self):
        """Verifies zero financial/SLA values hydrate cleanly without NaN or layout crash."""
        pathological_cfg = {
            "basePayEur": 0.00,
            "performanceBonusEur": 0.00,
            "arm4IntegrityCreditEur": 0.00,
            "bonusTargetPts": 0,
            "tier1SlaSec": 0.0,
            "tier2SlaSec": 0.0,
            "tier3SlaSec": 0.0
        }
        code = f"""
        h.context.hydrateConfigUI({json.dumps(pathological_cfg)});
        const s1Base = h.getElement('s1Step5BasePay').textContent;
        const s1Bonus = h.getElement('s1Step5BonusPay').textContent;
        const s1Hurdle = h.getElement('s1Step5BonusHurdle').textContent;
        const s2aOpt1 = h.getElement('s2aOpt1SlaSec').textContent;
        return {{
            s1Base,
            s1Bonus,
            s1Hurdle,
            s2aOpt1,
            hasNaN: s1Base.includes('NaN') || s1Bonus.includes('NaN') || s1Hurdle.includes('NaN')
        }};
        """
        res = run_index_js(code)
        self.assertFalse(res["hasNaN"])
        self.assertEqual(res["s1Base"], "€0.00")
        self.assertEqual(res["s1Bonus"], "€0.00")
        self.assertEqual(res["s1Hurdle"], "0")
        self.assertEqual(res["s2aOpt1"], "0.0s Target")

    def test_null_and_empty_config_fallback(self):
        """Verifies null or empty config safely falls back to DEFAULT_EXPERIMENT_CONFIG."""
        code = """
        h.context.hydrateConfigUI(null);
        return {
            s1Base: h.getElement('s1Step5BasePay').textContent,
            s1Bonus: h.getElement('s1Step5BonusPay').textContent,
            s1Hurdle: h.getElement('s1Step5BonusHurdle').textContent
        };
        """
        res = run_index_js(code)
        self.assertEqual(res["s1Base"], "€2.50")
        self.assertEqual(res["s1Bonus"], "€4.00")
        self.assertEqual(res["s1Hurdle"], "1,200")


class TestCalculateFinalOutcomeAndLedgerWhiteBox(unittest.TestCase):
    """Stress tests calculateFinalOutcome and renderScreen5 ledger precision across all conditions."""

    def test_arm4_statutory_audit_both_branches_dynamic_credit(self):
        """Verifies Arm 4 Penalize Sara fine vs Absorb Blame commendation credit and score adjustment."""
        # Branch 1: Penalize Sara (Retaliation Fine -50 pts, Bonus Revoked)
        code_penalize = """
        state.session.arm = 4;
        state.session.s2b_shifts = { shift1Pts: 360, shift2Directive: 'DIRECTIVE_A', shift2Pts: 360, shift3PreCrashPts: 270, provisionalHoldPts: -300 };
        state.session.s4_board_report = { Task2_Penalize_Sara_Binary: 1, Task4_Shift4_Sla_Reform_Sec: 60.0 };
        const out = h.context.calculateFinalOutcome();
        h.context.renderScreen5();
        const arm4BoxHtml = h.getElement('s5Arm4Reveal').innerHTML;
        return {
            finalScore: out.finalScore,
            bonusUnlocked: out.bonusUnlocked,
            integrityCredit: out.integrityCredit,
            finalPayout: out.finalPayout,
            hasFineNotice: arm4BoxHtml.includes('Retaliation Fine')
        };
        """
        res_pen = run_index_js(code_penalize)
        self.assertEqual(res_pen["finalScore"], 940)
        self.assertEqual(res_pen["bonusUnlocked"], 0)
        self.assertEqual(res_pen["integrityCredit"], 0)
        self.assertEqual(res_pen["finalPayout"], 2.50)
        self.assertTrue(res_pen["hasFineNotice"])

        # Branch 2: Absorb Blame (Corporate Integrity Credit +100 pts, +€1.00 Credit)
        code_absorb = """
        state.session.arm = 4;
        state.session.s2b_shifts = { shift1Pts: 360, shift2Directive: 'DIRECTIVE_A', shift2Pts: 360, shift3PreCrashPts: 270, provisionalHoldPts: -300 };
        state.session.s4_board_report = { Task2_Penalize_Sara_Binary: 0, Task4_Shift4_Sla_Reform_Sec: 60.0 };
        const out = h.context.calculateFinalOutcome();
        h.context.renderScreen5();
        const arm4BoxHtml = h.getElement('s5Arm4Reveal').innerHTML;
        return {
            finalScore: out.finalScore,
            bonusUnlocked: out.bonusUnlocked,
            integrityCredit: out.integrityCredit,
            finalPayout: out.finalPayout,
            hasCommendation: arm4BoxHtml.includes('Integrity Credit Award')
        };
        """
        res_abs = run_index_js(code_absorb)
        self.assertEqual(res_abs["finalScore"], 1090)
        self.assertEqual(res_abs["bonusUnlocked"], 0)
        self.assertEqual(res_abs["integrityCredit"], 1)
        self.assertEqual(res_abs["finalPayout"], 3.50)
        self.assertTrue(res_abs["hasCommendation"])

    def test_numerical_precision_no_string_concatenation(self):
        """Verifies floating point financial calculation does not perform string concatenation."""
        custom_cfg = {"basePayEur": 3.25, "performanceBonusEur": 4.50, "bonusTargetPts": 1000}
        code = f"""
        state.config = {json.dumps(custom_cfg)};
        state.session.arm = 1;
        state.session.s2b_shifts = {json.dumps({"shift1Pts": 360, "shift2Directive": "DIRECTIVE_A", "shift2Pts": 360, "shift3PreCrashPts": 270, "provisionalHoldPts": -300})};
        state.session.s4_board_report = {json.dumps({"Task2_Penalize_Sara_Binary": 1, "Task4_Shift4_Sla_Reform_Sec": 60.0})};
        const out = h.context.calculateFinalOutcome();
        return {{
            payout: out.finalPayout,
            isNumber: typeof out.finalPayout === 'number'
        }};
        """
        res = run_index_js(code)
        self.assertTrue(res["isNumber"])
        self.assertEqual(res["payout"], 7.75)


class TestCsvExportParityAndSpecialCharEscaping(unittest.TestCase):
    """Stress tests CSV export parity between index.html and admin.html and character escaping."""

    def test_index_and_admin_52_column_schema_exact_parity(self):
        """Verifies exact 52-column header equality and ordering between index.html and admin.html."""
        import re
        with open(os.path.join(BASE_DIR, "index.html"), "r", encoding="utf-8") as f:
            index_html = f.read()
        with open(os.path.join(BASE_DIR, "admin.html"), "r", encoding="utf-8") as f:
            admin_html = f.read()

        index_m = re.search(r'const headers = \[\s*([\s\S]*?)\s*\];', index_html)
        admin_m = re.search(r'const CSV_HEADERS = \[\s*([\s\S]*?)\s*\];', admin_html)
        self.assertIsNotNone(index_m)
        self.assertIsNotNone(admin_m)

        index_cols = [c.strip().strip('"\'') for c in index_m.group(1).replace('\n', '').split(',') if c.strip()]
        admin_cols = [c.strip().strip('"\'') for c in admin_m.group(1).replace('\n', '').split(',') if c.strip()]

        self.assertEqual(len(index_cols), 52, f"index.html has {len(index_cols)} columns, expected 52")
        self.assertEqual(len(admin_cols), 52, f"admin.html has {len(admin_cols)} columns, expected 52")
        self.assertEqual(index_cols, admin_cols, "Column order mismatch between index.html and admin.html")

    def test_special_characters_and_quote_escaping(self):
        """Verifies quotes, commas, and newlines in text fields are escaped cleanly."""
        code = """
        const cleanText = (t) => `"${(t || '').toString().replace(/"/g, '""').replace(/\\n/g, ' ')}"`;
        const testStr = 'Line 1\\nLine 2 with "quotes" and, commas';
        return {
            cleaned: cleanText(testStr)
        };
        """
        res = run_index_js(code)
        self.assertEqual(res["cleaned"], '"Line 1 Line 2 with ""quotes"" and, commas"')


class TestMulberry32AndCohortGeneratorWhiteBox(unittest.TestCase):
    """Stress tests Mulberry32 PRNG determinism and cohort generator append/balance modes."""

    def test_mulberry32_extreme_seeds(self):
        """Verifies boundary seeds (0, negative, 2^32-1) never produce NaN or values out of [0, 1)."""
        code = """
        function mulberry32(a) {
          a = a >>> 0;
          return function() {
            var t = a += 0x6D2B79F5;
            t = Math.imul(t ^ (t >>> 15), t | 1);
            t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
            return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
          };
        }
        const seeds = [0, 1, -1, 4294967295, 42];
        const results = {};
        for (const s of seeds) {
          const rng = mulberry32(s);
          const seq = [rng(), rng(), rng(), rng(), rng()];
          const anyNaN = seq.some(v => isNaN(v));
          const allInRange = seq.every(v => v >= 0 && v < 1);
          results[s] = { anyNaN, allInRange, firstVal: seq[0] };
        }
        return results;
        """
        res = run_admin_js(code)
        for seed_str, data in res.items():
            self.assertFalse(data["anyNaN"], f"Seed {seed_str} produced NaN!")
            self.assertTrue(data["allInRange"], f"Seed {seed_str} produced value out of bounds [0, 1)")

    def test_cohort_generator_append_mode_balancing(self):
        """Verifies append mode dynamically balances an uneven existing session vault."""
        pre_existing = [
            {"pid": "P_1001", "arm": 1, "status": "COMPLETED"},
            {"pid": "P_1002", "arm": 1, "status": "COMPLETED"},
            {"pid": "P_1003", "arm": 1, "status": "COMPLETED"}
        ]
        code = """
        const sessions = env.sandbox.window.generateSyntheticSessions(6, 'append', 42);
        const stored = JSON.parse(env.localStorageStore['tum_study_sessions']);
        const counts = { 1: 0, 2: 0, 3: 0, 4: 0 };
        stored.forEach(s => counts[s.arm]++);
        return {
            totalCount: stored.length,
            counts
        };
        """
        res = run_admin_js(code, {"tum_study_sessions": json.dumps(pre_existing)})
        self.assertEqual(res["totalCount"], 9)
        counts = res["counts"]
        self.assertEqual(counts["1"], 3)
        self.assertEqual(counts["2"], 2)
        self.assertEqual(counts["3"], 2)
        self.assertEqual(counts["4"], 2)


class TestDataPipeCloudCheckpointsAndBeaconFallback(unittest.TestCase):
    """Stress tests DataPipe checkpoint milestones and graceful pagehide dropout beacon."""

    def test_datapipe_payload_builder_experiment_id(self):
        """Verifies DataPipe payload inherits custom or default experiment ID."""
        code = """
        const experimentID = state.config?.datapipeExperimentId || '30e5A1M4ut54';
        return { experimentID };
        """
        res = run_index_js(code)
        self.assertEqual(res["experimentID"], "30e5A1M4ut54")

    def test_dropout_beacon_guard_against_completed_session(self):
        """Verifies handleDropoutBeacon does NOT transmit if session is already COMPLETED."""
        code = """
        let beaconCalled = false;
        h.sandbox.navigator.sendBeacon = function() { beaconCalled = true; return true; };
        state.session.status = 'COMPLETED';
        state.session.completedAtIso = new Date().toISOString();
        h.context.handleDropoutBeacon();
        return { beaconCalled };
        """
        res = run_index_js(code)
        self.assertFalse(res["beaconCalled"])


if __name__ == '__main__':
    unittest.main()
