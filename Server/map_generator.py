#!/usr/bin/env python3
"""
Smart Dashboard Map Generator - Refactored Version.

A comprehensive map generation system for e-paper displays that creates location-based
maps with weather overlays, timezone information, and optimized formatting.

This is the main orchestration class that coordinates all the specialized modules.
"""

import os
from typing import Dict, Optional
from PIL import Image

# Import specialized modules
from data_providers import WeatherProvider, TimezoneProvider, LocationProvider
from image_composition import OverlayComposer
from utils import EpaperConverter
from map_providers.mapbox import get_mapbox_provider


class MapGenerator:
    """
    Main map generator class that orchestrates all components.
    
    Features:
    - Location-based map generation
    - Weather data integration
    - Timezone-aware local time display
    - E-paper format conversion
    - Coordinate caching
    - Cross-platform font support
    """
    
    def __init__(self, weather_api_key: str = None, cache_file: str = "locations_cache.json"):
        """
        Initialize the map generator with all required providers.

        Args:
            weather_api_key: OpenWeatherMap API key. If not provided,
                    will try to get it from OPENWEATHER_API_KEY environment variable
            cache_file: Path to JSON file for caching coordinates
        """
        # Initialize Mapbox provider
        self.mapbox = get_mapbox_provider()
        if not self.mapbox.is_available():
            raise ValueError("Mapbox API key is required. Please set MAPBOX_API_KEY environment variable.")

        # Initialize data providers
        weather_key = weather_api_key or os.getenv('OPENWEATHER_API_KEY')
        self.weather_provider = WeatherProvider(weather_key)
        self.timezone_provider = TimezoneProvider()
        self.location_provider = LocationProvider(cache_file)
        
        # Initialize image composition
        self.overlay_composer = OverlayComposer(final_width=480, final_height=800)
        
        # Initialize converter
        self.epaper_converter = EpaperConverter()

        # Create Maps folder if it doesn't exist
        self.maps_folder = "Maps"
        if not os.path.exists(self.maps_folder):
            os.makedirs(self.maps_folder)
            print(f"📁 Created {self.maps_folder} folder")

    def get_coordinates_from_location(self, city: str, country: str) -> tuple[float, float]:
        """
        Get coordinates (lat, lng) for a city and country.
        Uses the location provider for caching and geocoding.

        Args:
            city: City name
            country: Country name

        Returns:
            Tuple with (latitude, longitude)

        Raises:
            Exception: If location cannot be found or API error occurs
        """
        return self.location_provider.get_coordinates(city, country)

    def get_weather_data(self, lat: float, lng: float) -> Optional[Dict]:
        """
        Get current weather data for coordinates.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            Weather data dictionary or None if unavailable
        """
        return self.weather_provider.get_weather_data(lat, lng)

    def download_weather_icon(self, icon_code: str) -> Optional[Image.Image]:
        """
        Download weather icon from OpenWeatherMap.

        Args:
            icon_code: Weather icon code

        Returns:
            PIL Image or None if download fails
        """
        return self.weather_provider.download_weather_icon(icon_code)

    def get_local_datetime(self, city: str, country: str, lat: float, lng: float) -> tuple[str, str, str, str]:
        """
        Get local date and time for coordinates with caching.

        Args:
            city: City name
            country: Country name
            lat: Latitude
            lng: Longitude

        Returns:
            Tuple of (date_string, time_string, timezone_name, utc_offset)
        """
        try:
            # Check if timezone is cached for this location
            cached_timezone, cached_offset = self.location_provider.get_cached_timezone_data(city, country)
            
            # Get timezone information
            timezone_name, utc_offset = self.timezone_provider.get_timezone_for_location(
                city=city, 
                country=country, 
                lat=lat, 
                lng=lng,
                cached_timezone=cached_timezone,
                cached_offset=cached_offset
            )
            
            # Cache timezone data if not already cached
            if not cached_timezone:
                self.location_provider.cache_timezone_data(city, country, timezone_name, utc_offset)

            # Get formatted local time
            date_str, time_str = self.timezone_provider.get_local_datetime(timezone_name)

            return date_str, time_str, timezone_name, utc_offset

        except Exception as e:
            print(f"⚠️  Could not get local time: {e}")
            # Fallback to UTC
            from datetime import datetime
            utc_time = datetime.utcnow()
            date_str = utc_time.strftime("%d %B")
            time_str = utc_time.strftime("%H:%M")
            return date_str, time_str, "UTC", "±0"

    def generate_map_image(self, lat: float, lng: float, zoom: int = 12, style: str = 'default') -> Image.Image:
        """
        Generate map image using Mapbox provider.

        Args:
            lat: Latitude
            lng: Longitude
            zoom: Zoom level (1-20)
            style: Map style (default, satellite, blueprint, etc.)

        Returns:
            PIL Image object
        """
        return self.mapbox.generate_map_image(lat, lng, zoom, style)

    def download_map_by_location(self, city: str, country: str, zoom: int = 12, 
                                save_path: str = None, include_weather: bool = True) -> str:
        """
        Download and save map for a city and country with weather overlay.
        Uses cached coordinates if available, otherwise fetches and caches them.

        Args:
            city: City name
            country: Country name
            zoom: Zoom level
            save_path: Path to save image (optional)
            include_weather: Whether to include weather overlay

        Returns:
            Path of saved file
        """
        # Get coordinates from cache or API
        lat, lng = self.get_coordinates_from_location(city, country)

        # Get weather data if requested
        weather_data = None
        weather_icon = None
        if include_weather and self.weather_provider.is_available():
            weather_data = self.get_weather_data(lat, lng)
            if weather_data:
                weather_icon = self.download_weather_icon(weather_data['icon'])

        # Get local datetime
        date_str, time_str, timezone_name, utc_offset = self.get_local_datetime(city, country, lat, lng)

        # Generate base map using Mapbox
        print(f"🗺️  Generating map for {city}, {country} (zoom: {zoom})...")
        
        try:
            # Generate square image using Mapbox
            square_image = self.generate_map_image(lat, lng, zoom, style='default')

            # Crop to final size to avoid deformation
            final_image = self.overlay_composer.crop_to_final_size(square_image)

            # Add information overlay
            final_image = self.overlay_composer.add_info_overlay(
                final_image, city, country, lat, lng, date_str, time_str, weather_data, weather_icon
            )

            # Generate save path in Maps folder with City_Country format
            if not save_path:
                clean_city = city.replace(' ', '_').replace(',', '').replace('.', '')
                clean_country = country.replace(' ', '_').replace(',', '').replace('.', '')
                save_path = os.path.join(self.maps_folder, f"{clean_city}_{clean_country}.png")

            # Save image
            final_image.save(save_path, 'PNG', optimize=True)
            print(f"✅ Map saved to: {save_path} ({self.overlay_composer.final_width}x{self.overlay_composer.final_height}px)")

            # Generate C array and binary files for e-paper display
            c_path, bin_path = self.epaper_converter.convert_png_to_epaper(save_path)
            
            return save_path

        except Exception as e:
            raise Exception(f"Error generating map: {e}")

    def download_map_by_coordinates(self, lat: float, lng: float, zoom: int = 12, save_path: str = None) -> str:
        """
        Download and save map for specified coordinates.

        Args:
            lat: Latitude
            lng: Longitude
            zoom: Zoom level
            save_path: Path to save image (optional)

        Returns:
            Path of saved file
        """
        try:
            print(f"🗺️  Generating map for ({lat:.4f}, {lng:.4f}) with zoom: {zoom}...")

            # Generate square image using Mapbox
            square_image = self.generate_map_image(lat, lng, zoom, style='default')

            # Crop to final size to avoid deformation
            final_image = self.overlay_composer.crop_to_final_size(square_image)

            # Determine save path
            if not save_path:
                save_path = f"map_{lat:.4f}_{lng:.4f}_{zoom}.png"

            # Save image
            final_image.save(save_path, 'PNG', optimize=True)
            print(f"✅ Map saved to: {save_path} ({self.overlay_composer.final_width}x{self.overlay_composer.final_height}px)")

            # Generate C array and binary files for e-paper display
            c_path, bin_path = self.epaper_converter.convert_png_to_epaper(save_path)

            return save_path

        except Exception as e:
            raise Exception(f"Error generating map: {e}")

    def list_cached_locations(self) -> Dict:
        """
        Get all cached locations.

        Returns:
            Dictionary with cached locations
        """
        return self.location_provider.list_cached_locations()

    def clear_cache(self):
        """Clear all cached locations."""
        self.location_provider.clear_cache()


def main():
    """Main function to demonstrate the map generator usage."""
    print("🗺️  Enhanced Map Generator - 480x800px (Refactored Version)")
    print("=" * 70)

    # Check for Mapbox API key
    mapbox_provider = get_mapbox_provider()
    if not mapbox_provider.is_available():
        print("❌ Mapbox API key not found!")
        print("   Please set MAPBOX_API_KEY environment variable")
        print("   Get your FREE key at: https://account.mapbox.com/")
        return

    try:
        # Initialize generator with all providers
        map_gen = MapGenerator()

        # Test locations
        test_locations = [
            ("Vienna", "Austria")
        ]

        for city, country in test_locations:
            try:
                map_file = map_gen.download_map_by_location(city, country, zoom=11)
                print(f"✅ {city}, {country} map generated: {map_file}")
            except Exception as e:
                print(f"❌ Error generating {city}, {country} map: {e}")

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
