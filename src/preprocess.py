import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================
# Configuration
# ============================================================

DATASET_DIR = Path(__file__).parent.parent / "dataset"
OUTPUT_FILE = DATASET_DIR / "can_intrusion_clean.csv"

FILES = {
    "DoS_dataset.csv": "DoS",
    "Fuzzy_dataset.csv": "Fuzzy",
    "gear_dataset.csv": "Gear_Spoofing",
    "RPM_dataset.csv": "RPM_Spoofing"
}

COLUMNS = [
    "Timestamp",
    "CAN_ID",
    "DLC",
    "Data_0",
    "Data_1",
    "Data_2",
    "Data_3",
    "Data_4",
    "Data_5",
    "Data_6",
    "Data_7",
    "Flag"
]

# Number of rows to keep from each class per file
MAX_NORMAL = 50000
MAX_ATTACK = 50000


# ============================================================
# Function to clean one dataset
# ============================================================

def process_file(filename, attack_type):

    file_path = DATASET_DIR / filename

    print("\n" + "=" * 70)
    print(f"Processing: {filename}")
    print(f"Attack type: {attack_type}")
    print("=" * 70)

    normal_parts = []
    attack_parts = []

    normal_count = 0
    attack_count = 0

    # Read in chunks so we don't load millions of rows into RAM
    for chunk in pd.read_csv(
        file_path,
        header=None,
        names=COLUMNS,
        chunksize=100000
    ):

        # Remove completely empty rows
        chunk = chunk.dropna(how="all")

        # Remove rows without a CAN ID
        chunk = chunk.dropna(subset=["CAN_ID"])

        # Convert flag to string
        chunk["Flag"] = chunk["Flag"].astype(str).str.strip().str.upper()

        # ----------------------------------------------------
        # Separate normal and attack traffic
        # ----------------------------------------------------

        normal = chunk[chunk["Flag"] == "R"].copy()
        attack = chunk[chunk["Flag"] == "T"].copy()

        # Keep limited amount of data
        if normal_count < MAX_NORMAL:
            remaining = MAX_NORMAL - normal_count
            normal = normal.head(remaining)

            if len(normal) > 0:
                normal_parts.append(normal)
                normal_count += len(normal)

        if attack_count < MAX_ATTACK:
            remaining = MAX_ATTACK - attack_count
            attack = attack.head(remaining)

            if len(attack) > 0:
                attack_parts.append(attack)
                attack_count += len(attack)

        # Stop reading once enough data is collected
        if normal_count >= MAX_NORMAL and attack_count >= MAX_ATTACK:
            break

    # Combine sampled data
    normal_df = (
        pd.concat(normal_parts, ignore_index=True)
        if normal_parts
        else pd.DataFrame(columns=COLUMNS)
    )

    attack_df = (
        pd.concat(attack_parts, ignore_index=True)
        if attack_parts
        else pd.DataFrame(columns=COLUMNS)
    )

    # --------------------------------------------------------
    # Add labels
    # --------------------------------------------------------

    normal_df["Label"] = 0
    normal_df["Attack_Type"] = "Normal"

    attack_df["Label"] = 1
    attack_df["Attack_Type"] = attack_type

    df = pd.concat(
        [normal_df, attack_df],
        ignore_index=True
    )

    print(f"Normal samples: {len(normal_df)}")
    print(f"Attack samples: {len(attack_df)}")

    return df


# ============================================================
# Process all four datasets
# ============================================================

all_datasets = []

for filename, attack_type in FILES.items():

    df = process_file(
        filename,
        attack_type
    )

    all_datasets.append(df)


# ============================================================
# Combine everything
# ============================================================

print("\nCombining datasets...")

combined_df = pd.concat(
    all_datasets,
    ignore_index=True
)


# ============================================================
# Convert CAN ID from hexadecimal to integer
# ============================================================

combined_df["CAN_ID_numeric"] = combined_df["CAN_ID"].apply(
    lambda x: int(str(x), 16)
    if pd.notna(x)
    else np.nan
)


# ============================================================
# Convert CAN data bytes from hexadecimal to integers
# ============================================================

DATA_COLUMNS = [
    "Data_0",
    "Data_1",
    "Data_2",
    "Data_3",
    "Data_4",
    "Data_5",
    "Data_6",
    "Data_7"
]

for column in DATA_COLUMNS:

    combined_df[column] = combined_df[column].apply(
        lambda x: int(str(x), 16)
        if pd.notna(x)
        else 0
    )


# ============================================================
# Convert numerical columns
# ============================================================

combined_df["Timestamp"] = pd.to_numeric(
    combined_df["Timestamp"],
    errors="coerce"
)

combined_df["DLC"] = pd.to_numeric(
    combined_df["DLC"],
    errors="coerce"
)


# ============================================================
# Remove invalid rows
# ============================================================

combined_df = combined_df.dropna(
    subset=[
        "Timestamp",
        "CAN_ID_numeric",
        "DLC"
    ]
)


# ============================================================
# Sort by timestamp
# ============================================================

combined_df = combined_df.sort_values(
    "Timestamp"
).reset_index(drop=True)


# ============================================================
# Calculate time difference between CAN messages
# ============================================================

combined_df["Time_Delta"] = (
    combined_df["Timestamp"].diff()
)

combined_df["Time_Delta"] = (
    combined_df["Time_Delta"]
    .fillna(0)
    .clip(lower=0)
)


# ============================================================
# Calculate approximate message frequency
# ============================================================

combined_df["Message_Rate"] = np.where(
    combined_df["Time_Delta"] > 0,
    1 / combined_df["Time_Delta"],
    0
)

# Prevent extreme values
combined_df["Message_Rate"] = (
    combined_df["Message_Rate"]
    .clip(upper=10000)
)


# ============================================================
# Shuffle dataset
# ============================================================

combined_df = combined_df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)


# ============================================================
# Save
# ============================================================

combined_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# Final information
# ============================================================

print("\n" + "=" * 70)
print("PREPROCESSING COMPLETE")
print("=" * 70)

print(f"\nTotal records: {len(combined_df)}")

print("\nClass distribution:")
print(combined_df["Label"].value_counts())

print("\nAttack distribution:")
print(combined_df["Attack_Type"].value_counts())

print("\nFinal columns:")
print(combined_df.columns.tolist())

print("\nSample:")
print(combined_df.head())

print(f"\nSaved to:")
print(OUTPUT_FILE)