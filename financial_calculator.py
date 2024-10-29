import pandas as pd
import numpy as np
from datetime import datetime
import os
import requests
from models.user import db, Trade, Sale
from flask_login import current_user

pd.set_option('display.float_format', lambda x: '%.2f' % x)

class TradeCalculator:
    def __init__(self):
        self.api_key = os.getenv('COINMARKETCAP_API_KEY')

    def fetch_latest_prices(self, symbols):
        """Fetch latest prices from CoinMarketCap API"""
        if not symbols:
            return {}
        
        formatted_symbols = []
        for symbol in symbols:
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

        try:
            response = requests.get(url, headers=headers, params=parameters)
            data = response.json()
            
            if 'data' not in data:
                return {}
                
            prices = {}
            for symbol in formatted_symbols:
                if symbol in data['data']:
                    price = data['data'][symbol]['quote']['USD']['price']
                    original_symbol = next(s for s in symbols if s.startswith(symbol))
                    prices[original_symbol] = price
                    
            return prices
        except Exception as e:
            print(f"Error fetching prices: {str(e)}")
            return {}

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

    def add_trade(self, market, entry_price, units):
        """Add a new trade with user association"""
        try:
            if not market or not isinstance(market, str):
                raise ValueError("Market symbol is required and must be a string")
            
            entry_price = self.validate_numeric(entry_price, "Entry price")
            units = self.validate_numeric(units, "Units")
            
            if entry_price is None:
                raise ValueError("Entry price is required and must be a positive number")
            
            if units is None:
                raise ValueError("Units is required and must be a positive number")
            
            position_size = self.calculate_position_size(entry_price, units)
            
            trade = Trade(
                market=market.upper(),
                entry_price=entry_price,
                units=units,
                remaining_units=units,
                position_size=position_size,
                user_id=current_user.id
            )
            
            db.session.add(trade)
            db.session.commit()
            
            return self.clean_trade_data(self.trade_to_dict(trade))
            
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error adding trade: {str(e)}")

    def sell_units(self, trade_id, units_to_sell, exit_price):
        """Record a partial sale of units"""
        try:
            trade = Trade.query.filter_by(id=trade_id, user_id=current_user.id).first()
            if not trade:
                raise ValueError("Trade not found")
            
            units_to_sell = self.validate_numeric(units_to_sell, "Units to sell")
            exit_price = self.validate_numeric(exit_price, "Exit price")
            
            if units_to_sell > trade.remaining_units:
                raise ValueError("Cannot sell more units than remaining")
            
            partial_pl = self.calculate_profit_loss(trade.entry_price, exit_price, units_to_sell)
            partial_pl_percent = self.calculate_win_loss_percentage(trade.entry_price, exit_price)
            
            sale = Sale(
                units_sold=units_to_sell,
                exit_price=exit_price,
                partial_pl=partial_pl,
                partial_pl_percentage=partial_pl_percent,
                trade_id=trade.id
            )
            
            trade.remaining_units -= units_to_sell
            trade.position_size = self.calculate_position_size(trade.entry_price, trade.remaining_units)
            
            db.session.add(sale)
            db.session.commit()
            
            return {
                'sale': self.clean_trade_data(self.sale_to_dict(sale)),
                'updated_trade': self.clean_trade_data(self.trade_to_dict(trade))
            }
            
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error processing sale: {str(e)}")

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

    def get_trade_sales_history(self, trade_id):
        """Get sales history for a specific trade"""
        trade = Trade.query.filter_by(id=trade_id, user_id=current_user.id).first()
        if not trade:
            return []
        return [self.clean_trade_data(self.sale_to_dict(sale)) for sale in trade.sales]

    def get_trades_json(self):
        """Get trades data in JSON-serializable format"""
        trades = Trade.query.filter_by(user_id=current_user.id).all()
        return [self.clean_trade_data(self.trade_to_dict(trade)) for trade in trades]

    def get_summary(self):
        """Get comprehensive trading summary"""
        trades = Trade.query.filter_by(user_id=current_user.id).all()
        if not trades:
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

        open_trades = [t for t in trades if t.remaining_units > 0]
        closed_trades = [t for t in trades if t.remaining_units == 0]
        
        open_market_symbols = list(set(t.market for t in open_trades))
        latest_prices = self.fetch_latest_prices(open_market_symbols)
        
        total_pl = sum(sale.partial_pl for trade in trades for sale in trade.sales)
        
        for trade in open_trades:
            if trade.market in latest_prices:
                current_price = latest_prices[trade.market]
                unrealized_pl = self.calculate_profit_loss(
                    trade.entry_price,
                    current_price,
                    trade.remaining_units
                )
                total_pl += unrealized_pl

        all_sales = [sale for trade in trades for sale in trade.sales]
        profitable_sales = [sale for sale in all_sales if sale.partial_pl > 0]
        win_rate = (len(profitable_sales) / len(all_sales) * 100) if all_sales else 0
        
        trades_by_market = {}
        for trade in trades:
            if trade.market not in trades_by_market:
                trades_by_market[trade.market] = {
                    'Market': trade.market,
                    'Count': 0,
                    'Total Position': 0
                }
            trades_by_market[trade.market]['Count'] += 1
            trades_by_market[trade.market]['Total Position'] += trade.position_size
            if trade.market in latest_prices:
                trades_by_market[trade.market]['Latest Price'] = latest_prices[trade.market]

        trades_by_market = list(trades_by_market.values())
        
        best_sale = None
        worst_sale = None
        if all_sales:
            best_sale = max(all_sales, key=lambda x: x.partial_pl_percentage)
            worst_sale = min(all_sales, key=lambda x: x.partial_pl_percentage)

        return {
            'total_trades': len(trades),
            'open_trades': len(open_trades),
            'closed_trades': len(closed_trades),
            'total_profit_loss': float(total_pl),
            'avg_profit_loss_percent': float(sum(s.partial_pl_percentage for s in all_sales) / len(all_sales)) if all_sales else 0,
            'total_invested': float(sum(t.position_size for t in trades)),
            'current_positions_value': float(sum(t.position_size for t in open_trades)),
            'largest_position': float(max(t.position_size for t in trades)) if trades else 0,
            'avg_position_size': float(sum(t.position_size for t in trades) / len(trades)) if trades else 0,
            'win_rate': float(win_rate),
            'trades_by_market': trades_by_market,
            'recent_trades': [self.clean_trade_data(self.trade_to_dict(t)) for t in sorted(trades, key=lambda x: x.date, reverse=True)[:5]],
            'best_performing': self.clean_trade_data(self.trade_to_dict(best_sale.trade)) if best_sale else None,
            'worst_performing': self.clean_trade_data(self.trade_to_dict(worst_sale.trade)) if worst_sale else None
        }

    @staticmethod
    def clean_trade_data(data):
        """Clean data for JSON serialization"""
        if isinstance(data, (list, tuple)):
            return [TradeCalculator.clean_trade_data(item) for item in data]
        elif isinstance(data, dict):
            return {k: (v.isoformat() if isinstance(v, datetime) else None if pd.isna(v) else v) 
                   for k, v in data.items()}
        return data

    @staticmethod
    def trade_to_dict(trade):
        """Convert Trade model to dictionary"""
        return {
            'id': trade.id,
            'Date': trade.date,
            'Market': trade.market,
            'Entry Price': trade.entry_price,
            'Units': trade.units,
            'Remaining Units': trade.remaining_units,
            'Position Size': trade.position_size
        }

    @staticmethod
    def sale_to_dict(sale):
        """Convert Sale model to dictionary"""
        return {
            'trade_id': sale.trade_id,
            'Date': sale.date,
            'Units Sold': sale.units_sold,
            'Exit Price': sale.exit_price,
            'Partial P/L': sale.partial_pl,
            'Partial P/L %': sale.partial_pl_percentage
        }
