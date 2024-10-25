document.addEventListener('DOMContentLoaded', function() {
    // ... Previous code until validateInput function ...

    function validateInput(input) {
        input.classList.remove('is-valid', 'is-invalid');
        
        if (!input.required && !input.value.trim()) {
            return true;
        }

        let isValid = true;
        const value = input.value.trim();

        if (input.id === 'market') {
            // Allow letters, numbers, hyphens, forward slashes, and dots for crypto pairs
            isValid = /^[A-Za-z0-9\-./]+$/.test(value);
        } else if (input.classList.contains('number-input')) {
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

    // ... Rest of the existing code ...

    // Update market input event listener
    const marketInput = document.getElementById('market');
    if (marketInput) {
        marketInput.addEventListener('input', (e) => {
            // Convert to uppercase while typing
            const value = e.target.value.toUpperCase();
            e.target.value = value;
            validateInput(marketInput);
        });

        marketInput.addEventListener('keypress', (e) => {
            // Allow only valid characters for market symbols
            if (!/[A-Za-z0-9\-./]/.test(e.key)) {
                e.preventDefault();
            }
        });
    }

    // ... Rest of the existing code ...

    tradeForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        if (!validateForm(tradeForm)) {
            showAlert('Please correct the errors in the form.', 'danger');
            return;
        }

        const formData = new FormData(tradeForm);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            if (key === 'market') {
                data[key] = value.toUpperCase();
            } else {
                data[key] = numberFormatter.unformat(value);
            }
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

    // ... Rest of the existing code remains the same ...
});
