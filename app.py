#!/usr/bin/env python3
"""
CrowdShield — Streamlit main app (stable, defensive, offline-first TTS)

Save as app.py and run:
    pip install -r requirements.txt
    streamlit run app.py

This file expects helper modules under src/: data_loader, routing, fusion_engine,
llm_insights, translate, alerting, authority, gps_mock, ux, risk_disaster,
risk_crowd, tts, live_weather. Minimal fallbacks are used where appropriate.
"""

from pathlib import Path
import time
import math
import random
from datetime import datetime
from io import BytesIO
import os
import logging

import streamlit as st
import folium
import pandas as pd
import plotly.graph_objects as go

# Local helpers (ensure src/ is a package)
from src import (
    data_loader,
    routing,
    fusion_engine,
    llm_insights,
    translate,
    alerting,
    authority,
    gps_mock,
    ux,
    risk_disaster,
    risk_crowd,
    tts as tts_module,
    live_weather,
)

# Basic logging
logger = logging.getLogger("crowdshield.app")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

# ---------------- Page config ----------------
st.set_page_config(layout="wide", page_title="CrowdShield — AI Disaster Copilot", page_icon="🛡️", initial_sidebar_state="expanded")

# Ensure data folders exist
Path("data/alerts").mkdir(parents=True, exist_ok=True)
Path("data/cache").mkdir(parents=True, exist_ok=True)

# ---------------- I18N ----------------
I18N = {
    "en": {"title": "CrowdShield Demo", "state": "Select state", "map": "Safety Map", "drivers": "Drivers", "severity": "Severity Tier", "advisory": "LLM Advisory", "risk_crowd": "Crowd risk", "risk_disaster": "Disaster risk", "recommendations": "Recommendations", "nearest": "Nearest shelter", "eta": "ETA", "distance": "Distance", "instructions": "Route instructions", "safety_methods": "Safety methods", "live_status": "Live Status", "refresh_rate": "Auto-refresh (seconds)", "enable_auto_refresh": "Enable Auto-Refresh", "history": "Risk History", "dispatch": "Authority dispatch", "incident": "Incident", "no_reports": "No recent reports"},
    "hi": {"title": "क्राउडशील्ड डेमो", "state": "राज्य चुनें", "map": "सुरक्षा मानचित्र"},
    "ml": {"title": "ക്രൗഡ്‌ഷീൽഡ് ഡെമോ", "state": "സംസ്ഥാനം തിരഞ്ഞെടുക്കുക", "map": "സുരക്ഷാ മാപ്പ്"},
    "ta": {"title": "கூட்டம் பாதுகாப்பு டெமோ", "state": "மாநிலத்தைத் தேர்ந்தெடுக்கவும்", "map": "பாதுகாப்பு வரைபடம்"},
}

STATES = ["Kerala", "Tamil Nadu", "Karnataka", "Maharashtra", "Uttar Pradesh", "Delhi", "West Bengal", "Rajasthan"]
STATE_CENTERS = {"Kerala": (10.1632, 76.6413), "Tamil Nadu": (11.1271, 78.6569), "Karnataka": (15.3173, 75.7139), "Maharashtra": (19.7515, 75.7139), "Uttar Pradesh": (26.8467, 80.9462), "Delhi": (28.6139, 77.2090), "West Bengal": (22.9868, 87.8550), "Rajasthan": (27.0238, 74.2179)}

# ---------------- Session defaults ----------------
if "risk_history" not in st.session_state:
    st.session_state.risk_history = []
if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.now()
if "auto_refresh_enabled" not in st.session_state:
    st.session_state.auto_refresh_enabled = False
if "refresh_interval" not in st.session_state:
    st.session_state.refresh_interval = 5
if "reports" not in st.session_state:
    st.session_state.reports = []
if "rainfall_slider" not in st.session_state:
    st.session_state.rainfall_slider = 30
if "wind_slider" not in st.session_state:
    st.session_state.wind_slider = 25
if "crowd_density_slider" not in st.session_state:
    st.session_state.crowd_density_slider = 1.0
if "scenario_trigger_flood" not in st.session_state:
    st.session_state.scenario_trigger_flood = False
if "scenario_trigger_crowd" not in st.session_state:
    st.session_state.scenario_trigger_crowd = False
