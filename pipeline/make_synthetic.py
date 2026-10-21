"""Generate SYNTHETIC raw inputs in exactly the formats the real pipeline produces.

!! Everything here is invented. Use ONLY to test the code and to build the dashboard UI before real data arrives.
!! Never report numbers from this data as findings. Outputs carry synthetic=1 and go to data_synthetic/.

Run:  BL_DATA_DIR=data_synthetic BL_SYNTHETIC=1 BL_PERIODS="2022-10-01:2022-12-10,2023-10-01:2023-12-10" python make_synthetic.py
"""
import numpy as np
import pandas as pd

from pipeline.config import *  # noqa: F401,F403
from pipeline.common import padded_periods, period_hours

rng = np.random.default_rng(7)


def ar1(n, phi, rng):
    x = np.zeros(n)
    e = rng.normal(0, np.sqrt(1 - phi ** 2), n)
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
    return x


def gauss(h, mu, sd):
    return np.exp(-0.5 * ((h - mu) / sd) ** 2)


def make_weather():
    g = WEATHER_GRID
    lats = np.arange(g["lat_min"], g["lat_max"] + 1e-9, g["step"])
    lons = np.arange(g["lon_min"], g["lon_max"] + 1e-9, g["step"])
    grid_frames, delhi_frames, base_by_period = [], [], {}
    for (start, end) in padded_periods():
        t = pd.date_range(start, pd.Timestamp(end) + pd.Timedelta(hours=23), freq="h")
        n = len(t)
        hr = t.hour.values
        doy = (t - pd.Timestamp(t[0].year, 10, 1)).days.values
        dir0 = 300 + 55 * ar1(n, 0.985, rng)
        spd = np.clip(2.6 + 1.1 * ar1(n, 0.985, rng) + 0.8 * np.sin(2 * np.pi * (hr - 9) / 24), 0.4, None)
        temp = 27 - 0.2 * doy + 6 * np.cos(2 * np.pi * (hr - 15) / 24) + rng.normal(0, 0.6, n)
        rh = np.clip(88 - 2.2 * (temp - 10) + rng.normal(0, 4, n), 15, 100)
        rain = np.zeros(n)
        for s in rng.choice(max(0, n - 4), size=max(0, min(2, n // 400)), replace=False):
            rain[s:s + 3] = rng.uniform(0.5, 4, 3)
        pres = 1002.0 + (0.05 * doy + 2.5 * ar1(n, 0.99, rng)) # type: ignore
        cloud = np.clip(25 + 25 * ar1(n, 0.95, rng), 0, 100)
        blh = np.clip((120 + 1200 * np.clip(np.sin(np.pi * (hr - 7) / 10), 0, None)) *
                      (1.0 - 0.003 * doy) * (0.75 + 0.12 * spd) + rng.normal(0, 40, n), 60, 2500)
        base_by_period[start] = dict(t=t, dir0=dir0, spd=spd)

        def frame(lat, lon, dir_off=0.0, spd_mul=1.0):
            d = (dir0 + dir_off) % 360
            s = spd * spd_mul
            return pd.DataFrame({
                "time": t, "temperature_2m": temp, "relative_humidity_2m": rh, "precipitation": rain,
                "surface_pressure": pres, "cloud_cover": cloud,
                "wind_speed_10m": s, "wind_direction_10m": d,
                "wind_speed_100m": s * 1.5, "wind_direction_100m": (d + 8) % 360,
                "boundary_layer_height": blh, "lat": lat, "lon": lon})
        for la in lats:
            for lo in lons:
                grid_frames.append(frame(la, lo, 12 * np.sin(0.5 * la + 0.3 * lo), 1 + 0.12 * np.sin(0.4 * la - 0.2 * lo)))
        delhi_frames.append(frame(DELHI_LAT, DELHI_LON, 12 * np.sin(0.5 * DELHI_LAT + 0.3 * DELHI_LON),
                                  1 + 0.12 * np.sin(0.4 * DELHI_LAT - 0.2 * DELHI_LON)))
    pd.concat(grid_frames, ignore_index=True).to_csv(RAW / "weather_grid_hourly.csv", index=False)
    pd.concat(delhi_frames, ignore_index=True).to_csv(RAW / "weather_delhi_hourly.csv", index=False)
    return base_by_period


def make_fires():
    rows = []
    centres = [(30.9, 75.5), (30.2, 76.0), (29.6, 76.3), (31.2, 74.8), (29.1, 75.4)]
    for (start, end) in padded_periods():
        days = pd.date_range(start, end, freq="D")
        scale = rng.uniform(0.7, 1.3)
        for d in days:
            doy = (d - pd.Timestamp(d.year, 11, 7)).days
            nd = int(scale * 1100 * np.exp(-(doy / 9.0) ** 2) + 15)
            for _ in range(1):
                c = rng.integers(0, len(centres), nd)
                lat = np.array([centres[i][0] for i in c]) + rng.normal(0, 0.45, nd)
                lon = np.array([centres[i][1] for i in c]) + rng.normal(0, 0.45, nd)
                afternoon = rng.random(nd) < 0.85
                local_min = np.where(afternoon, 13 * 60 + 30 + rng.normal(0, 40, nd), 90 + rng.normal(0, 30, nd))
                ts = d + pd.to_timedelta(local_min, unit="m") - pd.Timedelta(hours=5, minutes=30) # type: ignore
                ts_idx = pd.DatetimeIndex(ts)
                rows.append(pd.DataFrame({
                    "latitude": lat, "longitude": lon, "bright_ti4": rng.uniform(320, 367, nd), "scan": 0.4,
                    "track": 0.4, "acq_date": ts_idx.strftime("%Y-%m-%d"), "acq_time": ts_idx.strftime("%H%M").astype(int),
                    "satellite": "N", "instrument": "VIIRS", "confidence": rng.choice(["n", "h", "l"], nd, p=[.6, .3, .1]),
                    "version": "2.0NRT", "bright_ti5": rng.uniform(290, 305, nd),
                    "frp": np.round(rng.lognormal(1.5, 0.8, nd), 2),
                    "daynight": np.where(afternoon, "D", "N"), "source": "VIIRS_SNPP_SP"}))
    df = pd.concat(rows, ignore_index=True)
    df = df[(df.latitude.between(FIRE_BBOX[1], FIRE_BBOX[3])) & (df.longitude.between(FIRE_BBOX[0], FIRE_BBOX[2]))]
    df.to_csv(RAW / "firms_viirs.csv", index=False)
    return df


def make_air(base_by_period, fires):
    hrs = period_hours()
    # ----- stations
    st = []
    for i in range(38):
        st.append((f"SYN{i + 1:02d}", f"SYNTHETIC Delhi {i + 1:02d}", rng.uniform(28.45, 28.85), rng.uniform(76.95, 77.30), "Delhi"))
    boxes = [(28.50, 28.65, 77.30, 77.45), (28.40, 28.50, 76.95, 77.10), (28.65, 28.75, 77.40, 77.50), (28.35, 28.45, 77.25, 77.35)]
    for i in range(12):
        b = boxes[i % 4]
        st.append((f"SYN{39 + i:02d}", f"SYNTHETIC NCR {i + 1:02d}", rng.uniform(b[0], b[1]), rng.uniform(b[2], b[3]), "NCR"))
    stations = pd.DataFrame(st, columns=["station_id", "name", "lat", "lon", "region"])
    stations["needs_review"] = 0
    stations["openaq_location_id"] = np.nan
    stations["provider"] = "synthetic"
    stations.to_csv(REF / "stations.csv", index=False)

    # ----- shared drivers on the study hours
    rows = []
    fires["ts"] = pd.to_datetime(fires["acq_date"]) + pd.to_timedelta(fires["acq_time"] // 100, unit="h") + \
        pd.to_timedelta(fires["acq_time"] % 100, unit="m") + pd.Timedelta(hours=5, minutes=30)
    fires_daily = fires[fires.confidence != "l"].groupby(fires["ts"].dt.normalize()).size()
    for pid, ((a, b), (pa, pb)) in enumerate(zip(PERIODS, padded_periods())):
        base = base_by_period[pa]
        t_all = base["t"]
        idx = (t_all >= pd.Timestamp(a)) & (t_all <= pd.Timestamp(b) + pd.Timedelta(hours=23))
        t = t_all[idx]
        n = len(t)
        hr = t.hour.values
        nw = pd.Series(((base["dir0"] % 360 > 270) & (base["dir0"] % 360 < 350)).astype(float), index=t_all).rolling(24, min_periods=1).mean()[idx].values
        spd = base["spd"][idx]
        blh = 120 + 1200 * np.clip(np.sin(np.pi * (hr - 7) / 10), 0, None)
        fcount = fires_daily.reindex(t.normalize() - pd.Timedelta(days=1)).fillna(0).values
        stag = np.clip(1.4 - 0.18 * spd + (1000 - blh) / 1500, 0.5, 3.0)
        reg = (35 + 0.11 * fcount * (0.4 + 0.6 * nw)) * stag
        prof = 0.3 + 1.0 * gauss(hr, 9, 1.3) + 1.2 * gauss(hr, 19, 1.8)
        dust = np.clip(ar1(n, 0.99, rng) + 0.3, 0, None) * 0.5
        # scale events
        delhi_mult = np.ones(n)
        ncr_mult = np.ones(n)
        for s in rng.choice(max(0, n - 24), size=min(3, max(0, n - 24)), replace=False):
            delhi_mult[s:s + 18] = 2.4
        s_ncr = rng.integers(0, max(1, n - 24))
        ncr_mult[s_ncr:s_ncr + 18] = 2.2
        so2_burst = np.zeros(n)
        for s in rng.choice(max(0, n - 10), size=min(6, max(0, n - 10)), replace=False):
            so2_burst[s:s + 6] = rng.uniform(15, 40)
        for _, srow in stations.iterrows():
            is_delhi = srow.region == "Delhi"
            LT = rng.lognormal(0, 0.4)
            LD = rng.lognormal(0, 0.35)
            RM = rng.normal(1, 0.07)
            industrial = srow.station_id in ("SYN05", "SYN12", "SYN41")
            mult = delhi_mult if is_delhi else ncr_mult
            regm = reg * (1 + 0.3 * (mult - 1))
            local = (LT * 30 * prof * stag * 0.7 + LD * 25 * dust) * mult
            pm25 = np.maximum(3, (regm * RM + local) * rng.lognormal(0, 0.08, n))
            pm10 = pm25 * (1.5 + 0.4 * LD + 0.8 * dust) + rng.normal(0, 8, n)
            pm10 = np.maximum(pm10, pm25 * 1.05)
            no2 = np.maximum(2, 20 + 35 * LT * prof * stag * 0.6 + rng.normal(0, 6, n))
            co = np.maximum(0.1, 0.6 + 1.1 * LT * prof * stag * 0.7 + 0.004 * regm + rng.normal(0, 0.15, n))
            so2 = np.maximum(1, 6 + (so2_burst * (1 if industrial else 0)) + rng.normal(0, 2, n))
            o3 = np.maximum(1, 10 + 60 * np.clip(np.sin(np.pi * (hr - 8) / 10), 0, None) * (1 - 0.4 * stag / 3) + rng.normal(0, 5, n))
            data = {"pm25": pm25, "pm10": pm10, "no2": no2, "so2": so2, "co": co, "o3": o3}
            miss = rng.random(n) < 0.02
            for _ in range(3):
                s = rng.integers(0, n - 60)
                miss[s:s + rng.integers(6, 60)] = True
            if srow.station_id == "SYN30":                       # a mostly-dead station: should be dropped by QC
                miss |= rng.random(n) < 0.75
            if srow.station_id == "SYN07":                       # a flat-lined PM2.5 sensor block
                s = rng.integers(50, n - 60)
                pm25[s:s + 20] = pm25[s]
            for s in rng.choice(max(0, n - 2), size=min(3, max(0, n - 2)), replace=False):   # isolated spikes
                if rng.random() < 0.7:
                    pm25[s] = max(300, pm25[max(s - 1, 0)] * 6)
            for par, v in data.items():
                unit = "mg/m3" if par == "co" else "ug/m3"
                vv = v.copy()
                if srow.station_id == "SYN45" and par == "no2":  # unit-conversion test: this station reports ppb
                    vv, unit = vv / 1.882, "ppb"
                keep = ~miss
                rows.append(pd.DataFrame({"station_id": srow.station_id, "time": t[keep], "parameter": par,
                                          "value": np.round(vv[keep], 3), "unit": unit, "source": "SYNTHETIC"}))
    out = pd.concat(rows, ignore_index=True)
    out.to_csv(RAW / "aq_long.csv", index=False)
    return out


if __name__ == "__main__":
    assert SYNTHETIC, "Set BL_SYNTHETIC=1 (and BL_DATA_DIR=data_synthetic) so synthetic data cannot be mistaken for real data."
    base = make_weather()
    fires = make_fires()
    aq = make_air(base, fires)
    print(f"synthetic data written to {DATA}: {len(fires):,} fires, {len(aq):,} AQ rows")
