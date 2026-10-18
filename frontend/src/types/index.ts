export interface EpisodeSummary {
  episode_id: number;
  title: string;
  start: string;
  end: string;
  duration_days: number;
  peak_pm25: number;
  mean_pm25: number;
  season: string;
  diwali_window: number;
  dominant_source: string;
  dominant_share: number;
  dominant_label: string;
}

export interface LedgerEntry {
  episode_id: number;
  source: string;
  share_low_pct: number;
  share_mid_pct: number;
  share_high_pct: number;
  start: string;
  end: string;
  counterfactual_mean_pm25?: number;
  counterfactual_reduction_pct?: number;
  contradiction_penalty_factor?: number;
  status?: string;
  [key: string]: any;
}

export interface EvidenceLabel {
  episode_id: number;
  source: string;
  label: 'Supported' | 'Conflicting' | 'Insufficient evidence' | string;
  share_mid_pct: number;
  support_reasons?: string;
  cross_checks?: string;
  [key: string]: any;
}

export interface ActionRecommendation {
  episode_id: number;
  source: string;
  label: string;
  tier: 'act' | 'assess' | 'inspect' | 'alert' | 'collect' | 'verify' | string;
  action: string;
  responsible_party: string;
  verification_needed: string;
  caution: string;
  hotspot_stations?: string[];
  [key: string]: any;
}

export interface EpisodeTimeseriesPoint {
  time: string;
  delhi_pm25_hourly_mean?: number;
  delhi_pm25_daily_mean?: number;
  wind_speed_m_s?: number;
  stagnation_day?: number;
  fires_linked_median?: number;
  raw_fires_24h_pbhr?: number;
  [key: string]: any;
}

export interface EpisodeDetail {
  summary: EpisodeSummary;
  attribution: LedgerEntry[];
  evidence_labels: EvidenceLabel[];
  actions: ActionRecommendation[];
  timeseries: EpisodeTimeseriesPoint[];
}

export interface StationDetail {
  station_id: string;
  name: string;
  latitude: number;
  longitude: number;
  lat: number;
  lon: number;
  district: string;
  state: string;
  agency: string;
  station_type: string;
  status: 'OK' | 'watch' | 'suspect' | 'unassessed' | string;
  observed_pm25: number | null;
  expected_pm25: number | null;
  expected_spread: number | null;
  residual_pm25: number | null;
  z_score: number | null;
  hours_persistent: number;
  corr24h: number | null;
  reasons: string;
  is_suspect: boolean;
}

export interface SensorValidationReport {
  total_stations_evaluated: number;
  injected_fault_stations: number;
  untouched_stations: number;
  fault_types: string[];
  true_positives_detected: number;
  detection_rate_pct: number;
  false_alarm_rate_pct: number;
  detection_rate_suspect_only_pct?: number;
  false_alarm_rate_suspect_only_pct?: number;
  benchmark_passed: boolean;
  methodology: string;
}

export interface ForecastHourlyPoint {
  issue_time: string;
  horizon_h: number;
  target_time: string;
  pm25_pred: number;
  pm25_low: number;
  pm25_high: number;
  aqi_category: string;
}

export interface LatestForecastSummary {
  as_of_time: string;
  summary: string;
  horizons: Array<{
    horizon_h: number;
    target_time: string;
    pm25_pred: number;
    pm25_low: number;
    pm25_high: number;
    aqi_category: string;
  }>;
}

export interface ForecastEvaluationRow {
  method?: string;
  model_name?: string;
  horizon_h: number;
  rmse_ugm3?: number;
  rmse?: number;
  mae_ugm3?: number;
  mae?: number;
  r2_score?: number;
  r2?: number;
  beats_persistence?: boolean;
  aqi_category_acc_pct?: number;
  target_window?: string;
}

export interface PrecautionRow {
  date: string;
  evaluated_at?: string;
  group: string;
  current_pm25: number;
  current_aqi_band: string;
  current_advice_en: string;
  current_advice_hi: string;
  tomorrow_date?: string;
  tomorrow_pm25_forecast?: number;
  tomorrow_pm25_range?: string;
  tomorrow_aqi_band?: string;
  tomorrow_advice_en?: string;
  tomorrow_advice_hi?: string;
  source_context_en?: string;
  source_context_hi?: string;
  source_citation?: string;
  disclaimer_en?: string;
  disclaimer_hi?: string;
}

export interface AdviceGroup {
  id: string;
  name: string;
  name_hi: string;
}

export interface DustScheduleRow {
  hour: number;
  time_window: string;
  stagnation_inversion_factor: number;
  baseline_dust_index_sum: number;
  optimized_dust_index_sum: number;
  dust_index_reduction: number;
  baseline_weighted_exposure: number;
  optimized_weighted_exposure: number;
  exposure_reduction: number;
}

export interface DustDemoResponse {
  title: string;
  status: string;
  target_hotspot: string;
  simulated_sites_count: number;
  peak_reduction_pct: number;
  disclaimer: string;
  schedule: DustScheduleRow[];
}

export interface DustSimulationResult {
  status: string;
  parameters_applied: {
    shift_hours: number;
    misting_efficiency_pct: number;
    stagnation_avoidance_weight: number;
  };
  baseline_peak_score: number;
  simulated_peak_score: number;
  achieved_peak_reduction_pct: number;
  schedule: Array<{
    hour: number;
    baseline_dust_index_sum: number;
    custom_scheduled_score: number;
    reduction_pct: number;
    is_stagnation_hour: boolean;
  }>;
}

export interface BacktestComparisonRow {
  episode_id: number;
  episode_dates: string;
  source: string;
  comparison_type: 'contemporaneous_episode' | 'seasonal_baseline' | string;
  study_id: string;
  citation: string;
  method: string;
  study_period: string;
  model_low_pct: number;
  model_mid_pct: number;
  model_high_pct: number;
  ref_low_pct: number;
  ref_mid_pct: number;
  ref_high_pct: number;
  overlap: boolean;
  overlap_range: string;
  mid_concordance: boolean;
  status: string;
  divergence_pct: number;
  explanation: string;
  study_notes?: string;
}

export interface BacktestSummary {
  headline: string;
  total_comparisons: number;
  total_interval_overlaps: number;
  overlap_success_rate_pct: number;
  midpoint_concordance_rate_pct: number;
  contemporaneous_backtests: {
    total: number;
    overlaps: number;
    overlap_rate_pct: number;
    episodes_evaluated: number[];
  };
  seasonal_baseline_validation: {
    total: number;
    overlaps: number;
    overlap_rate_pct: number;
  };
  by_source: Record<string, {
    comparisons: number;
    overlaps: number;
    overlap_rate_pct: number;
    mean_divergence_pct: number;
  }>;
  methodology_limitations: string[];
}

export interface MetaSummary {
  project_name: string;
  version: string;
  description: string;
  core_principle: string;
  total_stations_active: number;
  episodes_cataloged: number;
  available_seasons: string[];
  sources_modeled: string[];
  attribution_method: string;
  uncertainty_method: string;
  validation_status: string;
}

export interface SourceProfile {
  id: string;
  name: string;
  name_hi: string;
  category: string;
  tracer_features: string[];
  description: string;
}
