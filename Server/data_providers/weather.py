#!/usr/bin/env python3
"""
Weather Data Provider for Smart Dashboard Server.

Handles fetching weather data from OpenWeatherMap API and downloading weather icons.
"""

import requests
import io
from typing import Optional, Dict
from PIL import Image


class WeatherProvider:
    """
    Weather data provider using OpenWeatherMap API.
    
    Features:
    - Current weather data fetching
    - Weather icon downloading
    - Temperature in Celsius
    - Error handling and fallbacks
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize weather provider.
        
        Args:
            api_key: OpenWeatherMap API key. If None, weather features will be disabled.
        """
        self.api_key = api_key
        self.weather_url = "http://api.openweathermap.org/data/2.5/weather"
        self.weather_icon_url = "http://openweathermap.org/img/wn/{icon}@2x.png"
        
        if not self.api_key:
            print("⚠️  OpenWeatherMap API key not found. Weather info will be disabled.")
            print("   Set OPENWEATHER_API_KEY environment variable to enable weather data.")
    
    def is_available(self) -> bool:
        """Check if weather provider is available (has API key)."""
        return self.api_key is not None
    
    def get_weather_data(self, lat: float, lng: float) -> Optional[Dict]:
        """
        Get current weather data for coordinates.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            Weather data dictionary or None if unavailable
        """
        if not self.api_key:
            return None

        try:
            params = {
                'lat': lat,
                'lon': lng,
                'appid': self.api_key,
                'units': 'metric'  # Celsius
            }

            response = requests.get(self.weather_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            weather_info = {
                'temperature': round(data['main']['temp']),
                'description': data['weather'][0]['description'].title(),
                'icon': data['weather'][0]['icon'],
                'city_name': data['name'],
                'country_code': data['sys']['country']
            }

            print(f"🌤️  Weather: {weather_info['temperature']}°C, {weather_info['description']}")
            return weather_info

        except Exception as e:
            print(f"⚠️  Could not fetch weather data: {e}")
            return None

    def download_weather_icon(self, icon_code: str) -> Optional[Image.Image]:
        """
        Download weather icon from OpenWeatherMap.

        Args:
            icon_code: Weather icon code

        Returns:
            PIL Image or None if download fails
        """
        try:
            icon_url = self.weather_icon_url.format(icon=icon_code)
            response = requests.get(icon_url, timeout=10)
            response.raise_for_status()

            icon_image = Image.open(io.BytesIO(response.content))
            return icon_image

        except Exception as e:
            print(f"⚠️  Could not download weather icon: {e}")
            return None
