import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# ==============================================================================
# MODEL TRAINING PIPELINE (Industrial Carbon Forecasting)
# Supervised Random Forest Regressor
# ==============================================================================

dataset_path = "dataset/hybrid_dataset.csv"
print(f"Loading hybrid dataset from {dataset_path}...")
df = pd.read_csv(dataset_path)

# ==============================================================================
# INPUT FEATURES (X) & TARGET (y)
# Strictly Leakage-Free: Only observable operating telemetry parameters
# ==============================================================================
FEATURES = [
    "Energy_Consumption",
    "Production_Output",
    "Working_Hour",
    "Weekend"
]
TARGET = "CO2_Emission"

# Rigorous Data Leakage Verification
assert TARGET not in FEATURES, "CRITICAL ERROR: Target CO2_Emission is present in input features!"
for feat in FEATURES:
    assert feat in df.columns, f"CRITICAL ERROR: Feature {feat} missing from dataset!"
    assert "co2" not in feat.lower(), f"CRITICAL ERROR: Target-derived feature {feat} in X!"

X = df[FEATURES]
y = df[TARGET]

print("\n========== MODEL FEATURE SPECIFICATION ==========")
print("Features used for training (X):", FEATURES)
print("Target variable (y)            :", TARGET)
print("Total dataset size             :", len(df))
print("Weekend distribution in X      :", df["Weekend"].value_counts().to_dict())
print("=================================================")

# ==============================================================================
# TRAIN / TEST SPLIT (Honest Independent Holdout)
# ==============================================================================
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)
print(f"\nTrain set size          : {len(X_train)} samples")
print(f"Test set size           : {len(X_test)} samples (Independent test set)")
print(f"Minimum training energy : {X_train['Energy_Consumption'].min():.2f} kWh")
print(f"Maximum training energy : {X_train['Energy_Consumption'].max():.2f} kWh")
print(f"Minimum testing energy  : {X_test['Energy_Consumption'].min():.2f} kWh")
print(f"Maximum testing energy  : {X_test['Energy_Consumption'].max():.2f} kWh")

# ==============================================================================
# FEATURE SCALING (Fitted strictly on Training set to eliminate data leakage)
# ==============================================================================
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)  # Transform test with training parameters only

print("[OK] StandardScaler fitted strictly on training data (Zero Test Leakage).")

# ==============================================================================
# TRAIN RANDOM FOREST REGRESSOR
# ==============================================================================
model = RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    random_state=42
)
model.fit(X_train_scaled, y_train)
print("[OK] Random Forest Regressor trained successfully.")

# ==============================================================================
# HONEST HOLDOUT EVALUATION
# ==============================================================================
train_preds = model.predict(X_train_scaled)
test_preds = model.predict(X_test_scaled)

train_r2 = r2_score(y_train, train_preds)
test_r2 = r2_score(y_test, test_preds)
test_mae = mean_absolute_error(y_test, test_preds)
test_rmse = np.sqrt(mean_squared_error(y_test, test_preds))

print("\n========== INITIAL EVALUATION METRICS ==========")
print(f"Training R² Score    : {train_r2:.4f}")
print(f"Independent Test R²  : {test_r2:.4f}")
print(f"Test MAE             : {test_mae:.4f} kg CO2")
print(f"Test RMSE            : {test_rmse:.4f} kg CO2")
print("================================================")

# ==============================================================================
# FEATURE IMPORTANCE
# ==============================================================================
print("\n========== FEATURE IMPORTANCES ==========")
for feat_name, importance in zip(FEATURES, model.feature_importances_):
    print(f"  {feat_name:22s} : {importance:.6f} ({importance * 100:.2f}%)")
print("=========================================\n")

# ==============================================================================
# SAVE MODEL & SCALER ARTIFACTS
# ==============================================================================
os.makedirs("model", exist_ok=True)
joblib.dump(model, "model/random_forest.pkl")
joblib.dump(scaler, "model/scaler.pkl")

print("[OK] Model saved  : model/random_forest.pkl")
print("[OK] Scaler saved : model/scaler.pkl")
print("[OK] Training pipeline finished successfully.")