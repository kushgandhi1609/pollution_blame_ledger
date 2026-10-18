"""Comprehensive test suite for Pollution Blame Ledger FastAPI backend."""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.main import app

client = TestClient(app)


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "documentation" in data


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["cataloged_episodes"] >= 6
    assert data["active_stations"] >= 50


def test_list_episodes():
    res = client.get("/api/episodes")
    assert res.status_code == 200
    episodes = res.json()
    assert len(episodes) >= 6
    for ep in episodes:
        assert "episode_id" in ep
        assert "start" in ep
        assert "end" in ep
        assert "peak_pm25" in ep
        assert ep["peak_pm25"] > 0


def test_get_episode_detail():
    res = client.get("/api/episodes/1")
    assert res.status_code == 200
    data = res.json()
    assert data["summary"]["episode_id"] == 1
    assert len(data["attribution"]) > 0
    assert len(data["evidence_labels"]) > 0
    assert len(data["actions"]) > 0
    assert len(data["timeseries"]) > 0


def test_episode_attribution():
    res = client.get("/api/episodes/1/attribution")
    assert res.status_code == 200
    data = res.json()
    sources = {r["source"] for r in data}
    assert "stubble_burning" in sources or "vehicular" in sources
    for r in data:
        assert "share_mid_pct" in r
        assert "share_low_pct" in r
        assert "share_high_pct" in r


def test_episode_labels():
    res = client.get("/api/episodes/1/labels")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    valid_labels = {"Supported", "Conflicting", "Insufficient evidence"}
    for r in data:
        assert r["label"] in valid_labels
        assert "label_reason" in r


def test_episode_actions():
    res = client.get("/api/episodes/1/actions")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    valid_tiers = {"act", "assess", "inspect", "alert", "collect", "verify"}
    for r in data:
        assert r["tier"] in valid_tiers
        assert "responsible_party" in r
        assert "where_target" in r


def test_stations_list():
    res = client.get("/api/sensors/stations")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 70
    first = data[0]
    assert "station_id" in first
    assert "latitude" in first
    assert "longitude" in first
    assert "status" in first


def test_sensor_health():
    res = client.get("/api/sensors/health")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    statuses = {r["status"] for r in data}
    assert "OK" in statuses or "watch" in statuses or "suspect" in statuses


def test_sensor_validation_report():
    res = client.get("/api/sensors/validation")
    assert res.status_code == 200
    data = res.json()
    assert data["detection_rate_pct"] == 100.0
    assert data["true_positives_detected"] == 5


def test_forecast():
    res = client.get("/api/forecast")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    first = data[0]
    assert "pm25_pred" in first
    assert "pm25_low" in first
    assert "pm25_high" in first
    assert "aqi_category" in first


def test_latest_forecast():
    res = client.get("/api/forecast/latest")
    assert res.status_code == 200
    data = res.json()
    assert "horizons" in data
    assert len(data["horizons"]) >= 2


def test_forecast_evaluation():
    res = client.get("/api/forecast/evaluation")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 6
    methods = {r["method"] for r in data}
    assert any("Gradient Boosting" in m for m in methods)
    assert any("Persistence" in m for m in methods)


def test_advice():
    res = client.get("/api/advice")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 5
    for r in data:
        assert "current_advice_en" in r
        assert "current_advice_hi" in r
        assert "tomorrow_advice_en" in r
        assert "source_citation" in r


def test_dust_demo():
    res = client.get("/api/dust-demo")
    assert res.status_code == 200
    data = res.json()
    assert data["peak_reduction_pct"] > 30.0
    assert len(data["schedule"]) > 0
    first = data["schedule"][0]
    assert "hour" in first
    assert "baseline_dust_index_sum" in first
    assert "optimized_dust_index_sum" in first


def test_dust_simulation():
    res = client.post(
        "/api/dust-demo/simulate",
        json={"shift_hours": 4, "misting_efficiency_pct": 25.0, "stagnation_avoidance_weight": 1.5},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["achieved_peak_reduction_pct"] > 20.0


def test_validation_backtest():
    res = client.get("/api/validation/backtest")
    assert res.status_code == 200
    data = res.json()
    assert data["summary"]["overlap_success_rate_pct"] == 100.0
    assert len(data["comparisons"]) == 63


def test_validation_health_impact():
    res = client.get("/api/validation/health-impact")
    assert res.status_code == 200
    data = res.json()
    assert "title" in data
    assert "episodes" in data


def test_validation_overview():
    res = client.get("/api/validation/overview")
    assert res.status_code == 200
    data = res.json()
    assert "backtest" in data
    assert "sensor_health_benchmark" in data
    assert "forecast_accuracy" in data


def test_meta_summary():
    res = client.get("/api/meta/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["episodes_cataloged"] >= 6
    assert data["total_stations_active"] >= 70
    assert "stubble_burning" in data["sources_modeled"]


def test_meta_sources():
    res = client.get("/api/meta/sources")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5


def test_meta_disclaimer():
    res = client.get("/api/meta/disclaimer")
    assert res.status_code == 200
    data = res.json()
    assert "Attribution is an estimate" in data["core_principle"]
