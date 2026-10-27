"""Reference evapotranspiration by FAO-56 Penman-Monteith.

This module is the physics core of the study. It is written so that each
intermediate quantity is a separate, individually testable function with its
unit in the name or the docstring, because unit errors are the classic failure
mode in crop-water work.

Symbols follow Allen, Pereira, Raes and Smith (1998), *Crop evapotranspiration:
guidelines for computing crop water requirements*, FAO Irrigation and Drainage
Paper 56. Equation numbers in the comments refer to that paper.

Units used throughout
---------------------
=========================  =============================
temperature                degrees Celsius
relative humidity          percent
wind speed at 2 m          metres per second
solar radiation            megajoules per square metre per day
pressure, vapour pressure  kilopascals
ET0                        millimetres per day
=========================  =============================

Why the input series needs no unit conversion
---------------------------------------------
The project's weather file carries the NASA POWER parameter names. Those
parameters are published in exactly the units FAO-56 expects: ``T2M`` in
degrees Celsius, ``RH2M`` in percent, ``WS2M`` in metres per second *at two
metres* and ``ALLSKY_SFC_SW_DWN`` in MJ m-2 day-1. In particular, because the
wind is already referenced to 2 m, the logarithmic wind-height correction of
FAO-56 equation 47 is deliberately **not** applied. Applying it would be a
silent error, so :func:`wind_speed_at_2m` exists to make the decision explicit
and testable.
"""

from __future__ import annotations

import dataclasses
from typing import Final

import numpy as np
import pandas as pd

from ml.config import SiteConfig
from ml.logging_utils import get_logger

log = get_logger("et0")

# --- physical constants (FAO-56) -------------------------------------------
SOLAR_CONSTANT_MJ_M2_MIN: Final[float] = 0.0820   # Gsc
STEFAN_BOLTZMANN_MJ: Final[float] = 4.903e-9      # sigma, MJ K-4 m-2 day-1
ALBEDO_GRASS: Final[float] = 0.23                 # alpha for the reference surface
LATENT_HEAT_MJ_PER_KG: Final[float] = 2.45        # lambda at ~20 C
DAYS_IN_YEAR: Final[float] = 365.0


ArrayLike = np.ndarray | pd.Series | float


def _as_array(value: ArrayLike) -> np.ndarray:
    return np.asarray(value, dtype=float)


# ==========================================================================
# 1. Astronomy and extraterrestrial radiation
# ==========================================================================
def inverse_relative_distance(day_of_year: ArrayLike) -> np.ndarray:
    """Earth-Sun inverse relative distance ``dr`` (FAO-56 eq. 23, dimensionless)."""
    j = _as_array(day_of_year)
    return 1.0 + 0.033 * np.cos(2.0 * np.pi * j / DAYS_IN_YEAR)


def solar_declination(day_of_year: ArrayLike) -> np.ndarray:
    """Solar declination in radians (FAO-56 eq. 24)."""
    j = _as_array(day_of_year)
    return 0.409 * np.sin(2.0 * np.pi * j / DAYS_IN_YEAR - 1.39)


def sunset_hour_angle(latitude_deg: float, day_of_year: ArrayLike) -> np.ndarray:
    """Sunset hour angle ``omega_s`` in radians (FAO-56 eq. 25).

    The argument of ``arccos`` is clipped to [-1, 1] so polar day and polar
    night return 0 or pi rather than a NaN.
    """
    phi = np.radians(latitude_deg)
    dec = solar_declination(day_of_year)
    return np.arccos(np.clip(-np.tan(phi) * np.tan(dec), -1.0, 1.0))


def extraterrestrial_radiation(latitude_deg: float, day_of_year: ArrayLike) -> np.ndarray:
    """Daily extraterrestrial radiation ``Ra`` in MJ m-2 day-1 (FAO-56 eq. 21).

    This is the single place latitude enters the ET0 calculation, which is why
    the site-sensitivity study in :mod:`ml.site_inference` can be expressed
    purely as a sweep over this function's first argument.
    """
    phi = np.radians(latitude_deg)
    dr = inverse_relative_distance(day_of_year)
    dec = solar_declination(day_of_year)
    ws = sunset_hour_angle(latitude_deg, day_of_year)
    return (
        (24.0 * 60.0 / np.pi)
        * SOLAR_CONSTANT_MJ_M2_MIN
        * dr
        * (ws * np.sin(phi) * np.sin(dec) + np.cos(phi) * np.cos(dec) * np.sin(ws))
    )


def clear_sky_radiation(
    ra_mj_m2_day: ArrayLike,
    elevation_m: float,
    turbidity_a: float = 0.75,
    turbidity_b: float = 2.0e-5,
) -> np.ndarray:
    """Clear-sky shortwave radiation ``Rso`` in MJ m-2 day-1 (FAO-56 eq. 37)."""
    return (turbidity_a + turbidity_b * float(elevation_m)) * _as_array(ra_mj_m2_day)


