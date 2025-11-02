"""Sensor polling manager built on :mod:`asyncio`."""

from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from queue import Queue
from typing import Dict, Iterable, Optional

from .sensors import Sensor, SensorReading

LOGGER = logging.getLogger(__name__)


@dataclass
class SensorUpdate:
    """A single sensor update event propagated to the UI."""

    sensor: Sensor
    reading: SensorReading


class SensorManager:
    """Manage background polling tasks for sensors."""

    def __init__(self, sensors: Iterable[Sensor]) -> None:
        self._sensors = list(sensors)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._tasks: Dict[Sensor, asyncio.Task[None]] = {}
        self._queue: Queue[SensorUpdate] | None = None

    @property
    def queue(self) -> Queue[SensorUpdate]:
        if self._queue is None:
            raise RuntimeError("Manager not started")
        return self._queue

    def start(self) -> None:
        if self._loop is not None:
            return
        self._loop = asyncio.new_event_loop()
        self._queue = Queue()

        def runner() -> None:
            asyncio.set_event_loop(self._loop)
            for sensor in self._sensors:
                task = self._loop.create_task(self._poll_sensor(sensor))
                self._tasks[sensor] = task
            try:
                self._loop.run_forever()
            finally:
                for task in self._tasks.values():
                    task.cancel()
                self._loop.run_until_complete(asyncio.gather(*self._tasks.values(), return_exceptions=True))
                self._loop.close()

        self._thread = threading.Thread(target=runner, name="SensorManager", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._loop is None:
            return
        self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread is not None:
            self._thread.join()
        self._loop = None
        self._thread = None
        self._tasks.clear()

    async def _poll_sensor(self, sensor: Sensor) -> None:
        assert self._queue is not None
        interval = max(sensor.update_interval.total_seconds(), 1.0)
        while True:
            try:
                reading = await sensor.fetch()
            except Exception as exc:  # pragma: no cover - defensive against buggy sensors
                LOGGER.exception("Failed to fetch data for %s", sensor.name)
                reading = SensorReading(
                    timestamp=datetime.now(timezone.utc),
                    values={},
                    status="error",
                    message=str(exc),
                )
            self.queue.put_nowait(SensorUpdate(sensor=sensor, reading=reading))
            await asyncio.sleep(interval)
