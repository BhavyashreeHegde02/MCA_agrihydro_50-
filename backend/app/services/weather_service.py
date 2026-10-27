"""Weather providers, behind one interface.

The API needs today's weather and a short forecast. Where those come from should
not leak into the prediction logic, so providers implement a common interface
and the rest of the service only sees :class:`WeatherReading`.

Three providers ship:

``NullProvider``
    The default. Returns nothing and says why. A farmer who has not configured a
    provider gets an honest "not available" and the option to enter readings by
    hand, rather than a silently invented forecast.
``OpenMeteoProvider``
    A keyless public API, which makes the integration demonstrable without the
    reviewer having to register for anything.
``OpenWeatherMapProvider``
    Key-based, read from the environment. Never hard-coded.

Two rules are enforced rather than documented.

**Live data is never silently mixed into training.** Every reading carries a
``source``, the database constrains that column, and the research series is
tagged ``historical_research``. Ingesting live observations into a training set
is a deliberate, separate act.

**A provider failure degrades, it does not crash.** Weather services time out.
The prediction endpoint stays usable with manually entered weather.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import threading
import time
from typing import Any, Protocol

import httpx

from app.core.config import settings
from ml.logging_utils import get_logger

log = get_logger("api.weather_service")


class WeatherUnavailableError(RuntimeError):
    """The configured provider could not supply a reading."""


@dataclasses.dataclass
class WeatherReading:
    """One day of weather from a provider, in the units FAO-56 expects."""

    date: dt.date
    temperature_mean_c: float
    temperature_min_c: float
    temperature_max_c: float
    humidity_pct: float
    rainfall_mm: float
    wind_speed_ms: float | None
    solar_radiation_mj_m2: float | None
    source: str
    provider: str
    is_forecast: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = dataclasses.asdict(self)
        payload["date"] = str(self.date)
        return payload


class WeatherProvider(Protocol):
    name: str

    def current(self, latitude: float, longitude: float) -> WeatherReading: ...

    def forecast(self, latitude: float, longitude: float, days: int) -> list[WeatherReading]: ...


# --------------------------------------------------------------------------
class NullProvider:
    """No provider configured. Explains itself instead of inventing data."""

    name = "none"

    def _refuse(self) -> WeatherUnavailableError:
        return WeatherUnavailableError(
            "No weather provider is configured. Set WEATHER_PROVIDER to 'open_meteo' "
            "(no API key needed) or 'openweathermap' with WEATHER_API_KEY. Until then, "
            "supply weather readings directly in the prediction request."
        )

    def current(self, latitude: float, longitude: float) -> WeatherReading:
        raise self._refuse()

    def forecast(self, latitude: float, longitude: float, days: int) -> list[WeatherReading]:
        raise self._refuse()


class OpenMeteoProvider:
    """Open-Meteo. Public, keyless, and reports shortwave radiation directly.

    Radiation matters: it is a FAO-56 input, and a provider that supplies it
    removes the need for the temperature-range substitution.
    """

    name = "open_meteo"
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    DAILY_FIELDS = (
        "temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
        "relative_humidity_2m_mean,precipitation_sum,"
        "wind_speed_10m_max,shortwave_radiation_sum"
    )

    def _fetch(self, latitude: float, longitude: float, days: int) -> dict[str, Any]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": self.DAILY_FIELDS,
            "timezone": "auto",
            "forecast_days": max(1, min(days, 16)),
            "wind_speed_unit": "ms",
        }
        try:
            response = httpx.get(self.BASE_URL, params=params,
                                 timeout=settings.weather_request_timeout_seconds)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as error:
            raise WeatherUnavailableError(
                f"the Open-Meteo request failed: {error}"
            ) from error

    @staticmethod
    def _reading(daily: dict[str, Any], index: int, is_forecast: bool) -> WeatherReading:
        def value(key: str) -> float | None:
            series = daily.get(key) or []
            if index >= len(series) or series[index] is None:
                return None
            return float(series[index])

        tmax, tmin = value("temperature_2m_max"), value("temperature_2m_min")
        tmean = value("temperature_2m_mean")
        if tmean is None and tmax is not None and tmin is not None:
            tmean = (tmax + tmin) / 2.0

        return WeatherReading(
            date=dt.date.fromisoformat(daily["time"][index]),
            temperature_mean_c=float(tmean if tmean is not None else 0.0),
            temperature_min_c=float(tmin if tmin is not None else 0.0),
            temperature_max_c=float(tmax if tmax is not None else 0.0),
            humidity_pct=float(value("relative_humidity_2m_mean") or 0.0),
            rainfall_mm=float(value("precipitation_sum") or 0.0),
            # Open-Meteo reports a 10 m maximum; ml.et0 converts it to the 2 m
            # reference height rather than treating it as already correct.
            wind_speed_ms=value("wind_speed_10m_max"),
            # Already MJ/m2/day, which is what FAO-56 expects.
            solar_radiation_mj_m2=value("shortwave_radiation_sum"),
            source="forecast" if is_forecast else "live_api",
            provider="open_meteo",
            is_forecast=is_forecast,
        )

    def current(self, latitude: float, longitude: float) -> WeatherReading:
        payload = self._fetch(latitude, longitude, days=1)
        return self._reading(payload["daily"], 0, is_forecast=False)

    def forecast(self, latitude: float, longitude: float, days: int = 7) -> list[WeatherReading]:
        payload = self._fetch(latitude, longitude, days=days)
        daily = payload["daily"]
        return [self._reading(daily, i, is_forecast=i > 0) for i in range(len(daily["time"]))]


class OpenWeatherMapProvider:
    """OpenWeatherMap. Requires a key, supplied through the environment."""

    name = "openweathermap"
    BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

    def __init__(self, api_key: str | None) -> None:
        self._api_key = api_key

    def _require_key(self) -> str:
        if not self._api_key:
            raise WeatherUnavailableError(
                "WEATHER_API_KEY is not set, so the OpenWeatherMap provider cannot "
                "be used. Set it in the environment, never in the source."
            )
        return self._api_key

    def _fetch(self, latitude: float, longitude: float) -> dict[str, Any]:
        params = {"lat": latitude, "lon": longitude,
                  "appid": self._require_key(), "units": "metric"}
        try:
            response = httpx.get(self.BASE_URL, params=params,
                                 timeout=settings.weather_request_timeout_seconds)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as error:
            raise WeatherUnavailableError(
                f"the OpenWeatherMap request failed: {error}"
            ) from error

    def _to_daily(self, payload: dict[str, Any]) -> list[WeatherReading]:
        """Aggregate three-hourly entries into daily readings.

        Temperature extremes become the day's min and max, humidity is averaged
        and precipitation summed, which is what FAO-56 needs. Radiation is not
        reported by this endpoint, so it is left absent and the baseline falls
        back to the documented FAO-56 substitution rather than guessing.
        """
        buckets: dict[dt.date, list[dict[str, Any]]] = {}
        for entry in payload.get("list", []):
            day = dt.datetime.fromtimestamp(entry["dt"], dt.timezone.utc).date()
            buckets.setdefault(day, []).append(entry)

        readings: list[WeatherReading] = []
        today = dt.date.today()
        for day, entries in sorted(buckets.items()):
            temperatures = [e["main"]["temp"] for e in entries]
            humidities = [e["main"]["humidity"] for e in entries]
            rain = sum(e.get("rain", {}).get("3h", 0.0) for e in entries)
            winds = [e.get("wind", {}).get("speed") for e in entries
                     if e.get("wind", {}).get("speed") is not None]
            readings.append(
                WeatherReading(
                    date=day,
                    temperature_mean_c=sum(temperatures) / len(temperatures),
                    temperature_min_c=min(temperatures),
                    temperature_max_c=max(temperatures),
                    humidity_pct=sum(humidities) / len(humidities),
                    rainfall_mm=float(rain),
                    wind_speed_ms=(sum(winds) / len(winds)) if winds else None,
                    solar_radiation_mj_m2=None,
                    source="forecast" if day > today else "live_api",
                    provider="openweathermap",
                    is_forecast=day > today,
                )
            )
        return readings

    def current(self, latitude: float, longitude: float) -> WeatherReading:
        readings = self._to_daily(self._fetch(latitude, longitude))
        if not readings:
            raise WeatherUnavailableError("OpenWeatherMap returned no usable entries")
        return readings[0]

    def forecast(self, latitude: float, longitude: float, days: int = 5) -> list[WeatherReading]:
        return self._to_daily(self._fetch(latitude, longitude))[:days]


# --------------------------------------------------------------------------
class WeatherService:
    """The provider plus a small time-to-live cache.

    Providers rate-limit and cost money per call, and a dashboard refresh should
    not trigger a fresh request for weather that has not changed. The cache key
    rounds coordinates to about a kilometre, which is well inside the resolution
    of any of these products.
    """

    def __init__(self, provider: WeatherProvider | None = None) -> None:
        self._provider = provider or self._build_provider()
        self._cache: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _build_provider() -> WeatherProvider:
        name = (settings.weather_provider or "none").strip().lower()
        if name == "open_meteo":
            return OpenMeteoProvider()
        if name == "openweathermap":
            return OpenWeatherMapProvider(settings.weather_api_key)
        return NullProvider()

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def is_configured(self) -> bool:
        return not isinstance(self._provider, NullProvider)

    def _cached(self, key: str, producer) -> Any:  # type: ignore[no-untyped-def]
        now = time.time()
        with self._lock:
            hit = self._cache.get(key)
            if hit and now - hit[0] < settings.weather_cache_ttl_seconds:
                return hit[1]
        value = producer()
        with self._lock:
            self._cache[key] = (now, value)
        return value

    @staticmethod
    def _key(prefix: str, latitude: float, longitude: float, extra: str = "") -> str:
        return f"{prefix}:{latitude:.2f}:{longitude:.2f}:{extra}"

    def current(self, latitude: float, longitude: float) -> WeatherReading:
        return self._cached(
            self._key("current", latitude, longitude),
            lambda: self._provider.current(latitude, longitude),
        )

    def forecast(self, latitude: float, longitude: float, days: int = 7) -> list[WeatherReading]:
        return self._cached(
            self._key("forecast", latitude, longitude, str(days)),
            lambda: self._provider.forecast(latitude, longitude, days),
        )

    def forecast_rainfall_total(self, latitude: float, longitude: float, days: int = 3) -> float | None:
        """Rain expected over the next few days, or ``None`` if unavailable."""
        try:
            readings = self.forecast(latitude, longitude, days=days + 1)
        except WeatherUnavailableError:
            return None
        return float(sum(r.rainfall_mm for r in readings if r.is_forecast))

    def status(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "configured": self.is_configured,
            "cache_ttl_seconds": settings.weather_cache_ttl_seconds,
            "cached_entries": len(self._cache),
            "note": (
                "Live and forecast readings are tagged by source and are never "
                "mixed into model training without a separate, deliberate "
                "ingestion step."
            ),
        }

    def clear_cache(self) -> None:
        with self._lock:
            self._cache.clear()


weather_service = WeatherService()
