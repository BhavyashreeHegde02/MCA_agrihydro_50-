"""Training, evaluation and explainability for the three research tasks.

The order of operations matters and is fixed here so it cannot drift:

1. split chronologically -- train, calibration, test;
2. fit the pipeline on the training partition only;
3. calibrate conformal intervals on the calibration partition;
4. evaluate once on the test partition, which nothing has touched.

The calibration partition doubles as the validation set. Using the *test*
residuals to size an interval and then reporting coverage on that same test set
would be circular, so calibration and test are kept strictly apart.
"""

from __future__ import annotations

import dataclasses
import platform
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Sequence

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance

from ml import metrics as M
from ml import models as model_lib
from ml import registry
from ml import target_builder as tb
from ml.config import RANDOM_SEED
from ml.logging_utils import get_logger

log = get_logger("training")


@dataclasses.dataclass
class TrainedModel:
    """One fitted model, its scores and its calibrated interval."""

    name: str
    spec: model_lib.ModelSpec
    pipeline: Any
    conformal: model_lib.ConformalInterval
    metrics: dict[str, dict[str, Any]]
    interval_metrics: dict[str, float]
    predictions_test: np.ndarray
    importance: pd.DataFrame | None = None

    @property
    def test_mae(self) -> float:
        return float(self.metrics["test"]["mae_mm_day"])


@dataclasses.dataclass
class TaskResult:
    """Everything produced for one task."""

    task: tb.TaskSpec
    models: dict[str, TrainedModel]
    split_summary: dict[str, Any]
    best_model_name: str
    comparison: pd.DataFrame
    error_breakdowns: dict[str, pd.DataFrame]

    @property
    def best(self) -> TrainedModel:
        return self.models[self.best_model_name]


# --------------------------------------------------------------------------
def train_task(
    panel: pd.DataFrame,
    task: tb.TaskSpec,
    *,
    coverage: float = 0.90,
    include_xgboost: bool = True,
    compute_importance: bool = True,
    importance_repeats: int = 5,
    importance_sample: int = 20_000,
) -> TaskResult:
    """Train every candidate model on one task and evaluate them identically."""
    features, labels, dates = tb.build_task_frame(panel, task)
    split = tb.chronological_split(dates)

    train_mask, calibration_mask, test_mask = split["train"], split["validation"], split["test"]
    x_train, y_train = features[train_mask], labels[train_mask].to_numpy()
    x_calibration, y_calibration = features[calibration_mask], labels[calibration_mask].to_numpy()
    x_test, y_test = features[test_mask], labels[test_mask].to_numpy()

    split_summary = {
        "strategy": "chronological, split on the observation date",
        "rationale": (
            "Weather is autocorrelated and crop cohorts overlap in time, so a "
            "random split would place adjacent days either side of the boundary "
            "and inflate every metric."
        ),
        "train_rows": int(train_mask.sum()),
        "calibration_rows": int(calibration_mask.sum()),
        "test_rows": int(test_mask.sum()),
        "train_end": str(pd.Timestamp(split["train_cutoff"]).date()),
        "calibration_end": str(pd.Timestamp(split["validation_cutoff"]).date()),
        "test_end": str(pd.to_datetime(dates).max().date()),
    }

    zoo = model_lib.model_zoo(include_xgboost=include_xgboost)
    trained: dict[str, TrainedModel] = {}

    for name, spec in zoo.items():
        log.info("[%s] fitting %s (%s)", task.name, name, spec.family)
        pipeline = model_lib.build_pipeline(spec, task.numerical, task.categorical)
        pipeline.fit(x_train, y_train)

        conformal = model_lib.calibrate_conformal(
            pipeline, x_calibration, y_calibration, coverage=coverage
        )

        predictions_test = pipeline.predict(x_test)
        lower, upper = conformal.apply(predictions_test)

        scores = {
            "train": M.regression_report(y_train, pipeline.predict(x_train)),
            "calibration": M.regression_report(y_calibration, pipeline.predict(x_calibration)),
            "test": M.regression_report(y_test, predictions_test),
        }
        interval_scores = M.interval_report(y_test, lower, upper, coverage)

        trained[name] = TrainedModel(
            name=name, spec=spec, pipeline=pipeline, conformal=conformal,
            metrics=scores, interval_metrics=interval_scores,
            predictions_test=predictions_test,
        )
        log.info("[%s] %-18s test MAE %.4f  RMSE %.4f  R2 %.4f  coverage %.3f",
                 task.name, name, scores["test"]["mae_mm_day"],
                 scores["test"]["rmse_mm_day"], scores["test"]["r2"],
                 interval_scores["empirical_coverage"])

    comparison = M.comparison_table(
        {
            name: {
                **model.metrics["test"],
                "family": model.spec.family,
                "empirical_coverage": model.interval_metrics["empirical_coverage"],
                "interval_width_mm_day": model.interval_metrics["mean_interval_width_mm_day"],
            }
            for name, model in trained.items()
        }
    )

    best_name = select_best_model(trained)
    log.info("[%s] selected %s", task.name, best_name)

    if compute_importance:
        trained[best_name].importance = permutation_feature_importance(
            trained[best_name].pipeline, x_test, y_test,
            repeats=importance_repeats, sample=importance_sample,
        )

    breakdowns = build_error_breakdowns(panel, task, test_mask, y_test,
                                        trained[best_name].predictions_test)

    return TaskResult(
        task=task, models=trained, split_summary=split_summary,
        best_model_name=best_name, comparison=comparison, error_breakdowns=breakdowns,
    )


