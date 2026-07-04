# Weather App

This folder contains a beginner-friendly command-line weather app and an advanced tkinter GUI weather app.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set your OpenWeatherMap API key:
   ```bash
   set OPENWEATHER_API_KEY=your_api_key_here
   ```
   On PowerShell, use `$env:OPENWEATHER_API_KEY="your_api_key_here"`.

## Run

### Command-line version
```bash
python weather_cli.py
```

### GUI version
```bash
python weather_gui.py
```

## Features
- City or ZIP input
- Current temperature in °C and °F
- Humidity, condition, and wind speed
- Friendly error handling for invalid input, API errors, and network problems
- GUI with icons, 6-hour forecast, 5-day forecast, and unit toggle
