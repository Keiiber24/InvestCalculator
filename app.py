from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import logging
from financial_calculator import TradeCalculator
import numpy as np
import pandas as pd
import traceback
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models.user import db, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///investment_calculator.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Flask-Login configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize the trade calculator
trade_calculator = TradeCalculator()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))

        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html', active_page='calculator')

@app.route('/trades')
@login_required
def trades():
    return render_template('trades.html', active_page='trades')

@app.route('/summary')
@login_required
def summary():
    summary_data = trade_calculator.get_summary()
    return render_template('summary.html', active_page='summary', summary=summary_data)

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Log incoming request
        logger.info(f"Calculate request received: {data}")

        # Validate and convert numeric inputs
        try:
            capital_total = float(data.get('capitalTotal', 0))
            risk_percentage = float(data.get('riskPercentage', 0))
            entry_price = float(data.get('entryPrice', 0))
            exit_price = float(data.get('exitPrice', 0))
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid numeric input: {str(e)}")
            return jsonify({"error": "Invalid numeric values provided"}), 400

        # Validate inputs
        if any(pd.isna([capital_total, risk_percentage, entry_price, exit_price])):
            return jsonify({"error": "Invalid numerical values provided"}), 400

        if any(v <= 0 for v in [capital_total, entry_price, exit_price]):
            return jsonify({"error": "Values must be greater than zero"}), 400

        if not 0 < risk_percentage <= 100:
            return jsonify({"error": "Risk percentage must be between 0 and 100"}), 400

        # Perform calculations
        capital_at_risk = capital_total * (risk_percentage / 100)
        risk_per_unit = abs(entry_price - exit_price)
        
        if risk_per_unit == 0:
            return jsonify({"error": "Entry price cannot equal exit price"}), 400
            
        position_size = capital_at_risk / risk_per_unit
        total_position_value = position_size * entry_price

        result = {
            'capitalAtRisk': round(capital_at_risk, 2),
            'riskPerUnit': round(risk_per_unit, 2),
            'positionSize': round(position_size, 2),
            'totalPositionValue': round(total_position_value, 2)
        }

        logger.info(f"Calculation successful: {result}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/add_trade', methods=['POST'])
@login_required
def add_trade():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Log incoming request
        logger.info(f"Add trade request received: {data}")

        # Validate required fields
        required_fields = ['market', 'entryPrice', 'units']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        # Add the trade using the calculator
        try:
            trade = trade_calculator.add_trade(
                market=data['market'],
                entry_price=data['entryPrice'],
                units=data['units']
            )

            # Get trades data
            trades_data = trade_calculator.get_trades_json()
            
            logger.info(f"Trade added successfully: {trade}")
            return jsonify({
                'trades': trades_data,
                'newTrade': trade
            })

        except ValueError as e:
            logger.error(f"Trade validation error: {str(e)}")
            return jsonify({"error": str(e)}), 400

    except Exception as e:
        logger.error(f"Unexpected error in add_trade: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "An unexpected error occurred while processing the trade"}), 500

@app.route('/sell_units/<int:trade_id>', methods=['POST'])
@login_required
def sell_units(trade_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Log incoming request
        logger.info(f"Sell units request received for trade {trade_id}: {data}")

        required_fields = ['units', 'exitPrice']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        # Process the sale
        try:
            result = trade_calculator.sell_units(
                trade_id=trade_id,
                units_to_sell=data['units'],
                exit_price=data['exitPrice']
            )

            # Get updated trades data and sales history
            trades_data = trade_calculator.get_trades_json()
            sales_history = trade_calculator.get_trade_sales_history(trade_id)
            
            logger.info(f"Units sold successfully: {result}")
            return jsonify({
                'trades': trades_data,
                'salesHistory': sales_history,
                'sale': result['sale'],
                'updatedTrade': result['updated_trade']
            })

        except ValueError as e:
            logger.error(f"Sale validation error: {str(e)}")
            return jsonify({"error": str(e)}), 400

    except Exception as e:
        logger.error(f"Unexpected error in sell_units: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "An unexpected error occurred while processing the sale"}), 500

@app.route('/get_sales_history/<int:trade_id>')
@login_required
def get_sales_history(trade_id):
    try:
        sales_history = trade_calculator.get_trade_sales_history(trade_id)
        return jsonify({'salesHistory': sales_history})
    except Exception as e:
        logger.error(f"Error retrieving sales history: {str(e)}")
        return jsonify({"error": "Failed to retrieve sales history"}), 500

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
