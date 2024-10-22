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
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Convert string inputs to Decimal with proper validation
        try:
            capital_total = Decimal(str(data.get('capitalTotal', '0')))
            risk_percentage = Decimal(str(data.get('riskPercentage', '0')))
            entry_price = Decimal(str(data.get('entryPrice', '0')))
            exit_price = Decimal(str(data.get('exitPrice', '0')))
        except (InvalidOperation, TypeError) as e:
            return jsonify({
                'error': 'Invalid number format. Please check your inputs.'
            }), 400

        # Validate minimum values
        if capital_total < Decimal('0.01'):
            return jsonify({'error': 'Investment capital must be at least 0.01'}), 400
        if not Decimal('0.1') <= risk_percentage <= Decimal('100'):
            return jsonify({'error': 'Risk percentage must be between 0.1 and 100'}), 400
        if entry_price < Decimal('0.0001') or exit_price < Decimal('0.0001'):
            return jsonify({'error': 'Prices must be at least 0.0001'}), 400

        # Perform calculations with increased decimal precision
        capital_at_risk = (capital_total * risk_percentage / Decimal('100')).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        risk_per_unit = abs(entry_price - exit_price).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        
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
        
    except Exception as e:
        app.logger.error(f'Calculation error: {str(e)}')
        return jsonify({
            'error': 'An unexpected error occurred. Please try again.'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
