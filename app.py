"""Entry point for the open sensor dashboard."""

from __future__ import annotations

from sensor_dashboard.config import DEFAULT_LOCATION
from sensor_dashboard.gui import SensorDashboardApp
from sensor_dashboard.manager import SensorManager
from sensor_dashboard.sensors import (
    GravityStationSensor,
    MetNoLightningSensor,
    NOAASolarWindSensor,
    OpenMeteoWeatherSensor,
    SatNogsObservationSensor,
    USGSEarthquakeSensor,
)


def build_manager() -> SensorManager:
    location = DEFAULT_LOCATION
    sensors = [
        OpenMeteoWeatherSensor(location),
        MetNoLightningSensor(location),
        USGSEarthquakeSensor(),
        NOAASolarWindSensor(),
        GravityStationSensor(),
        SatNogsObservationSensor(),
    ]
    return SensorManager(sensors)


def main() -> None:
    manager = build_manager()
    app = SensorDashboardApp(manager)
    app.run()


if __name__ == "__main__":
    main()
