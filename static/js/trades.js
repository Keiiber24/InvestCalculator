import { formatCurrency, formatNumber, formatPercentage, getProfitLossClass } from './utils.js';

// Initialize variables
let trades = [];
const tradeForm = document.getElementById('trade-form');
const tradesTableBody = document.getElementById('tradesTableBody');
const partialSaleModal = document.getElementById('partialSaleModal');
const partialSaleForm = document.getElementById('partial-sale-form');
const salesHistoryBody = document.getElementById('salesHistoryBody');
const tradeFilter = document.getElementById('tradeFilter');
const clearFilterBtn = document.getElementById('clearFilter');

// Format and validate numbers
const numberFormatter = {
    format(value) {
        if (!value) return '';
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 8
        }).format(value);
    },
    unformat(value) {
        if (!value) return null;
        const parsed = parseFloat(value.toString().replace(/[^\d.-]/g, ''));
        return isNaN(parsed) ? null : parsed;
    }
};

// Handle form validation
function validateForm(form) {
    let isValid = true;
    form.querySelectorAll('input[required]').forEach(input => {
        const value = input.value.trim();
        const numValue = input.type === 'text' ? numberFormatter.unformat(value) : value;
        
        if (!value || (input.type === 'text' && (numValue === null || numValue <= 0))) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        }
    });
    return isValid;
}

// Show/hide loading state
function showLoadingState(form) {
    const button = form.querySelector('button[type="submit"]');
    const spinner = button.querySelector('.spinner-border');
    button.disabled = true;
    spinner.classList.remove('d-none');
}

function hideLoadingState(form) {
    const button = form.querySelector('button[type="submit"]');
    const spinner = button.querySelector('.spinner-border');
    button.disabled = false;
    spinner.classList.add('d-none');
}

// Show alert message
function showAlert(message, type = 'success', location = 'page') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    if (location === 'modal') {
        const modalBody = partialSaleModal.querySelector('.modal-body');
        modalBody.insertAdjacentHTML('afterbegin', alertHtml);
    } else {
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());
        tradeForm.insertAdjacentHTML('beforebegin', alertHtml);
    }
}

// Update trades table
function updateTradesTable(filterText = '') {
    const filteredTrades = filterText
        ? trades.filter(trade => 
            trade.Market.toLowerCase().includes(filterText.toLowerCase()) ||
            trade.Units.toString().includes(filterText) ||
            trade['Entry Price'].toString().includes(filterText)
          )
        : trades;

    tradesTableBody.innerHTML = filteredTrades.map(trade => `
        <tr>
            <td>${new Date(trade.Date).toLocaleDateString()}</td>
            <td>${trade.Market}</td>
            <td>${formatCurrency(trade['Entry Price'])}</td>
            <td>${formatNumber(trade.Units, 8)}</td>
            <td>${formatNumber(trade['Remaining Units'], 8)}</td>
            <td>${formatCurrency(trade['Position Size'])}</td>
            <td>
                <span class="badge ${trade['Remaining Units'] > 0 ? 'bg-success' : 'bg-secondary'}">
                    ${trade['Remaining Units'] > 0 ? 'Open' : 'Closed'}
                </span>
            </td>
            <td>
                ${trade['Remaining Units'] > 0 ? `
                    <button class="btn btn-sm btn-warning" 
                            onclick="window.openSaleModal(${trade.id})"
                            data-trade-id="${trade.id}">
                        <i class="bi bi-cash me-1"></i>
                        Sell
                    </button>
                ` : ''}
            </td>
        </tr>
    `).join('');
}

// Handle trade form submission
tradeForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    if (!validateForm(tradeForm)) {
        showAlert('Please fill in all required fields correctly.', 'danger');
        return;
    }

    try {
        showLoadingState(tradeForm);

        const formData = new FormData(tradeForm);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            if (key === 'market') {
                data[key] = value.trim();
            } else {
                const numValue = numberFormatter.unformat(value);
                if (numValue === null) {
                    throw new Error(`Invalid value for ${key}`);
                }
                data[key] = numValue;
            }
        }

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
        showAlert(error.message || 'Failed to add trade', 'danger');
    } finally {
        hideLoadingState(tradeForm);
    }
});

// Handle partial sale form submission
partialSaleForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    if (!validateForm(partialSaleForm)) {
        showAlert('Please fill in all required fields correctly.', 'danger', 'modal');
        return;
    }

    try {
        showLoadingState(partialSaleForm);

        const tradeId = document.getElementById('saleTradeId').value;
        const units = numberFormatter.unformat(document.getElementById('saleUnits').value);
        const exitPrice = numberFormatter.unformat(document.getElementById('saleExitPrice').value);

        if (!tradeId || units === null || exitPrice === null) {
            throw new Error('Invalid sale data');
        }

        const response = await fetch(`/sell_units/${tradeId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                units: units,
                exitPrice: exitPrice
            }),
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Failed to process sale');
        }

        trades = result.trades;
        updateTradesTable();
        updateSalesHistory(result.salesHistory);
        showAlert('Units sold successfully!', 'success', 'modal');
        partialSaleForm.reset();

    } catch (error) {
        console.error('Error processing sale:', error);
        showAlert(error.message || 'Failed to process sale', 'danger', 'modal');
    } finally {
        hideLoadingState(partialSaleForm);
    }
});

// Filter trades
tradeFilter.addEventListener('input', function(e) {
    updateTradesTable(e.target.value);
});

// Clear filter
clearFilterBtn.addEventListener('click', function() {
    tradeFilter.value = '';
    updateTradesTable();
});

// Handle sorting
document.querySelectorAll('.sortable').forEach(header => {
    header.addEventListener('click', function() {
        const column = this.dataset.sort;
        trades.sort((a, b) => {
            if (typeof a[column] === 'string') {
                return a[column].localeCompare(b[column]);
            }
            return a[column] - b[column];
        });
        updateTradesTable(tradeFilter.value);
    });
});

// Initialize table with existing trades
fetch('/add_trade', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({}),
})
.then(response => response.json())
.then(result => {
    if (result.trades) {
        trades = result.trades;
        updateTradesTable();
    }
})
.catch(error => console.error('Error fetching trades:', error));

// Function to open sale modal
window.openSaleModal = async function(tradeId) {
    try {
        document.getElementById('saleTradeId').value = tradeId;
        const response = await fetch(`/get_sales_history/${tradeId}`);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to fetch sales history');
        }
        
        updateSalesHistory(result.salesHistory);
        const modal = new bootstrap.Modal(partialSaleModal);
        modal.show();
    } catch (error) {
        console.error('Error opening sale modal:', error);
        showAlert(error.message || 'Failed to open sale modal', 'danger');
    }
}

// Update sales history table
function updateSalesHistory(history) {
    salesHistoryBody.innerHTML = history.length ? history.map(sale => `
        <tr>
            <td>${new Date(sale.Date).toLocaleDateString()}</td>
            <td>${formatNumber(sale['Units Sold'], 8)}</td>
            <td>${formatCurrency(sale['Exit Price'])}</td>
            <td class="${getProfitLossClass(sale['Partial P/L'])}">
                ${formatCurrency(sale['Partial P/L'])}
            </td>
            <td class="${getProfitLossClass(sale['Partial P/L %'])}">
                ${formatPercentage(sale['Partial P/L %'])}
            </td>
        </tr>
    `).join('') : '<tr><td colspan="5" class="text-center">No sales history available</td></tr>';
}
