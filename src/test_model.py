import pandas as pd
import joblib
import numpy as np

# ==========================================================
# LOAD MODEL AND SCALER
# ==========================================================
model = joblib.load("model/random_forest.pkl")
scaler = joblib.load("model/scaler.pkl")

FEATURE_NAMES = ["Energy_Consumption", "Production_Output", "Working_Hour", "Weekend"]

import os

# Trained energy domain
TRAINED_MIN_ENERGY = 0.22
TRAINED_MAX_ENERGY = 19.79

# Previous model for comparison if available
prev_model = None
prev_scaler = None
if os.path.exists("model/random_forest_prev.pkl") and os.path.exists("model/scaler_prev.pkl"):
    prev_model = joblib.load("model/random_forest_prev.pkl")
    prev_scaler = joblib.load("model/scaler_prev.pkl")

# ==========================================================
# TEST INPUTS (Energy, Production, Working_Hour, Weekend)
# Testing full required spectrum from 0.5 to 19.0 kWh
# ==========================================================
test_data = pd.DataFrame([
    [0.5,   5.0, 10, 0],
    [1.0,  15.0, 11, 0],
    [2.0,  25.0, 12, 0],
    [3.0,  35.0, 13, 0],
    [5.0,  55.0, 14, 0],
    [6.0,  65.0, 15, 0],
    [8.0,  80.0, 10, 0],
    [10.0, 95.0, 14, 0],
    [15.0, 110.0, 16, 0],
    [19.0, 125.0, 20, 1]
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
print("\n========== MODEL INFERENCE TEST (LOW & HIGH ENERGY SPECTRUM) ==========\n")
print(f"Validated ML Training Range: {TRAINED_MIN_ENERGY:.2f} kWh to {TRAINED_MAX_ENERGY:.2f} kWh\n")

for (_, row), prediction in zip(test_data.iterrows(), predictions):
    energy = row['Energy_Consumption']
    prod = row['Production_Output']
    hour = int(row['Working_Hour'])
    wknd = int(row['Weekend'])

    in_range = TRAINED_MIN_ENERGY <= energy <= TRAINED_MAX_ENERGY
    status = "Within trained range" if in_range else "Outside trained range"

    prev_info = ""
    if prev_model is not None and prev_scaler is not None:
        prev_scaled = prev_scaler.transform(pd.DataFrame([[energy, prod, hour, wknd]], columns=FEATURE_NAMES))
        prev_pred = prev_model.predict(prev_scaled)[0]
        prev_info = f" | Prev Model: {prev_pred:6.2f} kg"

    print(
        f"Energy: {energy:5.2f} kWh | "
        f"Prod: {prod:5.1f} units | "
        f"Hour: {hour:02d}:00 | "
        f"Weekend: {wknd} -> "
        f"Predicted CO2: {prediction:6.3f} kg{prev_info} | "
        f"Status: {status}"
    )

print("\n==========================================================================")