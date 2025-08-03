#!/usr/bin/env python3
"""
Test script for the improved Smart Dashboard Map Generator
Tests timezone functionality and caching without requiring API keys
"""

import json
import os
from main import MapGenerator

def test_timezone_functionality():
    """Test the improved timezone functionality"""
    print("🧪 Testing Smart Dashboard Map Generator")
    print("=" * 50)
    
    # Initialize without API keys for testing
    try:
        map_gen = MapGenerator(api_key="test", weather_api_key="test")
    except ValueError:
        print("✅ Proper API key validation working")
        # Create a minimal version for testing
        map_gen = MapGenerator.__new__(MapGenerator)
        map_gen.cache_file = "test_cache.json"
        map_gen.locations_cache = {}
        
        # Initialize timezone functionality
        from tzwhere import tzwhere
        try:
            map_gen.tz = tzwhere.tzwhere()
            print("✅ tzwhere timezone finder initialized")
        except Exception as e:
            print(f"⚠️  tzwhere initialization failed: {e}")
            map_gen.tz = None
    
    # Test coordinates for major cities
    test_coords = [
        ("Vienna", "Austria", 48.2082, 16.3738),
        ("Tokyo", "Japan", 35.6762, 139.6503),
        ("New York", "USA", 40.7128, -74.0060),
        ("Sydney", "Australia", -33.8688, 151.2093),
    ]
    
    print("\n🌍 Testing timezone detection:")
    print("-" * 40)
    
    for city, country, lat, lng in test_coords:
        try:
            timezone_name, utc_offset = map_gen.get_timezone_for_coordinates(
                lat, lng, city, country
            )
            print(f"📍 {city}, {country}:")
            print(f"   Coordinates: {lat:.4f}, {lng:.4f}")
            print(f"   Timezone: {timezone_name}")
            print(f"   UTC Offset: {utc_offset}")
            print()
        except Exception as e:
            print(f"❌ Error testing {city}: {e}")
    
    # Test cache functionality
    print("💾 Testing cache functionality:")
    print("-" * 40)
    
    # Create a test cache entry
    test_cache = {
        "vienna, austria": {
            "lat": 48.2082,
            "lng": 16.3738,
            "city": "Vienna",
            "country": "Austria",
            "formatted_address": "Vienna, Austria",
            "timezone": "Europe/Vienna",
            "utc_offset": "+1"
        }
    }
    
    # Test cache key generation
    cache_key = map_gen._get_cache_key("Vienna", "Austria")
    print(f"✅ Cache key for 'Vienna, Austria': '{cache_key}'")
    
    # Simulate cache lookup
    map_gen.locations_cache = test_cache
    timezone_name, utc_offset = map_gen.get_timezone_for_coordinates(
        48.2082, 16.3738, "Vienna", "Austria"
    )
    print(f"✅ Cache lookup result: {timezone_name} (UTC{utc_offset})")
    
    print("\n🎉 Testing completed!")
    print("\nℹ️  To run with real API keys:")
    print("   1. Set GOOGLE_MAPS_API_KEY environment variable")
    print("   2. Set OPENWEATHER_API_KEY environment variable (optional)")
    print("   3. Run: python main.py")

if __name__ == "__main__":
    test_timezone_functionality()
