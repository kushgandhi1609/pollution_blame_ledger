"""Router for bilingual precaution advisor and CPCB/WHO health guidance."""

from fastapi import APIRouter, HTTPException, Query

from backend.loaders import (
    df_to_records,
    loader,
)
from backend.schemas import PrecautionRow

router = APIRouter(prefix="/advice", tags=["Precaution Advisor"])


@router.get("", response_model=list[PrecautionRow])
def get_daily_advice(
    group: str | None = Query(None, description="Filter by demographic group (e.g. general_public, children_schools, older_adults, outdoor_workers)"),
):
    """Returns bilingual (English & Hindi) CPCB/WHO health precautions tailored to AQI forecast and active source signals."""
    df = loader.get_advice()
    if df.empty:
        raise HTTPException(status_code=404, detail="Advice data not available.")
    if group:
        df = df[df["group"].str.lower() == group.lower()]
    return df_to_records(df)


@router.get("/groups")
def list_advice_groups() -> list[dict[str, str]]:
    """Returns available demographic vulnerability groups."""
    return [
        {"id": "general_public", "name": "General Public", "name_hi": "आम जनता"},
        {"id": "children_schools", "name": "Children & Schools", "name_hi": "बच्चे एवं स्कूल"},
        {"id": "older_adults", "name": "Older Adults (60+)", "name_hi": "वरिष्ठ नागरिक (60+)"},
        {"id": "cardiopulmonary_patients", "name": "Cardiopulmonary Patients", "name_hi": "हृदय व फेफड़ों के मरीज"},
        {"id": "outdoor_workers", "name": "Outdoor Workers", "name_hi": "बाहर काम करने वाले श्रमिक"},
    ]
