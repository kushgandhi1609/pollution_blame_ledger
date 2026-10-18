"""
forecast.py - Multi-horizon (24h and 48h) PM2.5 forecasting engine for Delhi-NCR.

HOW IT WORKS:
1. Inputs: City-level hourly features from pipeline/data/processed/city_hourly_final.csv.
   Uses strictly leakage-free features (look_ahead == 0):
   - Current & lagged pollution (pm25 median, 24h rolling mean, 3h diff, background, NCR median)
   - Atmospheric dispersion (wind speed 10m/100m, u/v components, BLH, ventilation index, rain)
   - Trajectory fire pathway (linked fires, travel lag, PBHR parcel fraction, raw fires)
   - Temporal & calendar markers (hour sin/cos, rush hour flags, weekend, Diwali window)
2. Modeling Architecture:
   - Gradient Boosting Regressor (HistGradientBoostingRegressor) predicting log(PM2.5)
   - Point forecast (squared_error loss)
   - Uncertainty envelope (quantile regression at 10th and 90th percentiles for an 80% interval)
3. Rigorous Evaluation:
   - 5-fold Time-Series Blocked Cross-Validation with a 72-hour purge gap between train and test.
   - Benchmark Comparisons:
     a. Persistence Baseline: tomorrow's PM2.5 equals today's PM2.5 (y_{t+h} = y_t)
     b. Diurnal/Seasonal Baseline: hour-of-day mean from training history
   - Metrics: MAE (ug/m3), RMSE (ug/m3), R2, and CPCB AQI Category Concordance (%)
4. Stated Scientific Limitations:
   - Training uses observed historical meteorology; operational real-time use relies on NWP forecast weather.
   - Sudden episodic surges (e.g. firecracker bursts or abrupt crop fire burning peaks) remain challenging.

Outputs (in pipeline/data/processed):
  - forecast_hourly.csv : issued forecasts for 24h and 48h horizons with uncertainty intervals and AQI categories
  - forecast_eval.csv   : performance comparison of model vs persistence vs diurnal baseline
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from common import tag_synthetic  # type: ignore

from config import FS_GAP_HOURS, FS_N_SPLITS, PROCESSED, RNG_SEED  # type: ignore

HORIZONS = [24, 48]

CANDIDATE_FEATURES = [
    # Recent pollution
    "delhi_pm25_median",
    "delhi_pm25_24h_mean",
    "delhi_pm25_diff3h",
    "delhi_pm25_diff24h",
    "delhi_regional_background_pm25",
    "delhi_background_share",
    "ncr_pm25_median",
    "ncr_minus_delhi_pm25",
    # Weather & Dispersion
    "temp_c",
    "rh_pct",
    "pressure_hpa",
    "wind_speed_ms",
    "wind_speed_100m_ms",
    "wind_u",
    "wind_v",
    "wind_dir_sin",
    "wind_dir_cos",
    "nw_wind_flag",
    "blh_m",
    "ventilation_m2s",
    "precip_24h_mm",
    "precip_72h_mm",
    "temp_range_24h_c",
    "pressure_change_6h",
    "wind_speed_roll6h",
    "stagnation_flag",
    # Trajectory & Fire pathway
    "traj_mean_speed_kmh",
    "traj_dist_48h_km",
    "traj_origin_bearing_48h",
    "traj_pbhr_frac",
    "traj_origin_sin",
    "traj_origin_cos",
    "fires_linked_median",
    "frp_linked_median",
    "fire_lag_p50_h",
    "fire_member_agree_frac",
    "raw_fires_24h_pbhr",
    # Calendar & Diwali
    "hour_sin",
    "hour_cos",
    "is_rush_am",
    "is_rush_pm",
    "is_night",
    "is_weekend",
    "days_from_diwali",
    "diwali_window",
]


def aqi_label(val: float) -> str:
    if np.isnan(val) or val < 0:
        return "unknown"
    if val <= 30:
        return "good"
    if val <= 60:
        return "satisfactory"
    if val <= 90:
        return "moderate"
    if val <= 120:
        return "poor"
    if val <= 250:
        return "very_poor"
    return "severe"


def evaluate_forecasts(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    
    # Categorical AQI accuracy
    cats_true = [aqi_label(v) for v in y_true]
    cats_pred = [aqi_label(v) for v in y_pred]
    cat_acc = np.mean([t == p for t, p in zip(cats_true, cats_pred)]) * 100.0
    
    return {
        "mae_ugm3": round(float(mae), 2),
        "rmse_ugm3": round(float(rmse), 2),
        "r2_score": round(float(r2), 3),
        "aqi_category_acc_pct": round(float(cat_acc), 1),
    }


def time_series_cv_folds(n_samples: int, n_splits: int, gap: int):
    fold_size = n_samples // (n_splits + 1)
    for i in range(1, n_splits + 1):
        train_end = fold_size * i
        test_start = train_end + gap
        test_end = min(test_start + fold_size, n_samples)
        if test_start < n_samples and test_end > test_start:
            yield np.arange(0, train_end), np.arange(test_start, test_end)


def main():
    city_hourly_path = PROCESSED / "city_hourly_final.csv"
    if not city_hourly_path.exists():
        sys.exit(f"Missing {city_hourly_path}. Run pipeline/s7_final.py first.")

    print("Loading city-level hourly dataset...")
    df = pd.read_csv(city_hourly_path, parse_dates=["time"])
    df = df.sort_values("time").reset_index(drop=True)

    # Filter candidate features to those actually present
    features = [f for f in CANDIDATE_FEATURES if f in df.columns]
    print(f"Using {len(features)} leakage-free driver and meteorological features.")

    eval_records = []
    operational_forecasts = []

    for h in HORIZONS:
        print(f"\nEvaluating and training {h}-hour forecast horizon (+{h}h)...")
        # Target: PM2.5 shifted forward by h hours
        df[f"target_{h}h"] = df["delhi_pm25_median"].shift(-h)
        
        # Valid dataset mask (requires feature vector and forward target)
        valid_mask = df[f"target_{h}h"].notna() & df["delhi_pm25_median"].notna()
        sub_df = pd.DataFrame(df.loc[valid_mask].copy()).reset_index(drop=True)
        
        feat_df = pd.DataFrame(sub_df[features])
        X = feat_df.fillna(feat_df.median())
        y_raw = sub_df[f"target_{h}h"].to_numpy(dtype=float)
        y_log = np.log(np.maximum(y_raw, 1.0))
        y_persistence = sub_df["delhi_pm25_median"].to_numpy(dtype=float)  # Persistence baseline

        # Cross-validation
        n_samples = len(sub_df)
        cv_model_preds = []
        cv_persist_preds = []
        cv_diurnal_preds = []
        cv_y_true = []

        folds = list(time_series_cv_folds(n_samples, FS_N_SPLITS, FS_GAP_HOURS))
        for train_idx, test_idx in folds:
            X_tr, y_tr_log = X.iloc[train_idx], y_log[train_idx]
            X_te, y_te_raw = X.iloc[test_idx], y_raw[test_idx]

            # Train Model
            reg = HistGradientBoostingRegressor(
                loss="squared_error", max_iter=150, min_samples_leaf=15, random_state=RNG_SEED
            )
            reg.fit(X_tr, y_tr_log)
            pred_raw = np.exp(reg.predict(X_te))

            # Diurnal baseline: mean target by hour of day from train set
            train_hours = sub_df.iloc[train_idx]["hour"].to_numpy(dtype=int)
            hour_means = {hr: float(np.mean(y_raw[train_idx][train_hours == hr])) for hr in range(24) if np.any(train_hours == hr)}
            test_hours = sub_df.iloc[test_idx]["hour"].to_numpy(dtype=int)
            default_val = float(np.mean(y_raw[train_idx]))
            pred_diurnal = np.array([hour_means.get(hr, default_val) for hr in test_hours])

            cv_model_preds.extend(pred_raw)
            cv_persist_preds.extend(y_persistence[test_idx])
            cv_diurnal_preds.extend(pred_diurnal)
            cv_y_true.extend(y_te_raw)

        # Compute CV evaluation metrics
        m_model = evaluate_forecasts(np.array(cv_y_true), np.array(cv_model_preds))
        m_persist = evaluate_forecasts(np.array(cv_y_true), np.array(cv_persist_preds))
        m_diurnal = evaluate_forecasts(np.array(cv_y_true), np.array(cv_diurnal_preds))

        eval_records.append(
            dict(horizon_h=h, method="Gradient Boosting (Ledger Engine)", beats_persistence=m_model["mae_ugm3"] < m_persist["mae_ugm3"], **m_model)
        )
        eval_records.append(
            dict(horizon_h=h, method="Persistence Baseline (y_t+h = y_t)", beats_persistence=False, **m_persist)
        )
        eval_records.append(
            dict(horizon_h=h, method="Diurnal Seasonal Mean Baseline", beats_persistence=False, **m_diurnal)
        )

        # Train Full Production Models for operational forecasting
        print(f"Training operational models for horizon +{h}h (median, 10th and 90th percentiles)...")
        reg_mid = HistGradientBoostingRegressor(
            loss="squared_error", max_iter=150, min_samples_leaf=15, random_state=RNG_SEED
        ).fit(X, y_log)

        reg_q10 = HistGradientBoostingRegressor(
            loss="quantile", quantile=0.10, max_iter=150, min_samples_leaf=15, random_state=RNG_SEED
        ).fit(X, y_log)

        reg_q90 = HistGradientBoostingRegressor(
            loss="quantile", quantile=0.90, max_iter=150, min_samples_leaf=15, random_state=RNG_SEED
        ).fit(X, y_log)

        # Generate forecasts for all hours in dataset
        all_feat = pd.DataFrame(df[features])
        all_X = all_feat.fillna(all_feat.median())
        pred_mid = np.exp(reg_mid.predict(all_X))
        pred_lo = np.exp(reg_q10.predict(all_X))
        pred_hi = np.exp(reg_q90.predict(all_X))

        # Enforce logical envelope: lo <= mid <= hi
        pred_lo = np.minimum(pred_lo, pred_mid)
        pred_hi = np.maximum(pred_hi, pred_mid)

        for idx, row in df.iterrows():
            issue_t = row["time"]
            target_t = issue_t + pd.Timedelta(hours=h)
            p_val = round(float(pred_mid[idx]), 1)
            p_lo = round(float(pred_lo[idx]), 1)
            p_hi = round(float(pred_hi[idx]), 1)
            cat = aqi_label(p_val)

            operational_forecasts.append(
                dict(
                    issue_time=issue_t,
                    target_time=target_t,
                    horizon_h=h,
                    pm25_pred=p_val,
                    pm25_low=p_lo,
                    pm25_high=p_hi,
                    aqi_category=cat,
                )
            )

    eval_df = pd.DataFrame(eval_records)
    out_eval = PROCESSED / "forecast_eval.csv"
    tag_synthetic(eval_df).to_csv(out_eval, index=False)

    forecast_df = pd.DataFrame(operational_forecasts)
    out_forecast = PROCESSED / "forecast_hourly.csv"
    tag_synthetic(forecast_df).to_csv(out_forecast, index=False)

    print("\n" + "=" * 80)
    print(" POLLUTION BLAME LEDGER - FORECAST ENGINE EVALUATION REPORT ")
    print("=" * 80)
    print(eval_df[["horizon_h", "method", "mae_ugm3", "rmse_ugm3", "r2_score", "aqi_category_acc_pct", "beats_persistence"]].to_string(index=False))

    print("\nSample Forecast Output (Latest 5 Issue Hours for +24h and +48h):")
    sample = pd.DataFrame(forecast_df[forecast_df["issue_time"].isin(list(df["time"].tail(3)))]).sort_values(by=["issue_time", "horizon_h"])
    print(sample[["issue_time", "target_time", "horizon_h", "pm25_pred", "pm25_low", "pm25_high", "aqi_category"]].to_string(index=False))

    print(f"\nSaved forecast evaluation -> {out_eval}")
    print(f"Saved hourly forecasts   -> {out_forecast}")
    print("=" * 80)


if __name__ == "__main__":
    main()
