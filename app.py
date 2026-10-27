import os
import json
import time
from datetime import datetime

import joblib
import pandas as pd
from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "models", "ids_model.pkl")
FEATURE_PATH = os.path.join(BASE_DIR, "models", "feature_names.json")
DATA_PATH = os.path.join(BASE_DIR, "dataset", "can_ml_features.csv")
LOG_PATH = os.path.join(BASE_DIR, "predictions_log.csv")

app = Flask(__name__)

model = joblib.load(MODEL_PATH)

with open(FEATURE_PATH, "r") as f:
    feature_names = json.load(f)

dataset = pd.read_csv(DATA_PATH)

SCENARIOS = {
    "DoS": "DoS",
    "Fuzzy": "Fuzzy",
    "Gear Spoofing": "Gear_Spoofing",
    "RPM Spoofing": "RPM_Spoofing",
}

stats = {
    "total": 0,
    "normal": 0,
    "attack": 0,
}


def create_features(can_id, payload):
    can_id = str(can_id).strip().lower().replace("0x", "")
    payload = [
        str(x).strip().lower().replace("0x", "")
        for x in payload
    ]

    if len(payload) != 8:
        raise ValueError("Payload must contain exactly 8 bytes.")

    can_id_numeric = int(can_id, 16)
    payload_values = [int(byte, 16) for byte in payload]

    if not 0 <= can_id_numeric <= 2047:
        raise ValueError("CAN ID must be between 0x000 and 0x7FF.")

    if any(value < 0 or value > 255 for value in payload_values):
        raise ValueError("Each payload byte must be between 00 and FF.")

    values = {
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
        [[values[name] for name in feature_names]],
        columns=feature_names,
    )


def predict_message(can_id, payload):
    features = create_features(can_id, payload)

    start = time.perf_counter()

    prediction = int(model.predict(features)[0])
    probabilities = model.predict_proba(features)[0]

    latency_ms = (time.perf_counter() - start) * 1000
    confidence = float(max(probabilities) * 100)

    status = "ATTACK" if prediction == 1 else "NORMAL"

    return status, confidence, latency_ms


def register_result(status):
    stats["total"] += 1

    if status == "ATTACK":
        stats["attack"] += 1
    else:
        stats["normal"] += 1


def log_prediction(record):
    pd.DataFrame([record]).to_csv(
        LOG_PATH,
        mode="a",
        header=not os.path.exists(LOG_PATH),
        index=False,
    )


def format_response(
    can_id,
    payload,
    status,
    confidence,
    latency_ms,
    scenario=None,
    ground_truth=None,
):
    register_result(status)

    timestamp = datetime.now().strftime("%H:%M:%S")

    can_id_clean = str(can_id).replace("0x", "").upper().zfill(3)
    payload_clean = [
        str(x).replace("0x", "").upper().zfill(2)
        for x in payload
    ]

    record = {
        "Timestamp": datetime.now().isoformat(timespec="seconds"),
        "Scenario": scenario or "",
        "Ground_Truth": ground_truth or "",
        "CAN_ID": can_id_clean,
        "Payload": " ".join(payload_clean),
        "Prediction": status,
        "Confidence": round(confidence, 4),
        "Latency_ms": round(latency_ms, 4),
    }

    log_prediction(record)

    return {
        "success": True,
        "timestamp": timestamp,
        "scenario": scenario,
        "ground_truth": ground_truth,
        "can_id": "0x" + can_id_clean,
        "payload": " ".join(payload_clean),
        "prediction": status,
        "confidence": round(confidence, 2),
        "latency_ms": round(latency_ms, 3),
        "stats": stats,
    }


@app.route("/")
def dashboard():
    return render_template(
        "index.html",
        scenarios=list(SCENARIOS.keys()),
    )

@app.route("/vehicle")
def vehicle_dashboard():
    return render_template("vehicle.html")


@app.route("/api/status")
def api_status():
    return jsonify({
        "server": "online",
        "model": "Random Forest IDS",
        "classification": "Binary: NORMAL / ATTACK",
        "features": len(feature_names),
        "dataset_messages": int(len(dataset)),
        "stats": stats,
    })


@app.route("/api/predict", methods=["POST"])
def api_predict():
    try:
        data = request.get_json(force=True)

        can_id = data.get("can_id")
        payload = data.get("payload")

        if not can_id or not isinstance(payload, list):
            return jsonify({
                "success": False,
                "error": "Provide can_id and an 8-byte payload list.",
            }), 400

        status, confidence, latency_ms = predict_message(
            can_id,
            payload,
        )

        return jsonify(
            format_response(
                can_id,
                payload,
                status,
                confidence,
                latency_ms,
            )
        )

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 400


@app.route("/api/simulate")
def api_simulate():
    row = dataset.sample(n=1).iloc[0]

    can_id = format(int(row["CAN_ID_numeric"]), "03X")
    payload = [
        format(int(row[f"Data_{i}"]), "02X")
        for i in range(8)
    ]

    status, confidence, latency_ms = predict_message(
        can_id,
        payload,
    )

    scenario = None
    ground_truth = "Normal" if row["Label"] == 0 else "Attack"

    return jsonify(
        format_response(
            can_id,
            payload,
            status,
            confidence,
            latency_ms,
            scenario=scenario,
            ground_truth=ground_truth,
        )
    )


@app.route("/api/scenario/<scenario_name>")
def api_scenario(scenario_name):
    """Replay one labeled message from a selected HCRL attack category."""

    if scenario_name not in SCENARIOS:
        return jsonify({
            "success": False,
            "error": "Unknown scenario.",
            "available": list(SCENARIOS.keys()),
        }), 404

    dataset_name = SCENARIOS[scenario_name]

    scenario_df = dataset[
        dataset["Attack_Type"] == dataset_name
    ]

    if scenario_df.empty:
        return jsonify({
            "success": False,
            "error": f"No messages found for {scenario_name}.",
        }), 404

    row = scenario_df.sample(n=1).iloc[0]

    can_id = format(int(row["CAN_ID_numeric"]), "03X")

    payload = [
        format(int(row[f"Data_{i}"]), "02X")
        for i in range(8)
    ]

    status, confidence, latency_ms = predict_message(
        can_id,
        payload,
    )

    return jsonify(
        format_response(
            can_id,
            payload,
            status,
            confidence,
            latency_ms,
            scenario=scenario_name,
            ground_truth=scenario_name,
        )
    )


@app.route("/api/reset", methods=["POST"])
def api_reset():
    stats["total"] = 0
    stats["normal"] = 0
    stats["attack"] = 0

    return jsonify({
        "success": True,
        "stats": stats,
    })


if __name__ == "__main__":
    print("=" * 65)
    print(" SDV CYBERSECURITY - CAN INTRUSION DETECTION DASHBOARD")
    print("=" * 65)
    print(" Dashboard: http://127.0.0.1:5000")
    print(" Model:     Random Forest IDS")
    print(" Features:  9")
    print(" Mode:      Simulated/replayed CAN traffic")
    print("=" * 65)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
