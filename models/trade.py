from .database import db
from datetime import datetime

class Trade(db.Model):
    __tablename__ = 'trade'
    
    id = db.Column(db.Integer, primary_key=True)
    market = db.Column(db.String(20), nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    units = db.Column(db.Float, nullable=False)
    remaining_units = db.Column(db.Float, nullable=False)
    position_size = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Add the relationship here instead of in User model
    user = db.relationship('User', backref=db.backref('trades', lazy='dynamic'))

    def __repr__(self):
        return f'<Trade {self.market} - {self.units}>'
