# Pollution Blame Ledger: dataset build guide

This guide covers how to build the dataset for the project, which features it contains and why, and how the features are selected. Everything is implemented in the scripts next to this file.

## 0. Read this first: what is real and what is not

- **No real data is included.** The environment I built this in could not reach Open-Meteo, OpenAQ, NASA FIRMS or CPCB (all blocked), so I could not download anything. You run the pipeline on your own machine with free API keys.
- **I tested all code on synthetic data** (`make_synthetic.py`). It is invented, written in the same formats the real downloads produce, and every output from it carries `synthetic = 1` and lives in `data_synthetic/`. It proves the code runs. It proves nothing about Delhi. Do not put numbers from it in your submission.
- Some API details (OpenAQ v3 field names, FIRMS date-range limits, whether Open-Meteo's archive offers `boundary_layer_height`) are from memory and could not be checked live. Each script says where to adjust if a call fails.
- **There are no ground-truth source labels** (nobody measured "this hour was 31 % stubble"). That shapes the whole design; see section 5.

## 1. Setup (about 15 minutes)

1. Python 3.10+, then `pip install -r requirements.txt`.
2. **OpenAQ key** (free): create an account at explore.openaq.org and copy the API key. `export OPENAQ_API_KEY=...`
3. **FIRMS key** (free): request a MAP_KEY on the NASA FIRMS site (area API page). `export FIRMS_MAP_KEY=...`
4. Open-Meteo needs no key for the free archive API.
5. Optional but valuable: CPCB CAAQMS data downloaded manually from the CPCB portal (one file per station). Use it where OpenAQ coverage is thin, especially for 2017.

## 2. Design decisions (so you can defend them)

| Decision | Choice | Reason |
|---|---|---|
| Time grain | Hourly, IST, hour-beginning | Trajectory lags are in hours; all sources can be made hourly |
| Study windows | 3 backtest seasons, 15 Oct to 5 Dec of 2017, 2021, 2023 | Matches the proposal; covers stubble season and Diwali. Add `2026-10-01:2026-11-30` for a live season (Diwali is 8 Nov 2026) |
| Padding | 4 days of weather and fires before each window | The trajectory look-back is 72 h |
| Units | ug/m3 for particles and gases, **mg/m3 for CO** | Converted from ppb/ppm in step 4 (25 C, 1 atm assumed) |
| Regions | `Delhi` vs `NCR` per station | Needed for the local/regional split and the NCR comparison |
| Output tables | hourly city table (main), station-hour panel, daily table | One per consumer: dashboard, models, backtests |

## 3. Step by step

Run from the project folder. `run_real.sh` strings these together, but run them one at a time the first time and check each output. **Start with one short window** (`export BL_PERIODS="2023-10-25:2023-11-20"`) so mistakes are cheap.

| Step | Command | What it does | Check afterwards |
|---|---|---|---|
| 0 | `python s0_stations.py` | Finds PM2.5 stations in the Delhi-NCR box via OpenAQ; guesses Delhi vs NCR from the station name | **Open `data/reference/stations.csv` and fix every row with `needs_review = 1`.** Delete stations you do not want. Aim for 25+ Delhi and 8+ NCR |
| 1 | `python s1_weather.py` | Hourly weather for a 1-degree grid over NW India (for trajectories) plus a Delhi point. Wind in m/s, times in IST | Row count, and whether `blh_m` is populated. If the archive endpoint rejects boundary-layer height, the script continues without it |
| 2 | `python s2_fires.py` | VIIRS fire detections in 5-day chunks, UTC to IST, drops low-confidence | Fires per day should rise in Oct, peak early Nov. Use `*_NRT` sources for the last 2 to 3 months |
| 3 | `python s3_airquality.py --openaq` (and/or `--cpcb DIR`) | Hourly observations in one long table. Slow and resumable because of OpenAQ rate limits | **Count stations with data per window.** If 2017 is thin on OpenAQ, use CPCB downloads |
| 4 | `python s4_clean.py` | Unit conversion, bounds, flat-line and spike removal, PM2.5 > PM10 flag, drops stations under 60 % complete | `station_qc_report.csv`: which stations were dropped and how many values were removed |
| 5 | `python s5_trajectories.py` | Back-trajectories from Delhi (10-member ensemble, 72 h) and fire linking | `traj_features_hourly.csv`; linked-fire counts should be near zero outside the fire season |
| 6 | `python s6_features.py` | Feature engineering (section 4) | Regime counts printed at the end; look for a sensible mix, not 100 % one category |
| 7 | `python s7_final.py` | Final tables, episodes, data dictionary | Warning line if any column is missing from the dictionary |
| 8 | `python s8_feature_selection.py` | Feature selection (section 5) | `feature_selection_report.csv` |

Things that commonly go wrong:

- **Timestamps.** The pipeline keeps everything in naive IST. OpenAQ times arrive with offsets and FIRMS times are UTC; both are converted. If a plot of PM2.5 by hour of day does not show morning and evening peaks, suspect a time shift.
- **CPCB file formats vary.** `--cpcb` guesses columns by pattern and prints the mapping it chose. Check it. File name stem must equal the `station_id` in `stations.csv`.
- **Station coordinates and regions** decide the whole local-vs-regional result. Check them on a map once.
- **Fire season only.** Linking is computed for months 9 to 12; outside that, linked-fire columns are 0 and `fire_link_computed = 0`.

## 4. Feature engineering: what is built and why

Every column is documented in `data/processed/data_dictionary.csv` (group, meaning, unit, source, whether it uses future hours).

**Time features** (`hour`, `hour_sin/cos`, `is_rush_am/pm`, `is_night`, `is_weekend`, `days_from_diwali`, `diwali_window`): traffic and night-time burning follow the clock, and the Diwali flag separates fireworks from everything else.

**Weather features** (from Delhi Open-Meteo): wind speed and direction (also as sin/cos and u/v), `nw_wind_flag` (wind from the stubble belt), boundary-layer height, `ventilation_m2s` (height x wind = how much the air can dilute), 24 h and 72 h rain (washout), `temp_range_24h_c` (inversion proxy), pressure change, `stagnation_flag`. Weather decides whether the same emissions produce 80 or 400 ug/m3, so any attribution has to account for it.

**Module 1, fire pathway** (`s5`): for each hour, an ensemble of backward trajectories. A fire counts as linked if a parcel passed within 40 km and within 6 h of the detection. Features: `fires_linked_median/p10/p90`, `frp_linked_median`, `fire_lag_p10/p50/p90_h` (the "18 to 30 hours ago" statement), `fire_member_agree_frac` (confidence), `traj_pbhr_frac` (time spent over Punjab/Haryana), origin bearing, parcel speed. `raw_fires_24h_pbhr` is the **naive fire count kept on purpose** as the baseline your method should beat, and a good slide.

**Module 2, local vs regional** (`s6`): per hour and region, the 10th percentile across stations is the regional background; each station's excess above it is local. Features: `regional_background_pm25`, `local_excess_pm25`, `local_excess_share`, `delhi_background_share`, `pm25_robust_z`, `hotspot_flag`.

**Module 3, fingerprints** (`s6`): `fp_traffic_z` (NO2 and CO against the station's own recent history), `fp_traffic_rush_ratio_no2/co` (rush hours vs midday), `fp_dust_ratio/z` (PM10/PM2.5), `fp_industrial_so2_z`, `fp_biomass_ratio` (PM2.5/PM10), `fp_biomass_night_rise`. These are **evidence lines for the ledger, not predictors**. They overlap (traffic and burning both raise CO) and the thresholds in the proposal are rules of thumb, so treat each as "supports" or "contradicts", never as proof.

**Module 5, Delhi to NCR** (`s6`): `ncr_pm25_median`, `ncr_minus_delhi_pm25`, `ncr_to_delhi_ratio`, `delhi_ncr_corr24h`, `frac_rising_delhi/ncr`, and `regime` (widespread / Delhi-concentrated / NCR-concentrated / mixed / no rise / insufficient data). The regime rule is a documented heuristic using station-share thresholds in `config.py`, so tune and justify them. Also `missing_data_warning`, `delhi_missing_frac`, `ncr_missing_frac` for the missing-data warnings.

**Short-term dynamics**: PM2.5 lags (1, 3, 24 h), trailing means (3, 6, 24 h), differences, and `rising_3h`.

**Look-ahead columns** (flagged `look_ahead = 1`): `fp_traffic_rush_ratio_*` and `fp_biomass_night_rise` use the whole day or the following night. They are fine for explaining a past episode and **must not be used in a forecasting model** (leakage).

## 5. Feature selection

Without labels you cannot train "source share" directly, so selection has two layers (`s8_feature_selection.py`):

1. **Evidence features are kept by design** (fingerprints, local/regional, NCR). They are the ledger's evidence lines; screening them against PM2.5 would be circular.
2. **Driver features are screened statistically** (weather, time, trajectory, fire) against log(Delhi median PM2.5). They contain no PM2.5 information, so there is no leakage:
   - drop if more than 30 % missing, or constant;
   - among features with |Spearman rho| of 0.95 or more, keep the one with the least missing data;
   - gradient-boosting model with blocked time-series cross-validation (72 h gap), permutation importance on held-out folds;
   - keep a feature only if its importance beats the best **shadow** (randomly shuffled copy) feature, is at least 0.5 % of R2, and is positive in at least 80 % of folds.

Outputs: `feature_selection_report.csv` (every feature and why it was kept or dropped) and `selected_features.json`.

What the synthetic test showed, which is relevant for reading the real run:
- The screen kept 6 drivers (ventilation, wind speed, hour of day and rush hour) and dropped noise features such as cloud cover, once I added the 0.5 % floor. Without the floor, noise features slipped through. Treat the output as a **shortlist**, then apply judgment.
- Cross-validated R2 varied a lot by fold (from negative to 0.73) because the first fold has little training data and seasons differ. Report the spread, not just the average.
- In the synthetic run neither the raw fire count nor the trajectory-linked counts survived the screen. That is expected: I generated the fake PM2.5 without simulating real transport, so the fire features have no genuine pathway to find. **On real data, comparing `fires_linked_median` against `raw_fires_24h_pbhr` is a real test of your core idea.** If linking does not beat the raw count, say so; that is a valid finding and fits the transparent-ledger story.

## 6. The final dataset (`data/processed/`)

| File | Rows | Use |
|---|---|---|
| `city_hourly_final.csv` | one per hour (about 1,200 per season) | **Main table**: dashboard time series, regime, fire pathway, weather, backtest inputs |
| `station_hourly_final.csv` | one per station-hour | Station-level maps, local excess, hotspots; includes all city/weather/trajectory columns |
| `city_daily_final.csv` | one per day | Daily summaries and `episode_id` (days at or above 150 ug/m3 daily mean for 2 or more days) |
| `episodes.csv` | one per episode | Episode list for the backtest |
| `traj_central_tracks.csv` | one per hour and 3-hour step | Draw the back-trajectory on the map |
| `station_qc_report.csv` | one per station | Data-quality transparency page |
| `data_dictionary.csv` | one per column | Documentation |
| `feature_selection_report.csv`, `selected_features.json` | | Feature selection results |

## 7. The backtest reference (you must fill this in)

`data/reference/reference_apportionment_TEMPLATE.csv` is blank on purpose: I will not invent published numbers. Fill one row per study, source and period (`low_pct`, `mid_pct`, `high_pct`, citation, DOI/URL). Candidates to look for and verify yourself: the IIT Kanpur Delhi source-apportionment study (2016), the TERI/ARAI study (2018), SAFAR emission inventory work, the Decision Support System that reports daily stubble-burning share for Delhi, and CSE or CEEW analyses of the 2017 and 2021 episodes. Record the method each used (receptor model vs dispersion model), since they are not directly comparable.

## 8. Limits you should state in your submission

- Estimates, not measurements: real apportionment needs chemical speciation or chemical transport models.
- Trajectories are horizontal-only with 1-degree winds; fire detections are not smoke amounts; VIIRS overpasses are 2 to 4 per day.
- Station coverage and equipment differ; 2017 coverage is the biggest risk.
- The regime classifier and background percentile are heuristics; show a sensitivity check (change the 10th percentile to 5th or 20th and see how the result moves).

## 9. Suggested order for the hackathon

1. Run synthetic end to end (5 minutes) to confirm your environment works.
2. Real run on one 4-week window; fix stations and units.
3. Add the other two seasons; check station counts per window.
4. Build the dashboard on `city_hourly_final.csv` first, then the map on `station_hourly_final.csv`.
5. Fill the reference table, run the backtest, write up successes and failures.
