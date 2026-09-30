import pandas as pd
from pathlib import Path

# Dataset folder
DATASET_DIR = Path(__file__).parent.parent / "dataset"

files = [
    "DoS_dataset.csv",
    "Fuzzy_dataset.csv",
    "gear_dataset.csv",
    "RPM_dataset.csv"
]

for filename in files:

    file_path = DATASET_DIR / filename

    print("\n" + "=" * 70)
    print(f"FILE: {filename}")
    print("=" * 70)

    try:
        df = pd.read_csv(file_path)

        print(f"\nRows: {len(df)}")
        print(f"Columns: {len(df.columns)}")

        print("\nColumn names:")
        print(df.columns.tolist())

        print("\nFirst 5 rows:")
        print(df.head())

        print("\nData types:")
        print(df.dtypes)

        print("\nMissing values:")
        print(df.isnull().sum())

    except Exception as e:
        print(f"ERROR reading {filename}: {e}")