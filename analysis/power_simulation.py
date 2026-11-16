"""Econometric simulation, parameter recovery, and power calibration for the 4-arm RCT."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import norm

SEED = 2026
N_PER_ARM = 60
OUT_DIR = Path(__file__).resolve().parent
CSV_PATH = OUT_DIR / "synthetic_cohort_N240.csv"

CSV_HEADERS = [
    "pid", "session_id", "timestamp_iso", "status", "arm", "D2_stamp", "D3_embodied",
    "D4_eu_ai_act", "speed_multiplier", "station_metadata", "sla_tier1", "sla_tier2",
    "sla_tier3", "target_pts", "shift_duration_sec", "s1b_executed", "s1b_case1_dwell_sec",
    "s1b_case1_pages_visited", "s1b_case1_page1_visited", "s1b_case1_page2_visited",
    "s1b_case1_page3_visited", "s1b_case2_dwell_sec", "s1b_case2_page1_visited",
    "s1b_case2_page2_visited", "s1b_case2_page3_visited", "s1b_case2_pages_visited",
    "s1b_case2_action", "s2a_initial_sla_pref_sec", "s2a_initial_archetype",
    "s2a_override_triggered", "s2b_shift2_directive", "s3_dwell_total_ms",
    "s3_page3_opened", "s3_box_d_dwell_ms", "Task1A_slider_sara", "Task1A_slider_ai",
    "Task1A_slider_sla", "Task1A_Derived_Sara_Share_Pct", "Task1B_Root_Cause_Code",
    "Task1C_CDS_Controllability_Sara", "Task1C_CDS_SLA_Constraint",
    "Task2_Penalize_Sara_Binary", "Task2_Choice_Label", "Task3_Justification_Char_Len",
    "Task3_Justification_Text", "Task4_Shift4_Sla_Reform_Sec",
    "Task4_Shift4_Compliant_Binary", "final_score_pts", "bonus_unlocked_binary",
    "integrity_credit_binary", "final_payout_eur", "completion_code",
]


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def generate_synthetic_cohort(n_per_arm: int = N_PER_ARM, seed: int = SEED) -> pd.DataFrame:
    """Simulate an N=240 (60/arm) 52-column cohort matching index.html's CSV schema."""
    rng = np.random.default_rng(seed)
    np.random.seed(seed)
    arms = np.repeat([1, 2, 3, 4], n_per_arm)
    rng.shuffle(arms)
    n = len(arms)

    d2 = (arms == 2).astype(int)
    d3 = (arms == 3).astype(int)
    d4 = (arms == 4).astype(int)

    # Pre-treatment baseline covariates (Screen 1B untimed Case 1 ~46.8s; Case 2 25.0s SLA)
    c1_dwell = np.round(np.clip(rng.normal(46.8, 6.2, n), 22.0, 75.0), 2)
    c1_p1 = np.ones(n, dtype=int)
    c1_p2 = rng.binomial(1, 0.92, n)
    c1_p3 = rng.binomial(1, 0.85, n)
    c1_pages = c1_p1 + c1_p2 + c1_p3

    c2_dwell = np.round(np.clip(rng.normal(21.4 - 1.2 * d3, 2.6, n), 8.0, 25.0), 2)
    c2_p1 = np.ones(n, dtype=int)
    c2_p2 = rng.binomial(1, 0.58 - 0.14 * d3, n)
    c2_p3 = rng.binomial(1, 0.34 - 0.12 * d3, n)
    c2_pages = c2_p1 + c2_p2 + c2_p3
    c2_action = np.where((c2_p3 == 1) & (rng.random(n) < 0.72), "ESCALATE", "QUICK_APPROVE")

    # Screen 2A policy setup (corporate override forced to 25.0s whenever preference > 25.0s)
    sla_choices = rng.choice([25.0, 38.0, 60.0], size=n, p=[0.22, 0.43, 0.35])
    arch_map = {25.0: "FAST_THROUGHPUT", 38.0: "BALANCED", 60.0: "SAFE_QUALITY"}
    sla_arch = [arch_map[float(v)] for v in sla_choices]
    override_trig = (sla_choices > 25.0).astype(int)

    # Screen 2B Shift 2 directive: Arm 3 elevates B_SLOW_FLOOR vs pooled {1, 2, 4}
    p_slow = _sigmoid(-1.15 + 1.35 * d3 + 0.25 * (sla_choices >= 38.0))
    shift2_b = rng.binomial(1, p_slow)
    shift2_dir = np.where(shift2_b == 1, "B_SLOW_FLOOR", "A_TRUST_AI")

    # Screen 3 forensic inspection telemetry
    s3_page3 = rng.binomial(1, _sigmoid(-0.2 + 0.65 * d2 + 1.15 * d3 + 1.45 * d4))
    s3_box_d_ms = np.round(
        np.clip(rng.normal(5200 + 2600 * d2 + 4100 * d3 + 5200 * d4, 1400, n), 1200, 24000)
    ).astype(int)
    s3_total_ms = (
        s3_box_d_ms + np.round(np.clip(rng.normal(14500 + 3000 * s3_page3, 3200, n), 6000, 38000)).astype(int)
    )

    # Screen 4 Stage I: Continuous blame sliders (0-10) & CDS controllability (1-9)
    latent_sys = 0.45 * (c1_dwell - 46.8) / 6.2 + 0.55 * (sla_choices >= 38.0) + rng.normal(0, 0.65, n)
    sl_sara = np.round(np.clip(6.6 - 1.15 * d2 - 1.85 * d3 - 2.35 * d4 - 0.55 * latent_sys + rng.normal(0, 1.1, n), 0.5, 10.0), 1)
    sl_ai = np.round(np.clip(3.2 + 1.65 * d2 + 0.45 * d3 + 0.70 * d4 + rng.normal(0, 1.0, n), 0.5, 10.0), 1)
    sl_sla = np.round(np.clip(3.8 + 0.50 * d2 + 2.15 * d3 + 1.85 * d4 + 0.65 * latent_sys + rng.normal(0, 1.0, n), 0.5, 10.0), 1)
    sara_share = np.round(100.0 * sl_sara / (sl_sara + sl_ai + sl_sla), 2)

    cds_sara = np.clip(np.rint(6.1 - 0.8 * d2 - 1.6 * d3 - 1.8 * d4 + rng.normal(0, 1.1, n)), 1, 9).astype(int)
    cds_sla = np.clip(np.rint(4.6 + 0.6 * d2 + 2.1 * d3 + 1.9 * d4 + rng.normal(0, 1.1, n)), 1, 9).astype(int)
    rc_code = np.where(sara_share >= 44.0, "H1", np.where(sl_ai >= sl_sla, "A2", "M3"))

    # Screen 4 Stage II: Binary sanctioning (Control p1 ~0.55-0.62; treatments reduce scapegoating)
    p_penalize = _sigmoid(0.42 - 0.85 * d2 - 1.35 * d3 - 1.95 * d4 - 0.35 * (latent_sys - 0.43))
    penalize = rng.binomial(1, p_penalize)
    choice_lbl = np.where(penalize == 1, "PENALIZE_SARA", "ABSORB_BLAME")

    # Task 4 reform choice (60s compliant yields 300 pts; 25s/38s yield 260 pts settlement)
    reform_sec = np.where(rng.random(n) < _sigmoid(-0.8 + 0.5 * d2 + 1.1 * d3 + 1.6 * d4), 60.0,
                          np.where(rng.random(n) < 0.55, 38.0, 25.0))
    reform_comp = (reform_sec == 60.0).astype(int)

    # Exact calculateFinalOutcome() payoff accounting (s4 settlement fixed at 260 unless compliant 60s)
    s2_pts = np.where(shift2_b == 1, 320, 360)
    hold_rel = np.where((arms < 4) & (penalize == 1), 300, 0)
    reg_adj = np.where(arms == 4, np.where(penalize == 1, -50, 100), 0)
    s4_pts = np.where(reform_comp == 1, 300, 260)
    final_pts = 360 + s2_pts + 270 - 300 + hold_rel + reg_adj + s4_pts
    bonus_bin = ((arms < 4) & (final_pts >= 1200)).astype(int)
    integ_bin = ((arms == 4) & (penalize == 0)).astype(int)
    payout_eur = np.round(2.50 + 4.00 * bonus_bin + 1.00 * integ_bin, 2)
    just_texts = [
        f"Reviewed Page 3 weight discrepancy and {int(sara_share[i])}% attribution across Shift 3 telemetry."
        for i in range(n)
    ]
    just_lens = [len(t) for t in just_texts]
    pids = [f"P{1001 + i}" for i in range(n)]
    sids = [f"SIM-{100000 + i}" for i in range(n)]
    codes = [f"DEMO-DONE-{1000 + i}" for i in range(n)]

    df = pd.DataFrame({
        "pid": pids, "session_id": sids,
        "timestamp_iso": ["2026-11-16T12:00:00Z"] * n, "status": ["COMPLETED"] * n,
        "arm": arms, "D2_stamp": d2, "D3_embodied": d3, "D4_eu_ai_act": d4,
        "speed_multiplier": np.ones(n, dtype=int), "station_metadata": ["desktop_1x"] * n,
        "sla_tier1": np.full(n, 25.0), "sla_tier2": np.full(n, 38.0), "sla_tier3": np.full(n, 60.0),
        "target_pts": np.full(n, 1200), "shift_duration_sec": np.full(n, 25.0),
        "s1b_executed": np.ones(n, dtype=int), "s1b_case1_dwell_sec": c1_dwell,
        "s1b_case1_pages_visited": c1_pages, "s1b_case1_page1_visited": c1_p1,
        "s1b_case1_page2_visited": c1_p2, "s1b_case1_page3_visited": c1_p3,
        "s1b_case2_dwell_sec": c2_dwell, "s1b_case2_page1_visited": c2_p1,
        "s1b_case2_page2_visited": c2_p2, "s1b_case2_page3_visited": c2_p3,
        "s1b_case2_pages_visited": c2_pages, "s1b_case2_action": c2_action,
        "s2a_initial_sla_pref_sec": sla_choices, "s2a_initial_archetype": sla_arch,
        "s2a_override_triggered": override_trig, "s2b_shift2_directive": shift2_dir,
        "s3_dwell_total_ms": s3_total_ms, "s3_page3_opened": s3_page3,
        "s3_box_d_dwell_ms": s3_box_d_ms, "Task1A_slider_sara": sl_sara,
        "Task1A_slider_ai": sl_ai, "Task1A_slider_sla": sl_sla,
        "Task1A_Derived_Sara_Share_Pct": sara_share, "Task1B_Root_Cause_Code": rc_code,
        "Task1C_CDS_Controllability_Sara": cds_sara, "Task1C_CDS_SLA_Constraint": cds_sla,
        "Task2_Penalize_Sara_Binary": penalize, "Task2_Choice_Label": choice_lbl,
        "Task3_Justification_Char_Len": just_lens, "Task3_Justification_Text": just_texts,
        "Task4_Shift4_Sla_Reform_Sec": reform_sec,
        "Task4_Shift4_Compliant_Binary": reform_comp, "final_score_pts": final_pts,
        "bonus_unlocked_binary": bonus_bin, "integrity_credit_binary": integ_bin,
        "final_payout_eur": payout_eur, "completion_code": codes,
    })
    return df[CSV_HEADERS]


