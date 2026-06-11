from flask import Flask, render_template, request, jsonify

from optimization.solver import optimize_route_and_patrol
from routing.routes import calculate_route_summary


app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/calculate-route", methods=["POST"])
def calculate_route():
    data = request.get_json()

    start = data.get("start") or data.get("punto_a")
    end = data.get("end") or data.get("punto_b")
    hour = data.get("hour") or data.get("hora") or "18:30"

    if not start or not end:
        return jsonify({"error": "Faltan punto A o punto B"}), 400

    start_lng = start.get("lng", start.get("lon"))
    end_lng = end.get("lng", end.get("lon"))

    route_summary = calculate_route_summary(
        start_lat=start["lat"],
        start_lon=start_lng,
        end_lat=end["lat"],
        end_lon=end_lng,
        hour=hour
    )

    candidate_routes = route_summary["candidate_routes"]

    optimization_result = optimize_route_and_patrol(candidate_routes)

    selected_route = optimization_result["selected_route"]

    distance_km = selected_route.get("distance_km", selected_route.get("distance", 0))
    time_min = selected_route.get("estimated_time_minutes", selected_route.get("time_min", 0))
    fuel_liters = selected_route.get("estimated_fuel_liters", selected_route.get("fuel_liters", 0))
    traffic_level = selected_route.get("traffic_level", "bajo")
    traffic_factor = selected_route.get("traffic_factor", 1.0)
    route_type = selected_route.get("route_type", "street")

    route_points = selected_route.get("route", [])

    route_for_map = [
        [point["lat"], point["lon"]]
        for point in route_points
    ]

    return jsonify({
        "route": route_for_map,
        "coordenadas": route_for_map,

        "route_name": optimization_result.get("selected_route_name", "Ruta optimizada"),
        "ruta_seleccionada": optimization_result.get("selected_route_name", "Ruta optimizada"),

        "distance_km": distance_km,
        "distancia": f"{distance_km} km",

        "time_min": time_min,
        "tiempo": f"{time_min} min",

        "fuel_liters": fuel_liters,
        "combustible": f"{fuel_liters} L",

        "traffic_level": traffic_level,
        "trafico": str(traffic_level).capitalize(),

        "traffic_factor": traffic_factor,

        "assigned_patrol": optimization_result["assigned_patrol"],
        "patrulla": optimization_result["assigned_patrol"],

        "cost": optimization_result["total_cost"],
        "costo": optimization_result["total_cost"],

        "route_type": route_type,
        "candidate_count": len(candidate_routes)
    })


if __name__ == "__main__":
    app.run(debug=True)