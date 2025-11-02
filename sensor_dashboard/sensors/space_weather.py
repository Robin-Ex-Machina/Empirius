"""Space weather observations from NOAA SWPC."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .base import Sensor, SensorReading, ensure_utc


class NOAASolarWindSensor(Sensor):
    """Retrieve near real-time solar wind plasma parameters."""

    def __init__(self, *, update_interval: timedelta | None = timedelta(minutes=5)) -> None:
        super().__init__(
            name="NOAA Solar Wind",
            source="https://services.swpc.noaa.gov/products/solar-wind/",
            category="astronomic",
            update_interval=update_interval,
        )

    async def fetch(self) -> SensorReading:
        payload = await self.request_json("https://services.swpc.noaa.gov/products/solar-wind/plasma-1-hour.json")
        if isinstance(payload, SensorReading):
            return payload
        if not isinstance(payload, list) or not payload:
            return SensorReading(
                timestamp=datetime.now(timezone.utc),
                values={},
                status="error",
                message="Unexpected response structure",
                raw=payload,
            )
        header, *rows = payload
        latest = rows[-1] if rows else []
        values = {key: latest[idx] if idx < len(latest) else None for idx, key in enumerate(header)}
        timestamp = ensure_utc(values.get("time_tag", datetime.now(timezone.utc))) if values else datetime.now(timezone.utc)
        display = {
            "Density (p/cc)": values.get("density"),
            "Speed (km/s)": values.get("speed"),
            "Temperature (K)": values.get("temperature"),
        }
        return SensorReading(timestamp=timestamp, values=display, raw=values)
