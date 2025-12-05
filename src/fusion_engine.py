"""
Fusion engine: combine disaster + crowd scores into severity tier
and multilingual recommendations with safe fallbacks.
"""

def fuse(disaster_score, crowd_score, i18n=None):
    # Weighted combination of disaster and crowd scores
    combined = max(disaster_score, crowd_score * 0.9)

    # Helper to safely fetch translations or fall back to English
    def _(key, default):
        if i18n and isinstance(i18n, dict):
            return i18n.get(key, default)
        return default

    # Decide severity tier and recommendations
    if combined < 0.2:
        tier = _("low", "Low")
        recommendations = [
            _("rec_monitor", "Monitor conditions"),
            _("rec_updates", "Send updates to residents")
        ]
    elif combined < 0.5:
        tier = _("medium", "Medium")
        recommendations = [
            _("rec_prepare", "Prepare shelters"),
            _("rec_limit", "Advise limited movement")
        ]
    elif combined < 0.8:
        tier = _("high", "High")
        recommendations = [
            _("rec_evac", "Activate evacuation protocol"),
            _("rec_vulnerable", "Prioritize vulnerable groups")
        ]
    else:
        tier = _("critical", "Critical")
        recommendations = [
            _("rec_immediate", "Immediate evacuation"),
            _("rec_services", "Deploy emergency services"),
            _("rec_broadcast", "Activate emergency broadcast")
        ]

    return tier, recommendations
