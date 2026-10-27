"""Analytics, weather, advisories, data quality and the research dashboard."""

from __future__ import annotations

import datetime as dt
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentFarmer, DbSession, ResearchUser, owned_farm, owned_field_crop
from app.db.models import (
    Advisory, Crop, DataQualityAlert, Farm, Field, FieldCrop, ModelVersionRecord,
    Prediction, User, WaterUse,
)
from app.schemas.core import AnalyticsOut, WeatherOut
from app.services.ml_service import model_service
from app.services.weather_service import WeatherUnavailableError, weather_service
from ml import config as ml_config

router = APIRouter(tags=["analytics"])


# ==========================================================================
# Weather
# ==========================================================================
@router.get("/weather/current", response_model=WeatherOut)
def current_weather(
    farmer: CurrentFarmer, db: DbSession,
    farm_id: int | None = Query(default=None),
    latitude: float | None = Query(default=None, ge=-90, le=90),
    longitude: float | None = Query(default=None, ge=-180, le=180),
) -> WeatherOut:
    lat, lon = _resolve_coordinates(db, farmer, farm_id, latitude, longitude)
    try:
        reading = weather_service.current(lat, lon)
    except WeatherUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "WEATHER_UNAVAILABLE", "message": str(error)},
        ) from error
    return WeatherOut(**reading.as_dict())


@router.get("/weather/forecast", response_model=list[WeatherOut])
def weather_forecast(
    farmer: CurrentFarmer, db: DbSession,
    farm_id: int | None = Query(default=None),
    latitude: float | None = Query(default=None, ge=-90, le=90),
    longitude: float | None = Query(default=None, ge=-180, le=180),
    days: int = Query(default=7, ge=1, le=16),
) -> list[WeatherOut]:
    lat, lon = _resolve_coordinates(db, farmer, farm_id, latitude, longitude)
    try:
        readings = weather_service.forecast(lat, lon, days=days)
    except WeatherUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "WEATHER_UNAVAILABLE", "message": str(error)},
        ) from error
    return [WeatherOut(**r.as_dict()) for r in readings]


@router.get("/weather/status")
def weather_status() -> dict[str, Any]:
    return weather_service.status()


def _resolve_coordinates(db, farmer, farm_id, latitude, longitude) -> tuple[float, float]:
    if latitude is not None and longitude is not None:
        return latitude, longitude
    if farm_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "LOCATION_REQUIRED",
                    "message": "Supply farm_id, or latitude and longitude."},
        )
    farm = owned_farm(db, farmer, farm_id)
    if farm.latitude is None or farm.longitude is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "FARM_HAS_NO_COORDINATES",
                    "message": f"Farm {farm_id} has no coordinates recorded."},
        )
    return farm.latitude, farm.longitude


