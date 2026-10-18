"""Router for PM2.5 hourly forecasts and evaluation benchmarks."""

from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from backend.loaders import (
    df_to_records,
    loader,
)
from backend.schemas import (
    ForecastEvaluationRow,
    ForecastHourlyPoint,
)

router = APIRouter(prefix="/forecast", tags=["Forecasting Engine"])


@router.get("", response_model=list[ForecastHourlyPoint])
def get_forecast(
    horizon: int | None = Query(None, description="Filter by horizon hours (24 or 48)"),
    limit: int = Query(48, ge=1, le=1000, description="Max number of points to return"),
):
    """Returns hourly PM2.5 predictions with 10th-90th quantile uncertainty intervals and CPCB AQI bands."""
    df = loader.get_forecast_hourly()
    if df.empty:
        raise HTTPException(status_code=404, detail="Forecast data not available.")
    
    sub = pd.DataFrame(df)
    if horizon:
        sub = pd.DataFrame(sub[sub["horizon_h"] == horizon])
    
    # Take latest predictions sorted by target_time
    sorted_df = sub.sort_values(by="target_time", ascending=False).head(limit)
    return df_to_records(sorted_df)


@router.get("/latest")
def get_latest_forecast_summary() -> dict[str, Any]:
    """Returns the most recent 24-hour and 48-hour forecast points with uncertainty ranges."""
    df = loader.get_forecast_hourly()
    if df.empty:
        raise HTTPException(status_code=404, detail="Forecast data not available.")

    latest_time = str(df["issue_time"].max())
    sub = pd.DataFrame(df[df["issue_time"] == latest_time]).sort_values(by="horizon_h")

    points = []
    for _, r in sub.iterrows():
        points.append({
            "horizon_h": int(str(r["horizon_h"])),
            "target_time": str(r["target_time"]),
            "pm25_pred": round(float(str(r["pm25_pred"])), 1),
            "pm25_low": round(float(str(r["pm25_low"])), 1),
            "pm25_high": round(float(str(r["pm25_high"])), 1),
            "aqi_category": str(r["aqi_category"]),
        })

    return {
        "as_of_time": latest_time,
        "summary": "Hourly gradient boosting model with 80% prediction intervals",
        "horizons": points,
    }


@router.get("/evaluation", response_model=list[ForecastEvaluationRow])
def get_forecast_evaluation():
    """Returns benchmark comparison of Gradient Boosting vs. Persistence and Seasonal Mean baselines."""
    df = loader.get_forecast_eval()
    if df.empty:
        raise HTTPException(status_code=404, detail="Forecast evaluation data not available.")
    return df_to_records(df)
