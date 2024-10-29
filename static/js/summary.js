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
            const value = element.textContent.trim();
            if (!value) return;

            const numValue = parseFloat(value.replace(/[^-\d.]/g, ''));
            
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
            console.error('Error formatting element:', error);
        }
    });

    // Apply color classes based on values with improved error handling
    document.querySelectorAll('[data-color-value]').forEach(element => {
        try {
            const rawValue = element.dataset.colorValue;
            
            // Skip if no value attribute or empty value
            if (!rawValue || rawValue.trim() === '') {
                return;
            }

            // Parse the value, handling potential numeric strings
            const value = parseFloat(rawValue);
            
            // Only proceed if we have a valid number
            if (!isNaN(value)) {
                // Remove any existing color classes
                element.classList.remove('text-success', 'text-danger');
                
                // Add appropriate color class
                if (value > 0) {
                    element.classList.add('text-success');
                } else if (value < 0) {
                    element.classList.add('text-danger');
                }
            }
        } catch (error) {
            console.error('Error applying color class:', error, {
                element: element,
                value: element.dataset.colorValue
            });
        }
    });

    // Refresh data periodically (every 60 seconds)
    function refreshData() {
        fetch('/summary')
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                document.querySelector('.container').innerHTML = doc.querySelector('.container').innerHTML;
                
                // Reapply formatting and color classes
                document.dispatchEvent(new Event('DOMContentLoaded'));
            })
            .catch(error => console.error('Error refreshing data:', error));
    }

    // Start periodic refresh
    setInterval(refreshData, 60000);
});
