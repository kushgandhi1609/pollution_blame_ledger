"""Step 5 - back-trajectories from Delhi and linking of FIRMS fires (the 'fire pathway' module).

For every hour in the study periods we trace an ensemble of air parcels BACKWARD from Delhi for
TRAJ_HOURS_BACK hours using hourly gridded winds (simplified, HYSPLIT-style: horizontal advection
only). A fire is 'linked' to that hour if some parcel passed within CORRIDOR_KM of it within
FIRE_TIME_WINDOW_H hours of the detection. Output is one row per hour with the number of linked
fires (with ensemble spread), their total FRP, the travel-time range, and trajectory descriptors.
Fire linking is only computed in FIRE_SEASON_MONTHS.

Outputs: data/interim/traj_features_hourly.csv, data/interim/traj_central_tracks.csv
Known limits: no vertical mixing, deposition or chemistry; wind from a 1-degree reanalysis grid.
"""
import sys
import time as _time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.ndimage import map_coordinates # type: ignore
from scipy.spatial import KDTree # type: ignore

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pipeline.common import bearing_deg, haversine_km, period_hours, wind_to_uv
from pipeline.config import (
    CORRIDOR_KM,
    DELHI_LAT,
    DELHI_LON,
    FIRE_MIN_LINK,
    FIRE_SEASON_MONTHS,
    FIRE_TIME_WINDOW_H,
    INTERIM,
    PBHR_BOX,
    PBHR_EXCLUDE_KM_FROM_DELHI,
    RAW,
    RNG_SEED,
    TRAJ_DIR_SD_DEG,
    TRAJ_HOURS_BACK,
    TRAJ_N_MEMBERS,
    TRAJ_SPEED_SD_FRAC,
    TRAJ_WIND_LEVEL,
)

KM_PER_DEG_LAT = 110.57
LAT0 = 29.5
KM_PER_DEG_LON = 111.32 * np.cos(np.deg2rad(LAT0))


def load_wind():
    df = pd.read_csv(RAW / "weather_grid_hourly.csv", parse_dates=["time"])
    sp_col, di_col = f"wind_speed_{TRAJ_WIND_LEVEL}", f"wind_direction_{TRAJ_WIND_LEVEL}"
    times = np.sort(np.asarray(df["time"].unique()))
    lats = np.sort(np.asarray(df["lat"].unique(), dtype=float))
    lons = np.sort(np.asarray(df["lon"].unique(), dtype=float))
    u, v = wind_to_uv(np.asarray(df[sp_col], dtype=float), np.asarray(df[di_col], dtype=float))
    df = df.assign(u=u, v=v)
    ti = pd.Index(times).get_indexer(pd.Index(df["time"]))
    yi = np.searchsorted(lats, np.asarray(df["lat"], dtype=float))
    xi = np.searchsorted(lons, np.asarray(df["lon"], dtype=float))
    U = np.full((len(times), len(lats), len(lons)), np.nan, dtype="float32")
    V = U.copy()
    U[ti, yi, xi] = np.asarray(df["u"], dtype="float32")
    V[ti, yi, xi] = np.asarray(df["v"], dtype="float32")
    # fill gaps: along time, then zero
    for A in (U, V):
        for iy in range(A.shape[1]):
            for ix in range(A.shape[2]):
                s = pd.Series(list(A[:, iy, ix])).interpolate(limit_direction="both")
                A[:, iy, ix] = np.asarray(s.fillna(0), dtype="float32")
    dt_times: list[pd.Timestamp] = [pd.Timestamp(t) for t in times]
    return pd.DatetimeIndex(dt_times), lats, lons, U, V


