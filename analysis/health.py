"""
health.py - translates episode PM2.5 exposure into illustrative health impacts and source contributions.

HOW IT WORKS (plain words):
1. Loads episode definitions (episodes.csv) and attribution shares (ledger_entries.csv).
2. Computes excess PM2.5 exposure above the WHO 24-hour guideline counterfactual baseline (15 ug/m3).
3. Applies peer-reviewed concentration-response relationships (WHO 2021 guidelines, Lancet Planetary Health)
   to calculate acute relative risk (RR) increases for:
   - All-cause short-term mortality risk
   - Acute respiratory morbidity (asthma exacerbation, emergency room visits)
   - Acute cardiovascular hospital admissions
4. Calculates illustrative cigarette equivalents (Berkeley Earth standard: 22 ug/m3 PM2.5 per 24 hours = 1 cigarette).
5. Apportions health impacts by source based on the Blame Ledger's estimated shares.
6. Provides demographic vulnerability stratifications (Children, Elderly, Cardiopulmonary Patients, Outdoor Workers).
7. Transparently documents all modeling assumptions and caveats upfront.

Outputs (in data/processed):
  - health_impacts.csv     : episode-level summary and source-apportioned health burdens
  - health_demographics.csv: vulnerability risk multipliers by demographic group
  - health_summary.json    : comprehensive health payload for the API and frontend dashboard

Run:
  python analysis/health.py
  (or from pipeline: python ../analysis/health.py)
"""
import json
import sys
from pathlib import Path
from typing import TypedDict

import numpy as np
import pandas as pd

# Allow importing config and common from the pipeline folder
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from common import tag_synthetic  # type: ignore

from config import PROCESSED  # type: ignore

# ----------------------------------------------------------------- Scientific Parameters
WHO_BASELINE_UGM3 = 15.0       # WHO 24-hr Air Quality Guideline counterfactual threshold
NAAQS_BASELINE_UGM3 = 60.0     # Indian National Ambient Air Quality Standard (24-hr)
BERKELEY_CIG_UGM3 = 22.0       # Berkeley Earth equivalence: 22 ug/m3 PM2.5 over 24h = 1 cigarette

# Beta coefficients per 10 ug/m3 excess PM2.5 (WHO 2021 & Lancet Planetary Health India studies)
# RR = exp(beta * excess_ugm3 / 10)
BETA_ALL_CAUSE = 0.008         # ~0.8% increase per 10 ug/m3 excess
BETA_RESPIRATORY = 0.018       # ~1.8% increase per 10 ug/m3 excess
BETA_CARDIOVASCULAR = 0.014    # ~1.4% increase per 10 ug/m3 excess


class DemographicProfile(TypedDict):
    group_id: str
    name: str
    description: str
    mortality_multiplier: float
    respiratory_multiplier: float
    cardiovascular_multiplier: float
    dose_multiplier: float
    actionable_guidance: str


DEMOGRAPHIC_PROFILES: list[DemographicProfile] = [
    {
        "group_id": "general_adult",
        "name": "General Healthy Adults (18-64)",
        "description": "Standard baseline physiological response with average indoor/outdoor time.",
        "mortality_multiplier": 1.0,
        "respiratory_multiplier": 1.0,
        "cardiovascular_multiplier": 1.0,
        "dose_multiplier": 1.0,
        "actionable_guidance": "Avoid prolonged outdoor strenuous exercise; wear N95 mask if outdoors during morning/evening peaks."
    },
    {
        "group_id": "children",
        "name": "Children & Adolescents (<15)",
        "description": "Narrower airways, developing lung tissue, and higher minute ventilation per kilogram of body weight.",
        "mortality_multiplier": 1.15,
        "respiratory_multiplier": 1.30,
        "cardiovascular_multiplier": 1.0,
        "dose_multiplier": 1.25,
        "actionable_guidance": "Suspend outdoor sports and physical education; keep classroom windows shut during high-AQI hours."
    },
    {
        "group_id": "elderly",
        "name": "Elderly (>65)",
        "description": "Reduced physiological reserve, higher baseline prevalence of underlying subclinical vascular disease.",
        "mortality_multiplier": 1.35,
        "respiratory_multiplier": 1.25,
        "cardiovascular_multiplier": 1.45,
        "dose_multiplier": 1.0,
        "actionable_guidance": "Strictly remain indoors; maintain access to prescribed cardiovascular and respiratory medications."
    },
    {
        "group_id": "cardiopulmonary",
        "name": "Patients with Asthma, COPD, or Heart Disease",
        "description": "Hyper-reactive airways and vulnerable endothelial vascular lining prone to acute systemic inflammation.",
        "mortality_multiplier": 1.50,
        "respiratory_multiplier": 1.60,
        "cardiovascular_multiplier": 1.55,
        "dose_multiplier": 1.0,
        "actionable_guidance": "Keep quick-relief inhalers immediately on hand; monitor peak expiratory flow; consult physician if symptoms escalate."
    },
    {
        "group_id": "outdoor_workers",
        "name": "Outdoor Workers & Active Commuters",
        "description": "Extended outdoor exposure (8-12 hours) coupled with elevated inhalation rates from physical labor.",
        "mortality_multiplier": 1.25,
        "respiratory_multiplier": 1.40,
        "cardiovascular_multiplier": 1.30,
        "dose_multiplier": 2.00,
        "actionable_guidance": "Mandatory employer-provided fit-tested N95 respirators; rotate strenuous work away from early morning peak smog hours."
    }
]

