"""Water productivity, budget allocation and district rainfall.

These endpoints answer the question the merged project exists to answer: given
a finite amount of water, which crop returns the most per drop? The water
engine and the district yield record each hold half the answer and neither can
produce it alone.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentFarmer, DbSession
from app.api.deps import owned_farm
from app.schemas.water_intelligence import (
    WaterBudgetRequest,
    WaterBudgetResponse,
    WaterProductivityResponse,
)
from app.services.water_intelligence_service import (
    SourceUnavailable,
    water_intelligence,
)
from ml.logging_utils import get_logger

log = get_logger("api.water_intelligence")

router = APIRouter(prefix="/water-intelligence", tags=["water intelligence"])


def _unavailable(error: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "error": "SOURCE_UNAVAILABLE",
            "message": str(error),
        },
    )


@router.get("/coverage")
def coverage(farmer: CurrentFarmer) -> dict[str, Any]:
    """What this deployment can answer, and on what evidence.

    The interface calls this before offering a feature, so a farmer is told
    "this deployment has no price data" rather than shown an empty column and
    left to guess whether the crops are worthless or the data is missing.
    """
    return water_intelligence.coverage()


@router.get("/productivity", response_model=WaterProductivityResponse)
def productivity(
    farmer: CurrentFarmer,
    state: str | None = Query(default=None, description="Narrow the yield median."),
    district: str | None = Query(default=None),
    min_observations: int = Query(default=5, ge=1, le=100),
) -> dict[str, Any]:
    """Rank crops by what they return per unit of water consumed.

    Two productivities are reported because they answer different questions:
    kilograms per cubic metre transpired (what the plant achieves) and per
    cubic metre delivered (what the farmer achieves, after irrigation losses).
    Value per cubic metre uses the annual minimum support price rather than the
    three-day market snapshot this project happens to hold.
    """
    try:
        return water_intelligence.productivity(
            state=state, district=district, min_observations=min_observations
        )
    except SourceUnavailable as error:
        raise _unavailable(error) from error


@router.post("/water-budget", response_model=WaterBudgetResponse)
def water_budget(
    payload: WaterBudgetRequest,
    farmer: CurrentFarmer,
    db: DbSession,
) -> dict[str, Any]:
    """What a finite seasonal water budget will actually grow.

    The farmer states the water they can get - a borewell's seasonal yield, a
    tank, a canal allocation - and the plot they want to grow on. Each crop is
    assessed against that volume: whether it finishes the plot, and if not, how
    much of the plot it does finish.

    A crop the budget cannot complete is reported with its irrigable area
    rather than dropped, because growing a smaller area properly is a real
    decision and this endpoint exists to inform it.
    """
    state, district = payload.state, payload.district

    # A farm the farmer owns can supply the location, so the interface does not
    # have to make them retype it.
    if payload.farm_id is not None:
        farm = owned_farm(db, farmer, payload.farm_id)
        state = state or farm.state
        district = district or farm.district

    try:
        return water_intelligence.budget(
            available_water_m3=payload.available_water_m3,
            plot_area_ha=payload.plot_area_ha,
            state=state,
            district=district,
        )
    except SourceUnavailable as error:
        raise _unavailable(error) from error


@router.get("/rainfall")
def district_rainfall(
    farmer: CurrentFarmer,
    db: DbSession,
    state: str | None = Query(default=None),
    district: str | None = Query(default=None),
    farm_id: int | None = Query(default=None),
) -> dict[str, Any]:
    """Recent rainfall for a district, against its long-period normal.

    Supply ``farm_id``, or ``state`` and ``district``. The rainfall file covers
    twenty days, so this is current-season context - departure from normal and
    dry-spell length - and the response says so rather than letting it be read
    as a trend.
    """
    if farm_id is not None:
        farm = owned_farm(db, farmer, farm_id)
        state = state or farm.state
        district = district or farm.district

    if not state or not district:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "LOCATION_REQUIRED",
                "message": "Supply farm_id, or both state and district.",
            },
        )

    try:
        context = water_intelligence.rainfall(state=state, district=district)
    except SourceUnavailable as error:
        raise _unavailable(error) from error

    if context is None:
        covered = water_intelligence.districts_with_rainfall(state=state)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "DISTRICT_NOT_COVERED",
                "message": (
                    f"The rainfall file has no records for {district}, {state}. "
                    "It covers twenty days across a limited set of districts."
                ),
                "details": {"covered_districts": covered},
            },
        )
    return context


@router.get("/rainfall/districts")
def covered_districts(
    farmer: CurrentFarmer,
    state: str | None = Query(default=None),
) -> dict[str, Any]:
    """Which districts the rainfall file covers."""
    try:
        names = water_intelligence.districts_with_rainfall(state=state)
    except SourceUnavailable as error:
        raise _unavailable(error) from error
    return {"state": state, "districts": names, "count": len(names)}
