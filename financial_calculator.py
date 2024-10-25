import pandas as pd
import numpy as np
from datetime import datetime
pd.set_option('display.float_format', lambda x: '%.8f' % x)

class TradeCalculator:
    def __init__(self):
        # Main trades DataFrame
        self.trades = pd.DataFrame(columns=[
            'id', 'Date', 'Market', 'Entry Price', 
            'Units', 'Remaining Units', 'Position Size', 'Trade Type'
        ])
        
        # Partial sales history DataFrame
        self.sales_history = pd.DataFrame(columns=[
            'trade_id', 'Date', 'Units Sold', 'Exit Price', 
            'Partial P/L', 'Partial P/L %'
        ])
        
        self.trade_counter = 0

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

    def add_trade(self, market, entry_price, units, trade_type='fiat'):
        """Add a new trade with trade type parameter"""
        try:
            # Validate inputs
            if not market or not isinstance(market, str):
                raise ValueError("Market symbol is required and must be a string")
            
            if trade_type not in ['fiat', 'crypto']:
                raise ValueError("Trade type must be either 'fiat' or 'crypto'")
            
            entry_price = self.validate_numeric(entry_price, "Entry price")
            units = self.validate_numeric(units, "Units")
            
            if entry_price is None:
                raise ValueError("Entry price is required and must be a positive number")
            
            if units is None:
                raise ValueError("Units is required and must be a positive number")
            
            # Generate unique trade ID
            self.trade_counter += 1
            trade_id = self.trade_counter
            
            # Calculate initial position size based on entry price and units
            position_size = self.calculate_position_size(entry_price, units)
            
            trade = {
                'id': trade_id,
                'Date': datetime.now(),
                'Market': market.upper(),
                'Entry Price': entry_price,
                'Units': units,
                'Remaining Units': units,
                'Position Size': position_size,
                'Trade Type': trade_type
            }
            
            # Add to DataFrame
            new_trade = pd.DataFrame([trade])
            self.trades = pd.concat([self.trades, new_trade], ignore_index=True)
            
            return self.clean_trade_data(trade)
            
        except Exception as e:
            raise ValueError(f"Error adding trade: {str(e)}")

    def sell_units(self, trade_id, units_to_sell, exit_price):
        """Record a partial sale of units"""
        try:
            trade_idx = self.trades.index[self.trades['id'] == trade_id].tolist()
            if not trade_idx:
                raise ValueError("Trade not found")
            
            trade_idx = trade_idx[0]
            trade = self.trades.iloc[trade_idx]
            
            units_to_sell = self.validate_numeric(units_to_sell, "Units to sell")
            exit_price = self.validate_numeric(exit_price, "Exit price")
            
            if units_to_sell > trade['Remaining Units']:
                raise ValueError("Cannot sell more units than remaining")
            
            # Calculate P/L for this sale
            partial_pl = self.calculate_profit_loss(trade['Entry Price'], exit_price, units_to_sell)
            partial_pl_percent = self.calculate_win_loss_percentage(trade['Entry Price'], exit_price)
            
            # Record the sale
            sale = {
                'trade_id': trade_id,
                'Date': datetime.now(),
                'Units Sold': units_to_sell,
                'Exit Price': exit_price,
                'Partial P/L': partial_pl,
                'Partial P/L %': partial_pl_percent
            }
            
            # Update remaining units and position size
            remaining_units = trade['Remaining Units'] - units_to_sell
            self.trades.at[trade_idx, 'Remaining Units'] = remaining_units
            # Update position size based on remaining units
            self.trades.at[trade_idx, 'Position Size'] = self.calculate_position_size(trade['Entry Price'], remaining_units)
            
            # Add to sales history
            new_sale = pd.DataFrame([sale])
            self.sales_history = pd.concat([self.sales_history, new_sale], ignore_index=True)
            
            return {
                'sale': self.clean_trade_data(sale),
                'updated_trade': self.clean_trade_data(self.trades.iloc[trade_idx].to_dict())
            }
            
        except Exception as e:
            raise ValueError(f"Error processing sale: {str(e)}")

    @staticmethod
    def calculate_position_size(entry_price, units):
        """Calculate position size based on entry price and units"""
        try:
            # Ensure high precision for the calculation
            entry_price = float(entry_price)
            units = float(units)
            return float(entry_price * units)
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def calculate_profit_loss(entry_price, exit_price, units):
        """Calculate profit/loss in dollar amount"""
        return float((exit_price - entry_price) * units)
    
    @staticmethod
    def calculate_win_loss_percentage(entry_price, exit_price):
        """Calculate percentage gain/loss"""
        return float(((exit_price - entry_price) / entry_price) * 100)

    def get_trade_sales_history(self, trade_id):
        """Get sales history for a specific trade"""
        sales = self.sales_history[self.sales_history['trade_id'] == trade_id]
        return self.clean_trade_data(sales.to_dict('records'))

    def get_trades_json(self):
        """Get trades data in JSON-serializable format"""
        return self.clean_trade_data(self.trades.to_dict('records'))

    @staticmethod
    def clean_trade_data(data):
        """Clean data for JSON serialization"""
        if isinstance(data, (list, tuple)):
            return [TradeCalculator.clean_trade_data(item) for item in data]
        elif isinstance(data, dict):
            return {k: (v.isoformat() if isinstance(v, datetime) else float(v) if isinstance(v, (int, float, np.integer, np.floating)) else v) 
                   for k, v in data.items()}
        return data
