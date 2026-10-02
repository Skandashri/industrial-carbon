import pandas as pd
import joblib
import numpy as np

# ==========================================================
# LOAD MODEL AND SCALER
# ==========================================================
model = joblib.load("model/random_forest.pkl")
scaler = joblib.load("model/scaler.pkl")

FEATURE_NAMES = ["Energy_Consumption", "Production_Output", "Working_Hour", "Weekend"]

# ==========================================================
# TEST INPUTS (Energy, Production, Working_Hour, Weekend)
# ==========================================================
test_data = pd.DataFrame([
    [10.0, 100.0, 10, 0],
    [12.5, 110.0, 14, 0],
    [15.0, 95.0, 8, 0],
    [18.0, 120.0, 16, 0],
    [19.5, 105.0, 20, 1]
], columns=FEATURE_NAMES)

# ==========================================================
# SCALE WITH FEATURE NAMES
# ==========================================================
test_scaled = scaler.transform(test_data)

# ==========================================================
# PREDICT
# ==========================================================
predictions = model.predict(test_scaled)

# ==========================================================
# DISPLAY
# ==========================================================
print("\n========== MODEL INFERENCE TEST ==========\n")

for (_, row), prediction in zip(test_data.iterrows(), predictions):
    print(
        f"Energy: {row['Energy_Consumption']:5.2f} kWh | "
        f"Prod: {row['Production_Output']:5.1f} units | "
        f"Hour: {int(row['Working_Hour']):02d}:00 | "
        f"Weekend: {int(row['Weekend'])} "
        f"-> CO2: {prediction:6.3f} kg"
    )

print("\n==========================================")