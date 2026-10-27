"""Typed loaders for every dataset in the study.

Three principles drive this module.

1. *Raw files are read-only.* :func:`raw_fingerprint` hashes them so a test can
   prove they were never edited, and nothing here ever opens a raw file for
   writing.
2. *Every dataset is declared before it is read.* :data:`DATASETS` is the single
   registry of what exists, what role it plays in the study, and which columns
   it is expected to carry. A silent schema drift becomes a loud failure.
3. *Column names are normalised once, here.* The source files mix spaces,
   capitals and punctuation (``"Nitrogen Value"``, ``"Kc (Crop Coefficient)"``);
   downstream code should never have to know that.
"""

from __future__ import annotations

import dataclasses
import hashlib
import re
from pathlib import Path
from typing import Final

import pandas as pd

from ml import config
from ml.logging_utils import get_logger

log = get_logger("data_loader")


# --------------------------------------------------------------------------
# Dataset registry
# --------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class DatasetSpec:
    """Declares one source file and the role it plays in the research."""

    key: str
    raw_filename: str
    cleaned_filename: str | None
    role: str
    #: ``primary`` feeds the CWR study; ``reference`` supplies agronomic
    #: constants; ``supporting`` provides context only; ``excluded`` is kept
    #: for the audit trail but must not enter the modelling path.
    tier: str
    expected_columns: tuple[str, ...]
    notes: str

    def raw_path(self) -> Path:
        return config.RAW_DIR / self.raw_filename

    def cleaned_path(self) -> Path | None:
        if self.cleaned_filename is None:
            return None
        return config.CLEANED_DIR / self.cleaned_filename


