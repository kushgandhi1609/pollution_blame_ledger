#!/usr/bin/env bash
# Test the code (and build UI against it) with FAKE data. Never report these numbers as findings.
set -e
export BL_DATA_DIR=data_synthetic BL_SYNTHETIC=1 BL_PERIODS="2022-10-01:2022-12-10,2023-10-01:2023-12-10"
python make_synthetic.py
python s2_fires.py --skip-fetch
python s4_clean.py
python s5_trajectories.py
python s6_features.py
python s7_final.py
python s8_feature_selection.py
