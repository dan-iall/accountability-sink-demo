#!/usr/bin/env python3
"""
HITL ACCOUNTABILITY STUDY — ADVERSARIAL DYNAMIC CONFIGURATION & TELEMETRY STRESS SUITE
=============================================================================
Milestone 3 Empirical Verification Harness.
Adversarially tests Option B Dynamic Configuration Binding in index.html:
1. Custom, non-default experiment configs (hurdle=1450, base=3.25, bonus=4.75, credit=1.50, SLAs=22/35/55)
2. Format and display across all 14 dynamic span elements without default leaks
3. calculateFinalOutcome() math and bonus qualification with custom thresholds
4. Screen 5 compensation ledger reactivity
5. Edge conditions: 99,999 hurdle, zero base/bonus, missing/undefined config keys
"""

import json
import os
import subprocess
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "index.html")

CUSTOM_CONFIG = {
    "bonusTargetPts": 1450,
    "basePayEur": 3.25,
    "performanceBonusEur": 4.75,
    "arm4IntegrityCreditEur": 1.50,
    "tier1SlaSec": 22.0,
    "tier2SlaSec": 35.0,
    "tier3SlaSec": 55.0,
    "shiftDurationSimSec": 20.0,
    "minJustificationChars": 40
}

def run_in_simulated_dom(js_snippet, custom_cfg=None, state_overrides=None, session_overrides=None):
    """
    Executes a JavaScript snippet inside a simulated browser DOM containing the real
    index.html script logic, with configurable state, DOM elements, and custom config.
    """
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Extract the main script from index.html (between <script> and </script> after Tailwind)
    script_match = html_content.split('<script>')[-1].rsplit('</script>', 1)[0]

    cfg_json = json.dumps(custom_cfg) if custom_cfg is not None else "null"
    state_json = json.dumps(state_overrides) if state_overrides is not None else "{}"
    sess_json = json.dumps(session_overrides) if session_overrides is not None else "{}"

    runner_script = f"""
    const fs = require('fs');
    const html = fs.readFileSync({json.dumps(INDEX_PATH)}, 'utf-8');

    // Simple simulated DOM Element
    class MockElement {{
      constructor(id, tag = 'div') {{
        this.id = id;
        this.tagName = tag.toUpperCase();
        this.textContent = '';
        this.innerHTML = '';
        this.className = '';
        this.classList = {{
          _classes: new Set(),
          add: (...cls) => cls.forEach(c => this.classList._classes.add(c)),
          remove: (...cls) => cls.forEach(c => this.classList._classes.delete(c)),
          contains: (c) => this.classList._classes.has(c),
          toggle: (c) => this.classList.contains(c) ? this.classList.remove(c) : this.classList.add(c)
        }};
        this.style = {{
          setProperty: (k, v) => {{ this.style[k] = v; }},
          getPropertyValue: (k) => this.style[k] || ''
        }};
        this.disabled = false;
        this.checked = false;
        this.value = '';
      }}
    }}

    // Parse all element IDs from index.html
    const elementsById = {{}};
    const idRegex = /\\sid=["']([^"']+)["']/g;
    let m;
    while ((m = idRegex.exec(html)) !== null) {{
      const id = m[1];
      if (!elementsById[id]) {{
        elementsById[id] = new MockElement(id);
      }}
    }}

    const vm = require('vm');
    const storage = {{}};
    const sandbox = {{
      console: console,
      Date: Date,
      Math: Math,
      parseInt: parseInt,
      parseFloat: parseFloat,
      isNaN: isNaN,
      Number: Number,
      String: String,
      Object: Object,
      Array: Array,
      Set: Set,
      Map: Map,
      JSON: JSON,
      URLSearchParams: URLSearchParams,
      localStorage: {{
        getItem: (k) => storage[k] || null,
        setItem: (k, v) => {{ storage[k] = String(v); }},
        removeItem: (k) => {{ delete storage[k]; }},
        clear: () => {{ Object.keys(storage).forEach(k => delete storage[k]); }}
      }},
      sessionStorage: {{
        getItem: (k) => storage[k] || null,
        setItem: (k, v) => {{ storage[k] = String(v); }},
        removeItem: (k) => {{ delete storage[k]; }},
        clear: () => {{ Object.keys(storage).forEach(k => delete storage[k]); }}
      }},
      document: {{
        title: '',
        getElementById: (id) => elementsById[id] || null,
        querySelectorAll: () => [],
        querySelector: (sel) => null,
        createElement: (tag) => new MockElement('mock-' + Date.now(), tag),
        addEventListener: () => {{}},
        removeEventListener: () => {{}},
        body: new MockElement('appBody', 'body')
      }},
      window: {{
        location: {{ search: '', pathname: '/index.html' }},
        history: {{ replaceState: () => {{}} }},
        addEventListener: () => {{}}
      }},
      navigator: {{ clipboard: {{ writeText: async () => {{}} }} }}
    }};
    sandbox.window.document = sandbox.document;
    sandbox.global = sandbox;
    sandbox.window.window = sandbox.window;

    vm.createContext(sandbox);

    // 1. Load the script from index.html into sandbox
    vm.runInContext({json.dumps(script_match)}, sandbox);

    // 2. Set overrides in sandbox
    const customConfigInput = {cfg_json};
    const stateOverrides = {state_json};
    const sessionOverrides = {sess_json};

    sandbox.__customConfigInput = customConfigInput;
    sandbox.__stateOverrides = stateOverrides;
    sandbox.__sessionOverrides = sessionOverrides;

    vm.runInContext(`
      if (__customConfigInput !== null) {{
        state.config = Object.assign({{}}, __customConfigInput);
      }}
      if (__stateOverrides) {{
        Object.assign(state, __stateOverrides);
      }}
      if (__sessionOverrides && Object.keys(__sessionOverrides).length > 0) {{
        if (!state.session) state.session = {{}};
        Object.assign(state.session, __sessionOverrides);
      }}
    `, sandbox);

    // 3. User snippet execution
    const __result = vm.runInContext(`(function() {{
      {js_snippet}
    }})()`, sandbox);

    console.log("__JSON_OUTPUT__:" + JSON.stringify(__result));
    """

    res = subprocess.run(["node", "-e", runner_script], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Node execution failed with code {res.returncode}:\nSTDERR:\n{res.stderr}\nSTDOUT:\n{res.stdout}")

    for line in res.stdout.splitlines():
        if line.startswith("__JSON_OUTPUT__:"):
            return json.loads(line[len("__JSON_OUTPUT__:"):])

    raise RuntimeError(f"Did not find __JSON_OUTPUT__ in stdout:\n{res.stdout}\nSTDERR:\n{res.stderr}")

class TestDynamicSpanHydration(unittest.TestCase):
    """Verifies that all 14 dynamic span elements reflect custom configs without default leaks."""

    def test_all_14_spans_reflect_custom_config(self):
        snippet = """
        hydrateConfigUI(state.config);

        const ids = [
          'hudBonusHurdle', 's1Step5BonusHurdle', 's1Step5BasePay', 's1Step5BonusPay',
          's1Step5TotalPay', 's1Step5TargetPayoutLabel', 's1Step5PenaltyBonusLoss',
          's1Step5PenaltyBaseOnly', 's1Step5SubQuotaPayoutLabel', 's2aOpt1SlaSec',
          's2aOpt2SlaSec', 's2aOpt3SlaSec', 's2bHudHurdle', 's2bHudBonusEur'
        ];

        const output = {};
        ids.forEach(id => {
          const el = document.getElementById(id);
          output[id] = el ? el.textContent : null;
        });
        return output;
        """
        res = run_in_simulated_dom(snippet, custom_cfg=CUSTOM_CONFIG)

        self.assertEqual(res['hudBonusHurdle'], '1,450')
        self.assertEqual(res['s1Step5BonusHurdle'], '1,450')
        self.assertEqual(res['s1Step5BasePay'], '€3.25')
        self.assertEqual(res['s1Step5BonusPay'], '€4.75')
        self.assertEqual(res['s1Step5TotalPay'], '€8.00')
        self.assertEqual(res['s1Step5TargetPayoutLabel'], '€8.00 EUR (€3.25 Base + €4.75 Bonus)')
        self.assertEqual(res['s1Step5PenaltyBonusLoss'], '€4.75')
        self.assertEqual(res['s1Step5PenaltyBaseOnly'], '€3.25')
        self.assertEqual(res['s1Step5SubQuotaPayoutLabel'], '€3.25 EUR (Guaranteed Base Only)')
        self.assertEqual(res['s2aOpt1SlaSec'], '22.0s Target')
        self.assertEqual(res['s2aOpt2SlaSec'], '35.0s Standard Pace')
        self.assertEqual(res['s2aOpt3SlaSec'], '55.0s Extended Pace')
        self.assertEqual(res['s2bHudHurdle'], '1,450')
        self.assertEqual(res['s2bHudBonusEur'], '€4.75')

    def test_no_hardcoded_defaults_leak_in_spans(self):
        snippet = """
        hydrateConfigUI(state.config);
        const ids = [
          'hudBonusHurdle', 's1Step5BonusHurdle', 's1Step5BasePay', 's1Step5BonusPay',
          's1Step5TotalPay', 's1Step5TargetPayoutLabel', 's1Step5PenaltyBonusLoss',
          's1Step5PenaltyBaseOnly', 's1Step5SubQuotaPayoutLabel', 's2aOpt1SlaSec',
          's2aOpt2SlaSec', 's2aOpt3SlaSec', 's2bHudHurdle', 's2bHudBonusEur'
        ];
        const texts = ids.map(id => document.getElementById(id)?.textContent || '');
        return texts.join(' || ');
        """
        combined = run_in_simulated_dom(snippet, custom_cfg=CUSTOM_CONFIG)
        defaults_to_check = ['1,200', '€2.50', '€4.00', '€6.50', '25.0s', '38.0s', '60.0s']
        for d in defaults_to_check:
            self.assertNotIn(d, combined, f"Leaked hardcoded default '{d}' in dynamic spans after hydration!")

class TestCalculateFinalOutcome(unittest.TestCase):
    """Verifies that calculateFinalOutcome() accurately uses custom financial stakes and bonus thresholds."""

    def test_arms_1_to_3_bonus_qualification_under_custom_hurdle(self):
        # With Dir A, Scapegoat (Task 2 Option 1), Shift 4 standard (260 pts):
        # finalScore = 360 + 360 + 270 - 300 + 300 + 260 = 1250 pts.
        # Under CUSTOM_CONFIG, bonusTargetPts = 1450.
        # Therefore: 1250 < 1450 => bonus is NOT unlocked!
        snippet = """
        state.session = {
          arm: 1,
          s2b_shifts: { shift1Pts: 360, shift2Directive: 'DIRECTIVE_A', shift2Pts: 360, shift3PreCrashPts: 270 },
          s4_board_report: { Task2_Penalize_Sara_Binary: 1, task4_sla_reform_sec: 25.0 }
        };
        return calculateFinalOutcome();
        """
        outcome = run_in_simulated_dom(snippet, custom_cfg=CUSTOM_CONFIG)
        self.assertEqual(outcome['finalScore'], 1250)
        self.assertEqual(outcome['bonusUnlocked'], 0, "Bonus must NOT be unlocked when 1250 < 1450 hurdle!")
        self.assertEqual(outcome['finalPayout'], 3.25, "Payout must equal basePayEur when bonus is missed!")

    def test_arms_1_to_3_bonus_unlocked_when_score_meets_custom_hurdle(self):
        # Now set hurdle = 1200 (or 1100). Score 1250 >= 1200 => bonus unlocked!
        # Payout should be basePayEur (3.25) + performanceBonusEur (4.75) = 8.00 EUR.
        cfg = dict(CUSTOM_CONFIG)
        cfg['bonusTargetPts'] = 1200
        snippet = """
        state.session = {
          arm: 2,
          s2b_shifts: { shift1Pts: 360, shift2Directive: 'DIRECTIVE_A', shift2Pts: 360, shift3PreCrashPts: 270 },
          s4_board_report: { Task2_Penalize_Sara_Binary: 1, task4_sla_reform_sec: 25.0 }
        };
        return calculateFinalOutcome();
        """
        outcome = run_in_simulated_dom(snippet, custom_cfg=cfg)
        self.assertEqual(outcome['finalScore'], 1250)
        self.assertEqual(outcome['bonusUnlocked'], 1, "Bonus MUST be unlocked when 1250 >= 1200!")
        self.assertEqual(outcome['finalPayout'], 8.00, "Payout must equal base (3.25) + bonus (4.75) = 8.00!")

    def test_arm_4_integrity_credit_and_revocation_under_custom_config(self):
        # Arm 4 - Penalize Sara: bonus revoked, integrity credit 0, final payout = basePayEur (3.25)
        snippet_penalize = """
        state.session = {
          arm: 4,
          s2b_shifts: { shift1Pts: 360, shift2Directive: 'DIRECTIVE_A', shift2Pts: 360, shift3PreCrashPts: 270 },
          s4_board_report: { Task2_Penalize_Sara_Binary: 1, task4_sla_reform_sec: 25.0 }
        };
        return calculateFinalOutcome();
        """
        out_penalize = run_in_simulated_dom(snippet_penalize, custom_cfg=CUSTOM_CONFIG)
        self.assertEqual(out_penalize['bonusUnlocked'], 0)
        self.assertEqual(out_penalize['integrityCredit'], 0)
        self.assertEqual(out_penalize['finalPayout'], 3.25)

        # Arm 4 - Absorb Blame: integrity credit 1, final payout = basePayEur (3.25) + arm4IntegrityCreditEur (1.50) = 4.75
        snippet_absorb = """
        state.session = {
          arm: 4,
          s2b_shifts: { shift1Pts: 360, shift2Directive: 'DIRECTIVE_A', shift2Pts: 360, shift3PreCrashPts: 270 },
          s4_board_report: { Task2_Penalize_Sara_Binary: 0, task4_sla_reform_sec: 25.0 }
        };
        return calculateFinalOutcome();
        """
        out_absorb = run_in_simulated_dom(snippet_absorb, custom_cfg=CUSTOM_CONFIG)
        self.assertEqual(out_absorb['bonusUnlocked'], 0)
        self.assertEqual(out_absorb['integrityCredit'], 1)
        self.assertEqual(out_absorb['finalPayout'], 4.75)

class TestScreen5LedgerAndArm4Reveal(unittest.TestCase):
    """Verifies Screen 5 compensation ledger and inspects Arm 4 reveal for hardcoded leaks."""

    def test_screen5_ledger_breakdown_text_reactive(self):
        snippet = """
        state.session = {
          pid: 'P_TEST',
          arm: 1,
          s2b_shifts: { shift1Pts: 360, shift2Directive: 'DIRECTIVE_A', shift2Pts: 360, shift3PreCrashPts: 270 },
          s4_board_report: { Task2_Penalize_Sara_Binary: 1, task4_sla_reform_sec: 25.0 }
        };
        renderScreen5();
        return {
          total: document.getElementById('s5PayoutTotalBadge')?.textContent,
          breakdown: document.getElementById('s5PayoutBreakdownText')?.textContent
        };
        """
        res = run_in_simulated_dom(snippet, custom_cfg=CUSTOM_CONFIG)
        self.assertEqual(res['total'], '€3.25 EUR')
        self.assertIn('€3.25 Base Fee', res['breakdown'])
        self.assertIn('Below 1,450 pt Bonus Hurdle', res['breakdown'])

    def test_screen5_arm4_reveal_leaks_hardcoded_defaults(self):
        """
        Adversarial Test: Check if s5Arm4Reveal leaks hardcoded defaults
        (€4.00, €2.50, +€1.00, €3.50) instead of custom config values.
        """
        snippet = """
        state.session = {
          pid: 'P_TEST_A4',
          arm: 4,
          s2b_shifts: { shift1Pts: 360, shift2Directive: 'DIRECTIVE_A', shift2Pts: 360, shift3PreCrashPts: 270 },
          s4_inquiry: { task2Choice: 'ABSORB_BLAME', task4ReformCode: 'TIER1_25S' }
        };
        renderScreen5();
        return document.getElementById('s5Arm4Reveal')?.innerHTML || '';
        """
        html = run_in_simulated_dom(snippet, custom_cfg=CUSTOM_CONFIG)

        leaks = []
        if '€1.00' in html and CUSTOM_CONFIG['arm4IntegrityCreditEur'] != 1.00:
            leaks.append("Leaked hardcoded '€1.00' integrity credit in s5Arm4Reveal")
        if '€3.50' in html and (CUSTOM_CONFIG['basePayEur'] + CUSTOM_CONFIG['arm4IntegrityCreditEur']) != 3.50:
            leaks.append("Leaked hardcoded '€3.50' total in s5Arm4Reveal")
        if '€2.50' in html and CUSTOM_CONFIG['basePayEur'] != 2.50:
            leaks.append("Leaked hardcoded '€2.50' base in s5Arm4Reveal")

        print("\n[EMPIRICAL AUDIT] Arm 4 Reveal Leaks Found:", leaks)
        # Note: We record this as an empirical finding in our challenge report


class TestScreen4Projections(unittest.TestCase):
    """Stress-tests Screen 4 score projections and card wording under custom hurdle."""

    def test_screen4_card_sub_badge_under_high_hurdle(self):
        """
        Adversarial Test: When bonusTargetPts = 1450, projected score is 1,250 pts.
        Does t2Opt1SubBadge falsely claim 'meets 1,450 pt threshold'?
        """
        snippet = """
        state.session = {
          s2b_shifts: { shift1Pts: 360, shift2Directive: 'DIRECTIVE_A', shift2Pts: 360, shift3PreCrashPts: 270 }
        };
        renderScreen4();
        return document.getElementById('t2Opt1SubBadge')?.textContent || '';
        """
        text = run_in_simulated_dom(snippet, custom_cfg=CUSTOM_CONFIG)
        print("\n[EMPIRICAL AUDIT] Screen 4 Task 2 Option 1 SubBadge:", text)
        if "meets 1,450 pt threshold" in text:
            print("[EMPIRICAL FINDING] S4 Task 2 Option 1 falsely claims 'meets 1,450 pt threshold' when projected score is 1,250 < 1,450!")

class TestEdgeConditions(unittest.TestCase):
    """Stress tests boundary and edge conditions: 99,999 hurdle, zero pays, missing keys."""

    def test_extreme_hurdle_99999(self):
        cfg = dict(CUSTOM_CONFIG)
        cfg['bonusTargetPts'] = 99999
        snippet = """
        hydrateConfigUI(state.config);
        const hudHurdle = document.getElementById('hudBonusHurdle')?.textContent;
        const s1Hurdle = document.getElementById('s1Step5BonusHurdle')?.textContent;
        const outcome = calculateFinalOutcome();
        return { hudHurdle, s1Hurdle, bonusUnlocked: outcome.bonusUnlocked, payout: outcome.finalPayout };
        """
        res = run_in_simulated_dom(snippet, custom_cfg=cfg, session_overrides={
            'arm': 1,
            's2b_shifts': {'shift1Pts': 360, 'shift2Directive': 'DIRECTIVE_A', 'shift2Pts': 360, 'shift3PreCrashPts': 270},
            's4_board_report': {'Task2_Penalize_Sara_Binary': 1, 'task4_sla_reform_sec': 25.0}
        })
        self.assertEqual(res['hudHurdle'], '99,999')
        self.assertEqual(res['s1Hurdle'], '99,999')
        self.assertEqual(res['bonusUnlocked'], 0)
        self.assertEqual(res['payout'], 3.25)

    def test_zero_base_pay_and_zero_bonus(self):
        cfg = dict(CUSTOM_CONFIG)
        cfg['basePayEur'] = 0.0
        cfg['performanceBonusEur'] = 0.0
        snippet = """
        hydrateConfigUI(state.config);
        const base = document.getElementById('s1Step5BasePay')?.textContent;
        const bonus = document.getElementById('s1Step5BonusPay')?.textContent;
        const total = document.getElementById('s1Step5TotalPay')?.textContent;
        const outcome = calculateFinalOutcome();
        return { base, bonus, total, payout: outcome.finalPayout };
        """
        res = run_in_simulated_dom(snippet, custom_cfg=cfg, session_overrides={
            'arm': 1,
            's2b_shifts': {'shift1Pts': 360, 'shift2Directive': 'DIRECTIVE_A', 'shift2Pts': 360, 'shift3PreCrashPts': 270},
            's4_board_report': {'Task2_Penalize_Sara_Binary': 1, 'task4_sla_reform_sec': 25.0}
        })
        self.assertEqual(res['base'], '€0.00')
        self.assertEqual(res['bonus'], '€0.00')
        self.assertEqual(res['total'], '€0.00')
        self.assertEqual(res['payout'], 0.0)

    def test_missing_config_keys_in_hydrate_and_calculate(self):
        snippet = """
        hydrateConfigUI({});
        const base = document.getElementById('s1Step5BasePay')?.textContent;
        const hurdle = document.getElementById('s1Step5BonusHurdle')?.textContent;
        state.config = {};
        const outcome = calculateFinalOutcome();
        return { base, hurdle, payout: outcome.finalPayout, hurdleVal: outcome.finalScore };
        """
        res = run_in_simulated_dom(snippet, custom_cfg={}, session_overrides={
            'arm': 1,
            's2b_shifts': {'shift1Pts': 360, 'shift2Directive': 'DIRECTIVE_A', 'shift2Pts': 360, 'shift3PreCrashPts': 270},
            's4_board_report': {'Task2_Penalize_Sara_Binary': 1, 'task4_sla_reform_sec': 25.0}
        })
        self.assertEqual(res['base'], '€2.50')
        self.assertEqual(res['hurdle'], '1,200')
        self.assertEqual(res['payout'], 6.50)  # 1250 >= 1200 default hurdle

    def test_render_screen4_partial_config_crash(self):
        """
        Adversarial Test: When state.config is a partial object (missing tier1SlaSec),
        does renderScreen4() crash due to state.config.tier1SlaSec.toFixed(1)?
        """
        snippet = """
        try {
          state.config = { bonusTargetPts: 1450 }; // partial config without SLA keys
          renderScreen4();
          return { crashed: false };
        } catch (e) {
          return { crashed: true, error: e.message };
        }
        """
        res = run_in_simulated_dom(snippet)
        print("\n[EMPIRICAL AUDIT] renderScreen4 with partial config:", res)
        self.assertFalse(res['crashed'], "Expected renderScreen4() not to crash on partial config without SLA keys")


if __name__ == '__main__':
    unittest.main()
