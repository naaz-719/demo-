from flask import Flask, request, jsonify
import mlflow.pyfunc
import mlflow
import pandas as pd
import joblib
import os

app = Flask(__name__)

# 1. Setup MLflow Tracking URI
# Using the absolute path to ensure Flask finds the mlruns folder
mlflow.set_tracking_uri("file:///C:/Users/hprus/Downloads/ml_artifacts/mlruns")

# 2. Define the exact path to your model folder
# This points directly to the artifact location on your drive
model_path = r"C:\\Users\\hprus\\Downloads\\ml_artifacts\\mlruns\\1\\models\\m-c219384735764878bc54f465161a6905\\artifacts"

# 3. Load Model & Features with Error Handling
try:
    print(f"--- Attempting to load model from: {model_path} ---")
    model = mlflow.pyfunc.load_model(model_path)
    
    # Load feature names (assuming it is in the 'model' folder one level up from Backend)
    feature_names_path = os.path.join("..", "model", "feature_names.pkl")
    feature_names = joblib.load(feature_names_path)
    
    print("✅ SUCCESS: Model and Feature names loaded successfully.")
except Exception as e:
    print(f"❌ ERROR DURING INITIALIZATION: {e}")
    model = None
    feature_names = None

@app.route('/', methods=['GET'])
def home():
    return "SUCCESS: Voyage API is active. Send POST requests to /predict"

@app.route('/predict', methods=['POST'])
def predict():
    # If the model failed to load at startup, return an error
    if model is None:
        return jsonify({'error': 'Model not loaded on server. Check server logs.'}), 500
    
    try:
        # Get data from POST request
        data = request.get_json(force=True)
        query_df = pd.DataFrame([data])
        
        # Reindex to match the training columns (fill missing with 0)
        if feature_names:
            query_df = query_df.reindex(columns=feature_names, fill_value=0)
        
        # Make Prediction
        prediction = model.predict(query_df)
        
        return jsonify({
            'status': 'ok', 
            'predicted_price': float(prediction[0])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    # Print available routes to terminal for debugging
    print("\n--- ACTIVE ROUTES ---")
    for rule in app.url_map.iter_rules():
        print(f"Path: {rule.rule} | Methods: {rule.methods}")
    print("----------------------\n")
    
    app.run(host='0.0.0.0', port=5000)