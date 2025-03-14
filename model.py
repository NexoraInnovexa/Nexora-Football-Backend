try:
    from backend.extensions import db
except ModuleNotFoundError:
    from extensions import db

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False, index=True)
    home_team = db.Column(db.String(100), nullable=False)
    away_team = db.Column(db.String(100), nullable=False)
    predicted_score = db.Column(db.String(50), nullable=False)  # AI-predicted score
    actual_score = db.Column(db.String(50), nullable=True)  # Real match result (nullable)
    match_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())  # Match time
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # Prediction time

    def __repr__(self):
        return f"<Prediction {self.home_team} vs {self.away_team}: {self.predicted_score}>"

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    plan = db.Column(db.String(50), nullable=False)  # monthly, yearly, lifetime
    access_code = db.Column(db.String(10), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=True)  # Null for lifetime plans
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Subscription {self.email}: {self.plan} (Expires: {self.expires_at})>"
