from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  
import requests
import joblib
import os
from datetime import datetime, timedelta
import random

# ✅ Handle dynamic import for local vs. Render
try:
    from backend.extensions import db
    from backend.model import Prediction, Subscription
    from backend.fetch_data import fetch_live_matches 
    from backend.routes import main  # ✅ Works locally
except ModuleNotFoundError:
    from routes import main  # ✅ Works on Render
    from extensions import db
    from model import Prediction, Subscription
    from fetch_data import fetch_live_matches 

app = Flask(__name__)

# ✅ Register Blueprint (No need to redefine /predict)
app.register_blueprint(main, url_prefix="/")

# ✅ Enable CORS for frontend
CORS(app, resources={r"/*": {"origins": "https://nexora-soccer-predictor.netlify.app"}})

# ✅ Load database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://football_db_45ja_user:password@host/football_db_45ja")

# ✅ Convert `postgres://` to `postgresql://` for compatibility (ONLY for SQLAlchemy)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ✅ Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ Initialize database
with app.app_context():
    db.init_app(app)
    db.create_all()

# ✅ Load Flutterwave API Key securely
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY", "FLWSECK_TEST")

# ✅ Load trained AI model safely
model_path = os.path.join(os.path.dirname(__file__), "football_model.pkl")
model = joblib.load(model_path) if os.path.exists(model_path) else None
if model:
    print("✅ AI Model loaded successfully.")
else:
    print(f"⚠️ Model file not found at {model_path}! Train the model first.")

# 🔹 Payment Route (Flutterwave)
@app.route('/payment', methods=['POST'])
def create_payment():
    data = request.json
    email = data.get("email")
    plan_type = data.get("plan_type")
    
    price_map = {"instant": 4, "monthly": 17, "yearly": 204, "lifetime": 5000}
    if plan_type not in price_map:
        return jsonify({"error": "Invalid plan type"}), 400
    
    price = price_map[plan_type]
    access_code = str(random.randint(1000, 9999)) if plan_type != "instant" else None
    expires_at = None if plan_type == "lifetime" else datetime.utcnow() + timedelta(days=30 if plan_type == "monthly" else 365)
    
    headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}", "Content-Type": "application/json"}
    payment_data = {
        "tx_ref": f"trx_{os.urandom(5).hex()}",
        "amount": price,
        "currency": "USD",
        "redirect_url": "https://nexora-soccer-predictor.netlify.app/payment-success",
        "payment_options": "card",
        "customer": {"email": email, "name": data.get("name", "Football Fan")},
        "customizations": {"title": "Football Prediction Payment", "description": f"AI football prediction - {plan_type} plan."}
    }
    
    try:
        response = requests.post("https://api.flutterwave.com/v3/payments", json=payment_data, headers=headers)
        response_data = response.json()
        if response_data.get("status") == "success":
            return jsonify({"message": "Payment initiated!", "payment_link": response_data["data"]["link"], "access_code": access_code})
        return jsonify({"error": "Payment failed. Try again."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# 🔹 Run Flask App
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Use Render's assigned port
    print(f"🚀 Server running on port {port}")
    app.run(host='0.0.0.0', port=port)
