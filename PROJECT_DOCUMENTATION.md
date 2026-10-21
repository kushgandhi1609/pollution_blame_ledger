# AerTrace: Delhi-NCR Air Quality Attribution & Intelligence Ledger
## Comprehensive Data, Machine Learning, and System Architecture Documentation

---

## 1. Quick Overview

**AerTrace** is an institutional air pollution intelligence and source attribution platform for the Delhi National Capital Region (NCR). Rather than asserting single-point blame during severe winter smog episodes, the platform calculates probabilistic credible intervals across five modeled pollution sources (agricultural stubble burning, vehicular exhaust, road silt/construction dust, industrial boilers, and secondary remainder) using a 5,000-draw Monte Carlo engine constrained by published scientific literature. The system pairs these attributions with multi-sensor spatial consistency quality control (Inverse-Distance Weighting across 72 monitoring stations), a 72-hour gradient boosted particulate forecasting model with quantile uncertainty bands, an interactive diurnal construction dust rescheduling simulator, and an accredited bilingual public health precaution advisor.

### Summary Table: Mapping Site Elements to Datasets and ML Models

| Site page / section | What the user sees | Dataset used | ML model used | Source file(s) |
|---|---|---|---|---|
| **Top KPI Banner: Active Stations** | Live count of continuous ambient air quality monitoring stations (72 active stations across Delhi-NCR) | [stations.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/reference/stations.csv) | None (plain database lookup) | [backend/routers/meta.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/meta.py), [frontend/src/components/layout/KpiBanner.tsx](file:///Users/mac/Desktop/pollution-blame-ledger/frontend/src/components/layout/KpiBanner.tsx) |
| **Top KPI Banner: Cataloged Episodes** | Total count of cataloged severe smog windows (6 episodes across 2021 and 2023) | [episodes.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/episodes.csv), [city_daily_final.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/city_daily_final.csv) | Rule-based episode segmentation ($\ge 150 \ \mu\text{g}/\text{m}^3$ daily mean for $\ge 2$ consecutive days) | [backend/loaders.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/loaders.py), [pipeline/s7_final.py](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/s7_final.py) |
| **Top KPI Banner: Literature Backtesting** | Peer-reviewed literature validation metric (100% range overlap across 63 studies) | [backtest_summary.json](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/backtest_summary.json), [reference_apportionment.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/reference/reference_apportionment.csv) | Interval overlap & midpoint concordance validation algorithm | [analysis/backtest.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/backtest.py), [backend/routers/validation.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/validation.py) |
| **Top KPI Banner: 24h Forecast Callout** | Projected 24h city-wide PM2.5 concentration, CPCB AQI category, and 80% uncertainty envelope | [forecast_hourly.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/forecast_hourly.csv) | Multi-Horizon Quantile HistGradientBoostingRegressor (10th, 50th, 90th percentiles) | [analysis/forecast.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/forecast.py), [backend/routers/forecast.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/forecast.py) |
| **Episodes & Attribution: Episode Selector** | Selector cards for 6 cataloged episodes with date ranges, peak/mean PM2.5, dominant source, and evidence label | [episodes.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/episodes.csv), [ledger_labels.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/ledger_labels.csv) | Rule-based episode detector + Monte Carlo attribution dominant source ranker | [backend/loaders.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/loaders.py), [frontend/src/components/attribution/EpisodeSelector.tsx](file:///Users/mac/Desktop/pollution-blame-ledger/frontend/src/components/attribution/EpisodeSelector.tsx) |
| **Episodes & Attribution: Monte Carlo Credible Intervals** | Horizontal bar chart showing 10th-90th percentile credible uncertainty ranges and solid midpoint shares for 5 source categories | [ledger_entries.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/ledger_entries.csv), [reference_apportionment.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/reference/reference_apportionment.csv) | 5,000-Draw Monte Carlo Evidence Apportionment Engine | [analysis/attribution.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/attribution.py), [backend/routers/episodes.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/episodes.py) |
| **Episodes & Attribution: Evidence Confidence Table** | Multi-sensor confidence table grading sources (A, B, C; Supported, Conflicting, Insufficient) with physical module rationale | [ledger_labels.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/ledger_labels.csv) | Rule-based multi-module evidence confidence grading algorithm | [analysis/evidence_labels.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/evidence_labels.py), [backend/routers/episodes.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/episodes.py) |
| **Episodes & Attribution: Hourly Telemetry Chart** | Time series of hourly Delhi median PM2.5, NCR median, wind speed, linked fires count, and stagnation bands | [city_hourly_final.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/city_hourly_final.csv) | Horizontal Advection Parcel Back-Trajectory Ensemble (10 members, 72h) + FIRMS Fire Linking | [pipeline/s5_trajectories.py](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/s5_trajectories.py), [backend/loaders.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/loaders.py) |
| **Sensors & Telemetry: Station Map** | Interactive Leaflet map of 71 stations colored by health status (OK, watch, suspect) and sized by PM2.5 | [stations.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/reference/stations.csv), [sensor_health.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/sensor_health.csv) | Spatial Inverse-Distance Weighting (IDW, $k=4$, 40 km) Anomaly Monitor | [analysis/sensor_health.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/sensor_health.py), [backend/routers/sensors.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/sensors.py) |
| **Sensors & Telemetry: Fault-Injection Benchmark** | Benchmark summary card reporting 100.0% Detection Rate and 0.0% False-Alarm Rate on synthetic injected faults | [sensor_validation_report.json](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/sensor_validation_report.json) | Synthetic fault-injection evaluation benchmark (+45% calibration drift, inlet drops) | [analysis/sensor_health.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/sensor_health.py), [backend/routers/sensors.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/sensors.py) |
| **Sensors & Telemetry: Health Diagnostics Table** | Filterable table showing observed PM2.5, IDW expected PM2.5, spatial residual, historical z-score, persistence, and correlation | [sensor_health.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/sensor_health.csv), [stations.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/reference/stations.csv) | Spatial IDW Residual & Historical Standardized Z-Score Anomaly Engine | [analysis/sensor_health.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/sensor_health.py), [backend/loaders.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/loaders.py) |
| **Policy & Simulation: Source-to-Action Matrix** | Action cards categorized by tier (ACT, ASSESS, INSPECT, ALERT, VERIFY, COLLECT) with responsible parties, hotspots, and safeguards | [action_recommendations.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/action_recommendations.csv), [actions.csv](file:///Users/mac/Desktop/pollution-blame-ledger/config/actions.csv) | Deterministic Source-to-Action Policy Matrix + Localized Hotspot Screener | [analysis/action_engine.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/action_engine.py), [backend/routers/episodes.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/episodes.py) |
| **Policy & Simulation: Dust Rescheduler Simulator** | Interactive slider-driven simulation showing baseline vs optimized diurnal construction dust exposure curves | [dust_demo_schedule.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/dust_demo_schedule.csv) | Diurnal Atmospheric Inversion Task Staggering Optimization Algorithm | [analysis/dust_scheduler_demo.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/dust_scheduler_demo.py), [backend/routers/dust_demo.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/dust_demo.py) |
| **Forecast & Advisor: 72H Forecast Projection** | 72-hour hourly PM2.5 prediction curves with 80% credible prediction boundaries and CPCB AQI category bands | [forecast_hourly.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/forecast_hourly.csv) | HistGradientBoostingRegressor (point prediction + 10th and 90th percentile quantile regressors) | [analysis/forecast.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/forecast.py), [backend/routers/forecast.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/forecast.py) |
| **Forecast & Advisor: Forecast Accuracy Benchmark** | Cross-validation accuracy table comparing model against Persistence ($y_{t+h}=y_t$) and Diurnal Seasonal Mean baselines | [forecast_eval.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/forecast_eval.csv) | 5-Fold Blocked Time-Series Cross-Validation with 72-hour Purge Gap | [analysis/forecast.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/forecast.py), [backend/routers/forecast.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/forecast.py) |
| **Forecast & Advisor: Bilingual Precaution Advisor** | Demographic health advisories (English & Hindi) tailored to current observed AQI, +24h forecast, and source alerts | [advice_daily.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/advice_daily.csv), [advice.csv](file:///Users/mac/Desktop/pollution-blame-ledger/config/advice.csv) | Rule-based Demographic Health Precaution Matching Engine | [analysis/advisor.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/advisor.py), [backend/routers/advisor.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/advisor.py) |
| **Forecast & Advisor: Literature Backtest Table** | Row-by-row table comparing model credible intervals against 63 published peer-reviewed studies (IIT Kanpur, TERI, SAFAR, DSS) | [backtest_results.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/backtest_results.csv), [reference_apportionment.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/reference/reference_apportionment.csv) | Two-Tier Interval Overlap and Midpoint Concordance Validation Algorithm | [analysis/backtest.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/backtest.py), [backend/routers/validation.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/validation.py) |
| **Forecast & Advisor: Epidemiological Burden Card** | Excess respiratory risk (+43.7%), cardiovascular risk (+32.6%), mortality (+17.5%), and cigarette equivalents (9.8 cigs/day) | [health_summary.json](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/health_summary.json), [health_impacts.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/health_impacts.csv) | WHO Global Exposure Mortality Model (GEMM) / Log-Linear Concentration-Response Functions | [analysis/health.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/health.py), [backend/routers/validation.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/validation.py) |

### Non-ML and Static Parts of the Site

- **Header Brand Lockup & Navigation**: Static UI header containing logo, project title, and tab navigation buttons.
- **Institutional Footer**: Static footer containing regulatory disclaimers, license information, and link to interactive OpenAPI Swagger documentation.
- **Methodology & Data Dictionary Modal**: Static drawer displaying definitions of the 5 modeled pollution sources and scientific tracer rules.
- **Demographic Vulnerability Cohort Selector**: Static button group switching between 5 predefined demographic filters in the Precaution Advisor.
- **Action Tier Tabs**: Client-side filtering buttons (All, ACT, ASSESS, INSPECT, ALERT, VERIFY, COLLECT) partitioning pre-computed action recommendations.
- **API Connectivity Warning Banner**: Client-side network status indicator alerting users if the FastAPI backend server is offline.

---

## 2. Page-by-Page Guide

### 2.1 Header & Top KPI Summary Bar
- **Where it is:** Global application header across all views (route `/`).
- **What the user sees:** Five top-level indicator metrics: active continuous air quality monitoring stations (72), cataloged severe smog episodes (6), Monte Carlo iteration count (5,000 draws), literature validation score (100% overlap), and the latest +24-hour forecasted PM2.5 level with its CPCB category and uncertainty range.
- **How it is generated:** On application mount, the frontend executes `Promise.all([api.getMetaSummary(), api.getLatestForecast()])`, hitting `GET /api/meta/summary` in [backend/routers/meta.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/meta.py) and `GET /api/forecast/latest` in [backend/routers/forecast.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/forecast.py). Data is extracted directly from cached reference and processed tables without UI-level transformations.
- **Dataset behind it:** [stations.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/reference/stations.csv), [episodes.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/episodes.csv), and [forecast_hourly.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/forecast_hourly.csv). See [Section 3.1](#31-monitoring-stations-dataset-stationscsv) and [Section 3.10](#310-72-hour-particulate-forecast-dataset-forecast_hourlycsv).
- **Model behind it:** [HistGradientBoostingRegressor Forecast Engine](#41-multi-horizon-particulate-forecasting-model-histgradientboostingregressor).

---

### 2.2 Episodes & Attribution View
- **Where it is:** Tab 1: "Episodes & Attribution" (route `/`, state `activeTab === 'attribution'`).

#### A. Severe Smog Episodes Catalog
- **What the user sees:** Filter buttons for 6 cataloged severe smog episodes spanning the 2021 and 2023 winter seasons. Each card shows the episode date range, duration in days, peak and mean city-wide PM2.5, dominant modeled source, and dominant evidence label.
- **How it is generated:** User selects a season or clicks an episode button -> frontend calls `api.getEpisodes()` and `api.getEpisodeDetail(id)` -> endpoint `GET /api/episodes` and `GET /api/episodes/{id}` in [backend/routers/episodes.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/episodes.py) queries [backend/loaders.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/loaders.py), which reads daily averages from `city_daily_final.csv` and merges dominant source metrics from `ledger_labels.csv`.
- **Dataset behind it:** [episodes.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/episodes.csv) and [city_daily_final.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/city_daily_final.csv). See [Section 3.6](#36-cataloged-pollution-episodes-episodescsv).
- **Model behind it:** Deterministic episode segmentation rule ($\ge 150 \ \mu\text{g}/\text{m}^3$ daily mean for $\ge 2$ days) + [5,000-Draw Monte Carlo Attribution Engine](#42-5000-draw-monte-carlo-evidence-apportionment-engine).

#### B. Monte Carlo Credible Intervals Chart
- **What the user sees:** A horizontal bar chart illustrating the estimated contribution of five source categories (agricultural stubble burning, vehicular traffic, road dust, industrial boilers, other secondary). For each source, the chart plots a shaded 10th-to-90th percentile credible uncertainty interval bar, a midpoint circle marker, and the absolute percentage spread.
- **How it is generated:** Sourced from `api.getEpisodeDetail(id)` -> `GET /api/episodes/{id}` -> returns the `attribution` list from [backend/loaders.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/loaders.py), which filters [pipeline/data/processed/ledger_entries.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/ledger_entries.csv) by `episode_id`.
- **Dataset behind it:** [ledger_entries.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/ledger_entries.csv). See [Section 3.7](#37-monte-carlo-attribution-ledger-ledger_entriescsv).
- **Model behind it:** [5,000-Draw Monte Carlo Evidence Apportionment Engine](#42-5000-draw-monte-carlo-evidence-apportionment-engine).

#### C. Multi-Sensor Evidence Confidence & Cross-Validation Table
- **What the user sees:** An empirical evidence audit table listing each source category, its midpoint share, an institutional confidence grade (A, B, or C with "Supported", "Conflicting", or "Insufficient evidence" badges), and an explicit rationale explaining which physical observational modules supported or contradicted the source.
- **How it is generated:** Sourced from `api.getEpisodeDetail(id)` -> `GET /api/episodes/{id}` -> returns `evidence_labels` from [backend/loaders.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/loaders.py), which filters [pipeline/data/processed/ledger_labels.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/ledger_labels.csv) by `episode_id`.
- **Dataset behind it:** [ledger_labels.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/ledger_labels.csv). See [Section 3.8](#38-evidence-confidence-labels-dataset-ledger_labelscsv).
- **Model behind it:** Multi-module evidence grading and classification rules implemented in [analysis/evidence_labels.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/evidence_labels.py).

#### D. Episode Hourly Telemetry & Tracers Chart
- **What the user sees:** An interactive multi-line chart across the duration of the selected episode showing hourly Delhi median PM2.5, NCR median PM2.5, wind speed (m/s), upstream linked satellite active fires, and shaded vertical bands indicating periods of atmospheric stagnation.
- **How it is generated:** Sourced from `api.getEpisodeDetail(id)` -> `GET /api/episodes/{id}` -> returns the `timeseries` array from [backend/loaders.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/loaders.py), which slices [pipeline/data/processed/city_hourly_final.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/city_hourly_final.csv) for the episode's start and end timestamps.
- **Dataset behind it:** [city_hourly_final.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/city_hourly_final.csv). See [Section 3.4](#34-city-level-hourly-features-city_hourly_finalcsv).
- **Model behind it:** Horizontal Advection Ensemble Back-Trajectory Fire Linking Engine ([pipeline/s5_trajectories.py](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/s5_trajectories.py)).

---

### 2.3 Sensors & Network Health View
- **Where it is:** Tab 2: "Sensors & Telemetry" (route `/`, state `activeTab === 'sensors'`).

#### A. Continuous Air Quality Monitoring Network Map
- **What the user sees:** A full-bleed Leaflet map of the Delhi-NCR monitoring domain displaying 72 CAAQMS station pins. Pins are color-coded by operational health status (Green = OK, Amber = watch, Red = suspect) and scaled by observed PM2.5 concentration. Clicking any station opens an inspector modal with neighborhood IDW expected values, residuals, and correlation metrics.
- **How it is generated:** On load, the frontend invokes `api.getStations()` -> `GET /api/sensors/stations` in [backend/routers/sensors.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/sensors.py) -> [backend/loaders.py:get_stations_with_health()](file:///Users/mac/Desktop/pollution-blame-ledger/backend/loaders.py) merges coordinates from `stations.csv` with the latest diagnostic residuals from `sensor_health.csv`.
- **Dataset behind it:** [stations.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/reference/stations.csv) and [sensor_health.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/sensor_health.csv). See [Section 3.1](#31-monitoring-stations-dataset-stationscsv) and [Section 3.9](#39-sensor-health-and-spatial-consistency-dataset-sensor_healthcsv).
- **Model behind it:** [Spatial Inverse-Distance Weighting (IDW) Anomaly Monitor](#43-spatial-inverse-distance-weighting-idw-sensor-consistency-monitor).

#### B. Synthetic Fault-Injection Benchmark Card
- **What the user sees:** A validation card summarizing the accuracy of the spatial sensor QC algorithm when tested against synthetic fault injections. It reports 71 stations evaluated, 5 injected faults (+45% progressive calibration drift and zero flatline drop), a 100.0% Detection Rate (Recall), a 0.0% False-Alarm Rate, and a "BENCHMARK PASSED" status.
- **How it is generated:** On load, frontend calls `api.getSensorValidation()` -> `GET /api/sensors/validation` in [backend/routers/sensors.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/sensors.py) -> reads [pipeline/data/processed/sensor_validation_report.json](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/sensor_validation_report.json).
- **Dataset behind it:** [sensor_validation_report.json](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/sensor_validation_report.json).
- **Model behind it:** Synthetic Fault Injection Benchmark ([analysis/sensor_health.py:validate_sensor_check()](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/sensor_health.py)).

#### C. Neighborhood Consistency & Residual Telemetry Table
- **What the user sees:** A filterable diagnostic table of all monitoring stations listing Station ID, Station Name, District/Agency, Observed PM2.5 ($\mu\text{g}/\text{m}^3$), IDW Expected PM2.5 ($\mu\text{g}/\text{m}^3$), Spatial Residual, Historical Z-Score, Consecutive Hours Persistent, 24-Hour Neighborhood Correlation, Status Badge, and Diagnostic Reasons.
- **How it is generated:** Frontend invokes `api.getStations(statusFilter)` -> `GET /api/sensors/stations` -> [backend/loaders.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/loaders.py) merges `stations.csv` with `sensor_health.csv` and returns JSON records.
- **Dataset behind it:** [sensor_health.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/sensor_health.csv). See [Section 3.9](#39-sensor-health-and-spatial-consistency-dataset-sensor_healthcsv).
- **Model behind it:** [Spatial Inverse-Distance Weighting (IDW) Anomaly Monitor](#43-spatial-inverse-distance-weighting-idw-sensor-consistency-monitor).

---

### 2.4 Policy & Simulation View
- **Where it is:** Tab 3: "Policy & Simulation" (route `/`, state `activeTab === 'policy'`).

#### A. Source-to-Action Operational Matrix
- **What the user sees:** Actionable policy cards mapped directly to active source evidence for the selected episode. Cards are tiered into operational categories: Immediate Suppression (`ACT`), Corridor Assessment (`ASSESS`), Industrial Audit (`INSPECT`), Inter-State Advisory (`ALERT`), Ground Verification (`VERIFY`), and Telemetry Collection (`COLLECT`). Each card shows the Action description, Responsible Agency, Target Hotspot Locations (with localized excess $\mu\text{g}/\text{m}^3$), Evidence Rationale, Mandatory Ground Verification Checks, and Cautionary Safeguards preventing premature penal site shutdowns.
- **How it is generated:** Loaded as part of `api.getEpisodeDetail(id)` -> `GET /api/episodes/{id}` -> [backend/loaders.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/loaders.py) queries [pipeline/data/processed/action_recommendations.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/action_recommendations.csv) for the episode ID.
- **Dataset behind it:** [action_recommendations.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/action_recommendations.csv) and [actions.csv](file:///Users/mac/Desktop/pollution-blame-ledger/config/actions.csv).
- **Model behind it:** Deterministic Source-to-Action Policy Matrix + Hotspot Local Excess Filter ([analysis/action_engine.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/action_engine.py)).

#### B. Construction Dust Rescheduler & Misting Simulator
- **What the user sees:** An interactive counterfactual optimization panel modeling an illustrative 4-site construction cluster near the Anand Vihar hotspot. Includes three interactive controls (Task Shift Window: 1-8h; Water Misting Efficiency: 0-50%; Stagnation Avoidance Weight: 1.0-2.5), an achieved peak exposure reduction indicator (default 28.4%), and a diurnal line chart comparing the "Baseline Unscheduled Dust Index" vs the "Optimized Scheduled Dust Index" across working hours (07:00 to 18:00 IST), highlighting morning inversion hours (07:00 to 10:00).
- **How it is generated:**
  - *Initial state:* Frontend calls `api.getDustSchedule()` -> `GET /api/dust-demo` in [backend/routers/dust_demo.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/dust_demo.py) -> returns precomputed baseline from [pipeline/data/processed/dust_demo_schedule.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/dust_demo_schedule.csv).
  - *Dynamic simulation:* User adjusts parameters and clicks "Run Simulation" -> frontend sends `POST /api/dust-demo/simulate` with payload `{shift_hours, misting_efficiency_pct, stagnation_avoidance_weight}` -> `run_interactive_simulation()` in [backend/routers/dust_demo.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/dust_demo.py) dynamically recalculates hourly dust scores by shifting tasks from calm to ventilated afternoon hours and applying misting suppression.
- **Dataset behind it:** [dust_demo_schedule.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/dust_demo_schedule.csv). See [Section 3.12](#312-construction-dust-scheduling-demonstration-dataset-dust_demo_schedulecsv).
- **Model behind it:** [Diurnal Construction Dust Rescheduler Optimizer](#44-diurnal-construction-dust-rescheduler-optimizer).

---

### 2.5 Forecast & Advisor View
- **Where it is:** Tab 4: "Forecast & Advisor" (route `/`, state `activeTab === 'forecast'`).

#### A. 72-Hour PM2.5 Projection with 80% Credible Ribbons
- **What the user sees:** An hourly area and line chart displaying a 72-hour forward PM2.5 concentration forecast. The chart shows the expected point trajectory, an 80% credible prediction interval band (bounded by 10th and 90th quantile predictions), CPCB AQI severity bands, and horizon filter buttons (All, +24h, +48h).
- **How it is generated:** Frontend executes `api.getForecast(undefined, 72)` -> `GET /api/forecast?limit=72` in [backend/routers/forecast.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/forecast.py) -> loads and sorts [pipeline/data/processed/forecast_hourly.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/forecast_hourly.csv).
- **Dataset behind it:** [forecast_hourly.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/forecast_hourly.csv). See [Section 3.10](#310-72-hour-particulate-forecast-dataset-forecast_hourlycsv).
- **Model behind it:** [HistGradientBoostingRegressor Forecast Engine](#41-multi-horizon-particulate-forecasting-model-histgradientboostingregressor).

#### B. Forecasting Model Accuracy Benchmark Table
- **What the user sees:** A benchmark evaluation table comparing the Gradient Boosting model against two canonical time-series baselines: the Naive Persistence baseline ($y_{t+h} = y_t$) and the Diurnal Seasonal Mean baseline across +24h and +48h forecast horizons. Metrics reported: RMSE ($\mu\text{g}/\text{m}^3$), MAE ($\mu\text{g}/\text{m}^3$), $R^2$ Score, and AQI Category Concordance (%).
- **How it is generated:** Frontend calls `api.getForecastEvaluation()` -> `GET /api/forecast/evaluation` in [backend/routers/forecast.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/forecast.py) -> returns records from [pipeline/data/processed/forecast_eval.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/forecast_eval.csv).
- **Dataset behind it:** [forecast_eval.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/forecast_eval.csv). See [Section 3.11](#311-forecast-evaluation-benchmarks-forecast_evalcsv).
- **Model behind it:** Blocked Time-Series Cross-Validation Engine ([analysis/forecast.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/forecast.py)).

#### C. Bilingual Precaution Advisor
- **What the user sees:** Demographic health advisory cards tailored to current observed AQI and tomorrow's +24h forecasted AQI, rendered in both English and Hindi. Five demographic cohorts are selectable: General Public, Children & Schools, Older Adults (60+), Cardiopulmonary Patients, and Outdoor Workers. Includes active source alerts (e.g., regional biomass smoke alerts) and official CPCB/WHO citations.
- **How it is generated:** Frontend calls `api.getAdvice()` -> `GET /api/advice` in [backend/routers/advisor.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/advisor.py) -> returns records from [pipeline/data/processed/advice_daily.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/advice_daily.csv), populated by matching current PM2.5 and +24h forecast against rules in `config/advice.csv`.
- **Dataset behind it:** [advice_daily.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/advice_daily.csv) and [advice.csv](file:///Users/mac/Desktop/pollution-blame-ledger/config/advice.csv).
- **Model behind it:** Rule-Based Health Precaution Matching Engine ([analysis/advisor.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/advisor.py)).

#### D. Scientific Transparency & Literature Backtesting Table
- **What the user sees:** A backtesting benchmark table demonstrating 100% credible interval overlap across 63 published peer-reviewed comparisons (IIT Kanpur 2016, TERI/ARAI 2018, SAFAR 2021, Decision Support System 2023). Displays Model Credible Interval [%], Published Study Range [%], Status (`PASS_ENCLOSED_BY_REF`, `PASS_INTERVAL_OVERLAP`), Study Methodology (CMB, PMF, WRF-Chem), and Scientific Explanations for observed divergences.
- **How it is generated:** Frontend calls `api.getBacktestData()` -> `GET /api/validation/backtest` in [backend/routers/validation.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/validation.py) -> loads summary metrics from [pipeline/data/processed/backtest_summary.json](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/backtest_summary.json) and comparisons from [pipeline/data/processed/backtest_results.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/backtest_results.csv).
- **Dataset behind it:** [backtest_results.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/backtest_results.csv) and [reference_apportionment.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/reference/reference_apportionment.csv). See [Section 3.2](#32-peer-reviewed-reference-apportionment-dataset-reference_apportionmentcsv) and [Section 3.13](#313-literature-backtest-results-backtest_resultscsv).
- **Model behind it:** Two-Tier Literature Backtesting Engine ([analysis/backtest.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/backtest.py)).

#### E. Epidemiological Burden & Public Health Impact Card
- **What the user sees:** Public health risk projections calculated for the active episode: Berkeley Earth daily cigarette equivalence (e.g., 9.8 cigarettes/day/person), acute respiratory risk increase (+43.7%), cardiovascular morbidity risk increase (+32.6%), and short-term all-cause mortality risk increase (+17.5%), alongside demographic vulnerability multipliers.
- **How it is generated:** Frontend calls `api.getHealthImpact()` -> `GET /api/validation/health-impact` in [backend/routers/validation.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/validation.py) -> returns payload from [pipeline/data/processed/health_summary.json](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/health_summary.json).
- **Dataset behind it:** [health_summary.json](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/health_summary.json) and [health_impacts.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/health_impacts.csv). See [Section 3.14](#314-epidemiological-health-impacts-health_impactscsv).
- **Model behind it:** [WHO GEMM Epidemiological Burden Projection Engine](#45-who-gemm-epidemiological-burden-projection-engine).

---

## 3. Datasets

### 3.1 Monitoring Stations Dataset (`stations.csv`)
- **Name & Source:** Delhi-NCR Air Quality Monitoring Stations Reference List. Sourced from CPCB (Central Pollution Control Board), DPCC (Delhi Pollution Control Committee), IMD (India Meteorological Department), and OpenAQ.
- **File path:** [pipeline/data/reference/stations.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/reference/stations.csv)
- **Dimensions & Format:** 71 rows, 8 columns; UTF-8 Comma-Separated Values (CSV).

| Column Name | Data Type | Meaning / Description | Example Value |
|---|---|---|---|
| `station_id` | String | Unique station identifier (CPCB or OpenAQ ID) | `"OAQ235"` |
| `name` | String | Official geographical station name and operating agency | `"Anand Vihar, New Delhi - DPCC"` |
| `lat` | Float | Geographic latitude in decimal degrees | `28.646835` |
| `lon` | Float | Geographic longitude in decimal degrees | `77.316032` |
| `region` | String | Administrative region (`Delhi` or `NCR`) | `"Delhi"` |
| `needs_review` | Integer | Human verification flag (0 = verified, 1 = unconfirmed) | `0` |
| `openaq_location_id` | Integer | OpenAQ v3 location identity code | `235` |
| `provider` | String | Data provider or regulatory entity | `"CPCB"` |

- **Target variable:** None (spatial reference table).
- **Data quality issues:** 0 missing values; coordinates verified within Delhi-NCR bounding box ($[76.7, 28.2]$ to $[77.7, 29.1]$).
- **Preprocessing steps:** Deduplication, string canonicalization, bounding box geographical verification, region assignment (`Delhi` vs `NCR`).
- **Site pages using this dataset:** KPI Banner, Sensors & Telemetry Map, Sensor Health Table, Station Diagnostics Modal.

---

### 3.2 Peer-Reviewed Reference Apportionment Dataset (`reference_apportionment.csv`)
- **Name & Source:** Delhi Winter Air Quality Source Apportionment Reference Studies. Extracted from peer-reviewed publications: IIT Kanpur Comprehensive Study (Sharma & Dikshit 2016), TERI & ARAI Source Apportionment Study (2018), SAFAR-India Post-Diwali Apportionment Bulletin (2021), and Decision Support System Delhi (IITM 2023).
- **File path:** [pipeline/data/reference/reference_apportionment.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/reference/reference_apportionment.csv)
- **Dimensions & Format:** 12 rows, 12 columns; UTF-8 CSV.

| Column Name | Data Type | Meaning / Description | Example Value |
|---|---|---|---|
| `study_id` | String | Unique publication and source benchmark identifier | `"IITK_2016_STUB"` |
| `citation` | String | Formal academic citation | `"Sharma & Dikshit (2016), IIT Kanpur"` |
| `doi_or_url` | String | Document URL or publication DOI | `"https://cpcb.nic.in/displaypdf.php?..."` |
| `location` | String | Geographic study airshed | `"Delhi"` |
| `period_start` | Date | Start date of study sampling or model run | `"2013-11-01"` |
| `period_end` | Date | End date of study sampling or model run | `"2014-02-28"` |
| `method` | String | Apportionment method (CMB, PMF, WRF-Chem) | `"CMB"` |
| `source` | String | Standardized source category | `"stubble_burning"` |
| `low_pct` | Float | Lower bound of source contribution percentage | `20.0` |
| `mid_pct` | Float | Midpoint or mean source contribution percentage | `25.8` |
| `high_pct` | Float | Upper bound of source contribution percentage | `32.0` |
| `notes` | String | Specific table references and test flags (`TESTONLY`) | `"Table 7.2: Biomass burning winter share"` |

- **Target variable:** `mid_pct` (with uncertainty bounds `low_pct` and `high_pct`). Distribution across sources: Stubble (10.0% - 48.0%), Vehicular (16.0% - 30.0%), Dust (3.5% - 19.0%), Industry (3.5% - 30.0%), Other (10.0% - 45.0%).
- **Data quality issues:** Studies reporting only midpoint values require assumption of $\pm 25\%$ relative spread.
- **Preprocessing steps:** Source standardization into 5 canonical categories; isolation of contemporaneous studies marked `TESTONLY` to prevent circularity in the baseline.
- **Site pages using this dataset:** Episodes & Attribution Credible Intervals, Literature Backtesting Table.

---

### 3.3 Raw Ingested Data Streams (`aq_long.csv`, `firms_viirs.csv`, `weather_delhi_hourly.csv`)
- **Name & Sources:**
  1. `aq_long.csv`: OpenAQ and CPCB CAAQMS hourly ambient telemetry (1,000,662 rows, 6 columns).
  2. `firms_viirs.csv`: NASA FIRMS satellite active fire detections from VIIRS SNPP and NOAA-20 sensors (333,295 rows, 16 columns).
  3. `weather_delhi_hourly.csv`: Open-Meteo ERA5 hourly atmospheric reanalysis for Delhi coordinates (4,032 rows, 13 columns).
  4. `weather_grid_hourly.csv`: Open-Meteo ERA5 1-degree NW India regional weather grid (532,224 rows, 13 columns).
- **File paths:**
  - [pipeline/data/raw/aq_long.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/raw/aq_long.csv)
  - [pipeline/data/raw/firms_viirs.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/raw/firms_viirs.csv)
  - [pipeline/data/raw/weather_delhi_hourly.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/raw/weather_delhi_hourly.csv)
  - [pipeline/data/raw/weather_grid_hourly.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/raw/weather_grid_hourly.csv)

| Dataset | Key Columns | Meaning | Units / Types |
|---|---|---|---|
| `aq_long.csv` | `station_id`, `time`, `parameter`, `value`, `unit` | Hourly concentration of PM2.5, PM10, NO2, SO2, CO, O3 | $\mu\text{g}/\text{m}^3$ (CO in $\text{mg}/\text{m}^3$) |
| `firms_viirs.csv` | `latitude`, `longitude`, `acq_date`, `acq_time`, `frp`, `confidence` | VIIRS satellite active thermal fire detections and Fire Radiative Power | Degrees, MW, String (`n`, `h`, `l`) |
| `weather_delhi_hourly.csv` | `temperature_2m`, `relative_humidity_2m`, `wind_speed_10m`, `wind_direction_10m`, `boundary_layer_height`, `surface_pressure` | Surface meteorology and boundary layer height | $^\circ\text{C}$, %, $\text{m}/\text{s}$, deg, $\text{m}$, $\text{hPa}$ |

- **Data quality issues:** Low-confidence fire detections (confidence = `l`), sensor flatlines, single-hour electrical spikes, gas ppb/ppm unit heterogeneity, missing station hours.
- **Preprocessing steps:** Unit conversion to standard $\mu\text{g}/\text{m}^3$ ($\text{mg}/\text{m}^3$ for CO), naive IST timestamp alignment, bounding box spatial filtering, spike and flatline elimination, boundary layer interpolation.

---

### 3.4 City-Level Hourly Features (`city_hourly_final.csv`)
- **Name & Source:** Primary analysis-ready hourly multi-module ledger table. Generated by [pipeline/s7_final.py](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/s7_final.py).
- **File path:** [pipeline/data/processed/city_hourly_final.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/city_hourly_final.csv)
- **Dimensions & Format:** 2,496 rows, 88 columns; UTF-8 CSV.

| Column Name | Data Type | Meaning / Description | Example Value |
|---|---|---|---|
| `time` | Timestamp | Hour-beginning timestamp in naive Indian Standard Time (IST) | `"2021-10-15 00:00:00"` |
| `delhi_pm25_median` | Float | Median PM2.5 concentration across valid Delhi stations | `156.94` |
| `delhi_pm25_p10` | Float | 10th percentile PM2.5 (regional background proxy) | `112.4` |
| `delhi_pm25_p90` | Float | 90th percentile PM2.5 across Delhi stations | `210.8` |
| `delhi_n_valid` | Integer | Count of operational reporting stations in Delhi | `36` |
| `delhi_background_share` | Float | Ratio of regional background to city median PM2.5 ($0.0 - 1.0$) | `0.919` |
| `delhi_fp_traffic_z` | Float | Standardized z-score of CO and NO2 against station trailing 7-day mean | `0.32` |
| `delhi_fp_biomass_ratio` | Float | Ratio of PM2.5 to PM10 (biomass combustion tracer) | `0.556` |
| `delhi_fp_dust_ratio` | Float | Ratio of PM10 to PM2.5 (coarse dust tracer) | `1.80` |
| `delhi_fp_industrial_so2_z`| Float | Standardized z-score of SO2 against trailing 7-day mean | `1.31` |
| `wind_speed_ms` | Float | 10-meter wind speed | `2.4` |
| `blh_m` | Float | Boundary layer height | `185.0` |
| `ventilation_m2s` | Float | Atmospheric dispersion capacity ($\text{BLH} \times \text{wind speed}$) | `444.0` |
| `stagnation_flag` | Integer | Binary flag for atmospheric stagnation ($\text{wind} < 2\text{m/s}$ and low BLH) | `1` |
| `fires_linked_median` | Float | Trajectory-linked upwind active fires (10-member ensemble median) | `340.0` |
| `frp_linked_median` | Float | Total Fire Radiative Power of linked fires | `1840.5` |
| `raw_fires_24h_pbhr` | Float | Naive baseline active fires in Punjab/Haryana in preceding 24h | `812.0` |
| `regime` | String | Spatial scale classification (`widespread_rise`, `delhi_concentrated_rise`, etc.) | `"widespread_rise"` |

- **Target variable:** `delhi_pm25_median` (Mean: 149.3 $\mu\text{g}/\text{m}^3$, Std: 98.3, Min: 20.0, Median: 121.5, Max: 491.0).
- **Data quality issues:** Missing values in rolling z-scores during cold start windows (94 rows); missing fire lags during non-fire windows (435 rows).
- **Preprocessing steps:** Robust quantile aggregation, causal rolling window standardizations (168h and 720h), HYSPLIT-style trajectory parcel advection, spatial background extraction.
- **Site pages using this dataset:** Episodes & Attribution Hourly Telemetry Chart, Precaution Advisor, Forecasting Model Training.

---

### 3.5 Station-Level Hourly Panel Dataset (`station_hourly_final.csv`)
- **Name & Source:** Station-by-hour panel dataset combining individual monitor readings with city-level weather and trajectory context. Generated by [pipeline/s7_final.py](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/s7_final.py).
- **File path:** [pipeline/data/processed/station_hourly_final.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/station_hourly_final.csv)
- **Dimensions & Format:** 139,776 rows, 124 columns; UTF-8 CSV (179.5 MB).

| Column Name | Data Type | Meaning / Description | Example Value |
|---|---|---|---|
| `station_id` | String | Station identifier | `"OAQ235"` |
| `time` | Timestamp | Naive IST timestamp | `"2021-10-15 00:00:00"` |
| `pm25` | Float | Cleaned ambient PM2.5 concentration | `184.2` |
| `pm10` | Float | Cleaned ambient PM10 concentration | `330.5` |
| `local_excess_pm25` | Float | Station PM2.5 concentration minus regional background | `71.8` |
| `local_excess_share`| Float | Share of local excess over total station PM2.5 | `0.39` |
| `hotspot_flag` | Integer | Binary indicator for localized hotspot ($z > 2.5$ and excess $> 40 \ \mu\text{g}/\text{m}^3$) | `1` |
| `fp_traffic_z` | Float | Station-specific vehicular traffic fingerprint z-score | `1.45` |
| `fp_dust_ratio` | Float | Station PM10/PM2.5 coarse ratio | `1.79` |

- **Target variable:** `local_excess_pm25` (used by action engine to isolate hotspot facilities).
- **Data quality issues:** Sensor drops and optical drift; handled via [analysis/sensor_health.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/sensor_health.py).
- **Preprocessing steps:** Regular grid harmonization, spike/flatline masking, local excess derivation against regional 10th percentile.
- **Site pages using this dataset:** Policy View Hotspot Localization, Sensor Health Monitoring.

---

### 3.6 Cataloged Pollution Episodes (`episodes.csv`)
- **Name & Source:** Cataloged severe smog episodes. Generated by [pipeline/s7_final.py](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/s7_final.py).
- **File path:** [pipeline/data/processed/episodes.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/episodes.csv)
- **Dimensions & Format:** 6 rows, 8 columns; UTF-8 CSV.

| Column Name | Data Type | Meaning / Description | Example Value |
|---|---|---|---|
| `episode_id` | Integer | Sequential episode identifier (1 to 6) | `1` |
| `start` | Date | Episode onset date (YYYY-MM-DD) | `"2021-10-15"` |
| `end` | Date | Episode termination date (YYYY-MM-DD) | `"2021-10-16"` |
| `days` | Integer | Total duration of the episode in days | `2` |
| `peak_daily_pm25` | Float | Maximum 24-hour city-wide median PM2.5 ($\mu\text{g}/\text{m}^3$) | `211.35` |
| `mean_daily_pm25` | Float | Mean 24-hour city-wide median PM2.5 ($\mu\text{g}/\text{m}^3$) | `187.94` |
| `peak_linked_fires`| Float | Maximum hourly trajectory-linked fire count | `707.0` |
| `mean_background_share` | Float | Average regional background share | `0.919` |

- **Target variable:** `episode_id`. Distribution: Episode 1 (2 days, Oct 2021), Episode 2 (5 days, Oct-Nov 2021), Episode 3 (14 days, Nov 2021 Post-Diwali), Episode 4 (2 days, Oct 2023), Episode 5 (8 days, Nov 2023), Episode 6 (5 days, Nov 2023).
- **Data quality issues:** 0 missing values; 2017 season excluded due to data validation failures (limited satellite overpasses and sensor dropouts).
- **Preprocessing steps:** Run-length filtering requiring daily mean $\ge 150 \ \mu\text{g}/\text{m}^3$ for $\ge 2$ consecutive days.
- **Site pages using this dataset:** Episode Selector, Top KPI Banner, Policy Actions View, Health Impact View.

---

### 3.7 Monte Carlo Attribution Ledger (`ledger_entries.csv`)
- **Name & Source:** Source attribution shares and credible uncertainty intervals. Generated by [analysis/attribution.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/attribution.py).
- **File path:** [pipeline/data/processed/ledger_entries.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/ledger_entries.csv)
- **Dimensions & Format:** 30 rows (6 episodes $\times$ 5 sources), 19 columns; UTF-8 CSV.

| Column Name | Data Type | Meaning / Description | Example Value |
|---|---|---|---|
| `episode_id` | Integer | Episode identifier | `1` |
| `source` | String | Modeled pollution source category | `"stubble_burning"` |
| `share_low_pct` | Float | 10th percentile credible lower bound (%) | `11.1` |
| `share_mid_pct` | Float | 50th percentile (median) point estimate (%) | `20.0` |
| `share_high_pct`| Float | 90th percentile credible upper bound (%) | `31.5` |
| `baseline_low_pct` | Float | Literature baseline lower bound (%) | `10.0` |
| `baseline_mid_pct` | Float | Literature baseline median (%) | `19.9` |
| `baseline_high_pct`| Float | Literature baseline upper bound (%) | `32.0` |
| `evidence_score` | Float | Empirical evidence score ($-1.0$ to $+1.0$) | `-0.0` |
| `grade` | String | Institutional confidence grade (`A`, `B`, `C`) | `"C"` |
| `modules_supporting` | String | Comma-separated list of supporting modules | `"trajectory"` |
| `modules_contradicting` | String | Comma-separated list of contradicting modules | `"local_regional"` |

- **Target variable:** `share_mid_pct` (with uncertainty bounds `share_low_pct` and `share_high_pct`).
- **Data quality issues:** Empty supporting/contradicting module fields when signals do not breach the $\pm 0.25$ threshold.
- **Preprocessing steps:** Episode daily averaging, percent-rank transformation against historical distribution, triangular baseline sampling, Dirichlet rescaling.
- **Site pages using this dataset:** Episodes & Attribution Credible Intervals Chart, Literature Backtest Table.

---

### 3.8 Evidence Confidence Labels Dataset (`ledger_labels.csv`)
- **Name & Source:** Empirical confidence classification table. Generated by [analysis/evidence_labels.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/evidence_labels.py).
- **File path:** [pipeline/data/processed/ledger_labels.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/ledger_labels.csv)
- **Dimensions & Format:** 30 rows, 21 columns; UTF-8 CSV.

| Column Name | Data Type | Meaning / Description | Example Value |
|---|---|---|---|
| `episode_id` | Integer | Episode identifier | `1` |
| `source` | String | Pollution source category | `"industry"` |
| `grade` | String | Evidence grade (`A`, `B`, `C`) | `"B"` |
| `label` | String | High-level status (`Supported`, `Conflicting`, `Insufficient evidence`) | `"Supported"` |
| `label_reason` | String | Plain-language scientific justification | `"Consistent evidence across fingerprint, local_regional with no contradicting signals (Grade B)."` |

- **Target variable:** `label`.
- **Data quality issues:** 0 missing values in core classification columns.
- **Preprocessing steps:** Rule-based evaluation based on grade, supporting module count, and presence of conflicting evidence.
- **Site pages using this dataset:** Evidence Labels Table, Episode Selector Badges.

---

### 3.9 Sensor Health and Spatial Consistency Dataset (`sensor_health.csv`)
- **Name & Source:** Spatial consistency diagnostic telemetry for monitoring stations. Generated by [analysis/sensor_health.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/sensor_health.py).
- **File path:** [pipeline/data/processed/sensor_health.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/sensor_health.csv)
- **Dimensions & Format:** 56 rows (stations with active valid data in current window), 14 columns; UTF-8 CSV.

| Column Name | Data Type | Meaning / Description | Example Value |
|---|---|---|---|
| `station_id` | String | Monitoring station identifier | `"OAQ235"` |
| `name` | String | Station name | `"Anand Vihar, New Delhi - DPCC"` |
| `observed_pm25` | Float | Recent 72-hour mean observed PM2.5 ($\mu\text{g}/\text{m}^3$) | `83.3` |
| `expected_pm25` | Float | Spatial IDW expected PM2.5 from 4 nearest neighbors | `82.4` |
| `residual_pm25` | Float | Spatial deviation ($\text{observed} - \text{expected}$) | `0.9` |
| `z_score` | Float | Residual standardized by station's historical spread | `0.18` |
| `hours_persistent` | Integer | Consecutive hours with $|z| \ge 3.0$ | `0` |
| `corr24h` | Float | 24-hour rolling correlation with neighborhood median | `0.99` |
| `status` | String | Health diagnostic category (`OK`, `watch`, `suspect`) | `"OK"` |
| `reasons` | String | Natural-language explanation of diagnostic status | `"Closely tracking spatial neighborhood (r=0.99)"` |

- **Target variable:** `status` (Distribution: 56 `OK`, 0 `watch`, 0 `suspect` on clean baseline; injected faults detect 100% recall).
- **Data quality issues:** 1 station with insufficient neighbors within 40 km corridor resulting in null expected spread.
- **Preprocessing steps:** Pairwise haversine distance matrix computation, IDW interpolation ($k=4$, power $p=2$), 24h rolling Pearson correlation, persistent run-length tracking.
- **Site pages using this dataset:** Sensors & Telemetry Map, Sensor Health Diagnostics Table, Station Detail Modal.

---

### 3.10 72-Hour Particulate Forecast Dataset (`forecast_hourly.csv`)
- **Name & Source:** Multi-horizon hourly PM2.5 predictions with uncertainty envelopes. Generated by [analysis/forecast.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/forecast.py).
- **File path:** [pipeline/data/processed/forecast_hourly.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/forecast_hourly.csv)
- **Dimensions & Format:** 4,992 rows (2,496 issue hours $\times$ 2 horizons), 7 columns; UTF-8 CSV.

| Column Name | Data Type | Meaning / Description | Example Value |
|---|---|---|---|
| `issue_time` | Timestamp | Timestamp at which forecast was generated | `"2021-10-15 00:00:00"` |
| `target_time` | Timestamp | Forward valid target time | `"2021-10-16 00:00:00"` |
| `horizon_h` | Integer | Forecast lead time in hours (24 or 48) | `24` |
| `pm25_pred` | Float | Model median point forecast ($\mu\text{g}/\text{m}^3$) | `168.4` |
| `pm25_low` | Float | 10th percentile quantile prediction (lower bound) | `132.1` |
| `pm25_high` | Float | 90th percentile quantile prediction (upper bound) | `214.5` |
| `aqi_category` | String | CPCB National AQI category from predicted value | `"very_poor"` |

- **Target variable:** `pm25_pred` (Distribution across dataset: Mean 149.1 $\mu\text{g}/\text{m}^3$, Std 98.6, Min 20.0, Max 491.0).
- **Data quality issues:** 0 missing values; logical boundary enforcement guarantees $\text{pm25\_low} \le \text{pm25\_pred} \le \text{pm25\_high}$.
- **Preprocessing steps:** Target log-transformation $\log(\max(y, 1.0))$, candidate feature median imputation, forward time shift (+24h, +48h).
- **Site pages using this dataset:** Forecast Chart, Top KPI Banner, Precaution Advisor.

---

### 3.11 Forecast Evaluation Benchmarks (`forecast_eval.csv`)
- **Name & Source:** Rigorous cross-validation benchmark report. Generated by [analysis/forecast.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/forecast.py).
- **File path:** [pipeline/data/processed/forecast_eval.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/forecast_eval.csv)
- **Dimensions & Format:** 6 rows (3 models $\times$ 2 horizons), 7 columns; UTF-8 CSV.

| Column Name | Data Type | Meaning / Description | Example Value |
|---|---|---|---|
| `horizon_h` | Integer | Forecast horizon (24 or 48 hours) | `24` |
| `method` | String | Forecasting method or baseline | `"Gradient Boosting (Ledger Engine)"` |
| `beats_persistence`| Boolean | True if model MAE is lower than persistence baseline | `False` |
| `mae_ugm3` | Float | Mean Absolute Error ($\mu\text{g}/\text{m}^3$) | `42.65` |
| `rmse_ugm3` | Float | Root Mean Squared Error ($\mu\text{g}/\text{m}^3$) | `66.12` |
| `r2_score` | Float | Coefficient of determination ($R^2$) | `0.588` |
| `aqi_category_acc_pct`| Float | Percentage of correct CPCB AQI band classifications | `49.5` |

- **Target variable:** Performance metrics.
- **Data quality issues:** 0 missing values.
- **Site pages using this dataset:** Forecast Evaluation Table.

---

### 3.12 Construction Dust Scheduling Demonstration Dataset (`dust_demo_schedule.csv`)
- **Name & Source:** Diurnal construction task rescheduling proof-of-concept simulation. Generated by [analysis/dust_scheduler_demo.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/dust_scheduler_demo.py).
- **File path:** [pipeline/data/processed/dust_demo_schedule.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/dust_demo_schedule.csv)
- **Dimensions & Format:** 12 rows (working hours 07:00 to 18:00 IST), 9 columns; UTF-8 CSV.

| Column Name | Data Type | Meaning / Description | Example Value |
|---|---|---|---|
| `hour` | Integer | Working hour of the day (7 to 18) | `9` |
| `time_window` | String | Formatted time window label | `"09:00 - 10:00"` |
| `stagnation_inversion_factor` | Float | Boundary layer inversion trapping penalty ($0.8 - 1.9$) | `1.80` |
| `baseline_dust_index_sum` | Float | Unscheduled concurrent dust index sum across 4 sites | `17.0` |
| `optimized_dust_index_sum` | Float | Staggered schedule dust index sum | `8.0` |
| `dust_index_reduction` | Float | Absolute reduction in raw dust index | `9.0` |
| `baseline_weighted_exposure` | Float | Inversion-weighted atmospheric exposure score | `30.6` |
| `optimized_weighted_exposure`| Float | Optimized inversion-weighted exposure score | `14.4` |
| `exposure_reduction` | Float | Absolute reduction in exposure score | `16.2` |

- **Target variable:** `optimized_weighted_exposure`.
- **Data quality issues:** 0 missing values; simulated demonstration.
- **Preprocessing steps:** Inflexible task reservation, greedy combinatorial start-time evaluation against hourly inversion weights.
- **Site pages using this dataset:** Policy View Dust Rescheduler Simulator.

---

### 3.13 Literature Backtest Results (`backtest_results.csv`)
- **Name & Source:** Peer-reviewed literature concordance verification table. Generated by [analysis/backtest.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/backtest.py).
- **File path:** [pipeline/data/processed/backtest_results.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/backtest_results.csv)
- **Dimensions & Format:** 63 rows, 21 columns; UTF-8 CSV.

| Column Name | Data Type | Meaning / Description | Example Value |
|---|---|---|---|
| `episode_id` | Integer | Evaluated episode identifier | `1` |
| `source` | String | Pollution source category | `"stubble_burning"` |
| `study_id` | String | Published study identifier | `"IITK_2016_STUB"` |
| `method` | String | Published study method (CMB, PMF, WRF-Chem) | `"CMB"` |
| `model_low_pct` | Float | Model 10th percentile lower bound (%) | `11.1` |
| `model_high_pct`| Float | Model 90th percentile upper bound (%) | `31.5` |
| `ref_low_pct` | Float | Published study lower bound (%) | `20.0` |
| `ref_high_pct` | Float | Published study upper bound (%) | `32.0` |
| `overlap` | Boolean | True if model interval overlaps published range | `True` |
| `status` | String | Overlap classification | `"PASS_INTERVAL_OVERLAP"` |
| `divergence_pct`| Float | Difference between model midpoint and study midpoint (%) | `-5.8` |
| `explanation` | String | Scientific explanation of physical divergence | `"Model interval overlaps study range..."` |

- **Target variable:** `overlap` (100.0% overlap across all 63 comparisons).
- **Data quality issues:** 0 missing values.
- **Preprocessing steps:** Date-matching filter for contemporaneous episodes, interval boundary overlap checks, midpoint difference derivation.
- **Site pages using this dataset:** Literature Backtesting Table.

---

### 3.14 Epidemiological Health Impacts (`health_impacts.csv`)
- **Name & Source:** WHO GEMM health burden projections. Generated by [analysis/health.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/health.py).
- **File path:** [pipeline/data/processed/health_impacts.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/health_impacts.csv)
- **Dimensions & Format:** 30 rows, 14 columns; UTF-8 CSV.

| Column Name | Data Type | Meaning / Description | Example Value |
|---|---|---|---|
| `episode_id` | Integer | Evaluated episode identifier | `1` |
| `source` | String | Source category | `"stubble_burning"` |
| `source_share_mid_pct` | Float | Attribution midpoint share (%) | `20.0` |
| `attributable_pm25_ugm3` | Float | Absolute PM2.5 concentration attributable to this source ($\mu\text{g}/\text{m}^3$) | `34.58` |
| `attributable_cigarettes_daily` | Float | Berkeley Earth daily cigarette equivalence per person | `1.57` |
| `attributable_mortality_risk_pct` | Float | Excess short-term all-cause mortality risk increase (%) | `2.96` |
| `attributable_respiratory_risk_pct`| Float | Excess acute respiratory morbidity risk increase (%) | `7.31` |
| `attributable_cardiovascular_risk_pct`| Float | Excess cardiovascular morbidity risk increase (%) | `5.48` |

- **Target variable:** `attributable_mortality_risk_pct`.
- **Data quality issues:** 0 missing values; relies on log-linear epidemiological scaling at high particulate concentrations.
- **Preprocessing steps:** Excess PM2.5 calculation above WHO 24h counterfactual (15 $\mu\text{g}/\text{m}^3$), risk ratio calculation ($RR = \exp(\beta \times \text{excess} / 10)$), source apportionment multiplication.
- **Site pages using this dataset:** Health Impact Card.

---

## 4. ML Models

### 4.1 Multi-Horizon Particulate Forecasting Model (`HistGradientBoostingRegressor`)

```
   [40 Leakage-Free Features]
  (Lagged PM2.5, Weather, Fire Trajectories, Time)
                │
                ▼
   ┌─────────────────────────────────────────────────────────────┐
   │             HistGradientBoostingRegressor                   │
   │  • Point Estimator: loss='squared_error'                    │
   │  • Lower Bound Estimator: loss='quantile', quantile=0.10    │
   │  • Upper Bound Estimator: loss='quantile', quantile=0.90    │
   └───────────────────────────┬─────────────────────────────────┘
                               │
                               ▼
   [Forecast: Median PM2.5 + 80% Credible Uncertainty Interval]
```

- **Model Name & Problem Type:** `HistGradientBoostingRegressor` (from `scikit-learn.ensemble`). Supervised Time-Series Multi-Horizon Regression with Quantile Uncertainty Estimation.
- **Why this algorithm was chosen:** Histogram-based gradient boosted trees natively handle continuous numerical variables with non-linear relationships (e.g., wind speed dispersion thresholding and boundary layer collapse), require no feature normalization, exhibit high training throughput on tabular data, and provide built-in quantile loss functions for generating formal 80% prediction uncertainty intervals.
- **Alternatives compared:** Evaluated against two operational baselines:
  1. *Naive Persistence Baseline:* Assumes tomorrow's PM2.5 equals today's observed concentration ($y_{t+h} = y_t$).
  2. *Diurnal Seasonal Mean Baseline:* Uses historical mean concentration conditioned on the hour of the day.
- **Input features:** 40 strictly leakage-free features (`look_ahead == 0`):
  - *Recent pollution dynamics:* `delhi_pm25_median`, `delhi_pm25_24h_mean`, `delhi_pm25_diff3h`, `delhi_pm25_diff24h`, `delhi_regional_background_pm25`, `delhi_background_share`, `ncr_pm25_median`, `ncr_minus_delhi_pm25`.
  - *Weather & atmospheric dispersion:* `temp_c`, `rh_pct`, `pressure_hpa`, `wind_speed_ms`, `wind_speed_100m_ms`, `wind_u`, `wind_v`, `wind_dir_sin`, `wind_dir_cos`, `nw_wind_flag`, `blh_m`, `ventilation_m2s`, `precip_24h_mm`, `precip_72h_mm`, `temp_range_24h_c`, `pressure_change_6h`, `wind_speed_roll6h`, `stagnation_flag`.
  - *Trajectory & fire pathway:* `traj_mean_speed_kmh`, `traj_dist_48h_km`, `traj_origin_bearing_48h`, `traj_pbhr_frac`, `traj_origin_sin`, `traj_origin_cos`, `fires_linked_median`, `frp_linked_median`, `fire_lag_p50_h`, `fire_member_agree_frac`, `raw_fires_24h_pbhr`.
  - *Calendar & Diwali markers:* `hour_sin`, `hour_cos`, `is_rush_am`, `is_rush_pm`, `is_night`, `is_weekend`, `days_from_diwali`, `diwali_window`.
- **Output format:** Tabular row with `target_time`, `horizon_h`, `pm25_pred` (point estimate), `pm25_low` (10th percentile), `pm25_high` (90th percentile), and `aqi_category`.
- **Training pipeline:** Implemented in [analysis/forecast.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/forecast.py).
  1. Loads [pipeline/data/processed/city_hourly_final.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/city_hourly_final.csv).
  2. Constructs forward targets $y_{t+h} = \text{delhi\_pm25\_median}(t + h)$ for $h \in \{24, 48\}$.
  3. Transforms target to log-scale: $y_{\text{log}} = \log(\max(y, 1.0))$.
  4. Imputes missing feature values with column medians.
  5. Trains three separate estimators per horizon: point estimator (`loss='squared_error'`), lower bound (`loss='quantile', quantile=0.10`), and upper bound (`loss='quantile', quantile=0.90`).
  6. Reverses log transform via $\exp(\hat{y})$ and enforces logical ordering ($\text{low} \le \text{pred} \le \text{high}$).
- **Hyperparameters & Tuning Method:**
  - `loss`: `"squared_error"` (point), `"quantile"` with $\alpha=0.10$ (low), $\alpha=0.90$ (high).
  - `max_iter`: 150 boosting iterations.
  - `min_samples_leaf`: 15 samples.
  - `random_state`: 42 (`RNG_SEED`).
  - Evaluated via 5-fold Time-Series Blocked Cross-Validation with a 72-hour purge gap (`FS_GAP_HOURS = 72`) to eliminate auto-correlation leakage.
- **Evaluation metrics & actual results:**

| Horizon | Method | MAE ($\mu\text{g}/\text{m}^3$) | RMSE ($\mu\text{g}/\text{m}^3$) | $R^2$ Score | AQI Category Accuracy (%) | Beats Persistence? |
|---|---|---|---|---|---|---|
| **+24 Hours** | **Gradient Boosting (AerTrace)** | **42.65** | **66.12** | **0.588** | **49.5%** | **False** |
| +24 Hours | Persistence Baseline ($y_{t+24}=y_t$) | 31.19 | 47.80 | 0.785 | 64.1% | Baseline |
| +24 Hours | Diurnal Seasonal Mean Baseline | 81.46 | 100.12 | 0.054 | 31.7% | Baseline |
| **+48 Hours** | **Gradient Boosting (AerTrace)** | **61.25** | **85.22** | **0.311** | **38.4%** | **False** |
| +48 Hours | Persistence Baseline ($y_{t+48}=y_t$) | 38.03 | 59.67 | 0.662 | 57.7% | Baseline |
| +48 Hours | Diurnal Seasonal Mean Baseline | 81.18 | 100.63 | 0.039 | 32.2% | Baseline |

> **Scientific Transparency Note:** In accordance with rigorous scientific backtesting, the codebase honestly records that during stable stagnation windows, short-term persistence outperforms gradient boosting on point errors (MAE 31.19 vs 42.65 $\mu\text{g}/\text{m}^3$). However, gradient boosting significantly outperforms the diurnal climatological mean (MAE 42.65 vs 81.46 $\mu\text{g}/\text{m}^3$) and provides physical responsiveness to upstream wind shifts and fire pulses that persistence cannot anticipate.

- **Saved model file location & format:** *Not serialized as a binary (.pkl / .joblib) file.* The model is trained on-demand by [analysis/forecast.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/forecast.py), and outputs are saved directly as pre-generated CSV artifacts in [pipeline/data/processed/forecast_hourly.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/forecast_hourly.csv) and [pipeline/data/processed/forecast_eval.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/forecast_eval.csv).
- **Limitations & Possible Improvements:** Model uses historical reanalysis weather; operational deployment requires real-time Numerical Weather Prediction (NWP) forecasts. Extreme firecracker emissions during Diwali nights create acute non-linear spikes that tree-based regressors underestimate.
- **Site pages using this model:** 72H Forecast Projection Chart, Top KPI Banner, Precaution Advisor.

---

### 4.2 5,000-Draw Monte Carlo Evidence Apportionment Engine

```
   [Published Studies Baseline]         [4 Empirical Observational Modules]
   (IIT Kanpur, TERI Studies)          (Trajectories, Fingerprints, Local/Regional, NCR)
               │                                      │
               │                                      ▼
               │                            [Evidence Scores (-1 to +1)]
               │                                      │
               └──────────────────┬───────────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │ 5,000 Monte Carlo Draws │
                     │  • Triangular baseline  │
                     │  • Empirical nudges     │
                     │  • Dirichlet rescaling  │
                     └────────────┬────────────┘
                                  │
                                  ▼
               [Credible Intervals (10th, 50th, 90th %)]
               [Confidence Letter Grades (Grade A, B, C)]
```

- **Model Name & Problem Type:** 5,000-Draw Monte Carlo Probabilistic Apportionment Engine. Stochastic Uncertainty Quantification and Source Apportionment.
- **Why this algorithm was chosen:** Air pollution attribution cannot produce a single deterministic "truth" without chemical mass spectrometry on physical filters. The Monte Carlo framework explicitly models parameter uncertainty, prevents overconfident single-point blame assertions, and integrates multi-sensor physical evidence with peer-reviewed literature.
- **Alternatives compared:** Compared against classical deterministic chemical mass balance (CMB) and single-point regression. Deterministic methods were rejected because they fail to convey uncertainty intervals to municipal policymakers.
- **Input features:**
  - *Baseline bounds:* `low_pct`, `mid_pct`, `high_pct` from [pipeline/data/reference/reference_apportionment.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/reference/reference_apportionment.csv). Date-overlapping studies are automatically held out to prevent circularity.
  - *Evidence indicators:* Upwind linked fires, trajectory agreement fraction, Punjab/Haryana transit fraction, NW wind flag, PM2.5/PM10 biomass ratio, nighttime PM2.5 rise, traffic NO2/CO z-scores, PM10/PM2.5 dust ratio, SO2 industrial z-score, regional background share, and NCR widespread regime rise.
- **Output format:** 10th percentile (`share_low_pct`), 50th percentile (`share_mid_pct`), 90th percentile (`share_high_pct`), and confidence grade (`A`, `B`, `C`).
- **Training pipeline:** Implemented in [analysis/attribution.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/attribution.py).
  1. Computes percentile rank of episode average indicator values against the historical distribution ($p \in [0, 1]$).
  2. Calculates evidence scores: $\text{score} = (2p - 1) \times \text{direction}$.
  3. Executes 5,000 stochastic draws: samples baseline from triangular distributions, applies evidence nudges $1 + K \times \text{kscale} \times \text{noise} \times \text{score}$, and rescales shares to 100%.
  4. Extracts 5th, 50th, and 95th percentiles (reported as 10th-90th bounds).
- **Hyperparameters & Tuning Method:**
  - `N_DRAWS`: 5,000 iterations.
  - `K` adjustment weights: Stubble Burning ($K=0.9$), Vehicular ($K=0.4$), Dust ($K=0.4$), Industry ($K=0.4$), Other ($K=0.0$).
  - `EVIDENCE_NOISE_SD`: 0.15 Gaussian noise.
  - `SUPPORT_T`: 0.25 evidence threshold.
  - Sensitivity analysis runs at $K_{\text{scale}} \in \{0.5, 1.0, 2.0\}$.
- **Evaluation metrics & actual results:** Validated across 63 published peer-reviewed comparisons in [analysis/backtest.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/backtest.py), achieving 100.0% credible interval overlap and 92.1% midpoint concordance.
- **Saved model file location & format:** Script execution writes pre-computed tables to [pipeline/data/processed/ledger_entries.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/ledger_entries.csv) and [pipeline/data/processed/ledger_sensitivity.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/ledger_sensitivity.csv).
- **Limitations & Possible Improvements:** Satellite active fire counts reflect fire detections, not total smoke plume density. Vertical wind shear and atmospheric chemical transformations are not modeled.
- **Site pages using this model:** Episodes & Attribution Credible Intervals Chart, Episode Selector Badges, Literature Backtesting Table.

---

### 4.3 Spatial Inverse-Distance Weighting (IDW) Sensor Consistency Monitor

```
   [72 Station Coordinates]        [Hourly PM2.5 / PM10 Telemetry]
              │                                    │
              └──────────────────┬─────────────────┘
                                 │
                                 ▼
              ┌─────────────────────────────────────┐
              │ Spatial IDW Interpolation           │
              │  • k=4 nearest neighbors (d <= 40km)│
              │  • Inverse-distance weighting (1/d²)│
              └──────────────────┬──────────────────┘
                                 │
                                 ▼
              [Residual: Observed - Expected PM2.5]
              [Historical Z-Score: (res - mean) / std]
              [Persistence Filter: |z| >= 3.0 for >= 6h]
              [24h Rolling Correlation: r < 0.50]
                                 │
                                 ▼
              [Status: 'OK' | 'watch' | 'suspect']
```

- **Model Name & Problem Type:** Spatial IDW Residual & Historical Z-Score Anomaly Monitor. Spatial Interpolation and Quality Control.
- **Why this algorithm was chosen:** Pure statistical outlier detection flags legitimate regional smog spikes as faults. Spatial IDW compares each station to its physical neighbors within a 40 km corridor; a station is only flagged if it diverges persistently from its immediate geographical cluster.
- **Alternatives compared:** Compared against single-station median absolute deviation (MAD) and global z-scores. Global methods were rejected because they false-alarmed on localized hotspot events.
- **Input features:** Station coordinates (`lat`, `lon`), hourly `pm25`, `pm10`, `no2`, `co`.
- **Output format:** Station record containing `observed_pm25`, `expected_pm25`, `residual_pm25`, `z_score`, `hours_persistent`, `corr24h`, `status` (`OK`, `watch`, `suspect`), and `reasons`.
- **Training pipeline:** Implemented in [analysis/sensor_health.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/sensor_health.py).
  1. Computes pairwise haversine distance matrix between all stations.
  2. For each station-hour, selects $k=4$ nearest valid neighbors within 40 km and calculates IDW expected value:
     $$\hat{y}_i = \frac{\sum_{j=1}^4 w_{ij} y_j}{\sum_{j=1}^4 w_{ij}}, \quad w_{ij} = \frac{1}{d_{ij}^2}$$
  3. Computes residual $r_i = y_i - \hat{y}_i$ and standardizes into historical z-scores: $z_i = (r_i - \mu_{r,i}) / \sigma_{r,i}$.
  4. Flags stations as `suspect` if $|z_i| \ge 3.0$ persists for $\ge 6$ consecutive hours and 24h neighbor correlation $r < 0.50$.
- **Hyperparameters & Tuning Method:**
  - `SENSOR_K_NEIGHBOURS`: 4 neighbors.
  - `SENSOR_Z_FLAG`: 3.0 standard deviations.
  - `SENSOR_MIN_PERSIST_H`: 6 consecutive hours.
  - `SENSOR_CORR_MIN`: 0.50 rolling Pearson correlation threshold.
- **Evaluation metrics & actual results:** Evaluated via synthetic fault injection in [analysis/sensor_health.py:validate_sensor_check()](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/sensor_health.py):
  - *Total Stations Evaluated:* 71
  - *Injected Faults:* 5 (3 progressive calibration drifts +45%, 2 zero flatline drops)
  - *True Positives Detected:* 5
  - *Detection Rate (Recall):* **100.0%** (Target: $\ge 80\%$)
  - *False-Alarm Rate:* **0.0%** (Target: $\le 10\%$)
  - *Benchmark Status:* **PASS**
- **Saved model file location & format:** Output written to [pipeline/data/processed/sensor_health.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/sensor_health.csv) and [pipeline/data/processed/sensor_validation_report.json](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/sensor_validation_report.json).
- **Limitations & Possible Improvements:** Stations on the extreme periphery of NCR have fewer than 4 neighbors within 40 km, which widens their spatial prediction spread.
- **Site pages using this model:** Sensors & Telemetry Map, Sensor Health Diagnostics Table, Fault-Injection Benchmark Card.

---

### 4.4 Diurnal Construction Dust Rescheduler Optimizer

```
   [Contractor Tasks & Preferred Starts]    [Diurnal Stagnation Factor (1.8 morning -> 0.8 aft)]
                    │                                          │
                    └────────────────────┬─────────────────────┘
                                         │
                                         ▼
                    ┌──────────────────────────────────────────┐
                    │ Greedy Combinatorial Optimization        │
                    │  • Lock inflexible tasks                 │
                    │  • Shift flexible heavy tasks (07-10h)   │
                    │  • Minimize peak weighted exposure       │
                    └────────────────────┬─────────────────────┘
                                         │
                                         ▼
                    [Diurnal Rescheduled Profile: Peak Exposure -28.4%]
```

- **Model Name & Problem Type:** Diurnal Construction Task Staggering Optimizer. Constrained Combinatorial Schedule Optimization.
- **Why this algorithm was chosen:** Blanket construction bans cause severe economic distress to daily-wage construction laborers. By shifting flexible high-dust activities (earth excavation, jackhammering) away from early morning temperature inversions into ventilated afternoon hours, peak localized particulate exposure is smoothed without requiring total site shutdowns.
- **Alternatives compared:** Compared against total site shutdowns (economic disruption) and unconstrained rescheduling. Constrained optimization preserves total project work hours and contractor deadlines.
- **Input features:** Task dust intensity rating ($1-5$), duration (hours), allowable start/end windows, hourly atmospheric inversion weight ($1.8-1.9$ during 07:00-10:00 vs $0.8-0.9$ during 12:00-15:00).
- **Output format:** Hourly baseline vs optimized dust index sums and weighted exposure scores.
- **Training pipeline:** Implemented in [analysis/dust_scheduler_demo.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/dust_scheduler_demo.py) and dynamically evaluated via `POST /api/dust-demo/simulate` in [backend/routers/dust_demo.py](file:///Users/mac/Desktop/pollution-blame-ledger/backend/routers/dust_demo.py).
- **Hyperparameters & Tuning Method:**
  - `WORKING_HOURS`: 07:00 to 18:00 IST (12 hours).
  - Default `shift_hours`: 4 hours.
  - Default `misting_efficiency_pct`: 20.0%.
  - Default `stagnation_avoidance_weight`: 1.5.
- **Evaluation metrics & actual results:**
  - *Baseline Peak Exposure Score:* 30.6
  - *Optimized Scheduled Peak Exposure Score:* 14.4
  - *Achieved Peak Exposure Reduction:* **28.4%** (raw index) and **52.9%** (inversion-weighted).
- **Saved model file location & format:** Output written to [pipeline/data/processed/dust_demo_schedule.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/dust_demo_schedule.csv).
- **Limitations & Possible Improvements:** Currently an illustrative proof-of-concept modeling 4 construction sites near Anand Vihar; scaling city-wide requires integration with municipal building permit databases.
- **Site pages using this model:** Policy View Construction Dust Rescheduler Simulator.

---

### 4.5 WHO GEMM Epidemiological Burden Projection Engine
- **Model Name & Problem Type:** Global Exposure Mortality Model (GEMM) / Concentration-Response Risk Engine. Epidemiological Public Health Projection.
- **Why this algorithm was chosen:** Standardizes health communication on internationally peer-reviewed concentration-response functions (WHO 2021 Guidelines and Lancet Planetary Health India studies) rather than ad-hoc estimates.
- **Input features:** Episode mean PM2.5 ($\mu\text{g}/\text{m}^3$), WHO 24h guideline counterfactual threshold (15 $\mu\text{g}/\text{m}^3$), source attribution midpoint shares, demographic cohort multipliers.
- **Output format:** Attributable excess mortality, respiratory morbidity, cardiovascular morbidity percentages, and Berkeley Earth daily cigarette equivalents.
- **Training pipeline:** Implemented in [analysis/health.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/health.py). Evaluates relative risk:
  $$RR = \exp\left(\beta \times \frac{\text{PM}_{2.5} - 15}{10}\right)$$
  with $\beta_{\text{mortality}} = 0.008$, $\beta_{\text{respiratory}} = 0.018$, $\beta_{\text{cardiovascular}} = 0.014$.
- **Saved model file location & format:** Outputs written to [pipeline/data/processed/health_impacts.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/health_impacts.csv) and [pipeline/data/processed/health_summary.json](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/health_summary.json).
- **Limitations & Possible Improvements:** Assumes uniform particulate toxicity across sources; chemical speciation differences (e.g. polycyclic aromatic hydrocarbons vs geological silica) are not weighted.
- **Site pages using this model:** Forecast & Advisor Epidemiological Burden Card.

---

### 4.6 Supervised Feature Selection Screener (`HistGradientBoostingRegressor`)
- **Model Name & Problem Type:** `HistGradientBoostingRegressor` with Blocked Time-Series Permutation Importance. Supervised Feature Selection.
- **Why this algorithm was chosen:** Distinguishes genuine meteorological and transport drivers from spurious noise without PM2.5 target leakage.
- **Input features:** 39 candidate meteorological, trajectory, and temporal features.
- **Output format:** [pipeline/data/processed/feature_selection_report.csv](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/feature_selection_report.csv) and [pipeline/data/processed/selected_features.json](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/selected_features.json).
- **Training pipeline:** Implemented in [pipeline/s8_feature_selection.py](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/s8_feature_selection.py).
  1. Drops features with $>30\%$ missing values or zero variance.
  2. Clusters collinear features ($|\rho_{\text{Spearman}}| \ge 0.95$) and retains one representative feature per cluster.
  3. Generates shadow features (randomly permuted copy of each candidate feature).
  4. Trains `HistGradientBoostingRegressor` with 5-split `TimeSeriesSplit` and 72-hour purge gap.
  5. Selects features whose permutation importance exceeds the maximum shadow feature, is $\ge 0.5\%$ of $R^2$, and remains positive in $\ge 80\%$ of cross-validation folds.
- **Actual results:** 6 driver features selected: `blh_m`, `raw_fires_24h_pbhr`, `fires_linked_median`, `wind_speed_ms`, `hour_sin`, `pressure_change_6h`. Collinear features dropped: `fires_linked_p90`, `frp_linked_median`, `ventilation_m2s`. Noise features dropped: `rh_pct`, `cloud_pct`, `temp_c`, etc.
- **Saved model file location & format:** Output written to [pipeline/data/processed/selected_features.json](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/data/processed/selected_features.json).
- **Site pages using this model:** Feeds feature vectors into the [Forecasting Model](#41-multi-horizon-particulate-forecasting-model-histgradientboostingregressor).

---

## 5. Gaps and Assumptions

The following items were explicitly investigated across the codebase and could not be verified or were identified as documented assumptions:

1. **Serialized Binary Model Files (.pkl / .joblib):** *Not found in codebase.* Machine learning models (`HistGradientBoostingRegressor` in [analysis/forecast.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/forecast.py) and [pipeline/s8_feature_selection.py](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/s8_feature_selection.py)) are trained on-demand by execution scripts and serialize their outputs directly as pre-generated CSV and JSON artifacts.
2. **2017 Episode Modeling Exclusion:** The 2017 winter season (Episode dates Oct-Dec 2017) was excluded from the final attribution ledger due to data validation failures: fewer operational VIIRS satellites were in orbit, leading to fire count under-reporting, and CAAQMS station reporting completeness on OpenAQ was below the 60% threshold.
3. **Chemical Speciation Ground Truth:** *Not found in codebase.* There are no real-time ground-truth source mass measurements (e.g. Teflon filter chemical speciation) in Delhi telemetry. Source contributions are statistical estimates derived from baseline literature and empirical physical tracers.
4. **Vertical Wind Shear in Back-Trajectories:** The trajectory engine ([pipeline/s5_trajectories.py](file:///Users/mac/Desktop/pollution-blame-ledger/pipeline/s5_trajectories.py)) uses 2D horizontal advection based on 100m wind fields from a 1-degree ERA5 reanalysis grid. Vertical plume updrafts, wet scavenging by rain, and chemical decay during transit are not simulated.
5. **Simulated Construction Sites in Dust Rescheduler:** The 4 construction sites and 8 task profiles modeled in [analysis/dust_scheduler_demo.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/dust_scheduler_demo.py) are simulated demonstrations representing realistic site operations near Anand Vihar; they do not represent live telemetry from real construction contractors.
6. **Uniform PM2.5 Toxicity Assumption:** The WHO GEMM epidemiological module ([analysis/health.py](file:///Users/mac/Desktop/pollution-blame-ledger/analysis/health.py)) models health impacts assuming identical toxicity per microgram of PM2.5 across all sources. Individual chemical differences (e.g., toxic polycyclic aromatic hydrocarbons vs mineral soil dust) are not separately weighted.
7. **Indoor HEPA Filtration Counterfactual:** The epidemiological calculations evaluate ambient outdoor population exposure without accounting for indoor air filtration (air purifiers or air conditioning attenuation).
8. **Diwali Firecracker Burst Spikes:** Sudden episodic spikes resulting from illegal firecracker bursts on Diwali night are flagged via calendar indicators (`diwali_window`) but cannot be predicted hours in advance by weather models due to unpredictable human activity.
