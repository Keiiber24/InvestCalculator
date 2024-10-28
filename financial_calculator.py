import pandas as pd
import numpy as np
from datetime import datetime
import os
import requests
import logging
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pd.set_option('display.float_format', lambda x: '%.2f' % x)

class TradeCalculator:
    def __init__(self, user_id=None):
        self.user_id = user_id
        # Add user_id to DataFrame structures
        self.trades = pd.DataFrame({
            'id': pd.Series(dtype='int64'),
            'user_id': pd.Series(dtype='int64'),
            'Date': pd.Series(dtype='datetime64[ns]'),
            'Market': pd.Series(dtype='string'),
            'Entry Price': pd.Series(dtype='float64'),
            'Units': pd.Series(dtype='float64'),
            'Remaining Units': pd.Series(dtype='float64'),
            'Position Size': pd.Series(dtype='float64')
        })
        
        self.sales_history = pd.DataFrame({
            'trade_id': pd.Series(dtype='int64'),
            'user_id': pd.Series(dtype='int64'),
            'Date': pd.Series(dtype='datetime64[ns]'),
            'Units Sold': pd.Series(dtype='float64'),
            'Exit Price': pd.Series(dtype='float64'),
            'Partial P/L': pd.Series(dtype='float64'),
            'Partial P/L %': pd.Series(dtype='float64')
        })
        
        self.trade_counter = 0
        self.api_key = os.getenv('COINMARKETCAP_API_KEY')
        if not self.api_key:
            logger.error("COINMARKETCAP_API_KEY environment variable is not set")
            raise ValueError("COINMARKETCAP_API_KEY environment variable is not set")
        
        # Configure session with retry logic
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def fetch_latest_prices(self, symbols):
        """Fetch latest prices from CoinMarketCap API with improved error handling and retry logic"""
        if not symbols:
            logger.warning("No symbols provided to fetch_latest_prices")
            return {}
        
        try:
            # Convert trading pair symbols to CoinMarketCap format
            formatted_symbols = []
            original_to_formatted = {}
            
            for symbol in symbols:
                try:
                    # Remove /USD or /USDT suffix and convert to uppercase
                    parts = symbol.split('/')
                    if len(parts) != 2 or parts[1] not in ['USD', 'USDT']:
                        logger.warning(f"Invalid market symbol format: {symbol}")
                        continue
                        
                    base_symbol = parts[0].upper()
                    formatted_symbols.append(base_symbol)
                    original_to_formatted[base_symbol] = symbol
                except Exception as e:
                    logger.error(f"Error formatting symbol {symbol}: {str(e)}")
                    continue
            
            if not formatted_symbols:
                logger.error("No valid symbols to query")
                return {}
            
            symbol_string = ','.join(formatted_symbols)
            logger.info(f"Fetching prices for symbols: {symbol_string}")
            
            url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
            parameters = {
                'symbol': symbol_string,
                'convert': 'USD'
            }
            headers = {
                'X-CMC_PRO_API_KEY': self.api_key,
                'Accept': 'application/json'
            }

            start_time = time.time()
            response = self.session.get(url, headers=headers, params=parameters, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"API request completed in {time.time() - start_time:.2f} seconds")
            
            if 'status' not in data:
                logger.error("Invalid API response format - missing status")
                return {}
                
            if data['status']['error_code'] != 0:
                logger.error(f"API error: {data['status']['error_message']}")
                return {}
            
            if 'data' not in data:
                logger.error(f"No data in response: {data}")
                return {}
            
            prices = {}
            for formatted_symbol, coin_data in data['data'].items():
                try:
                    if coin_data.get('quote', {}).get('USD', {}).get('price'):
                        original_symbol = original_to_formatted.get(formatted_symbol)
                        if original_symbol:
                            price = coin_data['quote']['USD']['price']
                            prices[original_symbol] = price
                            logger.info(f"Got price for {original_symbol}: {price}")
                except Exception as e:
                    logger.error(f"Error processing price data for {formatted_symbol}: {str(e)}")
                    continue
            
            return prices

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error processing API response: {str(e)}")
            return {}

    def validate_market_symbol(self, market):
        """Validate market symbol format"""
        if not market or not isinstance(market, str):
            raise ValueError("Market symbol is required and must be a string")
        
        # Normalize market symbol
        market = market.upper()
        if '/' not in market:
            market = f"{market}/USDT"
        
        parts = market.split('/')
        if len(parts) != 2 or parts[1] not in ['USD', 'USDT']:
            raise ValueError("Invalid market symbol format. Must be in format BASE/USDT or BASE/USD")
        
        return market

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

    def add_trade(self, market, entry_price, units, user_id=None):
        """Add a new trade with improved validation and error handling"""
        try:
            user_id = user_id or self.user_id
            if user_id is None:
                raise ValueError("User ID is required")

            # Log incoming trade request
            logger.info(f"Adding trade - Market: {market}, Entry Price: {entry_price}, Units: {units}, User ID: {user_id}")
            
            # Validate and normalize market symbol
            market = self.validate_market_symbol(market)
            
            # Validate other inputs
            entry_price = self.validate_numeric(entry_price, "Entry price")
            units = self.validate_numeric(units, "Units")
            
            if entry_price is None or units is None:
                raise ValueError("Entry price and units must be positive numbers")
            
            # Verify the market exists by fetching its price
            latest_prices = self.fetch_latest_prices([market])
            if not latest_prices:
                raise ValueError(f"Could not verify market {market}. Please check the symbol.")
            
            current_price = latest_prices.get(market)
            price_diff_percent = abs(current_price - entry_price) / current_price * 100
            if price_diff_percent > 10:
                logger.warning(f"Entry price differs significantly ({price_diff_percent:.2f}%) from current market price")
            
            # Generate unique trade ID
            self.trade_counter += 1
            trade_id = self.trade_counter
            
            # Calculate initial position size
            position_size = self.calculate_position_size(entry_price, units)
            
            # Create new trade with user_id
            new_trade = pd.DataFrame({
                'id': [trade_id],
                'user_id': [user_id],
                'Date': [datetime.utcnow()],
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
            
            logger.info(f"Trade added successfully - ID: {trade_id}")
            return self.clean_trade_data(new_trade.iloc[0].to_dict())
            
        except ValueError as e:
            logger.error(f"Trade validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error adding trade: {str(e)}")
            raise ValueError(f"Failed to add trade: {str(e)}")

    def sell_units(self, trade_id, units_to_sell, exit_price, user_id=None):
        """Record a partial sale of units with user_id support"""
        try:
            user_id = user_id or self.user_id
            if user_id is None:
                raise ValueError("User ID is required")

            trade_idx = self.trades.index[
                (self.trades['id'] == trade_id) & 
                (self.trades['user_id'] == user_id)
            ].tolist()

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
            
            # Record the sale with user_id
            sale = pd.DataFrame({
                'trade_id': [trade_id],
                'user_id': [user_id],
                'Date': [datetime.utcnow()],
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

    def get_trade_sales_history(self, trade_id, user_id=None):
        """Get sales history for a specific trade with user_id filtering"""
        user_id = user_id or self.user_id
        if user_id is None:
            raise ValueError("User ID is required")
            
        sales = self.sales_history[
            (self.sales_history['trade_id'] == trade_id) &
            (self.sales_history['user_id'] == user_id)
        ]
        return self.clean_trade_data(sales.to_dict('records'))

    def get_trades_json(self, user_id=None):
        """Get trades data in JSON-serializable format with user_id filtering"""
        user_id = user_id or self.user_id
        if user_id is None:
            raise ValueError("User ID is required")
            
        user_trades = self.trades[self.trades['user_id'] == user_id]
        return self.clean_trade_data(user_trades.to_dict('records'))

    def get_summary(self, user_id=None):
        """Get comprehensive trading summary with user_id filtering"""
        user_id = user_id or self.user_id
        if user_id is None:
            raise ValueError("User ID is required")

        # Filter trades by user_id
        user_trades = self.trades[self.trades['user_id'] == user_id]
        if user_trades.empty:
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

        # Filter trades and sales by user_id
        user_sales = self.sales_history[self.sales_history['user_id'] == user_id]
        open_trades = user_trades[user_trades['Remaining Units'] > 0]
        closed_trades = user_trades[user_trades['Remaining Units'] == 0]
        
        # Fetch latest prices for open trades
        open_market_symbols = open_trades['Market'].unique().tolist()
        latest_prices = self.fetch_latest_prices(open_market_symbols)
        
        # Calculate total P/L from sales
        total_pl = user_sales['Partial P/L'].sum()
        
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
        
        # Calculate win rate from user's sales
        profitable_sales = user_sales[user_sales['Partial P/L'] > 0]
        win_rate = len(profitable_sales) / len(user_sales) * 100 if not user_sales.empty else 0
        
        # Group trades by market and include latest prices
        trades_by_market = user_trades.groupby('Market').agg({
            'id': 'count',
            'Position Size': 'sum'
        }).reset_index()
        trades_by_market.columns = ['Market', 'Count', 'Total Position']
        
        # Add Latest Price column
        trades_by_market['Latest Price'] = trades_by_market['Market'].map(latest_prices)
        
        # Get best and worst performing trades based on P/L%
        if not user_sales.empty:
            best_sale = user_sales.loc[user_sales['Partial P/L %'].idxmax()]
            worst_sale = user_sales.loc[user_sales['Partial P/L %'].idxmin()]
            
            best_trade = user_trades[user_trades['id'] == best_sale['trade_id']].iloc[0]
            worst_trade = user_trades[user_trades['id'] == worst_sale['trade_id']].iloc[0]
        else:
            best_trade = None
            worst_trade = None

        summary = {
            'total_trades': len(user_trades),
            'open_trades': len(open_trades),
            'closed_trades': len(closed_trades),
            'total_profit_loss': float(total_pl),
            'avg_profit_loss_percent': float(user_sales['Partial P/L %'].mean()) if not user_sales.empty else 0,
            'total_invested': float(user_trades['Position Size'].sum()),
            'current_positions_value': float(open_trades['Position Size'].sum()),
            'largest_position': float(user_trades['Position Size'].max()),
            'avg_position_size': float(user_trades['Position Size'].mean()),
            'win_rate': float(win_rate),
            'trades_by_market': trades_by_market.to_dict('records'),
            'recent_trades': self.clean_trade_data(user_trades.sort_values('Date', ascending=False).head(5).to_dict('records')),
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
