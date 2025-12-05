"""
Crowd risk estimation using density heuristics with multilingual support.
"""

import pandas as pd
import yaml
from pathlib import Path

CONFIG = Path("configs/thresholds.yaml")

def _load_thresholds():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return {"crowd_density_per_m2": {"low": 0.5, "medium": 2, "high": 4}}

def score_crowd(crowd_df, trigger_surge=False, area_m2=1000.0, i18n=None):
    """
    Returns (score 0-1, drivers list).
    i18n: dictionary for multilingual labels (optional).
    """
    t = _load_thresholds()

    # Handle missing or empty data
    if crowd_df is None or crowd_df.empty:
        return 0.0, [i18n.get("no_data", "No crowd data") if i18n else "No crowd data"]

    if "people" not in crowd_df.columns:
        return 0.0, [i18n.get("missing_people", "Missing 'people' column") if i18n else "Missing 'people' column"]

    total_people = int(crowd_df["people"].sum())
    density = total_people / area_m2

    drivers = [
        f"{i18n.get('density','Density') if i18n else 'Density'}: {density:.2f} ppl/m2",
        f"Total people: {total_people}"
    ]

    score = 0.0
    if trigger_surge or density >= t["crowd_density_per_m2"]["high"]:
        score = 0.7
        drivers.append(i18n.get("high", "High density") if i18n else "High density")
    elif density >= t["crowd_density_per_m2"]["medium"]:
        score = 0.35
        drivers.append(i18n.get("medium", "Moderate density") if i18n else "Moderate density")
    else:
        drivers.append(i18n.get("low", "Low density") if i18n else "Low density")

    return min(1.0, score), drivers
