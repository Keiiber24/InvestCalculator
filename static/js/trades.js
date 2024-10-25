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

    // Initialize trade type field
    const selectedTradeType = document.querySelector('input[name="trade_type"]:checked');
    if (selectedTradeType) {
        tradeTypeField.value = selectedTradeType.value.toLowerCase();
    }

    document.querySelectorAll('input[name="trade_type"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            console.log('Trade type changed:', e.target.value);
            tradeTypeField.value = e.target.value.toLowerCase();
        });
    });

    // ... rest of the file remains the same ...
    [Previous content of trades.js from line 20 onwards]
