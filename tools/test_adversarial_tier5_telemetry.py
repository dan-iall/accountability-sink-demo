"""
test_adversarial_tier5_telemetry.py - Tier 5 Econometric & Telemetry Coverage Hardening
Adversarial white-box stress testing suite for:
  1. Canonical 47-Column and 52-Column CSV Export Parity, Zero-Value Preservation, and Escaping
  2. 3-Tier DataPipe Telemetry Payloads (_started, _midpoint, _session, _dropout)
  3. session.interaction_events Clickstream & Viewport AOI Parity
"""

import os
import sys
import json
import subprocess
import csv
import io
import re
import unittest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MVP2_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
INDEX_PATH = os.path.join(MVP2_DIR, "index.html")
ADMIN_PATH = os.path.join(MVP2_DIR, "admin.html")
CONFIG_PATH = os.path.join(MVP2_DIR, "experiment_config.json")


def run_node(js_script):
    """Executes Node.js script in the tools directory and returns stdout."""
    res = subprocess.run(
        ["node", "-e", js_script],
        cwd=BASE_DIR,
        capture_output=True,
        text=True
    )
    if res.returncode != 0:
        raise RuntimeError(f"Node execution failed (code {res.returncode}):\n{res.stderr}")
    return res.stdout


def extract_json(out):
    """Extracts JSON payload from command output safely ignoring extraneous console logs."""
    m = re.search(r"__JSON_START__([\s\S]*?)__JSON_END__", out)
    if m:
        return json.loads(m.group(1))
    for line in reversed(out.splitlines()):
        line = line.strip()
        if (line.startswith('{') and line.endswith('}')) or (line.startswith('[') and line.endswith(']')):
            try:
                return json.loads(line)
            except Exception:
                pass
    return json.loads(out)


