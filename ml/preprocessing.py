"""The preprocessing pipeline, end to end.

Running :func:`run_preprocessing` loads the source files, cleans them, validates
them, fills the one genuine gap, engineers the leakage-safe feature set, records
lineage for every column produced, and writes the results to
``datasets/processed`` with a metadata file describing the run.

The notebook calls the same functions in the same order and displays what they
return, so the notebook and a scripted run cannot disagree.

Scope boundary
--------------
Nothing here touches ET0, Kc or the target. Those belong to the physics baseline
in the next phase. Keeping them out means every feature this module produces is
independent of the eventual target by construction, which is a much stronger
leakage guarantee than checking for it afterwards.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml import config, data_cleaner, data_loader, data_validator, missing_value_handler
from ml.lineage import LineageRegistry
from ml.logging_utils import get_logger

log = get_logger("preprocessing")

DAYS_IN_YEAR = 365.25

#: Physically defensible bounds used by the validation stage. These are limits
#: on what a terrestrial daily observation can be, not limits on what this
#: particular site produces, so they flag corruption rather than unusual weather.
WEATHER_BOUNDS: dict[str, tuple[float | None, float | None]] = {
    "t2m": (-40.0, 60.0),
    "t2m_min": (-50.0, 50.0),
    "t2m_max": (-30.0, 60.0),
    "rh2m": (0.0, 100.0),
    "ws2m": (0.0, 60.0),
    "prectotcorr": (0.0, 1200.0),
    "allsky_sfc_sw_dwn": (0.0, 45.0),
}


@dataclasses.dataclass
class PreprocessingResult:
    """Everything one preprocessing run produced."""

    weather: pd.DataFrame
    soil: pd.DataFrame
    district_rainfall: pd.DataFrame
    crop_suitability: pd.DataFrame
    season_context: pd.DataFrame
    validation: data_validator.ValidationReport
    cleaning_log: pd.DataFrame
    raw_vs_cleaned: pd.DataFrame
    profiles: pd.DataFrame
    missing_summary: pd.DataFrame
    imputations: list[missing_value_handler.ImputationRecord]
    lineage: LineageRegistry
    metadata: dict[str, Any]


# ==========================================================================
# Feature engineering
# ==========================================================================
def engineer_temporal_features(frame: pd.DataFrame, date_column: str = "datetime") -> pd.DataFrame:
    """Calendar position, encoded so a model can use it.

    Day-of-year is encoded as a sine/cosine pair rather than a raw integer.
    A raw integer tells a model that 31 December and 1 January are 364 units
    apart, which is exactly wrong for a seasonal signal.
    """
    out = frame.copy()
    dates = pd.to_datetime(out[date_column])
    out["year"] = dates.dt.year
    out["month"] = dates.dt.month
    out["day_of_year"] = dates.dt.dayofyear

    angle = 2.0 * np.pi * out["day_of_year"] / DAYS_IN_YEAR
    out["doy_sin"] = np.sin(angle)
    out["doy_cos"] = np.cos(angle)

    month_angle = 2.0 * np.pi * (out["month"] - 1) / 12.0
    out["month_sin"] = np.sin(month_angle)
    out["month_cos"] = np.cos(month_angle)
    return out


def engineer_weather_features(
    frame: pd.DataFrame, *, rolling_windows: tuple[int, ...] = (7, 30)
) -> pd.DataFrame:
    """Derived weather quantities that do not presuppose the physics baseline.

    Rolling statistics are strictly backward-looking: each window ends on the
    current day and uses only that day and earlier ones. A centred window would
    let tomorrow's rainfall influence today's feature, which would be a leak in
    any forecasting experiment.
    """
    out = frame.sort_values("datetime").reset_index(drop=True).copy()

    out["temp_range_c"] = out["t2m_max"] - out["t2m_min"]
    out["temp_midrange_c"] = (out["t2m_max"] + out["t2m_min"]) / 2.0
    out["is_rain_day"] = (out["prectotcorr"] > 0.0).astype(int)

    for window in rolling_windows:
        out[f"rain_sum_{window}d_mm"] = (
            out["prectotcorr"].rolling(window=window, min_periods=1).sum()
        )
        out[f"rain_days_{window}d"] = (
            out["is_rain_day"].rolling(window=window, min_periods=1).sum()
        )
        out[f"temp_mean_{window}d_c"] = (
            out["t2m"].rolling(window=window, min_periods=1).mean()
        )
        out[f"rh_mean_{window}d_pct"] = (
            out["rh2m"].rolling(window=window, min_periods=1).mean()
        )

    # Days since the last day with measurable rain, capped so the value stays
    # meaningful through long dry spells.
    days_since = np.zeros(len(out), dtype=float)
    counter = 0.0
    for i, wet in enumerate(out["is_rain_day"].to_numpy()):
        counter = 0.0 if wet else counter + 1.0
        days_since[i] = counter
    out["days_since_rain"] = np.minimum(days_since, 120.0)

    return out


def register_lineage(registry: LineageRegistry, rolling_windows: tuple[int, ...] = (7, 30)) -> LineageRegistry:
    """Declare the provenance of every column the pipeline produces."""
    climate = "Climate_Data.csv"

    raw_weather = {
        "t2m": ("T2M", "degC", "2 m air temperature, daily mean"),
        "t2m_min": ("T2M_MIN", "degC", "2 m air temperature, daily minimum"),
        "t2m_max": ("T2M_MAX", "degC", "2 m air temperature, daily maximum"),
        "rh2m": ("RH2M", "%", "2 m relative humidity, daily mean"),
        "ws2m": ("WS2M", "m/s", "2 m wind speed; already at the FAO-56 reference height"),
        "prectotcorr": ("PRECTOTCORR", "mm/day", "bias-corrected total precipitation"),
        "allsky_sfc_sw_dwn": (
            "ALLSKY_SFC_SW_DWN", "MJ/m2/day",
            "all-sky downward shortwave irradiance; one day was imputed",
        ),
    }
    for feature, (source, unit, note) in raw_weather.items():
        registry.register(
            feature, "raw", climate, [source],
            "renamed to snake_case; sentinel values converted to NaN; "
            "physically impossible values voided",
            unit, note,
        )

    registry.register("datetime", "raw", climate, ["datetime"],
                      "parsed to a datetime and sorted ascending", "date",
                      "daily, complete, no gaps or repeats")

    for feature, transformation, unit in [
        ("year", "calendar year of the observation", "year"),
        ("month", "calendar month of the observation", "1-12"),
        ("day_of_year", "ordinal day of the observation", "1-366"),
        ("doy_sin", "sin(2*pi*day_of_year/365.25)", "dimensionless"),
        ("doy_cos", "cos(2*pi*day_of_year/365.25)", "dimensionless"),
        ("month_sin", "sin(2*pi*(month-1)/12)", "dimensionless"),
        ("month_cos", "cos(2*pi*(month-1)/12)", "dimensionless"),
    ]:
        registry.register(feature, "derived", climate, ["datetime"], transformation, unit,
                          "cyclical encoding keeps December adjacent to January"
                          if "sin" in feature or "cos" in feature else "")

    registry.register("temp_range_c", "derived", climate, ["T2M_MAX", "T2M_MIN"],
                      "T2M_MAX - T2M_MIN", "degC",
                      "proxy for cloudiness; also the input to the FAO-56 radiation estimator")
    registry.register("temp_midrange_c", "derived", climate, ["T2M_MAX", "T2M_MIN"],
                      "(T2M_MAX + T2M_MIN) / 2", "degC", "")
    registry.register("is_rain_day", "derived", climate, ["PRECTOTCORR"],
                      "1 when precipitation exceeds 0, else 0", "0/1", "")
    registry.register("days_since_rain", "derived", climate, ["PRECTOTCORR"],
                      "consecutive days without measurable rain, capped at 120", "days",
                      "backward-looking only")

    for window in rolling_windows:
        registry.register(f"rain_sum_{window}d_mm", "derived", climate, ["PRECTOTCORR"],
                          f"trailing {window}-day rainfall total ending on the current day",
                          "mm", "backward-looking window; no future information")
        registry.register(f"rain_days_{window}d", "derived", climate, ["PRECTOTCORR"],
                          f"count of rain days in the trailing {window} days", "days", "")
        registry.register(f"temp_mean_{window}d_c", "derived", climate, ["T2M"],
                          f"trailing {window}-day mean temperature", "degC", "")
        registry.register(f"rh_mean_{window}d_pct", "derived", climate, ["RH2M"],
                          f"trailing {window}-day mean relative humidity", "%", "")

    registry.register("allsky_sfc_sw_dwn_was_imputed", "derived", climate,
                      ["ALLSKY_SFC_SW_DWN"],
                      "flag marking days whose radiation was filled by FAO-56 eq. 50",
                      "0/1", "lets any result be recomputed with imputed days excluded")
    return registry


# ==========================================================================
# Validation
# ==========================================================================
def validate_weather(frame: pd.DataFrame, report: data_validator.ValidationReport) -> None:
    name = "climate"
    report.add(data_validator.check_columns_present(
        frame, name, ["datetime", "t2m", "t2m_min", "t2m_max", "rh2m", "ws2m",
                      "prectotcorr", "allsky_sfc_sw_dwn"]))
    report.add(data_validator.check_monotonic_dates(frame, name, "datetime"))
    report.add(data_validator.check_unique_key(frame, name, ["datetime"]))
    report.add(data_validator.check_sentinel_values(frame, name))
    report.add(data_validator.check_ordering(frame, name, "t2m_min", "t2m_max"))
    report.add(data_validator.check_ordering(frame, name, "t2m_min", "t2m"))
    report.add(data_validator.check_ordering(frame, name, "t2m", "t2m_max"))
    for column, (low, high) in WEATHER_BOUNDS.items():
        report.add(data_validator.check_value_range(frame, name, column, low, high))
    for column in ("t2m", "rh2m", "ws2m", "prectotcorr", "allsky_sfc_sw_dwn"):
        report.add(data_validator.check_missing_rate(frame, name, column, max_rate=0.0,
                                                     severity="error"))


def validate_soil(frame: pd.DataFrame, report: data_validator.ValidationReport) -> None:
    name = "soil"
    report.add(data_validator.check_columns_present(
        frame, name, ["district", "nitrogen", "phosphorus", "potassium", "ph"]))
    report.add(data_validator.check_value_range(frame, name, "ph", 3.0, 10.0))
    report.add(data_validator.check_value_range(frame, name, "nitrogen", 0.0, 2000.0))
    report.add(data_validator.check_value_range(frame, name, "phosphorus", 0.0, 500.0))
    report.add(data_validator.check_value_range(frame, name, "potassium", 0.0, 2000.0))
    report.add(data_validator.check_no_duplicate_rows(frame, name))


def validate_district_rainfall(frame: pd.DataFrame, report: data_validator.ValidationReport) -> None:
    name = "rainfall_district"
    report.add(data_validator.check_columns_present(frame, name, ["district", "normal_annual_rainfall_mm"]))
    report.add(data_validator.check_unique_key(frame, name, ["district_key"]))
    report.add(data_validator.check_value_range(frame, name, "normal_annual_rainfall_mm", 100.0, 8000.0))
    report.add(data_validator.check_custom(
        name, "state_total_removed",
        lambda: not frame["district"].astype(str).str.upper().str.contains("TOTAL").any(),
        "the state aggregate row was removed",
        "a state aggregate row is still present and would double-count",
        severity="error",
    ))


def validate_crop_suitability(frame: pd.DataFrame, report: data_validator.ValidationReport) -> None:
    name = "crop_recommendation"
    report.add(data_validator.check_columns_present(
        frame, name, ["n", "p", "k", "temperature", "humidity", "ph", "rainfall", "label"]))
    report.add(data_validator.check_value_range(frame, name, "ph", 3.0, 10.0))
    report.add(data_validator.check_value_range(frame, name, "temperature", -5.0, 55.0))
    report.add(data_validator.check_value_range(frame, name, "humidity", 0.0, 100.0))
    report.add(data_validator.check_value_range(frame, name, "rainfall", 0.0, 1000.0))
    report.add(data_validator.check_custom(
        name, "class_balance",
        lambda: frame["label"].value_counts().std() < 1e-9,
        "every crop class has an identical number of samples",
        "crop classes are unbalanced",
        severity="info",
    ))


# ==========================================================================
# Orchestration
# ==========================================================================
def run_preprocessing(
    *,
    latitude_for_imputation: float,
    rolling_windows: tuple[int, ...] = (7, 30),
    write_outputs: bool = True,
) -> PreprocessingResult:
    """Load, clean, validate, engineer and persist the analysis-ready tables."""
    config.ensure_directories()
    report = data_validator.ValidationReport()
    registry = LineageRegistry()
    cleaning_frames: list[pd.DataFrame] = []
    audit_frames: list[pd.DataFrame] = []
    profile_frames: list[pd.DataFrame] = []

    # ---- weather -------------------------------------------------------
    weather_raw = data_loader.load_dataset("climate", stage="raw")
    weather_in = data_loader.load_dataset("climate", stage="cleaned")
    audit_frames.append(data_cleaner.audit_raw_versus_cleaned(weather_raw, weather_in, "climate"))

    weather_log = data_cleaner.CleaningLog("climate")
    weather = data_cleaner.clean_weather(weather_in, weather_log)
    weather, radiation_record = missing_value_handler.impute_solar_radiation(
        weather, latitude_deg=latitude_for_imputation
    )
    weather = engineer_temporal_features(weather)
    weather = engineer_weather_features(weather, rolling_windows=rolling_windows)
    weather_log.record("feature_engineering",
                       f"added temporal and rolling features (windows: {list(rolling_windows)})",
                       len(weather), len(weather))
    cleaning_frames.append(weather_log.to_frame())
    validate_weather(weather, report)
    profile_frames.append(data_validator.profile(weather, "climate"))

    # ---- soil ----------------------------------------------------------
    soil_log = data_cleaner.CleaningLog("soil")
    soil = data_cleaner.clean_soil(data_loader.load_dataset("soil"), soil_log)
    cleaning_frames.append(soil_log.to_frame())
    validate_soil(soil, report)
    profile_frames.append(data_validator.profile(soil, "soil"))
    audit_frames.append(data_cleaner.audit_raw_versus_cleaned(
        data_loader.load_dataset("soil", stage="raw"),
        data_loader.load_dataset("soil"), "soil"))

    # ---- district rainfall ---------------------------------------------
    rainfall_log = data_cleaner.CleaningLog("rainfall_district")
    district_rainfall = data_cleaner.clean_district_rainfall(
        data_loader.load_dataset("rainfall_district"), rainfall_log)
    cleaning_frames.append(rainfall_log.to_frame())
    validate_district_rainfall(district_rainfall, report)
    profile_frames.append(data_validator.profile(district_rainfall, "rainfall_district"))

    # ---- crop suitability ----------------------------------------------
    suitability_log = data_cleaner.CleaningLog("crop_recommendation")
    crop_suitability = data_cleaner.clean_crop_recommendation(
        data_loader.load_dataset("crop_recommendation"), suitability_log)
    cleaning_frames.append(suitability_log.to_frame())
    validate_crop_suitability(crop_suitability, report)
    profile_frames.append(data_validator.profile(crop_suitability, "crop_recommendation"))

    # ---- season context (kept as context only) --------------------------
    context_log = data_cleaner.CleaningLog("season_context")
    season_context = data_cleaner.strip_text_columns(
        data_loader.load_dataset("season_context"), context_log)
    context_log.record(
        "scope_note",
        "retained as market and cropping context only; the raw file's temperature "
        "column was dropped upstream for implausible values and stays out",
        len(season_context), len(season_context),
    )
    cleaning_frames.append(context_log.to_frame())
    profile_frames.append(data_validator.profile(season_context, "season_context"))

    # ---- lineage --------------------------------------------------------
    register_lineage(registry, rolling_windows=rolling_windows)

    # ---- assemble -------------------------------------------------------
    metadata: dict[str, Any] = {
        "run_timestamp": config.run_timestamp(),
        "random_seed": config.RANDOM_SEED,
        "rolling_windows": list(rolling_windows),
        "latitude_used_for_radiation_imputation_deg": latitude_for_imputation,
        "rows": {
            "weather": len(weather),
            "soil": len(soil),
            "district_rainfall": len(district_rainfall),
            "crop_suitability": len(crop_suitability),
            "season_context": len(season_context),
        },
        "weather_date_range": [
            str(pd.to_datetime(weather["datetime"]).min().date()),
            str(pd.to_datetime(weather["datetime"]).max().date()),
        ],
        "validation": report.summary(),
        "imputations": [r.as_row() for r in ([radiation_record] if radiation_record else [])],
        "feature_count": len(registry),
    }

    result = PreprocessingResult(
        weather=weather,
        soil=soil,
        district_rainfall=district_rainfall,
        crop_suitability=crop_suitability,
        season_context=season_context,
        validation=report,
        cleaning_log=pd.concat(cleaning_frames, ignore_index=True),
        raw_vs_cleaned=pd.concat(audit_frames, ignore_index=True),
        profiles=pd.concat(profile_frames, ignore_index=True),
        missing_summary=missing_value_handler.missing_value_summary(
            {
                "climate": weather, "soil": soil,
                "rainfall_district": district_rainfall,
                "crop_recommendation": crop_suitability,
                "season_context": season_context,
            }
        ),
        imputations=[r for r in [radiation_record] if r is not None],
        lineage=registry,
        metadata=metadata,
    )

    if write_outputs:
        write_processed(result)
    return result


def write_processed(result: PreprocessingResult, directory: Path | None = None) -> dict[str, Path]:
    """Persist the analysis-ready tables and the run metadata."""
    directory = directory or config.PROCESSED_DIR
    directory.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    tables = {
        "daily_weather": result.weather,
        "soil_district_samples": result.soil,
        "district_rainfall_normals": result.district_rainfall,
        "crop_suitability_samples": result.crop_suitability,
        "season_context": result.season_context,
    }
    for name, frame in tables.items():
        path = directory / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        frame.to_csv(directory / f"{name}.csv", index=False, encoding="utf-8")
        written[name] = path
        log.info("wrote %s (%d rows x %d cols)", path.name, len(frame), frame.shape[1])

    lineage_path = directory / "feature_lineage.csv"
    result.lineage.save(lineage_path)
    written["feature_lineage"] = lineage_path

    metadata_path = directory / "preprocessing_metadata.json"
    metadata_path.write_text(json.dumps(result.metadata, indent=2, default=str), encoding="utf-8")
    written["metadata"] = metadata_path
    log.info("wrote %s", metadata_path.name)
    return written
