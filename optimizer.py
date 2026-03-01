import pandas as pd
import numpy as np
import joblib

# Load trained model
model = joblib.load("models/cycle_time_model.pkl")
def evaluate_single_config(
    cement, water, auto, curing,
    temperature, humidity
):
    curing_num = 1 if curing == "steam" else 0

    base_strength = (cement * 0.1) / water
    temp_factor = 1 + ((temperature - 20) * 0.02)
    humidity_factor = 1 - ((60 - humidity) * 0.005)
    curing_factor = 1.8 if curing == "steam" else 1.0

    strength_day1 = base_strength * temp_factor * humidity_factor * curing_factor * 0.4

    curing_cost = 500 if curing == "steam" else 100
    cost = cement * 2 + curing_cost + auto * 300

    features = pd.DataFrame([[
        cement,
        water,
        temperature,
        humidity,
        auto,
        curing_num,
        strength_day1,
        cost
    ]], columns=[
        "cement_ratio",
        "water_cement_ratio",
        "temperature",
        "humidity",
        "automation_level",
        "curing_type",
        "strength_day1",
        "production_cost"
    ])

    cycle_time = model.predict(features)[0]

    return cycle_time, cost
def recommend_strategy(
    temperature,
    humidity,
    min_strength=25,
    max_budget=5000
):
    cement_range = np.linspace(320, 480, 8)
    water_ratio_range = np.linspace(0.35, 0.55, 5)
    automation_levels = [1, 2, 3, 4]
    curing_types = ["normal", "steam"]

    results = []

    for cement in cement_range:
        for water in water_ratio_range:
            for auto in automation_levels:
                for curing in curing_types:

                    curing_num = 1 if curing == "steam" else 0

                    base_strength = (cement * 0.1) / water
                    temp_factor = 1 + ((temperature - 20) * 0.02)
                    humidity_factor = 1 - ((60 - humidity) * 0.005)
                    curing_factor = 1.8 if curing == "steam" else 1.0

                    strength_day1 = base_strength * temp_factor * humidity_factor * curing_factor * 0.4

                    if strength_day1 < min_strength:
                        continue

                    curing_cost = 500 if curing == "steam" else 100
                    cost = cement * 2 + curing_cost + auto * 300

                    if cost > max_budget:
                        continue

                    features = pd.DataFrame([[
                        cement,
                        water,
                        temperature,
                        humidity,
                        auto,
                        curing_num,
                        strength_day1,
                        cost
                    ]], columns=[
                        "cement_ratio",
                        "water_cement_ratio",
                        "temperature",
                        "humidity",
                        "automation_level",
                        "curing_type",
                        "strength_day1",
                        "production_cost"
                    ])

                    cycle_time = model.predict(features)[0]

                    score = (0.7 * cycle_time) + (0.3 * (cost / 1000))

                    results.append({
                        "cement_ratio": cement,
                        "water_ratio": water,
                        "automation": auto,
                        "curing": curing,
                        "cycle_time": round(cycle_time, 2),
                        "cost": round(cost, 2),
                        "score": score
                    })

    results = sorted(results, key=lambda x: x["score"])

    return results


def recommend_for_project(
    temperature,
    humidity,
    project_type,
    target_strength,
    max_budget,
    automation_level,
):
    """Recommend strategy for a project with fixed automation level."""
    # Infra projects typically need higher strength
    min_strength = target_strength if project_type == "Building" else max(target_strength, 28)

    cement_range = np.linspace(320, 480, 10)
    water_ratio_range = np.linspace(0.35, 0.55, 6)
    curing_types = ["normal", "steam"]

    results = []

    for cement in cement_range:
        for water in water_ratio_range:
            for curing in curing_types:
                curing_num = 1 if curing == "steam" else 0
                base_strength = (cement * 0.1) / water
                temp_factor = 1 + ((temperature - 20) * 0.02)
                humidity_factor = 1 - ((60 - humidity) * 0.005)
                curing_factor = 1.8 if curing == "steam" else 1.0
                strength_day1 = base_strength * temp_factor * humidity_factor * curing_factor * 0.4

                if strength_day1 < min_strength:
                    continue

                curing_cost = 500 if curing == "steam" else 100
                cost = cement * 2 + curing_cost + automation_level * 300

                if cost > max_budget:
                    continue

                features = pd.DataFrame([[
                    cement, water, temperature, humidity, automation_level,
                    curing_num, strength_day1, cost
                ]], columns=[
                    "cement_ratio", "water_cement_ratio", "temperature", "humidity",
                    "automation_level", "curing_type", "strength_day1", "production_cost"
                ])
                cycle_time = model.predict(features)[0]
                score = (0.7 * cycle_time) + (0.3 * (cost / 1000))

                results.append({
                    "cement_ratio": cement,
                    "water_ratio": water,
                    "automation": automation_level,
                    "curing": curing,
                    "cycle_time": round(cycle_time, 2),
                    "cost": round(cost, 2),
                    "strength_day1": round(strength_day1, 1),
                    "score": score,
                })

    results = sorted(results, key=lambda x: x["score"])
    return results


def simulate_scenario(baseline, scenario_type, scenario_value_pct, temperature, humidity):
    """
    Simulate a what-if scenario. Returns new cycle_time, new cost, deltas, and ROI.
    baseline: dict with cement_ratio, water_ratio, automation, curing, cycle_time, cost
    scenario_type: "steam_temp" | "ambient_temp" | "cement" | "humidity"
    scenario_value_pct: e.g. 10 for +10%
    """
    cement = baseline["cement_ratio"]
    water = baseline["water_ratio"]
    auto = baseline["automation"]
    curing = baseline["curing"]

    temp = temperature
    hum = humidity
    curing_num = 1 if curing == "steam" else 0
    curing_cost = 500 if curing == "steam" else 100

    if scenario_type == "steam_temp":
        # Steam temp +X% → apply to temp when steam curing (effective curing environment warmer)
        if curing == "steam":
            temp = temperature * (1 + scenario_value_pct / 100)
            curing_cost = 500 * (1 + scenario_value_pct / 100)  # More energy for hotter steam
        else:
            temp = temperature  # No effect for normal curing
    elif scenario_type == "ambient_temp":
        temp = temperature * (1 + scenario_value_pct / 100)
    elif scenario_type == "cement":
        cement = cement * (1 + scenario_value_pct / 100)
    elif scenario_type == "humidity":
        hum = humidity * (1 + scenario_value_pct / 100)

    base_strength = (cement * 0.1) / water
    temp_factor = 1 + ((temp - 20) * 0.02)
    humidity_factor = 1 - ((60 - hum) * 0.005)
    curing_factor = 1.8 if curing == "steam" else 1.0
    strength_day1 = base_strength * temp_factor * humidity_factor * curing_factor * 0.4

    cost = cement * 2 + curing_cost + auto * 300
    features = pd.DataFrame([[
        cement, water, temp, hum, auto, curing_num, strength_day1, cost
    ]], columns=[
        "cement_ratio", "water_cement_ratio", "temperature", "humidity",
        "automation_level", "curing_type", "strength_day1", "production_cost"
    ])
    cycle_time = model.predict(features)[0]

    ct_baseline = baseline["cycle_time"]
    cost_baseline = baseline["cost"]

    cycle_delta = round(cycle_time - ct_baseline, 2)
    cost_delta = round(cost - cost_baseline, 2)

    return {
        "cycle_time": round(cycle_time, 2),
        "cost": round(cost, 2),
        "cycle_delta": cycle_delta,
        "cost_delta": cost_delta,
    }