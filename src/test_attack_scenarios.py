import os
import json
import time

import joblib
import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "models", "ids_model.pkl")
FEATURE_PATH = os.path.join(BASE_DIR, "models", "feature_names.json")
DATA_PATH = os.path.join(BASE_DIR, "dataset", "can_ml_features.csv")


# ---------------------------------------------------------
# Load model
# ---------------------------------------------------------

print("\n" + "=" * 75)
print("       CAN INTRUSION DETECTION - ATTACK SCENARIO TEST")
print("=" * 75)

print("\nLoading model...")

model = joblib.load(MODEL_PATH)

with open(FEATURE_PATH, "r") as f:
    feature_names = json.load(f)

print("Model loaded successfully.")


# ---------------------------------------------------------
# Load dataset
# ---------------------------------------------------------

print("\nLoading dataset...")

df = pd.read_csv(DATA_PATH)

print(f"Dataset size: {len(df):,} messages")


# ---------------------------------------------------------
# Attack types
# ---------------------------------------------------------

attack_types = [
    "DoS",
    "Fuzzy",
    "Gear_Spoofing",
    "RPM_Spoofing"
]


# ---------------------------------------------------------
# Test each attack scenario
# ---------------------------------------------------------

results = []


for attack_type in attack_types:

    print("\n" + "-" * 75)
    print(f"TESTING: {attack_type}")
    print("-" * 75)

    attack_df = df[df["Attack_Type"] == attack_type].copy()

    if attack_df.empty:
        print(f"No records found for {attack_type}")
        continue

    print(f"Available messages: {len(attack_df):,}")

    # Select 20 messages from this attack category
    samples = attack_df.sample(
        n=min(20, len(attack_df)),
        random_state=42
    )

    predictions = []

    for _, row in samples.iterrows():

        features = pd.DataFrame(
            [[row[name] for name in feature_names]],
            columns=feature_names
        )

        start = time.perf_counter()

        prediction = int(model.predict(features)[0])
        probability = model.predict_proba(features)[0]

        latency = (time.perf_counter() - start) * 1000

        confidence = max(probability) * 100

        predicted_label = (
            "ATTACK"
            if prediction == 1
            else "NORMAL"
        )

        predictions.append(prediction)

        results.append({
            "Attack_Type": attack_type,
            "CAN_ID": format(int(row["CAN_ID_numeric"]), "03X"),
            "Prediction": predicted_label,
            "Confidence": confidence,
            "Latency_ms": latency
        })

    # Calculate detection rate

    attack_predictions = sum(predictions)
    total = len(predictions)

    detection_rate = (
        attack_predictions / total
    ) * 100

    print(f"\nMessages tested : {total}")
    print(f"Detected attacks: {attack_predictions}")
    print(f"Missed attacks  : {total - attack_predictions}")
    print(f"Detection rate  : {detection_rate:.2f}%")

    # Display representative CAN IDs

    print("\nSample predictions:")

    for result in results[-min(5, total):]:

        print(
            f"CAN ID: 0x{result['CAN_ID']} | "
            f"Prediction: {result['Prediction']:<6} | "
            f"Confidence: {result['Confidence']:.2f}% | "
            f"Latency: {result['Latency_ms']:.3f} ms"
        )


# ---------------------------------------------------------
# Overall results
# ---------------------------------------------------------

results_df = pd.DataFrame(results)

print("\n" + "=" * 75)
print("                    OVERALL RESULTS")
print("=" * 75)

if not results_df.empty:

    summary = []

    for attack_type in attack_types:

        subset = results_df[
            results_df["Attack_Type"] == attack_type
        ]

        detected = (
            subset["Prediction"] == "ATTACK"
        ).sum()

        total = len(subset)

        rate = (
            detected / total * 100
            if total > 0
            else 0
        )

        summary.append({
            "Attack Type": attack_type,
            "Messages Tested": total,
            "Detected": detected,
            "Missed": total - detected,
            "Detection Rate (%)": rate
        })

    summary_df = pd.DataFrame(summary)

    print("\n")
    print(summary_df.to_string(index=False))

    # Save detailed results

    output_path = os.path.join(
        BASE_DIR,
        "results",
        "attack_scenario_results.csv"
    )

    results_df.to_csv(
        output_path,
        index=False
    )

    print(
        f"\nDetailed results saved to:\n{output_path}"
    )

print("\nAttack scenario testing completed.")