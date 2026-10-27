"""Crop reference data and growth-stage curves."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import DbSession
from app.db.models import Crop
from app.schemas.core import CropDetail, CropOut, GrowthStageOut, KcCurvePoint
from app.services.baseline_service import get_kc_model

router = APIRouter(prefix="/crops", tags=["crops"])


@router.get("", response_model=list[CropOut])
def list_crops(db: DbSession) -> list[Crop]:
    """Every crop the system can model.

    A crop appears here only if it has a complete four-stage coefficient curve.
    Offering a crop the system cannot actually compute would produce a confusing
    failure later in the prediction flow.
    """
    return list(db.scalars(select(Crop).order_by(Crop.name)))


@router.get("/{crop_id}", response_model=CropDetail)
def get_crop(crop_id: int, db: DbSession) -> CropDetail:
    crop = db.get(Crop, crop_id)
    if crop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "CROP_NOT_FOUND", "message": f"No crop with id {crop_id}."},
        )
    detail = CropDetail.model_validate(crop)
    detail.stages = [GrowthStageOut.model_validate(s) for s in crop.stages]
    return detail


@router.get("/{crop_id}/growth-stages", response_model=list[GrowthStageOut])
def get_growth_stages(crop_id: int, db: DbSession) -> list[GrowthStageOut]:
    crop = db.get(Crop, crop_id)
    if crop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "CROP_NOT_FOUND", "message": f"No crop with id {crop_id}."},
        )
    return [GrowthStageOut.model_validate(s) for s in crop.stages]


@router.get("/{crop_id}/kc-curve", response_model=list[KcCurvePoint])
def get_kc_curve(
    crop_id: int, db: DbSession,
    step_days: int = Query(default=1, ge=1, le=30),
) -> list[KcCurvePoint]:
    """The day-by-day crop coefficient curve, for the growth-stage timeline.

    Development and late-season values are interpolated rather than tabulated,
    so this is a continuous curve rather than four steps.
    """
    crop = db.get(Crop, crop_id)
    if crop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "CROP_NOT_FOUND", "message": f"No crop with id {crop_id}."},
        )
    curve = get_kc_model().curve(crop.slug)
    sampled = curve.iloc[::step_days]
    return [
        KcCurvePoint(days_after_sowing=int(row.days_after_sowing),
                     stage=str(row.stage), kc=round(float(row.kc), 4))
        for row in sampled.itertuples()
    ]
