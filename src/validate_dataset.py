import pandas as pd

# ---------------------------------
# Load Hybrid Dataset
# ---------------------------------
hybrid_df = pd.read_csv("dataset/hybrid_dataset.csv")

# ---------------------------------
# Load IoT Carbon Dataset
# ---------------------------------
iot_df = pd.read_csv("dataset/iot_carbon.csv")

# ---------------------------------
# CO₂ column names
# ---------------------------------
HYBRID_CO2_COLUMN = "CO2_Emission"
IOT_CO2_COLUMN = "Carbon_Emission_kgCO2"

# ---------------------------------
# Hybrid Dataset Statistics
# ---------------------------------
hybrid_min = hybrid_df[HYBRID_CO2_COLUMN].min()
hybrid_max = hybrid_df[HYBRID_CO2_COLUMN].max()
hybrid_mean = hybrid_df[HYBRID_CO2_COLUMN].mean()

# ---------------------------------
# IoT Dataset Statistics
# ---------------------------------
iot_min = iot_df[IOT_CO2_COLUMN].min()
iot_max = iot_df[IOT_CO2_COLUMN].max()
iot_mean = iot_df[IOT_CO2_COLUMN].mean()

# ---------------------------------
# Display Statistics
# ---------------------------------
print("\n========== CO₂ Validation ==========\n")

print(f"{'Statistic':<15}{'Hybrid Dataset':>20}{'IoT Dataset':>20}")
print("-" * 55)

print(f"{'Minimum':<15}{hybrid_min:>20.2f}{iot_min:>20.2f}")
print(f"{'Maximum':<15}{hybrid_max:>20.2f}{iot_max:>20.2f}")
print(f"{'Average':<15}{hybrid_mean:>20.2f}{iot_mean:>20.2f}")

print("-" * 55)

# ---------------------------------
# Validation
# ---------------------------------
difference = abs(hybrid_mean - iot_mean)

print(f"\nAverage CO₂ Difference : {difference:.2f} kg")

if difference <= 5:
    print("✅ Excellent! Hybrid dataset is very realistic.")
elif difference <= 15:
    print("🟢 Good! Hybrid dataset is reasonably close to the IoT dataset.")
elif difference <= 30:
    print("🟡 Acceptable, but you may adjust the emission factor.")
else:
    print("🔴 Large difference detected.")
    print("Consider changing the emission factor from 0.82 to a value that better matches the IoT dataset.")

print("\n========== Validation Completed ==========")