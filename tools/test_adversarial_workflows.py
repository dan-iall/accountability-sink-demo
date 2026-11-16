#!/usr/bin/env python3
"""
TUM CIT Research Lab — Milestone 3 Empirical Challenger Test Suite
Adversarially tests core experimental workflows and decision logic in index.html:
1. S1 Navigation & Dwell Accumulation (rapid back/forth Steps 2-6, additive dwell, Arm 3 step 6 restriction)
2. S1B Practice Case 2 Tab combinations matrix crossed with Quick Approve vs Escalate
3. S2A Policy Setup (zero pre-selection, disabled lock button until explicit choice)
4. S2B Shift 2 Directive A vs Directive B (floor continuity notice, 32 cases cumulative score)
5. Shift 3 Counter ('Cleared: ${cases} / 36 Cases' zero-spoiler denominator and 75% progress scaling up to crash)
6. Screen 4 Disciplinary Task (header 690 pts / 650 pts unselected, live score projection for Option 1 vs 2)
"""

import json
import os
import subprocess
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HARNESS_JS = os.path.join(BASE_DIR, "tools", "workflow_challenger_harness.js")

def call_harness(fn_name, kwargs):
    code = f"""
    const harness = require('{HARNESS_JS}');
    const result = harness.{fn_name}({json.dumps(kwargs)});
    console.log('__RESULT__:' + JSON.stringify(result));
    """
    proc = subprocess.run(["node", "-e", code], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Harness execution failed (code {proc.returncode}):\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")
    for line in proc.stdout.splitlines():
        if line.startswith("__RESULT__:"):
            return json.loads(line[len("__RESULT__:"):])
    raise ValueError(f"Could not find __RESULT__ in output: {proc.stdout}")


class TestS1NavigationAndDwell(unittest.TestCase):
    """Stress tests S1 stepper navigation and dwell time logging."""

    def test_s1_rapid_bidirectional_dwell_accumulation(self):
        """Simulates rapid back-and-forth navigation (Steps 2-6) and checks additive dwell time."""
        # Arm 3: 1 -> 2 -> 1 -> 2 -> 3 -> 2 -> 4 -> 3 -> 5 -> 4 -> 5 -> 6 -> 5 -> 6
        nav_steps = [2, 1, 2, 3, 2, 4, 3, 5, 4, 5, 6, 5, 6]
        step_dwell_ms = 350
        res = call_harness("runS1NavigationScenario", {
            "arm": 3,
            "navigationSteps": nav_steps,
            "timeDwellPerStepMs": step_dwell_ms
        })

        self.assertEqual(res["arm"], 3)
        self.assertEqual(res["finalStep"], 6)
        dwells = res["dwells"]

        # Expected visits count per step:
        # Step 1: initial (1), returned to once -> 2 dwells
        # Step 2: visited 3 times
        # Step 3: visited 2 times
        # Step 4: visited 2 times
        # Step 5: visited 3 times
        # Step 6: visited 1 time (before transition back to 5)
        total_transitions = len(nav_steps)
        expected_total_ms = total_transitions * step_dwell_ms

        total_accumulated_ms = sum(dwells.values())
        self.assertEqual(total_accumulated_ms, expected_total_ms,
                         f"Dwell accumulation dropped ms: got {total_accumulated_ms}, expected {expected_total_ms}")

        # Check that no step has negative dwell
        for k, v in dwells.items():
            self.assertGreaterEqual(v, 0, f"Negative dwell detected for {k}: {v}")
            self.assertIsInstance(v, (int, float))

    def test_s1_step6_functional_prevention_for_non_arm3(self):
        """Asserts non-Arm-3 participants (Arms 1, 2, 4) are strictly prevented from entering Step 6."""
        for test_arm in [1, 2, 4]:
            with self.subTest(arm=test_arm):
                res = call_harness("runS1NavigationScenario", {
                    "arm": test_arm,
                    "navigationSteps": [2, 3, 4, 5, 6, 6, 6],
                    "timeDwellPerStepMs": 200
                })

                # Assert functionally clamped to 5
                self.assertEqual(res["finalStep"], 5,
                                 f"Arm {test_arm} was able to reach Step {res['finalStep']}!")
                self.assertTrue(res["btnStep5NextHidden"], f"Arm {test_arm} has visible btnStep5Next!")
                self.assertFalse(res["btnS1CompleteHidden"], f"Arm {test_arm} does not show btnS1Complete!")

    def test_s1_step6_pill_visibility_for_non_arm3(self):
        """Asserts Step 6 pill is hidden for non-Arm-3 participants (reveals className overwrite bug)."""
        for test_arm in [1, 2, 4]:
            with self.subTest(arm=test_arm):
                res = call_harness("runS1NavigationScenario", {
                    "arm": test_arm,
                    "navigationSteps": [2, 3, 4, 5],
                    "timeDwellPerStepMs": 200
                })
                # Bug check: renderS1Step overwrites pill6.className in loop (s <= 6), stripping 'hidden'
                self.assertTrue(res["pill6Hidden"], f"Arm {test_arm} has visible Step 6 pill due to className overwrite!")

    def test_s1_extreme_step_clamping(self):
        """Asserts out-of-bounds targetStep values clamp properly."""
        # Arm 3: clamped between 1 and 6
        res_arm3 = call_harness("runS1NavigationScenario", {
            "arm": 3,
            "navigationSteps": [-10, 0, 999],
            "timeDwellPerStepMs": 100
        })
        self.assertEqual(res_arm3["finalStep"], 6)

        # Arm 1: clamped between 1 and 5
        res_arm1 = call_harness("runS1NavigationScenario", {
            "arm": 1,
            "navigationSteps": [-10, 0, 999],
            "timeDwellPerStepMs": 100
        })
        self.assertEqual(res_arm1["finalStep"], 5)


class TestS1BPracticeCase2TabMatrix(unittest.TestCase):
    """Stress tests Case 2 tab inspection matrix crossed with Quick Approve vs Escalate."""

    def test_case2_tab_matrix_and_action_branching(self):
        """Tests all combinations of tab openings crossed with Quick Approve vs Escalate."""
        test_sequences = [
            # (tab_sequence, expected_visited, expected_unopened, note_snippet)
            ([], [1], [2, 3], "(Pages 2 & 3 Unopened)"),
            ([2], [1, 2], [3], "(Page 3 Scale Log Unopened)"),
            ([3], [1, 3], [2], "(Page 2 Outbound Manifest Unopened)"),
            ([2, 3], [1, 2, 3], [], "(All 3 Pages Checked)"),
            ([3, 2], [1, 2, 3], [], "(All 3 Pages Checked)"),
            ([2, 1, 2], [1, 2], [3], "(Page 3 Scale Log Unopened)"),
            ([3, 1, 3], [1, 3], [2], "(Page 2 Outbound Manifest Unopened)")
        ]

        actions = ["QUICK_APPROVE", "ESCALATE"]

        for seq, exp_visited, exp_unopened, exp_note in test_sequences:
            for act in actions:
                with self.subTest(sequence=seq, action=act):
                    res = call_harness("runS1BCase2Scenario", {
                        "tabSequence": seq,
                        "action": act
                    })

                    self.assertEqual(res["case2ActionRecorded"], act)
                    self.assertEqual(res["visitedTabs"], exp_visited)
                    self.assertEqual(res["unopenedTabs"], exp_unopened)
                    self.assertEqual(res["visitedCount"], len(exp_visited))

                    m2 = res["m2"]

                    # Assert action branching is strict:
                    if act == "QUICK_APPROVE":
                        self.assertTrue(m2.startswith("Approved at "),
                                        f"QUICK_APPROVE failed to render approval prefix: {m2}")
                        self.assertNotIn("Held & Escalated", m2,
                                         f"QUICK_APPROVE mistakenly rendered as Held & Escalated: {m2}")
                    else: # ESCALATE
                        self.assertTrue(m2.startswith("Held & Escalated at "),
                                        f"ESCALATE failed to render escalation prefix: {m2}")
                        self.assertNotIn("Approved at ", m2,
                                         f"ESCALATE mistakenly rendered as Approved: {m2}")

                    # Assert unopened pages note:
                    self.assertIn(exp_note, m2,
                                  f"Expected note '{exp_note}' not found in scorecard text: {m2}")


class TestS2APolicySetup(unittest.TestCase):
    """Stress tests Screen 2A Policy Setup Cockpit and status-quo anti-nudge constraints."""

    def test_s2a_initial_unselected_state(self):
        """Verifies zero pre-selection, disabled lock button, and neutral prompt on initial load."""
        res = call_harness("runS2APolicyScenario", {
            "preClickAttempt": True,
            "selectedOption": None
        })

        init = res["initialState"]
        # 1. Zero pre-selected radio buttons
        self.assertFalse(init["radio1Checked"], "Radio 1 was pre-selected!")
        self.assertFalse(init["radio2Checked"], "Radio 2 was pre-selected!")
        self.assertFalse(init["radio3Checked"], "Radio 3 was pre-selected!")
        self.assertIsNone(init["selectedSlaSec"], "selectedSlaSec was pre-set!")

        # 2. Lock button disabled & unclickable
        self.assertTrue(init["btnDisabled"], "Lock button was not disabled on screen entry!")
        self.assertTrue(init["btnHasPointerEventsNone"], "Lock button missing pointer-events-none class!")
        self.assertTrue(init["btnHasOpacity50"], "Lock button missing opacity-50 class!")

        # 3. Projection empty notice visible and metrics grid hidden
        self.assertFalse(init["emptyNoticeHidden"], "Projection empty notice was hidden on load!")
        self.assertTrue(init["metricsGridHidden"], "Projection metrics grid was shown before selection!")
        self.assertIn("Select an operational pacing policy above", init["lblBonusText"])

        # 4. Attempting to click lock button without selection does NOT record policy
        self.assertFalse(res["preLockAttemptRecorded"],
                         "Locking succeeded without an option being selected!")
        self.assertIsNone(res["sessionInitialSlaSec"],
                          "initialSlaPreferenceSec was recorded without user selection!")

    def test_s2a_explicit_options_selection_and_locking(self):
        """Verifies unlocking upon selection of Option 1 (25s), Option 2 (38s), and Option 3 (60s)."""
        options_spec = [
            (1, 25.0, "SPEED_25S", False, "36 Cases Cleared", "+360 Pts", "[ QUOTA MET // €4.00 BONUS ELIGIBLE ]"),
            (2, 38.0, "STEWARD_38S", True, "24 Cases Cleared", "+240 Pts", "[ SUB-QUOTA // BONUS FORFEITED ]"),
            (3, 60.0, "COMPLIANT_60S", True, "15 Cases Cleared", "+150 Pts", "[ SUB-QUOTA // BONUS FORFEITED ]")
        ]

        for opt, exp_sec, exp_arch, exp_override, exp_cases, exp_pts, exp_bonus in options_spec:
            with self.subTest(option=opt):
                res = call_harness("runS2APolicyScenario", {
                    "preClickAttempt": False,
                    "selectedOption": opt
                })

                post = res["postSelectState"]
                self.assertTrue(post["radioChecked"], f"Radio {opt} was not checked!")
                self.assertEqual(post["selectedSlaSec"], exp_sec)
                self.assertEqual(post["selectedArchetype"], exp_arch)
                self.assertFalse(post["btnDisabled"], f"Lock button remained disabled after choosing option {opt}!")
                self.assertTrue(post["btnCursorPointer"])
                self.assertEqual(post["lblProjCasesText"], exp_cases)
                self.assertEqual(post["lblProjPtsText"], exp_pts)
                self.assertIn(exp_bonus, post["lblProjBonusText"])

                # Post-lock session values
                self.assertEqual(res["sessionInitialSlaSec"], exp_sec)
                policy = res["s2aPolicyRecorded"]
                self.assertEqual(policy["initialSlaPreferenceSec"], exp_sec)
                self.assertEqual(policy["initialSlaArchetype"], exp_arch)
                self.assertEqual(policy["corporateOverrideTriggered"], exp_override)
                self.assertEqual(policy["activeFloorSlaSec"], 25.0)


class TestS2BShift2DirectiveBranches(unittest.TestCase):
    """Stress tests Shift 2 Directive A vs Directive B execution and continuity notice."""

    def test_shift2_directive_a_pathway(self):
        """Directive A maintains standard pace (36 cases, +360 pts, 720 cum pts, no floor notice)."""
        res = call_harness("runS2BShift2Scenario", {"directive": "A"})

        self.assertEqual(res["casesCleared"], 36)
        self.assertEqual(res["shift2Pts"], 360)
        self.assertEqual(res["shift2DirectiveLogged"], "A_TRUST_AI")
        self.assertIn("Directive A: Standard Pace (25.0s)", res["lblDir"])
        self.assertEqual(res["lblPts"], "+360 Points")
        self.assertEqual(res["lblCum"], "720 Points")
        self.assertTrue(res["excStatusHidden"], "Directive A mistakenly displayed floor exception notice!")
        self.assertFalse(res["modalDoneHidden"])

    def test_shift2_directive_b_pathway(self):
        """Directive B authorizes manual exception (32 cases, +320 pts, 680 cum pts, floor continuity notice)."""
        res = call_harness("runS2BShift2Scenario", {"directive": "B"})

        self.assertEqual(res["casesCleared"], 32)
        self.assertEqual(res["shift2Pts"], 320)
        self.assertEqual(res["shift2DirectiveLogged"], "B_SLOW_FLOOR")
        self.assertIn("Directive B: Verification Exception (-40 pt variance)", res["lblDir"])
        self.assertEqual(res["lblPts"], "+320 Points")
        self.assertEqual(res["lblCum"], "680 Points")

        # Crucial floor continuity notice revealed
        self.assertFalse(res["excStatusHidden"], "Directive B failed to reveal floor continuity notice!")
        expected_notice = "Shift 2 Exception Status: Temporary Station 2 pacing exception concluded (+320 pts). Floor dispatch resets to the active 25.0s Corporate Baseline for Shift 3."
        self.assertIn(expected_notice, res["excStatusText"])


class TestShift3CounterAndCrash(unittest.TestCase):
    """Stress tests Shift 3 zero-spoiler live counter, progress scaling, and audit freeze."""

    def test_shift3_counter_and_progress_scaling(self):
        """Verifies denominator is always / 36 Cases, scales to 75% at case 27, and triggers freeze."""
        res = call_harness("runShift3CounterScenario", {})

        # 1. Initial zero-spoiler HUD
        self.assertEqual(res["initialText"], "Cleared: 0 / 36 Cases")
        self.assertEqual(res["initialWidth"], "0%")

        # 2. Check each snapshot
        for snap in res["snapshots"]:
            counter_text = snap["counterText"]
            # Assert denominator is strictly / 36 Cases, never / 27 Cases
            self.assertIn("/ 36 Cases", counter_text,
                          f"Live counter spoiled incident by altering denominator: {counter_text}")
            self.assertNotIn("/ 27 Cases", counter_text)

        # Final snapshot (after crash freeze at case 27)
        final_snap = res["snapshots"][-1]
        self.assertEqual(final_snap["casesCleared"], 27)
        self.assertEqual(final_snap["progressWidth"], "75%")
        self.assertEqual(final_snap["counterText"], "Cleared: 27 / 36 Cases")

        # 3. Crash modal & station 2 alert
        self.assertFalse(res["modalCrashHidden"], "Crash modal was not revealed at case 27!")
        self.assertEqual(res["st2BadgeText"], "AUDIT FREEZE")
        self.assertIn("animate-pulse", res["st2BadgeClass"])
        self.assertIn("Approved without Page 3 scale check under 25.0s timer!", res["st2QueueStatus"])
        self.assertNotIn("13.4s", res["st2QueueStatus"])

        # 4. Provisional hold points
        self.assertEqual(res["preCrashPts"], 270)
        self.assertEqual(res["provisionalHoldPts"], -300)


class TestScreen4DisciplinaryTask(unittest.TestCase):
    """Stress tests Screen 4 points balance and dynamic score projections under Directives A & B."""

    def test_screen4_unselected_header_balance(self):
        """Verifies unprojected balance upon entry (690 pts for Dir A, 650 pts for Dir B)."""
        # Directive A path
        res_a = call_harness("runScreen4DisciplinaryScenario", {
            "directive": "A",
            "task2Selection": None
        })
        unsel_a = res_a["unselectedState"]
        self.assertEqual(
            unsel_a["headerText"],
            "Current Balance: 690 pts (990 pts Accrued | -300 pt Provisional Hold Pending Ruling)"
        )
        self.assertEqual(unsel_a["liveScoreText"], "690 PTS (HOLD PENDING)")
        self.assertIn("Projected score: 1,250 pts", unsel_a["opt1SubBadgeText"])
        self.assertIn("Projected score: 950 pts", unsel_a["opt2SubBadgeText"])

        # Directive B path
        res_b = call_harness("runScreen4DisciplinaryScenario", {
            "directive": "B",
            "task2Selection": None
        })
        unsel_b = res_b["unselectedState"]
        self.assertEqual(
            unsel_b["headerText"],
            "Current Balance: 650 pts (950 pts Accrued | -300 pt Provisional Hold Pending Ruling)"
        )
        self.assertEqual(unsel_b["liveScoreText"], "650 PTS (HOLD PENDING)")
        self.assertIn("Projected score: 1,210 pts", unsel_b["opt1SubBadgeText"])
        self.assertIn("Projected score: 910 pts", unsel_b["opt2SubBadgeText"])

    def test_screen4_live_score_projection_option1_vs_option2(self):
        """Verifies live score projection updates upon choosing Option 1 vs Option 2."""
        # 1. Directive A + Option 1 (Scapegoat: 990 + 0 + 260 = 1,250)
        res_a_opt1 = call_harness("runScreen4DisciplinaryScenario", {
            "directive": "A",
            "task2Selection": 1
        })
        self.assertIn("Projected Score: 1250 pts (Meets 1,200 pt Bonus Hurdle)",
                      res_a_opt1["postTask2State"]["headerText"])
        self.assertEqual(res_a_opt1["postTask2State"]["liveScoreText"], "690 PTS (PROJ: 1250)")

        # 2. Directive A + Option 2 (Absorb: 990 - 300 + 260 = 950)
        res_a_opt2 = call_harness("runScreen4DisciplinaryScenario", {
            "directive": "A",
            "task2Selection": 2
        })
        self.assertIn("Projected Score: 950 pts (Below 1,200 pt Bonus Hurdle)",
                      res_a_opt2["postTask2State"]["headerText"])
        self.assertEqual(res_a_opt2["postTask2State"]["liveScoreText"], "690 PTS (PROJ: 950)")

        # 3. Directive B + Option 1 (Scapegoat: 950 + 0 + 260 = 1,210)
        res_b_opt1 = call_harness("runScreen4DisciplinaryScenario", {
            "directive": "B",
            "task2Selection": 1
        })
        self.assertIn("Projected Score: 1210 pts (Meets 1,200 pt Bonus Hurdle)",
                      res_b_opt1["postTask2State"]["headerText"])
        self.assertEqual(res_b_opt1["postTask2State"]["liveScoreText"], "650 PTS (PROJ: 1210)")

        # 4. Directive B + Option 2 (Absorb: 950 - 300 + 260 = 910)
        res_b_opt2 = call_harness("runScreen4DisciplinaryScenario", {
            "directive": "B",
            "task2Selection": 2
        })
        self.assertIn("Projected Score: 910 pts (Below 1,200 pt Bonus Hurdle)",
                      res_b_opt2["postTask2State"]["headerText"])
        self.assertEqual(res_b_opt2["postTask2State"]["liveScoreText"], "650 PTS (PROJ: 910)")

    def test_screen4_task4_points_stability(self):
        """Verifies Task 4 selection holds Shift 4 points at constant +260 pts (zero points leak)."""
        for reform_opt in [1, 2, 3]:
            with self.subTest(reform=reform_opt):
                res = call_harness("runScreen4DisciplinaryScenario", {
                    "directive": "A",
                    "task2Selection": 1,
                    "task4Selection": reform_opt
                })
                # Projected score remains 1,250 across all reform options
                self.assertIn("Projected Score: 1250 pts", res["postTask4State"]["headerText"])
                self.assertEqual(res["postTask4State"]["liveScoreText"], "690 PTS (PROJ: 1250)")


if __name__ == "__main__":
    unittest.main()
