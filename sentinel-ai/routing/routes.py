import math
from datetime import datetime





def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia aproximada entre dos coordenadas usando la fórmula Haversine.
    Retorna la distancia en kilómetros.
    """

    # Radio de la Tierra en kilómetros
    earth_radius = 6371

    # Convertir grados a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Diferencias
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Fórmula Haversine
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = earth_radius * c

    return round(distance, 2)


def generate_simple_route(start_lat, start_lon, end_lat, end_lon, points=10):
    """
    Genera una ruta simple entre punto A y punto B.
    Retorna una lista de coordenadas intermedias.
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


def get_traffic_factor(hour=None):
    """
    Calcula el factor de tráfico simulado según la hora.
    
    Horarios:
    07:00 - 09:00 -> alto, factor 1.6
    12:00 - 14:00 -> medio, factor 1.3
    18:00 - 20:00 -> alto, factor 1.5
    Otro horario -> bajo, factor 1.0
    """

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
    """
    Calcula el tiempo estimado de viaje.
    
    Fórmula:
    tiempo = distancia / velocidad_promedio

    El resultado se ajusta con el factor de tráfico.
    Retorna el tiempo en minutos.
    """

    if average_speed <= 0:
        raise ValueError("La velocidad promedio debe ser mayor a 0.")

    time_hours = distance_km / average_speed
    time_minutes = time_hours * 60

    adjusted_time = time_minutes * traffic_factor

    return round(adjusted_time, 2)


def estimate_fuel(distance_km, fuel_per_km=0.10):
    """
    Calcula el combustible estimado.
    
    Se asume:
    0.10 litros por kilómetro
    equivalente a 10 litros cada 100 km.
    """

    fuel = distance_km * fuel_per_km

    return round(fuel, 2)


def calculate_route_summary(start_lat, start_lon, end_lat, end_lon, hour=None):
    """
    Función principal para usar desde Flask.
    Recibe punto A y punto B.
    Retorna distancia, tiempo, combustible, tráfico y ruta.
    """

    distance = haversine_distance(start_lat, start_lon, end_lat, end_lon)

    traffic = get_traffic_factor(hour)

    estimated_time = estimate_time(
        distance_km=distance,
        average_speed=35,
        traffic_factor=traffic["factor"]
    )

    estimated_fuel = estimate_fuel(distance)

    route = generate_simple_route(
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon
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
        "distance_km": distance,
        "estimated_time_minutes": estimated_time,
        "estimated_fuel_liters": estimated_fuel,
        "traffic_level": traffic["level"],
        "traffic_factor": traffic["factor"],
        "route": route
    }



if __name__ == "__main__":
    # Coordenadas de ejemplo dentro de Santa Cruz de la Sierra
    start_lat = -17.7833
    start_lon = -63.1821

    end_lat = -17.7540
    end_lon = -63.1990

    result = calculate_route_summary(
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon,
        hour=8
    )

    print("Resumen de ruta:")
    print(result)