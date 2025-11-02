"""Seismic data from the USGS Earthquake Hazards Program."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from .base import Sensor, SensorReading, ensure_utc


class USGSEarthquakeSensor(Sensor):
    """Retrieve the most recent earthquakes above a magnitude threshold."""

    def __init__(self, *, min_magnitude: float = 2.5, update_interval: timedelta | None = timedelta(minutes=2)) -> None:
        super().__init__(
            name="USGS Earthquakes",
            source="https://earthquake.usgs.gov/",
            category="seismic",
            update_interval=update_interval,
        )
        self._min_magnitude = min_magnitude

    async def fetch(self) -> SensorReading:
        payload = await self.request_json("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson")
        if isinstance(payload, SensorReading):
            return payload
        features: List[Dict[str, Any]] = payload.get("features", [])
        earthquakes: List[Dict[str, Any]] = []
        for feature in features:
            props = feature.get("properties", {})
            magnitude = props.get("mag")
            if magnitude is None or magnitude < self._min_magnitude:
                continue
            time_ms = props.get("time")
            timestamp = ensure_utc(datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc)) if time_ms else datetime.now(timezone.utc)
            earthquakes.append(
                {
                    "time": timestamp.isoformat(),
                    "magnitude": magnitude,
                    "place": props.get("place"),
                    "url": props.get("url"),
                }
            )
        timestamp = ensure_utc(payload.get("metadata", {}).get("generated", datetime.now(timezone.utc)))
        values = {"Events": earthquakes[:5], "Count": len(earthquakes)}
        return SensorReading(timestamp=timestamp, values=values, raw=features)
