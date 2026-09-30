import pandas as pd
import numpy as np
import json
import joblib

import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path

from sklearn.model_selection import train_test_split

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
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

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "ids_model.pkl"
)

FEATURE_PATH = (
    BASE_DIR
    / "models"
    / "feature_names.json"
)

RESULTS_DIR = (
    BASE_DIR
    / "results"
)

RESULTS_DIR.mkdir(
    exist_ok=True
)


# ============================================================
# Load dataset
# ============================================================

print("=" * 70)
print("LOADING DATA")
print("=" * 70)

df = pd.read_csv(
    DATASET_PATH
)

print(
    f"\nDataset shape: {df.shape}"
)


# ============================================================
# Load features
# ============================================================

with open(
    FEATURE_PATH,
    "r"
) as file:

    feature_names = json.load(
        file
    )

X = df[
    feature_names
]

y = df[
    "Label"
]


# ============================================================
# Recreate SAME test split
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


print(
    f"\nTest samples: {len(X_test):,}"
)


# ============================================================
# Load trained model
# ============================================================

print("\nLoading trained Random Forest...")

model = joblib.load(
    MODEL_PATH
)


# ============================================================
# Make predictions
# ============================================================

print("Generating predictions...")

y_pred = model.predict(
    X_test
)


# ============================================================
# Calculate metrics
# ============================================================

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


# ============================================================
# Print metrics
# ============================================================

print("\n" + "=" * 70)
print("MODEL EVALUATION")
print("=" * 70)

print(
    f"\nAccuracy : {accuracy:.6f} "
    f"({accuracy * 100:.4f}%)"
)

print(
    f"Precision: {precision:.6f} "
    f"({precision * 100:.4f}%)"
)

print(
    f"Recall   : {recall:.6f} "
    f"({recall * 100:.4f}%)"
)

print(
    f"F1 Score : {f1:.6f} "
    f"({f1 * 100:.4f}%)"
)


# ============================================================
# Classification report
# ============================================================

print("\n" + "=" * 70)
print("CLASSIFICATION REPORT")
print("=" * 70)

report = classification_report(
    y_test,
    y_pred,
    target_names=[
        "Normal",
        "Attack"
    ],
    digits=4
)

print(
    report
)


# ============================================================
# Confusion Matrix
# ============================================================

cm = confusion_matrix(
    y_test,
    y_pred
)

print("\n" + "=" * 70)
print("CONFUSION MATRIX")
print("=" * 70)

print(cm)

tn, fp, fn, tp = cm.ravel()

print(
    f"\nTrue Negatives : {tn:,}"
)

print(
    f"False Positives: {fp:,}"
)

print(
    f"False Negatives: {fn:,}"
)

print(
    f"True Positives : {tp:,}"
)


# ============================================================
# Plot confusion matrix
# ============================================================

plt.figure(
    figsize=(7, 6)
)

sns.heatmap(
    cm,
    annot=True,
    fmt=",d",
    cmap="Blues",
    xticklabels=[
        "Normal",
        "Attack"
    ],
    yticklabels=[
        "Normal",
        "Attack"
    ]
)

plt.title(
    "Random Forest Confusion Matrix"
)

plt.xlabel(
    "Predicted Label"
)

plt.ylabel(
    "Actual Label"
)

plt.tight_layout()

CONFUSION_PATH = (
    RESULTS_DIR
    / "08_confusion_matrix.png"
)

plt.savefig(
    CONFUSION_PATH,
    dpi=300
)

plt.close()


# ============================================================
# Feature importance
# ============================================================

print("\n" + "=" * 70)
print("FEATURE IMPORTANCE")
print("=" * 70)

importance = model.feature_importances_

feature_importance = pd.DataFrame({
    "Feature": feature_names,
    "Importance": importance
})

feature_importance = (
    feature_importance
    .sort_values(
        by="Importance",
        ascending=False
    )
)

print(
    feature_importance.to_string(
        index=False
    )
)


# ============================================================
# Feature importance plot
# ============================================================

plt.figure(
    figsize=(10, 6)
)

plt.barh(
    feature_importance["Feature"],
    feature_importance["Importance"]
)

plt.gca().invert_yaxis()

plt.title(
    "Random Forest Feature Importance"
)

plt.xlabel(
    "Importance"
)

plt.ylabel(
    "Feature"
)

plt.tight_layout()

IMPORTANCE_PATH = (
    RESULTS_DIR
    / "09_feature_importance.png"
)

plt.savefig(
    IMPORTANCE_PATH,
    dpi=300
)

plt.close()


# ============================================================
# Save metrics
# ============================================================

metrics = pd.DataFrame({
    "Metric": [
        "Accuracy",
        "Precision",
        "Recall",
        "F1 Score",
        "True Negatives",
        "False Positives",
        "False Negatives",
        "True Positives"
    ],
    "Value": [
        accuracy,
        precision,
        recall,
        f1,
        tn,
        fp,
        fn,
        tp
    ]
})

METRICS_PATH = (
    RESULTS_DIR
    / "evaluation_metrics.csv"
)

metrics.to_csv(
    METRICS_PATH,
    index=False
)


# ============================================================
# Final output
# ============================================================

print("\n" + "=" * 70)
print("EVALUATION COMPLETE")
print("=" * 70)

print(
    f"\nConfusion matrix saved to:"
    f"\n{CONFUSION_PATH}"
)

print(
    f"\nFeature importance saved to:"
    f"\n{IMPORTANCE_PATH}"
)

print(
    f"\nMetrics saved to:"
    f"\n{METRICS_PATH}"
)