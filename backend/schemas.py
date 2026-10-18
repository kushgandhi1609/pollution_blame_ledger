"""Pydantic schemas for type-safe API responses matching the data artifacts."""

from typing import Any

from pydantic import BaseModel

# -----------------------------------------------------------------------------
# Episodes & Attribution
# -----------------------------------------------------------------------------

class EpisodeSummary(BaseModel):
    episode_id: int
    title: str
    start: str
    end: str
    duration_days: int
    season: str
    is_diwali_window: bool
    peak_pm25: float
    mean_pm25: float
    dominant_source: str
    dominant_share_pct: float
    dominant_label: str
    status: str


class LedgerEntry(BaseModel):
    episode_id: int
    source: str
    share_low_pct: float
    share_mid_pct: float
    share_high_pct: float
    evidence_score: float
    grade: str
    modules_supporting: str | None = None
    modules_contradicting: str | None = None
    evidence_for: str | None = None
    evidence_against: str | None = None
    limitations: str | None = None
    notes: str | None = None


class EvidenceLabel(BaseModel):
    episode_id: int
    source: str
    share_mid_pct: float
    grade: str
    evidence_score: float
    label: str
    label_reason: str
    modules_supporting: str | None = None
    modules_contradicting: str | None = None
    evidence_for: str | None = None
    evidence_against: str | None = None


class ActionRecommendation(BaseModel):
    episode_id: int
    start: str
    end: str
    source: str
    share_mid_pct: float
    label: str
    tier: str
    action: str
    responsible_party: str
    where_target: str
    why_evidence: str
    verification_needed: str
    caution: str


class EpisodeDetail(BaseModel):
    summary: EpisodeSummary
    attribution: list[dict[str, Any]]
    evidence_labels: list[dict[str, Any]]
    actions: list[dict[str, Any]]
    timeseries: list[dict[str, Any]]


# -----------------------------------------------------------------------------
# Sensors & Health
# -----------------------------------------------------------------------------

class StationDetail(BaseModel):
    station_id: str
    name: str
    latitude: float
    longitude: float
    lat: float
    lon: float
    district: str
    state: str
    agency: str
    station_type: str
    status: str
    observed_pm25: float | None = None
    expected_pm25: float | None = None
    expected_spread: float | None = None
    residual_pm25: float | None = None
    z_score: float | None = None
    hours_persistent: int | None = None
    corr24h: float | None = None
    reasons: str
    is_suspect: bool


class SensorValidationReport(BaseModel):
    total_stations_evaluated: int
    injected_fault_stations: int
    fault_types: list[str]
    true_positives_detected: int
    detection_rate_pct: float
    false_alarm_rate_pct: float
    benchmark_passed: bool
    methodology: str


# -----------------------------------------------------------------------------
# Forecast & Precaution
# -----------------------------------------------------------------------------

class ForecastHourlyPoint(BaseModel):
    issue_time: str
    target_time: str
    horizon_h: int
    pm25_pred: float
    pm25_low: float
    pm25_high: float
    aqi_category: str


class ForecastEvaluationRow(BaseModel):
    horizon_h: int
    method: str
    beats_persistence: bool
    mae_ugm3: float
    rmse_ugm3: float
    r2_score: float
    aqi_category_acc_pct: float


class PrecautionRow(BaseModel):
    date: str
    evaluated_at: str
    group: str
    current_pm25: float
    current_aqi_band: str
    current_advice_en: str
    current_advice_hi: str
    tomorrow_date: str
    tomorrow_pm25_forecast: float
    tomorrow_pm25_range: str
    tomorrow_aqi_band: str
    tomorrow_advice_en: str
    tomorrow_advice_hi: str
    source_context_en: str
    source_context_hi: str
    source_citation: str
    disclaimer_en: str
    disclaimer_hi: str


# -----------------------------------------------------------------------------
# Dust Demo
# -----------------------------------------------------------------------------

class DustScheduleRow(BaseModel):
    hour: int
    time_window: str
    stagnation_inversion_factor: float
    baseline_dust_index_sum: float
    optimized_dust_index_sum: float
    dust_index_reduction: float
    baseline_weighted_exposure: float
    optimized_weighted_exposure: float
    exposure_reduction: float


class DustDemoResponse(BaseModel):
    title: str
    status: str
    target_hotspot: str
    simulated_sites_count: int
    peak_reduction_pct: float
    disclaimer: str
    schedule: list[DustScheduleRow]


# -----------------------------------------------------------------------------
# Backtest & Health Validation
# -----------------------------------------------------------------------------

class BacktestSummary(BaseModel):
    headline: str
    total_comparisons: int
    total_interval_overlaps: int
    overlap_success_rate_pct: float
    midpoint_concordance_count: int
    midpoint_concordance_rate_pct: float
    contemporaneous_backtests: dict[str, Any]
    seasonal_baseline_validation: dict[str, Any]
    by_source: dict[str, Any]
    methodology_limitations: Any = []


class MetaSummary(BaseModel):
    project_name: str
    version: str
    description: str
    core_principle: str
    total_stations_active: int
    episodes_cataloged: int
    available_seasons: list[str]
    sources_modeled: list[str]
    attribution_method: str
    uncertainty_method: str
    validation_status: str
