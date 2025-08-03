# Automated Smart Dashboard Map Server

This project generates automated map images every hour using GitHub Actions. Perfect for smart displays, dashboards, and real-time location monitoring.

## 🚀 Quick Start

1. **Fork this repository**
2. **Add your API keys as GitHub Secrets:**
   - `GOOGLE_MAPS_API_KEY` (required)
   - `OPENWEATHER_API_KEY` (optional, for weather)
3. **That's it!** Maps will be generated every hour automatically.

## 🎯 Features

- ⏰ **Hourly Updates** - GitHub Actions runs automatically every hour
- 🗺️ **High Quality Maps** - 480x800px perfect for portrait displays
- 🌤️ **Weather Integration** - Current temperature and conditions
- 🕐 **Local Time** - Shows local date/time for each location
- 📍 **Precise Coordinates** - Lat/lng display with N/S, E/W indicators
- 💾 **Smart Caching** - Coordinates and timezones cached for performance
- 🌍 **Offline Timezone** - No external API calls for timezone data

## 📱 Perfect For

- Smart home displays
- Digital signage
- Location dashboards
- Travel planning
- Real-time monitoring

## 🛠️ Local Development

```bash
# 1. Clone and setup
git clone <your-repo>
cd Smart\ Dashboard\ server/Server

# 2. Create virtual environment
python -m venv smart_dashboard_server
source smart_dashboard_server/bin/activate  # Linux/Mac
# OR
.\smart_dashboard_server\Scripts\Activate.ps1  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export GOOGLE_MAPS_API_KEY="your-key"
export OPENWEATHER_API_KEY="your-key"  # optional

# 5. Run
python main.py
```

## 🔧 Configuration

### Adding Cities
Edit `main.py` to add more locations:

```python
test_locations = [
    ("Vienna", "Austria"),
    ("Tokyo", "Japan"),
    ("New York", "USA"),
    ("Sydney", "Australia"),
    # Add your cities here
]
```

### GitHub Secrets Setup
1. Go to your repository Settings → Secrets and variables → Actions
2. Add these secrets:
   - `GOOGLE_MAPS_API_KEY`: Get from [Google Cloud Console](https://console.cloud.google.com/)
   - `OPENWEATHER_API_KEY`: Get from [OpenWeatherMap](https://openweathermap.org/api) (optional)

## 📦 What's Generated

- **Maps**: Saved in `Maps/` folder as `City_Country.png`
- **Cache**: Location data stored in `locations_cache.json`
- **Automation**: Runs via `.github/workflows/generate-maps.yml`

## 🕒 Schedule

- **Hourly**: Every hour at minute 0 (00:00, 01:00, 02:00, etc.)
- **Manual**: Can be triggered manually from GitHub Actions tab
- **Auto-commit**: New maps are automatically committed and pushed

## 🌍 Timezone Intelligence

The system smartly handles timezones:
1. **Cache first** - Checks if timezone already known
2. **Offline lookup** - Uses `tzwhere` for precise detection
3. **Fallback** - Basic estimation if needed
4. **Caching** - Stores for future use

## 📁 Repository Structure

```
Server/
├── main.py                    # Main generator script
├── requirements.txt           # Python dependencies  
├── locations_cache.json       # Cached location data
├── Maps/                      # Generated images (auto-updated)
├── .github/workflows/         # GitHub Actions automation
└── smart_dashboard_server/    # Virtual environment (local only)
```

## 🔐 Security Note

- API keys are stored as GitHub Secrets (encrypted)
- Never commit API keys to code
- Restrict API keys to necessary services only

## 🚨 Troubleshooting

**Maps not generating?**
- Check GitHub Actions tab for errors
- Verify API keys are set correctly
- Ensure APIs are enabled in Google Cloud Console

**Wrong timezone?**
- The system uses offline timezone detection
- Times are automatically adjusted for DST
- Check that coordinates are accurate

**Out of API quota?**
- Google Maps has usage limits
- Consider caching and fewer locations
- Monitor usage in Google Cloud Console

---

**🎉 That's it! Your automated map server is ready to go!**
