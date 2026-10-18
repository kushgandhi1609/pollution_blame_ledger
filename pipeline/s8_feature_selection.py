"""Step 8 - feature selection for the *driver* features.

There are no ground-truth source labels, so selection is done in two layers:
  1. EVIDENCE features (pollutant fingerprints, local/regional, NCR comparison) are kept BY DESIGN:
     they are the ledger's evidence lines, not predictors, and screening them against PM2.5 would leak.
  2. DRIVER features (weather, time, trajectory/fire) are screened statistically against
     log(Delhi median PM2.5) using only features that cannot contain PM2.5 information:
       a) drop features with > FS_MAX_MISSING missing values
       b) drop constant features
       c) cluster features with |Spearman rho| >= FS_CORR_THRESHOLD and keep one per cluster
       d) gradient-boosting model, blocked time-series CV with a gap, permutation importance on
          held-out folds; a feature is kept only if it beats the best 'shadow' (shuffled) feature.
Outputs: data/processed/feature_selection_report.csv, data/processed/selected_features.json
"""
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score
from sklearn.model_selection import TimeSeriesSplit

from config import PROCESSED, FS_MAX_MISSING, FS_CORR_THRESHOLD, FS_N_SPLITS, FS_GAP_HOURS, FS_MIN_IMPORTANCE, RNG_SEED

DRIVER_GROUPS = {"weather", "time", "trajectory", "fire"}
EVIDENCE_GROUPS = {"fingerprint", "local_regional", "ncr", "ratio"}
EXCLUDE = {"hour", "dow", "month", "fire_link_computed",    # pure calendar / bookkeeping
           "traj_origin_bearing_48h", "wind_dir_deg"}         # raw angles: use their sin/cos versions


def main():
    city = pd.read_csv(PROCESSED / "city_hourly_final.csv", parse_dates=["time"])
    dd = pd.read_csv(PROCESSED / "data_dictionary.csv")
    dd = dd[dd.table == "city_hourly_final"].set_index("column")
    group = dd["group"].to_dict()
    look_ahead = dd["look_ahead"].to_dict()

    cand = [c for c in city.columns if group.get(c) in DRIVER_GROUPS and c not in EXCLUDE
            and not look_ahead.get(c, 0)]
    y = pd.Series(np.log1p(city["delhi_pm25_median"]))
    keep_rows = y.notna()
    X = pd.DataFrame(city.loc[keep_rows, cand]).reset_index(drop=True)
    y = pd.Series(y[keep_rows]).reset_index(drop=True)
    t = pd.Series(city.loc[keep_rows, "time"]).reset_index(drop=True)

    rep = pd.DataFrame({"feature": cand, "group": [group[c] for c in cand]})
    rep["missing_frac"] = [X[c].isna().mean() for c in cand]
    rep["n_unique"] = [X[c].nunique() for c in cand]
    rep["pass_missing"] = rep.missing_frac <= FS_MAX_MISSING
    rep["pass_variance"] = rep.n_unique > 1
    ok = rep[rep.pass_missing & rep.pass_variance].feature.tolist()

    # ---- correlation clusters (greedy; least-missing features win)
    X_ok = pd.DataFrame(X[ok])
    corr = pd.DataFrame(X_ok.corr(method="spearman")).abs()
    order = sorted(ok, key=lambda c: (X[c].isna().mean(), c))
    kept, dropped_for = [], {}
    for c in order:
        clash = [k for k in kept if corr.loc[c, k] >= FS_CORR_THRESHOLD]
        if clash:
            dropped_for[c] = clash[0]
        else:
            kept.append(c)
    rep["pass_correlation"] = rep.feature.isin(kept)
    rep["redundant_with"] = rep.feature.map(dropped_for)

    # ---- model-based screening with shadow features
    rng = np.random.default_rng(RNG_SEED)
    Xs = X[kept].copy()
    shadows = pd.DataFrame({f"shadow_{c}": rng.permutation(np.asarray(Xs[c])) for c in kept})
    XA = pd.concat([Xs, shadows], axis=1)
    tscv = TimeSeriesSplit(n_splits=FS_N_SPLITS, gap=FS_GAP_HOURS)
    imps, scores = [], []
    for tr, te in tscv.split(XA):
        mdl = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_depth=4,
                                            random_state=RNG_SEED)
        mdl.fit(XA.iloc[tr], y.iloc[tr])
        scores.append(r2_score(y.iloc[te], mdl.predict(XA.iloc[te])))
        pi = permutation_importance(mdl, XA.iloc[te], y.iloc[te], n_repeats=5, random_state=RNG_SEED, n_jobs=-1)
        imp_mean = getattr(pi, "importances_mean", None)
        if imp_mean is None:
            imp_mean = pi["importances_mean"]
        imps.append(imp_mean)
    imp = pd.DataFrame(imps, columns=XA.columns)
    mean_imp, std_imp = imp.mean(), imp.std()
    shadow_max = mean_imp[[c for c in XA.columns if c.startswith("shadow_")]].max()
    rep["perm_importance_mean"] = rep.feature.map(mean_imp)
    rep["perm_importance_std"] = rep.feature.map(std_imp)
    rep["beats_shadow"] = rep.perm_importance_mean > max(shadow_max, FS_MIN_IMPORTANCE)
    rep["folds_positive"] = rep.feature.map((imp > 0).mean())          # stability across CV folds
    rep["selected"] = rep.pass_correlation & rep.beats_shadow & (rep.folds_positive >= 0.8)
    rep = rep.sort_values(["selected", "perm_importance_mean"], ascending=[False, False])
    rep.to_csv(PROCESSED / "feature_selection_report.csv", index=False)

    evidence = {}
    for c, gname in group.items():
        if gname in EVIDENCE_GROUPS and c in city.columns:
            evidence.setdefault(gname, []).append(c)
    out = {
        "note": "Driver features are statistically screened; evidence features are kept by design.",
        "cv_r2_per_fold": [round(float(s), 3) for s in scores],
        "importance_threshold": float(max(shadow_max, FS_MIN_IMPORTANCE)),
        "driver_features_selected": rep.loc[rep.selected, "feature"].tolist(),
        "driver_features_dropped": {
            "too_many_missing": rep.loc[~rep.pass_missing, "feature"].tolist(),
            "constant": rep.loc[~rep.pass_variance, "feature"].tolist(),
            "redundant": dropped_for,
            "not_better_than_noise": rep.loc[rep.pass_correlation & ~rep.selected, "feature"].tolist()},
        "evidence_features_by_design": evidence,
    }
    (PROCESSED / "selected_features.json").write_text(json.dumps(out, indent=2))
    print("CV R2 per fold:", out["cv_r2_per_fold"])
    print("selected drivers:", out["driver_features_selected"])
    print("redundant:", dropped_for)


if __name__ == "__main__":
    main()
