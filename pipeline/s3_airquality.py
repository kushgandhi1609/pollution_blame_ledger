"""Step 3 - hourly air-quality observations into one long table.

Sources (use either or both):
  --openaq   OpenAQ v3 hourly aggregates for every sensor in data/reference/sensors.csv
             (needs OPENAQ_API_KEY; rate limited, so it is slow and resumable).
  --cpcb DIR folder of CPCB CAAQMS exports (.csv/.xlsx), ONE FILE PER STATION, file name stem = station_id
             in stations.csv. Column names are detected by pattern; check the printed mapping.
Output: data/raw/aq_long.csv with columns station_id, time (IST, hour-beginning), parameter, value, unit, source
Usage: python s3_airquality.py --openaq  |  --cpcb path/to/folder  |  --skip-fetch
"""
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

from config import RAW, REF, PERIODS, POLLUTANTS, INTERIM

BASE = "https://api.openaq.org/v3"


def _get(path, params):
    key = os.environ.get("OPENAQ_API_KEY")
    if not key:
        sys.exit("Set OPENAQ_API_KEY first.")
    for attempt in range(8):
        r = requests.get(BASE + path, params=params, headers={"X-API-Key": key}, timeout=90)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            time.sleep(60)
            continue
        if r.status_code in (404, 410):
            return {"results": []}
        time.sleep(5 * (attempt + 1))
    raise RuntimeError("OpenAQ failed: " + path)


def fetch_openaq():
    sensors = pd.read_csv(REF / "sensors.csv")
    cache = INTERIM / "openaq_cache"
    cache.mkdir(exist_ok=True)
    frames = []
    for _, s in sensors.iterrows():
        for (a, b) in PERIODS:
            f = cache / f"{s.sensor_id}_{a}_{b}.csv"
            if f.exists():
                frames.append(pd.read_csv(f))
                continue
            rows, page = [], 1
            while True:
                js = _get(f"/sensors/{int(s.sensor_id)}/hours", {
                    "datetime_from": f"{a}T00:00:00+05:30", "datetime_to": f"{b}T23:59:59+05:30",
                    "limit": 1000, "page": page})
                res = js.get("results", [])
                for it in res:
                    t = it["period"]["datetimeFrom"]["local"]
                    rows.append({"station_id": s.station_id, "time": t, "parameter": s.parameter,
                                 "value": it["value"], "unit": it["parameter"].get("units", s.units),
                                 "source": "openaq"})
                if len(res) < 1000:
                    break
                page += 1
                time.sleep(1.1)
            df = pd.DataFrame(rows, columns=["station_id", "time", "parameter", "value", "unit", "source"])
            df.to_csv(f, index=False)
            frames.append(df)
            time.sleep(1.1)
        print(f"  openaq sensor {int(s.sensor_id)} ({s.station_id}, {s.parameter}) done")
    out = pd.concat(frames, ignore_index=True)
    return out


PATTERNS = {"pm25": r"pm\s*2\.?5", "pm10": r"pm\s*10", "no2": r"\bno2\b", "so2": r"\bso2\b",
            "co": r"^co\b|\bco\s*\(", "o3": r"ozone|\bo3\b"}
TIME_PATTERNS = ["from date", "datetime", "timestamp", "date", "time"]


def load_cpcb(folder):
    rows = []
    for f in sorted(Path(folder).glob("*")):
        if f.suffix.lower() not in (".csv", ".xlsx", ".xls"):
            continue
        df = pd.read_csv(f) if f.suffix.lower() == ".csv" else pd.read_excel(f)
        low = {c: str(c).strip().lower() for c in df.columns}
        tcol = next((c for p in TIME_PATTERNS for c, l in low.items() if l.startswith(p)), None)
        if tcol is None:
            print("  skipped (no time column found):", f.name)
            continue
        mapping = {}
        for par, pat in PATTERNS.items():
            col = next((c for c, l in low.items() if re.search(pat, l)), None)
            if col is not None:
                mapping[par] = col
        print(f"  {f.name}: time={tcol!r} mapping={mapping}")
        t = pd.to_datetime(df[tcol], dayfirst=True, errors="coerce")
        for par, col in mapping.items():
            unit_hint = str(col).lower()
            unit = "mg/m3" if (par == "co") else ("ppb" if "ppb" in unit_hint else "ug/m3")
            tmp = pd.DataFrame({"station_id": f.stem, "time": t,
                                "parameter": par, "value": pd.to_numeric(df[col], errors="coerce"),
                                "unit": unit, "source": "cpcb"})
            rows.append(tmp.dropna(subset=["time", "value"]))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def main():
    if "--skip-fetch" in sys.argv:
        print("aq: using existing", RAW / "aq_long.csv")
        return
    parts = []
    if "--openaq" in sys.argv:
        parts.append(fetch_openaq())
    if "--cpcb" in sys.argv:
        parts.append(load_cpcb(sys.argv[sys.argv.index("--cpcb") + 1]))
    if not parts:
        sys.exit("Choose --openaq and/or --cpcb DIR (or --skip-fetch).")
    out = pd.concat(parts, ignore_index=True)
    # normalise timestamps to naive IST
    t = pd.to_datetime(out["time"], utc=False, errors="coerce", format="mixed")
    if getattr(t.dt, "tz", None) is not None:
        t = t.dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    out["time"] = t
    out = out.dropna(subset=["time", "value"])
    out.to_csv(RAW / "aq_long.csv", index=False)
    print(f"aq: {len(out):,} rows -> {RAW / 'aq_long.csv'}")


if __name__ == "__main__":
    main()
