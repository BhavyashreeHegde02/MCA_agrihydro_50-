"""The core prediction flow.

    request -> validate -> gather context -> physics baseline -> ML inference
            -> conformal interval -> irrigation arithmetic -> advisory -> persist

The physics baseline runs **every** time, not only as a fallback. It gives the
response a reference figure the machine-learning number can be compared against,
which is what lets a farmer -- and a reviewer -- notice when the model has
wandered somewhere implausible.

When no model is promoted the endpoint still answers, serving the baseline and
marking the machine-learning fields unavailable with a reason. It never invents
a confidence value to fill the gap.
"""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import desc, select

from app.api.deps import CurrentFarmer, DbSession, owned_field_crop
from app.db.models import (
    Advisory, Crop, Farm, Field, FieldCrop, ModelVersionRecord, Prediction,
)
from app.schemas.core import (
    AdvisoryOut, ExplanationOut, IntervalOut, ModelInfoOut, PredictionOut,
    PredictionRequest, PredictionSummary,
)
from app.services import advisory_service
from app.services.baseline_service import (
    WeatherInput, build_model_features, compute_field_day,
)
from app.services.ml_service import ModelUnavailableError, model_service
from app.services.weather_service import WeatherUnavailableError, weather_service

router = APIRouter(prefix="/predictions", tags=["predictions"])


def _resolve_weather(payload: PredictionRequest, farm: Farm, target_date: dt.date) -> WeatherInput:
    """Use the caller's readings, or fetch them from the configured provider."""
    if payload.weather is not None:
        return WeatherInput(date=target_date, source="manual",
                            **payload.weather.model_dump())

    if farm.latitude is None or farm.longitude is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "FARM_HAS_NO_COORDINATES",
                "message": (
                    "Fetching weather needs the farm's latitude and longitude. "
                    "Add them to the farm, or send the weather readings in the "
                    "request instead."
                ),
            },
        )
    try:
        reading = weather_service.current(farm.latitude, farm.longitude)
    except WeatherUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "WEATHER_UNAVAILABLE", "message": str(error)},
        ) from error

    return WeatherInput(
        date=target_date,
        temperature_mean_c=reading.temperature_mean_c,
        temperature_min_c=reading.temperature_min_c,
        temperature_max_c=reading.temperature_max_c,
        humidity_pct=reading.humidity_pct,
        rainfall_mm=reading.rainfall_mm,
        wind_speed_ms=reading.wind_speed_ms,
        solar_radiation_mj_m2=reading.solar_radiation_mj_m2,
        source=reading.source,
    )


