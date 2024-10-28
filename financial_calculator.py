import pandas as pd
import numpy as np
from datetime import datetime
import os
import requests
pd.set_option('display.float_format', lambda x: '%.2f' % x)

class TradeCalculator:
    def __init__(self):
        # Main trades DataFrame with proper dtypes
        self.trades = pd.DataFrame({
            'id': pd.Series(dtype='int64'),
            'Date': pd.Series(dtype='datetime64[ns]'),
            'Market': pd.Series(dtype='string'),
            'Entry Price': pd.Series(dtype='float64'),
            'Units': pd.Series(dtype='float64'),
            'Remaining Units': pd.Series(dtype='float64'),
            'Position Size': pd.Series(dtype='float64')
        })
        
        # Partial sales history DataFrame with proper dtypes
        self.sales_history = pd.DataFrame({
            'trade_id': pd.Series(dtype='int64'),
            'Date': pd.Series(dtype='datetime64[ns]'),
            'Units Sold': pd.Series(dtype='float64'),
            'Exit Price': pd.Series(dtype='float64'),
            'Partial P/L': pd.Series(dtype='float64'),
            'Partial P/L %': pd.Series(dtype='float64')
        })
        
        self.trade_counter = 0
        self.api_key = os.getenv('COINMARKETCAP_API_KEY')
        if not self.api_key:
            raise ValueError("COINMARKETCAP_API_KEY environment variable is not set")

    def fetch_latest_prices(self, symbols):
        """Fetch latest prices from CoinMarketCap API"""
        if not symbols:
            return {}
        
        try:
            # Convert trading pair symbols to CoinMarketCap format
            formatted_symbols = []
            for symbol in symbols:
                # Remove /USD or /USDT suffix and convert to uppercase
                base_symbol = symbol.split('/')[0].upper()
                formatted_symbols.append(base_symbol)
            
            symbol_string = ','.join(formatted_symbols)
            
            url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
            parameters = {
                'symbol': symbol_string,
                'convert': 'USD'
            }
            headers = {
                'X-CMC_PRO_API_KEY': self.api_key,
                'Accept': 'application/json'
            }

            response = requests.get(url, headers=headers, params=parameters)
            response.raise_for_status()  # Raise exception for bad status codes
            data = response.json()
            
            if 'data' not in data:
                print(f"No data in response: {data}")
                return {}
                
            prices = {}
            for symbol in formatted_symbols:
                if symbol in data['data']:
                    price = data['data'][symbol]['quote']['USD']['price']
                    # Reconstruct original trading pair format
                    original_symbol = next(s for s in symbols if s.startswith(symbol))
                    prices[original_symbol] = price
                    
            return prices
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {str(e)}")
            return {}
        except Exception as e:
            print(f"Error processing API response: {str(e)}")
            return {}

    def validate_numeric(self, value, field_name):
        """Validate numeric input"""
        if value is None or value == '':
            return None
        try:
            value = float(value)
            if pd.isna(value):
                return None
            if value <= 0:
                raise ValueError(f"{field_name} must be greater than zero")
            return value
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric value for {field_name}")

    @staticmethod
    def calculate_position_size(entry_price, units):
        """Calculate position size based on entry price and units"""
        return float(entry_price * units)

    @staticmethod
    def calculate_profit_loss(entry_price, exit_price, units):
        """Calculate profit/loss in dollar amount"""
        return float((exit_price - entry_price) * units)

    @staticmethod
    def calculate_win_loss_percentage(entry_price, exit_price):
        """Calculate percentage gain/loss"""
        return float(((exit_price - entry_price) / entry_price) * 100)

    def add_trade(self, market, entry_price, units):
        """Add a new trade with improved validation"""
        try:
            # Validate market format
            if not market or not isinstance(market, str):
                raise ValueError("Market symbol is required and must be a string")
            
            # Ensure market follows the correct format (e.g., BTC/USDT)
            if '/' not in market:
                market = f"{market}/USDT"  # Add default quote currency if missing
            market = market.upper()
            
            # Validate other inputs
            entry_price = self.validate_numeric(entry_price, "Entry price")
            units = self.validate_numeric(units, "Units")
            
            if entry_price is None or units is None:
                raise ValueError("Entry price and units must be positive numbers")
            
            # Verify the market exists by fetching its price
            latest_prices = self.fetch_latest_prices([market])
            if not latest_prices:
                raise ValueError(f"Could not verify market {market}. Please check the symbol.")
            
            # Generate unique trade ID
            self.trade_counter += 1
            trade_id = self.trade_counter
            
            # Calculate initial position size
            position_size = self.calculate_position_size(entry_price, units)
            
            # Create new trade
            new_trade = pd.DataFrame({
                'id': [trade_id],
                'Date': [datetime.now()],
                'Market': [market],
                'Entry Price': [entry_price],
                'Units': [units],
                'Remaining Units': [units],
                'Position Size': [position_size]
            })
            
            # Add to trades DataFrame
            self.trades = pd.concat(
                [self.trades, new_trade],
                ignore_index=True
            ).astype(self.trades.dtypes.to_dict())
            
            return self.clean_trade_data(new_trade.iloc[0].to_dict())
            
        except Exception as e:
            print(f"Error adding trade: {str(e)}")
            raise ValueError(str(e))

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
            
            # Record the sale with proper types
            sale = pd.DataFrame({
                'trade_id': [trade_id],
                'Date': [datetime.now()],
                'Units Sold': [units_to_sell],
                'Exit Price': [exit_price],
                'Partial P/L': [partial_pl],
                'Partial P/L %': [partial_pl_percent]
            })
            
            # Update remaining units
            remaining_units = trade['Remaining Units'] - units_to_sell
            self.trades.at[trade_idx, 'Remaining Units'] = remaining_units
            
            # Update position size based on remaining units
            self.trades.at[trade_idx, 'Position Size'] = self.calculate_position_size(
                trade['Entry Price'], 
                remaining_units
            )
            
            # Add to sales history with proper types
            self.sales_history = pd.concat(
                [self.sales_history, sale],
                ignore_index=True
            ).astype(self.sales_history.dtypes.to_dict())
            
            return {
                'sale': self.clean_trade_data(sale.iloc[0].to_dict()),
                'updated_trade': self.clean_trade_data(self.trades.iloc[trade_idx].to_dict())
            }
            
        except Exception as e:
            raise ValueError(f"Error processing sale: {str(e)}")

    def get_trade_sales_history(self, trade_id):
        """Get sales history for a specific trade"""
        sales = self.sales_history[self.sales_history['trade_id'] == trade_id]
        return self.clean_trade_data(sales.to_dict('records'))

    def get_trades_json(self):
        """Get trades data in JSON-serializable format"""
        return self.clean_trade_data(self.trades.to_dict('records'))

    def get_summary(self):
        """Get comprehensive trading summary"""
        if self.trades.empty:
            return {
                'total_trades': 0,
                'open_trades': 0,
                'closed_trades': 0,
                'total_profit_loss': 0,
                'avg_profit_loss_percent': 0,
                'total_invested': 0,
                'current_positions_value': 0,
                'largest_position': 0,
                'avg_position_size': 0,
                'win_rate': 0,
                'trades_by_market': [],
                'recent_trades': [],
                'best_performing': None,
                'worst_performing': None
            }

        # Calculate basic statistics
        open_trades = self.trades[self.trades['Remaining Units'] > 0]
        closed_trades = self.trades[self.trades['Remaining Units'] == 0]
        
        # Fetch latest prices for open trades
        open_market_symbols = open_trades['Market'].unique().tolist()
        latest_prices = self.fetch_latest_prices(open_market_symbols)
        
        # Calculate total P/L from sales
        total_pl = self.sales_history['Partial P/L'].sum()
        
        # Add unrealized P/L from open positions using latest prices
        for _, trade in open_trades.iterrows():
            if trade['Market'] in latest_prices:
                current_price = latest_prices[trade['Market']]
                unrealized_pl = self.calculate_profit_loss(
                    trade['Entry Price'],
                    current_price,
                    trade['Remaining Units']
                )
                total_pl += unrealized_pl
        
        # Calculate win rate
        profitable_sales = self.sales_history[self.sales_history['Partial P/L'] > 0]
        win_rate = len(profitable_sales) / len(self.sales_history) * 100 if not self.sales_history.empty else 0
        
        # Group trades by market and include latest prices
        trades_by_market = self.trades.groupby('Market').agg({
            'id': 'count',
            'Position Size': 'sum'
        }).reset_index()
        trades_by_market.columns = ['Market', 'Count', 'Total Position']
        
        # Add Latest Price column
        trades_by_market['Latest Price'] = trades_by_market['Market'].map(latest_prices)
        
        # Get best and worst performing trades based on P/L%
        if not self.sales_history.empty:
            best_sale = self.sales_history.loc[self.sales_history['Partial P/L %'].idxmax()]
            worst_sale = self.sales_history.loc[self.sales_history['Partial P/L %'].idxmin()]
            
            best_trade = self.trades[self.trades['id'] == best_sale['trade_id']].iloc[0]
            worst_trade = self.trades[self.trades['id'] == worst_sale['trade_id']].iloc[0]
        else:
            best_trade = None
            worst_trade = None

        summary = {
            'total_trades': len(self.trades),
            'open_trades': len(open_trades),
            'closed_trades': len(closed_trades),
            'total_profit_loss': float(total_pl),
            'avg_profit_loss_percent': float(self.sales_history['Partial P/L %'].mean()) if not self.sales_history.empty else 0,
            'total_invested': float(self.trades['Position Size'].sum()),
            'current_positions_value': float(open_trades['Position Size'].sum()),
            'largest_position': float(self.trades['Position Size'].max()),
            'avg_position_size': float(self.trades['Position Size'].mean()),
            'win_rate': float(win_rate),
            'trades_by_market': trades_by_market.to_dict('records'),
            'recent_trades': self.clean_trade_data(self.trades.sort_values('Date', ascending=False).head(5).to_dict('records')),
            'best_performing': self.clean_trade_data(best_trade.to_dict()) if best_trade is not None else None,
            'worst_performing': self.clean_trade_data(worst_trade.to_dict()) if worst_trade is not None else None
        }
        
        return summary

    @staticmethod
    def clean_trade_data(data):
        """Clean data for JSON serialization"""
        if isinstance(data, (list, tuple)):
            return [TradeCalculator.clean_trade_data(item) for item in data]
        elif isinstance(data, dict):
            return {k: (v.isoformat() if isinstance(v, datetime) else None if pd.isna(v) else v) 
                   for k, v in data.items()}
        return data
