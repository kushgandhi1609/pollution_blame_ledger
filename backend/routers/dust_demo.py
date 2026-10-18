"""Router for construction dust scheduling demonstration and interactive simulation."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.loaders import (
    loader,
)
from backend.schemas import DustDemoResponse, DustScheduleRow

router = APIRouter(prefix="/dust-demo", tags=["Dust Rescheduler Demo"])


class SimulationParams(BaseModel):
    shift_hours: int = 4
    misting_efficiency_pct: float = 20.0
    stagnation_avoidance_weight: float = 1.5


@router.get("", response_model=DustDemoResponse)
def get_dust_schedule():
    """Returns baseline vs. optimized dust emission scores illustrating peak diurnal flattening."""
    df = loader.get_dust_demo()
    if df.empty:
        raise HTTPException(status_code=404, detail="Dust demo schedule not available.")

    records = [
        DustScheduleRow(
            hour=int(str(r["hour"])),
            time_window=str(r["time_window"]),
            stagnation_inversion_factor=round(float(str(r["stagnation_inversion_factor"])), 2),
            baseline_dust_index_sum=round(float(str(r["baseline_dust_index_sum"])), 1),
            optimized_dust_index_sum=round(float(str(r["optimized_dust_index_sum"])), 1),
            dust_index_reduction=round(float(str(r["dust_index_reduction"])), 1),
            baseline_weighted_exposure=round(float(str(r["baseline_weighted_exposure"])), 1),
            optimized_weighted_exposure=round(float(str(r["optimized_weighted_exposure"])), 1),
            exposure_reduction=round(float(str(r["exposure_reduction"])), 1),
        )
        for _, r in df.iterrows()
    ]

    # Calculate overall peak reduction
    base_peak = float(str(df["baseline_dust_index_sum"].max()))
    sched_peak = float(str(df["optimized_dust_index_sum"].max()))
    peak_reduct = round(((base_peak - sched_peak) / base_peak) * 100.0, 1)

    return DustDemoResponse(
        title="Construction Dust Rescheduler Demonstration",
        status="Simulated Proof-of-Concept",
        target_hotspot="Anand Vihar / East Delhi Cluster",
        simulated_sites_count=4,
        peak_reduction_pct=peak_reduct,
        disclaimer=(
            "Simulated illustrative demonstration: demonstrates peak atmospheric exposure "
            "smoothing via diurnal activity shifting, not gross emission elimination."
        ),
        schedule=records,
    )


@router.post("/simulate")
def run_interactive_simulation(params: SimulationParams) -> dict[str, Any]:
    """Dynamically simulates diurnal schedule shifts based on user-supplied parameters."""
    df = loader.get_dust_demo().copy()
    if df.empty:
        raise HTTPException(status_code=404, detail="Base dust data not available.")

    # Re-simulate scores with custom parameters
    misting_factor = 1.0 - (params.misting_efficiency_pct / 100.0)
    simulated_records = []

    for _, r in df.iterrows():
        h = int(str(r["hour"]))
        base = float(str(r["baseline_dust_index_sum"]))
        is_stagnant = h in [7, 8, 9, 10]

        if is_stagnant:
            # Shift heavy tasks away from stagnant hours
            sim_score = base * 0.45 * misting_factor
        elif h in [12, 13, 14, 15]:
            # Redistributed to ventilated afternoon
            sim_score = (base * 1.3) * misting_factor
        else:
            sim_score = base * misting_factor

        simulated_records.append({
            "hour": h,
            "baseline_dust_index_sum": round(base, 1),
            "custom_scheduled_score": round(sim_score, 1),
            "reduction_pct": round(((base - sim_score) / base) * 100.0, 1) if base > 0 else 0.0,
            "is_stagnation_hour": is_stagnant,
        })

    base_peak = max(r["baseline_dust_index_sum"] for r in simulated_records)
    new_peak = max(r["custom_scheduled_score"] for r in simulated_records)
    new_reduction = round(((base_peak - new_peak) / base_peak) * 100.0, 1)

    return {
        "status": "success",
        "parameters_applied": params.model_dump(),
        "baseline_peak_score": base_peak,
        "simulated_peak_score": new_peak,
        "achieved_peak_reduction_pct": new_reduction,
        "schedule": simulated_records,
    }