if "lang" not in st.session_state:
    st.session_state.lang = "en"
if "last_tts_time" not in st.session_state:
    st.session_state.last_tts_time = 0.0

# ---------------- Sidebar ----------------
st.sidebar.title("🛡️ " + I18N[st.session_state.lang]["title"])
lang = st.sidebar.selectbox("Language / भाषा / ഭാഷ / மொழி", options=list(I18N.keys()), index=list(I18N.keys()).index(st.session_state.lang))
st.session_state.lang = lang
i18n = I18N.get(lang, I18N["en"])

state = st.sidebar.selectbox(i18n["state"], options=STATES, index=STATES.index("Kerala") if "Kerala" in STATES else 0)
role = st.sidebar.radio("User role", ["Citizen", "Authority"], index=0)

st.sidebar.markdown("#### 🎭 Scenarios")
col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    if st.button("Stadium crowd", key="btn_stadium"):
        st.session_state.rainfall_slider = 10
        st.session_state.wind_slider = 10
        st.session_state.crowd_density_slider = 8.0
        st.session_state.scenario_trigger_crowd = True
        st.rerun()
with col_s2:
    if st.button("Coastal flood", key="btn_coastal"):
        st.session_state.rainfall_slider = 180
        st.session_state.wind_slider = 80
        st.session_state.scenario_trigger_flood = True
        st.session_state.crowd_density_slider = 2.0
        st.rerun()

st.sidebar.markdown("### 🎛️ Simulation Controls")
trigger_flood = st.sidebar.checkbox("🌊 Trigger Flood", value=st.session_state.scenario_trigger_flood)
trigger_crowd = st.sidebar.checkbox("👥 Trigger Crowd Surge", value=st.session_state.scenario_trigger_crowd)
offline_mode = st.sidebar.checkbox("📴 Offline Mode (local graph/satellite)", value=False)

st.sidebar.markdown("### 🌦️ Weather Controls")
rainfall_mm = st.sidebar.slider("Rainfall (mm)", 0, 200, value=st.session_state.get("rainfall_slider", 30), step=5, key="rainfall_slider")
wind_kph = st.sidebar.slider("Wind speed (kph)", 0, 150, value=st.session_state.get("wind_slider", 25), step=5, key="wind_slider")
crowd_density = st.sidebar.slider("Crowd Density (people/m²)", 0.0, 10.0, value=st.session_state.get("crowd_density_slider", 1.0), step=0.1, key="crowd_density_slider")

st.sidebar.markdown("### 🗺️ Routing")
route_mode = st.sidebar.radio("Route Mode", ["Shortest", "Fastest", "Safest"], index=0)
find_route = st.sidebar.button("🔍 Find Safe Route", key="btn_find_route")

st.sidebar.markdown("### 🔄 Live Updates")
st.session_state.auto_refresh_enabled = st.sidebar.checkbox(i18n["enable_auto_refresh"], value=st.session_state.auto_refresh_enabled)
if st.session_state.auto_refresh_enabled:
    st.session_state.refresh_interval = st.sidebar.slider(i18n["refresh_rate"], 2, 30, st.session_state.refresh_interval, 1)
if st.sidebar.button("🔄 Manual Refresh", key="btn_manual_refresh"):
    st.session_state.last_update = datetime.now()
    st.rerun()

st.sidebar.markdown("### 📢 Alerts")
def send_sms_safe(body):
    from_num = os.getenv("TWILIO_FROM") or getattr(alerting, "TWILIO_FROM", None)
    to_num = os.getenv("TWILIO_TO") or getattr(alerting, "TWILIO_TO", None)
    if not from_num or not to_num:
        st.sidebar.error("Twilio not configured: set TWILIO_FROM and TWILIO_TO environment variables.")
        return False
    if from_num == to_num:
        st.sidebar.error("Twilio error: 'From' and 'To' numbers are identical. Use different numbers.")
        return False
    try:
        if hasattr(alerting, "send_twilio_sms"):
            ok, msg = alerting.send_twilio_sms(body)
            if ok:
                st.sidebar.success(f"✅ SMS sent: {msg}")
            else:
                st.sidebar.warning(f"⚠️ SMS status: {msg}")
            return ok
        else:
            st.sidebar.error("Alerting module does not provide send_twilio_sms.")
            return False
    except Exception as e:
        st.sidebar.error(f"SMS send exception: {e}")
        return False