@router.post("/cwr", response_model=PredictionOut)
def predict_crop_water_requirement(
    payload: PredictionRequest, farmer: CurrentFarmer, db: DbSession
) -> PredictionOut:
    """Estimate today's crop water demand and the irrigation it implies."""
    planting = owned_field_crop(db, farmer, payload.field_crop_id)
    field = db.get(Field, planting.field_id)
    farm = db.get(Farm, field.farm_id)
    crop = db.get(Crop, planting.crop_id)

    target_date = payload.prediction_date or dt.date.today()
    if target_date < planting.sowing_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "DATE_BEFORE_SOWING",
                "message": (
                    f"The prediction date {target_date} is before this crop was sown "
                    f"on {planting.sowing_date}."
                ),
            },
        )

    weather = _resolve_weather(payload, farm, target_date)
    area_ha = planting.planting_area_ha or field.area_ha

    # ---- physics baseline, always ---------------------------------------
    try:
        baseline = compute_field_day(
            weather=weather,
            crop_slug=crop.slug,
            sowing_date=planting.sowing_date,
            area_ha=area_ha,
            irrigation_method=field.irrigation_method,
            irrigation_efficiency_override=(
                payload.irrigation_efficiency_override or field.irrigation_efficiency
            ),
            soil_type=field.soil_type,
        )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "NO_CROP_COEFFICIENT",
                    "message": f"No growth-stage crop coefficient curve exists for "
                               f"{crop.slug!r}: {error}"},
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "BASELINE_FAILED", "message": str(error)},
        ) from error

    # ---- machine learning, when a model is promoted ----------------------
    cwr = baseline.etc_mm_day
    lower = upper = coverage = None
    source = "physics_baseline"
    model_info = ModelInfoOut(available=False,
                              unavailable_reason=model_service.unavailable_reason)
    features: dict = {}

    if model_service.load_failed:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "PREDICTION_MODEL_UNAVAILABLE",
                "message": model_service.unavailable_reason,
            },
        )

    if model_service.is_available:
        features = build_model_features(
            weather=weather, crop_slug=crop.slug,
            days_after_sowing=baseline.days_after_sowing,
            growth_stage=baseline.growth_stage,
            rain_7d_mm=payload.rain_last_7_days_mm,
            rain_30d_mm=payload.rain_last_30_days_mm,
            days_since_rain=payload.days_since_rain,
        )
        try:
            prediction = model_service.predict(features)
            cwr = prediction.value_mm_day
            lower, upper = prediction.lower_mm_day, prediction.upper_mm_day
            coverage = prediction.nominal_coverage
            source = "ml_model"
            metadata = model_service.metadata
            model_info = ModelInfoOut(
                available=True, name=prediction.model_name,
                version=prediction.model_version, algorithm=prediction.algorithm,
                task=(metadata.get("task") or {}).get("task"),
            )
        except ModelUnavailableError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "PREDICTION_MODEL_UNAVAILABLE",
                    "message": str(error),
                },
            ) from error

    # ---- irrigation arithmetic on the served demand ----------------------
    from ml.baseline import (
        depth_to_litres, gross_irrigation_requirement, net_irrigation_requirement,
    )

    net = float(net_irrigation_requirement([cwr], [baseline.effective_rainfall_mm], 0.0)[0])
    gross = float(gross_irrigation_requirement([net], baseline.application_efficiency)[0])
    litres = float(depth_to_litres(gross, area_ha)) if area_ha else None

    # ---- previous prediction, for the trend message ----------------------
    previous = db.scalar(
        select(Prediction)
        .where(Prediction.field_crop_id == planting.id,
               Prediction.prediction_date < target_date)
        .order_by(desc(Prediction.prediction_date))
        .limit(1)
    )

    advisories = advisory_service.build_advisories(
        crop_name=crop.name,
        growth_stage=baseline.growth_stage,
        days_after_sowing=baseline.days_after_sowing,
        etc_mm_day=cwr, etc_lower=lower, etc_upper=upper, coverage=coverage,
        rainfall_mm=weather.rainfall_mm,
        effective_rainfall_mm=baseline.effective_rainfall_mm,
        net_irrigation_mm=net, gross_irrigation_mm=gross,
        gross_irrigation_litres=litres,
        application_efficiency=baseline.application_efficiency,
        area_ha=area_ha,
        forecast_rainfall_mm=payload.forecast_rainfall_mm,
        previous_etc_mm_day=previous.cwr_mm_day if previous else None,
        estimated_inputs=baseline.et0_inputs_estimated,
        prediction_source=source,
    )

    # ---- persist ---------------------------------------------------------
    record_id = None
    if payload.persist:
        model_version_id = _ensure_model_version_row(db) if source == "ml_model" else None
        record = Prediction(
            field_crop_id=planting.id,
            model_version_id=model_version_id,
            prediction_date=target_date,
            days_after_sowing=baseline.days_after_sowing,
            growth_stage=baseline.growth_stage,
            kc_value=baseline.kc,
            et0_mm_day=baseline.et0_mm_day,
            cwr_mm_day=cwr,
            cwr_baseline_mm_day=baseline.etc_mm_day,
            cwr_lower_mm_day=lower,
            cwr_upper_mm_day=upper,
            interval_coverage=coverage,
            prediction_source=source,
            effective_rainfall_mm=baseline.effective_rainfall_mm,
            net_irrigation_mm=net,
            gross_irrigation_mm=gross,
            gross_irrigation_litres=litres,
            application_efficiency=baseline.application_efficiency,
            weather_snapshot=weather.as_snapshot(),
            soil_snapshot={"soil_type": field.soil_type,
                           "irrigation_method": field.irrigation_method},
            feature_snapshot=features or None,
            assumptions=baseline.assumptions,
        )
        db.add(record)
        db.flush()
        for message in advisories:
            db.add(Advisory(prediction_id=record.id, **message.as_dict()))
        db.commit()
        db.refresh(record)
        record_id = record.id

    return PredictionOut(
        id=record_id,
        field_crop_id=planting.id,
        prediction_date=target_date,
        crop_name=crop.name,
        crop_slug=crop.slug,
        growth_stage=baseline.growth_stage,
        days_after_sowing=baseline.days_after_sowing,
        kc_value=round(baseline.kc, 4),
        et0_mm_day=round(baseline.et0_mm_day, 3),
        cwr_mm_day=round(cwr, 3),
        cwr_baseline_mm_day=round(baseline.etc_mm_day, 3),
        interval=IntervalOut(
            lower_mm_day=round(lower, 3) if lower is not None else None,
            upper_mm_day=round(upper, 3) if upper is not None else None,
            nominal_coverage=coverage,
            method=(model_service.interval_settings.get("method")
                    if model_service.is_available else None),
            note=(
                "Split conformal interval, calibrated on held-out data. Its "
                "coverage was measured, not assumed."
                if coverage else
                "No interval: this figure is the physics reference, which has no "
                "calibrated uncertainty attached."
            ),
        ),
        rainfall_mm=weather.rainfall_mm,
        effective_rainfall_mm=round(baseline.effective_rainfall_mm, 3),
        net_irrigation_mm=round(net, 3),
        gross_irrigation_mm=round(gross, 3),
        gross_irrigation_litres=round(litres, 1) if litres is not None else None,
        application_efficiency=baseline.application_efficiency,
        water_need=advisory_service.water_need_status(cwr),
        model_info=model_info,
        prediction_source=source,
        estimated_inputs=baseline.et0_inputs_estimated,
        advisories=[AdvisoryOut(**m.as_dict()) for m in advisories],
        assumptions=baseline.assumptions,
        weather_used=weather.as_snapshot(),
    )


