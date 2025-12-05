"""
CrowdShield Data Loader — unified version
Handles weather, hazards, shelters, crowd telemetry, cached advisories, and batch preloading.
"""

import os
import json
import requests
import pandas as pd
import geopandas as gpd
from pathlib import Path
from shapely.geometry import shape
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")

DATA_DIR = Path("data")
CACHE = {}

# ---------------- Weather Loader ----------------
def get_weather(state="Kerala", use_cache=True):
    """
    Get live weather data for a given state using OpenWeatherMap API.
    Falls back to static mock if API key or request fails.
    Caches results per state to avoid repeated API calls.
    """
    if use_cache and "weather" in CACHE and state in CACHE["weather"]:
        return CACHE["weather"][state]

    coords = {
        "Kerala": (9.9312, 76.2673),
        "Tamil Nadu": (13.0827, 80.2707),
        "Karnataka": (12.9716, 77.5946),
        "Maharashtra": (19.0760, 72.8777),
        "Uttar Pradesh": (26.8467, 80.9462),
        "Delhi": (28.7041, 77.1025),
        "West Bengal": (22.5726, 88.3639),
        "Rajasthan": (26.9124, 75.7873),
    }
    lat, lon = coords.get(state, (20.5937, 78.9629))  # fallback: India center

    result = {"state": state, "rainfall_mm": 30, "wind_kph": 25, "timestamp": None}
    if OPENWEATHER_KEY:
        try:
            resp = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"lat": lat, "lon": lon, "appid": OPENWEATHER_KEY, "units": "metric"},
                timeout=5
            )
            if resp.ok:
                data = resp.json()
                result = {
                    "state": state,
                    "rainfall_mm": data.get("rain", {}).get("1h", 0),
                    "wind_kph": data.get("wind", {}).get("speed", 0) * 3.6,
                    "timestamp": data.get("dt")
                }
        except Exception as e:
            print(f"Weather API error for {state}:", e)

    CACHE.setdefault("weather", {})[state] = result
    return result

# ---------------- Hazard Loader ----------------
def load_hazards(path="data/hazard_zones.geojson", spread_km=0.0):
    """
    Load hazard polygons from a GeoJSON file.
    Optionally expand hazards outward by spread_km (buffer in km).
    Returns a GeoDataFrame.
    """
    p = Path(path)
    if not p.exists():
        return gpd.GeoDataFrame(columns=["hazard", "geometry"])

    try:
        gdf = gpd.read_file(p)
    except Exception:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        features = []
        for feat in data.get("features", []):
            geom = shape(feat["geometry"])
            props = feat.get("properties", {})
            features.append({**props, "geometry": geom})
        gdf = gpd.GeoDataFrame(features, geometry="geometry", crs="EPSG:4326")

    # Buffer correctly in meters
    if spread_km > 0 and not gdf.empty:
        try:
            # Reproject to Web Mercator (meters)
            gdf = gdf.to_crs(epsg=3857)
            gdf["geometry"] = gdf.buffer(spread_km * 1000)
            # Convert back to WGS84 for folium display
            gdf = gdf.to_crs(epsg=4326)
        except Exception as e:
            print("Hazard buffer reprojection error:", e)

    return gdf

# ---------------- Shelter Loader ----------------
def load_shelters(path="data/safe_zones.csv"):
    """
    Load shelters from CSV.
    Returns DataFrame with name, lat, lon, capacity.
    """
    p = Path(path)
    if p.exists():
        try:
            df = pd.read_csv(p)
            return df[["name", "lat", "lon", "capacity"]]
        except Exception as e:
            print("Error reading shelters CSV:", e)
    # Fallback sample
    return pd.DataFrame([
        {"name": "Fallback Shelter", "lat": 9.93, "lon": 76.26, "capacity": 50}
    ])

# ---------------- Crowd Loader ----------------
def load_crowd(path="data/crowd_sim.csv"):
    """
    Load crowd telemetry from CSV.
    Returns DataFrame with id, lat, lon, people.
    """
    p = Path(path)
    if p.exists():
        try:
            df = pd.read_csv(p)
            return df[["id", "lat", "lon", "people"]]
        except Exception as e:
            print("Error reading crowd CSV:", e)
    return pd.DataFrame(columns=["id", "lat", "lon", "people"])

# ---------------- Cached Advisories ----------------
def load_cached_advisories(path="data/cached_advisories.json"):
    """
    Load cached advisories from JSON.
    """
    p = Path(path)
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Error reading cached advisories:", e)
    return {}

# ---------------- Cache Clear ----------------
def clear_caches():
    """
    Clear in-memory cache.
    """
    CACHE.clear()

# ---------------- Batch Preloader ----------------
SUPPORTED_STATES = [
    "Kerala", "Tamil Nadu", "Karnataka", "Maharashtra",
    "Uttar Pradesh", "Delhi", "West Bengal", "Rajasthan"
]

def preload_all_states(use_cache=True):
    """
    Preload hazards, shelters, crowd telemetry, and weather for all supported states.
    Stores results in CACHE["states"] keyed by state name.
    """
    CACHE.setdefault("states", {})
    for state in SUPPORTED_STATES:
        try:
            hazards = load_hazards(f"data/hazard_zones_{state.lower().replace(' ', '_')}.geojson")
            shelters = load_shelters(f"data/safe_zones_{state.lower().replace(' ', '_')}.csv")
            crowd = load_crowd(f"data/crowd_sim_{state.lower().replace(' ', '_')}.csv")
            weather = get_weather(state, use_cache=use_cache)
            
            CACHE["states"][state] = {
                "hazards": hazards,
                "shelters": shelters,
                "crowd": crowd,
                "weather": weather
            }
        except Exception as e:
            print(f"Preload error for {state}: {e}")
    return CACHE["states"]

def get_state_data(state):
    """
    Retrieve preloaded data for a given state.
    Falls back to on-demand loaders if not preloaded.
    """
    if "states" in CACHE and state in CACHE["states"]:
        return CACHE["states"][state]
    # Fallback: load on demand
    return {
        "hazards": load_hazards(f"data/hazard_zones_{state.lower().replace(' ', '_')}.geojson"),
        "shelters": load_shelters(f"data/safe_zones_{state.lower().replace(' ', '_')}.csv"),
        "crowd": load_crowd(f"data/crowd_sim_{state.lower().replace(' ', '_')}.csv"),
        "weather": get_weather(state)
    }
