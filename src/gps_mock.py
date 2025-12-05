"""
GPS mock to provide sample origin points.

Previously this only returned coordinates around Kochi, Kerala.
To make the demo feel more realistic across India, we support
state-based mock locations while keeping the old API for backward
compatibility.
"""

# Default waypoints around Kochi (legacy behaviour)
WAYPOINTS = [
    (9.931233, 76.267304),
    (9.932000, 76.268000),
    (9.930500, 76.265500),
]


def get_mock_location(index: int = 0):
    """
    Return a mock location from the legacy Kochi waypoints.

    Kept for backward compatibility – other modules may still import
    this directly.
    """
    return WAYPOINTS[index % len(WAYPOINTS)]


# Approximate central points for supported states
STATE_WAYPOINTS = {
    "Kerala": (10.1632, 76.6413),
    "Tamil Nadu": (11.1271, 78.6569),
    "Karnataka": (15.3173, 75.7139),
    "Maharashtra": (19.7515, 75.7139),
    "Uttar Pradesh": (26.8467, 80.9462),
    "Delhi": (28.6139, 77.2090),
    "West Bengal": (22.9868, 87.8550),
    "Rajasthan": (27.0238, 74.2179),
}


def get_mock_location_for_state(state: str):
    """
    Return a deterministic mock location for the given state.

    Falls back to the first legacy waypoint (Kochi) if the state
    is unknown, so that the rest of the app continues to work.
    """
    return STATE_WAYPOINTS.get(state, WAYPOINTS[0])