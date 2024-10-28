#!/usr/bin/env python3
from financial_calculator import TradeCalculator

def main():
    # Initialize calculator with a test user ID
    calc = TradeCalculator(user_id=1)
    
    print("Investment Portfolio Calculator Test")
    print("-" * 50)
    
    # Test 1: Add an open trade
    print("\nTest 1: Adding an open trade (BTC/USDT)")
    calc.add_trade("BTC/USDT", 35000.00, 0.5)
    
    # Test 2: Add another open trade
    print("\nTest 2: Adding another open trade (ETH/USDT)")
    trade = calc.add_trade("ETH/USDT", 2000.00, 5)
    
    # Test 3: Sell some units from the ETH trade
    print("\nTest 3: Selling partial units from ETH trade")
    calc.sell_units(trade['id'], 2, 2100.00)
    
    # Display full summary
    print("\nFinal Trade Summary:")
    print("=" * 80)
    print(calc.get_summary())
    print("=" * 80)

if __name__ == "__main__":
    main()
