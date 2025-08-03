# 🚀 Quick Setup Guide

## Setting Up API Keys for Local Development

### Step 1: Get Your API Keys

#### Google Maps API Key (Required)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable these APIs:
   - **Maps Static API**
   - **Geocoding API**
4. Go to "Credentials" → "Create Credentials" → "API Key"
5. Copy your API key

#### OpenWeather API Key (Optional)
1. Go to [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for free account
3. Copy your API key from "My API keys"

### Step 2: Configure VS Code

1. **Open the `launch.json` file** (located in `.vscode/launch.json`)

2. **Replace the placeholder values** with your actual API keys:
   ```json
   "env": {
       "GOOGLE_MAPS_API_KEY": "YOUR_ACTUAL_GOOGLE_MAPS_API_KEY_HERE",
       "OPENWEATHER_API_KEY": "YOUR_ACTUAL_OPENWEATHER_API_KEY_HERE"
   }
   ```

3. **Save the file**

### Step 3: Run the Project

1. **Open VS Code** in the project folder
2. **Press F5** or go to "Run and Debug" → "Smart Dashboard Server"
3. **The project will automatically:**
   - Activate the `smart_dashboard_server` virtual environment
   - Load your API keys
   - Run the main.py script

### Alternative: Run from Terminal

```bash
# Activate virtual environment
.\smart_dashboard_server\Scripts\Activate.ps1  # Windows
source smart_dashboard_server/bin/activate     # Linux/Mac

# Set environment variables for this session
$env:GOOGLE_MAPS_API_KEY="your_key_here"           # Windows PowerShell
$env:OPENWEATHER_API_KEY="your_key_here"          # Windows PowerShell

export GOOGLE_MAPS_API_KEY="your_key_here"        # Linux/Mac/Git Bash
export OPENWEATHER_API_KEY="your_key_here"        # Linux/Mac/Git Bash

# Run the script
python main.py
```

## 🔐 Security Notes

- **Never commit API keys to Git!** The `.gitignore` file protects the `launch.json` with your keys
- **For GitHub Actions:** API keys are stored as repository secrets (already configured)
- **Local Development:** API keys are in VS Code configuration only

## 🎯 Ready to Go!

Once configured, you can:
- **Press F5** to run locally with your API keys
- **Push to GitHub** for automated hourly map generation
- **Add more cities** by editing the `test_locations` in `main.py`

Your setup is complete! 🎉
