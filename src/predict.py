"""
Industrial Carbon Forecasting - Inference Module
Accepts core parameters:
- energy_kwh: float
- production_output: float
- working_hour: int (0-23)
- weekend: int (0 or 1)

Outputs forecasted CO2 emissions (kg) using Random Forest model / emission factor.
"""

import joblib
import numpy as np
import pandas as pd
import os

MODEL_PATH = "model/random_forest.pkl"
SCALER_PATH = "model/scaler.pkl"
EMISSION_FACTOR = 0.82  # CEA Scope 2 standard (kg CO2/kWh)

MODEL_ENERGY_MIN = 6.48
MODEL_ENERGY_MAX = 19.79

FEATURE_NAMES = ["Energy_Consumption", "Production_Output", "Working_Hour", "Weekend"]

_model = None
_scaler = None

def load_inference_pipeline():
    global _model, _scaler
    if _model is None or _scaler is None:
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            _model = joblib.load(MODEL_PATH)
            _scaler = joblib.load(SCALER_PATH)
        else:
            raise FileNotFoundError("Trained model or scaler not found in model/ directory.")
    return _model, _scaler

def predict_carbon_emission(energy_kwh, production_output, working_hour=12, weekend=0):
    """
    Computes forecasted CO2 emissions in kg.
    Uses Random Forest when energy is within training domain [6.48, 19.79],
    falls back to standard CEA Scope 2 grid emission factor (0.82 kg/kWh) otherwise.
    """
    energy = float(energy_kwh)
    production = float(production_output)
    hour = int(working_hour)
    wknd = int(weekend)

    model, scaler = load_inference_pipeline()

    if MODEL_ENERGY_MIN <= energy <= MODEL_ENERGY_MAX:
        df_feat = pd.DataFrame([[energy, production, hour, wknd]], columns=FEATURE_NAMES)
        scaled_feat = scaler.transform(df_feat)
        predicted_co2 = float(model.predict(scaled_feat)[0])
        method = "Random Forest Regressor (AI Model)"
        is_ai = True
    else:
        predicted_co2 = float(energy * EMISSION_FACTOR)
        method = f"Scope 2 Grid Emission Factor ({EMISSION_FACTOR} kg CO2/kWh)"
        is_ai = False

    predicted_co2 = max(0.0, round(predicted_co2, 2))
    return {
        "energy_kwh": energy,
        "production_output": production,
        "working_hour": hour,
        "weekend": wknd,
        "predicted_co2": predicted_co2,
        "method": method,
        "is_ai": is_ai
    }

if __name__ == "__main__":
    result = predict_carbon_emission(12.5, 100, 14, 0)
    print("Inference Result:", result)
