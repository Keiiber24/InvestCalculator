document.addEventListener('DOMContentLoaded', function() {
    // Format currency values
    function formatCurrency(value) {
        if (value === null || value === undefined) return '-';
        return new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    }

    // Format number values
    function formatNumber(value, isUnits = false) {
        if (value === null || value === undefined) return '-';
        return new Intl.NumberFormat('es-ES', {
            minimumFractionDigits: isUnits ? 8 : 2,
            maximumFractionDigits: isUnits ? 8 : 2
        }).format(value);
    }

    // Format percentage values
    function formatPercentage(value) {
        if (value === null || value === undefined) return '-';
        return new Intl.NumberFormat('es-ES', {
            style: 'percent',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value / 100);
    }

    // Get profit/loss CSS class
    function getProfitLossClass(value) {
        if (value === null || value === undefined) return '';
        return value > 0 ? 'text-success' : value < 0 ? 'text-danger' : '';
    }
});
