#!/usr/bin/env bash
# Full REAL-data run. Set keys first:
#   export OPENAQ_API_KEY=...   export FIRMS_MAP_KEY=...
# Optional: export BL_PERIODS="2023-10-15:2023-12-05"   (start small first!)
set -e
python s0_stations.py                       # then REVIEW data/reference/stations.csv by hand
python s1_weather.py
python s2_fires.py
python s3_airquality.py --openaq            # and/or: --cpcb path/to/cpcb_csv_folder
python s4_clean.py
python s5_trajectories.py
python s6_features.py
python s7_final.py
python s8_feature_selection.py
