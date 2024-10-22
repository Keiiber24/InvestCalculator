document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('calculator-form');
    const resultDiv = document.getElementById('result');
    const chartCanvas = document.getElementById('risk-chart');
    const themeToggle = document.getElementById('theme-toggle');
    const calculateBtn = document.getElementById('calculateBtn');
    const spinner = calculateBtn.querySelector('.spinner-border');
    const riskPercentageInput = document.getElementById('riskPercentage');
    const entryPriceInput = document.getElementById('entryPrice');
    const exitPriceInput = document.getElementById('exitPrice');
    const capitalTotalInput = document.getElementById('capitalTotal');
    let chart = null;

    // Real-time risk amount calculation
    function updateRiskAmount() {
        const capitalTotal = parseFloat(capitalTotalInput.value) || 0;
        const riskPercentage = parseFloat(riskPercentageInput.value) || 0;
        
        if (capitalTotal <= 0 || isNaN(capitalTotal)) {
            return;
        }
        
        const riskAmount = capitalTotal * (riskPercentage / 100);
        
        const riskDisplay = document.getElementById('risk-display');
        if (riskDisplay) {
            riskDisplay.textContent = formatNumber(riskAmount);
            
            if (riskPercentage > 5) {
                riskDisplay.classList.add('text-danger');
                riskDisplay.classList.remove('text-warning');
                riskDisplay.title = 'Advertencia: Riesgo alto (>5%)';
            } else {
                riskDisplay.classList.remove('text-danger');
                riskDisplay.classList.add('text-warning');
                riskDisplay.title = '';
            }
        }
    }

    // Validate stop loss vs entry price
    function validateStopLoss() {
        const entryPrice = parseFloat(entryPriceInput.value);
        const exitPrice = parseFloat(exitPriceInput.value);
        
        if (isNaN(entryPrice) || isNaN(exitPrice)) {
            return false;
        }
        
        if (exitPrice >= entryPrice) {
            exitPriceInput.classList.add('is-invalid');
            exitPriceInput.classList.remove('is-valid');
            return false;
        } else {
            exitPriceInput.classList.remove('is-invalid');
            exitPriceInput.classList.add('is-valid');
            return true;
        }
    }

    // Form validation
    function validateForm() {
        const inputs = form.querySelectorAll('input[required], select[required]');
        let isValid = true;

        inputs.forEach(input => {
            const value = parseFloat(input.value);
            
            if (input.type === 'number') {
                if (isNaN(value) || value <= 0) {
                    isValid = false;
                    input.classList.add('is-invalid');
                    input.classList.remove('is-valid');
                } else {
                    input.classList.remove('is-invalid');
                    input.classList.add('is-valid');
                }
            } else if (!input.value) {
                isValid = false;
                input.classList.add('is-invalid');
                input.classList.remove('is-valid');
            } else {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            }

            // Specific validation for risk percentage
            if (input.id === 'riskPercentage') {
                const riskValue = parseFloat(input.value);
                if (isNaN(riskValue) || riskValue < 0 || riskValue > 100) {
                    isValid = false;
                    input.classList.add('is-invalid');
                    input.classList.remove('is-valid');
                }
                if (riskValue > 5) {
                    input.classList.add('text-danger');
                } else {
                    input.classList.remove('text-danger');
                }
            }
        });

        return isValid && validateStopLoss();
    }

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        // Show loading state
        calculateBtn.disabled = true;
        spinner.classList.remove('d-none');

        try {
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            // Validate numeric values
            for (const key in data) {
                const value = parseFloat(data[key]);
                if (!isNaN(value)) {
                    data[key] = value;
                }
            }

            const response = await fetch('/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Error en el cálculo');
            }

            displayResults(result);
            updateChart(result);
        } catch (error) {
            console.error('Error:', error);
            resultDiv.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    ${error.message || 'Ha ocurrido un error. Por favor, intente nuevamente.'}
                </div>
            `;
        } finally {
            // Hide loading state
            calculateBtn.disabled = false;
            spinner.classList.add('d-none');
        }
    });

    // Rest of the code remains the same...
    // [Previous functions: displayResults, updateChart, updateChartTheme, formatNumber, getCurrencySymbol]
});
