document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('calculator-form');
    const resultDiv = document.getElementById('result');
    const chartCanvas = document.getElementById('risk-chart');
    const themeToggle = document.getElementById('theme-toggle');
    let chart = null;

    // Theme toggle
    themeToggle.addEventListener('change', function() {
        document.documentElement.classList.toggle('dark');
        updateChartTheme();
    });

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        // Input validation
        if (!validateInputs(data)) {
            return;
        }

        fetch('/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
        .then(response => response.json())
        .then(result => {
            displayResults(result);
            updateChart(result);
        })
        .catch(error => {
            console.error('Error:', error);
            resultDiv.innerHTML = '<p class="text-danger">An error occurred. Please try again.</p>';
        });
    });

    function validateInputs(data) {
        const fields = ['capitalTotal', 'riskPercentage', 'entryPrice', 'exitPrice'];
        for (const field of fields) {
            if (isNaN(parseFloat(data[field])) || parseFloat(data[field]) <= 0) {
                resultDiv.innerHTML = `<p class="text-danger">Please enter a valid positive number for ${field.replace(/([A-Z])/g, ' $1').toLowerCase()}.</p>`;
                return false;
            }
        }
        if (parseFloat(data.riskPercentage) > 100) {
            resultDiv.innerHTML = '<p class="text-danger">Risk percentage cannot be greater than 100%.</p>';
            return false;
        }
        return true;
    }

    function displayResults(result) {
        resultDiv.innerHTML = `
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h2 class="card-title mb-0">Calculation Results</h2>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <h5 class="text-primary">Capital at Risk:</h5>
                            <p class="lead">${formatNumber(result.capitalAtRisk)}</p>
                            <small class="text-muted">The amount of capital you're risking on this trade.</small>
                        </div>
                        <div class="col-md-6 mb-3">
                            <h5 class="text-primary">Risk per Unit:</h5>
                            <p class="lead">${formatNumber(result.riskPerUnit)}</p>
                            <small class="text-muted">The difference between your entry and exit prices.</small>
                        </div>
                        <div class="col-md-6 mb-3">
                            <h5 class="text-primary">Position Size:</h5>
                            <p class="lead">${formatNumber(result.positionSize)}</p>
                            <small class="text-muted">The number of units you should trade based on your risk parameters.</small>
                        </div>
                        <div class="col-md-6 mb-3">
                            <h5 class="text-primary">Total Position Value:</h5>
                            <p class="lead">${formatNumber(result.totalPositionValue)}</p>
                            <small class="text-muted">The total value of your position at the entry price.</small>
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
            type: 'pie',
            data: {
                labels: ['Capital at Risk', 'Remaining Capital'],
                datasets: [{
                    data: [result.capitalAtRisk, remainingCapital],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Capital Distribution'
                    }
                }
            }
        });

        updateChartTheme();
    }

    function updateChartTheme() {
        if (!chart) return;

        const isDark = document.documentElement.classList.contains('dark');
        chart.options.plugins.legend.labels.color = isDark ? '#fff' : '#666';
        chart.options.plugins.title.color = isDark ? '#fff' : '#666';
        chart.update();
    }

    function formatNumber(num) {
        return new Intl.NumberFormat('en-US', { style: 'decimal', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num);
    }
});
