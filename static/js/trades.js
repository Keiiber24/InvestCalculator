document.addEventListener('DOMContentLoaded', function() {
    const tradeForm = document.getElementById('trade-form');
    const tradesTableBody = document.getElementById('tradesTableBody');
    const tradeFilter = document.getElementById('tradeFilter');
    const clearFilterBtn = document.getElementById('clearFilter');
    let trades = [];
    let currentSort = { column: 'Date', direction: 'desc' };

    class NumberFormatter {
        constructor() {
            this.thousandsSeparator = '.';
            this.decimalSeparator = ',';
        }

        format(value) {
            if (value === null || value === undefined || value === '') return '';
            
            // Convert to string and clean
            const cleanValue = String(value).replace(/[^\d,]/g, '');
            const [integerPart, ...decimalParts] = cleanValue.split(',');
            const formattedInteger = this.#formatInteger(integerPart);
            const decimalPart = decimalParts.length > 0 ? decimalParts[decimalParts.length - 1] : '';

            if (String(value).endsWith(',')) {
                return `${formattedInteger},`;
            } else if (decimalPart) {
                return `${formattedInteger},${decimalPart}`;
            }
            return formattedInteger;
        }

        #formatInteger(value) {
            const trimmedValue = value.replace(/^0+/, '') || '0';
            return trimmedValue.replace(/\B(?=(\d{3})+(?!\d))/g, this.thousandsSeparator);
        }

        unformat(value) {
            if (value === null || value === undefined || value === '') return null;
            const unformatted = value.replace(/\./g, '').replace(',', '.');
            const parsed = parseFloat(unformatted);
            return isNaN(parsed) ? null : parsed;
        }
    }

    const numberFormatter = new NumberFormatter();

    // Initialize number inputs
    document.querySelectorAll('.number-input').forEach(input => {
        input.addEventListener('input', (e) => {
            const oldValue = input.value;
            const formattedValue = numberFormatter.format(input.value);
            
            if (oldValue !== formattedValue) {
                input.value = formattedValue;
            }
            validateInput(input);
        });

        input.addEventListener('keypress', (e) => {
            if (!/[\d,]/.test(e.key)) {
                e.preventDefault();
            }
        });

        // Add blur event for final validation
        input.addEventListener('blur', () => {
            validateInput(input);
        });
    });

    // Status change handler
    const statusSelect = document.getElementById('status');
    const exitPriceInput = document.getElementById('exitPrice');
    
    statusSelect.addEventListener('change', () => {
        const isClosedTrade = statusSelect.value === 'Closed';
        exitPriceInput.required = isClosedTrade;
        validateInput(exitPriceInput);
    });

    function validateInput(input) {
        // Clear previous validation state
        input.classList.remove('is-valid', 'is-invalid');
        
        // Skip validation if the field is not required and empty
        if (!input.required && !input.value.trim()) {
            return true;
        }

        let isValid = true;
        const value = input.value.trim();

        if (input.classList.contains('number-input')) {
            const numValue = numberFormatter.unformat(value);
            isValid = numValue !== null && !isNaN(numValue) && numValue >= 0;

            // Special validation for exit price when status is "Closed"
            if (input.id === 'exitPrice' && statusSelect.value === 'Closed') {
                isValid = isValid && value !== '';
            }
        } else {
            isValid = value !== '';
        }

        // Update validation classes
        input.classList.toggle('is-valid', isValid);
        input.classList.toggle('is-invalid', !isValid);
        
        return isValid;
    }

    function validateForm() {
        console.log('Validating form...');
        const inputs = tradeForm.querySelectorAll('input[required], select[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!validateInput(input)) {
                console.log(`Validation failed for ${input.id}`);
                isValid = false;
            }
        });

        // Additional validation for exit price when status is "Closed"
        if (statusSelect.value === 'Closed') {
            const exitPriceValid = validateInput(exitPriceInput);
            if (!exitPriceValid) {
                console.log('Exit price validation failed for closed trade');
                isValid = false;
            }
        }

        console.log(`Form validation result: ${isValid}`);
        return isValid;
    }

    // Form submission
    tradeForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('Form submitted, performing validation...');

        if (!validateForm()) {
            console.log('Form validation failed');
            showAlert('Please correct the errors in the form.', 'danger');
            return;
        }

        const formData = new FormData(tradeForm);
        const data = {};
        
        // Process form data
        for (let [key, value] of formData.entries()) {
            if (key === 'market' || key === 'status') {
                data[key] = value;
            } else {
                const numValue = numberFormatter.unformat(value);
                data[key] = numValue;
            }
        }

        console.log('Submitting trade data:', data);

        try {
            const response = await fetch('/add_trade', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            const result = await response.json();
            
            if (!response.ok) {
                console.error('Server returned error:', result);
                throw new Error(result.error || 'Failed to add trade');
            }

            console.log('Trade added successfully:', result);
            trades = result.trades;
            updateTradesTable();
            tradeForm.reset();
            
            // Show success message
            showAlert('Trade added successfully!', 'success');

        } catch (error) {
            console.error('Error adding trade:', error);
            showAlert(error.message || 'Failed to add trade. Please try again.', 'danger');
        }
    });

    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        tradeForm.insertAdjacentElement('beforebegin', alertDiv);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    // Table sorting and filtering implementation...
    document.querySelectorAll('.sortable').forEach(header => {
        header.addEventListener('click', () => {
            const column = header.dataset.sort;
            currentSort.direction = currentSort.column === column && currentSort.direction === 'asc' ? 'desc' : 'asc';
            currentSort.column = column;
            updateTradesTable();
        });
    });

    tradeFilter.addEventListener('input', updateTradesTable);
    clearFilterBtn.addEventListener('click', () => {
        tradeFilter.value = '';
        updateTradesTable();
    });

    function updateTradesTable() {
        const filterValue = tradeFilter.value.toLowerCase();
        let filteredTrades = trades.filter(trade => 
            Object.values(trade).some(value => 
                String(value).toLowerCase().includes(filterValue)
            )
        );

        // Sort trades
        filteredTrades.sort((a, b) => {
            let aVal = a[currentSort.column];
            let bVal = b[currentSort.column];

            // Handle null/undefined values in sorting
            if (aVal === null || aVal === undefined) return 1;
            if (bVal === null || bVal === undefined) return -1;
            if ((aVal === null || aVal === undefined) && (bVal === null || bVal === undefined)) return 0;

            // Convert to comparable values
            if (typeof aVal === 'string') aVal = aVal.toLowerCase();
            if (typeof bVal === 'string') bVal = bVal.toLowerCase();

            if (aVal < bVal) return currentSort.direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return currentSort.direction === 'asc' ? 1 : -1;
            return 0;
        });

        tradesTableBody.innerHTML = filteredTrades.map(trade => `
            <tr>
                <td>${new Date(trade.Date).toLocaleString()}</td>
                <td>${trade.Market}</td>
                <td><span class="badge ${trade.Status === 'Open' ? 'bg-warning' : 'bg-success'}">${trade.Status}</span></td>
                <td>${formatCurrency(trade['Entry Price'])}</td>
                <td>${trade['Exit Price'] !== null ? formatCurrency(trade['Exit Price']) : '-'}</td>
                <td>${formatNumber(trade.Units)}</td>
                <td>${formatCurrency(trade['Position Size'])}</td>
                <td class="${getProfitLossClass(trade['Profit/Loss'])}">${trade['Profit/Loss'] !== null ? formatCurrency(trade['Profit/Loss']) : '-'}</td>
                <td class="${getProfitLossClass(trade['Win/Loss %'])}">${trade['Win/Loss %'] !== null ? formatPercentage(trade['Win/Loss %']) : '-'}</td>
            </tr>
        `).join('');
    }

    function formatCurrency(value) {
        if (value === null || value === undefined) return '-';
        return new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'USD'
        }).format(value);
    }

    function formatNumber(value) {
        if (value === null || value === undefined) return '-';
        return new Intl.NumberFormat('es-ES').format(value);
    }

    function formatPercentage(value) {
        if (value === null || value === undefined) return '-';
        return new Intl.NumberFormat('es-ES', {
            style: 'percent',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value / 100);
    }

    function getProfitLossClass(value) {
        if (value === null || value === undefined) return '';
        return value > 0 ? 'text-success' : value < 0 ? 'text-danger' : '';
    }
});
