"""Step 7 - assemble the final analysis-ready tables and the data dictionary.

Outputs in data/processed/:
  city_hourly_final.csv       one row per hour: Delhi/NCR aggregates + weather + fire-pathway + regime   (MAIN TABLE)
  station_hourly_final.csv    one row per station-hour: station features + the city/weather/trajectory columns
  city_daily_final.csv        one row per day, with episode ids
  episodes.csv                detected pollution episodes
  data_dictionary.csv         every column: group, meaning, unit, source, look-ahead flag
  traj_central_tracks.csv     central back-trajectory per hour (for the map)
data/reference/reference_apportionment_TEMPLATE.csv  (blank: fill from published studies for backtesting)
"""
import re
import shutil

import numpy as np
import pandas as pd

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pipeline.config import *  # noqa: F401,F403
from pipeline.common import tag_synthetic

# (name, group, description, unit, source, look_ahead)
D = [
    ("station_id", "id", "Station identifier", "", "stations.csv", 0),
    ("time", "id", "Hour-beginning timestamp, IST", "", "", 0),
    ("period_id", "id", "Index of the study period (see config PERIODS)", "", "", 0),
    ("synthetic", "id", "1 = synthetic test data, NOT real", "", "make_synthetic.py", 0),
    ("region", "meta", "Delhi or NCR (check needs_review in stations.csv)", "", "stations.csv", 0),
    ("lat", "meta", "Station latitude", "deg", "stations.csv", 0),
    ("lon", "meta", "Station longitude", "deg", "stations.csv", 0),
    ("pm25", "pollutant", "PM2.5 after QC", "ug/m3", "CPCB/OpenAQ", 0),
    ("pm10", "pollutant", "PM10 after QC", "ug/m3", "CPCB/OpenAQ", 0),
    ("no2", "pollutant", "NO2 after QC", "ug/m3", "CPCB/OpenAQ", 0),
    ("so2", "pollutant", "SO2 after QC", "ug/m3", "CPCB/OpenAQ", 0),
    ("co", "pollutant", "CO after QC", "mg/m3", "CPCB/OpenAQ", 0),
    ("o3", "pollutant", "O3 after QC", "ug/m3", "CPCB/OpenAQ", 0),
    ("qc_pm_inconsistent", "qc", "1 if PM2.5 > 1.2*PM10 + 10 (one of the two channels is suspect)", "flag", "derived", 0),
    ("hour", "time", "Hour of day (IST)", "h", "derived", 0),
    ("dow", "time", "Day of week, Monday=0", "", "derived", 0),
    ("month", "time", "Month number", "", "derived", 0),
    ("is_weekend", "time", "1 on Saturday/Sunday", "flag", "derived", 0),
    ("hour_sin", "time", "sin(2*pi*hour/24)", "", "derived", 0),
    ("hour_cos", "time", "cos(2*pi*hour/24)", "", "derived", 0),
    ("is_rush_am", "time", "1 for 07-10 h", "flag", "derived", 0),
    ("is_rush_pm", "time", "1 for 17-21 h", "flag", "derived", 0),
    ("is_night", "time", "1 for 22-05 h", "flag", "derived", 0),
    ("days_from_diwali", "time", "Signed days to nearest Diwali (NaN beyond 30 days)", "days", "config", 0),
    ("diwali_window", "time", "1 within 2 days of Diwali", "flag", "config", 0),
    ("pm25_pm10_ratio", "ratio", "PM2.5/PM10 (needs PM10>=20, no QC inconsistency)", "", "derived", 0),
    ("pm10_pm25_ratio", "ratio", "PM10/PM2.5 (needs PM2.5>=10)", "", "derived", 0),
    ("pm25_lag1h", "temporal", "PM2.5 one hour earlier (same station)", "ug/m3", "derived", 0),
    ("pm25_lag3h", "temporal", "PM2.5 three hours earlier", "ug/m3", "derived", 0),
    ("pm25_lag24h", "temporal", "PM2.5 24 hours earlier", "ug/m3", "derived", 0),
    ("pm25_roll3h", "temporal", "Trailing 3-hour mean PM2.5", "ug/m3", "derived", 0),
    ("pm25_roll6h", "temporal", "Trailing 6-hour mean PM2.5", "ug/m3", "derived", 0),
    ("pm25_roll24h", "temporal", "Trailing 24-hour mean PM2.5", "ug/m3", "derived", 0),
    ("pm25_diff1h", "temporal", "PM2.5 change over 1 hour", "ug/m3", "derived", 0),
    ("pm25_diff3h", "temporal", "PM2.5 change over 3 hours", "ug/m3", "derived", 0),
    ("pm25_diff24h", "temporal", "PM2.5 change over 24 hours", "ug/m3", "derived", 0),
    ("rising_3h", "temporal", "1 if PM2.5 rose >20 ug/m3 and >15% in 3 h", "flag", "derived", 0),
    ("fp_traffic_z", "fingerprint", "Mean z-score of NO2 and CO vs station's trailing 7-day history (traffic)", "z", "derived", 0),
    ("fp_traffic_rush_ratio_no2", "fingerprint", "Daily mean NO2 in rush hours / 12-15 h NO2 (traffic); uses the whole day", "ratio", "derived", 1),
    ("fp_traffic_rush_ratio_co", "fingerprint", "Same for CO", "ratio", "derived", 1),
    ("fp_dust_ratio", "fingerprint", "PM10/PM2.5 (dust)", "ratio", "derived", 0),
    ("fp_dust_z", "fingerprint", "z-score of PM10/PM2.5 vs trailing 30-day history", "z", "derived", 0),
    ("fp_industrial_so2_z", "fingerprint", "z-score of SO2 vs trailing 7-day history (industrial/coal)", "z", "derived", 0),
    ("fp_biomass_ratio", "fingerprint", "PM2.5/PM10 (biomass burning)", "ratio", "derived", 0),
    ("fp_biomass_night_rise", "fingerprint", "Night (22-05 h) minus afternoon (12-17 h) PM2.5; uses later hours", "ug/m3", "derived", 1),
    ("regional_background_pm25", "local_regional", "10th percentile of PM2.5 across valid stations of the same region", "ug/m3", "derived", 0),
    ("local_excess_pm25", "local_regional", "Station PM2.5 minus regional background", "ug/m3", "derived", 0),
    ("local_excess_share", "local_regional", "local_excess / PM2.5, clipped to 0-1", "", "derived", 0),
    ("pm25_robust_z", "local_regional", "Robust z of PM2.5 across stations of the region at that hour", "z", "derived", 0),
    ("hotspot_flag", "local_regional", "1 if robust z>2.5 and >40 ug/m3 above the regional median", "flag", "derived", 0),
    ("delhi_pm25_median", "city", "Median PM2.5 across valid Delhi stations (main target-like series)", "ug/m3", "derived", 0),
    ("delhi_pm25_mean", "city", "Mean PM2.5 across valid Delhi stations", "ug/m3", "derived", 0),
    ("delhi_pm25_p10", "city", "10th percentile across Delhi stations", "ug/m3", "derived", 0),
    ("delhi_pm25_p90", "city", "90th percentile across Delhi stations", "ug/m3", "derived", 0),
    ("delhi_n_valid", "city", "Number of Delhi stations with valid PM2.5", "count", "derived", 0),
    ("delhi_n_stations", "city", "Number of Delhi stations kept after QC", "count", "derived", 0),
    ("delhi_pm25_spread", "city", "(P75-P25)/median across Delhi stations", "", "derived", 0),
    ("delhi_pm10_median", "city", "Delhi median PM10", "ug/m3", "derived", 0),
    ("delhi_no2_median", "city", "Delhi median NO2", "ug/m3", "derived", 0),
    ("delhi_so2_median", "city", "Delhi median SO2", "ug/m3", "derived", 0),
    ("delhi_co_median", "city", "Delhi median CO", "mg/m3", "derived", 0),
    ("delhi_o3_median", "city", "Delhi median O3", "ug/m3", "derived", 0),
    ("delhi_regional_background_pm25", "local_regional", "Delhi regional background (10th percentile)", "ug/m3", "derived", 0),
    ("delhi_background_share", "local_regional", "background / Delhi median, 0-1 (regional share of the pollution)", "", "derived", 0),
    ("delhi_hotspot_count", "local_regional", "Number of Delhi stations flagged as hotspots", "count", "derived", 0),
    ("frac_rising_delhi", "ncr", "Share of valid Delhi stations with rising_3h", "", "derived", 0),
    ("ncr_pm25_median", "ncr", "Median PM2.5 across valid NCR stations", "ug/m3", "derived", 0),
    ("ncr_n_valid", "ncr", "Number of NCR stations with valid PM2.5", "count", "derived", 0),
    ("ncr_n_stations", "ncr", "NCR stations kept after QC", "count", "derived", 0),
    ("frac_rising_ncr", "ncr", "Share of valid NCR stations with rising_3h", "", "derived", 0),
    ("ncr_minus_delhi_pm25", "ncr", "NCR median minus Delhi median", "ug/m3", "derived", 0),
    ("ncr_to_delhi_ratio", "ncr", "NCR median / Delhi median", "", "derived", 0),
    ("delhi_ncr_corr24h", "ncr", "Trailing 24 h correlation of Delhi and NCR median series", "", "derived", 0),
    ("delhi_pm25_24h_mean", "city", "Trailing 24 h mean of Delhi median PM2.5", "ug/m3", "derived", 0),
    ("delhi_pm25_diff3h", "city", "3 h change of Delhi median PM2.5", "ug/m3", "derived", 0),
    ("delhi_pm25_diff24h", "city", "24 h change of Delhi median PM2.5", "ug/m3", "derived", 0),
    ("delhi_aqi_category_24h", "city", "CPCB PM2.5 category from the 24 h mean", "", "derived", 0),
    ("regime", "ncr", "Rule-based scale of the episode (widespread / Delhi-concentrated / NCR-concentrated / mixed / no rise / insufficient data); heuristic", "", "derived", 0),
    ("delhi_missing_frac", "qc", "Share of Delhi stations missing at this hour", "", "derived", 0),
    ("ncr_missing_frac", "qc", "Share of NCR stations missing at this hour", "", "derived", 0),
    ("missing_data_warning", "qc", "1 if either region is missing >40% of stations", "flag", "derived", 0),
    ("temp_c", "weather", "2 m temperature", "C", "Open-Meteo", 0),
    ("rh_pct", "weather", "Relative humidity", "%", "Open-Meteo", 0),
    ("precip_mm", "weather", "Precipitation", "mm", "Open-Meteo", 0),
    ("pressure_hpa", "weather", "Surface pressure", "hPa", "Open-Meteo", 0),
    ("cloud_pct", "weather", "Cloud cover", "%", "Open-Meteo", 0),
    ("wind_speed_ms", "weather", "10 m wind speed", "m/s", "Open-Meteo", 0),
    ("wind_speed_100m_ms", "weather", "100 m wind speed", "m/s", "Open-Meteo", 0),
    ("wind_dir_deg", "weather", "10 m wind direction (from)", "deg", "Open-Meteo", 0),
    ("wind_u", "weather", "East-west wind component of air motion", "m/s", "derived", 0),
    ("wind_v", "weather", "North-south wind component of air motion", "m/s", "derived", 0),
    ("wind_dir_sin", "weather", "sin of wind direction", "", "derived", 0),
    ("wind_dir_cos", "weather", "cos of wind direction", "", "derived", 0),
    ("nw_wind_flag", "weather", "1 if wind from 270-350 deg (direction of the stubble belt)", "flag", "derived", 0),
    ("blh_m", "weather", "Boundary-layer height (empty if the endpoint does not provide it)", "m", "Open-Meteo", 0),
    ("ventilation_m2s", "weather", "blh x wind speed (dispersion capacity)", "m2/s", "derived", 0),
    ("precip_24h_mm", "weather", "Rain in the last 24 h", "mm", "derived", 0),
    ("precip_72h_mm", "weather", "Rain in the last 72 h", "mm", "derived", 0),
    ("temp_range_24h_c", "weather", "Max-min temperature over 24 h (inversion proxy)", "C", "derived", 0),
    ("pressure_change_6h", "weather", "6 h pressure change", "hPa", "derived", 0),
    ("wind_speed_roll6h", "weather", "6 h mean wind speed", "m/s", "derived", 0),
    ("stagnation_flag", "weather", "1 if wind<2 m/s and low mixing (blh<500 m, or RH>80% if blh missing)", "flag", "derived", 0),
    ("traj_mean_speed_kmh", "trajectory", "Median ensemble mean parcel speed", "km/h", "derived", 0),
    ("traj_dist_48h_km", "trajectory", "Distance of the 48 h-back parcel position from Delhi", "km", "derived", 0),
    ("traj_origin_bearing_48h", "trajectory", "Bearing from Delhi to the 48 h-back position", "deg", "derived", 0),
    ("traj_origin_sin", "trajectory", "sin of the 48 h origin bearing (use instead of the raw angle in models)", "", "derived", 0),
    ("traj_origin_cos", "trajectory", "cos of the 48 h origin bearing", "", "derived", 0),
    ("traj_pbhr_frac", "trajectory", "Share of trajectory hours spent over Punjab/Haryana (>60 km from Delhi)", "", "derived", 0),
    ("fire_link_computed", "trajectory", "1 if fire linking was run for this hour (fire season only)", "flag", "derived", 0),
    ("fires_linked_median", "fire", "Fires linked to this hour's parcels (ensemble median)", "count", "FIRMS+Open-Meteo", 0),
    ("fires_linked_p10", "fire", "10th percentile over ensemble members", "count", "derived", 0),
    ("fires_linked_p90", "fire", "90th percentile over ensemble members", "count", "derived", 0),
    ("frp_linked_median", "fire", "Total fire radiative power of linked fires", "MW", "derived", 0),
    ("fire_lag_p10_h", "fire", "10th percentile of travel time to the linked fires", "h", "derived", 0),
    ("fire_lag_p50_h", "fire", "Median travel time to linked fires", "h", "derived", 0),
    ("fire_lag_p90_h", "fire", "90th percentile travel time", "h", "derived", 0),
    ("fire_member_agree_frac", "fire", "Share of ensemble members linking >=20 fires (confidence in the fire link)", "", "derived", 0),
    ("raw_fires_24h_pbhr", "fire", "NAIVE baseline: fire detections in last 24 h inside the Punjab/Haryana box", "count", "FIRMS", 0),
]
DICT = {r[0]: r for r in D}