class TestCanonicalCsvExportHardening(unittest.TestCase):
    """Stress testing 47-column & 52-column CSV export across edge-case sessions."""

    def test_canonical_column_count_and_headers_order(self):
        """Validates that index.html and admin.html CSV headers match 100% across all 52 columns."""
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            idx_html = f.read()
        with open(ADMIN_PATH, "r", encoding="utf-8") as f:
            adm_html = f.read()

        m_idx = re.search(r"function exportParticipantCsv\(\)\s*\{[\s\S]*?const headers = \[([\s\S]*?)\];", idx_html)
        self.assertIsNotNone(m_idx, "Could not find CSV headers in index.html")
        idx_cols = [h.strip().strip('"').strip("'") for h in m_idx.group(1).split(",") if h.strip()]

        m_adm = re.search(r"const CSV_HEADERS = \[([\s\S]*?)\];", adm_html)
        self.assertIsNotNone(m_adm, "Could not find CSV_HEADERS in admin.html")
        adm_cols = [h.strip().strip('"').strip("'") for h in m_adm.group(1).split(",") if h.strip()]

        self.assertEqual(len(idx_cols), 52, f"Expected 52 index columns, got {len(idx_cols)}")
        self.assertEqual(len(adm_cols), 52, f"Expected 52 admin columns, got {len(adm_cols)}")
        self.assertEqual(idx_cols, adm_cols, "Column header mismatch between index and admin CSV exports")

    def test_csv_row_parity_on_completed_synthetic_sessions(self):
        """Tests column-by-column value match on synthetic cohort sessions across Arms 1-4."""
        js = """
        const vm = require('vm');
        const { createAdminEnvironment } = require('./admin_vm_harness.js');
        const { createHarnessContext } = require('./workflow_challenger_harness.js');

        const adminEnv = createAdminEnvironment();
        let lastAdminCsv = null;
        adminEnv.sandbox.Blob = function(parts) { lastAdminCsv = parts[0]; };

        // Generate 4 balanced sessions (arms 1, 2, 3, 4)
        const sessions = adminEnv.sandbox.window.generateSyntheticSessions(4, 'replace', 12345);
        adminEnv.elements.btnExportCsv.click();

        const idxCtx = createHarnessContext();
        let lastIdxCsv = null;
        idxCtx.sandbox.Blob = function(parts) { lastIdxCsv = parts[0]; };
        idxCtx.sandbox.document.createElement = () => ({ click: ()=>{}, setAttribute: ()=>{} });

        const results = [];
        for (let i = 0; i < sessions.length; i++) {
          const sess = sessions[i];
          vm.runInContext("state.session = " + JSON.stringify(sess), idxCtx.context);
          idxCtx.context.exportParticipantCsv();
          results.push({
            pid: sess.pid,
            arm: sess.arm,
            idxCsv: lastIdxCsv
          });
        }

        console.log(JSON.stringify({
          adminCsv: lastAdminCsv,
          results
        }));
        """
        out = run_node(js)
        data = json.loads(out)
        admin_rows = list(csv.reader(io.StringIO(data["adminCsv"])))
        self.assertEqual(len(admin_rows), 5)  # Header + 4 sessions

        for i, res in enumerate(data["results"]):
            adm_row = admin_rows[i + 1]
            idx_rows = list(csv.reader(io.StringIO(res["idxCsv"])))
            idx_row = idx_rows[1]
            self.assertEqual(len(adm_row), 52)
            self.assertEqual(len(idx_row), 52)
            self.assertEqual(adm_row, idx_row, f"Row mismatch for session {res['pid']} arm {res['arm']}")

    def test_zero_value_preservation(self):
        """Validates that 0.0 slider ratings, 0 pts, and €0.00 payouts are never overwritten by falsy fallback defaults."""
        js = """
        const vm = require('vm');
        const { createAdminEnvironment } = require('./admin_vm_harness.js');
        const { createHarnessContext } = require('./workflow_challenger_harness.js');

        const zeroSession = {
          pid: 'P_ZERO_TEST',
          sessionId: 'S_ZERO_123',
          startedAtIso: '2026-11-08T09:00:00.000Z',
          status: 'COMPLETED',
          arm: 1,
          D2_stamp: 0,
          D3_embodied: 0,
          D4_eu_ai_act: 0,
          speedMultiplier: 1,
          stationMetadata: 'Station Zero',
          config_snapshot: { sla_tier1: 25.0, sla_tier2: 38.0, sla_tier3: 60.0, target_pts: 1200, shift_duration_sec: 25.0 },
          s1b_floor: { executed: false },
          s2a_policy: { initialSlaPreferenceSec: 25.0, initialSlaArchetype: 'SPEED_25S', corporateOverrideTriggered: false },
          s2b_shifts: { shift2Directive: 'A_TRUST_AI' },
          s3_audit: { dwell_s3_total_ms: 0, page3Opened: false, dwell_box_d_treatment_ms: 0 },
          s4_board_report: {
            sliderSara: 0.0, sliderAi: 0.0, sliderSla: 0.0,
            Task1A_Derived_Sara_Share_Pct: 0.0,
            Task1B_Root_Cause_Code: 'H-1',
            Task1C_CDS_Controllability_Sara: 0,
            Task1C_CDS_SLA_Constraint: 0,
            Task2_Penalize_Sara_Binary: 0,
            Task2_Choice_Label: 'ABSORB_BLAME',
            Task3_Justification_Char_Len: 0,
            Task3_Justification_Text: '',
            Task4_Shift4_Sla_Reform_Sec: 25.0,
            Task4_Shift4_Compliant_Binary: 0
          },
          s5_outcome: { finalManagerScorePts: 0, bonusUnlockedBinary: 0, integrityCreditAwardedBinary: 0, finalPayoutEur: 0.0 },
          completionCode: 'STUDY-DONE-ZERO'
        };

        const adminEnv = createAdminEnvironment({ study_sessions: JSON.stringify([zeroSession]) });
        let adminCsv = null;
        adminEnv.sandbox.Blob = function(parts) { adminCsv = parts[0]; };
        adminEnv.elements.btnExportCsv.click();

        const idxCtx = createHarnessContext();
        let idxCsv = null;
        idxCtx.sandbox.Blob = function(parts) { idxCsv = parts[0]; };
        idxCtx.sandbox.document.createElement = () => ({ click: ()=>{}, setAttribute: ()=>{} });

        vm.runInContext('state.session = ' + JSON.stringify(zeroSession), idxCtx.context);
        idxCtx.context.exportParticipantCsv();

        console.log(JSON.stringify({ adminCsv, idxCsv }));
        """
        out = run_node(js)
        data = json.loads(out)
        adm_row = list(csv.reader(io.StringIO(data["adminCsv"])))[1]
        idx_row = list(csv.reader(io.StringIO(data["idxCsv"])))[1]

        # Verify exact parity
        self.assertEqual(adm_row, idx_row)

        # Explicitly verify that zero fields preserved their numeric 0 value instead of defaults
        # Task1A_slider_sara is col 34, slider_ai is 35, slider_sla is 36
        self.assertEqual(idx_row[34], "0")
        self.assertEqual(idx_row[35], "0")
        self.assertEqual(idx_row[36], "0")
        self.assertEqual(idx_row[37], "0")   # Task1A_Derived_Sara_Share_Pct !== 33.33
        self.assertEqual(idx_row[39], "0")   # Task1C_CDS_Controllability_Sara !== 5
        self.assertEqual(idx_row[40], "0")   # Task1C_CDS_SLA_Constraint !== 5
        self.assertEqual(idx_row[41], "0")   # Task2_Penalize_Sara_Binary !== default
        self.assertEqual(idx_row[46], "0")   # Task4_Shift4_Compliant_Binary !== default
        self.assertEqual(idx_row[47], "0")   # final_score_pts
        self.assertEqual(idx_row[48], "0")   # bonus_unlocked_binary
        self.assertEqual(idx_row[49], "0")   # integrity_credit_binary
        self.assertEqual(idx_row[50], "0")   # final_payout_eur !== 2.50

    def test_delimiter_injection_safety(self):
        """Validates that RFC 4180 escaping protects against delimiter, quote, and newline CSV injection."""
        js = """
        const vm = require('vm');
        const { createAdminEnvironment } = require('./admin_vm_harness.js');
        const { createHarnessContext } = require('./workflow_challenger_harness.js');

        const evilSession = {
          pid: 'P_123,EVIL"QUOTE',
          sessionId: 'S_123\\nINJECT',
          startedAtIso: '2026-11-08T09:00:00.000Z',
          status: 'COMPLETED',
          arm: 1,
          stationMetadata: 'Station, Room 101 "Alpha"',
          config_snapshot: { sla_tier1: 25.0, sla_tier2: 38.0, sla_tier3: 60.0, target_pts: 1200, shift_duration_sec: 25.0 },
          s1b_floor: { executed: false },
          s4_board_report: {
            sliderSara: 5.0, sliderAi: 5.0, sliderSla: 5.0,
            Task1A_Derived_Sara_Share_Pct: 33.33, Task1B_Root_Cause_Code: 'H-1',
            Task1C_CDS_Controllability_Sara: 5, Task1C_CDS_SLA_Constraint: 5,
            Task2_Penalize_Sara_Binary: 1, Task2_Choice_Label: 'PENALIZE_SARA',
            Task3_Justification_Text: 'Line 1,\\nLine 2 with "quotes" and , commas.',
            Task3_Justification_Char_Len: 42,
            Task4_Shift4_Sla_Reform_Sec: 25.0, Task4_Shift4_Compliant_Binary: 0
          },
          s5_outcome: { finalManagerScorePts: 1000, bonusUnlockedBinary: 0, integrityCreditAwardedBinary: 0, finalPayoutEur: 2.50 },
          completionCode: 'STUDY-DONE-"CODE",123'
        };

        const adminEnv = createAdminEnvironment({ study_sessions: JSON.stringify([evilSession]) });
        let adminCsv = null;
        adminEnv.sandbox.Blob = function(parts) { adminCsv = parts[0]; };
        adminEnv.elements.btnExportCsv.click();

        const idxCtx = createHarnessContext();
        let idxCsv = null;
        idxCtx.sandbox.Blob = function(parts) { idxCsv = parts[0]; };
        idxCtx.sandbox.document.createElement = () => ({ click: ()=>{}, setAttribute: ()=>{} });

        vm.runInContext('state.session = ' + JSON.stringify(evilSession), idxCtx.context);
        idxCtx.context.exportParticipantCsv();

        console.log(JSON.stringify({ adminCsv, idxCsv }));
        """
        out = run_node(js)
        data = json.loads(out)
        adm_rows = list(csv.reader(io.StringIO(data["adminCsv"])))
        idx_rows = list(csv.reader(io.StringIO(data["idxCsv"])))

        # Exactly 2 logical rows (Header + 1 session row), despite embedded newlines
        self.assertEqual(len(adm_rows), 2)
        self.assertEqual(len(idx_rows), 2)
        self.assertEqual(adm_rows[1], idx_rows[1])

        # Verify parsed cell contents match raw strings exactly without corruption
        self.assertEqual(idx_rows[1][0], 'P_123,EVIL"QUOTE')
        self.assertEqual(idx_rows[1][1], 'S_123\nINJECT')
        self.assertEqual(idx_rows[1][9], 'Station, Room 101 "Alpha"')
        self.assertEqual(idx_rows[1][44], 'Line 1,\nLine 2 with "quotes" and , commas.')
        self.assertEqual(idx_rows[1][51], 'STUDY-DONE-"CODE",123')

    def test_incomplete_and_dropout_session_parity(self):
        """Tests that incomplete sessions and dropouts correctly export empty cells for unreached stages."""
        js = """
        const vm = require('vm');
        const { createAdminEnvironment } = require('./admin_vm_harness.js');
        const { createHarnessContext } = require('./workflow_challenger_harness.js');

        const dropouts = [
          // Dropout at Screen 1 (Onboarding)
          {
            pid: 'P_DROP_S1',
            sessionId: 'S_DROP_1',
            startedAtIso: '2026-11-08T08:00:00.000Z',
            status: 'DROPOUT',
            arm: 3,
            config_snapshot: { sla_tier1: 25.0, sla_tier2: 38.0, sla_tier3: 60.0, target_pts: 1200, shift_duration_sec: 25.0 },
            s1b_floor: { executed: false },
            s2a_policy: {},
            s2b_shifts: {},
            s3_audit: {},
            s4_board_report: {},
            s5_outcome: {},
            completionCode: null
          },
          // Dropout at Screen 2B (Floor Crash)
          {
            pid: 'P_DROP_S2',
            sessionId: 'S_DROP_2',
            startedAtIso: '2026-11-08T08:15:00.000Z',
            status: 'DROPOUT',
            arm: 4,
            config_snapshot: { sla_tier1: 25.0, sla_tier2: 38.0, sla_tier3: 60.0, target_pts: 1200, shift_duration_sec: 25.0 },
            s1b_floor: { executed: false },
            s2a_policy: { initialSlaPreferenceSec: 38.0, initialSlaArchetype: 'BALANCED_38S', corporateOverrideTriggered: true },
            s2b_shifts: { shift2Directive: 'B_SLOW_FLOOR' },
            s3_audit: { dwell_s3_total_ms: 12000, page3Opened: true, dwell_box_d_treatment_ms: 5000 },
            s4_board_report: {},
            s5_outcome: {},
            completionCode: null
          }
        ];

        const adminEnv = createAdminEnvironment({ study_sessions: JSON.stringify(dropouts) });
        let adminCsv = null;
        adminEnv.sandbox.Blob = function(parts) { adminCsv = parts[0]; };
        adminEnv.elements.btnExportCsv.click();

        const idxCtx = createHarnessContext();
        let lastIdxCsv = null;
        idxCtx.sandbox.Blob = function(parts) { lastIdxCsv = parts[0]; };
        idxCtx.sandbox.document.createElement = () => ({ click: ()=>{}, setAttribute: ()=>{} });

        const idxRows = [];
        for (const sess of dropouts) {
          vm.runInContext('state.session = ' + JSON.stringify(sess), idxCtx.context);
          idxCtx.context.exportParticipantCsv();
          idxRows.push(lastIdxCsv);
        }

        console.log(JSON.stringify({ adminCsv, idxRows }));
        """
        out = run_node(js)
        data = json.loads(out)
        adm_rows = list(csv.reader(io.StringIO(data["adminCsv"])))

        for i in range(len(data["idxRows"])):
            adm_row = adm_rows[i + 1]
            idx_row = list(csv.reader(io.StringIO(data["idxRows"][i])))[1]
            self.assertEqual(len(adm_row), 52)
            self.assertEqual(len(idx_row), 52)
            self.assertEqual(adm_row, idx_row)

            # Assert unreached sections resolve to empty strings
            self.assertEqual(idx_row[34], "")  # sliderSara is empty
            self.assertEqual(idx_row[35], "")  # sliderAi is empty
            self.assertEqual(idx_row[37], "")  # task1a_share is empty
            self.assertEqual(idx_row[47], "")  # final_score_pts is empty
            self.assertEqual(idx_row[50], "")  # final_payout_eur is empty
            self.assertEqual(idx_row[51], "")  # completionCode is empty for dropout


