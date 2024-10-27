import { formatCurrency, formatNumber, formatPercentage, getProfitLossClass } from './utils.js';

document.addEventListener('DOMContentLoaded', function() {
    // Format currency values
    document.querySelectorAll('[data-currency]').forEach(element => {
        const value = parseFloat(element.dataset.currency);
        if (!isNaN(value)) {
            element.textContent = formatCurrency(value);
            element.classList.add(getProfitLossClass(value));
        }
    });

    // Format percentage values
    document.querySelectorAll('[data-percentage]').forEach(element => {
        const value = parseFloat(element.dataset.percentage);
        if (!isNaN(value)) {
            element.textContent = formatPercentage(value);
            element.classList.add(getProfitLossClass(value));
        }
    });

    // Format numbers with specific decimal places
    document.querySelectorAll('[data-number]').forEach(element => {
        const value = parseFloat(element.dataset.number);
        if (!isNaN(value)) {
            const decimals = parseInt(element.dataset.decimals || '2');
            element.textContent = formatNumber(value, decimals);
        }
    });

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add refresh button functionality
    const refreshBtn = document.getElementById('refreshSummary');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            window.location.reload();
        });
    }
});
