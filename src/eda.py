import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).parent.parent

DATASET_PATH = BASE_DIR / "dataset" / "can_intrusion_clean.csv"
RESULTS_DIR = BASE_DIR / "results"

RESULTS_DIR.mkdir(exist_ok=True)

# ============================================================
# Load dataset
# ============================================================

print("Loading dataset...")

df = pd.read_csv(DATASET_PATH)

print(f"Dataset loaded: {len(df):,} records")

print("\nColumns:")
print(df.columns.tolist())


# ============================================================
# Basic information
# ============================================================

print("\n" + "=" * 70)
print("BASIC DATASET INFORMATION")
print("=" * 70)

print("\nDataset shape:")
print(df.shape)

print("\nMissing values:")
print(df.isnull().sum())

print("\nAttack distribution:")
print(df["Attack_Type"].value_counts())


# ============================================================
# 1. NORMAL VS ATTACK DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("1. NORMAL VS ATTACK")
print("=" * 70)

label_counts = df["Label"].value_counts()

print(label_counts)

plt.figure(figsize=(7, 5))

label_counts.rename(
    index={
        0: "Normal",
        1: "Attack"
    }
).plot(
    kind="bar"
)

plt.title("Normal vs Attack CAN Messages")
plt.xlabel("Traffic Type")
plt.ylabel("Number of Messages")
plt.xticks(rotation=0)

plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "01_normal_vs_attack.png",
    dpi=300
)

plt.close()


# ============================================================
# 2. MOST FREQUENT CAN IDs
# ============================================================

print("\n" + "=" * 70)
print("2. MOST FREQUENT CAN IDs")
print("=" * 70)

top_can_ids = (
    df["CAN_ID"]
    .value_counts()
    .head(15)
)

print(top_can_ids)

plt.figure(figsize=(10, 6))

top_can_ids.sort_values().plot(
    kind="barh"
)

plt.title("Top 15 Most Frequent CAN IDs")
plt.xlabel("Number of Messages")
plt.ylabel("CAN ID")

plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "02_top_can_ids.png",
    dpi=300
)

plt.close()


# ============================================================
# 3. CAN ID PATTERNS: NORMAL VS ATTACK
# ============================================================

print("\n" + "=" * 70)
print("3. CAN ID PATTERNS")
print("=" * 70)

top_ids = (
    df["CAN_ID"]
    .value_counts()
    .head(10)
    .index
)

can_id_attack = pd.crosstab(
    df[df["CAN_ID"].isin(top_ids)]["CAN_ID"],
    df[df["CAN_ID"].isin(top_ids)]["Attack_Type"]
)

print(can_id_attack)

plt.figure(figsize=(12, 7))

can_id_attack.plot(
    kind="bar",
    figsize=(12, 7)
)

plt.title("CAN ID Distribution by Traffic Type")
plt.xlabel("CAN ID")
plt.ylabel("Number of Messages")
plt.xticks(rotation=45)

plt.legend(
    title="Traffic Type"
)

plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "03_can_id_attack_patterns.png",
    dpi=300
)

plt.close()


# ============================================================
# 4. DLC DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("4. DLC DISTRIBUTION")
print("=" * 70)

dlc_distribution = pd.crosstab(
    df["DLC"],
    df["Attack_Type"]
)

print(dlc_distribution)

plt.figure(figsize=(10, 6))

dlc_distribution.plot(
    kind="bar",
    figsize=(10, 6)
)

plt.title("DLC Distribution by Traffic Type")
plt.xlabel("DLC")
plt.ylabel("Number of Messages")
plt.xticks(rotation=0)

plt.legend(
    title="Traffic Type"
)

plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "04_dlc_distribution.png",
    dpi=300
)

plt.close()


# ============================================================
# 5. CAN PAYLOAD BYTE ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("5. CAN PAYLOAD ANALYSIS")
print("=" * 70)

payload_columns = [
    "Data_0",
    "Data_1",
    "Data_2",
    "Data_3",
    "Data_4",
    "Data_5",
    "Data_6",
    "Data_7"
]

payload_means = df.groupby(
    "Attack_Type"
)[payload_columns].mean()

print("\nAverage payload byte values:")
print(payload_means.round(2))

plt.figure(figsize=(12, 7))

sns.heatmap(
    payload_means,
    annot=True,
    fmt=".1f"
)

plt.title("Average CAN Payload Bytes by Traffic Type")
plt.xlabel("CAN Payload Byte")
plt.ylabel("Traffic Type")

plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "05_payload_heatmap.png",
    dpi=300
)

plt.close()


# ============================================================
# 6. ATTACK TYPE COMPARISON
# ============================================================

print("\n" + "=" * 70)
print("6. ATTACK TYPE COMPARISON")
print("=" * 70)

attack_only = df[
    df["Attack_Type"] != "Normal"
]

attack_counts = (
    attack_only["Attack_Type"]
    .value_counts()
)

print(attack_counts)

plt.figure(figsize=(9, 6))

attack_counts.plot(
    kind="bar"
)

plt.title("Distribution of Attack Types")
plt.xlabel("Attack Type")
plt.ylabel("Number of Messages")
plt.xticks(rotation=20)

plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "06_attack_types.png",
    dpi=300
)

plt.close()


# ============================================================
# 7. FEATURE CORRELATION
# ============================================================

print("\n" + "=" * 70)
print("7. FEATURE CORRELATION")
print("=" * 70)

feature_columns = [
    "CAN_ID_numeric",
    "DLC",
    "Data_0",
    "Data_1",
    "Data_2",
    "Data_3",
    "Data_4",
    "Data_5",
    "Data_6",
    "Data_7",
    "Label"
]

correlation = df[
    feature_columns
].corr()

print("\nCorrelation with Label:")

print(
    correlation["Label"]
    .sort_values(
        ascending=False
    )
)

plt.figure(figsize=(12, 9))

sns.heatmap(
    correlation,
    annot=True,
    fmt=".2f"
)

plt.title("Feature Correlation Matrix")

plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "07_feature_correlation.png",
    dpi=300
)

plt.close()


# ============================================================
# Additional analysis: CAN ID by attack type
# ============================================================

print("\n" + "=" * 70)
print("TOP CAN IDs FOR EACH ATTACK")
print("=" * 70)

for attack_type in attack_only["Attack_Type"].unique():

    print(f"\n{attack_type}:")

    top_attack_ids = (
        attack_only[
            attack_only["Attack_Type"] == attack_type
        ]["CAN_ID"]
        .value_counts()
        .head(10)
    )

    print(top_attack_ids)


# ============================================================
# Summary
# ============================================================

print("\n" + "=" * 70)
print("EDA COMPLETE")
print("=" * 70)

print("\nGraphs saved in:")

print(RESULTS_DIR)

print("\nGenerated files:")

for file in sorted(RESULTS_DIR.glob("*.png")):

    print(
        " -",
        file.name
    )