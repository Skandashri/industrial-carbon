import pandas as pd
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor

# ==========================================
# Load Dataset
# ==========================================
df = pd.read_csv("dataset/hybrid_dataset.csv")

# ==========================================
# Input Features (X)
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
# Target (y)
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
# Feature Scaling
# ==========================================
scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ==========================================
# Train Random Forest Model
# ==========================================
model = RandomForestRegressor(
    n_estimators=100,
    random_state=42,
    max_depth=10,
)

model.fit(X_train_scaled, y_train)

print("✅ Model Training Completed")

# ==========================================
# Create model folder
# ==========================================
os.makedirs("model", exist_ok=True)

# ==========================================
# Save Model
# ==========================================
joblib.dump(model, "model/random_forest.pkl")

# Save Scaler
joblib.dump(scaler, "model/scaler.pkl")

print("✅ Model saved: model/random_forest.pkl")
print("✅ Scaler saved: model/scaler.pkl")

print("\nTraining Completed Successfully!")