from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import dotenv
import logging
try:
    from backend.extensions import db
    
except ModuleNotFoundError:
    from extensions import db
    
# 🔹 Load environment variables from .env file
dotenv.load_dotenv()

# 🔹 Set up logging for better debugging
logging.basicConfig(level=logging.DEBUG)

# 🔹 Create Flask App Factory
def create_app():
    app = Flask(__name__)

    # 🔹 Database Configuration
    # Fetch the database URL from the environment variable or use the default
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://football_db_45ja_user:FcSz0jnwqUujnD1o1ZmWBaMEMP22RuiO@dpg-cv88815ds78s73e900hg-a/football_db_45ja'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 🔹 Initialize Extensions
    db.init_app(app)
    Migrate(app, db)  # Initialize Flask-Migrate with app and db

    # 🔹 Import and Register Routes (use relative import)
    from routes import main
    app.register_blueprint(main)

    return app