def run_model_1_sanctioning(df: pd.DataFrame) -> None:
    """Model 1: Binary sanctioning LPM (HC3), Logit AMEs, and pooled Shift 2 contrast."""
    print("\n=== MODEL 1: BINARY SANCTIONING (Task2_Penalize_Sara_Binary) ===")
    # Omit s2b_shift2_directive in 4-arm ATEs to prevent post-treatment collider bias
    lpm = smf.ols(
        "Task2_Penalize_Sara_Binary ~ D2_stamp + D3_embodied + D4_eu_ai_act + s1b_case1_dwell_sec + s2a_initial_sla_pref_sec",
        data=df,
    ).fit(cov_type="HC3")
    print("OLS LPM (HC3) Treatment ATEs:")
    for term in ["D2_stamp", "D3_embodied", "D4_eu_ai_act"]:
        print(f"  {term:14s}: coef={lpm.params[term]:+.4f} (SE={lpm.bse[term]:.4f}, p={lpm.pvalues[term]:.4f})")

    logit = smf.logit(
        "Task2_Penalize_Sara_Binary ~ D2_stamp + D3_embodied + D4_eu_ai_act + s1b_case1_dwell_sec + s2a_initial_sla_pref_sec",
        data=df,
    ).fit(disp=False)
    mfx = logit.get_margeff(at="overall")
    print("Logit Average Marginal Effects (overall):")
    for idx, name in enumerate(["D2_stamp", "D3_embodied", "D4_eu_ai_act"]):
        print(f"  {name:14s}: dy/dx={mfx.margeff[idx]:+.4f} (SE={mfx.margeff_se[idx]:.4f}, p={mfx.pvalues[idx]:.4f})")

    df_s2 = df.assign(shift2_slow=(df["s2b_shift2_directive"] == "B_SLOW_FLOOR").astype(int))
    s2_fit = smf.ols("shift2_slow ~ D3_embodied", data=df_s2).fit(cov_type="HC3")
    print(f"Pooled Shift 2 Contrast (Arm 3 n=60 vs {{1,2,4}} n=180): {s2_fit.params['D3_embodied']:+.4f} (SE={s2_fit.bse['D3_embodied']:.4f}, p={s2_fit.pvalues['D3_embodied']:.4f})")


