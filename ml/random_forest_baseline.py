"""Offline Random Forest research baseline, isolated from production models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline

from ml import models, target_builder
from ml.config import RANDOM_SEED

MODEL_NAME = "Random Forest"
MODEL_ROLE = "research_baseline"
TARGET_COLUMN = target_builder.TARGET_COLUMN
APPROVED_PANEL_RELATIVE_PATH = Path("datasets/processed/cwr_baseline_panel.parquet")
TARGET_ASSESSMENT_RELATIVE_PATH = Path("docs/target_assessment.md")
TARGET_METADATA_RELATIVE_PATH = Path(
    "artifacts/models/reduced_input/v2/metadata.json"
)
RESEARCH_OUTPUT_RELATIVE_PATH = Path(
    "artifacts/research_baselines/random_forest"
)
PRODUCTION_MODEL_RELATIVE_PATH = Path("artifacts/models")
QUARANTINED_TARGET_DATASETS = frozenset(
    {"crop_dataset.csv", "crop_water_data.csv", "data_season.csv"}
)
RESEARCH_FEATURES = tuple(target_builder.TASKS["reduced_input"].features)

LEAKAGE_AUDIT = (
    ("et0_mm_day", "EXCLUDED", "Direct FAO-56 reference input; target is ET0 × Kc."),
    ("kc", "EXCLUDED", "Direct crop-coefficient multiplier in the target."),
    ("etc_mm_day", "EXCLUDED", "The target itself must never appear in X."),
    ("allsky_sfc_sw_dwn", "EXCLUDED", "Withheld from the approved reduced-input task."),
    ("ws2m", "EXCLUDED", "Withheld from the approved reduced-input task."),
    ("rn_mj_m2_day and other ET0-derived terms", "EXCLUDED", "Downstream of FAO-56 ET0."),
    ("effective_rainfall_mm", "EXCLUDED", "Water-balance output, not a permitted input."),
    ("net_irrigation_mm and gross_irrigation_mm", "EXCLUDED", "Derived after the crop-water calculation."),
    (
        "root_zone_depletion_mm, depletion_fraction, irrigation_triggered",
        "EXCLUDED",
        "Post-event irrigation-state outputs.",
    ),
    (
        "selected reduced-input predictors",
        "ALLOWED (LAGGED 1 DAY)",
        "Only the prior observation day within the same crop cohort is available at issue time.",
    ),
)


def approved_panel_path(project_root: Path) -> Path:
    """Return the only panel path permitted as training input."""
    return (project_root / APPROVED_PANEL_RELATIVE_PATH).resolve()


def load_approved_panel(project_root: Path) -> pd.DataFrame:
    """Load the approved reference-derived panel, never a quarantined source."""
    path = approved_panel_path(project_root)
    if path.name in QUARANTINED_TARGET_DATASETS or not path.is_file():
        raise FileNotFoundError(f"Approved CWR reference panel not found: {path}")
    return pd.read_parquet(path)


def assess_target_readiness(
    target_metadata: dict[str, Any],
    panel: pd.DataFrame,
    assessment_text: str,
) -> tuple[bool, list[str]]:
    """Validate the documented ETc reference target without claiming field truth."""
    reasons: list[str] = []
    required_metadata = {
        "name": TARGET_COLUMN,
        "unit": "mm/day",
        "definition": "ETc = ET0 x Kc",
        "provenance_class": "reference_derived",
    }
    for key, expected in required_metadata.items():
        if target_metadata.get(key) != expected:
            reasons.append(
                f"target metadata {key!r} must be {expected!r}; "
                f"found {target_metadata.get(key)!r}"
            )
    if target_metadata.get("is_field_observed") is not False:
        reasons.append("target must explicitly be marked as not field-observed")
    statement = str(target_metadata.get("statement", "")).lower()
    if "not an observed field measurement" not in statement:
        reasons.append("target metadata must disclose that it is not field-observed")

    assessment = assessment_text.lower()
    if "reference-derived" not in assessment or "not measured field cwr" not in assessment:
        reasons.append(
            "the project target assessment must approve a reference-derived "
            "target and distinguish it from measured field CWR"
        )

    required_columns = {TARGET_COLUMN, "et0_mm_day", "kc"}
    missing_columns = sorted(required_columns - set(panel.columns))
    if missing_columns:
        reasons.append(f"panel is missing target provenance columns: {missing_columns}")
    else:
        target = pd.to_numeric(panel[TARGET_COLUMN], errors="coerce").to_numpy(dtype=float)
        et0 = pd.to_numeric(panel["et0_mm_day"], errors="coerce").to_numpy(dtype=float)
        kc = pd.to_numeric(panel["kc"], errors="coerce").to_numpy(dtype=float)
        if not len(target) or not (
            np.isfinite(target).all()
            and np.isfinite(et0).all()
            and np.isfinite(kc).all()
        ):
            reasons.append("target, ET0, and Kc must be finite for every panel row")
        elif (target < 0).any() or (et0 < 0).any() or (kc < 0).any():
            reasons.append("target, ET0, and Kc must be non-negative")
        elif not np.allclose(target, et0 * kc, rtol=1e-6, atol=1e-8):
            reasons.append("panel target does not reproduce the documented ETc = ET0 × Kc")

    return not reasons, reasons


def select_features(panel: pd.DataFrame) -> list[str]:
    """Select only the existing, approved reduced-input task predictors."""
    missing = sorted(set(RESEARCH_FEATURES) - set(panel.columns))
    if missing:
        raise ValueError(f"Approved reduced-input features are missing: {missing}")
    target_builder.assert_no_leakage(RESEARCH_FEATURES, "reduced_input")
    if TARGET_COLUMN in RESEARCH_FEATURES:
        raise ValueError("The target column must not be included in model features.")
    return list(RESEARCH_FEATURES)


def build_one_day_ahead_panel(
    panel: pd.DataFrame, features: Sequence[str]
) -> pd.DataFrame:
    """Align each target day with that crop cohort's prior-day information."""
    required = {"crop", "sowing_date", "date", TARGET_COLUMN, *features}
    missing = sorted(required - set(panel.columns))
    if missing:
        raise ValueError(f"Panel is missing one-day-ahead columns: {missing}")

    aligned = panel.sort_values(["crop", "sowing_date", "date"]).copy()
    cohorts = aligned.groupby(["crop", "sowing_date"], sort=False)
    aligned["feature_date"] = cohorts["date"].shift(1)
    aligned[list(features)] = cohorts[list(features)].shift(1)
    aligned = aligned.dropna(
        subset=["feature_date", TARGET_COLUMN, *features]
    ).reset_index(drop=True)

    target_dates = pd.to_datetime(aligned["date"])
    feature_dates = pd.to_datetime(aligned["feature_date"])
    if not (feature_dates < target_dates).all():
        raise ValueError("Every feature row must precede its target date.")
    if not ((target_dates - feature_dates).dt.days == 1).all():
        raise ValueError("Each feature row must be exactly one calendar day before its target.")
    return aligned


