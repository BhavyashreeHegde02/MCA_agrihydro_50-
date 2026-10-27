"""The relational schema.

Seventeen tables covering who the farmer is, what they farm, what the system
predicted, what it advised and which model produced it.

Two decisions are worth stating because they shape everything downstream.

**A prediction stores what it saw.** ``predictions`` keeps the weather snapshot,
the soil snapshot and the exact feature vector alongside the output. Without
that, a prediction from six months ago cannot be explained or reproduced, since
the weather record and the model will both have moved on.

**Demand and irrigation requirement are separate columns.** ``cwr_mm_day`` is
what the crop will transpire; ``net_irrigation_mm`` and ``gross_irrigation_mm``
are what must reach the root zone and what must be delivered. Collapsing them
into one number is the most common way this kind of system gives wrong advice.

JSON columns hold genuinely schema-less snapshots only. Anything queried or
joined is a real column with a real type.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Index,
    Integer, JSON, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for every table."""


class TimestampMixin:
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


# ==========================================================================
# Identity
# ==========================================================================
class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Role gates the research dashboard. Farmers never see other farmers' data.
    role: Mapped[str] = mapped_column(String(20), default="farmer", nullable=False)

    farmer: Mapped["Farmer | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )

    __table_args__ = (
        CheckConstraint("role in ('farmer','researcher','admin')", name="ck_users_role"),
    )


class Farmer(Base, TimestampMixin):
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))
    state: Mapped[str | None] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(100))
    taluk: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(Text)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)

    user: Mapped[User] = relationship(back_populates="farmer")
    farms: Mapped[list["Farm"]] = relationship(
        back_populates="farmer", cascade="all, delete-orphan"
    )


# ==========================================================================
# Land
# ==========================================================================
class Farm(Base, TimestampMixin):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str | None] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(100), index=True)
    taluk: Mapped[str | None] = mapped_column(String(100))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    total_area_ha: Mapped[float] = mapped_column(Float, nullable=False)

    farmer: Mapped[Farmer] = relationship(back_populates="farms")
    fields: Mapped[list["Field"]] = relationship(
        back_populates="farm", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("total_area_ha > 0", name="ck_farms_area_positive"),
        CheckConstraint("latitude is null or (latitude between -90 and 90)",
                        name="ck_farms_latitude"),
        CheckConstraint("longitude is null or (longitude between -180 and 180)",
                        name="ck_farms_longitude"),
    )


class Field(Base, TimestampMixin):
    __tablename__ = "fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    area_ha: Mapped[float] = mapped_column(Float, nullable=False)
    soil_type: Mapped[str | None] = mapped_column(String(64))
    irrigation_method: Mapped[str | None] = mapped_column(String(64))
    # Null means "use the configured default for this irrigation method"; an
    # explicit value is the farmer's own measured or preferred efficiency.
    irrigation_efficiency: Mapped[float | None] = mapped_column(Float)

    farm: Mapped[Farm] = relationship(back_populates="fields")
    plantings: Mapped[list["FieldCrop"]] = relationship(
        back_populates="field", cascade="all, delete-orphan"
    )
    soil_samples: Mapped[list["SoilData"]] = relationship(
        back_populates="field", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("area_ha > 0", name="ck_fields_area_positive"),
        CheckConstraint(
            "irrigation_efficiency is null or "
            "(irrigation_efficiency > 0 and irrigation_efficiency <= 1)",
            name="ck_fields_efficiency_range",
        ),
    )


# ==========================================================================
# Agronomy reference
# ==========================================================================
class Crop(Base, TimestampMixin):
    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str | None] = mapped_column(String(64))
    cycle_length_days: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_source: Mapped[str | None] = mapped_column(String(255))

    stages: Mapped[list["CropGrowthStage"]] = relationship(
        back_populates="crop", cascade="all, delete-orphan",
        order_by="CropGrowthStage.stage_order",
    )
    varieties: Mapped[list["CropVariety"]] = relationship(
        back_populates="crop", cascade="all, delete-orphan",
        order_by="CropVariety.name",
    )


