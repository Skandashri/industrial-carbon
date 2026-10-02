import os
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

# ==============================================================================
# EVALUATION CONFIGURATION & DIRECTORIES
# ==============================================================================
os.makedirs("static/graphs", exist_ok=True)
os.makedirs("reports/graphs", exist_ok=True)
os.makedirs("reports", exist_ok=True)

# ==============================================================================
# LOAD DATASET & ARTIFACTS
# ==============================================================================
dataset_path = "dataset/hybrid_dataset.csv"
print(f"Loading evaluation dataset from {dataset_path}...")
df = pd.read_csv(dataset_path)

FEATURES = [
    "Energy_Consumption",
    "Production_Output",
    "Working_Hour",
    "Weekend"
]
TARGET = "CO2_Emission"

# Verify schema
for col in FEATURES + [TARGET]:
    if col not in df.columns:
        raise ValueError(f"Required column '{col}' is missing from hybrid_dataset.csv!")

X = df[FEATURES]
y = df[TARGET]

# ==============================================================================
# WEEKEND DISTRIBUTION VALIDATION CHECK (Requirement 9)
# ==============================================================================
print("\n========== WEEKEND DISTRIBUTION VALIDATION ==========")
weekend_counts = df["Weekend"].value_counts().to_dict()
print("Weekend distribution:")
for val in [0, 1]:
    count = weekend_counts.get(val, 0)
    pct = (count / len(df)) * 100
    label = "Weekday" if val == 0 else "Weekend"
    print(f"  {val} ({label:7s}) = {count:5d} records ({pct:.2f}%)")

if df["Weekend"].nunique() < 2:
    print("\n[WARNING] Dataset contains only ONE Weekend value! Variance cannot be evaluated.")
else:
    print("\n[OK] Validation Passed: Both Weekend=0 (Weekdays) and Weekend=1 (Weekends) are present.")
print("====================================================\n")

# ==============================================================================
# INDEPENDENT TRAIN / TEST SPLIT (Zero Contamination)
# ==============================================================================
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

# Load trained pipeline artifacts
scaler = joblib.load("model/scaler.pkl")
model = joblib.load("model/random_forest.pkl")

# Scale test features using the training scaler
X_test_scaled = scaler.transform(X_test)

# Predict strictly on the holdout test set
y_pred = model.predict(X_test_scaled)

# ==============================================================================
# RIGOROUS SCIENTIFIC METRIC COMPUTATION
# ==============================================================================
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)

# Safe MAPE calculation (handling zero or near-zero values gracefully)
valid_mask = y_test > 0.1
if valid_mask.sum() > 0:
    mape = np.mean(np.abs((y_test[valid_mask] - y_pred[valid_mask]) / y_test[valid_mask])) * 100.0
else:
    mape = 0.0

# 5-Fold Cross-Validation on Training Data with zero fold-leakage
cv_pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("rf", RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42))
])
kfold = KFold(n_splits=5, shuffle=True, random_state=42)
cv_r2_scores = cross_val_score(cv_pipeline, X_train, y_train, cv=kfold, scoring="r2")
cv_r2_mean = cv_r2_scores.mean()
cv_r2_std = cv_r2_scores.std()

# ==============================================================================
# PRINT REPORT
# ==============================================================================
print("==================================================")
print("     SCIENTIFIC MODEL EVALUATION REPORT")
print("==================================================")
print(f"Total Dataset Records       : {len(df):d}")
print(f"Holdout Test Samples        : {len(y_test):d} (20% split)")
print(f"Input Features Evaluated    : {FEATURES}")
print(f"Target Variable             : {TARGET}")
print("--------------------------------------------------")
print(f"Mean Absolute Error (MAE)   : {mae:.4f} kg CO2")
print(f"Mean Squared Error (MSE)    : {mse:.4f}")
print(f"Root Mean Squared Error(RMSE: {rmse:.4f} kg CO2")
print(f"Coefficient of Determ. (R²) : {r2:.4f}")
print(f"Mean Abs. Pct. Error (MAPE) : {mape:.2f}%")
print(f"5-Fold CV Mean R² Score     : {cv_r2_mean:.4f} (+/- {cv_r2_std:.4f})")
print("--------------------------------------------------")
print("NOTE: R² is the coefficient of determination (goodness-of-fit),")
print("not a simplistic percentage accuracy metric.")
print("==================================================\n")

# ==============================================================================
# SAVE RESULTS TO REPORT FILE
# ==============================================================================
with open("reports/results.txt", "w", encoding="utf-8") as file:
    file.write("==================================================\n")
    file.write("INDUSTRIAL CARBON FORECASTING - MODEL EVALUATION\n")
    file.write("==================================================\n\n")
    file.write(f"Total Records       : {len(df)}\n")
    file.write(f"Holdout Test Set    : {len(y_test)} samples (20%)\n")
    file.write(f"Features Used       : {', '.join(FEATURES)}\n")
    file.write(f"Target Feature      : {TARGET}\n\n")
    file.write("PERFORMANCE METRICS (INDEPENDENT TEST SET):\n")
    file.write(f"  MAE               : {mae:.4f} kg CO2\n")
    file.write(f"  MSE               : {mse:.4f}\n")
    file.write(f"  RMSE              : {rmse:.4f} kg CO2\n")
    file.write(f"  R^2 Score          : {r2:.4f}\n")
    file.write(f"  MAPE              : {mape:.2f}%\n")
    file.write(f"  5-Fold CV Mean R^2 : {cv_r2_mean:.4f} (+/- {cv_r2_std:.4f})\n\n")
    file.write("WEEKEND DISTRIBUTION:\n")
    for val in [0, 1]:
        file.write(f"  Weekend={val} : {weekend_counts.get(val, 0)} records ({weekend_counts.get(val, 0)/len(df)*100:.1f}%)\n")
    file.write("\nFEATURE IMPORTANCES (RANDOM FOREST):\n")
    for feat_name, imp in zip(FEATURES, model.feature_importances_):
        file.write(f"  {feat_name:22s}: {imp:.6f} ({imp*100:.2f}%)\n")

