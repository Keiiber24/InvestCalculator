document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('calculator-form');
    const resultDiv = document.getElementById('result');
    const chartCanvas = document.getElementById('risk-chart');
    const calculateBtn = document.getElementById('calculateBtn');
    const spinner = calculateBtn.querySelector('.spinner-border');
    let chart = null;

    // Set appropriate step values and validation for decimal inputs
    const decimalInputs = {
        'capitalTotal': { step: '0.01', min: '0.01' },
        'riskPercentage': { step: '0.1', min: '0.1', max: '100' },
        'entryPrice': { step: '0.0001', min: '0.0001' },
        'exitPrice': { step: '0.0001', min: '0.0001' }
    };

    // Configure decimal inputs
    Object.entries(decimalInputs).forEach(([id, config]) => {
        const input = document.getElementById(id);
        if (input) {
            Object.entries(config).forEach(([attr, value]) => {
                input.setAttribute(attr, value);
            });
        }
    });

    // Form validation with decimal precision
    function validateForm() {
        const inputs = form.querySelectorAll('input[required], select[required]');
        let isValid = true;

        inputs.forEach(input => {
            const value = parseFloat(input.value);
            const config = decimalInputs[input.id];

            if (!input.value || isNaN(value)) {
                isValid = false;
                input.classList.add('is-invalid');
                return;
            }

            if (config) {
                const min = parseFloat(config.min);
                const max = config.max ? parseFloat(config.max) : Infinity;
                const step = parseFloat(config.step);

                // Check if value respects step
                const remainder = (value - min) % step;
                const isStepValid = Math.abs(remainder) < Number.EPSILON || 
                                  Math.abs(remainder - step) < Number.EPSILON;

                if (value < min || value > max || !isStepValid) {
                    isValid = false;
                    input.classList.add('is-invalid');
                    return;
                }
            }

            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        });

        return isValid;
    }

    // Real-time validation with decimal handling
    form.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            const config = decimalInputs[input.id];

            if (!e.target.value || isNaN(value)) {
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
                return;
            }

            if (config) {
                const min = parseFloat(config.min);
                const max = config.max ? parseFloat(config.max) : Infinity;
                if (value < min || value > max) {
                    input.classList.remove('is-valid');
                    input.classList.add('is-invalid');
                    return;
                }
            }

            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        });

        // Handle paste events
        input.addEventListener('paste', (e) => {
            setTimeout(() => {
                const value = input.value.replace(/[^\d.-]/g, '');
                input.value = value;
                input.dispatchEvent(new Event('input'));
            }, 0);
        });
    });

    // Increment/Decrement buttons with decimal precision
    document.querySelectorAll('[data-action]').forEach(button => {
        button.addEventListener('click', () => {
            const input = button.parentElement.querySelector('input');
            const config = decimalInputs[input.id];
            if (!config) return;

            const step = parseFloat(config.step);
            const min = parseFloat(config.min);
            const max = config.max ? parseFloat(config.max) : Infinity;
            let value = parseFloat(input.value) || 0;

            if (button.dataset.action === 'increment') {
                value = Math.min(value + step, max);
            } else {
                value = Math.max(value - step, min);
            }

            // Format to maintain proper decimal places
            const decimals = config.step.split('.')[1]?.length || 0;
            input.value = value.toFixed(decimals);
            input.dispatchEvent(new Event('input'));
        });
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

        // Ensure numeric values are properly formatted
        Object.keys(decimalInputs).forEach(key => {
            if (data[key]) {
                data[key] = parseFloat(data[key]);
            }
        });

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
                    An error occurred. Please try again.
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
                    <h2 class="card-title h4 mb-0 text-warning">Investment Results</h2>
                </div>
                <div class="card-body">
                    <div class="row g-4">
                        <div class="col-md-6">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-currency-exchange fs-4 text-warning me-2"></i>
                                <div>
                                    <h5 class="text-gradient mb-1">Capital at Risk</h5>
                                    <p class="h3 mb-1">${currencySymbol}${formatNumber(result.capitalAtRisk)}</p>
                                    <small class="text-muted">Amount you're risking on this investment</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-graph-up fs-4 text-warning me-2"></i>
                                <div>
                                    <h5 class="text-gradient mb-1">Risk per Unit</h5>
                                    <p class="h3 mb-1">${currencySymbol}${formatNumber(result.riskPerUnit)}</p>
                                    <small class="text-muted">Price difference between purchase and stop loss</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-rulers fs-4 text-warning me-2"></i>
                                <div>
                                    <h5 class="text-gradient mb-1">Position Size</h5>
                                    <p class="h3 mb-1">${formatNumber(result.positionSize, 4)} units</p>
                                    <small class="text-muted">Number of units to invest</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-cash-stack fs-4 text-warning me-2"></i>
                                <div>
                                    <h5 class="text-gradient mb-1">Total Investment Value</h5>
                                    <p class="h3 mb-1">${currencySymbol}${formatNumber(result.totalPositionValue)}</p>
                                    <small class="text-muted">Total value at purchase price</small>
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
                labels: ['Capital at Risk', 'Available Capital'],
                datasets: [{
                    data: [result.capitalAtRisk, remainingCapital],
                    backgroundColor: [
                        'rgba(241, 196, 15, 0.8)',  // Warning color (gold)
                        'rgba(52, 152, 219, 0.8)'   // Info color (blue)
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
                            color: 'var(--bs-text-light)'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Investment Capital Distribution',
                        color: 'var(--bs-text-light)'
                    }
                }
            }
        });
    }

    function formatNumber(num, decimals = 2) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
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
