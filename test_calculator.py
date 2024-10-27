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
    
    # Test 2: Add a closed trade with profit
    print("\nTest 2: Adding a closed trade with profit (GOOGL)")
    calc.add_trade("GOOGL", 2750.00, 10, 2800.00, "Closed")
    
    # Test 3: Add a closed trade with loss
    print("\nTest 3: Adding a closed trade with loss (MSFT)")
    calc.add_trade("MSFT", 280.75, 50, 275.50, "Closed")
    
    # Display full summary
    print("\nFinal Trade Summary:")
    print("=" * 80)
    print(calc.get_summary())
    print("=" * 80)

if __name__ == "__main__":
    main()
