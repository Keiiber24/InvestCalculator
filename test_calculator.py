#!/usr/bin/env python3
from financial_calculator import TradeCalculator
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api():
    """Test CoinMarketCap API integration"""
    calc = TradeCalculator()
    
    # Test price fetching for multiple symbols
    test_symbols = ['BTC/USDT', 'ETH/USDT']
    logger.info(f"Testing price fetch for symbols: {test_symbols}")
    prices = calc.fetch_latest_prices(test_symbols)
    logger.info(f"Fetched prices: {prices}")
    
    # Add test trades
    logger.info("Adding test trades")
    trades = []
    for symbol, price in prices.items():
        trade = calc.add_trade(symbol, price, 0.5)
        trades.append(trade)
        logger.info(f"Added trade for {symbol}: {trade}")
    
    # Get summary to test price integration
    logger.info("Getting trade summary")
    summary = calc.get_summary()
    logger.info("Trades by market:")
    for market_data in summary['trades_by_market']:
        logger.info(f"Market: {market_data['Market']}")
        logger.info(f"Latest Price: {market_data.get('Latest Price', 'N/A')}")

if __name__ == "__main__":
    test_api()
