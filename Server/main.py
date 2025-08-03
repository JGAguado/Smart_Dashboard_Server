import requests
import os
import json
from typing import Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
import pytz
import sys
from png_to_epaper_converter import convert_png_to_c_file

# Simple timezone mapping for common cities/countries
TIMEZONE_MAPPING = {
    # European cities
    'vienna': 'Europe/Vienna',
    'austria': 'Europe/Vienna',
    'berlin': 'Europe/Berlin', 
    'germany': 'Europe/Berlin',
    'paris': 'Europe/Paris',
    'france': 'Europe/Paris',
    'london': 'Europe/London',
    'uk': 'Europe/London',
    'united kingdom': 'Europe/London',
    'madrid': 'Europe/Madrid',
    'spain': 'Europe/Madrid',
    'rome': 'Europe/Rome',
    'italy': 'Europe/Rome',
    
    # American cities
    'new york': 'America/New_York',
    'usa': 'America/New_York',
    'united states': 'America/New_York',
    'los angeles': 'America/Los_Angeles',
    'chicago': 'America/Chicago',
    'miami': 'America/New_York',
    
    # Asian cities
    'tokyo': 'Asia/Tokyo',
    'japan': 'Asia/Tokyo',
    'beijing': 'Asia/Shanghai',
    'china': 'Asia/Shanghai',
    'seoul': 'Asia/Seoul',
    'south korea': 'Asia/Seoul',
    'mumbai': 'Asia/Kolkata',
    'india': 'Asia/Kolkata',
    
    # Other cities
    'sydney': 'Australia/Sydney',
    'australia': 'Australia/Sydney',
    'moscow': 'Europe/Moscow',
    'russia': 'Europe/Moscow',
    'cairo': 'Africa/Cairo',
    'egypt': 'Africa/Cairo',
    'dubai': 'Asia/Dubai',
    'uae': 'Asia/Dubai',
}

def estimate_timezone_from_coordinates(lat: float, lng: float) -> Tuple[str, str]:
    """
    Estimate timezone from coordinates using longitude-based calculation.
    This is a fallback method when no mapping is available.
    """
    # Basic estimation: UTC offset = longitude / 15
    utc_offset_hours = round(lng / 15)
    utc_offset_hours = max(-12, min(12, utc_offset_hours))  # Clamp to valid range
    
    if utc_offset_hours == 0:
        timezone_name = "UTC"
        offset_str = "±0"
    else:
        # Create a generic timezone name
        timezone_name = f"Etc/GMT{-utc_offset_hours:+d}"
        offset_str = f"{utc_offset_hours:+d}" if utc_offset_hours != 0 else "±0"
    
    return timezone_name, offset_str