DAILY = {
    "date": ("id", "Calendar day", "", "", 0),
    "delhi_pm25_daily_mean": ("city", "Mean of hourly Delhi median PM2.5 (>=18 valid hours)", "ug/m3", "derived", 0),
    "delhi_pm25_daily_max": ("city", "Maximum hourly Delhi median PM2.5", "ug/m3", "derived", 0),
    "ncr_pm25_daily_mean": ("ncr", "Mean of hourly NCR median PM2.5", "ug/m3", "derived", 0),
    "fires_linked_daily_max": ("fire", "Max hourly linked-fire count", "count", "derived", 0),
    "fires_linked_daily_mean": ("fire", "Mean hourly linked-fire count", "count", "derived", 0),
    "raw_fires_pbhr_daily_mean": ("fire", "Naive 24 h fire count (daily mean)", "count", "derived", 0),
    "nw_wind_frac": ("weather", "Share of hours with NW wind", "", "derived", 0),
    "wind_speed_daily_mean": ("weather", "Mean wind speed", "m/s", "derived", 0),
    "blh_daily_mean": ("weather", "Mean boundary-layer height", "m", "derived", 0),
    "precip_daily_mm": ("weather", "Total precipitation", "mm", "derived", 0),
    "background_share_daily_mean": ("local_regional", "Mean regional background share", "", "derived", 0),
    "frac_hours_widespread": ("ncr", "Share of hours classified widespread_rise", "", "derived", 0),
    "frac_hours_delhi_concentrated": ("ncr", "Share of hours classified delhi_concentrated_rise", "", "derived", 0),
    "diwali_window": ("time", "1 within 2 days of Diwali", "flag", "config", 0),
    "is_episode_day": ("episode", "1 if daily mean >= threshold", "flag", "derived", 0),
    "episode_id": ("episode", "Episode number (consecutive episode days, min length in config); 0 = none", "", "derived", 0),
    "synthetic": ("id", "1 = synthetic test data", "", "", 0),
}


