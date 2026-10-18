"""Step 2 - NASA FIRMS VIIRS active-fire detections.

Needs FIRMS_MAP_KEY (free: https://firms.modaps.eosdis.nasa.gov/api/area/). Downloads the area
API in 5-day chunks, then cleans: converts UTC overpass time to IST, drops low-confidence
detections, assigns a fire_id. Manual alternative: request the archive by area/date on the FIRMS
website, save as data/raw/firms_viirs.csv, and run with --skip-fetch.
Outputs: data/raw/firms_viirs.csv (as received), data/interim/fires_clean.csv
"""
import os
import sys
import time

import pandas as pd
import requests

from config import RAW, INTERIM, FIRE_BBOX, FIRMS_SOURCES, FIRMS_CHUNK_DAYS
from common import padded_periods

API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


def fetch():
    key = os.environ.get("FIRMS_MAP_KEY")
    if not key:
        sys.exit("Set FIRMS_MAP_KEY (free) or download manually and use --skip-fetch.")
    cache = INTERIM / "firms_cache"
    cache.mkdir(exist_ok=True)
    w, s, e, n = FIRE_BBOX
    frames = []
    for (start, end) in padded_periods():
        days = pd.date_range(start, end, freq="D")
        for src in FIRMS_SOURCES:
            for i in range(0, len(days), FIRMS_CHUNK_DAYS):
                d0 = days[i]
                nd = min(FIRMS_CHUNK_DAYS, len(days) - i)
                f = cache / f"{src}_{d0:%Y%m%d}_{nd}.csv"
                if not f.exists():
                    url = f"{API}/{key}/{src}/{w},{s},{e},{n}/{nd}/{d0:%Y-%m-%d}"
                    for attempt in range(5):
                        r = requests.get(url, timeout=120)
                        if r.status_code == 200 and "latitude" in r.text[:200]:
                            f.write_text(r.text)
                            break
                        if "Invalid" in r.text[:200]:
                            sys.exit("FIRMS says: " + r.text[:200])
                        time.sleep(10 * (attempt + 1))
                    else:
                        print("  warning: could not fetch", src, d0.date(), r.text[:100])
                        continue
                    time.sleep(0.5)
                frames.append(pd.read_csv(f).assign(source=src))
    if not frames:
        sys.exit("No FIRMS data downloaded.")
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(RAW / "firms_viirs.csv", index=False)
    print(f"FIRMS: {len(df):,} detections downloaded")


def clean():
    df = pd.read_csv(RAW / "firms_viirs.csv")
    if "source" not in df:
        df["source"] = "VIIRS"
    hhmm = df["acq_time"].astype(int).astype(str).str.zfill(4)
    utc = pd.to_datetime(df["acq_date"].astype(str) + " " + hhmm, format="%Y-%m-%d %H%M")
    df["time_ist"] = utc + pd.Timedelta(hours=5, minutes=30)
    conf = df["confidence"].astype(str).str.lower().str[0]
    n0 = len(df)
    df = df[conf != "l"].copy()                      # drop low-confidence VIIRS detections
    df = df.drop_duplicates(subset=["latitude", "longitude", "time_ist", "source"])
    df = df.sort_values("time_ist").reset_index(drop=True)
    df["fire_id"] = df.index
    out = df[["fire_id", "latitude", "longitude", "time_ist", "frp", "confidence", "daynight", "source"]]
    out = out.rename(columns={"latitude": "lat", "longitude": "lon"})
    out.to_csv(INTERIM / "fires_clean.csv", index=False)
    print(f"fires: {n0:,} raw -> {len(out):,} after filtering -> {INTERIM / 'fires_clean.csv'}")


if __name__ == "__main__":
    if "--skip-fetch" not in sys.argv:
        fetch()
    clean()
