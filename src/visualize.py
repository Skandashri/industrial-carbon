import os
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

# ==========================================
# Load Dataset & Artifacts
# ==========================================
df = pd.read_csv("dataset/hybrid_dataset.csv")

FEATURES = [
    "Energy_Consumption",
    "Production_Output",
    "Working_Hour",
    "Weekend",
]
TARGET = "CO2_Emission"

X = df[FEATURES]
y = df[TARGET]

# Train-Test Split (20% holdout test set)
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
)

scaler = joblib.load("model/scaler.pkl")
model = joblib.load("model/random_forest.pkl")

# Scale test set using training scaler
X_test_scaled = scaler.transform(X_test)
y_pred = model.predict(X_test_scaled)

os.makedirs("reports/graphs", exist_ok=True)

# =========================================================
# 1. Prediction vs Actual
# =========================================================
plt.figure(figsize=(9, 6))
plt.scatter(
    y_test,
    y_pred,
    alpha=0.65,
    edgecolors="#0f172a",
    linewidths=0.5,
    c="#2563eb",
    label="Test Observations (N=240)"
)
min_val = min(y_test.min(), y_pred.min())
max_val = max(y_test.max(), y_pred.max())
plt.plot(
    [min_val, max_val],
    [min_val, max_val],
    linestyle="--",
    color="#dc2626",
    linewidth=2,
    label="Ideal Parity Line (y = x)"
)
plt.xlabel("Actual CO₂ Emission (kg CO₂)", fontsize=11, fontweight="bold")
plt.ylabel("Predicted CO₂ Emission (kg CO₂)", fontsize=11, fontweight="bold")
plt.title("Actual vs Predicted CO₂ Emission (Holdout Test Set)", fontsize=12, fontweight="bold", pad=12)
plt.legend(frameon=True, facecolor="white", framealpha=0.9)
plt.grid(True, alpha=0.25, linestyle=":")
plt.tight_layout()
plt.savefig("reports/graphs/prediction_vs_actual.png", dpi=300, bbox_inches="tight")
plt.close()

# =========================================================
# 2. Residual Plot
# =========================================================
residuals = y_test - y_pred
plt.figure(figsize=(9, 6))
plt.scatter(
    y_pred,
    residuals,
    alpha=0.65,
    edgecolors="#0f172a",
    linewidths=0.5,
    c="#059669",
    label="Test Residuals"
)
plt.axhline(0, linestyle="--", color="#dc2626", linewidth=2, label="Zero Error Reference")
plt.xlabel("Predicted CO₂ Emission (kg CO₂)", fontsize=11, fontweight="bold")
plt.ylabel("Residual (Actual − Predicted, kg CO₂)", fontsize=11, fontweight="bold")
plt.title("Residual Distribution Analysis", fontsize=12, fontweight="bold", pad=12)
plt.legend(frameon=True, facecolor="white", framealpha=0.9)
plt.grid(True, alpha=0.25, linestyle=":")
plt.tight_layout()
plt.savefig("reports/graphs/residual_plot.png", dpi=300, bbox_inches="tight")
plt.close()

# =========================================================
# 3. Feature Importance
# =========================================================
importance_df = pd.DataFrame({
    "Feature": FEATURES,
    "Importance": model.feature_importances_
}).sort_values("Importance", ascending=True)

plt.figure(figsize=(10, 6))
bars = plt.barh(
    importance_df["Feature"],
    importance_df["Importance"],
    color="#0284c7",
    edgecolor="#0f172a",
    linewidth=0.6
)
plt.xlabel("Feature Importance Score", fontsize=11, fontweight="bold")
plt.ylabel("Features", fontsize=11, fontweight="bold")
plt.title("Random Forest Feature Importance", fontsize=12, fontweight="bold", pad=12)
plt.grid(axis="x", alpha=0.25, linestyle=":")

for bar, value in zip(bars, importance_df["Importance"]):
    pct = value * 100.0
    plt.text(
        value + 0.01,
        bar.get_y() + bar.get_height() / 2,
        f"{value:.4f} ({pct:.2f}%)",
        va="center",
        fontsize=9,
        fontweight="bold"
    )

plt.xlim(0, max(importance_df["Importance"]) * 1.18)
plt.tight_layout()
plt.savefig("reports/graphs/feature_importance.png", dpi=300, bbox_inches="tight")
plt.close()

# =========================================================
# 4. Correlation Heatmap
# =========================================================
corr_cols = [
    "Energy_Consumption",
    "Production_Output",
    "Working_Hour",
    "Weekend",
    "CO2_Emission"
]
corr = df[corr_cols].corr()

plt.figure(figsize=(10, 8))
heatmap = plt.imshow(corr, cmap="coolwarm", vmin=-1.0, vmax=1.0)
cbar = plt.colorbar(heatmap)
cbar.set_label("Pearson Correlation", fontsize=10, fontweight="bold")

plt.xticks(range(len(corr_cols)), corr_cols, rotation=35, ha="right", fontsize=9, fontweight="bold")
plt.yticks(range(len(corr_cols)), corr_cols, fontsize=9, fontweight="bold")

for i in range(len(corr_cols)):
    for j in range(len(corr_cols)):
        val = corr.iloc[i, j]
        text_color = "white" if abs(val) > 0.55 else "black"
        plt.text(j, i, f"{val:.2f}", ha="center", va="center", color=text_color, fontsize=10, fontweight="bold")

plt.title("Correlation Heatmap of Model Variables", fontsize=12, fontweight="bold", pad=14)
plt.tight_layout()
plt.savefig("reports/graphs/correlation_heatmap.png", dpi=300, bbox_inches="tight")
plt.close()

print("===================================")
print("[OK] All Graphs Generated Successfully")
print("===================================")
print("1. reports/graphs/prediction_vs_actual.png")
print("2. reports/graphs/residual_plot.png")
print("3. reports/graphs/feature_importance.png")
print("4. reports/graphs/correlation_heatmap.png")