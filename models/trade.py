from datetime import datetime
from .database import db

class Trade(db.Model):
    __tablename__ = 'trade'
    
    id = db.Column(db.Integer, primary_key=True)
    market = db.Column(db.String(20), nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    units = db.Column(db.Float, nullable=False)
    remaining_units = db.Column(db.Float, nullable=False)
    position_size = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    
    # Define relationship with Sale using string reference
    sales = db.relationship('Sale', backref=db.backref('trade', lazy=True),
                          lazy=True, cascade='all, delete-orphan')

    def __init__(self, market, entry_price, units, user_id):
        self.market = market
        self.entry_price = entry_price
        self.units = units
        self.remaining_units = units
        self.position_size = entry_price * units
        self.user_id = user_id

    def __repr__(self):
        return f'<Trade {self.market} - {self.units}>'
