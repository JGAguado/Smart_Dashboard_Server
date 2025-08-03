import requests
import os
import json
from typing import Dict, Tuple, Optional
from PIL import Image
import io

class MapGenerator:
    def __init__(self, api_key: str = None, cache_file: str = "locations_cache.json"):
        """
        Initialize the map generator.

        Args:
            api_key: Google Maps API key. If not provided,
                    will try to get it from GOOGLE_MAPS_API_KEY environment variable
            cache_file: Path to JSON file for caching coordinates
        """
        self.api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.api_key:
            raise ValueError("Google Maps API key is required. Either provide it during initialization or set GOOGLE_MAPS_API_KEY environment variable.")

        self.cache_file = cache_file
        self.locations_cache = self._load_cache()

        # Predefined cities with coordinates and optimal zoom (lat, lng, zoom_level)
        self.cities = {
            'vienna': (48.2082, 16.3738, 11),      # Vienna metropolitan area
            'madrid': (40.4168, -3.7038, 10),     # Madrid metropolitan area
            'new_york': (40.7128, -74.0060, 10),  # NYC metropolitan area
            'tokyo': (35.6762, 139.6503, 10)      # Tokyo metropolitan area
        }

        # Image configuration - use square to avoid deformation
        self.square_size = 800  # Square size for download
        self.final_width = 480  # Final width after crop
        self.final_height = 800 # Final height after crop
        self.base_url = "https://maps.googleapis.com/maps/api/staticmap"
        self.geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"

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

    def get_coordinates_from_location(self, city: str, country: str) -> Tuple[float, float]:
        """
        Get coordinates (lat, lng) for a city and country.
        First checks cache, then uses Google Geocoding API if not cached.

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

        # If not cached, get from API
        print(f"🔍 Looking up coordinates for {city}, {country}...")
        address = f"{city}, {country}"

        params = {
            'address': address,
            'key': self.api_key
        }

        try:
            response = requests.get(self.geocoding_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data['status'] != 'OK':
                raise Exception(f"Geocoding API error: {data['status']}")

            if not data['results']:
                raise Exception(f"No results found for '{address}'")

            # Get the first result's location
            location = data['results'][0]['geometry']['location']
            lat = location['lat']
            lng = location['lng']

            # Cache the result
            self.locations_cache[cache_key] = {
                'lat': lat,
                'lng': lng,
                'city': city.title(),
                'country': country.title(),
                'formatted_address': data['results'][0]['formatted_address']
            }
            self._save_cache()

            print(f"📍 Found and cached coordinates for {city}, {country}: {lat:.4f}, {lng:.4f}")
            return lat, lng

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error during geocoding: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected response format from geocoding API: {e}")

    def get_city_info(self, city_name: str) -> Tuple[float, float, int]:
        """
        Get coordinates and recommended zoom for a predefined city.

        Args:
            city_name: Name of the city (vienna, madrid, new_york, tokyo)

        Returns:
            Tuple with (latitude, longitude, zoom)
        """
        city_name = city_name.lower().replace(' ', '_')
        if city_name in self.cities:
            return self.cities[city_name]
        else:
            raise ValueError(f"City '{city_name}' not found. Available cities: {list(self.cities.keys())}")

    def generate_map_url(self, lat: float, lng: float, zoom: int = 12, map_type: str = 'roadmap') -> str:
        """
        Generate URL for static map.

        Args:
            lat: Latitude
            lng: Longitude
            zoom: Zoom level (1-20)
            map_type: Map type (roadmap, satellite, hybrid, terrain)

        Returns:
            Static map URL
        """
        params = {
            'center': f"{lat},{lng}",
            'zoom': zoom,
            'size': f"{self.square_size}x{self.square_size}",  # Square to avoid deformation
            'maptype': map_type,
            'scale': 2,  # High resolution
            'format': 'png',
            'key': self.api_key,
            'style': [
                # Google Maps standard style - REMOVE ALL LABELS
                'feature:all|element:labels|visibility:off',
                'feature:administrative|element:labels|visibility:off',
                'feature:poi|element:labels|visibility:off',
                'feature:road|element:labels|visibility:off',
                'feature:transit|element:labels|visibility:off',

                # Landscape and background colors
                'feature:landscape|element:all|color:0xf2f2f2',
                'feature:landscape.natural|element:geometry|color:0xe8e8e8',

                # PARKS AND GREEN AREAS (GREEN)
                'feature:landscape.natural.landcover|element:geometry|color:0x8bc34a',
                'feature:poi.park|element:geometry|color:0x66bb6a',
                'feature:landscape.natural.terrain|element:geometry|color:0xa5d6a7',

                # WATER BODIES (BLUE)
                'feature:water|element:all|color:0x42a5f5',
                'feature:water|element:geometry|color:0x1976d2',

                # ROADS
                'feature:road|element:geometry|color:0xffffff',
                'feature:road|element:geometry.stroke|color:0xe0e0e0',
                'feature:road.highway|element:geometry|color:0xffc107',
                'feature:road.highway|element:geometry.stroke|color:0xff8f00',
                'feature:road.arterial|element:geometry|color:0xffffff',
                'feature:road.arterial|element:geometry.stroke|color:0xbdbdbd',
                'feature:road.local|element:geometry|color:0xffffff',
                'feature:road.local|element:geometry.stroke|color:0xe0e0e0',

                # Buildings and structures
                'feature:poi.business|element:geometry|color:0xeeeeee',
                'feature:poi.medical|element:geometry|color:0xff5722',
                'feature:poi.school|element:geometry|color:0x795548',

                # Urban areas
                'feature:landscape.man_made|element:geometry|color:0xf5f5f5',

                # LAND/SOIL (BROWN)
                'feature:landscape.natural.terrain|element:geometry|color:0x8d6e63',

                # Public transport
                'feature:transit|element:all|visibility:off'
            ]
        }

        # Build URL
        url = self.base_url + '?'
        url_params = []

        for key, value in params.items():
            if key == 'style':
                for style in value:
                    url_params.append(f"style={style}")
            else:
                url_params.append(f"{key}={value}")

        return url + '&'.join(url_params)

    def crop_to_final_size(self, image: Image.Image) -> Image.Image:
        """
        Crop square image to final size of 480x800px from center.

        Args:
            image: Square input image

        Returns:
            Cropped image at 480x800px
        """
        width, height = image.size

        # Calculate coordinates for centered crop
        left = (width - self.final_width) // 2
        top = (height - self.final_height) // 2
        right = left + self.final_width
        bottom = top + self.final_height

        # Crop image
        cropped = image.crop((left, top, right, bottom))
        return cropped

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
            url = self.generate_map_url(lat, lng, zoom)
            print(f"🗺️  Generating map for ({lat:.4f}, {lng:.4f}) with zoom: {zoom}...")

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Verify response contains an image
            if 'image' not in response.headers.get('content-type', ''):
                raise Exception("Response does not contain a valid image")

            # Process square image
            square_image = Image.open(io.BytesIO(response.content))

            # Crop to final size to avoid deformation
            final_image = self.crop_to_final_size(square_image)

            # Determine save path
            if not save_path:
                save_path = f"map_{lat:.4f}_{lng:.4f}_{zoom}.png"

            # Save image
            final_image.save(save_path, 'PNG', optimize=True)
            print(f"✅ Map saved to: {save_path} ({self.final_width}x{self.final_height}px)")

            return save_path

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")
        except Exception as e:
            raise Exception(f"Error generating map: {e}")

    def download_map_by_location(self, city: str, country: str, zoom: int = 12, save_path: str = None) -> str:
        """
        Download and save map for a city and country.
        Uses cached coordinates if available, otherwise fetches and caches them.

        Args:
            city: City name
            country: Country name
            zoom: Zoom level
            save_path: Path to save image (optional)

        Returns:
            Path of saved file
        """
        # Get coordinates from cache or API
        lat, lng = self.get_coordinates_from_location(city, country)

        # Generate map using coordinates
        if not save_path:
            # Clean filename
            clean_city = city.replace(' ', '_').replace(',', '')
            clean_country = country.replace(' ', '_').replace(',', '')
            save_path = f"map_{clean_city}_{clean_country}_{zoom}.png"

        return self.download_map_by_coordinates(lat, lng, zoom, save_path)

    def download_map_by_city(self, city: str, custom_zoom: int = None, save_path: str = None) -> str:
        """
        Download and save map for a predefined city.

        Args:
            city: Name of predefined city
            custom_zoom: Custom zoom level (optional)
            save_path: Path to save image (optional)

        Returns:
            Path of saved file
        """
        lat, lng, default_zoom = self.get_city_info(city)
        zoom = custom_zoom if custom_zoom is not None else default_zoom

        if not save_path:
            save_path = f"map_{city}_{zoom}.png"

        return self.download_map_by_coordinates(lat, lng, zoom, save_path)

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

    def generate_all_predefined_cities(self, custom_zoom: int = None) -> Dict[str, str]:
        """
        Generate maps for all predefined cities.

        Args:
            custom_zoom: Custom zoom level for all cities (optional)

        Returns:
            Dictionary with city: file_path
        """
        results = {}
        print(f"🌍 Generating maps for {len(self.cities)} predefined cities...")
        print(f"📐 Final size: {self.final_width}x{self.final_height}px")

        for city in self.cities.keys():
            try:
                file_path = self.download_map_by_city(city, custom_zoom)
                results[city] = file_path
            except Exception as e:
                print(f"❌ Error generating map for {city}: {e}")
                results[city] = None

        print(f"\n✅ Process completed. {len([r for r in results.values() if r])} maps generated.")
        return results


def main():
    """Main function to demonstrate the map generator usage."""
    print("🗺️  Enhanced Map Generator - 480x800px (no deformation)")
    print("=" * 65)

    # Check for API key
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("❌ Google Maps API key not found!")
        print("   Please set GOOGLE_MAPS_API_KEY environment variable")
        print("   or provide the key when initializing MapGenerator")
        return

    try:
        # Initialize generator
        map_gen = MapGenerator()

        print("\nPredefined cities with dynamic zoom:")
        for city, (lat, lng, zoom) in map_gen.cities.items():
            print(f"  • {city.title()}: {lat:.4f}, {lng:.4f} (zoom: {zoom})")

        print(f"\n📋 Map features:")
        print(f"  • Final size: 480x800px (no deformation)")
        print(f"  • No text/labels")
        print(f"  • Coordinates caching system")
        print(f"  • Standard Google Maps style")
        print(f"  • Parks in green, water in blue, land in brown")

        # Example of main workflow: city/country input
        print("\n" + "=" * 65)
        print("Example: Generating maps using city/country input...")
        print("=" * 65)

        # Test locations
        test_locations = [
            ("Paris", "France"),
            ("London", "UK"),
            ("Berlin", "Germany"),
            ("Paris", "France")  # This should use cache
        ]

        for city, country in test_locations:
            try:
                map_file = map_gen.download_map_by_location(city, country, zoom=11)
                print(f"✅ {city}, {country} map generated: {map_file}")
            except Exception as e:
                print(f"❌ Error generating {city}, {country} map: {e}")

        # Show cache status
        print(f"\n📊 Cache now contains {len(map_gen.list_cached_locations())} locations")

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