class TestDataPipeTelemetryArchitecture(unittest.TestCase):
    """Adversarial testing of 3-Tier DataPipe cloud telemetry and graceful dropout beacons."""

    def test_datapipe_started_checkpoint_payload(self):
        """Validates that session initialization dispatches an enrollment ping (_started.json)."""
        js = """
        const { createHarnessContext } = require('./workflow_challenger_harness.js');
        const h = createHarnessContext(1731000000000);

        const payloads = [];
        h.sandbox.fetch = async function(url, opts) {
          payloads.push({ url, body: JSON.parse(opts.body) });
          return { ok: true, json: async () => ({}) };
        };

        h.sandbox.window.location.search = '?arm=2&speed=1';
        h.context.initSession();

        console.log('__JSON_START__' + JSON.stringify(payloads) + '__JSON_END__');
        """
        out = run_node(js)
        payloads = extract_json(out)
        self.assertGreaterEqual(len(payloads), 1)
        req = payloads[0]["body"]
        self.assertTrue(req["filename"].endswith("_arm2_started.json"))
        data = json.loads(req["data"])
        self.assertEqual(data["event"], "SESSION_START")
        self.assertEqual(data["arm"], 2)
        self.assertIn("startedAtIso", data)
        self.assertIn("config_snapshot", data)

    def test_datapipe_midpoint_checkpoint_payload(self):
        """Validates that entering Screen 4 triggers a post-crash midpoint checkpoint (_midpoint.json)."""
        js = """
        const { createHarnessContext } = require('./workflow_challenger_harness.js');
        const h = createHarnessContext(1731000000000);

        const payloads = [];
        h.sandbox.fetch = async function(url, opts) {
          payloads.push({ url, body: JSON.parse(opts.body) });
          return { ok: true, json: async () => ({}) };
        };

        h.sandbox.window.location.search = '?arm=3&speed=1';
        h.context.initSession();
        h.context.showScreen('screenS4');

        // Calling showScreen again must not duplicate the checkpoint
        h.context.showScreen('screenS4');

        console.log('__JSON_START__' + JSON.stringify(payloads) + '__JSON_END__');
        """
        out = run_node(js)
        payloads = extract_json(out)
        midpoint_payloads = [p for p in payloads if p["body"]["filename"].endswith("_midpoint.json")]
        self.assertEqual(len(midpoint_payloads), 1, "Expected exactly 1 midpoint checkpoint payload")
        req = midpoint_payloads[0]["body"]
        self.assertTrue(req["filename"].endswith("_arm3_midpoint.json"))
        data = json.loads(req["data"])
        self.assertIsNotNone(data.get("midpointSyncedIso"))

    def test_datapipe_terminal_session_checkpoint_payload(self):
        """Validates that session finalization dispatches terminal dossier (_session.json)."""
        js = """
        const { createHarnessContext } = require('./workflow_challenger_harness.js');
        const h = createHarnessContext(1731000000000);

        const payloads = [];
        h.sandbox.fetch = async function(url, opts) {
          payloads.push({ url, body: JSON.parse(opts.body) });
          return { ok: true, json: async () => ({}) };
        };

        h.sandbox.window.location.search = '?arm=4&speed=1';
        h.context.initSession();
        h.context.finalizeSession();

        console.log('__JSON_START__' + JSON.stringify(payloads) + '__JSON_END__');
        """
        out = run_node(js)
        payloads = extract_json(out)
        session_payloads = [p for p in payloads if p["body"]["filename"].endswith("_session.json")]
        self.assertEqual(len(session_payloads), 1)
        req = session_payloads[0]["body"]
        self.assertTrue(req["filename"].endswith("_arm4_session.json"))
        data = json.loads(req["data"])
        self.assertEqual(data["status"], "COMPLETED")
        self.assertIsNotNone(data.get("completionCode"))

    def test_datapipe_dropout_beacon_fallback(self):
        """Validates that window pagehide triggers graceful dropout beacon (_dropout.json) on uncompleted sessions."""
        js = """
        const { createHarnessContext } = require('./workflow_challenger_harness.js');
        const h = createHarnessContext(1731000000000);
        const vm = require('vm');

        let beaconSent = null;
        h.sandbox.navigator = {
          userAgent: 'MockBrowser',
          sendBeacon: function(url, blob) {
            beaconSent = { url, parts: blob.parts };
            return true;
          }
        };

        h.sandbox.window.location.search = '?arm=1&speed=1';
        h.context.initSession();
        h.context.showScreen('screenS2B');

        // Trigger dropout beacon
        vm.runInContext('handleDropoutBeacon()', h.context);

        // A second trigger should be a no-op (guard flag)
        vm.runInContext('handleDropoutBeacon()', h.context);

        console.log('__JSON_START__' + JSON.stringify(beaconSent) + '__JSON_END__');
        """
        out = run_node(js)
        beacon = extract_json(out)
        self.assertIsNotNone(beacon)
        body = json.loads(beacon["parts"][0])
        self.assertTrue(body["filename"].endswith("_arm1_dropout.json"))
        data = json.loads(body["data"])
        self.assertEqual(data["status"], "DROPOUT")
        self.assertEqual(data["dropoutScreen"], "screenS2B")
        self.assertIsNotNone(data.get("dropoutAtIso"))


