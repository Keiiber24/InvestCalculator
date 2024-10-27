import pandas as pd
import numpy as np
from datetime import datetime
import os
import requests
import logging
from requests.exceptions import Timeout, RequestException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            logger.warning("CoinMarketCap API key not found in environment variables")

    def fetch_latest_prices(self, symbols):
        """Fetch latest prices from CoinMarketCap API"""
        if not symbols:
            logger.info("No symbols provided to fetch prices")
            return {}
        
        if not self.api_key:
            logger.error("CoinMarketCap API key not available")
            return {}

        # Convert trading pair symbols to CoinMarketCap format
        formatted_symbols = []
        symbol_mapping = {}
        
        for symbol in symbols:
            # Remove /USD or /USDT suffix and convert to uppercase
            base_symbol = symbol.split('/')[0].upper()
            formatted_symbols.append(base_symbol)
            symbol_mapping[base_symbol] = symbol
            logger.info(f"Formatted symbol: {symbol} -> {base_symbol}")
        
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

        try:
            # Add timeout to prevent hanging
            response = requests.get(url, headers=headers, params=parameters, timeout=10)
            response.raise_for_status()  # Raise exception for bad status codes
            data = response.json()
            
            logger.debug(f"API Response: {data}")
            
            if 'data' not in data:
                logger.error(f"Invalid API response format: {data}")
                return {}
                
            prices = {}
            for base_symbol in formatted_symbols:
                if base_symbol in data['data']:
                    price = data['data'][base_symbol]['quote']['USD']['price']
                    original_symbol = symbol_mapping[base_symbol]
                    prices[original_symbol] = price
                    logger.info(f"Got price for {original_symbol}: {price}")
                else:
                    logger.warning(f"No price data found for symbol: {base_symbol}")
            
            return prices
            
        except Timeout:
            logger.error("Request timed out while fetching prices from CoinMarketCap")
            return {}
        except RequestException as e:
            logger.error(f"Error fetching prices from CoinMarketCap: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error while fetching prices: {str(e)}")
            return {}

    # ... [rest of the class implementation remains the same]
