import pandas as pd
import numpy as np
from datetime import datetime
pd.set_option('display.float_format', lambda x: '%.2f' % x)

class TradeCalculator:
    def __init__(self):
        columns = pd.Index(['Date', 'Market', 'Status', 'Entry Price', 'Exit Price', 
                          'Units', 'Position Size', 'Profit/Loss', 'Win/Loss %'])
        self.trades = pd.DataFrame(columns=columns)
    
    def validate_numeric(self, value, field_name):
        """Validate numeric input"""
        if value is None:
            return None
        try:
            value = float(value)
            if np.isnan(value):
                return None
            return value
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric value for {field_name}")

    def add_trade(self, market, entry_price, units, exit_price=None, status="Open"):
        # Validate market
        if not market or not isinstance(market, str):
            raise ValueError("Market symbol is required and must be a string")
            
        # Validate status
        if status not in ["Open", "Closed"]:
            raise ValueError("Status must be either 'Open' or 'Closed'")
            
        # Validate numeric inputs
        entry_price = self.validate_numeric(entry_price, "entry price")
        units = self.validate_numeric(units, "units")
        exit_price = self.validate_numeric(exit_price, "exit price")
        
        if entry_price is None or units is None:
            raise ValueError("Entry price and units are required")
        
        if status == "Closed" and exit_price is None:
            raise ValueError("Exit price is required for closed trades")

        trade = {
            'Date': datetime.now(),
            'Market': market,
            'Status': status,
            'Entry Price': entry_price,
            'Exit Price': exit_price,
            'Units': units
        }
        
        # Calculate position size
        trade['Position Size'] = self.calculate_position_size(trade['Entry Price'], trade['Units'])
        
        # Calculate P/L and Win/Loss % if trade is closed
        if exit_price is not None:
            trade['Profit/Loss'] = self.calculate_profit_loss(
                trade['Entry Price'], trade['Exit Price'], trade['Units']
            )
            trade['Win/Loss %'] = self.calculate_win_loss_percentage(
                trade['Entry Price'], trade['Exit Price']
            )
        
        # Convert any remaining NaN values to None for JSON serialization
        trade = {k: None if isinstance(v, float) and np.isnan(v) else v 
                for k, v in trade.items()}
        
        new_trade = pd.DataFrame([trade])
        self.trades = pd.concat([self.trades, new_trade], ignore_index=True)
        
        # Convert DataFrame to dict for JSON serialization
        return trade
    
    @staticmethod
    def calculate_position_size(entry_price, units):
        """Calculate total position value"""
        result = entry_price * units
        return np.nan_to_num(result, nan=None)
    
    @staticmethod
    def calculate_profit_loss(entry_price, exit_price, units):
        """Calculate profit/loss in dollar amount"""
        if None in (entry_price, exit_price, units):
            return None
        result = (exit_price - entry_price) * units
        return np.nan_to_num(result, nan=None)
    
    @staticmethod
    def calculate_win_loss_percentage(entry_price, exit_price):
        """Calculate percentage gain/loss"""
        if None in (entry_price, exit_price):
            return None
        result = ((exit_price - entry_price) / entry_price) * 100
        return np.nan_to_num(result, nan=None)
    
    def close_trade(self, index, exit_price):
        """Close an open trade with exit price"""
        exit_price = self.validate_numeric(exit_price, "exit price")
        if exit_price is None:
            raise ValueError("Valid exit price is required")
            
        if index in self.trades.index:
            self.trades.at[index, 'Exit Price'] = exit_price
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
