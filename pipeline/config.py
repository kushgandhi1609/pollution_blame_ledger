"""Central configuration for the Pollution Blame Ledger data pipeline.

Everything tunable lives here. Environment variables:
  BL_DATA_DIR    data folder name (default "data"); synthetic runs use "data_synthetic"
  BL_PERIODS     "start:end,start:end" (default: three backtest episodes)
  BL_SYNTHETIC   "1" marks all outputs with synthetic=1
  FIRMS_MAP_KEY  NASA FIRMS key (free)      OPENAQ_API_KEY  OpenAQ v3 key (free)
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SYNTHETIC = os.environ.get("BL_SYNTHETIC", "0") == "1"
DATA = ROOT / os.environ.get("BL_DATA_DIR", "data")
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
REF = DATA / "reference"
for _p in (RAW, INTERIM, PROCESSED, REF):
    _p.mkdir(parents=True, exist_ok=True)

# All timestamps in the pipeline are naive Indian Standard Time, hour-beginning.
TZ = "Asia/Kolkata"

# ----------------------------------------------------------------- study periods
# Default: the three episodes named in the proposal for backtesting, with margins.
# To add the live 2026 season (Diwali is 8 Nov 2026) append "2026-10-01:2026-11-30".
_DEFAULT_PERIODS = "2017-10-15:2017-12-05,2021-10-15:2021-12-05,2023-10-15:2023-12-05"
PERIODS = [tuple(x.split(":")) for x in os.environ.get("BL_PERIODS", _DEFAULT_PERIODS).split(",")]
LOOKBACK_PAD_DAYS = 4          # weather/fire data fetched this many days before each period (trajectory look-back)

# Diwali dates (VERIFY against an official calendar before relying on them)
DIWALI_DATES = {
    2016: "2016-10-30", 2017: "2017-10-19", 2018: "2018-11-07", 2019: "2019-10-27",
    2020: "2020-11-14", 2021: "2021-11-04", 2022: "2022-10-24", 2023: "2023-11-12",
    2024: "2024-10-31", 2025: "2025-10-20", 2026: "2026-11-08",
}

# ----------------------------------------------------------------- geography
DELHI_LAT, DELHI_LON = 28.6139, 77.2090
STATION_BBOX = (76.7, 28.2, 77.7, 29.1)      # lon_min, lat_min, lon_max, lat_max for station discovery
NCR_NAME_KEYWORDS = ["noida", "gurugram", "gurgaon", "ghaziabad", "faridabad", "greater noida",
                     "sonipat", "bahadurgarh", "meerut", "bulandshahr", "baghpat", "rohtak"]

WEATHER_GRID = dict(lat_min=24.0, lat_max=34.0, lon_min=70.0, lon_max=81.0, step=1.0)
FIRE_BBOX = (70.0, 24.0, 81.0, 34.0)         # west, south, east, north
PBHR_BOX = dict(lat_min=28.5, lat_max=32.6, lon_min=73.8, lon_max=77.6)   # Punjab + Haryana (approx.)
PBHR_EXCLUDE_KM_FROM_DELHI = 60

# ----------------------------------------------------------------- data sources
FIRMS_SOURCES = ["VIIRS_SNPP_SP", "VIIRS_NOAA20_SP"]   # use *_NRT for the last ~2-3 months
FIRMS_CHUNK_DAYS = 5
POLLUTANTS = ["pm25", "pm10", "no2", "so2", "co", "o3"]

# ----------------------------------------------------------------- quality control
QC_BOUNDS = {"pm25": (0, 1500), "pm10": (0, 2000), "no2": (0, 500), "so2": (0, 500),
             "co": (0, 50), "o3": (0, 500)}               # ug/m3 (CO in mg/m3)
FLATLINE_HOURS = {"pm25": 8, "pm10": 8, "no2": 12, "so2": 12, "co": 12, "o3": 12}
SPIKE_FACTOR = 4.0
SPIKE_MIN_VALUE = 250.0
MIN_STATION_COMPLETENESS = 0.60                            # share of hours with PM2.5 after QC

# ----------------------------------------------------------------- local vs regional, NCR
BACKGROUND_PERCENTILE = 0.10
MIN_STATIONS_FOR_BACKGROUND = {"Delhi": 8, "NCR": 4}
RISE_ABS_UG = 20.0             # 3-hour rise thresholds for "station is rising"
RISE_REL = 0.15
HOTSPOT_Z = 2.5
HOTSPOT_MIN_EXCESS = 40.0
FRAC_RISING_WIDE = 0.60
FRAC_RISING_LOW = 0.25
MISSING_WARNING_FRAC = 0.40

# ----------------------------------------------------------------- back-trajectories
TRAJ_WIND_LEVEL = "100m"       # "100m" or "10m"
TRAJ_HOURS_BACK = 72
TRAJ_N_MEMBERS = 10            # member 0 is the unperturbed central trajectory
TRAJ_DIR_SD_DEG = 15.0         # wind-direction perturbation (std dev)
TRAJ_SPEED_SD_FRAC = 0.20      # lognormal std of wind-speed scaling
CORRIDOR_KM = 40.0             # a fire is "linked" if within this distance of the parcel ...
FIRE_TIME_WINDOW_H = 6.0       # ... and within this many hours of the parcel's passage
FIRE_MIN_LINK = 20             # members with >= this many linked fires "agree" fire influence is present
FIRE_SEASON_MONTHS = (9, 10, 11, 12)   # fire linking is only computed in these months
RNG_SEED = 42

# ----------------------------------------------------------------- episodes
EPISODE_PM25_DAILY = 150.0     # daily Delhi median PM2.5 (ug/m3) counted as an episode day
EPISODE_MIN_DAYS = 2

# ----------------------------------------------------------------- feature selection
FS_MAX_MISSING = 0.30
FS_CORR_THRESHOLD = 0.95
FS_N_SPLITS = 5
FS_GAP_HOURS = 72
FS_MIN_IMPORTANCE = 0.005      # also require >= 0.5% R2 drop when the feature is shuffled

# ----------------------------------------------------------------- sensor health check
SENSOR_K_NEIGHBOURS = 4
SENSOR_Z_FLAG = 3.0
SENSOR_MIN_PERSIST_H = 6
SENSOR_CORR_MIN = 0.5