if st.sidebar.button("📱 Send SMS Alert", key="btn_send_sms"):
    send_sms_safe("CrowdShield advisory: check app for details")

play_alert = st.sidebar.checkbox("🔊 Play Audio Alert", value=False)
show_charts = st.sidebar.checkbox("📊 Show Interactive Charts", value=True)

st.sidebar.markdown("### 📝 Crowd Reports")
with st.sidebar.form("report_form"):
    report_type = st.selectbox("Incident type", ["Flooding", "Crowd crush", "Blocked road", "Other"])
    report_severity = st.select_slider("Severity", options=["low", "medium", "high", "critical"], value="medium")
    report_note = st.text_area("Details (optional)", height=60)
    submitted_report = st.form_submit_button("Submit report", key="btn_submit_report")

if submitted_report:
    origin_lat, origin_lon = gps_mock.get_mock_location_for_state(state)
    st.session_state.reports.append({"lat": origin_lat, "lon": origin_lon, "type": report_type, "severity": report_severity, "note": report_note, "timestamp": datetime.now().isoformat()})
    st.sidebar.success("✅ Report submitted")

st.sidebar.markdown("---")
st.sidebar.caption("💡 Tip: Enable auto-refresh for live updates. Adjust sliders to simulate conditions.")

# Auto-refresh
if st.session_state.auto_refresh_enabled:
    time_since_update = (datetime.now() - st.session_state.last_update).total_seconds()
    if time_since_update >= st.session_state.refresh_interval:
        st.session_state.last_update = datetime.now()
        time.sleep(0.05)
        st.rerun()

# ---------------- Data loading ----------------
haz_path = f"data/hazard_zones_{state.lower().replace(' ', '_')}.geojson"
shel_path = f"data/safe_zones_{state.lower().replace(' ', '_')}.csv"
crowd_path = f"data/crowd_sim_{state.lower().replace(' ', '_')}.csv"

def safe_load_hazards(path):
    try:
        return data_loader.load_hazards(path) if Path(path).exists() else data_loader.load_hazards()
    except Exception as exc:
        st.warning(f"Could not load hazards ({path}): {exc}")
        try:
            return data_loader.load_hazards()
        except Exception:
            st.error("Unable to load any hazard file.")
            return pd.DataFrame()

def safe_load_shelters(path):
    try:
        return data_loader.load_shelters(path) if Path(path).exists() else data_loader.load_shelters()
    except Exception as exc:
        st.warning(f"Could not load shelters ({path}): {exc}")
        return pd.DataFrame()

def safe_load_crowd(path):
    try:
        df = data_loader.load_crowd(path) if Path(path).exists() else data_loader.load_crowd()
        if not df.empty and "people" in df.columns:
            mean_people = max(1.0, df["people"].mean())
            df["people"] = df["people"] * (crowd_density / (mean_people / 1000.0))
        return df
    except Exception as exc:
        st.warning(f"Could not load crowd data ({path}): {exc}")
        return pd.DataFrame()

hazards = safe_load_hazards(haz_path)
shelters = safe_load_shelters(shel_path)
crowd_sim = safe_load_crowd(crowd_path)

# ---------------- Hazard normalization helper ----------------
try:
    import geopandas as gpd
    from shapely import wkt
    from shapely.geometry.base import BaseGeometry
except Exception:
    gpd = None
    wkt = None
    BaseGeometry = None

def normalize_hazards(haz):
    import pandas as pd
    if gpd is not None and isinstance(haz, gpd.GeoDataFrame):
        return haz
    if isinstance(haz, (str, Path)):
        p = Path(haz)
        if p.exists() and gpd is not None:
            try:
                return gpd.read_file(str(p))
            except Exception:
                return pd.DataFrame()
    if isinstance(haz, pd.DataFrame):
        df = haz.copy()
        if "geometry" in df.columns:
            if df["geometry"].dtype == object and df["geometry"].apply(lambda x: isinstance(x, str)).all() and wkt is not None:
                df["geometry"] = df["geometry"].apply(lambda s: wkt.loads(s) if isinstance(s, str) else s)
            if gpd is not None:
                return gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
            return df
        if "wkt" in df.columns and wkt is not None:
            df["geometry"] = df["wkt"].apply(lambda s: wkt.loads(s) if isinstance(s, str) else None)
            if gpd is not None:
                return gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
            return df
    try:
        from shapely.geometry.base import BaseGeometry as _BG
        if isinstance(haz, _BG):
            if gpd is not None:
                return gpd.GeoDataFrame([{"geometry": haz}], geometry="geometry", crs="EPSG:4326")
            return pd.DataFrame([{"geometry": haz}])
    except Exception:
        pass
    return pd.DataFrame()

