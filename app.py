from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    capital_total = float(data['capitalTotal'])
    risk_percentage = float(data['riskPercentage'])
    entry_price = float(data['entryPrice'])
    exit_price = float(data['exitPrice'])

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