class MapGenerator:
    def __init__(self, api_key: str = None, weather_api_key: str = None, cache_file: str = "locations_cache.json"):
        """
        Initialize the map generator.

        Args:
            api_key: Google Maps API key. If not provided,
                    will try to get it from GOOGLE_MAPS_API_KEY environment variable
            weather_api_key: OpenWeatherMap API key. If not provided,
                    will try to get it from OPENWEATHER_API_KEY environment variable
            cache_file: Path to JSON file for caching coordinates
        """
        self.api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        self.weather_api_key = weather_api_key or os.getenv('OPENWEATHER_API_KEY')

        if not self.api_key:
            raise ValueError("Google Maps API key is required. Either provide it during initialization or set GOOGLE_MAPS_API_KEY environment variable.")

        if not self.weather_api_key:
            print("⚠️  OpenWeatherMap API key not found. Weather info will be disabled.")
            print("   Set OPENWEATHER_API_KEY environment variable to enable weather data.")

        self.cache_file = cache_file
        self.locations_cache = self._load_cache()

        # Setup fonts for cross-platform compatibility
        self.font_path = self._setup_fonts()

        # Create Maps folder if it doesn't exist
        self.maps_folder = "Maps"
        if not os.path.exists(self.maps_folder):
            os.makedirs(self.maps_folder)
            print(f"📁 Created {self.maps_folder} folder")


        # Image configuration - use square to avoid deformation
        self.square_size = 800  # Square size for download
        self.final_width = 480  # Final width after crop
        self.final_height = 800 # Final height after crop
        self.base_url = "https://maps.googleapis.com/maps/api/staticmap"
        self.geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.weather_url = "http://api.openweathermap.org/data/2.5/weather"
        self.weather_icon_url = "http://openweathermap.org/img/wn/{icon}@2x.png"

    def _setup_fonts(self) -> str:
        """
        Setup Quicksand font for cross-platform compatibility.
        Returns path to the font file.
        """
        fonts_dir = "fonts"
        os.makedirs(fonts_dir, exist_ok=True)
        
        # Check for the manually added Quicksand variable font
        font_file = os.path.join(fonts_dir, "Quicksand-VariableFont_wght.ttf")
        if os.path.exists(font_file):
            print(f"✅ Using Quicksand font (Bold): {font_file}")
            return font_file
        
        # If font is not found, return None and use system fonts
        print("⚠️ Quicksand font not found in fonts folder")
        print("🔄 Will use system fonts as fallback")
        return None

    def _get_font(self, size: int):
        """
        Get font with specified size and bold weight, with fallback to system fonts.
        """
        try:
            if self.font_path and os.path.exists(self.font_path):
                # For variable fonts, specify a bolder weight (700 = Bold)
                # Quicksand variable font supports weights from 300 to 700
                try:
                    # Load font with bold weight (700)
                    font = ImageFont.truetype(self.font_path, size)
                    # For variable fonts, we can set font variations
                    if hasattr(font, 'set_variation_by_axes'):
                        font.set_variation_by_axes([700])  # Bold weight
                    elif hasattr(font, 'set_variation_by_name'):
                        font.set_variation_by_name(weight=700)
                    return font
                except:
                    # Fallback to regular loading if variation setting fails
                    return ImageFont.truetype(self.font_path, size)
        except Exception as e:
            print(f"⚠️ Could not load Quicksand font: {e}")
        
        # Fallback fonts for different operating systems - prioritize bold versions
        fallback_fonts = [
            # Windows bold fonts
            "C:/Windows/Fonts/arialbd.ttf",  # Arial Bold
            "C:/Windows/Fonts/arial.ttf",
            "arialbd.ttf", 
            "arial.ttf",
            "Arial.ttf",
            # Linux bold fonts
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "DejaVuSans-Bold.ttf",
            "DejaVuSans.ttf",
            "LiberationSans-Bold.ttf",
            "LiberationSans-Regular.ttf",
            "FreeSans.ttf",
            # Mac bold fonts
            "/System/Library/Fonts/Arial Bold.ttf",
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        
        for font_name in fallback_fonts:
            try:
                return ImageFont.truetype(font_name, size)
            except:
                continue
        
        # Final fallback to default font
        print(f"⚠️ Using default font for size {size}")
        return ImageFont.load_default()

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

    def get_weather_data(self, lat: float, lng: float) -> Optional[Dict]:
        """
        Get current weather data for coordinates.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            Weather data dictionary or None if unavailable
        """
        if not self.weather_api_key:
            return None

        try:
            params = {
                'lat': lat,
                'lon': lng,
                'appid': self.weather_api_key,
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
            print(f"�������️  Could not download weather icon: {e}")
            return None

    def get_timezone_for_coordinates(self, lat: float, lng: float, city: str = None, country: str = None) -> Tuple[str, str]:
        """
        Get timezone and UTC offset for coordinates.
        First checks cache if city/country provided, then uses mapping or estimation.

        Args:
            lat: Latitude
            lng: Longitude
            city: City name (optional, for cache lookup)
            country: Country name (optional, for cache lookup)

        Returns:
            Tuple of (timezone_name, utc_offset_string)
        """
        # Check cache first if city and country are provided
        if city and country:
            cache_key = self._get_cache_key(city, country)
            if cache_key in self.locations_cache:
                cached_data = self.locations_cache[cache_key]
                if 'timezone' in cached_data and 'utc_offset' in cached_data:
                    timezone_name = cached_data['timezone']
                    utc_offset = cached_data['utc_offset']
                    print(f"🕐 Found cached timezone: {timezone_name} (UTC{utc_offset})")
                    return timezone_name, utc_offset

        try:
            # Try to find timezone using city/country mapping
            timezone_name = None
            
            if city and country:
                # Check city first, then country
                city_lower = city.lower().strip()
                country_lower = country.lower().strip()
                
                if city_lower in TIMEZONE_MAPPING:
                    timezone_name = TIMEZONE_MAPPING[city_lower]
                elif country_lower in TIMEZONE_MAPPING:
                    timezone_name = TIMEZONE_MAPPING[country_lower]

            # If no mapping found, estimate from coordinates
            if timezone_name is None:
                timezone_name, offset_str = estimate_timezone_from_coordinates(lat, lng)
                print(f"⚠️  Using estimated timezone based on coordinates: {timezone_name} (UTC{offset_str})")
                return timezone_name, offset_str

            # Calculate UTC offset using the mapped timezone
            try:
                # Use pytz as primary method (more reliable)
                timezone = pytz.timezone(timezone_name)
                now = datetime.now(timezone)

                # Get UTC offset in seconds and convert to hours
                utc_offset_seconds = now.utcoffset().total_seconds()
                utc_offset_hours = int(utc_offset_seconds / 3600)

                # Format offset string
                if utc_offset_hours == 0:
                    offset_str = "±0"
                elif utc_offset_hours > 0:
                    offset_str = f"+{utc_offset_hours}"
                else:
                    offset_str = str(utc_offset_hours)

                # Cache the result if city/country provided
                if city and country:
                    cache_key = self._get_cache_key(city, country)
                    if cache_key in self.locations_cache:
                        self.locations_cache[cache_key]['timezone'] = timezone_name
                        self.locations_cache[cache_key]['utc_offset'] = offset_str
                        self._save_cache()

                print(f"🕐 Timezone determined: {timezone_name} (UTC{offset_str})")
                return timezone_name, offset_str

            except Exception as e:
                print(f"⚠️  Error calculating offset for {timezone_name}: {e}")
                # Fallback to coordinate estimation
                return estimate_timezone_from_coordinates(lat, lng)

        except Exception as e:
            print(f"⚠️  Error determining timezone: {e}")
            return estimate_timezone_from_coordinates(lat, lng)

    def get_local_datetime(self, city: str, country: str, lat: float, lng: float) -> Tuple[str, str, str, str]:
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
            cache_key = self._get_cache_key(city, country)
            if cache_key in self.locations_cache and 'timezone' in self.locations_cache[cache_key]:
                timezone_name = self.locations_cache[cache_key]['timezone']
                utc_offset = self.locations_cache[cache_key].get('utc_offset', '±0')
            else:
                timezone_name, utc_offset = self.get_timezone_for_coordinates(lat, lng, city, country)

            # Use pytz for timezone handling
            timezone = pytz.timezone(timezone_name)
            local_time = datetime.now(timezone)

            # Format: "03 August" instead of "03/01/2025"
            date_str = local_time.strftime("%d %B")
            time_str = local_time.strftime("%H:%M")

            return date_str, time_str, timezone_name, utc_offset

        except Exception as e:
            print(f"⚠️  Could not get local time: {e}")
            # Fallback to UTC
            utc_time = datetime.utcnow()
            date_str = utc_time.strftime("%d %B")
            time_str = utc_time.strftime("%H:%M")
            return date_str, time_str, "UTC", "±0"

    def generate_map_url(self, lat: float, lng: float, zoom: int = 12, map_type: str = 'roadmap') -> str:
        """
        Generate URL for static map with enhanced styling including better building contrast.

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
                # REMOVE ALL LABELS
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

                # ROADS (basic colors - traffic overlay not available in static maps)
                'feature:road|element:geometry|color:0xffffff',
                'feature:road|element:geometry.stroke|color:0xe0e0e0',
                'feature:road.highway|element:geometry|color:0xffc107',
                'feature:road.highway|element:geometry.stroke|color:0xff8f00',
                'feature:road.arterial|element:geometry|color:0xffffff',
                'feature:road.arterial|element:geometry.stroke|color:0xbdbdbd',
                'feature:road.local|element:geometry|color:0xffffff',
                'feature:road.local|element:geometry.stroke|color:0xe0e0e0',

                # BUILDINGS WITH HIGH CONTRAST GRAY TONES
                # General urban/man-made areas - Very light gray
                'feature:landscape.man_made|element:geometry|color:0xf8f8f8',

                # Low-density residential - Light gray
                'feature:poi.business|element:geometry|color:0xdddddd',

                # Commercial/office buildings - Medium gray
                'feature:poi.government|element:geometry|color:0xbbbbbb',
                'feature:poi.medical|element:geometry|color:0xaaaaaa',

                # Important/institutional buildings - Dark gray
                'feature:poi.school|element:geometry|color:0x999999',
                'feature:poi.place_of_worship|element:geometry|color:0x888888',

                # High-rise/urban core - Very dark gray
                'feature:poi.establishment|element:geometry|color:0x777777',
                'feature:poi.point_of_interest|element:geometry|color:0x666666',

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

    def add_info_overlay(self, image: Image.Image, city: str, country: str, lat: float, lng: float, weather_data: Optional[Dict] = None) -> Image.Image:
        """
        Add information overlay with solid white background and rounded corners ON TOP of the map.

        Args:
            image: Base map image
            city: City name
            country: Country name
            lat: Latitude
            lng: Longitude
            weather_data: Weather information dictionary

        Returns:
            Image with overlay ON TOP
        """
        # Make sure we're working with RGB mode to avoid alpha issues
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Work directly on the image
        draw = ImageDraw.Draw(image)

        # Overlay dimensions and position - optimized for 480x800px
        overlay_width = 320      # Slightly wider for better text layout
        overlay_height = 160     # Slightly taller for comfortable spacing
        x = (self.final_width - overlay_width) // 2  # Centered horizontally
        y = self.final_height - overlay_height - 30  # 30px margin from bottom

        # Draw rounded rectangle directly ON the map with PURE WHITE background
        corner_radius = 15

        # Draw the solid white rounded rectangle - NO ALPHA, just pure RGB
        draw.rounded_rectangle(
            [x, y, x + overlay_width, y + overlay_height],
            radius=corner_radius,
            fill=(255, 255, 255),  # Pure white RGB
            outline=(180, 180, 180),  # Gray border for definition
            width=2
        )

        # Load fonts with consistent sizing
        try:
            # Define optimized font sizes for 480x800px dashboard display
            TITLE_SIZE = 24      # City/Country - larger for prominence  
            COORD_SIZE = 16      # Coordinates - readable but smaller
            TEMP_SIZE = 28       # Temperature - prominent, most important
            DATE_SIZE = 18       # Date - clear and readable
            TIME_SIZE = 24       # Time - important, same as title
            
            # Use our cross-platform font loading
            title_font = self._get_font(TITLE_SIZE)
            coord_font = self._get_font(COORD_SIZE)
            temp_font = self._get_font(TEMP_SIZE)
            date_font = self._get_font(DATE_SIZE)
            time_font = self._get_font(TIME_SIZE)
            
            print(f"🔤 Optimized fonts for 480x800px - Title: {TITLE_SIZE}px, Temp: {TEMP_SIZE}px, Time: {TIME_SIZE}px")
            
        except Exception as e:
            print(f"⚠️ Font loading error: {e}")
            # Final fallback to default
            title_font = ImageFont.load_default()
            coord_font = ImageFont.load_default()
            temp_font = ImageFont.load_default()
            date_font = ImageFont.load_default()
            time_font = ImageFont.load_default()

        # Text colors - pure black for maximum contrast
        text_color = (0, 0, 0)  # Pure black
        coord_color = (60, 60, 60)  # Darker gray for coordinates

        # Calculate text positions relative to the overlay box - increased margins for better spacing
        text_y_base = y + 25  # Top margin - more space from top

        # City, Country (top line)
        city_text = f"{city.title()}, {country.title()}"
        text_bbox = draw.textbbox((0, 0), city_text, font=title_font)
        text_width = text_bbox[2] - text_bbox[0]

        # Center the text within the overlay
        text_x = x + (overlay_width - text_width) // 2
        draw.text((text_x, text_y_base), city_text, fill=text_color, font=title_font)

        # Coordinates (second line) - Improved format with N/S and E/W indicators
        lat_dir = "N" if lat >= 0 else "S"
        lng_dir = "E" if lng >= 0 else "W"
        coord_text = f"{abs(lat):.4f}°{lat_dir}   {abs(lng):.4f}°{lng_dir}"

        text_bbox = draw.textbbox((0, 0), coord_text, font=coord_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = x + (overlay_width - text_width) // 2
        draw.text((text_x, text_y_base + 35), coord_text, fill=coord_color, font=coord_font)  # Increased spacing

        # Weather and datetime information (bottom section) - properly aligned groups
        if weather_data:
            # Get local date and time with UTC offset
            date_str, time_str, timezone_name, utc_offset = self.get_local_datetime(city, country, lat, lng)

            # Download and add weather icon
            weather_icon = self.download_weather_icon(weather_data['icon'])
            temp_text = f"{weather_data['temperature']}°C"

            if weather_icon:
                # Optimized icon size for better proportion with larger fonts
                icon_size = 80  # Balanced size for dashboard display

                # Resize first, then handle transparency properly
                weather_icon = weather_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
                
                # Keep transparency by preserving RGBA mode for proper blending
                if weather_icon.mode != 'RGBA':
                    weather_icon = weather_icon.convert('RGBA')
                
                # Ensure the icon has proper transparency by checking if it's mostly opaque
                # If it has a solid background, we'll keep it as is since it's the icon design

                # Calculate dimensions for datetime group (treated as single block)
                date_bbox = draw.textbbox((0, 0), date_str, font=date_font)
                time_bbox = draw.textbbox((0, 0), time_str, font=time_font)

                # DateTime group dimensions - width is max of date/time, height includes both
                datetime_width = max(date_bbox[2] - date_bbox[0], time_bbox[2] - time_bbox[0])
                datetime_height = (date_bbox[3] - date_bbox[1]) + (time_bbox[3] - time_bbox[1]) + 5  # 5px spacing

                # Calculate dimensions for temperature text
                temp_bbox = draw.textbbox((0, 0), temp_text, font=temp_font)
                temp_width = temp_bbox[2] - temp_bbox[0]
                temp_height = temp_bbox[3] - temp_bbox[1]

                # Calculate total width for horizontal layout: datetime_group + icon + temp
                group_spacing = 15
                total_width = datetime_width + group_spacing + icon_size + group_spacing + temp_width
                start_x = x + (overlay_width - total_width) // 2

                # Position groups horizontally
                datetime_group_x = start_x
                icon_x = datetime_group_x + datetime_width + group_spacing
                temp_x = icon_x + icon_size + group_spacing

                # Vertical positioning - center all elements on same baseline
                element_y = text_y_base + 45

                # Calculate vertical centering for each element
                max_height = max(datetime_height, icon_size, temp_height)

                # Draw datetime group (left) - vertically centered
                datetime_y_offset = (max_height - datetime_height) // 2
                date_x = datetime_group_x + (datetime_width - (date_bbox[2] - date_bbox[0])) // 2
                time_x = datetime_group_x + (datetime_width - (time_bbox[2] - time_bbox[0])) // 2

                draw.text((date_x, element_y + datetime_y_offset), date_str, fill=text_color, font=date_font)
                draw.text((time_x, element_y + datetime_y_offset + 20), time_str, fill=text_color, font=time_font)

                # Draw weather icon (center) - vertically centered with proper transparency
                icon_y_offset = (max_height - icon_size) // 2
                # Use the alpha channel as mask for proper transparency blending
                image.paste(weather_icon, (icon_x, element_y + icon_y_offset), weather_icon)

                # Draw temperature (right) - vertically centered
                temp_y_offset = (max_height - temp_height) // 2
                draw.text((temp_x, element_y + temp_y_offset), temp_text, fill=text_color, font=temp_font)

            else:
                # No icon, show datetime and temperature groups only
                date_str, time_str, timezone_name, utc_offset = self.get_local_datetime(city, country, lat, lng)

                # Calculate positioning for two groups
                date_bbox = draw.textbbox((0, 0), date_str, font=date_font)
                time_bbox = draw.textbbox((0, 0), time_str, font=time_font)
                temp_bbox = draw.textbbox((0, 0), temp_text, font=temp_font)

                datetime_width = max(date_bbox[2] - date_bbox[0], time_bbox[2] - time_bbox[0])
                temp_width = temp_bbox[2] - temp_bbox[0]

                group_spacing = 30
                total_width = datetime_width + group_spacing + temp_width
                start_x = x + (overlay_width - total_width) // 2
                element_y = text_y_base + 65

                # Draw datetime group
                date_x = start_x + (datetime_width - (date_bbox[2] - date_bbox[0])) // 2
                time_x = start_x + (datetime_width - (time_bbox[2] - time_bbox[0])) // 2

                draw.text((date_x, element_y), date_str, fill=text_color, font=date_font)
                draw.text((time_x, element_y + 20), time_str, fill=text_color, font=time_font)

                # Draw temperature group
                temp_x = start_x + datetime_width + group_spacing
                draw.text((temp_x, element_y + 10), temp_text, fill=text_color, font=temp_font)

        return image

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

    def download_map_by_location(self, city: str, country: str, zoom: int = 12, save_path: str = None, include_weather: bool = True) -> str:
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
        if include_weather:
            weather_data = self.get_weather_data(lat, lng)

        # Generate base map
        url = self.generate_map_url(lat, lng, zoom)
        print(f"🗺️  Generating map for {city}, {country} (zoom: {zoom})...")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Verify response contains an image
            if 'image' not in response.headers.get('content-type', ''):
                raise Exception("Response does not contain a valid image")

            # Process square image
            square_image = Image.open(io.BytesIO(response.content))

            # Crop to final size to avoid deformation
            final_image = self.crop_to_final_size(square_image)

            # Add information overlay
            final_image = self.add_info_overlay(final_image, city, country, lat, lng, weather_data)

            # Generate save path in Maps folder with City_Country format
            if not save_path:
                clean_city = city.replace(' ', '_').replace(',', '').replace('.', '')
                clean_country = country.replace(' ', '_').replace(',', '').replace('.', '')
                save_path = os.path.join(self.maps_folder, f"{clean_city}_{clean_country}.png")

            # Save image
            final_image.save(save_path, 'PNG', optimize=True)
            print(f"✅ Map saved to: {save_path} ({self.final_width}x{self.final_height}px)")

            # Generate C array file for e-paper display
            c_path = os.path.splitext(save_path)[0] + '.c'
            print(f"🔄 Converting to e-paper format...")
            if convert_png_to_c_file(save_path, c_path):
                print(f"✅ E-paper C array saved to: {c_path}")
            else:
                print(f"⚠️  Failed to generate e-paper format")

            return save_path

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")
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

            # Generate C array file for e-paper display
            c_path = os.path.splitext(save_path)[0] + '.c'
            print(f"🔄 Converting to e-paper format...")
            if convert_png_to_c_file(save_path, c_path):
                print(f"✅ E-paper C array saved to: {c_path}")
            else:
                print(f"⚠️  Failed to generate e-paper format")

            return save_path

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")
        except Exception as e:
            raise Exception(f"Error generating map: {e}")

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
