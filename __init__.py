from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import dotenv

# 🔹 Load environment variables from .env file
dotenv.load_dotenv()

# 🔹 Initialize Database
db = SQLAlchemy()
migrate = Migrate()  # Keep migrate separate to initialize properly

# 🔹 Create Flask App Factory
def create_app():
    app = Flask(__name__)

    # 🔹 Database Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Amarachi1994@localhost/football_db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 🔹 Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)  # Now properly initialized

    # 🔹 Import and Register Routes
    from backend.routes import main
    app.register_blueprint(main)

    return app
