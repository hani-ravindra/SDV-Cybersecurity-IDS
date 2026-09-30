import pandas as pd
import numpy as np
import json
import time
import joblib

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).parent.parent

DATASET_PATH = (
    BASE_DIR
    / "dataset"
    / "can_ml_features.csv"
)

MODEL_DIR = (
    BASE_DIR
    / "models"
)

MODEL_DIR.mkdir(
    exist_ok=True
)


# ============================================================
# Load dataset
# ============================================================

print("=" * 70)
print("LOADING ML DATASET")
print("=" * 70)

df = pd.read_csv(DATASET_PATH)

print(f"\nDataset shape: {df.shape}")


# ============================================================
# Load feature names
# ============================================================

FEATURE_FILE = MODEL_DIR / "feature_names.json"

with open(FEATURE_FILE, "r") as file:
    feature_names = json.load(file)


print("\nFeatures used:")
for feature in feature_names:
    print(f"  - {feature}")


# ============================================================
# Prepare X and y
# ============================================================

X = df[feature_names]

y = df["Label"]


print("\nTarget distribution:")
print(y.value_counts())


# ============================================================
# Train / Test split
# ============================================================

print("\n" + "=" * 70)
print("CREATING TRAIN / TEST SPLIT")
print("=" * 70)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print(f"\nTraining samples: {len(X_train):,}")
print(f"Testing samples:  {len(X_test):,}")

print("\nTraining distribution:")
print(y_train.value_counts())

print("\nTesting distribution:")
print(y_test.value_counts())


# ============================================================
# Define models
# ============================================================

models = {

    "Logistic Regression": Pipeline([
        (
            "scaler",
            StandardScaler()
        ),
        (
            "classifier",
            LogisticRegression(
                max_iter=1000,
                random_state=42
            )
        )
    ]),

    "Decision Tree": DecisionTreeClassifier(
        max_depth=20,
        min_samples_split=5,
        random_state=42
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=150,
        max_depth=20,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
}


# ============================================================
# Train models
# ============================================================

results = []

trained_models = {}

for name, model in models.items():

    print("\n" + "=" * 70)
    print(f"TRAINING: {name}")
    print("=" * 70)

    start_time = time.time()

    model.fit(
        X_train,
        y_train
    )

    training_time = time.time() - start_time

    # Predictions
    y_pred = model.predict(X_test)

    # Metrics
    accuracy = accuracy_score(
        y_test,
        y_pred
    )

    precision = precision_score(
        y_test,
        y_pred,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        y_pred,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        y_pred,
        zero_division=0
    )

    results.append({
        "Model": name,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1_Score": f1,
        "Training_Time_Seconds": training_time
    })

    trained_models[name] = model

    print(f"\nAccuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1 Score : {f1:.4f}")
    print(f"Training time: {training_time:.2f} seconds")


# ============================================================
# Compare models
# ============================================================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by="F1_Score",
    ascending=False
).reset_index(drop=True)


print("\n" + "=" * 70)
print("MODEL COMPARISON")
print("=" * 70)

print(
    results_df.to_string(
        index=False
    )
)


# ============================================================
# Select best model
# ============================================================

best_model_name = results_df.iloc[0]["Model"]

best_model = trained_models[
    best_model_name
]


print("\n" + "=" * 70)
print("BEST MODEL")
print("=" * 70)

print(
    f"\nSelected model: {best_model_name}"
)


# ============================================================
# Save best model
# ============================================================

MODEL_PATH = (
    MODEL_DIR
    / "ids_model.pkl"
)

joblib.dump(
    best_model,
    MODEL_PATH
)


# ============================================================
# Save model metadata
# ============================================================

metadata = {
    "model": best_model_name,
    "features": feature_names,
    "target": "Label",
    "classes": {
        "0": "Normal",
        "1": "Attack"
    },
    "test_size": 0.20,
    "random_state": 42
}

METADATA_PATH = (
    MODEL_DIR
    / "model_metadata.json"
)

with open(
    METADATA_PATH,
    "w"
) as file:

    json.dump(
        metadata,
        file,
        indent=4
    )


# ============================================================
# Save comparison results
# ============================================================

RESULTS_PATH = (
    BASE_DIR
    / "results"
    / "model_comparison.csv"
)

RESULTS_PATH.parent.mkdir(
    exist_ok=True
)

results_df.to_csv(
    RESULTS_PATH,
    index=False
)


# ============================================================
# Final output
# ============================================================

print("\n" + "=" * 70)
print("MODEL TRAINING COMPLETE")
print("=" * 70)

print(
    f"\nBest model: {best_model_name}"
)

print(
    f"\nModel saved to:"
    f"\n{MODEL_PATH}"
)

print(
    f"\nMetadata saved to:"
    f"\n{METADATA_PATH}"
)

print(
    f"\nComparison saved to:"
    f"\n{RESULTS_PATH}"
)
