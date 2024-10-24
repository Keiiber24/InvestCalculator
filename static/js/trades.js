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
            if (!value) return '';
            const cleanValue = value.replace(/[^\d,]/g, '');
            const [integerPart, ...decimalParts] = cleanValue.split(',');
            const formattedInteger = this.#formatInteger(integerPart);
            const decimalPart = decimalParts.length > 0 ? decimalParts[decimalParts.length - 1] : '';

            if (value.endsWith(',')) {
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
            if (!value) return '';
            return value.replace(/\./g, '').replace(',', '.');
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
        });

        input.addEventListener('keypress', (e) => {
            if (!/[\d,]/.test(e.key)) {
                e.preventDefault();
            }
        });
    });

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
                data[key] = numberFormatter.unformat(value);
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

            if (!response.ok) {
                throw new Error('Failed to add trade');
            }

            const result = await response.json();
            trades = result.trades;
            updateTradesTable();
            tradeForm.reset();

        } catch (error) {
            console.error('Error:', error);
            alert('Failed to add trade. Please try again.');
        }
    });

    // Form validation
    function validateForm() {
        const inputs = tradeForm.querySelectorAll('input[required], select[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-invalid');
            }

            if (input.classList.contains('number-input') && input.value.trim()) {
                const unformattedValue = numberFormatter.unformat(input.value);
                if (isNaN(parseFloat(unformattedValue))) {
                    isValid = false;
                    input.classList.add('is-invalid');
                }
            }
        });

        return isValid;
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
                <td>${trade['Exit Price'] ? formatCurrency(trade['Exit Price']) : '-'}</td>
                <td>${formatNumber(trade.Units)}</td>
                <td>${formatCurrency(trade['Position Size'])}</td>
                <td class="${getProfitLossClass(trade['Profit/Loss'])}">${trade['Profit/Loss'] ? formatCurrency(trade['Profit/Loss']) : '-'}</td>
                <td class="${getProfitLossClass(trade['Win/Loss %'])}">${trade['Win/Loss %'] ? formatPercentage(trade['Win/Loss %']) : '-'}</td>
            </tr>
        `).join('');
    }

    function formatCurrency(value) {
        if (value == null) return '-';
        return new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'USD'
        }).format(value);
    }

    function formatNumber(value) {
        if (value == null) return '-';
        return new Intl.NumberFormat('es-ES').format(value);
    }

    function formatPercentage(value) {
        if (value == null) return '-';
        return new Intl.NumberFormat('es-ES', {
            style: 'percent',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value / 100);
    }

    function getProfitLossClass(value) {
        if (!value) return '';
        return value > 0 ? 'text-success' : value < 0 ? 'text-danger' : '';
    }
});
