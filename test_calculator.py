#!/usr/bin/env python3
import logging
from financial_calculator import TradeCalculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Initialize calculator
    calc = TradeCalculator()
    
    # Test CoinMarketCap API integration
    test_symbols = ['BTC/USDT', 'ETH/USDT']
    logger.info(f"Testing price fetch for symbols: {test_symbols}")
    prices = calc.fetch_latest_prices(test_symbols)
    logger.info(f"Fetched prices: {prices}")
    
    if not prices:
        logger.error("Failed to fetch prices from CoinMarketCap API")
        return
    
    # Add test trades
    logger.info("Adding test trades")
    trades_added = []
    for symbol in test_symbols:
        if symbol in prices:
            try:
                trade = calc.add_trade(symbol, prices[symbol], 0.5)
                trades_added.append(trade)
                logger.info(f"Added trade for {symbol}: {trade}")
            except Exception as e:
                logger.error(f"Error adding trade for {symbol}: {str(e)}")
    
    if not trades_added:
        logger.error("No trades were added successfully")
        return
    
    # Get and display summary to verify price updates
    try:
        logger.info("Getting trade summary")
        summary = calc.get_summary()
        
        # Log trades by market to verify latest prices
        logger.info("Trades by market:")
        if summary['trades_by_market']:
            for market in summary['trades_by_market']:
                logger.info(f"Market: {market['Market']}")
                logger.info(f"Latest Price: {market.get('Latest Price')}")
        else:
            logger.warning("No trades by market data available")
    except Exception as e:
        logger.error(f"Error getting summary: {str(e)}")

if __name__ == "__main__":
    main()
