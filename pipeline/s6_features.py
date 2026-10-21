"""Step 6 - feature engineering.

Builds, from the cleaned station data and Delhi weather:
  * station-level features: time, ratios, lags/rolling, pollutant fingerprints,
    local-vs-regional excess, hotspot flags, "rising" flags
  * city-level hourly table: Delhi/NCR aggregates, background share, regime classification
    (widespread / Delhi-concentrated / ...), missing-data warnings, weather features
Outputs: data/interim/station_features.csv, data/interim/city_features.csv
Columns that use information from AFTER the row's hour are marked look-ahead in the data dictionary.
"""
import numpy as np
import pandas as pd

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pipeline.config import *  # noqa: F401,F403
from pipeline.common import period_hours, wind_to_uv


# ------------------------------------------------------------------ time features
def add_time_features(df, col="time"):
    t = df[col]
    df["hour"] = t.dt.hour
    df["dow"] = t.dt.dayofweek
    df["month"] = t.dt.month
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["is_rush_am"] = df["hour"].between(7, 10).astype(int)
    df["is_rush_pm"] = df["hour"].between(17, 21).astype(int)
    df["is_night"] = ((df["hour"] >= 22) | (df["hour"] <= 5)).astype(int)
    dd = pd.to_datetime(list(DIWALI_DATES.values()))
    days = (t.dt.normalize().values[:, None] - dd.values[None, :]) / np.timedelta64(1, "D")
    nearest = days[np.arange(len(df)), np.abs(days).argmin(axis=1)]
    df["days_from_diwali"] = np.where(np.abs(nearest) <= 30, nearest, np.nan)
    df["diwali_window"] = (np.abs(nearest) <= 2).astype(int)
    return df


# ------------------------------------------------------------------ station-level
def rolling_z(g, col, window=168, min_periods=48):
    mean = g[col].transform(lambda s: s.rolling(window, min_periods=min_periods).mean())
    std = g[col].transform(lambda s: s.rolling(window, min_periods=min_periods).std())
    return (g.obj[col] - mean) / std.replace(0, np.nan)


