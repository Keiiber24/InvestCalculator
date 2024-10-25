document.addEventListener('DOMContentLoaded', function() {
    const tradeForm = document.getElementById('trade-form');
    const tradesTableBody = document.getElementById('tradesTableBody');
    const tradeFilter = document.getElementById('tradeFilter');
    const clearFilterBtn = document.getElementById('clearFilter');
    const partialSaleModal = new bootstrap.Modal(document.getElementById('partialSaleModal'));
    const partialSaleForm = document.getElementById('partial-sale-form');
    const salesHistoryBody = document.getElementById('salesHistoryBody');
    const tradeTypeField = document.getElementById('trade_type');
    let trades = [];
    let currentSort = { column: 'Date', direction: 'desc' };

    // Initialize trade type
    function initializeTradeType() {
        const selectedTradeType = document.querySelector('input[name="trade_type"]:checked');
        if (selectedTradeType) {
            const value = selectedTradeType.value.toLowerCase();
            tradeTypeField.value = value;
            console.log('Trade type initialized:', { value, type: typeof value });
        }
    }

    // Initialize on load
    initializeTradeType();

    // Trade type radio button handlers
    document.querySelectorAll('input[name="trade_type"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            const value = e.target.value.toLowerCase();
            tradeTypeField.value = value;
            console.log('Trade type changed:', { value, type: typeof value });
        });
    });

    class NumberFormatter {
        constructor() {
            this.thousandsSeparator = '.';
            this.decimalSeparator = ',';
        }

        format(value) {
            if (value === null || value === undefined || value === '') return '';
            
            let strValue = String(value);
            if (typeof value === 'number') {
                strValue = value.toFixed(8);
            }
            const cleanValue = strValue.replace(/[^\d,]/g, '');
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

    // Number input handlers
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

    function validateTradeType() {
        const value = tradeTypeField.value.toLowerCase();
        const isValid = value === 'fiat' || value === 'crypto';
        console.log('Validating trade type:', { value, isValid, type: typeof value });
        return isValid;
    }

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
        } else if (input.id === 'trade_type') {
            isValid = validateTradeType();
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

        // Additional trade type validation
        if (!validateTradeType()) {
            isValid = false;
            showAlert('Invalid trade type. Must be either "fiat" or "crypto".', 'danger');
        }

        return isValid;
    }

    // Trade form submission
    tradeForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        if (!validateForm(tradeForm)) {
            showAlert('Please correct the errors in the form.', 'danger');
            return;
        }

        const formData = new FormData(tradeForm);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = key === 'market' ? value : 
                       key === 'trade_type' ? value.toLowerCase() :
                       numberFormatter.unformat(value);
        }

        // Log form data before submission
        console.log('Submitting trade data:', {
            ...data,
            trade_type: { value: data.trade_type, type: typeof data.trade_type }
        });

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
            
            // Log response data
            console.log('Server response:', result);
            
            if (!response.ok) {
                throw new Error(result.error || 'Failed to add trade');
            }

            trades = result.trades;
            updateTradesTable();
            tradeForm.reset();
            initializeTradeType();
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

    // Rest of the file remains unchanged...
    [Previous content from line 189 onwards]
