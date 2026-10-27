"""Farmer profile, farms, fields, plantings and soil samples."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import (
    CurrentFarmer, DbSession, owned_field, owned_field_crop, owned_farm,
)
from app.db.models import Crop, Farm, Field, FieldCrop, SoilData
from app.schemas.common import Message
from app.schemas.core import (
    FarmCreate, FarmDetail, FarmOut, FarmerOut, FarmerUpdate, FieldCreate,
    FieldCropCreate, FieldCropDetail, FieldCropOut, FieldOut, FieldUpdate,
    FarmUpdate, SoilDataCreate, SoilDataOut,
)
from app.services.baseline_service import get_kc_model

router = APIRouter(tags=["farms"])


# ==========================================================================
# Farmer profile
# ==========================================================================
@router.get("/farmers/profile", response_model=FarmerOut)
def get_profile(farmer: CurrentFarmer) -> FarmerOut:
    return FarmerOut.model_validate(farmer)


@router.put("/farmers/profile", response_model=FarmerOut)
def update_profile(payload: FarmerUpdate, farmer: CurrentFarmer, db: DbSession) -> FarmerOut:
    for attribute, value in payload.model_dump(exclude_unset=True).items():
        setattr(farmer, attribute, value)
    db.commit()
    db.refresh(farmer)
    return FarmerOut.model_validate(farmer)


# ==========================================================================
# Farms
# ==========================================================================
@router.get("/farms", response_model=list[FarmOut])
def list_farms(farmer: CurrentFarmer, db: DbSession) -> list[Farm]:
    return list(db.scalars(select(Farm).where(Farm.farmer_id == farmer.id).order_by(Farm.id)))


@router.post("/farms", response_model=FarmOut, status_code=status.HTTP_201_CREATED)
def create_farm(payload: FarmCreate, farmer: CurrentFarmer, db: DbSession) -> Farm:
    farm = Farm(farmer_id=farmer.id, **payload.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("/farms/{farm_id}", response_model=FarmDetail)
def get_farm(farm_id: int, farmer: CurrentFarmer, db: DbSession) -> FarmDetail:
    farm = owned_farm(db, farmer, farm_id)
    detail = FarmDetail.model_validate(farm)
    detail.fields = [FieldOut.model_validate(f) for f in farm.fields]
    return detail


@router.put("/farms/{farm_id}", response_model=FarmOut)
def update_farm(farm_id: int, payload: FarmUpdate, farmer: CurrentFarmer, db: DbSession) -> Farm:
    farm = owned_farm(db, farmer, farm_id)
    for attribute, value in payload.model_dump(exclude_unset=True).items():
        setattr(farm, attribute, value)
    db.commit()
    db.refresh(farm)
    return farm


@router.delete("/farms/{farm_id}", response_model=Message)
def delete_farm(farm_id: int, farmer: CurrentFarmer, db: DbSession) -> Message:
    farm = owned_farm(db, farmer, farm_id)
    db.delete(farm)
    db.commit()
    return Message(message=f"Farm {farm_id} and everything recorded under it was deleted.")


# ==========================================================================
# Fields
# ==========================================================================
@router.get("/farms/{farm_id}/fields", response_model=list[FieldOut])
def list_fields(farm_id: int, farmer: CurrentFarmer, db: DbSession) -> list[Field]:
    farm = owned_farm(db, farmer, farm_id)
    return list(farm.fields)


@router.post("/farms/{farm_id}/fields", response_model=FieldOut,
             status_code=status.HTTP_201_CREATED)
def create_field(farm_id: int, payload: FieldCreate, farmer: CurrentFarmer,
                 db: DbSession) -> Field:
    farm = owned_farm(db, farmer, farm_id)

    # A field cannot be larger than the farm that contains it, and the fields
    # together cannot exceed it either. Catching this here prevents nonsense
    # water volumes downstream.
    allocated = sum(f.area_ha for f in farm.fields)
    if allocated + payload.area_ha > farm.total_area_ha + 1e-9:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "AREA_EXCEEDS_FARM",
                "message": (
                    f"This field would bring the total field area to "
                    f"{allocated + payload.area_ha:g} ha, but the farm is only "
                    f"{farm.total_area_ha:g} ha."
                ),
                "details": {"farm_area_ha": farm.total_area_ha,
                            "already_allocated_ha": allocated,
                            "requested_ha": payload.area_ha},
            },
        )

    field = Field(farm_id=farm.id, **payload.model_dump())
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@router.put("/fields/{field_id}", response_model=FieldOut)
def update_field(field_id: int, payload: FieldUpdate, farmer: CurrentFarmer,
                 db: DbSession) -> Field:
    field = owned_field(db, farmer, field_id)
    for attribute, value in payload.model_dump(exclude_unset=True).items():
        setattr(field, attribute, value)
    db.commit()
    db.refresh(field)
    return field


@router.delete("/fields/{field_id}", response_model=Message)
def delete_field(field_id: int, farmer: CurrentFarmer, db: DbSession) -> Message:
    field = owned_field(db, farmer, field_id)
    db.delete(field)
    db.commit()
    return Message(message=f"Field {field_id} was deleted.")


# ==========================================================================
# Plantings
# ==========================================================================
def _planting_detail(db, planting: FieldCrop, today: dt.date | None = None) -> FieldCropDetail:
    """Attach the live agronomic state a farmer actually wants to see."""
    today = today or dt.date.today()
    crop = db.get(Crop, planting.crop_id)
    field = db.get(Field, planting.field_id)
    kc_model = get_kc_model()

    days = (today - planting.sowing_date).days
    stage = kc = None
    if days >= 0 and crop is not None:
        try:
            stage = kc_model.stage_for_day(crop.slug, days).stage
            kc = round(kc_model.kc(crop.slug, days), 4)
        except KeyError:
            stage = kc = None

    cycle = crop.cycle_length_days if crop else 0
    detail = FieldCropDetail(
        **FieldCropOut.model_validate(planting).model_dump(),
        crop_name=crop.name if crop else "unknown",
        crop_slug=crop.slug if crop else "unknown",
        field_name=field.name if field else "unknown",
        days_after_sowing=max(days, 0),
        current_stage=stage,
        current_kc=kc,
        cycle_length_days=cycle,
        progress_pct=round(100.0 * min(max(days, 0) / cycle, 1.0), 1) if cycle else 0.0,
    )
    return detail


@router.get("/fields/{field_id}/crops", response_model=list[FieldCropDetail])
def list_plantings(field_id: int, farmer: CurrentFarmer, db: DbSession) -> list[FieldCropDetail]:
    field = owned_field(db, farmer, field_id)
    return [_planting_detail(db, planting) for planting in field.plantings]


@router.post("/fields/{field_id}/crops", response_model=FieldCropDetail,
             status_code=status.HTTP_201_CREATED)
def create_planting(field_id: int, payload: FieldCropCreate, farmer: CurrentFarmer,
                    db: DbSession) -> FieldCropDetail:
    field = owned_field(db, farmer, field_id)
    crop = db.get(Crop, payload.crop_id)
    if crop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "CROP_NOT_FOUND",
                    "message": f"No crop with id {payload.crop_id}. "
                               "Call GET /api/v1/crops for the list."},
        )

    area = payload.planting_area_ha or field.area_ha
    if area > field.area_ha + 1e-9:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "AREA_EXCEEDS_FIELD",
                    "message": f"Planting area {area:g} ha exceeds the field's "
                               f"{field.area_ha:g} ha."},
        )

    planting = FieldCrop(
        field_id=field.id, crop_id=crop.id, sowing_date=payload.sowing_date,
        planting_area_ha=area, notes=payload.notes,
    )
    db.add(planting)
    db.commit()
    db.refresh(planting)
    return _planting_detail(db, planting)


@router.get("/field-crops/{field_crop_id}", response_model=FieldCropDetail)
def get_planting(field_crop_id: int, farmer: CurrentFarmer, db: DbSession) -> FieldCropDetail:
    planting = owned_field_crop(db, farmer, field_crop_id)
    return _planting_detail(db, planting)


@router.get("/field-crops", response_model=list[FieldCropDetail])
def list_all_plantings(
    farmer: CurrentFarmer, db: DbSession,
    active_only: bool = Query(default=True),
) -> list[FieldCropDetail]:
    """Every planting the farmer has, across all farms and fields."""
    statement = (
        select(FieldCrop)
        .join(Field, Field.id == FieldCrop.field_id)
        .join(Farm, Farm.id == Field.farm_id)
        .where(Farm.farmer_id == farmer.id)
        .order_by(FieldCrop.sowing_date.desc())
    )
    if active_only:
        statement = statement.where(FieldCrop.status == "active")
    return [_planting_detail(db, planting) for planting in db.scalars(statement)]


# ==========================================================================
# Soil
# ==========================================================================
@router.post("/fields/{field_id}/soil-data", response_model=SoilDataOut,
             status_code=status.HTTP_201_CREATED)
def add_soil_sample(field_id: int, payload: SoilDataCreate, farmer: CurrentFarmer,
                    db: DbSession) -> SoilData:
    field = owned_field(db, farmer, field_id)
    sample = SoilData(field_id=field.id, source="farmer_entry", **payload.model_dump())
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return sample


@router.get("/fields/{field_id}/soil-data", response_model=list[SoilDataOut])
def list_soil_samples(field_id: int, farmer: CurrentFarmer, db: DbSession) -> list[SoilData]:
    field = owned_field(db, farmer, field_id)
    return list(
        db.scalars(
            select(SoilData).where(SoilData.field_id == field.id)
            .order_by(SoilData.sample_date.desc().nullslast(), SoilData.id.desc())
        )
    )