def run_trajectories(times, lats, lons, U, V, start_idx, rng):
    n, m, K = len(start_idx), TRAJ_N_MEMBERS, TRAJ_HOURS_BACK
    step_lat = lats[1] - lats[0]
    step_lon = lons[1] - lons[0]
    lat = np.full((n, m), DELHI_LAT)
    lon = np.full((n, m), DELHI_LON)
    tr_lat = np.empty((K + 1, n, m))
    tr_lon = np.empty((K + 1, n, m))
    tr_lat[0], tr_lon[0] = lat, lon
    theta = np.deg2rad(rng.normal(0, TRAJ_DIR_SD_DEG, (n, m)))
    scale = rng.lognormal(0, TRAJ_SPEED_SD_FRAC, (n, m))
    theta[:, 0], scale[:, 0] = 0.0, 1.0           # member 0 = unperturbed central trajectory
    cth, sth = np.cos(theta), np.sin(theta)
    T = len(times)
    for k in range(K):
        t_idx = np.clip(start_idx - k, 0, T - 1)[:, None] * np.ones((1, m))
        fy = np.clip((lat - lats[0]) / step_lat, 0, len(lats) - 1)
        fx = np.clip((lon - lons[0]) / step_lon, 0, len(lons) - 1)
        coords = np.stack([t_idx.ravel(), fy.ravel(), fx.ravel()])
        u = map_coordinates(U, coords, order=1, mode="nearest").reshape(n, m)
        v = map_coordinates(V, coords, order=1, mode="nearest").reshape(n, m)
        u2 = (u * cth - v * sth) * scale
        v2 = (u * sth + v * cth) * scale
        lat = lat - v2 * 3600.0 / 111320.0
        lon = lon - u2 * 3600.0 / (111320.0 * np.cos(np.deg2rad(lat)))
        lat = np.clip(lat, lats[0], lats[-1])
        lon = np.clip(lon, lons[0], lons[-1])
        tr_lat[k + 1], tr_lon[k + 1] = lat, lon
    return tr_lat, tr_lon


def to_km(lat, lon):
    return (lon - 77.0) * KM_PER_DEG_LON, (lat - 28.0) * KM_PER_DEG_LAT


