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
        if value is None or value == '':
            return None
        try:
            value = float(value)
            if pd.isna(value):
                return None
            if value < 0:
                raise ValueError(f"{field_name} cannot be negative")
            return value
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric value for {field_name}")

    def add_trade(self, market, entry_price, units, exit_price=None, status="Open"):
        """Add a new trade with validation"""
        try:
            # Validate market
            if not market or not isinstance(market, str):
                raise ValueError("Market symbol is required and must be a string")
            
            # Validate status
            if status not in ["Open", "Closed"]:
                raise ValueError("Status must be either 'Open' or 'Closed'")
            
            # Validate numeric inputs
            entry_price = self.validate_numeric(entry_price, "Entry price")
            units = self.validate_numeric(units, "Units")
            exit_price = self.validate_numeric(exit_price, "Exit price") if exit_price else None
            
            if entry_price is None:
                raise ValueError("Entry price is required and must be a positive number")
            
            if units is None:
                raise ValueError("Units is required and must be a positive number")
            
            if status == "Closed":
                if exit_price is None:
                    raise ValueError("Exit price is required for closed trades")

            trade = {
                'Date': datetime.now(),
                'Market': market.upper(),
                'Status': status,
                'Entry Price': entry_price,
                'Exit Price': exit_price,
                'Units': units
            }
            
            # Calculate position size
            trade['Position Size'] = self._safe_calculate(
                self.calculate_position_size,
                trade['Entry Price'],
                trade['Units']
            )
            
            # Calculate P/L and Win/Loss % if trade is closed
            if exit_price is not None:
                trade['Profit/Loss'] = self._safe_calculate(
                    self.calculate_profit_loss,
                    trade['Entry Price'],
                    trade['Exit Price'],
                    trade['Units']
                )
                trade['Win/Loss %'] = self._safe_calculate(
                    self.calculate_win_loss_percentage,
                    trade['Entry Price'],
                    trade['Exit Price']
                )
            else:
                trade['Profit/Loss'] = None
                trade['Win/Loss %'] = None
            
            # Ensure all NaN values are converted to None for JSON serialization
            trade = {k: None if pd.isna(v) else v for k, v in trade.items()}
            
            # Add to DataFrame
            new_trade = pd.DataFrame([trade])
            self.trades = pd.concat([self.trades, new_trade], ignore_index=True)
            
            return trade
            
        except Exception as e:
            raise ValueError(f"Error adding trade: {str(e)}")

    def _safe_calculate(self, calc_func, *args):
        """Safely perform calculations handling None/NaN values"""
        try:
            if any(pd.isna(arg) or arg is None for arg in args):
                return None
            result = calc_func(*args)
            return None if pd.isna(result) else result
        except Exception:
            return None

    @staticmethod
    def calculate_position_size(entry_price, units):
        """Calculate total position value"""
        return float(entry_price * units)
    
    @staticmethod
    def calculate_profit_loss(entry_price, exit_price, units):
        """Calculate profit/loss in dollar amount"""
        return float((exit_price - entry_price) * units)
    
    @staticmethod
    def calculate_win_loss_percentage(entry_price, exit_price):
        """Calculate percentage gain/loss"""
        return float(((exit_price - entry_price) / entry_price) * 100)
    
    def get_trades_json(self):
        """Get trades data in JSON-serializable format"""
        return self.trades.replace({pd.NA: None, np.nan: None}).to_dict('records')
