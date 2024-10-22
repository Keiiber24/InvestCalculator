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
            resultDiv.innerHTML = '<p class="text-red-500">An error occurred. Please try again.</p>';
        });
    });

    function validateInputs(data) {
        const fields = ['capitalTotal', 'riskPercentage', 'entryPrice', 'exitPrice'];
        for (const field of fields) {
            if (isNaN(parseFloat(data[field])) || parseFloat(data[field]) <= 0) {
                resultDiv.innerHTML = `<p class="text-red-500">Please enter a valid positive number for ${field.replace(/([A-Z])/g, ' $1').toLowerCase()}.</p>`;
                return false;
            }
        }
        if (parseFloat(data.riskPercentage) > 100) {
            resultDiv.innerHTML = '<p class="text-red-500">Risk percentage cannot be greater than 100%.</p>';
            return false;
        }
        return true;
    }

    function displayResults(result) {
        resultDiv.innerHTML = `
            <h2 class="text-xl font-bold mb-4">Calculation Results</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <p><strong>Capital at Risk:</strong> ${formatNumber(result.capitalAtRisk)}</p>
                    <p class="text-sm text-gray-600 dark:text-gray-400">The amount of capital you're risking on this trade.</p>
                </div>
                <div>
                    <p><strong>Risk per Unit:</strong> ${formatNumber(result.riskPerUnit)}</p>
                    <p class="text-sm text-gray-600 dark:text-gray-400">The difference between your entry and exit prices.</p>
                </div>
                <div>
                    <p><strong>Position Size:</strong> ${formatNumber(result.positionSize)}</p>
                    <p class="text-sm text-gray-600 dark:text-gray-400">The number of units you should trade based on your risk parameters.</p>
                </div>
                <div>
                    <p><strong>Total Position Value:</strong> ${formatNumber(result.totalPositionValue)}</p>
                    <p class="text-sm text-gray-600 dark:text-gray-400">The total value of your position at the entry price.</p>
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
