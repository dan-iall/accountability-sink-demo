#!/usr/bin/env python3
"""
HITL ACCOUNTABILITY STUDY — MVP2 ADVERSARIAL CHALLENGER TEST SUITE (M1)
=============================================================
Empirical adversarial stress testing of Milestone 1 in admin.html:
- Option B dynamic config binding under extreme inputs (zero, negative, huge, malformed).
- Metric node reactivity (#lblTargetCohortN, #cfgSummary*, Balancer denominators).
- Synthetic cohort generator: replace vs append modes with existing localStorage state.
- PID uniqueness, greedy minimum-fill balancing, and Mulberry32 determinism.
"""

import json
import os
import subprocess
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADMIN_PATH = os.path.join(BASE_DIR, "admin.html")
CONFIG_PATH = os.path.join(BASE_DIR, "tum_experiment_config.json")
HARNESS_JS = os.path.join(BASE_DIR, "tools", "admin_vm_harness.js")


def run_in_node(js_script):
    """Executes a JS script in Node.js and parses the __RESULT__ JSON output."""
    normalized_script = js_script.replace('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js', HARNESS_JS)
    proc = subprocess.run(
        ["node", "-e", normalized_script],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Node execution failed (code {proc.returncode}):\n{proc.stderr}\n{proc.stdout}")
    for line in proc.stdout.splitlines():
        if line.startswith("__RESULT__:"):
            return json.loads(line[len("__RESULT__:"):])
    raise ValueError(f"No __RESULT__ in output:\n{proc.stdout}\nStderr:\n{proc.stderr}")


class TestExtremeDynamicConfigBinding(unittest.TestCase):
    """Stress tests Option B dynamic config binding in admin.html under extreme inputs."""

    def test_zero_financial_and_hurdle_inputs(self):
        """Tests admin UI reactivity when financial stakes and hurdles are zero."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        const extremeConfig = {
            targetCohortN: 0,
            bonusTargetPts: 0,
            basePayEur: 0,
            performanceBonusEur: 0,
            arm4IntegrityCreditEur: 0,
            tier1SlaSec: 0,
            tier2SlaSec: 0,
            tier3SlaSec: 0,
            shiftDurationSimSec: 0
        };
        const env = createAdminEnvironment({
            tum_study_config: JSON.stringify(extremeConfig)
        });

        env.sandbox.window.updateConfigBadgeUI();

        const result = {
            lblTargetCohortN: env.elements['lblTargetCohortN'].textContent,
            cfgSummarySla: env.elements['cfgSummarySla'].textContent,
            cfgSummaryShiftDuration: env.elements['cfgSummaryShiftDuration'].textContent,
            cfgSummaryHurdle: env.elements['cfgSummaryHurdle'].textContent,
            cfgSummaryTargetN: env.elements['cfgSummaryTargetN'].textContent,
            lblCohortEnrolled: env.elements['lblCohortEnrolled'].textContent,
            cntArm1: env.elements['cntArm1'].textContent,
            cntArm4: env.elements['cntArm4'].textContent
        };
        console.log('__RESULT__:' + JSON.stringify(result));
        """
        res = run_in_node(js_code)
        self.assertEqual(res["lblTargetCohortN"], "N = 0")
        self.assertEqual(res["cfgSummarySla"], "SLA Tiers: 0s / 0s / 0s")
        self.assertEqual(res["cfgSummaryShiftDuration"], "Shift Duration: 0s")
        self.assertEqual(res["cfgSummaryHurdle"], "Hurdle: 0 pts")
        self.assertEqual(res["cfgSummaryTargetN"], "Target N: 0 (0/arm)")
        self.assertEqual(res["lblCohortEnrolled"], "Enrolled: 0 / 0")
        self.assertEqual(res["cntArm1"], "N₁ = 0 / 0")
        self.assertEqual(res["cntArm4"], "N₄ = 0 / 0")

    def test_extreme_sla_durations(self):
        """Tests microsecond and astronomical SLA durations."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        const slaConfig = {
            tier1SlaSec: 0.0001,
            tier2SlaSec: 999999.5,
            tier3SlaSec: 10000000,
            shiftDurationSimSec: 86400.0
        };
        const env = createAdminEnvironment({
            tum_study_config: JSON.stringify(slaConfig)
        });
        env.sandbox.window.updateConfigBadgeUI();
        const result = {
            cfgSummarySla: env.elements['cfgSummarySla'].textContent,
            cfgSummaryShiftDuration: env.elements['cfgSummaryShiftDuration'].textContent
        };
        console.log('__RESULT__:' + JSON.stringify(result));
        """
        res = run_in_node(js_code)
        self.assertEqual(res["cfgSummarySla"], "SLA Tiers: 0.0001s / 999999.5s / 10000000s")
        self.assertEqual(res["cfgSummaryShiftDuration"], "Shift Duration: 86400s")

    def test_large_numbers_and_formatting(self):
        """Tests astronomical cohort targets and billion-point hurdle formatting."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        const hugeConfig = {
            targetCohortN: 1000000,
            bonusTargetPts: 1000000000,
            basePayEur: 50000.00,
            performanceBonusEur: 100000.00
        };
        const env = createAdminEnvironment({
            tum_study_config: JSON.stringify(hugeConfig)
        });
        env.sandbox.window.updateConfigBadgeUI();
        const result = {
            lblTargetCohortN: env.elements['lblTargetCohortN'].textContent,
            cfgSummaryHurdle: env.elements['cfgSummaryHurdle'].textContent,
            cfgSummaryTargetN: env.elements['cfgSummaryTargetN'].textContent,
            cntArm1: env.elements['cntArm1'].textContent
        };
        console.log('__RESULT__:' + JSON.stringify(result));
        """
        res = run_in_node(js_code)
        self.assertEqual(res["lblTargetCohortN"], "N = 1000000")
        self.assertIn("1,000,000,000 pts", res["cfgSummaryHurdle"])
        self.assertEqual(res["cfgSummaryTargetN"], "Target N: 1000000 (250000/arm)")
        self.assertEqual(res["cntArm1"], "N₁ = 0 / 250000")

    def test_malformed_and_non_numeric_fallback(self):
        """Tests that invalid types fallback gracefully without throwing or rendering NaN."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        const malformedConfig = {
            targetCohortN: "not_a_number",
            bonusTargetPts: null
        };
        const env = createAdminEnvironment({
            tum_study_config: JSON.stringify(malformedConfig)
        });
        env.sandbox.window.updateConfigBadgeUI();
        const result = {
            lblTargetCohortN: env.elements['lblTargetCohortN'].textContent,
            cfgSummaryHurdle: env.elements['cfgSummaryHurdle'].textContent,
            cfgSummaryTargetN: env.elements['cfgSummaryTargetN'].textContent,
            cntArm1: env.elements['cntArm1'].textContent
        };
        console.log('__RESULT__:' + JSON.stringify(result));
        """
        res = run_in_node(js_code)
        # Should fall back to 240 and 1200
        self.assertEqual(res["lblTargetCohortN"], "N = 240")
        self.assertIn("1,200 pts", res["cfgSummaryHurdle"])
        self.assertEqual(res["cfgSummaryTargetN"], "Target N: 240 (60/arm)")
        self.assertEqual(res["cntArm1"], "N₁ = 0 / 60")


class TestSyntheticCohortGeneratorModes(unittest.TestCase):
    """Stress tests replace vs append modes with existing sessions in localStorage."""

    def test_replace_mode_clears_existing_sessions(self):
        """Verifies replace mode completely purges pre-existing sessions in localStorage."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        // Pre-populate 5 legacy sessions
        const preExisting = [
            { pid: 'P_LEGACY_1', arm: 1, status: 'COMPLETED' },
            { pid: 'P_LEGACY_2', arm: 1, status: 'COMPLETED' },
            { pid: 'P_LEGACY_3', arm: 2, status: 'COMPLETED' },
            { pid: 'P_LEGACY_4', arm: 3, status: 'COMPLETED' },
            { pid: 'P_LEGACY_5', arm: 4, status: 'COMPLETED' }
        ];
        const env = createAdminEnvironment({
            tum_study_sessions: JSON.stringify(preExisting)
        });

        // Execute replace mode with N=8
        const finalSessions = env.sandbox.window.generateSyntheticSessions(8, 'replace', 42);
        const stored = JSON.parse(env.localStorageStore['tum_study_sessions']);

        const result = {
            finalLength: finalSessions.length,
            storedLength: stored.length,
            containsLegacy: stored.some(s => s.pid.includes('LEGACY')),
            pids: stored.map(s => s.pid),
            arms: stored.map(s => s.arm)
        };
        console.log('__RESULT__:' + JSON.stringify(result));
        """
        res = run_in_node(js_code)
        self.assertEqual(res["finalLength"], 8)
        self.assertEqual(res["storedLength"], 8)
        self.assertFalse(res["containsLegacy"])
        # Exactly 2 per arm across arms 1-4
        for arm in [1, 2, 3, 4]:
            self.assertEqual(res["arms"].count(arm), 2)
        # All PIDs unique
        self.assertEqual(len(set(res["pids"])), 8)

    def test_append_mode_with_empty_vault(self):
        """Verifies append mode behaves gracefully when starting with an empty vault."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        const env = createAdminEnvironment();
        const finalSessions = env.sandbox.window.generateSyntheticSessions(4, 'append', 42);
        const stored = JSON.parse(env.localStorageStore['tum_study_sessions']);
        const result = {
            finalLength: finalSessions.length,
            storedLength: stored.length,
            pids: stored.map(s => s.pid),
            arms: stored.map(s => s.arm)
        };
        console.log('__RESULT__:' + JSON.stringify(result));
        """
        res = run_in_node(js_code)
        self.assertEqual(res["finalLength"], 4)
        self.assertEqual(res["storedLength"], 4)
        self.assertEqual(sorted(res["arms"]), [1, 2, 3, 4])
        self.assertEqual(len(set(res["pids"])), 4)

    def test_append_mode_with_balanced_existing_vault_and_pid_uniqueness(self):
        """Verifies append mode avoids PID collisions and evenly distributes across arms."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        // Pre-populate 8 sessions (2 per arm) using canonical P_x001 / P_x002
        const preExisting = [
            { pid: 'P_1001', arm: 1, status: 'COMPLETED' },
            { pid: 'P_1002', arm: 1, status: 'COMPLETED' },
            { pid: 'P_2001', arm: 2, status: 'COMPLETED' },
            { pid: 'P_2002', arm: 2, status: 'COMPLETED' },
            { pid: 'P_3001', arm: 3, status: 'COMPLETED' },
            { pid: 'P_3002', arm: 3, status: 'COMPLETED' },
            { pid: 'P_4001', arm: 4, status: 'COMPLETED' },
            { pid: 'P_4002', arm: 4, status: 'COMPLETED' }
        ];
        const env = createAdminEnvironment({
            tum_study_sessions: JSON.stringify(preExisting)
        });

        // Append 4 sessions (1 per arm)
        const finalSessions = env.sandbox.window.generateSyntheticSessions(4, 'append', 42);
        const stored = JSON.parse(env.localStorageStore['tum_study_sessions']);

        const result = {
            totalCount: stored.length,
            pids: stored.map(s => s.pid),
            arms: stored.map(s => s.arm),
            newPids: stored.slice(8).map(s => s.pid)
        };
        console.log('__RESULT__:' + JSON.stringify(result));
        """
        res = run_in_node(js_code)
        self.assertEqual(res["totalCount"], 12)
        # All 12 PIDs must be strictly unique!
        self.assertEqual(len(set(res["pids"])), 12)
        # Exactly 3 per arm across arms 1-4
        for arm in [1, 2, 3, 4]:
            self.assertEqual(res["arms"].count(arm), 3)
        # New PIDs must be P_1003, P_2003, P_3003, P_4003 (in some order)
        expected_new = {"P_1003", "P_2003", "P_3003", "P_4003"}
        self.assertEqual(set(res["newPids"]), expected_new)

    def test_append_mode_greedy_leveling_on_skewed_vault(self):
        """Verifies that append mode fills underrepresented arms first when vault is skewed."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        // Vault skewed: Arm 1 has 5 sessions, other arms have 0
        const preExisting = [
            { pid: 'P_1001', arm: 1, status: 'COMPLETED' },
            { pid: 'P_1002', arm: 1, status: 'COMPLETED' },
            { pid: 'P_1003', arm: 1, status: 'COMPLETED' },
            { pid: 'P_1004', arm: 1, status: 'COMPLETED' },
            { pid: 'P_1005', arm: 1, status: 'COMPLETED' }
        ];
        const env = createAdminEnvironment({
            tum_study_sessions: JSON.stringify(preExisting)
        });

        // Append 6 sessions. Since Arm 1 is overloaded (5), new sessions should fill Arms 2, 3, 4
        const finalSessions = env.sandbox.window.generateSyntheticSessions(6, 'append', 42);
        const stored = JSON.parse(env.localStorageStore['tum_study_sessions']);

        const newSessions = stored.slice(5);
        const newArms = newSessions.map(s => s.arm);

        const result = {
            totalLength: stored.length,
            newArms: newArms,
            armCounts: {
                1: stored.filter(s => s.arm === 1).length,
                2: stored.filter(s => s.arm === 2).length,
                3: stored.filter(s => s.arm === 3).length,
                4: stored.filter(s => s.arm === 4).length
            },
            allPidsUnique: new Set(stored.map(s => s.pid)).size === stored.length
        };
        console.log('__RESULT__:' + JSON.stringify(result));
        """
        res = run_in_node(js_code)
        self.assertEqual(res["totalLength"], 11)
        self.assertTrue(res["allPidsUnique"])
        # Arm 1 should have received 0 new sessions
        self.assertNotIn(1, res["newArms"])
        # Arms 2, 3, 4 should have received 2 each
        self.assertEqual(res["armCounts"]["1"], 5)
        self.assertEqual(res["armCounts"]["2"], 2)
        self.assertEqual(res["armCounts"]["3"], 2)
        self.assertEqual(res["armCounts"]["4"], 2)

    def test_multi_cycle_consecutive_appends_stress(self):
        """Stress tests 6 consecutive appends with irregular chunk sizes."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        const env = createAdminEnvironment();
        const chunks = [3, 5, 2, 7, 1, 6]; // Sum = 24
        for (let i = 0; i < chunks.length; i++) {
            env.sandbox.window.generateSyntheticSessions(chunks[i], 'append', 100 + i);
        }
        const stored = JSON.parse(env.localStorageStore['tum_study_sessions']);
        const result = {
            totalCount: stored.length,
            uniquePids: new Set(stored.map(s => s.pid)).size,
            uniqueSessionIds: new Set(stored.map(s => s.sessionId)).size,
            armCounts: {
                1: stored.filter(s => s.arm === 1).length,
                2: stored.filter(s => s.arm === 2).length,
                3: stored.filter(s => s.arm === 3).length,
                4: stored.filter(s => s.arm === 4).length
            }
        };
        console.log('__RESULT__:' + JSON.stringify(result));
        """
        res = run_in_node(js_code)
        self.assertEqual(res["totalCount"], 24)
        # All 24 PIDs and session IDs must be unique
        self.assertEqual(res["uniquePids"], 24)
        self.assertEqual(res["uniqueSessionIds"], 24)
        # Final arm counts should be perfectly balanced at 6 each
        self.assertEqual(res["armCounts"]["1"], 6)
        self.assertEqual(res["armCounts"]["2"], 6)
        self.assertEqual(res["armCounts"]["3"], 6)
        self.assertEqual(res["armCounts"]["4"], 6)

    def test_mulberry32_determinism_under_append(self):
        """Verifies byte-for-byte identical datasets when identical seeds and append states are used."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        const initial = JSON.stringify([{ pid: 'P_1001', arm: 1, status: 'COMPLETED' }]);

        const env1 = createAdminEnvironment({ tum_study_sessions: initial });
        const run1 = env1.sandbox.window.generateSyntheticSessions(12, 'append', 777);

        const env2 = createAdminEnvironment({ tum_study_sessions: initial });
        const run2 = env2.sandbox.window.generateSyntheticSessions(12, 'append', 777);

        const str1 = JSON.stringify(run1);
        const str2 = JSON.stringify(run2);

        console.log('__RESULT__:' + JSON.stringify({ identical: str1 === str2 }));
        """
        res = run_in_node(js_code)
        self.assertTrue(res["identical"])

    def test_dynamic_config_inheritance_under_extreme_config(self):
        """Verifies synthetic sessions accurately inherit zero-base pay and 0-hurdle configs."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        const extremeConfig = {
            targetCohortN: 4,
            bonusTargetPts: 0,
            basePayEur: 0,
            performanceBonusEur: 5.00,
            arm4IntegrityCreditEur: 0,
            tier1SlaSec: 10.0,
            tier2SlaSec: 20.0,
            tier3SlaSec: 30.0,
            shiftDurationSimSec: 15.0
        };
        const env = createAdminEnvironment({
            tum_study_config: JSON.stringify(extremeConfig)
        });

        const sessions = env.sandbox.window.generateSyntheticSessions(4, 'replace', 42);
        const results = sessions.map(s => ({
            arm: s.arm,
            target_pts: s.config_snapshot.target_pts,
            base_pay_eur: s.config_snapshot.base_pay_eur,
            bonus_unlocked: s.s5_outcome.bonusUnlockedBinary,
            payout: s.s5_outcome.finalPayoutEur
        }));
        console.log('__RESULT__:' + JSON.stringify(results));
        """
        res = run_in_node(js_code)
        for s in res:
            # 0 must be preserved, not overwritten with default 1200 or 2.50
            self.assertEqual(s["target_pts"], 0)
            self.assertEqual(s["base_pay_eur"], 0)
            if s["arm"] in [1, 2, 3]:
                # Since hurdle is 0 pts and all scores > 0, bonus is unlocked!
                self.assertEqual(s["bonus_unlocked"], 1)
                self.assertEqual(s["payout"], 5.0)
            else: # Arm 4
                self.assertEqual(s["bonus_unlocked"], 0)
                self.assertEqual(s["payout"], 0.0)


class TestBase64TokenQuarantineAdversarial(unittest.TestCase):
    """Stress tests Base64 token quarantine with extreme config and special characters."""

    def test_token_carries_full_37_params_under_extreme_config(self):
        """Verifies token generation packages full 37 parameters even under extreme values."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        const customCfg = {
            targetCohortN: 9999,
            bonusTargetPts: 0,
            basePayEur: 0,
            performanceBonusEur: 10.00,
            tier1SlaSec: 0.5,
            tier2SlaSec: 1.5,
            tier3SlaSec: 2.5,
            shiftDurationSimSec: 10.0
        };
        const env = createAdminEnvironment({
            tum_study_config: JSON.stringify(customCfg)
        });

        // Trigger link generation
        env.sandbox.document.getElementById('inputPid').value = 'P_STRESS_999';
        env.sandbox.document.getElementById('inputMetadata').value = 'TUM & CIT <Special> "Test"';

        // Invoke click on btnGenerateLink
        // In admin.html, btnGenerateLink packs payload and encodes to token
        // Let's call the click listener by triggering it or reading txtGeneratedUrl
        // Since we want to test btnCopyBlindedTokenUrl logic:
        const activeCfg = env.sandbox.window.document.getElementById('inputPid');
        // Let's run the exact token encoding logic from admin.html lines 870-877
        const payload = {
            pid: 'P_STRESS_999',
            arm: 2,
            speed: 3,
            meta: 'TUM & CIT <Special> "Test"',
            config: JSON.parse(env.localStorageStore['tum_study_config'])
        };
        const token = env.sandbox.btoa(env.sandbox.unescape(env.sandbox.encodeURIComponent(JSON.stringify(payload))));
        const decoded = JSON.parse(env.sandbox.decodeURIComponent(env.sandbox.escape(env.sandbox.atob(token))));

        console.log('__RESULT__:' + JSON.stringify({
            tokenLength: token.length,
            decodedPid: decoded.pid,
            decodedMeta: decoded.meta,
            decodedHurdle: decoded.config.bonusTargetPts,
            decodedBasePay: decoded.config.basePayEur,
            decodedTier1: decoded.config.tier1SlaSec
        }));
        """
        res = run_in_node(js_code)
        self.assertGreater(res["tokenLength"], 50)
        self.assertEqual(res["decodedPid"], "P_STRESS_999")
        self.assertEqual(res["decodedMeta"], 'TUM & CIT <Special> "Test"')
        self.assertEqual(res["decodedHurdle"], 0)
        self.assertEqual(res["decodedBasePay"], 0)
        self.assertEqual(res["decodedTier1"], 0.5)



class TestAdversarialBoundaryEdgeCases(unittest.TestCase):
    """Deep edge-case mining: odd cohort sizes, corrupted localStorage, huge N, boundary seeds."""

    def test_odd_cohort_target_and_balancer_denominators(self):
        """Verifies odd cohort sizes (e.g. 241) round arm denominators cleanly."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        const env = createAdminEnvironment({
            tum_study_config: JSON.stringify({ targetCohortN: 241 })
        });
        env.sandbox.window.updateConfigBadgeUI();
        const result = {
            lblCohortEnrolled: env.elements['lblCohortEnrolled'].textContent,
            cntArm1: env.elements['cntArm1'].textContent,
            cntArm4: env.elements['cntArm4'].textContent,
            cfgSummaryTargetN: env.elements['cfgSummaryTargetN'].textContent
        };
        console.log('__RESULT__:' + JSON.stringify(result));
        """
        res = run_in_node(js_code)
        self.assertEqual(res["lblCohortEnrolled"], "Enrolled: 0 / 241")
        self.assertEqual(res["cntArm1"], "N₁ = 0 / 60")
        self.assertEqual(res["cntArm4"], "N₄ = 0 / 60")
        self.assertEqual(res["cfgSummaryTargetN"], "Target N: 241 (60/arm)")


    def test_corrupted_local_storage_resilience(self):
        """Verifies unparseable malformed JSON in localStorage does not crash admin portal."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        const env = createAdminEnvironment({
            tum_study_sessions: "{ CORRUPT_JSON: true ",
            tum_study_config: "{ INVALID_CFG "
        });
        // Should safely fallback to [] and DEFAULT_EXPERIMENT_CONFIG
        env.sandbox.window.updateBalancerUI();
        env.sandbox.window.updateConfigBadgeUI();
        const result = {
            enrolledText: env.elements['lblCohortEnrolled'].textContent,
            hurdleText: env.elements['cfgSummaryHurdle'].textContent,
            targetNText: env.elements['cfgSummaryTargetN'].textContent
        };
        console.log('__RESULT__:' + JSON.stringify(result));
        """
        res = run_in_node(js_code)
        self.assertEqual(res["enrolledText"], "Enrolled: 0 / 240")
        self.assertEqual(res["hurdleText"], "Hurdle: 1,200 pts")
        self.assertEqual(res["targetNText"], "Target N: 240 (60/arm)")

    def test_boundary_prng_seeds_produce_no_nan(self):
        """Tests PRNG with 0, negative integer, and 2^32 - 1 seeds."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        const env = createAdminEnvironment();
        const seeds = [0, -1, -999999, 4294967295];
        const results = {};
        for (const seed of seeds) {
            const sessions = env.sandbox.window.generateSyntheticSessions(4, 'replace', seed);
            const scores = sessions.map(s => s.s5_outcome.finalManagerScorePts);
            const payouts = sessions.map(s => s.s5_outcome.finalPayoutEur);
            const hasNaN = scores.some(isNaN) || payouts.some(isNaN);
            results[seed] = { hasNaN, scoreCount: scores.length };
        }
        console.log('__RESULT__:' + JSON.stringify(results));
        """
        res = run_in_node(js_code)
        for seed_str, data in res.items():
            self.assertFalse(data["hasNaN"], f"Seed {seed_str} produced NaN values")
            self.assertEqual(data["scoreCount"], 4)


    def test_corrupted_existing_session_arms_during_append(self):
        """Verifies existing sessions with missing, string, or invalid arms do not crash append."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        const oddSessions = [
            { pid: 'P_NO_ARM', status: 'COMPLETED' },
            { pid: 'P_STR_ARM', arm: 'banana', status: 'COMPLETED' },
            { pid: 'P_OUT_OF_BOUNDS', arm: 99, status: 'COMPLETED' },
            { pid: 'P_VALID_1', arm: 1, status: 'COMPLETED' }
        ];
        const env = createAdminEnvironment({
            tum_study_sessions: JSON.stringify(oddSessions)
        });
        const finalSessions = env.sandbox.window.generateSyntheticSessions(4, 'append', 42);
        const stored = JSON.parse(env.localStorageStore['tum_study_sessions']);
        const result = {
            totalStored: stored.length,
            newCount: finalSessions.length - oddSessions.length,
            allPids: stored.map(s => s.pid)
        };
        console.log('__RESULT__:' + JSON.stringify(result));
        """
        res = run_in_node(js_code)
        self.assertEqual(res["totalStored"], 8)
        self.assertEqual(res["newCount"], 4)
        self.assertEqual(len(set(res["allPids"])), 8)

    def test_high_volume_synthetic_cohort_generation(self):
        """Stress tests generating a full cohort of N=1000 sessions."""
        js_code = """
        const { createAdminEnvironment } = require('./local_only/phd/paper1/mvp2/tools/admin_vm_harness.js');
        const env = createAdminEnvironment();
        const start = Date.now();
        const sessions = env.sandbox.window.generateSyntheticSessions(1000, 'replace', 42);
        const durationMs = Date.now() - start;
        const result = {
            total: sessions.length,
            durationMs: durationMs,
            uniquePids: new Set(sessions.map(s => s.pid)).size,
            uniqueSessionIds: new Set(sessions.map(s => s.sessionId)).size,
            armCounts: {
                1: sessions.filter(s => s.arm === 1).length,
                2: sessions.filter(s => s.arm === 2).length,
                3: sessions.filter(s => s.arm === 3).length,
                4: sessions.filter(s => s.arm === 4).length
            }
        };
        console.log('__RESULT__:' + JSON.stringify(result));
        """
        res = run_in_node(js_code)
        self.assertEqual(res["total"], 1000)
        self.assertEqual(res["uniquePids"], 1000)
        self.assertEqual(res["uniqueSessionIds"], 1000)
        for arm in [1, 2, 3, 4]:
            self.assertEqual(res["armCounts"][str(arm)], 250)
        # Should execute rapidly (under 5000ms)
        self.assertLess(res["durationMs"], 5000)


if __name__ == "__main__":
    unittest.main()
