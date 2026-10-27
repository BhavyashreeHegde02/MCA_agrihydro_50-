"""Build the application-facing curated data layer without blending evidence.

Raw and cleaned inputs are read-only. The only write target is
``datasets/curated``; weather, soil, and rainfall remain independent context
tables because their provenance does not support field-level joins.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from ml import config, data_loader, water_productivity


OUTPUT_DIR = config.DATASETS_DIR / "curated"
AGGREGATE_CROPS = water_productivity.AGGREGATE_CROPS

_CROP_ALIASES: dict[str, tuple[str, str]] = {
    "paddy": ("rice", "Paddy is identified as rice in the source reference."),
    "paddy rice": ("rice", "Paddy is identified as rice in the source reference."),
    "paddy (rice)": ("rice", "Paddy is identified as rice in the source reference."),
    "finger millet ragi": (
        "finger_millet", "Ragi is identified as finger millet in the source reference."
    ),
    "finger millet (ragi)": (
        "finger_millet", "Ragi is identified as finger millet in the source reference."
    ),
    "ragi": ("finger_millet", "Ragi is identified as finger millet in the source reference."),
    "soyabean": ("soybean", "Documented spelling variant of soybean."),
    "soybean": ("soybean", "Source name normalized to lowercase."),
}

_CATEGORY_BY_CROP: dict[str, str] = {
    "rice": "cereal",
    "wheat": "cereal",
    "maize": "cereal",
    "barley": "cereal",
    "sorghum": "cereal",
    "kharif_sorghum": "cereal",
    "rabi_sorghum": "cereal",
    "pearl_millet": "millet",
    "finger_millet": "millet",
    "chickpea": "pulse",
    "pigeonpea": "pulse",
    "minor_pulses": "pulse",
    "groundnut": "oilseed",
    "sesamum": "oilseed",
    "rapeseed_and_mustard": "oilseed",
    "safflower": "oilseed",
    "castor": "oilseed",
    "linseed": "oilseed",
    "sunflower": "oilseed",
    "soybean": "oilseed",
    "oilseeds": "aggregate",
    "sugarcane": "sugar",
    "cotton": "fibre",
    "fruits": "fruit",
    "vegetables": "vegetable",
    "fruits_and_vegetables": "aggregate",
    "potatoes": "vegetable",
    "onion": "vegetable",
    "fodder": "fodder",
    "cumin": "spice",
    "chickpea": "pulse",
}


def _slug(value: object) -> str:
    text = re.sub(r"\([^)]*\)", " ", str(value)).strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _canonical_crop(value: object) -> tuple[str, str, str]:
    original = str(value).strip()
    key = re.sub(r"\s+", " ", original.lower())
    if key in _CROP_ALIASES:
        canonical, reason = _CROP_ALIASES[key]
        return canonical, reason, "REVIEWED_EXPLICIT_MAPPING"
    canonical = _slug(original)
    return canonical, "Lowercase and separator normalization only.", "FORMAT_NORMALIZED"


def _category(canonical_crop: str) -> str | None:
    return _CATEGORY_BY_CROP.get(canonical_crop)


def _source_row_ids(source_dataset: str, count: int) -> list[str]:
    """Use physical CSV record numbers for lineage, never as join keys."""
    return [f"{source_dataset}:row:{row_number}" for row_number in range(2, count + 2)]


def _crop_header_labels(raw_columns: list[object]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for column in raw_columns:
        normalized = data_loader.normalise_columns(pd.DataFrame(columns=[column])).columns[0]
        if normalized.endswith("_area_1000_ha"):
            slug = normalized.removesuffix("_area_1000_ha")
            label = re.split(r"\s+AREA\b", str(column), maxsplit=1, flags=re.IGNORECASE)[0].strip()
            labels[slug] = label
    return labels


def _load_crop_sources(project_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw_path = project_root / "datasets" / "raw" / "Crops_data.csv"
    raw = data_loader._read_any(raw_path)
    raw_normalized = data_loader.normalise_columns(raw)
    source_key = ["dist_code", "year", "state_name", "dist_name"]
    if raw_normalized.duplicated(source_key).any():
        raise ValueError("Crops_data.csv has duplicate district-year source keys.")

    raw_normalized["_source_row_id"] = _source_row_ids("Crops_data.csv", len(raw_normalized))
    long = water_productivity.build_district_yield(raw)
    long = long.merge(
        raw_normalized[source_key + ["state_code", "_source_row_id"]],
        left_on=["district_code", "year", "state", "district"],
        right_on=["dist_code", "year", "state_name", "dist_name"],
        how="left",
        validate="many_to_one",
        indicator="_source_match",
    )
    if not long["_source_match"].eq("both").all():
        raise ValueError("Some reshaped crop records could not be traced to source rows.")

    source_labels = _crop_header_labels(list(raw.columns))
    long["crop_source_slug"] = long["crop"].map(_slug)
    long["crop"] = long["crop_source_slug"].map(source_labels)
    if long["crop"].isna().any():
        raise ValueError("A crop series could not be mapped to its source column label.")
    source_crop_names = sorted(long["crop"].dropna().unique())
    mapping_sources = {crop: "Crops_data.csv" for crop in source_crop_names}
    for filename, column in (
        ("Karnataka_Crop_Growth_Stage_Reference_cleaned.csv", "Crop"),
        ("Crop_Calender_cleaned.csv", "Crop"),
    ):
        reference = pd.read_csv(project_root / "datasets" / "cleaned" / filename)
        for crop in reference[column].dropna().astype(str).str.strip().unique():
            mapping_sources.setdefault(crop, filename)

    long = long[~long["is_aggregate"]].copy()
    # Rows with no positive reported area are not evidence that a crop was grown.
    long = long[pd.to_numeric(long["area_1000_ha"], errors="coerce").gt(0)].copy()

    mapping_rows: list[dict[str, Any]] = []
    for crop, source_dataset in sorted(mapping_sources.items()):
        canonical, reason, mapping_status = _canonical_crop(crop)
        category = _category(canonical)
        mapping_rows.append(
            {
                "original_crop_name": crop,
                "canonical_crop_name": canonical,
                "crop_category": category,
                "mapping_reason": reason,
                "mapping_source": f"{source_dataset}; explicit mapping/format rules in ml/data_integration.py",
                "source_dataset": source_dataset,
                "source_row_id": f"{source_dataset}:crop_label:{crop}",
                "mapping_status": mapping_status if category else "REVIEW_REQUIRED_CATEGORY",
                "transformation_type": (
                    "EXPLICIT_CANONICAL_ALIAS" if mapping_status == "REVIEWED_EXPLICIT_MAPPING"
                    else "FORMAT_NORMALIZATION_ONLY"
                ),
            }
        )
    crop_mapping = pd.DataFrame(mapping_rows)

    season = long["crop"].str.extract(r"^(Kharif|Rabi)\s+", expand=False)
    long["season"] = season.fillna("ANNUAL")
    crop_lookup = crop_mapping.set_index("original_crop_name")
    long["canonical_crop"] = long["crop"].map(crop_lookup["canonical_crop_name"])
    long["crop_category"] = long["crop"].map(crop_lookup["crop_category"])
    long["mapping_status"] = long["crop"].map(crop_lookup["mapping_status"])

    evidence = pd.DataFrame(
        {
            "state": long["state"],
            "district": long["district"],
            "district_code": long["district_code"],
            "state_code": long["state_code"],
            "canonical_state": long["state"].astype(str).str.strip().str.upper(),
            "canonical_district": long["district"].astype(str).str.strip().str.upper().str.replace(r"\s+", " ", regex=True),
            "year": long["year"],
            "crop": long["crop"],
            "canonical_crop": long["canonical_crop"],
            "crop_category": long["crop_category"],
            "area": long["area_1000_ha"],
            "production": long["production_1000_t"],
            "yield": long["yield_kg_ha"],
            "season": long["season"],
            "evidence_type": "HISTORICAL_CROP_PRODUCTION",
            "source_dataset": "Crops_data.csv",
            "source_row_id": long["_source_row_id"],
            "transformation_type": "WIDE_CROP_TRIPLET_UNPIVOT",
            "mapping_status": long["mapping_status"],
        }
    ).reset_index(drop=True)
    duplicate_key = ["state_code", "district_code", "year", "canonical_crop", "season"]
    if evidence.duplicated(duplicate_key).any():
        raise ValueError("Crop evidence contains duplicate district-year-crop-season keys.")
    return evidence, crop_mapping, raw_normalized


def _build_location_mapping(raw_normalized: pd.DataFrame) -> pd.DataFrame:
    raw = raw_normalized[["state_name", "dist_name", "state_code", "dist_code"]].drop_duplicates()
    state_canonical = raw["state_name"].astype(str).str.strip().str.upper().str.replace(r"\s+", " ", regex=True)
    district_canonical = raw["dist_name"].astype(str).str.strip().str.upper().str.replace(r"\s+", " ", regex=True)
    return pd.DataFrame(
        {
            "original_state": raw["state_name"].to_numpy(),
            "canonical_state": state_canonical.to_numpy(),
            "original_district": raw["dist_name"].to_numpy(),
            "canonical_district": district_canonical.to_numpy(),
            "state_code": raw["state_code"].to_numpy(),
            "district_code": raw["dist_code"].to_numpy(),
            "mapping_status": [
                "FORMAT_ONLY" if str(a) != str(b) or str(c) != str(d) else "IDENTITY_PRESERVED"
                for a, b, c, d in zip(raw["state_name"], state_canonical, raw["dist_name"], district_canonical)
            ],
            "mapping_source": "Crops_data.csv; no district-boundary crosswalk applied",
            "source_dataset": "Crops_data.csv",
            "source_row_id": [f"Crops_data.csv:district_code:{code}" for code in raw["dist_code"]],
            "transformation_type": "FORMAT_NORMALIZATION_ONLY",
        }
    ).reset_index(drop=True)


def _active_model_support(project_root: Path) -> tuple[set[str], str]:
    pointer = project_root / "artifacts" / "models" / "ACTIVE"
    if not pointer.exists():
        return set(), "NO_ACTIVE_MODEL"
    active_reference = pointer.read_text(encoding="utf-8").strip()
    if "/" not in active_reference:
        return set(), "INVALID_ACTIVE_POINTER"
    model_path = project_root / "artifacts" / "models" / active_reference / "metadata.json"
    if not model_path.exists():
        return set(), "ACTIVE_MODEL_METADATA_MISSING"
    metadata = json.loads(model_path.read_text(encoding="utf-8"))
    test_n = ((metadata.get("metrics") or {}).get("test") or {}).get("n", 0)
    task = (metadata.get("task") or {}).get("task")
    target = metadata.get("target_definition") or {}
    crops = (metadata.get("baseline_assumptions") or {}).get("crop_coefficients", {}).get("crops", [])
    feature_order = metadata.get("feature_order") or []
    validated = (
        task == "reduced_input"
        and target.get("name") == "etc_mm_day"
        and target.get("provenance_class") == "reference_derived"
        and target.get("is_field_observed") is False
        and isinstance(test_n, int)
        and test_n > 0
        and "crop" in feature_order
    )
    if not validated:
        return set(), "ACTIVE_MODEL_NOT_VALIDATED_FOR_CROP_SUPPORT"
    canonical = set()
    for crop in crops:
        canonical_name, _, _ = _canonical_crop(crop)
        canonical.add(canonical_name)
    # The model calls this crop paddy; the production/reference source calls the
    # same crop rice, as documented by YIELD_CROP_NAMES in water_productivity.
    if "paddy" in canonical:
        canonical.add("rice")
    return canonical, f"{active_reference}; validated held-out rows={test_n}; target=reference-derived"


def _support_status(canonical_crop: str, supported: set[str], reference_crops: set[str]) -> str:
    if canonical_crop in supported:
        return "SUPPORTED"
    if canonical_crop in reference_crops:
        return "REFERENCE_ONLY"
    return "UNDER_DEVELOPMENT"


def _build_reference_catalog(
    project_root: Path,
    evidence: pd.DataFrame,
    supported: set[str],
) -> pd.DataFrame:
    stage_path = project_root / "datasets" / "processed" / "crop_stage_reference.csv"
    stages = pd.read_csv(stage_path)
    stages["canonical_crop"] = stages["crop"].map(
        lambda crop: _canonical_crop(crop)[0]
    )
    reference_crops = set(stages["canonical_crop"].dropna())
    category_by_crop = {
        crop: category
        for crop, category in zip(evidence["canonical_crop"], evidence["crop_category"])
    }
    for crop in reference_crops:
        category_by_crop.setdefault(crop, _category(crop))

    rows: list[dict[str, Any]] = []
    for source_line, row in enumerate(stages.to_dict("records"), start=2):
        crop = row["canonical_crop"]
        source = str(row["source"])
        rows.append(
            {
                "crop": row["display_name"],
                "canonical_crop": crop,
                "crop_category": category_by_crop.get(crop),
                "growth_stage": row["stage"],
                "kc": row["kc_anchor"],
                "duration_days": row["duration_days"],
                "source": source,
                "reference_type": "MODEL_STAGE_REFERENCE",
                "cwr_support_status": _support_status(crop, supported, reference_crops),
                "source_dataset": source,
                "source_row_id": f"crop_stage_reference.csv:row:{source_line}",
                "transformation_type": "MODEL_STAGE_REFERENCE_PRESERVED",
                "mapping_status": "CANONICAL_CROP_MAPPED",
            }
        )
    referenced = set(stages["canonical_crop"].dropna())
    observed = set(evidence["canonical_crop"].dropna())
    for crop in sorted(observed - referenced):
        source_name = evidence.loc[evidence["canonical_crop"].eq(crop), "crop"].iloc[0]
        rows.append(
            {
                "crop": source_name,
                "canonical_crop": crop,
                "crop_category": category_by_crop.get(crop),
                "growth_stage": pd.NA,
                "kc": pd.NA,
                "duration_days": pd.NA,
                "source": pd.NA,
                "reference_type": "NO_STAGE_REFERENCE",
                "cwr_support_status": _support_status(crop, supported, reference_crops),
                "source_dataset": "Crops_data.csv",
                "source_row_id": f"Crops_data.csv:crop:{crop}",
                "transformation_type": "CROP_EVIDENCE_CATALOG_ENTRY",
                "mapping_status": "CANONICAL_CROP_MAPPED",
            }
        )
    return pd.DataFrame(rows)


def _build_soil_context(project_root: Path) -> pd.DataFrame:
    path = project_root / "datasets" / "cleaned" / "Soil_data_cleaned.csv"
    source = pd.read_csv(path)
    return pd.DataFrame(
        {
            "state_if_verified": pd.NA,
            "district": source["District"],
            "nitrogen": source["Nitrogen Value"],
            "phosphorus": source["Phosphorous value"],
            "potassium": source["Potassium value"],
            "ph": source["pH"],
            "data_status": "PROVISIONAL",
            "source_dataset": "Soil_data_cleaned.csv",
            "source_row_id": _source_row_ids("Soil_data_cleaned.csv", len(source)),
            "transformation_type": "COLUMN_RENAME_STATE_UNVERIFIED",
            "mapping_status": "STATE_SAMPLE_DATE_UNVERIFIED",
        }
    )


def _build_rainfall_context(project_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    daily = data_loader.load_dataset("district_rainfall_daily", stage="raw")
    category = daily["daily_category"].astype("string")
    rainfall = pd.DataFrame(
        {
            "state": daily["state"],
            "district": daily["district"],
            "date": pd.to_datetime(daily["date"], errors="coerce"),
            "rainfall": pd.to_numeric(daily["daily_actual"], errors="coerce"),
            "category": category,
            "period_type": "DAILY_OBSERVATION",
            "source_dataset": "rainfall_districtwise_daily_imd.csv",
            "source_row_id": _source_row_ids("rainfall_districtwise_daily_imd.csv", len(daily)),
            "quality_flag": [
                "CATEGORY_ND_ZERO_UNVERIFIED" if str(value).strip().upper() == "ND" else "AS_REPORTED"
                for value in category
            ],
            "transformation_type": "DAILY_FIELDS_NORMALIZED",
            "mapping_status": "SOURCE_LOCATION_LABEL_PRESERVED",
        }
    )

    normal_path = project_root / "datasets" / "processed" / "district_rainfall_normals.csv"
    normals = pd.read_csv(normal_path)
    annual_normals = pd.DataFrame(
        {
            "state": "Karnataka",
            "district": normals["district"],
            "date": pd.NaT,
            "rainfall": pd.to_numeric(normals["normal_annual_rainfall_mm"], errors="coerce"),
            "category": "ANNUAL_NORMAL",
            "period_type": "ANNUAL_NORMAL",
            "source_dataset": "Rainfall_2016_districtwise.csv",
            "source_row_id": [
                f"district_rainfall_normals.csv:district_code:{code}"
                for code in normals["serial_no"]
            ],
            "quality_flag": "NORMAL_REFERENCE_PERIOD_UNSPECIFIED",
            "transformation_type": "ANNUAL_NORMAL_PRESERVED_SEPARATELY",
            "mapping_status": "SOURCE_DISTRICT_LABEL_PRESERVED",
        }
    )
    return rainfall, annual_normals


def _build_weather_context(project_root: Path) -> pd.DataFrame:
    path = project_root / "datasets" / "cleaned" / "Climate_Data_cleaned.csv"
    climate = pd.read_csv(path)
    return pd.DataFrame(
        {
            "date": pd.to_datetime(climate["datetime"], errors="coerce"),
            "tavg": climate["T2M"],
            "tmin": climate["T2M_MIN"],
            "tmax": climate["T2M_MAX"],
            "relative_humidity": climate["RH2M"],
            "wind_speed": climate["WS2M"],
            "precipitation": climate["PRECTOTCORR"],
            "solar_radiation": climate["ALLSKY_SFC_SW_DWN"],
            "site_id": "UNKNOWN",
            "location_status": "UNKNOWN",
            "units_status": "UNVERIFIED",
            "provenance_status": "UNVERIFIED",
            "source_dataset": "Climate_Data_cleaned.csv",
            "source_row_id": _source_row_ids("Climate_Data_cleaned.csv", len(climate)),
            "transformation_type": "CLEANED_CLIMATE_FIELDS_RENAMED",
            "mapping_status": "NO_LOCATION_JOIN",
        }
    )


def _join_report(
    left: str,
    right: str,
    key: str,
    cardinality: str,
    matched: int,
    unmatched: int,
    expansion: int,
    temporal: str,
    spatial: str,
    units: str,
    status: str,
) -> dict[str, Any]:
    return {
        "left_dataset": left,
        "right_dataset": right,
        "join_key": key,
        "cardinality": cardinality,
        "matched_rows": matched,
        "unmatched_rows": unmatched,
        "duplicate_expansion": expansion,
        "temporal_compatibility": temporal,
        "spatial_compatibility": spatial,
        "unit_compatibility": units,
        "status": status,
    }


def _build_join_report(
    evidence: pd.DataFrame,
    crop_mapping: pd.DataFrame,
    location_mapping: pd.DataFrame,
    reference_catalog: pd.DataFrame,
    soil_context: pd.DataFrame,
    rainfall_context: pd.DataFrame,
    rainfall_normals: pd.DataFrame,
    weather_context: pd.DataFrame,
) -> pd.DataFrame:
    evidence_crop_match = evidence["crop"].isin(crop_mapping["original_crop_name"])
    location_keys = location_mapping[["original_state", "original_district", "state_code", "district_code"]].drop_duplicates()
    evidence_location_match = pd.MultiIndex.from_frame(evidence[["state", "district", "state_code", "district_code"]]).isin(
        pd.MultiIndex.from_frame(location_keys)
    )
    reference_lookup = reference_catalog[["canonical_crop", "cwr_support_status"]].drop_duplicates("canonical_crop")
    if reference_lookup["canonical_crop"].duplicated().any():
        raise ValueError("Crop support lookup is not many-to-one.")
    reference_match = evidence["canonical_crop"].isin(reference_lookup["canonical_crop"])

    reports = [
        _join_report("crop_location_evidence", "canonical_crop_mapping", "crop = original_crop_name", "many-to-one", int(evidence_crop_match.sum()), int((~evidence_crop_match).sum()), 0, "year preserved", "source location preserved", "source fields retained", "SAFE"),
        _join_report("crop_location_evidence", "canonical_location_mapping", "state + district + state_code + district_code", "many-to-one", int(evidence_location_match.sum()), int((~evidence_location_match).sum()), 0, "year preserved", "historical labels retained; no boundary crosswalk", "not applicable", "SAFE"),
        _join_report("crop_location_evidence", "crop_reference_catalog", "canonical_crop to unique support lookup", "many-to-one", int(reference_match.sum()), int((~reference_match).sum()), 0, "no temporal join; crop key only", "no spatial join", "not applicable", "SAFE"),
        _join_report("crop_location_evidence", "weather_context", "none", "no join", 0, len(evidence), 0, "INCOMPATIBLE: crop years 2010-2017 vs weather 2018-2024", "UNKNOWN", "UNVERIFIED", "REJECTED_UNSAFE"),
        _join_report("crop_location_evidence", "soil_context_reference", "district only (insufficient)", "one-to-many / unresolved", 0, len(evidence), 0, "UNKNOWN", "REJECTED: no verified state/sample linkage", "UNVERIFIED", "REJECTED_UNSAFE"),
        _join_report("crop_location_evidence", "rainfall_context", "state + district would still be insufficient", "no join", 0, len(evidence), 0, "INCOMPATIBLE: 2026 observations vs 2010-2017 evidence", "source labels preserved; boundaries not aligned", "rainfall units unverified", "REJECTED_UNSAFE"),
        _join_report("rainfall_context", "rainfall_normals_context", "district only", "no join", 0, len(rainfall_context), 0, "REJECTED: daily observations vs annual normal with unknown reference period", "district boundary/version compatibility unverified", "rainfall units differ or unverified", "REJECTED_UNSAFE"),
        _join_report("weather_context", "crop_location_evidence", "none", "no join", 0, len(weather_context), 0, "INCOMPATIBLE date coverage", "UNKNOWN", "UNVERIFIED", "REJECTED_UNSAFE"),
    ]
    return pd.DataFrame(reports)


def _build_application_view(evidence: pd.DataFrame, catalog: pd.DataFrame) -> pd.DataFrame:
    support = catalog[["canonical_crop", "cwr_support_status"]].drop_duplicates("canonical_crop")
    if support["canonical_crop"].duplicated().any():
        raise ValueError("Cannot build application view from duplicate crop support keys.")
    keys = [
        "state", "canonical_state", "district", "canonical_district", "district_code",
        "season", "canonical_crop", "crop_category",
    ]
    view = evidence.groupby(keys, dropna=False, as_index=False).agg(
        years_represented=("year", "nunique"),
        first_year=("year", "min"),
        last_year=("year", "max"),
        mean_reported_area=("area", "mean"),
        mean_reported_production=("production", "mean"),
        mean_reported_yield=("yield", "mean"),
        source_row_ids=("source_row_id", lambda values: "|".join(sorted(set(values)))),
    )
    view = view.merge(support, on="canonical_crop", how="left", validate="many_to_one", indicator="_support_match")
    if not view["_support_match"].eq("both").all():
        raise ValueError("Application view contains a crop without a support status.")
    view["evidence_type"] = "REGIONAL_CROP_EVIDENCE_NOT_SUITABILITY"
    view["source_dataset"] = "Crops_data.csv"
    view["transformation_type"] = "GROUPED_REPORTED_POSITIVE_AREA_RECORDS"
    view["mapping_status"] = "CANONICAL_LOCATION_AND_CROP_MAPPED"
    return view.drop(columns="_support_match")


def build_curated_layer(
    project_root: Path | None = None,
    output_dir: Path | None = None,
    *,
    export: bool = True,
) -> dict[str, pd.DataFrame]:
    """Build curated tables from the repository's current pipeline outputs."""
    project_root = project_root or config.PROJECT_ROOT
    output_dir = output_dir or project_root / "datasets" / "curated"

    evidence, crop_mapping, raw_crop = _load_crop_sources(project_root)
    location_mapping = _build_location_mapping(raw_crop)
    supported, support_basis = _active_model_support(project_root)
    reference_catalog = _build_reference_catalog(project_root, evidence, supported)
    soil_context = _build_soil_context(project_root)
    rainfall_context, rainfall_normals = _build_rainfall_context(project_root)
    weather_context = _build_weather_context(project_root)
    application_view = _build_application_view(evidence, reference_catalog)
    join_report = _build_join_report(
        evidence, crop_mapping, location_mapping, reference_catalog,
        soil_context, rainfall_context, rainfall_normals, weather_context,
    )

    tables = {
        "canonical_crop_mapping": crop_mapping,
        "canonical_location_mapping": location_mapping,
        "crop_location_evidence": evidence,
        "crop_reference_catalog": reference_catalog,
        "soil_context_reference": soil_context,
        "rainfall_context": rainfall_context,
        "rainfall_normals_context": rainfall_normals,
        "weather_context": weather_context,
        "application_location_view": application_view,
        "join_validation_report": join_report,
    }
    if export:
        output_dir.mkdir(parents=True, exist_ok=True)
        for name, frame in tables.items():
            frame.to_csv(output_dir / f"{name}.csv", index=False, encoding="utf-8")
        summary = {
            "support_basis": support_basis,
            "table_rows": {name: len(frame) for name, frame in tables.items()},
            "join_status_counts": join_report["status"].value_counts().to_dict(),
            "raw_and_cleaned_inputs_written": False,
            "cartesian_products_created": False,
        }
        (output_dir / "integration_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
    return tables


__all__ = ["OUTPUT_DIR", "build_curated_layer"]