# ==============================================================================
# GRAPH 1: ACTUAL VS PREDICTED (Test Set)
# ==============================================================================
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
    label=f"Ideal Parity ($R^2 = {r2:.4f}$)"
)
plt.xlabel("Actual Industrial CO₂ Emission (kg CO₂)", fontsize=11, fontweight="bold")
plt.ylabel("Predicted CO₂ Emission (kg CO₂)", fontsize=11, fontweight="bold")
plt.title("Actual vs Predicted Industrial CO₂ Emission (Holdout Test Set)", fontsize=12, fontweight="bold", pad=12)
plt.legend(frameon=True, facecolor="white", framealpha=0.9)
plt.grid(True, alpha=0.25, linestyle=":")
plt.tight_layout()
plt.savefig("static/graphs/actual_vs_predicted_fixed.png", dpi=300, bbox_inches="tight")
plt.savefig("reports/graphs/prediction_vs_actual.png", dpi=300, bbox_inches="tight")
plt.close()

# ==============================================================================
# GRAPH 2: RESIDUAL ANALYSIS (Test Set Residuals)
# ==============================================================================
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
plt.axhline(0, linestyle="--", color="#dc2626", linewidth=2, label=f"Zero Error Baseline (MAE = {mae:.3f} kg)")
plt.xlabel("Predicted CO₂ Emission (kg CO₂)", fontsize=11, fontweight="bold")
plt.ylabel("Residual Error (Actual − Predicted, kg CO₂)", fontsize=11, fontweight="bold")
plt.title("Residual Distribution Analysis (Homoscedasticity Verification)", fontsize=12, fontweight="bold", pad=12)
plt.legend(frameon=True, facecolor="white", framealpha=0.9)
plt.grid(True, alpha=0.25, linestyle=":")
plt.tight_layout()
plt.savefig("static/graphs/residual_analysis_fixed.png", dpi=300, bbox_inches="tight")
plt.savefig("reports/graphs/residual_plot.png", dpi=300, bbox_inches="tight")
plt.close()

# ==============================================================================
# GRAPH 3: RANDOM FOREST FEATURE IMPORTANCE
# ==============================================================================
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
plt.ylabel("Industrial Telemetry Features", fontsize=11, fontweight="bold")
plt.title("Random Forest Gini Feature Importance", fontsize=12, fontweight="bold", pad=12)
plt.grid(axis="x", alpha=0.25, linestyle=":")

# Annotate exact values & percentages on bars
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
plt.savefig("static/graphs/feature_importance_fixed.png", dpi=300, bbox_inches="tight")
plt.savefig("reports/graphs/feature_importance.png", dpi=300, bbox_inches="tight")
plt.close()

# ==============================================================================
# GRAPH 4: CORRELATION HEATMAP (Clean & Non-NaN)
# ==============================================================================
HEATMAP_COLUMNS = [
    "Energy_Consumption",
    "Production_Output",
    "Working_Hour",
    "Weekend",
    "CO2_Emission"
]
correlation = df[HEATMAP_COLUMNS].corr()

plt.figure(figsize=(10, 8))
heatmap = plt.imshow(correlation, cmap="coolwarm", vmin=-1.0, vmax=1.0)
cbar = plt.colorbar(heatmap)
cbar.set_label("Pearson Correlation Coefficient", fontsize=10, fontweight="bold")

plt.xticks(range(len(HEATMAP_COLUMNS)), HEATMAP_COLUMNS, rotation=35, ha="right", fontsize=9, fontweight="bold")
plt.yticks(range(len(HEATMAP_COLUMNS)), HEATMAP_COLUMNS, fontsize=9, fontweight="bold")

# Annotate values
for i in range(len(HEATMAP_COLUMNS)):
    for j in range(len(HEATMAP_COLUMNS)):
        val = correlation.iloc[i, j]
        text_color = "white" if abs(val) > 0.55 else "black"
        plt.text(j, i, f"{val:.2f}", ha="center", va="center", color=text_color, fontsize=10, fontweight="bold")

plt.title("Multivariate Correlation Heatmap (All Industrial Features & Target)", fontsize=12, fontweight="bold", pad=14)
plt.tight_layout()
plt.savefig("static/graphs/correlation_heatmap_fixed.png", dpi=300, bbox_inches="tight")
plt.savefig("reports/graphs/correlation_heatmap.png", dpi=300, bbox_inches="tight")
plt.close()

print("[OK] All 4 evaluation graphs successfully created and updated in:")
print("  - static/graphs/ (Web UI Dashboard)")
print("  - reports/graphs/ (Project Reports)")
print("[OK] reports/results.txt successfully updated.")