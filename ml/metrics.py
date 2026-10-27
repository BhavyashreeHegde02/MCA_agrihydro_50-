"""Evaluation metrics, and the reasons for including or omitting each one."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ml.logging_utils import get_logger

log = get_logger("metrics")


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean absolute error, in the target's own unit (mm/day).

    The headline metric here, because an irrigation decision is made in
    millimetres and an average error of 0.4 mm/day is directly interpretable.
    """
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root mean squared error. Penalises large misses more heavily than MAE."""
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


def r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Share of variance explained, relative to predicting the mean."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")


def mape(y_true: np.ndarray, y_pred: np.ndarray, floor: float = 0.5) -> float:
    """Mean absolute percentage error, over records above ``floor`` only.

    Crop demand approaches zero during the initial stage of a low-Kc crop on a
    cool day. Percentage error explodes there and the mean becomes dominated by
    records nobody would irrigate for. Restricting to records above a
    decision-relevant floor keeps the number meaningful; the share of records
    used is reported alongside it by :func:`regression_report`.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = np.abs(y_true) >= floor
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)


def bias(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean signed error. Positive means the model over-predicts demand.

    Direction matters operationally in a way magnitude does not: systematic
    over-prediction wastes water, systematic under-prediction stresses the crop.
    """
    return float(np.mean(np.asarray(y_pred) - np.asarray(y_true)))


def nash_sutcliffe(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Nash-Sutcliffe efficiency, the hydrological convention.

    Algebraically identical to R-squared for a point forecast, reported because
    hydrology and irrigation literature quote NSE and a reader from that field
    will look for it.
    """
    return r2(y_true, y_pred)


def regression_report(y_true: np.ndarray, y_pred: np.ndarray, *, mape_floor: float = 0.5) -> dict[str, float]:
    """Every metric at once."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    usable = float(np.mean(np.abs(y_true) >= mape_floor))
    return {
        "mae_mm_day": round(mae(y_true, y_pred), 4),
        "rmse_mm_day": round(rmse(y_true, y_pred), 4),
        "r2": round(r2(y_true, y_pred), 4),
        "nse": round(nash_sutcliffe(y_true, y_pred), 4),
        "mape_pct": round(mape(y_true, y_pred, mape_floor), 3),
        "mape_coverage_pct": round(100.0 * usable, 1),
        "bias_mm_day": round(bias(y_true, y_pred), 4),
        "n": int(len(y_true)),
    }


# --------------------------------------------------------------------------
# Interval metrics
# --------------------------------------------------------------------------
def picp(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float:
    """Prediction interval coverage probability: the share actually inside."""
    y_true = np.asarray(y_true, dtype=float)
    return float(np.mean((y_true >= np.asarray(lower)) & (y_true <= np.asarray(upper))))


def mean_interval_width(lower: np.ndarray, upper: np.ndarray) -> float:
    """Average interval width, in the target's unit.

    Coverage alone is trivially gamed by making every interval enormous, so
    width is always reported beside it.
    """
    return float(np.mean(np.asarray(upper) - np.asarray(lower)))


def interval_report(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray,
                    nominal: float) -> dict[str, float]:
    coverage = picp(y_true, lower, upper)
    return {
        "nominal_coverage": round(float(nominal), 4),
        "empirical_coverage": round(coverage, 4),
        "coverage_gap": round(coverage - float(nominal), 4),
        "mean_interval_width_mm_day": round(mean_interval_width(lower, upper), 4),
        "median_interval_width_mm_day": round(
            float(np.median(np.asarray(upper) - np.asarray(lower))), 4),
        "n": int(len(np.asarray(y_true))),
    }


# --------------------------------------------------------------------------
# Error breakdowns
# --------------------------------------------------------------------------
def error_by_group(
    y_true: np.ndarray, y_pred: np.ndarray, groups: pd.Series, group_name: str
) -> pd.DataFrame:
    """Per-group error, to expose where an aggregate metric is hiding a failure."""
    frame = pd.DataFrame(
        {"y_true": np.asarray(y_true, dtype=float),
         "y_pred": np.asarray(y_pred, dtype=float),
         group_name: groups.to_numpy()}
    )
    frame["abs_error"] = (frame["y_true"] - frame["y_pred"]).abs()
    frame["error"] = frame["y_pred"] - frame["y_true"]

    out = frame.groupby(group_name).agg(
        n=("y_true", "size"),
        mean_actual=("y_true", "mean"),
        mean_predicted=("y_pred", "mean"),
        mae_mm_day=("abs_error", "mean"),
        bias_mm_day=("error", "mean"),
    )
    out["rmse_mm_day"] = frame.groupby(group_name).apply(
        lambda g: float(np.sqrt(np.mean((g["y_true"] - g["y_pred"]) ** 2))),
        include_groups=False,
    )
    return out.round(4).sort_values("mae_mm_day", ascending=False)


def comparison_table(results: dict[str, dict[str, Any]]) -> pd.DataFrame:
    """Model-by-model comparison, ordered by the headline metric."""
    frame = pd.DataFrame(results).T
    if "mae_mm_day" in frame.columns:
        frame = frame.sort_values("mae_mm_day")
    return frame