hazards = normalize_hazards(hazards)

# ---------------- Live weather ----------------
try:
    live_wx = live_weather.fetch_weather_for_state(state)
    base_rain = live_wx.get("rainfall_mm", rainfall_mm) if live_wx else rainfall_mm
    base_wind = live_wx.get("wind_kph", wind_kph) if live_wx else wind_kph
except Exception:
    base_rain = rainfall_mm
    base_wind = wind_kph

weather = {"state": state, "rainfall_mm": base_rain, "wind_kph": base_wind, "timestamp": datetime.now().timestamp()}

# ---------------- Risk scoring & fusion ----------------
try:
    disaster_score, drivers = risk_disaster.score_disaster(weather, trigger_flood)
except Exception as e:
    st.warning(f"Disaster scoring failed: {e}")
    disaster_score, drivers = 0.0, [f"Disaster scoring error: {e}"]

try:
    crowd_score, crowd_drivers = risk_crowd.score_crowd(crowd_sim, trigger_crowd)
except Exception as e:
    st.warning(f"Crowd scoring failed: {e}")
    crowd_score, crowd_drivers = 0.0, [f"Crowd scoring error: {e}"]

try:
    severity, recommendations = fusion_engine.fuse(disaster_score, crowd_score, i18n=i18n)
except Exception as e:
    st.warning(f"Fusion error: {e}")
    severity, recommendations = "Medium", ["Fusion engine error"]

# Update risk history
current_time = datetime.now()
st.session_state.risk_history.append({"timestamp": current_time, "disaster_score": float(disaster_score), "crowd_score": float(crowd_score), "combined": float(max(disaster_score, crowd_score * 0.9)), "severity": severity})
if len(st.session_state.risk_history) > 100:
    st.session_state.risk_history = st.session_state.risk_history[-100:]

# ---------------- Helpers ----------------
def haversine_km(p1, p2):
    lat1, lon1 = p1
    lat2, lon2 = p2
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def simulate_live_location(state_name, jitter_meters=50):
    base = gps_mock.get_mock_location_for_state(state_name)
    if not base:
        return (9.931233, 76.267304)
    lat, lon = base
    jitter_deg = (jitter_meters / 111000.0)
    return (lat + random.uniform(-jitter_deg, jitter_deg), lon + random.uniform(-jitter_deg, jitter_deg))

# Robust TTS play wrapper with cooldown
def play_and_stream_tts(text, lang="en", cooldown_seconds=3):
    now = time.time()
    if now - st.session_state.get("last_tts_time", 0) < cooldown_seconds:
        st.warning(f"Please wait {cooldown_seconds} seconds between TTS requests.")
        return False
    st.session_state.last_tts_time = now

    try:
        path = tts_module.generate_tts(text, lang=lang)
        if isinstance(path, str) and path.lower().endswith(".mp3") and Path(path).exists():
            try:
                st.audio(path, format="audio/mp3")
                return True
            except Exception:
                try:
                    with open(path, "rb") as f:
                        st.audio(f.read(), format="audio/mp3")
                        return True
                except Exception as e:
                    st.warning(f"Audio playback failed: {e}")
                    return False
        else:
            # text fallback
            st.info("TTS fallback (text):")
            st.write(path)
            return False
    except Exception as e:
        st.warning(f"TTS play error: {e}")
        return False

