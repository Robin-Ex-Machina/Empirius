"""Gravity observations from publicly shared gravimeter datasets."""

from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import Dict, List, Optional

from .base import Sensor, SensorReading, ensure_utc
from ..network import NetworkError, fetch_json, fetch_text


class GravityStationSensor(Sensor):
    """Fetch the latest gravity observation from the datahub.io sample dataset."""

    def __init__(self, *, update_interval: timedelta | None = timedelta(hours=1)) -> None:
        super().__init__(
            name="Global Gravity Stations",
            source="https://datahub.io/core/gravity",
            category="gravity",
            update_interval=update_interval,
        )

    async def _resolve_dataset_url(self) -> Optional[str]:
        """Resolve the canonical CSV download URL from the datapackage metadata."""

        try:
            metadata = await fetch_json("https://datahub.io/core/gravity/datapackage.json")
        except NetworkError:
            return None

        resources = metadata.get("resources") if isinstance(metadata, dict) else None
        if not isinstance(resources, list):
            return None

        for resource in resources:
            if not isinstance(resource, dict):
                continue
            if resource.get("format", "").lower() != "csv":
                continue
            path = resource.get("path")
            if not isinstance(path, str) or not path:
                continue
            if path.startswith("http"):
                return path
            # Datahub stores archived resources under pkgstore
            return f"https://pkgstore.datahub.io/core/gravity/{path.lstrip('/')}"
        return None

    async def fetch(self) -> SensorReading:
        dataset_url = await self._resolve_dataset_url()
        if dataset_url is None:
            return SensorReading(
                timestamp=datetime.now(timezone.utc),
                values={},
                status="error",
                message="Gravity dataset metadata unavailable",
            )

        try:
            csv_text = await fetch_text(dataset_url)
        except NetworkError as exc:
            return SensorReading(
                timestamp=datetime.now(timezone.utc),
                values={},
                status="error",
                message=f"Failed to download gravity dataset: {exc}",
            )
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
