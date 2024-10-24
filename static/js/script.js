document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('calculator-form');
    const resultDiv = document.getElementById('result');
    const calculateBtn = document.getElementById('calculateBtn');
    const spinner = calculateBtn.querySelector('.spinner-border');

    class NumberFormatter {
        constructor() {
            this.thousandsSeparator = '.';
            this.decimalSeparator = ',';
        }

        format(value) {
            if (!value) return '';

            // Elimina cualquier caracter no numérico excepto coma
            const cleanValue = value.replace(/[^\d,]/g, '');

            // Divide en parte entera y decimal
            const [integerPart, ...decimalParts] = cleanValue.split(',');

            // Procesa la parte entera para agregar separadores de miles
            const formattedInteger = this.#formatInteger(integerPart);

            // Si hay parte decimal, la añade
            const decimalPart = decimalParts.length > 0 ? decimalParts[decimalParts.length - 1] : '';

            // Reconstruye el número
            if (value.endsWith(',')) {
                return `${formattedInteger},`;
            } else if (decimalPart) {
                return `${formattedInteger},${decimalPart}`;
            }
            return formattedInteger;
        }

        #formatInteger(value) {
            // Elimina ceros no significativos al inicio
            const trimmedValue = value.replace(/^0+/, '') || '0';

            // Agrega los separadores de miles
            return trimmedValue.replace(/\B(?=(\d{3})+(?!\d))/g, this.thousandsSeparator);
        }

        unformat(value) {
            if (!value) return '';
            return value.replace(/\./g, '').replace(',', '.');
        }

        getCaretPosition(oldValue, newValue, oldPosition) {
            // Cuenta los separadores antes de la posición del cursor
            const oldSeparators = (oldValue.slice(0, oldPosition).match(/\./g) || []).length;
            const newSeparators = (newValue.slice(0, oldPosition).match(/\./g) || []).length;

            return oldPosition + (newSeparators - oldSeparators);
        }
    }

    const numberFormatter = new NumberFormatter();

    function handleNumberInput(input, e) {
        const oldValue = input.value;
        const oldPosition = input.selectionStart;

        // Si es una coma y ya existe una, no hace nada
        if (e.data === ',' && oldValue.includes(',')) {
            e.preventDefault();
            return;
        }

        const formattedValue = numberFormatter.format(input.value);

        if (oldValue !== formattedValue) {
            input.value = formattedValue;

            // Calcula la nueva posición del cursor
            const newPosition = numberFormatter.getCaretPosition(oldValue, formattedValue, oldPosition);
            input.setSelectionRange(newPosition, newPosition);
        }

        // Validación
        validateInput(input);
    }

    function validateInput(input) {
        const unformattedValue = numberFormatter.unformat(input.value);
        const isValid = unformattedValue && !isNaN(parseFloat(unformattedValue));

        if (input.value) {
            input.classList.toggle('is-valid', isValid);
            input.classList.toggle('is-invalid', !isValid);
        } else {
            input.classList.remove('is-valid', 'is-invalid');
        }
    }

    // Form validation
    function validateForm() {
        const inputs = form.querySelectorAll('input[required]');
        let isValid = true;

        inputs.forEach(input => {
            const unformattedValue = numberFormatter.unformat(input.value);
            if (!unformattedValue) {
                isValid = false;
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            }

            // Specific validation for risk percentage
            if (input.id === 'riskPercentage') {
                const value = parseFloat(unformattedValue);
                if (value < 0 || value > 100) {
                    isValid = false;
                    input.classList.add('is-invalid');
                }
            }
        });

        return isValid;
    }

    // Inicializar campos numéricos
    const numberInputs = document.querySelectorAll('#capitalTotal, #entryPrice, #exitPrice');

    numberInputs.forEach(input => {
        input.setAttribute('type', 'text');
        input.setAttribute('inputmode', 'decimal');

        // Formatear valor inicial si existe
        if (input.value) {
            input.value = numberFormatter.format(input.value);
        }

        // Event listeners
        input.addEventListener('input', (e) => handleNumberInput(input, e));

        input.addEventListener('keypress', (e) => {
            // Solo permite números y coma
            if (!/[\d,]/.test(e.key)) {
                e.preventDefault();
            }
        });

        input.addEventListener('paste', (e) => {
            e.preventDefault();
            const pastedText = (e.clipboardData || window.clipboardData).getData('text');
            const cleanedText = pastedText.replace(/[^\d,]/g, '');

            const cursorPos = input.selectionStart;
            const textBeforeCursor = input.value.substring(0, cursorPos);
            const textAfterCursor = input.value.substring(cursorPos);

            input.value = textBeforeCursor + cleanedText + textAfterCursor;
            input.dispatchEvent(new Event('input'));
        });
    });

    // Increment/Decrement buttons
    document.querySelectorAll('[data-action]').forEach(button => {
        button.addEventListener('click', () => {
            const input = button.parentElement.querySelector('input');
            const step = parseFloat(input.step) || 1;
            const min = parseFloat(input.min);
            const max = parseFloat(input.max);
            let value = parseFloat(numberFormatter.unformat(input.value)) || 0;

            if (button.dataset.action === 'increment') {
                value = Math.min(value + step, max || Infinity);
            } else {
                value = Math.max(value - step, min || -Infinity);
            }

            input.value = numberFormatter.format(value.toString());
            input.dispatchEvent(new Event('input'));
        });
    });

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        // Show loading state
        calculateBtn.disabled = true;
        spinner.classList.remove('d-none');

        const formData = new FormData(form);
        const data = {};

        // Desformatear números antes de enviar
        for (let [key, value] of formData.entries()) {
            data[key] = numberFormatter.unformat(value);
        }

        try {
            const response = await fetch('/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                throw new Error('Calculation failed');
            }

            const result = await response.json();
            displayResults(result);
        } catch (error) {
            console.error('Error:', error);
            resultDiv.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    An error occurred. Please try again.
                </div>
            `;
        } finally {
            calculateBtn.disabled = false;
            spinner.classList.add('d-none');
        }
    });

    function displayResults(result) {
        resultDiv.innerHTML = `
            <div class="card shadow-lg border-0">
                <div class="card-header bg-primary">
                    <h2 class="card-title h4 mb-0 text-yellow">Investment Results</h2>
                </div>
                <div class="card-body">
                    <div class="row g-4">
                        <div class="col-md-6">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-currency-exchange fs-4 text-warning me-2"></i>
                                <div>
                                    <h5 class="text-gradient mb-1">Capital at Risk</h5>
                                    <p class="h3 mb-1">${formatNumber(result.capitalAtRisk)}</p>
                                    <small class="text-muted">Amount you're risking on this investment</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-graph-up fs-4 text-warning me-2"></i>
                                <div>
                                    <h5 class="text-gradient mb-1">Risk per Unit</h5>
                                    <p class="h3 mb-1">${formatNumber(result.riskPerUnit)}</p>
                                    <small class="text-muted">Price difference between purchase and stop loss</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-rulers fs-4 text-warning me-2"></i>
                                <div>
                                    <h5 class="text-gradient mb-1">Position Size</h5>
                                    <p class="h3 mb-1">${formatNumber(result.positionSize)} units</p>
                                    <small class="text-muted">Number of units to invest</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-cash-stack fs-4 text-warning me-2"></i>
                                <div>
                                    <h5 class="text-gradient mb-1">Total Investment Value</h5>
                                    <p class="h3 mb-1">${formatNumber(result.totalPositionValue)}</p>
                                    <small class="text-muted">Total value at purchase price</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Función para formatear números en los resultados
    function formatNumber(num) {
        return new Intl.NumberFormat('es-ES', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(num);
    }
});