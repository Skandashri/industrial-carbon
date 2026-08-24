import pandas as pd
import joblib
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

# ==========================================
# Load Dataset
# ==========================================
df = pd.read_csv("dataset/hybrid_dataset.csv")

# ==========================================
# Input Features
# ==========================================
X = df[
    [
        "Energy_Consumption",
        "Temperature",
        "Humidity",
        "Production_Output",
        "Working_Hour",
        "Weekend",
    ]
]

# ==========================================
# Target
# ==========================================
y = df["CO2_Emission"]

# ==========================================
# Train-Test Split
# ==========================================
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
)

# ==========================================
# Load Scaler
# ==========================================
scaler = joblib.load("model/scaler.pkl")

X_test_scaled = scaler.transform(X_test)

# ==========================================
# Load Trained Model
# ==========================================
model = joblib.load("model/random_forest.pkl")

# ==========================================
# Predict
# ==========================================
y_pred = model.predict(X_test_scaled)

# ==========================================
# Evaluation Metrics
# ==========================================
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)

# ==========================================
# Print Results
# ==========================================
print("\n========== Model Evaluation ==========\n")

print(f"Mean Absolute Error (MAE) : {mae:.4f}")
print(f"Mean Squared Error (MSE)  : {mse:.4f}")
print(f"Root Mean Squared Error (RMSE) : {rmse:.4f}")
print(f"R² Score : {r2:.4f}")

print("\n======================================")

# ==========================================
# Save Results
# ==========================================
with open("reports/results.txt", "w") as f:
    f.write("MODEL EVALUATION RESULTS\n")
    f.write("=========================\n\n")
    f.write(f"MAE  : {mae:.4f}\n")
    f.write(f"MSE  : {mse:.4f}\n")
    f.write(f"RMSE : {rmse:.4f}\n")
    f.write(f"R² Score : {r2:.4f}\n")

print("\n✅ Results saved to reports/results.txt")

