"""What the model is asked to predict, and what it is allowed to see.

The study has no independently observed crop water requirement. Phase 1
established that the one candidate column fails four physical and statistical
tests, so it is not used. The supervised target is therefore stated explicitly:

    target = ETc, crop evapotranspiration in mm/day,
             computed as ET0 (FAO-56 Penman-Monteith) x Kc (growth-stage curve)

This is a **reference-derived** quantity. A model trained on it learns and
refines a physics reference; it does not predict field-observed water use, and
no result from it should ever be described as though it did.

Why that needs three separate tasks
-----------------------------------
ETc is a deterministic function of the weather inputs and the crop coefficient.
Hand a model all of those inputs and it will recover the formula to three or
four decimal places. The resulting R-squared is near one and means nothing about
predictive skill -- it measures function approximation, not prediction.

Pretending otherwise is the single easiest way to produce an impressive and
worthless result, so the tasks are separated and labelled:

``surrogate`` (Task A)
    Every input FAO-56 uses. Near-perfect recovery is *expected*. Run as a
    wiring check on the pipeline, reported as a formula-surrogate result, and
    never quoted as predictive accuracy.

``reduced_input`` (Task B)
    Radiation and wind withheld, because a smallholder has neither. What remains
    is temperature, humidity, recent rainfall, crop and crop age. The withheld
    variables carry real information, so the error is genuine and irreducible.
    This is the primary research question.

``forecast`` (Task C)
    Predict demand *h* days ahead using only information available today.
    Future weather is genuinely unknown, so this is a real forecasting problem.

Leakage control
---------------
:data:`LEAKAGE_SENSITIVE` lists every column that is algebraically downstream of
ET0. None of them may appear in any task except the surrogate diagnostic, where
their presence is the entire point. :func:`assert_no_leakage` enforces it, and a
test asserts that a deliberately leaky feature set is rejected.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Literal, Sequence

import numpy as np
import pandas as pd

from ml.logging_utils import get_logger

log = get_logger("target_builder")

TaskName = Literal["surrogate", "reduced_input", "forecast"]

TARGET_COLUMN = "etc_mm_day"

#: Columns computed from ET0, or from which ET0 can be reconstructed exactly.
#: Admitting any of these to a model predicting ETc leaks the target.
LEAKAGE_SENSITIVE: frozenset[str] = frozenset(
    {
        "et0_mm_day", "etc_mm_day", "kc",
        "rn_mj_m2_day", "rns_mj_m2_day", "rnl_mj_m2_day",
        "ra_mj_m2_day", "rso_mj_m2_day",
        "es_kpa", "ea_kpa", "vpd_kpa", "delta_kpa_c",
        "et0_radiation_term_mm_day", "et0_aerodynamic_term_mm_day",
        "net_irrigation_mm", "gross_irrigation_mm",
        "root_zone_depletion_mm", "depletion_fraction", "irrigation_triggered",
        "effective_rainfall_mm",
    }
)

#: The full FAO-56 input set. Enough to reconstruct ET0 almost exactly.
SURROGATE_FEATURES: tuple[str, ...] = (
    "t2m", "t2m_min", "t2m_max", "rh2m", "ws2m", "allsky_sfc_sw_dwn",
    "temp_range_c", "day_of_year", "doy_sin", "doy_cos",
    "days_after_sowing", "crop", "growth_stage",
)

#: What a farmer can plausibly supply: a thermometer, a humidity reading, a
#: rain gauge, the crop, and the sowing date. No pyranometer, no anemometer.
REDUCED_INPUT_FEATURES: tuple[str, ...] = (
    "t2m", "t2m_min", "t2m_max", "rh2m",
    "temp_range_c", "rainfall_mm", "rain_sum_7d_mm", "rain_sum_30d_mm",
    "days_since_rain", "day_of_year", "doy_sin", "doy_cos", "month",
    "days_after_sowing", "crop", "growth_stage",
)

#: The reduced set minus anything stage-aware, used for the ablation that tests
#: whether growth-stage awareness actually earns its place.
REDUCED_INPUT_NO_STAGE_FEATURES: tuple[str, ...] = tuple(
    f for f in REDUCED_INPUT_FEATURES if f not in {"growth_stage", "days_after_sowing"}
)

CATEGORICAL_FEATURES: frozenset[str] = frozenset({"crop", "growth_stage", "irrigation_method", "soil_type"})


@dataclasses.dataclass(frozen=True)
class TaskSpec:
    """One supervised task: its features, its target, and what it is for."""

    name: str
    features: tuple[str, ...]
    target: str
    horizon_days: int
    purpose: str
    reporting_note: str

    @property
    def categorical(self) -> list[str]:
        return [f for f in self.features if f in CATEGORICAL_FEATURES]

    @property
    def numerical(self) -> list[str]:
        return [f for f in self.features if f not in CATEGORICAL_FEATURES]

    def as_metadata(self) -> dict[str, Any]:
        return {
            "task": self.name,
            "target": self.target,
            "horizon_days": self.horizon_days,
            "n_features": len(self.features),
            "numerical_features": self.numerical,
            "categorical_features": self.categorical,
            "purpose": " ".join(self.purpose.split()),
            "reporting_note": " ".join(self.reporting_note.split()),
        }


TASKS: dict[str, TaskSpec] = {
    "surrogate": TaskSpec(
        name="surrogate",
        features=SURROGATE_FEATURES,
        target=TARGET_COLUMN,
        horizon_days=0,
        purpose=(
            "Give the model every input FAO-56 uses and confirm it can recover "
            "the reference. A wiring check on the feature pipeline, the target "
            "construction and the training loop."
        ),
        reporting_note=(
            "DIAGNOSTIC ONLY. Near-perfect scores are expected because the target "
            "is a deterministic function of these inputs. This is function "
            "approximation, not predictive skill, and must never be quoted as "
            "model accuracy."
        ),
    ),
    "reduced_input": TaskSpec(
        name="reduced_input",
        features=REDUCED_INPUT_FEATURES,
        target=TARGET_COLUMN,
        horizon_days=0,
        purpose=(
            "Estimate crop water demand without solar radiation or wind speed, "
            "which a smallholder cannot measure. The primary research question."
        ),
        reporting_note=(
            "Genuine estimation problem. The withheld variables carry real "
            "information, so the residual error is irreducible rather than a "
            "modelling failure."
        ),
    ),
    "reduced_input_no_stage": TaskSpec(
        name="reduced_input_no_stage",
        features=REDUCED_INPUT_NO_STAGE_FEATURES,
        target=TARGET_COLUMN,
        horizon_days=0,
        purpose=(
            "The reduced-input task with growth-stage information removed, to "
            "measure what stage awareness is actually worth."
        ),
        reporting_note="Ablation. Compare against reduced_input on identical splits.",
    ),
    "forecast_7d": TaskSpec(
        name="forecast_7d",
        features=REDUCED_INPUT_FEATURES,
        target=TARGET_COLUMN,
        horizon_days=7,
        purpose=(
            "Predict demand seven days ahead from information available today. "
            "Irrigation is planned in advance, so this is the operationally "
            "useful form of the question."
        ),
        reporting_note=(
            "Real forecasting: future weather is unknown. Compare against a "
            "seasonal-climatology baseline, not against zero."
        ),
    ),
}


# --------------------------------------------------------------------------
def assert_no_leakage(features: Sequence[str], task: str) -> None:
    """Refuse a feature set that contains a target-derived column.

    The surrogate task is exempt by design: its whole purpose is to hand the
    model the formula's inputs and confirm recovery.
    """
    if task == "surrogate":
        return
    offenders = sorted(set(features) & LEAKAGE_SENSITIVE)
    if offenders:
        raise ValueError(
            f"task {task!r} includes target-derived feature(s) {offenders}. "
            "These are algebraically downstream of ET0 and would leak the target. "
            "Remove them, or use the 'surrogate' task if formula recovery is the "
            "intention."
        )


def build_target(panel: pd.DataFrame) -> pd.Series:
    """The supervised target: reference-derived crop evapotranspiration, mm/day."""
    if TARGET_COLUMN not in panel.columns:
        raise KeyError(f"panel has no {TARGET_COLUMN!r} column; run the baseline first")
    target = panel[TARGET_COLUMN].astype(float)
    if target.isna().any():
        raise ValueError(f"{TARGET_COLUMN} contains missing values")
    if (target < 0).any():
        raise ValueError(f"{TARGET_COLUMN} contains negative values, which is unphysical")
    return target


def build_task_frame(panel: pd.DataFrame, task: TaskSpec) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Assemble ``(X, y, dates)`` for one task.

    For a forecasting task the target is shifted forward within each crop cohort,
    so a row's features describe today and its label describes the day *h* ahead.
    Shifting within the cohort matters: a global shift would let the last day of
    one cohort borrow the first day of the next.
    """
    assert_no_leakage(task.features, task.name)

    missing = [f for f in task.features if f not in panel.columns]
    if missing:
        raise KeyError(f"task {task.name!r} needs column(s) absent from the panel: {missing}")

    frame = panel.copy()

    if task.horizon_days > 0:
        frame = frame.sort_values(["crop", "sowing_date", "date"]).reset_index(drop=True)
        frame["_label"] = frame.groupby(["crop", "sowing_date"])[task.target].shift(
            -task.horizon_days
        )
        frame = frame.dropna(subset=["_label"]).reset_index(drop=True)
        label = frame["_label"].astype(float)
    else:
        label = build_target(frame)

    features = frame[list(task.features)].copy()
    dates = pd.to_datetime(frame["date"])

    log.info("task %-24s %7d rows x %2d features (horizon %d d)",
             task.name, len(features), features.shape[1], task.horizon_days)
    return features, label, dates


