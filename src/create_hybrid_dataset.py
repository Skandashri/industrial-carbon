import pandas as pd

# ---------------------------------
# Load Feature Engineered Dataset
# ---------------------------------
df = pd.read_csv("dataset/industrial_energy_features.csv")

# ---------------------------------
# Standard Emission Factor
# Electricity: 0.82 kg CO₂ per kWh
# ---------------------------------
EMISSION_FACTOR = 0.82

# ---------------------------------
# Create CO₂ Emission Column
# ---------------------------------
df["CO2_Emission"] = (
    df["Energy_Consumption"] * EMISSION_FACTOR
).round(2)

# ---------------------------------
# Save Hybrid Dataset
# ---------------------------------
output_file = "dataset/hybrid_dataset.csv"
df.to_csv(output_file, index=False)

print("✅ CO₂ Emission column created successfully!")
print(f"Saved as: {output_file}")

print("\nFirst 5 Rows:")
print(df[[
    "Energy_Consumption",
    "Temperature",
    "Humidity",
    "Production_Output",
    "CO2_Emission"
]].head())

print("\nDataset Shape:", df.shape)