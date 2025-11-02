"""Base sensor definitions."""

from __future__ import annotations

import abc
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Mapping

from ..config import DEFAULT_POLL_INTERVAL
from ..network import NetworkError, fetch_json


@dataclass
class SensorReading:
    """Normalized container for sensor data."""

    timestamp: datetime
    values: Dict[str, Any]
    raw: Any | None = None
    status: str = "ok"
    message: str | None = None


class Sensor(abc.ABC):
    """Abstract base class for all sensors."""

    name: str
    source: str
    category: str
    update_interval: timedelta

    def __init__(
        self,
        *,
        name: str,
        source: str,
        category: str,
        update_interval: timedelta | None = None,
    ) -> None:
        self.name = name
        self.source = source
        self.category = category
        self.update_interval = update_interval or DEFAULT_POLL_INTERVAL

    async def request_json(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float = 30.0,
    ) -> Any:
        """Wrapper around :func:`fetch_json` that normalizes network errors."""

        try:
            return await fetch_json(url, params=params, headers=headers, timeout=timeout)
        except NetworkError as exc:  # pragma: no cover - depends on network
            return SensorReading(
                timestamp=datetime.now(timezone.utc),
                values={},
                status="error",
                message=f"Network error: {exc}",
            )

    @abc.abstractmethod
    async def fetch(self) -> SensorReading:
        """Retrieve the latest reading from the sensor."""


def ensure_utc(timestamp: datetime | str | int | float) -> datetime:
    """Ensure that *timestamp* is timezone-aware and normalized to UTC."""

    if isinstance(timestamp, datetime):
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)
        return timestamp.astimezone(timezone.utc)
    if isinstance(timestamp, (int, float)):
        divisor = 1000 if timestamp > 10_000_000_000 else 1
        return datetime.fromtimestamp(timestamp / divisor, tz=timezone.utc)
    iso = timestamp.replace("Z", "+00:00")
    return datetime.fromisoformat(iso).astimezone(timezone.utc)
