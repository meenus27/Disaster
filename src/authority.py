"""
Authority micro-playbook with dispatch simulation and ETA overlay.
Supports both role-based and severity-based playbooks.
"""
import math
import networkx as nx
from datetime import timedelta

PLAYBOOKS_ROLE = {
    "Local Authority": ["Issue public advisory", "Activate shelters", "Coordinate transport"],
    "First Responder": ["Dispatch ground team", "Prepare medical aid", "Coordinate with command"],
    "Community Leader": ["Open local shelter", "Broadcast instructions", "Assist elderly"]
}

PLAYBOOKS_SEVERITY = {
    "Critical": ["Dispatch Ambulance", "Deploy Rescue Boat"],
    "High": ["Dispatch Fire Truck", "Send Medical Team"],
    "Medium": ["Send Patrol", "Open Shelter"],
    "Low": ["Monitor Situation"]
}

def haversine_m(origin, target):
    """Compute haversine distance in meters."""
    lat1, lon1 = origin
    lat2, lon2 = target
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def dispatch(identifier, G, origin, target, speed_kmph=30):
    """
    Dispatch a resource and compute ETA overlay.
    identifier can be a role (e.g. 'Local Authority') or severity (e.g. 'Critical').
    Falls back to haversine if graph routing fails.
    """
    # Select actions
    actions = PLAYBOOKS_ROLE.get(identifier) or PLAYBOOKS_SEVERITY.get(identifier) or ["Monitor Situation"]
    
    # Try graph-based routing
    try:
        path = nx.shortest_path(G, origin, target, weight="length")
        length = sum(G.edges[u, v]["length"] for u, v in zip(path[:-1], path[1:]))
        eta_minutes = (length / 1000) / (speed_kmph / 60)
        return {
            "identifier": identifier,
            "actions": actions,
            "eta": round(eta_minutes, 1),
            "path": path,
            "distance_m": int(length)
        }
    except Exception:
        # Fallback: haversine
        dist_m = haversine_m(origin, target)
        speed_mps = (speed_kmph * 1000) / 3600
        eta_seconds = dist_m / speed_mps if speed_mps > 0 else None
        eta = timedelta(seconds=int(eta_seconds)) if eta_seconds else None
        return {
            "identifier": identifier,
            "actions": actions,
            "eta": str(eta) if eta else None,
            "path": [],
            "distance_m": int(dist_m)
        }
