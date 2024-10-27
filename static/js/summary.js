document.addEventListener('DOMContentLoaded', function() {
    // Format currency values with error handling
    function formatCurrency(value) {
        try {
            if (value === null || value === undefined || isNaN(value)) {
                return 'N/A';
            }
            const numValue = parseFloat(value);
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(numValue);
        } catch (error) {
            console.error('Error formatting currency:', error);
            return 'N/A';
        }
    }

    // Format number values with error handling
    function formatNumber(value, isUnits = false) {
        try {
            if (value === null || value === undefined || isNaN(value)) {
                return 'N/A';
            }
            const numValue = parseFloat(value);
            return new Intl.NumberFormat('en-US', {
                minimumFractionDigits: isUnits ? 8 : 2,
                maximumFractionDigits: isUnits ? 8 : 2
            }).format(numValue);
        } catch (error) {
            console.error('Error formatting number:', error);
            return 'N/A';
        }
    }

    // Format percentage values with error handling
    function formatPercentage(value) {
        try {
            if (value === null || value === undefined || isNaN(value)) {
                return 'N/A';
            }
            const numValue = parseFloat(value);
            return new Intl.NumberFormat('en-US', {
                style: 'percent',
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(numValue / 100);
        } catch (error) {
            console.error('Error formatting percentage:', error);
            return 'N/A';
        }
    }

    // Apply dynamic formatting to numbers with error handling
    function applyFormatting() {
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

                // Add loading indicator class if it's a Latest Price cell
                if (element.closest('td') && element.closest('td').classList.contains('latest-price')) {
                    element.classList.add('loading');
                }
            } catch (error) {
                console.error('Error formatting element:', error);
            }
        });
    }

    // Apply color classes based on values with improved error handling
    function applyColorClasses() {
        document.querySelectorAll('[data-color-value]').forEach(element => {
            try {
                const value = parseFloat(element.dataset.colorValue);
                if (!isNaN(value)) {
                    element.classList.remove('text-success', 'text-danger');
                    if (value > 0) {
                        element.classList.add('text-success');
                    } else if (value < 0) {
                        element.classList.add('text-danger');
                    }
                }
            } catch (error) {
                console.error('Error applying color class:', error);
            }
        });
    }

    // Function to refresh the summary page
    async function refreshSummary() {
        try {
            const response = await fetch('/summary');
            const text = await response.text();
            const parser = new DOMParser();
            const newDoc = parser.parseFromString(text, 'text/html');
            
            // Update the trades by market table
            const currentTable = document.querySelector('#trades-by-market-table');
            const newTable = newDoc.querySelector('#trades-by-market-table');
            if (currentTable && newTable) {
                currentTable.querySelector('tbody').innerHTML = newTable.querySelector('tbody').innerHTML;
            }
            
            // Apply formatting to the updated content
            applyFormatting();
            applyColorClasses();
            
            // Add visual feedback for the update
            const cells = document.querySelectorAll('.latest-price');
            cells.forEach(cell => {
                cell.classList.add('price-updated');
                setTimeout(() => {
                    cell.classList.remove('price-updated');
                }, 1000);
            });
        } catch (error) {
            console.error('Error refreshing summary:', error);
        }
    }

    // Initial formatting
    applyFormatting();
    applyColorClasses();

    // Set up automatic refresh every 60 seconds
    setInterval(refreshSummary, 60000);
});
