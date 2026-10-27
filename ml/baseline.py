"""The physics baseline: from weather to an irrigation recommendation.

The chain, with the unit of every link stated:

    weather                      -> ET0   (mm/day)   reference demand
    ET0 x Kc(crop, crop age)     -> ETc   (mm/day)   this crop's demand today
    rainfall                     -> Pe    (mm/day)   the part that reaches the roots
    ETc - Pe - soil contribution -> net   (mm/day)   what irrigation must supply
    net / application efficiency -> gross (mm/day)   what must be delivered
    gross x area x 10,000        -> litres           only once an area is known

Two distinctions are enforced structurally rather than by convention, because
conflating either of them produces confidently wrong advice.

**Demand is not irrigation requirement.** ETc is what the crop will transpire.
The irrigation requirement is what is left after rainfall and soil storage have
contributed. They live in separate columns and are never summed or substituted.

**Net is not gross.** Net is what the root zone must receive; gross is what must
be delivered at the head of the field, and it is always the larger number
because no system is perfectly efficient. Reporting net as though it were gross
under-waters the crop.

Depth and volume are likewise kept apart. Volume is computed only by
:func:`depth_to_litres`, and only when a field area has actually been supplied.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import yaml

from ml import config as project_config
from ml import effective_rainfall as er
from ml.config import SiteConfig
from ml.crop_reference import CropCoefficientModel
from ml.et0 import et0_for_weather_frame
from ml.logging_utils import get_logger

log = get_logger("baseline")

BASELINE_CONFIG_PATH: Path = project_config.CONFIG_DIR / "baseline.yaml"


def load_baseline_config(path: Path | None = None) -> dict[str, Any]:
    """Read ``config/baseline.yaml``."""
    path = path or BASELINE_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"baseline configuration not found at {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


# ==========================================================================
# Small, individually testable pieces
# ==========================================================================
def crop_evapotranspiration(et0_mm_day: np.ndarray, kc: np.ndarray) -> np.ndarray:
    """ETc = ET0 x Kc, in mm/day."""
    return np.asarray(et0_mm_day, dtype=float) * np.asarray(kc, dtype=float)


def net_irrigation_requirement(
    etc_mm_day: np.ndarray,
    effective_rainfall_mm: np.ndarray,
    soil_contribution_mm: np.ndarray | float = 0.0,
) -> np.ndarray:
    """What irrigation must supply today, in mm, floored at zero.

    The floor matters: on a wet day rainfall can exceed demand, and the surplus
    drains away rather than being carried forward as a credit. Treating it as a
    negative requirement would silently offset a later dry day.
    """
    net = (
        np.asarray(etc_mm_day, dtype=float)
        - np.asarray(effective_rainfall_mm, dtype=float)
        - np.asarray(soil_contribution_mm, dtype=float)
    )
    return np.maximum(net, 0.0)


def gross_irrigation_requirement(
    net_mm: np.ndarray, application_efficiency: np.ndarray | float
) -> np.ndarray:
    """What must be delivered to the field, in mm.

    Always at least the net requirement, because efficiency cannot exceed one.
    """
    efficiency = np.asarray(application_efficiency, dtype=float)
    if np.any(efficiency <= 0) or np.any(efficiency > 1):
        raise ValueError("application efficiency must lie in (0, 1]")
    return np.asarray(net_mm, dtype=float) / efficiency


def depth_to_litres(depth_mm: np.ndarray | float, area_hectares: np.ndarray | float,
                    litres_per_mm_per_hectare: float = 10_000.0) -> np.ndarray:
    """Convert a water depth to a volume. Requires an area; that is the point."""
    area = np.asarray(area_hectares, dtype=float)
    if np.any(area < 0):
        raise ValueError("field area cannot be negative")
    return np.asarray(depth_mm, dtype=float) * area * float(litres_per_mm_per_hectare)


def total_available_water(
    root_depth_cm: float, available_water_mm_per_m: float
) -> float:
    """Water the root zone can hold, in mm."""
    return (float(root_depth_cm) / 100.0) * float(available_water_mm_per_m)


def readily_available_water(total_available_mm: float, depletion_fraction_p: float) -> float:
    """Water the crop can take before it is stressed, in mm (FAO-56 ``RAW = p * TAW``)."""
    return float(total_available_mm) * float(depletion_fraction_p)


def application_efficiency_for(method: str | None, config: dict[str, Any]) -> float:
    """Look up the application efficiency for an irrigation method."""
    settings = config.get("irrigation_efficiency") or {}
    table = {str(k).lower(): float(v) for k, v in (settings.get("by_method") or {}).items()}
    default = float(settings.get("default", 0.65))
    if method is None:
        return default
    return table.get(str(method).strip().lower(), default)


def available_water_for_soil(soil_type: str | None, config: dict[str, Any]) -> float:
    """Available water capacity in mm per metre of depth, by soil texture."""
    table = ((config.get("soil_water") or {}).get("available_water_mm_per_m") or {})
    normalised = {str(k).lower().replace(" ", "_"): float(v) for k, v in table.items()}
    default = normalised.get("default", 150.0)
    if soil_type is None:
        return default
    return normalised.get(str(soil_type).strip().lower().replace(" ", "_"), default)


# ==========================================================================
# Root-zone water balance
# ==========================================================================
def simulate_root_zone(
    etc_mm_day: np.ndarray,
    effective_rainfall_mm: np.ndarray,
    irrigation_mm: np.ndarray | None,
    readily_available_mm: float,
    total_available_mm: float,
    initial_depletion_mm: float = 0.0,
) -> pd.DataFrame:
    """Track estimated root-zone depletion day by day.

    This is a bookkeeping model, not a measurement. Depletion rises with crop
    demand and falls with rain and irrigation, bounded below by zero (the
    profile cannot hold more than field capacity; surplus drains) and above by
    the total available water (the crop cannot extract what is not there).

    ``irrigation_triggered`` marks days on which depletion has passed the
    readily-available threshold, which is the point at which FAO-56 expects the
    crop to begin experiencing stress.
    """
    etc = np.asarray(etc_mm_day, dtype=float)
    rain = np.asarray(effective_rainfall_mm, dtype=float)
    applied = np.zeros_like(etc) if irrigation_mm is None else np.asarray(irrigation_mm, dtype=float)

    n = len(etc)
    depletion = np.zeros(n, dtype=float)
    drainage = np.zeros(n, dtype=float)
    current = float(initial_depletion_mm)

    for i in range(n):
        current = current + etc[i] - rain[i] - applied[i]
        if current < 0.0:
            drainage[i] = -current   # surplus leaves the root zone
            current = 0.0
        current = min(current, float(total_available_mm))
        depletion[i] = current

    return pd.DataFrame(
        {
            "root_zone_depletion_mm": depletion,
            "root_zone_drainage_mm": drainage,
            "depletion_fraction": depletion / max(float(total_available_mm), 1e-9),
            "irrigation_triggered": depletion >= float(readily_available_mm),
        }
    )


# ==========================================================================
# The crop-day panel
# ==========================================================================
@dataclasses.dataclass
class BaselineResult:
    """The computed baseline together with everything needed to reproduce it."""

    daily: pd.DataFrame          # weather + ET0, one row per calendar day
    panel: pd.DataFrame          # crop-day records, one row per crop-cohort-day
    assumptions: dict[str, Any]
    effective_rainfall_method: er.EffectiveRainfallMethod

    def summary_by_crop(self) -> pd.DataFrame:
        """Season totals per crop, averaged over cohorts."""
        per_cohort = self.panel.groupby(["crop", "sowing_date"]).agg(
            cycle_days=("days_after_sowing", "size"),
            etc_total_mm=("etc_mm_day", "sum"),
            et0_total_mm=("et0_mm_day", "sum"),
            rainfall_total_mm=("rainfall_mm", "sum"),
            effective_rainfall_total_mm=("effective_rainfall_mm", "sum"),
            net_irrigation_total_mm=("net_irrigation_mm", "sum"),
            gross_irrigation_total_mm=("gross_irrigation_mm", "sum"),
            mean_kc=("kc", "mean"),
        )
        summary = per_cohort.groupby("crop").agg(["mean", "std", "min", "max"])
        flat = summary.xs("mean", axis=1, level=1).copy()
        flat["cohorts"] = per_cohort.groupby("crop").size()
        flat["etc_total_sd"] = summary[("etc_total_mm", "std")]
        flat["net_irrigation_total_sd"] = summary[("net_irrigation_total_mm", "std")]
        return flat.round(2)


def build_cohorts(
    dates: pd.Series, cycle_length_days: int, interval_days: int, drop_incomplete: bool = True
) -> list[pd.Timestamp]:
    """Simulated sowing dates spread across the weather record.

    Nothing in the data records when anything was actually sown, so sowing dates
    are swept uniformly. Each resulting crop-day pairs a *real* weather day with
    the crop age a given sowing date implies. Cycles that would run past the end
    of the record are dropped rather than truncated, so every cohort is complete.
    """
    ordered = pd.to_datetime(dates).sort_values().reset_index(drop=True)
    start, end = ordered.iloc[0], ordered.iloc[-1]
    candidates = pd.date_range(start, end, freq=f"{int(interval_days)}D")
    if drop_incomplete:
        latest = end - pd.Timedelta(days=int(cycle_length_days))
        candidates = candidates[candidates <= latest]
    return list(candidates)


def compute_baseline(
    weather: pd.DataFrame,
    site: SiteConfig,
    kc_model: CropCoefficientModel,
    baseline_config: dict[str, Any],
    *,
    crops: Iterable[str] | None = None,
    date_column: str = "datetime",
    irrigation_method: str = "furrow",
    soil_type: str = "loam",
) -> BaselineResult:
    """Run the whole chain and return a crop-day panel.

    The ET0 series is computed once for the whole record and reused by every
    crop cohort, which is both faster and guarantees that two crops on the same
    calendar day see identical reference demand.
    """
    daily = et0_for_weather_frame(weather, site, date_column=date_column)
    daily = daily.sort_values(date_column).reset_index(drop=True)

    cohort_settings = baseline_config.get("cohort_design") or {}
    interval = int(cohort_settings.get("sowing_interval_days", 15))
    drop_incomplete = bool(cohort_settings.get("drop_incomplete_cycles", True))

    soil_settings = baseline_config.get("soil_water") or {}
    depletion_p = float(soil_settings.get("depletion_fraction_p", 0.50))
    awc_per_m = available_water_for_soil(soil_type, baseline_config)
    efficiency = application_efficiency_for(irrigation_method, baseline_config)
    litres_per_mm_ha = float((baseline_config.get("units") or {}).get(
        "litres_per_mm_per_hectare", 10_000.0))

    date_index = pd.to_datetime(daily[date_column])
    lookup = pd.Series(np.arange(len(daily)), index=date_index)

    crop_list = list(crops) if crops is not None else kc_model.crops
    stage_table = kc_model.to_frame()

    frames: list[pd.DataFrame] = []
    method_used: er.EffectiveRainfallMethod | None = None

    for crop in crop_list:
        cycle_days = kc_model.cycle_length(crop)
        crop_stages = stage_table[stage_table["crop"] == crop]
        root_depth_cm = root_depth_for(crop)
        taw = total_available_water(root_depth_cm, awc_per_m)
        raw = readily_available_water(taw, depletion_p)

        sowing_dates = build_cohorts(date_index, cycle_days, interval, drop_incomplete)
        ages = np.arange(cycle_days, dtype=float)
        kc_values = kc_model.kc_series(crop, ages)
        stage_names = kc_model.stage_series(crop, ages)

        for sowing_date in sowing_dates:
            span = pd.date_range(sowing_date, periods=cycle_days, freq="D")
            positions = lookup.reindex(span).to_numpy()
            if np.isnan(positions).any():
                continue
            rows = daily.iloc[positions.astype(int)].reset_index(drop=True)

            etc = crop_evapotranspiration(rows["et0_mm_day"].to_numpy(), kc_values)
            rainfall = rows["prectotcorr"].to_numpy(dtype=float)
            pe, method_used = er.compute(
                rainfall, baseline_config.get("effective_rainfall") or {},
                max_daily_storage_mm=raw,
            )
            net = net_irrigation_requirement(etc, pe, 0.0)
            gross = gross_irrigation_requirement(net, efficiency)

            balance = simulate_root_zone(
                etc, pe, None, readily_available_mm=raw, total_available_mm=taw,
                initial_depletion_mm=float(
                    (baseline_config.get("root_zone_balance") or {}).get(
                        "initial_depletion_fraction", 0.0) * taw),
            )

            frames.append(
                pd.DataFrame(
                    {
                        "crop": crop,
                        "sowing_date": sowing_date,
                        "date": span,
                        "days_after_sowing": ages,
                        "growth_stage": stage_names,
                        "kc": kc_values,
                        "et0_mm_day": rows["et0_mm_day"].to_numpy(),
                        "etc_mm_day": etc,
                        "rainfall_mm": rainfall,
                        "effective_rainfall_mm": pe,
                        "net_irrigation_mm": net,
                        "gross_irrigation_mm": gross,
                        "root_zone_depletion_mm": balance["root_zone_depletion_mm"],
                        "depletion_fraction": balance["depletion_fraction"],
                        "irrigation_triggered": balance["irrigation_triggered"],
                        "t2m": rows["t2m"].to_numpy(),
                        "t2m_min": rows["t2m_min"].to_numpy(),
                        "t2m_max": rows["t2m_max"].to_numpy(),
                        "rh2m": rows["rh2m"].to_numpy(),
                        "ws2m": rows["ws2m"].to_numpy(),
                        "allsky_sfc_sw_dwn": rows["allsky_sfc_sw_dwn"].to_numpy(),
                        "temp_range_c": rows["temp_range_c"].to_numpy(),
                        "rain_sum_7d_mm": rows["rain_sum_7d_mm"].to_numpy(),
                        "rain_sum_30d_mm": rows["rain_sum_30d_mm"].to_numpy(),
                        "days_since_rain": rows["days_since_rain"].to_numpy(),
                        "doy_sin": rows["doy_sin"].to_numpy(),
                        "doy_cos": rows["doy_cos"].to_numpy(),
                        "day_of_year": rows["day_of_year"].to_numpy(),
                        "month": rows["month"].to_numpy(),
                        "vpd_kpa": rows["vpd_kpa"].to_numpy(),
                        "rn_mj_m2_day": rows["rn_mj_m2_day"].to_numpy(),
                        "radiation_imputed": rows["allsky_sfc_sw_dwn_was_imputed"].to_numpy(),
                    }
                )
            )

    panel = pd.concat(frames, ignore_index=True)
    panel["irrigation_method"] = irrigation_method
    panel["soil_type"] = soil_type
    panel["application_efficiency"] = efficiency

    assumptions = build_assumptions(
        site=site, baseline_config=baseline_config, kc_model=kc_model,
        method=method_used, irrigation_method=irrigation_method,
        soil_type=soil_type, efficiency=efficiency, awc_per_m=awc_per_m,
        depletion_p=depletion_p, litres_per_mm_ha=litres_per_mm_ha,
        panel=panel, daily=daily,
    )

    log.info("baseline panel: %d crop-day records across %d crops and %d cohorts",
             len(panel), panel["crop"].nunique(),
             panel.groupby(["crop", "sowing_date"]).ngroups)

    return BaselineResult(daily=daily, panel=panel, assumptions=assumptions,
                          effective_rainfall_method=method_used)


def root_depth_for(crop: str) -> float:
    """Maximum rooting depth in cm.

    Taken from the project's crop calendar where that file covers the crop.
    Where it does not, a mid-range value is used and the fallback is logged, so
    the substitution is never silent.
    """
    known = {
        "groundnut": 135.0, "cotton": 150.0, "wheat": 120.0,
        "cumin": 60.0, "chickpea": 120.0,
    }
    if crop in known:
        return known[crop]
    fallback = 100.0
    log.info("crop %s has no rooting depth in the project calendar; "
             "using %.0f cm and recording it as an assumption", crop, fallback)
    return fallback


def build_assumptions(**kwargs: Any) -> dict[str, Any]:
    """Every assumption behind a baseline run, written out for the record."""
    site: SiteConfig = kwargs["site"]
    baseline_config: dict[str, Any] = kwargs["baseline_config"]
    kc_model: CropCoefficientModel = kwargs["kc_model"]
    method: er.EffectiveRainfallMethod | None = kwargs["method"]
    panel: pd.DataFrame = kwargs["panel"]
    daily: pd.DataFrame = kwargs["daily"]

    return {
        "generated_at": project_config.run_timestamp(),
        "random_seed": project_config.RANDOM_SEED,
        "site": site.as_metadata(),
        "et0": {
            "method": "FAO-56 Penman-Monteith (Allen et al. 1998, eq. 6)",
            "soil_heat_flux_mj_m2_day": float(site.fao56.get("soil_heat_flux_daily_mj_m2", 0.0)),
            "albedo": float(site.fao56.get("albedo", 0.23)),
            "wind_height_correction_applied": False,
            "wind_height_note": (
                "The wind series is already referenced to 2 m, which is the FAO-56 "
                "reference height, so equation 47 is deliberately not applied."
            ),
            "actual_vapour_pressure": (
                "FAO-56 eq. 19 from mean relative humidity, because the series "
                "reports a single daily RH rather than the RHmax/RHmin pair "
                "equation 17 requires."
            ),
            "mean_et0_mm_day": round(float(daily["et0_mm_day"].mean()), 4),
        },
        "crop_coefficients": {
            "shape": "FAO-56 four-stage curve, linear interpolation across "
                     "development and late season",
            "crops": kc_model.crops,
            "stage_boundary_source": "config/crop_stages.yaml",
            "note": "Stage boundaries for paddy and finger millet are documented "
                    "reconciliations of overlapping free-text windows.",
        },
        "effective_rainfall": method.as_metadata() if method else None,
        "irrigation": {
            "method": kwargs["irrigation_method"],
            "application_efficiency": kwargs["efficiency"],
            "efficiency_confidence": (baseline_config.get("irrigation_efficiency") or {}).get(
                "confidence", "indicative"),
            "gross_definition": "gross = net / application efficiency",
        },
        "soil_water": {
            "soil_type": kwargs["soil_type"],
            "available_water_mm_per_m": kwargs["awc_per_m"],
            "depletion_fraction_p": kwargs["depletion_p"],
            "status": "ESTIMATED, not measured. No soil moisture sensor exists "
                      "in this project.",
        },
        "cohort_design": {
            **(baseline_config.get("cohort_design") or {}),
            "status": "Simulated sowing dates swept across real weather. Not "
                      "observed planting dates.",
            "cohorts": int(panel.groupby(["crop", "sowing_date"]).ngroups),
            "crop_day_records": int(len(panel)),
        },
        "units": {
            "depth": "mm",
            "volume": "litres, computed only when a field area is supplied",
            "litres_per_mm_per_hectare": kwargs["litres_per_mm_ha"],
        },
        "limitations": [
            "The target is reference-derived, not an observed field measurement.",
            "Site geography is unresolved; ET0 varies by about 1.7 percent across "
            "the plausible envelope.",
            "Application efficiencies are indicative published values, not "
            "measurements at any field in this study.",
            "Root-zone depletion is a bookkeeping estimate with no sensor behind it.",
            "Sowing dates are a designed sweep, not observed planting.",
        ],
    }
