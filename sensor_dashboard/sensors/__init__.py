"""Available sensor implementations."""

from .base import Sensor, SensorReading
from .open_meteo import OpenMeteoWeatherSensor
from .usgs import USGSEarthquakeSensor
from .lightning import MetNoLightningSensor
from .space_weather import NOAASolarWindSensor
from .gravity import GravityStationSensor
from .satnogs import SatNogsObservationSensor

__all__ = [
    "Sensor",
    "SensorReading",
    "OpenMeteoWeatherSensor",
    "USGSEarthquakeSensor",
    "MetNoLightningSensor",
    "NOAASolarWindSensor",
    "GravityStationSensor",
    "SatNogsObservationSensor",
]
