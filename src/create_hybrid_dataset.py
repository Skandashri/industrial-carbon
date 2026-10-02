import pandas as pd
import numpy as np

# ==============================================================================
# INDUSTRIAL HYBRID DATASET GENERATION PIPELINE
# Scope 2 & Process Carbon Emission Synthesis
# ==============================================================================
#
# VIVA & DEFENSE RATIONALE (Academic Explanation):
# In actual manufacturing operations, total greenhouse gas (GHG) emissions do NOT
# scale as an identical single-variable linear function of motor electricity.
# Under the GHG Protocol Corporate Standard, industrial carbon footprint comprises:
#
# 1. SCOPE 2 ELECTRICAL BASELINE:
#    Direct electricity consumption of the industrial machinery motor drive.
#    Baseline electrical emission constant: 0.65 kg CO2 / kWh.
#    Emission_energy = Energy_Consumption * 0.65
#
# 2. PRODUCTION & PROCESS OPERATIONAL EFFECT:
#    Producing physical units requires ancillary process energy (pneumatic tooling,
#    coolant pumping, parts handling, packaging). Each produced finished unit
#    introduces ~0.020 kg CO2 of process carbon footprint.
#    Emission_production = Production_Output * 0.020
#    (Naturally evaluates to 0 kg CO2 when machine is Idle or in Maintenance).
#
# 3. MACHINE STATUS & EQUIPMENT EFFICIENCY EFFECT:
#    - 'High' (+1.10 kg CO2): Over-stressed machine operation causing elevated
#      I^2*R thermal dissipation, lower power factor, and harmonic distortion losses.
#    - 'Normal' (0.00 kg CO2): Balanced nominal operating efficiency baseline.
#    - 'Idle' (+0.50 kg CO2): Standby parasitic energy loss where electricity is
#      consumed without producing useful output (pure carbon inefficiency).
#    - 'Maintenance' (-0.30 kg CO2): Offline sub-system inspection and diagnostic mode.
#
# 4. TEMPORAL DIURNAL SHIFT EFFECT (Working_Hour):
#    Grid marginal emissions follow a 24-hour diurnal curve. During peak daytime
#    manufacturing hours (08:00 - 18:00), grid operators dispatch thermal peaker plants
#    having higher marginal emission intensity, and plant HVAC/cooling demands peak.
#    Emission_hour = sin((Working_Hour - 6) / 24 * 2 * pi) * 0.85
#
# 5. WEEKEND OPERATIONAL EFFECT (Weekend):
#    Weekend operations involve lower overall plant baseload sharing, discontinuous
#    batch processing, and utility auxiliary cycling, introducing overhead:
#    Emission_weekend = Weekend * 1.35
#
# 6. REALISTIC OPERATIONAL & SENSOR VARIATION (epsilon):
#    Small zero-mean Gaussian variation representing Current Transformer (CT)
#    measurement tolerances (+/-1%), line voltage fluctuations (+/-2%), and raw
#    material property variations:
#    epsilon ~ Normal(mean=0.0, std=0.18) with random_seed=42 for reproducibility.
#
# COMPLETE MULTI-VARIABLE CO2 EMISSION FORMULA:
# CO2_Emission = max(0.1, round(
#     Emission_energy + Emission_production + Status_Effect +
#     Emission_hour + Emission_weekend + epsilon, 2
# ))
# ==============================================================================

input_file = "dataset/industrial_energy_features.csv"
output_file = "dataset/hybrid_dataset.csv"

print(f"Loading engineered features from {input_file}...")
df = pd.read_csv(input_file)

# Drop any obsolete columns
for obsolete_col in ["Temperature", "Humidity", "ambient_temp_C", "humidity_%"]:
    if obsolete_col in df.columns:
        df.drop(columns=[obsolete_col], inplace=True)

# 1. Base electricity emission component
emission_energy = df["Energy_Consumption"] * 0.65

# 2. Production process emission component
emission_production = df["Production_Output"] * 0.020

# 3. Machine operational state effect
status_effect_map = {
    "High": 1.10,
    "Normal": 0.00,
    "Idle": 0.50,
    "Maintenance": -0.30
}
status_effect = df["Machine_Status"].map(status_effect_map).fillna(0.00)

# 4. Diurnal shift working hour effect
hour_effect = np.sin((df["Working_Hour"] - 6.0) / 24.0 * 2.0 * np.pi) * 0.85

# 5. Weekend operational baseload overhead
weekend_effect = df["Weekend"] * 1.35

# 6. Realistic operational / sensor measurement variation (fixed seed for reproducibility)
np.random.seed(42)
noise = np.random.normal(loc=0.0, scale=0.18, size=len(df))

# Synthesize multi-variable CO2 emissions
df["CO2_Emission"] = (
    emission_energy +
    emission_production +
    status_effect +
    hour_effect +
    weekend_effect +
    noise
).clip(lower=0.1).round(2)

# Save hybrid dataset
df.to_csv(output_file, index=False)

print("\n[OK] Hybrid Dataset created successfully!")
print(f"Saved to: {output_file}")
print("Dataset Shape:", df.shape)
print("Columns in hybrid dataset:", df.columns.tolist())

print("\n========== TARGET CO2 EMISSION SUMMARY ==========")
print(df["CO2_Emission"].describe())

print("\n========== CORRELATIONS WITH CO2_EMISSION ==========")
numeric_cols = ["Energy_Consumption", "Production_Output", "Working_Hour", "Weekend", "CO2_Emission"]
corr_series = df[numeric_cols].corr()["CO2_Emission"].sort_values(ascending=False)
for col, val in corr_series.items():
    print(f"  {col:22s} : {val:+.4f}")

print("\n========== WEEKEND CHECK IN HYBRID DATASET ==========")
print("Weekend value counts:")
print(df["Weekend"].value_counts().to_dict())

print("\nFirst 5 Rows:")
print(df[["Timestamp", "Energy_Consumption", "Production_Output", "Machine_Status", "Working_Hour", "Weekend", "CO2_Emission"]].head())