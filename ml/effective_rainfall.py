"""How much of the rain that fell actually reaches the crop.

Rainfall and *effective* rainfall are different quantities. Part of every event
is caught by the canopy and evaporates, part runs off, and part drains past the
roots. Only the remainder offsets irrigation.

There is no single correct method, so the method is a declared, swappable
choice rather than a constant buried in a formula. Three are implemented and
the active one is named in ``config/baseline.yaml``.

A unit error worth naming
-------------------------
The USDA Soil Conservation Service formula is quoted constantly in crop-water
work, and it is defined on **monthly** rainfall totals. Applied to a daily
value it returns an effective fraction near 0.98 for a 10 mm day, which would
credit almost the whole of a light shower to the crop. In reality most of a
2 mm day never reaches the root zone at all.

:func:`usda_scs_monthly` therefore refuses to run on a daily series unless
explicitly forced, and the default daily method is one that behaves correctly at
a daily time step.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Literal

import numpy as np
import pandas as pd

from ml.logging_utils import get_logger

log = get_logger("effective_rainfall")

Method = Literal["daily_threshold_fraction", "fixed_fraction", "usda_scs_monthly"]


@dataclasses.dataclass(frozen=True)
class EffectiveRainfallMethod:
    """The active method and the parameters it was run with."""

    name: str
    parameters: dict[str, Any]
    description: str

    def as_metadata(self) -> dict[str, Any]:
        return {
            "method": self.name,
            "parameters": dict(self.parameters),
            "description": " ".join(self.description.split()),
        }


# --------------------------------------------------------------------------
# Daily methods
# --------------------------------------------------------------------------
def daily_threshold_fraction(
    rainfall_mm: np.ndarray | pd.Series,
    *,
    interception_threshold_mm: float = 2.0,
    infiltration_fraction: float = 0.75,
    max_daily_storage_mm: float | np.ndarray = 40.0,
) -> np.ndarray:
    """Effective rainfall at a daily time step.

    Three things happen to a day's rain, in order:

    1. the first few millimetres wet the canopy and the soil surface and
       evaporate, contributing nothing;
    2. a fixed fraction of what remains infiltrates, the rest running off or
       draining below the root zone;
    3. what infiltrates cannot exceed what the root zone can still hold.

    A 1 mm shower therefore contributes nothing, and a 200 mm storm contributes
    only what the profile can store.
    """
    rain = np.asarray(rainfall_mm, dtype=float)
    above_threshold = np.maximum(rain - float(interception_threshold_mm), 0.0)
    infiltrated = float(infiltration_fraction) * above_threshold
    return np.minimum(infiltrated, np.asarray(max_daily_storage_mm, dtype=float))


def fixed_fraction(
    rainfall_mm: np.ndarray | pd.Series, *, fraction: float = 0.80
) -> np.ndarray:
    """A constant share of every event is effective.

    The simplest assumption available. Retained as a comparison baseline, and
    useful precisely because its crudeness is obvious: it credits a 0.5 mm day
    with 0.4 mm of usable water, which cannot be right.
    """
    return float(fraction) * np.asarray(rainfall_mm, dtype=float)


def usda_scs_monthly(
    monthly_rainfall_mm: np.ndarray | pd.Series, *, force_daily: bool = False
) -> np.ndarray:
    """USDA SCS effective rainfall from a **monthly** total.

    ``Pe = P (125 - 0.2 P) / 125`` for ``P < 250`` mm, else ``Pe = 125 + 0.1 P``.

    Raises if the input looks like a daily series, because applying a monthly
    formula to daily values is a unit error rather than an approximation.
    Pass ``force_daily=True`` only to demonstrate that error deliberately.
    """
    rain = np.asarray(monthly_rainfall_mm, dtype=float)
    if not force_daily and rain.size > 0 and float(np.nanmedian(rain)) < 10.0:
        raise ValueError(
            "usda_scs_monthly() received values with a median below 10 mm, which "
            "looks like a daily series. This formula is defined on monthly totals; "
            "applying it daily overstates effective rainfall badly. Aggregate to "
            "monthly first, or use daily_threshold_fraction()."
        )
    return np.where(rain < 250.0, rain * (125.0 - 0.2 * rain) / 125.0, 125.0 + 0.1 * rain)


# --------------------------------------------------------------------------
# Dispatch
# --------------------------------------------------------------------------
def compute(
    rainfall_mm: np.ndarray | pd.Series,
    config: dict[str, Any],
    *,
    max_daily_storage_mm: float | np.ndarray | None = None,
) -> tuple[np.ndarray, EffectiveRainfallMethod]:
    """Apply the method named in ``config`` and return it alongside the result."""
    name = str(config.get("method", "daily_threshold_fraction"))

    if name == "daily_threshold_fraction":
        settings = dict(config.get("daily_threshold_fraction") or {})
        storage = (
            settings.get("default_max_daily_storage_mm", 40.0)
            if max_daily_storage_mm is None
            else max_daily_storage_mm
        )
        values = daily_threshold_fraction(
            rainfall_mm,
            interception_threshold_mm=float(settings.get("interception_threshold_mm", 2.0)),
            infiltration_fraction=float(settings.get("infiltration_fraction", 0.75)),
            max_daily_storage_mm=storage,
        )
        used = EffectiveRainfallMethod(
            name=name,
            parameters={
                "interception_threshold_mm": float(settings.get("interception_threshold_mm", 2.0)),
                "infiltration_fraction": float(settings.get("infiltration_fraction", 0.75)),
                "max_daily_storage_mm": (
                    "per-crop root zone" if max_daily_storage_mm is not None
                    else float(settings.get("default_max_daily_storage_mm", 40.0))
                ),
            },
            description=str(settings.get("basis", "")),
        )

    elif name == "fixed_fraction":
        settings = dict(config.get("fixed_fraction") or {})
        fraction = float(settings.get("fraction", 0.80))
        values = fixed_fraction(rainfall_mm, fraction=fraction)
        used = EffectiveRainfallMethod(name, {"fraction": fraction},
                                       str(settings.get("basis", "")))

    elif name == "usda_scs_monthly":
        settings = dict(config.get("usda_scs_monthly") or {})
        values = usda_scs_monthly(rainfall_mm)
        used = EffectiveRainfallMethod(name, {}, str(settings.get("basis", "")))

    else:
        raise ValueError(
            f"unknown effective rainfall method {name!r}; expected one of "
            "daily_threshold_fraction, fixed_fraction, usda_scs_monthly"
        )

    # An effective depth can never exceed what fell, and can never be negative.
    rain = np.asarray(rainfall_mm, dtype=float)
    values = np.clip(values, 0.0, rain)
    log.info("effective rainfall via %s: %.1f%% of %.0f mm total retained",
             name, 100.0 * values.sum() / max(rain.sum(), 1e-9), rain.sum())
    return values, used


def compare_methods(
    rainfall_mm: np.ndarray | pd.Series, config: dict[str, Any]
) -> pd.DataFrame:
    """Side-by-side comparison of the daily methods, for the write-up.

    The SCS row is computed with ``force_daily=True`` specifically to show how
    far wrong the monthly formula goes when misapplied to daily data.
    """
    rain = np.asarray(rainfall_mm, dtype=float)
    total = float(rain.sum())
    settings = dict(config.get("daily_threshold_fraction") or {})

    rows = []
    for label, values, note in (
        (
            "daily_threshold_fraction",
            daily_threshold_fraction(
                rain,
                interception_threshold_mm=float(settings.get("interception_threshold_mm", 2.0)),
                infiltration_fraction=float(settings.get("infiltration_fraction", 0.75)),
                max_daily_storage_mm=float(settings.get("default_max_daily_storage_mm", 40.0)),
            ),
            "daily method used by this study",
        ),
        (
            "fixed_fraction_0.80",
            fixed_fraction(rain, fraction=0.80),
            "crude comparison baseline",
        ),
        (
            "usda_scs_misapplied_daily",
            usda_scs_monthly(rain, force_daily=True),
            "MONTHLY formula applied daily: shown to demonstrate the unit error",
        ),
    ):
        values = np.clip(values, 0.0, rain)
        rows.append(
            {
                "method": label,
                "effective_total_mm": round(float(values.sum()), 1),
                "share_of_rainfall_pct": round(100.0 * float(values.sum()) / max(total, 1e-9), 1),
                "effective_from_a_2mm_day": round(
                    float(np.clip(_single(label, 2.0, settings), 0.0, 2.0)), 3
                ),
                "effective_from_a_20mm_day": round(
                    float(np.clip(_single(label, 20.0, settings), 0.0, 20.0)), 3
                ),
                "note": note,
            }
        )
    return pd.DataFrame(rows)


def _single(method_label: str, value_mm: float, settings: dict[str, Any]) -> float:
    """Effective depth produced by one method from a single day of rain."""
    array = np.array([value_mm], dtype=float)
    if method_label.startswith("daily_threshold"):
        return float(
            daily_threshold_fraction(
                array,
                interception_threshold_mm=float(settings.get("interception_threshold_mm", 2.0)),
                infiltration_fraction=float(settings.get("infiltration_fraction", 0.75)),
                max_daily_storage_mm=float(settings.get("default_max_daily_storage_mm", 40.0)),
            )[0]
        )
    if method_label.startswith("fixed_fraction"):
        return float(fixed_fraction(array, fraction=0.80)[0])
    return float(usda_scs_monthly(array, force_daily=True)[0])
