import os
import sys
import json
import time
import argparse
import random

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
# Load model and feature names
# ---------------------------------------------------------

print("\nLoading IDS model...")

model = joblib.load(MODEL_PATH)

with open(FEATURE_PATH, "r") as f:
    feature_names = json.load(f)

print("Model loaded successfully.")
print("Features:", feature_names)


# ---------------------------------------------------------
# Convert CAN message into model features
# ---------------------------------------------------------

def create_features(can_id, payload):

    can_id_numeric = int(can_id, 16)

    payload_values = [
        int(byte, 16)
        for byte in payload
    ]

    if len(payload_values) != 8:
        raise ValueError("Payload must contain exactly 8 bytes.")

    features = {
        "CAN_ID_numeric": can_id_numeric,
        "Data_0": payload_values[0],
        "Data_1": payload_values[1],
        "Data_2": payload_values[2],
        "Data_3": payload_values[3],
        "Data_4": payload_values[4],
        "Data_5": payload_values[5],
        "Data_6": payload_values[6],
        "Data_7": payload_values[7],
    }

    return pd.DataFrame(
        [[features[name] for name in feature_names]],
        columns=feature_names
    )


# ---------------------------------------------------------
# Detect a single CAN message
# ---------------------------------------------------------

def detect_message(can_id, payload):

    features = create_features(can_id, payload)

    start_time = time.perf_counter()

    prediction = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]

    processing_time = (time.perf_counter() - start_time) * 1000

    confidence = max(probabilities) * 100

    if prediction == 1:
        status = "ATTACK"
    else:
        status = "NORMAL"

    return status, confidence, processing_time


# ---------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------

def interactive_mode():

    print("\n" + "=" * 60)
    print("        REAL-TIME CAN INTRUSION DETECTION")
    print("=" * 60)

    print("\nEnter CAN messages in this format:")
    print("CAN ID : 0316")
    print("Payload: 05 22 68 09 22 20 00 75")

    print("\nType 'exit' to stop.\n")

    while True:

        try:

            can_id = input("CAN ID > ").strip()

            if can_id.lower() == "exit":
                break

            payload_input = input("Payload > ").strip()

            if payload_input.lower() == "exit":
                break

            payload = payload_input.split()

            status, confidence, processing_time = detect_message(
                can_id,
                payload
            )

            print("\n----------------------------------------")
            print(f"CAN ID       : 0x{can_id.upper()}")
            print(f"Payload      : {' '.join(payload).upper()}")
            print(f"Prediction   : {status}")
            print(f"Confidence   : {confidence:.2f}%")
            print(f"Processing   : {processing_time:.3f} ms")

            if status == "ATTACK":
                print("SECURITY ALERT: Suspicious CAN message detected!")

            print("----------------------------------------\n")

        except ValueError as e:
            print(f"\nError: {e}\n")

        except KeyboardInterrupt:
            print("\n\nDetection stopped.")
            break


# ---------------------------------------------------------
# Simulated real-time CAN stream
# ---------------------------------------------------------

def simulation_mode(number_of_messages=20, delay=0.5):

    print("\n" + "=" * 70)
    print("       SIMULATED REAL-TIME CAN INTRUSION DETECTION")
    print("=" * 70)

    if not os.path.exists(DATA_PATH):
        print("\nDataset not found:")
        print(DATA_PATH)
        return

    print("\nLoading CAN messages from dataset...")

    df = pd.read_csv(DATA_PATH)

    print(f"Loaded {len(df):,} CAN messages.")
    print(f"Simulating {number_of_messages} messages...\n")

    print(
        f"{'No.':<5}"
        f"{'CAN ID':<10}"
        f"{'Payload':<26}"
        f"{'Prediction':<12}"
        f"{'Confidence':<12}"
        f"{'Latency':<10}"
    )

    print("-" * 75)

    samples = df.sample(
        n=min(number_of_messages, len(df)),
        random_state=random.randint(1, 10000)
    )

    for index, row in enumerate(samples.itertuples(index=False), start=1):

        can_id = format(int(row.CAN_ID_numeric), "04x")

        payload = [
            format(int(getattr(row, f"Data_{i}")), "02x")
            for i in range(8)
        ]

        status, confidence, processing_time = detect_message(
            can_id,
            payload
        )

        payload_string = " ".join(payload).upper()

        print(
            f"{index:<5}"
            f"0x{can_id.upper():<8}"
            f"{payload_string:<26}"
            f"{status:<12}"
            f"{confidence:>7.2f}%"
            f"{processing_time:>9.3f} ms"
        )

        if status == "ATTACK":
            print("      >>> SECURITY ALERT: ATTACK DETECTED <<<")

        time.sleep(delay)

    print("\nSimulation completed.")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Real-time simulated CAN intrusion detection"
    )

    parser.add_argument(
        "--demo",
        type=int,
        help="Run simulated CAN stream with N messages"
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between simulated CAN messages"
    )

    args = parser.parse_args()

    if args.demo:
        simulation_mode(
            number_of_messages=args.demo,
            delay=args.delay
        )
    else:
        interactive_mode()