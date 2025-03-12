from backend.extensions import db

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    home_team = db.Column(db.String(100), nullable=False)
    away_team = db.Column(db.String(100), nullable=False)
    predicted_score = db.Column(db.String(50), nullable=False)  # AI-predicted score
    actual_score = db.Column(db.String(50), nullable=True)  # Real match result (nullable)
    match_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())  # Match time
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # Prediction time

    def __repr__(self):
        return f"<Prediction {self.home_team} vs {self.away_team}: {self.predicted_score}>"
