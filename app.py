from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # ✅ Import CORS
import requests
import joblib
import os
from routes import main  # ✅ Ensure correct import for your project

app = Flask(__name__)

# ✅ Register Blueprint after app is created
app.register_blueprint(main)

# ✅ Enable CORS for frontend (Netlify or Vercel)
CORS(app, resources={r"/*": {"origins": ["https://nexora-soccer-predictor.netlify.app"]}})

# ✅ Load database URL from environment variable (for Render)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://football_db_45ja_user:FcSz0jnwqUujnD1o1ZmWBaMEMP22RuiO@dpg-cv88815ds78s73e900hg-a/football_db_45ja")

# ✅ Convert `postgresql://` to `postgres://` for compatibility (ONLY for SQLAlchemy)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ✅ Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ✅ Load Flutterwave API Key securely
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY", "FLWSECK_TEST")

# 🔹 Load trained AI model safely
model_path = os.path.join(os.path.dirname(__file__), "football_model.pkl")

if os.path.exists(model_path):
    model = joblib.load(model_path)
    print("✅ AI Model loaded successfully.")
else:
    print(f"⚠️ Model file not found at {model_path}! Train the model first.")
    model = None

# 🔹 Define Prediction Table
class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    home_team = db.Column(db.String(100), nullable=False)
    away_team = db.Column(db.String(100), nullable=False)
    predicted_score = db.Column(db.String(50), nullable=False)

    def __init__(self, user_email, home_team, away_team, predicted_score):
        self.user_email = user_email
        self.home_team = home_team
        self.away_team = away_team
        self.predicted_score = predicted_score

# 🔹 Ensure DB Tables Exist Before Running Flask
with app.app_context():
    db.create_all()

# 🔹 Fetch Real-Time Match Data (Fixed Version)
def get_live_match_data(home_team, away_team):
    API_KEY = os.getenv("FOOTBALL_API_KEY", "your_football_api_key")
    url = f"https://api.sportsdata.io/v4/soccer/scores/json/MatchesByDate/2024-MAR-10?key={API_KEY}"

    response = requests.get(url)
    
    if response.status_code == 200:
        matches = response.json()  # Ensure we get a list of matches

        # ✅ Look for the match that contains home_team & away_team
        for match in matches:
            if (
                match.get("HomeTeam") and match.get("AwayTeam") and
                home_team.lower() in match["HomeTeam"].lower() and
                away_team.lower() in match["AwayTeam"].lower()
            ):
                return {
                    "home_team": match["HomeTeam"],
                    "away_team": match["AwayTeam"],
                    "home_goals": match["HomeTeamScore"] if match.get("HomeTeamScore") is not None else 0,
                    "away_goals": match["AwayTeamScore"] if match.get("AwayTeamScore") is not None else 0,
                }

        print(f"⚠️ No match found for {home_team} vs {away_team}.")
        return None

    else:
        print(f"⚠️ Failed to fetch live data: {response.text}")
        return None

# 🔹 AI Prediction API
@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({"error": "AI model not available. Please train it first!"}), 500

    data = request.json
    user_email = data.get('email')
    home_team = data.get('home_team')
    away_team = data.get('away_team')

    if not home_team or not away_team:
        return jsonify({"error": "Missing home or away team"}), 400

    # Fetch real-time match data
    match_data = get_live_match_data(home_team, away_team)

    if not match_data:
        return jsonify({"error": "Live data not available"}), 400

    # ✅ AI Model Predicts Score
    features = [match_data["home_goals"], match_data["away_goals"]]
    predicted_score = model.predict([features])[0]

    # ✅ Store Prediction in Database
    new_prediction = Prediction(user_email, match_data["home_team"], match_data["away_team"], predicted_score)
    db.session.add(new_prediction)
    db.session.commit()

    return jsonify({
        "home_team": match_data["home_team"],
        "away_team": match_data["away_team"],
        "predicted_score": predicted_score
    })

# 🔹 Payment Route (Flutterwave)
@app.route('/payment', methods=['POST'])
def create_payment():
    data = request.json
    try:
        headers = {
            "Authorization": f"Bearer {FLW_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        payment_data = {
            "tx_ref": f"trx_{os.urandom(5).hex()}",
            "amount": 4,  # Charge $4
            "currency": "USD",
            "redirect_url": "https://nexora-soccer-predictor.netlify.app/payment-success",
            "payment_options": "card",
            "customer": {
                "email": data["email"],
                "name": data.get("name", "Football Fan")
            },
            "customizations": {
                "title": "Football Prediction Payment",
                "description": "AI-generated football match predictions."
            }
        }

        response = requests.post("https://api.flutterwave.com/v3/payments", json=payment_data, headers=headers)
        response_data = response.json()

        if response_data["status"] == "success":
            return jsonify({"message": "Payment initiated!", "payment_link": response_data["data"]["link"]})
        else:
            return jsonify({"error": "Payment failed. Try again."}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# 🔹 Run Flask App
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
