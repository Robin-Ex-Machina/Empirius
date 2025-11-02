"""Gravity observations from publicly shared gravimeter datasets."""

from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import Dict, List

from .base import Sensor, SensorReading, ensure_utc
from ..network import fetch_text


class GravityStationSensor(Sensor):
    """Fetch the latest gravity observation from the datahub.io sample dataset."""

    def __init__(self, *, update_interval: timedelta | None = timedelta(hours=1)) -> None:
        super().__init__(
            name="Global Gravity Stations",
            source="https://datahub.io/core/gravity",
            category="gravity",
            update_interval=update_interval,
        )

    async def fetch(self) -> SensorReading:
        csv_text = await fetch_text("https://datahub.io/core/gravity/r/gravity.csv")
        reader = csv.DictReader(StringIO(csv_text))
        rows: List[Dict[str, str]] = list(reader)
        if not rows:
            return SensorReading(
                timestamp=datetime.now(timezone.utc),
                values={},
                status="error",
                message="Dataset returned no rows",
            )
        latest = rows[-1]
        timestamp_value = latest.get("Date") or latest.get("date")
        timestamp = ensure_utc(timestamp_value) if timestamp_value else datetime.now(timezone.utc)
        values = {
            "Station": latest.get("Station"),
            "Country": latest.get("Country"),
            "Gravity (mGal)": latest.get("Gravity"),
            "Latitude": latest.get("Latitude"),
            "Longitude": latest.get("Longitude"),
        }
        return SensorReading(timestamp=timestamp, values=values, raw=latest)
