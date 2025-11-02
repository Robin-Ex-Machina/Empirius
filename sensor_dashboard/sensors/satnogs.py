"""SDR observations from the SatNOGS network."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from .base import Sensor, SensorReading, ensure_utc


class SatNogsObservationSensor(Sensor):
    """Fetch recent radio observations collected by SatNOGS ground stations."""

    def __init__(self, *, status: str = "good", limit: int = 5, update_interval: timedelta | None = timedelta(minutes=10)) -> None:
        super().__init__(
            name="SatNOGS Observations",
            source="https://db.satnogs.org/api/observations/",
            category="sdr",
            update_interval=update_interval,
        )
        self._status = status
        self._limit = limit

    async def fetch(self) -> SensorReading:
        params = {"status": self._status, "limit": self._limit, "ordering": "-start"}
        payload = await self.request_json("https://db.satnogs.org/api/observations/", params=params)
        if isinstance(payload, SensorReading):
            return payload
        if not isinstance(payload, list):
            return SensorReading(
                timestamp=datetime.now(timezone.utc),
                values={},
                status="error",
                message="Unexpected response structure",
                raw=payload,
            )
        observations: List[Dict[str, Any]] = []
        for item in payload:
            start = ensure_utc(item.get("start", datetime.now(timezone.utc)))
            end = ensure_utc(item.get("end", start))
            observations.append(
                {
                    "id": item.get("id"),
                    "satellite": item.get("satellite"),
                    "ground_station": item.get("ground_station"),
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "frequency": item.get("frequency"),
                    "waterfall": item.get("waterfall"),
                }
            )
        timestamp = ensure_utc(observations[0]["start"]) if observations else datetime.now(timezone.utc)
        values = {"Observations": observations}
        return SensorReading(timestamp=timestamp, values=values, raw=payload)