class CropGrowthStage(Base, TimestampMixin):
    __tablename__ = "crop_growth_stages"

    id: Mapped[int] = mapped_column(primary_key=True)
    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crops.id", ondelete="CASCADE"), index=True, nullable=False
    )
    stage_name: Mapped[str] = mapped_column(String(64), nullable=False)
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False)
    start_day: Mapped[int] = mapped_column(Integer, nullable=False)
    end_day: Mapped[int] = mapped_column(Integer, nullable=False)
    # Null on the development stage, where Kc is interpolated rather than fixed.
    kc_value: Mapped[float | None] = mapped_column(Float)
    kc_basis: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)

    crop: Mapped[Crop] = relationship(back_populates="stages")

    __table_args__ = (
        UniqueConstraint("crop_id", "stage_order", name="uq_stage_order_per_crop"),
        CheckConstraint("end_day > start_day", name="ck_stage_duration_positive"),
    )


class CropVariety(Base, TimestampMixin):
    """A named variety of a crop, where one is known.

    Varieties differ in cycle length far more than in crop coefficient - a
    short-duration paddy may finish thirty days sooner than a long-duration
    one, which moves every growth-stage boundary and therefore every Kc the
    prediction uses. So ``cycle_length_days`` is the field that matters here,
    and it is nullable: a variety whose duration this project cannot source is
    still worth recording by name, and falls back to the crop's own cycle.

    Deliberately not mandatory on a planting. Many farmers will not know the
    variety, and refusing to predict without it would be worse than predicting
    with the crop-level figures.
    """

    __tablename__ = "crop_varieties"

    id: Mapped[int] = mapped_column(primary_key=True)
    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crops.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    #: Overrides the crop's cycle length when known.
    cycle_length_days: Mapped[int | None] = mapped_column(Integer)
    duration_class: Mapped[str | None] = mapped_column(String(32))
    #: Where this variety's figures came from. Null means unsourced, which the
    #: interface should say rather than implying an authority that is absent.
    reference_source: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)

    crop: Mapped[Crop] = relationship(back_populates="varieties")

    __table_args__ = (
        UniqueConstraint("crop_id", "name", name="uq_variety_name_per_crop"),
        CheckConstraint(
            "cycle_length_days is null or cycle_length_days > 0",
            name="ck_variety_cycle_positive",
        ),
    )


class DistrictSoilMap(Base, TimestampMixin):
    """Typical soil for a district, used when a field has no reading of its own.

    This exists so the system can offer a starting point without inventing one.
    Every row carries its ``source``, and anything derived from it is marked as
    district-typical rather than measured: a farmer's own sample always wins,
    and a value that came from here must never be presented as though it came
    from their field.

    Soil chemistry does not enter the water balance at all - it informs crop
    suitability. That separation is why this table can be approximate without
    making the irrigation figures approximate.
    """

    __tablename__ = "district_soil_map"

    id: Mapped[int] = mapped_column(primary_key=True)
    state: Mapped[str] = mapped_column(String(64), nullable=False)
    #: Canonical district name. The sources this project holds disagree about
    #: these, so they are normalised through ml.districts before storage.
    district: Mapped[str] = mapped_column(String(64), nullable=False)
    ph_level: Mapped[float | None] = mapped_column(Float)
    nitrogen: Mapped[float | None] = mapped_column(Float)
    phosphorus: Mapped[float | None] = mapped_column(Float)
    potassium: Mapped[float | None] = mapped_column(Float)
    organic_matter: Mapped[float | None] = mapped_column(Float)
    dominant_texture: Mapped[str | None] = mapped_column(String(64))
    #: Which file these figures came from, so a value can be traced back.
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    sample_count: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint("state", "district", name="uq_district_soil_location"),
        CheckConstraint(
            "ph_level is null or (ph_level between 0 and 14)",
            name="ck_district_soil_ph_range",
        ),
        Index("ix_district_soil_lookup", "state", "district"),
    )


class FieldCrop(Base, TimestampMixin):
    """A specific planting: this crop, in this field, sown on this date."""

    __tablename__ = "field_crops"

    id: Mapped[int] = mapped_column(primary_key=True)
    field_id: Mapped[int] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), index=True, nullable=False
    )
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), index=True, nullable=False)
    #: Optional. Most farmers will not know it, and the prediction falls back
    #: to the crop's own cycle length when it is absent.
    variety_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_varieties.id", ondelete="SET NULL"), index=True
    )
    sowing_date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    planting_area_ha: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    field: Mapped[Field] = relationship(back_populates="plantings")
    crop: Mapped[Crop] = relationship()
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="field_crop", cascade="all, delete-orphan"
    )
    irrigation_records: Mapped[list["IrrigationRecord"]] = relationship(
        back_populates="field_crop", cascade="all, delete-orphan"
    )
    water_use: Mapped[list["WaterUse"]] = relationship(
        back_populates="field_crop", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("status in ('active','harvested','abandoned')",
                        name="ck_field_crops_status"),
    )


