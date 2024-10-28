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

    # Rest of the class implementation remains the same
