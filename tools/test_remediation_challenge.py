#!/usr/bin/env python3
"""
HITL Accountability Study — Milestone 3 Iteration 2
Comprehensive Empirical Adversarial Remediation Challenge Suite
================================================================
Empirically verifies:
1. Step 6 pill visibility and stepping across Arms 1, 2, 3, 4
2. Partial & empty configuration safety across renderScreen4, renderScreen3, launchCase2
3. Screen 4 Task 2 dynamic hurdle forfeiture vs achievement
4. Screen 5 Arm 4 statutory audit reveal dynamic currency & zero leak of hardcoded literals
5. Screen 2A dynamic policy card & modal hydration
"""

import json
import os
import subprocess
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARNESS_PATH = os.path.join(BASE_DIR, "tools", "workflow_challenger_harness.js")

def run_in_harness(js_code, custom_cfg=None, session_overrides=None, state_overrides=None):
    """Executes arbitrary JS inside the audited workflow challenger harness VM environment."""
    cfg_json = json.dumps(custom_cfg) if custom_cfg is not None else "null"
    sess_json = json.dumps(session_overrides) if session_overrides is not None else "{}"
    state_json = json.dumps(state_overrides) if state_overrides is not None else "{}"

    wrapper = f"""
    const vm = require('vm');
    const harness = require({json.dumps(HARNESS_PATH)});
    const h = harness.createHarnessContext();
    const state = vm.runInContext('state', h.context);
    h.context.initSession();

    const customCfg = {cfg_json};
    if (customCfg !== null) {{
      state.config = customCfg;
    }}
    const sessOverrides = {sess_json};
    Object.assign(state.session, sessOverrides);
    const stOverrides = {state_json};
    Object.assign(state, stOverrides);

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


class TestRemediationVectors(unittest.TestCase):

    def test_vector_1_step6_pill_visibility_all_arms(self):
        """
        Vector 1: Empirically verify Step 6 pill visibility across all 4 arms.
        Arm 1, 2, 4 must strictly hide #s1PillStep6 across all steps 1-5.
        Arm 3 must strictly show #s1PillStep6 (never hidden).
        """
        for arm in [1, 2, 3, 4]:
            for step in range(1, 6):
                code = f"""
                state.session.arm = {arm};
                state.currentS1Step = {step};
                h.context.renderS1Step();
                const pill6 = h.getElement('s1PillStep6');
                const btnStep5Next = h.getElement('btnStep5Next');
                const btnS1Complete = h.getElement('btnS1Complete');
                return {{
                  arm: {arm},
                  step: {step},
                  pill6Hidden: pill6.classList.contains('hidden'),
                  pill6Classes: pill6.className,
                  btnStep5NextHidden: btnStep5Next.classList.contains('hidden'),
                  btnS1CompleteHidden: btnS1Complete.classList.contains('hidden')
                }};
                """
                res = run_in_harness(code)
                if arm in [1, 2, 4]:
                    self.assertTrue(
                        res["pill6Hidden"],
                        f"Arm {arm} Step {step} leaked #s1PillStep6: classes='{res['pill6Classes']}'"
                    )
                    # When on Step 5, ensure Arm 1, 2, 4 show Complete button and hide Next button
                    if step == 5:
                        self.assertTrue(res["btnStep5NextHidden"], f"Arm {arm} Step 5 showed btnStep5Next")
                        self.assertFalse(res["btnS1CompleteHidden"], f"Arm {arm} Step 5 hid btnS1Complete")
                else:  # Arm 3
                    self.assertFalse(
                        res["pill6Hidden"],
                        f"Arm 3 Step {step} unexpectedly hid #s1PillStep6"
                    )
                    if step == 5:
                        self.assertFalse(res["btnStep5NextHidden"], "Arm 3 Step 5 hid btnStep5Next")
                        self.assertTrue(res["btnS1CompleteHidden"], "Arm 3 Step 5 showed btnS1Complete")

    def test_vector_2_partial_and_empty_config_safety(self):
        """
        Vector 2: Stress-test partial and empty configurations to confirm
        renderScreen4, renderScreen3, and launchCase2 never throw TypeError.
        """
        test_configs = [
            ("partial_bonus_only", {"bonusTargetPts": 1450}),
            ("partial_base_pay_only", {"basePayEur": 3.00}),
            ("partial_sla1_only", {"tier1SlaSec": 20.0}),
            ("empty_object", {}),
            ("null_config", None),
        ]

        for cfg_name, test_cfg in test_configs:
            code = f"""
            const results = {{}};
            try {{
              state.config = {json.dumps(test_cfg)};
              h.context.renderScreen4();
              results.renderScreen4 = {{ success: true }};
            }} catch (e) {{
              results.renderScreen4 = {{ success: false, error: e.message }};
            }}

            try {{
              state.config = {json.dumps(test_cfg)};
              h.context.renderScreen3();
              results.renderScreen3 = {{ success: true }};
            }} catch (e) {{
              results.renderScreen3 = {{ success: false, error: e.message }};
            }}

            try {{
              state.config = {json.dumps(test_cfg)};
              h.context.launchCase2();
              results.launchCase2 = {{ success: true }};
            }} catch (e) {{
              results.launchCase2 = {{ success: false, error: e.message }};
            }}
            return results;
            """
            res = run_in_harness(code)
            self.assertTrue(
                res["renderScreen4"]["success"],
                f"renderScreen4 crashed under {cfg_name}: {res['renderScreen4'].get('error')}"
            )
            self.assertTrue(
                res["renderScreen3"]["success"],
                f"renderScreen3 crashed under {cfg_name}: {res['renderScreen3'].get('error')}"
            )
            self.assertTrue(
                res["launchCase2"]["success"],
                f"launchCase2 crashed under {cfg_name}: {res['launchCase2'].get('error')}"
            )

    def test_vector_3_task2_hurdle_bonus_forfeiture_vs_achievement(self):
        """
        Vector 3: Empirically verify #t2Opt1SubBadge and #t2Opt2SubBadge
        accurately compute forfeiture vs achievement against active bonusTargetPts.
        """
        scenarios = [
            # directive, hurdle, base, bonus, exp_opt1_achieved, exp_opt2_achieved
            ("DIRECTIVE_A", 1450, 3.25, 4.75, False, False), # 1250 < 1450, 950 < 1450
            ("DIRECTIVE_A", 1200, 2.50, 4.00, True, False),  # 1250 >= 1200, 950 < 1200
            ("DIRECTIVE_B", 1200, 2.50, 4.00, True, False),  # 1210 >= 1200, 910 < 1200
            ("DIRECTIVE_B", 1250, 2.50, 4.00, False, False), # 1210 < 1250, 910 < 1250
            ("DIRECTIVE_A", 1250, 3.00, 5.00, True, False),  # 1250 == 1250 (exact boundary)
            ("DIRECTIVE_A", 900,  3.00, 5.00, True, True),   # 1250 >= 900, 950 >= 900
        ]

        for directive, hurdle, base, bonus, exp1, exp2 in scenarios:
            custom_cfg = {
                "bonusTargetPts": hurdle,
                "basePayEur": base,
                "performanceBonusEur": bonus
            }
            code = f"""
            state.session.s2b_shifts = {{ shift2Directive: '{directive}' }};
            h.context.renderScreen4();
            const sb1 = h.getElement('t2Opt1SubBadge');
            const sb2 = h.getElement('t2Opt2SubBadge');
            return {{
              sb1Text: sb1 ? sb1.textContent : '',
              sb2Text: sb2 ? sb2.textContent : ''
            }};
            """
            res = run_in_harness(code, custom_cfg=custom_cfg)
            sb1 = res["sb1Text"]
            sb2 = res["sb2Text"]

            if exp1:
                self.assertIn("bonus achieved", sb1)
                self.assertNotIn("bonus forfeited", sb1)
            else:
                self.assertIn("bonus forfeited", sb1)
                self.assertNotIn("bonus achieved", sb1)
                self.assertIn(f"€{base:.2f} base fee only", sb1)

            if exp2:
                self.assertIn("bonus achieved", sb2)
                self.assertNotIn("bonus forfeited", sb2)
            else:
                self.assertIn("bonus forfeited", sb2)
                self.assertNotIn("bonus achieved", sb2)
                self.assertIn(f"€{base:.2f} base fee only", sb2)

    def test_vector_4_arm4_reveal_currency_interpolation_and_zero_leaks(self):
        """
        Vector 4: Empirically verify #s5Arm4Reveal under custom currency profile
        (base=3.25, bonus=4.75, credit=1.50) renders exact math and leaks ZERO literals.
        """
        custom_cfg = {
            "basePayEur": 3.25,
            "performanceBonusEur": 4.75,
            "arm4IntegrityCreditEur": 1.50
        }
        forbidden_literals = ["€4.00", "€2.50", "€3.50", "€1.00", "+€1.00", "€6.50"]

        # 4A: Penalize Sara Branch (Scapegoat)
        code_penalize = """
        state.session.arm = 4;
        state.session.s2b_shifts = { shift1Pts: 360, shift2Directive: 'DIRECTIVE_A', shift2Pts: 360, shift3PreCrashPts: 270 };
        state.session.s4_board_report = { Task2_Penalize_Sara_Binary: 1, task4_sla_reform_sec: 25.0 };
        h.context.renderScreen5();
        const arm4Box = h.getElement('s5Arm4Reveal');
        return {
          hidden: arm4Box.classList.contains('hidden'),
          html: arm4Box.innerHTML
        };
        """
        res_penalize = run_in_harness(code_penalize, custom_cfg=custom_cfg)
        self.assertFalse(res_penalize["hidden"], "Arm 4 reveal hidden under Arm 4 Penalize Sara")
        html_p = res_penalize["html"]
        self.assertIn("€4.75", html_p, "Arm 4 Scapegoat must interpolate bonus €4.75")
        self.assertIn("€3.25", html_p, "Arm 4 Scapegoat must interpolate base €3.25")
        for lit in forbidden_literals:
            self.assertNotIn(lit, html_p, f"Arm 4 Scapegoat leaked hardcoded literal {lit}!")

        # 4B: Absorb Blame Branch (Integrity)
        code_absorb = """
        state.session.arm = 4;
        state.session.s2b_shifts = { shift1Pts: 360, shift2Directive: 'DIRECTIVE_A', shift2Pts: 360, shift3PreCrashPts: 270 };
        state.session.s4_board_report = { Task2_Penalize_Sara_Binary: 0, task4_sla_reform_sec: 25.0 };
        h.context.renderScreen5();
        const arm4Box = h.getElement('s5Arm4Reveal');
        return {
          hidden: arm4Box.classList.contains('hidden'),
          html: arm4Box.innerHTML
        };
        """
        res_absorb = run_in_harness(code_absorb, custom_cfg=custom_cfg)
        self.assertFalse(res_absorb["hidden"], "Arm 4 reveal hidden under Arm 4 Absorb Blame")
        html_a = res_absorb["html"]
        self.assertIn("+€1.50", html_a, "Arm 4 Absorb must interpolate integrity credit +€1.50")
        self.assertIn("€4.75 EUR (€3.25 Base + €1.50 Integrity Credit)", html_a, "Arm 4 total payout must be €4.75")
        for lit in forbidden_literals:
            self.assertNotIn(lit, html_a, f"Arm 4 Absorb leaked hardcoded literal {lit}!")

        # 4C: Non-Arm-4 arms must hide #s5Arm4Reveal
        for test_arm in [1, 2, 3]:
            code_other = f"""
            state.session.arm = {test_arm};
            state.session.s2b_shifts = {{ shift1Pts: 360, shift2Directive: 'DIRECTIVE_A', shift2Pts: 360, shift3PreCrashPts: 270 }};
            state.session.s4_board_report = {{ Task2_Penalize_Sara_Binary: 1, task4_sla_reform_sec: 25.0 }};
            h.context.renderScreen5();
            const arm4Box = h.getElement('s5Arm4Reveal');
            return {{
              hidden: arm4Box.classList.contains('hidden'),
              html: arm4Box.innerHTML
            }};
            """
            res_other = run_in_harness(code_other, custom_cfg=custom_cfg)
            self.assertTrue(res_other["hidden"], f"Arm {test_arm} failed to hide #s5Arm4Reveal")
            self.assertEqual(res_other["html"], "", f"Arm {test_arm} has non-empty #s5Arm4Reveal")

    def test_vector_5_screen2a_and_modals_dynamic_hydration(self):
        """
        Vector 5: Verify that hydrateConfigUI dynamically populates Screen 2A
        policy cards, specialist windows, and shift completion modals.
        """
        custom_cfg = {
            "basePayEur": 3.25,
            "performanceBonusEur": 4.75,
            "bonusTargetPts": 1450,
            "tier1SlaSec": 22.0,
            "tier2SlaSec": 35.0,
            "tier3SlaSec": 55.0
        }
        code = """
        h.context.hydrateConfigUI(state.config);
        return {
          c1Bonus: h.getElement('s2aCard1BonusPay')?.textContent,
          c1Total: h.getElement('s2aCard1TotalPay')?.textContent,
          c1Badge: h.getElement('s2aCard1BadgeBonus')?.textContent,
          c1Win: h.getElement('s2aCard1Window')?.textContent,
          c2Loss: h.getElement('s2aCard2BonusLoss')?.textContent,
          c2Base: h.getElement('s2aCard2BaseOnly')?.textContent,
          c2Win: h.getElement('s2aCard2Window')?.textContent,
          c3Loss: h.getElement('s2aCard3BonusLoss')?.textContent,
          c3Base: h.getElement('s2aCard3BaseOnly')?.textContent,
          c3Win: h.getElement('s2aCard3Window')?.textContent,
          m1BonusEur: h.getElement('m1BonusEur')?.textContent,
          m1Hurdle: h.getElement('m1BonusHurdle')?.textContent,
          m2ResetSec: h.getElement('shift2ExceptionResetSec')?.textContent,
          m2BonusEur: h.getElement('m2BonusEur')?.textContent
        };
        """
        res = run_in_harness(code, custom_cfg=custom_cfg)
        self.assertEqual(res["c1Bonus"], "€4.75")
        self.assertEqual(res["c1Total"], "€8.00")
        self.assertEqual(res["c1Badge"], "€4.75")
        self.assertEqual(res["c1Win"], "22.0s / ticket")
        self.assertEqual(res["c2Loss"], "€4.75")
        self.assertEqual(res["c2Base"], "€3.25")
        self.assertEqual(res["c2Win"], "35.0s / ticket")
        self.assertEqual(res["c3Loss"], "€4.75")
        self.assertEqual(res["c3Base"], "€3.25")
        self.assertEqual(res["c3Win"], "55.0s / ticket")
        self.assertEqual(res["m1BonusEur"], "€4.75")
        self.assertEqual(res["m1Hurdle"], "1,450")
        self.assertEqual(res["m2ResetSec"], "22.0s")
        self.assertEqual(res["m2BonusEur"], "€4.75")


if __name__ == '__main__':
    unittest.main()
