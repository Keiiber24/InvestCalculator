from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import logging
from financial_calculator import TradeCalculator
import numpy as np
import pandas as pd
import traceback
from flask_login import LoginManager, login_required, current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_key_only_for_development"

    # Ensure instance path exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Configure SQLAlchemy with absolute path
    db_path = os.path.join(app.instance_path, 'investment.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Import database and models
    from models import db
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(id):
        from models import User
        return User.query.get(int(id))

    # Register blueprints
    from routes.auth import auth
    app.register_blueprint(auth, url_prefix='/auth')

    # Drop and recreate all tables
    with app.app_context():
        from models import User, Trade, Sale
        db.drop_all()  # Drop all existing tables
        db.create_all()  # Create all tables

    return app

app = create_app()

@app.route('/')
@login_required
def index():
    return render_template('index.html', active_page='calculator')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
