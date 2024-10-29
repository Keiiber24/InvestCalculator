#!/usr/bin/env python3
import logging
from financial_calculator import TradeCalculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__main__)

def main():
    # Initialize calculator
    calc = TradeCalculator()
    
    # Test CoinMarketCap API integration
    test_symbols = ['BTC/USDT', 'ETH/USDT']
    logger.info(f"Testing price fetch for symbols: {test_symbols}")
    prices = calc.fetch_latest_prices(test_symbols)
    logger.info(f"Fetched prices: {prices}")
    
    # Add test trades
    logger.info("Adding test trades")
    for symbol in test_symbols:
        if symbol in prices:
            trade = calc.add_trade(symbol, prices[symbol], 0.5)
            logger.info(f"Added trade for {symbol}: {trade}")
    
    # Get and display summary to verify price updates
    logger.info("Getting trade summary")
    summary = calc.get_summary()
    
    # Log trades by market to verify latest prices
    logger.info("Trades by market:")
    for market in summary['trades_by_market']:
        logger.info(f"Market: {market['Market']}")
        logger.info(f"Latest Price: {market.get('Latest Price')}")

if __name__ == "__main__":
    main()
