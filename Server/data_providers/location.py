#!/usr/bin/env python3
"""
Location Provider for Smart Dashboard Server.

Handles location geocoding, coordinate caching, and location data management.
"""

import json
import os
from typing import Dict, Tuple
from map_providers.mapbox import get_mapbox_provider


class LocationProvider:
    """
    Location provider for geocoding and coordinate caching.
    
    Features:
    - Address to coordinates conversion using Mapbox
    - Local JSON file caching
    - Cache management (add, remove, clear)
    - Timezone and UTC offset caching
    """
    
    def __init__(self, cache_file: str = "locations_cache.json"):
        """
        Initialize location provider.
        
        Args:
            cache_file: Path to JSON file for caching coordinates
        """
        self.cache_file = cache_file
        self.locations_cache = self._load_cache()
        
        # Initialize Mapbox provider
        self.mapbox = get_mapbox_provider()
        if not self.mapbox.is_available():
            raise ValueError("Mapbox API key is required. Please set MAPBOX_API_KEY environment variable.")
    
    def _load_cache(self) -> Dict:
        """Load coordinates cache from JSON file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    print(f"📂 Loaded {len(cache)} cached locations from {self.cache_file}")
                    return cache
            else:
                print(f"📂 Creating new cache file: {self.cache_file}")
                return {}
        except Exception as e:
            print(f"⚠️  Error loading cache file: {e}. Starting with empty cache.")
            return {}

    def _save_cache(self):
        """Save coordinates cache to JSON file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.locations_cache, f, indent=2, ensure_ascii=False)
            print(f"💾 Cache saved with {len(self.locations_cache)} locations")
        except Exception as e:
            print(f"⚠️  Error saving cache: {e}")

    def _get_cache_key(self, city: str, country: str) -> str:
        """Generate cache key for city/country combination."""
        return f"{city.lower().strip()}, {country.lower().strip()}"

    def get_coordinates(self, city: str, country: str) -> Tuple[float, float]:
        """
        Get coordinates (lat, lng) for a city and country.
        First checks cache, then uses Mapbox Geocoding API if not cached.

        Args:
            city: City name
            country: Country name

        Returns:
            Tuple with (latitude, longitude)

        Raises:
            Exception: If location cannot be found or API error occurs
        """
        cache_key = self._get_cache_key(city, country)

        # Check if coordinates are cached
        if cache_key in self.locations_cache:
            cached_data = self.locations_cache[cache_key]
            lat, lng = cached_data['lat'], cached_data['lng']
            print(f"📍 Found cached coordinates for {city}, {country}: {lat:.4f}, {lng:.4f}")
            return lat, lng

        # If not cached, get from Mapbox API
        print(f"🔍 Looking up coordinates for {city}, {country}...")
        
        try:
            lat, lng = self.mapbox.get_coordinates(city, country)

            # Cache the result
            self.locations_cache[cache_key] = {
                'lat': lat,
                'lng': lng,
                'city': city.title(),
                'country': country.title(),
                'formatted_address': f"{city.title()}, {country.title()}"
            }
            self._save_cache()

            print(f"📍 Found and cached coordinates for {city}, {country}: {lat:.4f}, {lng:.4f}")
            return lat, lng

        except Exception as e:
            raise Exception(f"Mapbox geocoding error: {e}")
    
    def get_cached_timezone_data(self, city: str, country: str) -> Tuple[str, str]:
        """
        Get cached timezone and UTC offset for a location.
        
        Args:
            city: City name
            country: Country name
            
        Returns:
            Tuple of (timezone_name, utc_offset) or (None, None) if not cached
        """
        cache_key = self._get_cache_key(city, country)
        if cache_key in self.locations_cache:
            cached_data = self.locations_cache[cache_key]
            timezone = cached_data.get('timezone')
            utc_offset = cached_data.get('utc_offset')
            if timezone and utc_offset:
                return timezone, utc_offset
        return None, None
    
    def cache_timezone_data(self, city: str, country: str, timezone_name: str, utc_offset: str):
        """
        Cache timezone data for a location.
        
        Args:
            city: City name
            country: Country name
            timezone_name: Timezone name (e.g., 'Europe/Vienna')
            utc_offset: UTC offset string (e.g., '+1', '-5', '±0')
        """
        cache_key = self._get_cache_key(city, country)
        if cache_key in self.locations_cache:
            self.locations_cache[cache_key]['timezone'] = timezone_name
            self.locations_cache[cache_key]['utc_offset'] = utc_offset
            self._save_cache()
    
    def list_cached_locations(self) -> Dict:
        """
        Get all cached locations.

        Returns:
            Dictionary with cached locations
        """
        return self.locations_cache.copy()

    def clear_cache(self):
        """Clear all cached locations."""
        self.locations_cache.clear()
        self._save_cache()
        print("🗑️  Cache cleared")
