#!/usr/bin/env python3
from financial_calculator import TradeCalculator

def main():
    # Initialize calculator
    calc = TradeCalculator()
    
    print("Investment Portfolio Calculator Test")
    print("-" * 50)
    
    # Test 1: Add an open trade
    print("\nTest 1: Adding an open trade (AAPL)")
    calc.add_trade("AAPL", 150.50, 100)
    
    # Test 2: Add another trade and sell some units
    print("\nTest 2: Adding and selling GOOGL units")
    trade = calc.add_trade("GOOGL", 2750.00, 10)
    calc.sell_units(trade['id'], 5, 2800.00)
    
    # Test 3: Add and fully close a trade
    print("\nTest 3: Adding and closing MSFT trade")
    trade = calc.add_trade("MSFT", 280.75, 50)
    calc.sell_units(trade['id'], 50, 275.50)
    
    # Display full summary
    print("\nFinal Trade Summary:")
    print("=" * 80)
    summary = calc.get_summary()
    for key, value in summary.items():
        if isinstance(value, (list, dict)):
            print(f"{key}:")
            print(value)
        else:
            print(f"{key}: {value}")
    print("=" * 80)

if __name__ == "__main__":
    main()
