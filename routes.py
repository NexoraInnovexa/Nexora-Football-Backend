from flask import Blueprint, request, jsonify
from backend import db
from backend.model import Prediction  # ✅ Fix import (ensure models.py exists)
from backend.fetch_data import fetch_live_matches  # ✅ Import live data fetcher
import joblib
import os

main = Blueprint("main", __name__)

# ✅ Load the AI model
model_path = os.path.join(os.path.dirname(__file__), "football_model.pkl")

if os.path.exists(model_path):
    model = joblib.load(model_path)
    print("✅ AI Model loaded successfully")
else:
    print("⚠️ Model file not found! Train the model first.")
    model = None

@main.route("/")
def home():
    return jsonify({"message": "Welcome to AI Football Predictor!"})

# ✅ New API to Get Live Football Data
@main.route("/live_matches", methods=["GET"])
def get_live_matches():
    """API endpoint to fetch real-time football matches"""
    df = fetch_live_matches()
    
    if df is not None:
        return jsonify(df.to_dict(orient="records"))
    else:
        return jsonify({"error": "Failed to fetch live match data"}), 500

# ✅ AI-Powered Football Prediction API
@main.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'GET':
        return jsonify({"message": "Use POST request with home_team and away_team"}), 200

    if model is None:
        return jsonify({"error": "AI model not available. Please train it first!"}), 500

    data = request.json
    home_team = data.get("home_team")
    away_team = data.get("away_team")
    
    if not home_team or not away_team:
        return jsonify({"error": "Missing team names"}), 400

    # Default features (update with real match data)
    match_features = [[1, 1]]  # Replace with real stats

    predicted_winner = model.predict(match_features)[0]  # Use AI model to predict

    prediction_result = "Draw"
    if predicted_winner == 1:
        prediction_result = f"{home_team} Wins"
    elif predicted_winner == 0:
        prediction_result = f"{away_team} Wins"

    # ✅ Save prediction to the database
    prediction = Prediction(
        user_email="test@example.com",
        home_team=home_team,
        away_team=away_team,
        predicted_score=prediction_result
    )
    db.session.add(prediction)
    db.session.commit()

    return jsonify({
        "home_team": home_team,
        "away_team": away_team,
        "predicted_winner": prediction_result
    })
