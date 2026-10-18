"""
attribution.py - builds the "ledger": one entry per episode and source.

HOW IT WORKS (plain words)
1. BASELINE: published source shares (low / mid / high) from reference_apportionment.csv.
   For each episode we leave out any study that covers the SAME dates, so the later backtest
   is a fair test (otherwise the model would just copy the answer).
2. EVIDENCE: for each source we look at the episode's evidence (wind-linked fires, fingerprints,
   local-vs-regional split, Delhi-vs-NCR pattern, weather) and turn each into a score between
   -1 (evidence points against) and +1 (evidence points toward), by comparing the episode with
   all other days in the dataset.
3. ADJUST + UNCERTAINTY: a Monte Carlo run (5000 draws) samples the baseline inside its published
   range, nudges each source up or down by its evidence score (the nudge sizes in K below are
   MODELLING CHOICES, not measurements), and rescales to 100%. We report the 5th-50th-95th percentile.
4. GRADE: A / B / C by how many independent modules agree (see grade()).

Outputs (in data/processed):  ledger_entries.csv   ledger_sensitivity.csv
Run from the pipeline folder:  python ../analysis/attribution.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from common import tag_synthetic  # type: ignore

from config import PROCESSED, REF, RNG_SEED, SYNTHETIC  # type: ignore

# ----------------------------------------------------------------- settings (all documented choices)
SOURCES = ["stubble_burning", "vehicular", "dust", "industry", "other"]
N_DRAWS = 5000
SEASONAL_MAX_DAYS = 200        # reference rows longer than this are treated as annual, not seasonal
DEFAULT_REL_SPREAD = 0.25      # if a study gives only a mid value, assume +/-25% (flagged in the ledger)
EVIDENCE_NOISE_SD = 0.15       # noise added to each evidence score in the Monte Carlo
SUPPORT_T = 0.25               # module score needed to count as supporting / contradicting
K = {"stubble_burning": 0.9, "vehicular": 0.4, "dust": 0.4, "industry": 0.4, "other": 0.0}
GRADED_MODULES = {"trajectory", "fingerprint", "local_regional", "ncr_regime"}   # 'weather' is context only
PCTS = (5, 50, 95)
EXCLUDED_YEARS = {2017}        # seasons that failed data validation: their episodes are skipped

# (module, hourly column, direction, plain-language label)
IND = {
    "stubble_burning": [
        ("trajectory", "fires_linked_median", +1, "Upwind fires linked to Delhi's air by wind paths (per hour)"),
        ("trajectory", "fire_member_agree_frac", +1, "Share of wind-path ensemble members passing over fires"),
        ("trajectory", "traj_pbhr_frac", +1, "Share of the 48 h wind path over Punjab/Haryana"),
        ("trajectory", "nw_wind_flag", +1, "Share of hours with north-westerly wind"),
        ("fingerprint", "delhi_fp_biomass_ratio", +1, "PM2.5/PM10 ratio (biomass-burning fingerprint)"),
        ("fingerprint", "delhi_fp_biomass_night_rise", +1, "Night-time PM2.5 rise (biomass-burning fingerprint)"),
        ("local_regional", "delhi_background_share", +1, "Regional-background share of Delhi PM2.5"),
        ("ncr_regime", "_widespread", +1, "Share of hours with a Delhi-and-NCR-wide rise"),
    ],
    "vehicular": [
        ("fingerprint", "delhi_fp_traffic_z", +1, "Traffic fingerprint (CO/NO2 above normal)"),
        ("fingerprint", "delhi_fp_traffic_rush_ratio_no2", +1, "NO2 rush-hour peak ratio"),
        ("local_regional", "delhi_background_share", -1, "Regional-background share (lower = more local)"),
        ("local_regional", "delhi_hotspot_count", +1, "Number of local hotspot stations"),
        ("ncr_regime", "_delhi_conc", +1, "Share of hours with a Delhi-concentrated rise"),
        ("ncr_regime", "_widespread", -1, "Share of hours with a region-wide rise (lower favours local sources)"),
        ("weather", "stagnation_flag", +1, "Share of stagnant-air hours"),
        ("weather", "ventilation_m2s", -1, "Ventilation index (lower = air trapped)"),
    ],
    "dust": [
        ("fingerprint", "delhi_fp_dust_ratio", +1, "PM10/PM2.5 ratio (dust fingerprint)"),
        ("fingerprint", "delhi_fp_dust_z", +1, "Dust fingerprint (z-score)"),
        ("local_regional", "delhi_background_share", -1, "Regional-background share (lower = more local)"),
        ("ncr_regime", "_delhi_conc", +1, "Share of hours with a Delhi-concentrated rise"),
        ("weather", "wind_speed_ms", +1, "Wind speed (stronger wind lifts dust)"),
        ("weather", "precip_72h_mm", -1, "Rain in the previous 72 h (dry = more dust)"),
    ],
    "industry": [
        ("fingerprint", "delhi_fp_industrial_so2_z", +1, "SO2 fingerprint (industrial/coal)"),
        ("local_regional", "delhi_background_share", -1, "Regional-background share (lower = more local)"),
        ("ncr_regime", "_delhi_conc", +1, "Share of hours with a Delhi-concentrated rise"),
    ],
    "other": [],
}

LIMITS = {
    "stubble_burning": "Fire detections show burning, not smoke amount; satellites pass only a few times a day; "
                       "wind paths are horizontal only (no vertical mixing or chemistry).",
    "vehicular": "The CO/NO2 fingerprint is shared with other combustion sources; no traffic counts are used.",
    "dust": "A high PM10/PM2.5 ratio can also come from other coarse sources; rain and humidity distort it.",
    "industry": "SO2 spikes have several possible origins; wind direction relative to industrial areas is not used.",
    "other": "No direct evidence is available for this group, so its share stays near the published baseline.",
}
COMMON_LIMIT = ("Estimate, not a measurement: published baseline adjusted by documented weights "
                "(modelling choices); the local/regional and NCR modules do not tell local sources apart; "
                "evidence modules are not fully independent (local/regional and NCR share regional PM2.5 signals); "
                "2017 season excluded due to data validation failure.")


# ----------------------------------------------------------------- loading
def load_inputs():
    hourly = pd.read_csv(PROCESSED / "city_hourly_final.csv", parse_dates=["time"])
    episodes = pd.read_csv(PROCESSED / "episodes.csv", parse_dates=["start", "end"])
    ref_path = REF / "reference_apportionment.csv"
    if not ref_path.exists():
        sys.exit(f"Missing {ref_path}. Fill the reference table first (see the guide).")
    ref = pd.read_csv(ref_path)
    need = ["study_id", "citation", "doi_or_url", "period_start", "period_end", "source",
            "low_pct", "mid_pct", "high_pct"]
    miss = [c for c in need if c not in ref.columns]
    if miss:
        sys.exit(f"reference_apportionment.csv is missing columns: {miss}")
    ref = ref.dropna(subset=["study_id", "source"]).copy()
    if "notes" not in ref.columns:
        ref["notes"] = ""
    # rows marked TESTONLY in notes are kept as the answer key for the backtest, never used in the baseline
    ref["_testonly"] = ref["notes"].astype(str).str.upper().str.contains("TESTONLY")
    if not SYNTHETIC and ref["study_id"].astype(str).str.upper().str.startswith("FAKE").any():
        sys.exit("The reference table contains FAKE test rows. Never use them with real data.")
    bad = sorted(set(ref["source"]) - set(SOURCES))
    if bad:
        sys.exit(f"Unknown source names in the reference table: {bad}. Allowed: {SOURCES}")
    for c in ["low_pct", "mid_pct", "high_pct"]:
        ref[c] = pd.to_numeric(ref[c], errors="coerce")
    for c in ["period_start", "period_end"]:
        ref[c] = pd.to_datetime(ref[c], errors="coerce")
    if bool(ref[["period_start", "period_end"]].isna().to_numpy().any()):
        sys.exit("Every reference row needs period_start and period_end as YYYY-MM-DD.")
    if bool(ref["mid_pct"].isna().to_numpy().any()):
        sys.exit("Every reference row needs mid_pct (low/high may be empty).")
    return hourly, episodes, ref


def daily_table(hourly):
    h = hourly.copy()
    h["date"] = h["time"].dt.normalize()
    h["_widespread"] = (h["regime"] == "widespread_rise").astype(float)
    h["_delhi_conc"] = (h["regime"] == "delhi_concentrated_rise").astype(float)
    h["_insufficient"] = (h["regime"] == "insufficient_data").astype(float)
    fire_ok = h["fire_link_computed"].astype(float) > 0
    for c in ["fires_linked_median", "fire_member_agree_frac"]:
        h[c] = h[c].where(fire_ok)
    cols = sorted({c for s in IND.values() for (_, c, _, _) in s} |
                  {"raw_fires_24h_pbhr", "_insufficient", "missing_data_warning"})
    cols = [c for c in cols if c in h.columns]
    return h.groupby("date")[cols].mean(numeric_only=True)


def pct_rank(series, v):
    s = series.dropna().to_numpy()
    if len(s) < 20 or pd.isna(v):
        return np.nan
    return ((s < v).sum() + 0.5 * (s == v).sum()) / len(s)


# ----------------------------------------------------------------- evidence
def episode_evidence(daily, ep):
    days = daily.loc[(daily.index >= ep["start"]) & (daily.index <= ep["end"])]
    out = {}
    for src, inds in IND.items():
        rows, mod_scores = [], {}
        for module, col, direction, label in inds:
            if col not in daily.columns:
                continue
            val = days[col].mean()
            p = pct_rank(daily[col], val)
            if np.isnan(p):
                continue
            score = (2 * p - 1) * direction
            rows.append(dict(module=module, col=col, label=label, val=val, pct=p, score=score))
            mod_scores.setdefault(module, []).append(score)
        mods = {m: float(np.mean(v)) for m, v in mod_scores.items()}
        out[src] = dict(rows=rows, modules=mods,
                        score=float(np.mean(list(mods.values()))) if mods else 0.0)
    # extra contradiction line: many fires burning but few linked to Delhi by the wind
    if "raw_fires_24h_pbhr" in daily.columns and "fires_linked_median" in daily.columns:
        pr = pct_rank(daily["raw_fires_24h_pbhr"], days["raw_fires_24h_pbhr"].mean())
        pl = pct_rank(daily["fires_linked_median"], days["fires_linked_median"].mean())
        if not np.isnan(pr) and not np.isnan(pl) and pr >= 0.75 and pl <= 0.40:
            out["stubble_burning"]["rows"].append(dict(
                module="trajectory", col="raw_vs_linked", val=np.nan, pct=np.nan, score=-1.0,
                label="Many fires were burning (raw count high) but few were linked to Delhi by the wind paths, "
                      "so the smoke probably did not reach Delhi"))
            # Update trajectory module score and overall score so grade() and adjustments reflect the contradiction
            traj_scores = [r["score"] for r in out["stubble_burning"]["rows"] if r["module"] == "trajectory"]
            out["stubble_burning"]["modules"]["trajectory"] = float(np.mean(traj_scores))
            out["stubble_burning"]["score"] = float(np.mean(list(out["stubble_burning"]["modules"].values())))
    return out, days


def describe(r):
    if r["col"] == "raw_vs_linked":
        return r["label"]
    return f"[{r['module']}] {r['label']}: episode average {r['val']:.3g} (higher than {r['pct']:.0%} of days)"


def grade(modules, data_quality_bad):
    support = [m for m, s in modules.items() if m in GRADED_MODULES and s >= SUPPORT_T]
    contra = [m for m, s in modules.items() if m in GRADED_MODULES and s <= -SUPPORT_T]
    if len(support) >= 3 and not contra:
        g = "A"
    elif len(support) >= 2 and len(contra) <= 1:
        g = "B"
    else:
        g = "C"
    if data_quality_bad and g != "C":
        g = {"A": "B", "B": "C"}[g]
    return g, support, contra


# ----------------------------------------------------------------- baseline
def baseline_for(ref, src, ep_start, ep_end):
    notes = []
    r = ref[(ref["source"] == src) & (~ref["_testonly"])].copy()
    r["_days"] = (r["period_end"] - r["period_start"]).dt.days
    r["_overlap"] = (r["period_start"] <= ep_end) & (r["period_end"] >= ep_start)
    pick = r[(r["_days"] <= SEASONAL_MAX_DAYS) & (~r["_overlap"])]
    if pick.empty:
        pick = r[~r["_overlap"]]
        if not pick.empty:
            notes.append("baseline uses annual (non-seasonal) studies")
    if pick.empty:
        pick = r
        if not pick.empty:
            notes.append("CIRCULAR: baseline includes a study covering the same dates as this episode")
    if pick.empty:
        return None, notes
    lo, hi = pick["low_pct"].copy(), pick["high_pct"].copy()
    assumed = lo.isna() | hi.isna()
    lo = lo.fillna(pick["mid_pct"] * (1 - DEFAULT_REL_SPREAD))
    hi = hi.fillna(pick["mid_pct"] * (1 + DEFAULT_REL_SPREAD))
    if assumed.any():
        notes.append(f"assumed +/-{DEFAULT_REL_SPREAD:.0%} spread for {int(assumed.sum())} study row(s) with only a mid value")
    arr = np.column_stack([np.minimum(lo, pick["mid_pct"]), pick["mid_pct"], np.maximum(hi, pick["mid_pct"])]) / 100.0
    return dict(arr=arr, ids=list(pick["study_id"].astype(str))), notes


def simulate(base, scores, kscale, rng):
    n = N_DRAWS
    draws = np.zeros((n, len(SOURCES)))
    for j, s in enumerate(SOURCES):
        arr = base[s]["arr"]
        idx = rng.integers(0, len(arr), n)
        lo, mid, hi = arr[idx, 0], arr[idx, 1], arr[idx, 2]
        x = mid.copy()
        ok = hi > lo
        if ok.any():
            x[ok] = rng.triangular(lo[ok], np.clip(mid[ok], lo[ok], hi[ok]), hi[ok])
        sc = np.clip(scores[s] + rng.normal(0, EVIDENCE_NOISE_SD, n), -1, 1)
        factor = 1 + K[s] * kscale * rng.uniform(0.5, 1.5, n) * sc
        draws[:, j] = x * np.clip(factor, 0.1, None)
    return draws / draws.sum(axis=1, keepdims=True)


# ----------------------------------------------------------------- main
def main():
    hourly, episodes, ref = load_inputs()
    daily = daily_table(hourly)
    rng = np.random.default_rng(RNG_SEED)
    rows, sens = [], []
    for _, ep in episodes.iterrows():
        ep_start = pd.Timestamp(str(ep["start"]))
        ep_end = pd.Timestamp(str(ep["end"]))
        if ep_start.year in EXCLUDED_YEARS:
            print(f"Skipping episode {ep['episode_id']} ({ep_start.date()}): season excluded after failing data validation")
            continue
        ev, days = episode_evidence(daily, ep)
        base, base_notes = {}, {}
        for s in SOURCES:
            b, n = baseline_for(ref, s, ep_start, ep_end)
            if b is None:
                sys.exit(f"No reference rows for source '{s}'. Add at least one study row for every source (rows marked TESTONLY do not count).")
            base[s], base_notes[s] = b, n
        scores = {s: ev[s]["score"] if ev[s]["modules"] else 0.0 for s in SOURCES}
        sim = simulate(base, scores, 1.0, rng)
        pct = np.percentile(sim, PCTS, axis=0) * 100
        miss = days["missing_data_warning"].mean() if "missing_data_warning" in days else 0.0
        insuf = days["_insufficient"].mean() if "_insufficient" in days else 0.0
        bad = bool(miss > 0.25 or insuf > 0.20)
        for j, s in enumerate(SOURCES):
            g, sup, con = grade(ev[s]["modules"], bad)
            fors = [describe(r) for r in ev[s]["rows"] if r["score"] >= SUPPORT_T]
            againsts = [describe(r) for r in ev[s]["rows"] if r["score"] <= -SUPPORT_T]
            arr = base[s]["arr"] * 100
            notes = list(base_notes[s])
            if bad:
                notes.append(f"data quality: {insuf:.0%} of episode hours lacked enough stations; grade lowered one level")
            if ep_start.year <= 2017:
                notes.append("2017: fewer VIIRS satellites were probably available, so fire counts are lower and not comparable with later seasons")
            rows.append(dict(
                episode_id=ep["episode_id"], start=ep_start.date(), end=ep_end.date(), source=s,
                share_low_pct=round(pct[0, j], 1), share_mid_pct=round(pct[1, j], 1), share_high_pct=round(pct[2, j], 1),
                baseline_low_pct=round(arr[:, 0].min(), 1), baseline_mid_pct=round(float(np.median(arr[:, 1])), 1),
                baseline_high_pct=round(arr[:, 2].max(), 1), baseline_studies=" | ".join(base[s]["ids"]),
                evidence_score=round(scores[s], 2), grade=g,
                modules_supporting=",".join(sup), modules_contradicting=",".join(con),
                evidence_for=" | ".join(fors), evidence_against=" | ".join(againsts),
                limitations=LIMITS[s] + " " + COMMON_LIMIT, notes=" | ".join(notes)))
        for ks in (0.5, 1.0, 2.0):                       # sensitivity to the adjustment weights
            med = np.median(simulate(base, scores, ks, np.random.default_rng(RNG_SEED)), axis=0) * 100
            sens.append(dict(episode_id=ep["episode_id"], k_scale=ks, **{s: round(med[j], 1) for j, s in enumerate(SOURCES)}))
    if not rows:
        sys.exit("No episodes left after exclusions.")
    led = tag_synthetic(pd.DataFrame(rows))
    led.to_csv(PROCESSED / "ledger_entries.csv", index=False)
    tag_synthetic(pd.DataFrame(sens)).to_csv(PROCESSED / "ledger_sensitivity.csv", index=False)
    show = led[["episode_id", "source", "share_low_pct", "share_mid_pct", "share_high_pct", "baseline_mid_pct", "grade"]]
    print(show.to_string(index=False))
    print(f"\nledger_entries.csv: {len(led)} rows ({episodes.shape[0]} episodes x {len(SOURCES)} sources) -> {PROCESSED}")


if __name__ == "__main__":
    main()
