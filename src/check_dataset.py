import pandas as pd

# ==========================================================
# LOAD DATASET
# ==========================================================

df = pd.read_csv(
    "dataset/hybrid_dataset.csv"
)


# ==========================================================
# CHECK IMPORTANT COLUMNS
# ==========================================================

columns = [
    "Energy_Consumption",
    "Production_Output",
    "Working_Hour",
    "Weekend",
    "CO2_Emission"
]


print("\n========== DATASET DIAGNOSTIC ==========\n")


# ==========================================================
# DATASET SIZE
# ==========================================================

print("Rows:", len(df))
print("Columns:", len(df.columns))


# ==========================================================
# STATISTICS
# ==========================================================

print("\n========== COLUMN STATISTICS ==========\n")

print(
    df[columns].describe()
)


# ==========================================================
# ENERGY RANGE
# ==========================================================

print("\n========== ENERGY RANGE ==========\n")

print(
    "Minimum Energy:",
    df["Energy_Consumption"].min()
)

print(
    "Maximum Energy:",
    df["Energy_Consumption"].max()
)

print(
    "Mean Energy:",
    df["Energy_Consumption"].mean()
)


# ==========================================================
# CO2 RANGE
# ==========================================================

print("\n========== CO2 RANGE ==========\n")

print(
    "Minimum CO2:",
    df["CO2_Emission"].min()
)

print(
    "Maximum CO2:",
    df["CO2_Emission"].max()
)

print(
    "Mean CO2:",
    df["CO2_Emission"].mean()
)


# ==========================================================
# UNIQUE ENERGY VALUES
# ==========================================================

print("\n========== ENERGY SAMPLE ==========\n")

print(
    df["Energy_Consumption"]
    .sort_values()
    .head(20)
    .to_string(index=False)
)

print("\n...")

print(
    df["Energy_Consumption"]
    .sort_values()
    .tail(20)
    .to_string(index=False)
)


# ==========================================================
# CORRELATION
# ==========================================================

print("\n========== CORRELATION WITH CO2 ==========\n")

print(
    df[columns].corr()["CO2_Emission"]
    .sort_values(ascending=False)
)


print(
    "\n========================================"
)