# Safe graph loader (validate return)
def safe_load_graph(online=True, center_point=None):
    try:
        try:
            G = routing.load_graph(online=online, center_point=center_point)
        except TypeError:
            G = routing.load_graph(online=online)
        except Exception:
            G = routing.load_graph(online=online)
        try:
            import networkx as nx
            if isinstance(G, nx.Graph) or (hasattr(G, "nodes") and hasattr(G, "edges")):
                return G
        except Exception:
            if hasattr(G, "nodes") and hasattr(G, "edges"):
                return G
        if isinstance(G, dict) and "graph" in G and hasattr(G["graph"], "nodes"):
            return G["graph"]
        st.warning(f"Graph loader returned unexpected type: {type(G)}; using fallback.")
        return None
    except Exception as e:
        st.warning(f"Graph load error: {e}")
        return None

# ---------------- UI: header & map rendering ----------------
col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
with col_header1:
    st.title("🛡️ CrowdShield — AI Disaster Copilot")
with col_header2:
    status_color = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Critical": "🔴"}.get(severity, "⚪")
    st.metric(i18n["live_status"], f"{status_color} {severity}")
with col_header3:
    update_time = st.session_state.last_update.strftime("%H:%M:%S")
    st.caption(f"Last update: {update_time}")
    if st.session_state.auto_refresh_enabled:
        st.caption(f"🔄 Auto-refresh: {st.session_state.refresh_interval}s")

st.markdown("---")

left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader(i18n["map"])
    center_point = STATE_CENTERS.get(state, (9.931233, 76.267304))

    # Build base map via ux helper
    try:
        m = ux.create_base_map(center_point=center_point, zoom_start=12)
        if m is None:
            m = folium.Map(location=center_point, zoom_start=12, tiles="OpenStreetMap")
    except Exception as e:
        st.warning(f"ux.create_base_map failed: {e}")
        m = folium.Map(location=center_point, zoom_start=12, tiles="OpenStreetMap")

    # Add hazards, shelters, crowd points
    try:
        ux.add_hazards_to_map(m, hazards, i18n=i18n)
    except Exception as e:
        st.warning(f"Could not add hazards: {e}")

    try:
        ux.add_shelters_to_map(m, shelters, i18n=i18n)
    except Exception as e:
        st.warning(f"Could not add shelters: {e}")

    try:
        if crowd_sim is not None and not crowd_sim.empty:
            for _, c in crowd_sim.iterrows():
                try:
                    folium.CircleMarker(location=[float(c["lat"]), float(c["lon"])], radius=5, color="#1f77b4", fill=True, fill_color="#1f77b4", tooltip=f'Crowd {c.get("id","?")} • {int(c.get("people",0))} people').add_to(m)
                except Exception:
                    continue
    except Exception as e:
        st.warning(f"Could not add crowd points: {e}")

    # Origin
    simulate_live = st.checkbox("Simulate live location (mock device)", value=True)
    origin = simulate_live_location(state) if simulate_live else (gps_mock.get_mock_location_for_state(state) or (9.931233, 76.267304))
    try:
        ux.add_origin_to_map(m, origin, i18n=i18n)
    except Exception:
        try:
            folium.Marker(location=origin, tooltip="You (origin)").add_to(m)
        except Exception:
            pass

    # Nearest shelter
    try:
        shelter_rows = []
        if shelters is not None and not shelters.empty:
            for _, r in shelters.iterrows():
                try:
                    shelter_rows.append((float(r.lat), float(r.lon), r.get("name", "Shelter")))
                except Exception:
                    continue
        if shelter_rows:
            target = min(shelter_rows, key=lambda s: haversine_km(origin, (s[0], s[1])))
            target_coord = (target[0], target[1])
            target_name = target[2]
            dist_km = haversine_km(origin, target_coord)
            eta_min = int((dist_km / 4.5) * 60)
        else:
            target_coord = center_point
            target_name = "Fallback Shelter"
            dist_km = haversine_km(origin, target_coord)
            eta_min = int((dist_km / 4.5) * 60)
    except Exception as e:
        st.warning(f"Nearest shelter selection failed: {e}")
        target_coord = center_point
        target_name = "Fallback Shelter"
        dist_km = 0.0
        eta_min = 0

    # Routing (defensive)
    route = None
    route_mode_used = route_mode
    if find_route:
        G = safe_load_graph(online=not offline_mode, center_point=center_point)
        if G is None:
            try:
                route = routing.grid_route_fallback(origin, target_coord)
                route_mode_used = "Grid fallback (no graph)"
            except Exception:
                steps = 20
                lat1, lon1 = origin
                lat2, lon2 = target_coord
                route = [(lat1 + (lat2 - lat1) * i / steps, lon1 + (lon2 - lon1) * i / steps) for i in range(steps + 1)]
                route_mode_used = "Straight-line fallback (no graph)"
        else:
            try:
                G_blocked = routing.block_edges_by_hazards(G, hazards) if hazards is not None else G
                if route_mode == "Shortest" and hasattr(routing, "compute_shortest_path"):
                    route = routing.compute_shortest_path(G_blocked, origin, target_coord)
                elif route_mode == "Fastest" and hasattr(routing, "compute_fastest_path"):
                    route = routing.compute_fastest_path(G_blocked, origin, target_coord)
                elif route_mode == "Safest" and hasattr(routing, "compute_safest_path"):
                    route = routing.compute_safest_path(G_blocked, origin, target_coord, hazards)
                else:
                    route = routing.grid_route_fallback(origin, target_coord)
                    route_mode_used = "Grid fallback (compute_* missing)"
                if not route or len(route) < 2:
                    route = routing.grid_route_fallback(origin, target_coord)
                    route_mode_used = "Grid fallback (invalid route)"
            except Exception as e:
                st.warning(f"Routing failed: {e}")
                try:
                    route = routing.grid_route_fallback(origin, target_coord)
                    route_mode_used = "Grid fallback (exception)"
                except Exception:
                    steps = 20
                    lat1, lon1 = origin
                    lat2, lon2 = target_coord
                    route = [(lat1 + (lat2 - lat1) * i / steps, lon1 + (lon2 - lon1) * i / steps) for i in range(steps + 1)]
                    route_mode_used = "Straight-line fallback (exception)"

    # Add route and highlight
    try:
        ux.add_route_to_map(m, route, i18n=i18n) if route else None
    except Exception:
        try:
            if route:
                folium.PolyLine(locations=[(pt[0], pt[1]) for pt in route], color="green", weight=4).add_to(m)
        except Exception:
            pass

    try:
        folium.CircleMarker(location=target_coord, radius=8, color="purple", fill=True, fillColor="purple", tooltip=f"Target: {target_name}").add_to(m)
    except Exception:
        pass

    try:
        ux.add_reports_to_map(m, st.session_state.get("reports", []), i18n=i18n)
    except Exception:
        for r in st.session_state.get("reports", []):
            try:
                folium.Marker(location=(r["lat"], r["lon"]), tooltip=f"{r['type']} ({r['severity']})").add_to(m)
            except Exception:
                continue

    # Render map
    try:
        ux.render_map(m, height=600)
    except Exception as e:
        st.error(f"Map rendering error: {e}")
        st.exception(e)

