from flask import Blueprint, request, jsonify, send_from_directory
import os
import joblib
import random
import traceback  # ✅ Import traceback for debugging
from datetime import datetime, timedelta

try:
    from backend.extensions import db
    from backend.model import Prediction, Subscription  # ✅ Ensure models.py has Subscription
    from backend.fetch_data import fetch_live_matches  # ✅ Import live data fetcher
except ModuleNotFoundError:
    from extensions import db
    from model import Prediction, Subscription
    from fetch_data import fetch_live_matches

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

ADMIN_ACCESS_CODE = os.getenv("ADMIN_ACCESS_CODE")   # ✅ Hardcoded admin access code

@main.route("/generate_access", methods=["POST"])
def generate_access():
    """Generate a 4-digit access code for a user based on their subscription."""
    data = request.json
    email = data.get("email")
    plan = data.get("plan")  # monthly, yearly, lifetime
    
    if not email or plan not in ["monthly", "yearly", "lifetime"]:
        return jsonify({"error": "Invalid request"}), 400
    
    existing_subscription = Subscription.query.filter_by(email=email).first()
    
    if existing_subscription and existing_subscription.plan == "lifetime":
        return jsonify({"access_code": existing_subscription.access_code, "expires_at": "Never"})
    
    new_code = str(random.randint(1000, 9999))
    expiration = None if plan == "lifetime" else datetime.utcnow() + timedelta(days=30 if plan == "monthly" else 365)
    
    if existing_subscription:
        existing_subscription.access_code = new_code
        existing_subscription.expires_at = expiration
    else:
        subscription = Subscription(email=email, plan=plan, access_code=new_code, expires_at=expiration)
        db.session.add(subscription)
    
    db.session.commit()
    return jsonify({"access_code": new_code, "expires_at": expiration.isoformat() if expiration is not None else "Never"})

@main.route("/regenerate_access", methods=["POST"])
def regenerate_access():
    """Regenerate a lost access code without extending expiration."""
    data = request.json
    email = data.get("email")
    
    subscription = Subscription.query.filter_by(email=email).first()
    if not subscription:
        return jsonify({"error": "No active subscription found"}), 404
    
    new_code = str(random.randint(1000, 9999))
    subscription.access_code = new_code
    db.session.commit()
    
    return jsonify({"access_code": new_code, "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else "Never"})
  

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

# ✅ Admin Dashboard API
@main.route("/admin", methods=["GET"])
def admin_dashboard():
    """View all subscribers and predictions."""
    subscribers = Subscription.query.all()
    predictions = Prediction.query.all()
    
    subscribers_data = [{"email": sub.email, "plan": sub.plan, "access_code": sub.access_code, "expires_at": sub.expires_at} for sub in subscribers]
    predictions_data = [{"user_email": pred.user_email, "home_team": pred.home_team, "away_team": pred.away_team, "predicted_score": pred.predicted_score} for pred in predictions]
    
    return jsonify({"subscribers": subscribers_data, "predictions": predictions_data})

@main.route("/admin/delete_prediction", methods=["POST"])
def delete_prediction():
    """Delete a specific prediction."""
    data = request.json
    prediction_id = data.get("prediction_id")
    
    prediction = Prediction.query.get(prediction_id)
    if not prediction:
        return jsonify({"error": "Prediction not found"}), 404
    
    db.session.delete(prediction)
    db.session.commit()
    
    return jsonify({"message": "Prediction deleted successfully"})


# ✅ AI-Powered Prediction API
@main.route('/predict', methods=['POST'])
def predict():
    """Predict football match outcome if user has a valid access code."""
    try:
        if model is None:
            return jsonify({"error": "AI model not available. Please train it first!"}), 500
        
        data = request.json
        email = data.get("email")
        access_code = data.get("access_code")
        home_team = data.get("home_team")
        away_team = data.get("away_team")

        if not home_team or not away_team or not email or not access_code:
            return jsonify({"error": "Missing required fields"}), 400
        
        if access_code != ADMIN_ACCESS_CODE:
            subscription = Subscription.query.filter_by(email=email, access_code=access_code).first()
            if not subscription or (subscription.expires_at and subscription.expires_at < datetime.utcnow()):
                return jsonify({"error": "Invalid or expired access code"}), 403
        
        match_stats = get_live_match_data(home_team, away_team)
        if not match_stats:
            return jsonify({"error": "No live data found for this match"}), 400
        
        match_features = [[match_stats["home_goals"], match_stats["away_goals"]]]
        predicted_winner = int(model.predict(match_features)[0])

        prediction_result = "Draw"
        if predicted_winner == 1:
            prediction_result = f"{home_team} Wins"
        elif predicted_winner == 0:
            prediction_result = f"{away_team} Wins"
        
        prediction = Prediction(user_email=email, home_team=home_team, away_team=away_team, predicted_score=prediction_result)
        db.session.add(prediction)
        db.session.commit()

        return jsonify({
            "home_team": home_team,
            "away_team": away_team,
            "predicted_winner": prediction_result
        })
    except Exception as e:
        print("🔥 ERROR:", str(e))
        print(traceback.format_exc())
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500
