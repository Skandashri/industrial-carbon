import pandas as pd

# -----------------------------
# Load Cleaned Dataset
# -----------------------------
df = pd.read_csv("dataset/industrial_energy_cleaned.csv")

print("Missing values before cleaning:")
print(df.isnull().sum())

# -----------------------------
# Fill missing values with Mean
# -----------------------------
df["Energy_Consumption"] = df["Energy_Consumption"].fillna(
    df["Energy_Consumption"].mean()
)

df["Temperature"] = df["Temperature"].fillna(
    df["Temperature"].mean()
)

df["Humidity"] = df["Humidity"].fillna(
    df["Humidity"].mean()
)

# -----------------------------
# Drop rows with remaining missing values
# -----------------------------
df.dropna(inplace=True)

print("\nMissing values after cleaning:")
print(df.isnull().sum())

# -----------------------------
# Save Cleaned Dataset
# -----------------------------
df.to_csv("dataset/industrial_energy_cleaned.csv", index=False)

print("\n✅ Missing values handled successfully!")
print("\nDataset Shape:", df.shape)
print("\nFirst 5 Rows:")
print(df.head())