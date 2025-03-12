from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # ✅ Import CORS
import requests
import joblib
import os
from backend.routes import main  # ✅ Import Blueprint correctly

app = Flask(__name__)

# ✅ Register Blueprint (No need to redefine /predict)
app.register_blueprint(main, url_prefix="/")

# ✅ Enable CORS for frontend (Netlify or Vercel)
CORS(app, origins=["https://nexora-soccer-predictor.netlify.app"])

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
    port = int(os.environ.get("PORT", 10000))  # Use Render's assigned port
    print(f"🚀 Server running on port {port}")  # Debug log
    app.run(host='0.0.0.0', port=port)