with right_col:
    severity_colors = {"Low": "#2ECC71", "Medium": "#F5B041", "High": "#E67E22", "Critical": "#C0392B"}
    st.subheader(i18n["severity"])
    color = severity_colors.get(severity, "#bdc3c7")
    st.markdown(f"<div style='padding:12px;border-radius:8px;background:{color};color:white;font-weight:bold;text-align:center;font-size:18px;box-shadow:0 4px 6px rgba(0,0,0,0.1)'>{severity}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**" + i18n["drivers"] + ":**")
    driver_icons = {"rainfall": "🌧️", "wind": "💨", "flood": "🌊", "crowd": "👥", "density": "📊"}
    for d in drivers + crowd_drivers:
        icon = "⚠️"
        for key, emoji in driver_icons.items():
            if key.lower() in str(d).lower():
                icon = emoji
                break
        st.write(f"{icon} {d}")

    st.markdown("---")
    try:
        advisory_en = llm_insights.generate_advisory(severity, drivers + crowd_drivers, role=role)
    except Exception:
        advisory_en = "Unable to produce advisory at this time."

    advisory_out = advisory_en
    if lang != "en":
        try:
            advisory_out = translate.translate(advisory_en, dest=lang) if hasattr(translate, "translate") else advisory_en
        except Exception:
            advisory_out = advisory_en

    st.subheader(i18n["advisory"])
    st.info(advisory_out)

    # Play TTS alert if requested
    if play_alert:
        try:
            nav_msg_en = f"Current risk level is {severity}. Nearest shelter {target_name} is {dist_km:.1f} kilometers away, approximately {eta_min} minutes on foot."
            if route:
                nav_msg_en += f" Using {route_mode_used} route. Follow the marked path and avoid hazards."
            full_msg_en = f"{nav_msg_en} Advisory: {advisory_en}"
            tts_text = full_msg_en
            if lang != "en":
                try:
                    tts_text = translate.translate(full_msg_en, dest=lang)
                except Exception:
                    tts_text = full_msg_en
            tts_lang = lang if lang in ("en", "hi", "ml", "ta") else "en"
            ok = play_and_stream_tts(tts_text, lang=tts_lang, cooldown_seconds=3)
            if ok:
                st.success("🔊 Playing alert")
            else:
                st.warning("TTS generation failed or produced text fallback.")
        except Exception as e:
            st.warning(f"TTS error: {e}")

    st.markdown("---")
    st.subheader(i18n["recommendations"])
    for i, r in enumerate(recommendations, 1):
        st.write(f"{i}. {r}")

    st.markdown("---")
    st.subheader(i18n["nearest"])
    st.markdown(f"**{target_name}**")
    col_dist, col_eta = st.columns(2)
    with col_dist:
        st.metric(i18n["distance"], f"{dist_km:.2f} km")
    with col_eta:
        st.metric(i18n["eta"], f"~{eta_min} min")

    if route:
        st.markdown("---")
        st.subheader(i18n["instructions"])
        for i, pt in enumerate(route[:20], 1):
            st.write(f"📍 Step {i}: ({pt[0]:.5f}, {pt[1]:.5f})")
        if len(route) > 20:
            st.caption(f"... and {len(route) - 20} more steps")
        st.caption(f"Mode: {route_mode_used}")

