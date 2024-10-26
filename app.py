from flask import Flask, render_template, request, jsonify
import os
import logging
from financial_calculator import TradeCalculator
import numpy as np
import pandas as pd
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# Initialize the trade calculator
trade_calculator = TradeCalculator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/trades')
def trades():
    return render_template('trades.html')

@app.route('/summary')
def summary():
    summary_data = trade_calculator.get_summary()
    return render_template('summary.html', summary=summary_data)

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
def get_sales_history(trade_id):
    try:
        sales_history = trade_calculator.get_trade_sales_history(trade_id)
        return jsonify({'salesHistory': sales_history})
    except Exception as e:
        logger.error(f"Error retrieving sales history: {str(e)}")
        return jsonify({"error": "Failed to retrieve sales history"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