def run_model_2_blame_share(df: pd.DataFrame) -> None:
    """Model 2: Papke & Wooldridge (1996) Fractional Logit + stacked Blame-Distortion."""
    print("\n=== MODEL 2: BOUNDED BLAME SHARE & WITHIN-SUBJECT DISTORTION ===")
    work = df.copy()
    work["sara_share_frac"] = work["Task1A_Derived_Sara_Share_Pct"] / 100.0
    frac = smf.glm(
        "sara_share_frac ~ D2_stamp + D3_embodied + D4_eu_ai_act + s1b_case1_dwell_sec + s2a_initial_sla_pref_sec",
        data=work,
        family=sm.families.Binomial(),
    ).fit(cov_type="HC3")
    print("Papke-Wooldridge (1996) Fractional Logit (HC3, log-odds):")
    for term in ["D2_stamp", "D3_embodied", "D4_eu_ai_act"]:
        print(f"  {term:14s}: coef={frac.params[term]:+.4f} (SE={frac.bse[term]:.4f}, p={frac.pvalues[term]:.4f})")

    # Stacked within-subject Blame-Distortion: Stage I (MoneyTask=0) vs Stage II (MoneyTask=1)
    t0 = work[["pid", "D2_stamp", "D3_embodied", "D4_eu_ai_act"]].assign(MoneyTask=0, Y=work["sara_share_frac"])
    t1 = work[["pid", "D2_stamp", "D3_embodied", "D4_eu_ai_act"]].assign(MoneyTask=1, Y=work["Task2_Penalize_Sara_Binary"].astype(float))
    stacked = pd.concat([t0, t1], ignore_index=True)
    dist_fit = smf.ols(
        "Y ~ (D2_stamp + D3_embodied + D4_eu_ai_act) * MoneyTask",
        data=stacked,
    ).fit(cov_type="cluster", cov_kwds={"groups": stacked["pid"]})
    print("Stacked Within-Subject Blame-Distortion (Clustered by pid):")
    for term in ["MoneyTask", "D2_stamp:MoneyTask", "D3_embodied:MoneyTask", "D4_eu_ai_act:MoneyTask"]:
        print(f"  {term:22s}: coef={dist_fit.params[term]:+.4f} (SE={dist_fit.bse[term]:.4f}, p={dist_fit.pvalues[term]:.4f})")