class TestClickstreamAndViewportAoiTelemetry(unittest.TestCase):
    """Adversarial testing of session.interaction_events clickstream and Viewport AOI taxonomy."""

    def test_interaction_events_clickstream_structure(self):
        """Validates that document clicks populate state.session.interaction_events with all 10 required keys."""
        js = """
        const { createHarnessContext } = require('./workflow_challenger_harness.js');
        const h = createHarnessContext(1731000000000);
        const vm = require('vm');

        h.sandbox.window.location.search = '?arm=3&speed=1';
        h.context.initSession();

        // Simulate click on an interactive element with data-aoi
        const btn = h.getElement('btnDirectiveA');
        btn.setAttribute('data-aoi', 's4_task2_scapegoat_fork');
        btn.innerText = 'Directive A: Rely on Copilot';

        h.sandbox.document.dispatchEvent({
          type: 'click',
          target: btn,
          clientX: 250,
          clientY: 400
        });

        const sess = vm.runInContext('state.session', h.context);
        console.log('__JSON_START__' + JSON.stringify(sess.interaction_events) + '__JSON_END__');
        """
        out = run_node(js)
        events = extract_json(out)
        self.assertGreaterEqual(len(events), 1)
        evt = events[0]

        required_keys = [
            "t_rel_ms", "timestamp_iso", "screen", "step",
            "target_id", "target_tag", "target_aoi", "label", "x", "y"
        ]
        for k in required_keys:
            self.assertIn(k, evt, f"Missing required clickstream key: {k}")

        self.assertGreaterEqual(evt["t_rel_ms"], 0)
        self.assertEqual(evt["target_id"], "btnDirectiveA")
        self.assertEqual(evt["target_aoi"], "s4_task2_scapegoat_fork")
        self.assertEqual(evt["x"], 250)
        self.assertEqual(evt["y"], 400)

    def test_viewport_aoi_canonical_map_and_parity(self):
        """Validates that window.getScreenAOIMap() extracts active bounding boxes matching the canonical AOI taxonomy."""
        js = """
        const { createHarnessContext } = require('./workflow_challenger_harness.js');
        const h = createHarnessContext(1731000000000);

        h.sandbox.window.location.search = '?arm=1&speed=1';
        h.context.initSession();

        // Seed mock active elements with data-aoi
        const el1 = h.getElement('cardAiExplainer');
        el1.setAttribute('data-aoi', 'ai_copilot');
        const el2 = h.getElement('sliderSara');
        el2.setAttribute('data-aoi', 'blame_sliders_group');

        const aois = h.sandbox.window.getScreenAOIMap(false);
        console.log('__JSON_START__' + JSON.stringify(aois) + '__JSON_END__');
        """
        out = run_node(js)
        aois = extract_json(out)
        self.assertGreaterEqual(len(aois), 2)

        aoi_names = [a["category"] for a in aois]
        self.assertIn("ai_copilot", aoi_names)
        self.assertIn("blame_sliders_group", aoi_names)

        for a in aois:
            self.assertIn("aoi_id", a)
            self.assertIn("category", a)
            self.assertIn("screen_id", a)
            self.assertIn("x", a)
            self.assertIn("y", a)
            self.assertIn("width", a)
            self.assertIn("height", a)
            self.assertGreater(a["width"], 0)
            self.assertGreater(a["height"], 0)


if __name__ == "__main__":
    unittest.main()
