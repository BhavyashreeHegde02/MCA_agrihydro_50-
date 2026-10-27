"""Recovering what can be known about the weather site, and bounding the rest.

The weather series has no latitude, longitude or elevation column, and FAO-56
needs latitude and elevation. Rather than assume a coordinate, this module does
two things that can be checked:

1. :func:`estimate_latitude` **estimates** latitude from the radiation series
   itself, and reports how tightly the data constrains it.
2. :func:`et0_sensitivity` **bounds** the consequence of the residual
   uncertainty by recomputing ET0 across a whole envelope of plausible sites.

The second result is the one that matters for the study. If ET0 barely moves
across the envelope, the unresolved site is a documented limitation rather than
a threat to the conclusions, and that can be demonstrated instead of asserted.

Method behind the latitude estimate
-----------------------------------
On a cloud-free day the incoming shortwave radiation approaches the clear-sky
ceiling, so the clearness index

    Kt = Rs / Ra(latitude, day-of-year)

should reach roughly the same value on the clearest day of every month. The
seasonal *shape* of ``Ra`` is controlled almost entirely by latitude: near the
equator it is nearly flat, and it swings harder as latitude increases. So the
latitude whose ``Ra`` flattens the month-to-month profile of the high-percentile
``Kt`` is the latitude most consistent with the observations.

Only rain-free dry-season days enter the fit, because monsoon months never
produce a clear sky and would drag the high percentile down for reasons that
have nothing to do with latitude.

Known bias
----------
The estimator assumes atmospheric transparency is constant through the year.
It is not: winter haze and pre-monsoon dust both depress ``Rs`` in specific
months, and both push the fitted latitude upward. The estimate is therefore an
upper-leaning one and is reported as a weak constraint, never as the site's
location.
"""

from __future__ import annotations

import dataclasses
from typing import Sequence

import numpy as np
import pandas as pd

from ml.config import SiteConfig
from ml.et0 import extraterrestrial_radiation, penman_monteith_et0
from ml.logging_utils import get_logger

log = get_logger("site_inference")

#: Months in which cloud-free days actually occur at this site. Derived from the
#: rainfall climatology of the series itself (June-September carry ~95% of the
#: annual total), not assumed from a region.
DEFAULT_DRY_MONTHS: tuple[int, ...] = (11, 12, 1, 2, 3, 4, 5)


@dataclasses.dataclass(frozen=True)
class LatitudeEstimate:
    """Result of the clear-sky latitude fit."""

    latitude_deg: float
    clear_sky_kt: float
    objective: float
    plausible_range_deg: tuple[float, float]
    resample_mean_deg: float
    resample_sd_deg: float
    n_days_used: int
    profile: pd.DataFrame

    def describe(self) -> str:
        low, high = self.plausible_range_deg
        return (
            f"latitude estimate {self.latitude_deg:.2f} degN "
            f"(resampling {self.resample_mean_deg:.2f} +/- {self.resample_sd_deg:.2f}; "
            f"objective within 1.5x of minimum over {low:.2f}-{high:.2f} degN), "
            f"implied clear-sky Kt {self.clear_sky_kt:.3f}, "
            f"fitted on {self.n_days_used} rain-free dry-season days"
        )


def _clearness_objective(
    latitude_deg: float,
    day_of_year: np.ndarray,
    month: np.ndarray,
    rs: np.ndarray,
    quantile: float,
) -> tuple[float, float]:
    """Return (coefficient of variation, mean level) of the monthly clear-sky Kt."""
    ra = extraterrestrial_radiation(latitude_deg, day_of_year)
    kt = rs / ra
    monthly = pd.Series(kt).groupby(pd.Series(month)).quantile(quantile)
    return float(monthly.std() / monthly.mean()), float(monthly.mean())


def estimate_latitude(
    weather: pd.DataFrame,
    *,
    date_column: str = "datetime",
    solar_column: str = "allsky_sfc_sw_dwn",
    rain_column: str = "prectotcorr",
    dry_months: Sequence[int] = DEFAULT_DRY_MONTHS,
    quantile: float = 0.95,
    search_deg: tuple[float, float] = (1.0, 35.0),
    step_deg: float = 0.25,
) -> LatitudeEstimate:
    """Fit latitude to the seasonal shape of the clear-sky radiation envelope."""
    frame = weather.dropna(subset=[solar_column]).copy()
    dates = pd.to_datetime(frame[date_column])
    frame["_doy"] = dates.dt.dayofyear
    frame["_month"] = dates.dt.month
    frame["_year"] = dates.dt.year

    subset = frame[frame["_month"].isin(list(dry_months))]
    if rain_column in subset.columns:
        subset = subset[subset[rain_column] <= 0.0]
    if len(subset) < 100:
        raise ValueError(
            f"only {len(subset)} rain-free dry-season days available; "
            "too few to constrain latitude"
        )

    grid = np.arange(search_deg[0], search_deg[1] + 1e-9, step_deg)
    doy = subset["_doy"].to_numpy(dtype=float)
    month = subset["_month"].to_numpy(dtype=int)
    rs = subset[solar_column].to_numpy(dtype=float)

    records = []
    for lat in grid:
        cv, level = _clearness_objective(float(lat), doy, month, rs, quantile)
        records.append({"latitude_deg": float(lat), "objective_cv": cv, "clear_sky_kt": level})
    profile = pd.DataFrame(records)

    best = profile.loc[profile["objective_cv"].idxmin()]
    plausible = profile[profile["objective_cv"] <= best["objective_cv"] * 1.5]

    # Leave-one-year-out resampling: how much does the estimate move if any
    # single year is withheld?
    per_year: list[float] = []
    for year in sorted(subset["_year"].unique()):
        held = subset[subset["_year"] != year]
        if len(held) < 100:
            continue
        cvs = [
            _clearness_objective(
                float(lat),
                held["_doy"].to_numpy(dtype=float),
                held["_month"].to_numpy(dtype=int),
                held[solar_column].to_numpy(dtype=float),
                quantile,
            )[0]
            for lat in grid
        ]
        per_year.append(float(grid[int(np.argmin(cvs))]))

    estimate = LatitudeEstimate(
        latitude_deg=float(best["latitude_deg"]),
        clear_sky_kt=float(best["clear_sky_kt"]),
        objective=float(best["objective_cv"]),
        plausible_range_deg=(
            float(plausible["latitude_deg"].min()),
            float(plausible["latitude_deg"].max()),
        ),
        resample_mean_deg=float(np.mean(per_year)) if per_year else float("nan"),
        resample_sd_deg=float(np.std(per_year)) if per_year else float("nan"),
        n_days_used=int(len(subset)),
        profile=profile,
    )
    log.info("%s", estimate.describe())
    return estimate


