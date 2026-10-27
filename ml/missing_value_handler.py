"""Filling gaps, with the method chosen to suit the variable.

The guiding rule is that an imputation should use the physics of the quantity
being imputed whenever the physics is available. For a daily weather series
that is usually possible, and it produces a defensible value instead of an
arbitrary one.

Only one primary-path value is actually missing in this project's data: a single
day of shortwave radiation, which the upstream provider flagged with its -999
sentinel. That day is filled from the day's temperature range using the FAO-56
radiation estimator, which is the method FAO-56 itself prescribes when measured
radiation is unavailable. Two alternatives are implemented alongside it so the
choice can be compared rather than asserted.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Literal

import numpy as np
import pandas as pd

from ml.et0 import extraterrestrial_radiation
from ml.logging_utils import get_logger

log = get_logger("missing_value_handler")

ImputationMethod = Literal["fao56_temperature_range", "linear_interpolation", "seasonal_normal"]


@dataclasses.dataclass
class ImputationRecord:
    """What was filled, where, how, and with what value."""

    column: str
    method: str
    n_filled: int
    indices: list[Any]
    filled_values: list[float]
    justification: str
    comparison: dict[str, float] = dataclasses.field(default_factory=dict)

    def as_row(self) -> dict[str, Any]:
        return {
            "column": self.column,
            "method": self.method,
            "n_filled": self.n_filled,
            "filled_values": [round(v, 4) for v in self.filled_values],
            "justification": self.justification,
        }


def estimate_solar_radiation_from_temperature_range(
    tmax_c: np.ndarray,
    tmin_c: np.ndarray,
    day_of_year: np.ndarray,
    latitude_deg: float,
    krs: float = 0.16,
) -> np.ndarray:
    """Shortwave radiation from the daily temperature range (FAO-56 eq. 50).

    ``Rs = krs * sqrt(Tmax - Tmin) * Ra``. The temperature range is a proxy for
    cloudiness: clear days heat up and cool down more. ``krs`` is 0.16 for
    interior locations and 0.19 near a coast; the interior value is used and is
    exposed in ``config/site.yaml`` so the choice is visible.
    """
    ra = extraterrestrial_radiation(latitude_deg, day_of_year)
    return krs * np.sqrt(np.maximum(tmax_c - tmin_c, 0.0)) * ra


def _seasonal_normal(series: pd.Series, day_of_year: pd.Series, window: int = 7) -> pd.Series:
    """Mean of the same calendar window across all other years."""
    filled = series.copy()
    for index in series.index[series.isna()]:
        target = int(day_of_year.loc[index])
        offsets = ((day_of_year - target + 182) % 365) - 182
        neighbours = series[(offsets.abs() <= window) & series.notna()]
        if not neighbours.empty:
            filled.loc[index] = float(neighbours.mean())
    return filled


def impute_solar_radiation(
    weather: pd.DataFrame,
    latitude_deg: float,
    *,
    column: str = "allsky_sfc_sw_dwn",
    date_column: str = "datetime",
    tmax_column: str = "t2m_max",
    tmin_column: str = "t2m_min",
    method: ImputationMethod = "fao56_temperature_range",
    krs: float = 0.16,
) -> tuple[pd.DataFrame, ImputationRecord | None]:
    """Fill missing radiation days and record exactly what was done.

    Every method is evaluated on the missing days so the record carries what the
    alternatives would have produced. That turns the choice of imputation into
    something a reader can check instead of a hidden decision.
    """
    frame = weather.copy()
    missing_mask = frame[column].isna()
    n_missing = int(missing_mask.sum())
    if n_missing == 0:
        log.info("%s: nothing to impute", column)
        return frame, None

    dates = pd.to_datetime(frame[date_column])
    doy = dates.dt.dayofyear

    physics = estimate_solar_radiation_from_temperature_range(
        frame[tmax_column].to_numpy(dtype=float),
        frame[tmin_column].to_numpy(dtype=float),
        doy.to_numpy(dtype=float),
        latitude_deg,
        krs=krs,
    )
    interpolated = frame[column].interpolate(method="linear", limit_direction="both")
    seasonal = _seasonal_normal(frame[column], doy)

    candidates = {
        "fao56_temperature_range": pd.Series(physics, index=frame.index),
        "linear_interpolation": interpolated,
        "seasonal_normal": seasonal,
    }
    chosen = candidates[method]

    frame.loc[missing_mask, column] = chosen[missing_mask].to_numpy()
    frame[f"{column}_was_imputed"] = missing_mask

    comparison = {
        name: float(values[missing_mask].mean()) for name, values in candidates.items()
    }

    record = ImputationRecord(
        column=column,
        method=method,
        n_filled=n_missing,
        indices=[str(d.date()) for d in dates[missing_mask]],
        filled_values=[float(v) for v in chosen[missing_mask]],
        justification=(
            "FAO-56 equation 50 estimates shortwave radiation from the daily "
            "temperature range when measured radiation is unavailable. It is "
            "preferred over interpolation here because it uses same-day "
            "observations rather than borrowing from adjacent days, and because "
            "it is the substitution FAO-56 itself prescribes."
        ),
        comparison=comparison,
    )
    log.info(
        "%s: imputed %d day(s) on %s -> %.2f MJ/m2/day (interpolation would give "
        "%.2f, seasonal normal %.2f)",
        column, n_missing, record.indices,
        comparison[method], comparison["linear_interpolation"], comparison["seasonal_normal"],
    )
    return frame, record


def missing_value_summary(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Per-column missingness across every loaded dataset."""
    rows = []
    for name, frame in frames.items():
        for column in frame.columns:
            n_missing = int(frame[column].isna().sum())
            if n_missing:
                rows.append(
                    {
                        "dataset": name,
                        "column": column,
                        "n_missing": n_missing,
                        "pct_missing": round(100 * n_missing / len(frame), 3),
                        "n_rows": len(frame),
                    }
                )
    if not rows:
        return pd.DataFrame(columns=["dataset", "column", "n_missing", "pct_missing", "n_rows"])
    return pd.DataFrame(rows).sort_values(["dataset", "pct_missing"], ascending=[True, False])
