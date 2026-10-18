# AERTRACE
### Delhi-NCR Air Quality Attribution & Intelligence Ledger

> **Core Scientific Principle:**  
> *"Attribution is an estimate with uncertainty, not a verdict."*  
> AerTrace provides probabilistic credible bounds, multi-sensor verification checks, and emergency policy prioritization—safeguarding against premature or unilateral penal action.

---

## Overview

**AERTRACE** is an institutional-grade, evidence-to-action air pollution intelligence platform designed for the Delhi National Capital Region (NCR). Rather than relying on single-point blame assertions during acute winter smog spikes, AerTrace deploys a rigorous analytical stack:

1. **5,000-Draw Monte Carlo Attribution Engine:** Computes 10th-to-90th percentile credible intervals across five modeled source categories (agricultural stubble burning, vehicular exhaust, road silt/construction dust, industrial boilers, and secondary remainder).
2. **Spatial IDW Sensor Network QC:** Analyzes 72 continuous ambient air quality monitoring stations (CPCB/DPCC) using Inverse-Distance Weighting ($k=4$, 40 km corridor) to flag persistent local sensor drift (`watch` / `suspect`) without deleting raw telemetry.
3. **Prioritized Source-to-Action Policy Matrix:** Links active source fingerprints to actionable municipal tiers (`ACT`, `ASSESS`, `INSPECT`, `ALERT`, `VERIFY`, `COLLECT`) with mandatory verification requirements.
4. **Diurnal Dust Rescheduler Simulation:** Counterfactual modeling demonstrating how shifting mechanical construction activities away from morning calm hours flattens peak exposure without requiring total site shutdowns.
5. **72-Hour Gradient Boosted Forecasting:** Ensemble particulate forecasting incorporating boundary layer inversion dynamics, satellite fire radiative power (FRP), and transport trajectory parcel lags.
6. **Peer-Reviewed Literature Backtesting:** Validated against 63 published peer-reviewed studies (IIT Kanpur, SAFAR, TERI, NEERI), achieving 100% credible interval overlap.

---

## Repository Structure

```text
pollution-blame-ledger/
├── analysis/               # Core scientific modeling engines
│   ├── attribution.py      # Monte Carlo evidence apportionment engine
│   ├── backtest.py         # 63-study peer-reviewed literature backtest
│   ├── evidence_labels.py  # Confidence grading & physical cross-checks
│   ├── forecast.py         # 72h gradient boosted forecasting model
│   ├── health.py           # WHO GEMM epidemiological burden module
│   └── sensor_health.py    # Spatial IDW sensor consistency monitor
├── backend/                # FastAPI REST API
│   ├── loaders.py          # In-memory artifact caching & query helpers
│   ├── main.py             # Application entrypoint & CORS middleware
│   ├── routers/            # Domain endpoints (episodes, sensors, forecast, etc.)
│   └── schemas.py          # Pydantic data models
├── config/                 # Operational rules & domain matrices
│   ├── actions.csv         # Source-to-action policy & verification matrix
│   └── advice.csv          # Bilingual CPCB/WHO health precaution rules
├── frontend/               # React 18 + Vite + TypeScript application
│   ├── public/             # Static assets (AerTrace logo, favicon)
│   ├── src/
│   │   ├── components/     # Institutional UI components (Recharts, Leaflet)
│   │   ├── services/       # Typed API client
│   │   ├── styles/         # CSS design tokens (Navy-anchored palette)
│   │   └── types/          # TypeScript interface definitions
│   └── vite.config.ts      # Vite dev server configuration & API proxy
├── pipeline/               # Data ingestion & feature generation
│   ├── data/               # Processed, reference, and raw datasets
│   └── make_synthetic.py   # Deterministic synthetic test data generator
├── tests/                  # Automated backend test suite (22 unit tests)
│   └── test_backend.py
├── pyproject.toml          # Project configuration & tool settings
├── requirements.txt        # Python backend & pipeline dependencies
└── README.md
```