# ==========================================================================
# Analytics
# ==========================================================================
@router.get("/analytics/cwr", response_model=AnalyticsOut)
def cwr_analytics(
    farmer: CurrentFarmer, db: DbSession,
    field_crop_id: int | None = Query(default=None),
    start_date: dt.date | None = Query(default=None),
    end_date: dt.date | None = Query(default=None),
) -> AnalyticsOut:
    """Predicted demand against water actually applied.

    The balance is the number worth looking at: persistent over-application
    wastes water, persistent under-application stresses the crop. It compares a
    modelled demand with a farmer-reported application, so it is a planning
    indicator rather than a measurement of either quantity.
    """
    statement = (
        select(Prediction)
        .join(FieldCrop, FieldCrop.id == Prediction.field_crop_id)
        .join(Field, Field.id == FieldCrop.field_id)
        .join(Farm, Farm.id == Field.farm_id)
        .where(Farm.farmer_id == farmer.id)
        .order_by(Prediction.prediction_date)
    )
    if field_crop_id is not None:
        owned_field_crop(db, farmer, field_crop_id)
        statement = statement.where(Prediction.field_crop_id == field_crop_id)
    if start_date:
        statement = statement.where(Prediction.prediction_date >= start_date)
    if end_date:
        statement = statement.where(Prediction.prediction_date <= end_date)

    predictions = list(db.scalars(statement))

    water_statement = (
        select(WaterUse)
        .join(FieldCrop, FieldCrop.id == WaterUse.field_crop_id)
        .join(Field, Field.id == FieldCrop.field_id)
        .join(Farm, Farm.id == Field.farm_id)
        .where(Farm.farmer_id == farmer.id)
    )
    if field_crop_id is not None:
        water_statement = water_statement.where(WaterUse.field_crop_id == field_crop_id)
    water_records = list(db.scalars(water_statement))

    applied = sum(w.water_used_mm for w in water_records)
    demand = sum(p.cwr_mm_day for p in predictions)
    net = sum(p.net_irrigation_mm for p in predictions)
    gross = sum(p.gross_irrigation_mm for p in predictions)

    by_stage: dict[str, dict[str, float]] = {}
    for prediction in predictions:
        bucket = by_stage.setdefault(
            prediction.growth_stage, {"days": 0, "demand_mm": 0.0, "gross_mm": 0.0}
        )
        bucket["days"] += 1
        bucket["demand_mm"] += prediction.cwr_mm_day
        bucket["gross_mm"] += prediction.gross_irrigation_mm

    return AnalyticsOut(
        field_crop_id=field_crop_id,
        period_start=predictions[0].prediction_date if predictions else None,
        period_end=predictions[-1].prediction_date if predictions else None,
        predictions=len(predictions),
        total_predicted_demand_mm=round(demand, 2),
        total_net_irrigation_mm=round(net, 2),
        total_gross_irrigation_mm=round(gross, 2),
        total_water_applied_mm=round(applied, 2),
        balance_mm=round(applied - gross, 2),
        by_growth_stage=[
            {"growth_stage": stage, "days": values["days"],
             "total_demand_mm": round(values["demand_mm"], 2),
             "mean_demand_mm_day": round(values["demand_mm"] / values["days"], 3),
             "total_gross_irrigation_mm": round(values["gross_mm"], 2)}
            for stage, values in sorted(by_stage.items())
        ],
        daily_series=[
            {"date": str(p.prediction_date), "cwr_mm_day": round(p.cwr_mm_day, 3),
             "baseline_mm_day": round(p.cwr_baseline_mm_day, 3),
             "lower": round(p.cwr_lower_mm_day, 3) if p.cwr_lower_mm_day else None,
             "upper": round(p.cwr_upper_mm_day, 3) if p.cwr_upper_mm_day else None,
             "gross_irrigation_mm": round(p.gross_irrigation_mm, 3),
             "effective_rainfall_mm": round(p.effective_rainfall_mm, 3),
             "growth_stage": p.growth_stage, "kc": round(p.kc_value, 3)}
            for p in predictions
        ],
        note=(
            "Predicted demand is modelled; applied water is farmer-reported. The "
            "balance compares a model with a self-report, so treat it as a "
            "planning indicator rather than a measured water balance."
        ),
    )


