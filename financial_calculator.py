import pandas as pd
import numpy as np
from datetime import datetime
pd.set_option('display.float_format', lambda x: '%.2f' % x)

class TradeCalculator:
    def __init__(self):
        columns = pd.Index(['Date', 'Market', 'Status', 'Entry Price', 'Exit Price', 
                          'Units', 'Position Size', 'Profit/Loss', 'Win/Loss %'])
        self.trades = pd.DataFrame(columns=columns)
    
    def add_trade(self, market, entry_price, units, exit_price=None, status="Open"):
        trade = {
            'Date': datetime.now(),
            'Market': market,
            'Status': status,
            'Entry Price': float(entry_price),
            'Exit Price': float(exit_price) if exit_price else None,
            'Units': float(units)
        }
        
        # Calculate position size
        trade['Position Size'] = self.calculate_position_size(trade['Entry Price'], trade['Units'])
        
        # Calculate P/L and Win/Loss % if trade is closed
        if exit_price:
            trade['Profit/Loss'] = self.calculate_profit_loss(
                trade['Entry Price'], trade['Exit Price'], trade['Units']
            )
            trade['Win/Loss %'] = self.calculate_win_loss_percentage(
                trade['Entry Price'], trade['Exit Price']
            )
        
        self.trades = pd.concat([self.trades, pd.DataFrame([trade])], ignore_index=True)
    
    @staticmethod
    def calculate_position_size(entry_price, units):
        """Calculate total position value"""
        return entry_price * units
    
    @staticmethod
    def calculate_profit_loss(entry_price, exit_price, units):
        """Calculate profit/loss in dollar amount"""
        return (exit_price - entry_price) * units
    
    @staticmethod
    def calculate_win_loss_percentage(entry_price, exit_price):
        """Calculate percentage gain/loss"""
        return ((exit_price - entry_price) / entry_price) * 100
    
    def close_trade(self, index, exit_price):
        """Close an open trade with exit price"""
        if index in self.trades.index:
            self.trades.at[index, 'Exit Price'] = float(exit_price)
            self.trades.at[index, 'Status'] = 'Closed'
            self.trades.at[index, 'Profit/Loss'] = self.calculate_profit_loss(
                self.trades.at[index, 'Entry Price'],
                exit_price,
                self.trades.at[index, 'Units']
            )
            self.trades.at[index, 'Win/Loss %'] = self.calculate_win_loss_percentage(
                self.trades.at[index, 'Entry Price'],
                exit_price
            )
    
    def get_summary(self):
        """Get formatted trade summary"""
        if len(self.trades) == 0:
            return "No trades recorded"
            
        formatted_trades = self.trades.copy()
        
        # Format numeric columns
        numeric_formats = {
            'Entry Price': '${:.2f}',
            'Exit Price': '${:.2f}',
            'Position Size': '${:.2f}',
            'Profit/Loss': '${:.2f}',
            'Win/Loss %': '{:.2f}%'
        }
        
        for col, fmt in numeric_formats.items():
            if col in formatted_trades.columns:
                formatted_trades[col] = formatted_trades[col].apply(
                    lambda x: fmt.format(x) if pd.notnull(x) else '-'
                )
        
        return formatted_trades.to_string(index=False)

if __name__ == "__main__":
    # Example usage
    calc = TradeCalculator()
    
    # Add some sample trades
    calc.add_trade("AAPL", 150.50, 100)  # Open trade
    calc.add_trade("GOOGL", 2750.00, 10, 2800.00, "Closed")  # Closed trade
    calc.add_trade("MSFT", 280.75, 50, 285.50, "Closed")  # Closed trade
    
    # Display the trades summary
    print("\nTrade Summary:")
    print(calc.get_summary())
