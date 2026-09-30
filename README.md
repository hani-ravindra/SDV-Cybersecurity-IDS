# Stage 11 — Attack Scenario Dashboard

This update adds browser-based testing for:

- DoS
- Fuzzy
- Gear Spoofing
- RPM Spoofing

The dashboard replays one labeled message from the HCRL-derived dataset for the selected scenario.

Important:
The current Random Forest model is binary:
0 = NORMAL
1 = ATTACK

The scenario name is obtained from the dataset's Attack_Type label. It is not a multiclass prediction from the current model.

## Installation

Copy these files into the existing SDV-Cybersecurity-IDS project:

app.py
templates/index.html
static/style.css
static/app.js

Keep the existing:

models/
dataset/

## Run

From the project root:

python app.py

Then open:

http://127.0.0.1:5000

## Scenario testing

Click one of:

- DoS
- Fuzzy
- Gear Spoofing
- RPM Spoofing

The selected labeled CAN message is sent through the Random Forest and the dashboard displays:

- Scenario
- CAN ID
- Payload
- IDS Prediction
- Confidence
- Inference latency
- Security alert
- Event log

## API

GET /api/scenario/DoS
GET /api/scenario/Fuzzy
GET /api/scenario/Gear%20Spoofing
GET /api/scenario/RPM%20Spoofing

GET /api/simulate

POST /api/predict

POST /api/reset
