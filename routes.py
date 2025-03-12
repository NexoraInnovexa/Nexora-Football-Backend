from flask import Blueprint, request, jsonify, send_from_directory, current_app, Response
from extensions import db
from model import Prediction  # ✅ Ensure models.py exists
from fetch_data import fetch_live_matches  # ✅ Import live data fetcher
import joblib
import os

# ✅ Initialize Flask Blueprint
main = Blueprint("main", __name__, static_folder="../frontend/public", template_folder="../frontend/public")

# ✅ Load the AI model
model_path = os.path.join(os.path.dirname(__file__), "football_model.pkl")

if os.path.exists(model_path):
    model = joblib.load(model_path)
    print("✅ AI Model loaded successfully")
else:
    print("⚠️ Model file not found! Train the model first.")
    model = None

# ✅ Serve React Frontend (Fix 404 Error)
@main.route("/", methods=["GET"])
def serve_home():
    """Serve the frontend index.html"""
    return send_from_directory(main.static_folder, "index.html")

@main.route("/favicon.ico", methods=["GET"])
def serve_favicon():
    """Prevent favicon errors by returning an empty response"""
    return Response(status=204)  # Returns 204 No Content instead of error

@main.route("/<path:path>", methods=["GET"])
def serve_static_files(path):
    """Serve static files like CSS, JS, and images"""
    file_path = os.path.join(main.static_folder, path)

    if os.path.exists(file_path):
        return send_from_directory(main.static_folder, path)
    
    return send_from_directory(main.static_folder, "index.html")  

# ✅ API to Get Live Football Data
@main.route("/live_matches", methods=["GET"])
def get_live_matches():
    """Fetch real-time football matches"""
    df = fetch_live_matches()
    
    if df is not None:
        return jsonify(df.to_dict(orient="records"))
    else:
        return jsonify({"error": "Failed to fetch live match data"}), 500


# ✅ AI-Powered Football Prediction API
@main.route('/predict', methods=['POST'])
def predict():
    """Predict football match outcome"""
    if model is None:
        return jsonify({"error": "AI model not available. Please train it first!"}), 500

    data = request.json
    home_team = data.get("home_team")
    away_team = data.get("away_team")
    
    if not home_team or not away_team:
        return jsonify({"error": "Missing team names"}), 400

    # Dummy match features (replace with real stats)
    match_features = [[1, 1]]  # Ensure it's a 2D list format

    try:
        predicted_winner = int(model.predict(match_features)[0])  # ✅ Fix potential error
    except Exception as e:
        return jsonify({"error": f"Model prediction failed: {str(e)}"}), 500

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
