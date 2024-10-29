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
            console.warn('Error formatting currency:', error);
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
            console.warn('Error formatting number:', error);
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
            console.warn('Error formatting percentage:', error);
            return '0.00%';
        }
    }

    // Apply dynamic formatting to numbers with error handling
    document.querySelectorAll('[data-format]').forEach(element => {
        try {
            const format = element.dataset.format;
            let value = element.textContent.trim();
            
            // Skip empty or invalid elements
            if (!value || value === '-' || value === 'N/A') return;

            // Parse numeric value, handling currency symbols
            const numValue = parseFloat(value.replace(/[^-\d.]/g, ''));
            if (isNaN(numValue)) return;
            
            switch (format) {
                case 'currency':
                    element.textContent = formatCurrency(numValue);
                    break;
                case 'number':
                    element.textContent = formatNumber(numValue);
                    break;
                case 'percentage':
                    element.textContent = formatPercentage(numValue);
                    break;
                default:
                    console.warn('Unknown format type:', format);
            }
        } catch (error) {
            console.warn('Error formatting element:', error);
        }
    });

    // Apply color classes based on values with improved error handling
    document.querySelectorAll('[data-color-value]').forEach(element => {
        try {
            const value = element.dataset.colorValue;
            if (!value || value === '-' || value === 'N/A') return;

            const numValue = parseFloat(value);
            if (isNaN(numValue)) return;

            // Remove existing color classes first
            element.classList.remove('text-success', 'text-danger');
            
            // Add appropriate color class
            if (numValue > 0) {
                element.classList.add('text-success');
            } else if (numValue < 0) {
                element.classList.add('text-danger');
            }
        } catch (error) {
            console.warn('Error applying color class:', error, 'to element:', element);
        }
    });

    // Auto-refresh prices every 60 seconds
    setInterval(() => {
        window.location.reload();
    }, 60000);
});
