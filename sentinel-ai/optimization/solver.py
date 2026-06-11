from pathlib import Path

import pandas as pd
import pyomo.environ as pyo


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "patrols.csv"


def read_patrols():
    df = pd.read_csv(DATA_PATH)

    if "patrol" in df.columns:
        patrols = df["patrol"].astype(str).tolist()
    elif "patrol_name" in df.columns:
        patrols = df["patrol_name"].astype(str).tolist()
    elif "patrol_id" in df.columns:
        patrols = df["patrol_id"].astype(str).tolist()
    else:
        raise ValueError(
            "El archivo patrols.csv debe contener una columna 'patrol', 'patrol_name' o 'patrol_id'."
        )

    if "load" not in df.columns:
        raise ValueError("El archivo patrols.csv debe contener una columna 'load'.")

    patrol_load = dict(zip(patrols, df["load"]))

    return patrols, patrol_load


def optimize_route_and_patrol(candidate_routes):
    """
    Modelo de optimización con Pyomo + GLPK.

    El solver elige simultáneamente:
    - qué ruta candidata utilizar
    - qué patrulla asignar

    Variable:
    x[r,p] = 1 si se elige la ruta r y la patrulla p
    x[r,p] = 0 en otro caso
    """

    patrols, patrol_load = read_patrols()

    routes = [route["route_id"] for route in candidate_routes]

    route_data = {
        route["route_id"]: route
        for route in candidate_routes
    }

    penalty_load = 10
    weight_distance = 1.0
    weight_time = 0.4
    weight_fuel = 8.0
    weight_traffic = 2.0

    model = pyo.ConcreteModel()

    model.R = pyo.Set(initialize=routes)
    model.P = pyo.Set(initialize=patrols)

    model.x = pyo.Var(model.R, model.P, domain=pyo.Binary)

    def cost(route_id, patrol):
        route = route_data[route_id]

        distance_cost = route["distance_km"] * weight_distance
        time_cost = route["estimated_time_minutes"] * weight_time
        fuel_cost = route["estimated_fuel_liters"] * weight_fuel
        traffic_cost = route["traffic_factor"] * weight_traffic
        load_cost = patrol_load[patrol] * penalty_load

        return distance_cost + time_cost + fuel_cost + traffic_cost + load_cost

    def objective_rule(model):
        return sum(
            cost(r, p) * model.x[r, p]
            for r in model.R
            for p in model.P
        )

    model.objective = pyo.Objective(
        rule=objective_rule,
        sense=pyo.minimize
    )

    def only_one_route_patrol_rule(model):
        return sum(
            model.x[r, p]
            for r in model.R
            for p in model.P
        ) == 1

    model.only_one_assignment = pyo.Constraint(
        rule=only_one_route_patrol_rule
    )

    solver = pyo.SolverFactory("glpk")
    result = solver.solve(model)

    selected_route_id = None
    selected_patrol = None

    for r in model.R:
        for p in model.P:
            value = pyo.value(model.x[r, p])
            if value is not None and round(value) == 1:
                selected_route_id = r
                selected_patrol = p
                break

        if selected_route_id is not None:
            break

    total_cost = pyo.value(model.objective)

    selected_route = route_data[selected_route_id]

    return {
        "selected_route_id": selected_route_id,
        "selected_route_name": selected_route["route_name"],
        "assigned_patrol": selected_patrol,
        "total_cost": round(total_cost, 2),
        "selected_route": selected_route
    }


def assign_patrol(distance_km, traffic_factor):
    """
    Función antigua mantenida por compatibilidad.
    """
    patrols, patrol_load = read_patrols()

    penalty = 10

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=patrols)
    model.x = pyo.Var(model.P, domain=pyo.Binary)

    def objective_rule(model):
        return sum(
            (
                distance_km * traffic_factor
                + patrol_load[p] * penalty
            ) * model.x[p]
            for p in model.P
        )

    model.objective = pyo.Objective(
        rule=objective_rule,
        sense=pyo.minimize
    )

    def one_patrol_rule(model):
        return sum(model.x[p] for p in model.P) == 1

    model.one_patrol_constraint = pyo.Constraint(rule=one_patrol_rule)

    solver = pyo.SolverFactory("glpk")
    solver.solve(model)

    assigned_patrol = None

    for p in model.P:
        if round(pyo.value(model.x[p])) == 1:
            assigned_patrol = p
            break

    total_cost = pyo.value(model.objective)

    return assigned_patrol, total_cost