def main():
    t0 = _time.time()
    rng = np.random.default_rng(RNG_SEED)
    times, lats, lons, U, V = load_wind()
    hours_df: pd.DataFrame = period_hours()
    start_idx = pd.Index(times).get_indexer(pd.Index(hours_df["time"]))
    ok = start_idx >= 0
    if not ok.all():
        print(f"warning: {(~ok).sum()} study hours missing from weather data; they get NaN trajectory features")
    hours = pd.DataFrame(hours_df[ok].reset_index(drop=True))
    hours_time = pd.to_datetime(hours["time"])
    start_idx = start_idx[ok]
    print(f"trajectories: {len(hours):,} start hours x {TRAJ_N_MEMBERS} members x {TRAJ_HOURS_BACK} h")
    tr_lat, tr_lon = run_trajectories(times, lats, lons, U, V, start_idx, rng)   # (K+1, n, m)
    K1, n, m = tr_lat.shape

    # ------------------------------------------------------------- trajectory descriptors
    out = pd.DataFrame({"time": hours_time})
    d_all = haversine_km(tr_lat[:-1], tr_lon[:-1], tr_lat[1:], tr_lon[1:])      # km per hour
    out["traj_mean_speed_kmh"] = np.median(d_all.mean(axis=0), axis=1)
    k48 = min(48, K1 - 1)
    out["traj_dist_48h_km"] = np.median(haversine_km(DELHI_LAT, DELHI_LON, tr_lat[k48], tr_lon[k48]), axis=1)
    out["traj_origin_bearing_48h"] = bearing_deg(DELHI_LAT, DELHI_LON, np.median(tr_lat[k48], axis=1),
                                                 np.median(tr_lon[k48], axis=1))
    inbox = (tr_lat[1:] >= PBHR_BOX["lat_min"]) & (tr_lat[1:] <= PBHR_BOX["lat_max"]) & \
            (tr_lon[1:] >= PBHR_BOX["lon_min"]) & (tr_lon[1:] <= PBHR_BOX["lon_max"]) & \
            (haversine_km(DELHI_LAT, DELHI_LON, tr_lat[1:], tr_lon[1:]) > PBHR_EXCLUDE_KM_FROM_DELHI)
    out["traj_pbhr_frac"] = np.median(inbox.mean(axis=0), axis=1)
    out["traj_origin_sin"] = np.sin(np.deg2rad(out["traj_origin_bearing_48h"]))
    out["traj_origin_cos"] = np.cos(np.deg2rad(out["traj_origin_bearing_48h"]))

    # central track for the map (member 0, every 3 hours)
    ks = np.arange(0, K1, 3)
    tracks = pd.DataFrame({
        "time": np.repeat(hours_time.to_numpy(), len(ks)),
        "hours_back": np.tile(ks, n),
        "lat": tr_lat[ks, :, 0].T.ravel(), "lon": tr_lon[ks, :, 0].T.ravel()})
    tracks.to_csv(INTERIM / "traj_central_tracks.csv", index=False)

    # ------------------------------------------------------------- fire linking
    fires = pd.read_csv(INTERIM / "fires_clean.csv", parse_dates=["time_ist"])
    fx_, fy_ = to_km(np.asarray(fires["lat"], dtype=float), np.asarray(fires["lon"], dtype=float))
    t_ref = pd.Timestamp("2000-01-01")
    ft = (pd.to_datetime(fires["time_ist"]) - t_ref).dt.total_seconds().to_numpy() / 3600.0
    tscale = CORRIDOR_KM / FIRE_TIME_WINDOW_H
    tree = KDTree(np.c_[fx_, fy_, ft * tscale])
    frp = np.asarray(fires["frp"].fillna(0), dtype=float)

    cols = ["fires_linked_median", "fires_linked_p10", "fires_linked_p90", "frp_linked_median",
            "fire_lag_p10_h", "fire_lag_p50_h", "fire_lag_p90_h", "fire_member_agree_frac"]
    res = np.full((n, len(cols)), np.nan)
    season = hours_time.dt.month.isin(FIRE_SEASON_MONTHS).to_numpy()
    out["fire_link_computed"] = season.astype(int)
    px, py = to_km(tr_lat, tr_lon)                                         # (K1, n, m)
    pt = ((hours_time.to_numpy().astype("datetime64[s]") - np.datetime64("2000-01-01T00:00:00")) / np.timedelta64(1, "h")).astype(float)
    ks_all = np.arange(K1)
    for i in np.flatnonzero(season):
        tt = (pt[i] - ks_all) * tscale                                      # (K1,)
        pts = np.stack([px[:, i, :], py[:, i, :], np.repeat(tt[:, None], m, axis=1)], axis=-1)  # (K1, m, 3)
        hits = tree.query_ball_point(pts.reshape(-1, 3), r=CORRIDOR_KM)
        hits = np.asarray(hits, dtype=object).reshape(K1, m)
        counts, frps, l10, l50, l90 = [], [], [], [], []
        for j in range(m):
            first = {}
            for k in range(K1):
                for fid in hits[k, j]:
                    if fid not in first:
                        first[fid] = k
            if first:
                ids = np.fromiter(first.keys(), dtype=int)
                lags = np.fromiter(first.values(), dtype=float)
                counts.append(len(ids)); frps.append(float(frp[ids].sum()))
                l10.append(np.percentile(lags, 10)); l50.append(np.median(lags)); l90.append(np.percentile(lags, 90))
            else:
                counts.append(0); frps.append(0.0); l10.append(np.nan); l50.append(np.nan); l90.append(np.nan)
        c = np.array(counts)
        res[i] = [np.median(c), np.percentile(c, 10), np.percentile(c, 90), np.median(frps),
                  np.nanmedian(l10) if np.isfinite(l10).any() else np.nan,
                  np.nanmedian(l50) if np.isfinite(l50).any() else np.nan,
                  np.nanmedian(l90) if np.isfinite(l90).any() else np.nan,
                  float((c >= FIRE_MIN_LINK).mean())]
        if i % 500 == 0:
            print(f"  linked {i}/{n} start hours ({_time.time() - t0:.0f}s)")
    for c_i, c_n in enumerate(cols):
        out[c_n] = res[:, c_i].tolist()
    out.loc[~season, ["fires_linked_median", "fires_linked_p10", "fires_linked_p90", "frp_linked_median"]] = 0.0

    # ------------------------------------------------------------- naive baseline: raw fire count
    box = fires[(fires.lat.between(PBHR_BOX["lat_min"], PBHR_BOX["lat_max"])) &
                (fires.lon.between(PBHR_BOX["lon_min"], PBHR_BOX["lon_max"]))]
    time_floor = [pd.Timestamp(t).floor("h") for t in box["time_ist"]]
    hourly_counts = box.groupby(time_floor)["time_ist"].count()
    full_idx = pd.date_range(times.min(), times.max(), freq="h")
    full_series = hourly_counts.reindex(full_idx, fill_value=0).astype(float)
    roll_sum_series = full_series.rolling(24, min_periods=1).sum()
    roll_sum = dict(zip(full_idx, np.asarray(roll_sum_series, dtype=float)))
    out["raw_fires_24h_pbhr"] = [float(roll_sum.get(pd.Timestamp(t), 0.0)) for t in out["time"]]
    out.to_csv(INTERIM / "traj_features_hourly.csv", index=False)
    print(f"trajectories done in {_time.time() - t0:.0f}s -> {INTERIM / 'traj_features_hourly.csv'}")


if __name__ == "__main__":
    main()