---

## Prerequisites

- **Python:** Version 3.10 or higher (tested on 3.10, 3.11, 3.12, 3.14)
- **Node.js:** Version 18.0 or higher
- **npm:** Version 9.0 or higher

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/kushgandhi1609/pollution_blame_ledger.git
cd pollution_blame_ledger
```

---

### 2. Backend Setup (FastAPI & Scientific Pipeline)

1. **Create and activate a virtual environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   *(On Windows: `.venv\Scripts\activate`)*

2. **Install Python dependencies:**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Verify the test suite:**

   ```bash
   pytest
   ```
   *All 22 unit and integration tests should pass.*

4. **Start the FastAPI backend server:**

   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

   The backend will be live at:
   - API Root: `http://localhost:8000/`
   - Interactive Swagger Docs: `http://localhost:8000/docs`
   - Alternative ReDoc: `http://localhost:8000/redoc`

---

### 3. Frontend Setup (React + Vite + TypeScript)

Open a new terminal window, navigate to the `frontend/` directory, and start the development server:

1. **Navigate to the frontend directory:**

   ```bash
   cd frontend
   ```

2. **Install Node packages:**

   ```bash
   npm install
   ```

3. **Start the Vite development server:**

   ```bash
   npm run dev
   ```

4. **Open your browser:**

   Navigate to `http://localhost:5173/`

The frontend automatically proxies `/api` requests to the FastAPI backend running on `http://localhost:8000`.

---

## Running the Data & Analytical Pipeline

If you wish to re-generate analytical artifacts or run the scientific modeling scripts from scratch:

```bash
# Activate your virtual environment
source .venv/bin/activate

# 1. Generate or verify synthetic baseline data
python pipeline/make_synthetic.py

# 2. Run the 5,000-draw Monte Carlo attribution engine
python analysis/attribution.py

# 3. Run the spatial IDW sensor network consistency check
python analysis/sensor_health.py

# 4. Run the peer-reviewed literature backtest benchmark
python analysis/backtest.py
```

---

## API Documentation Summary

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/meta/summary` | GET | System metadata, active station count, cataloged episodes. |
| `/api/episodes` | GET | List cataloged severe smog episodes with peak and mean metrics. |
| `/api/episodes/{id}` | GET | Complete episode breakdown (attribution, labels, actions, timeseries). |
| `/api/episodes/{id}/attribution` | GET | 5,000-draw Monte Carlo uncertainty intervals (10th, 50th, 90th). |
| `/api/sensors/stations` | GET | 72 NCR stations with coordinates, health status, and IDW residuals. |
| `/api/sensors/validation` | GET | Synthetic fault-injection benchmark report (recall and false-alarm rates). |
| `/api/forecast` | GET | 72-hour hourly PM2.5 projections with 80% credible prediction ribbons. |
| `/api/advice` | GET | Bilingual (English & Hindi) CPCB/WHO health guidance. |
| `/api/dust-demo/simulate` | POST | Interactive diurnal task shifting simulation. |
| `/api/validation/backtest` | GET | 63-study peer-reviewed literature comparison table. |
| `/api/validation/health-impact` | GET | WHO GEMM excess mortality and DALY burden projections. |

---

## Scientific & Regulatory Disclaimer

Attribution estimates generated by AerTrace represent probabilistic calculations reflecting atmospheric transport modeling, chemical tracers, and regional parcel back-trajectories. 

- Modeling results indicate estimated source contributions with quantified uncertainty intervals; they do not constitute legal proof or judicial verdicts.
- No commercial entity, industrial facility, or agricultural community should be subjected to unilateral punitive measures, site shutdowns, or financial penalties based solely on model estimates without formal on-site regulatory inspection and certified filter gravimetry.

---

## License

This project is licensed under the Apache 2.0 License. See the `LICENSE` file for details.
