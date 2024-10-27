import pandas as pd
import numpy as np
from datetime import datetime

class TradeCalculator:
    def __init__(self):
        # Main trades DataFrame
        self.trades = pd.DataFrame({
            'id': pd.Series(dtype='int64'),
            'Date': pd.Series(dtype='datetime64[ns]'),
            'Market': pd.Series(dtype='str'),
            'Entry Price': pd.Series(dtype='float64'),
            'Units': pd.Series(dtype='float64'),
            'Remaining Units': pd.Series(dtype='float64'),
            'Position Size': pd.Series(dtype='float64')
        })
        
        # Partial sales history DataFrame
        self.sales_history = pd.DataFrame({
            'trade_id': pd.Series(dtype='int64'),
            'Date': pd.Series(dtype='datetime64[ns]'),
            'Units Sold': pd.Series(dtype='float64'),
            'Exit Price': pd.Series(dtype='float64'),
            'Partial P/L': pd.Series(dtype='float64'),
            'Partial P/L %': pd.Series(dtype='float64')
        })
        
        self.trade_counter = 0

    def validate_numeric(self, value, field_name):
        """Validate numeric input"""
        try:
            if value is None or str(value).strip() == '':
                raise ValueError(f"{field_name} is required")
            value = float(value)
            if pd.isna(value) or value <= 0:
                raise ValueError(f"{field_name} must be a positive number")
            return value
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid {field_name}: {str(e)}")

    def calculate_position_size(self, entry_price, units):
        """Calculate position size based on entry price and units"""
        return float(entry_price * units)
    
    def calculate_profit_loss(self, entry_price, exit_price, units):
        """Calculate profit/loss in dollar amount"""
        return float((exit_price - entry_price) * units)
    
    def calculate_win_loss_percentage(self, entry_price, exit_price):
        """Calculate percentage gain/loss"""
        return float(((exit_price - entry_price) / entry_price) * 100)

    def add_trade(self, market, entry_price, units):
        """Add a new trade with simplified parameters"""
        try:
            # Validate market
            if not market or not isinstance(market, str):
                raise ValueError("Market symbol is required and must be a string")
            
            # Validate numeric inputs
            entry_price = self.validate_numeric(entry_price, "Entry price")
            units = self.validate_numeric(units, "Units")
            
            # Generate unique trade ID
            self.trade_counter += 1
            trade_id = self.trade_counter
            
            # Calculate initial position size
            position_size = self.calculate_position_size(entry_price, units)
            
            # Create trade record
            trade = {
                'id': trade_id,
                'Date': datetime.now(),
                'Market': market.upper(),
                'Entry Price': float(entry_price),
                'Units': float(units),
                'Remaining Units': float(units),
                'Position Size': float(position_size)
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
            # Find the trade
            trade_rows = self.trades[self.trades['id'] == trade_id]
            if len(trade_rows) == 0:
                raise ValueError("Trade not found")
            
            trade_idx = trade_rows.index[0]
            trade = self.trades.iloc[trade_idx]
            
            # Validate inputs
            units_to_sell = self.validate_numeric(units_to_sell, "Units to sell")
            exit_price = self.validate_numeric(exit_price, "Exit price")
            
            # Check remaining units
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
            
            # Update remaining units
            remaining_units = trade['Remaining Units'] - units_to_sell
            self.trades.at[trade_idx, 'Remaining Units'] = remaining_units
            
            # Update position size based on remaining units
            self.trades.at[trade_idx, 'Position Size'] = self.calculate_position_size(
                trade['Entry Price'],
                remaining_units
            )
            
            # Add to sales history
            new_sale = pd.DataFrame([sale])
            self.sales_history = pd.concat([self.sales_history, new_sale], ignore_index=True)
            
            return {
                'sale': self.clean_trade_data(sale),
                'updated_trade': self.clean_trade_data(self.trades.iloc[trade_idx].to_dict())
            }
            
        except Exception as e:
            raise ValueError(f"Error processing sale: {str(e)}")

    def get_trades_json(self):
        """Get trades data in JSON-serializable format"""
        return self.clean_trade_data(self.trades.to_dict('records'))

    def get_trade_sales_history(self, trade_id):
        """Get sales history for a specific trade"""
        sales = self.sales_history[self.sales_history['trade_id'] == trade_id]
        return self.clean_trade_data(sales.to_dict('records'))

    def get_summary(self):
        """Get comprehensive trading summary"""
        try:
            if self.trades.empty:
                return {
                    'total_trades': 0,
                    'open_trades': 0,
                    'closed_trades': 0,
                    'total_profit_loss': 0.0,
                    'avg_profit_loss_percent': 0.0,
                    'total_invested': 0.0,
                    'current_positions_value': 0.0,
                    'largest_position': 0.0,
                    'avg_position_size': 0.0,
                    'win_rate': 0.0,
                    'trades_by_market': [],
                    'recent_trades': [],
                    'best_performing': None,
                    'worst_performing': None
                }

            # Calculate basic statistics
            open_trades = self.trades[self.trades['Remaining Units'] > 0]
            closed_trades = self.trades[self.trades['Remaining Units'] == 0]
            
            # Calculate total P/L from sales
            total_pl = float(self.sales_history['Partial P/L'].sum()) if not self.sales_history.empty else 0.0
            
            # Calculate win rate
            profitable_sales = self.sales_history[self.sales_history['Partial P/L'] > 0]
            win_rate = float((len(profitable_sales) / len(self.sales_history) * 100)) if not self.sales_history.empty else 0.0
            
            # Group trades by market
            trades_by_market = self.trades.groupby('Market').agg({
                'id': 'count',
                'Position Size': 'sum'
            }).reset_index().rename(columns={'id': 'Count', 'Position Size': 'Total Position'})
            
            # Get best and worst performing trades
            best_trade = None
            worst_trade = None
            if not self.sales_history.empty:
                best_sale_idx = self.sales_history['Partial P/L %'].idxmax()
                worst_sale_idx = self.sales_history['Partial P/L %'].idxmin()
                
                best_trade_id = self.sales_history.loc[best_sale_idx, 'trade_id']
                worst_trade_id = self.sales_history.loc[worst_sale_idx, 'trade_id']
                
                if len(self.trades[self.trades['id'] == best_trade_id]) > 0:
                    best_trade = self.trades[self.trades['id'] == best_trade_id].iloc[0].to_dict()
                if len(self.trades[self.trades['id'] == worst_trade_id]) > 0:
                    worst_trade = self.trades[self.trades['id'] == worst_trade_id].iloc[0].to_dict()

            summary = {
                'total_trades': int(len(self.trades)),
                'open_trades': int(len(open_trades)),
                'closed_trades': int(len(closed_trades)),
                'total_profit_loss': float(total_pl),
                'avg_profit_loss_percent': float(self.sales_history['Partial P/L %'].mean()) if not self.sales_history.empty else 0.0,
                'total_invested': float(self.trades['Position Size'].sum()),
                'current_positions_value': float(open_trades['Position Size'].sum()),
                'largest_position': float(self.trades['Position Size'].max()),
                'avg_position_size': float(self.trades['Position Size'].mean()),
                'win_rate': float(win_rate),
                'trades_by_market': self.clean_trade_data(trades_by_market.to_dict('records')),
                'recent_trades': self.clean_trade_data(self.trades.sort_values('Date', ascending=False).head(5).to_dict('records')),
                'best_performing': self.clean_trade_data(best_trade),
                'worst_performing': self.clean_trade_data(worst_trade)
            }
            
            return summary
            
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return None

    @staticmethod
    def clean_trade_data(data):
        """Clean data for JSON serialization"""
        if data is None:
            return None
        if isinstance(data, (list, tuple)):
            return [TradeCalculator.clean_trade_data(item) for item in data]
        if isinstance(data, dict):
            return {
                k: (
                    v.isoformat() if isinstance(v, datetime)
                    else None if pd.isna(v)
                    else float(v) if isinstance(v, (np.floating, np.integer))
                    else str(v) if isinstance(v, str)
                    else v
                )
                for k, v in data.items()
            }
        return data