# --------------------------------------------------------------------------
def chronological_split(
    dates: pd.Series,
    *,
    train_fraction: float = 0.6,
    validation_fraction: float = 0.2,
) -> dict[str, np.ndarray]:
    """Split by calendar time, not at random.

    Weather is autocorrelated and crop cohorts overlap in time. A random split
    would put a day from the middle of a cohort in training and its neighbour in
    test, which inflates every metric. Splitting on the calendar means the test
    period is genuinely unseen.

    The split is on the *observation* date, so a cohort that straddles a boundary
    contributes its early days to the earlier partition and its later days to the
    later one. No cohort is ever fully duplicated across partitions.
    """
    if not 0 < train_fraction < 1 or not 0 < validation_fraction < 1:
        raise ValueError("fractions must lie strictly between 0 and 1")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("train and validation fractions must leave room for a test set")

    dates = pd.to_datetime(dates)
    train_cutoff = dates.quantile(train_fraction)
    validation_cutoff = dates.quantile(train_fraction + validation_fraction)

    train = (dates <= train_cutoff).to_numpy()
    validation = ((dates > train_cutoff) & (dates <= validation_cutoff)).to_numpy()
    test = (dates > validation_cutoff).to_numpy()

    log.info(
        "chronological split: train %d (to %s) | val %d (to %s) | test %d (to %s)",
        train.sum(), train_cutoff.date(),
        validation.sum(), validation_cutoff.date(),
        test.sum(), dates.max().date(),
    )
    return {
        "train": train, "validation": validation, "test": test,
        "train_cutoff": train_cutoff, "validation_cutoff": validation_cutoff,
    }