# ==========================================================================
# Observations
# ==========================================================================
class SoilData(Base, TimestampMixin):
    __tablename__ = "soil_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    field_id: Mapped[int] = mapped_column(
        ForeignKey("fields.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sample_date: Mapped[dt.date | None] = mapped_column(Date)
    ph_level: Mapped[float | None] = mapped_column(Float)
    nitrogen: Mapped[float | None] = mapped_column(Float)
    phosphorus: Mapped[float | None] = mapped_column(Float)
    potassium: Mapped[float | None] = mapped_column(Float)
    organic_matter: Mapped[float | None] = mapped_column(Float)
    texture: Mapped[str | None] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(32), default="farmer_entry", nullable=False)

    field: Mapped[Field] = relationship(back_populates="soil_samples")

    __table_args__ = (
        CheckConstraint("ph_level is null or (ph_level between 0 and 14)",
                        name="ck_soil_ph_range"),
    )


class WeatherObservation(Base, TimestampMixin):
    """Daily weather, tagged by where it came from.

    ``source`` separates the historical research series from live provider data.
    They must never be mixed into a training set without a controlled ingestion
    step, and the column is what makes that separation enforceable.
    """

    __tablename__ = "weather_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_key: Mapped[str] = mapped_column(String(128), nullable=False)
    observed_on: Mapped[dt.date] = mapped_column(Date, nullable=False)
    temperature_mean_c: Mapped[float | None] = mapped_column(Float)
    temperature_min_c: Mapped[float | None] = mapped_column(Float)
    temperature_max_c: Mapped[float | None] = mapped_column(Float)
    humidity_pct: Mapped[float | None] = mapped_column(Float)
    wind_speed_ms: Mapped[float | None] = mapped_column(Float)
    rainfall_mm: Mapped[float | None] = mapped_column(Float)
    solar_radiation_mj_m2: Mapped[float | None] = mapped_column(Float)
    et0_mm_day: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(32), nullable=False)

    __table_args__ = (
        UniqueConstraint("location_key", "observed_on", "source", name="uq_weather_point"),
        Index("ix_weather_location_date", "location_key", "observed_on"),
        CheckConstraint("source in ('historical_research','live_api','forecast','manual')",
                        name="ck_weather_source"),
    )


# ==========================================================================
# Model output
# ==========================================================================
class ModelVersionRecord(Base, TimestampMixin):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(128), nullable=False)
    task: Mapped[str | None] = mapped_column(String(64))
    trained_at: Mapped[str | None] = mapped_column(String(64))
    dataset_fingerprint: Mapped[str | None] = mapped_column(String(64))
    target_definition: Mapped[dict | None] = mapped_column(JSON)
    features: Mapped[list | None] = mapped_column(JSON)
    metrics: Mapped[dict | None] = mapped_column(JSON)
    interval: Mapped[dict | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("model_name", "version", name="uq_model_version"),
        Index("ix_model_versions_active", "is_active"),
    )


