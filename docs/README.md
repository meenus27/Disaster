# 🛡️ CrowdShield — AI Disaster Copilot

An advanced, live, and interactive disaster management application with real-time risk assessment, routing, and multilingual support.

## ✨ Features

### 🎯 Core Features
- **Real-time Risk Assessment**: Dynamic disaster and crowd risk scoring
- **Interactive Maps**: Live folium maps with hazards, shelters, and routes
- **Smart Routing**: Shortest, fastest, and safest path computation
- **Multilingual Support**: English, Hindi, Malayalam, and Tamil
- **Live Updates**: Auto-refresh capability with customizable intervals
- **Interactive Charts**: Plotly visualizations for risk history and trends
- **Audio Alerts**: Text-to-speech advisories in multiple languages
- **SMS Integration**: Twilio integration for emergency alerts

### 🚀 Enhanced Interactive Features
- **Auto-Refresh**: Enable automatic updates with configurable intervals (2-30 seconds)
- **Live Status Indicators**: Real-time severity badges with color coding
- **Interactive Charts**: 
  - Time series risk score charts
  - Gauge indicators for risk levels
  - Risk distribution metrics
- **Dynamic Controls**: Sliders for weather conditions and crowd density simulation
- **Route Visualization**: Enhanced map markers and route styling
- **Real-time Data History**: Track risk scores over time (last 50 updates)

## 📋 Requirements

See `requirements.txt` for full dependency list. Key dependencies include:
- Streamlit >= 1.28.0
- Folium >= 0.14.0
- Plotly >= 5.17.0
- NetworkX >= 3.1
- GeoPandas >= 0.14.0
- OpenAI >= 1.0.0 (optional, for LLM advisories)
- Twilio >= 8.10.0 (optional, for SMS alerts)

## 🔧 Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd "Disaster Pitch"
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (optional):
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run the application:
```bash
streamlit run app.py
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following optional variables:

```env
# OpenWeatherMap API (for live weather data)
OPENWEATHER_API_KEY=your_api_key_here

# OpenAI API (for LLM advisories)
OPENAI_API_KEY=your_api_key_here

# Twilio (for SMS alerts)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_TO_NUMBER=+1234567890
```

### Data Files

The app expects data files in the `data/` directory:
- `hazard_zones_{state}.geojson` - Hazard zone polygons
- `safe_zones_{state}.csv` - Shelter locations (name, lat, lon, capacity)
- `crowd_sim_{state}.csv` - Crowd telemetry (id, lat, lon, people)

If files are missing, the app will use fallback sample data.

## 🎮 Usage

1. **Select Language**: Choose from English, Hindi, Malayalam, or Tamil
2. **Select State**: Choose the state for data visualization
3. **Adjust Controls**: 
   - Use sliders to simulate weather conditions (rainfall, wind speed)
   - Adjust crowd density slider to simulate crowd conditions
   - Enable/disable flood or crowd surge triggers
4. **Enable Auto-Refresh**: Toggle auto-refresh for live updates
5. **Compute Routes**: Click "Find Safe Route" to compute paths
6. **View Charts**: Enable interactive charts to see risk trends
7. **Send Alerts**: Use SMS alert button to send notifications

## 📊 Interactive Features

### Real-Time Updates
- Enable auto-refresh in the sidebar
- Set refresh interval (2-30 seconds)
- Risk scores update automatically
- Charts update with new data points

### Interactive Charts
- **Time Series**: Track disaster, crowd, and combined risk over time
- **Gauge Indicators**: Visual representation of current risk level
- **Risk Metrics**: Live dashboard with percentage breakdowns

### Map Features
- **Multiple Tile Layers**: Switch between OpenStreetMap, Stamen Terrain, and CartoDB
- **Enhanced Markers**: Color-coded hazards, shelters, and routes
- **Route Visualization**: Start/end markers and highlighted paths

## 🏗️ Project Structure

```
Disaster Pitch/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env.example          # Environment variable template
├── data/                 # Data directory
│   ├── alerts/          # Generated alerts and TTS files
│   ├── cache/           # Cached data
│   └── *.geojson        # Hazard zone files
│   └── *.csv            # Shelter and crowd data
├── src/                  # Source modules
│   ├── __init__.py
│   ├── data_loader.py   # Data loading utilities
│   ├── routing.py       # Route computation
│   ├── fusion_engine.py # Risk fusion logic
│   ├── llm_insights.py  # LLM advisory generation
│   ├── translate.py     # Translation utilities
│   ├── alerting.py      # SMS alerting
│   ├── ux.py            # Map UI components
│   ├── risk_disaster.py # Disaster risk scoring
│   ├── risk_crowd.py    # Crowd risk scoring
│   ├── tts.py           # Text-to-speech
│   ├── gps_mock.py      # GPS mock data
│   ├── satellite_sim.py # Satellite simulation
│   └── authority.py     # Authority playbooks
└── configs/             # Configuration files
    └── thresholds.yaml  # Risk thresholds
```

## 🎨 UI Enhancements

- **Modern Design**: Clean, intuitive interface with color-coded severity badges
- **Responsive Layout**: Wide layout optimized for maps and charts
- **Status Indicators**: Live status badges with emoji icons
- **Progress Bars**: Animated progress bars for risk scores
- **Tooltips**: Helpful hints and tips throughout the interface

## 🔒 Error Handling

The application includes comprehensive error handling:
- Graceful fallbacks for missing data files
- Offline mode support when APIs are unavailable
- Mock data generation when real data is missing
- Error messages with helpful guidance

## 🚧 Development Notes

- The app uses Streamlit session state for maintaining history and settings
- Auto-refresh uses `st.rerun()` with time-based triggers
- All route computations include error handling and fallbacks
- Map rendering supports multiple tile layers for flexibility

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contributing guidelines here]

## 📧 Support

[Add support contact information here]

---

**Note**: This is a demo application. For production use, ensure proper security measures, API key management, and data validation are in place.

