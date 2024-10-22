document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('calculator-form');
    const resultDiv = document.getElementById('result');
    const chartCanvas = document.getElementById('risk-chart');
    const calculateBtn = document.getElementById('calculateBtn');
    const spinner = calculateBtn.querySelector('.spinner-border');
    let chart = null;

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
            }
        });

        return isValid;
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
                                    <p class="h3 mb-1">${formatNumber(result.positionSize)} units</p>
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

    function formatNumber(num) {
        return new Intl.NumberFormat('en-US', {
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
