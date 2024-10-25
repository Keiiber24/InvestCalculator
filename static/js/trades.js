document.addEventListener('DOMContentLoaded', function() {
    const tradeForm = document.getElementById('trade-form');
    const tradesTableBody = document.getElementById('tradesTableBody');
    const tradeFilter = document.getElementById('tradeFilter');
    const clearFilterBtn = document.getElementById('clearFilter');
    const partialSaleModal = new bootstrap.Modal(document.getElementById('partialSaleModal'));
    const partialSaleForm = document.getElementById('partial-sale-form');
    const salesHistoryBody = document.getElementById('salesHistoryBody');
    let trades = [];
    let currentSort = { column: 'Date', direction: 'desc' };

    class NumberFormatter {
        constructor() {
            this.thousandsSeparator = '.';
            this.decimalSeparator = ',';
        }

        format(value) {
            if (!value) return '';
            
            const isNegative = value.startsWith('-');
            value = value.replace('-', '');
            
            const parts = value.split(',');
            const integerPart = parts[0].replace(/[^\d]/g, '');
            const decimalPart = parts[1] ? parts[1].replace(/[^\d]/g, '') : '';
            
            const formattedInteger = this.#formatInteger(integerPart);
            
            let result = formattedInteger;
            if (value.includes(',') || decimalPart) {
                result += ',' + decimalPart;
            }
            
            return isNegative ? '-' + result : result;
        }

        #formatInteger(value) {
            const trimmedValue = value.replace(/^0+/, '') || '0';
            return trimmedValue.replace(/\B(?=(\d{3})+(?!\d))/g, this.thousandsSeparator);
        }

        unformat(value) {
            if (!value) return null;
            const normalized = value.replace(/\./g, '').replace(',', '.');
            return Number(normalized);
        }
    }

    const numberFormatter = new NumberFormatter();

    function validateInput(input) {
        input.classList.remove('is-valid', 'is-invalid');
        
        if (!input.required && !input.value.trim()) {
            return true;
        }

        let isValid = true;
        const value = input.value.trim();

        if (input.classList.contains('number-input')) {
            const numValue = numberFormatter.unformat(value);
            isValid = numValue !== null && !isNaN(numValue) && numValue > 0;
            
            if (input.id === 'saleUnits') {
                const tradeId = document.getElementById('saleTradeId').value;
                const trade = trades.find(t => t.id === parseInt(tradeId));
                if (trade && numValue > trade['Remaining Units']) {
                    isValid = false;
                }
            }
        } else {
            isValid = value !== '';
        }

        input.classList.toggle('is-valid', isValid);
        input.classList.toggle('is-invalid', !isValid);
        
        return isValid;
    }

    function validateForm(form) {
        const inputs = form.querySelectorAll('input[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!validateInput(input)) {
                isValid = false;
            }
        });

        return isValid;
    }

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

        input.addEventListener('blur', () => {
            validateInput(input);
        });
    });

    tradeForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        if (!validateForm(tradeForm)) {
            showAlert('Please correct the errors in the form.', 'danger');
            return;
        }

        const formData = new FormData(tradeForm);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = numberFormatter.unformat(value);
        }

        try {
            const submitButton = tradeForm.querySelector('button[type="submit"]');
            const spinner = submitButton.querySelector('.spinner-border');
            submitButton.disabled = true;
            spinner.classList.remove('d-none');

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
            showAlert('Trade added successfully!', 'success');

        } catch (error) {
            console.error('Error adding trade:', error);
            showAlert(error.message || 'Failed to add trade. Please try again.', 'danger');
        } finally {
            const submitButton = tradeForm.querySelector('button[type="submit"]');
            const spinner = submitButton.querySelector('.spinner-border');
            submitButton.disabled = false;
            spinner.classList.add('d-none');
        }
    });

    partialSaleForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        if (!validateForm(partialSaleForm)) {
            showAlert('Please correct the errors in the form.', 'danger', 'modal');
            return;
        }

        const tradeId = document.getElementById('saleTradeId').value;
        const data = {
            units: numberFormatter.unformat(document.getElementById('saleUnits').value),
            exitPrice: numberFormatter.unformat(document.getElementById('saleExitPrice').value)
        };

        try {
            const submitButton = partialSaleForm.querySelector('button[type="submit"]');
            const spinner = submitButton.querySelector('.spinner-border');
            submitButton.disabled = true;
            spinner.classList.remove('d-none');

            const response = await fetch(`/sell_units/${tradeId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Failed to process sale');
            }

            trades = result.trades;
            updateTradesTable();
            updateSalesHistory(result.salesHistory);
            partialSaleForm.reset();
            partialSaleModal.hide();
            showAlert('Units sold successfully!', 'success');

        } catch (error) {
            console.error('Error processing sale:', error);
            showAlert(error.message || 'Failed to process sale. Please try again.', 'danger', 'modal');
        } finally {
            const submitButton = partialSaleForm.querySelector('button[type="submit"]');
            const spinner = submitButton.querySelector('.spinner-border');
            submitButton.disabled = false;
            spinner.classList.add('d-none');
        }
    });

    function showAlert(message, type, location = 'page') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        if (location === 'modal') {
            partialSaleForm.insertAdjacentElement('beforebegin', alertDiv);
        } else {
            tradeForm.insertAdjacentElement('beforebegin', alertDiv);
        }
        
        setTimeout(() => alertDiv.remove(), 5000);
    }

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

        filteredTrades.sort((a, b) => {
            let aVal = a[currentSort.column];
            let bVal = b[currentSort.column];

            if (aVal === null || aVal === undefined) return 1;
            if (bVal === null || bVal === undefined) return -1;
            if ((aVal === null || aVal === undefined) && (bVal === null || bVal === undefined)) return 0;

            if (typeof aVal === 'string') aVal = aVal.toLowerCase();
            if (typeof bVal === 'string') bVal = bVal.toLowerCase();

            if (aVal < bVal) return currentSort.direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return currentSort.direction === 'asc' ? 1 : -1;
            return 0;
        });

        tradesTableBody.innerHTML = filteredTrades.map(trade => {
            const isOpen = trade['Remaining Units'] > 0;
            const statusBadge = isOpen ? 
                '<span class="badge bg-success">Open</span>' : 
                '<span class="badge bg-secondary">Closed</span>';
            
            return `
                <tr data-trade-id="${trade.id}">
                    <td>${new Date(trade.Date).toLocaleString()}</td>
                    <td>${trade.Market}</td>
                    <td>${formatCurrency(trade['Entry Price'])}</td>
                    <td>${formatNumber(trade.Units, 'units')}</td>
                    <td>${formatNumber(trade['Remaining Units'], 'units')}</td>
                    <td>${formatCurrency(trade['Position Size'])}</td>
                    <td>${statusBadge}</td>
                    <td>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-info view-history-btn" title="View History">
                                <i class="bi bi-clock-history me-1"></i>
                                History
                            </button>
                            ${isOpen ? `
                                <button class="btn btn-sm btn-outline-warning sell-units-btn" title="Sell Units">
                                    <i class="bi bi-cash-coin me-1"></i>
                                    Sell
                                </button>
                            ` : ''}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        document.querySelectorAll('.view-history-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const tradeId = e.target.closest('tr').dataset.tradeId;
                openSaleModal(parseInt(tradeId), 'history');
            });
        });

        document.querySelectorAll('.sell-units-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const tradeId = e.target.closest('tr').dataset.tradeId;
                openSaleModal(parseInt(tradeId), 'sell');
            });
        });
    }

    async function openSaleModal(tradeId, mode = 'history') {
        const trade = trades.find(t => t.id === tradeId);
        if (!trade) return;

        document.getElementById('saleTradeId').value = tradeId;
        
        const saleForm = document.getElementById('partial-sale-form');
        const modalTitle = document.querySelector('.modal-title');
        
        if (mode === 'sell' && trade['Remaining Units'] > 0) {
            saleForm.style.display = 'block';
            modalTitle.textContent = 'Sell Units';
            document.getElementById('saleUnits').value = '';
            document.getElementById('saleExitPrice').value = '';
        } else {
            saleForm.style.display = 'none';
            modalTitle.textContent = 'Trade History';
        }

        try {
            const response = await fetch(`/get_sales_history/${tradeId}`);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Failed to fetch sales history');
            }

            updateSalesHistory(result.salesHistory);
            partialSaleModal.show();

        } catch (error) {
            console.error('Error fetching sales history:', error);
            showAlert('Failed to load sales history', 'danger');
        }
    }

    function updateSalesHistory(salesHistory) {
        salesHistoryBody.innerHTML = salesHistory.map(sale => `
            <tr>
                <td>${new Date(sale.Date).toLocaleString()}</td>
                <td>${formatNumber(sale['Units Sold'], 'units')}</td>
                <td>${formatCurrency(sale['Exit Price'])}</td>
                <td class="${getProfitLossClass(sale['Partial P/L'])}">${formatCurrency(sale['Partial P/L'])}</td>
                <td class="${getProfitLossClass(sale['Partial P/L %'])}">${formatPercentage(sale['Partial P/L %'])}</td>
            </tr>
        `).join('');

        if (salesHistory.length === 0) {
            salesHistoryBody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center">No sales history available</td>
                </tr>
            `;
        }
    }

    function formatNumber(value, type = 'default') {
        if (value === null || value === undefined) return '-';
        const options = {
            minimumFractionDigits: type === 'units' ? 8 : 2,
            maximumFractionDigits: type === 'units' ? 8 : 2,
            useGrouping: true
        };
        return new Intl.NumberFormat('es-ES', options).format(value);
    }

    function formatCurrency(value) {
        if (value === null || value === undefined) return '-';
        return new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'USD'
        }).format(value);
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