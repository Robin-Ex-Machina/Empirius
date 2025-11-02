"""Lightning detection data from MET Norway's Weather API."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from ..config import Location
from .base import Sensor, SensorReading, ensure_utc


class MetNoLightningSensor(Sensor):
    """Retrieve lightning strike summaries around a point of interest."""

    def __init__(
        self,
        location: Location,
        *,
        radius_km: int = 100,
        update_interval: timedelta | None = timedelta(minutes=1),
    ) -> None:
        super().__init__(
            name=f"MET Lightning ({location.name})",
            source="https://api.met.no/weatherapi/lightning/1.0/",
            category="lightning",
            update_interval=update_interval,
        )
        self._location = location
        self._radius = radius_km

    async def fetch(self) -> SensorReading:
        params = {
            "lat": self._location.latitude,
            "lon": self._location.longitude,
            "msl": self._location.altitude_m,
            "radius": self._radius,
        }
        headers = {"Accept": "application/json"}
        payload = await self.request_json("https://api.met.no/weatherapi/lightning/1.0/", params=params, headers=headers)
        if isinstance(payload, SensorReading):
            return payload
        data: Dict[str, Any] = payload.get("data", {})
        strikes: List[Dict[str, Any]] = []
        for strike in data.get("strikes", []):
            timestamp = strike.get("time")
            strikes.append(
                {
                    "time": ensure_utc(timestamp).isoformat() if timestamp else datetime.now(timezone.utc).isoformat(),
                    "lat": strike.get("lat"),
                    "lon": strike.get("lon"),
                    "peak_current": strike.get("peak_current"),
                }
            )
        meta = payload.get("meta", {})
        timestamp = ensure_utc(meta.get("last_observation", datetime.now(timezone.utc)))
        values = {"Strikes": strikes[:10], "Count": len(strikes)}
        return SensorReading(timestamp=timestamp, values=values, raw=payload)