ASSUMPTIONS = [
    "Ambient outdoor monitor readings represent average city-wide population inhalation exposure (indoor filtration from HEPA filters or air conditioning attenuation is not modeled).",
    "Log-linear concentration-response relationships from epidemiological studies are evaluated assuming monotonic risk scaling at severe episodic levels (>200 ug/m3).",
    "Toxicity per microgram of PM2.5 is treated as uniform across sources; chemical species toxicity differences (e.g., toxic polycyclic aromatic hydrocarbons vs geological mineral dust) are not individually weighted.",
    "Counterfactual baseline is the WHO 2021 24-hour guideline of 15 ug/m3; excess risk is evaluated strictly above this counterfactual.",
    "Cigarette equivalence is derived from the Berkeley Earth mathematical model (1 cigarette/day ~ 22 ug/m3 PM2.5 over 24h) and is provided strictly as an illustrative communication metric.",
    "All figures are illustrative statistical public health projections, not individualized clinical diagnoses or official mortality statistics."
]

CITATIONS = [
    {"source": "WHO (2021)", "title": "WHO global air quality guidelines: particulate matter (PM2.5 and PM10), ozone, nitrogen dioxide, sulfur dioxide and carbon monoxide", "url": "https://iris.who.int/handle/10665/345329"},
    {"source": "Burnett et al. (2018)", "title": "Global estimates of mortality associated with long-term exposure to ambient fine particulate matter", "url": "https://doi.org/10.1073/pnas.1803222115"},
    {"source": "Muller & Muller (2015)", "title": "Air Pollution and Cigarette Equivalence", "url": "https://berkeleyearth.org/air-pollution-and-cigarette-equivalence/"},
    {"source": "Lancet Planetary Health (2020)", "title": "Health and economic impact of air pollution in the states of India: the Global Burden of Disease Study 1990-2019", "url": "https://doi.org/10.1016/S2542-5196(20)30298-9"}
]


def load_inputs():
    episodes_path = PROCESSED / "episodes.csv"
    ledger_path = PROCESSED / "ledger_entries.csv"

    if not episodes_path.exists():
        sys.exit(f"Missing {episodes_path}. Pipeline step s7 must be run first.")
    if not ledger_path.exists():
        sys.exit(f"Missing {ledger_path}. attribution.py must be run first.")

    episodes = pd.read_csv(episodes_path)
    ledger = pd.read_csv(ledger_path)

    episodes["start"] = pd.to_datetime(episodes["start"])
    episodes["end"] = pd.to_datetime(episodes["end"])
    ledger["start"] = pd.to_datetime(ledger["start"])
    ledger["end"] = pd.to_datetime(ledger["end"])

    return episodes, ledger


