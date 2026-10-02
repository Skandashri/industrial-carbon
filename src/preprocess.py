import pandas as pd
import os

# -------------------------------------------------------------
# Preprocessing Pipeline (Industrial Carbon Forecasting)
# Reads raw industrial dataset and extracts core parameters:
# 1. Timestamp (covering full weekly cycles including weekends)
# 2. Energy_Consumption (kWh)
# 3. Production_Output (Units)
# 4. Machine_Status (Normal, High, Idle, Maintenance)
# NOTE: Temperature and Humidity are completely eliminated.
# -------------------------------------------------------------

raw_file = "dataset/industrial_energy.csv"
output_file = "dataset/industrial_energy_cleaned.csv"

def derive_machine_status(row):
    """
    Derives realistic machine operating status from industrial telemetry:
    - Maintenance: Machine undergoing scheduled maintenance or repair.
    - Idle: Machine powered on standby with zero production output.
    - High: Machine operating under high electrical energy/load state.
    - Normal: Machine operating under standard balanced conditions.
    """
    prod_mode = str(row.get("production_mode", "")).strip()
    energy_state = str(row.get("energy_state", "")).strip()

    if prod_mode == "Maintenance":
        return "Maintenance"
    elif prod_mode == "Idle":
        return "Idle"
    elif energy_state == "High":
        return "High"
    else:
        return "Normal"

if os.path.exists(raw_file):
    print(f"Loading raw dataset from {raw_file}...")
    raw_df = pd.read_csv(raw_file)

    # Standardize column mapping
    df = pd.DataFrame()
    df["Timestamp"] = pd.to_datetime(raw_df["timestamp"])
    df["Energy_Consumption"] = pd.to_numeric(raw_df["energy_kWh"], errors="coerce")
    df["Production_Output"] = pd.to_numeric(raw_df["production_output_units"], errors="coerce")
    df["Machine_Status"] = raw_df.apply(derive_machine_status, axis=1)
else:
    print(f"Loading existing cleaned dataset from {output_file}...")
    df = pd.read_csv(output_file)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    # Ensure temperature and humidity are dropped if previously present
    for obsolete_col in ["Temperature", "Humidity", "ambient_temp_C", "humidity_%"]:
        if obsolete_col in df.columns:
            df.drop(columns=[obsolete_col], inplace=True)

print("Missing values before cleaning:")
print(df.isnull().sum())

# Clean missing values
df["Energy_Consumption"] = df["Energy_Consumption"].fillna(df["Energy_Consumption"].mean())
df["Production_Output"] = df["Production_Output"].fillna(0.0)
df["Machine_Status"] = df["Machine_Status"].fillna("Normal")
df.dropna(subset=["Energy_Consumption", "Production_Output", "Timestamp"], inplace=True)

# Save cleaned dataset without temperature or humidity
df.to_csv(output_file, index=False)

print("\n[OK] Core parameters cleaned successfully without Temperature/Humidity!")
print("Dataset Shape:", df.shape)
print("Columns:", df.columns.tolist())
print("Machine_Status distribution:\n", df["Machine_Status"].value_counts())
print(f"Timestamp range: {df['Timestamp'].min()} to {df['Timestamp'].max()}")
print("\nFirst 5 Rows:")
print(df.head())