"""Irrigation arithmetic, records and water-use tracking."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import desc, select

from app.api.deps import CurrentFarmer, DbSession, owned_field_crop
from app.db.models import (
    Farm, Field, FieldCrop, IrrigationRecord, Prediction, WaterUse,
)
from app.schemas.core import (
    IrrigationCalculationOut, IrrigationCalculationRequest, IrrigationRecordCreate,
    IrrigationRecordOut, WaterUseCreate, WaterUseOut,
)
from ml.baseline import (
    depth_to_litres, gross_irrigation_requirement, net_irrigation_requirement,
)

router = APIRouter(tags=["irrigation"])


@router.post("/irrigation/calculate", response_model=IrrigationCalculationOut)
def calculate_irrigation(
    payload: IrrigationCalculationRequest, farmer: CurrentFarmer, db: DbSession
) -> IrrigationCalculationOut:
    """Recalculate the requirement under different assumptions.

    This is the what-if tool: take an existing prediction and ask what changes
    if the irrigation system were more efficient, or if forecast rain is counted.
    The stored prediction is not modified, so the original advice stays intact.
    """
    record = db.get(Prediction, payload.prediction_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND",
                    "message": f"No prediction with id {payload.prediction_id}."},
        )
    planting = owned_field_crop(db, farmer, record.field_crop_id)
    field = db.get(Field, planting.field_id)

    efficiency = payload.irrigation_efficiency or record.application_efficiency
    area = payload.area_ha or planting.planting_area_ha or field.area_ha

    assumptions = [
        f"Crop water demand of {record.cwr_mm_day:.2f} mm/day is taken from "
        f"prediction {record.id} and not recomputed.",
        f"Effective rainfall of {record.effective_rainfall_mm:.2f} mm is the "
        f"portion of observed rain that reaches the root zone.",
        f"Application efficiency of {efficiency:.0%} means that share of the "
        f"delivered water reaches the roots.",
        "No soil-water contribution is credited; the root-zone balance is an "
        "estimate with no sensor behind it.",
    ]

    # Forecast rain is credited only at the same effective fraction as observed
    # rain. Counting a forecast at full value would systematically under-water.
    available = record.effective_rainfall_mm
    if payload.forecast_rainfall_mm:
        effective_fraction = (
            record.effective_rainfall_mm / max(
                (record.weather_snapshot or {}).get("rainfall_mm") or 0.0, 1e-9)
            if (record.weather_snapshot or {}).get("rainfall_mm") else 0.75
        )
        credited = payload.forecast_rainfall_mm * min(max(effective_fraction, 0.0), 1.0)
        available += credited
        assumptions.append(
            f"Forecast rainfall of {payload.forecast_rainfall_mm:.1f} mm is credited "
            f"at {min(max(effective_fraction, 0.0), 1.0):.0%}, giving {credited:.2f} mm. "
            f"A forecast is not an observation and may not arrive."
        )

    net = float(net_irrigation_requirement([record.cwr_mm_day], [available], 0.0)[0])
    gross = float(gross_irrigation_requirement([net], efficiency)[0])
    litres = float(depth_to_litres(gross, area)) if area else None

    return IrrigationCalculationOut(
        prediction_id=record.id,
        cwr_mm_day=round(record.cwr_mm_day, 3),
        effective_rainfall_mm=round(record.effective_rainfall_mm, 3),
        forecast_rainfall_mm=payload.forecast_rainfall_mm,
        net_irrigation_mm=round(net, 3),
        gross_irrigation_mm=round(gross, 3),
        gross_irrigation_litres=round(litres, 1) if litres else None,
        application_efficiency=efficiency,
        assumptions=assumptions,
    )


# ==========================================================================
# Records
# ==========================================================================
@router.post("/irrigation/records", response_model=IrrigationRecordOut,
             status_code=status.HTTP_201_CREATED)
def record_irrigation(payload: IrrigationRecordCreate, farmer: CurrentFarmer,
                      db: DbSession) -> IrrigationRecord:
    """Log an irrigation event, and mirror it into the water-use ledger."""
    planting = owned_field_crop(db, farmer, payload.field_crop_id)
    field = db.get(Field, planting.field_id)

    record = IrrigationRecord(**payload.model_dump())
    db.add(record)

    area = planting.planting_area_ha or field.area_ha
    existing = db.scalar(
        select(WaterUse).where(WaterUse.field_crop_id == planting.id,
                               WaterUse.record_date == payload.irrigation_date)
    )
    if existing is None:
        db.add(
            WaterUse(
                field_crop_id=planting.id, record_date=payload.irrigation_date,
                water_used_mm=payload.water_applied_mm,
                water_used_litres=float(depth_to_litres(payload.water_applied_mm, area))
                if area else None,
                water_source=payload.method, area_irrigated_ha=area,
            )
        )
    else:
        # Two applications on one day accumulate rather than overwrite.
        existing.water_used_mm += payload.water_applied_mm
        if area:
            existing.water_used_litres = float(depth_to_litres(existing.water_used_mm, area))

    db.commit()
    db.refresh(record)
    return record


@router.get("/irrigation/records", response_model=list[IrrigationRecordOut])
def list_irrigation_records(
    farmer: CurrentFarmer, db: DbSession,
    field_crop_id: int | None = Query(default=None),
    start_date: dt.date | None = Query(default=None),
    end_date: dt.date | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
) -> list[IrrigationRecord]:
    statement = (
        select(IrrigationRecord)
        .join(FieldCrop, FieldCrop.id == IrrigationRecord.field_crop_id)
        .join(Field, Field.id == FieldCrop.field_id)
        .join(Farm, Farm.id == Field.farm_id)
        .where(Farm.farmer_id == farmer.id)
        .order_by(desc(IrrigationRecord.irrigation_date))
        .limit(limit)
    )
    if field_crop_id is not None:
        owned_field_crop(db, farmer, field_crop_id)
        statement = statement.where(IrrigationRecord.field_crop_id == field_crop_id)
    if start_date:
        statement = statement.where(IrrigationRecord.irrigation_date >= start_date)
    if end_date:
        statement = statement.where(IrrigationRecord.irrigation_date <= end_date)
    return list(db.scalars(statement))


# ==========================================================================
# Water use
# ==========================================================================
@router.post("/water-use", response_model=WaterUseOut, status_code=status.HTTP_201_CREATED)
def record_water_use(payload: WaterUseCreate, farmer: CurrentFarmer,
                     db: DbSession) -> WaterUse:
    planting = owned_field_crop(db, farmer, payload.field_crop_id)
    field = db.get(Field, planting.field_id)
    area = payload.area_irrigated_ha or planting.planting_area_ha or field.area_ha

    existing = db.scalar(
        select(WaterUse).where(WaterUse.field_crop_id == planting.id,
                               WaterUse.record_date == payload.record_date)
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "ALREADY_RECORDED",
                    "message": f"Water use for {payload.record_date} is already "
                               f"recorded for this planting (id {existing.id})."},
        )

    record = WaterUse(
        **payload.model_dump(),
        water_used_litres=float(depth_to_litres(payload.water_used_mm, area)) if area else None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/water-use", response_model=list[WaterUseOut])
def list_water_use(
    farmer: CurrentFarmer, db: DbSession,
    field_crop_id: int | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
) -> list[WaterUse]:
    statement = (
        select(WaterUse)
        .join(FieldCrop, FieldCrop.id == WaterUse.field_crop_id)
        .join(Field, Field.id == FieldCrop.field_id)
        .join(Farm, Farm.id == Field.farm_id)
        .where(Farm.farmer_id == farmer.id)
        .order_by(desc(WaterUse.record_date))
        .limit(limit)
    )
    if field_crop_id is not None:
        owned_field_crop(db, farmer, field_crop_id)
        statement = statement.where(WaterUse.field_crop_id == field_crop_id)
    return list(db.scalars(statement))