def calculate_health_impacts():
    episodes, ledger = load_inputs()

    impact_rows = []
    episode_summaries = []

    for _, ep in episodes.iterrows():
        ep_id = int(str(ep["episode_id"]))
        days = float(str(ep["days"]))
        pm_mean = float(str(ep["mean_daily_pm25"]))
        pm_peak = float(str(ep["peak_daily_pm25"]))
        ep_start = pd.Timestamp(str(ep["start"]))
        ep_end = pd.Timestamp(str(ep["end"]))

        # Excess exposures
        excess_who = max(0.0, pm_mean - WHO_BASELINE_UGM3)
        excess_naaqs = max(0.0, pm_mean - NAAQS_BASELINE_UGM3)

        # Baseline Relative Risks (General Adult)
        rr_all_cause = np.exp(BETA_ALL_CAUSE * excess_who / 10.0)
        rr_respiratory = np.exp(BETA_RESPIRATORY * excess_who / 10.0)
        rr_cardiovascular = np.exp(BETA_CARDIOVASCULAR * excess_who / 10.0)

        # Percentage increases
        pct_inc_mort = round((rr_all_cause - 1.0) * 100.0, 1)
        pct_inc_resp = round((rr_respiratory - 1.0) * 100.0, 1)
        pct_inc_cardio = round((rr_cardiovascular - 1.0) * 100.0, 1)

        # Population Attributable Fraction (PAF %)
        paf_all_cause = round(((rr_all_cause - 1.0) / rr_all_cause) * 100.0, 1)

        # Cigarette equivalents
        cigs_per_day = round(pm_mean / BERKELEY_CIG_UGM3, 1)
        cigs_cumulative = round(cigs_per_day * days, 1)

        # Source breakdown from ledger
        ep_ledger = ledger[ledger["episode_id"] == ep_id]
        source_breakdown = []

        for _, l in ep_ledger.iterrows():
            src = str(l["source"])
            share_mid = float(str(l["share_mid_pct"]))
            share_low = float(str(l["share_low_pct"]))
            share_high = float(str(l["share_high_pct"]))

            src_pm25 = round(pm_mean * (share_mid / 100.0), 1)
            src_cigs_day = round(cigs_per_day * (share_mid / 100.0), 2)
            src_cigs_cum = round(cigs_cumulative * (share_mid / 100.0), 1)

            # Impact row for table
            impact_rows.append({
                "episode_id": ep_id,
                "start": ep_start.strftime("%Y-%m-%d"),
                "end": ep_end.strftime("%Y-%m-%d"),
                "duration_days": int(days),
                "source": src,
                "source_share_mid_pct": share_mid,
                "source_share_low_pct": share_low,
                "source_share_high_pct": share_high,
                "attributable_pm25_ugm3": src_pm25,
                "attributable_cigarettes_daily": src_cigs_day,
                "attributable_cigarettes_total": src_cigs_cum,
                "attributable_mortality_risk_pct": round(pct_inc_mort * (share_mid / 100.0), 2),
                "attributable_respiratory_risk_pct": round(pct_inc_resp * (share_mid / 100.0), 2),
                "attributable_cardiovascular_risk_pct": round(pct_inc_cardio * (share_mid / 100.0), 2),
            })

            source_breakdown.append({
                "source": src,
                "share_mid_pct": share_mid,
                "attributable_pm25_ugm3": src_pm25,
                "attributable_cigarettes_total": src_cigs_cum,
            })

        # Demographic specific calculations
        demographic_impacts = []
        for demo in DEMOGRAPHIC_PROFILES:
            dose_mult = float(demo["dose_multiplier"])
            resp_mult = float(demo["respiratory_multiplier"])
            cardio_mult = float(demo["cardiovascular_multiplier"])

            effective_dose = float(pm_mean * dose_mult)
            demo_excess = float(max(0.0, effective_dose - WHO_BASELINE_UGM3))
            demo_rr_resp = float(np.exp(BETA_RESPIRATORY * resp_mult * demo_excess / 10.0))
            demo_rr_cardio = float(np.exp(BETA_CARDIOVASCULAR * cardio_mult * demo_excess / 10.0))
            demo_cigs = round((effective_dose / BERKELEY_CIG_UGM3) * days, 1)

            demographic_impacts.append({
                "group_id": demo["group_id"],
                "group_name": demo["name"],
                "excess_respiratory_risk_pct": round((demo_rr_resp - 1.0) * 100.0, 1),
                "excess_cardiovascular_risk_pct": round((demo_rr_cardio - 1.0) * 100.0, 1),
                "effective_cigarette_equivalents": demo_cigs,
                "guidance": demo["actionable_guidance"]
            })

        episode_summaries.append({
            "episode_id": ep_id,
            "dates": f"{ep_start.strftime('%Y-%m-%d')} to {ep_end.strftime('%Y-%m-%d')}",
            "days": int(days),
            "mean_pm25_ugm3": round(pm_mean, 1),
            "peak_pm25_ugm3": round(pm_peak, 1),
            "excess_pm25_above_who_ugm3": round(excess_who, 1),
            "excess_pm25_above_naaqs_ugm3": round(excess_naaqs, 1),
            "acute_relative_risks": {
                "all_cause_mortality_rr": round(rr_all_cause, 3),
                "all_cause_excess_risk_pct": pct_inc_mort,
                "population_attributable_fraction_pct": paf_all_cause,
                "respiratory_morbidity_rr": round(rr_respiratory, 3),
                "respiratory_excess_risk_pct": pct_inc_resp,
                "cardiovascular_morbidity_rr": round(rr_cardiovascular, 3),
                "cardiovascular_excess_risk_pct": pct_inc_cardio,
            },
            "cigarette_equivalents": {
                "daily_cigarettes_per_person": cigs_per_day,
                "cumulative_cigarettes_per_person": cigs_cumulative,
                "standard": "Berkeley Earth (22 ug/m3 over 24h = 1 cigarette)"
            },
            "source_breakdown": source_breakdown,
            "demographic_vulnerability": demographic_impacts
        })

    # Save DataFrames
    df_impacts = pd.DataFrame(impact_rows)
    df_impacts = tag_synthetic(df_impacts)
    df_impacts.to_csv(PROCESSED / "health_impacts.csv", index=False)

    df_demo = pd.DataFrame(DEMOGRAPHIC_PROFILES)
    df_demo.to_csv(PROCESSED / "health_demographics.csv", index=False)

    # Save Master JSON payload
    summary_payload = {
        "title": "Pollution Blame Ledger - Health Impact Module",
        "description": "Translates episodic PM2.5 exposure into acute health risks and source-attributable burdens.",
        "episodes": episode_summaries,
        "assumptions": ASSUMPTIONS,
        "citations": CITATIONS
    }

    with open(PROCESSED / "health_summary.json", "w") as f:
        json.dump(summary_payload, f, indent=2)

    # Formatted Console Output
    print("\n" + "=" * 80)
    print(" POLLUTION BLAME LEDGER - HEALTH IMPACT ASSESSMENT ")
    print("=" * 80)
    print(f"Evaluated {len(episodes)} episodes using WHO Air Quality Guidelines & Berkeley Earth metrics.\n")

    for ep in episode_summaries:
        print("-" * 80)
        print(f"Episode {ep['episode_id']} | {ep['dates']} ({ep['days']} days)")
        print(f"Mean PM2.5: {ep['mean_pm25_ugm3']} ug/m3 (Peak: {ep['peak_pm25_ugm3']} ug/m3)")
        print(f"Excess above WHO (15 ug/m3): +{ep['excess_pm25_above_who_ugm3']} ug/m3")
        print(f"Illustrative Exposure: {ep['cigarette_equivalents']['daily_cigarettes_per_person']} cigs/day "
              f"({ep['cigarette_equivalents']['cumulative_cigarettes_per_person']} cigarettes total per resident)")
        print(f"Acute Health Risk Elevation: +{ep['acute_relative_risks']['all_cause_excess_risk_pct']}% all-cause mortality, "
              f"+{ep['acute_relative_risks']['respiratory_excess_risk_pct']}% respiratory hospital admissions")

        print("\nSource Attribution of Cigarette Equivalents:")
        for s in ep["source_breakdown"]:
            print(f"  - {s['source'].replace('_', ' ').capitalize():<18}: {s['share_mid_pct']:>4.1f}% share -> "
                  f"{s['attributable_cigarettes_total']:>5.1f} total cigarettes")
        print()

    print("=" * 80)
    print("STATED MODELING ASSUMPTIONS & LIMITATIONS (Upfront):")
    for i, a in enumerate(ASSUMPTIONS, 1):
        print(f" {i}. {a}")
    print("=" * 80)

    print("\nOutput saved:")
    print(f"  - {PROCESSED / 'health_impacts.csv'}")
    print(f"  - {PROCESSED / 'health_demographics.csv'}")
    print(f"  - {PROCESSED / 'health_summary.json'}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    calculate_health_impacts()
