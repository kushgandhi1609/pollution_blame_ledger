"""In-memory data loaders and query helpers for processed artifacts."""

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from backend.config import PROCESSED_DIR, REFERENCE_DIR
except ImportError:
    from config import PROCESSED_DIR, REFERENCE_DIR  # type: ignore


def _sanitize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Replaces NaN, inf, -inf with None for valid JSON serialization."""
    sanitized = []
    for r in records:
        clean_row = {}
        for k, v in r.items():
            if (isinstance(v, float) and (np.isnan(v) or np.isinf(v))) or pd.isna(v):
                clean_row[k] = None
            else:
                clean_row[k] = v
        sanitized.append(clean_row)
    return sanitized


def df_to_records(df: Any) -> list[dict[str, Any]]:
    """Converts any DataFrame or slice cleanly into sanitized JSON-serializable records."""
    if df is None:
        return []
    as_df = df if isinstance(df, pd.DataFrame) else pd.DataFrame(df)
    return _sanitize_records(as_df.to_dict(orient="records"))


def _safe_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        if bool(pd.isna(val)):
            return None
        f = float(str(val))
        return None if (np.isnan(f) or np.isinf(f)) else f
    except (ValueError, TypeError, AttributeError):
        return None


def _safe_str(val: Any, default: str = "") -> str:
    if val is None:
        return default
    try:
        if bool(pd.isna(val)):
            return default
        return str(val)
    except (ValueError, TypeError, AttributeError):
        return default


def _safe_bool(val: Any) -> bool:
    if val is None:
        return False
    try:
        if bool(pd.isna(val)):
            return False
        return bool(val)
    except (ValueError, TypeError, AttributeError):
        return False


class DataLoader:
    """Thread-safe data cache and query provider."""

    def __init__(self):
        self._cache: dict[str, Any] = {}
        print(f"[DataLoader] Loading artifacts from: {PROCESSED_DIR}")

    def get_city_daily(self) -> pd.DataFrame:
        if "city_daily" not in self._cache:
            p = PROCESSED_DIR / "city_daily_final.csv"
            df = pd.read_csv(p) if p.exists() else pd.DataFrame()
            self._cache["city_daily"] = df
        return self._cache["city_daily"]

    def get_city_hourly(self) -> pd.DataFrame:
        if "city_hourly" not in self._cache:
            p = PROCESSED_DIR / "city_hourly_final.csv"
            df = pd.read_csv(p) if p.exists() else pd.DataFrame()
            self._cache["city_hourly"] = df
        return self._cache["city_hourly"]

    def get_ledger_entries(self) -> pd.DataFrame:
        if "ledger_entries" not in self._cache:
            p = PROCESSED_DIR / "ledger_entries.csv"
            df = pd.read_csv(p) if p.exists() else pd.DataFrame()
            self._cache["ledger_entries"] = df
        return self._cache["ledger_entries"]

    def get_ledger_labels(self) -> pd.DataFrame:
        if "ledger_labels" not in self._cache:
            p = PROCESSED_DIR / "ledger_labels.csv"
            df = pd.read_csv(p) if p.exists() else pd.DataFrame()
            self._cache["ledger_labels"] = df
        return self._cache["ledger_labels"]

    def get_action_recommendations(self) -> pd.DataFrame:
        if "action_recommendations" not in self._cache:
            p = PROCESSED_DIR / "action_recommendations.csv"
            df = pd.read_csv(p) if p.exists() else pd.DataFrame()
            self._cache["action_recommendations"] = df
        return self._cache["action_recommendations"]

    def get_stations(self) -> pd.DataFrame:
        if "stations" not in self._cache:
            p = REFERENCE_DIR / "stations.csv"
            df = pd.read_csv(p) if p.exists() else pd.DataFrame()
            self._cache["stations"] = df
        return self._cache["stations"]

    def get_sensor_health(self) -> pd.DataFrame:
        if "sensor_health" not in self._cache:
            p = PROCESSED_DIR / "sensor_health.csv"
            df = pd.read_csv(p) if p.exists() else pd.DataFrame()
            self._cache["sensor_health"] = df
        return self._cache["sensor_health"]

    def get_sensor_validation_report(self) -> dict[str, Any]:
        if "sensor_val" not in self._cache:
            p = PROCESSED_DIR / "sensor_validation_report.json"
            if p.exists():
                self._cache["sensor_val"] = json.loads(p.read_text())
            else:
                self._cache["sensor_val"] = {}
        return self._cache["sensor_val"]

    def get_forecast_hourly(self) -> pd.DataFrame:
        if "forecast_hourly" not in self._cache:
            p = PROCESSED_DIR / "forecast_hourly.csv"
            df = pd.read_csv(p) if p.exists() else pd.DataFrame()
            # Merge with city_hourly_final to get actual observed values (delhi_pm25_median)
            if not df.empty:
                hourly = self.get_city_hourly()
                if not hourly.empty:
                    # Merge on target_time
                    df = df.merge(
                        hourly[['time', 'delhi_pm25_median']],
                        left_on='target_time',
                        right_on='time',
                        how='left'
                    ).drop(columns=['time'])
            self._cache["forecast_hourly"] = df
        return self._cache["forecast_hourly"]

    def get_forecast_eval(self) -> pd.DataFrame:
        if "forecast_eval" not in self._cache:
            p = PROCESSED_DIR / "forecast_eval.csv"
            df = pd.read_csv(p) if p.exists() else pd.DataFrame()
            self._cache["forecast_eval"] = df
        return self._cache["forecast_eval"]

    def get_advice(self) -> pd.DataFrame:
        if "advice" not in self._cache:
            p = PROCESSED_DIR / "advice_daily.csv"
            df = pd.read_csv(p) if p.exists() else pd.DataFrame()
            self._cache["advice"] = df
        return self._cache["advice"]

    def get_dust_demo(self) -> pd.DataFrame:
        if "dust_demo" not in self._cache:
            p = PROCESSED_DIR / "dust_demo_schedule.csv"
            df = pd.read_csv(p) if p.exists() else pd.DataFrame()
            self._cache["dust_demo"] = df
        return self._cache["dust_demo"]

    def get_backtest_summary(self) -> dict[str, Any]:
        if "backtest_summary" not in self._cache:
            p = PROCESSED_DIR / "backtest_summary.json"
            if p.exists():
                self._cache["backtest_summary"] = json.loads(p.read_text())
            else:
                self._cache["backtest_summary"] = {}
        return self._cache["backtest_summary"]

    def get_backtest_results(self) -> pd.DataFrame:
        if "backtest_results" not in self._cache:
            p = PROCESSED_DIR / "backtest_results.csv"
            df = pd.read_csv(p) if p.exists() else pd.DataFrame()
            self._cache["backtest_results"] = df
        return self._cache["backtest_results"]

    def get_health_summary(self) -> dict[str, Any]:
        if "health_summary" not in self._cache:
            p = PROCESSED_DIR / "health_summary.json"
            if p.exists():
                self._cache["health_summary"] = json.loads(p.read_text())
            else:
                self._cache["health_summary"] = {}
        return self._cache["health_summary"]


# Global singleton
loader = DataLoader()


# -----------------------------------------------------------------------------
# High-Level Service Methods
# -----------------------------------------------------------------------------

def get_episodes_list() -> list[dict[str, Any]]:
    """Returns aggregated metadata for all 6 detected pollution episodes."""
    daily = loader.get_city_daily()
    entries = loader.get_ledger_entries()

    if daily.empty or "episode_id" not in daily.columns:
        return []

    ep_days = daily[daily["episode_id"] > 0]
    episodes = []

    for ep_id, g in ep_days.groupby("episode_id"):
        start_date = str(g["date"].min())
        end_date = str(g["date"].max())
        duration_days = len(g)
        peak_pm25 = float(str(g["delhi_pm25_daily_mean"].max()))
        mean_pm25 = float(str(g["delhi_pm25_daily_mean"].mean()))
        season = str(start_date[:4])
        diwali = int(str(g["diwali_window"].max())) if "diwali_window" in g.columns else 0

        # Find dominant source from ledger entries (replacing labels check)
        ep_entries = entries[entries["episode_id"] == ep_id]
        dominant_source = "unknown"
        dominant_share = 0.0
        dominant_label = "Insufficient evidence"

        if not ep_entries.empty:
            top_row = ep_entries.sort_values(by="share_mid_pct", ascending=False).iloc[0]
            dominant_source = str(top_row["source"])
            dominant_share = float(str(top_row["share_mid_pct"]))

            # Fixed logic: the "Other" category in ledger_entries.csv usually has the
            # highest midpoint share but the lowest evidence grade (Grade C).
            # We should look for the source with the best balance of share and evidence.

            # First, try to find the highest-share source that is actually 'Supported' (Grade A or B)
            supported_sources = ep_entries[ep_entries["grade"].isin(["A", "B"])]
            if not supported_sources.empty:
                best_supported = supported_sources.sort_values(by="share_mid_pct", ascending=False).iloc[0]
                dominant_source = str(best_supported["source"])
                dominant_share = float(str(best_supported["share_mid_pct"]))
                grade = str(best_supported["grade"])
            else:
                # Fallback to the absolute dominant source if nothing is supported
                best_overall = ep_entries.sort_values(by="share_mid_pct", ascending=False).iloc[0]
                dominant_source = str(best_overall["source"])
                dominant_share = float(str(best_overall["share_mid_pct"]))
                grade = str(best_overall["grade"])

            if grade == "A":
                dominant_label = "Strongly Supported"
            elif grade == "B":
                dominant_label = "Supported"
            else:
                dominant_label = "Insufficient evidence"

        title = f"Episode {ep_id}: {season} Severe Smog Window"
        if diwali:
            title = f"Episode {ep_id}: {season} Post-Diwali Smog Episode"

        episodes.append({
            "episode_id": int(str(ep_id)),
            "title": title,
            "start": start_date,
            "end": end_date,
            "duration_days": duration_days,
            "season": season,
            "is_diwali_window": bool(diwali),
            "peak_pm25": round(peak_pm25, 1),
            "mean_pm25": round(mean_pm25, 1),
            "dominant_source": dominant_source,
            "dominant_share_pct": round(dominant_share, 1),
            "dominant_label": dominant_label,
            "status": "Archived Review",
        })

    return sorted(episodes, key=lambda x: x["episode_id"])


def get_episode_detail(episode_id: int) -> dict[str, Any] | None:
    """Returns complete breakdown of an episode including attribution, labels, and actions."""
    ep_list = get_episodes_list()
    match = [e for e in ep_list if e["episode_id"] == episode_id]
    if not match:
        return None
    summary = match[0]

    # Ledger entries
    ledger_df = loader.get_ledger_entries()
    entries = []
    if not ledger_df.empty:
        entries = df_to_records(ledger_df[ledger_df["episode_id"] == episode_id])

    # Evidence labels - we now use the same data as entries since labels are embedded
    labels = []
    if not ledger_df.empty:
        ep_entries = ledger_df[ledger_df["episode_id"] == episode_id]
        labels = df_to_records(ep_entries[['episode_id', 'source', 'share_mid_pct', 'evidence_for']].rename(columns={'evidence_for': 'label'}))

    # Actions
    actions_df = loader.get_action_recommendations()
    actions = []
    if not actions_df.empty:
        actions = df_to_records(actions_df[actions_df["episode_id"] == episode_id])

    # Hourly timeseries for window
    hourly_df = loader.get_city_hourly()
    timeseries = []
    if not hourly_df.empty:
        start_ts = f"{summary['start']} 00:00:00"
        end_ts = f"{summary['end']} 23:59:59"
        sub = hourly_df[(hourly_df["time"] >= start_ts) & (hourly_df["time"] <= end_ts)]
        cols = [
            "time", "delhi_pm25_median", "ncr_pm25_median",
            "wind_speed_ms", "stagnation_flag", "regime",
            "fires_linked_median", "raw_fires_24h_pbhr"
        ]
        available_cols = [c for c in cols if c in sub.columns]
        timeseries = df_to_records(sub[available_cols])

    return {
        "summary": summary,
        "attribution": entries,
        "evidence_labels": labels,
        "actions": actions,
        "timeseries": timeseries,
    }


def get_stations_with_health() -> list[dict[str, Any]]:
    """Merges station master coordinates with latest sensor health diagnostics."""
    st_df = loader.get_stations()
    sh_df = loader.get_sensor_health()

    if st_df.empty:
        return []

    # Map sensor health by station_id
    health_map: dict[str, dict[str, Any]] = {}
    if not sh_df.empty:
        for _, r in sh_df.iterrows():
            sid = _safe_str(r["station_id"])
            st_val = _safe_str(r["status"], "OK")
            health_map[sid] = {
                "status": st_val,
                "observed_pm25": _safe_float(r["observed_pm25"]),
                "expected_pm25": _safe_float(r["expected_pm25"]),
                "expected_spread": _safe_float(r["expected_spread"]),
                "residual_pm25": _safe_float(r["residual_pm25"]),
                "z_score": _safe_float(r["z_score"]),
                "hours_persistent": int(_safe_float(r["hours_persistent"]) or 0),
                "corr24h": _safe_float(r["corr24h"]),
                "reasons": _safe_str(r["reasons"], "Normal tracking"),
                "is_suspect": st_val == "suspect",
            }

    records: list[dict[str, Any]] = []
    for _, r in st_df.iterrows():
        sid = _safe_str(r["station_id"])
        h = health_map.get(sid, {
            "status": "OK",
            "observed_pm25": None,
            "expected_pm25": None,
            "expected_spread": None,
            "residual_pm25": None,
            "z_score": 0.0,
            "hours_persistent": 0,
            "corr24h": 1.0,
            "reasons": "No anomalies reported",
            "is_suspect": False,
        })

        lat = _safe_float(r.get("lat"))
        lon = _safe_float(r.get("lon"))
        lat_val = lat if lat is not None else 0.0
        lon_val = lon if lon is not None else 0.0
        records.append({
            "station_id": sid,
            "name": _safe_str(r["name"]),
            "latitude": lat_val,
            "longitude": lon_val,
            "lat": lat_val,
            "lon": lon_val,
            "district": _safe_str(r.get("region"), "Delhi NCR"),
            "state": _safe_str(r.get("state"), "Delhi"),
            "agency": _safe_str(r.get("provider"), "CPCB/DPCC"),
            "station_type": _safe_str(r.get("station_type"), "ambient"),
            **h,
        })

    return records
