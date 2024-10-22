from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

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

        # Validate inputs
        if capital_total <= 0:
            return jsonify({'error': 'El capital total debe ser mayor que cero'}), 400
        if risk_percentage <= 0 or risk_percentage > 100:
            return jsonify({'error': 'El porcentaje de riesgo debe estar entre 0 y 100'}), 400
        if entry_price <= 0:
            return jsonify({'error': 'El precio de entrada debe ser mayor que cero'}), 400
        if exit_price <= 0:
            return jsonify({'error': 'El precio de stop loss debe ser mayor que cero'}), 400
        if exit_price >= entry_price:
            return jsonify({'error': 'El precio de stop loss debe ser menor que el precio de entrada'}), 400

        capital_at_risk = capital_total * (risk_percentage / 100)
        risk_per_unit = abs(entry_price - exit_price)
        
        # Check for division by zero
        if risk_per_unit == 0:
            return jsonify({'error': 'La diferencia entre el precio de entrada y stop loss no puede ser cero'}), 400

        position_size = capital_at_risk / risk_per_unit
        total_position_value = position_size * entry_price

        return jsonify({
            'capitalAtRisk': round(capital_at_risk, 2),
            'riskPerUnit': round(risk_per_unit, 2),
            'positionSize': round(position_size, 2),
            'totalPositionValue': round(total_position_value, 2)
        })
    except ValueError as e:
        return jsonify({'error': 'Por favor, ingrese valores numéricos válidos'}), 400
    except Exception as e:
        return jsonify({'error': 'Ha ocurrido un error en el cálculo'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
