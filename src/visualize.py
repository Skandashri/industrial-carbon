import os
import joblib
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split

# ==========================================
# Load Dataset
# ==========================================
df = pd.read_csv("dataset/hybrid_dataset.csv")

# ==========================================
# Features and Target
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
# Load Scaler & Model
# ==========================================
scaler = joblib.load("model/scaler.pkl")
model = joblib.load("model/random_forest.pkl")

X_test_scaled = scaler.transform(X_test)

# ==========================================
# Predictions
# ==========================================
y_pred = model.predict(X_test_scaled)

# ==========================================
# Create Graph Folder
# ==========================================
os.makedirs("reports/graphs", exist_ok=True)

# =========================================================
# 1. Prediction vs Actual
# =========================================================
plt.figure(figsize=(8,6))
plt.scatter(y_test, y_pred)
plt.plot(
    [y_test.min(), y_test.max()],
    [y_test.min(), y_test.max()],
    linestyle="--"
)
plt.xlabel("Actual CO₂ Emission")
plt.ylabel("Predicted CO₂ Emission")
plt.title("Actual vs Predicted CO₂ Emission")
plt.tight_layout()
plt.savefig("reports/graphs/prediction_vs_actual.png")
plt.close()

# =========================================================
# 2. Residual Plot
# =========================================================
residuals = y_test - y_pred

plt.figure(figsize=(8,6))
plt.scatter(y_pred, residuals)
plt.axhline(y=0, linestyle="--")
plt.xlabel("Predicted CO₂")
plt.ylabel("Residual")
plt.title("Residual Plot")
plt.tight_layout()
plt.savefig("reports/graphs/residual_plot.png")
plt.close()

# =========================================================
# 3. Feature Importance
# =========================================================
importance = model.feature_importances_

plt.figure(figsize=(8,6))
plt.bar(X.columns, importance)
plt.xticks(rotation=30)
plt.xlabel("Features")
plt.ylabel("Importance")
plt.title("Feature Importance")
plt.tight_layout()
plt.savefig("reports/graphs/feature_importance.png")
plt.close()

# =========================================================
# 4. Correlation Heatmap
# =========================================================
corr = df[
    [
        "Energy_Consumption",
        "Temperature",
        "Humidity",
        "Production_Output",
        "Working_Hour",
        "Weekend",
        "CO2_Emission",
    ]
].corr()

plt.figure(figsize=(8,6))
plt.imshow(corr, interpolation="nearest")
plt.colorbar()

plt.xticks(range(len(corr.columns)), corr.columns, rotation=90)
plt.yticks(range(len(corr.columns)), corr.columns)

# Display correlation values
for i in range(len(corr.columns)):
    for j in range(len(corr.columns)):
        plt.text(
            j,
            i,
            f"{corr.iloc[i, j]:.2f}",
            ha="center",
            va="center",
            fontsize=8,
        )

plt.title("Correlation Heatmap")
plt.tight_layout()
plt.savefig("reports/graphs/correlation_heatmap.png")
plt.close()

print("===================================")
print("✅ All Graphs Generated Successfully")
print("===================================")
print("1. prediction_vs_actual.png")
print("2. residual_plot.png")
print("3. feature_importance.png")
print("4. correlation_heatmap.png")
print("\nSaved inside reports/graphs/")