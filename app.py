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

    # Configure SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///investment.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Import database and models
    from models.database import db
    from models import User, Trade

    # Initialize extensions
    db.init_app(app)
    
    # Initialize Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    # Register blueprints
    from routes.auth import auth
    app.register_blueprint(auth, url_prefix='/auth')

    # Create all tables
    with app.app_context():
        db.create_all()

    return app

app = create_app()

# Initialize trade calculator (will be set per user)
trade_calculator = None

@app.before_request
def init_trade_calculator():
    global trade_calculator
    if current_user.is_authenticated:
        trade_calculator = TradeCalculator(user_id=current_user.id)

@app.route('/')
@login_required
def index():
    return render_template('index.html', active_page='calculator')

@app.route('/trades')
@login_required
def trades():
    return render_template('trades.html', active_page='trades')

@app.route('/summary')
@login_required
def summary():
    if not trade_calculator:
        return redirect(url_for('auth.login'))
    summary_data = trade_calculator.get_summary()
    return render_template('summary.html', active_page='summary', summary=summary_data)

@app.route('/calculate', methods=['POST'])
@login_required
def calculate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        logger.info(f"Calculate request received: {data}")

        try:
            capital_total = float(data.get('capitalTotal', 0))
            risk_percentage = float(data.get('riskPercentage', 0))
            entry_price = float(data.get('entryPrice', 0))
            exit_price = float(data.get('exitPrice', 0))
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid numeric input: {str(e)}")
            return jsonify({"error": "Invalid numeric values provided"}), 400

        if any(pd.isna([capital_total, risk_percentage, entry_price, exit_price])):
            return jsonify({"error": "Invalid numerical values provided"}), 400

        if any(v <= 0 for v in [capital_total, entry_price, exit_price]):
            return jsonify({"error": "Values must be greater than zero"}), 400

        if not 0 < risk_percentage <= 100:
            return jsonify({"error": "Risk percentage must be between 0 and 100"}), 400

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

        logger.info(f"Add trade request received: {data}")

        required_fields = ['market', 'entryPrice', 'units']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        try:
            trade = trade_calculator.add_trade(
                market=data['market'],
                entry_price=data['entryPrice'],
                units=data['units']
            )

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

        logger.info(f"Sell units request received for trade {trade_id}: {data}")

        required_fields = ['units', 'exitPrice']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        try:
            result = trade_calculator.sell_units(
                trade_id=trade_id,
                units_to_sell=data['units'],
                exit_price=data['exitPrice']
            )

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

@app.route('/get_latest_prices', methods=['POST'])
@login_required
def get_latest_prices():
    try:
        data = request.get_json()
        if not data or 'markets' not in data:
            return jsonify({"error": "No markets provided"}), 400

        markets = data['markets']
        if not isinstance(markets, list):
            return jsonify({"error": "Markets must be provided as a list"}), 400

        latest_prices = trade_calculator.fetch_latest_prices(markets)
        return jsonify({'prices': latest_prices})

    except Exception as e:
        logger.error(f"Error fetching latest prices: {str(e)}")
        return jsonify({"error": "Failed to fetch latest prices"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
