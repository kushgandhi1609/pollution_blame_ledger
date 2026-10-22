"""
sensor_health.py - spatial neighbourhood consistency check for monitoring stations.

HOW IT WORKS:
1. Inverse-Distance Weighting (IDW): for each station and hour, predicts the expected PM2.5
   from its nearest k valid neighbouring stations (within NEIGHBOUR_MAX_KM).
2. Spatial residual and z-score: residual = observed - expected, standardised against that
   station's own historical residual mean and spread.
3. Persistence counter: counts consecutive hours with |z| >= SENSOR_Z_FLAG
   (a single odd hour is not enough).
4. Pattern correlation: 24-hour rolling Pearson correlation with the all-station median.
5. Cross-pollutant check: PM2.5 should not be implausibly higher than PM10.
6. Status:
   - 'OK'         : tracks consistently with its neighbourhood.
   - 'watch'      : moderate or short-lived deviation.
   - 'suspect'    : persistent deviation (>= SENSOR_MIN_PERSIST_H hours) with either low
                    correlation or a very large average deviation.
   - 'unassessed' : no valid neighbours or no recent data, so no judgement is made.
   The word 'suspect' is used on purpose: the check can never prove a fault.
   Raw readings are never changed.
7. Validation: injects synthetic faults into copies of healthy stations and reports the
   detection rate and the false-alarm rate on untouched stations.

Outputs:
  - pipeline/data/processed/sensor_health.csv
  - pipeline/data/processed/sensor_validation_report.json

Run from the pipeline folder:  python ../analysis/sensor_health.py
"""
import json
import sys
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

warnings.filterwarnings("ignore", category=RuntimeWarning)

PIPELINE_DIR = Path(__file__).resolve().parents[1] / "pipeline"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

import config as _cfg  # type: ignore  # noqa: E402
from common import tag_synthetic  # type: ignore  # noqa: E402
from config import PROCESSED, REF  # type: ignore  # noqa: E402

# Settings: read from pipeline/config.py if present, otherwise use these defaults.
SENSOR_K_NEIGHBOURS: int = int(getattr(_cfg, "SENSOR_K_NEIGHBOURS", 4))
SENSOR_Z_FLAG: float = float(getattr(_cfg, "SENSOR_Z_FLAG", 3.0))
SENSOR_MIN_PERSIST_H: int = int(getattr(_cfg, "SENSOR_MIN_PERSIST_H", 6))
SENSOR_CORR_MIN: float = float(getattr(_cfg, "SENSOR_CORR_MIN", 0.5))

NEIGHBOUR_MAX_KM = 40.0      # neighbours must be within this distance
NEIGHBOUR_MIN_KM = 0.05      # ignore duplicates / the station itself
RECENT_HOURS = 72            # window used for the station summary
WATCH_PERSIST_H = 3          # persistence that triggers 'watch'
WATCH_Z = 2.0                # average |z| that triggers 'watch'
WATCH_CORR = 0.4             # correlation below this triggers 'watch'


def safe_nanmean(values: ArrayLike) -> float:
    """Mean over non-NaN values; NaN if there are none (no warnings)."""
    arr = np.asarray(values, dtype=float)
    mask = ~np.isnan(arr)
    return float(np.mean(arr[mask])) if bool(np.any(mask)) else float("nan")


def safe_nanmax(values: ArrayLike, default: float = 0.0) -> float:
    """Max over non-NaN values; `default` if there are none (no warnings)."""
    arr = np.asarray(values, dtype=float)
    mask = ~np.isnan(arr)
    return float(np.max(arr[mask])) if bool(np.any(mask)) else default


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r_earth = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    return float(2.0 * r_earth * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a)))


