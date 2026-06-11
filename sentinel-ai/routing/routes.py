import math
from datetime import datetime

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
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(earth_radius * c, 2)


def generate_simple_route(start_lat, start_lon, end_lat, end_lon, points=10):
    """
    Ruta de respaldo en línea recta si OSMnx falla.
    """
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


def generate_street_route(start_lat, start_lon, end_lat, end_lon):
    """
    Genera una ruta real por calles usando OpenStreetMap.
    Descarga solo un área pequeña alrededor de los puntos para que sea más rápido.
    """
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

    route_nodes = nx.shortest_path(
        graph,
        origin_node,
        destination_node,
        weight="length"
    )

    route = []

    for node in route_nodes:
        route.append({
            "lat": round(graph.nodes[node]["y"], 6),
            "lon": round(graph.nodes[node]["x"], 6)
        })

    distance_meters = 0

    for u, v in zip(route_nodes[:-1], route_nodes[1:]):
        edge_data = graph.get_edge_data(u, v)

        if edge_data:
            first_edge = list(edge_data.values())[0]
            distance_meters += first_edge.get("length", 0)

    distance_km = round(distance_meters / 1000, 2)

    return route, distance_km


def get_traffic_factor(hour=None):
    if hour is None:
        current_hour = datetime.now().hour
    else:
        if isinstance(hour, str) and ":" in hour:
            current_hour = int(hour.split(":")[0])
        else:
            current_hour = int(hour)

    if 7 <= current_hour < 9:
        return {
            "level": "alto",
            "factor": 1.6
        }

    elif 12 <= current_hour < 14:
        return {
            "level": "medio",
            "factor": 1.3
        }

    elif 18 <= current_hour < 20:
        return {
            "level": "alto",
            "factor": 1.5
        }

    else:
        return {
            "level": "bajo",
            "factor": 1.0
        }


def estimate_time(distance_km, average_speed=35, traffic_factor=1.0):
    if average_speed <= 0:
        raise ValueError("La velocidad promedio debe ser mayor a 0.")

    time_hours = distance_km / average_speed
    time_minutes = time_hours * 60
    adjusted_time = time_minutes * traffic_factor

    return round(adjusted_time, 2)


def estimate_fuel(distance_km, fuel_per_km=0.10):
    fuel = distance_km * fuel_per_km
    return round(fuel, 2)


def calculate_route_summary(start_lat, start_lon, end_lat, end_lon, hour=None):
    """
    Función principal para Flask.
    Primero intenta calcular por calles reales.
    Si falla, usa línea recta para no romper la demo.
    """
    traffic = get_traffic_factor(hour)

    try:
        route, distance = generate_street_route(
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon
        )

        route_type = "street"

    except Exception as error:
        print("Error usando OSMnx. Se usará ruta simple:", error)

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

        route_type = "simple"

    estimated_time = estimate_time(
        distance_km=distance,
        average_speed=35,
        traffic_factor=traffic["factor"]
    )

    estimated_fuel = estimate_fuel(distance)

    return {
        "start": {
            "lat": start_lat,
            "lon": start_lon
        },
        "end": {
            "lat": end_lat,
            "lon": end_lon
        },
        "distance_km": distance,
        "estimated_time_minutes": estimated_time,
        "estimated_fuel_liters": estimated_fuel,
        "traffic_level": traffic["level"],
        "traffic_factor": traffic["factor"],
        "route": route,
        "route_type": route_type
    }


if __name__ == "__main__":
    result = calculate_route_summary(
        start_lat=-17.7833,
        start_lon=-63.1821,
        end_lat=-17.7540,
        end_lon=-63.1990,
        hour="08:00"
    )

    print(result)