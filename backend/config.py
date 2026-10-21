"""FastAPI backend configuration and filesystem paths."""

from pathlib import Path
import os

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
PIPELINE_DIR = BASE_DIR / "pipeline"

# Use BL_DATA_DIR env var if present (e.g., "data_synthetic"), otherwise default to "data"
DATA_DIR_NAME = os.environ.get("BL_DATA_DIR", "data")
PROCESSED_DIR = PIPELINE_DIR / DATA_DIR_NAME / "processed"
REFERENCE_DIR = PIPELINE_DIR / DATA_DIR_NAME / "reference"
CONFIG_DIR = BASE_DIR / "config"

# CORS origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "*",
]

# API Metadata
API_TITLE = "The Pollution Blame Ledger API"
API_VERSION = "1.0.0"
API_DESCRIPTION = (
    "Evidence-to-action air pollution attribution and intelligence engine for Delhi-NCR. "
    "Designed with the core principle: Attribution is an estimate with quantified uncertainty, "
    "not a judicial verdict."
)