def build_dictionary(tables):
    rows, missing = [], []
    for tname, df in tables.items():
        for c in df.columns:
            if tname == "city_daily_final":
                e = DAILY.get(c)
                if e:
                    rows.append((tname, c) + e)
                else:
                    missing.append((tname, c))
                continue
            e = DICT.get(c)
            if e is None and c.startswith("delhi_fp_") and ("fp_" + c[len("delhi_fp_"):]) in DICT:
                base = DICT["fp_" + c[len("delhi_fp_"):]]
                e = (c, base[1], "Delhi median of: " + base[2], base[3], base[4], base[5])
            if e:
                rows.append((tname, c) + e[1:])
            else:
                missing.append((tname, c))
    out = pd.DataFrame(rows, columns=["table", "column", "group", "description", "unit", "source", "look_ahead"])
    return out, missing


def daily_table(city):
    c = city.copy()
    c["date"] = c["time"].dt.normalize()
    g = c.groupby("date")
    d = pd.DataFrame({
        "delhi_pm25_daily_mean": g["delhi_pm25_median"].mean().where(g["delhi_pm25_median"].count() >= 18),
        "delhi_pm25_daily_max": g["delhi_pm25_median"].max(),
        "ncr_pm25_daily_mean": g["ncr_pm25_median"].mean(),
        "fires_linked_daily_max": g["fires_linked_median"].max(),
        "fires_linked_daily_mean": g["fires_linked_median"].mean(),
        "raw_fires_pbhr_daily_mean": g["raw_fires_24h_pbhr"].mean(),
        "nw_wind_frac": g["nw_wind_flag"].mean(),
        "wind_speed_daily_mean": g["wind_speed_ms"].mean(),
        "blh_daily_mean": g["blh_m"].mean(),
        "precip_daily_mm": g["precip_mm"].sum(),
        "background_share_daily_mean": g["delhi_background_share"].mean(),
        "frac_hours_widespread": g["regime"].apply(lambda s: (s == "widespread_rise").mean()),
        "frac_hours_delhi_concentrated": g["regime"].apply(lambda s: (s == "delhi_concentrated_rise").mean()),
        "diwali_window": g["diwali_window"].max(),
    }).reset_index()
    d["is_episode_day"] = (d["delhi_pm25_daily_mean"] >= EPISODE_PM25_DAILY).astype(int)
    # consecutive runs
    run = (d["is_episode_day"] != d["is_episode_day"].shift()).cumsum()
    size = pd.Series(d.groupby(run)["is_episode_day"].transform("size"))
    valid = (d["is_episode_day"] == 1) & (size >= EPISODE_MIN_DAYS)
    ids = run.where(valid)
    d["episode_id"] = ids.rank(method="dense").fillna(0).astype(int)
    d["is_episode_day"] = valid.astype(int)
    return d


