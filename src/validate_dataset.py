import sys
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ---------------------------------
# Load Hybrid Dataset
# ---------------------------------
hybrid_df = pd.read_csv("dataset/hybrid_dataset.csv")

# ---------------------------------
# Load IoT Carbon Dataset
# ---------------------------------
iot_df = pd.read_csv("dataset/iot_carbon.csv")

# ---------------------------------
# CO2 column names
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
print("\n========== CO2 Validation ==========\n")

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

print(f"\nAverage CO2 Difference : {difference:.2f} kg")

if difference <= 15:
    print("[OK] Excellent! Hybrid dataset has realistic industrial emission domain.")
elif difference <= 30:
    print("[OK] Good! Hybrid dataset is reasonably aligned with baseline emissions.")
else:
    print("[INFO] Difference detected between industrial equipment emissions and personal IoT emissions.")

print("\n========== Validation Completed ==========")