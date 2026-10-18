"""FastAPI backend configuration and filesystem paths."""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
PIPELINE_DIR = BASE_DIR / "pipeline"
PROCESSED_DIR = PIPELINE_DIR / "data" / "processed"
REFERENCE_DIR = PIPELINE_DIR / "data" / "reference"
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
