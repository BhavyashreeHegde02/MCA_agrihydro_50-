"""Model definitions, preprocessing and conformal prediction intervals.

Everything a model needs is wrapped in a single scikit-learn ``Pipeline``, so
imputation, scaling and encoding are fitted on the training partition only and
travel with the model to inference. This is what makes the guarantee in the
project brief -- that inference uses exactly the preprocessing used in training
-- structural rather than aspirational: there is only one object, and the API
loads that same object.

Uncertainty uses **split conformal prediction**. A model is fitted on the
training partition, its absolute residuals are measured on a held-out
calibration partition, and the interval half-width is the appropriate quantile
of those residuals. Two things make this worth the small extra effort over a
fabricated confidence number: the coverage guarantee is distribution-free, and
it is *checkable* -- :func:`ml.metrics.interval_report` measures whether the
nominal coverage was actually achieved on data the calibration never saw.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Callable, Sequence

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.config import RANDOM_SEED
from ml.logging_utils import get_logger

log = get_logger("models")

try:  # optional, and the study must still run without it
    from xgboost import XGBRegressor

    XGBOOST_AVAILABLE = True
except ImportError:  # pragma: no cover - environment dependent
    XGBOOST_AVAILABLE = False
    log.info("xgboost is not installed; it will be skipped")


# --------------------------------------------------------------------------
# Preprocessing
# --------------------------------------------------------------------------
def build_preprocessor(
    numerical: Sequence[str], categorical: Sequence[str], *, scale: bool = True
) -> ColumnTransformer:
    """Impute and encode, fitted on training data only.

    Scaling is skipped for tree models, where it changes nothing and only costs
    time, but the imputer is always present so that a missing value at inference
    produces a prediction rather than an exception.
    """
    numeric_steps: list[tuple[str, Any]] = [("impute", SimpleImputer(strategy="median"))]
    if scale:
        numeric_steps.append(("scale", StandardScaler()))

    return ColumnTransformer(
        transformers=[
            ("num", Pipeline(numeric_steps), list(numerical)),
            (
                "cat",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        # An unseen crop at inference must not crash the API.
                        ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                list(categorical),
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


# --------------------------------------------------------------------------
# The model zoo
# --------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class ModelSpec:
    """One candidate model and the reason it is in the comparison."""

    name: str
    factory: Callable[[], Any]
    needs_scaling: bool
    family: str
    rationale: str


def model_zoo(*, include_xgboost: bool = True) -> dict[str, ModelSpec]:
    """Candidate models, from trivial to flexible.

    The two baselines are not filler. A model that cannot beat the seasonal mean
    has learned nothing, and without that reference an R-squared of 0.8 is
    impossible to interpret.
    """
    specs: list[ModelSpec] = [
        ModelSpec(
            "dummy_mean", lambda: DummyRegressor(strategy="mean"), False, "baseline",
            "Predicts the training mean. The floor any real model must clear.",
        ),
        ModelSpec(
            "ridge", lambda: Ridge(alpha=1.0, random_state=RANDOM_SEED), True, "linear",
            "Interpretable linear reference. Its shortfall against the tree "
            "models measures how much of the signal is genuinely non-linear.",
        ),
        ModelSpec(
            "random_forest",
            lambda: RandomForestRegressor(
                n_estimators=300, max_depth=None, min_samples_leaf=2,
                n_jobs=-1, random_state=RANDOM_SEED,
            ),
            False, "tree ensemble",
            "Captures interactions between crop stage and weather without being "
            "told they exist.",
        ),
        ModelSpec(
            "gradient_boosting",
            lambda: GradientBoostingRegressor(
                n_estimators=300, learning_rate=0.08, max_depth=4,
                subsample=0.9, random_state=RANDOM_SEED,
            ),
            False, "boosted trees",
            "Sequential boosting, usually the strongest of the classical methods "
            "on tabular data of this size.",
        ),
    ]
    if include_xgboost and XGBOOST_AVAILABLE:
        specs.append(
            ModelSpec(
                "xgboost",
                lambda: XGBRegressor(
                    n_estimators=400, learning_rate=0.08, max_depth=6,
                    subsample=0.9, colsample_bytree=0.9, n_jobs=-1,
                    random_state=RANDOM_SEED, tree_method="hist",
                ),
                False, "boosted trees",
                "Included only where its extra complexity earns a measurable "
                "improvement over gradient boosting.",
            )
        )
    return {spec.name: spec for spec in specs}


def build_pipeline(spec: ModelSpec, numerical: Sequence[str], categorical: Sequence[str]) -> Pipeline:
    """A single fitted object carrying preprocessing and estimator together."""
    return Pipeline(
        [
            ("preprocess", build_preprocessor(numerical, categorical, scale=spec.needs_scaling)),
            ("model", spec.factory()),
        ]
    )


# --------------------------------------------------------------------------
# Conformal prediction intervals
# --------------------------------------------------------------------------
@dataclasses.dataclass
class ConformalInterval:
    """A calibrated interval half-width, and the evidence for it."""

    half_width: float
    nominal_coverage: float
    n_calibration: int
    residual_quantile: float
    method: str = "split conformal, absolute residual"

    def apply(self, predictions: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Turn point predictions into intervals, floored at zero.

        Crop demand cannot be negative, so the lower bound is clipped. That
        makes the interval slightly conservative near zero, which is the correct
        direction to err for an irrigation recommendation.
        """
        predictions = np.asarray(predictions, dtype=float)
        lower = np.maximum(predictions - self.half_width, 0.0)
        upper = predictions + self.half_width
        return lower, upper

    def as_metadata(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "nominal_coverage": self.nominal_coverage,
            "half_width_mm_day": round(self.half_width, 4),
            "n_calibration": self.n_calibration,
            "residual_quantile": round(self.residual_quantile, 4),
        }


def calibrate_conformal(
    model: Pipeline,
    x_calibration: pd.DataFrame,
    y_calibration: np.ndarray,
    *,
    coverage: float = 0.90,
) -> ConformalInterval:
    """Derive an interval half-width from held-out residuals.

    The finite-sample correction ``ceil((n+1) * coverage) / n`` is what gives
    split conformal its distribution-free guarantee; using the plain empirical
    quantile would under-cover slightly on small calibration sets.
    """
    if not 0 < coverage < 1:
        raise ValueError("coverage must lie strictly between 0 and 1")

    predictions = model.predict(x_calibration)
    residuals = np.abs(np.asarray(y_calibration, dtype=float) - predictions)
    n = len(residuals)
    level = min(np.ceil((n + 1) * coverage) / n, 1.0)
    half_width = float(np.quantile(residuals, level))

    log.info("conformal calibration on %d records: nominal %.0f%% -> half-width %.4f mm/day",
             n, 100 * coverage, half_width)
    return ConformalInterval(
        half_width=half_width, nominal_coverage=coverage,
        n_calibration=n, residual_quantile=float(level),
    )


# --------------------------------------------------------------------------
# Feature names after preprocessing
# --------------------------------------------------------------------------
def transformed_feature_names(pipeline: Pipeline) -> list[str]:
    """Column names after the ColumnTransformer, for importance reporting."""
    preprocessor = pipeline.named_steps["preprocess"]
    try:
        return list(preprocessor.get_feature_names_out())
    except Exception:  # pragma: no cover - older sklearn fallbacks
        return [f"feature_{i}" for i in range(preprocessor.transform_shape_[1])]
