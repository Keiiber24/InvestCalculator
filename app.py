from flask import Flask, render_template, request, jsonify
import os
import logging
from financial_calculator import TradeCalculator
import numpy as np
import pandas as pd
import traceback
from flask_login import LoginManager, current_user, login_required
from models.database import db
from models.user import User
from routes.auth import auth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///investment.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

# Register blueprints
app.register_blueprint(auth, url_prefix='/auth')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# Dictionary to store user-specific calculators
user_calculators = {}

def get_calculator():
    """Get or create a calculator instance for the current user"""
    if not current_user.is_authenticated:
        raise ValueError("Authentication required")
    
    user_id = current_user.id
    if user_id not in user_calculators:
        user_calculators[user_id] = TradeCalculator(user_id)
    return user_calculators[user_id]

@app.route('/')
@login_required
def index():
    return render_template('index.html', active_page='calculator')

# ... rest of the routes remain the same ...
