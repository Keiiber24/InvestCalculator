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
    return render_template('index.html', active_page='calculator')

@app.route('/trades')
def trades():
    return render_template('trades.html', active_page='trades')

@app.route('/summary')
def summary():
    try:
        summary_data = trade_calculator.get_summary()
        if summary_data is None:
            logger.error("Failed to generate summary data")
            return render_template('error.html', error="Failed to generate summary data"), 500

        # Format numerical values for display
        for key in ['total_profit_loss', 'total_invested', 'current_positions_value', 'avg_position_size', 'largest_position']:
            if key in summary_data:
                summary_data[key] = round(float(summary_data[key]), 2)

        # Ensure win_rate is properly formatted
        if 'win_rate' in summary_data:
            summary_data['win_rate'] = round(float(summary_data['win_rate']), 1)

        return render_template('summary.html', active_page='summary', summary=summary_data)
    except Exception as e:
        logger.error(f"Error in summary route: {str(e)}\n{traceback.format_exc()}")
        return render_template('error.html', error="An unexpected error occurred"), 500

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
            # If no data is provided, return current trades list
            trades_data = trade_calculator.get_trades_json()
            return jsonify({'trades': trades_data})

        # Log incoming request
        logger.info(f"Add trade request received: {data}")

        # Validate required fields
        required_fields = ['market', 'entryPrice', 'units']
        if not all(field in data for field in required_fields):
            missing = [field for field in required_fields if field not in data]
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

        try:
            # Add the trade
            trade = trade_calculator.add_trade(
                market=str(data['market']).strip(),
                entry_price=float(data['entryPrice']),
                units=float(data['units'])
            )
            
            if trade is None:
                return jsonify({"error": "Failed to add trade"}), 500

            trades_data = trade_calculator.get_trades_json()
            return jsonify({
                'trades': trades_data,
                'newTrade': trade
            })

        except ValueError as e:
            logger.error(f"Trade validation error: {str(e)}")
            return jsonify({"error": str(e)}), 400

    except Exception as e:
        logger.error(f"Unexpected error in add_trade: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/sell_units/<int:trade_id>', methods=['POST'])
def sell_units(trade_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Log incoming request
        logger.info(f"Sell units request received for trade {trade_id}: {data}")

        required_fields = ['units', 'exitPrice']
        if not all(field in data for field in required_fields):
            missing = [field for field in required_fields if field not in data]
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

        try:
            result = trade_calculator.sell_units(
                trade_id=trade_id,
                units_to_sell=float(data['units']),
                exit_price=float(data['exitPrice'])
            )

            if result is None:
                return jsonify({"error": "Failed to process sale"}), 500

            trades_data = trade_calculator.get_trades_json()
            sales_history = trade_calculator.get_trade_sales_history(trade_id)
            
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
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/get_sales_history/<int:trade_id>')
def get_sales_history(trade_id):
    try:
        sales_history = trade_calculator.get_trade_sales_history(trade_id)
        return jsonify({'salesHistory': sales_history})
    except Exception as e:
        logger.error(f"Error retrieving sales history: {str(e)}")
        return jsonify({"error": "Failed to retrieve sales history"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
