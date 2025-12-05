"""
Disaster risk scoring using thresholds with multilingual support.
"""

import yaml
from pathlib import Path

CONFIG = Path("configs/thresholds.yaml")

def _load_thresholds():
    if CONFIG.exists():
        with open(CONFIG, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {
        "rainfall_mm": {"low": 10, "medium": 25, "high": 50},
        "wind_kph": {"low": 20, "medium": 40, "high": 80}
    }

def score_disaster(weather, trigger_flood=False, i18n=None):
    """
    Returns (score 0-1, drivers list).
    weather: dict with rainfall_mm, wind_kph, state, timestamp.
    """
    t = _load_thresholds()
    rainfall = weather.get("rainfall_mm", 0)
    wind = weather.get("wind_kph", 0)

    score = 0.0
    drivers = []

    # Rainfall scoring
    if rainfall >= t["rainfall_mm"]["high"] or trigger_flood:
        score += 0.6
        drivers.append(f"{i18n.get('risk_disaster','Disaster risk') if i18n else 'Disaster risk'}: Severe rainfall ({rainfall} mm)")
    elif rainfall >= t["rainfall_mm"]["medium"]:
        score += 0.3
        drivers.append(f"Moderate rainfall ({rainfall} mm)")
    else:
        drivers.append(f"Low rainfall ({rainfall} mm)")

    # Wind scoring
    if wind >= t["wind_kph"]["high"]:
        score += 0.4
        drivers.append(f"High winds ({wind:.1f} kph)")
    elif wind >= t["wind_kph"]["medium"]:
        score += 0.15
        drivers.append(f"Moderate winds ({wind:.1f} kph)")
    else:
        drivers.append(f"Low winds ({wind:.1f} kph)")

    return min(1.0, score), drivers