def _ensure_model_version_row(db) -> int | None:
    """Mirror the promoted model into the database so predictions can join to it."""
    metadata = model_service.metadata
    name, version = metadata.get("model_name"), metadata.get("version")
    if not name or not version:
        return None

    existing = db.scalar(
        select(ModelVersionRecord).where(
            ModelVersionRecord.model_name == name, ModelVersionRecord.version == version
        )
    )
    if existing is not None:
        return existing.id

    db.execute(
        ModelVersionRecord.__table__.update().values(is_active=False)
    )
    record = ModelVersionRecord(
        model_name=name, version=version,
        algorithm=str(metadata.get("algorithm", "unknown")),
        task=(metadata.get("task") or {}).get("task"),
        trained_at=metadata.get("saved_at"),
        dataset_fingerprint=metadata.get("dataset_fingerprint"),
        target_definition=metadata.get("target_definition"),
        features=metadata.get("feature_order"),
        metrics=metadata.get("metrics"),
        interval=metadata.get("interval"),
        is_active=True,
    )
    db.add(record)
    db.flush()
    return record.id


# ==========================================================================
# History and explanation
# ==========================================================================
@router.get("/history", response_model=list[PredictionSummary])
def prediction_history(
    farmer: CurrentFarmer, db: DbSession,
    field_crop_id: int | None = Query(default=None),
    start_date: dt.date | None = Query(default=None),
    end_date: dt.date | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Prediction]:
    statement = (
        select(Prediction)
        .join(FieldCrop, FieldCrop.id == Prediction.field_crop_id)
        .join(Field, Field.id == FieldCrop.field_id)
        .join(Farm, Farm.id == Field.farm_id)
        .where(Farm.farmer_id == farmer.id)
        .order_by(desc(Prediction.prediction_date), desc(Prediction.id))
        .limit(limit)
    )
    if field_crop_id is not None:
        owned_field_crop(db, farmer, field_crop_id)
        statement = statement.where(Prediction.field_crop_id == field_crop_id)
    if start_date:
        statement = statement.where(Prediction.prediction_date >= start_date)
    if end_date:
        statement = statement.where(Prediction.prediction_date <= end_date)
    return list(db.scalars(statement))


