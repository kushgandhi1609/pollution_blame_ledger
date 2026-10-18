"""Step 1 - hourly weather from Open-Meteo for a grid over north-west India (+ one Delhi point).

Outputs: data/raw/weather_grid_hourly.csv, data/raw/weather_delhi_hourly.csv
Wind is requested in m/s (Open-Meteo defaults to km/h) and times in IST.
boundary_layer_height is requested too; if the endpoint rejects it the script continues without it
(then ventilation features are left empty). Resumable: finished batches are cached.
Usage: python s1_weather.py [--skip-fetch]
"""
import sys
import time

import numpy as np
import pandas as pd
import requests

from config import RAW, INTERIM, TZ, WEATHER_GRID, DELHI_LAT, DELHI_LON
from common import padded_periods

URL = "https://archive-api.open-meteo.com/v1/archive"
CORE = ["temperature_2m", "relative_humidity_2m", "precipitation", "surface_pressure", "cloud_cover",
        "wind_speed_10m", "wind_direction_10m", "wind_speed_100m", "wind_direction_100m"]
OPTIONAL = ["boundary_layer_height"]
BATCH = 10


def _get(params):
    for attempt in range(6):
        try:
            r = requests.get(URL, params=params, timeout=120)
        except requests.RequestException:
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            time.sleep(45 * (attempt + 1))
            continue
        if r.status_code == 400:
            raise ValueError(r.text[:300])
        time.sleep(5 * (attempt + 1))
    raise RuntimeError("Open-Meteo request failed repeatedly")


def fetch_batch(points, start, end):
    lats = ",".join(f"{p[0]:.4f}" for p in points)
    lons = ",".join(f"{p[1]:.4f}" for p in points)
    js = None
    for variables in (CORE + OPTIONAL, CORE):
        params = dict(latitude=lats, longitude=lons, start_date=start, end_date=end,
                      hourly=",".join(variables), timezone=TZ, wind_speed_unit="ms")
        try:
            js = _get(params)
            break
        except ValueError as e:
            if variables == CORE:
                raise
            print("  note: boundary_layer_height not accepted here, continuing without it:", str(e)[:120])
    if isinstance(js, dict):
        js = [js]
    frames = []
    for p, item in zip(points, js):
        h = pd.DataFrame(item["hourly"])
        h["time"] = pd.to_datetime(h["time"])
        h["lat"], h["lon"] = p
        frames.append(h)
    return pd.concat(frames, ignore_index=True)


def main(skip_fetch=False):
    grid_out, delhi_out = RAW / "weather_grid_hourly.csv", RAW / "weather_delhi_hourly.csv"
    if skip_fetch and grid_out.exists() and delhi_out.exists():
        print("weather: using existing files")
        return
    g = WEATHER_GRID
    lats = np.arange(g["lat_min"], g["lat_max"] + 1e-9, g["step"])
    lons = np.arange(g["lon_min"], g["lon_max"] + 1e-9, g["step"])
    points = [(float(a), float(b)) for a in lats for b in lons]
    cache = INTERIM / "weather_cache"
    cache.mkdir(exist_ok=True)
    grid_frames, delhi_frames = [], []
    for (start, end) in padded_periods():
        for i in range(0, len(points), BATCH):
            f = cache / f"grid_{start}_{end}_{i}.csv"
            if f.exists():
                grid_frames.append(pd.read_csv(f, parse_dates=["time"]))
                continue
            df = fetch_batch(points[i:i + BATCH], start, end)
            df.to_csv(f, index=False)
            grid_frames.append(df)
            print(f"  weather {start}..{end} points {i}-{i + BATCH} of {len(points)}")
            time.sleep(1.0)
        f = cache / f"delhi_{start}_{end}.csv"
        if f.exists():
            delhi_frames.append(pd.read_csv(f, parse_dates=["time"]))
        else:
            df = fetch_batch([(DELHI_LAT, DELHI_LON)], start, end)
            df.to_csv(f, index=False)
            delhi_frames.append(df)
    pd.concat(grid_frames, ignore_index=True).to_csv(grid_out, index=False)
    pd.concat(delhi_frames, ignore_index=True).to_csv(delhi_out, index=False)
    print("weather done ->", grid_out)


if __name__ == "__main__":
    main(skip_fetch="--skip-fetch" in sys.argv)
