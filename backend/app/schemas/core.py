"""Request and response models for the whole API.

Validation lives here rather than in the handlers. A negative field area, a pH
of 20 or a humidity of 150 is rejected at the boundary with a message naming the
field, which is both safer and kinder to the client than a database error.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

ORM = ConfigDict(from_attributes=True)


# ==========================================================================
# Auth
# ==========================================================================
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72,
                          description="At least 8 characters; bcrypt caps at 72 bytes")
    full_name: str = Field(min_length=2, max_length=255)
    phone: str = Field(description="10-digit Indian mobile number")
    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    taluk: str | None = Field(default=None, max_length=100)

    @field_validator("full_name")
    @classmethod
    def _trim_full_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Enter your full name.")
        return value

    @field_validator("password")
    @classmethod
    def _require_password_complexity(cls, value: str) -> str:
        message = (
            "Password must contain at least 8 characters, one uppercase letter, "
            "one lowercase letter, one number and one special character."
        )
        if not all((
            re.search(r"[A-Z]", value),
            re.search(r"[a-z]", value),
            re.search(r"\d", value),
            re.search(r"[^A-Za-z\d]", value),
        )):
            raise ValueError(message)
        return value

    @field_validator("phone")
    @classmethod
    def _validate_indian_mobile(cls, value: str) -> str:
        if not re.fullmatch(r"\d{10}", value):
            raise ValueError("Mobile number must contain exactly 10 digits.")
        if not re.fullmatch(r"[6-9]\d{9}", value):
            raise ValueError("Mobile number must start with 6, 7, 8 or 9.")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ORM
    id: int
    email: str
    full_name: str
    phone: str | None
    role: str
    is_active: bool
    created_at: dt.datetime


# ==========================================================================
# Farmer, farm, field
# ==========================================================================
class FarmerOut(BaseModel):
    model_config = ORM
    id: int
    user_id: int
    full_name: str
    phone: str | None
    state: str | None
    district: str | None
    taluk: str | None
    address: str | None
    preferred_language: str


class FarmerUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    state: str | None = None
    district: str | None = None
    taluk: str | None = None
    address: str | None = None
    preferred_language: str | None = Field(default=None, max_length=10)


class FarmCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    state: str | None = None
    district: str | None = None
    taluk: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    total_area_ha: float = Field(gt=0, le=100_000, description="Total farm area in hectares")


class FarmUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    state: str | None = None
    district: str | None = None
    taluk: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    total_area_ha: float | None = Field(default=None, gt=0, le=100_000)


class FieldOut(BaseModel):
    model_config = ORM
    id: int
    farm_id: int
    name: str
    area_ha: float
    soil_type: str | None
    irrigation_method: str | None
    irrigation_efficiency: float | None


class FarmOut(BaseModel):
    model_config = ORM
    id: int
    farmer_id: int
    name: str
    state: str | None
    district: str | None
    taluk: str | None
    latitude: float | None
    longitude: float | None
    total_area_ha: float
    created_at: dt.datetime


class FarmDetail(FarmOut):
    fields: list[FieldOut] = Field(default_factory=list)


IrrigationMethod = Literal["drip", "sprinkler", "furrow", "flood", "basin", "surface"]


class FieldCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    area_ha: float = Field(gt=0, le=100_000)
    soil_type: str | None = Field(default=None, max_length=64)
    irrigation_method: IrrigationMethod | None = None
    irrigation_efficiency: float | None = Field(
        default=None, gt=0, le=1,
        description="Leave unset to use the configured default for the method",
    )


class FieldUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    area_ha: float | None = Field(default=None, gt=0, le=100_000)
    soil_type: str | None = None
    irrigation_method: IrrigationMethod | None = None
    irrigation_efficiency: float | None = Field(default=None, gt=0, le=1)


# ==========================================================================
# Crops
# ==========================================================================
class GrowthStageOut(BaseModel):
    model_config = ORM
    id: int
    stage_name: str
    stage_order: int
    start_day: int
    end_day: int
    kc_value: float | None
    kc_basis: str | None


class CropOut(BaseModel):
    model_config = ORM
    id: int
    slug: str
    name: str
    category: str | None
    cycle_length_days: int
    reference_source: str | None


class CropDetail(CropOut):
    stages: list[GrowthStageOut] = Field(default_factory=list)


class KcCurvePoint(BaseModel):
    days_after_sowing: int
    stage: str
    kc: float


class FieldCropCreate(BaseModel):
    crop_id: int
    sowing_date: dt.date
    planting_area_ha: float | None = Field(default=None, gt=0)
    notes: str | None = None

    @field_validator("sowing_date")
    @classmethod
    def _not_absurdly_future(cls, value: dt.date) -> dt.date:
        if value > dt.date.today() + dt.timedelta(days=365):
            raise ValueError("sowing date is more than a year in the future")
        return value


class FieldCropOut(BaseModel):
    model_config = ORM
    id: int
    field_id: int
    crop_id: int
    sowing_date: dt.date
    planting_area_ha: float | None
    status: str
    notes: str | None


class FieldCropDetail(FieldCropOut):
    crop_name: str
    crop_slug: str
    field_name: str
    days_after_sowing: int
    current_stage: str | None
    current_kc: float | None
    cycle_length_days: int
    progress_pct: float


# ==========================================================================
# Soil
# ==========================================================================
class SoilDataCreate(BaseModel):
    sample_date: dt.date | None = None
    ph_level: float | None = Field(default=None, ge=0, le=14)
    nitrogen: float | None = Field(default=None, ge=0)
    phosphorus: float | None = Field(default=None, ge=0)
    potassium: float | None = Field(default=None, ge=0)
    organic_matter: float | None = Field(default=None, ge=0, le=100)
    texture: str | None = Field(default=None, max_length=64)


class SoilDataOut(SoilDataCreate):
    model_config = ORM
    id: int
    field_id: int
    source: str


# ==========================================================================
# Weather
# ==========================================================================
class WeatherInputSchema(BaseModel):
    """Weather supplied directly by the caller.

    Wind and radiation are optional because a farmer rarely has either. When
    they are absent the baseline substitutes documented FAO-56 values and the
    response says which inputs were estimated.
    """

    temperature_mean_c: float = Field(ge=-50, le=60)
    temperature_min_c: float = Field(ge=-60, le=55)
    temperature_max_c: float = Field(ge=-40, le=65)
    humidity_pct: float = Field(ge=0, le=100)
    rainfall_mm: float = Field(default=0.0, ge=0, le=1500)
    wind_speed_ms: float | None = Field(default=None, ge=0, le=75)
    solar_radiation_mj_m2: float | None = Field(default=None, ge=0, le=45)

    @model_validator(mode="after")
    def _temperatures_ordered(self) -> "WeatherInputSchema":
        if self.temperature_min_c > self.temperature_max_c:
            raise ValueError("temperature_min_c cannot exceed temperature_max_c")
        if not (self.temperature_min_c <= self.temperature_mean_c <= self.temperature_max_c):
            raise ValueError(
                "temperature_mean_c must lie between temperature_min_c and temperature_max_c"
            )
        return self


class WeatherOut(BaseModel):
    date: dt.date
    temperature_mean_c: float
    temperature_min_c: float
    temperature_max_c: float
    humidity_pct: float
    rainfall_mm: float
    wind_speed_ms: float | None
    solar_radiation_mj_m2: float | None
    source: str
    provider: str
    is_forecast: bool


# ==========================================================================
# Prediction
# ==========================================================================
class PredictionRequest(BaseModel):
    field_crop_id: int
    prediction_date: dt.date | None = Field(
        default=None, description="Defaults to today"
    )
    weather: WeatherInputSchema | None = Field(
        default=None,
        description="Supply readings directly, or leave unset to use the configured provider",
    )
    use_weather_provider: bool = Field(
        default=False,
        description="Fetch weather from the configured provider using the farm's coordinates",
    )
    rain_last_7_days_mm: float | None = Field(default=None, ge=0, le=5000)
    rain_last_30_days_mm: float | None = Field(default=None, ge=0, le=20000)
    days_since_rain: float | None = Field(default=None, ge=0, le=365)
    forecast_rainfall_mm: float | None = Field(default=None, ge=0, le=1500)
    irrigation_efficiency_override: float | None = Field(default=None, gt=0, le=1)
    persist: bool = Field(default=True, description="Store the prediction for history")

    @model_validator(mode="after")
    def _need_a_weather_source(self) -> "PredictionRequest":
        if self.weather is None and not self.use_weather_provider:
            raise ValueError(
                "supply 'weather' readings, or set use_weather_provider to true so the "
                "server fetches them"
            )
        return self


class IntervalOut(BaseModel):
    lower_mm_day: float | None
    upper_mm_day: float | None
    nominal_coverage: float | None
    method: str | None
    note: str


class ModelInfoOut(BaseModel):
    available: bool
    name: str | None = None
    version: str | None = None
    algorithm: str | None = None
    task: str | None = None
    unavailable_reason: str | None = None


class AdvisoryOut(BaseModel):
    advisory_type: str
    headline: str
    detail: str
    priority: str
    action_required: bool


class PredictionOut(BaseModel):
    """The core response.

    Demand and irrigation requirement are separate fields, and net and gross are
    separate fields, because collapsing either pair is how this kind of system
    gives wrong advice.
    """

    model_config = ConfigDict(protected_namespaces=())

    id: int | None
    field_crop_id: int
    prediction_date: dt.date

    crop_name: str
    crop_slug: str
    growth_stage: str
    days_after_sowing: int
    kc_value: float

    # demand
    et0_mm_day: float = Field(description="Reference evapotranspiration, FAO-56")
    cwr_mm_day: float = Field(description="Crop water demand; what the crop will transpire")
    cwr_baseline_mm_day: float = Field(description="The same quantity from the physics reference")
    interval: IntervalOut

    # irrigation
    rainfall_mm: float
    effective_rainfall_mm: float = Field(description="Part of the rain that reaches the roots")
    net_irrigation_mm: float = Field(description="Depth that must reach the root zone")
    gross_irrigation_mm: float = Field(description="Depth that must be delivered to the field")
    gross_irrigation_litres: float | None = Field(
        default=None, description="Computed only when a field area is known"
    )
    application_efficiency: float

    water_need: dict[str, Any]
    model_info: ModelInfoOut
    prediction_source: Literal["ml_model", "physics_baseline"]
    estimated_inputs: list[str]
    advisories: list[AdvisoryOut]
    assumptions: dict[str, Any]
    weather_used: dict[str, Any]


class PredictionSummary(BaseModel):
    model_config = ORM
    id: int
    prediction_date: dt.date
    growth_stage: str
    kc_value: float
    et0_mm_day: float
    cwr_mm_day: float
    net_irrigation_mm: float
    gross_irrigation_mm: float
    prediction_source: str
    created_at: dt.datetime


class ExplanationOut(BaseModel):
    prediction_id: int
    available: bool
    method: str | None = None
    note: str | None = None
    reason: str | None = None
    prediction_mm_day: float | None = None
    contributors: list[dict[str, Any]] = Field(default_factory=list)
    baseline_comparison: dict[str, Any] | None = None


# ==========================================================================
# Irrigation and water use
# ==========================================================================
class IrrigationCalculationRequest(BaseModel):
    prediction_id: int
    irrigation_efficiency: float | None = Field(default=None, gt=0, le=1)
    forecast_rainfall_mm: float | None = Field(default=None, ge=0, le=1500)
    area_ha: float | None = Field(default=None, gt=0)


class IrrigationCalculationOut(BaseModel):
    prediction_id: int
    cwr_mm_day: float
    effective_rainfall_mm: float
    forecast_rainfall_mm: float | None
    net_irrigation_mm: float
    gross_irrigation_mm: float
    gross_irrigation_litres: float | None
    application_efficiency: float
    assumptions: list[str]


class IrrigationRecordCreate(BaseModel):
    field_crop_id: int
    irrigation_date: dt.date
    method: str | None = Field(default=None, max_length=64)
    duration_hours: float | None = Field(default=None, ge=0, le=48)
    water_applied_mm: float = Field(ge=0, le=1000)
    application_efficiency: float | None = Field(default=None, gt=0, le=1)
    notes: str | None = None


class IrrigationRecordOut(IrrigationRecordCreate):
    model_config = ORM
    id: int
    created_at: dt.datetime


class WaterUseCreate(BaseModel):
    field_crop_id: int
    record_date: dt.date
    water_used_mm: float = Field(ge=0, le=1000)
    water_source: str | None = Field(default=None, max_length=64)
    area_irrigated_ha: float | None = Field(default=None, gt=0)
    estimated_cost: float | None = Field(default=None, ge=0)


class WaterUseOut(WaterUseCreate):
    model_config = ORM
    id: int
    water_used_litres: float | None


# ==========================================================================
# Analytics and recommendation
# ==========================================================================
class AnalyticsOut(BaseModel):
    field_crop_id: int | None
    period_start: dt.date | None
    period_end: dt.date | None
    predictions: int
    total_predicted_demand_mm: float
    total_net_irrigation_mm: float
    total_gross_irrigation_mm: float
    total_water_applied_mm: float
    balance_mm: float
    by_growth_stage: list[dict[str, Any]]
    daily_series: list[dict[str, Any]]
    note: str


class CropRecommendationRequest(BaseModel):
    nitrogen: float = Field(ge=0, le=500)
    phosphorus: float = Field(ge=0, le=500)
    potassium: float = Field(ge=0, le=500)
    ph: float = Field(ge=3, le=10)
    temperature_c: float = Field(ge=-10, le=55)
    humidity_pct: float = Field(ge=0, le=100)
    rainfall_mm: float = Field(ge=0, le=5000, description="Expected seasonal rainfall")
    available_water_mm: float | None = Field(
        default=None, ge=0, le=5000,
        description="Water the farmer can supply over the season, as a depth",
    )
    top_n: int = Field(default=5, ge=1, le=22)


class CropRecommendationItem(BaseModel):
    crop: str
    suitability_score: float
    suitability_rank: int
    estimated_season_demand_mm: float | None
    water_feasible: bool | None
    water_balance_mm: float | None
    combined_score: float
    reasons: list[str]
    caveats: list[str]


class CropRecommendationOut(BaseModel):
    recommendations: list[CropRecommendationItem]
    method: dict[str, Any]
    limitations: list[str]