# ==========================================================================
# 2. Atmospheric properties
# ==========================================================================
def atmospheric_pressure(elevation_m: float) -> float:
    """Mean barometric pressure in kPa from elevation (FAO-56 eq. 7)."""
    return 101.3 * ((293.0 - 0.0065 * float(elevation_m)) / 293.0) ** 5.26


def psychrometric_constant(pressure_kpa: float) -> float:
    """Psychrometric constant ``gamma`` in kPa/degC (FAO-56 eq. 8)."""
    return 0.665e-3 * float(pressure_kpa)


def saturation_vapour_pressure(temperature_c: ArrayLike) -> np.ndarray:
    """Saturation vapour pressure ``e0(T)`` in kPa (FAO-56 eq. 11)."""
    t = _as_array(temperature_c)
    return 0.6108 * np.exp(17.27 * t / (t + 237.3))


def mean_saturation_vapour_pressure(tmax_c: ArrayLike, tmin_c: ArrayLike) -> np.ndarray:
    """Mean saturation vapour pressure ``es`` in kPa (FAO-56 eq. 12).

    FAO-56 is explicit that ``es`` must be the average of the saturation
    pressures at Tmax and Tmin, not the saturation pressure at Tmean. Using
    Tmean understates ``es`` and therefore understates the vapour-pressure
    deficit, so the distinction is kept in a named function.
    """
    return 0.5 * (saturation_vapour_pressure(tmax_c) + saturation_vapour_pressure(tmin_c))


def actual_vapour_pressure_from_rh(
    tmax_c: ArrayLike, tmin_c: ArrayLike, rh_mean_pct: ArrayLike
) -> np.ndarray:
    """Actual vapour pressure ``ea`` in kPa from mean relative humidity (FAO-56 eq. 19).

    Equation 19 is the form recommended when only mean RH is available, which is
    the case here: the weather series reports a single daily ``RH2M`` rather
    than the RHmax/RHmin pair that equation 17 would need.
    """
    rh = np.clip(_as_array(rh_mean_pct), 0.0, 100.0)
    return (rh / 100.0) * mean_saturation_vapour_pressure(tmax_c, tmin_c)


def slope_vapour_pressure_curve(temperature_c: ArrayLike) -> np.ndarray:
    """Slope ``Delta`` of the vapour-pressure curve in kPa/degC (FAO-56 eq. 13)."""
    t = _as_array(temperature_c)
    return 4098.0 * (0.6108 * np.exp(17.27 * t / (t + 237.3))) / (t + 237.3) ** 2


def wind_speed_at_2m(wind_speed: ArrayLike, measurement_height_m: float = 2.0) -> np.ndarray:
    """Wind speed referenced to 2 m in m/s (FAO-56 eq. 47).

    Returns the input unchanged when it was already measured at 2 m. The
    project's ``WS2M`` series is a 2 m product, so in this study the function is
    an identity -- which is precisely why it is written down rather than assumed.
    """
    u = _as_array(wind_speed)
    height = float(measurement_height_m)
    if abs(height - 2.0) < 1e-9:
        return u
    return u * (4.87 / np.log(67.8 * height - 5.42))


# ==========================================================================
# 3. Radiation balance
# ==========================================================================
def net_shortwave_radiation(rs_mj_m2_day: ArrayLike, albedo: float = ALBEDO_GRASS) -> np.ndarray:
    """Net shortwave radiation ``Rns`` in MJ m-2 day-1 (FAO-56 eq. 38)."""
    return (1.0 - float(albedo)) * _as_array(rs_mj_m2_day)


def net_longwave_radiation(
    tmax_c: ArrayLike,
    tmin_c: ArrayLike,
    ea_kpa: ArrayLike,
    rs_mj_m2_day: ArrayLike,
    rso_mj_m2_day: ArrayLike,
) -> np.ndarray:
    """Net outgoing longwave radiation ``Rnl`` in MJ m-2 day-1 (FAO-56 eq. 39).

    The cloudiness term ``Rs/Rso`` is clipped to [0, 1]. Values slightly above 1
    occur in real radiation products on very clear days and would otherwise push
    ``Rnl`` above its physical ceiling.
    """
    tmax_k = _as_array(tmax_c) + 273.16
    tmin_k = _as_array(tmin_c) + 273.16
    ea = np.clip(_as_array(ea_kpa), 0.0, None)
    cloud = np.clip(_as_array(rs_mj_m2_day) / np.maximum(_as_array(rso_mj_m2_day), 1e-9), 0.0, 1.0)
    return (
        STEFAN_BOLTZMANN_MJ
        * ((tmax_k ** 4 + tmin_k ** 4) / 2.0)
        * (0.34 - 0.14 * np.sqrt(ea))
        * (1.35 * cloud - 0.35)
    )