def _trimmed_means(y: np.ndarray, trim_frac: float) -> tuple[float, float]:
    """Return (lower_mean_trim_top, upper_mean_trim_bottom) after trimming trim_frac."""
    if trim_frac <= 0.0:
        m = float(np.mean(y))
        return m, m
    n_keep = max(1, int(np.floor(len(y) * (1.0 - trim_frac))))
    y_sorted = np.sort(y)
    return float(np.mean(y_sorted[:n_keep])), float(np.mean(y_sorted[-n_keep:]))


def run_model_3_lee_bounds(df: pd.DataFrame, seed: int = SEED) -> None:
    """Model 3: Lee (2009) trimming bounds under simulated differential timeout attrition."""
    print("\n=== MODEL 3: LEE (2009) TIMER ATTRITION TRIMMING BOUNDS ===")
    rng = np.random.default_rng(seed + 1)
    keep_prob = df["arm"].map({1: 0.95, 2: 0.93, 3: 0.85, 4: 0.92}).to_numpy()
    observed = rng.binomial(1, keep_prob) == 1
    df_obs = df.assign(observed=observed)

    y1 = df_obs.loc[(df_obs["arm"] == 1) & df_obs["observed"], "Task2_Penalize_Sara_Binary"].to_numpy()
    r1 = float(df_obs.loc[df_obs["arm"] == 1, "observed"].mean())
    for k, label in [(2, "D2_stamp"), (3, "D3_embodied"), (4, "D4_eu_ai_act")]:
        yk = df_obs.loc[(df_obs["arm"] == k) & df_obs["observed"], "Task2_Penalize_Sara_Binary"].to_numpy()
        rk = float(df_obs.loc[df_obs["arm"] == k, "observed"].mean())
        naive = float(np.mean(yk) - np.mean(y1))
        if r1 >= rk:
            q = (r1 - rk) / r1
            y1_low, y1_high = _trimmed_means(y1, q)
            lb, ub = float(np.mean(yk) - y1_high), float(np.mean(yk) - y1_low)
        else:
            q = (rk - r1) / rk
            yk_low, yk_high = _trimmed_means(yk, q)
            lb, ub = float(yk_low - np.mean(y1)), float(yk_high - np.mean(y1))
        print(f"  {label:14s}: ret=({rk:.3f} vs {r1:.3f}, q={q:.3f}) naive={naive:+.4f} Lee=[{lb:+.4f}, {ub:+.4f}]")


