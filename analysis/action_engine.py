"""
action_engine.py - Source-to-Action Engine for the Pollution Blame Ledger.

HOW IT WORKS:
1. Reads attribution ledger entries with labels from pipeline/data/processed/ledger_labels.csv.
2. Loads human-editable policy action rules from config/actions.csv.
3. Cross-references episode dates with station_hourly_final.csv to find top localized
   hotspot stations (highest local_excess_pm25) for localized sources (dust, vehicular, industry).
4. Excludes any station flagged as 'suspect' if sensor_health.csv exists.
5. Emits proportionate, non-punitive, evidence-grounded action recommendations
   with explicit verification requirements and cautionary safeguards.
6. Writes pipeline/data/processed/action_recommendations.csv.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from common import tag_synthetic  # type: ignore

from config import PROCESSED, REF  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
CONFIG_ACTIONS = ROOT / "config" / "actions.csv"


def load_sensor_suspects() -> set[str]:
    """Returns station IDs marked suspect from sensor_health.csv if available."""
    sensor_path = PROCESSED / "sensor_health.csv"
    if not sensor_path.exists():
        return set()
    try:
        sdf = pd.read_csv(sensor_path)
        if "status" in sdf.columns and "station_id" in sdf.columns:
            suspects = set(sdf.loc[sdf["status"] == "suspect", "station_id"].unique())
            return suspects
    except Exception:
        pass
    return set()


def get_episode_hotspots(
    station_df: pd.DataFrame,
    station_names: dict[str, str],
    start_date: str,
    end_date: str,
    suspect_stations: set[str],
    top_n: int = 3,
) -> str:
    """Finds top stations with highest local excess PM2.5 during the episode."""
    mask = (station_df["time"] >= start_date) & (station_df["time"] <= end_date + " 23:59:59")
    ep_st = station_df.loc[mask]
    if ep_st.empty or "local_excess_pm25" not in ep_st.columns:
        return "City-wide monitoring network"

    # Filter out suspect stations
    valid_st = ep_st[~ep_st["station_id"].isin(suspect_stations)]
    if valid_st.empty:
        valid_st = ep_st

    # Average local excess per station
    means = valid_st.groupby("station_id")["local_excess_pm25"].mean().dropna()
    top = means.sort_values(ascending=False).head(top_n)
    if top.empty:
        return "City-wide monitoring network"

    items = []
    for sid, excess in top.items():
        name = station_names.get(sid, sid)
        items.append(f"{name} (+{excess:.1f} ug/m3 local excess)")
    return "; ".join(items)


def main():
    if not CONFIG_ACTIONS.exists():
        sys.exit(f"Missing configuration file {CONFIG_ACTIONS}.")

    ledger_labels_path = PROCESSED / "ledger_labels.csv"
    if not ledger_labels_path.exists():
        sys.exit(f"Missing {ledger_labels_path}. Run analysis/evidence_labels.py first.")

    actions_cfg = pd.read_csv(CONFIG_ACTIONS)
    ledger_df = pd.read_csv(ledger_labels_path)
    suspects = load_sensor_suspects()

    # Load station names mapping
    stations_ref_path = REF / "stations.csv"
    station_names = {}
    if stations_ref_path.exists():
        st_ref = pd.read_csv(stations_ref_path)
        station_names = dict(zip(st_ref["station_id"], st_ref["name"]))

    # Load station hourly final for hotspot analysis
    station_hourly_path = PROCESSED / "station_hourly_final.csv"
    station_df = pd.DataFrame()
    if station_hourly_path.exists():
        station_df = pd.read_csv(
            station_hourly_path,
            usecols=["time", "station_id", "local_excess_pm25", "hotspot_flag"],
        )

    recommendations = []
    for _, row in ledger_df.iterrows():
        ep_id = int(str(row["episode_id"]))
        start = str(row["start"])
        end = str(row["end"])
        source = str(row["source"])
        label = str(row["label"])
        share_mid = float(str(row["share_mid_pct"]))

        # Lookup action in config
        match = actions_cfg[(actions_cfg["source"] == source) & (actions_cfg["label"] == label)]
        if match.empty:
            # Fallback for source if specific label row is missing
            match = actions_cfg[actions_cfg["source"] == source]
        if match.empty:
            # General fallback
            match = actions_cfg[actions_cfg["source"] == "any"]

        rule = match.iloc[0]
        tier = rule["tier"]
        action = rule["action"]
        responsible = rule["responsible_party"]
        verification = rule["verification_needed"]
        caution = rule["caution"]

        # Determine target area ("where")
        if source in ("dust", "vehicular", "industry") and not station_df.empty:
            where_target = get_episode_hotspots(station_df, station_names, start, end, suspects)
        elif source == "stubble_burning":
            where_target = "North-West regional airshed (Punjab/Haryana agricultural corridors & Delhi entry gates)"
        else:
            where_target = "National Capital Region regional monitoring domain"

        # Determine evidence rationale ("why")
        has_ev = bool(pd.notna(row["evidence_for"]))
        evidence_for = str(row["evidence_for"]) if has_ev else ""
        label_reason = str(row["label_reason"])
        why_evidence = f"[{label}] {label_reason}"
        if len(evidence_for) > 0 and label == "Supported":
            primary_evidence = evidence_for.split(" | ")[0]
            why_evidence += f" Key observation: {primary_evidence}."

        recommendations.append(
            dict(
                episode_id=ep_id,
                start=start,
                end=end,
                source=source,
                share_mid_pct=share_mid,
                label=label,
                tier=tier,
                action=action,
                responsible_party=responsible,
                where_target=where_target,
                why_evidence=why_evidence,
                verification_needed=verification,
                caution=caution,
            )
        )

    rec_df = tag_synthetic(pd.DataFrame(recommendations))
    out_path = PROCESSED / "action_recommendations.csv"
    rec_df.to_csv(out_path, index=False)

    print("=" * 80)
    print(" POLLUTION BLAME LEDGER - SOURCE-TO-ACTION RECOMMENDATIONS ENGINE ")
    print("=" * 80)
    print(f"Generated {len(rec_df)} action recommendations for {ledger_df['episode_id'].nunique()} episodes.")
    print("\nSummary by Action Tier:")
    print(pd.Series(rec_df["tier"].value_counts()).to_string())

    print("\nSample Action Output (Episode 3 - Severe Post-Diwali Episode):")
    sample = pd.DataFrame(
        rec_df[rec_df["episode_id"] == 3][
            ["source", "label", "tier", "action", "responsible_party", "verification_needed"]
        ]
    )
    print(sample.to_string(index=False))
    print(f"\nSaved recommendations -> {out_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