def select_best_model(trained: dict[str, TrainedModel], tolerance: float = 0.02) -> str:
    """Pick a model on error, but prefer a simpler one when the gap is trivial.

    The numerically best model is not automatically the right choice. If a
    linear model is within a couple of percent of a boosted ensemble, the
    simpler model is preferred: it is faster to serve, easier to explain to a
    farmer, and less likely to behave strangely on an input the training data
    never contained.
    """
    ranked = sorted(
        (m for m in trained.values() if m.spec.family != "baseline"),
        key=lambda m: m.test_mae,
    )
    if not ranked:
        return min(trained, key=lambda n: trained[n].test_mae)

    best = ranked[0]
    simplicity = {"linear": 0, "tree ensemble": 1, "boosted trees": 2, "baseline": 3}
    for candidate in ranked:
        within_tolerance = candidate.test_mae <= best.test_mae * (1 + tolerance)
        if within_tolerance and simplicity[candidate.spec.family] < simplicity[best.spec.family]:
            log.info("preferring %s over %s: MAE within %.0f%% and structurally simpler",
                     candidate.name, best.name, tolerance * 100)
            best = candidate
    return best.name


def permutation_feature_importance(
    pipeline: Any, x_test: pd.DataFrame, y_test: np.ndarray,
    *, repeats: int = 5, sample: int = 20_000,
) -> pd.DataFrame:
    """Importance measured by shuffling each input column on held-out data.

    Permutation importance is computed on the *original* columns rather than the
    one-hot expansion, so ``crop`` appears once instead of scattered across eight
    indicator columns. It is measured on held-out data because importance derived
    from training data reports what the model memorised, not what it uses.
    """
    x_test = x_test.reset_index(drop=True)
    y_test = np.asarray(y_test, dtype=float)

    if len(x_test) > sample:
        # Sample by position so features and labels stay aligned. Permutation
        # importance refits nothing but predicts once per feature per repeat, so
        # capping the size keeps the cost bounded on a large panel.
        rng = np.random.default_rng(RANDOM_SEED)
        positions = rng.choice(len(x_test), size=sample, replace=False)
        x_test = x_test.iloc[positions].reset_index(drop=True)
        y_test = y_test[positions]

    result = permutation_importance(
        pipeline, x_test, y_test, n_repeats=repeats,
        random_state=RANDOM_SEED, scoring="neg_mean_absolute_error", n_jobs=1,
    )
    return (
        pd.DataFrame(
            {
                "feature": list(x_test.columns),
                "importance_mae_increase": result.importances_mean,
                "std": result.importances_std,
            }
        )
        .sort_values("importance_mae_increase", ascending=False)
        .reset_index(drop=True)
    )


def build_error_breakdowns(
    panel: pd.DataFrame, task: tb.TaskSpec, test_mask: np.ndarray,
    y_test: np.ndarray, predictions: np.ndarray,
) -> dict[str, pd.DataFrame]:
    """Error by crop, growth stage and season, to expose hidden failures."""
    frame = panel.copy()
    if task.horizon_days > 0:
        frame = frame.sort_values(["crop", "sowing_date", "date"]).reset_index(drop=True)
        frame["_label"] = frame.groupby(["crop", "sowing_date"])[task.target].shift(
            -task.horizon_days)
        frame = frame.dropna(subset=["_label"]).reset_index(drop=True)

    test_rows = frame[test_mask].reset_index(drop=True)
    out: dict[str, pd.DataFrame] = {}
    for column, label in (("crop", "crop"), ("growth_stage", "growth_stage")):
        if column in test_rows.columns:
            out[label] = M.error_by_group(y_test, predictions, test_rows[column], column)

    if "month" in test_rows.columns:
        out["month"] = M.error_by_group(y_test, predictions, test_rows["month"], "month")
    return out


# --------------------------------------------------------------------------
def persist_task(
    result: TaskResult,
    panel: pd.DataFrame,
    *,
    baseline_assumptions: dict[str, Any],
    make_active: bool = False,
) -> registry.ModelVersion:
    """Save the selected model with everything needed to serve and audit it."""
    best = result.best
    training_environment: dict[str, str | None] = {
        "python": platform.python_version(),
    }
    for distribution, key in (
        ("scikit-learn", "scikit_learn"),
        ("xgboost", "xgboost"),
        ("joblib", "joblib"),
    ):
        try:
            training_environment[key] = version(distribution)
        except PackageNotFoundError:
            training_environment[key] = None

    metadata = {
        "algorithm": type(best.pipeline.named_steps["model"]).__name__,
        "training_environment": training_environment,
        "model_family": best.spec.family,
        "selection_rationale": best.spec.rationale,
        "task": result.task.as_metadata(),
        "target_definition": tb.target_definition_metadata(panel),
        "feature_order": list(result.task.features),
        "numerical_features": result.task.numerical,
        "categorical_features": result.task.categorical,
        "split": result.split_summary,
        "metrics": best.metrics,
        "interval": {**best.conformal.as_metadata(), **best.interval_metrics},
        "model_comparison": result.comparison.reset_index().rename(
            columns={"index": "model"}).to_dict(orient="records"),
        "dataset_fingerprint": registry.dataset_fingerprint(
            panel[[c for c in result.task.features if c in panel.columns]]),
        "baseline_assumptions": baseline_assumptions,
        "preprocessing": (
            "Imputation, scaling and one-hot encoding are inside the saved "
            "pipeline and were fitted on the training partition only, so "
            "inference uses exactly the preprocessing used in training."
        ),
    }
    return registry.save_model(
        name=result.task.name,
        pipeline=best.pipeline,
        metadata=metadata,
        feature_importance=best.importance,
        make_active=make_active,
    )
