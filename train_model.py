import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from fetch_data import fetch_live_matches

# ✅ Fetch live football data
df = fetch_live_matches()

if df is not None and not df.empty:
    # ✅ Convert team names into numeric values
    label_encoder = LabelEncoder()
    df["home_team"] = label_encoder.fit_transform(df["home_team"])
    df["away_team"] = label_encoder.fit_transform(df["away_team"])

    # ✅ Features and Target
    X = df.drop(columns=["winner"])  # Features
    y = df["winner"]  # Target (1 = Home Win, 0 = Away Win, 2 = Draw)

    # ✅ Load existing model if available
    try:
        model = joblib.load("football_model.pkl")
        print("✅ Existing model loaded. Retraining...")
    except FileNotFoundError:
        print("⚠️ No existing model found. Training a new one...")
        model = RandomForestClassifier()

    # ✅ Train or retrain the model
    model.fit(X, y)

    # ✅ Save the updated model
    joblib.dump(model, "football_model.pkl")
    print("✅ Model retrained and saved.")
else:
    print("⚠️ No new match data available.")
