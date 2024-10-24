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
    });

    function validateInput(input) {
        const value = numberFormatter.unformat(input.value);
        const isValid = value !== null && !isNaN(value) && value >= 0;
        
        if (input.value.trim()) {
            input.classList.toggle('is-valid', isValid);
            input.classList.toggle('is-invalid', !isValid);
        } else {
            input.classList.remove('is-valid', 'is-invalid');
        }
        
        return isValid;
    }

    // Form validation
    function validateForm() {
        const inputs = tradeForm.querySelectorAll('input[required], select[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (input.classList.contains('number-input')) {
                if (!validateInput(input)) {
                    isValid = false;
                }
            } else if (!input.value.trim()) {
                isValid = false;
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-invalid');
            }
        });

        // Additional validation for exit price when status is "Closed"
        const status = document.getElementById('status');
        const exitPrice = document.getElementById('exitPrice');
        if (status.value === 'Closed') {
            if (!validateInput(exitPrice)) {
                isValid = false;
                exitPrice.classList.add('is-invalid');
            }
        }

        return isValid;
    }

    // Form submission
    tradeForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        const formData = new FormData(tradeForm);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            if (key === 'market' || key === 'status') {
                data[key] = value;
            } else {
                const numValue = numberFormatter.unformat(value);
                data[key] = numValue === null ? null : numValue;
            }
        }

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
                throw new Error(result.error || 'Failed to add trade');
            }

            trades = result.trades;
            updateTradesTable();
            tradeForm.reset();
            
            // Show success message
            showAlert('Trade added successfully!', 'success');

        } catch (error) {
            console.error('Error:', error);
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

    // Table sorting
    document.querySelectorAll('.sortable').forEach(header => {
        header.addEventListener('click', () => {
            const column = header.dataset.sort;
            currentSort.direction = currentSort.column === column && currentSort.direction === 'asc' ? 'desc' : 'asc';
            currentSort.column = column;
            updateTradesTable();
        });
    });

    // Table filtering
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

            // Handle null values in sorting
            if (aVal === null) return 1;
            if (bVal === null) return -1;
            if (aVal === null && bVal === null) return 0;

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
        if (value === null) return '-';
        return new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'USD'
        }).format(value);
    }

    function formatNumber(value) {
        if (value === null) return '-';
        return new Intl.NumberFormat('es-ES').format(value);
    }

    function formatPercentage(value) {
        if (value === null) return '-';
        return new Intl.NumberFormat('es-ES', {
            style: 'percent',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value / 100);
    }

    function getProfitLossClass(value) {
        if (value === null) return '';
        return value > 0 ? 'text-success' : value < 0 ? 'text-danger' : '';
    }
});
