"""
Journey Explorer & Canonical Specification Verification Suite
Validates that EXPERIMENT_JOURNEY_EXPLORER.html (and Section 11 of WHAT_WE_ARE_BUILDING.md when present)
rigorously model all 4 experimental arms and choice paths.
"""

import json
import os
import subprocess
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestJourneyExplorerAndSpec(unittest.TestCase):

    def setUp(self):
        self.doc_path = os.path.join(BASE_DIR, "docs", "WHAT_WE_ARE_BUILDING.md")
        self.root_html_path = os.path.join(BASE_DIR, "EXPERIMENT_JOURNEY_EXPLORER.html")
        docs_html = os.path.join(BASE_DIR, "docs", "EXPERIMENT_JOURNEY_EXPLORER.html")
        self.html_path = docs_html if os.path.exists(docs_html) else self.root_html_path

    def test_what_we_are_building_section_11_structure(self):
        if not os.path.exists(self.doc_path):
            self.skipTest("docs/WHAT_WE_ARE_BUILDING.md withheld in public export")
        with open(self.doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        required_sections = [
            "# 🗺️ SECTION 11: Master Participant Journey & Arm-by-Arm Decision Architecture",
            "### 11.1 Master 4-Arm Comparative Architectural Overview",
            "### 11.2 Master Experimental Flow & Routing Architecture",
            "### 11.3 Arm 1 Journey Deep Dive: Corporate Status Quo (Control Baseline)",
            "### 11.4 Arm 2 Journey Deep Dive: STAMP Cognitive Ergonomics Diagnostic",
            "### 11.5 Arm 3 Journey Deep Dive: Embodied Sensorimotor Friction",
            "#### 11.5.1 Concrete Step-by-Step Scenario Walkthrough: Participant in Arm 3",
            "#### 11.5.2 Detailed Screen-by-Screen Input & Consequence Table for Arm 3",
            "#### 11.5.3 Exhaustive 8-Branch Combinatorial Decision & Payout Matrix for Arm 3",
            "### 11.6 Arm 4 Journey Deep Dive: EU AI Act Regulatory Intervention & Integrity Trap",
            "### 11.7 Cross-Arm Master Decision & Consequence Matrix",
            "### 11.8 The Interactive Generative UI Journey Explorer"
        ]

        for sec in required_sections:
            self.assertIn(sec, content, f"Missing required Section 11 heading: {sec}")

        # Assert all 8 paths are enumerated in Section 11.5.3
        for path_num in range(1, 9):
            self.assertIn(f"**Path {path_num}**", content, f"Missing Path {path_num} in Section 11.5.3")

    def test_interactive_journey_explorer_html_integrity(self):
        self.assertTrue(os.path.exists(self.root_html_path), "EXPERIMENT_JOURNEY_EXPLORER.html must exist at root")
        target_html = self.html_path if os.path.exists(self.html_path) else self.root_html_path

        with open(target_html, "r", encoding="utf-8") as f:
            html = f.read()

        # Check required DOM elements
        required_elements = [
            'id="btnArm1"', 'id="btnArm2"', 'id="btnArm3"', 'id="btnArm4"',
            'id="screenView1"', 'id="screenView1B"', 'id="screenView2A"',
            'id="screenView2B"', 'id="screenView3"', 'id="screenView4"', 'id="screenView5"',
            'id="boxDContainer"', 'id="s4Task2ForkContainer"', 'id="s5Arm4RevealContainer"',
            'id="csvPreviewBox"', 'id="jsonPreviewBox"'
        ]
        for elem in required_elements:
            self.assertIn(elem, html, f"Missing interactive DOM element: {elem}")

        # Check mathematical engine and function definitions
        required_functions = [
            'function initSimulator()',
            'function setArm(armNum)',
            'function goToStep(step)',
            'function updateCase1Dwell(val)',
            'function updateCase2Pages(val)',
            'function setS2aSla(slaSec)',
            'function setShift2Directive(dir)',
            'function setTask2Choice(choice)',
            'function setTask4Sla(slaVal)',
            'function applyPreset(presetKey)',
            'function syncControlsFromState()',
            'function updateSimulator()',
            'function renderBoxD()',
            'function renderArm4Reveal(isScapegoat)',
            'function renderLedger('
        ]
        for fn in required_functions:
            self.assertIn(fn, html, f"Missing core simulator function: {fn}")

    def test_simulator_js_node_execution_and_preset_sync(self):
        node_script = f"""
        const fs = require('fs');
        const vm = require('vm');
        const html = fs.readFileSync('{self.html_path}', 'utf-8');
        let script = html.substring(html.indexOf('<script>') + 8, html.indexOf('</script>', html.indexOf('<script>') + 8));
        script = script.replace('const simState =', 'var simState =');

        const elements = {{}};
        function getEl(id) {{
          if (!elements[id]) {{
            elements[id] = {{
              textContent: '', innerHTML: '', className: '', value: '0',
              classList: {{ add: ()=>{{}}, remove: ()=>{{}}, contains: ()=>false }},
              style: {{}}
            }};
          }}
          return elements[id];
        }}
        const sandbox = {{
          document: {{ getElementById: getEl, getElementsByName: () => [] }},
          navigator: {{ clipboard: {{ writeText: ()=>{{}} }} }},
          alert: () => {{}},
          window: {{}},
          console: console
        }};
        vm.createContext(sandbox);
        vm.runInContext(script, sandbox);
        vm.runInContext('initSimulator()', sandbox);

        // 1. Arm 3 Absorb Preset
        vm.runInContext('applyPreset("arm3_absorb")', sandbox);
        const p1 = sandbox.simState;
        if (p1.arm !== 3 || !p1.s1b.executed || p1.s4.task2Choice !== 0) throw new Error('arm3_absorb state mismatch');

        // 2. Arm 4 Reveal Preset (Anti-Leakage Check: s1b.executed must be false!)
        vm.runInContext('applyPreset("arm4_reveal")', sandbox);
        const p2 = sandbox.simState;
        if (p2.arm !== 4 || p2.s1b.executed !== false || p2.s4.task2Choice !== 1) throw new Error('arm4_reveal state mismatch');

        // 3. Arm 4 Integrity Preset
        vm.runInContext('applyPreset("arm4_integrity")', sandbox);
        const p3 = sandbox.simState;
        if (p3.arm !== 4 || p3.s1b.executed !== false || p3.s4.task2Choice !== 0) throw new Error('arm4_integrity state mismatch');

        // 4. Verify 52-Column CSV Telemetry
        const csv = elements['csvPreviewBox'].textContent;
        const cols = csv.split(',');
        if (cols.length !== 52) throw new Error('Expected 52 CSV columns, got ' + cols.length);

        console.log('__RESULT__:' + JSON.stringify({{ success: true, colCount: cols.length }}));
        """
        proc = subprocess.run(["node", "-e", node_script], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Node script failed:\n{proc.stderr}")
        self.assertIn('"success":true', proc.stdout)

    def test_arm3_all_8_combinatorial_branches_in_node(self):
        node_script = f"""
        const fs = require('fs');
        const vm = require('vm');
        const html = fs.readFileSync('{self.html_path}', 'utf-8');
        let script = html.substring(html.indexOf('<script>') + 8, html.indexOf('</script>', html.indexOf('<script>') + 8));
        script = script.replace('const simState =', 'var simState =');

        const elements = {{}};
        function getEl(id) {{
          if (!elements[id]) {{
            elements[id] = {{
              textContent: '', innerHTML: '', className: '', value: '0',
              classList: {{ add: ()=>{{}}, remove: ()=>{{}}, contains: ()=>false }},
              style: {{}}
            }};
          }}
          return elements[id];
        }}
        const sandbox = {{
          document: {{ getElementById: getEl, getElementsByName: () => [] }},
          navigator: {{ clipboard: {{ writeText: ()=>{{}} }} }},
          alert: () => {{}},
          window: {{}}
        }};
        vm.createContext(sandbox);
        vm.runInContext(script, sandbox);
        vm.runInContext('initSimulator()', sandbox);

        // Expected truth table per Section 11.5.3
        const truthTable = [
          {{ dir: 'A_TRUST_AI', choice: 1, sla: 60.0, expPts: 1290, expPay: '€6.50' }},
          {{ dir: 'A_TRUST_AI', choice: 1, sla: 25.0, expPts: 1250, expPay: '€6.50' }},
          {{ dir: 'A_TRUST_AI', choice: 0, sla: 60.0, expPts: 990, expPay: '€2.50' }},
          {{ dir: 'A_TRUST_AI', choice: 0, sla: 25.0, expPts: 950, expPay: '€2.50' }},
          {{ dir: 'B_SLOW_FLOOR', choice: 1, sla: 60.0, expPts: 1250, expPay: '€6.50' }},
          {{ dir: 'B_SLOW_FLOOR', choice: 1, sla: 25.0, expPts: 1210, expPay: '€6.50' }},
          {{ dir: 'B_SLOW_FLOOR', choice: 0, sla: 60.0, expPts: 950, expPay: '€2.50' }},
          {{ dir: 'B_SLOW_FLOOR', choice: 0, sla: 25.0, expPts: 910, expPay: '€2.50' }}
        ];

        sandbox.setArm(3);
        for (let i = 0; i < truthTable.length; i++) {{
          const row = truthTable[i];
          sandbox.setShift2Directive(row.dir);
          sandbox.setTask2Choice(row.choice);
          sandbox.setTask4Sla(row.sla);

          const finalPts = parseInt(elements['lblFinalScoreTotal'].textContent);
          const payText = elements['lblFinalCompensationRow'].textContent;

          if (finalPts !== row.expPts) {{
            throw new Error('Path ' + (i+1) + ' pts mismatch: got ' + finalPts + ', exp ' + row.expPts);
          }}
          if (!payText.includes(row.expPay)) {{
            throw new Error('Path ' + (i+1) + ' payout mismatch: got ' + payText + ', exp ' + row.expPay);
          }}
        }}

        console.log('__RESULT__:ALL_8_PATHS_VERIFIED');
        """
        proc = subprocess.run(["node", "-e", node_script], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Node script failed:\n{proc.stderr}")
        self.assertIn("__RESULT__:ALL_8_PATHS_VERIFIED", proc.stdout)


if __name__ == "__main__":
    unittest.main()