def make_pipeline(features: Sequence[str]) -> Pipeline:
    """Build preprocessing and the repository-approved classical RF baseline."""
    features = list(features)
    if not features or len(features) != len(set(features)):
        raise ValueError("Features must be non-empty and unique.")
    target_builder.assert_no_leakage(features, "reduced_input")
    if TARGET_COLUMN in features:
        raise ValueError("The target column must not be included in model features.")

    categorical = [name for name in features if name in target_builder.CATEGORICAL_FEATURES]
    numerical = [name for name in features if name not in categorical]
    preprocessor = models.build_preprocessor(
        numerical, categorical, scale=False
    )
    estimator = models.model_zoo(include_xgboost=False)["random_forest"].factory()
    if not isinstance(estimator, RandomForestRegressor):
        raise TypeError("The repository's random_forest baseline is not a regressor.")
    return Pipeline(
        [("preprocess", preprocessor), ("model", estimator)]
    )


def regression_metrics(actual: Sequence[float], predicted: Sequence[float]) -> dict[str, float]:
    """Return comparable regression metrics and explicitly signed residual summaries."""
    actual_values = np.asarray(actual, dtype=float)
    predicted_values = np.asarray(predicted, dtype=float)
    if actual_values.shape != predicted_values.shape or not actual_values.size:
        raise ValueError("Actual and predicted values must have equal, non-empty shapes.")
    residuals = actual_values - predicted_values
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    return {
        "mae_mm_day": float(mean_absolute_error(actual_values, predicted_values)),
        "rmse_mm_day": float(np.sqrt(mean_squared_error(actual_values, predicted_values))),
        "r2": float(r2_score(actual_values, predicted_values)),
        "mean_residual_mm_day": float(np.mean(residuals)),
        "median_absolute_error_mm_day": float(np.median(np.abs(residuals))),
        "bias_predicted_minus_actual_mm_day": float(-np.mean(residuals)),
    }


