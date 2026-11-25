#!/usr/bin/env python3
import json
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNNER_JS = os.path.join(BASE_DIR, "tools", "test_inspection_runner.js")

def run_js_scenario(tab_sequence, action="QUICK_APPROVE", options=None):
    if options is None:
        options = {}
    code = f"""
    const {{ runScenario }} = require('{RUNNER_JS}');
    const result = runScenario({json.dumps(tab_sequence)}, '{action}', {json.dumps(options)});
    console.log('__RESULT__:' + JSON.stringify(result));
    """
    proc = subprocess.run(["node", "-e", code], capture_output=True, text=True, check=True)
    for line in proc.stdout.splitlines():
        if line.startswith("__RESULT__:"):
            return json.loads(line[len("__RESULT__:"):])
    raise ValueError(f"Could not find __RESULT__ in output: {proc.stdout}")

def parse_csv_row(csv_string):
    lines = [line.strip() for line in csv_string.strip().split("\n") if line.strip()]
    headers = [h.strip('"') for h in lines[0].split(",")]
    values = [v.strip('"') for v in lines[1].split(",")]
    return dict(zip(headers, values))

def test_tab_combination_scenarios():
    print("--------------------------------------------------")
    print("TEST: Tab Combination Inspection Scenarios & Telemetry")
    
    # 1. Tab 1 only
    r1 = run_js_scenario([], "QUICK_APPROVE")
    assert "Pages Inspected: 1/3 (Pages 2 & 3 Unopened)" in r1["kpiMetric"], f"Failed Tab 1 only metric: {r1['kpiMetric']}"
    assert r1["s1b"]["case2Page1Visited"] is True
    assert r1["s1b"]["case2Page2Visited"] is False
    assert r1["s1b"]["case2Page3Visited"] is False
    assert r1["s1b"]["case2PagesVisitedCount"] == 1
    assert r1["s1b"]["case2PagesVisited"] == [1]
    assert r1["s1b"]["case2PagesUnopened"] == [2, 3]
    csv1 = parse_csv_row(r1["csv"])
    assert csv1["s1b_case2_page1_visited"] == "1"
    assert csv1["s1b_case2_page2_visited"] == "0"
    assert csv1["s1b_case2_page3_visited"] == "0"
    assert csv1["s1b_case2_pages_visited"] == "1"
    print("  ✓ Scenario 1: Tab 1 only -> 'Pages Inspected: 1/3 (Pages 2 & 3 Unopened)'")

    # 2. Tabs 1 & 2
    r2 = run_js_scenario([2], "QUICK_APPROVE")
    assert "Pages Inspected: 2/3 (Page 3 Scale Log Unopened)" in r2["kpiMetric"], f"Failed Tabs 1 & 2 metric: {r2['kpiMetric']}"
    assert r2["s1b"]["case2Page1Visited"] is True
    assert r2["s1b"]["case2Page2Visited"] is True
    assert r2["s1b"]["case2Page3Visited"] is False
    assert r2["s1b"]["case2PagesVisitedCount"] == 2
    assert r2["s1b"]["case2PagesVisited"] == [1, 2]
    assert r2["s1b"]["case2PagesUnopened"] == [3]
    csv2 = parse_csv_row(r2["csv"])
    assert csv2["s1b_case2_page1_visited"] == "1"
    assert csv2["s1b_case2_page2_visited"] == "1"
    assert csv2["s1b_case2_page3_visited"] == "0"
    assert csv2["s1b_case2_pages_visited"] == "2"
    print("  ✓ Scenario 2: Tabs 1 & 2 -> 'Pages Inspected: 2/3 (Page 3 Scale Log Unopened)'")

    # 3. Tabs 1 & 3
    r3 = run_js_scenario([3], "QUICK_APPROVE")
    assert "Pages Inspected: 2/3 (Page 2 Outbound Manifest Unopened)" in r3["kpiMetric"], f"Failed Tabs 1 & 3 metric: {r3['kpiMetric']}"
    assert r3["s1b"]["case2Page1Visited"] is True
    assert r3["s1b"]["case2Page2Visited"] is False
    assert r3["s1b"]["case2Page3Visited"] is True
    assert r3["s1b"]["case2PagesVisitedCount"] == 2
    assert r3["s1b"]["case2PagesVisited"] == [1, 3]
    assert r3["s1b"]["case2PagesUnopened"] == [2]
    csv3 = parse_csv_row(r3["csv"])
    assert csv3["s1b_case2_page1_visited"] == "1"
    assert csv3["s1b_case2_page2_visited"] == "0"
    assert csv3["s1b_case2_page3_visited"] == "1"
    assert csv3["s1b_case2_pages_visited"] == "2"
    print("  ✓ Scenario 3: Tabs 1 & 3 -> 'Pages Inspected: 2/3 (Page 2 Outbound Manifest Unopened)'")

    # 4. All 3 tabs
    r4 = run_js_scenario([2, 3], "QUICK_APPROVE")
    assert "Pages Inspected: 3/3 (All 3 Pages Checked)" in r4["kpiMetric"], f"Failed All 3 tabs metric: {r4['kpiMetric']}"
    assert r4["s1b"]["case2Page1Visited"] is True
    assert r4["s1b"]["case2Page2Visited"] is True
    assert r4["s1b"]["case2Page3Visited"] is True
    assert r4["s1b"]["case2PagesVisitedCount"] == 3
    assert r4["s1b"]["case2PagesVisited"] == [1, 2, 3]
    assert r4["s1b"]["case2PagesUnopened"] == []
    csv4 = parse_csv_row(r4["csv"])
    assert csv4["s1b_case2_page1_visited"] == "1"
    assert csv4["s1b_case2_page2_visited"] == "1"
    assert csv4["s1b_case2_page3_visited"] == "1"
    assert csv4["s1b_case2_pages_visited"] == "3"
    print("  ✓ Scenario 4: All 3 tabs -> 'Pages Inspected: 3/3 (All 3 Pages Checked)'")

    # 5. Escalation path with Tab 1 only
    r5 = run_js_scenario([], "ESCALATE")
    assert "Held & Escalated" in r5["kpiMetric"]
    assert "Pages Inspected: 1/3 (Pages 2 & 3 Unopened)" in r5["kpiMetric"]
    print("  ✓ Scenario 5: Escalation path with Tab 1 only -> 'Held & Escalated at ... | Pages Inspected: 1/3 (Pages 2 & 3 Unopened)'")

    # 6. Practice Case 1 tab combinations & unopened tracking
    rc1_1 = run_js_scenario([], "QUICK_APPROVE", {"case1Sequence": []})
    assert rc1_1["s1b"]["case1Page1Visited"] is True
    assert rc1_1["s1b"]["case1Page2Visited"] is False
    assert rc1_1["s1b"]["case1Page3Visited"] is False
    assert rc1_1["s1b"]["case1PagesVisited"] == [1]
    assert rc1_1["s1b"]["case1PagesUnopened"] == [2, 3]
    assert rc1_1["s1b"]["case1PagesVisitedCount"] == 1
    assert "Pages Inspected: 1/3" in rc1_1["kpiCase1Metric"]
    csv_c1_1 = parse_csv_row(rc1_1["csv"])
    assert csv_c1_1["s1b_case1_page1_visited"] == "1"
    assert csv_c1_1["s1b_case1_page2_visited"] == "0"
    assert csv_c1_1["s1b_case1_page3_visited"] == "0"
    assert csv_c1_1["s1b_case1_pages_visited"] == "1"

    rc1_2 = run_js_scenario([], "QUICK_APPROVE", {"case1Sequence": [2]})
    assert rc1_2["s1b"]["case1PagesVisited"] == [1, 2]
    assert rc1_2["s1b"]["case1PagesUnopened"] == [3]
    assert rc1_2["s1b"]["case1PagesVisitedCount"] == 2

    rc1_3 = run_js_scenario([], "QUICK_APPROVE", {"case1Sequence": [3]})
    assert rc1_3["s1b"]["case1PagesVisited"] == [1, 3]
    assert rc1_3["s1b"]["case1PagesUnopened"] == [2]
    assert rc1_3["s1b"]["case1PagesVisitedCount"] == 2

    rc1_all = run_js_scenario([], "QUICK_APPROVE", {"case1Sequence": [2, 3]})
    assert rc1_all["s1b"]["case1PagesVisited"] == [1, 2, 3]
    assert rc1_all["s1b"]["case1PagesUnopened"] == []
    assert rc1_all["s1b"]["case1PagesVisitedCount"] == 3
    print("  ✓ Scenario 6: Practice Case 1 tab combinations & unopened tracking verified")

    # 7. Rapid alternating tab switches (e.g. 1 -> 2 -> 1 -> 3 -> 1 -> 2)
    r_alt = run_js_scenario([2, 1, 3, 1, 2], "QUICK_APPROVE")
    assert r_alt["s1b"]["case2PagesVisited"] == [1, 2, 3]
    assert r_alt["s1b"]["case2PagesUnopened"] == []
    assert "Pages Inspected: 3/3 (All 3 Pages Checked)" in r_alt["kpiMetric"]
    assert r_alt["s1b"]["case2Page1DwellMs"] >= 0
    assert r_alt["s1b"]["case2Page2DwellMs"] >= 0
    assert r_alt["s1b"]["case2Page3DwellMs"] >= 0
    print("  ✓ Scenario 7: Rapid multi-tab alternation verified")

    # 8. Arm 3 Benchmark Recall Card binding (Screen 3 Box D)
    r_bm1 = run_js_scenario([], "QUICK_APPROVE", {"arm": 3})
    assert "Pages Inspected: 1/3 (Pages 2 & 3 Unopened)" in r_bm1["arm3BenchmarkQuotaStatus"]

    r_bm2 = run_js_scenario([2], "QUICK_APPROVE", {"arm": 3})
    assert "Pages Inspected: 2/3 (Page 3 Scale Log Unopened)" in r_bm2["arm3BenchmarkQuotaStatus"]

    r_bm3 = run_js_scenario([3], "QUICK_APPROVE", {"arm": 3})
    assert "Pages Inspected: 2/3 (Page 2 Outbound Manifest Unopened)" in r_bm3["arm3BenchmarkQuotaStatus"]

    r_bm_all = run_js_scenario([2, 3], "QUICK_APPROVE", {"arm": 3})
    assert "Pages Inspected: 3/3 (All 3 Pages Checked)" in r_bm_all["arm3BenchmarkQuotaStatus"]
    assert "text-emerald-600" in r_bm_all["arm3BenchmarkClass"]

    r_bm_timeout = run_js_scenario([2], "QUICK_APPROVE", {"arm": 3, "case2TimedOut": True})
    assert "Pages Inspected: 2/3 (Page 3 Scale Log Unopened) / SLA Timeout" in r_bm_timeout["arm3BenchmarkQuotaStatus"]
    assert "text-rose-600" in r_bm_timeout["arm3BenchmarkClass"]
    print("  ✓ Scenario 8: Arm 3 Benchmark Recall Card rendering & timeouts verified")

    # 9. Application-wide CSV export schema consistency (index.html vs admin.html)
    import re
    with open(os.path.join(BASE_DIR, "index.html"), "r", encoding="utf-8") as f:
        idx_txt = f.read()
    with open(os.path.join(BASE_DIR, "admin.html"), "r", encoding="utf-8") as f:
        adm_txt = f.read()

    m_idx = re.search(r"function exportParticipantCsv\(\)\s*\{[\s\S]*?const headers = \[([\s\S]*?)\];", idx_txt)
    idx_cols = [h.strip().strip('"').strip("'") for h in m_idx.group(1).split(",") if h.strip()]
    m_adm = re.search(r"const CSV_HEADERS = \[([\s\S]*?)\];", adm_txt)
    adm_cols = [h.strip().strip('"').strip("'") for h in m_adm.group(1).split(",") if h.strip()]

    assert len(idx_cols) == 52, f"Expected 52 index CSV headers, got {len(idx_cols)}"
    assert idx_cols == adm_cols, f"Mismatch between index and admin CSV headers: {set(idx_cols) ^ set(adm_cols)}"
    print("  ✓ Scenario 9: Application-wide 52-column CSV telemetry schema verified across index.html & admin.html")

    # 10. Backwards compatibility & legacy floor state hydration
    legacy_floor = {
        "executed": True,
        "case1TotalDwellSec": 45.0,
        "case1PagesVisitedCount": 3,
        "case2TotalDwellSec": 18.0,
        "case2PagesVisitedCount": 2,
        "case2Page3Visited": False,
        "case2Action": "QUICK_APPROVE"
    }
    r_leg = run_js_scenario([], "QUICK_APPROVE", {"legacyFloorState": legacy_floor, "arm": 3})
    assert "Pages Inspected: 2/3 (Page 3 Scale Log Unopened)" in r_leg["kpiMetric"], f"Legacy metric failed: {r_leg['kpiMetric']}"
    assert "Pages Inspected: 2/3 (Page 3 Scale Log Unopened)" in r_leg["arm3BenchmarkQuotaStatus"]
    csv_leg = parse_csv_row(r_leg["csv"])
    assert csv_leg["s1b_case2_page1_visited"] == "1"
    assert csv_leg["s1b_case2_page2_visited"] == "1"
    assert csv_leg["s1b_case2_page3_visited"] == "0"
    assert csv_leg["s1b_case1_page1_visited"] == "1"
    assert csv_leg["s1b_case1_page2_visited"] == "1"
    assert csv_leg["s1b_case1_page3_visited"] == "1"
    print("  ✓ Scenario 10: Backwards compatibility & legacy floor state hydration verified")

    # 11. Practice Case 1 scorecard explicit unopened enumeration
    r_c1_p1 = run_js_scenario([], "QUICK_APPROVE", {"case1Sequence": []})
    assert "Pages Inspected: 1/3 (Pages 2 & 3 Unopened)" in r_c1_p1["kpiCase1Metric"]
    r_c1_p2 = run_js_scenario([], "QUICK_APPROVE", {"case1Sequence": [2]})
    assert "Pages Inspected: 2/3 (Page 3 Scale Log Unopened)" in r_c1_p2["kpiCase1Metric"]
    r_c1_p3 = run_js_scenario([], "QUICK_APPROVE", {"case1Sequence": [3]})
    assert "Pages Inspected: 2/3 (Page 2 Outbound Manifest Unopened)" in r_c1_p3["kpiCase1Metric"]
    r_c1_all = run_js_scenario([], "QUICK_APPROVE", {"case1Sequence": [2, 3]})
    assert "Pages Inspected: 3/3 (All 3 Pages Checked)" in r_c1_all["kpiCase1Metric"]
    print("  ✓ Scenario 11: Case 1 scorecard explicit unopened enumeration verified")

    # 12. Full Telemetry JSON export verification
    r_json = run_js_scenario([2], "QUICK_APPROVE", {"case1Sequence": []})
    assert r_json["jsonExport"], "JSON export was empty"
    sess_export = json.loads(r_json["jsonExport"])
    f_export = sess_export["s1b_floor"]
    assert f_export["case2Page1Visited"] is True
    assert f_export["case2Page2Visited"] is True
    assert f_export["case2Page3Visited"] is False
    assert f_export["case2PagesVisited"] == [1, 2]
    assert f_export["case2PagesUnopened"] == [3]
    assert f_export["case1PagesVisited"] == [1]
    assert f_export["case1PagesUnopened"] == [2, 3]
    print("  ✓ Scenario 12: Full Telemetry JSON export schema verified")

    # 13. Admin portal CSV export legacy session hydration verification
    code_adm = f"""
    const fs = require('fs');
    const vm = require('vm');
    const html = fs.readFileSync('{os.path.join(BASE_DIR, "admin.html")}', 'utf-8');
    const scriptMatch = html.match(/<script>([\\s\\S]*?)<\\/script>[\\s\\r\\n]*<\\/body>/i);
    let capturedCsv = '';
    const listeners = {{}};
    function createMockEl() {{
      return {{
        addEventListener: () => {{}},
        classList: {{ add: () => {{}}, remove: () => {{}} }},
        appendChild: () => {{}},
        removeChild: () => {{}},
        innerHTML: '',
        textContent: '',
        querySelectorAll: () => [],
        click: () => {{}}
      }};
    }}
    const sandbox = {{
      window: {{ location: {{ search: '?token=PHD2026' }}, addEventListener: () => {{}} }},
      location: {{ search: '?token=PHD2026' }},
      URLSearchParams: URLSearchParams,
      Blob: function(parts) {{ capturedCsv = parts.join(''); }},
      URL: {{ createObjectURL: () => 'blob:mock', revokeObjectURL: () => {{}} }},
      document: {{
        getElementById: (id) => {{
          if (!listeners[id]) listeners[id] = {{}};
          const el = createMockEl();
          el.addEventListener = (ev, fn) => {{ listeners[id][ev] = fn; }};
          return el;
        }},
        createElement: () => createMockEl(),
        body: createMockEl(),
        querySelectorAll: () => []
      }},
      sessionStorage: {{ getItem: () => '1', setItem: () => {{}} }},
      localStorage: {{
        getItem: (k) => {{
          if (k === 'study_sessions') {{
            return JSON.stringify([{{
              sessionId: 'LEGACY_TEST',
              pid: 'P_LEGACY',
              arm: 3,
              s1b_floor: {{
                executed: true,
                case1TotalDwellSec: 46.2,
                case1PagesVisitedCount: 3,
                case2TotalDwellSec: 18.4,
                case2PagesVisitedCount: 2,
                case2Page3Visited: false
              }}
            }}]);
          }}
          return null;
        }}
      }},
      console: console,
      Date: Date
    }};
    const context = vm.createContext(sandbox);
    vm.runInContext(scriptMatch[1], context);
    listeners['btnExportCsv']['click']();
    console.log('__ADMIN_CSV__:' + Buffer.from(capturedCsv).toString('base64'));
    listeners['btnExportJson']['click']();
    console.log('__ADMIN_JSON__:' + Buffer.from(capturedCsv).toString('base64'));
    """
    import base64
    proc_adm = subprocess.run(["node", "-e", code_adm], capture_output=True, text=True, check=True)
    adm_csv_str = ""
    adm_json_str = ""
    for line in proc_adm.stdout.splitlines():
        if line.startswith("__ADMIN_CSV__:"):
            adm_csv_str = base64.b64decode(line[len("__ADMIN_CSV__:"):].strip()).decode('utf-8')
        elif line.startswith("__ADMIN_JSON__:"):
            adm_json_str = base64.b64decode(line[len("__ADMIN_JSON__:"):].strip()).decode('utf-8')

    adm_row = parse_csv_row(adm_csv_str)
    assert adm_row["s1b_executed"] == "1"
    assert adm_row["s1b_case1_page1_visited"] == "1"
    assert adm_row["s1b_case1_page2_visited"] == "1"
    assert adm_row["s1b_case1_page3_visited"] == "1"
    assert adm_row["s1b_case2_page1_visited"] == "1"
    assert adm_row["s1b_case2_page2_visited"] == "1"
    assert adm_row["s1b_case2_page3_visited"] == "0"
    assert adm_row["s1b_case2_pages_visited"] == "2"
    print("  ✓ Scenario 13: Admin portal CSV export legacy session hydration verified")

    # 14. Admin portal JSON export legacy session hydration & state.s1b Set hydration
    adm_sessions = json.loads(adm_json_str)
    f_adm = adm_sessions[0]["s1b_floor"]
    assert f_adm["case2Page1Visited"] is True
    assert f_adm["case2Page2Visited"] is True
    assert f_adm["case2Page3Visited"] is False
    assert f_adm["case2PagesVisited"] == [1, 2]
    assert f_adm["case2PagesUnopened"] == [3]
    assert f_adm["case2PagesVisitedCount"] == 2
    assert f_adm["case1Page1Visited"] is True
    assert f_adm["case1PagesVisited"] == [1, 2, 3]
    assert f_adm["case1PagesUnopened"] == []
    print("  ✓ Scenario 14: Admin portal JSON export legacy session hydration & state.s1b Set hydration verified")

if __name__ == "__main__":
    test_tab_combination_scenarios()
    print("\nALL TAB COMBINATION INSPECTION TESTS PASSED!")
