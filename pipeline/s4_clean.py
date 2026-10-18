"""Step 4 - quality control and a regular hourly grid per station.

Reads  data/raw/aq_long.csv + data/reference/stations.csv
Writes data/interim/station_hourly_clean.csv (wide: one row per station-hour) and
       data/processed/station_qc_report.csv (what was removed and which stations were dropped).
Rules (thresholds in config.py): unit conversion, physical bounds, flat-lined sensors,
isolated single-hour spikes, PM2.5 > PM10 inconsistency flag, minimum station completeness.
"""
import numpy as np
import pandas as pd

from config import RAW, REF, INTERIM, PROCESSED, POLLUTANTS, QC_BOUNDS, FLATLINE_HOURS, \
    SPIKE_FACTOR, SPIKE_MIN_VALUE, MIN_STATION_COMPLETENESS
from common import period_hours

# multipliers to canonical units: ug/m3 (CO: mg/m3). Gas ppb/ppm conversions assume 25 C, 1 atm.
PPB_TO_UG = {"no2": 1.882, "so2": 2.62, "o3": 1.96}
CO_PPM_TO_MG = 1.145


def norm_unit(u):
    u = str(u).lower().replace("µ", "u").replace("μ", "u").replace("³", "3").replace(" ", "")
    return u


def factor(par, unit):
    u = norm_unit(unit)
    if u in ("ug/m3", "ugm-3"):
        return 0.001 if par == "co" else 1.0
    if u in ("mg/m3",):
        return 1.0 if par == "co" else 1000.0
    if u == "ppb":
        return CO_PPM_TO_MG / 1000 if par == "co" else PPB_TO_UG.get(par)
    if u == "ppm":
        return CO_PPM_TO_MG if par == "co" else (PPB_TO_UG.get(par) * 1000 if par in PPB_TO_UG else None)
    return None


def run_lengths_flag(s: pd.Series, min_len: int) -> pd.Series:
    """True where a value repeats unchanged for >= min_len consecutive hours."""
    change = (s != s.shift()).cumsum()
    size = s.groupby(change).transform("size")
    return s.notna() & (size >= min_len)


def qc_one_station(d: pd.DataFrame):
    d = d.sort_values("time").copy()
    stats = {}
    for p in POLLUTANTS:
        s = d[p]
        stats[f"{p}_raw_n"] = int(s.notna().sum())
        lo, hi = QC_BOUNDS[p]
        bad = s.notna() & ((s < lo) | (s > hi))
        stats[f"{p}_bounds"] = int(bad.sum())
        s = s.mask(bad)
        flat = run_lengths_flag(s, FLATLINE_HOURS[p])
        stats[f"{p}_flatline"] = int(flat.sum())
        s = s.mask(flat)
        if p in ("pm25", "pm10"):
            nb = pd.concat([s.shift(1), s.shift(-1)], axis=1).max(axis=1)
            has_nb = s.shift(1).notna() & s.shift(-1).notna()
            spike = has_nb & (s > SPIKE_FACTOR * nb) & (s > SPIKE_MIN_VALUE)
            stats[f"{p}_spike"] = int(spike.sum())
            s = s.mask(spike)
        d[p] = s
    d["qc_pm_inconsistent"] = (d["pm25"] > 1.2 * d["pm10"] + 10).astype(int)
    stats["pm_inconsistent"] = int(d["qc_pm_inconsistent"].sum())
    stats["completeness_pm25"] = float(d["pm25"].notna().mean())
    return d, stats


def main():
    aq = pd.read_csv(RAW / "aq_long.csv", parse_dates=["time"])
    stations = pd.read_csv(REF / "stations.csv")
    aq = aq[aq.parameter.isin(POLLUTANTS) & aq.station_id.isin(stations.station_id)].copy()

    # unit conversion
    fac = [factor(p, u) for p, u in zip(aq.parameter, aq.unit)]
    aq["factor"] = fac
    n_unknown = aq["factor"].isna().sum()
    if n_unknown:
        print(f"warning: dropping {n_unknown:,} rows with unknown unit: {aq.loc[aq.factor.isna(), 'unit'].unique()[:5]}")
    aq = aq.dropna(subset=["factor"])
    aq["value"] = aq["value"] * aq["factor"]
    aq["time"] = aq["time"].dt.floor("h")

    wide = aq.pivot_table(index=["station_id", "time"], columns="parameter", values="value", aggfunc="mean").reset_index()
    for p in POLLUTANTS:
        if p not in wide:
            wide[p] = np.nan

    # regular hourly grid per station over the study periods
    grid = period_hours()
    frames, report = [], []
    for sid in stations.station_id:
        d = wide[wide.station_id == sid]
        g = grid.merge(d.drop(columns="station_id"), on="time", how="left")
        g.insert(0, "station_id", sid)
        g, stats = qc_one_station(g)
        stats["station_id"] = sid
        stats["kept"] = int(stats["completeness_pm25"] >= MIN_STATION_COMPLETENESS)
        report.append(stats)
        if stats["kept"]:
            frames.append(g)
    rep = pd.DataFrame(report).merge(stations[["station_id", "name", "region"]], on="station_id", how="left")
    rep.to_csv(PROCESSED / "station_qc_report.csv", index=False)
    clean = pd.concat(frames, ignore_index=True)
    clean.to_csv(INTERIM / "station_hourly_clean.csv", index=False)
    print(f"clean: kept {int(rep.kept.sum())}/{len(rep)} stations; dropped for low completeness: "
          f"{rep.loc[rep.kept == 0, 'station_id'].tolist()}")
    print(f"       PM2.5 completeness among kept stations: {clean.pm25.notna().mean():.1%}")


if __name__ == "__main__":
    main()