def research_metadata(
    *,
    target_metadata: dict[str, Any],
    features: Sequence[str],
    split: dict[str, Any],
    n_rows: int,
) -> dict[str, Any]:
    """Create metadata that explicitly cannot represent a production model."""
    return {
        "model_name": MODEL_NAME,
        "model_role": MODEL_ROLE,
        "production": False,
        "active_model": False,
        "production_ready": False,
        "active": False,
        "algorithm": "sklearn.ensemble.RandomForestRegressor",
        "research_positioning": "Random Forest is used as a conventional tree-based baseline.",
        "target": target_metadata,
        "feature_order": list(features),
        "horizon_days": 1,
        "feature_timing": (
            "All selected predictors are lagged one observation day within "
            "each crop/sowing-date cohort; the target is the following day's "
            "reference-derived ETc."
        ),
        "split": split,
        "n_rows": int(n_rows),
        "random_state": RANDOM_SEED,
        "hyperparameters": {
            "n_estimators": 300,
            "max_depth": None,
            "min_samples_leaf": 2,
            "n_jobs": -1,
            "random_state": RANDOM_SEED,
            "max_features": 1.0,
            "configuration_source": (
                "Preserves the approved ml.models.model_zoo random_forest "
                "baseline; sklearn's default max_features=1.0 is retained."
            ),
        },
        "evaluation_target_note": (
            "Scores measure agreement with reference-derived FAO-56 ETc, "
            "not field-observed crop water use."
        ),
    }


def save_research_outputs(
    *,
    project_root: Path,
    pipeline: Pipeline,
    metrics: dict[str, Any],
    feature_importance: pd.DataFrame,
    predictions_test: pd.DataFrame,
    residuals: pd.DataFrame,
    metadata: dict[str, Any],
) -> Path:
    """Write the six research-only outputs without using the production registry."""
    if (
        metadata.get("model_role") != MODEL_ROLE
        or metadata.get("production") is not False
        or metadata.get("active_model") is not False
        or metadata.get("production_ready") is not False
        or metadata.get("active") is not False
    ):
        raise ValueError("Refusing to save metadata that does not mark this as research-only.")

    output_dir = (project_root / RESEARCH_OUTPUT_RELATIVE_PATH).resolve()
    production_dir = (project_root / PRODUCTION_MODEL_RELATIVE_PATH).resolve()
    if output_dir == production_dir or production_dir in output_dir.parents:
        raise ValueError("Research artifacts must remain outside artifacts/models.")
    output_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(pipeline, output_dir / "rf_model.joblib", compress=3)
    (output_dir / "rf_metrics.json").write_text(
        json.dumps(metrics, indent=2, allow_nan=False), encoding="utf-8"
    )
    feature_importance.to_csv(
        output_dir / "rf_feature_importance.csv", index=False, encoding="utf-8"
    )
    predictions_test.to_csv(
        output_dir / "rf_predictions_test.csv", index=False, encoding="utf-8"
    )
    residuals.to_csv(
        output_dir / "rf_residuals.csv", index=False, encoding="utf-8"
    )
    (output_dir / "rf_metadata.json").write_text(
        json.dumps(metadata, indent=2, allow_nan=False), encoding="utf-8"
    )
    return output_dir
