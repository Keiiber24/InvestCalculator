from datetime import datetime
from .database import db

class Sale(db.Model):
    __tablename__ = 'sale'
    
    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.Integer, db.ForeignKey('trade.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    units_sold = db.Column(db.Float, nullable=False)
    exit_price = db.Column(db.Float, nullable=False)
    profit_loss = db.Column(db.Float, nullable=False)
    profit_loss_percentage = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Changed relationship without backref
    user = db.relationship('User')

    def __init__(self, trade_id, units_sold, exit_price, entry_price, user_id):
        self.trade_id = trade_id
        self.user_id = user_id
        self.units_sold = units_sold
        self.exit_price = exit_price
        self.profit_loss = (exit_price - entry_price) * units_sold
        self.profit_loss_percentage = ((exit_price - entry_price) / entry_price) * 100

    def __repr__(self):
        return f'<Sale {self.trade_id} - {self.units_sold} units>'
