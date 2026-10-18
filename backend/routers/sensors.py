"""Router for sensor network health, spatial IDW anomaly checks, and validation benchmarks."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.loaders import (
    df_to_records,
    get_stations_with_health,
    loader,
)
from backend.schemas import (
    SensorValidationReport,
    StationDetail,
)

router = APIRouter(prefix="/sensors", tags=["Sensors & Data Health"])


@router.get("/stations", response_model=list[StationDetail])
def list_stations(
    status: str | None = Query(None, description="Filter by health status: OK, watch, suspect"),
    district: str | None = Query(None, description="Filter by district name"),
):
    """Returns all 72 Delhi-NCR monitoring stations with coordinates and latest health diagnostics."""
    stations = get_stations_with_health()
    if status:
        stations = [s for s in stations if s["status"].lower() == status.lower()]
    if district:
        stations = [s for s in stations if district.lower() in s["district"].lower()]
    return stations


@router.get("/health")
def get_sensor_health_table(
    status: str | None = Query(None, description="Filter by status: OK, watch, suspect"),
) -> list[dict[str, Any]]:
    """Returns detailed neighborhood IDW residuals, z-scores, and correlation metrics for all evaluated stations."""
    df = loader.get_sensor_health()
    if df.empty:
        raise HTTPException(status_code=404, detail="Sensor health data not available.")
    if status:
        df = df[df["status"].str.lower() == status.lower()]
    return df_to_records(df)


@router.get("/validation", response_model=SensorValidationReport)
def get_sensor_validation():
    """Returns quantitative validation benchmark results from synthetic fault injection experiments."""
    val = loader.get_sensor_validation_report()
    if not val:
        raise HTTPException(status_code=404, detail="Sensor validation benchmark report not found.")
    return val


@router.get("/{station_id}")
def get_station(station_id: str) -> dict[str, Any]:
    """Returns metadata and health diagnostics for an individual monitoring station."""
    stations = get_stations_with_health()
    match = [s for s in stations if s["station_id"].lower() == station_id.lower()]
    if not match:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found.")
    return match[0]