def station_features(st, stations):
    st = st.merge(stations[["station_id", "region", "lat", "lon"]], on="station_id", how="left")
    st = st.sort_values(["station_id", "time"]).reset_index(drop=True)
    st = add_time_features(st)
    g = st.groupby(["station_id", "period_id"], sort=False)

    ok = (st["qc_pm_inconsistent"] == 0) & (st["pm10"] >= 20)
    st["pm25_pm10_ratio"] = np.where(ok, st["pm25"] / st["pm10"], np.nan)
    st["pm10_pm25_ratio"] = np.where(ok & (st["pm25"] >= 10), st["pm10"] / st["pm25"], np.nan)

    for lag in (1, 3, 24):
        st[f"pm25_lag{lag}h"] = g["pm25"].shift(lag)
    for w in (3, 6, 24):
        st[f"pm25_roll{w}h"] = g["pm25"].transform(lambda s, w=w: s.rolling(w, min_periods=max(2, w // 2)).mean())
    st["pm25_diff1h"] = st["pm25"] - st["pm25_lag1h"]
    st["pm25_diff3h"] = st["pm25"] - st["pm25_lag3h"]
    st["pm25_diff24h"] = st["pm25"] - st["pm25_lag24h"]
    st["rising_3h"] = ((st["pm25_diff3h"] > RISE_ABS_UG) &
                       (st["pm25_diff3h"] > RISE_REL * st["pm25_lag3h"])).astype(float)
    st.loc[st["pm25_diff3h"].isna(), "rising_3h"] = np.nan

    # ---- fingerprints (causal rolling baselines of the station's own history)
    g = st.groupby(["station_id", "period_id"], sort=False)
    st["z_no2"] = rolling_z(g, "no2")
    st["z_co"] = rolling_z(g, "co")
    st["fp_traffic_z"] = st[["z_no2", "z_co"]].mean(axis=1, skipna=True)
    st["fp_industrial_so2_z"] = rolling_z(g, "so2")
    st["fp_dust_ratio"] = st["pm10_pm25_ratio"]
    st["_dust"] = st["pm10_pm25_ratio"]
    g = st.groupby(["station_id", "period_id"], sort=False)
    st["fp_dust_z"] = rolling_z(g, "_dust", window=720, min_periods=168)
    st["fp_biomass_ratio"] = st["pm25_pm10_ratio"]
    st = st.drop(columns=["_dust", "z_no2", "z_co"])

    # ---- daily fingerprints
    st["date"] = st["time"].dt.normalize()
    rush = st[(st["is_rush_am"] == 1) | (st["is_rush_pm"] == 1)].groupby(["station_id", "date"])[["no2", "co"]].mean()
    mid = st[st["hour"].between(12, 15)].groupby(["station_id", "date"])[["no2", "co"]].mean()
    daily = pd.DataFrame({
        "fp_traffic_rush_ratio_no2": rush["no2"] / mid["no2"].replace(0, np.nan),
        "fp_traffic_rush_ratio_co": rush["co"] / mid["co"].replace(0, np.nan)}).reset_index()
    # night rise: mean PM2.5 22:00 of day d to 04:59 of d+1, minus mean 12:00-16:59 of day d (LOOK-AHEAD)
    nd = st["date"].where(st["hour"] >= 22, st["date"] - pd.Timedelta(days=1))
    night = st[(st["hour"] >= 22) | (st["hour"] <= 4)].assign(nd=nd).groupby(["station_id", "nd"])["pm25"].mean()
    aft = st[st["hour"].between(12, 16)].groupby(["station_id", "date"])["pm25"].mean()
    night.index.names = ["station_id", "date"]
    nr = (night - aft).rename("fp_biomass_night_rise").reset_index()
    st = st.merge(daily, on=["station_id", "date"], how="left").merge(nr, on=["station_id", "date"], how="left")

    # ---- local vs regional (per hour and region)
    grp = st.groupby(["time", "region"])["pm25"]
    n_valid = grp.transform("count")
    q10 = grp.transform(lambda s: s.quantile(BACKGROUND_PERCENTILE))
    minimum = st["region"].map(MIN_STATIONS_FOR_BACKGROUND).fillna(4)
    st["regional_background_pm25"] = np.where(n_valid >= minimum, q10, np.nan)
    st["local_excess_pm25"] = st["pm25"] - st["regional_background_pm25"]
    st["local_excess_share"] = (st["local_excess_pm25"] / st["pm25"]).clip(0, 1)
    med = grp.transform("median")
    dev = (st["pm25"] - med).abs()
    st["_dev"] = dev
    mad = st.groupby(["time", "region"])["_dev"].transform("median")
    st["pm25_robust_z"] = (st["pm25"] - med) / (1.4826 * mad.replace(0, np.nan))
    st["hotspot_flag"] = ((st["pm25_robust_z"] > HOTSPOT_Z) & ((st["pm25"] - med) > HOTSPOT_MIN_EXCESS)).astype(int)
    st.loc[st["pm25"].isna(), "hotspot_flag"] = 0
    st = st.drop(columns=["_dev", "date"])
    return st


# ------------------------------------------------------------------ weather
def weather_features():
    w = pd.read_csv(RAW / "weather_delhi_hourly.csv", parse_dates=["time"]).drop_duplicates("time")
    w = w.sort_values("time").set_index("time")
    full = w.reindex(pd.date_range(w.index.min(), w.index.max(), freq="h"))
    u, v = wind_to_uv(full["wind_speed_10m"], full["wind_direction_10m"])
    f = pd.DataFrame(index=full.index)
    f["temp_c"] = full["temperature_2m"]
    f["rh_pct"] = full["relative_humidity_2m"]
    f["precip_mm"] = full["precipitation"]
    f["pressure_hpa"] = full["surface_pressure"]
    f["cloud_pct"] = full["cloud_cover"]
    f["wind_speed_ms"] = full["wind_speed_10m"]
    f["wind_speed_100m_ms"] = full["wind_speed_100m"]
    f["wind_dir_deg"] = full["wind_direction_10m"]
    f["wind_u"], f["wind_v"] = u, v
    f["wind_dir_sin"] = np.sin(np.deg2rad(full["wind_direction_10m"]))
    f["wind_dir_cos"] = np.cos(np.deg2rad(full["wind_direction_10m"]))
    f["nw_wind_flag"] = full["wind_direction_10m"].between(270, 350).astype(int)
    f["blh_m"] = full["boundary_layer_height"] if "boundary_layer_height" in full else np.nan
    f["ventilation_m2s"] = f["blh_m"] * f["wind_speed_ms"]
    f["precip_24h_mm"] = f["precip_mm"].rolling(24, min_periods=12).sum()
    f["precip_72h_mm"] = f["precip_mm"].rolling(72, min_periods=24).sum()
    f["temp_range_24h_c"] = full["temperature_2m"].rolling(24, min_periods=18).max() - \
        full["temperature_2m"].rolling(24, min_periods=18).min()
    f["pressure_change_6h"] = f["pressure_hpa"].diff(6)
    f["wind_speed_roll6h"] = f["wind_speed_ms"].rolling(6, min_periods=3).mean()
    low_mix = (f["blh_m"] < 500) if bool(f["blh_m"].notna().any()) else (f["rh_pct"] > 80)
    f["stagnation_flag"] = ((f["wind_speed_ms"] < 2.0) & low_mix).astype(int)
    f.index.name = "time"
    return f.reset_index()


# ------------------------------------------------------------------ city level
def aqi_category(x):
    bins = [-np.inf, 30, 60, 90, 120, 250, np.inf]
    labels = ["good", "satisfactory", "moderate", "poor", "very_poor", "severe"]
    return pd.cut(x, bins=bins, labels=labels)


def classify_regime(r):
    nd, nn = r["delhi_n_valid"], r["ncr_n_valid"]
    fd, fn = r["frac_rising_delhi"], r["frac_rising_ncr"]
    if nd < MIN_STATIONS_FOR_BACKGROUND["Delhi"] or nn < MIN_STATIONS_FOR_BACKGROUND["NCR"] \
            or np.isnan(fd) or np.isnan(fn):
        return "insufficient_data"
    if fd >= FRAC_RISING_WIDE and fn >= FRAC_RISING_WIDE:
        return "widespread_rise"
    if fd >= 0.5 and fn <= FRAC_RISING_LOW:
        return "delhi_concentrated_rise"
    if fn >= 0.5 and fd <= FRAC_RISING_LOW:
        return "ncr_concentrated_rise"
    if fd < FRAC_RISING_LOW and fn < FRAC_RISING_LOW:
        return "no_significant_rise"
    return "mixed"


def city_features(st, wx):
    hours = period_hours()
    delhi = st[st.region == "Delhi"]
    ncr = st[st.region == "NCR"]
    D = delhi.groupby("time")
    c = pd.DataFrame(index=pd.Index(hours["time"], name="time"))
    c["delhi_pm25_median"] = D["pm25"].median()
    c["delhi_pm25_mean"] = D["pm25"].mean()
    c["delhi_pm25_p10"] = D["pm25"].quantile(0.10)
    c["delhi_pm25_p90"] = D["pm25"].quantile(0.90)
    c["delhi_n_valid"] = D["pm25"].count()
    c["delhi_n_stations"] = delhi["station_id"].nunique()
    c["delhi_pm25_spread"] = (D["pm25"].quantile(0.75) - D["pm25"].quantile(0.25)) / c["delhi_pm25_median"]
    for p in ("pm10", "no2", "so2", "co", "o3"):
        c[f"delhi_{p}_median"] = D[p].median()
    for fp in ("fp_traffic_z", "fp_traffic_rush_ratio_no2", "fp_dust_ratio", "fp_dust_z",
               "fp_industrial_so2_z", "fp_biomass_ratio", "fp_biomass_night_rise"):
        c[f"delhi_{fp}"] = D[fp].median()
    c["delhi_regional_background_pm25"] = D["regional_background_pm25"].first()
    c["delhi_background_share"] = (c["delhi_regional_background_pm25"] / c["delhi_pm25_median"]).clip(0, 1)
    c["delhi_hotspot_count"] = D["hotspot_flag"].sum()
    c["frac_rising_delhi"] = D["rising_3h"].mean()
    N = ncr.groupby("time")
    c["ncr_pm25_median"] = N["pm25"].median()
    c["ncr_n_valid"] = N["pm25"].count()
    c["ncr_n_stations"] = ncr["station_id"].nunique()
    c["frac_rising_ncr"] = N["rising_3h"].mean()
    c[["ncr_n_valid", "delhi_n_valid"]] = c[["ncr_n_valid", "delhi_n_valid"]].fillna(0)
    c["ncr_minus_delhi_pm25"] = c["ncr_pm25_median"] - c["delhi_pm25_median"]
    c["ncr_to_delhi_ratio"] = c["ncr_pm25_median"] / c["delhi_pm25_median"]
    c["period_id"] = hours.set_index("time")["period_id"]
    c = c.reset_index()
    parts = []
    for _, g in c.groupby("period_id"):
        g = g.copy()
        g["delhi_ncr_corr24h"] = g["delhi_pm25_median"].rolling(24, min_periods=12).corr(g["ncr_pm25_median"])
        g["delhi_pm25_24h_mean"] = g["delhi_pm25_median"].rolling(24, min_periods=18).mean()
        g["delhi_pm25_diff3h"] = g["delhi_pm25_median"].diff(3)
        g["delhi_pm25_diff24h"] = g["delhi_pm25_median"].diff(24)
        parts.append(g)
    c = pd.concat(parts, ignore_index=True)
    c["delhi_aqi_category_24h"] = pd.Series(aqi_category(c["delhi_pm25_24h_mean"])).astype(str)
    c["regime"] = c.apply(classify_regime, axis=1)
    c["delhi_missing_frac"] = 1 - (c["delhi_n_valid"] / c["delhi_n_stations"]).clip(0, 1)
    c["ncr_missing_frac"] = 1 - (c["ncr_n_valid"] / c["ncr_n_stations"].replace(0, np.nan)).clip(0, 1)
    c["missing_data_warning"] = ((c["delhi_missing_frac"] > MISSING_WARNING_FRAC) |
                                 (c["ncr_missing_frac"] > MISSING_WARNING_FRAC)).astype(int)
    c = add_time_features(c)
    c = c.merge(wx, on="time", how="left")
    return c


def main():
    stations = pd.read_csv(REF / "stations.csv")
    st = pd.read_csv(INTERIM / "station_hourly_clean.csv", parse_dates=["time"])
    st = station_features(st, stations)
    wx = weather_features()
    city = city_features(st, wx)
    st.to_csv(INTERIM / "station_features.csv", index=False)
    city.to_csv(INTERIM / "city_features.csv", index=False)
    print(f"features: station table {st.shape}, city table {city.shape}")
    print("regime counts:\n", city["regime"].value_counts().to_string())


if __name__ == "__main__":
    main()