def target_definition_metadata(panel: pd.DataFrame) -> dict[str, Any]:
    """The formal statement of what the target is, stored with every model."""
    target = panel[TARGET_COLUMN]
    return {
        "name": TARGET_COLUMN,
        "unit": "mm/day",
        "definition": "ETc = ET0 x Kc",
        "et0_method": "FAO-56 Penman-Monteith (Allen et al. 1998, eq. 6)",
        "kc_source": "growth-stage curve built from the project's agronomic "
                     "reference files; see config/crop_stages.yaml",
        "provenance_class": "reference_derived",
        "is_field_observed": False,
        "statement": (
            "This target is derived from a physics reference applied to a real "
            "weather series. It is NOT an observed field measurement of water "
            "use. Any model trained on it learns and refines a reference-derived "
            "quantity, and results must be reported in those terms."
        ),
        "why_not_the_supplied_column": (
            "crop_water_data.csv -> water_requirement_liters was tested and "
            "rejected: the stated volumes imply irrigation depths about a hundred "
            "times smaller than the lightest real application, its "
            "evapotranspiration column is uncorrelated with all of its physical "
            "drivers simultaneously, all nine numeric columns are "
            "indistinguishable from uniform draws, and a log-linear model "
            "recovers 90 percent of its variance as a clipped multiplicative "
            "formula. See docs/dataset_analysis.md section 5."
        ),
        "n_records": int(len(target)),
        "mean": round(float(target.mean()), 4),
        "std": round(float(target.std()), 4),
        "min": round(float(target.min()), 4),
        "max": round(float(target.max()), 4),
    }