class Prediction(Base, TimestampMixin):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    field_crop_id: Mapped[int] = mapped_column(
        ForeignKey("field_crops.id", ondelete="CASCADE"), index=True, nullable=False
    )
    model_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("model_versions.id"), index=True
    )
    prediction_date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)

    # -- agronomic context ------------------------------------------------
    days_after_sowing: Mapped[int] = mapped_column(Integer, nullable=False)
    growth_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    kc_value: Mapped[float] = mapped_column(Float, nullable=False)

    # -- demand, kept distinct from irrigation ----------------------------
    et0_mm_day: Mapped[float] = mapped_column(Float, nullable=False)
    cwr_mm_day: Mapped[float] = mapped_column(Float, nullable=False)
    cwr_baseline_mm_day: Mapped[float] = mapped_column(Float, nullable=False)
    cwr_lower_mm_day: Mapped[float | None] = mapped_column(Float)
    cwr_upper_mm_day: Mapped[float | None] = mapped_column(Float)
    interval_coverage: Mapped[float | None] = mapped_column(Float)
    prediction_source: Mapped[str] = mapped_column(String(32), nullable=False)

    # -- irrigation, kept distinct from demand ----------------------------
    effective_rainfall_mm: Mapped[float] = mapped_column(Float, nullable=False)
    net_irrigation_mm: Mapped[float] = mapped_column(Float, nullable=False)
    gross_irrigation_mm: Mapped[float] = mapped_column(Float, nullable=False)
    gross_irrigation_litres: Mapped[float | None] = mapped_column(Float)
    application_efficiency: Mapped[float] = mapped_column(Float, nullable=False)

    # -- reproducibility snapshots ----------------------------------------
    weather_snapshot: Mapped[dict | None] = mapped_column(JSON)
    soil_snapshot: Mapped[dict | None] = mapped_column(JSON)
    feature_snapshot: Mapped[dict | None] = mapped_column(JSON)
    assumptions: Mapped[dict | None] = mapped_column(JSON)

    field_crop: Mapped[FieldCrop] = relationship(back_populates="predictions")
    model_version: Mapped[ModelVersionRecord | None] = relationship()
    advisories: Mapped[list["Advisory"]] = relationship(
        back_populates="prediction", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("cwr_mm_day >= 0", name="ck_predictions_cwr_non_negative"),
        CheckConstraint("gross_irrigation_mm >= net_irrigation_mm",
                        name="ck_predictions_gross_at_least_net"),
        CheckConstraint("prediction_source in ('ml_model','physics_baseline')",
                        name="ck_predictions_source"),
        Index("ix_predictions_field_crop_date", "field_crop_id", "prediction_date"),
    )


class Advisory(Base, TimestampMixin):
    __tablename__ = "advisories"

    id: Mapped[int] = mapped_column(primary_key=True)
    prediction_id: Mapped[int] = mapped_column(
        ForeignKey("predictions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    advisory_type: Mapped[str] = mapped_column(String(64), nullable=False)
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    action_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    prediction: Mapped[Prediction] = relationship(back_populates="advisories")

    __table_args__ = (
        CheckConstraint("priority in ('low','medium','high')", name="ck_advisories_priority"),
    )


# ==========================================================================
# Farmer records
# ==========================================================================
class IrrigationRecord(Base, TimestampMixin):
    __tablename__ = "irrigation_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    field_crop_id: Mapped[int] = mapped_column(
        ForeignKey("field_crops.id", ondelete="CASCADE"), index=True, nullable=False
    )
    irrigation_date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    method: Mapped[str | None] = mapped_column(String(64))
    duration_hours: Mapped[float | None] = mapped_column(Float)
    water_applied_mm: Mapped[float] = mapped_column(Float, nullable=False)
    application_efficiency: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)

    field_crop: Mapped[FieldCrop] = relationship(back_populates="irrigation_records")

    __table_args__ = (
        CheckConstraint("water_applied_mm >= 0", name="ck_irrigation_non_negative"),
    )


class WaterUse(Base, TimestampMixin):
    __tablename__ = "water_use"

    id: Mapped[int] = mapped_column(primary_key=True)
    field_crop_id: Mapped[int] = mapped_column(
        ForeignKey("field_crops.id", ondelete="CASCADE"), index=True, nullable=False
    )
    record_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    water_used_mm: Mapped[float] = mapped_column(Float, nullable=False)
    water_used_litres: Mapped[float | None] = mapped_column(Float)
    water_source: Mapped[str | None] = mapped_column(String(64))
    area_irrigated_ha: Mapped[float | None] = mapped_column(Float)
    estimated_cost: Mapped[float | None] = mapped_column(Float)

    field_crop: Mapped[FieldCrop] = relationship(back_populates="water_use")

    __table_args__ = (
        UniqueConstraint("field_crop_id", "record_date", name="uq_water_use_per_day"),
    )


class DataQualityAlert(Base, TimestampMixin):
    __tablename__ = "data_quality_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    prediction_id: Mapped[int | None] = mapped_column(
        ForeignKey("predictions.id", ondelete="CASCADE"), index=True
    )
    scope: Mapped[str] = mapped_column(String(64), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    detected_value: Mapped[float | None] = mapped_column(Float)
    expected_range: Mapped[dict | None] = mapped_column(JSON)

    __table_args__ = (
        CheckConstraint("severity in ('info','warning','error')",
                        name="ck_alerts_severity"),
    )
