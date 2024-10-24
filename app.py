from flask import Flask, render_template, request, jsonify
import os
from financial_calculator import TradeCalculator
import numpy as np

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# Initialize the trade calculator
trade_calculator = TradeCalculator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/trades')
def trades():
    return render_template('trades.html', trades=trade_calculator.trades)

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        capital_total = float(data['capitalTotal'])
        risk_percentage = float(data['riskPercentage'])
        entry_price = float(data['entryPrice'])
        exit_price = float(data['exitPrice'])

        # Validate inputs
        if any(np.isnan([capital_total, risk_percentage, entry_price, exit_price])):
            return jsonify({"error": "Invalid numerical values provided"}), 400

        capital_at_risk = capital_total * (risk_percentage / 100)
        risk_per_unit = abs(entry_price - exit_price)
        position_size = capital_at_risk / risk_per_unit
        total_position_value = position_size * entry_price

        return jsonify({
            'capitalAtRisk': round(capital_at_risk, 2),
            'riskPerUnit': round(risk_per_unit, 2),
            'positionSize': round(position_size, 2),
            'totalPositionValue': round(total_position_value, 2)
        })
    except KeyError as e:
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400
    except ValueError as e:
        return jsonify({"error": f"Invalid value: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/add_trade', methods=['POST'])
def add_trade():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate required fields
        required_fields = ['market', 'entryPrice', 'units', 'status']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        # Add the trade using the calculator
        trade = trade_calculator.add_trade(
            market=data['market'],
            entry_price=data['entryPrice'],
            units=data['units'],
            exit_price=data.get('exitPrice'),
            status=data['status']
        )

        # Return the trades data with the new trade
        return jsonify({
            'trades': trade_calculator.trades.replace({np.nan: None}).to_dict('records'),
            'newTrade': trade
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
