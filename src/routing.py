import os
import osmnx as ox
import networkx as nx
from shapely.geometry import Point

DATA_PATH = os.path.join("data", "local_graph.graphml")

def load_graph(online=True, center=(9.9312, 76.2673), dist=1500):
    """
    Load OSMnx graph or local cached graph.
    Falls back to grid graph if OSMnx fails.
    """
    if not online and os.path.exists(DATA_PATH):
        return ox.load_graphml(DATA_PATH)
    try:
        G = ox.graph_from_point(center, dist=dist, network_type="walk")
        ox.save_graphml(G, DATA_PATH)
        return G
    except Exception as e:
        print(f"Graph loading error: {e}")
        return build_grid_graph()

def build_grid_graph(size=10):
    """Fallback simple grid graph for offline demo."""
    G = nx.grid_2d_graph(size, size)
    for (u, v) in G.edges():
        G.edges[u, v]["length"] = 1
    return G

def block_edges_by_hazards(G, hazard_polygons):
    """
    Remove edges whose midpoint lies inside hazard polygons.
    Returns number of blocked edges.
    """
    if G is None or hazard_polygons is None:
        return 0
    blocked = 0
    for u, v, data in list(G.edges(data=True)):
        try:
            if "geometry" in data:
                midpoint = data["geometry"].centroid
            else:
                midpoint = Point((G.nodes[u]["x"] + G.nodes[v]["x"]) / 2,
                                 (G.nodes[u]["y"] + G.nodes[v]["y"]) / 2)
            for poly in hazard_polygons:
                if poly.contains(midpoint):
                    G.remove_edge(u, v)
                    blocked += 1
                    break
        except Exception as e:
            print(f"Edge hazard check error: {e}")
    return blocked

def compute_shortest_path(G, origin, target, weight="length"):
    """
    Compute shortest path. Handles errors gracefully.
    """
    if G is None:
        return None
    try:
        origin_node = ox.nearest_nodes(G, origin[1], origin[0]) if hasattr(ox, 'nearest_nodes') else origin
        target_node = ox.nearest_nodes(G, target[1], target[0]) if hasattr(ox, 'nearest_nodes') else target
        path = nx.shortest_path(G, origin_node, target_node, weight=weight)
        return _nodes_to_coords(G, path, origin, target)
    except Exception as e:
        print(f"Shortest path error: {e}")
        return None

def compute_fastest_path(G, origin, target):
    """
    Compute fastest path by travel time. Handles errors gracefully.
    """
    if G is None:
        return None
    try:
        for u, v, k, data in G.edges(keys=True, data=True):
            speed = data.get("speed_kph", 30)
            if "length" in data and speed > 0:
                data["time"] = data["length"] / (speed * 1000 / 3600)
            else:
                data["time"] = data.get("length", 100) / 10
        origin_node = ox.nearest_nodes(G, origin[1], origin[0]) if hasattr(ox, 'nearest_nodes') else origin
        target_node = ox.nearest_nodes(G, target[1], target[0]) if hasattr(ox, 'nearest_nodes') else target
        path = nx.shortest_path(G, origin_node, target_node, weight="time")
        return _nodes_to_coords(G, path, origin, target)
    except Exception as e:
        print(f"Fastest path error: {e}")
        return None

def compute_safest_path(G, origin, target):
    """
    Compute safest path avoiding hazards. Handles errors gracefully.
    """
    if G is None:
        return None
    try:
        for u, v, k, data in G.edges(keys=True, data=True):
            hazard_penalty = data.get("hazard_penalty", 0)
            length = data.get("length", 100)
            data["safe_weight"] = length * (1 + hazard_penalty)
        origin_node = ox.nearest_nodes(G, origin[1], origin[0]) if hasattr(ox, 'nearest_nodes') else origin
        target_node = ox.nearest_nodes(G, target[1], target[0]) if hasattr(ox, 'nearest_nodes') else target
        path = nx.shortest_path(G, origin_node, target_node, weight="safe_weight")
        return _nodes_to_coords(G, path, origin, target)
    except Exception as e:
        print(f"Safest path error: {e}")
        return None

def grid_route_fallback(origin, target):
    """Crude straight-line fallback."""
    return [origin, target]

def _nodes_to_coords(G, path, origin, target):
    """Helper: convert node IDs to coordinates."""
    coords = []
    for node in path:
        if isinstance(node, tuple):
            coords.append(node)
        else:
            try:
                coords.append((G.nodes[node].get('y', origin[0]), G.nodes[node].get('x', origin[1])))
            except:
                coords.append(origin)
    return coords if coords else [origin, target]
