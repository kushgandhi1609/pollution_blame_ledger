"""Shared helpers."""
import numpy as np
import pandas as pd

from pipeline.config import PERIODS, LOOKBACK_PAD_DAYS, SYNTHETIC


def period_hours() -> pd.DataFrame:
    """One row per hour of every study period: columns time, period_id."""
    frames = []
    for i, (a, b) in enumerate(PERIODS):
        idx = pd.date_range(a, pd.Timestamp(b) + pd.Timedelta(hours=23), freq="h")
        frames.append(pd.DataFrame({"time": idx, "period_id": i}))
    return pd.concat(frames, ignore_index=True)


def padded_periods():
    """(start, end) strings with look-back padding, for weather and fire downloads."""
    out = []
    for a, b in PERIODS:
        s = (pd.Timestamp(a) - pd.Timedelta(days=LOOKBACK_PAD_DAYS)).strftime("%Y-%m-%d")
        out.append((s, b))
    return out


def wind_to_uv(speed, direction_deg):
    """Meteorological direction (where wind blows FROM) -> u (east), v (north) of the air motion."""
    rad = np.deg2rad(direction_deg)
    return -speed * np.sin(rad), -speed * np.cos(rad)


def bearing_deg(lat1, lon1, lat2, lon2):
    p1, p2 = np.deg2rad(lat1), np.deg2rad(lat2)
    dl = np.deg2rad(lon2 - lon1)
    x = np.sin(dl) * np.cos(p2)
    y = np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl)
    return (np.degrees(np.arctan2(x, y)) + 360) % 360


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = np.deg2rad(lat1), np.deg2rad(lat2)
    dphi = p2 - p1
    dl = np.deg2rad(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def tag_synthetic(df: pd.DataFrame) -> pd.DataFrame:
    if SYNTHETIC:
        df = df.copy()
        df["synthetic"] = 1
    return df
