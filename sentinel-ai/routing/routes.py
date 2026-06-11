import math
from datetime import datetime
from itertools import islice

import networkx as nx
import osmnx as ox


def haversine_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(earth_radius * c, 2)


def get_traffic_factor(hour=None):
    if hour is None:
        current_hour = datetime.now().hour
    else:
        if isinstance(hour, str) and ":" in hour:
            current_hour = int(hour.split(":")[0])
        else:
            current_hour = int(hour)

    if 7 <= current_hour < 9:
        return {"level": "alto", "factor": 1.6}
    elif 12 <= current_hour < 14:
        return {"level": "medio", "factor": 1.3}
    elif 18 <= current_hour < 20:
        return {"level": "alto", "factor": 1.5}
    else:
        return {"level": "bajo", "factor": 1.0}


def estimate_time(distance_km, average_speed=35, traffic_factor=1.0):
    time_hours = distance_km / average_speed
    time_minutes = time_hours * 60
    return round(time_minutes * traffic_factor, 2)


def estimate_fuel(distance_km, fuel_per_km=0.10):
    return round(distance_km * fuel_per_km, 2)


def generate_simple_route(start_lat, start_lon, end_lat, end_lon, points=10):
    route = []

    for i in range(points + 1):
        fraction = i / points

        lat = start_lat + (end_lat - start_lat) * fraction
        lon = start_lon + (end_lon - start_lon) * fraction

        route.append({
            "lat": round(lat, 6),
            "lon": round(lon, 6)
        })

    return route


def graph_to_simple_digraph(graph):
    """
    Convierte el grafo de OSMnx a un DiGraph simple.
    Esto permite usar k-shortest paths con NetworkX.
    """
    simple_graph = nx.DiGraph()

    for node, data in graph.nodes(data=True):
        simple_graph.add_node(node, **data)

    for u, v, data in graph.edges(data=True):
        length = data.get("length", 1)

        if simple_graph.has_edge(u, v):
            if length < simple_graph[u][v].get("length", float("inf")):
                simple_graph[u][v]["length"] = length
        else:
            simple_graph.add_edge(u, v, length=length)

    return simple_graph


def path_to_coordinates(graph, path):
    route = []

    for node in path:
        route.append({
            "lat": round(graph.nodes[node]["y"], 6),
            "lon": round(graph.nodes[node]["x"], 6)
        })

    return route


def calculate_path_distance(graph, path):
    distance_meters = 0

    for u, v in zip(path[:-1], path[1:]):
        edge_data = graph.get_edge_data(u, v)

        if edge_data:
            distance_meters += edge_data.get("length", 0)

    return round(distance_meters / 1000, 2)


def generate_candidate_routes(start_lat, start_lon, end_lat, end_lon, hour=None, max_routes=3):
    """
    Genera varias rutas candidatas reales usando OSMnx + NetworkX.
    Luego el solver elige cuál ruta conviene usar.
    """
    traffic = get_traffic_factor(hour)

    center_lat = (start_lat + end_lat) / 2
    center_lon = (start_lon + end_lon) / 2

    straight_distance_km = haversine_distance(
        start_lat,
        start_lon,
        end_lat,
        end_lon
    )

    dist_meters = max(2000, int(straight_distance_km * 1000 * 1.8))

    graph = ox.graph_from_point(
        (center_lat, center_lon),
        dist=dist_meters,
        network_type="drive",
        simplify=True
    )

    origin_node = ox.distance.nearest_nodes(
        graph,
        X=start_lon,
        Y=start_lat
    )

    destination_node = ox.distance.nearest_nodes(
        graph,
        X=end_lon,
        Y=end_lat
    )

    simple_graph = graph_to_simple_digraph(graph)

    paths = list(islice(
        nx.shortest_simple_paths(
            simple_graph,
            origin_node,
            destination_node,
            weight="length"
        ),
        max_routes
    ))

    route_names = [
        "Ruta 1 - Menor distancia",
        "Ruta 2 - Alternativa vial",
        "Ruta 3 - Alternativa secundaria"
    ]

    candidates = []

    for index, path in enumerate(paths):
        distance = calculate_path_distance(simple_graph, path)
        time_min = estimate_time(
            distance_km=distance,
            average_speed=35,
            traffic_factor=traffic["factor"]
        )
        fuel_liters = estimate_fuel(distance)

        candidates.append({
            "route_id": index,
            "route_name": route_names[index] if index < len(route_names) else f"Ruta {index + 1}",
            "route": path_to_coordinates(simple_graph, path),
            "distance_km": distance,
            "estimated_time_minutes": time_min,
            "estimated_fuel_liters": fuel_liters,
            "traffic_level": traffic["level"],
            "traffic_factor": traffic["factor"],
            "route_type": "street"
        })

    return candidates


def generate_fallback_candidates(start_lat, start_lon, end_lat, end_lon, hour=None):
    """
    Si OSMnx falla, genera una ruta simple para no romper la demo.
    """
    traffic = get_traffic_factor(hour)

    distance = haversine_distance(
        start_lat,
        start_lon,
        end_lat,
        end_lon
    )

    route = generate_simple_route(
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon
    )

    time_min = estimate_time(
        distance_km=distance,
        average_speed=35,
        traffic_factor=traffic["factor"]
    )

    fuel_liters = estimate_fuel(distance)

    return [
        {
            "route_id": 0,
            "route_name": "Ruta simple de respaldo",
            "route": route,
            "distance_km": distance,
            "estimated_time_minutes": time_min,
            "estimated_fuel_liters": fuel_liters,
            "traffic_level": traffic["level"],
            "traffic_factor": traffic["factor"],
            "route_type": "simple"
        }
    ]


def calculate_route_summary(start_lat, start_lon, end_lat, end_lon, hour=None):
    """
    Función principal para Flask.

    Ahora genera varias rutas candidatas y deja que el solver elija
    la mejor combinación ruta-patrulla.
    """
    try:
        candidates = generate_candidate_routes(
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            hour=hour,
            max_routes=3
        )
    except Exception as error:
        print("Error usando OSMnx. Se usará ruta simple:", error)

        candidates = generate_fallback_candidates(
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            hour=hour
        )

    return {
        "start": {
            "lat": start_lat,
            "lon": start_lon
        },
        "end": {
            "lat": end_lat,
            "lon": end_lon
        },
        "candidate_routes": candidates
    }