def _binary_mde_fixed_point(n1: int, n2: int, p1: float = 0.50, r2: float = 0.18, alpha: float = 0.05, power: float = 0.80) -> float:
    """Solve fixed-point binary MDE delta_p under covariate adjustment (1 - r2)."""
    c = float(norm.ppf(1.0 - alpha / 2.0) + norm.ppf(power))
    dp = c * np.sqrt((1.0 - r2) * p1 * (1.0 - p1) * (1.0 / n1 + 1.0 / n2))
    for _ in range(50):
        p2 = p1 - dp
        dp = c * np.sqrt((1.0 - r2) * (p1 * (1.0 - p1) / n1 + p2 * (1.0 - p2) / n2))
    return float(dp)


def run_model_4_power_table() -> None:
    """Model 4: Closed-form parameterized power & MDE calibration table."""
    print("\n=== MODEL 4: CLOSED-FORM POWER & MDE CALIBRATION (alpha=0.05, 1-beta=0.80, p1=0.50) ===")
    c = float(norm.ppf(0.975) + norm.ppf(0.80))
    for label, n_arm, n_total in [("N1=240 (n=60/arm)", 60, 240), ("N2=480 (n=120/arm)", 120, 480)]:
        d_unadj = c * np.sqrt(2.0 / n_arm)
        d_adj = c * np.sqrt(2.0 * (1.0 - 0.18) / n_arm)
        dp_adj = 100.0 * _binary_mde_fixed_point(n_arm, n_arm, p1=0.50, r2=0.18)
        print(f"  {label:18s}: d_unadj={d_unadj:.3f} SD | d_adj(R2=0.18)={d_adj:.3f} SD | binary_dp(R2=0.18)={dp_adj:.2f} pp")
    dp_shift2 = 100.0 * c * np.sqrt(0.50 * 0.50 * (1.0 / 60.0 + 1.0 / 180.0))
    print(f"  Pooled Shift 2 (Arm 3 n=60 vs {{1,2,4}} n=180, R2=0.00): binary_dp={dp_shift2:.2f} pp")


def main() -> None:
    df = generate_synthetic_cohort()
    df.to_csv(CSV_PATH, index=False)
    print(f"Exported {len(df)} rows x {df.shape[1]} columns to {CSV_PATH}")
    print("Arm breakdown (n, penalize_rate, mean_sara_share_pct, shift2_slow_rate):")
    summary = df.groupby("arm").agg(
        n=("pid", "count"),
        penalize_rate=("Task2_Penalize_Sara_Binary", "mean"),
        sara_share=("Task1A_Derived_Sara_Share_Pct", "mean"),
        shift2_slow=("s2b_shift2_directive", lambda s: float(np.mean(s == "B_SLOW_FLOOR"))),
    )
    print(summary.round(4))
    run_model_1_sanctioning(df)
    run_model_2_blame_share(df)
    run_model_3_lee_bounds(df)
    run_model_4_power_table()


if __name__ == "__main__":
    main()
