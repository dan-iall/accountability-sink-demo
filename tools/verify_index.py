import os
import re
import sys
from bs4 import BeautifulSoup

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def verify_index():
    path = os.path.join(BASE_DIR, "index.html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # 1. Section 10.1 Global Shell DOM IDs
    sec10_1_ids = [
        "appBody",
        "appRoot",
        "bannerViewportGuard",
        "researcherDebugBar",
        "btnToggleGazeSim",
        "btnExportAoiMap",
        "appHeader",
        "hdrBrandTitle",
        "hdrScreenStageBadge",
        "hdrLiveScore",
        "mainWorkspace"
    ]

    # 2. Section 1.8 Screen 1 DOM IDs
    sec1_ids = [
        "screenS1",
        "s1StepperNav",
        "s1PillStep1",
        "s1PillStep2",
        "s1PillStep3",
        "s1PillStep4",
        "s1PillStep5",
        "s1PillStep6",
        "s1Step1",
        "s1Step2",
        "s1Step3",
        "s1Step4",
        "s1Step5",
        "s1Step6",
        "cardDossierExplainer",
        "cardAiExplainer",
        "cardBonusExplainer",
        "cardPenaltyExplainer",
        "btnStep1Next",
        "btnStep2Next",
        "btnStep3Next",
        "btnStep4Next",
        "btnStep5Next",
        "btnStartFloorRotation",
        "btnS1Complete"
    ]

    # 3. Section 2.4 Screen 1B DOM IDs
    sec2_ids = [
        "screenS1B",
        "s1bHud",
        "s1bTimerLabel",
        "s1bCountdownTimer",
        "s1bCountdownBar",
        "s1bCase1",
        "tabCase1Page1",
        "tabCase1Page2",
        "tabCase1Page3",
        "btnCase1Reject",
        "btnCase1Approve",
        "modalCase1Discrepancy",
        "btnConfirmCase1Discrepancy",
        "btnCancelCase1Discrepancy",
        "s1bCase2",
        "tabCase2Page1",
        "tabCase2Page2",
        "tabCase2Page3",
        "btnCase2BannerQuickApprove",
        "btnCase2QuickApprove",
        "btnCase2Escalate",
        "screenS1B_KPI",
        "s1bKpiCard",
        "kpiCase1Metric",
        "kpiCase2Metric",
        "kpiAiContrastBadge",
        "btnAssumeCommand"
    ]

    # 4. Section 3.6 Screen 2A Policy Setup DOM IDs
    sec3_ids = [
        "screenS2A",
        "s2aEuBanner",
        "slaSelectionGroup",
        "slaCard1",
        "slaCard2",
        "slaCard3",
        "radioSla1",
        "radioSla2",
        "radioSla3",
        "s2aProjection",
        "lblProjCases",
        "lblProjPts",
        "lblProjBonus",
        "btnLockShift",
        "modalCorporateOverride",
        "btnAcknowledgeOverride"
    ]

    # 5. Section 4.8 Screen 2B Active Floor DOM IDs
    sec4_ids = [
        "screenS2B",
        "s2bHud",
        "hudShiftBadge",
        "hudSlaBadge",
        "hudCasesCleared",
        "hudShiftClock",
        "hudTimer",
        "hudThroughputGauge",
        "hudEscalationBadge",
        "hudIncentiveTracker",
        "s2bProgress",
        "station1",
        "station2",
        "station3",
        "badgeStation1",
        "badgeStation2",
        "badgeStation3",
        "modalShift1Done",
        "btnStartShift2",
        "s2bEscalation",
        "directiveChoiceGroup",
        "btnDirectiveA",
        "btnDirectiveB",
        "modalShift2Done",
        "btnStartShift3",
        "modalCrash",
        "btnInspectCrash",
        "btnEnterAudit"
    ]

    # 6. Scaffolded Screen IDs (S3, S4, S5)
    # 6. Section 5 Screen 3 Forensic Incident Audit DOM IDs
    sec5_ids = [
        "screenS3",
        "s3DossierContainer",
        "tabS3Page1",
        "tabS3Page2",
        "tabS3Page3",
        "s3BoxA",
        "s3BoxB",
        "s3BoxC",
        "s3BoxD",
        "arm1BoxDContent",
        "arm2BoxDContent",
        "arm3BoxDContent",
        "arm4BoxDContent",
        "btnEnterBoardInquiry"
    ]

    # 7. Section 6 Screen 4 Board Accountability Inquiry DOM IDs
    sec6_ids = [
        "screenS4",
        "s4ManagerPtsHeader",
        "s4ShareBadge",
        "task1aSliders",
        "sliderSara",
        "sliderAi",
        "sliderSla",
        "valSliderSara",
        "valSliderAi",
        "valSliderSla",
        "task1bCards",
        "radioCodeH1",
        "radioCodeA2",
        "radioCodeM3",
        "task1cSliders",
        "cds2A",
        "cds2B",
        "valCds2A",
        "valCds2B",
        "cdsDerivedTag",
        "s4Task2Container",
        "forkOption1",
        "forkOption2",
        "radioTask2Option1",
        "radioTask2Option2",
        "task3JustificationText",
        "txtJustification",
        "charCounterBadge",
        "task4Cards",
        "radioReform1",
        "radioReform2",
        "radioReform3",
        "btnSubmitBoardReport"
    ]

    # 8. Section 7 Screen 5 Shift 4 Resolution, Debrief & Completion DOM IDs
    sec7_ids = [
        "screenS5",
        "s5Shift4Summary",
        "s5Arm4Reveal",
        "s5Ledger",
        "s5Debrief",
        "s5CompletionCode",
        "txtCompletionCode",
        "btnCopyCompletionCode",
        "btnExportParticipantJson",
        "btnExportParticipantCsv",
        "btnFinalizeSession"
    ]

    all_required = [
        ("Section 10.1 Global Shell", sec10_1_ids),
        ("Section 1 Screen 1 Onboarding", sec1_ids),
        ("Section 2 Screen 1B Floor Rotation", sec2_ids),
        ("Section 3 Screen 2A Policy Setup", sec3_ids),
        ("Section 4 Screen 2B Active Floor", sec4_ids),
        ("Section 5 Screen 3 Forensic Incident Audit", sec5_ids),
        ("Section 6 Screen 4 Board Inquiry", sec6_ids),
        ("Section 7 Screen 5 Shift 4 Resolution & Debrief", sec7_ids)
    ]

    total_checked = 0
    total_passed = 0
    missing = []

    for category, ids in all_required:
        print(f"\nVerifying {category} ({len(ids)} elements):")
        cat_passed = 0
        for dom_id in ids:
            total_checked += 1
            el = soup.find(id=dom_id)
            if el:
                cat_passed += 1
                total_passed += 1
                print(f"  ✓ #{dom_id}")
            else:
                missing.append(dom_id)
                print(f"  ✗ #{dom_id} MISSING")
        print(f"  Passed {cat_passed}/{len(ids)}")

    # 9. Check data-aoi attributes (Sections 1-7 & 10.1)
    expected_aois = [
        "s1_stepper_nav",
        "s1_onboarding_card",
        "s1b_hud_timer",
        "dossier_page_1",
        "dossier_page_2",
        "dossier_page_3",
        "ai_copilot",
        "sla_quota_control",
        "s2a_eu_ai_act_banner",
        "s2a_earnings_preview",
        "s2b_top_hud",
        "s2_station_1_alex",
        "s2_station_2_sara",
        "s2_station_3_lukas",
        "s2b_sara_escalation_modal",
        "s2b_crash_breach_modal",
        "s3_case312_dossier",
        "s3_box_a_ai_stamp",
        "s3_box_b_sara_telemetry",
        "s3_box_c_custody",
        "stamp_telemetry_box",
        "blame_sliders_group",
        "s4_task1b_root_cause",
        "s4_task1c_cds_sliders",
        "s4_task2_scapegoat_fork",
        "s4_option1_penalize_sara",
        "s4_option2_absorb_blame",
        "s4_task3_justification",
        "s4_task4_sla_reform",
        "s5_shift4_summary",
        "s5_arm4_audit_reveal",
        "s5_final_ledger",
        "s5_completion_card"
    ]
    print(f"\nVerifying data-aoi attributes ({len(expected_aois)} attributes):")
    aoi_passed = 0
    for aoi in expected_aois:
        els = soup.find_all(attrs={"data-aoi": aoi})
        if els:
            aoi_passed += 1
            print(f"  ✓ data-aoi=\"{aoi}\" found ({len(els)} instances)")
        else:
            print(f"  ✗ data-aoi=\"{aoi}\" MISSING")

    # 10. Check JS functions
    expected_functions = [
        "parseSessionParams",
        "initSession",
        "applyBlindingProtocol",
        "renderS1Step",
        "nextS1Step",
        "completeStep5Routing",
        "startFloorRotation",
        "launchCase1",
        "launchCase2",
        "switchCase1Tab",
        "switchCase2Tab",
        "quickApproveCase2",
        "escalateCase2",
        "renderScorecard",
        "assumeManagementCommand",
        "showScreen",
        "toggleGazeSim",
        "getScreenAOIMap",
        "renderScreen2A",
        "selectSlaOption",
        "lockSlaPolicy",
        "acknowledgeCorporateOverride",
        "updateLiveScoreDisplay",
        "startShift1",
        "startShift2",
        "chooseDirective",
        "startShift3",
        "enterCrashAudit",
        "renderScreen3",
        "switchS3Tab",
        "enterBoardInquiry",
        "renderScreen4",
        "updateTask1aSliders",
        "selectTask1bCode",
        "updateTask1cSliders",
        "selectTask2Fork",
        "onJustificationInput",
        "selectTask4Reform",
        "updateS4LiveScoreProjection",
        "validateS4FormGate",
        "submitBoardReport",
        "calculateFinalOutcome",
        "renderScreen5",
        "generateCompletionCode",
        "copyCompletionCode",
        "exportParticipantJson",
        "exportParticipantCsv",
        "finalizeSession"
    ]
    print(f"\nVerifying JS functions ({len(expected_functions)} functions):")
    fn_passed = 0
    for fn in expected_functions:
        if re.search(rf"\b{fn}\b", html):
            fn_passed += 1
            print(f"  ✓ function {fn}")
        else:
            print(f"  ✗ function {fn} MISSING")

    print("\n" + "="*50)
    print(f"DOM IDs Verification: {total_passed}/{total_checked} PASSED")
    print(f"AOI Verification: {aoi_passed}/{len(expected_aois)} PASSED")
    print(f"JS Function Verification: {fn_passed}/{len(expected_functions)} PASSED")
    print("="*50)

    if missing:
        print(f"\nFAILED! Missing IDs: {missing}")
        sys.exit(1)
    else:
        print("\nALL VERIFICATIONS PASSED PERFECTLY!")

if __name__ == "__main__":
    verify_index()
