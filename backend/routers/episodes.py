"""Router for episodes, attribution ledger, evidence labels, and action recommendations."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.loaders import (
    df_to_records,
    get_episode_detail,
    get_episodes_list,
    loader,
)
from backend.schemas import (
    EpisodeDetail,
    EpisodeSummary,
)

router = APIRouter(prefix="/episodes", tags=["Episodes & Attribution"])


@router.get("", response_model=list[EpisodeSummary])
def list_episodes(
    season: str | None = Query(None, description="Filter by season year (e.g. 2021, 2023)"),
    dominant_source: str | None = Query(None, description="Filter by dominant source"),
):
    """Lists all cataloged severe pollution episodes with high-level summary metrics."""
    episodes = get_episodes_list()
    if season:
        episodes = [e for e in episodes if e["season"] == season]
    if dominant_source:
        episodes = [e for e in episodes if e["dominant_source"] == dominant_source]
    return episodes


@router.get("/{episode_id}", response_model=EpisodeDetail)
def get_episode(episode_id: int):
    """Returns comprehensive episode details including attribution, evidence labels, actions, and hourly timeseries."""
    detail = get_episode_detail(episode_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found.")
    return detail


@router.get("/{episode_id}/attribution")
def get_episode_attribution(episode_id: int) -> list[dict[str, Any]]:
    """Returns source attribution shares and Monte Carlo uncertainty intervals for an episode."""
    df = loader.get_ledger_entries()
    if df.empty:
        raise HTTPException(status_code=404, detail="Attribution ledger not available.")
    sub = df[df["episode_id"] == episode_id]
    if sub.empty:
        raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found in attribution ledger.")
    return df_to_records(sub)


@router.get("/{episode_id}/labels")
def get_episode_labels(episode_id: int) -> list[dict[str, Any]]:
    """Returns evidence confidence labels (Supported / Conflicting / Insufficient) with rationale."""
    df = loader.get_ledger_labels()
    if df.empty:
        raise HTTPException(status_code=404, detail="Evidence labels not available.")
    sub = df[df["episode_id"] == episode_id]
    if sub.empty:
        raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found in evidence labels.")
    return df_to_records(sub)


@router.get("/{episode_id}/actions")
def get_episode_actions(
    episode_id: int,
    tier: str | None = Query(None, description="Filter by action tier (act, assess, inspect, alert, collect, verify)"),
) -> list[dict[str, Any]]:
    """Returns source-to-action recommendations, responsible parties, hotspots, and verification checks."""
    df = loader.get_action_recommendations()
    if df.empty:
        raise HTTPException(status_code=404, detail="Action recommendations not available.")
    sub = df[df["episode_id"] == episode_id]
    if sub.empty:
        raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found in actions.")
    if tier:
        sub = sub[sub["tier"] == tier]
    return df_to_records(sub)


@router.get("/{episode_id}/timeseries")
def get_episode_timeseries(episode_id: int) -> list[dict[str, Any]]:
    """Returns hourly PM2.5, wind speed, stagnation flag, and back-trajectory fire metrics during the episode window."""
    detail = get_episode_detail(episode_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found.")
    return detail["timeseries"]