@router.get("/{prediction_id}", response_model=dict)
def prediction_detail(prediction_id: int, farmer: CurrentFarmer, db: DbSession) -> dict:
    record = _owned_prediction(db, farmer, prediction_id)
    crop = db.get(Crop, db.get(FieldCrop, record.field_crop_id).crop_id)
    return {
        "id": record.id,
        "field_crop_id": record.field_crop_id,
        "prediction_date": str(record.prediction_date),
        "crop_name": crop.name if crop else None,
        "growth_stage": record.growth_stage,
        "days_after_sowing": record.days_after_sowing,
        "kc_value": record.kc_value,
        "et0_mm_day": record.et0_mm_day,
        "cwr_mm_day": record.cwr_mm_day,
        "cwr_baseline_mm_day": record.cwr_baseline_mm_day,
        "cwr_lower_mm_day": record.cwr_lower_mm_day,
        "cwr_upper_mm_day": record.cwr_upper_mm_day,
        "interval_coverage": record.interval_coverage,
        "effective_rainfall_mm": record.effective_rainfall_mm,
        "net_irrigation_mm": record.net_irrigation_mm,
        "gross_irrigation_mm": record.gross_irrigation_mm,
        "gross_irrigation_litres": record.gross_irrigation_litres,
        "application_efficiency": record.application_efficiency,
        "prediction_source": record.prediction_source,
        "weather_snapshot": record.weather_snapshot,
        "soil_snapshot": record.soil_snapshot,
        "feature_snapshot": record.feature_snapshot,
        "assumptions": record.assumptions,
        "advisories": [
            {"advisory_type": a.advisory_type, "headline": a.headline,
             "detail": a.detail, "priority": a.priority,
             "action_required": a.action_required}
            for a in record.advisories
        ],
        "created_at": record.created_at.isoformat(),
    }


@router.get("/{prediction_id}/explanation", response_model=ExplanationOut)
def prediction_explanation(prediction_id: int, farmer: CurrentFarmer,
                           db: DbSession) -> ExplanationOut:
    """Why the model produced this number, and how it compares to the reference."""
    record = _owned_prediction(db, farmer, prediction_id)

    comparison = {
        "baseline_cwr_mm_day": round(record.cwr_baseline_mm_day, 3),
        "served_cwr_mm_day": round(record.cwr_mm_day, 3),
        "difference_mm_day": round(record.cwr_mm_day - record.cwr_baseline_mm_day, 3),
        "note": (
            "The physics reference is computed on every request. A large gap "
            "between it and the model output is a signal to investigate, not a "
            "sign that either is correct."
        ),
    }

    if record.prediction_source != "ml_model" or not record.feature_snapshot:
        return ExplanationOut(
            prediction_id=record.id, available=False,
            reason=("This prediction came from the physics reference rather than a "
                    "model, so there is no learned behaviour to explain. The "
                    "calculation chain is in the prediction's assumptions field."),
            baseline_comparison=comparison,
        )

    from app.services.ml_service import Prediction as MLPrediction

    explanation = model_service.explain(
        record.feature_snapshot,
        MLPrediction(
            value_mm_day=record.cwr_mm_day, lower_mm_day=record.cwr_lower_mm_day,
            upper_mm_day=record.cwr_upper_mm_day, nominal_coverage=record.interval_coverage,
            model_name="", model_version="", algorithm="", source="ml_model",
        ),
    )
    return ExplanationOut(
        prediction_id=record.id,
        available=explanation.get("available", False),
        method=explanation.get("method"),
        note=explanation.get("note"),
        reason=explanation.get("reason"),
        prediction_mm_day=explanation.get("prediction_mm_day"),
        contributors=explanation.get("contributors", []),
        baseline_comparison=comparison,
    )


def _owned_prediction(db, farmer, prediction_id: int) -> Prediction:
    record = db.get(Prediction, prediction_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND",
                    "message": f"No prediction with id {prediction_id} was found."},
        )
    owned_field_crop(db, farmer, record.field_crop_id)
    return record
