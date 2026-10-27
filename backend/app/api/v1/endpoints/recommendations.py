"""Water-aware crop recommendation."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentFarmer
from app.schemas.core import CropRecommendationOut, CropRecommendationRequest
from app.services import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/crops", response_model=CropRecommendationOut)
def recommend_crops(
    payload: CropRecommendationRequest, farmer: CurrentFarmer
) -> CropRecommendationOut:
    """Rank crops on agronomic suitability and on whether the water exists to grow them.

    Suitability alone can recommend a crop the farmer cannot water. This combines
    both and states the trade-off rather than hiding it behind a single score.
    """
    _ = farmer
    try:
        result = recommendation_service.recommend(
            nitrogen=payload.nitrogen,
            phosphorus=payload.phosphorus,
            potassium=payload.potassium,
            ph=payload.ph,
            temperature_c=payload.temperature_c,
            humidity_pct=payload.humidity_pct,
            rainfall_mm=payload.rainfall_mm,
            available_water_mm=payload.available_water_mm,
            top_n=payload.top_n,
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "REFERENCE_DATA_MISSING", "message": str(error)},
        ) from error
    return CropRecommendationOut(**result)
