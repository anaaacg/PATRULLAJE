
from pathlib import Path

import pyomo.environ as pyo
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "patrols.csv"


def assign_patrol(distance_km, traffic_factor):
    """
    Asigna una ruta a una patrulla usando Pyomo + GLPK.
    Los datos de patrullas se leen desde un archivo CSV.
    """

    
    # Leer datos desde CSV

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

    penalty = 10


    # Crear modelo

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=patrols)

    model.x = pyo.Var(model.P, domain=pyo.Binary)

  
    # Función objetivo

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

   
    # Restricción

    def one_patrol_rule(model):
        return sum(model.x[p] for p in model.P) == 1

    model.one_patrol_constraint = pyo.Constraint(rule=one_patrol_rule)

   

    # Resolver con GLPK

    solver = pyo.SolverFactory("glpk")
    result = solver.solve(model)

    
    # Obtener resultado

    assigned_patrol = None

    for p in model.P:
        if pyo.value(model.x[p]) == 1:
            assigned_patrol = p
            break

    total_cost = pyo.value(model.objective)

    return assigned_patrol, total_cost


if __name__ == "__main__":
    patrol, cost = assign_patrol(distance_km=8.5, traffic_factor=1.2)

    print("Patrulla asignada:", patrol)
    print("Costo calculado:", cost)