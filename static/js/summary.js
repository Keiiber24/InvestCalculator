document.addEventListener('DOMContentLoaded', function() {
    // Format currency values with error handling
    function formatCurrency(value) {
        try {
            const numValue = parseFloat(value);
            if (isNaN(numValue)) return '$0.00';
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(numValue);
        } catch (error) {
            console.error('Error formatting currency:', error);
            return '$0.00';
        }
    }

    // Format number values with error handling
    function formatNumber(value, isUnits = false) {
        try {
            const numValue = parseFloat(value);
            if (isNaN(numValue)) return isUnits ? '0.00000000' : '0.00';
            return new Intl.NumberFormat('en-US', {
                minimumFractionDigits: isUnits ? 8 : 2,
                maximumFractionDigits: isUnits ? 8 : 2
            }).format(numValue);
        } catch (error) {
            console.error('Error formatting number:', error);
            return isUnits ? '0.00000000' : '0.00';
        }
    }

    // Format percentage values with error handling
    function formatPercentage(value) {
        try {
            const numValue = parseFloat(value);
            if (isNaN(numValue)) return '0.00%';
            return new Intl.NumberFormat('en-US', {
                style: 'percent',
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(numValue / 100);
        } catch (error) {
            console.error('Error formatting percentage:', error);
            return '0.00%';
        }
    }

    // Apply dynamic formatting to numbers with error handling
    document.querySelectorAll('[data-format]').forEach(element => {
        try {
            const format = element.dataset.format;
            const value = parseFloat(element.textContent);
            
            switch (format) {
                case 'currency':
                    element.textContent = formatCurrency(value);
                    break;
                case 'number':
                    element.textContent = formatNumber(value);
                    break;
                case 'percentage':
                    element.textContent = formatPercentage(value);
                    break;
                default:
                    console.warn('Unknown format type:', format);
            }
        } catch (error) {
            console.error('Error formatting element:', error);
        }
    });

    // Apply color classes based on values
    document.querySelectorAll('[data-color-value]').forEach(element => {
        try {
            const value = parseFloat(element.dataset.colorValue);
            if (!isNaN(value)) {
                element.classList.add(value > 0 ? 'text-success' : value < 0 ? 'text-danger' : '');
            }
        } catch (error) {
            console.error('Error applying color class:', error);
        }
    });
});
