"""
Live weather integration for CrowdShield.

Uses OpenWeatherMap as an example data source. This is optional:
if no API key is configured or the call fails, callers should fall
back to the existing slider-based simulation.
"""

import os
from typing import Dict, Any, Optional

import requests


STATE_FALLBACK_CITY = {
    "Kerala": "Kochi,IN",
    "Tamil Nadu": "Chennai,IN",
    "Karnataka": "Bengaluru,IN",
    "Maharashtra": "Mumbai,IN",
    "Uttar Pradesh": "Lucknow,IN",
    "Delhi": "Delhi,IN",
    "West Bengal": "Kolkata,IN",
    "Rajasthan": "Jaipur,IN",
}


def fetch_weather_for_state(state: str) -> Optional[Dict[str, Any]]:
    """
    Fetch current weather for a representative city in the given state.

    Requires OPENWEATHER_API_KEY to be set. Returns a dict with keys:
      - rainfall_mm
      - wind_kph
      - raw (full API JSON)

    Returns None on any error.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return None

    city = STATE_FALLBACK_CITY.get(state, "Delhi,IN")
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": api_key, "units": "metric"}
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        # OpenWeather: rainfall from rain.1h or rain.3h, wind speed in m/s.
        rain = 0.0
        rain_info = data.get("rain") or {}
        if "1h" in rain_info:
            rain = float(rain_info["1h"])
        elif "3h" in rain_info:
            rain = float(rain_info["3h"]) / 3.0

        wind_ms = float(data.get("wind", {}).get("speed", 0.0))
        wind_kph = wind_ms * 3.6

        return {
            "rainfall_mm": rain,
            "wind_kph": wind_kph,
            "raw": data,
        }
    except Exception as e:
        print(f"Live weather fetch error for state={state}: {e}")
        return None


