"""Weather sensors powered by the Open-Meteo API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from ..config import Location
from .base import Sensor, SensorReading, ensure_utc


@dataclass
class WeatherFields:
    """Container for weather-related metrics returned by Open-Meteo."""

    temperature_c: float | None
    pressure_hpa: float | None
    rain_mm: float | None

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "WeatherFields":
        return cls(
            temperature_c=payload.get("temperature_2m"),
            pressure_hpa=payload.get("pressure_msl"),
            rain_mm=payload.get("rain"),
        )


class OpenMeteoWeatherSensor(Sensor):
    """Current temperature, pressure, and precipitation for a location."""

    def __init__(self, location: Location, *, update_interval: timedelta | None = timedelta(minutes=5)) -> None:
        super().__init__(
            name=f"Open-Meteo Weather ({location.name})",
            source="https://open-meteo.com/",
            category="weather",
            update_interval=update_interval,
        )
        self._location = location

    async def fetch(self) -> SensorReading:
        params = {
            "latitude": self._location.latitude,
            "longitude": self._location.longitude,
            "current": "temperature_2m,pressure_msl,rain",
        }
        payload = await self.request_json("https://api.open-meteo.com/v1/forecast", params=params)
        if isinstance(payload, SensorReading):
            return payload
        current = payload.get("current", {})
        weather = WeatherFields.from_payload(current)
        timestamp_raw = current.get("time")
        if timestamp_raw:
            timestamp = ensure_utc(timestamp_raw)
        else:
            timestamp = datetime.now(timezone.utc)
        values = {
            "Temperature (°C)": weather.temperature_c,
            "Pressure (hPa)": weather.pressure_hpa,
            "Rain (mm)": weather.rain_mm,
        }
        return SensorReading(timestamp=timestamp, values=values, raw=current)
