import numpy as np
import pandas as pd
import os

def generate_dataset(n_samples=5000):
    np.random.seed(42)

    if not os.path.exists("data"):
        os.makedirs("data")

    data = []

    for _ in range(n_samples):
        cement_ratio = np.random.uniform(300, 500)
        water_cement_ratio = np.random.uniform(0.3, 0.6)
        temperature = np.random.uniform(10, 40)
        humidity = np.random.uniform(40, 90)
        automation_level = np.random.randint(1, 5)
        curing_type = np.random.choice(["normal", "steam"])

        base_strength = (cement_ratio * 0.1) / water_cement_ratio
        temp_factor = 1 + ((temperature - 20) * 0.04)
        humidity_factor = 1 - ((60 - humidity) * 0.01)

        if curing_type == "steam":
            curing_factor = 1.8
            curing_cost = 500
        else:
            curing_factor = 1.0
            curing_cost = 100

        strength_day1 = base_strength * temp_factor * humidity_factor * curing_factor * 0.4
        target_strength = 30

        cycle_time = max(1, target_strength / (strength_day1 + 1))
        cycle_time = cycle_time - (automation_level * 0.2)
        cycle_time += np.random.normal(0, 0.3)
        cycle_time = max(0.5, cycle_time)
        production_cost = (
            cement_ratio * 2
            + curing_cost
            + (automation_level * 300)
        )

        data.append([
            cement_ratio,
            water_cement_ratio,
            temperature,
            humidity,
            automation_level,
            curing_type,
            strength_day1,
            cycle_time,
            production_cost
        ])

    df = pd.DataFrame(data, columns=[
        "cement_ratio",
        "water_cement_ratio",
        "temperature",
        "humidity",
        "automation_level",
        "curing_type",
        "strength_day1",
        "cycle_time",
        "production_cost"
    ])

    df.to_csv("data/precast_data.csv", index=False)
    print("Dataset generated successfully.")

if __name__ == "__main__":
    generate_dataset()