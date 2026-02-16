from flask import Flask, request, jsonify
import joblib
import pandas as pd
import os

app = Flask(__name__)

# Load model & scaler
MODEL_PATH = "model/flight_price_model.pkl"
SCALER_PATH = "model/scaler.pkl"

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

# EXACT features used during training
FEATURE_COLUMNS = [
    "distance",
    "day",
    "agency_CloudNine",
    "agency_FlyingDrops",
    "agency_Rainbow",
    "flightType_economy",
    "flightType_business",
    "flightType_firstClass",
    "flightType_premium"
]

NUMERIC_COLS = ["distance", "day"]

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "Flight Price API running"})

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()

        # Required fields
        required = ["distance", "flightType", "agency"]
        for r in required:
            if r not in data:
                return jsonify({"error": f"Missing field: {r}"}), 400

        # Base dataframe
        df = pd.DataFrame([{
            "distance": data["distance"],
            "day": data.get("day", 1),
            "flightType": data["flightType"],
            "agency": data["agency"]
        }])

        # One-hot encode
        df = pd.get_dummies(df, columns=["flightType", "agency"])

        # Align columns EXACTLY to training
        df = df.reindex(columns=FEATURE_COLUMNS, fill_value=0)

        # Scale numeric features
        df[NUMERIC_COLS] = scaler.transform(df[NUMERIC_COLS])

        # Predict
        prediction = model.predict(df)[0]

        return jsonify({
            "predicted_price": round(float(prediction), 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
