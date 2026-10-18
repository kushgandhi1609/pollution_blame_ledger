import {
  ActionRecommendation,
  AdviceGroup,
  BacktestComparisonRow,
  BacktestSummary,
  DustDemoResponse,
  DustSimulationResult,
  EpisodeDetail,
  EpisodeSummary,
  EpisodeTimeseriesPoint,
  EvidenceLabel,
  ForecastEvaluationRow,
  ForecastHourlyPoint,
  LatestForecastSummary,
  LedgerEntry,
  MetaSummary,
  PrecautionRow,
  SensorValidationReport,
  SourceProfile,
  StationDetail,
} from '../types';

const BASE_URL = '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API Error [${res.status}]: ${errorText || res.statusText}`);
  }
  return res.json();
}

export const api = {
  // Meta
  getMetaSummary: (): Promise<MetaSummary> =>
    fetch(`${BASE_URL}/meta/summary`).then(handleResponse<MetaSummary>),

  getSources: (): Promise<SourceProfile[]> =>
    fetch(`${BASE_URL}/meta/sources`).then(handleResponse<SourceProfile[]>),

  // Episodes
  getEpisodes: (season?: string, dominant_source?: string): Promise<EpisodeSummary[]> => {
    const params = new URLSearchParams();
    if (season) params.set('season', season);
    if (dominant_source) params.set('dominant_source', dominant_source);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return fetch(`${BASE_URL}/episodes${qs}`).then(handleResponse<EpisodeSummary[]>);
  },

  getEpisodeDetail: (episodeId: number): Promise<EpisodeDetail> =>
    fetch(`${BASE_URL}/episodes/${episodeId}`).then(handleResponse<EpisodeDetail>),

  getEpisodeAttribution: (episodeId: number): Promise<LedgerEntry[]> =>
    fetch(`${BASE_URL}/episodes/${episodeId}/attribution`).then(handleResponse<LedgerEntry[]>),

  getEpisodeLabels: (episodeId: number): Promise<EvidenceLabel[]> =>
    fetch(`${BASE_URL}/episodes/${episodeId}/labels`).then(handleResponse<EvidenceLabel[]>),

  getEpisodeActions: (episodeId: number, tier?: string): Promise<ActionRecommendation[]> => {
    const qs = tier ? `?tier=${encodeURIComponent(tier)}` : '';
    return fetch(`${BASE_URL}/episodes/${episodeId}/actions${qs}`).then(
      handleResponse<ActionRecommendation[]>
    );
  },

  getEpisodeTimeseries: (episodeId: number): Promise<EpisodeTimeseriesPoint[]> =>
    fetch(`${BASE_URL}/episodes/${episodeId}/timeseries`).then(
      handleResponse<EpisodeTimeseriesPoint[]>
    ),

  // Sensors & Network Health
  getStations: (status?: string, district?: string): Promise<StationDetail[]> => {
    const params = new URLSearchParams();
    if (status) params.set('status', status);
    if (district) params.set('district', district);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return fetch(`${BASE_URL}/sensors/stations${qs}`).then(handleResponse<StationDetail[]>);
  },

  getSensorHealthTable: (status?: string): Promise<any[]> => {
    const qs = status ? `?status=${encodeURIComponent(status)}` : '';
    return fetch(`${BASE_URL}/sensors/health${qs}`).then(handleResponse<any[]>);
  },

  getSensorValidation: (): Promise<SensorValidationReport> =>
    fetch(`${BASE_URL}/sensors/validation`).then(handleResponse<SensorValidationReport>),

  // Forecast
  getForecast: (horizon?: number, limit = 72): Promise<ForecastHourlyPoint[]> => {
    const params = new URLSearchParams();
    if (horizon) params.set('horizon', horizon.toString());
    params.set('limit', limit.toString());
    return fetch(`${BASE_URL}/forecast?${params.toString()}`).then(
      handleResponse<ForecastHourlyPoint[]>
    );
  },

  getLatestForecast: (): Promise<LatestForecastSummary> =>
    fetch(`${BASE_URL}/forecast/latest`).then(handleResponse<LatestForecastSummary>),

  getForecastEvaluation: (): Promise<ForecastEvaluationRow[]> =>
    fetch(`${BASE_URL}/forecast/evaluation`).then(handleResponse<ForecastEvaluationRow[]>),

  // Precaution Advisor
  getAdvice: (group?: string): Promise<PrecautionRow[]> => {
    const qs = group ? `?group=${encodeURIComponent(group)}` : '';
    return fetch(`${BASE_URL}/advice${qs}`).then(handleResponse<PrecautionRow[]>);
  },

  getAdviceGroups: (): Promise<AdviceGroup[]> =>
    fetch(`${BASE_URL}/advice/groups`).then(handleResponse<AdviceGroup[]>),

  // Dust Demonstration & Simulation
  getDustSchedule: (): Promise<DustDemoResponse> =>
    fetch(`${BASE_URL}/dust-demo`).then(handleResponse<DustDemoResponse>),

  simulateDustShift: (params: {
    shift_hours: number;
    misting_efficiency_pct: number;
    stagnation_avoidance_weight: number;
  }): Promise<DustSimulationResult> =>
    fetch(`${BASE_URL}/dust-demo/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    }).then(handleResponse<DustSimulationResult>),

  // Validation
  getBacktestData: (): Promise<{
    summary: BacktestSummary;
    total_comparisons: number;
    comparisons: BacktestComparisonRow[];
  }> => fetch(`${BASE_URL}/validation/backtest`).then(handleResponse<any>),

  getHealthImpact: (): Promise<any> =>
    fetch(`${BASE_URL}/validation/health-impact`).then(handleResponse<any>),

  getValidationOverview: (): Promise<any> =>
    fetch(`${BASE_URL}/validation/overview`).then(handleResponse<any>),
};
