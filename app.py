from flask import Flask, render_template, request, jsonify
import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        
        # Convert string inputs to Decimal for precise calculation
        capital_total = Decimal(str(data['capitalTotal']))
        risk_percentage = Decimal(str(data['riskPercentage']))
        entry_price = Decimal(str(data['entryPrice']))
        exit_price = Decimal(str(data['exitPrice']))
        
        # Validate inputs
        if any(x <= 0 for x in [capital_total, entry_price, exit_price]) or not (0 < risk_percentage <= 100):
            return jsonify({
                'error': 'Invalid input values. Please check your inputs.'
            }), 400

        # Perform calculations with Decimal precision
        capital_at_risk = (capital_total * risk_percentage / Decimal('100')).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        risk_per_unit = abs(entry_price - exit_price).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        
        # Avoid division by zero
        if risk_per_unit == 0:
            return jsonify({
                'error': 'Entry and exit prices cannot be equal.'
            }), 400
            
        position_size = (capital_at_risk / risk_per_unit).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        total_position_value = (position_size * entry_price).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

        return jsonify({
            'capitalAtRisk': str(capital_at_risk),
            'riskPerUnit': str(risk_per_unit),
            'positionSize': str(position_size),
            'totalPositionValue': str(total_position_value)
        })
        
    except (InvalidOperation, TypeError, ValueError) as e:
        return jsonify({
            'error': 'Invalid number format. Please check your inputs.'
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'An unexpected error occurred.'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
