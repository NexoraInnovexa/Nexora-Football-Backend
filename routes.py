from flask import Blueprint, request, jsonify, send_from_directory
import os
import joblib

try:
    from backend.extensions import db
    from backend.model import Prediction  # ✅ Ensure models.py exists
    from backend.fetch_data import fetch_live_matches  # ✅ Import live data fetcher
except ModuleNotFoundError:
    from extensions import db
    from model import Prediction  # ✅ Ensure models.py exists
    from fetch_data import fetch_live_matches  # ✅ Import live data fetcher

# ✅ Initialize Flask Blueprint
main = Blueprint("main", __name__, static_folder="build", static_url_path="/")

# ✅ Load the AI model
model_path = os.path.join(os.path.dirname(__file__), "football_model.pkl")

if os.path.exists(model_path):
    model = joblib.load(model_path)
    print("✅ AI Model loaded successfully")
else:
    print("⚠️ Model file not found! Train the model first.")
    model = None

# ✅ Serve React Frontend
@main.route("/", methods=["GET"])
def serve_home():
    """Serve the React frontend index.html"""
    return send_from_directory(main.static_folder, "index.html")

@main.route("/<path:path>", methods=["GET"])
def serve_static_files(path):
    """Serve static files like CSS, JS, and images"""
    file_path = os.path.join(main.static_folder, path)
    if os.path.exists(file_path):
        return send_from_directory(main.static_folder, path)
    return send_from_directory(main.static_folder, "index.html")   

# ✅ Fetch Live Matches API
@main.route("/live_matches", methods=["GET"])
def get_live_matches():
    """Fetch real-time football matches"""
    df = fetch_live_matches()
    
    if df is not None:
        return jsonify(df.to_dict(orient="records"))
    else:
        return jsonify({"error": "Failed to fetch live match data"}), 500


# 🔹 Extract match stats from live data
def get_live_match_data(home_team, away_team):
    """Find specific match stats from live data"""
    df = fetch_live_matches()

    if df is None or df.empty:
        return None

    # Normalize column names to lowercase
    df.columns = df.columns.str.lower()
    home_team = home_team.lower()
    away_team = away_team.lower()

    required_columns = {"hometeam", "awayteam", "hometeamscore", "awayteamscore"}
    if not required_columns.issubset(df.columns):
        return None

    # Find the match in the DataFrame
    match = df[(df["hometeam"].str.lower() == home_team) & 
               (df["awayteam"].str.lower() == away_team)]

    if match.empty:
        return None

    return {
        "home_goals": int(match.iloc[0]["hometeamscore"]) if "hometeamscore" in match.columns else 0,
        "away_goals": int(match.iloc[0]["awayteamscore"]) if "awayteamscore" in match.columns else 0
    }


# ✅ AI-Powered Prediction API
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

    # ✅ Fetch live match stats
    match_stats = get_live_match_data(home_team, away_team)

    if not match_stats:
        return jsonify({"error": "No live data found for this match"}), 400

    # ✅ Prepare model input features
    match_features = [[match_stats["home_goals"], match_stats["away_goals"]]]  # Modify based on your model

    try:
        predicted_winner = int(model.predict(match_features)[0])  # Ensure model output is converted correctly
    except Exception as e:
        return jsonify({"error": f"Model prediction failed: {str(e)}"}), 500

    # ✅ Interpret prediction results
    prediction_result = "Draw"
    if predicted_winner == 1:
        prediction_result = f"{home_team} Wins"
    elif predicted_winner == 0:
        prediction_result = f"{away_team} Wins"

    # ✅ Save prediction to the database
    prediction = Prediction(
        user_email=data.get("email", "anonymous@example.com"),  # Ensure email is provided
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