DATASETS: Final[dict[str, DatasetSpec]] = {
    "climate": DatasetSpec(
        key="climate",
        raw_filename="Climate_Data.csv",
        cleaned_filename="Climate_Data_cleaned.csv",
        role="Daily meteorological series driving ET0.",
        tier="primary",
        expected_columns=(
            "datetime", "DATE", "MONTH", "YEAR", "T2M", "T2M_MIN", "T2M_MAX",
            "RH2M", "WS2M", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN",
        ),
        notes=(
            "Column names match the NASA POWER daily-point parameter set exactly "
            "(T2M, RH2M, WS2M, PRECTOTCORR, ALLSKY_SFC_SW_DWN), which fixes the "
            "units but not the location: no latitude/longitude column is present."
        ),
    ),
    "crop_calendar": DatasetSpec(
        key="crop_calendar",
        raw_filename="Crop_Calender.csv",
        cleaned_filename="Crop_Calender_cleaned.csv",
        role="Stage durations, rooting depth and Kc for five crops.",
        tier="reference",
        expected_columns=(
            "Crop", "Stage", "Duration (days)", "Root Depth (cm)",
            "Kc (Crop Coefficient)", "ETo (mm/day)", "ETc (mm/day)",
            "Effective Rainfall (mm)", "WHC (mm/m)",
        ),
        notes=(
            "The ETo/ETc columns are the compiler's own worked example, not "
            "measurements, and are not used as data. Only Kc, stage duration, "
            "root depth and water-holding capacity are consumed."
        ),
    ),
    "growth_stage_reference": DatasetSpec(
        key="growth_stage_reference",
        raw_filename="Karnataka_Crop_Growth_Stage_Reference.xlsx",
        cleaned_filename="Karnataka_Crop_Growth_Stage_Reference_cleaned.csv",
        role="Growth-stage-aware Kc references for paddy, finger millet and maize.",
        tier="reference",
        expected_columns=(
            "Crop", "Growth Stage", "Stage Description",
            "Indicative Duration / Timing", "Kc Reference", "Kc Type",
            "Evidence Source",
        ),
        notes=(
            "Kc values are held as free text with ranges and citations; "
            "ml/crop_reference.py parses them under documented rules."
        ),
    ),
    "crop_recommendation": DatasetSpec(
        key="crop_recommendation",
        raw_filename="Crop_recommendation.csv",
        cleaned_filename="Crop_recommendation_cleaned.csv",
        role="Agronomic suitability samples for the crop-recommendation module.",
        tier="primary",
        expected_columns=("N", "P", "K", "temperature", "humidity", "ph", "rainfall", "label"),
        notes="Feeds the suitability classifier only; never the CWR regression.",
    ),
    "soil": DatasetSpec(
        key="soil",
        raw_filename="Soil data.csv",
        cleaned_filename="Soil_data_cleaned.csv",
        role="District-level soil nutrient and pH samples.",
        tier="supporting",
        expected_columns=("District", "Nitrogen Value", "Phosphorous value", "Potassium value", "pH"),
        notes="District aggregates only; no field-level or dated sampling.",
    ),
    "rainfall_district": DatasetSpec(
        key="rainfall_district",
        raw_filename="Rainfall_2016_districtwise.csv",
        cleaned_filename="Rainfall_2016_districtwise_cleaned.csv",
        role="Karnataka district normal annual rainfall and rain-gauge counts.",
        tier="supporting",
        expected_columns=("Sl.No", "Districts"),
        notes=(
            "Annual normals, not a daily series. Usable as a regional context "
            "lookup; it cannot join to a daily weather record."
        ),
    ),
    "crop_water": DatasetSpec(
        key="crop_water",
        raw_filename="crop_water_data.csv",
        cleaned_filename="crop_water_data_cleaned.csv",
        role="Candidate CWR target, held under investigation.",
        tier="excluded",
        expected_columns=(
            "crop_type", "soil_type", "growth_stage", "temperature", "humidity",
            "rainfall_mm", "wind_speed_kmh", "solar_radiation", "field_area_ha",
            "irrigation_method", "crop_age_days", "soil_moisture_pct",
            "evapotranspiration", "water_requirement_liters",
        ),
        notes=(
            "Retained as a documented negative control. ml/target_audit.py shows "
            "it fails physical-consistency and distributional realism tests, so "
            "water_requirement_liters is not used as ground truth."
        ),
    ),
    "season_context": DatasetSpec(
        key="season_context",
        raw_filename="data_season.csv",
        cleaned_filename="data_season_supporting_cleaned.csv",
        role="Karnataka crop/area/price/season context, 2004-2019.",
        tier="supporting",
        expected_columns=("Year", "Location", "Area", "Rainfall", "Soil type", "Irrigation", "Humidity", "Crops", "price", "Season"),
        notes=(
            "The raw file's Temperature column reaches physically impossible "
            "values and was dropped during earlier cleaning; it stays dropped."
        ),
    ),
    "crop_generic": DatasetSpec(
        key="crop_generic",
        raw_filename="crop_dataset.csv",
        cleaned_filename=None,
        role="Unlabelled temperature/humidity/rainfall to water-volume table.",
        tier="excluded",
        expected_columns=("temperature_C", "humidity_%", "rainfall_mm", "water_required_liters"),
        notes=(
            "No crop, no date, no location, no stated units for the target. "
            "Archived for completeness; outside the research path."
        ),
    ),
    # ----------------------------------------------------------------------
    # Sources brought in from the Crop Intelligence Platform
    # ----------------------------------------------------------------------
    # These three are what make water *productivity* computable. The water
    # engine already knows how much a crop drinks; none of the original
    # AgriHydro files said what the crop produced in return, or what that
    # produce is worth, or what rain actually fell in a named district. These
    # do. Their coverage limits are stated per file, because each one is
    # narrower than it first appears.
    "district_yield": DatasetSpec(
        key="district_yield",
        raw_filename="Crops_data.csv",
        cleaned_filename=None,
        role="District-year crop yield, area and production, 2010-2017.",
        tier="primary",
        expected_columns=(
            "Dist Code", "Year", "State Code", "State Name", "Dist Name",
            "RICE YIELD (Kg per ha)", "WHEAT YIELD (Kg per ha)",
        ),
        notes=(
            "Wide format: an AREA/PRODUCTION/YIELD triplet per crop across 80 "
            "columns, reshaped to long by build_district_yield(). 2484 "
            "district-year rows over 311 districts and 20 states. SORGHUM and "
            "OILSEEDS are aggregates of other columns in the same file and are "
            "flagged so they are never double-counted against their parts. "
            "Yields are reported production over reported area, so a district "
            "with unreported area yields a zero that means 'not recorded' "
            "rather than 'nothing grew'; those rows are flagged, not dropped."
        ),
    ),
    "district_rainfall_daily": DatasetSpec(
        key="district_rainfall_daily",
        raw_filename="rainfall_districtwise_daily_imd.csv",
        cleaned_filename=None,
        role="IMD daily district rainfall, actual against long-period normal.",
        tier="supporting",
        expected_columns=("State", "District", "Date", "Daily Actual", "Daily Normal"),
        notes=(
            "COVERAGE IS SHORT: 19 August to 7 September 2026, twenty days. "
            "14545 rows covering 728 districts nationally, of which 620 rows are "
            "Karnataka across 31 districts. This supports current-season "
            "context - departure from "
            "normal, dry-spell length - and nothing longer. It is not a "
            "climatology and must never be used as one. Column names carry "
            "embedded newlines and a misspelling ('Departue') in the source; "
            "they are normalised on read rather than corrected in the file."
        ),
    ),
    "market_prices": DatasetSpec(
        key="market_prices",
        raw_filename="Market_Wise_Price_Arrival_08-09-2026_08-43-27_AM.xlsx",
        cleaned_filename=None,
        role="Commodity price, arrival volume and minimum support price.",
        tier="supporting",
        expected_columns=("Commodity Group", "Commodity", "MSP (Rs./Quintal) 2026-27"),
        notes=(
            "COVERAGE IS SHORT: three observation dates, 4-6 September 2026, "
            "19 commodities, 57 commodity-date slots of which only 46 carry a "
            "numeric price. The header sits on the third row under a title "
            "row. A dash in the source means no trade was recorded and is kept "
            "as null rather than zero. Any rupees-per-cubic-metre figure "
            "derived from this is a snapshot at one week's prices, not a "
            "seasonal average, and the interface says so."
        ),
    ),
}

