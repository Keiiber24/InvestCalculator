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
        const riskAmount = capitalTotal * (riskPercentage / 100);
        
        const riskDisplay = document.getElementById('risk-display');
        if (riskDisplay) {
            riskDisplay.textContent = formatNumber(riskAmount);
            
            // Add warning for high risk
            if (riskPercentage > 5) {
                riskDisplay.classList.add('text-danger');
                riskDisplay.classList.remove('text-warning');
            } else {
                riskDisplay.classList.remove('text-danger');
                riskDisplay.classList.add('text-warning');
            }
        }
    }

    // Validate stop loss vs entry price
    function validateStopLoss() {
        const entryPrice = parseFloat(entryPriceInput.value) || 0;
        const exitPrice = parseFloat(exitPriceInput.value) || 0;
        
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
            if (!input.value) {
                isValid = false;
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            }

            // Specific validation for risk percentage
            if (input.id === 'riskPercentage') {
                const value = parseFloat(input.value);
                if (value < 0 || value > 100) {
                    isValid = false;
                    input.classList.add('is-invalid');
                }
                if (value > 5) {
                    input.classList.add('text-danger');
                } else {
                    input.classList.remove('text-danger');
                }
            }
        });

        return isValid && validateStopLoss();
    }

    // Real-time validation
    form.querySelectorAll('input, select').forEach(input => {
        input.addEventListener('input', () => {
            if (input.value) {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            } else {
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
            }
            
            if (input.id === 'riskPercentage' || input.id === 'capitalTotal') {
                updateRiskAmount();
            }
            
            if (input.id === 'entryPrice' || input.id === 'exitPrice') {
                validateStopLoss();
            }
        });
    });

    // Increment/Decrement buttons
    document.querySelectorAll('[data-action]').forEach(button => {
        button.addEventListener('click', () => {
            const input = button.parentElement.querySelector('input');
            const step = parseFloat(input.step) || 1;
            const min = parseFloat(input.min);
            const max = parseFloat(input.max);
            let value = parseFloat(input.value) || 0;

            if (button.dataset.action === 'increment') {
                value = Math.min(value + step, max || Infinity);
            } else {
                value = Math.max(value - step, min || -Infinity);
            }

            input.value = value;
            input.dispatchEvent(new Event('input'));
        });
    });

    // Theme toggle
    themeToggle.addEventListener('change', function() {
        document.documentElement.classList.toggle('dark');
        updateChartTheme();
    });

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        // Show loading state
        calculateBtn.disabled = true;
        spinner.classList.remove('d-none');

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch('/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                throw new Error('Calculation failed');
            }

            const result = await response.json();
            displayResults(result);
            updateChart(result);
        } catch (error) {
            console.error('Error:', error);
            resultDiv.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    Ha ocurrido un error. Por favor, intente nuevamente.
                </div>
            `;
        } finally {
            // Hide loading state
            calculateBtn.disabled = false;
            spinner.classList.add('d-none');
        }
    });

    function displayResults(result) {
        const currencySymbol = getCurrencySymbol(form.baseCurrency.value);
        resultDiv.innerHTML = `
            <div class="card shadow-lg border-0">
                <div class="card-header bg-primary">
                    <h2 class="card-title h4 mb-0 text-warning">Resultados del Cálculo</h2>
                </div>
                <div class="card-body">
                    <div class="row g-4">
                        <div class="col-md-6">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-currency-exchange fs-4 text-warning me-2"></i>
                                <div>
                                    <h5 class="text-gradient mb-1">Capital de Riesgo</h5>
                                    <p class="h3 mb-1">${currencySymbol}${formatNumber(result.capitalAtRisk)}</p>
                                    <small class="text-muted">Capital de Riesgo = ${formatNumber(parseFloat(form.capitalTotal.value))} × ${parseFloat(form.riskPercentage.value)}%</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-graph-up fs-4 text-warning me-2"></i>
                                <div>
                                    <h5 class="text-gradient mb-1">Monto a Arriesgar por Unidad</h5>
                                    <p class="h3 mb-1">${currencySymbol}${formatNumber(result.riskPerUnit)}</p>
                                    <small class="text-muted">Precio de Entrada - Stop Loss = ${formatNumber(parseFloat(form.entryPrice.value))} - ${formatNumber(parseFloat(form.exitPrice.value))}</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-rulers fs-4 text-warning me-2"></i>
                                <div>
                                    <h5 class="text-gradient mb-1">Total Unidades</h5>
                                    <p class="h3 mb-1">${formatNumber(result.positionSize)} unidades</p>
                                    <small class="text-muted">Capital de Riesgo ÷ Monto a Arriesgar por Unidad</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-cash-stack fs-4 text-warning me-2"></i>
                                <div>
                                    <h5 class="text-gradient mb-1">Valor Total de la Posición</h5>
                                    <p class="h3 mb-1">${currencySymbol}${formatNumber(result.totalPositionValue)}</p>
                                    <small class="text-muted">Total Unidades × Precio de Entrada</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    function updateChart(result) {
        const ctx = chartCanvas.getContext('2d');
        const remainingCapital = parseFloat(form.capitalTotal.value) - result.capitalAtRisk;

        if (chart) {
            chart.destroy();
        }

        chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Capital en Riesgo', 'Capital Restante'],
                datasets: [{
                    data: [result.capitalAtRisk, remainingCapital],
                    backgroundColor: [
                        'rgba(241, 196, 15, 0.8)',
                        'rgba(52, 152, 219, 0.8)'
                    ],
                    borderColor: [
                        'rgba(241, 196, 15, 1)',
                        'rgba(52, 152, 219, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: getComputedStyle(document.documentElement)
                                .getPropertyValue('--bs-text-light')
                        }
                    },
                    title: {
                        display: true,
                        text: 'Distribución del Capital',
                        color: getComputedStyle(document.documentElement)
                            .getPropertyValue('--bs-text-light')
                    }
                }
            }
        });
    }

    function updateChartTheme() {
        if (!chart) return;

        const textColor = getComputedStyle(document.documentElement)
            .getPropertyValue('--bs-text-light');

        chart.options.plugins.legend.labels.color = textColor;
        chart.options.plugins.title.color = textColor;
        chart.update();
    }

    function formatNumber(num) {
        return new Intl.NumberFormat('es-ES', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(num);
    }

    function getCurrencySymbol(currency) {
        const symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥',
            'AUD': 'A$'
        };
        return symbols[currency] || currency;
    }
});
