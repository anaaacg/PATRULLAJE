from flask import Flask, render_template, request, jsonify
from routing.routes import calculate_route_summary
from optimization.solver import assign_patrol

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

    route_data = calculate_route_summary(
        start_lat=start["lat"],
        start_lon=start_lng,
        end_lat=end["lat"],
        end_lon=end_lng,
        hour=hour
    )

    assigned_patrol, total_cost = assign_patrol(
        distance_km=route_data["distance_km"],
        traffic_factor=route_data["traffic_factor"]
    )

    route_for_map = [
        [point["lat"], point["lon"]]
        for point in route_data["route"]
    ]

    return jsonify({
        "route": route_for_map,
        "coordenadas": route_for_map,

        "distance_km": route_data["distance_km"],
        "distancia": f'{route_data["distance_km"]} km',

        "time_min": route_data["estimated_time_minutes"],
        "tiempo": f'{route_data["estimated_time_minutes"]} min',

        "fuel_liters": route_data["estimated_fuel_liters"],
        "combustible": f'{route_data["estimated_fuel_liters"]} L',

        "traffic_level": route_data["traffic_level"],
        "trafico": route_data["traffic_level"].capitalize(),

        "traffic_factor": route_data["traffic_factor"],

        "assigned_patrol": assigned_patrol,
        "patrulla": assigned_patrol,

        "cost": round(total_cost, 2),
        "costo": round(total_cost, 2)
    })


if __name__ == "__main__":
    app.run(debug=True)