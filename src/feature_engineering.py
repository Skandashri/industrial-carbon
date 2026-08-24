import pandas as pd
import numpy as np

# ---------------------------------
# Load the cleaned dataset
# ---------------------------------
df = pd.read_csv("dataset/industrial_energy_cleaned.csv")

# ---------------------------------
# Convert Timestamp to datetime
# ---------------------------------
df["Timestamp"] = pd.to_datetime(df["Timestamp"])

# ---------------------------------
# Feature 1: Energy per Product
# ---------------------------------
df["Energy_per_Product"] = (
    df["Energy_Consumption"] /
    df["Production_Output"].replace(0, np.nan)
)

# Replace infinity or NaN values
df["Energy_per_Product"] = df["Energy_per_Product"].fillna(0)

# ---------------------------------
# Feature 2: Working Hour
# ---------------------------------
df["Working_Hour"] = df["Timestamp"].dt.hour

# ---------------------------------
# Feature 3: Day of Week
# Monday = 0, Sunday = 6
# ---------------------------------
df["Day_of_Week"] = df["Timestamp"].dt.dayofweek

# ---------------------------------
# Feature 4: Weekend
# Saturday & Sunday = 1
# ---------------------------------
df["Weekend"] = df["Day_of_Week"].apply(
    lambda x: 1 if x >= 5 else 0
)

# ---------------------------------
# Save the new dataset
# ---------------------------------
df.to_csv("dataset/industrial_energy_features.csv", index=False)

print("✅ Feature Engineering Completed Successfully!")

print("\nNew Features Added:")
print(df.columns.tolist())

print("\nFirst 5 Rows:")
print(df.head())