# ==========================================================================
# 4. Penman-Monteith
# ==========================================================================
@dataclasses.dataclass(frozen=True)
class ET0Result:
    """ET0 together with every intermediate quantity that produced it.

    Keeping the intermediates is what makes the baseline auditable: a reviewer
    can check ``Rn``, ``es - ea`` and ``gamma`` rather than having to trust a
    single output column.
    """

    et0_mm_day: np.ndarray
    ra_mj_m2_day: np.ndarray
    rso_mj_m2_day: np.ndarray
    rn_mj_m2_day: np.ndarray
    rns_mj_m2_day: np.ndarray
    rnl_mj_m2_day: np.ndarray
    es_kpa: np.ndarray
    ea_kpa: np.ndarray
    vpd_kpa: np.ndarray
    delta_kpa_c: np.ndarray
    gamma_kpa_c: float
    pressure_kpa: float
    radiation_term_mm_day: np.ndarray
    aerodynamic_term_mm_day: np.ndarray

    def to_frame(self, index: pd.Index | None = None) -> pd.DataFrame:
        data = {
            "et0_mm_day": self.et0_mm_day,
            "ra_mj_m2_day": self.ra_mj_m2_day,
            "rso_mj_m2_day": self.rso_mj_m2_day,
            "rn_mj_m2_day": self.rn_mj_m2_day,
            "rns_mj_m2_day": self.rns_mj_m2_day,
            "rnl_mj_m2_day": self.rnl_mj_m2_day,
            "es_kpa": self.es_kpa,
            "ea_kpa": self.ea_kpa,
            "vpd_kpa": self.vpd_kpa,
            "delta_kpa_c": self.delta_kpa_c,
            "et0_radiation_term_mm_day": self.radiation_term_mm_day,
            "et0_aerodynamic_term_mm_day": self.aerodynamic_term_mm_day,
        }
        return pd.DataFrame(data, index=index)


def penman_monteith_et0(
    *,
    tmean_c: ArrayLike,
    tmax_c: ArrayLike,
    tmin_c: ArrayLike,
    rh_mean_pct: ArrayLike,
    wind_speed_ms: ArrayLike,
    solar_radiation_mj_m2_day: ArrayLike,
    day_of_year: ArrayLike,
    latitude_deg: float,
    elevation_m: float,
    albedo: float = ALBEDO_GRASS,
    soil_heat_flux_mj_m2_day: float = 0.0,
    wind_measurement_height_m: float = 2.0,
    turbidity_a: float = 0.75,
    turbidity_b: float = 2.0e-5,
) -> ET0Result:
    """Daily reference evapotranspiration in mm/day (FAO-56 eq. 6).

    ``G`` defaults to zero because FAO-56 states that daily soil heat flux under
    a reference grass surface is negligible relative to ``Rn``.
    """
    tmean = _as_array(tmean_c)
    tmax = _as_array(tmax_c)
    tmin = _as_array(tmin_c)
    rs = _as_array(solar_radiation_mj_m2_day)

    pressure = atmospheric_pressure(elevation_m)
    gamma = psychrometric_constant(pressure)

    es = mean_saturation_vapour_pressure(tmax, tmin)
    ea = actual_vapour_pressure_from_rh(tmax, tmin, rh_mean_pct)
    vpd = np.maximum(es - ea, 0.0)
    delta = slope_vapour_pressure_curve(tmean)

    ra = extraterrestrial_radiation(latitude_deg, day_of_year)
    rso = clear_sky_radiation(ra, elevation_m, turbidity_a, turbidity_b)
    rns = net_shortwave_radiation(rs, albedo)
    rnl = net_longwave_radiation(tmax, tmin, ea, rs, rso)
    rn = rns - rnl

    u2 = wind_speed_at_2m(wind_speed_ms, wind_measurement_height_m)

    denominator = delta + gamma * (1.0 + 0.34 * u2)
    radiation_term = (0.408 * delta * (rn - float(soil_heat_flux_mj_m2_day))) / denominator
    aerodynamic_term = (gamma * (900.0 / (tmean + 273.0)) * u2 * vpd) / denominator

    return ET0Result(
        et0_mm_day=radiation_term + aerodynamic_term,
        ra_mj_m2_day=ra,
        rso_mj_m2_day=rso,
        rn_mj_m2_day=rn,
        rns_mj_m2_day=rns,
        rnl_mj_m2_day=rnl,
        es_kpa=es,
        ea_kpa=ea,
        vpd_kpa=vpd,
        delta_kpa_c=delta,
        gamma_kpa_c=gamma,
        pressure_kpa=pressure,
        radiation_term_mm_day=radiation_term,
        aerodynamic_term_mm_day=aerodynamic_term,
    )


