# Map Generator - 480x800px Google Maps Images

A Python tool that generates high-quality map images (480x800px) using Google Maps Static API with intelligent coordinate caching system.

## 🌟 Features

- **No Deformation**: Downloads 800x800px square images and crops to 480x800px to avoid distortion
- **Clean Maps**: No text labels, clean Google Maps style
- **Smart Caching**: Automatically caches coordinates in JSON to minimize API calls
- **City/Country Input**: Simply provide city and country names - no need to look up coordinates
- **Dynamic Zoom**: Optimized zoom levels for different metropolitan areas
- **Standard Google Maps Style**: Parks in green, water in blue, roads in white/yellow

## 🚀 Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Setup Google Maps API Key

Get your API key from [Google Cloud Console](https://console.cloud.google.com/):
1. Create a new project or select existing one
2. Enable "Maps Static API" and "Geocoding API"
3. Create credentials (API Key)
4. Set the environment variable:

```bash
# Windows
set GOOGLE_MAPS_API_KEY=your_api_key_here

# Linux/Mac
export GOOGLE_MAPS_API_KEY=your_api_key_here
```

### 3. Basic Usage

```python
from main import MapGenerator

# Initialize (API key from environment variable)
map_gen = MapGenerator()

# Generate map using city/country (MAIN WORKFLOW)
map_file = map_gen.download_map_by_location("Paris", "France", zoom=12)
print(f"Map saved: {map_file}")
```

## 📋 Main Workflow

### Primary Input: City + Country

The system is designed around the **city/country** input pattern:

1. **User requests**: `"Paris, France"`
2. **System checks cache**: Looks in `locations_cache.json`
3. **If cached**: Uses stored coordinates ⚡
4. **If not cached**: 
   - Calls Google Geocoding API 🌐
   - Stores coordinates in cache 💾
   - Uses coordinates for map generation
5. **Generates map**: 480x800px image saved

### Cache Structure

The `locations_cache.json` file stores:

```json
{
  "paris, france": {
    "lat": 48.8566,
    "lng": 2.3522,
    "city": "Paris",
    "country": "France",
    "formatted_address": "Paris, France"
  }
}
```

## 🛠️ API Reference

### Core Methods

#### `download_map_by_location(city, country, zoom=12, save_path=None)`
**Main method** - Generate map using city/country names.

```python
# Basic usage
map_file = map_gen.download_map_by_location("Tokyo", "Japan")

# With custom zoom and path
map_file = map_gen.download_map_by_location(
    "London", "UK", 
    zoom=13, 
    save_path="london_map.png"
)
```

#### `download_map_by_coordinates(lat, lng, zoom=12, save_path=None)`
Generate map using exact coordinates.

```python
map_file = map_gen.download_map_by_coordinates(40.7128, -74.0060, zoom=11)
```

#### `download_map_by_city(city, custom_zoom=None, save_path=None)`
Generate map for predefined cities (Vienna, Madrid, New York, Tokyo).

```python
map_file = map_gen.download_map_by_city("vienna")
```

### Cache Management

#### `list_cached_locations()`
Get all cached locations.

```python
cached = map_gen.list_cached_locations()
print(f"Cached locations: {len(cached)}")
```

#### `clear_cache()`
Clear all cached coordinates.

```python
map_gen.clear_cache()
```

## 📊 Examples

### Example 1: Tourist Cities

```python
from main import MapGenerator

map_gen = MapGenerator()

cities = [
    ("Rome", "Italy"),
    ("Barcelona", "Spain"),
    ("Amsterdam", "Netherlands"),
    ("Prague", "Czech Republic")
]

for city, country in cities:
    try:
        map_file = map_gen.download_map_by_location(city, country, zoom=12)
        print(f"✅ {city}: {map_file}")
    except Exception as e:
        print(f"❌ {city}: {e}")
```

### Example 2: Multiple Maps Same City

```python
# First call - fetches coordinates from API
map1 = map_gen.download_map_by_location("Berlin", "Germany", zoom=10)

# Second call - uses cached coordinates (faster!)
map2 = map_gen.download_map_by_location("Berlin", "Germany", zoom=14)
```

### Example 3: Batch Processing

```python
def generate_city_maps(cities_list, zoom=12):
    map_gen = MapGenerator()
    results = {}
    
    for city, country in cities_list:
        try:
            filename = f"{city}_{country}_{zoom}.png"
            map_file = map_gen.download_map_by_location(
                city, country, zoom, filename
            )
            results[f"{city}, {country}"] = map_file
        except Exception as e:
            results[f"{city}, {country}"] = f"Error: {e}"
    
    return results

# Usage
cities = [("Paris", "France"), ("London", "UK"), ("Berlin", "Germany")]
results = generate_city_maps(cities, zoom=11)
```

## ⚙️ Configuration

### Image Settings
- **Final size**: 480x800px (no deformation)
- **Download size**: 800x800px (cropped to final size)
- **Format**: PNG with optimization
- **Scale**: 2 (high resolution)

### Map Style
- **No labels**: All text removed
- **Parks**: Green (#66bb6a)
- **Water**: Blue (#1976d2)
- **Roads**: White with gray borders
- **Highways**: Yellow (#ffc107)
- **Buildings**: Light gray (#eeeeee)
- **Land**: Brown (#8d6e63)

### Zoom Levels
- **10**: Large metropolitan areas
- **11**: City centers  
- **12**: Urban districts
- **13-15**: Neighborhoods
- **16+**: Street level

## 🗂️ File Structure

```
project/
├── main.py                 # Main MapGenerator class
├── requirements.txt        # Dependencies
├── locations_cache.json    # Coordinate cache (auto-generated)
├── README.md              # This file
└── generated_maps/        # Output directory (optional)
    ├── map_Paris_France_12.png
    ├── map_London_UK_11.png
    └── ...
```

## 📝 Requirements

```
requests>=2.31.0
Pillow>=10.0.0
```

## 🔧 Troubleshooting

### Common Issues

**API Key Error**
```
ValueError: Google Maps API key is required
```
- Solution: Set `GOOGLE_MAPS_API_KEY` environment variable

**Location Not Found**
```
Exception: No results found for 'Unknown City, Unknown Country'
```
- Solution: Check city/country spelling and try alternative names

**Network Timeout**
```
Exception: Network error during geocoding: timeout
```
- Solution: Check internet connection, try again

**Cache Permission Error**
```
⚠️ Error saving cache: Permission denied
```
- Solution: Ensure write permissions in current directory

### Performance Tips

1. **Use cache**: Repeated requests for same city are much faster
2. **Batch processing**: Process multiple cities in one script run
3. **Optimal zoom**: Use zoom 10-12 for metropolitan areas
4. **Error handling**: Always wrap API calls in try/except blocks

## 🌍 Supported Locations

The geocoding API supports virtually any location worldwide:

- **Cities**: "New York", "Tokyo", "London"
- **Regions**: "California", "Tuscany", "Bavaria"  
- **Landmarks**: "Eiffel Tower", "Central Park"
- **Addresses**: "1600 Pennsylvania Avenue, Washington DC"

## 📄 License

MIT License - feel free to use in your projects!

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

---

**Made with ❤️ for creating beautiful map visualizations**