def compute_distance_matrix(stations_df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    station_ids = [str(s) for s in stations_df["station_id"].tolist()]
    n = len(station_ids)
    dist = np.zeros((n, n), dtype=float)
    coords = stations_df[["lat", "lon"]].to_numpy(dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_km(float(coords[i, 0]), float(coords[i, 1]),
                             float(coords[j, 0]), float(coords[j, 1]))
            dist[i, j] = d
            dist[j, i] = d
    return dist, station_ids


def rolling_corr_np(x: np.ndarray, y: np.ndarray, window: int, min_periods: int) -> np.ndarray:
    """Rolling Pearson correlation using only hours where both values exist."""
    n = len(x)
    out = np.full(n, np.nan)
    for t in range(n):
        lo = max(0, t - window + 1)
        xs, ys = x[lo : t + 1], y[lo : t + 1]
        ok = ~(np.isnan(xs) | np.isnan(ys))
        if ok.sum() < min_periods:
            continue
        xs, ys = xs[ok], ys[ok]
        if np.std(xs) == 0 or np.std(ys) == 0:
            continue
        out[t] = float(np.corrcoef(xs, ys)[0, 1])
    return out


def run_sensor_check(
    hourly_df: pd.DataFrame, stations_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    # PM2.5 and PM10 matrices: time x station_id
    pm25_mat = hourly_df.pivot(index="time", columns="station_id", values="pm25")
    pm10_mat = hourly_df.pivot(index="time", columns="station_id", values="pm10")

    dist_mat, station_ids = compute_distance_matrix(stations_df)
    st_idx = {sid: i for i, sid in enumerate(station_ids)}

    # Keep only stations that are in both the station list and the hourly data
    common_stations = [s for s in station_ids if s in pm25_mat.columns]
    pm25_mat = pm25_mat[common_stations]
    pm25_vals: NDArray[np.float64] = np.asarray(pm25_mat.to_numpy(dtype=float), dtype=np.float64)  # (n_times, n_stations)

    times = pm25_mat.index
    n_times = len(times)
    n_stations = len(common_stations)
    common_idx = [st_idx[s] for s in common_stations]

    expected_mat = np.full((n_times, n_stations), np.nan)
    spread_mat = np.full((n_times, n_stations), np.nan)

    # 1. IDW expected value and spatial spread
    for s_col, sid in enumerate(common_stations):
        dists = dist_mat[st_idx[sid], common_idx]
        neighbour_mask = (dists > NEIGHBOUR_MIN_KM) & (dists <= NEIGHBOUR_MAX_KM)
        neighbour_indices = np.where(neighbour_mask)[0]
        nearest = neighbour_indices[np.argsort(dists[neighbour_indices])][:SENSOR_K_NEIGHBOURS]
        if len(nearest) == 0:
            continue

        weights = 1.0 / (dists[nearest] ** 2)
        nbr_vals = pm25_vals[:, nearest]                       # (n_times, k)
        valid = ~np.isnan(nbr_vals)

        w_valid = np.where(valid, weights[None, :], 0.0)
        w_sums = w_valid.sum(axis=1)
        has_data = w_sums > 0

        clean_nbr = np.where(valid, nbr_vals, 0.0)
        exp_vals = np.full(n_times, np.nan)
        exp_vals[has_data] = (clean_nbr * w_valid).sum(axis=1)[has_data] / w_sums[has_data]
        expected_mat[:, s_col] = exp_vals

        clean_exp = np.where(has_data, exp_vals, 0.0)[:, None]
        diff_sq = np.where(valid, (clean_nbr - clean_exp) ** 2, 0.0)
        spread = np.sqrt((diff_sq * w_valid).sum(axis=1) / np.maximum(w_sums, 1e-6))
        spread_mat[:, s_col] = np.where(has_data, spread, np.nan)

    # 2. Residuals and station-specific z-scores
    residuals = pm25_vals - expected_mat
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        res_stds = np.nanstd(residuals, axis=0)
        res_means = np.nanmean(residuals, axis=0)
    res_stds = np.where(np.isnan(res_stds) | (res_stds < 1.0), 1.0, res_stds)
    res_means = np.where(np.isnan(res_means), 0.0, res_means)
    z_scores = (residuals - res_means[None, :]) / res_stds[None, :]

    # 3. Persistence counter (consecutive hours with |z| >= threshold)
    persist_counts = np.zeros_like(z_scores)
    for j in range(n_stations):
        run = 0
        for t in range(n_times):
            z = z_scores[t, j]
            if not np.isnan(z) and abs(z) >= SENSOR_Z_FLAG:
                run += 1
            else:
                run = 0
            persist_counts[t, j] = run

    # 4. 24 h rolling correlation with the all-station median
    with np.errstate(all="ignore"):
        nbr_medians = np.asarray(np.nanmedian(pm25_vals, axis=1), dtype=float)
    corr24_mat = np.full((n_times, n_stations), np.nan)
    for j in range(n_stations):
        corr24_mat[:, j] = rolling_corr_np(
            np.asarray(pm25_vals[:, j], dtype=float), nbr_medians, 24, 12
        )

    # Station-level summary over the most recent window
    name_map = dict(zip(stations_df["station_id"], stations_df["name"]))
    region_map = dict(zip(stations_df["station_id"], stations_df["region"]))
    coords_map = {r["station_id"]: (r["lat"], r["lon"]) for _, r in stations_df.iterrows()}
    recent: slice = slice(-RECENT_HOURS, None) if n_times >= RECENT_HOURS else slice(0, None)

    rows: list[dict[str, Any]] = []
    for j, sid in enumerate(common_stations):
        lat, lon = coords_map.get(sid, (np.nan, np.nan))

        obs = safe_nanmean(pm25_vals[recent, j])
        exp = safe_nanmean(expected_mat[recent, j])
        spr = safe_nanmean(spread_mat[recent, j])
        res = obs - exp if not (np.isnan(obs) or np.isnan(exp)) else float("nan")
        z_mean = safe_nanmean(z_scores[recent, j])
        max_persist = int(safe_nanmax(persist_counts[recent, j], default=0.0))
        corr = safe_nanmean(corr24_mat[recent, j])

        # Cross-pollutant check
        pm10_recent = float("nan")
        if sid in pm10_mat.columns:
            pm10_recent = safe_nanmean(pm10_mat[sid].to_numpy(dtype=float)[recent])
        ratio_inconsistent = (
            not np.isnan(obs) and not np.isnan(pm10_recent)
            and pm10_recent > 0 and obs > 1.25 * pm10_recent + 15
        )

        status = "OK"
        reasons: list[str] = []

        if np.isnan(obs) or np.isnan(exp):
            status = "unassessed"
            reasons.append("Not assessed: no recent data or no valid neighbours within "
                           f"{NEIGHBOUR_MAX_KM:.0f} km")
        else:
            low_corr = bool(np.isnan(corr) or corr < SENSOR_CORR_MIN)
            large_dev = (not np.isnan(z_mean)) and abs(z_mean) >= SENSOR_Z_FLAG
            if max_persist >= SENSOR_MIN_PERSIST_H and (low_corr or large_dev):
                status = "suspect"
                direction = "higher" if z_mean > 0 else "lower"
                reasons.append(
                    f"Persistent deviation ({max_persist} consecutive hours with |z| >= {SENSOR_Z_FLAG:g}), "
                    f"reading {direction} than its {SENSOR_K_NEIGHBOURS} nearest neighbours would suggest"
                )
                if low_corr and not np.isnan(corr):
                    reasons.append(f"Low correlation with the regional trend (r={corr:.2f})")
                if ratio_inconsistent:
                    reasons.append("PM2.5 is implausibly high compared with PM10, so the PM2.5 measurement may be affected")
            elif (max_persist >= WATCH_PERSIST_H
                  or (not np.isnan(z_mean) and abs(z_mean) >= WATCH_Z)
                  or (not np.isnan(corr) and corr < WATCH_CORR)):
                status = "watch"
                reasons.append(
                    f"Moderate or short-lived deviation (average |z|={abs(z_mean):.1f}, "
                    f"{max_persist} h persistence)"
                )
                if not np.isnan(corr) and corr < WATCH_CORR:
                    reasons.append(f"Weak tracking of the regional trend (r={corr:.2f})")
            else:
                reasons.append(
                    f"Tracking its neighbourhood (r={corr:.2f}, typical residual about +/-{res_stds[j]:.1f} ug/m3)"
                )

        rows.append({
            "station_id": sid,
            "name": name_map.get(sid, sid),
            "region": region_map.get(sid, "Delhi"),
            "lat": lat,
            "lon": lon,
            "observed_pm25": round(obs, 1) if not np.isnan(obs) else None,
            "expected_pm25": round(exp, 1) if not np.isnan(exp) else None,
            "expected_spread": round(spr, 1) if not np.isnan(spr) else None,
            "residual_pm25": round(res, 1) if not np.isnan(res) else None,
            "z_score": round(z_mean, 2) if not np.isnan(z_mean) else None,
            "hours_persistent": max_persist,
            "corr24h": round(corr, 2) if not np.isnan(corr) else None,
            "status": status,
            "reasons": "; ".join(reasons),
        })

    return pd.DataFrame(rows), pd.DataFrame(pm25_mat)


def validate_sensor_check(
    hourly_df: pd.DataFrame, stations_df: pd.DataFrame
) -> dict[str, Any]:
    """Synthetic fault-injection test.

    Takes the 5 stations with the most complete PM2.5 data and corrupts a copy of their last
    48 hours: 3 get a +45% calibration offset, 2 drop to a flat 3 ug/m3 (inlet blockage).
    All other stations are left untouched. Reports how many injected stations are flagged
    (detection rate) and how many untouched stations are flagged (false-alarm rate), both for
    'suspect or watch' and for 'suspect' only.
    Note: the corrupted stations also act as neighbours of the untouched ones, which is a
    deliberately harsh test for false alarms.
    """
    in_data = set(hourly_df["station_id"].unique())
    stations = [str(s) for s in stations_df["station_id"].tolist() if str(s) in in_data]
    if len(stations) < 10:
        return {"error": "Need at least 10 stations with data to run the validation",
                "total_stations_evaluated": len(stations), "benchmark_passed": False}

    completeness = hourly_df.groupby("station_id")["pm25"].apply(lambda s: float(s.notna().mean()))
    ranked = sorted(stations, key=lambda s: (-float(completeness.get(s, 0.0)), s))
    test_stations = ranked[:5]
    untouched = [s for s in stations if s not in test_stations]

    df_copy = hourly_df.copy()
    last_times = sorted(df_copy["time"].unique())[-48:]
    in_last = df_copy["time"].isin(last_times)

    drift_stations = test_stations[:3]
    flat_stations = test_stations[3:5]
    mask_drift = df_copy["station_id"].isin(drift_stations) & in_last
    mask_flat = df_copy["station_id"].isin(flat_stations) & in_last
    df_copy.loc[mask_drift, "pm25"] = df_copy.loc[mask_drift, "pm25"] * 1.45
    df_copy.loc[mask_flat, "pm25"] = 3.0

    val_summary, _ = run_sensor_check(df_copy, stations_df)
    status_by_station = dict(zip(val_summary["station_id"], val_summary["status"]))

    def flagged(ids: list[str], levels: set[str]) -> int:
        return sum(1 for s in ids if status_by_station.get(s) in levels)

    both = {"suspect", "watch"}
    only = {"suspect"}
    n_inj, n_unt = len(test_stations), max(len(untouched), 1)

    tp_both, tp_only = flagged(test_stations, both), flagged(test_stations, only)
    fp_both, fp_only = flagged(untouched, both), flagged(untouched, only)

    detection_pct = round(100.0 * tp_both / n_inj, 1)
    false_alarm_pct = round(100.0 * fp_both / n_unt, 1)

    return {
        "total_stations_evaluated": len(stations),
        "injected_fault_stations": n_inj,
        "untouched_stations": len(untouched),
        "fault_types": ["+45% calibration offset (last 48 h)", "Inlet blockage: flat drop to 3 ug/m3 (last 48 h)"],
        "true_positives_detected": tp_both,
        "detection_rate_pct": detection_pct,
        "false_alarm_rate_pct": false_alarm_pct,
        "detection_rate_suspect_only_pct": round(100.0 * tp_only / n_inj, 1),
        "false_alarm_rate_suspect_only_pct": round(100.0 * fp_only / n_unt, 1),
        "definition": "detection and false-alarm rates count stations flagged 'suspect' or 'watch'; "
                      "the *_suspect_only values count 'suspect' alone",
        "benchmark_passed": detection_pct >= 80.0 and false_alarm_pct <= 10.0,
        "methodology": f"Inverse-distance weighting (k={SENSOR_K_NEIGHBOURS}, {NEIGHBOUR_MAX_KM:.0f} km) "
                       "with persistent z-score residual analysis",
    }


def main() -> None:
    station_hourly_path = PROCESSED / "station_hourly_final.csv"
    stations_ref_path = REF / "stations.csv"

    if not station_hourly_path.exists() or not stations_ref_path.exists():
        sys.exit(f"Missing required data in {PROCESSED} or {REF}.")

    print("Loading station observations and geography...")
    stations_df = pd.read_csv(stations_ref_path)
    hourly_df = pd.read_csv(station_hourly_path, usecols=["time", "station_id", "pm25", "pm10"])

    print(f"Running spatial neighbourhood consistency check on {len(stations_df)} stations...")
    summary_df, _ = run_sensor_check(hourly_df, stations_df)

    out_csv = PROCESSED / "sensor_health.csv"
    tag_synthetic(summary_df).to_csv(out_csv, index=False)

    print("Running synthetic fault-injection validation...")
    val_report = validate_sensor_check(hourly_df, stations_df)
    out_json = PROCESSED / "sensor_validation_report.json"
    with open(out_json, "w") as f:
        json.dump(val_report, f, indent=2)

    print("=" * 80)
    print(" POLLUTION BLAME LEDGER - SENSOR HEALTH ASSESSMENT ")
    print("=" * 80)
    print(f"Total stations assessed: {len(summary_df)}")
    print("\nStatus breakdown:")
    print(summary_df["status"].value_counts().to_string())

    flagged_df = summary_df[summary_df["status"].isin(["watch", "suspect"])]
    if len(flagged_df) > 0:
        print("\nStations on the watch / suspect list:")
        cols = ["station_id", "name", "observed_pm25", "expected_pm25", "residual_pm25", "status", "reasons"]
        print(flagged_df[cols].to_string(index=False))
    else:
        print("\nAll assessed stations track within their neighbourhood tolerance.")

    print("\nValidation results (synthetic fault injection):")
    if "error" in val_report:
        print(f"  Skipped: {val_report['error']}")
    else:
        print(f"  Detection rate (suspect or watch)  : {val_report['detection_rate_pct']}% (target >= 80%)")
        print(f"  False-alarm rate (suspect or watch): {val_report['false_alarm_rate_pct']}% (target <= 10%)")
        print(f"  Detection / false alarms, suspect only: "
              f"{val_report['detection_rate_suspect_only_pct']}% / {val_report['false_alarm_rate_suspect_only_pct']}%")
        print(f"  Benchmark: {'PASS' if val_report['benchmark_passed'] else 'REVIEW'}")

    print(f"\nSaved sensor health -> {out_csv}")
    print(f"Saved validation    -> {out_json}")
    print("=" * 80)


if __name__ == "__main__":
    main()