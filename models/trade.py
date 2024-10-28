from .database import db
from datetime import datetime

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    market = db.Column(db.String(20), nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    units = db.Column(db.Float, nullable=False)
    remaining_units = db.Column(db.Float, nullable=False)
    position_size = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
