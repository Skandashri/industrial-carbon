import pandas as pd
import numpy as np

# -------------------------------------------------------------
# Feature Engineering Pipeline (Industrial Carbon Forecasting)
# Derives:
# 1. Energy_per_Product: specific energy consumption (kWh / unit)
# 2. Working_Hour: 24-hr industrial operating shift hour (0-23)
# 3. Day_of_Week: 0 (Monday) to 6 (Sunday)
# 4. Weekend: Binary flag (1 if Saturday/Sunday, else 0)
# Includes validation for natural weekend & temporal distribution.
# NOTE: Temperature and Humidity are completely eliminated.
# -------------------------------------------------------------

input_file = "dataset/industrial_energy_cleaned.csv"
output_file = "dataset/industrial_energy_features.csv"

print(f"Loading cleaned dataset from {input_file}...")
df = pd.read_csv(input_file)

# Ensure obsolete columns are removed
for obsolete_col in ["Temperature", "Humidity", "ambient_temp_C", "humidity_%"]:
    if obsolete_col in df.columns:
        df.drop(columns=[obsolete_col], inplace=True)

df["Timestamp"] = pd.to_datetime(df["Timestamp"])

# Specific energy consumption (kWh per unit produced)
# Safe division handling for Idle or Maintenance when Production_Output is 0
df["Energy_per_Product"] = (
    df["Energy_Consumption"] / df["Production_Output"].replace(0, np.nan)
).fillna(0.0).round(4)

# Temporal shift features derived directly from real timestamps
df["Working_Hour"] = df["Timestamp"].dt.hour
df["Day_of_Week"] = df["Timestamp"].dt.dayofweek
df["Weekend"] = df["Day_of_Week"].apply(lambda x: 1 if x >= 5 else 0)

# =============================================================
# VALIDATION CHECKS (Temporal & Weekend Distribution)
# =============================================================
print("\n========== TEMPORAL & WEEKEND VALIDATION ==========")
print(f"Working_Hour range : min={df['Working_Hour'].min()}, max={df['Working_Hour'].max()} (Covering {df['Working_Hour'].nunique()} unique hours)")
print(f"Day_of_Week range  : min={df['Day_of_Week'].min()} (Mon), max={df['Day_of_Week'].max()} (Sun) (Covering {df['Day_of_Week'].nunique()} days)")

weekend_counts = df["Weekend"].value_counts().to_dict()
print("\nWeekend distribution:")
for val in [0, 1]:
    count = weekend_counts.get(val, 0)
    pct = (count / len(df)) * 100
    label = "Weekday" if val == 0 else "Weekend"
    print(f"  {val} ({label:7s}) = {count:5d} records ({pct:.2f}%)")

if df["Weekend"].nunique() < 2:
    print("\n[WARNING] Dataset contains only ONE Weekend value! Model cannot learn weekend variance.")
else:
    print("\n[OK] Dataset successfully contains BOTH Weekend=0 (Weekdays) and Weekend=1 (Weekends).")
print("===================================================\n")

# Save features dataset
df.to_csv(output_file, index=False)

print("[OK] Feature Engineering Completed Successfully!")
print(f"Saved to: {output_file}")
print("Dataset Shape:", df.shape)
print("Columns:", df.columns.tolist())
print("\nFirst 5 Rows:")
print(df.head())