def hargreaves_et0(
    tmean_c: ArrayLike,
    tmax_c: ArrayLike,
    tmin_c: ArrayLike,
    day_of_year: ArrayLike,
    latitude_deg: float,
    coefficient: float = 0.0023,
) -> np.ndarray:
    """Temperature-only ET0 in mm/day (FAO-56 eq. 52).

    Used purely as an independent cross-check. It shares only the temperature
    inputs with Penman-Monteith, so agreement between the two is meaningful
    evidence that the radiation and humidity terms have not been mis-scaled.
    """
    tmean = _as_array(tmean_c)
    tmax = _as_array(tmax_c)
    tmin = _as_array(tmin_c)
    ra = extraterrestrial_radiation(latitude_deg, day_of_year)
    return coefficient * (tmean + 17.8) * np.sqrt(np.maximum(tmax - tmin, 0.0)) * (ra / LATENT_HEAT_MJ_PER_KG)


# ==========================================================================
# 5. Frame-level entry point
# ==========================================================================
#: Maps the normalised weather column names onto the Penman-Monteith arguments.
WEATHER_COLUMN_MAP: Final[dict[str, str]] = {
    "tmean_c": "t2m",
    "tmax_c": "t2m_max",
    "tmin_c": "t2m_min",
    "rh_mean_pct": "rh2m",
    "wind_speed_ms": "ws2m",
    "solar_radiation_mj_m2_day": "allsky_sfc_sw_dwn",
}


def et0_for_weather_frame(
    weather: pd.DataFrame,
    site: SiteConfig,
    *,
    date_column: str = "datetime",
    latitude_deg: float | None = None,
    elevation_m: float | None = None,
    attach_intermediates: bool = True,
) -> pd.DataFrame:
    """Compute ET0 for a daily weather table.

    ``site`` supplies the coordinates and the FAO-56 settings, and is checked by
    :meth:`~ml.config.SiteConfig.require_usable` first, so an unresolved site
    produces an explanatory error rather than a fabricated number. The explicit
    ``latitude_deg`` / ``elevation_m`` overrides exist for the sensitivity sweep.
    """
    site.require_usable()
    lat = site.latitude_deg if latitude_deg is None else float(latitude_deg)
    elev = site.elevation_m if elevation_m is None else float(elevation_m)
    assert lat is not None and elev is not None  # guaranteed by require_usable

    missing = [c for c in WEATHER_COLUMN_MAP.values() if c not in weather.columns]
    if missing:
        raise KeyError(f"weather frame is missing required column(s): {missing}")

    dates = pd.to_datetime(weather[date_column])
    settings = site.fao56

    result = penman_monteith_et0(
        tmean_c=weather[WEATHER_COLUMN_MAP["tmean_c"]].to_numpy(dtype=float),
        tmax_c=weather[WEATHER_COLUMN_MAP["tmax_c"]].to_numpy(dtype=float),
        tmin_c=weather[WEATHER_COLUMN_MAP["tmin_c"]].to_numpy(dtype=float),
        rh_mean_pct=weather[WEATHER_COLUMN_MAP["rh_mean_pct"]].to_numpy(dtype=float),
        wind_speed_ms=weather[WEATHER_COLUMN_MAP["wind_speed_ms"]].to_numpy(dtype=float),
        solar_radiation_mj_m2_day=weather[WEATHER_COLUMN_MAP["solar_radiation_mj_m2_day"]].to_numpy(dtype=float),
        day_of_year=dates.dt.dayofyear.to_numpy(dtype=float),
        latitude_deg=lat,
        elevation_m=elev,
        albedo=float(settings.get("albedo", ALBEDO_GRASS)),
        soil_heat_flux_mj_m2_day=float(settings.get("soil_heat_flux_daily_mj_m2", 0.0)),
        wind_measurement_height_m=float(settings.get("wind_measurement_height_m", 2.0)),
        turbidity_a=float(settings.get("clear_sky_turbidity_a", 0.75)),
        turbidity_b=float(settings.get("clear_sky_turbidity_b", 2.0e-5)),
    )

    out = weather.copy()
    if attach_intermediates:
        frame = result.to_frame(index=out.index)
        for column in frame.columns:
            out[column] = frame[column]
    else:
        out["et0_mm_day"] = result.et0_mm_day

    out["et0_latitude_deg"] = lat
    out["et0_elevation_m"] = elev
    out["et0_site_status"] = site.resolution_status
    return out