def main():
    city = pd.read_csv(INTERIM / "city_features.csv", parse_dates=["time"])
    st = pd.read_csv(INTERIM / "station_features.csv", parse_dates=["time"])
    traj = pd.read_csv(INTERIM / "traj_features_hourly.csv", parse_dates=["time"])
    city = city.merge(traj, on="time", how="left")
    city = tag_synthetic(city)

    ctx_cols = [c for c in city.columns if c not in st.columns] + ["time"]
    st_final = tag_synthetic(st.merge(city[ctx_cols], on="time", how="left"))
    daily = tag_synthetic(daily_table(city))
    ep = (daily[daily.episode_id > 0].groupby("episode_id")
          .agg(start=("date", "min"), end=("date", "max"), days=("date", "count"),
               peak_daily_pm25=("delhi_pm25_daily_mean", "max"),
               mean_daily_pm25=("delhi_pm25_daily_mean", "mean"),
               peak_linked_fires=("fires_linked_daily_max", "max"),
               mean_background_share=("background_share_daily_mean", "mean")).reset_index())

    city.to_csv(PROCESSED / "city_hourly_final.csv", index=False)
    st_final.to_csv(PROCESSED / "station_hourly_final.csv", index=False)
    daily.to_csv(PROCESSED / "city_daily_final.csv", index=False)
    ep.to_csv(PROCESSED / "episodes.csv", index=False)
    shutil.copy(INTERIM / "traj_central_tracks.csv", PROCESSED / "traj_central_tracks.csv")

    dd, missing = build_dictionary({"city_hourly_final": city, "station_hourly_final": st_final,
                                    "city_daily_final": daily})
    dd.to_csv(PROCESSED / "data_dictionary.csv", index=False)
    if missing:
        print("WARNING: columns without a dictionary entry:", missing)

    pd.DataFrame(columns=["study_id", "citation", "doi_or_url", "location", "period_start", "period_end",
                          "method", "source", "low_pct", "mid_pct", "high_pct", "notes"]).to_csv(
        REF / "reference_apportionment_TEMPLATE.csv", index=False)

    print(f"final tables written to {PROCESSED}")
    print(f"  city_hourly_final   {city.shape}\n  station_hourly_final {st_final.shape}\n  city_daily_final    {daily.shape}")
    print(f"  episodes detected: {len(ep)}")


if __name__ == "__main__":
    main()