def et0_sensitivity(
    weather: pd.DataFrame,
    site: SiteConfig,
    *,
    date_column: str = "datetime",
    latitudes: Sequence[float] | None = None,
    elevations: Sequence[float] | None = None,
) -> pd.DataFrame:
    """Recompute mean ET0 across an envelope of latitudes and elevations.

    Returns one row per (latitude, elevation) corner with the resulting mean and
    total ET0, plus the percentage departure from the envelope mean. This is the
    evidence that decides whether the unresolved site actually matters.
    """
    if latitudes is None:
        low, high = site.latitude_envelope
        latitudes = list(np.round(np.linspace(low, high, 7), 2))
    if elevations is None:
        low, high = site.elevation_envelope
        elevations = list(np.round(np.linspace(low, high, 3), 1))

    dates = pd.to_datetime(weather[date_column])
    doy = dates.dt.dayofyear.to_numpy(dtype=float)
    settings = site.fao56

    usable = weather.dropna(subset=["allsky_sfc_sw_dwn"])
    usable_doy = pd.to_datetime(usable[date_column]).dt.dayofyear.to_numpy(dtype=float)

    rows = []
    for lat in latitudes:
        for elev in elevations:
            result = penman_monteith_et0(
                tmean_c=usable["t2m"].to_numpy(dtype=float),
                tmax_c=usable["t2m_max"].to_numpy(dtype=float),
                tmin_c=usable["t2m_min"].to_numpy(dtype=float),
                rh_mean_pct=usable["rh2m"].to_numpy(dtype=float),
                wind_speed_ms=usable["ws2m"].to_numpy(dtype=float),
                solar_radiation_mj_m2_day=usable["allsky_sfc_sw_dwn"].to_numpy(dtype=float),
                day_of_year=usable_doy,
                latitude_deg=float(lat),
                elevation_m=float(elev),
                albedo=float(settings.get("albedo", 0.23)),
                soil_heat_flux_mj_m2_day=float(settings.get("soil_heat_flux_daily_mj_m2", 0.0)),
                wind_measurement_height_m=float(settings.get("wind_measurement_height_m", 2.0)),
                turbidity_a=float(settings.get("clear_sky_turbidity_a", 0.75)),
                turbidity_b=float(settings.get("clear_sky_turbidity_b", 2.0e-5)),
            )
            et0 = result.et0_mm_day
            rows.append(
                {
                    "latitude_deg": float(lat),
                    "elevation_m": float(elev),
                    "mean_et0_mm_day": float(np.mean(et0)),
                    "min_et0_mm_day": float(np.min(et0)),
                    "max_et0_mm_day": float(np.max(et0)),
                    "annual_et0_mm": float(np.sum(et0) / (len(et0) / 365.25)),
                }
            )
    _ = doy  # the full-series day-of-year is not needed once NaNs are dropped

    frame = pd.DataFrame(rows)
    envelope_mean = frame["mean_et0_mm_day"].mean()
    frame["pct_from_envelope_mean"] = 100.0 * (frame["mean_et0_mm_day"] - envelope_mean) / envelope_mean
    return frame


def sensitivity_summary(sensitivity: pd.DataFrame) -> dict[str, float]:
    """Condense :func:`et0_sensitivity` into the numbers quoted in the write-up."""
    values = sensitivity["mean_et0_mm_day"].to_numpy(dtype=float)
    mean = float(values.mean())
    return {
        "envelope_mean_et0_mm_day": mean,
        "envelope_min_et0_mm_day": float(values.min()),
        "envelope_max_et0_mm_day": float(values.max()),
        "half_spread_pct": float(100.0 * (values.max() - values.min()) / 2.0 / mean),
        "corners_evaluated": int(len(values)),
    }


def rainfall_regime(weather: pd.DataFrame, *, date_column: str = "datetime",
                    rain_column: str = "prectotcorr") -> pd.DataFrame:
    """Monthly rainfall climatology, used as independent evidence about the region."""
    frame = weather.copy()
    dates = pd.to_datetime(frame[date_column])
    frame["_month"] = dates.dt.month
    frame["_year"] = dates.dt.year
    n_years = frame["_year"].nunique()
    monthly = frame.groupby("_month")[rain_column].sum() / n_years
    out = monthly.rename("mean_monthly_rainfall_mm").to_frame()
    out["share_of_annual_pct"] = 100.0 * out["mean_monthly_rainfall_mm"] / out["mean_monthly_rainfall_mm"].sum()
    out.index.name = "month"
    return out.round(2)
