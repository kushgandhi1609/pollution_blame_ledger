"""FastAPI application entrypoint for The Pollution Blame Ledger."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import (
    ALLOWED_ORIGINS,
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
)
from backend.loaders import get_episodes_list, loader
from backend.routers import (
    advisor,
    dust_demo,
    episodes,
    forecast,
    meta,
    sensors,
    validation,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preloads all analytical data artifacts into memory on startup."""
    print("[Pollution Blame Ledger] Pre-loading data artifacts into memory...")
    loader.get_city_daily()
    loader.get_city_hourly()
    loader.get_ledger_entries()
    loader.get_ledger_labels()
    loader.get_action_recommendations()
    loader.get_stations()
    loader.get_sensor_health()
    loader.get_sensor_validation_report()
    loader.get_forecast_hourly()
    loader.get_forecast_eval()
    loader.get_advice()
    loader.get_dust_demo()
    loader.get_backtest_summary()
    loader.get_backtest_results()
    loader.get_health_summary()
    print("[Pollution Blame Ledger] All 15 core artifacts loaded. Ready for queries.")
    yield
    print("[Pollution Blame Ledger] Shutting down.")


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers under /api prefix
app.include_router(episodes.router, prefix="/api")
app.include_router(sensors.router, prefix="/api")
app.include_router(forecast.router, prefix="/api")
app.include_router(advisor.router, prefix="/api")
app.include_router(dust_demo.router, prefix="/api")
app.include_router(validation.router, prefix="/api")
app.include_router(meta.router, prefix="/api")


@app.get("/", tags=["Root"])
def root():
    """Root endpoint providing API overview and navigation links."""
    return {
        "title": API_TITLE,
        "version": API_VERSION,
        "status": "online",
        "documentation": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "episodes": "/api/episodes",
            "sensors": "/api/sensors/stations",
            "sensor_health": "/api/sensors/health",
            "forecast": "/api/forecast",
            "advice": "/api/advice",
            "dust_demo": "/api/dust-demo",
            "validation_backtest": "/api/validation/backtest",
            "health_impact": "/api/validation/health-impact",
            "meta_summary": "/api/meta/summary",
        },
    }


@app.get("/health", tags=["Root"])
def health_check():
    """Health check endpoint for container orchestrators and monitoring agents."""
    episodes_count = len(get_episodes_list())
    stations_count = len(loader.get_stations())
    return {
        "status": "healthy",
        "cataloged_episodes": episodes_count,
        "active_stations": stations_count,
        "memory_cached_tables": len(loader._cache),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