PRIMARY_KEYS: Final[tuple[str, ...]] = tuple(
    k for k, s in DATASETS.items() if s.tier == "primary"
)


# --------------------------------------------------------------------------
# Column-name normalisation
# --------------------------------------------------------------------------
_NON_ALNUM = re.compile(r"[^0-9a-zA-Z]+")

#: Names that the generic slugifier would render awkwardly, or that carry a
#: unit we want to keep visible in the column name.
_EXPLICIT_RENAMES: Final[dict[str, str]] = {
    "duration_days": "duration_days",
    "root_depth_cm": "root_depth_cm",
    "kc_crop_coefficient": "kc",
    "eto_mm_day": "reference_eto_mm_day_source",
    "etc_mm_day": "reference_etc_mm_day_source",
    "effective_rainfall_mm": "season_effective_rainfall_mm_source",
    "whc_mm_m": "water_holding_capacity_mm_per_m",
    "nitrogen_value": "nitrogen",
    "phosphorous_value": "phosphorus",
    "potassium_value": "potassium",
    "ph": "ph",
    "sl_no": "serial_no",
    "districts": "district",
    "raingaugestations_working_r_gs": "raingauge_working",
    "raingaugestations_not_working": "raingauge_not_working",
    "raingauge_stations_total": "raingauge_total",
    "annual_normal_rainfall_rainydays": "normal_rainy_days",
    "normal_rainfall": "normal_annual_rainfall_mm",
    "growth_stage": "growth_stage",
    "stage_description": "stage_description",
    "indicative_duration_timing": "timing_text",
    "kc_reference": "kc_text",
    "kc_type": "kc_type",
    "evidence_source": "evidence_source",
    "temperature_c": "temperature",
    "humidity": "humidity",
    "soil_type": "soil_type",
    "yeilds": "yield_value",
}


