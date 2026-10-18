import React, { useEffect, useState } from 'react';
import { Header, ActiveTab } from './components/layout/Header';
import { KpiBanner } from './components/layout/KpiBanner';
import { AttributionView } from './components/attribution/AttributionView';
import { SensorsView } from './components/sensors/SensorsView';
import { PolicyView } from './components/policy/PolicyView';
import { ForecastAdvisorView } from './components/forecast/ForecastAdvisorView';
import { MethodologyModal } from './components/modals/MethodologyModal';
import { api } from './services/api';
import {
  AdviceGroup,
  BacktestComparisonRow,
  BacktestSummary,
  DustDemoResponse,
  EpisodeDetail,
  EpisodeSummary,
  ForecastEvaluationRow,
  ForecastHourlyPoint,
  LatestForecastSummary,
  MetaSummary,
  PrecautionRow,
  SensorValidationReport,
  SourceProfile,
  StationDetail,
} from './types';
import { AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('attribution');
  const [isMethodologyOpen, setIsMethodologyOpen] = useState<boolean>(false);

  // Global Analytical State
  const [meta, setMeta] = useState<MetaSummary | null>(null);
  const [sources, setSources] = useState<SourceProfile[]>([]);
  const [latestForecast, setLatestForecast] = useState<LatestForecastSummary | null>(null);

  // Tab 1: Episodes & Attribution
  const [episodes, setEpisodes] = useState<EpisodeSummary[]>([]);
  const [selectedEpisodeId, setSelectedEpisodeId] = useState<number>(1);
  const [selectedSeason, setSelectedSeason] = useState<string>('');
  const [episodeDetail, setEpisodeDetail] = useState<EpisodeDetail | null>(null);
  const [episodeLoading, setEpisodeLoading] = useState<boolean>(false);

  // Tab 2: Sensors
  const [stations, setStations] = useState<StationDetail[]>([]);
  const [sensorValidation, setSensorValidation] = useState<SensorValidationReport | null>(null);

  // Tab 3: Policy & Simulation
  const [dustDemo, setDustDemo] = useState<DustDemoResponse | null>(null);

  // Tab 4: Forecast, Advisor & Backtesting
  const [forecastPoints, setForecastPoints] = useState<ForecastHourlyPoint[]>([]);
  const [forecastEval, setForecastEval] = useState<ForecastEvaluationRow[]>([]);
  const [advice, setAdvice] = useState<PrecautionRow[]>([]);
  const [adviceGroups, setAdviceGroups] = useState<AdviceGroup[]>([]);
  const [backtestSummary, setBacktestSummary] = useState<BacktestSummary | null>(null);
  const [backtestComparisons, setBacktestComparisons] = useState<BacktestComparisonRow[]>([]);
  const [healthData, setHealthData] = useState<any>(null);

  const [apiError, setApiError] = useState<string | null>(null);
  const [initialLoading, setInitialLoading] = useState<boolean>(true);

  // Initial Data Load
  useEffect(() => {
    async function init() {
      try {
        setInitialLoading(true);
        const [
          metaData,
          sourcesData,
          latestFc,
          episodesList,
          stationsList,
          sensorVal,
          dustData,
          fcPoints,
          fcEval,
          adv,
          advGroups,
          btData,
          health,
        ] = await Promise.all([
          api.getMetaSummary().catch(() => null),
          api.getSources().catch(() => []),
          api.getLatestForecast().catch(() => null),
          api.getEpisodes().catch(() => []),
          api.getStations().catch(() => []),
          api.getSensorValidation().catch(() => null),
          api.getDustSchedule().catch(() => null),
          api.getForecast(undefined, 72).catch(() => []),
          api.getForecastEvaluation().catch(() => []),
          api.getAdvice().catch(() => []),
          api.getAdviceGroups().catch(() => []),
          api.getBacktestData().catch(() => null),
          api.getHealthImpact().catch(() => null),
        ]);

        if (metaData) setMeta(metaData);
        if (sourcesData) setSources(sourcesData);
        if (latestFc) setLatestForecast(latestFc);
        if (episodesList && episodesList.length > 0) {
          setEpisodes(episodesList);
          setSelectedEpisodeId(episodesList[0].episode_id);
        }
        if (stationsList) setStations(stationsList);
        if (sensorVal) setSensorValidation(sensorVal);
        if (dustData) setDustDemo(dustData);
        if (fcPoints) setForecastPoints(fcPoints);
        if (fcEval) setForecastEval(fcEval);
        if (adv) setAdvice(adv);
        if (advGroups) setAdviceGroups(advGroups);
        if (btData) {
          setBacktestSummary(btData.summary);
          setBacktestComparisons(btData.comparisons || []);
        }
        if (health) setHealthData(health);
      } catch (err: any) {
        console.error('Initialization error:', err);
        setApiError(err.message || 'Could not connect to FastAPI backend.');
      } finally {
        setInitialLoading(false);
      }
    }

    init();
  }, []);

  // Fetch detail whenever selectedEpisodeId changes
  useEffect(() => {
    if (!selectedEpisodeId) return;

    let isMounted = true;
    setEpisodeLoading(true);

    api
      .getEpisodeDetail(selectedEpisodeId)
      .then((detail) => {
        if (isMounted) {
          setEpisodeDetail(detail);
        }
      })
      .catch((err) => {
        console.error(`Failed to load episode ${selectedEpisodeId}:`, err);
      })
      .finally(() => {
        if (isMounted) setEpisodeLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedEpisodeId]);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 1. Header with Brand Lockup & Navigation */}
      <Header
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab)}
        onOpenMethodology={() => setIsMethodologyOpen(true)}
      />

      {/* 2. Top-level KPI Summary Bar */}
      <KpiBanner meta={meta} latestForecast={latestForecast} />

      {/* API Connectivity Warning Banner (if backend is offline) */}
      {apiError && (
        <div
          style={{
            maxWidth: '1440px',
            margin: '12px auto 0 auto',
            width: '100%',
            padding: '0 24px',
          }}
        >
          <div
            style={{
              backgroundColor: 'var(--color-warning-bg)',
              border: '1px solid var(--color-warning-border)',
              borderRadius: 'var(--radius-sm)',
              padding: '10px 16px',
              fontSize: '12px',
              color: 'var(--color-warning-text)',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <AlertCircle size={16} />
            <span>
              Backend API communication note: Ensure the FastAPI backend server is active on port 8000 (<code>uvicorn backend.main:app --port 8000</code>).
            </span>
          </div>
        </div>
      )}

      {/* 3. Main Workspace Area */}
      <main
        style={{
          flex: 1,
          maxWidth: '1440px',
          width: '100%',
          margin: '0 auto',
          padding: '24px',
        }}
      >
        {initialLoading ? (
          <div
            style={{
              padding: '80px 20px',
              textAlign: 'center',
              color: 'var(--color-text-muted)',
              fontSize: '14px',
            }}
          >
            Connecting to AerTrace intelligence engine and preloading spatial telemetry...
          </div>
        ) : (
          <>
            {activeTab === 'attribution' && (
              <AttributionView
                episodes={episodes}
                selectedEpisodeId={selectedEpisodeId}
                onSelectEpisode={(id) => setSelectedEpisodeId(id)}
                selectedSeason={selectedSeason}
                onSelectSeason={(s) => setSelectedSeason(s)}
                episodeDetail={episodeDetail}
                loading={episodeLoading}
              />
            )}

            {activeTab === 'sensors' && (
              <SensorsView
                stations={stations}
                validation={sensorValidation}
                loading={initialLoading}
              />
            )}

            {activeTab === 'policy' && (
              <PolicyView
                actions={episodeDetail?.actions || []}
                dustDemo={dustDemo}
                activeEpisodeTitle={episodeDetail?.summary.title}
              />
            )}

            {activeTab === 'forecast' && (
              <ForecastAdvisorView
                forecastPoints={forecastPoints}
                forecastEval={forecastEval}
                advice={advice}
                adviceGroups={adviceGroups}
                backtestSummary={backtestSummary}
                backtestComparisons={backtestComparisons}
                healthData={healthData}
              />
            )}
          </>
        )}
      </main>

      {/* 4. Institutional Footer */}
      <footer
        style={{
          backgroundColor: 'var(--color-surface)',
          borderTop: '1px solid var(--color-border)',
          padding: '20px 24px',
          marginTop: 'auto',
        }}
      >
        <div
          style={{
            maxWidth: '1440px',
            margin: '0 auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
            fontSize: '11px',
            color: 'var(--color-text-muted)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <img
              src="/aertrace_logo.png"
              alt="AerTrace"
              style={{ height: '20px', width: 'auto', opacity: 0.85 }}
            />
            <span>
              <strong>AERTRACE</strong> • Delhi-NCR Air Quality Attribution &amp; Intelligence Ledger
            </span>
          </div>

          <div>
            Built with 5,000-draw Monte Carlo modeling • Standardized on CPCB, DPCC &amp; WHO GEMM benchmarks
          </div>

          <div style={{ display: 'flex', gap: '16px' }}>
            <button
              onClick={() => setIsMethodologyOpen(true)}
              style={{ color: 'var(--color-primary)', fontSize: '11px', fontWeight: 500 }}
            >
              Methodology &amp; Disclaimers
            </button>
            <a
              href="/docs"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: 'var(--color-primary)', fontSize: '11px', fontWeight: 500 }}
            >
              Interactive API Docs
            </a>
          </div>
        </div>
      </footer>

      {/* 5. Global Methodology & Data Dictionary Drawer/Modal */}
      <MethodologyModal
        isOpen={isMethodologyOpen}
        onClose={() => setIsMethodologyOpen(false)}
        sources={sources}
      />
    </div>
  );
};

export default App;