# ---------------- Charts & Footer ----------------
if show_charts and st.session_state.risk_history:
    st.markdown("---")
    st.subheader(i18n["history"])
    df_history = pd.DataFrame(st.session_state.risk_history)
    if not df_history.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_history["timestamp"], y=df_history["disaster_score"], mode='lines+markers', name='Disaster Risk', line=dict(color='#E67E22', width=2)))
        fig.add_trace(go.Scatter(x=df_history["timestamp"], y=df_history["crowd_score"], mode='lines+markers', name='Crowd Risk', line=dict(color='#3498DB', width=2)))
        fig.add_trace(go.Scatter(x=df_history["timestamp"], y=df_history["combined"], mode='lines+markers', name='Combined Risk', line=dict(color='#E74C3C', width=3)))
        fig.update_layout(title="Risk Scores Over Time", xaxis_title="Time", yaxis_title="Risk Score (0-1)", hovermode='x unified', height=300)
        st.plotly_chart(fig)

    st.markdown("### Current Risk Breakdown")
    risk_col1, risk_col2, risk_col3 = st.columns(3)
    with risk_col1:
        st.metric("Disaster Risk", f"{disaster_score*100:.1f}%")
    with risk_col2:
        st.metric("Crowd Risk", f"{crowd_score*100:.1f}%")
    with risk_col3:
        combined_risk = max(disaster_score, crowd_score * 0.9)
        st.metric("Combined Risk", f"{combined_risk*100:.1f}%")

st.markdown("---")
st.subheader(i18n.get("safety_methods", "Safety methods"))
safety_tips = ["🏔️ Move to higher ground and avoid flood-prone areas", "🚫 Do not walk or drive through floodwaters", "🚪 In crowds, stay near exits and avoid dense clusters", "🎒 Carry ID, medicines, and an emergency kit", "📱 Follow official instructions; prefer SMS/low-bandwidth channels in outages", "🔋 Keep devices charged and have backup power", "👥 Stay in groups and inform others of your location"]
for tip in safety_tips:
    st.write(tip)

st.markdown("---")
st.caption(f"🔄 Auto-refresh: {'ON' if st.session_state.auto_refresh_enabled else 'OFF'} | 📊 Charts: {'ON' if show_charts else 'OFF'} | 🌐 Mode: {'Offline' if offline_mode else 'Online'} | 📍 State: {state}")
st.caption("Notes: TTS and SMS have fallbacks; check sidebar messages for errors.")
