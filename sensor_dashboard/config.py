"""Configuration for the sensor dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


USER_AGENT = "EmpiriusSensorDashboard/0.1 (+https://example.com/contact)"
DEFAULT_POLL_INTERVAL = timedelta(minutes=5)
GUI_REFRESH_INTERVAL_MS = 1000


@dataclass(frozen=True)
class Location:
    """Simple geographic location description."""

    name: str
    latitude: float
    longitude: float
    altitude_m: float = 0.0


DEFAULT_LOCATION = Location(name="New York City", latitude=40.7128, longitude=-74.0060, altitude_m=10)
