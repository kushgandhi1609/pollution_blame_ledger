"""
advisor.py - Precaution Advisor providing accredited, bilingual (English & Hindi)
health advisories based on current AQI, 24h forecast, and source attribution context.

HOW IT WORKS:
1. Loads the latest observed conditions from pipeline/data/processed/city_hourly_final.csv.
2. Loads the +24h forecasted air quality from pipeline/data/processed/forecast_hourly.csv.
3. Loads accredited bilingual health advisories from config/advice.csv.
4. Checks attribution ledger labels from pipeline/data/processed/ledger_labels.csv
   to add source-aware situational guidance (e.g. regional stubble smoke vs local dust/traffic).
5. Emits demographic-specific guidance for:
   - General Public
   - Children & Schools
   - Older Adults (60+)
   - Cardiopulmonary Patients (Asthma / COPD / Heart Disease)
   - Outdoor Workers
6. Tags all outputs with official citations and explicit non-medical-advice disclaimers.

Output:
  - pipeline/data/processed/advice_daily.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from common import tag_synthetic  # type: ignore

from config import PROCESSED  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
CONFIG_ADVICE = ROOT / "config" / "advice.csv"

DISCLAIMER_EN = "General public health guidance based on official CPCB/WHO advisories. Not individualized medical advice."
DISCLAIMER_HI = "आधिकारिक सीपीसीबी/डब्ल्यूएचओ परामर्श पर आधारित सामान्य सार्वजनिक स्वास्थ्य मार्गदर्शन। व्यक्तिगत चिकित्सीय सलाह नहीं।"


def pm25_to_band(pm25: float) -> str:
    if np.isnan(pm25) or pm25 < 0:
        return "moderate"
    if pm25 <= 30:
        return "good"
    if pm25 <= 60:
        return "satisfactory"
    if pm25 <= 90:
        return "moderate"
    if pm25 <= 120:
        return "poor"
    if pm25 <= 250:
        return "very_poor"
    return "severe"


def get_source_context(labels_df: pd.DataFrame) -> tuple[str, str]:
    """Generates source-aware precaution add-ons based on supported sources."""
    if labels_df.empty:
        return "", ""

    # Check the latest episode in the ledger
    latest_ep = labels_df["episode_id"].max()
    ep_rows = labels_df[labels_df["episode_id"] == latest_ep]

    stubble_supported = len(ep_rows[(ep_rows["source"] == "stubble_burning") & (ep_rows["label"] == "Supported")]) > 0
    dust_supported = len(ep_rows[(ep_rows["source"] == "dust") & (ep_rows["label"] == "Supported")]) > 0
    veh_supported = len(ep_rows[(ep_rows["source"] == "vehicular") & (ep_rows["label"] == "Supported")]) > 0

    add_en = []
    add_hi = []

    if stubble_supported:
        add_en.append(
            "Source alert: High regional biomass smoke transport detected. Keep doors and windows sealed, "
            "especially during morning and nighttime cold air inversions."
        )
        add_hi.append(
            "स्रोत चेतावनी: क्षेत्रीय पराली के धुएं का उच्च स्तर दर्ज किया गया है। सुबह और रात की ठंड में खिड़कियां-दरवाजे बंद रखें।"
        )

    if dust_supported or veh_supported:
        add_en.append(
            "Local alert: Significant local dust/traffic excess identified along major arterial corridors. "
            "Avoid high-congestion transit corridors and unpaved construction zones."
        )
        add_hi.append(
            "स्थानीय चेतावनी: प्रमुख सड़कों और निर्माण क्षेत्रों में धूल एवं ट्रैफिक का अधिक स्तर है। भीड़भाड़ वाले मार्गों से बचें।"
        )

    note_en = " ".join(add_en) if add_en else "Atmospheric dispersion is currently tracking standard seasonal baseline conditions."
    note_hi = " ".join(add_hi) if add_hi else "मौजूदा वायुमंडलीय फैलाव सामान्य मौसमी आधार रेखा के अनुरूप है।"
    return note_en, note_hi


def main():
    if not CONFIG_ADVICE.exists():
        sys.exit(f"Missing configuration file {CONFIG_ADVICE}.")

    city_hourly_path = PROCESSED / "city_hourly_final.csv"
    forecast_path = PROCESSED / "forecast_hourly.csv"
    labels_path = PROCESSED / "ledger_labels.csv"

    if not city_hourly_path.exists() or not forecast_path.exists():
        sys.exit(f"Missing required tables in {PROCESSED}.")

    advice_cfg = pd.read_csv(CONFIG_ADVICE)
    city_df = pd.read_csv(city_hourly_path, parse_dates=["time"])
    forecast_df = pd.read_csv(forecast_path, parse_dates=["issue_time", "target_time"])
    labels_df = pd.read_csv(labels_path) if labels_path.exists() else pd.DataFrame()

    # 1. Latest Observed Conditions
    latest_obs = city_df.dropna(subset=["delhi_pm25_median"]).iloc[-1]
    curr_time = latest_obs["time"]
    curr_pm25 = float(latest_obs["delhi_pm25_median"])
    curr_band = pm25_to_band(curr_pm25)

    # 2. Tomorrow's +24h Forecast
    # Match the forecast issued at or near latest_obs
    fc_subset = forecast_df[
        (forecast_df["issue_time"] == curr_time) & (forecast_df["horizon_h"] == 24)
    ]
    if fc_subset.empty:
        fc_subset = forecast_df[forecast_df["horizon_h"] == 24].iloc[-1:]

    fc_row = fc_subset.iloc[0]
    fc_time = fc_row["target_time"]
    fc_pm25 = float(fc_row["pm25_pred"])
    fc_low = float(fc_row["pm25_low"])
    fc_high = float(fc_row["pm25_high"])
    fc_band = str(fc_row["aqi_category"])

    source_note_en, source_note_hi = get_source_context(labels_df)

    groups = advice_cfg["group"].unique()
    advice_rows = []

    for grp in groups:
        # Lookup advice for current band
        curr_match = advice_cfg[(advice_cfg["aqi_band"] == curr_band) & (advice_cfg["group"] == grp)]
        curr_en = curr_match.iloc[0]["advice_en"] if not curr_match.empty else "Follow general outdoor precautions."
        curr_hi = curr_match.iloc[0]["advice_hi"] if not curr_match.empty else "सामान्य सावधानियों का पालन करें।"
        citation = curr_match.iloc[0]["source_citation"] if not curr_match.empty else "CPCB / WHO Guidelines"

        # Lookup advice for tomorrow's forecast band
        fc_match = advice_cfg[(advice_cfg["aqi_band"] == fc_band) & (advice_cfg["group"] == grp)]
        fc_en = fc_match.iloc[0]["advice_en"] if not fc_match.empty else "Maintain standard vigilance."
        fc_hi = fc_match.iloc[0]["advice_hi"] if not fc_match.empty else "सतर्कता बनाए रखें।"

        advice_rows.append(
            dict(
                date=curr_time.date(),
                evaluated_at=curr_time,
                group=grp,
                current_pm25=round(curr_pm25, 1),
                current_aqi_band=curr_band,
                current_advice_en=curr_en,
                current_advice_hi=curr_hi,
                tomorrow_date=fc_time.date(),
                tomorrow_pm25_forecast=round(fc_pm25, 1),
                tomorrow_pm25_range=f"{fc_low:.1f} - {fc_high:.1f} ug/m3",
                tomorrow_aqi_band=fc_band,
                tomorrow_advice_en=fc_en,
                tomorrow_advice_hi=fc_hi,
                source_context_en=source_note_en,
                source_context_hi=source_note_hi,
                source_citation=citation,
                disclaimer_en=DISCLAIMER_EN,
                disclaimer_hi=DISCLAIMER_HI,
            )
        )

    out_df = tag_synthetic(pd.DataFrame(advice_rows))
    out_csv = PROCESSED / "advice_daily.csv"
    out_df.to_csv(out_csv, index=False)

    print("=" * 80)
    print(" POLLUTION BLAME LEDGER - BILINGUAL PRECAUTION ADVISOR ")
    print("=" * 80)
    print(f"Current Observation  : {curr_time} -> {curr_pm25:.1f} ug/m3 [{curr_band.upper()}]")
    print(f"Tomorrow's Forecast  : {fc_time} (+24h) -> {fc_pm25:.1f} ug/m3 [{fc_band.upper()}] (80% interval: {fc_low:.1f} to {fc_high:.1f} ug/m3)")
    print(f"\nSource Situational Context:\n  [EN] {source_note_en}\n  [HI] {source_note_hi}")
    print("\nAdvisories by Demographic Vulnerability Group:")

    sample_cols = ["group", "current_aqi_band", "current_advice_en", "tomorrow_aqi_band", "tomorrow_advice_en"]
    for _, r in out_df[sample_cols].iterrows():
        grp = str(r["group"]).upper().replace("_", " ")
        c_band = str(r["current_aqi_band"])
        c_adv = str(r["current_advice_en"])
        t_band = str(r["tomorrow_aqi_band"])
        t_adv = str(r["tomorrow_advice_en"])
        print(f"\n• {grp}:")
        print(f"  Now ({c_band})       : {c_adv}")
        print(f"  Tomorrow ({t_band}): {t_adv}")

    print(f"\nSaved daily advice table -> {out_csv}")
    print("=" * 80)


if __name__ == "__main__":
    main()