@router.get("/advisory")
def latest_advisories(
    farmer: CurrentFarmer, db: DbSession,
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    """The most recent advice across all of this farmer's plantings."""
    rows = db.execute(
        select(Advisory, Prediction, Crop)
        .join(Prediction, Prediction.id == Advisory.prediction_id)
        .join(FieldCrop, FieldCrop.id == Prediction.field_crop_id)
        .join(Crop, Crop.id == FieldCrop.crop_id)
        .join(Field, Field.id == FieldCrop.field_id)
        .join(Farm, Farm.id == Field.farm_id)
        .where(Farm.farmer_id == farmer.id)
        .order_by(Prediction.prediction_date.desc(), Advisory.id.desc())
        .limit(limit)
    ).all()

    return {
        "advisories": [
            {"id": advisory.id, "prediction_id": prediction.id,
             "prediction_date": str(prediction.prediction_date),
             "crop": crop.name, "advisory_type": advisory.advisory_type,
             "headline": advisory.headline, "detail": advisory.detail,
             "priority": advisory.priority, "action_required": advisory.action_required}
            for advisory, prediction, crop in rows
        ],
        "count": len(rows),
    }


# ==========================================================================
# Data quality
# ==========================================================================
@router.get("/data-quality/summary")
def data_quality_summary(db: DbSession) -> dict[str, Any]:
    """What the system knows about the trustworthiness of its own inputs.

    Surfacing this in the app is deliberate. A farmer acting on an estimate
    built from estimated inputs should be able to see that.
    """
    site = ml_config.load_site_config()
    alerts = db.scalar(select(func.count()).select_from(DataQualityAlert)) or 0

    predictions_with_estimates = db.scalar(
        select(func.count()).select_from(Prediction)
        .where(Prediction.prediction_source == "physics_baseline")
    ) or 0
    total_predictions = db.scalar(select(func.count()).select_from(Prediction)) or 0

    return {
        "site": {
            "resolution_status": site.resolution_status,
            "is_provisional": site.is_provisional,
            "latitude_deg": site.latitude_deg,
            "elevation_m": site.elevation_m,
            "impact": (
                "Across the plausible site envelope, reference evapotranspiration "
                "varies by under two percent. The limitation is documented rather "
                "than eliminated."
            ),
        },
        "target": {
            "provenance": "reference_derived",
            "is_field_observed": False,
            "statement": (
                "The model was trained on a FAO-56 reference-derived crop "
                "evapotranspiration, not on observed field water use. No "
                "independently observed water requirement exists in this project's "
                "data."
            ),
        },
        "model": model_service.status(),
        "weather": weather_service.status(),
        "counters": {
            "total_predictions": total_predictions,
            "served_from_physics_baseline": predictions_with_estimates,
            "open_alerts": alerts,
        },
    }


@router.get("/data-quality/alerts")
def data_quality_alerts(
    db: DbSession, limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    alerts = list(
        db.scalars(select(DataQualityAlert).order_by(DataQualityAlert.id.desc()).limit(limit))
    )
    return {
        "alerts": [
            {"id": a.id, "scope": a.scope, "alert_type": a.alert_type,
             "severity": a.severity, "description": a.description,
             "detected_value": a.detected_value, "expected_range": a.expected_range,
             "created_at": a.created_at.isoformat()}
            for a in alerts
        ],
        "count": len(alerts),
    }


# ==========================================================================
# Research dashboard
# ==========================================================================
@router.get("/admin/model-performance")
def model_performance(user: ResearchUser, db: DbSession) -> dict[str, Any]:
    """Every trained model version, with the caveats that must accompany them."""
    from ml import registry

    versions = registry.list_versions()
    records = list(db.scalars(select(ModelVersionRecord).order_by(ModelVersionRecord.id)))
    _ = user

    return {
        "registry": versions.to_dict(orient="records") if not versions.empty else [],
        "database_records": [
            {"model_name": r.model_name, "version": r.version, "algorithm": r.algorithm,
             "task": r.task, "is_active": r.is_active, "metrics": r.metrics,
             "interval": r.interval}
            for r in records
        ],
        "active": model_service.status(),
        "reporting_caveats": [
            "The 'surrogate' task is a diagnostic. Its target is a deterministic "
            "function of its inputs, so near-perfect scores confirm the pipeline "
            "is wired correctly and say nothing about predictive skill.",
            "The 'reduced_input' task is the research result: it withholds solar "
            "radiation and wind speed, which a farmer cannot measure.",
            "Every metric is computed on a chronologically held-out test period.",
            "Prediction intervals are split-conformal and their coverage was "
            "measured on the test set, not assumed.",
        ],
    }


@router.get("/admin/dataset-statistics")
def dataset_statistics(user: ResearchUser) -> dict[str, Any]:
    """Provenance of the data behind the served model."""
    import json

    _ = user
    metadata_path = ml_config.PROCESSED_DIR / "preprocessing_metadata.json"
    assumptions_path = ml_config.ARTIFACTS_DIR / "assumptions.json"

    payload: dict[str, Any] = {}
    if metadata_path.exists():
        payload["preprocessing"] = json.loads(metadata_path.read_text(encoding="utf-8"))
    if assumptions_path.exists():
        payload["baseline_assumptions"] = json.loads(
            assumptions_path.read_text(encoding="utf-8"))
    payload["target"] = (model_service.metadata or {}).get("target_definition")
    return payload


@router.get("/admin/prediction-statistics")
def prediction_statistics(user: ResearchUser, db: DbSession) -> dict[str, Any]:
    _ = user
    total = db.scalar(select(func.count()).select_from(Prediction)) or 0
    by_source = db.execute(
        select(Prediction.prediction_source, func.count())
        .group_by(Prediction.prediction_source)
    ).all()
    by_stage = db.execute(
        select(Prediction.growth_stage, func.count(), func.avg(Prediction.cwr_mm_day))
        .group_by(Prediction.growth_stage)
    ).all()

    return {
        "total_predictions": total,
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "farms": db.scalar(select(func.count()).select_from(Farm)) or 0,
        "plantings": db.scalar(select(func.count()).select_from(FieldCrop)) or 0,
        "by_source": [{"source": s, "count": c} for s, c in by_source],
        "by_growth_stage": [
            {"growth_stage": s, "count": c, "mean_cwr_mm_day": round(float(m or 0), 3)}
            for s, c, m in by_stage
        ],
    }
