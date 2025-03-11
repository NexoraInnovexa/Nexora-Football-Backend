from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # ✅ Import CORS
import requests
import joblib
import os

app = Flask(__name__)

# ✅ Enable CORS for frontend (Netlify or Vercel)
CORS(app, origins=["https://nexora-soccer-predictor.netlify.app/", "https://your-frontend-domain.com"])

# 🔹 Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Amarachi1994@localhost/football_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ✅ Flutterwave API Key
FLW_SECRET_KEY = "your_flutterwave_secret_key"

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

# 🔹 Fetch Real-Time Match Data
def get_live_match_data(home_team, away_team):
    API_KEY = "your_football_api_key"
    url = f"https://api.sportsdata.io/v4/soccer/scores/json/Teams?key={API_KEY}"
    
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
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

    # Example: Extract useful stats for AI input
    features = [
        match_data.get('home_goals', 0),  # Use 0 if data is missing
        match_data.get('away_goals', 0)
    ]

    # ✅ AI Model Predicts Score
    predicted_score = model.predict([features])[0]

    # ✅ Store Prediction in Database
    new_prediction = Prediction(user_email, home_team, away_team, predicted_score)
    db.session.add(new_prediction)
    db.session.commit()

    return jsonify({
        "home_team": home_team,
        "away_team": away_team,
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
            "redirect_url": "https://your-frontend-domain.com/payment-success",
            "payment_options": "card",
            "customer": {
                "email": data["email"],
                "name": data["name"]
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
    app.run(debug=True)