def slugify_column(name: str) -> str:
    """Turn a source column heading into a snake_case identifier."""
    text = _NON_ALNUM.sub("_", str(name).strip()).strip("_").lower()
    text = re.sub(r"_+", "_", text)
    return _EXPLICIT_RENAMES.get(text, text)


def normalise_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``frame`` with snake_case column names."""
    out = frame.copy()
    out.columns = [slugify_column(c) for c in out.columns]
    return out


# --------------------------------------------------------------------------
# Raw-file integrity
# --------------------------------------------------------------------------
def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def raw_fingerprint() -> pd.DataFrame:
    """Hash every file under ``datasets/raw`` so edits become detectable."""
    rows = []
    for path in sorted(config.RAW_DIR.iterdir()):
        if path.is_file():
            rows.append(
                {
                    "filename": path.name,
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
            )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------
def _read_any(path: Path) -> pd.DataFrame:
    """Read a CSV or Excel file, tolerating the non-UTF-8 bytes in the raw CSVs."""
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    try:
        return pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        log.warning("%s is not valid UTF-8; re-reading as latin-1", path.name)
        return pd.read_csv(path, encoding="latin-1")


def load_dataset(
    key: str,
    *,
    stage: str = "cleaned",
    normalise: bool = True,
) -> pd.DataFrame:
    """Load one registered dataset.

    Parameters
    ----------
    key
        A key of :data:`DATASETS`.
    stage
        ``"cleaned"`` (default) reads from ``datasets/cleaned``, falling back to
        ``datasets/raw`` when no cleaned counterpart exists. ``"raw"`` always
        reads the untouched original, which is what the raw-versus-cleaned audit
        uses.
    normalise
        Apply :func:`normalise_columns`. Turn this off when comparing against
        the literal source headings.
    """
    if key not in DATASETS:
        raise KeyError(f"Unknown dataset {key!r}. Known: {sorted(DATASETS)}")
    spec = DATASETS[key]

    if stage == "raw":
        path = spec.raw_path()
    elif stage == "cleaned":
        path = spec.cleaned_path() or spec.raw_path()
    else:
        raise ValueError(f"stage must be 'raw' or 'cleaned', got {stage!r}")

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset {key!r} expected at {path}, which does not exist. "
            "Datasets are tracked in the repository; restore it rather than "
            "substituting a different file."
        )

    frame = _read_any(path)
    log.info("loaded %-22s %-12s %5d rows x %2d cols  <- %s",
             key, f"[{stage}]", len(frame), frame.shape[1], path.name)
    return normalise_columns(frame) if normalise else frame


def load_all(stage: str = "cleaned", *, include_excluded: bool = True) -> dict[str, pd.DataFrame]:
    """Load every registered dataset that exists at ``stage``."""
    out: dict[str, pd.DataFrame] = {}
    for key, spec in DATASETS.items():
        if not include_excluded and spec.tier == "excluded":
            continue
        try:
            out[key] = load_dataset(key, stage=stage)
        except FileNotFoundError as exc:
            log.warning("skipping %s: %s", key, exc)
    return out


def registry_frame() -> pd.DataFrame:
    """The dataset registry as a table, for reports and the notebook."""
    rows = []
    for spec in DATASETS.values():
        cleaned = spec.cleaned_path()
        rows.append(
            {
                "key": spec.key,
                "tier": spec.tier,
                "raw_file": spec.raw_filename,
                "cleaned_file": spec.cleaned_filename or "-",
                "raw_exists": spec.raw_path().exists(),
                "cleaned_exists": bool(cleaned and cleaned.exists()),
                "role": spec.role,
                "notes": spec.notes,
            }
        )
    return pd.DataFrame(rows)
