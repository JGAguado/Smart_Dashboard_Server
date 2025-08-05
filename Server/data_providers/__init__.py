"""
Data providers package for Smart Dashboard Server.

This package contains modules for fetching external data:
- weather: Weather data from OpenWeatherMap
- timezone: Timezone handling and UTC offset calculation
- location: Location geocoding and coordinate caching
"""

from .weather import WeatherProvider
from .timezone import TimezoneProvider
from .location import LocationProvider

__all__ = ['WeatherProvider', 'TimezoneProvider', 'LocationProvider']
