import pandas as pd
import numpy as np
import json
from pathlib import Path

# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).parent.parent

INPUT_FILE = (
    BASE_DIR
    / "dataset"
    / "can_intrusion_clean.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "dataset"
    / "can_ml_features.csv"
)

FEATURE_FILE = (
    BASE_DIR
    / "models"
    / "feature_names.json"
)

# Create models directory if needed
FEATURE_FILE.parent.mkdir(
    exist_ok=True
)


# ============================================================
# Load dataset
# ============================================================

print("Loading cleaned CAN dataset...")

df = pd.read_csv(INPUT_FILE)

print(f"Records loaded: {len(df):,}")


# ============================================================
# Define feature columns
# ============================================================

payload_features = [
    "Data_0",
    "Data_1",
    "Data_2",
    "Data_3",
    "Data_4",
    "Data_5",
    "Data_6",
    "Data_7"
]

selected_features = [
    "CAN_ID_numeric"
] + payload_features


# ============================================================
# Verify required columns
# ============================================================

missing_features = [
    feature
    for feature in selected_features
    if feature not in df.columns
]

if missing_features:

    raise ValueError(
        f"Missing features: {missing_features}"
    )


# ============================================================
# Create ML dataset
# ============================================================

ml_df = df[
    selected_features
    + [
        "Label",
        "Attack_Type"
    ]
].copy()


# ============================================================
# Handle missing values
# ============================================================

print("\nChecking missing values...")

print(
    ml_df.isnull().sum()
)


# Fill numerical missing values
ml_df[selected_features] = (
    ml_df[selected_features]
    .fillna(0)
)


# ============================================================
# Ensure numerical types
# ============================================================

for feature in selected_features:

    ml_df[feature] = pd.to_numeric(
        ml_df[feature],
        errors="coerce"
    )


# Replace any remaining invalid values
ml_df[selected_features] = (
    ml_df[selected_features]
    .replace(
        [np.inf, -np.inf],
        np.nan
    )
    .fillna(0)
)


# ============================================================
# Verify feature ranges
# ============================================================

print("\nFeature ranges:")

for feature in selected_features:

    print(
        f"{feature:18s}"
        f" Min={ml_df[feature].min():8.2f}"
        f" Max={ml_df[feature].max():8.2f}"
    )


# ============================================================
# Feature correlation with target
# ============================================================

print("\nCorrelation with attack label:")

correlations = (
    ml_df[
        selected_features + ["Label"]
    ]
    .corr()["Label"]
    .drop("Label")
    .sort_values(
        ascending=False
    )
)

print(
    correlations
)


# ============================================================
# Save ML dataset
# ============================================================

ml_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# Save feature names
# ============================================================

with open(
    FEATURE_FILE,
    "w"
) as file:

    json.dump(
        selected_features,
        file,
        indent=4
    )


# ============================================================
# Final summary
# ============================================================

print("\n" + "=" * 70)
print("FEATURE ENGINEERING COMPLETE")
print("=" * 70)

print(
    f"\nNumber of ML features: "
    f"{len(selected_features)}"
)

print("\nSelected features:")

for feature in selected_features:

    print(
        f"  ✓ {feature}"
    )

print("\nExcluded features:")

print("  ✗ Timestamp")
print("  ✗ DLC")
print("  ✗ Flag")
print("  ✗ Time_Delta")
print("  ✗ Message_Rate")

print(
    f"\nML dataset saved to:\n{OUTPUT_FILE}"
)

print(
    f"\nFeature list saved to:\n{FEATURE_FILE}"
)

print(
    f"\nFinal ML dataset shape: "
    f"{ml_df.shape}"
)