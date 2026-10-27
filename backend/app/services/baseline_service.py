"""The physics baseline, for a single field on a single day.

This is the same FAO-56 chain the research pipeline runs, applied to one
request instead of a seven-year panel. It reuses ``ml.et0``, ``ml.baseline`` and
``ml.crop_reference`` directly rather than re-implementing them, so the number
the API returns and the number the study reports come from identical code.

The baseline has a second job beyond producing a reference figure: it is the
fallback. When no model has been promoted, the prediction endpoint serves this
and marks the machine-learning fields unavailable. A farmer gets a physically
defensible answer; nobody gets a fabricated one.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
from functools import lru_cache
from typing import Any

from ml import baseline as baseline_lib
from ml import config as ml_config
from ml import data_loader
from ml import effective_rainfall as er
from ml.crop_reference import CropCoefficientModel
from ml.et0 import penman_monteith_et0
from ml.logging_utils import get_logger

log = get_logger("api.baseline_service")


@lru_cache(maxsize=1)
def get_kc_model() -> CropCoefficientModel:
    """The growth-stage crop coefficient curves, loaded once."""
    return CropCoefficientModel.from_sources(data_loader.load_dataset("crop_calendar"))


@lru_cache(maxsize=1)
def get_baseline_config() -> dict[str, Any]:
    return baseline_lib.load_baseline_config()


@lru_cache(maxsize=1)
def get_site_config():  # type: ignore[no-untyped-def]
    return ml_config.load_site_config()


@dataclasses.dataclass
class WeatherInput:
    """One day of weather for one field."""

    date: dt.date
    temperature_mean_c: float
    temperature_min_c: float
    temperature_max_c: float
    humidity_pct: float
    rainfall_mm: float
    wind_speed_ms: float | None = None
    solar_radiation_mj_m2: float | None = None
    source: str = "manual"

    def as_snapshot(self) -> dict[str, Any]:
        return {
            "date": str(self.date),
            "temperature_mean_c": self.temperature_mean_c,
            "temperature_min_c": self.temperature_min_c,
            "temperature_max_c": self.temperature_max_c,
            "humidity_pct": self.humidity_pct,
            "rainfall_mm": self.rainfall_mm,
            "wind_speed_ms": self.wind_speed_ms,
            "solar_radiation_mj_m2": self.solar_radiation_mj_m2,
            "source": self.source,
        }


@dataclasses.dataclass
class BaselineOutput:
    """The full physics chain for one field-day, with every link exposed."""

    et0_mm_day: float
    kc: float
    growth_stage: str
    days_after_sowing: int
    etc_mm_day: float
    effective_rainfall_mm: float
    net_irrigation_mm: float
    gross_irrigation_mm: float
    application_efficiency: float
    gross_irrigation_litres: float | None
    et0_inputs_estimated: list[str]
    assumptions: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


# --------------------------------------------------------------------------
def estimate_missing_radiation(
    temperature_max_c: float, temperature_min_c: float, day_of_year: int, latitude_deg: float,
    krs: float = 0.16,
) -> float:
    """Shortwave radiation from the daily temperature range (FAO-56 eq. 50).

    A farmer's weather source rarely reports radiation. FAO-56 provides this
    substitution for exactly that case, and the response records that it was
    used so the estimate is never mistaken for a measurement.
    """
    from ml.missing_value_handler import estimate_solar_radiation_from_temperature_range

    import numpy as np

    return float(
        estimate_solar_radiation_from_temperature_range(
            np.array([temperature_max_c]), np.array([temperature_min_c]),
            np.array([float(day_of_year)]), latitude_deg, krs=krs,
        )[0]
    )


def default_wind_speed_ms() -> float:
    """FAO-56's recommended substitute when wind is unmeasured.

    FAO-56 suggests 2 m/s as a global average for locations with no wind data.
    It is a declared substitution, reported in the response, not a measurement.
    """
    return 2.0


def compute_field_day(
    *,
    weather: WeatherInput,
    crop_slug: str,
    sowing_date: dt.date,
    area_ha: float | None = None,
    irrigation_method: str | None = None,
    irrigation_efficiency_override: float | None = None,
    soil_type: str | None = None,
) -> BaselineOutput:
    """Run weather -> ET0 -> ETc -> effective rainfall -> irrigation for one day."""
    site = get_site_config()
    site.require_usable()
    config = get_baseline_config()
    kc_model = get_kc_model()

    days_after_sowing = (weather.date - sowing_date).days
    if days_after_sowing < 0:
        raise ValueError(
            f"the prediction date {weather.date} is before the sowing date {sowing_date}"
        )

    estimated: list[str] = []

    solar = weather.solar_radiation_mj_m2
    if solar is None:
        solar = estimate_missing_radiation(
            weather.temperature_max_c, weather.temperature_min_c,
            weather.date.timetuple().tm_yday, float(site.latitude_deg),
            krs=float(site.fao56.get("krs_interior", 0.16)),
        )
        estimated.append("solar_radiation_estimated_from_temperature_range_fao56_eq50")

    wind = weather.wind_speed_ms
    if wind is None:
        wind = default_wind_speed_ms()
        estimated.append("wind_speed_substituted_with_fao56_default_2_m_per_s")

    result = penman_monteith_et0(
        tmean_c=weather.temperature_mean_c,
        tmax_c=weather.temperature_max_c,
        tmin_c=weather.temperature_min_c,
        rh_mean_pct=weather.humidity_pct,
        wind_speed_ms=wind,
        solar_radiation_mj_m2_day=solar,
        day_of_year=weather.date.timetuple().tm_yday,
        latitude_deg=float(site.latitude_deg),
        elevation_m=float(site.elevation_m),
        albedo=float(site.fao56.get("albedo", 0.23)),
        soil_heat_flux_mj_m2_day=float(site.fao56.get("soil_heat_flux_daily_mj_m2", 0.0)),
        wind_measurement_height_m=float(site.fao56.get("wind_measurement_height_m", 2.0)),
        turbidity_a=float(site.fao56.get("clear_sky_turbidity_a", 0.75)),
        turbidity_b=float(site.fao56.get("clear_sky_turbidity_b", 2.0e-5)),
    )
    et0 = float(result.et0_mm_day)

    kc = kc_model.kc(crop_slug, days_after_sowing)
    stage = kc_model.stage_for_day(crop_slug, days_after_sowing).stage
    etc = et0 * kc

    # Root-zone storage caps how much of a day's rain can be retained.
    awc_per_m = baseline_lib.available_water_for_soil(soil_type, config)
    depletion_p = float((config.get("soil_water") or {}).get("depletion_fraction_p", 0.50))
    root_depth_cm = baseline_lib.root_depth_for(crop_slug)
    taw = baseline_lib.total_available_water(root_depth_cm, awc_per_m)
    raw = baseline_lib.readily_available_water(taw, depletion_p)

    effective, method = er.compute(
        [weather.rainfall_mm], config.get("effective_rainfall") or {},
        max_daily_storage_mm=raw,
    )
    effective_mm = float(effective[0])

    efficiency = (
        float(irrigation_efficiency_override)
        if irrigation_efficiency_override is not None
        else baseline_lib.application_efficiency_for(irrigation_method, config)
    )

    net = float(baseline_lib.net_irrigation_requirement([etc], [effective_mm], 0.0)[0])
    gross = float(baseline_lib.gross_irrigation_requirement([net], efficiency)[0])

    litres = None
    if area_ha is not None:
        litres_per_mm_ha = float((config.get("units") or {}).get(
            "litres_per_mm_per_hectare", 10_000.0))
        litres = float(baseline_lib.depth_to_litres(gross, area_ha, litres_per_mm_ha))

    assumptions = {
        "et0_method": "FAO-56 Penman-Monteith (Allen et al. 1998, eq. 6)",
        "site": {
            "latitude_deg": site.latitude_deg,
            "elevation_m": site.elevation_m,
            "resolution_status": site.resolution_status,
            "is_provisional": site.is_provisional,
        },
        "kc": {
            "value": round(kc, 4),
            "stage": stage,
            "curve": "FAO-56 four-stage, interpolated across development and late season",
            "source": "config/crop_stages.yaml and the project agronomic references",
        },
        "effective_rainfall": method.as_metadata(),
        "irrigation_efficiency": {
            "value": efficiency,
            "method": irrigation_method,
            "origin": ("field override" if irrigation_efficiency_override is not None
                       else "configured default for this irrigation method"),
            "confidence": "indicative published value, not measured at this field",
        },
        "soil_water": {
            "soil_type": soil_type,
            "available_water_mm_per_m": awc_per_m,
            "total_available_water_mm": round(taw, 2),
            "readily_available_water_mm": round(raw, 2),
            "status": "ESTIMATED, no soil moisture sensor",
        },
        "estimated_inputs": estimated,
        "units": {
            "depth": "mm/day",
            "volume": "litres, computed only because a field area was supplied"
            if area_ha is not None else "not computed: no field area supplied",
        },
    }

    return BaselineOutput(
        et0_mm_day=et0,
        kc=kc,
        growth_stage=stage,
        days_after_sowing=days_after_sowing,
        etc_mm_day=etc,
        effective_rainfall_mm=effective_mm,
        net_irrigation_mm=net,
        gross_irrigation_mm=gross,
        application_efficiency=efficiency,
        gross_irrigation_litres=litres,
        et0_inputs_estimated=estimated,
        assumptions=assumptions,
    )


def build_model_features(
    *, weather: WeatherInput, crop_slug: str, days_after_sowing: int, growth_stage: str,
    rain_7d_mm: float | None = None, rain_30d_mm: float | None = None,
    days_since_rain: float | None = None,
) -> dict[str, Any]:
    """Assemble the inputs the trained model expects.

    Names match the training panel exactly. Rolling rainfall terms come from the
    caller when history is available; when it is not they fall back to today's
    rainfall, and the endpoint reports which inputs were absent so the farmer is
    not shown an over-confident number built on missing context.
    """
    import math

    day_of_year = weather.date.timetuple().tm_yday
    angle = 2.0 * math.pi * day_of_year / 365.25
    return {
        "t2m": weather.temperature_mean_c,
        "t2m_min": weather.temperature_min_c,
        "t2m_max": weather.temperature_max_c,
        "rh2m": weather.humidity_pct,
        "ws2m": weather.wind_speed_ms,
        "allsky_sfc_sw_dwn": weather.solar_radiation_mj_m2,
        "temp_range_c": weather.temperature_max_c - weather.temperature_min_c,
        "rainfall_mm": weather.rainfall_mm,
        "rain_sum_7d_mm": rain_7d_mm if rain_7d_mm is not None else weather.rainfall_mm,
        "rain_sum_30d_mm": rain_30d_mm if rain_30d_mm is not None else weather.rainfall_mm,
        "days_since_rain": (days_since_rain if days_since_rain is not None
                            else (0.0 if weather.rainfall_mm > 0 else 1.0)),
        "day_of_year": day_of_year,
        "doy_sin": math.sin(angle),
        "doy_cos": math.cos(angle),
        "month": weather.date.month,
        "days_after_sowing": float(days_after_sowing),
        "crop": crop_slug,
        "growth_stage": growth_stage,
    }
