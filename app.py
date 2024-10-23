from flask import Flask, render_template, request, jsonify
import os
import locale

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# Set locale for number formatting
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        capital_total = float(data['capitalTotal'])
        risk_percentage = float(data['riskPercentage'])
        entry_price = float(data['entryPrice'])
        exit_price = float(data['exitPrice'])

        # Perform calculations with proper decimal handling
        capital_at_risk = round(capital_total * (risk_percentage / 100), 2)
        risk_per_unit = round(abs(entry_price - exit_price), 2)
        position_size = round(capital_at_risk / risk_per_unit, 2)
        total_position_value = round(position_size * entry_price, 2)

        return jsonify({
            'capitalAtRisk': capital_at_risk,
            'riskPerUnit': risk_per_unit,
            'positionSize': position_size,
            'totalPositionValue': total_position_value
        })
    except (ValueError, TypeError, ZeroDivisionError) as e:
        return jsonify({'error': 'Invalid input values'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
